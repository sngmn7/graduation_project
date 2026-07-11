cat > README.md << 'EOF'
# Graduation Project — Intelligent User-Following Autonomous Carrier

지능형 사용자 추종 자율주행 카트 로봇 프로젝트.
Jetson Nano (ROS2 Humble) + STM32H723 + MD400T BLDC 모터 드라이버 + RPLiDAR S2 + UWB(DWM1001) + MediaPipe 제스처 인식 기반으로 구성.

---

## 1. 시스템 구조 및 통신 검증

ROS2 노드 구조: `gesture_control`(제스처 인식) / `carrier_hardware`(모터 제어 및 오도메트리) / `carrier_description`(URDF) / `carrier_lidar`(라이다)로 분리 설계.

| 항목 | 이미지 |
|---|---|
| 노드-토픽 통신 그래프 | ![rqt_graph](docs/robot_pictures/rqt_graph.png) |
| 제어 노드 구조 | ![control_node](docs/robot_pictures/control_node.png) |
| 하드웨어 노드 실행 로그 | ![hardware_node_commute](docs/robot_pictures/hardware_node_commute.png) |
| 엔코더 피드백 파이프라인 구조 | ![encoder_feedback_structure](docs/robot_pictures/encoder_feedback_structure.png) |

**검증 경로**: Jetson → STM32 (UART, 0xAA) → STM32 → MD400T (RS485 폴링) → STM32 → Jetson (UART, 0xBB 피드백)
전체 통신 왕복(loopback)이 정상 동작함을 실시간 RPM 피드백 로그로 확인.

---

## 2. MediaPipe 제스처 인식 및 모터 제어

카메라 입력(nvarguscamerasrc) 기반 MediaPipe 제스처 인식 → `/cmd_vel` 발행 → `carrier_hardware`가 STM32로 RPM 명령 전송.

| 제스처 | 이미지 |
|---|---|
| 카메라 인식 화면 | ![gesture_camera](docs/robot_pictures/gesture_camera.png) |
| 전진 (Come Closer) | ![come_closer_gesture](docs/robot_pictures/come_closer_gesture.png) |
| 추종 (Follow) | ![follow_gesture](docs/robot_pictures/follow_gesture.png) |
| 정지 (Stop) | ![stop_gesture](docs/robot_pictures/stop_gesture.png) |
| 복귀 대기 (Return Wait) | ![return_wait_gesture](docs/robot_pictures/return_wait_gesture.png) |
| 제스처 → 바퀴 제어 터미널 로그 | ![gesture_wheel_control_terminal](docs/robot_pictures/gesture_wheel_control_terminal.png) |

---

## 3. 모터 RPM 명령/피드백 검증

| 항목 | 이미지 |
|---|---|
| RPM 명령 전송 | ![wheel_rpm_order](docs/robot_pictures/wheel_rpm_order.png) |
| 실제 구동 확인 | ![wheel_rpm_operation](docs/robot_pictures/wheel_rpm_operation.png) |
| 오도메트리 각속도 그래프 (rqt_plot) | ![matplot](docs/robot_pictures/matplot.png) |

---

## 4. RPLiDAR S2 스캔 검증

| 항목 | 이미지 |
|---|---|
| RPLiDAR 노드 실행 | ![rplidar_node](docs/robot_pictures/rplidar_node.png) |
| Robot State Publisher / URDF | ![robot_urdf_node](docs/robot_pictures/robot_urdf_node.png) |
| 레이저 스캔 값 | ![laser_scan_value](docs/robot_pictures/laser_scan_value.png) |
| 레이저 스캔 (하늘소 랩실) | ![laser_scan_hanulso](docs/robot_pictures/laser_scan_hanulso.png) |

---

## 5. SLAM 매핑 결과

slam_toolbox (online_async) 기반 실내 매핑.

| 위치 | 이미지 |
|---|---|
| 랩실 지도 1 | ![lab_map1](docs/robot_pictures/lab_map1.png) |
| 랩실 지도 2 | ![lab_map2](docs/robot_pictures/lab_map2.pgm) |
| 하늘소관 지도 1 | ![map_hanulso](docs/robot_pictures/map_hanulso.png) |
| 하늘소관 지도 2 | ![map_hanulso2](docs/robot_pictures/map_hanulso2.png) |
| 매핑 결과 1 | ![map1](docs/robot_pictures/map1.png) |
| 매핑 결과 2 | ![map2](docs/robot_pictures/map2.png) |
| 매핑 결과 3 | ![map3](docs/robot_pictures/map3.png) |
| 매핑 결과 4 | ![map4](docs/robot_pictures/map4.png) |
| slam_toolbox 노드 실행 | ![slam_toolbox_node](docs/robot_pictures/slam_toolbox_node.png) |

원본 맵 데이터(`.pgm`)는 `docs/robot_pictures/`에 함께 저장되어 있습니다 (`checkpoint4.pgm`, `checkpoint5.pgm`, `room_map.pgm` 등).

---

## Tech Stack

- **Compute**: Jetson Nano (ROS2 Humble)
- **MCU**: STM32H723 (FreeRTOS)
- **Motor Driver**: MD400T BLDC (RS485)
- **Sensors**: RPLiDAR S2, UWB DWM1001
- **Gesture Recognition**: MediaPipe
- **Navigation**: slam_toolbox → AMCL → Nav2 (예정)
EOF
