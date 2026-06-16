# -*- coding: utf-8 -*-
"""
Voice API — 语音监听控制 + 远程触发
GET  /api/voice/status    — 语音监听状态
POST /api/voice/start     — 启动监听
POST /api/voice/stop      — 停止监听
POST /api/voice/trigger   — 远程文字触发（直接传文字走 Agent）
POST /api/voice/upload    — 上传音频识别
"""
import logging

from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger("SmartHome")


@router.get("/voice/status")
async def voice_status():
    """获取语音监听状态"""
    try:
        from perception.listener import get_listener
        return {"success": True, "data": get_listener().get_status()}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/voice/start")
async def voice_start():
    """启动语音监听"""
    try:
        from perception.listener import get_listener
        listener = get_listener()
        listener.start()
        return {"success": True, "data": listener.get_status()}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/voice/stop")
async def voice_stop():
    """停止语音监听"""
    try:
        from perception.listener import get_listener
        get_listener().stop()
        return {"success": True, "data": {"listening": False}}
    except Exception as e:
        return {"success": False, "error": str(e)}


class VoiceTriggerRequest(BaseModel):
    text: str


@router.post("/voice/trigger")
async def voice_trigger(req: VoiceTriggerRequest):
    """
    远程文字触发：直接将文字送入 Agent 状态机处理。
    用途：Web 前端语音识别后可直接调用此接口走 Agent。
    """
    try:
        if not req.text.strip():
            return {"success": False, "error": "文字不能为空"}

        from perception.listener import get_listener
        get_listener().trigger_with_text(req.text.strip())
        return {"success": True, "data": {"text": req.text.strip(), "status": "processing"}}
    except Exception as e:
        logger.error("Voice trigger error: %s", e)
        return {"success": False, "error": str(e)}


@router.post("/voice/upload")
async def voice_upload(audio: UploadFile = File(...)):
    """
    上传音频文件 → 云端 STT 识别 → 文字送入 Agent。
    用途：硬件按钮录音后上传音频。
    """
    try:
        audio_bytes = await audio.read()
        if not audio_bytes:
            return {"success": False, "error": "音频为空"}

        from perception.speech import recognize_audio
        text = recognize_audio(audio_bytes, filename=audio.filename or "audio.wav")

        if not text:
            return {"success": False, "error": "识别失败，请检查 STT 配置"}

        # 识别成功，送入 Agent
        from perception.listener import get_listener
        get_listener().trigger_with_text(text)

        return {
            "success": True,
            "data": {"text": text, "status": "processing"},
        }
    except Exception as e:
        logger.error("Voice upload error: %s", e)
        return {"success": False, "error": str(e)}
