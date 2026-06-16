"""
Hardware — OLED 显示驱动
SSD1351 128×128 RGB 彩色 SPI
显示模式: 表情 / 对话 / 数据 / 提醒
"""
import logging
import threading
from pathlib import Path

logger = logging.getLogger("SmartHome.hardware")

_instance = None
_instance_lock = threading.Lock()


def get_oled() -> "OLEDDisplay":
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = OLEDDisplay()
    return _instance

# SSD1351 RGB 颜色常量
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_YELLOW = (255, 200, 50)
COLOR_CYAN = (0, 200, 255)
COLOR_GREEN = (50, 255, 100)
COLOR_RED = (255, 50, 50)
COLOR_BLUE = (110, 140, 255)
COLOR_PURPLE = (150, 80, 255)
COLOR_ORANGE = (255, 150, 50)

# 表情颜色映射
MOOD_COLORS = {
    "开心": COLOR_YELLOW,
    "好奇": COLOR_CYAN,
    "困倦": COLOR_PURPLE,
    "警觉": COLOR_RED,
    "话多": COLOR_GREEN,
    "平静": COLOR_BLUE,
    "孤独": COLOR_ORANGE,
    "默认": COLOR_WHITE,
}

# 像素风表情定义（眼睛坐标 + 嘴巴类型）
_EXPRESSIONS = {
    "开心": {"eyes": [(40, 36), (88, 36)], "mouth": "smile"},
    "好奇": {"eyes": [(40, 32), (88, 40)], "mouth": "small_o"},
    "困倦": {"eyes": [(40, 40), (88, 40)], "mouth": "flat"},
    "警觉": {"eyes": [(40, 28), (88, 28)], "mouth": "open"},
    "话多": {"eyes": [(40, 36), (88, 36)], "mouth": "talking"},
    "平静": {"eyes": [(40, 36), (88, 36)], "mouth": "smile"},
    "孤独": {"eyes": [(40, 40), (88, 40)], "mouth": "frown"},
    "默认": {"eyes": [(40, 36), (88, 36)], "mouth": "smile"},
}


