"""
Tool — RGB LED 控制
供 Agent 调用：设置 LED 颜色/模式
"""
import logging

logger = logging.getLogger("SmartHome")


def set_led(r: int = 0, g: int = 0, b: int = 0, mood: str | None = None) -> dict:
    """设置 RGB LED 颜色"""
    try:
        from hardware.led import RGBLed
        led = RGBLed()
        if mood:
            led.set_mood(mood)
        else:
            led.set_color(r, g, b)
        logger.debug("LED: r=%d g=%d b=%d mood=%s", r, g, b, mood)
        return {"success": True}
    except Exception as e:
        logger.debug("LED mock: r=%d g=%d b=%d mood=%s", r, g, b, mood)
        return {"success": True, "mock": True}
