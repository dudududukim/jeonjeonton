import asyncio
import requests
from xml.etree import ElementTree as ET
from datetime import datetime
from config.settings import Settings

class WeatherService:
    def __init__(self, event_bus, settings: Settings):
        self.event_bus = event_bus
        self.settings = settings
        self.last_data = {}

        self.event_bus.subscribe(EventType.WEATHER_UPDATE, self.handle_update)

    async def handle_update(self, event):
        data = await self.fetch_data()
        self.last_data = data
        await self.event_bus.emit(Event(EventType.ACTUATOR_POP, {'needed': self.determine_needed(data)}))

    async def fetch_data(self):
        # Simplified fetch from APIs (based on attachment [2])
        now = datetime.now()
        base_date = now.strftime("%Y%m%d")
        base_time = (now.hour - 1) * 100  # Example

        # Fetch current temp, precipitation, etc. (implement API calls here)
        # Placeholder
        return {
            'current_temp': '25',
            'precipitation': '20',
            'uv_index': '5',
            'dust': '보통',
            'humidity': '50'
        }

    def determine_needed(self, data):
        needed = []
        if int(data['precipitation']) >= self.settings.THRESHOLDS['precipitation']:
            needed.append(1)  # Umbrella
        # Add other conditions
        return needed

    async def start(self):
        while True:
            await asyncio.sleep(self.settings.WEATHER_UPDATE_INTERVAL)
            await self.handle_update(Event(EventType.WEATHER_UPDATE, {}))
