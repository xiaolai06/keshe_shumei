"""
Hardware — USB 音响驱动
TTS 语音播报 + 音效播放
"""
import asyncio
import logging
import subprocess
import tempfile
import threading
from pathlib import Path

logger = logging.getLogger("SmartHome.hardware")

_instance = None
_instance_lock = threading.Lock()


def get_speaker() -> "Speaker":
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = Speaker()
    return _instance


class Speaker:
    """USB 音响驱动（edge-tts 生成 + mpg123/aplay 播放）"""

    def __init__(self, voice: str = "zh-CN-XiaoxiaoNeural"):
        self.voice = voice
        self._available: bool | None = None

    def _check(self) -> bool:
        """检查 mpg123 是否可用"""
        if self._available is None:
            try:
                subprocess.run(["mpg123", "--version"], capture_output=True, timeout=3)
                self._available = True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                self._available = False
        return self._available

    async def speak(self, text: str):
        """TTS 语音播报（异步）

        流程: text → edge-tts 生成 MP3 → mpg123 播放
        """
        if not text or not text.strip():
            return

        try:
            import edge_tts
        except ImportError:
            logger.error("edge-tts 未安装: pip install edge-tts")
            return

        tmp_path = Path(tempfile.gettempdir()) / f"pet_tts_{id(text) % 100000}.mp3"

        try:
            communicate = edge_tts.Communicate(text.strip(), self.voice)
            await communicate.save(str(tmp_path))
            logger.info("TTS generated: %s", tmp_path)
            self.play_mp3(str(tmp_path))
        except Exception as e:
            logger.error("TTS failed: %s", e)
        finally:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass

    def speak_sync(self, text: str):
        """同步包装：后台线程执行，不阻塞调用线程"""
        threading.Thread(target=lambda: asyncio.run(self.speak(text)), daemon=True).start()

    def play_mp3(self, filepath: str):
        """播放 MP3 文件"""
        if not Path(filepath).exists():
            logger.error("MP3 file not found: %s", filepath)
            return

        if self._check():
            try:
                subprocess.run(["mpg123", "-q", filepath], timeout=30, capture_output=True)
                logger.info("Played MP3: %s", filepath)
                return
            except Exception as e:
                logger.error("mpg123 failed: %s", e)

        # fallback: aplay 不支持 mp3，尝试 ffmpeg 转换
        try:
            wav_path = filepath.replace(".mp3", ".wav")
            subprocess.run(
                ["ffmpeg", "-y", "-i", filepath, "-acodec", "pcm_s16le", wav_path],
                capture_output=True, timeout=10,
            )
            self.play_wav(wav_path)
        except Exception as e:
            logger.error("MP3 playback failed: %s", e)

    def play_wav(self, filepath: str):
        """播放 WAV 文件"""
        if not Path(filepath).exists():
            logger.error("WAV file not found: %s", filepath)
            return

        try:
            subprocess.run(["aplay", "-q", filepath], timeout=30, capture_output=True)
            logger.info("Played WAV: %s", filepath)
        except FileNotFoundError:
            logger.error("aplay 不可用")
        except Exception as e:
            logger.error("WAV playback failed: %s", e)
