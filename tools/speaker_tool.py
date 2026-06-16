"""
Tool — 语音播放（TTS）
供 Agent 调用：文字转语音播放
"""
import logging
import asyncio

logger = logging.getLogger("SmartHome")


async def play_speaker(text: str) -> dict:
    """TTS 文字转语音并播放"""
    try:
        from hardware.speaker import get_speaker
        spk = get_speaker()
        await spk.speak(text)
        logger.debug("Speaker: %s", text[:30])
        return {"success": True, "text": text}
    except Exception as e:
        logger.debug("Speaker mock: %s", text[:30])
        return {"success": True, "text": text, "mock": True}


def play_speaker_sync(text: str) -> dict:
    """同步版本（供非 async 上下文调用）"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 在已有 event loop 中，创建 task
            asyncio.ensure_future(play_speaker(text))
            return {"success": True, "text": text, "async": True}
        return loop.run_until_complete(play_speaker(text))
    except Exception:
        logger.debug("Speaker mock: %s", text[:30])
        return {"success": True, "text": text, "mock": True}
