# config.py
# 각종 설정 값 존재하는 파일

# 카메라 설정
FRAME_WIDTH = 640  # 캡처할 프레임 너비
FRAME_HEIGHT = 480  # 캡처할 프레임 높이

# YOLO 설정
YOLO_MODEL_PATH = "yolov8n"  # YOLO 가중치 파일 경로
YOLO_FURNITURE_CLASSES = [56, 59]  # COCO 기준 chair=56, bed=59
YOLO_CONF_THRESHOLD = 0.5  # 탐지 신뢰도 임계값
YOLO_IOU_THRESHOLD = 0.4  # NMS(IOU) 임계값

# Gesture Recognizer 경로 설정
GESTURE_MODEL_PATH = "gesture_recognizer.task"
GESTURE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task"