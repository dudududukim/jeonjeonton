import time
import datetime
try:
    import RPi.GPIO as GPIO
except ImportError:
    print("RPi.GPIO를 찾을 수 없습니다. 라즈베리파이에서 실행해주세요.")
    exit()

PIR_PIN = 18  # PIR 센서 핀 번호

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)

print("=== PIR SENSOR RAW DATA OUTPUT ===")
print(f"PIN: {PIR_PIN}")
print(f"START_TIME: {datetime.datetime.now()}")
print("FORMAT: TIMESTAMP,PIN_STATE")
print("=" * 50)
time.sleep(2)

try:
    while True:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        state = GPIO.input(PIR_PIN)
        print(f"{timestamp},{state}")
        time.sleep(0.2)
except KeyboardInterrupt:
    print("\n=== TEST TERMINATED ===")
finally:
    GPIO.cleanup()
    print(f"GPIO_CLEANUP: {datetime.datetime.now()}")
