"""
智居物语 — FastAPI Web Application
"""
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import config
from web.routers import chat, sensors, camera, memory, reminders, status, settings, voice
from scheduler.reminder import ReminderScheduler

logger = logging.getLogger("SmartHome")

STATIC_DIR = Path(__file__).parent / "static"

_stop_event = threading.Event()
_sensor_thread: threading.Thread | None = None
reminder_scheduler = ReminderScheduler()


def _sensor_poll_loop():
    """Background thread: poll sensors every SENSOR_POLL_INTERVAL seconds"""
    from memory.sensor_manager import read_and_store
    while not _stop_event.is_set():
        try:
            read_and_store()
        except Exception:
            logger.exception("Sensor read failed")
        _stop_event.wait(timeout=config.SENSOR_POLL_INTERVAL)


def _load_existing_reminders():
    """启动时从 DB 加载所有活跃提醒到调度器"""
    from memory.database import get_conn
    try:
        with get_conn() as conn:
            rows = conn.execute("SELECT * FROM reminders WHERE is_active = 1").fetchall()
        for row in rows:
            r = dict(row)
            job_id = f"reminder-{r['id']}"
            if r["type"] == "once" and r["trigger_at"]:
                trigger_time = datetime.fromisoformat(r["trigger_at"])
                if trigger_time > datetime.now():
                    reminder_scheduler.add_once(
                        job_id, trigger_time,
                        callback=lambda rid=r["id"], c=r["content"]: _on_reminder_trigger(rid, c),
                    )
            elif r["type"] == "cron" and r["cron_expr"]:
                reminder_scheduler.add_cron(
                    job_id, r["cron_expr"],
                    callback=lambda rid=r["id"], c=r["content"]: _on_reminder_trigger(rid, c),
                )
        logger.info("Loaded %d active reminders", len(rows))
    except Exception as e:
        logger.error("Failed to load reminders: %s", e)


def _on_reminder_trigger(reminder_id: int, content: str):
    """提醒触发回调"""
    logger.info("⏰ 提醒触发 [%d]: %s", reminder_id, content)
    # 标记为已触发
    from memory.database import get_conn
    try:
        with get_conn() as conn:
            conn.execute("UPDATE reminders SET is_active = 0 WHERE id = ?", (reminder_id,))
    except Exception as e:
        logger.error("Failed to deactivate reminder %d: %s", reminder_id, e)


@asynccontextmanager
async def lifespan(app):
    """Application lifespan: startup / shutdown."""
    global _sensor_thread

    from memory.database import init_db
    init_db()
    logger.info("Database initialized")

    # 加载持久化的配置
    config.load_llm_config()
    logger.info("LLM config loaded: model=%s", config.LLM_MODEL)

    # 传感器轮询
    if config.SERVICE_SENSOR_ENABLED:
        _stop_event.clear()
        _sensor_thread = threading.Thread(target=_sensor_poll_loop, daemon=True, name="sensor-poll")
        _sensor_thread.start()
        logger.info("Sensor polling started (interval=%ds)", config.SENSOR_POLL_INTERVAL)
    else:
        logger.info("Sensor polling disabled (SERVICE_SENSOR_ENABLED=False)")

    # 提醒调度器
    if config.SERVICE_REMINDER_ENABLED:
        reminder_scheduler.start()
        _load_existing_reminders()
        logger.info("Reminder scheduler started")
    else:
        logger.info("Reminder scheduler disabled (SERVICE_REMINDER_ENABLED=False)")

    # 语音监听（VAD 持续监听麦克风）
    if config.SERVICE_VOICE_ENABLED:
        try:
            from perception.listener import get_listener
            voice_listener = get_listener()
            voice_listener.start()
            logger.info("Voice listener started (threshold=%d)", config.VOICE_ENERGY_THRESHOLD)
        except Exception as e:
            logger.warning("Voice listener failed to start: %s", e)
    else:
        logger.info("Voice listener disabled (SERVICE_VOICE_ENABLED=False)")

    logger.info("Web service ready: http://%s:%d", config.WEB_HOST, config.WEB_PORT)
    yield

    # 关闭语音监听
    if config.SERVICE_VOICE_ENABLED:
        try:
            from perception.listener import get_listener
            get_listener().stop()
        except Exception:
            pass

    if config.SERVICE_REMINDER_ENABLED:
        reminder_scheduler.shutdown()
    _stop_event.set()
    if _sensor_thread:
        _sensor_thread.join(timeout=5)

    # 释放所有 GPIO 资源
    try:
        import RPi.GPIO as GPIO
        GPIO.cleanup()
        logger.info("GPIO cleanup done")
    except Exception:
        pass

    logger.info("System shutdown complete")


app = FastAPI(title="智居物语", version="0.1.0", lifespan=lifespan)

# ── Mount routers ──
app.include_router(chat.router,       prefix="/api", tags=["chat"])
app.include_router(sensors.router,    prefix="/api", tags=["sensors"])
app.include_router(camera.router,     prefix="/api", tags=["camera"])
app.include_router(memory.router,     prefix="/api", tags=["memory"])
app.include_router(reminders.router,  prefix="/api", tags=["reminders"])
app.include_router(status.router,     prefix="/api", tags=["status"])
app.include_router(settings.router,   prefix="/api", tags=["settings"])
app.include_router(voice.router,      prefix="/api", tags=["voice"])

# ── Static files ──
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=FileResponse)
async def index():
    """Serve the main dashboard page."""
    return FileResponse(str(STATIC_DIR / "index.html"))
