"""
Settings API — 配置接口
GET/PUT /api/settings/llm       — 读取/保存 LLM 配置
GET     /api/settings/llm/models — 获取模型列表
POST    /api/settings/llm/test   — 测试 LLM 连接
GET/PUT /api/settings/stt       — 读取/保存 STT 语音配置
POST    /api/settings/stt/test   — 测试 STT 连接
POST    /api/stt/recognize       — 语音识别（接收音频）
"""
import logging
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel, Field

import config

router = APIRouter()
logger = logging.getLogger("SmartHome")


class LLMConfigUpdate(BaseModel):
    """LLM 配置更新请求"""
    provider: str = Field(default="deepseek")
    api_key: str = Field(default="")
    base_url: str = Field(default="")
    model: str = Field(default="")
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=512, ge=64, le=8192)


class STTConfigUpdate(BaseModel):
    """STT 配置更新请求"""
    provider: str = Field(default="openai")
    api_key: str = Field(default="")
    base_url: str = Field(default="")
    model: str = Field(default="whisper-1")
    language: str = Field(default="zh")


# ─── LLM ───────────────────────────────────────

@router.get("/settings/llm")
async def get_llm_settings():
    return {
        "success": True,
        "data": config.get_llm_config_safe(),
        "presets": config.LLM_PRESETS,
    }


@router.put("/settings/llm")
async def update_llm_settings(cfg: LLMConfigUpdate):
    llm_cfg = cfg.model_dump()
    config.save_llm_config(llm_cfg)
    try:
        from agent.llm_client import refresh_llm
        refresh_llm()
    except Exception as e:
        logger.warning("Failed to refresh LLM client: %s", e)
    return {"success": True, "data": config.get_llm_config_safe()}


@router.get("/settings/llm/models")
async def list_models():
    try:
        from agent.llm_client import get_llm
        llm = get_llm()
        models = llm.list_models()
        return {"success": True, "data": models}
    except Exception as e:
        logger.error("List models error: %s", e)
        return {"success": False, "data": [], "error": str(e)}


@router.post("/settings/llm/test")
async def test_llm_connection():
    try:
        from agent.llm_client import get_llm
        llm = get_llm()
        result = llm.test_connection()
        return {"success": result["success"], "data": result}
    except Exception as e:
        logger.error("Test connection error: %s", e)
        return {"success": False, "data": {"success": False, "message": str(e), "latency_ms": 0, "model": ""}}


# ─── STT 语音识别 ────────────────────────────────

@router.get("/settings/stt")
async def get_stt_settings():
    return {
        "success": True,
        "data": config.get_stt_config_safe(),
        "presets": config.STT_PRESETS,
    }


@router.put("/settings/stt")
async def update_stt_settings(cfg: STTConfigUpdate):
    stt_cfg = cfg.model_dump()
    config.save_stt_config(stt_cfg)
    return {"success": True, "data": config.get_stt_config_safe()}


@router.post("/settings/stt/test")
async def test_stt_connection():
    try:
        from perception.speech import test_stt_connection
        result = test_stt_connection()
        return {"success": result["success"], "data": result}
    except Exception as e:
        return {"success": False, "data": {"success": False, "message": str(e), "latency_ms": 0}}


@router.post("/stt/recognize")
async def stt_recognize(audio: UploadFile = File(...)):
    """
    接收浏览器录音的音频文件，调用云端 STT API 识别。限制 10MB。
    """
    try:
        # 上传大小限制: 10MB
        MAX_SIZE = 10 * 1024 * 1024
        content_length = audio.size or 0
        if content_length > MAX_SIZE:
            return {"success": False, "error": f"音频文件过大（最大 10MB），当前 {content_length / 1024 / 1024:.1f}MB"}

        audio_bytes = await audio.read()
        if not audio_bytes:
            return {"success": False, "error": "音频为空"}

        from perception.speech import recognize_audio
        text = recognize_audio(audio_bytes, filename=audio.filename or "audio.webm")

        if text:
            return {"success": True, "data": {"text": text}}
        return {"success": False, "error": "识别失败，请检查 STT 配置"}
    except Exception as e:
        logger.error("STT recognize error: %s", e)
        return {"success": False, "error": str(e)}
