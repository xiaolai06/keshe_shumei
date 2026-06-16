"""
Tool — OLED 显示控制
供 Agent 调用：设置 OLED 表情/文字（SSD1351 RGB 彩色）
"""
import logging

logger = logging.getLogger("SmartHome")


def set_oled(expression: str = "", text: str = "") -> dict:
    """设置 OLED 显示内容"""
    try:
        from hardware.oled import get_oled
        oled = get_oled()
        if expression:
            oled.show_expression(expression)
        if text:
            oled.show_text(text)
        logger.debug("OLED: expression=%s, text=%s", expression, text[:20])
        return {"success": True, "expression": expression, "text": text}
    except Exception as e:
        logger.debug("OLED mock: %s / %s", expression, text[:20])
        return {"success": True, "expression": expression, "text": text, "mock": True}
