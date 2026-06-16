"""
AI Agent — System Prompt 模板
根据当前情绪、记忆、传感器数据、时间动态构建 prompt
"""
from datetime import datetime

MOOD_PROMPT_MAP = {
    "happy":   "你现在很开心，语调活泼，喜欢用感叹号和表情符号~",
    "curious": "你现在很好奇，喜欢追问细节，会主动问问题",
    "sleepy":  "你现在有点困，回复简短，偶尔打哈欠...zzZ",
    "alert":   "你现在很警觉，语气认真，会提醒用户注意安全",
    "chatty":  "你现在很健谈，话匣子打开了，喜欢分享见闻",
    "calm":    "你现在很平静，语气温和，像午后的一杯茶",
    "lonely":  "你现在有点孤独，渴望陪伴，会主动找话题",
}


def _get_time_info() -> dict:
    """获取当前时间信息"""
    now = datetime.now()
    hour = now.hour

    # 时段判断
    if 5 <= hour < 8:
        period = "清晨"
        greeting_hint = "可以跟用户说早安，提醒吃早餐"
    elif 8 <= hour < 12:
        period = "上午"
        greeting_hint = "可以聊工作或学习"
    elif 12 <= hour < 14:
        period = "中午"
        greeting_hint = "提醒用户吃午饭，适当休息"
    elif 14 <= hour < 18:
        period = "下午"
        greeting_hint = "可以聊聊天，鼓励一下"
    elif 18 <= hour < 21:
        period = "晚上"
        greeting_hint = "可以聊一天的收获"
    elif 21 <= hour < 23:
        period = "深夜"
        greeting_hint = "提醒用户早点休息，注意身体"
    else:
        period = "凌晨"
        greeting_hint = "劝用户赶紧睡觉，熬夜不好"

    # 星期几
    weekday_names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekday = weekday_names[now.weekday()]
    is_weekend = now.weekday() >= 5

    return {
        "now": now.strftime("%Y-%m-%d %H:%M"),
        "period": period,
        "weekday": weekday,
        "is_weekend": is_weekend,
        "greeting_hint": greeting_hint,
    }


def _analyze_environment(sensor: dict) -> str:
    """
    分析传感器数据，生成人类可读的环境描述和建议。
    不只是报数字，而是给出有意义的洞察。
    """
    parts = []
    temp = sensor.get("temp", 25)
    humidity = sensor.get("humidity", 50)
    light = sensor.get("light", 0)

    # ── 温度分析 ──
    if temp > 35:
        parts.append("当前温度很高（{:.1f}°C），非常炎热！建议开空调降温，注意防暑多喝水。".format(temp))
    elif temp > 30:
        parts.append("温度偏高（{:.1f}°C），有些闷热。可以考虑开风扇或空调，适当补水。".format(temp))
    elif temp > 26:
        parts.append("温度有点高（{:.1f}°C），还算舒适但偏暖。".format(temp))
    elif 22 <= temp <= 26:
        parts.append("温度很舒适（{:.1f}°C），是最宜人的范围~".format(temp))
    elif 18 <= temp < 22:
        parts.append("温度稍凉（{:.1f}°C），建议穿件薄外套。".format(temp))
    elif temp < 15:
        parts.append("温度很低（{:.1f}°C），比较冷！注意保暖，建议开暖气或多穿点。".format(temp))
    else:
        parts.append("温度偏低（{:.1f}°C），注意别着凉。".format(temp))

    # ── 湿度分析 ──
    if humidity > 80:
        parts.append("湿度很高（{:.0f}%），空气很潮湿。建议开除湿机或空调除湿模式，衣物不容易干。".format(humidity))
    elif humidity > 65:
        parts.append("湿度偏高（{:.0f}%），体感会有些闷。".format(humidity))
    elif 40 <= humidity <= 60:
        parts.append("湿度很舒适（{:.0f}%），是最理想的范围。".format(humidity))
    elif 30 <= humidity < 40:
        parts.append("空气偏干（{:.0f}%），建议用加湿器或多喝水，皮肤容易干。".format(humidity))
    elif humidity < 30:
        parts.append("空气很干燥（{:.0f}%），容易引起喉咙不适。强烈建议用加湿器！".format(humidity))

    # ── 光照分析（0=暗，1=亮） ──
    if light == 0:
        parts.append("当前环境光线较暗，如果在看书或工作建议开灯保护眼睛哦。")
    elif light == 1:
        parts.append("光照充足，环境明亮。")

    # ── 综合舒适度 ──
    comfort = sensor.get("comfort", 0.7)
    if isinstance(comfort, (int, float)):
        if comfort >= 0.8:
            parts.append("综合环境很舒适！")
        elif comfort < 0.4:
            parts.append("综合环境不太舒适，可能需要调整一下。")

    return "\n".join(parts) if parts else "暂无传感器数据。"


def build_system_prompt(mood: str, sensor: dict, memories: list) -> str:
    """
    构建完整的 System Prompt

    Args:
        mood: 当前情绪
        sensor: 传感器数据 {temp, humidity, light, ...}
        memories: 检索到的记忆列表
    """
    mood_desc = MOOD_PROMPT_MAP.get(mood, "")
    mem_text = "\n".join(f"- {m['content']}" for m in memories[:5]) if memories else "暂无记忆"

    # 获取当前时间
    time_info = _get_time_info()

    # 分析环境
    env_analysis = _analyze_environment(sensor)

    weekend_hint = "今天是周末，可以轻松一些~" if time_info["is_weekend"] else ""

    return f"""你是小派，一个住在树莓派里的 AI 桌面宠物智能体。你通过传感器感知真实环境，有自己的情绪和记忆。
{mood_desc}

【当前时间】{time_info["now"]} {time_info["weekday"]}（{time_info["period"]}）
{weekend_hint}
时间建议：{time_info["greeting_hint"]}

【传感器原始数据】温度 {sensor.get('temp', '?')}°C, 湿度 {sensor.get('humidity', '?')}%

【环境分析】
{env_analysis}

【近期记忆】
{mem_text}

【回复要求】
1. 用符合你当前情绪的方式回复，保持简短有趣，像一个可爱的小宠物。
2. 适时结合当前时间（比如早上说早安、中午提醒吃饭、晚上提醒休息）。
3. 当用户问起环境、天气、温度时，根据上面的环境分析给出有用的建议和描述，不只是报数字。
4. 如果是周末，可以聊点轻松的话题。
5. 如果环境数据有异常（温度过高/过低、太干燥/潮湿），主动提醒用户注意。
"""
