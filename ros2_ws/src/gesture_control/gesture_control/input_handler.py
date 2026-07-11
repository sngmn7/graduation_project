# input_handler.py

import cv2
from config import FRAME_WIDTH, FRAME_HEIGHT

try:
    from picamera2 import Picamera2
    _HAS_PICAMERA2 = True
except Exception:
    _HAS_PICAMERA2 = False


class InputHandler:
    def __init__(self, source=0, width=FRAME_WIDTH, height=FRAME_HEIGHT):

        self.width = int(width)
        self.height = int(height)

        self._mode = None           # "picam2" or "cv2"
        self.cap = None             # for cv2
        self.picam2 = None          # for picamera2
        self._opened = False

        if isinstance(source, str):
            self._init_cv2(source)
            return

        self._init_cv2(source)

    def _init_picam2(self):
        try:
            self.picam2 = Picamera2()
            config = self.picam2.create_video_configuration(
                main={"size": (self.width, self.height), "format": "RGB888"}
            )
            self.picam2.configure(config)
            self.picam2.start()
            self._mode = "picam2"
            self._opened = True
        except Exception as e:
            print(f"?? Picamera2 횄횎짹창횊짯 쩍횉횈횖: {e}")
            self._opened = False

    def _init_cv2(self, source):
        pipeline = (
            "nvarguscamerasrc sensor-id=0 ! "
            "video/x-raw(memory:NVMM), width=1280, height=720, format=NV12, framerate=30/1 ! "
            "nvvidconv flip-method=0 ! "
            "video/x-raw, format=BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=BGR ! "
            "appsink drop=True"
        )

        self.cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

        if not self.cap.isOpened():
            print("CSI 카메라 열기 실패")
            self._opened = False
            self._mode = "cv2"
            return

        self._mode = "cv2"
        self._opened = True

    def is_opened(self):
        return self._opened

    def get_frame(self):
        """
        횉횗 횉횁쨌쨔?횙?쨩 ?횖쩐챤쩌짯 쨔횦횊짱(BGR).
        쩍횉횈횖 쩍횄 None.
        """
        if not self._opened:
            return None

        if self._mode == "picam2":
            try:
                # Picamera2쨈횂 RGB 쨔챔쩔짯?쨩 쨔횦횊짱 -> BGR쨌횓 쨘짱횊짱횉횠 OpenCV 횊짙횊짱
                frame_rgb = self.picam2.capture_array()
                if frame_rgb is None:
                    return None
                frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                #return frame_bgr
                return frame_rgb
            except Exception as e:
                print(f"?? Picamera2 횉횁쨌쨔?횙 횆쨍횄쨀 쩍횉횈횖: {e}")
                return None

        elif self._mode == "cv2":
            success, frame = self.cap.read()
            if not success:
                return None
            return frame

        return None

    def release(self):
        """
        횆쨍횄쨀 쨍짰쩌횘쩍쨘 횉횠횁짝
        """
        if self._mode == "picam2" and self.picam2 is not None:
            try:
                self.picam2.stop()
            except Exception:
                pass
            self.picam2 = None
            self._opened = False

        if self._mode == "cv2" and self.cap is not None:
            if self.cap.isOpened():
                self.cap.release()
            self.cap = None
            self._opened = False
