import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw
import threading
from datetime import datetime
from events.event_types import Event, EventType
from weather.weather_api import WeatherAPI

class WeatherGUI(tk.Tk):
    def __init__(self, event_bus):
        super().__init__()
        self.title("라즈베리파이 날씨 정보")
        self.geometry("1200x650")
        self.configure(bg='#f5f5f5')
        
        # 이벤트 버스 연결
        self.event_bus = event_bus
        self.event_bus.subscribe(EventType.WEATHER_UPDATE, self.on_weather_update)
        
        # 날씨 API 인스턴스
        self.weather_api = WeatherAPI()
        
        # 업데이트 상태 플래그
        self.is_updating = False
        
        # 날씨 데이터 초기값
        self.weather_data = {
            'current_temp': '--°C',
            'precipitation': '--%',
            'max_temp': '--°C',
            'min_temp': '--°C',
            'uv_index': '--',
            'dust': '--',
            'humidity': '--%'
        }
        
        self.setup_ui()
        self.update_weather_data()
        
        # 10분마다 데이터 자동 업데이트
        self.auto_update()

    def setup_ui(self):
        """UI 구성"""
        # 메인 컨테이너
        main_frame = tk.Frame(self, bg='#f5f5f5')
        main_frame.pack(fill='both', expand=True, padx=30, pady=30)
        
        # 왼쪽 컨테이너 (정사각형 + 버튼)
        left_container = tk.Frame(main_frame, bg='#f5f5f5')
        left_container.pack(side='left', padx=(0, 30))
        
        # 왼쪽 프레임 (메인 정보 - 정사각형)
        self.left_frame = tk.Frame(left_container, bg='white', width=400, height=400, relief='solid', bd=2)
        self.left_frame.pack()
        self.left_frame.pack_propagate(False)
        
        # 업데이트 버튼 (정사각형 밑에)
        self.update_button = tk.Button(left_container,
                                     text="🔄 새로고침",
                                     font=('맑은 고딕', 12),
                                     bg='#f5f5f5',
                                     fg='#6c757d',
                                     relief='flat',
                                     bd=0,
                                     activebackground='#e9ecef',
                                     activeforeground='#495057',
                                     cursor='hand2',
                                     command=self.manual_update)
        self.update_button.pack(pady=(15, 0))
        
        # 오른쪽 프레임 (세부 정보 카드들 - 3x2 격자)
        self.right_frame = tk.Frame(main_frame, bg='#f5f5f5')
        self.right_frame.pack(side='right', fill='both', expand=True)
        
        # UI 구성요소 생성
        self.setup_main_display()
        self.setup_detail_cards()
        
        # 상태바
        self.status_bar = tk.Label(self, text="데이터 로딩 중...",
                                 font=('맑은 고딕', 9), bg='#e9ecef', fg='#6c757d')
        self.status_bar.pack(side='bottom', fill='x')

    def create_icon(self, icon_type, size=(64, 64)):
        """아이콘 생성"""
        icon = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(icon)
        
        if icon_type == 'temp':
            # 온도계
            bulb_size = min(size[0]//4, size[1]//4)
            stem_height = int(size[1] * 0.5)
            stem_width = max(2, size[0]//15)
            
            # 하단 bulb
            draw.ellipse((size[0]//2 - bulb_size, size[1] - 2*bulb_size,
                         size[0]//2 + bulb_size, size[1]), fill='#ff6b6b')
            
            # 줄기
            draw.rectangle((size[0]//2 - stem_width, size[1] - stem_height - bulb_size,
                           size[0]//2 + stem_width, size[1] - bulb_size), fill='#ff6b6b')
            
            # 상단 원
            top_bulb = max(3, size[0]//15)
            draw.ellipse((size[0]//2 - top_bulb, size[1] - stem_height - bulb_size - top_bulb*2,
                         size[0]//2 + top_bulb, size[1] - stem_height - bulb_size + top_bulb*2), fill='#ff6b6b')
        
        elif icon_type == 'rain':
            # 비
            draw.ellipse((size[0]*0.2, size[1]*0.1, size[0]*0.8, size[1]*0.5), fill='#74c0fc')
            # 빗방울
            for i in range(3):
                x = size[0]*0.3 + i * size[0]*0.2
                draw.line([(x, size[1]*0.6), (x-size[0]*0.05, size[1]*0.85)], fill='#339af0', width=max(1, size[0]//20))
        
        elif icon_type == 'uv':
            # 태양
            center = (size[0]//2, size[1]//2)
            sun_radius = min(size[0], size[1]) // 6
            draw.ellipse((center[0]-sun_radius, center[1]-sun_radius,
                         center[0]+sun_radius, center[1]+sun_radius), fill='#ffd43b')
            
            # 햇살
            import math
            for i in range(8):
                angle = i * 45
                ray_length = min(size[0], size[1]) // 4
                x1 = center[0] + ray_length * math.cos(math.radians(angle))
                y1 = center[1] + ray_length * math.sin(math.radians(angle))
                draw.line([center, (x1, y1)], fill='#ffd43b', width=max(1, size[0]//25))
        
        elif icon_type == 'dust':
            # 먼지
            dust_size = max(4, size[0]//10)
            for i in range(6):
                x = size[0]*0.25 + (i % 3) * size[0]*0.25
                y = size[1]*0.3 + (i // 3) * size[1]*0.25
                draw.ellipse((x, y, x+dust_size, y+dust_size), fill='#868e96')
        
        elif icon_type == 'humidity':
            # 물방울
            drop_width = min(size[0], size[1]) // 3
            drop_height = min(size[0], size[1]) // 2
            
            # 물방울 몸통
            draw.ellipse((size[0]//2 - drop_width//2, size[1]//2 + drop_height//4,
                         size[0]//2 + drop_width//2, size[1]//2 + drop_height), fill='#339af0')
            
            # 물방울 꼭지점
            draw.polygon([(size[0]//2, size[1]//2 - drop_height//4),
                         (size[0]//2 - drop_width//2, size[1]//2 + drop_height//4),
                         (size[0]//2 + drop_width//2, size[1]//2 + drop_height//4)], fill='#339af0')
        
        return ImageTk.PhotoImage(icon)

    def setup_main_display(self):
        """메인 디스플레이 (현재 온도) 설정"""
        # 제목
        self.main_title = tk.Label(self.left_frame, text="현재 온도",
                                 font=('맑은 고딕', 24, 'bold'),
                                 bg='white', fg='#495057')
        self.main_title.pack(pady=(50, 20))
        
        # 온도 아이콘
        self.temp_icon = self.create_icon('temp', (120, 120))
        self.icon_label = tk.Label(self.left_frame, image=self.temp_icon, bg='white')
        self.icon_label.pack(pady=20)
        
        # 온도 값
        self.temp_value = tk.Label(self.left_frame, text=self.weather_data['current_temp'],
                                 font=('맑은 고딕', 48, 'bold'), bg='white', fg='#212529')
        self.temp_value.pack(pady=(20, 50))

    def setup_detail_cards(self):
        """세부 정보 카드들 설정 - 3x2 격자 배치"""
        self.cards_data = [
            ('강수확률', 'precipitation', 'rain'),
            ('최고 기온', 'max_temp', 'temp'),
            ('최저 기온', 'min_temp', 'temp'),
            ('자외선 지수', 'uv_index', 'uv'),
            ('미세먼지', 'dust', 'dust'),
            ('습도', 'humidity', 'humidity')
        ]
        
        self.card_labels = {}
        
        # 3x2 격자 배치
        for i, (title, data_key, icon_type) in enumerate(self.cards_data):
            row = i // 3  # 행 (0 또는 1)
            col = i % 3   # 열 (0, 1, 또는 2)
            
            # 카드 프레임
            card = tk.Frame(self.right_frame, bg='white', relief='solid', bd=2,
                           width=240, height=160)
            card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            card.pack_propagate(False)
            
            # 아이콘
            icon = self.create_icon(icon_type, (60, 60))
            icon_label = tk.Label(card, image=icon, bg='white')
            icon_label.image = icon
            icon_label.pack(pady=(15, 5))
            
            # 제목
            title_label = tk.Label(card, text=title, font=('맑은 고딕', 14),
                                 bg='white', fg='#6c757d')
            title_label.pack(pady=(0, 5))
            
            # 값
            value_label = tk.Label(card, text=self.weather_data[data_key],
                                 font=('맑은 고딕', 18, 'bold'),
                                 bg='white', fg='#212529')
            value_label.pack(pady=(0, 15))
            
            # 라벨 저장 (업데이트용)
            self.card_labels[data_key] = value_label
        
        # 격자 열 크기 조정
        for i in range(3):
            self.right_frame.grid_columnconfigure(i, weight=1)
        for i in range(2):
            self.right_frame.grid_rowconfigure(i, weight=1)

    def on_weather_update(self, event):
        """이벤트 버스에서 날씨 업데이트 이벤트 수신"""
        print("이벤트 버스에서 날씨 업데이트 요청 수신")
        self.update_weather_data()

    def manual_update(self):
        """수동 업데이트 버튼 클릭 시 호출"""
        if self.is_updating:
            return
        
        # 버튼 상태 변경
        self.update_button.config(text="⏳ 업데이트 중...", state='disabled')
        self.status_bar.config(text="수동 업데이트 중...")
        
        # 강제 새로고침으로 업데이트 실행
        def fetch_data():
            try:
                self.is_updating = True
                new_data = self.weather_api.get_all_weather_data(force_refresh=True)
                self.after(0, lambda: self.update_ui(new_data))
            except Exception as e:
                print(f"수동 업데이트 오류: {e}")
                self.after(0, lambda: self.update_error(str(e)))
            finally:
                self.is_updating = False
        
        thread = threading.Thread(target=fetch_data)
        thread.daemon = True
        thread.start()

    def update_weather_data(self):
        """날씨 데이터 업데이트"""
        def fetch_data():
            try:
                self.is_updating = True
                self.status_bar.config(text="날씨 데이터 업데이트 중...")
                new_data = self.weather_api.get_all_weather_data()
                # UI 업데이트 (메인 스레드에서 실행)
                self.after(0, lambda: self.update_ui(new_data))
            except Exception as e:
                print(f"날씨 데이터 업데이트 오류: {e}")
                self.after(0, lambda: self.update_error(str(e)))
            finally:
                self.is_updating = False
        
        # 백그라운드에서 API 호출
        thread = threading.Thread(target=fetch_data)
        thread.daemon = True
        thread.start()

    def update_ui(self, new_data):
        """UI 업데이트"""
        self.weather_data.update(new_data)
        
        # 메인 온도 업데이트
        self.temp_value.config(text=self.weather_data['current_temp'])
        
        # 카드 데이터 업데이트
        for data_key, label in self.card_labels.items():
            label.config(text=self.weather_data[data_key])
        
        # 상태바 및 버튼 복원
        current_time = datetime.now().strftime("%H:%M:%S")
        self.status_bar.config(text=f"마지막 업데이트: {current_time}")
        self.update_button.config(text="🔄 새로고침", state='normal')

    def update_error(self, error_msg):
        """업데이트 오류 처리"""
        self.status_bar.config(text=f"업데이트 오류: {error_msg}")
        self.update_button.config(text="🔄 새로고침", state='normal')

    def auto_update(self):
        """10분마다 자동 업데이트"""
        self.update_weather_data()
        # 600000ms = 10분
        self.after(600000, self.auto_update)

    def run(self):
        """GUI 실행"""
        self.mainloop()
