# -*- coding: utf-8 -*-
"""
Perception — 语音监听服务 (VAD + STT + Agent)
持续监听麦克风 → 能量检测停顿 → 云端 STT 识别 → Agent 决策 → 硬件输出

数据流:
  INMP441 → arecord → VAD帧检测 → 缓存语音段 → STT API → 文字
    → Agent 状态机(Perceive→Recall→Think→Decide→Act)
    → OLED 表情 + LED 颜色 + TTS 音响播报
"""
import asyncio
import logging
import struct
import threading
import time
import wave
import io

import config

logger = logging.getLogger("SmartHome.listener")


class VoiceListener:
    """
    基于能量阈值的 VAD 语音监听器。
    持续监听麦克风，检测语音段落，送入 STT → Agent。
    """

    def __init__(
        self,
        energy_threshold: int | None = None,
        silence_duration_ms: int | None = None,
        min_speech_ms: int | None = None,
        max_speech_s: int | None = None,
    ):
        # 从 config 读取，允许参数覆盖
        self.energy_threshold = energy_threshold or config.VOICE_ENERGY_THRESHOLD
        self.silence_duration_ms = silence_duration_ms or config.VOICE_SILENCE_MS
        self.min_speech_ms = min_speech_ms or config.VOICE_MIN_SPEECH_MS
        self.max_speech_s = max_speech_s or config.VOICE_MAX_SPEECH_S

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._processing = False     # 是否正在处理一段语音
        self._manual_trigger: bytes | None = None  # Web 远程触发的音频

    # ─── 构建 WAV 文件 ───────────────────────────

    @staticmethod
    def _raw_to_wav(raw_pcm: bytes, sample_rate: int = 16000, channels: int = 1) -> bytes:
        """将 raw PCM 转换为 WAV 格式的 bytes"""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)  # S16_LE
            wf.setframerate(sample_rate)
            wf.writeframes(raw_pcm)
        return buf.getvalue()

    # ─── STT 识别 ────────────────────────────────

    def _recognize(self, wav_bytes: bytes) -> str | None:
        """调用云端 STT API 识别语音"""
        try:
            from perception.speech import recognize_audio
            text = recognize_audio(wav_bytes, filename="speech.wav")
            if text and text.strip():
                logger.info("🎤 语音识别: %s", text[:80])
                return text.strip()
            logger.debug("STT 返回空文字")
            return None
        except Exception as e:
            logger.error("STT 识别失败: %s", e)
            return None

    # ─── Agent 处理 ──────────────────────────────

    def _process_voice(self, text: str):
        """将识别文字送入 Agent 状态机，驱动全部输出"""
        try:
            from agent.graph import get_agent
            from memory.sensor_manager import get_latest
            from memory.manager import MemoryManager

            sensor = get_latest()
            memo = MemoryManager()

            state = {
                "messages": [{"role": "user", "content": text}],
                "sensor_data": {
                    "temp": sensor.get("temperature", 25),
                    "humidity": sensor.get("humidity", 50),
                    "light": sensor.get("light_level", 300),
                    "comfort": sensor.get("comfort_score", 0.7),
                },
                "voice_text": text,
                "image_desc": None,
                "recalled_memories": [],
                "mood": "happy",
                "oled_text": "",
                "oled_expression": "默认",
                "next_action": "act",
            }

            agent = get_agent()
            result = agent.invoke(state)

            messages = result.get("messages", [])
            reply = messages[-1].content if messages else "嗯..."
            mood = result.get("mood", "happy")
            oled_expr = result.get("oled_expression", "默认")

            logger.info("🤖 Agent 回复 [%s]: %s", mood, reply[:60])

            # ── TTS 语音播报 ──
            try:
                from hardware.speaker import get_speaker
                spk = get_speaker()
                spk.speak_sync(reply[:200])
            except Exception as e:
                logger.debug("TTS skipped: %s", e)

            # ── OLED 显示 ──
            try:
                from hardware.oled import get_oled
                oled = get_oled()
                oled.show_expression(oled_expr)
                if reply:
                    oled.show_text(reply[:60])
            except Exception as e:
                logger.debug("OLED skipped: %s", e)

            # ── LED 情绪颜色 ──
            try:
                from hardware.led import get_led
                get_led().set_mood(mood)
            except Exception as e:
                logger.debug("LED skipped: %s", e)

            # ── 记录交互 ──
            try:
                memo.log_interaction("voice", text, reply, mood)
            except Exception:
                pass

        except Exception as e:
            logger.error("Agent 处理失败: %s", e)

    # ─── 主监听循环 ──────────────────────────────

    def _listen_loop(self):
        """后台线程：持续录音 + VAD 检测 + 语音段处理"""
        from perception.microphone import get_microphone

        mic = get_microphone()
        if not mic.start():
            logger.error("麦克风启动失败，语音监听退出")
            return

        frame_ms = mic.frame_duration_ms
        silence_frames_needed = self.silence_duration_ms // frame_ms
        min_speech_frames = self.min_speech_ms // frame_ms
        max_speech_frames = int(self.max_speech_s * 1000 / frame_ms)

        buffer = bytearray()
        silence_count = 0
        speech_frames = 0
        is_speaking = False

        logger.info(
            "语音监听启动: 阈值=%d, 静音=%dms(%d帧), 最短语音=%dms, 最长=%ds",
            self.energy_threshold, self.silence_duration_ms,
            silence_frames_needed, self.min_speech_ms, self.max_speech_s,
        )

        while not self._stop_event.is_set():
            # ── 检查 Web 远程触发 ──
            if self._manual_trigger:
                wav = self._manual_trigger
                self._manual_trigger = None
                self._processing = True
                text = self._recognize(wav)
                if text:
                    self._process_voice(text)
                self._processing = False
                continue

            # ── 读取一帧 ──
            frame = mic.read_frame()
            if not frame:
                if not self._stop_event.is_set():
                    time.sleep(0.1)
                    mic.start()
                continue

            # ── 计算能量 ──
            rms = mic.frame_rms(frame)

            if rms > self.energy_threshold:
                # 有声音
                is_speaking = True
                silence_count = 0
                speech_frames += 1
                buffer.extend(frame)

                # 防止超长录音
                if speech_frames >= max_speech_frames:
                    logger.info("语音过长（%ds），强制截断处理", self.max_speech_s)
                    silence_count = silence_frames_needed  # 触发处理

            elif is_speaking:
                # 静音但之前在说话 → 继续缓存（保留句尾）
                silence_count += 1
                speech_frames += 1
                buffer.extend(frame)

                if silence_count >= silence_frames_needed:
                    # ★ 停顿检测到 → 一句话结束
                    if speech_frames >= min_speech_frames:
                        self._processing = True
                        wav_bytes = self._raw_to_wav(bytes(buffer))
                        logger.info(
                            "语音段: %d 帧 (%.1fs), RMS≈%.0f → 发送识别",
                            speech_frames,
                            speech_frames * frame_ms / 1000,
                            rms,
                        )
                        text = self._recognize(wav_bytes)
                        if text:
                            self._process_voice(text)
                        self._processing = False
                    else:
                        logger.debug("语音太短 (%d帧)，忽略", speech_frames)

                    # 重置
                    buffer.clear()
                    is_speaking = False
                    silence_count = 0
                    speech_frames = 0

            # 静音且没在说话 → 继续监听，什么都不做

        mic.stop()
        logger.info("语音监听已退出")

    # ─── 公开接口 ────────────────────────────────

    def start(self):
        """启动后台监听线程"""
        if self._thread and self._thread.is_alive():
            logger.warning("语音监听已在运行")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._listen_loop, daemon=True, name="voice-listener",
        )
        self._thread.start()
        logger.info("语音监听线程已启动")

    def stop(self):
        """停止监听"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("语音监听已停止")

    def trigger_with_audio(self, wav_bytes: bytes):
        """Web 远程触发：传入 WAV 音频进行识别"""
        self._manual_trigger = wav_bytes

    def trigger_with_text(self, text: str):
        """Web 远程触发：直接传入文字走 Agent"""
        t = threading.Thread(
            target=self._process_voice, args=(text,), daemon=True,
        )
        t.start()

    @property
    def is_listening(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def is_processing(self) -> bool:
        return self._processing

    def get_status(self) -> dict:
        return {
            "listening": self.is_listening,
            "processing": self.is_processing,
            "energy_threshold": self.energy_threshold,
            "silence_ms": self.silence_duration_ms,
        }


# ─── 全局单例 ──────────────────────────────────
_listener: VoiceListener | None = None
_listener_lock = threading.Lock()


def get_listener() -> VoiceListener:
    """获取全局语音监听器单例"""
    global _listener
    if _listener is None:
        with _listener_lock:
            if _listener is None:
                _listener = VoiceListener()
    return _listener
