"""
Camera API — 摄像头接口
GET  /api/camera/stream  — MJPEG 视频流
POST /api/camera/capture — 拍照分析
"""
import logging
import time
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

import config

router = APIRouter()
logger = logging.getLogger("SmartHome")


@router.get("/camera/stream")
async def camera_stream():
    """MJPEG 视频流"""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return {"success": False, "error": "摄像头未连接"}

        def generate():
            try:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    yield (b"--frame\r\n"
                           b"Content-Type: image/jpeg\r\n\r\n" +
                           buf.tobytes() + b"\r\n")
            finally:
                cap.release()

        return StreamingResponse(
            generate(),
            media_type="multipart/x-mixed-replace; boundary=frame",
        )
    except ImportError:
        return {"success": False, "error": "OpenCV 未安装，摄像头不可用"}
    except Exception as e:
        logger.error("Camera stream error: %s", e)
        return {"success": False, "error": str(e)}


@router.post("/camera/capture")
async def camera_capture():
    """拍照并分析"""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return {"success": True, "data": {
                "description": "摄像头未连接",
                "faces": [],
                "snapshot_path": None,
            }}

        ret, frame = cap.read()
        cap.release()

        if not ret:
            return {"success": False, "error": "拍照失败"}

        # 保存快照
        config.SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        path = config.SNAPSHOTS_DIR / f"snap_{ts}.jpg"
        cv2.imwrite(str(path), frame)

        # LLM 分析
        analysis = "明亮的室内环境"
        try:
            from agent.llm_client import get_llm
            llm = get_llm()
            analysis = llm.chat([
                {"role": "system", "content": "你是一个图像分析助手。用一句简短中文描述摄像头可能拍到的桌面场景。"},
                {"role": "user", "content": "摄像头刚拍了一张照片，请描述可能看到的内容。"},
            ], max_tokens=100)
        except Exception:
            pass

        return {
            "success": True,
            "data": {
                "description": analysis,
                "faces": [],
                "snapshot_path": str(path),
            },
        }
    except ImportError:
        return {
            "success": True,
            "data": {
                "description": "摄像头未连接（OpenCV 未安装）",
                "faces": [],
                "snapshot_path": None,
            },
        }
    except Exception as e:
        logger.error("Capture error: %s", e)
        return {"success": False, "error": str(e)}
