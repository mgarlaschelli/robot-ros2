# Release Notes

## v1.0.0 — 14/03/2026

### Features

#### Robot (ROS2)
- ROS2 Jazzy-based autonomous robot control system designed for Raspberry Pi Zero 2W
- Three operating modes: **Stand By**, **Patrol**, and **Manual**
- Patrol mode with ultrasonic sensor obstacle detection and automatic avoidance (reverse + turn right)
- Manual mode driven by `joy_cmd_vel` topic (joystick/web controller input)
- Differential drive motor control via `robot_movement` node
- HC-SR04 ultrasonic range sensor integration
- Mode switching via ROS2 services (`set_standby`, `set_patrol`, `set_manual`)
- Current mode published on `controller/mode` topic

#### Controller (Web Console)
- Browser-based web console running in a Docker container (no installation required on host)
- Python/FastAPI backend with ROS2 Jazzy integration
- React + TypeScript frontend with dark theme UI
- **Operating Mode panel**: select Stand By, Patrol, or Manual — calls the robot ROS2 services on change; displays current active mode via WebSocket
- **Manual Control panel**: directional arrow buttons (up, down, left, right) with animated joystick indicator; publishes velocity commands to `joy_cmd_vel` topic
- Docker Compose setup with volume mount for live development
- `colcon build` and `npm run build` supported inside the container

### Bug Fixes

- None

---
