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
    """有源蜂鸣器驱动（GPIO 12，单例）

    注意：有源蜂鸣器只能在固定频率发声，freq 参数仅保留接口兼容性，
    实际不影响音调。如需变频音效需换用无源蜂鸣器 + PWM 驱动。
    """

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

    def beep(self, duration: float = 0.2):
        """响一声（有源蜂鸣器，固定频率）"""
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
        """提醒音：3 短声"""
        for _ in range(3):
            self.beep(0.15)
            time.sleep(0.1)

    def welcome_sound(self):
        """欢迎音：1 长声"""
        self.beep(0.3)

    def alarm_sound(self):
        """警报音：5 急促短声"""
        for _ in range(5):
            self.beep(0.1)
            time.sleep(0.05)

    def level_up_sound(self):
        """升级音：3 声递进（有源蜂鸣器无法变频，用间隔区分）"""
        for duration in [0.1, 0.15, 0.2]:
            self.beep(duration)
            time.sleep(0.05)

    def beep_async(self, duration: float = 0.2):
        """异步响铃（后台线程，不阻塞调用者）"""
        threading.Thread(target=self.beep, args=(duration,), daemon=True).start()
