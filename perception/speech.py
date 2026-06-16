"""
Perception — 语音识别（云端 STT API）
浏览器录音 → 上传到后端 → 调用云端 Whisper API → 返回文字
"""
import io
import logging

import config

logger = logging.getLogger("SmartHome")


def recognize_audio(audio_bytes: bytes, filename: str = "audio.webm") -> str | None:
    """
    调用云端 STT API 识别音频。

    Args:
        audio_bytes: 音频文件的二进制内容（webm/wav/mp3/ogg）
        filename: 文件名（用于 MIME 类型推断）

    Returns:
        识别出的文字，失败返回 None
    """
    api_key = config.STT_API_KEY
    base_url = config.STT_BASE_URL.rstrip("/")
    model = config.STT_MODEL
    language = config.STT_LANGUAGE

    if not api_key:
        logger.warning("STT API Key 未配置")
        return None

    url = f"{base_url}/audio/transcriptions"
    files = {"file": (filename, audio_bytes)}
    data = {"model": model}
    if language:
        data["language"] = language
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        import httpx

        # 同步请求（httpx 不需要 async）
        with httpx.Client(timeout=30) as client:
            resp = client.post(url, headers=headers, files=files, data=data)
            resp.raise_for_status()
            result = resp.json()
            text = result.get("text", "")
            logger.info("STT recognized: %s", text[:80])
            return text

    except ImportError:
        # 没有 httpx，用 requests 的 fallback
        try:
            import requests
            resp = requests.post(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                files={"file": (filename, audio_bytes)},
                data={"model": model, "language": language},
                timeout=30,
            )
            resp.raise_for_status()
            text = resp.json().get("text", "")
            logger.info("STT recognized: %s", text[:80])
            return text
        except Exception as e:
            logger.error("STT request failed (requests): %s", e)
            return None
    except Exception as e:
        logger.error("STT request failed: %s", e)
        return None


def test_stt_connection() -> dict:
    """测试 STT API 连通性"""
    api_key = config.STT_API_KEY
    if not api_key:
        return {"success": False, "message": "API Key 未配置"}

    import time
    base_url = config.STT_BASE_URL.rstrip("/")
    start = time.time()

    try:
        import httpx
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                f"{base_url}/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            latency = int((time.time() - start) * 1000)
            if resp.status_code == 200:
                return {"success": True, "message": "连接成功", "latency_ms": latency}
            return {"success": False, "message": f"HTTP {resp.status_code}", "latency_ms": latency}
    except Exception as e:
        latency = int((time.time() - start) * 1000)
        return {"success": False, "message": str(e), "latency_ms": latency}
