"""
Agent Node — Recall（记忆检索）
从记忆系统检索相关记忆
"""
import logging
from agent.state import PetState

logger = logging.getLogger("SmartHome")


def recall_node(state: PetState) -> dict:
    """
    记忆检索节点：根据用户输入检索相关记忆。
    """
    messages = state.get("messages", [])
    # 取最后一条用户消息作为查询
    query = ""
    for msg in reversed(messages):
        if hasattr(msg, "content") and msg.type == "human":
            query = msg.content
            break
        elif isinstance(msg, dict) and msg.get("role") == "user":
            query = msg.get("content", "")
            break

    memories = []
    if query:
        try:
            from memory.manager import MemoryManager
            mm = MemoryManager()
            memories = mm.recall(query, top_k=5)
        except Exception as e:
            logger.debug("Memory recall failed (expected if no memories yet): %s", e)

    # 也获取最近上下文作为工作记忆
    recent = []
    try:
        recent = mm.get_recent_context(n=5)
    except Exception:
        pass

    all_memories = memories + recent
    logger.debug("Recall: %d memories retrieved", len(all_memories))
    return {"recalled_memories": all_memories}
