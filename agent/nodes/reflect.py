"""
Agent Node — Reflect（反思）
定期总结近期记忆，写入长期记忆
"""
import logging
from agent.state import PetState

logger = logging.getLogger("SmartHome")


def reflect_node(state: PetState) -> dict:
    """
    反思节点：总结近期交互，提取重要信息存入长期记忆。
    """
    try:
        from memory.manager import MemoryManager
        mm = MemoryManager()

        # 获取最近上下文
        recent = mm.get_recent_context(n=20)
        if recent:
            mm.reflect(recent)
            logger.info("Reflect: summarized %d recent interactions", len(recent))
        else:
            logger.debug("Reflect: no recent interactions to summarize")
    except Exception as e:
        logger.warning("Reflect failed: %s", e)

    return {}
