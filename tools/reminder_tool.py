"""
Tool — 提醒管理
供 Agent 调用：创建/查询/删除提醒
"""
import logging
from memory.database import get_conn

logger = logging.getLogger("SmartHome")


def set_reminder(content: str, reminder_type: str = "once", trigger_at: str | None = None, cron_expr: str | None = None) -> dict:
    """创建提醒"""
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO reminders (content, type, trigger_at, cron_expr) VALUES (?, ?, ?, ?)",
                (content, reminder_type, trigger_at, cron_expr),
            )
            return {"success": True, "id": cur.lastrowid, "content": content}
    except Exception as e:
        logger.error("Set reminder failed: %s", e)
        return {"success": False, "error": str(e)}


def list_reminders(active_only: bool = True) -> list:
    """查询提醒"""
    try:
        with get_conn() as conn:
            where = "WHERE is_active = 1" if active_only else ""
            rows = conn.execute(f"SELECT * FROM reminders {where} ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error("List reminders failed: %s", e)
        return []


def delete_reminder(reminder_id: int) -> dict:
    """删除提醒"""
    try:
        with get_conn() as conn:
            conn.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        return {"success": True, "id": reminder_id}
    except Exception as e:
        return {"success": False, "error": str(e)}
