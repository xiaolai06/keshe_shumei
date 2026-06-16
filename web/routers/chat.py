"""
Chat API — AI 对话接口
POST /api/chat       — 文字对话
POST /api/chat/stream — 流式对话 (SSE)
"""
import asyncio
import logging
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from memory.sensor_manager import get_latest
from memory.manager import MemoryManager

router = APIRouter()
logger = logging.getLogger("SmartHome")

_memo = MemoryManager()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat(req: ChatRequest):
    """文字对话（非流式）—— 调用 Agent 状态机"""
    try:
        from agent.graph import get_agent
        agent = get_agent()

        # 构建初始 state
        sensor = get_latest()
        state = {
            "messages": [{"role": "user", "content": req.message}],
            "sensor_data": {
                "temp": sensor.get("temperature", 25),
                "humidity": sensor.get("humidity", 50),
                "light": sensor.get("light_level", 300),
                "comfort": sensor.get("comfort_score", 0.7),
            },
            "voice_text": None,
            "image_desc": None,
            "recalled_memories": [],
            "mood": "happy",
            "oled_text": "",
            "oled_expression": "默认",
            "next_action": "act",
        }

        result = await asyncio.to_thread(agent.invoke, state)
        messages = result.get("messages", [])
        reply = messages[-1].content if messages else "嗯...我没听清"
        mood = result.get("mood", "happy")
        oled = result.get("oled_expression", "默认")

        # TTS 语音播报（后台异步，不阻塞响应）
        try:
            from tools.speaker_tool import play_speaker
            _task = asyncio.create_task(play_speaker(reply[:200]))
        except Exception as e:
            logger.debug("TTS skipped: %s", e)

        return {
            "success": True,
            "data": {
                "reply": reply,
                "mood": mood,
                "oled_expression": oled,
            },
        }
    except Exception as e:
        logger.error("Chat error: %s", e)
        # 降级：直接调用 LLM
        try:
            from agent.llm_client import get_llm
            llm = get_llm()
            reply = await asyncio.to_thread(llm.chat, [{"role": "user", "content": req.message}])
            return {
                "success": True,
                "data": {"reply": reply, "mood": "happy", "oled_expression": "默认"},
            }
        except Exception as e2:
            logger.error("Chat fallback error: %s", e2)
            return {
                "success": False,
                "data": {"reply": "对话出错，请稍后再试", "mood": "alert", "oled_expression": "警觉"},
            }


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """流式对话 (Server-Sent Events)"""

    async def generate():
        try:
            from agent.llm_client import get_llm
            llm = get_llm()

            sensor = get_latest()
            from agent.prompt import build_system_prompt
            system = build_system_prompt("happy", sensor, _memo.get_recent_context(5))

            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": req.message},
            ]

            full_reply = ""
            async for token in llm.chat_stream(messages):
                full_reply += token
                yield f"data: {token}\n\n"

            # 记录交互
            _memo.log_interaction("web", req.message, full_reply, "happy")

            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error("Stream chat error: %s", e)
            yield f"data: ⚠️ 对话出错: {e}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
