import asyncio
from config.settings import Settings
from events.event_bus import EventBus
from weather.weather_service import WeatherService
from sensors.pir_sensor import PIRSensor
from actuators.actuator_controller import ActuatorController
from camera.camera_service import CameraService
from ai.gemini_service import GeminiService
from gui.weather_gui import WeatherGUI
from utils.logger import setup_logger

async def main():
    settings = Settings()
    event_bus = EventBus()
    logger = setup_logger(settings.LOG_LEVEL)

    # Initialize services
    weather = WeatherService(event_bus, settings)
    pir = PIRSensor(event_bus, settings)
    actuator = ActuatorController(event_bus, settings)
    camera = CameraService(event_bus, settings)
    gemini = GeminiService(event_bus, settings)

    # Start services
    tasks = [
        weather.start(),
        pir.start(),
        actuator.start()
    ]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
