"""
AI Agent — PetState 定义
LangGraph 状态机的全局状态结构
"""
from typing import TypedDict, Annotated
from langgraph.graph import add_messages


class PetState(TypedDict):
    """桌宠 Agent 全局状态"""
    # 对话消息（LangGraph 自动管理）
    messages: Annotated[list, add_messages]

    # 传感器快照
    sensor_data: dict   # {temp, humidity, light, fire_detected, comfort_score}

    # 语音输入
    voice_text: str | None

    # 图像描述
    image_desc: str | None

    # 记忆检索结果
    recalled_memories: list  # [{content, importance, score, source}]

    # 当前情绪
    mood: str  # happy/curious/sleepy/alert/chatty/calm/lonely

    # OLED 输出
    oled_text: str
    oled_expression: str

    # 决策路由
    next_action: str  # "tools" | "act" | "reflect" | "end"
