import asyncio
import serial
from config.settings import Settings
from events.event_types import Event, EventType

class ActuatorController:
    def __init__(self, event_bus, settings: Settings):
        self.event_bus = event_bus
        self.settings = settings
        self.serial = None
        self.active = set()
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
            
            # 시작 시 모든 액추에이터 초기화
            await self.send_command("0")
            print("액추에이터 컨트롤러 시작됨")
            
        except Exception as e:
            print(f"아두이노 연결 실패: {e}")
            raise

    async def handle_pop(self, event):
        """필요한 액추에이터들을 올리기"""
        needed_ids = event.detail['needed']
        
        if not needed_ids:
            print("올릴 액추에이터가 없습니다.")
            return
            
        # 아두이노 코드에 맞게 ID 매핑
        arduino_command = self.map_to_arduino_ids(needed_ids)
        
        print(f"액추에이터 올리기: {needed_ids} -> 아두이노 명령: '{arduino_command}'")
        await self.send_command(arduino_command)
        
        # 활성화된 액추에이터 기록
        self.active.update(needed_ids)

    async def handle_down(self, event):
        """모든 활성화된 액추에이터 내리기"""
        if self.active:
            print(f"액추에이터 내리기: {self.active}")
            # 아두이노 코드에서 '6'은 모든 액추에이터를 내리는 명령
            await self.send_command("6")
            self.active.clear()
            
            # 카메라 캡처 이벤트 발생
            await self.event_bus.emit(Event(EventType.CAMERA_CAPTURE, {}))
        else:
            print("내릴 액추에이터가 없습니다.")

    def map_to_arduino_ids(self, needed_ids):
        """Python 서비스의 ID를 아두이노 명령어로 매핑"""
        # Python 서비스 ID -> 아두이노 명령 매핑
        # weather_service.py의 determine_needed 결과를 아두이노 코드와 매핑
        mapping = {
            1: '1',  # 우산 -> 1번 액추에이터 (우산)
            2: '4',  # 선크림 -> 4번 액추에이터 (선글라스+선크림)
            3: '4',  # 선글라스 -> 4번 액추에이터 (선글라스+선크림)  
            4: '3',  # 마스크 -> 3번 액추에이터 (마스크)
            5: '2'   # 외투(추위) -> 2번 액추에이터 (핫팩)
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
        return command if command else "0"

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
            
            # 액추에이터 작동 시간 대기
            await asyncio.sleep(self.settings.ACTUATOR_OPERATION_TIME)
            
        except Exception as e:
            print(f"시리얼 명령 전송 오류: {e}")

    async def stop(self):
        """액추에이터 컨트롤러 종료"""
        if self.active:
            print("종료 전 모든 액추에이터 내리기")
            await self.send_command("6")
            self.active.clear()
        
        if self.serial and self.serial.is_open:
            await self.send_command("0")  # 모든 액추에이터 정지
            self.serial.close()
            print("시리얼 연결 종료")

    def __del__(self):
        """소멸자에서 시리얼 포트 정리"""
        if hasattr(self, 'serial') and self.serial and self.serial.is_open:
            self.serial.close()
