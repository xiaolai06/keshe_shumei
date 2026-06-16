"""
Hardware — RGB LED 驱动 (已移除)

当前硬件配置中不包含 RGB LED，此文件保留为兼容桩。
所有调用将静默忽略，不产生任何效果。
"""
import logging

logger = logging.getLogger("SmartHome.hardware")


class RGBLed:
    """RGB LED 兼容桩（无实际硬件）"""

    def __init__(self, pin_r: int = 0, pin_g: int = 0, pin_b: int = 0):
        logger.debug("RGB LED not available (hardware removed)")

    def set_color(self, r: int, g: int, b: int):
        logger.debug("LED stub: set_color(%d, %d, %d) ignored", r, g, b)

    def set_mood(self, mood: str):
        logger.debug("LED stub: set_mood(%s) ignored", mood)

    def set_alert(self, alert_type: str):
        logger.debug("LED stub: set_alert(%s) ignored", alert_type)

    def blink(self, r: int, g: int, b: int, times: int = 3, interval: float = 0.3):
        logger.debug("LED stub: blink ignored")

    def off(self):
        logger.debug("LED stub: off ignored")


def get_led() -> RGBLed:
    return RGBLed()
