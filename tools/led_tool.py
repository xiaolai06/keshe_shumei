"""
Tool — RGB LED 控制 (已移除)

当前硬件配置中不包含 RGB LED，此文件保留为兼容桩。
所有调用将静默忽略，不产生任何效果。
"""
import logging

logger = logging.getLogger("SmartHome")


def set_led(r: int = 0, g: int = 0, b: int = 0, mood: str | None = None) -> dict:
    """设置 RGB LED 颜色（兼容桩，无实际硬件）"""
    logger.debug("LED stub: r=%d g=%d b=%d mood=%s", r, g, b, mood)
    return {"success": True, "mock": True, "message": "RGB LED 硬件未配置"}
