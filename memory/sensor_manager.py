"""
Sensor Data Manager — read sensors, store to DB, query history
"""
import logging
from datetime import datetime, timedelta, timezone

from memory.database import get_conn
from perception.sensors import SensorReader

logger = logging.getLogger("SmartHome.sensors")

_reader = SensorReader()


def read_and_store() -> dict:
    """Read sensors and store one row to DB. Returns the reading."""
    data = _reader.read_all()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO sensor_readings (temperature, humidity, light_level) "
            "VALUES (?, ?, ?)",
            (data["temperature"], data["humidity"], data["light_lux"]),
        )
    return data


def get_latest() -> dict:
    """Get the most recent sensor reading from DB"""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM sensor_readings ORDER BY id DESC LIMIT 1"
        ).fetchone()
    if row is None:
        return _reader._read_mock()
    return {
        "temperature": row["temperature"],
        "humidity": row["humidity"],
        "light_lux": row["light_level"],
        "fire_detected": False,
        "comfort_score": _calc_comfort(row["temperature"], row["humidity"]),
        "timestamp": row["timestamp"],
    }


def get_history(hours: int = 24, step_seconds: int = 300) -> list[dict]:
    """
    Query sensor history with downsampling.
    step_seconds: minimum gap between returned rows.
    """
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT timestamp, temperature, humidity, light_level "
            "FROM sensor_readings WHERE timestamp >= ? ORDER BY timestamp",
            (since,),
        ).fetchall()

    if not rows:
        return []

    result = []
    last_ts = None
    for row in rows:
        ts = row["timestamp"]
        if last_ts is not None:
            dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            last_dt = datetime.strptime(last_ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            if (dt - last_dt).total_seconds() < step_seconds:
                continue
        result.append({
            "timestamp": ts,
            "temperature": row["temperature"],
            "humidity": row["humidity"],
            "light_level": row["light_level"],
        })
        last_ts = ts

    return result


def _calc_comfort(temp: float, humidity: float) -> float:
    """Calculate comfort score 0-1 from temperature and humidity"""
    # Optimal: temp 20-26, humidity 40-60
    temp_score = 1.0 - min(abs(temp - 23) / 10, 1.0)
    humi_score = 1.0 - min(abs(humidity - 50) / 30, 1.0)
    return round((temp_score * 0.6 + humi_score * 0.4), 2)
