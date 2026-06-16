"""
Perception — 摄像头捕获
USB 摄像头 + OpenCV
"""
# TODO: 接入 OpenCV
# import cv2

HARDWARE_AVAILABLE = False


class CameraCapture:
    """摄像头捕获接口"""

    def __init__(self, device_id: int = 0, width: int = 640, height: int = 480):
        self.device_id = device_id
        self.width = width
        self.height = height
        self._cap = None

    def start(self):
        """打开摄像头"""
        # TODO: self._cap = cv2.VideoCapture(self.device_id)
        pass

    def capture_frame(self):
        """捕获一帧图像"""
        # TODO: ret, frame = self._cap.read()
        return None

    def stop(self):
        """释放摄像头"""
        # TODO: self._cap.release()
        pass

    def get_mjpeg_frame(self):
        """获取 MJPEG 编码帧（用于 Web 流）"""
        # TODO: cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        return None