class OLEDDisplay:
    """OLED 显示驱动 (SPI 接口, SSD1351 128×128 RGB 彩色)"""

    def __init__(
        self,
        spi_port: int = 0,
        spi_device: int = 0,
        gpio_cs: int = 8,
        gpio_dc: int = 13,
        gpio_rst: int = 24,
        font_path: str = "",
    ):
        self.gpio_cs = gpio_cs
        self.gpio_dc = gpio_dc
        self.gpio_rst = gpio_rst
        self.font_path = font_path
        self._device = None
        self._width = 128
        self._height = 128

    def _get_device(self):
        """延迟初始化 SSD1351 OLED 设备"""
        if self._device is not None:
            return self._device
        try:
            from luma.core.interface.serial import spi
            from luma.oled.device import ssd1351

            serial = spi(
                port=0, device=0,
                gpio_DC=self.gpio_dc,
                gpio_RST=self.gpio_rst,
                gpio_CS=self.gpio_cs,
            )
            self._device = ssd1351(serial, width=self._width, height=self._height)
            logger.info("OLED initialized: %dx%d RGB SPI (SSD1351)", self._width, self._height)
            return self._device
        except ImportError:
            logger.error("luma.oled 未安装: pip install luma.oled pillow")
            return None
        except Exception as e:
            logger.error("OLED init failed: %s", e)
            return None

    def _get_font(self, size: int = 14):
        """获取字体（优先中文字体，回退默认）"""
        try:
            from PIL import ImageFont
            if self.font_path and Path(self.font_path).exists():
                return ImageFont.truetype(self.font_path, size)
            # 尝试系统中文字体
            for path in ["/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
                         "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                         "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]:
                if Path(path).exists():
                    return ImageFont.truetype(path, size)
            return ImageFont.load_default()
        except Exception:
            return None

    def show_expression(self, expression: str):
        """显示表情（开心、好奇、困倦等）— RGB 彩色版"""
        device = self._get_device()
        if not device:
            return

        try:
            from PIL import Image, ImageDraw

            img = Image.new("RGB", (self._width, self._height), COLOR_BLACK)
            draw = ImageDraw.Draw(img)

            expr = _EXPRESSIONS.get(expression, _EXPRESSIONS["默认"])
            color = MOOD_COLORS.get(expression, COLOR_WHITE)

            # 画眼睛（实心圆，使用表情颜色）
            for ex, ey in expr["eyes"]:
                draw.ellipse((ex - 6, ey - 6, ex + 6, ey + 6), fill=color)

            # 画嘴巴
            mouth = expr["mouth"]
            cx, my = 64, 70
            if mouth == "smile":
                draw.arc((cx - 16, my - 8, cx + 16, my + 14), 0, 180, fill=color, width=2)
            elif mouth == "frown":
                draw.arc((cx - 16, my + 4, cx + 16, my + 24), 180, 360, fill=color, width=2)
            elif mouth == "open":
                draw.ellipse((cx - 10, my - 6, cx + 10, my + 12), fill=color)
            elif mouth == "small_o":
                draw.ellipse((cx - 6, my - 3, cx + 6, my + 9), fill=color)
            elif mouth == "flat":
                draw.line((cx - 14, my + 4, cx + 14, my + 4), fill=color, width=2)
            elif mouth == "talking":
                draw.arc((cx - 14, my - 6, cx + 14, my + 10), 0, 180, fill=color, width=2)
                draw.line((cx - 14, my + 4, cx + 14, my + 4), fill=color, width=2)

            # 底部显示表情名
            font = self._get_font(12)
            if font:
                draw.text((4, 110), expression, fill=color, font=font)

            device.display(img)
            logger.info("OLED expression: %s (color)", expression)

        except Exception as e:
            logger.error("OLED show_expression failed: %s", e)

    def show_text(self, text: str):
        """显示文字（对话回复，自动换行）— RGB 彩色版"""
        device = self._get_device()
        if not device or not text:
            return

        try:
            from PIL import Image, ImageDraw

            img = Image.new("RGB", (self._width, self._height), COLOR_BLACK)
            draw = ImageDraw.Draw(img)
            font = self._get_font(14)

            if font:
                # 自动换行：每行约 10 个中文字符（128px / 14px ≈ 9）
                lines = []
                line = ""
                for ch in text:
                    line += ch
                    if len(line) >= 9:
                        lines.append(line)
                        line = ""
                if line:
                    lines.append(line)

                # 最多显示 8 行（128px / 16px per line）
                y = 4
                for ln in lines[:8]:
                    draw.text((4, y), ln, fill=COLOR_WHITE, font=font)
                    y += 16
            else:
                # 无字体时显示截断的 ASCII
                draw.text((4, 4), text[:16], fill=COLOR_WHITE)
                draw.text((4, 20), text[16:32], fill=COLOR_WHITE)
                draw.text((4, 36), text[32:48], fill=COLOR_WHITE)

            device.display(img)
            logger.info("OLED text: %s...", text[:30])

        except Exception as e:
            logger.error("OLED show_text failed: %s", e)

    def show_data(self, temp: float, humidity: float, light: bool | None = None):
        """显示传感器数据 — RGB 彩色版"""
        device = self._get_device()
        if not device:
            return

        try:
            from PIL import Image, ImageDraw

            img = Image.new("RGB", (self._width, self._height), COLOR_BLACK)
            draw = ImageDraw.Draw(img)
            font = self._get_font(16)
            font_sm = self._get_font(12)

            if font:
                # 温度
                temp_color = COLOR_WHITE
                if temp > 30:
                    temp_color = COLOR_RED
                elif temp < 15:
                    temp_color = COLOR_CYAN
                draw.text((4, 8), f"Temp: {temp:.1f}C", fill=temp_color, font=font)

                # 湿度
                draw.text((4, 32), f"Humi: {humidity:.0f}%", fill=COLOR_BLUE, font=font)

                # 光照
                if light is not None:
                    light_text = "Light" if light else "Dark"
                    light_color = COLOR_YELLOW if light else COLOR_PURPLE
                    draw.text((4, 56), light_text, fill=light_color, font=font)

                # 舒适度指示
                comfort = "Nice!" if 20 <= temp <= 26 and 40 <= humidity <= 60 else "OK"
                if temp > 30:
                    comfort = "Hot!"
                elif temp < 15:
                    comfort = "Cold!"
                if font_sm:
                    draw.text((4, 100), comfort, fill=COLOR_GREEN, font=font_sm)

            device.display(img)

        except Exception as e:
            logger.error("OLED show_data failed: %s", e)

    def show_reminder(self, text: str):
        """显示提醒内容 — RGB 彩色版"""
        device = self._get_device()
        if not device:
            return

        try:
            from PIL import Image, ImageDraw

            img = Image.new("RGB", (self._width, self._height), COLOR_BLACK)
            draw = ImageDraw.Draw(img)
            font = self._get_font(14)

            # 闹钟图标（橙色圆形 + 指针）
            draw.ellipse((8, 8, 36, 36), outline=COLOR_ORANGE, width=2)
            draw.line((22, 14, 22, 24), fill=COLOR_ORANGE, width=2)
            draw.line((22, 22, 30, 22), fill=COLOR_ORANGE, width=2)
            # 铃铛
            draw.line((4, 4, 12, 12), fill=COLOR_ORANGE, width=2)
            draw.line((36, 12, 44, 4), fill=COLOR_ORANGE, width=2)

            # 提醒文字
            if font:
                lines = []
                line = ""
                for ch in text:
                    line += ch
                    if len(line) >= 8:
                        lines.append(line)
                        line = ""
                if line:
                    lines.append(line)
                y = 44
                for ln in lines[:5]:
                    draw.text((4, y), ln, fill=COLOR_WHITE, font=font)
                    y += 18

            device.display(img)
            logger.info("OLED reminder: %s", text[:30])

        except Exception as e:
            logger.error("OLED show_reminder failed: %s", e)

    def clear(self):
        """清屏"""
        device = self._get_device()
        if device:
            try:
                device.cleanup()
                self._device = None
                logger.info("OLED cleared")
            except Exception as e:
                logger.error("OLED clear failed: %s", e)
