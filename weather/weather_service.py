import asyncio
import requests
from xml.etree import ElementTree as ET
from datetime import datetime
from config.settings import Settings
from events.event_types import Event, EventType
from weather.weather_api import WeatherAPI

class WeatherService:
    def __init__(self, event_bus, settings: Settings):
        self.event_bus = event_bus
        self.settings = settings
        self.weather_api = WeatherAPI()
        self.last_data = {}
        self.event_bus.subscribe(EventType.WEATHER_UPDATE, self.handle_update)

    async def handle_update(self, event):
        print("날씨 서비스 업데이트 시작")
        data = await self.fetch_data()
        self.last_data = data
        needed = self.determine_needed(data)
        if needed:
            await self.event_bus.emit(Event(EventType.ACTUATOR_POP, {'needed': needed}))

    async def fetch_data(self):
        """실제 API에서 날씨 데이터 가져오기"""
        try:
            # weather_api.py의 API 사용
            raw_data = self.weather_api.get_all_weather_data()
            
            # 액추에이터 로직을 위해 숫자 값 추출
            data = {
                'current_temp': raw_data['current_temp'].replace('°C', ''),
                'precipitation': raw_data['precipitation'].replace('%', ''),
                'uv_index': raw_data['uv_index'],
                'dust': raw_data['dust'],
                'humidity': raw_data['humidity'].replace('%', '')
            }
            
            print(f"날씨 데이터 업데이트: 온도 {data['current_temp']}°C, 강수확률 {data['precipitation']}%")
            return data
            
        except Exception as e:
            print(f"날씨 API 호출 오류: {e}")
            # 기본값 반환
            return {
                'current_temp': '25',
                'precipitation': '20',
                'uv_index': '5',
                'dust': '보통',
                'humidity': '50'
            }

    def determine_needed(self, data):
        """필요한 액추에이터 결정"""
        needed = []
        
        try:
            # 강수확률 체크
            if int(data['precipitation']) >= self.settings.THRESHOLDS['precipitation']:
                needed.append(1)  # 우산
                print(f"우산 필요 - 강수확률: {data['precipitation']}%")
            
            # 자외선 지수 체크
            if data['uv_index'].isdigit():
                uv_val = int(data['uv_index'])
                if uv_val >= self.settings.THRESHOLDS['uv_sunscreen']:
                    needed.append(2)  # 선크림
                    print(f"선크림 필요 - 자외선지수: {uv_val}")
                if uv_val >= self.settings.THRESHOLDS['uv_sunglasses']:
                    needed.append(3)  # 선글라스
                    print(f"선글라스 필요 - 자외선지수: {uv_val}")
            
            # 미세먼지 체크
            if data['dust'] in self.settings.THRESHOLDS['dust_bad']:
                needed.append(4)  # 마스크
                print(f"마스크 필요 - 미세먼지: {data['dust']}")
            
            # 온도 체크
            if data['current_temp'].isdigit():
                temp_val = int(data['current_temp'])
                if temp_val <= self.settings.THRESHOLDS['cold_temp']:
                    needed.append(5)  # 외투
                    print(f"외투 필요 - 온도: {temp_val}°C")
            
        except Exception as e:
            print(f"액추에이터 결정 오류: {e}")
        
        return needed

    async def start(self):
        print("날씨 서비스 시작됨")
        while True:
            await asyncio.sleep(self.settings.WEATHER_UPDATE_INTERVAL)
            print("날씨 업데이트 중...")
            await self.handle_update(Event(EventType.WEATHER_UPDATE, {}))
