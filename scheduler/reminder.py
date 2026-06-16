"""
Scheduler — 提醒调度器
APScheduler 定时/周期/条件提醒
"""
import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger("SmartHome")


def _default_callback(job_id: str, content: str):
    """提醒触发时的默认回调：记录日志 + 更新 DB"""
    logger.info("⏰ 提醒触发 [%s]: %s", job_id, content)
    try:
        from memory.database import get_conn
        with get_conn() as conn:
            conn.execute(
                "UPDATE reminders SET is_active = 0 WHERE id = ?",
                (int(job_id.replace("reminder-", "")),),
            )
    except Exception as e:
        logger.error("Failed to deactivate reminder %s: %s", job_id, e)


class ReminderScheduler:
    """提醒调度器"""

    def __init__(self):
        self._scheduler = BackgroundScheduler()
        self._jobs: dict[str, dict] = {}

    def start(self):
        """启动调度器"""
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("APScheduler started")

    def add_once(self, job_id: str, trigger_time, callback=None):
        """添加一次性提醒"""
        cb = callback or (lambda: _default_callback(job_id, self._jobs.get(job_id, {}).get("content", "")))
        trigger = DateTrigger(run_date=trigger_time)
        self._scheduler.add_job(cb, trigger, id=job_id, replace_existing=True)
        self._jobs[job_id] = {"type": "once", "trigger": str(trigger_time)}
        logger.info("Added once reminder: %s at %s", job_id, trigger_time)

    def add_cron(self, job_id: str, cron_expr: str, callback=None):
        """添加周期提醒（cron 表达式，如 '0 8 * * *'）"""
        cb = callback or (lambda: _default_callback(job_id, self._jobs.get(job_id, {}).get("content", "")))
        parts = cron_expr.strip().split()
        if len(parts) == 5:
            trigger = CronTrigger(
                minute=parts[0], hour=parts[1],
                day=parts[2], month=parts[3], day_of_week=parts[4],
            )
        else:
            logger.warning("Invalid cron expr: %s, falling back to hourly", cron_expr)
            trigger = CronTrigger(minute=0)
        self._scheduler.add_job(cb, trigger, id=job_id, replace_existing=True)
        self._jobs[job_id] = {"type": "cron", "cron": cron_expr}
        logger.info("Added cron reminder: %s [%s]", job_id, cron_expr)

    def add_interval(self, job_id: str, seconds: int, callback=None):
        """添加定时间隔任务"""
        cb = callback or (lambda: _default_callback(job_id, self._jobs.get(job_id, {}).get("content", "")))
        trigger = IntervalTrigger(seconds=seconds)
        self._scheduler.add_job(cb, trigger, id=job_id, replace_existing=True)
        self._jobs[job_id] = {"type": "interval", "seconds": seconds}
        logger.info("Added interval reminder: %s every %ds", job_id, seconds)

    def remove(self, job_id: str):
        """移除提醒"""
        try:
            self._scheduler.remove_job(job_id)
        except Exception:
            pass
        self._jobs.pop(job_id, None)
        logger.info("Removed reminder: %s", job_id)

    def list_jobs(self) -> list:
        """返回所有活跃任务"""
        return [{"id": k, **v} for k, v in self._jobs.items()]

    def shutdown(self):
        """关闭调度器"""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("APScheduler stopped")
