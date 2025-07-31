import asyncio
try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

from config.settings import Settings
from events.event_types import Event, EventType

class PIRSensor:
    def __init__(self, event_bus, settings: Settings):
        self.event_bus = event_bus
        self.settings = settings
        self.present = False
        if GPIO:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(settings.PIR_PIN, GPIO.IN)

    async def start(self):
        while True:
            state = GPIO.input(self.settings.PIR_PIN) if GPIO else False  # Simulate if no GPIO
            if state and not self.present:
                self.present = True
                await self.event_bus.emit(Event(EventType.HUMAN_COME, {}))
            elif not state and self.present:
                self.present = False
                await self.event_bus.emit(Event(EventType.HUMAN_OUT, {}))
            await asyncio.sleep(0.1)
