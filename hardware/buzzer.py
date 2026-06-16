"""
Hardware — 蜂鸣器驱动
有源蜂鸣器：高电平响，低电平停
单例模式：全局只初始化一次 GPIO
"""
import logging
import time
import threading

logger = logging.getLogger("SmartHome.hardware")

_instance = None
_lock = threading.Lock()


def get_buzzer() -> "Buzzer":
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = Buzzer()
    return _instance


class Buzzer:
    """有源蜂鸣器驱动（GPIO 12，单例）"""

    def __init__(self, pin: int = 12):
        self.pin = pin
        self._initialized = False
        self._hw_lock = threading.Lock()

    def _init_gpio(self) -> bool:
        if self._initialized:
            return True
        with self._hw_lock:
            if self._initialized:
                return True
            try:
                import RPi.GPIO as GPIO
                GPIO.setwarnings(False)
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.pin, GPIO.OUT)
                GPIO.output(self.pin, GPIO.LOW)
                self._initialized = True
                logger.info("Buzzer initialized: GPIO %d", self.pin)
                return True
            except ImportError:
                logger.debug("RPi.GPIO not available")
                return False
            except Exception as e:
                logger.error("Buzzer init failed: %s", e)
                return False

    def beep(self, freq: int = 1000, duration: float = 0.2):
        if not self._init_gpio():
            return
        try:
            import RPi.GPIO as GPIO
            GPIO.output(self.pin, GPIO.HIGH)
            time.sleep(duration)
            GPIO.output(self.pin, GPIO.LOW)
        except Exception as e:
            logger.error("Buzzer beep failed: %s", e)

    def reminder_sound(self):
        for _ in range(3):
            self.beep(1000, 0.15)
            time.sleep(0.1)

    def welcome_sound(self):
        self.beep(800, 0.3)

    def alarm_sound(self):
        for _ in range(5):
            self.beep(300, 0.1)
            time.sleep(0.05)

    def level_up_sound(self):
        for freq in [523, 659, 784]:
            self.beep(freq, 0.15)
            time.sleep(0.05)

    def beep_async(self, freq: int = 1000, duration: float = 0.2):
        threading.Thread(target=self.beep, args=(freq, duration), daemon=True).start()
