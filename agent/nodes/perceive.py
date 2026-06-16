"""
Agent Node — Perceive（感知）
合并传感器数据、当前时间、语音输入到 state
"""
import logging
from datetime import datetime
from agent.state import PetState

logger = logging.getLogger("SmartHome")


def perceive_node(state: PetState) -> dict:
    """
    感知节点：读取当前环境数据和系统时间，合并到 state。
    如果 state 中已有 sensor_data（由 web 层传入），则直接使用。
    """
    sensor = state.get("sensor_data", {})
    if not sensor:
        # 从 sensor_manager 获取最新数据
        try:
            from memory.sensor_manager import get_latest
            latest = get_latest()
            sensor = {
                "temp": latest.get("temperature", 25.0),
                "humidity": latest.get("humidity", 50.0),
                "light": latest.get("light_level", 0),
                "comfort": latest.get("comfort_score", 0.7),
            }
        except Exception:
            sensor = {"temp": 25.0, "humidity": 50.0, "light": 0, "comfort": 0.7}

    # 注入当前时间信息
    now = datetime.now()
    sensor.setdefault("datetime", now.strftime("%Y-%m-%d %H:%M"))
    sensor.setdefault("hour", now.hour)

    voice = state.get("voice_text")
    image = state.get("image_desc")

    logger.debug("Perceive: temp=%.1f, time=%s, voice=%s, image=%s",
                 sensor.get("temp", 0), sensor.get("datetime", "?"),
                 bool(voice), bool(image))

    return {"sensor_data": sensor}
