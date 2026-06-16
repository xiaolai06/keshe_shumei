"""
Hardware — OLED 显示驱动
SSD1306 128×64 SPI
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

# 像素风表情定义（16×16 简笔画，用坐标列表表示）
_EXPRESSIONS = {
    "开心": {"eyes": [(40, 20), (88, 20)], "mouth": "smile"},
    "好奇": {"eyes": [(40, 18), (88, 22)], "mouth": "small_o"},
    "困倦": {"eyes": [(40, 22), (88, 22)], "mouth": "flat"},
    "警觉": {"eyes": [(40, 16), (88, 16)], "mouth": "open"},
    "话多": {"eyes": [(40, 20), (88, 20)], "mouth": "talking"},
    "平静": {"eyes": [(40, 20), (88, 20)], "mouth": "smile"},
    "孤独": {"eyes": [(40, 22), (88, 22)], "mouth": "frown"},
    "默认": {"eyes": [(40, 20), (88, 20)], "mouth": "smile"},
}


class OLEDDisplay:
    """OLED 显示驱动 (SPI 接口, SSD1306 128×64)"""

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
        self._height = 64

    def _get_device(self):
        """延迟初始化 OLED 设备"""
        if self._device is not None:
            return self._device
        try:
            from luma.core.interface.serial import spi
            from luma.oled.device import ssd1306

            serial = spi(
                port=0, device=0,
                gpio_DC=self.gpio_dc,
                gpio_RST=self.gpio_rst,
                gpio_CS=self.gpio_cs,
            )
            self._device = ssd1306(serial, width=self._width, height=self._height)
            logger.info("OLED initialized: %dx%d SPI", self._width, self._height)
            return self._device
        except ImportError:
            logger.error("luma.oled 未安装: pip install luma.oled pillow")
            return None
        except Exception as e:
            logger.error("OLED init failed: %s", e)
            return None

    def _get_font(self, size: int = 12):
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
        """显示表情（开心、好奇、困倦等）"""
        device = self._get_device()
        if not device:
            return

        try:
            from PIL import Image, ImageDraw

            img = Image.new("1", (self._width, self._height), 0)
            draw = ImageDraw.Draw(img)

            expr = _EXPRESSIONS.get(expression, _EXPRESSIONS["默认"])

            # 画眼睛（实心圆）
            for ex, ey in expr["eyes"]:
                draw.ellipse((ex - 4, ey - 4, ex + 4, ey + 4), fill=1)

            # 画嘴巴
            mouth = expr["mouth"]
            cx, my = 64, 42
            if mouth == "smile":
                draw.arc((cx - 12, my - 6, cx + 12, my + 10), 0, 180, fill=1)
            elif mouth == "frown":
                draw.arc((cx - 12, my, cx + 12, my + 16), 180, 360, fill=1)
            elif mouth == "open":
                draw.ellipse((cx - 8, my - 4, cx + 8, my + 8), fill=1)
            elif mouth == "small_o":
                draw.ellipse((cx - 4, my - 2, cx + 4, my + 6), fill=1)
            elif mouth == "flat":
                draw.line((cx - 10, my + 2, cx + 10, my + 2), fill=1)
            elif mouth == "talking":
                draw.arc((cx - 10, my - 4, cx + 10, my + 8), 0, 180, fill=1)
                draw.line((cx - 10, my + 2, cx + 10, my + 2), fill=1)

            # 底部显示表情名
            font = self._get_font(10)
            if font:
                draw.text((4, 54), expression, fill=1, font=font)

            device.display(img)
            logger.info("OLED expression: %s", expression)

        except Exception as e:
            logger.error("OLED show_expression failed: %s", e)

    def show_text(self, text: str):
        """显示文字（对话回复，自动换行）"""
        device = self._get_device()
        if not device or not text:
            return

        try:
            from PIL import Image, ImageDraw

            img = Image.new("1", (self._width, self._height), 0)
            draw = ImageDraw.Draw(img)
            font = self._get_font(12)

            if font:
                # 自动换行：每行约 16 个中文字符
                lines = []
                line = ""
                for ch in text:
                    line += ch
                    if len(line) >= 16:
                        lines.append(line)
                        line = ""
                if line:
                    lines.append(line)

                # 最多显示 5 行（64px / 13px per line）
                y = 2
                for ln in lines[:5]:
                    draw.text((2, y), ln, fill=1, font=font)
                    y += 13
            else:
                # 无字体时显示截断的 ASCII
                draw.text((2, 2), text[:21], fill=1)
                draw.text((2, 16), text[21:42], fill=1)

            device.display(img)
            logger.info("OLED text: %s...", text[:30])

        except Exception as e:
            logger.error("OLED show_text failed: %s", e)

    def show_data(self, temp: float, humidity: float):
        """显示传感器数据"""
        device = self._get_device()
        if not device:
            return

        try:
            from PIL import Image, ImageDraw

            img = Image.new("1", (self._width, self._height), 0)
            draw = ImageDraw.Draw(img)
            font = self._get_font(14)
            font_sm = self._get_font(10)

            if font:
                draw.text((4, 4), f"Temp: {temp:.1f}C", fill=1, font=font)
                draw.text((4, 24), f"Humi: {humidity:.0f}%", fill=1, font=font)

                # 舒适度指示
                comfort = "Nice!" if 20 <= temp <= 26 and 40 <= humidity <= 60 else "OK"
                if temp > 30:
                    comfort = "Hot!"
                elif temp < 15:
                    comfort = "Cold!"
                if font_sm:
                    draw.text((4, 48), comfort, fill=1, font=font_sm)

            device.display(img)

        except Exception as e:
            logger.error("OLED show_data failed: %s", e)

    def show_reminder(self, text: str):
        """显示提醒内容"""
        device = self._get_device()
        if not device:
            return

        try:
            from PIL import Image, ImageDraw

            img = Image.new("1", (self._width, self._height), 0)
            draw = ImageDraw.Draw(img)
            font = self._get_font(12)

            # 闹钟图标（简单矩形+两条线）
            draw.rectangle((4, 4, 20, 20), outline=1)
            draw.line((12, 4, 12, 10), fill=1)
            draw.line((12, 10, 18, 10), fill=1)
            draw.line((2, 2, 6, 6), fill=1)
            draw.line((18, 6, 22, 2), fill=1)

            # 提醒文字
            if font:
                lines = []
                line = ""
                for ch in text:
                    line += ch
                    if len(line) >= 14:
                        lines.append(line)
                        line = ""
                if line:
                    lines.append(line)
                y = 4
                for ln in lines[:4]:
                    draw.text((26, y), ln, fill=1, font=font)
                    y += 14

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
