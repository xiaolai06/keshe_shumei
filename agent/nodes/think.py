"""
Agent Node — Think（LLM 推理）
构建 prompt + 调用大模型
"""
import json
import logging
from agent.state import PetState
from agent.prompt import build_system_prompt

logger = logging.getLogger("SmartHome")


def think_node(state: PetState) -> dict:
    """
    推理节点：构建 prompt，调用 LLM，返回回复。
    """
    messages = state.get("messages", [])
    mood = state.get("mood", "happy")
    sensor = state.get("sensor_data", {})
    memories = state.get("recalled_memories", [])

    # 构建 system prompt
    system_prompt = build_system_prompt(mood, sensor, memories)

    # 构建消息列表
    llm_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        if hasattr(msg, "content"):
            role = "assistant" if msg.type == "ai" else "user"
            llm_messages.append({"role": role, "content": msg.content})
        elif isinstance(msg, dict):
            llm_messages.append(msg)

    # 如果有语音输入，追加到消息中
    voice = state.get("voice_text")
    if voice:
        llm_messages.append({"role": "user", "content": f"[语音输入] {voice}"})

    # 如果有图像描述，追加
    image_desc = state.get("image_desc")
    if image_desc:
        llm_messages.append({"role": "system", "content": f"[摄像头画面] {image_desc}"})

    # 调用 LLM
    try:
        from agent.llm_client import get_llm
        llm = get_llm()
        reply = llm.chat(llm_messages)
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        reply = "哎呀，我的大脑好像卡住了...等会儿再聊吧~"

    logger.debug("Think: reply=%s", reply[:80])
    return {"messages": [{"role": "assistant", "content": reply}]}
