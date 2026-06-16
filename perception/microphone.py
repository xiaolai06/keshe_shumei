# -*- coding: utf-8 -*-
"""
Perception — 硬件麦克风驱动 (INMP441 I2S)
arecord 持续录音 → 提供音频帧给 VAD 使用
"""
import logging
import struct
import subprocess
import threading
import time

import config

logger = logging.getLogger("SmartHome.hardware")


def _rms(samples: list[int]) -> float:
    """计算音频帧的 RMS 能量"""
    if not samples:
        return 0.0
    return (sum(s * s for s in samples) / len(samples)) ** 0.5


class Microphone:
    """
    INMP441 I2S 麦克风驱动。
    用 arecord 后台持续录音，提供 read_frame() 给上层 VAD 使用。
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        sample_width: int = 2,       # S16_LE = 2 bytes
        frame_duration_ms: int = 50,  # 每帧 50ms
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.sample_width = sample_width
        self.frame_duration_ms = frame_duration_ms

        # 每帧字节数 = 16000 × 1 × 2 × 0.05 = 1600
        self.frame_size = int(
            sample_rate * channels * sample_width * frame_duration_ms / 1000
        )

        self._process: subprocess.Popen | None = None
        self._lock = threading.Lock()
        self._running = False

    def start(self) -> bool:
        """启动 arecord 后台录音进程"""
        with self._lock:
            if self._running:
                return True
            try:
                cmd = [
                    "arecord",
                    "-D", "default",
                    "-f", "S16_LE",
                    "-r", str(self.sample_rate),
                    "-c", str(self.channels),
                    "-t", "raw",
                    "-q",
                    "-",            # 输出到 stdout
                ]
                self._process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                )
                self._running = True
                logger.info("麦克风启动: %dHz, %dch, 帧=%d bytes",
                            self.sample_rate, self.channels, self.frame_size)
                return True
            except FileNotFoundError:
                logger.error("arecord 不可用，请安装: sudo apt install alsa-utils")
                return False
            except Exception as e:
                logger.error("麦克风启动失败: %s", e)
                return False

    def read_frame(self) -> bytes | None:
        """
        读取一帧原始音频数据。
        返回 bytes（frame_size 字节），录音结束返回 None。
        """
        if not self._running or not self._process:
            return None
        try:
            data = self._process.stdout.read(self.frame_size)
            if len(data) < self.frame_size:
                return None
            return data
        except Exception:
            return None

    def frame_to_samples(self, frame: bytes) -> list[int]:
        """将原始 bytes 解包为 16-bit 有符号整数列表"""
        count = len(frame) // self.sample_width
        return struct.unpack(f"<{count}h", frame)

    def frame_rms(self, frame: bytes) -> float:
        """计算一帧的 RMS 能量"""
        return _rms(self.frame_to_samples(frame))

    def stop(self):
        """停止录音进程"""
        with self._lock:
            self._running = False
            if self._process:
                try:
                    self._process.terminate()
                    self._process.wait(timeout=3)
                except Exception:
                    try:
                        self._process.kill()
                    except Exception:
                        pass
                self._process = None
            logger.info("麦克风已停止")

    @property
    def is_running(self) -> bool:
        return self._running


# ─── 单例 ──────────────────────────────────────
_mic_instance: Microphone | None = None
_mic_lock = threading.Lock()


def get_microphone() -> Microphone:
    """获取全局麦克风单例"""
    global _mic_instance
    if _mic_instance is None:
        with _mic_lock:
            if _mic_instance is None:
                _mic_instance = Microphone()
    return _mic_instance
