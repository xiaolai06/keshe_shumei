"""
Tool — 蜂鸣器控制
供 Agent 调用：播放提示音
"""
import logging

logger = logging.getLogger("SmartHome")


def play_buzzer(sound: str = "beep") -> dict:
    """播放蜂鸣器提示音"""
    try:
        from hardware.buzzer import Buzzer
        buzzer = Buzzer()
        if sound == "reminder":
            buzzer.reminder_sound()
        elif sound == "welcome":
            buzzer.welcome_sound()
        elif sound == "alarm":
            buzzer.alarm_sound()
        elif sound == "level_up":
            buzzer.level_up_sound()
        else:
            buzzer.beep()
        logger.debug("Buzzer: %s", sound)
        return {"success": True, "sound": sound}
    except Exception as e:
        logger.debug("Buzzer mock: %s", sound)
        return {"success": True, "sound": sound, "mock": True}
