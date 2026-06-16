"""
Agent Node — Act（执行输出）
输出回复、更新情绪、控制 OLED/LED/蜂鸣器
环境异常时自动报警
"""
import logging
from agent.state import PetState

logger = logging.getLogger("SmartHome")

_MOOD_KEYWORDS = {
    "happy": ["开心", "高兴", "哈哈", "太好了", "不错", "~", "！"],
    "curious": ["？", "什么", "为什么", "怎么", "告诉我"],
    "sleepy": ["困", "睡觉", "休息", "晚安", "zzZ", "..."],
    "alert": ["注意", "小心", "危险", "警告", "温度过高"],
    "chatty": ["其实", "你知道吗", "说起来", "对了"],
    "calm": ["嗯", "好的", "平静", "安静"],
    "lonely": ["陪", "想念", "无聊", "一个人"],
}

# 环境异常阈值
_TEMP_HIGH = 32.0
_TEMP_LOW = 15.0
_HUMI_HIGH = 85.0
_HUMI_LOW = 25.0


def _infer_mood(reply: str, sensor: dict) -> str:
    """根据回复内容和环境推断情绪"""
    scores = {m: 0 for m in _MOOD_KEYWORDS}

    for mood, keywords in _MOOD_KEYWORDS.items():
        for kw in keywords:
            if kw in reply:
                scores[mood] += 1

    temp = sensor.get("temp", 25)
    if temp > _TEMP_HIGH:
        scores["alert"] += 2
    elif temp < _TEMP_LOW:
        scores["sleepy"] += 1
    elif 22 <= temp <= 26:
        scores["happy"] += 1

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "happy"


def _check_environment(sensor: dict) -> list[str]:
    """检查环境数据，返回异常列表"""
    alerts = []
    temp = sensor.get("temp")
    humidity = sensor.get("humidity")

    if temp is not None:
        if temp > _TEMP_HIGH:
            alerts.append(f"温度过高: {temp:.1f}°C (>{_TEMP_HIGH}°C)")
        elif temp < _TEMP_LOW:
            alerts.append(f"温度过低: {temp:.1f}°C (<{_TEMP_LOW}°C)")

    if humidity is not None:
        if humidity > _HUMI_HIGH:
            alerts.append(f"湿度过高: {humidity:.0f}% (>{_HUMI_HIGH}%)")
        elif humidity < _HUMI_LOW:
            alerts.append(f"湿度过低: {humidity:.0f}% (<{_HUMI_LOW}%)")

    return alerts


def _trigger_alerts(alerts: list[str], sensor: dict):
    """环境异常时触发蜂鸣器 + OLED 警告"""
    # 蜂鸣器响警报
    try:
        from hardware.buzzer import get_buzzer
        buzzer = get_buzzer()
        buzzer.alarm_sound()
    except Exception as e:
        logger.debug("Buzzer alert skipped: %s", e)

    # OLED 显示警告
    try:
        from hardware.oled import get_oled
        oled = get_oled()
        alert_text = alerts[0] if alerts else "环境异常"
        oled.show_text(f"⚠ {alert_text}")
    except Exception as e:
        logger.debug("OLED alert skipped: %s", e)

    logger.warning("环境异常: %s", "; ".join(alerts))


def act_node(state: PetState) -> dict:
    """执行节点：输出回复、更新情绪、控制硬件、检测环境异常"""
    messages = state.get("messages", [])
    sensor = state.get("sensor_data", {})

    # 获取最新 AI 回复
    reply = ""
    for msg in reversed(messages):
        if hasattr(msg, "content") and msg.type == "ai":
            reply = msg.content
            break
        elif isinstance(msg, dict) and msg.get("role") == "assistant":
            reply = msg.get("content", "")
            break

    # 推断情绪
    mood = _infer_mood(reply, sensor)

    # 记录交互到数据库
    try:
        from memory.database import get_conn
        user_input = ""
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.type == "human":
                user_input = msg.content
                break
            elif isinstance(msg, dict) and msg.get("role") == "user":
                user_input = msg.get("content", "")
                break

        # 根据 state 推断来源：有 voice_text 则为语音，否则为 web
        source = "voice" if state.get("voice_text") else "web"

        with get_conn() as conn:
            conn.execute(
                "INSERT INTO interactions (source, user_input, agent_reply, mood) VALUES (?, ?, ?, ?)",
                (source, user_input, reply, mood),
            )
    except Exception as e:
        logger.debug("Failed to log interaction: %s", e)

    # 映射情绪 → OLED 表情名
    oled_expression = {
        "happy": "开心", "curious": "好奇", "sleepy": "困倦",
        "alert": "警觉", "chatty": "健谈", "calm": "平静", "lonely": "孤独",
    }.get(mood, "默认")

    # ——— 驱动硬件输出（使用单例） ———

    try:
        from hardware.oled import get_oled
        oled = get_oled()
        oled.show_expression(oled_expression)
        if reply:
            oled.show_text(reply[:60])
    except Exception as e:
        logger.debug("OLED output skipped: %s", e)

    # ——— 环境异常检测 ———
    alerts = _check_environment(sensor)
    if alerts:
        _trigger_alerts(alerts, sensor)
        # 强制切换到 alert 情绪
        if mood != "alert":
            mood = "alert"
            oled_expression = "警觉"

    logger.debug("Act: mood=%s, oled=%s, alerts=%d", mood, oled_expression, len(alerts))
    return {
        "mood": mood,
        "oled_expression": oled_expression,
        "oled_text": reply[:20] if reply else "",
    }
