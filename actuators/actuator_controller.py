import asyncio
import serial
from config.settings import Settings
from events.event_types import Event, EventType

class ActuatorController:
    def __init__(self, event_bus, settings: Settings):
        self.event_bus = event_bus
        self.settings = settings
        self.serial = None
        self.active = set() # 현재 활성화된 액추에이터 ID를 저장하는 set
        self.first_valid_signal_processed = False # 첫 번째 유효한 신호가 처리되었는지 여부

        self.event_bus.subscribe(EventType.ACTUATOR_POP, self.handle_pop)
        self.event_bus.subscribe(EventType.HUMAN_OUT, self.handle_down)

    async def start(self):
        """시리얼 연결 시작"""
        try:
            self.serial = serial.Serial(
                self.settings.SERIAL_PORT,
                self.settings.SERIAL_BAUDRATE,
                timeout=self.settings.SERIAL_TIMEOUT
            )
            print(f"아두이노 연결 성공: {self.settings.SERIAL_PORT}")
            await asyncio.sleep(2)  # 아두이노 초기화 대기
            
            # 시작 시 모든 액추에이터 초기화 (모두 내림)
            await self.send_command("0")
            self.active.clear() # 시작 시 active 상태도 초기화
            self.first_valid_signal_processed = False # 컨트롤러 시작 시 플래그 초기화
            print("액추에이터 컨트롤러 시작됨")
            
        except Exception as e:
            print(f"아두이노 연결 실패: {e}")
            raise

    async def handle_pop(self, event):
        """필요한 액추에이터들을 올리기"""
        needed_ids = event.detail['needed']
        current_needed_set = set(needed_ids)

        # 첫 번째 유효한 신호가 이미 처리되었다면, 이후 모든 ACTUATOR_POP 이벤트를 무시
        if self.first_valid_signal_processed:
            print("첫 유효 신호 처리 완료. 이후 ACTUATOR_POP 신호는 무시합니다.")
            return

        # 필요한 액추에이터가 전혀 없는 경우 (모두 내릴 때)
        if not needed_ids:
            print("올릴 액추에이터가 없습니다. 모든 액추에이터를 내립니다.")
            await self.send_command("0") # 모든 액추에이터 내리는 명령 전송
            self.active.clear() # 활성화된 액추에이터 목록 초기화
            await asyncio.sleep(2) # 기존 딜레이 유지
            print("액추에이터 팝업 완료 ")
            # 비어있는 신호는 '첫 유효 신호'로 간주하지 않으므로 플래그를 변경하지 않음
            return

        # 첫 번째 유효한 (비어있지 않은) 신호가 들어온 경우
        print(f"첫 번째 유효 신호 감지. 액추에이터 올리기: {needed_ids}")
        
        # 아두이노 코드에 맞게 ID 매핑
        arduino_command = self.map_to_arduino_ids(needed_ids)
        print(f"액추에이터 올리기: {needed_ids} -> 아두이노 명령: '{arduino_command}'")
        
        await self.send_command(arduino_command)
        
        # 활성화된 액추에이터 목록을 현재 필요한 목록으로 업데이트
        self.active = current_needed_set
        
        # 첫 번째 유효 신호 처리 완료 플래그 설정
        self.first_valid_signal_processed = True
        
        # await asyncio.sleep(2)  # 액추에이터 작동 시간 대기 - 이 부분을 제거했습니다.
        
        print("액추에이터 팝업 완료 ")
        

    async def handle_down(self, event):
        """모든 활성화된 액추에이터 내리기"""
        if self.active:
            print(f"액추에이터 내리기: {self.active}")
            # 아두이노 코드에서 '6'은 모든 액추에이터를 내리는 명령
            await self.send_command("6")
            self.active.clear() # 모든 액추에이터가 내려갔으므로 active 상태 초기화
            # 사람이 나갔으므로, 다음 사람이 들어왔을 때 다시 액추에이터가 작동할 수 있도록 플래그 초기화
            self.first_valid_signal_processed = False 
        else:
            print("내릴 액추에이터가 없습니다.")

    def map_to_arduino_ids(self, needed_ids):
        """Python 서비스의 ID를 아두이노 명령어로 매핑"""
        # Python 서비스 ID -> 아두이노 명령 매핑
        mapping = {
            1: '5',  # 우산 -> 1번 액추에이터 (우산)
            2: '3',  # 선크림 -> 3번 액추에이터 (선글라스+선크림) 
            3: '1',  # 핸드크림 (이전 습도 체크 매핑 3번)
            4: '4',  # 마스크 -> 3번 액추에이터 (마스크)
            5: '2',  # 외투(추위) -> 2번 액추에이터 (핫팩)
        }
        
        # 중복 제거하면서 아두이노 명령 생성
        arduino_ids = set()
        for python_id in needed_ids:
            if python_id in mapping:
                arduino_ids.add(mapping[python_id])
            else:
                print(f"알 수 없는 액추에이터 ID: {python_id}")
        
        # 정렬된 문자열로 반환 (예: "13", "24" 등)
        command = ''.join(sorted(arduino_ids))
        return command if command else "0" # 명령이 없으면 '0' (모두 내림)

    async def send_command(self, command):
        """아두이노로 명령 전송"""
        if not self.serial or not self.serial.is_open:
            print("시리얼 연결이 없습니다.")
            return

        try:
            # 아두이노 코드가 '\n'으로 명령의 끝을 인식
            full_command = f"{command}\n"
            self.serial.write(full_command.encode())
            print(f"아두이노로 명령 전송: '{command}'")
            
            # 아두이노 응답 확인 (선택사항)
            await asyncio.sleep(0.1)
            if self.serial.in_waiting > 0:
                response = self.serial.readline().decode('utf-8').rstrip()
                print(f"아두이노 응답: {response}")
            
        except Exception as e:
            print(f"시리얼 명령 전송 오류: {e}")

    async def stop(self):
        """액추에이터 컨트롤러 종료"""
        if self.active:
            print("종료 전 모든 액추에이터 내리기")
            await self.send_command("6")
            self.active.clear()
            
        if self.serial and self.serial.is_open:
            await self.send_command("0")  # 모든 액추에이터 정지 (안전 종료)
            self.serial.close()
            print("시리얼 연결 종료")

    def __del__(self):
        """소멸자에서 시리얼 포트 정리"""
        if hasattr(self, 'serial') and self.serial and self.serial.is_open:
            self.serial.close()
