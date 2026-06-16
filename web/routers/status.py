"""
Status / Evolution API — 状态和进化接口
GET /api/status            — 当前状态
GET /api/evolution         — 进化信息
GET /api/evolution/history — 进化历史
"""
import json
import logging
from datetime import datetime
from fastapi import APIRouter
from memory.database import get_conn

router = APIRouter()
logger = logging.getLogger("SmartHome")


@router.get("/status")
async def get_status():
    """获取桌宠当前状态"""
    try:
        with get_conn() as conn:
            evo = conn.execute("SELECT * FROM evolution_state WHERE id = 1").fetchone()
            mood_row = conn.execute(
                "SELECT mood FROM mood_log ORDER BY id DESC LIMIT 1"
            ).fetchone()
            interactions = conn.execute("SELECT COUNT(*) as cnt FROM interactions").fetchone()
            first = conn.execute(
                "SELECT timestamp FROM interactions ORDER BY id ASC LIMIT 1"
            ).fetchone()

        mood = mood_row["mood"] if mood_row else (evo["mood"] if evo else "happy")
        total = interactions["cnt"] if interactions else 0

        days = 1
        if first and first["timestamp"]:
            try:
                created = datetime.fromisoformat(first["timestamp"])
                days = max(1, (datetime.utcnow() - created).days)
            except (ValueError, TypeError):
                pass

        return {
            "success": True,
            "data": {
                "name": evo["name"] if evo else "智居物语",
                "mood": mood,
                "level": evo["level"] if evo else 1,
                "exp": evo["exp"] if evo else 0,
                "days_alive": days,
                "total_interactions": total,
            },
        }
    except Exception as e:
        logger.error("Get status error: %s", e)
        return {
            "success": True,
            "data": {
                "name": "智居物语", "mood": "happy", "level": 1,
                "exp": 0, "days_alive": 1, "total_interactions": 0,
            },
        }


@router.get("/evolution")
async def get_evolution():
    """获取进化信息"""
    try:
        with get_conn() as conn:
            evo = conn.execute("SELECT personality FROM evolution_state WHERE id = 1").fetchone()

        personality = {"curiosity": 0.5, "friendliness": 0.5, "energy": 0.5}
        if evo and evo["personality"]:
            try:
                personality = json.loads(evo["personality"]) if isinstance(evo["personality"], str) else evo["personality"]
            except Exception:
                pass

        return {"success": True, "data": personality}
    except Exception as e:
        logger.error("Get evolution error: %s", e)
        return {"success": True, "data": {"curiosity": 0.5, "friendliness": 0.5, "energy": 0.5}}


@router.get("/evolution/history")
async def get_evolution_history(limit: int = 50):
    """获取进化历史（mood_log）"""
    try:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT mood, score, factors, timestamp FROM mood_log ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            history = [dict(row) for row in rows]
        return {"success": True, "data": history}
    except Exception as e:
        logger.error("Get evolution history error: %s", e)
        return {"success": True, "data": []}
