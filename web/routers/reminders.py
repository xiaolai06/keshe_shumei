"""
Reminders API — 提醒管理接口
GET    /api/reminders          — 获取提醒列表
POST   /api/reminders          — 创建提醒
PUT    /api/reminders/{id}     — 更新提醒
DELETE /api/reminders/{id}     — 删除提醒
"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from memory.database import get_conn

router = APIRouter()
logger = logging.getLogger("SmartHome")


def _get_scheduler():
    """延迟获取调度器实例（避免循环导入）"""
    from web.app import reminder_scheduler
    return reminder_scheduler


class ReminderCreate(BaseModel):
    type: str = Field(default="once", description="once/cron/condition")
    content: str
    trigger_at: str | None = None
    cron_expr: str | None = None
    condition: str | None = None


class ReminderUpdate(BaseModel):
    content: str | None = None
    type: str | None = None
    trigger_at: str | None = None
    cron_expr: str | None = None
    is_active: bool | None = None


@router.get("/reminders")
async def list_reminders():
    """获取所有提醒"""
    try:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM reminders ORDER BY is_active DESC, created_at DESC"
            ).fetchall()
            reminders = [dict(row) for row in rows]
        return {"success": True, "data": reminders}
    except Exception as e:
        logger.error("List reminders error: %s", e)
        return {"success": True, "data": []}


@router.post("/reminders")
async def create_reminder(req: ReminderCreate):
    """创建提醒"""
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO reminders (content, type, trigger_at, cron_expr, condition) VALUES (?, ?, ?, ?, ?)",
                (req.content, req.type, req.trigger_at, req.cron_expr, req.condition),
            )
            reminder_id = cur.lastrowid

        # 注册到调度器
        job_id = f"reminder-{reminder_id}"
        scheduler = _get_scheduler()
        if req.type == "once" and req.trigger_at:
            trigger_time = datetime.fromisoformat(req.trigger_at)
            scheduler.add_once(
                job_id, trigger_time,
                callback=lambda rid=reminder_id, c=req.content: _fire(rid, c),
            )
        elif req.type == "cron" and req.cron_expr:
            scheduler.add_cron(
                job_id, req.cron_expr,
                callback=lambda rid=reminder_id, c=req.content: _fire(rid, c),
            )

        return {
            "success": True,
            "data": {
                "id": reminder_id,
                "content": req.content,
                "type": req.type,
                "trigger_at": req.trigger_at,
                "cron_expr": req.cron_expr,
                "is_active": True,
            },
        }
    except Exception as e:
        logger.error("Create reminder error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/reminders/{reminder_id}")
async def update_reminder(reminder_id: int, req: ReminderUpdate):
    """更新提醒"""
    try:
        fields = []
        params = []
        if req.content is not None:
            fields.append("content = ?")
            params.append(req.content)
        if req.type is not None:
            fields.append("type = ?")
            params.append(req.type)
        if req.trigger_at is not None:
            fields.append("trigger_at = ?")
            params.append(req.trigger_at)
        if req.cron_expr is not None:
            fields.append("cron_expr = ?")
            params.append(req.cron_expr)
        if req.is_active is not None:
            fields.append("is_active = ?")
            params.append(req.is_active)

        if not fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        params.append(reminder_id)
        with get_conn() as conn:
            conn.execute(
                f"UPDATE reminders SET {', '.join(fields)} WHERE id = ?",
                params,
            )
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Update reminder error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/reminders/{reminder_id}")
async def delete_reminder(reminder_id: int):
    """删除提醒"""
    try:
        with get_conn() as conn:
            conn.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        # 从调度器移除
        _get_scheduler().remove(f"reminder-{reminder_id}")
        return {"success": True}
    except Exception as e:
        logger.error("Delete reminder error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


def _fire(reminder_id: int, content: str):
    """提醒触发回调"""
    logger.info("⏰ 提醒触发 [%d]: %s", reminder_id, content)
    try:
        with get_conn() as conn:
            conn.execute("UPDATE reminders SET is_active = 0 WHERE id = ?", (reminder_id,))
    except Exception as e:
        logger.error("Failed to deactivate reminder %d: %s", reminder_id, e)
