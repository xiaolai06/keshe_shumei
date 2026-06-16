"""
Sensors API — 传感器数据接口
GET /api/sensors          — 最新传感器数据
GET /api/sensors/history  — 历史数据（支持降采样）
"""
from fastapi import APIRouter, Query

from memory.sensor_manager import get_latest, get_history

router = APIRouter()

_RANGE_MAP = {
    "1h":  (1,   10),
    "6h":  (6,   60),
    "24h": (24,  300),
    "7d":  (168, 1800),
}


@router.get("/sensors")
async def get_sensors():
    """返回最新传感器数据"""
    data = get_latest()
    return {"success": True, "data": data}


@router.get("/sensors/history")
async def get_sensor_history(range: str = Query("24h", pattern=r"^(1h|6h|24h|7d)$")):
    """返回降采样后的传感器历史"""
    hours, step = _RANGE_MAP.get(range, (24, 300))
    rows = get_history(hours=hours, step_seconds=step)
    return {
        "success": True,
        "data": rows,
        "meta": {"range": range, "step": step, "count": len(rows)},
    }
