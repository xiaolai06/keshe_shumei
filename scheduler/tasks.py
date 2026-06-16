"""
Scheduler Tasks — 定期任务
定期反思、传感器摘要、短期记忆整理
"""
import logging
from datetime import datetime, timezone

from memory.database import get_conn

logger = logging.getLogger("SmartHome")


def daily_summary():
    """每日短期记忆摘要"""
    try:
        with get_conn() as conn:
            # 统计今日交互
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            stats = conn.execute(
                "SELECT COUNT(*) as cnt FROM interactions WHERE date(timestamp) = date('now')"
            ).fetchone()

            # 温度范围
            temp = conn.execute(
                "SELECT MIN(temperature) as tmin, MAX(temperature) as tmax FROM sensor_readings WHERE date(timestamp) = date('now')"
            ).fetchone()

            # 提取话题（简单：取用户输入关键词）
            topics_row = conn.execute(
                "SELECT user_input FROM interactions WHERE date(timestamp) = date('now') ORDER BY id DESC LIMIT 10"
            ).fetchall()
            topics = "日常对话"
            if topics_row:
                inputs = [r["user_input"][:20] for r in topics_row if r["user_input"]]
                topics = "、".join(inputs[:3]) if inputs else "日常对话"

            tmin = round(temp["tmin"], 1) if temp and temp["tmin"] else 22
            tmax = round(temp["tmax"], 1) if temp and temp["tmax"] else 26
            cnt = stats["cnt"] if stats else 0

            conn.execute(
                "INSERT OR REPLACE INTO short_term_memory (date, summary, interaction_count, temp_range, topics) VALUES (?, ?, ?, ?, ?)",
                (today, f"今日交互 {cnt} 次", cnt, f"{tmin}~{tmax}°C", topics),
            )
        logger.info("Daily summary: %d interactions, %s~%s°C", cnt, tmin, tmax)
    except Exception as e:
        logger.error("Daily summary failed: %s", e)


def log_mood(mood: str, score: float, factors: dict | None = None):
    """记录情绪日志"""
    try:
        import json
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO mood_log (mood, score, factors) VALUES (?, ?, ?)",
                (mood, score, json.dumps(factors or {})),
            )
    except Exception as e:
        logger.debug("Log mood failed: %s", e)
