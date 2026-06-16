"""
Hardware — RGB LED 驱动
PWM 调色，表达情绪
共阳极：GPIO LOW = 亮，GPIO HIGH = 灭
单例模式：全局只初始化一次 GPIO
"""
import logging
import time
import threading

logger = logging.getLogger("SmartHome.hardware")

MOOD_COLORS = {
    "happy":   (255, 200, 50),
    "curious": (0, 180, 255),
    "sleepy":  (80, 50, 120),
    "alert":   (255, 50, 50),
    "chatty":  (50, 255, 100),
    "calm":    (110, 140, 255),
    "lonely":  (99, 102, 241),
}

ALERT_COLORS = {
    "temp_high":  (255, 0, 0),
    "temp_low":   (0, 100, 255),
    "humi_high":  (0, 200, 255),
    "humi_low":   (255, 150, 0),
    "gas_alert":  (255, 0, 0),
}

_instance = None
_lock = threading.Lock()


def get_led() -> "RGBLed":
    """获取 LED 单例"""
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = RGBLed()
    return _instance


class RGBLed:
    """RGB LED 驱动（共阳极，GPIO PWM，单例）"""

    def __init__(self, pin_r: int = 27, pin_g: int = 22, pin_b: int = 5):
        self.pin_r = pin_r
        self.pin_g = pin_g
        self.pin_b = pin_b
        self._pwm: dict = {}
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
                for pin in [self.pin_r, self.pin_g, self.pin_b]:
                    GPIO.setup(pin, GPIO.OUT)
                    self._pwm[pin] = GPIO.PWM(pin, 1000)
                    self._pwm[pin].start(0)
                self._initialized = True
                logger.info("RGB LED initialized: R=%d G=%d B=%d", self.pin_r, self.pin_g, self.pin_b)
                return True
            except ImportError:
                logger.debug("RPi.GPIO not available")
                return False
            except Exception as e:
                logger.error("LED GPIO init failed: %s", e)
                return False

    def set_color(self, r: int, g: int, b: int):
        if not self._init_gpio():
            return
        with self._hw_lock:
            try:
                self._pwm[self.pin_r].ChangeDutyCycle((255 - r) / 255 * 100)
                self._pwm[self.pin_g].ChangeDutyCycle((255 - g) / 255 * 100)
                self._pwm[self.pin_b].ChangeDutyCycle((255 - b) / 255 * 100)
            except Exception as e:
                logger.error("LED set_color failed: %s", e)

    def set_mood(self, mood: str):
        color = MOOD_COLORS.get(mood, (110, 140, 255))
        self.set_color(*color)
        logger.info("LED mood: %s → RGB%s", mood, color)

    def set_alert(self, alert_type: str):
        color = ALERT_COLORS.get(alert_type, (255, 0, 0))
        self.set_color(*color)

    def blink(self, r: int, g: int, b: int, times: int = 3, interval: float = 0.3):
        def _blink():
            for _ in range(times):
                self.set_color(r, g, b)
                time.sleep(interval)
                self.set_color(0, 0, 0)
                time.sleep(interval)
        threading.Thread(target=_blink, daemon=True).start()

    def off(self):
        self.set_color(0, 0, 0)
