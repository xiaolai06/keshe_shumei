"""
Chat API — AI 对话接口
POST /api/chat       — 文字对话
POST /api/chat/stream — 流式对话 (SSE)
"""
import asyncio
import logging
from datetime import datetime
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


def _build_sensor_state() -> dict:
    """构建包含传感器数据 + 当前时间的 sensor_data dict"""
    sensor = get_latest()
    now = datetime.now()
    return {
        "temp": sensor.get("temperature", 25),
        "humidity": sensor.get("humidity", 50),
        "light": sensor.get("light_level", 0),
        "comfort": sensor.get("comfort_score", 0.7),
        "datetime": now.strftime("%Y-%m-%d %H:%M"),
        "hour": now.hour,
    }


@router.post("/chat")
async def chat(req: ChatRequest):
    """文字对话（非流式）—— 调用 Agent 状态机"""
    try:
        from agent.graph import get_agent
        agent = get_agent()

        # 构建初始 state
        state = {
            "messages": [{"role": "user", "content": req.message}],
            "sensor_data": _build_sensor_state(),
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
            from agent.prompt import build_system_prompt
            llm = get_llm()
            system = build_system_prompt("happy", _build_sensor_state(), _memo.get_recent_context(5))
            reply = await asyncio.to_thread(llm.chat, [
                {"role": "system", "content": system},
                {"role": "user", "content": req.message},
            ])
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
    """流式对话 (Server-Sent Events)

    相比非流式版本增加了：
    - 记忆检索（关键词 + 最近上下文）
    - 流式完成后推断情绪 + 更新 OLED
    - 记录交互到数据库（含推断后的情绪）
    """

    async def generate():
        try:
            from agent.llm_client import get_llm
            from agent.prompt import build_system_prompt
            llm = get_llm()

            sensor = _build_sensor_state()

            # 记忆检索：关键词匹配 + 最近上下文
            recent_context = _memo.get_recent_context(5)
            try:
                recalled = _memo.recall(req.message, top_k=3)
            except Exception:
                recalled = []
            all_memories = recalled + recent_context

            system = build_system_prompt("happy", sensor, all_memories)

            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": req.message},
            ]

            full_reply = ""
            async for token in llm.chat_stream(messages):
                full_reply += token
                yield f"data: {token}\n\n"

            # 流式完成后：推断情绪
            from agent.nodes.act import _infer_mood
            mood = _infer_mood(full_reply, sensor)
            oled_expression = {
                "happy": "开心", "curious": "好奇", "sleepy": "困倦",
                "alert": "警觉", "chatty": "健谈", "calm": "平静", "lonely": "孤独",
            }.get(mood, "默认")

            # 更新 OLED 表情
            try:
                from hardware.oled import get_oled
                oled = get_oled()
                oled.show_expression(oled_expression)
                if full_reply:
                    oled.show_text(full_reply[:60])
            except Exception:
                pass

            # 记录交互到数据库
            try:
                from memory.database import get_conn
                with get_conn() as conn:
                    conn.execute(
                        "INSERT INTO interactions (source, user_input, agent_reply, mood) VALUES (?, ?, ?, ?)",
                        ("web", req.message, full_reply, mood),
                    )
            except Exception:
                pass

            # 发送情绪元数据给前端
            import json
            meta = json.dumps({"mood": mood, "oled_expression": oled_expression}, ensure_ascii=False)
            yield f"data: [META]{meta}\n\n"

            # TTS 语音播报
            try:
                from tools.speaker_tool import play_speaker
                asyncio.create_task(play_speaker(full_reply[:200]))
            except Exception:
                pass

            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error("Stream chat error: %s", e)
            yield f"data: ⚠️ 对话出错: {e}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
