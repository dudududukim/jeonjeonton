import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import os
from dotenv import load_dotenv
import time # time 모듈 추가

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
        
        # API 호출 재시도 설정
        self.MAX_RETRIES = 3 # 최대 재시도 횟수
        self.INITIAL_DELAY = 1 # 초기 재시도 지연 시간 (초)
        self.TIMEOUT = 30 # API 호출 타임아웃 (초) - 기존 10초에서 30초로 증가

    def parse_xml(self, xml_text):
        """XML 파싱 유틸 함수"""
        return ET.fromstring(xml_text)
    
    def _make_api_request(self, url, params):
        """API 요청을 보내고 재시도 로직을 포함하는 내부 함수"""
        delay = self.INITIAL_DELAY
        for attempt in range(self.MAX_RETRIES):
            try:
                res = requests.get(url, params=params, timeout=self.TIMEOUT)
                res.raise_for_status() # HTTP 오류 (4xx, 5xx)가 발생하면 예외 발생
                return res.text
            except requests.exceptions.Timeout:
                print(f"API 호출 타임아웃 발생 (시도 {attempt + 1}/{self.MAX_RETRIES}). {delay}초 후 재시도...")
            except requests.exceptions.ConnectionError as e:
                print(f"API 연결 오류 발생 (시도 {attempt + 1}/{self.MAX_RETRIES}): {e}. {delay}초 후 재시도...")
            except requests.exceptions.RequestException as e:
                print(f"API 요청 오류 발생 (시도 {attempt + 1}/{self.MAX_RETRIES}): {e}. {delay}초 후 재시도...")
            
            time.sleep(delay) # 재시도 전 대기
            delay *= 2 # 지수 백오프: 다음 재시도 대기 시간을 두 배로 늘림
        print(f"최대 재시도 횟수 {self.MAX_RETRIES}번 초과. API 호출 실패.")
        return None # 모든 재시도 실패 시 None 반환

    def get_base_datetime_for_vilage_fcst(self, now):
        """
        단기예보 API 호출을 위한 base_date와 base_time을 계산합니다.
        가장 최근에 발표된 예보 시간을 기준으로 합니다.
        """
        base_times = ["0200", "0500", "0800", "1100", "1400", "1700", "2000", "2300"]
        
        # API 발표 시간을 고려하여 현재 시간에서 40분을 뺀 시간을 기준으로 계산
        target_time = now - timedelta(minutes=40) 
        
        base_date = target_time.strftime("%Y%m%d")
        base_time = None

        # 가장 최근의 발표 시간을 찾는다
        for bt in sorted(base_times, reverse=True): # 가장 늦은 시간부터 역순으로 탐색
            if int(target_time.strftime("%H%M")) >= int(bt):
                base_time = bt
                break
        
        # 만약 현재 시간 기준으로 오늘 발표된 예보가 없다면 (예: 새벽 1시 50분), 전날 마지막 예보 사용
        if base_time is None:
            base_date = (target_time - timedelta(days=1)).strftime("%Y%m%d")
            base_time = "2300" # 전날 마지막 발표 시간
            
        return base_date, base_time

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
        
        xml_text = self._make_api_request(url, params)
        if xml_text is None:
            print("초단기실황 API 호출 실패 후 기본값 반환.")
            return {'T1H': '?', 'PTY': '없음', 'RN1': '강수없음'} # 기본값 반환
        
        try:
            root = self.parse_xml(xml_text)
            result = {}
            for item in root.iter("item"):
                category = item.find("category").text
                value = item.find("obsrValue").text
                result[category] = value
            return result
        except Exception as e:
            print(f"초단기실황 XML 파싱 오류: {e}")
            return {'T1H': '?', 'PTY': '없음', 'RN1': '강수없음'} # 파싱 오류 시 기본값 반환
    
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
        
        xml_text = self._make_api_request(url, params)
        if xml_text is None:
            print("단기예보 API 호출 실패 후 기본값 반환.")
            return {'POP': '?', 'TMN': '?', 'TMX': '?', 'REH': '?', 'SKY': '1'} # 기본값 반환
        
        try:
            root = self.parse_xml(xml_text)
            fcst = {'POP': None, 'TMN': None, 'TMX': None, 'REH': None, 'SKY': None}
            for item in root.iter("item"):
                cat = item.find("category").text
                val = item.find("fcstValue").text
                if cat in fcst and fcst[cat] is None: # 이미 값이 있으면 덮어쓰지 않음
                    fcst[cat] = val
            # None 값들을 기본값으로 대체
            for key, value in fcst.items():
                if value is None:
                    if key in ['POP', 'REH']: fcst[key] = '?'
                    elif key in ['TMN', 'TMX']: fcst[key] = '?'
                    elif key == 'SKY': fcst[key] = '1' # 맑음
            return fcst
        except Exception as e:
            print(f"단기예보 XML 파싱 오류: {e}")
            return {'POP': '?', 'TMN': '?', 'TMX': '?', 'REH': '?', 'SKY': '1'} # 파싱 오류 시 기본값 반환
    
    def get_uv_index(self):
        """자외선 지수"""
        date_str = datetime.now().strftime("%Y%m%d%H")
        url = "http://apis.data.go.kr/1360000/LivingWthrIdxServiceV4/getUVIdxV4"
        params = {
            "serviceKey": self.KEY,
            "areaNo": 1168058000, # 서울 강남구 코드
            "time": date_str,
            "dataType": "XML"
        }
        
        xml_text = self._make_api_request(url, params)
        if xml_text is None:
            print("자외선 지수 API 호출 실패 후 기본값 0 반환.")
            return "0" # API 호출 실패 시 기본값 0 반환
        
        try:
            root = ET.fromstring(xml_text)
            item = root.find(".//item")
            if item is None:
                print("자외선 데이터 없음 (item 태그를 찾을 수 없음). 기본값 0 반환.")
                return "0" # 데이터 없으면 0 반환
            
            uv_value = item.find("h0") # 현재 시각의 자외선 지수
            # 값이 없거나 비어있으면 0 반환
            return uv_value.text if uv_value is not None and uv_value.text.strip() else "0"
        except Exception as e:
            print(f"자외선 지수 XML 파싱 오류: {e}. 기본값 0 반환.")
            return "0" # 파싱 오류 시 기본값 0 반환
    
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
        
        xml_text = self._make_api_request(url, params)
        if xml_text is None:
            print("미세먼지 API 호출 실패 후 기본값 '정보없음' 반환.")
            return "정보없음" # API 호출 실패 시 기본값 반환
        
        try:
            root = self.parse_xml(xml_text)
            pm10 = root.find(".//pm10Grade")
            pm10_val = pm10.text if pm10 is not None else "정보없음"
            # 미세먼지 등급을 텍스트로 매핑, 없으면 '정보없음'
            pm10_txt = {"1": "좋음", "2": "보통", "3": "나쁨", "4": "매우 나쁨"}.get(pm10_val, "정보없음")
            return pm10_txt
        except Exception as e:
            print(f"미세먼지 XML 파싱 오류: {e}. 기본값 '정보없음' 반환.")
            return "정보없음" # 파싱 오류 시 기본값 반환
    
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
        
        # 초단기실황 API를 위한 시간 설정 (현재 시간 기준 20분 전)
        date_str_nowcast = now.strftime("%Y%m%d")
        time_str_nowcast = (now - timedelta(minutes=20)).strftime("%H00")
        
        print(f"초단기실황 요청에 사용된 base_time: {time_str_nowcast}")
        
        # 단기예보 API를 위한 base_date와 base_time 계산
        vilage_base_date, vilage_base_time = self.get_base_datetime_for_vilage_fcst(now)
        print(f"단기예보 요청에 사용된 base_date: {vilage_base_date}, base_time: {vilage_base_time}")

        # API 호출
        nowcast = self.get_ultra_nowcast(self.NX, self.NY, date_str_nowcast, time_str_nowcast)
        vilage = self.get_vilage_fcst(self.NX, self.NY, vilage_base_date, vilage_base_time)
        uv = self.get_uv_index()
        pm10 = self.get_air_quality()
        
        # SKY 코드 매핑 (단기예보)
        sky_code = vilage.get('SKY', '1') # 기본값 '1' (맑음)
        sky_txt = {"1": "맑음", "3": "구름많음", "4": "흐림"}.get(sky_code, "맑음")
        
        # GUI 포맷에 맞게 데이터 정리
        weather_data = {
            'current_temp': f"{nowcast.get('T1H', '?')}°C",
            'precipitation': f"{vilage.get('POP', '?')}%", # 강수확률
            'max_temp': f"{vilage.get('TMX', '?')}°C", # 최고 기온
            'min_temp': f"{vilage.get('TMN', '?')}°C", # 최저 기온
            'uv_index': str(uv), # uv_index는 이제 항상 숫자로 반환될 것임
            'dust': pm10,
            'humidity': f"{vilage.get('REH', '?')}%", # 습도
            'sky_condition': sky_txt,
            'rain_amount': f"{nowcast.get('RN1', '0')}mm"
        }
        
        # 콘솔 출력
        print(f"""{now.strftime("%Y년 %m월 %d일 %H시 %M분")}
위치 ({self.NX}, {self.NY})
현재 [기온 {nowcast.get('T1H','?')}℃, 강수형태 {nowcast.get('PTY','없음')}, 1시간 강수량 {nowcast.get('RN1','강수없음')}mm
자외선 지수 {uv}, 미세먼지 {pm10} ]
오늘 [{sky_txt}, 강수확률{vilage.get('POP','강수확률없음')}, 습도 {vilage.get('REH','?')}%, 최저 기온 {vilage.get('TMN','?')}℃ / 최고 기온 {vilage.get('TMX','?')}℃]""")
        
        # 캐시 업데이트
        self.cached_data = weather_data
        self.last_update_time = now
        
        return weather_data
