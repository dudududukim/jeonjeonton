import asyncio
import time
import sys # sys 모듈은 여전히 필요하지만, exit() 호출은 제거됩니다.

try:
    import RPi.GPIO as GPIO
except ImportError:
    # RPi.GPIO 모듈이 없는 경우 경고 메시지 출력 후 GPIO를 None으로 설정하여 시뮬레이션 모드로 작동
    print("⚠️ RPi.GPIO 모듈을 찾을 수 없습니다. GPIO 시뮬레이션 모드로 작동합니다.")
    GPIO = None # 프로그램 종료 대신 GPIO를 None으로 설정하여 계속 진행

from config.settings import Settings
from events.event_types import Event, EventType

class PIRSensor:
    def __init__(self, event_bus, settings: Settings):
        self.event_bus = event_bus
        self.settings = settings
        self.present = False # 현재 사람이 있는지 여부
        self.last_detection_time = None # 마지막으로 사람이 감지된 시간

        # 초음파 센서 핀 설정 (settings에서 가져오도록 변경)
        # GPIO가 None이 아닐 때만 핀 설정을 시도
        if GPIO:
            self.TRIG_PIN = settings.ULTRASONIC_TRIG_PIN
            self.ECHO_PIN = settings.ULTRASONIC_ECHO_PIN
            
            # 감지 임계값 및 안정화 조건 (settings에서 가져오도록 변경)
            self.DETECTION_DISTANCE = settings.ULTRASONIC_DETECTION_DISTANCE # cm
            self.STABLE_DETECTION_COUNT = settings.ULTRASONIC_STABLE_DETECTION_COUNT
            self.TIMEOUT_SECONDS = settings.ULTRASONIC_TIMEOUT_SECONDS

            # GPIO 초기화
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.TRIG_PIN, GPIO.OUT)
            GPIO.setup(self.ECHO_PIN, GPIO.IN)
            GPIO.output(self.TRIG_PIN, False) # TRIG 핀 초기화 (LOW)
            
            print(f"✅ HC-SR04P 초음파 센서 초기화 완료")
            print(f"   TRIG 핀: {self.TRIG_PIN}, ECHO 핀: {self.ECHO_PIN}")
            print(f"   감지 거리: {self.DETECTION_DISTANCE}cm 이내")
            print(f"   안정화 조건: 연속 {self.STABLE_DETECTION_COUNT}번 감지")
            print(f"   타임아웃: {self.TIMEOUT_SECONDS}초")
        else:
            print("⚠️ GPIO 시뮬레이션 모드로 초음파 센서가 작동합니다.")


    def get_distance(self):
        """초음파센서로 거리 측정 (cm 단위)"""
        if not GPIO: # GPIO 시뮬레이션 모드일 경우
            return None # 거리를 측정할 수 없으므로 None 반환

        try:
            # TRIG 핀에 10us 펄스 발생
            GPIO.output(self.TRIG_PIN, True)
            time.sleep(0.00001)
            GPIO.output(self.TRIG_PIN, False)
            
            # ECHO 핀이 HIGH가 될 때까지 대기 (펄스 시작 시간 측정)
            pulse_start = time.time()
            timeout_start = time.time()
            while GPIO.input(self.ECHO_PIN) == 0:
                pulse_start = time.time()
                if time.time() - timeout_start > 0.1: # 0.1초 타임아웃 추가
                    return None
            
            # ECHO 핀이 LOW가 될 때까지 대기 (펄스 종료 시간 측정)
            pulse_end = time.time()
            timeout_end = time.time()
            while GPIO.input(self.ECHO_PIN) == 1:
                pulse_end = time.time()
                if time.time() - timeout_end > 0.1: # 0.1초 타임아웃 추가
                    return None
            
            pulse_duration = pulse_end - pulse_start
            distance = pulse_duration * 17150 # 음속(343m/s)을 이용한 거리 계산 (왕복 거리의 절반)
            
            # 비정상적인 값 필터링 (센서의 유효 측정 범위)
            if distance > 400 or distance < 2: # 2cm ~ 400cm 범위 밖은 무시
                return None
            
            return round(distance, 2)
        except Exception as e:
            # print(f"거리 측정 오류: {e}") # 디버깅 시에만 활성화
            return None

    async def start(self):
        print("🔍 HC-SR04P 초음파 센서 모니터링 시작")
        
        # 센서 안정화 대기
        print("⏳ 센서 안정화 2초 대기...") # 초음파 센서는 PIR보다 안정화 시간이 짧음
        await asyncio.sleep(2)
        print("🚀 인체감지 시작!")
        
        person_present_logic = False # 내부 로직에서 사람 존재 여부
        consecutive_detections = 0 # 연속 감지 횟수
        
        while True:
            # GPIO가 None이면 시뮬레이션 모드로 작동
            if not GPIO:
                # 시뮬레이션 모드에서는 항상 사람이 없다고 가정
                current_state = False
                distance = None # 시뮬레이션 모드에서는 거리 측정 불가
            else:
                distance = self.get_distance()
            
            current_time = time.time()
            
            if distance is None: # 거리 측정 실패 또는 시뮬레이션 모드
                consecutive_detections = 0 # 측정 실패 시 연속 감지 초기화
                # 사람이 있다고 판단된 상태에서 측정 실패가 계속되면 타임아웃 로직으로 넘어감
                if person_present_logic and self.last_detection_time and \
                   current_time - self.last_detection_time >= self.TIMEOUT_SECONDS:
                    if self.present: # 실제 이벤트 발행은 self.present 상태 변화 시에만
                        self.present = False
                        self.last_detection_time = None
                        print(f"👋 사람이 {self.TIMEOUT_SECONDS}초간 감지되지 않음 - HUMAN_OUT 이벤트 발생")
                        await self.event_bus.emit(Event(EventType.HUMAN_OUT, {}))
                await asyncio.sleep(0.1)
                continue
            
            # 감지 범위 내에 물체가 있는지 확인
            if distance <= self.DETECTION_DISTANCE:
                consecutive_detections += 1
                self.last_detection_time = current_time # 감지될 때마다 마지막 감지 시간 업데이트
                
                # 연속으로 안정적인 감지가 이루어졌을 때만 "사람 있음"으로 판단
                if not person_present_logic and consecutive_detections >= self.STABLE_DETECTION_COUNT:
                    person_present_logic = True
                    if not self.present: # 실제 이벤트 발행은 self.present 상태 변화 시에만
                        self.present = True
                        print("🚶 사람 감지됨 - HUMAN_COME 이벤트 발생")
                        await self.event_bus.emit(Event(EventType.HUMAN_COME, {}))
                    
            else: # 감지 범위 밖에 물체가 있을 때
                consecutive_detections = 0 # 연속 감지 카운트 리셋
                
                # 사람이 있다고 판단된 상태에서 일정 시간 동안 감지되지 않으면 "사람 없음"으로 판단
                if person_present_logic and self.last_detection_time and \
                   current_time - self.last_detection_time >= self.TIMEOUT_SECONDS:
                    person_present_logic = False
                    if self.present: # 실제 이벤트 발행은 self.present 상태 변화 시에만
                        self.present = False
                        self.last_detection_time = None # 타이머 리셋
                        print(f"👋 사람이 {self.TIMEOUT_SECONDS}초간 감지되지 않음 - HUMAN_OUT 이벤트 발생")
                        await self.event_bus.emit(Event(EventType.HUMAN_OUT, {}))
            
            await asyncio.sleep(0.1) # 100ms 간격으로 센서 읽기

    def stop(self):
        if GPIO:
            GPIO.cleanup()
            print("🧹 HC-SR04P 센서 GPIO 정리 완료")

