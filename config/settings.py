import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        self.WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
        self.GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
        self.PIR_PIN = int(os.getenv('PIR_PIN', '18'))
        self.CAMERA_PORT = int(os.getenv('CAMERA_PORT', '0'))
        self.SERIAL_PORT = os.getenv('SERIAL_PORT', '/dev/ttyUSB0')
        self.SERIAL_BAUDRATE = int(os.getenv('SERIAL_BAUDRATE', '9600'))
        self.SERIAL_TIMEOUT = int(os.getenv('SERIAL_TIMEOUT', '2'))
        self.WEATHER_UPDATE_INTERVAL = int(os.getenv('WEATHER_UPDATE_INTERVAL', '300'))
        self.ACTUATOR_OPERATION_TIME = int(os.getenv('ACTUATOR_OPERATION_TIME', '6'))
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

        # Weather thresholds
        self.THRESHOLDS = {
            'precipitation': 0,
            'cold_temp': 40,
            'uv_sunscreen': 6,
            'uv_sunglasses': 3,
            'dust_bad': ['나쁨', '매우나쁨'],
            'low_humidity': 40
        }
