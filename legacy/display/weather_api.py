import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class WeatherAPI:
    def __init__(self):
        # .env 파일에서 API 키 로드
        self.KEY = os.getenv('WEATHER_KEY')
        
        # API 키가 없으면 에러 발생
        if not self.KEY:
            raise ValueError("WEATHER_KEY가 .env 파일에 설정되지 않았습니다.")
        
        # 격자 좌표 (서울 강남구 기준)
        self.NX, self.NY = 61, 125
        # 캐시 관련
        self.last_update_time = None
        self.cached_data = None
    
    def parse_xml(self, xml_text):
        """XML 파싱 유틸 함수"""
        return ET.fromstring(xml_text)
    
    def get_ultra_nowcast(self, nx, ny, base_date, base_time):
        """현재 기온, 강수형태, 1시간 강수량 (초단기실황)"""
        url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
        params = {
            "serviceKey": self.KEY,
            "pageNo": "1",
            "numOfRows": "100",
            "dataType": "XML",
            "base_date": base_date,
            "base_time": base_time,
            "nx": nx,
            "ny": ny,
        }
        
        try:
            res = requests.get(url, params=params, timeout=10)
            root = self.parse_xml(res.text)
            result = {}
            for item in root.iter("item"):
                category = item.find("category").text
                value = item.find("obsrValue").text
                result[category] = value
            return result
        except Exception as e:
            print(f"초단기실황 API 오류: {e}")
            return {}
    
    def get_vilage_fcst(self, nx, ny, base_date, base_time):
        """강수확률, 금일 최저/최고기온, 습도 (단기예보)"""
        url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
        params = {
            "serviceKey": self.KEY,
            "pageNo": "1",
            "numOfRows": "500",
            "dataType": "XML",
            "base_date": base_date,
            "base_time": base_time,
            "nx": nx,
            "ny": ny,
        }
        
        try:
            res = requests.get(url, params=params, timeout=10)
            root = self.parse_xml(res.text)
            fcst = {'POP': None, 'TMN': None, 'TMX': None, 'REH': None, 'SKY': None}
            for item in root.iter("item"):
                cat = item.find("category").text
                val = item.find("fcstValue").text
                if cat in fcst and fcst[cat] is None:
                    fcst[cat] = val
            return fcst
        except Exception as e:
            print(f"단기예보 API 오류: {e}")
            return {'POP': None, 'TMN': None, 'TMX': None, 'REH': None, 'SKY': None}
    
    def get_uv_index(self):
        """자외선 지수"""
        date_str = datetime.now().strftime("%Y%m%d%H")
        url = "http://apis.data.go.kr/1360000/LivingWthrIdxServiceV4/getUVIdxV4"
        params = {
            "serviceKey": self.KEY,
            "areaNo": 1168058000,
            "time": date_str,
            "dataType": "XML"
        }
        
        try:
            res = requests.get(url, params=params, timeout=10)
            if res.status_code != 200:
                return f"API 호출 실패: {res.status_code}"
            
            root = ET.fromstring(res.text)
            item = root.find(".//item")
            if item is None:
                return "자외선 데이터 없음"
            
            uv_value = item.find("h0")
            return uv_value.text if uv_value is not None and uv_value.text.strip() else "정보없음"
        except Exception as e:
            print(f"자외선 지수 API 오류: {e}")
            return "정보없음"
    
    def get_air_quality(self, station="강남구"):
        """미세먼지 정보 (한국환경공단, 에어코리아)"""
        url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMsrstnAcctoRltmMesureDnsty"
        params = {
            "serviceKey": self.KEY,
            "returnType": "xml",
            "numOfRows": "1",
            "pageNo": "1",
            "stationName": station,
            "dataTerm": "DAILY",
            "ver": "1.0"
        }
        
        try:
            res = requests.get(url, params=params, timeout=10)
            root = self.parse_xml(res.text)
            pm10 = root.find(".//pm10Grade")
            pm10_val = pm10.text if pm10 is not None else "정보없음"
            pm10_txt = {"1": "좋음", "2": "보통", "3": "나쁨", "4": "매우 나쁨"}.get(pm10_val, "정보없음")
            return pm10_txt
        except Exception as e:
            print(f"미세먼지 API 오류: {e}")
            return "정보없음"
    
    def get_all_weather_data(self, force_refresh=False):
        """모든 날씨 데이터를 통합하여 반환"""
        now = datetime.now()
        
        # 캐시 확인 (5분 이내 데이터가 있으면 재사용, 강제 새로고침이 아닌 경우)
        if (not force_refresh and 
            self.last_update_time and 
            self.cached_data and 
            (now - self.last_update_time).total_seconds() < 300):  # 5분
            print("캐시된 데이터 사용")
            return self.cached_data
        
        print("새로운 API 호출 실행")
        
        # 시간 설정 (원본 코드와 동일)
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M")
        base_time = (now - timedelta(minutes=20)).strftime("%H00")
        
        print(f"요청에 사용된 base_time: {base_time}")
        
        # API 호출 (원본 코드와 동일한 방식)
        nowcast = self.get_ultra_nowcast(self.NX, self.NY, date_str, base_time)
        vilage = self.get_vilage_fcst(self.NX, self.NY, date_str, "0800")  # 단기예보 발표시간
        uv = self.get_uv_index()
        pm10 = self.get_air_quality()
        
        # SKY 코드 매핑 (단기예보)
        sky_code = vilage.get('SKY', '1')
        sky_txt = {"1": "맑음", "3": "구름많음", "4": "흐림"}.get(sky_code, "맑음")
        
        # GUI 포맷에 맞게 데이터 정리
        weather_data = {
            'current_temp': f"{nowcast.get('T1H', '?')}°C",
            'precipitation': f"{vilage.get('POP', '?')}%",
            'max_temp': f"{vilage.get('TMX', '?')}°C",
            'min_temp': f"{vilage.get('TMN', '?')}°C",
            'uv_index': str(uv),
            'dust': pm10,
            'humidity': f"{vilage.get('REH', '?')}%",
            'sky_condition': sky_txt,
            'rain_amount': f"{nowcast.get('RN1', '0')}mm"
        }
        
        # 콘솔 출력 (원본 코드와 동일)
        print(f"""{date_str[:4]}년 {date_str[4:6]}월 {date_str[6:]}일 {time_str[:2]}시 {time_str[2:]}분
위치 ({self.NX}, {self.NY})
현재 [기온 {nowcast.get('T1H','?')}℃, 강수형태 {nowcast.get('PTY','없음')}, 1시간 강수량 {nowcast.get('RN1','강수없음')}mm
자외선 지수 {uv}, 미세먼지 {pm10}]
오늘 [{sky_txt}, 습도 {vilage.get('REH','?')}%, 최저 기온 {vilage.get('TMN','?')}℃ / 최고 기온 {vilage.get('TMX','?')}℃]""")
        
        # 캐시 업데이트
        self.cached_data = weather_data
        self.last_update_time = now
        
        return weather_data
