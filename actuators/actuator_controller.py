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
        self.serial = serial.Serial(self.settings.SERIAL_PORT, self.settings.SERIAL_BAUDRATE, timeout=self.settings.SERIAL_TIMEOUT)
        await asyncio.sleep(2)  # Stabilize connection

    async def handle_pop(self, event):
        ids = event.detail['needed']
        await self.send_command(f"POP:{','.join(map(str, ids))}")
        self.active.update(ids)

    async def handle_down(self, event):
        if self.active:
            await self.send_command(f"DOWN:{','.join(map(str, self.active))}")
            self.active.clear()
            await self.event_bus.emit(Event(EventType.CAMERA_CAPTURE, {}))

    async def send_command(self, command):
        self.serial.write(f"{command}\n".encode())
        await asyncio.sleep(self.settings.ACTUATOR_OPERATION_TIME)
