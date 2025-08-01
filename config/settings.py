import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        # API 키 설정
        self.WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
        self.GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

        # 센서 및 통신 핀 설정 (기존 PIR_PIN은 초음파 센서 설정으로 대체)
        # 초음파 센서 설정 (새로 추가되거나 기존 PIR_PIN을 대체)
        self.ULTRASONIC_TRIG_PIN = int(os.getenv('ULTRASONIC_TRIG_PIN', '23'))
        self.ULTRASONIC_ECHO_PIN = int(os.getenv('ULTRASONIC_ECHO_PIN', '24'))
        self.ULTRASONIC_DETECTION_DISTANCE = int(os.getenv('ULTRASONIC_DETECTION_DISTANCE', '120')) # cm
        self.ULTRASONIC_STABLE_DETECTION_COUNT = int(os.getenv('ULTRASONIC_STABLE_DETECTION_COUNT', '3'))
        self.ULTRASONIC_TIMEOUT_SECONDS = int(os.getenv('ULTRASONIC_TIMEOUT_SECONDS', '10')) # 사람이 없다고 판단하는 시간 (초)

        # 카메라 설정
        self.CAMERA_PORT = int(os.getenv('CAMERA_PORT', '0'))

        # 시리얼 통신 설정
        self.SERIAL_PORT = os.getenv('SERIAL_PORT', '/dev/ttyACM0') # 기본값을 /dev/ttyACM0으로 변경 (라즈베리파이 아두이노 기본)
        self.SERIAL_BAUDRATE = int(os.getenv('SERIAL_BAUDRATE', '9600'))
        self.SERIAL_TIMEOUT = float(os.getenv('SERIAL_TIMEOUT', '1')) # float으로 변경

        # 서비스 간격 및 시간 설정
        self.WEATHER_UPDATE_INTERVAL = int(os.getenv('WEATHER_UPDATE_INTERVAL', '3600')) # 1시간 (3600초)
        self.ACTUATOR_OPERATION_TIME = float(os.getenv('ACTUATOR_OPERATION_TIME', '5')) # float으로 변경, 기본값 5초

        # 로깅 설정
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

        # 날씨 임계값 설정 (환경 변수에서 로드하도록 변경)
        self.THRESHOLDS = {
            'precipitation': int(os.getenv('THRESHOLD_PRECIPITATION', '0')), # 강수확률 20% 이상 시 우산
            'cold_temp': float(os.getenv('THRESHOLD_COLD_TEMP', '10')),     # 온도 10도 이하 시 핫팩
            'uv_sunscreen': int(os.getenv('THRESHOLD_UV_SUNSCREEN', '0')),   # 자외선 지수 3 이상 시 선크림 (기존 0에서 3으로 변경)
            'dust_bad': os.getenv('THRESHOLD_DUST_BAD', '좋음,보통,나쁨,매우 나쁨').split(','), # 미세먼지 '나쁨' 이상 시 마스크 (기존 '보통' 포함에서 제거)
            'low_humidity': int(os.getenv('THRESHOLD_LOW_HUMIDITY', '90'))  # 습도 40% 이하 시 핸드크림 (기존 100에서 40으로 변경)
        }

        # 폰트 설정 (새로 추가)
        self.FONT_PATH = os.getenv('FONT_PATH', '/usr/share/fonts/truetype/nanum/NanumGothic.ttf') # 나눔고딕 기본 경로
