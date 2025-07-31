import asyncio
import threading
import time
from config.settings import Settings
from events.event_bus import EventBus
from weather.weather_service import WeatherService
from sensors.pir_sensor import PIRSensor
from actuators.actuator_controller import ActuatorController
from camera.camera_service import CameraService
from ai.gemini_service import GeminiService
from gui.weather_gui import WeatherGUI
from utils.logger import setup_logger

# 전역 변수로 이벤트 버스와 루프 공유
shared_event_bus = None
background_loop = None

def start_background_services():
    """백그라운드 서비스들을 별도 스레드에서 실행"""
    global shared_event_bus, background_loop
    
    background_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(background_loop)
    
    settings = Settings()
    logger = setup_logger(settings.LOG_LEVEL)

    # Initialize services with shared event bus
    weather = WeatherService(shared_event_bus, settings)
    pir = PIRSensor(shared_event_bus, settings)
    actuator = ActuatorController(shared_event_bus, settings)
    camera = CameraService(shared_event_bus, settings)
    gemini = GeminiService(shared_event_bus, settings)

    print("백그라운드 서비스 시작됨")

    # Start services
    tasks = [
        weather.start(),
        pir.start(),
        actuator.start()
    ]

    try:
        background_loop.run_until_complete(asyncio.gather(*tasks))
    except Exception as e:
        print(f"백그라운드 서비스 에러: {e}")

def main():
    global shared_event_bus, background_loop
    
    settings = Settings()
    
    # 공유 이벤트 버스 생성
    shared_event_bus = EventBus()

    # 백그라운드 서비스를 별도 스레드에서 시작
    background_thread = threading.Thread(target=start_background_services, daemon=True)
    background_thread.start()
    
    # 백그라운드 루프가 준비될 때까지 잠시 대기
    time.sleep(1)

    # GUI는 메인 스레드에서 실행 (공유 이벤트 버스 사용)
    gui = WeatherGUI(shared_event_bus, background_loop)
    gui.run()

if __name__ == "__main__":
    main()
