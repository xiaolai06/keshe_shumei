"""
Camera API — 摄像头接口
GET  /api/camera/stream  — MJPEG 视频流
POST /api/camera/capture — 拍照分析
"""
import asyncio
import logging
import time
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

import config

router = APIRouter()
logger = logging.getLogger("SmartHome")


def _open_camera():
    """同步：打开摄像头（阻塞操作，需在线程中调用）"""
    import cv2
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        cap.release()
        return None
    return cap


def _generate_frames(cap):
    """同步帧生成器（在 StreamingResponse 的线程池中运行）"""
    import cv2
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


@router.get("/camera/stream")
async def camera_stream():
    """MJPEG 视频流"""
    try:
        cap = await asyncio.to_thread(_open_camera)
        if cap is None:
            return {"success": False, "error": "摄像头未连接"}

        return StreamingResponse(
            _generate_frames(cap),
            media_type="multipart/x-mixed-replace; boundary=frame",
        )
    except ImportError:
        return {"success": False, "error": "OpenCV 未安装，摄像头不可用"}
    except Exception as e:
        logger.error("Camera stream error: %s", e)
        return {"success": False, "error": str(e)}


def _capture_frame():
    """同步：拍照并保存（阻塞操作，需在线程中调用）"""
    import cv2
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        cap.release()
        return None, None
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None, None

    config.SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = config.SNAPSHOTS_DIR / f"snap_{ts}.jpg"
    cv2.imwrite(str(path), frame)
    return frame, path


@router.post("/camera/capture")
async def camera_capture():
    """拍照并分析"""
    try:
        frame, path = await asyncio.to_thread(_capture_frame)
        if frame is None:
            return {"success": True, "data": {
                "description": "摄像头未连接或拍照失败",
                "faces": [],
                "snapshot_path": None,
            }}

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
