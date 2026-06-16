"""
Tool — 摄像头控制
供 Agent 调用：拍照/场景分析
"""
import logging
import time
from pathlib import Path

import config

logger = logging.getLogger("SmartHome")


def take_photo() -> dict:
    """拍照并保存"""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return {"success": False, "error": "摄像头未连接"}
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return {"success": False, "error": "拍照失败"}

        config.SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        path = config.SNAPSHOTS_DIR / f"snap_{ts}.jpg"
        cv2.imwrite(str(path), frame)
        return {"success": True, "path": str(path), "timestamp": ts}
    except ImportError:
        return {"success": False, "error": "OpenCV 未安装"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def analyze_scene(description: str = "") -> str:
    """分析场景（用 LLM 描述）"""
    try:
        from agent.llm_client import get_llm
        llm = get_llm()
        return llm.chat([
            {"role": "system", "content": "你是桌宠小派的视觉系统。用一句可爱的话描述你看到的场景。"},
            {"role": "user", "content": description or "摄像头拍到了什么？"},
        ], max_tokens=100)
    except Exception:
        return "我看到了一些东西，但说不清楚~"
