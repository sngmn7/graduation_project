# gesture_detector.py

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import GestureRecognizer, GestureRecognizerOptions, RunningMode
from enum import Enum
import urllib.request
import os
import time
from .config import GESTURE_MODEL_PATH, GESTURE_MODEL_URL

class Gesture(Enum):
    NONE = "none"
    THUMBS_UP = "thumbs_up"       # 👍 엄지 따봉
    OPEN_WAVE = "open_wave"       # 🖐️ 손 펴기 (Open_Palm)
    CLOSED_FIST = "closed_fist"   # ✊ 주먹 쥐기
    POINTING_UP = "pointing_up"   # ☝️ 검지 들기

class GestureDetector:
    def __init__(self):
        # 모델 파일 없으면 자동 다운로드
        if not os.path.exists(GESTURE_MODEL_PATH):
            print(f"새로운 제스처 인식 모델 다운로드 중... ({GESTURE_MODEL_PATH})")
            urllib.request.urlretrieve(GESTURE_MODEL_URL, GESTURE_MODEL_PATH)

        # GestureRecognizer 설정
        options = GestureRecognizerOptions(
            base_options=BaseOptions(model_asset_path=GESTURE_MODEL_PATH),
            running_mode=RunningMode.VIDEO,
            num_hands=2,  # 양손 모두 인식 가능하도록 설정
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self._detector = GestureRecognizer.create_from_options(options)

    def detect(self, frame):
        """
        프레임에서 제스처를 감지하고 (제스처 타입, 랜드마크 결과)를 반환함.
        """
        # BGR -> RGB 변환 (MediaPipe용)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # 비디오 모드이므로 타임스탬프 필요
        timestamp_ms = int(time.time() * 1000)
        
        # 제스처 인식 실행
        result = self._detector.recognize_for_video(mp_image, timestamp_ms)
        
        # 결과 해석
        final_gesture = Gesture.NONE
        
        if result.gestures:
            # 가장 신뢰도가 높은 첫 번째 손의 제스처 확인
            top_gesture = result.gestures[0][0].category_name
            
            # MediaPipe 기본 라벨을 사용자 정의 Enum으로 매핑
            if top_gesture == "Thumb_Up":
                final_gesture = Gesture.THUMBS_UP
            elif top_gesture == "Open_Palm":
                final_gesture = Gesture.OPEN_WAVE
            elif top_gesture == "Closed_Fist":
                final_gesture = Gesture.CLOSED_FIST
            elif top_gesture == "Pointing_Up":
                final_gesture = Gesture.POINTING_UP
        
        return final_gesture, result
    
    def draw_landmarks(self, frame, result):
        if not result or not result.hand_landmarks:
            return

        h, w, _ = frame.shape
        HAND_CONNECTIONS = [
            (0,1),(1,2),(2,3),(3,4),
            (0,5),(5,6),(6,7),(7,8),
            (0,9),(9,10),(10,11),(11,12),
            (0,13),(13,14),(14,15),(15,16),
            (0,17),(17,18),(18,19),(19,20),
            (5,9),(9,13),(13,17)
        ]
        for hand_landmarks in result.hand_landmarks:
            for lm in hand_landmarks:
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)

            for start_idx, end_idx in HAND_CONNECTIONS:
                p1 = (int(hand_landmarks[start_idx].x * w), int(hand_landmarks[start_idx].y * h))
                p2 = (int(hand_landmarks[end_idx].x * w), int(hand_landmarks[end_idx].y * h))
                cv2.line(frame, p1, p2, (0, 200, 0), 2)

    def release(self):
        self._detector.close()
