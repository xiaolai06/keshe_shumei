"""
Perception — 传感器读取
DS18B20 温度 + DHT22 温湿度 + 光敏电阻(数字输出)
"""
import logging
import time

logger = logging.getLogger("SmartHome.sensors")

try:
    import board
    import adafruit_dht
    import RPi.GPIO as GPIO
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False
    logger.info("Hardware libraries not available, using mock sensor data")

import config


class SensorReader:
    """传感器统一读取接口"""

    def __init__(self):
        self._dht = None
        self._dht_initialized = False
        self._gpio_initialized = False

    def _ensure_gpio(self):
        """一次性 GPIO 全局初始化"""
        if self._gpio_initialized or not HARDWARE_AVAILABLE:
            return
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            self._gpio_initialized = True
        except Exception as e:
            logger.error("GPIO init failed: %s", e)

    def _init_dht(self):
        """延迟初始化 DHT22 传感器"""
        if self._dht_initialized:
            return self._dht is not None
        if not HARDWARE_AVAILABLE:
            return False
        try:
            self._dht = adafruit_dht.DHT22(board.D17)
            self._dht_initialized = True
            logger.info("DHT22 initialized on GPIO %d", config.PIN_DHT22)
            return True
        except Exception as e:
            logger.error("DHT22 init failed: %s", e)
            return False

    def _read_ds18b20(self) -> float | None:
        """从 DS18B20 读取温度（1-Wire 协议）"""
        try:
            import glob
            base_dir = "/sys/bus/w1/devices/"
            devices = glob.glob(base_dir + "28-*")
            if not devices:
                return None
            device_file = devices[0] + "/temperature"
            with open(device_file) as f:
                return float(f.read().strip()) / 1000.0
        except Exception as e:
            logger.debug("DS18B20 read failed: %s", e)
            return None

    def _read_dht22(self) -> tuple[float | None, float | None]:
        """从 DHT22 读取温度和湿度"""
        if not self._init_dht():
            return None, None
        try:
            temp = self._dht.temperature
            humidity = self._dht.humidity
            return temp, humidity
        except RuntimeError as e:
            logger.debug("DHT22 read failed (transient): %s", e)
            return None, None
        except Exception as e:
            logger.error("DHT22 read error: %s", e)
            return None, None

    def _read_light_digital(self) -> bool | None:
        """
        读取光敏传感器数字输出。
        模块带 LM393 比较器，输出高/低电平表示亮/暗。
        """
        if not HARDWARE_AVAILABLE:
            return None
        try:
            self._ensure_gpio()
            GPIO.setup(config.PIN_LIGHT, GPIO.IN)
            value = GPIO.input(config.PIN_LIGHT)
            # 光敏模块：高电平通常表示光照充足（具体取决于模块电位器调节）
            return bool(value)
        except Exception as e:
            logger.debug("Light sensor read failed: %s", e)
            return None

    def read_all(self) -> dict:
        """读取所有传感器数据"""
        if not HARDWARE_AVAILABLE:
            return self._read_mock()
        return self._read_hardware()

    def _read_hardware(self) -> dict:
        """从真实硬件读取传感器数据"""
        result = {
            "temperature": None,
            "humidity": None,
            "light_level": None,
            "fire_detected": False,
        }

        # DS18B20 温度
        ds18b20_temp = self._read_ds18b20()
        if ds18b20_temp is not None:
            result["temperature"] = ds18b20_temp

        # DHT22 温湿度
        dht_temp, dht_humidity = self._read_dht22()
        if dht_temp is not None:
            # 如果 DS18B20 没读到，用 DHT22 的温度
            if result["temperature"] is None:
                result["temperature"] = dht_temp
        if dht_humidity is not None:
            result["humidity"] = dht_humidity

        # 光敏传感器（数字输出）
        light = self._read_light_digital()
        if light is not None:
            result["light_level"] = 1 if light else 0

        # 填充缺失值
        if result["temperature"] is None:
            result["temperature"] = 25.0
        if result["humidity"] is None:
            result["humidity"] = 50.0
        if result["light_level"] is None:
            result["light_level"] = 0

        return result

    def _read_mock(self) -> dict:
        """开发环境 mock 数据"""
        import random
        return {
            "temperature": round(22 + random.random() * 6, 1),
            "humidity": round(50 + random.random() * 20, 1),
            "light_level": random.choice([0, 1]),
            "fire_detected": False,
        }
