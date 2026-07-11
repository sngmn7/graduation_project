#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped

import serial
import struct
import math
import threading
import time


# ── 로봇 물리 상수 ──────────────────────────────
WHEEL_RADIUS   = 0.130   # 바퀴 반지름 (m) : 260mm / 2
WHEEL_BASE     = 0.5     # 좌우 바퀴 중심 간 거리 (m)
SERIAL_PORT    = '/dev/ttyTHS1'
BAUD_RATE      = 57600

# 패킷 헤더
HDR_CMD  = 0xAA   # Jetson → STM32
HDR_FB   = 0xBB   # STM32  → Jetson


class HardwareNode(Node):
    def __init__(self):
        super().__init__('hardware_node')
        self.get_logger().info("Hardware Node 시작")

        # ── 시리얼 초기화 ──────────────────────────
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
            self.get_logger().info(f"UART 연결 성공: {SERIAL_PORT} @ {BAUD_RATE}")
        except Exception as e:
            self.get_logger().error(f"UART 연결 실패: {e}")
            self.ser = None

        # ── ROS2 인터페이스 ────────────────────────
        self.cmd_vel_sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        # ── Odometry 상태 변수 ─────────────────────
        self.x     = 0.0
        self.y     = 0.0
        self.theta = 0.0
        self.last_time = self.get_clock().now()

        # ── 피드백 수신 스레드 ─────────────────────
        self.running = True
        self.fb_thread = threading.Thread(target=self.feedback_loop, daemon=True)
        self.fb_thread.start()

    # ──────────────────────────────────────────────
    # /cmd_vel 콜백 : linear.x / angular.z → RPM
    # ──────────────────────────────────────────────
    def cmd_vel_callback(self, msg):
        linear  = msg.linear.x
        angular = msg.angular.z

        # Differential drive 변환
        left_vel  = linear - angular * WHEEL_BASE / 2.0
        right_vel = linear + angular * WHEEL_BASE / 2.0

        # m/s → RPM
        left_rpm  = int(left_vel  / (2.0 * math.pi * WHEEL_RADIUS) * 60.0)
        right_rpm = int(right_vel / (2.0 * math.pi * WHEEL_RADIUS) * 60.0)

        self.get_logger().info(f"CMD: linear={linear}, left_rpm={left_rpm}, right_rpm={right_rpm}")
        # 오른쪽 바퀴가 반대 방향으로 장착 → 부호 반전
        self.send_rpm(left_rpm, right_rpm)

    # ──────────────────────────────────────────────
    # STM32로 RPM 패킷 전송  (0xAA 헤더, 6바이트)
    # ──────────────────────────────────────────────
    def send_rpm(self, m1, m2):
        if self.ser is None:
            return

        m1 = int(m1) & 0xFFFF
        m2 = int(m2) & 0xFFFF

        pkt = bytearray(6)
        pkt[0] = HDR_CMD
        pkt[1] = m1 & 0xFF
        pkt[2] = (m1 >> 8) & 0xFF
        pkt[3] = m2 & 0xFF
        pkt[4] = (m2 >> 8) & 0xFF
        pkt[5] = (pkt[1] + pkt[2] + pkt[3] + pkt[4]) & 0xFF

        self.ser.write(pkt)

    # ──────────────────────────────────────────────
    # STM32 RPM 피드백 수신 루프 (별도 스레드)
    # ──────────────────────────────────────────────
    def feedback_loop(self):
        left_rpm = None
        right_rpm = None

        while self.running:
            if self.ser is None:
                time.sleep(0.1)
                continue

            data = self.ser.read(6)

            if len(data) == 6 and data[0] == HDR_FB:
                m1 = struct.unpack_from('<h', data, 1)[0]
                m2 = struct.unpack_from('<h', data, 3)[0]

                left_rpm = m1
                right_rpm = m2

                # 둘 다 받았을 때만 odom 업데이트
                if left_rpm is not None and right_rpm is not None:
                    self.update_odom(left_rpm, right_rpm)
                    left_rpm = None
                    right_rpm = None

    # ──────────────────────────────────────────────
    # RPM → /odom 적분 & 발행
    # ──────────────────────────────────────────────
    def update_odom(self, left_rpm, right_rpm):
        now = self.get_clock().now()
        dt  = (now - self.last_time).nanoseconds / 1e9
        self.last_time = now

        if dt <= 0.0 or dt > 1.0:
            return
        if not hasattr(self, 'prev_left_rpm'):
            self.prev_left_rpm = 0
            self.prev_right_rpm = 0

        if abs(left_rpm - self.prev_left_rpm) > 150:
            left_rpm = self.prev_left_rpm
        if abs(right_rpm - self.prev_right_rpm) > 150:
            right_rpm = self.prev_right_rpm

        self.prev_left_rpm = left_rpm
        self.prev_right_rpm = right_rpm
        if abs(left_rpm) < 15 and abs(right_rpm) < 15:
            self.get_logger().info(f"필터링됨: L={left_rpm}, R={right_rpm}")
            left_rpm = 0
            right_rpm = 0
        else:
            self.get_logger().info(f"통과됨: L={left_rpm}, R={right_rpm}")
        # RPM → 선속도 (m/s)
        left_vel  = left_rpm  * 2.0 * math.pi * WHEEL_RADIUS / 60.0
        right_vel = right_rpm * 2.0 * math.pi * WHEEL_RADIUS / 60.0

        # 로봇 선속도 / 각속도
        linear  = (left_vel + right_vel) / 2.0
        angular = (right_vel - left_vel) / WHEEL_BASE

        # 위치 적분
        self.x     += linear * math.cos(self.theta) * dt
        self.y     += linear * math.sin(self.theta) * dt
        self.theta += angular * dt

        # 쿼터니언 (yaw only)
        qz = math.sin(self.theta / 2.0)
        qw = math.cos(self.theta / 2.0)

        # ── Odometry 토픽 발행 ─────────────────────
        odom = Odometry()
        odom.header.stamp    = now.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id  = 'base_link'

        odom.pose.pose.position.x  = self.x
        odom.pose.pose.position.y  = self.y
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw

        odom.twist.twist.linear.x  = linear
        odom.twist.twist.angular.z = angular

        self.odom_pub.publish(odom)

        # ── TF 브로드캐스트 (odom → base_link) ────
        tf = TransformStamped()
        tf.header.stamp    = now.to_msg()
        tf.header.frame_id = 'odom'
        tf.child_frame_id  = 'base_link'

        tf.transform.translation.x = self.x
        tf.transform.translation.y = self.y
        tf.transform.translation.z = 0.0
        tf.transform.rotation.z    = qz
        tf.transform.rotation.w    = qw

        self.tf_broadcaster.sendTransform(tf)

    def shutdown(self):
        self.running = False
        if self.ser:
            self.send_rpm(0, 0)
            self.ser.close()


def main(args=None):
    rclpy.init(args=args)
    node = HardwareNode()

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
