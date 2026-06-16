"""
Perception — 传感器读取
DS18B20 温度 + DHT11 湿度 + BH1750 光照
"""
# TODO: 接入真实硬件驱动
# try:
#     import RPi.GPIO as GPIO
#     import adafruit_dht
#     HARDWARE_AVAILABLE = True
# except ImportError:
#     HARDWARE_AVAILABLE = False

HARDWARE_AVAILABLE = False


class SensorReader:
    """传感器统一读取接口"""

    def read_all(self) -> dict:
        """读取所有传感器数据"""
        if HARDWARE_AVAILABLE:
            return self._read_hardware()
        return self._read_mock()

    def _read_hardware(self) -> dict:
        """从真实硬件读取"""
        # TODO: 实现 DS18B20 + DHT11 + BH1750 读取
        return self._read_mock()

    def _read_mock(self) -> dict:
        """开发环境 mock 数据"""
        import random
        return {
            "temperature": round(22 + random.random() * 6, 1),
            "humidity": round(50 + random.random() * 20, 1),
            "light_lux": round(200 + random.random() * 300),
            "fire_detected": False,
        }
