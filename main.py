import asyncio
import threading
from config.settings import Settings
from events.event_bus import EventBus
from weather.weather_service import WeatherService
from sensors.pir_sensor import PIRSensor
from actuators.actuator_controller import ActuatorController
from camera.camera_service import CameraService
from ai.gemini_service import GeminiService
from gui.weather_gui import WeatherGUI
from utils.logger import setup_logger

def start_background_services():
    """백그라운드 서비스들을 별도 스레드에서 실행"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    settings = Settings()
    event_bus = EventBus()
    logger = setup_logger(settings.LOG_LEVEL)
    
    # Initialize services
    weather = WeatherService(event_bus, settings)
    pir = PIRSensor(event_bus, settings)
    actuator = ActuatorController(event_bus, settings)
    camera = CameraService(event_bus, settings)
    gemini = GeminiService(event_bus, settings)
    
    print("백그라운드 서비스 시작됨")
    
    # Start services
    tasks = [
        weather.start(),
        pir.start(),
        actuator.start()
    ]
    
    try:
        loop.run_until_complete(asyncio.gather(*tasks))
    except Exception as e:
        print(f"백그라운드 서비스 에러: {e}")

def main():
    settings = Settings()
    event_bus = EventBus()
    
    # 백그라운드 서비스를 별도 스레드에서 시작
    background_thread = threading.Thread(target=start_background_services, daemon=True)
    background_thread.start()
    
    # GUI는 메인 스레드에서 실행
    gui = WeatherGUI(event_bus)
    gui.run()  # mainloop() 실행

if __name__ == "__main__":
    main()  # asyncio.run() 제거
