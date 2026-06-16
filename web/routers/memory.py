"""
Memory API — 记忆查询接口
GET /api/memory         — 分页查询记忆
GET /api/memory/search  — 语义搜索
"""
import logging
from fastapi import APIRouter, Query
from memory.database import get_conn
from memory.manager import MemoryManager

router = APIRouter()
logger = logging.getLogger("SmartHome")
_memo = MemoryManager()


@router.get("/memory")
async def list_memories(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """分页获取长期记忆 + 短期摘要"""
    offset = (page - 1) * limit

    long_term = []
    try:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT id, category, content, importance, created_at FROM long_term_memory ORDER BY id DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            for row in rows:
                long_term.append({
                    "id": row["id"],
                    "category": row["category"],
                    "content": row["content"],
                    "importance": row["importance"],
                    "created_at": row["created_at"],
                })
    except Exception as e:
        logger.error("List memories error: %s", e)

    short_term = _memo.get_short_term(days=7)

    return {
        "success": True,
        "data": {
            "long_term": long_term,
            "short_term": short_term,
        },
    }


@router.get("/memory/search")
async def search_memories(q: str = Query("", min_length=0)):
    """搜索记忆"""
    if not q.strip():
        return {"success": True, "data": []}
    results = _memo.recall(q, top_k=10)
    return {"success": True, "data": results}
