"""
Tool — 记忆管理
供 Agent 调用：存储/检索记忆
"""
import logging
from memory.manager import MemoryManager

logger = logging.getLogger("SmartHome")
_memo = MemoryManager()


def save_memory(content: str, importance: int = 5) -> dict:
    """存入一条长期记忆"""
    _memo.store(content, importance)
    return {"success": True, "content": content, "importance": importance}


def search_memory(query: str, top_k: int = 5) -> list:
    """语义搜索记忆"""
    return _memo.recall(query, top_k)
