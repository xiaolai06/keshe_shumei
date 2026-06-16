"""
Agent Node — Decide（决策路由）
根据 LLM 输出和当前状态决定下一步
"""
import logging
from agent.state import PetState

logger = logging.getLogger("SmartHome")


def decide_node(state: PetState) -> dict:
    """
    决策节点：判断是否需要工具调用、反思、或直接输出。
    当前简化实现：直接路由到 act。
    """
    # 检查交互次数，决定是否需要反思
    messages = state.get("messages", [])
    interaction_count = len([m for m in messages
                            if (hasattr(m, "content") and m.type == "human")
                            or (isinstance(m, dict) and m.get("role") == "user")])

    import config
    if interaction_count > 0 and interaction_count % config.REFLECT_THRESHOLD == 0:
        logger.debug("Decide: routing to reflect (interaction=%d)", interaction_count)
        return {"next_action": "reflect"}

    logger.debug("Decide: routing to act")
    return {"next_action": "act"}


def route_decision(state: PetState) -> str:
    """条件路由函数，用于 LangGraph 的 conditional_edges"""
    return state.get("next_action", "act")
