#!/usr/bin/env python3

import os
import cv2
import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from ament_index_python.packages import get_package_share_directory

from .gesture_detector import GestureDetector, Gesture


class GestureControlNode(Node):
    def __init__(self):
        super().__init__('gesture_control_node')
        self.get_logger().info("Gesture Control Node 시작")

        self.pipeline = (
            "nvarguscamerasrc sensor-id=0 ! "
            "video/x-raw(memory:NVMM), width=1280, height=720, format=NV12, framerate=30/1 ! "
            "nvvidconv flip-method=0 ! "
            "video/x-raw, format=BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=BGR ! "
            "appsink drop=True max-buffers=1"
        )

        try:
            package_share_dir = get_package_share_directory('gesture_control')
            self.model_path = os.path.join(
                package_share_dir,
                'models',
                'gesture_recognizer.task'
            )
            self.get_logger().info(f"모델 경로: {self.model_path}")
        except Exception as e:
            self.get_logger().error(f"모델 경로 찾기 실패: {e}")
            self.model_path = None

        self.cap = cv2.VideoCapture(self.pipeline, cv2.CAP_GSTREAMER)

        if not self.cap.isOpened():
            self.get_logger().error("CSI 카메라 열기 실패")
            return

        self.detector = GestureDetector()

        # /cmd_vel 퍼블리셔
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.prev_gesture = Gesture.NONE
        self.current_gesture = Gesture.NONE
        self.gesture_count = 0
        self.required_frames = 5

        # 엄지 복귀 동작 상태 관리
        self.return_wait = False
        self.return_start_time = 0.0
        self.return_delay_sec = 1.0

        self.timer = self.create_timer(0.033, self.process_frame)

    def publish_cmd_vel(self, linear_x, angular_z=0.0):
        twist = Twist()
        twist.linear.x = linear_x
        twist.angular.z = angular_z
        self.cmd_vel_pub.publish(twist)

    def process_frame(self):
        ret, frame = self.cap.read()

        if not ret or frame is None:
            return

        gesture, mp_results = self.detector.detect(frame)

        # 엄지 입력 후 대기 상태 처리
        if self.return_wait:
            elapsed = time.time() - self.return_start_time

            if elapsed >= self.return_delay_sec:
                self.get_logger().info("[복귀] 대기 완료 -> 느린 속도로 주행")
                self.publish_cmd_vel(0.3)   # 느린 속도

                self.return_wait = False
                self.prev_gesture = Gesture.THUMBS_UP

            self.detector.draw_landmarks(frame, mp_results)
            self.draw_label(frame, Gesture.THUMBS_UP)

            cv2.imshow("Gesture Detection", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.destroy_node()

            return

        if gesture == self.current_gesture:
            self.gesture_count += 1
        else:
            self.current_gesture = gesture
            self.gesture_count = 1

        if (
            self.gesture_count >= self.required_frames and
            gesture != self.prev_gesture
        ):
            # 주먹 = 정지
            if gesture == Gesture.CLOSED_FIST:
                self.get_logger().info("[제스처] 주먹 -> 정지")
                self.publish_cmd_vel(0.0)

            # 손바닥 = 추종 재개
            elif gesture == Gesture.OPEN_WAVE:
                self.get_logger().info("[제스처] 손바닥 -> 추종 재개")
                self.publish_cmd_vel(0.5)

            # 엄지 = 먼저 멈춤, 일정 시간 후 느린 속도 복귀
            elif gesture == Gesture.THUMBS_UP:
                self.get_logger().info("[제스처] 엄지 -> 정지 후 복귀 대기")
                self.publish_cmd_vel(0.0)

                self.return_wait = True
                self.return_start_time = time.time()

            # 검지 = 가까이 가기, 빠른 속도
            elif gesture == Gesture.POINTING_UP:
                self.get_logger().info("[제스처] 검지 -> 가까이 이동")
                self.publish_cmd_vel(0.8)

            self.prev_gesture = gesture

        self.detector.draw_landmarks(frame, mp_results)
        self.draw_label(frame, gesture)

        cv2.imshow("Gesture Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.destroy_node()

    def draw_label(self, frame, gesture):
        if gesture == Gesture.CLOSED_FIST:
            label = "STOP"
            color = (0, 0, 255)

        elif gesture == Gesture.OPEN_WAVE:
            label = "FOLLOW"
            color = (0, 255, 0)

        elif gesture == Gesture.THUMBS_UP:
            label = "RETURN WAIT"
            color = (255, 255, 0)

        elif gesture == Gesture.POINTING_UP:
            label = "COME CLOSER"
            color = (255, 0, 255)

        else:
            label = ""
            color = (255, 255, 255)

        if label:
            cv2.putText(
                frame,
                label,
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                color,
                3,
                cv2.LINE_AA
            )

    def shutdown(self):
        self.publish_cmd_vel(0.0)   # 종료 시 정지
        self.cap.release()

        if hasattr(self.detector, 'release'):
            self.detector.release()

        cv2.destroyAllWindows()


def main(args=None):
    rclpy.init(args=args)

    node = GestureControlNode()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()