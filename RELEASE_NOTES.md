# Release Notes

## v1.1.0 — 22/03/2026

### Features

#### Robot (ROS2)
- OV5647 Raspberry Pi camera integration via new `camera` node in `robot_sensors`
- Publishes compressed JPEG frames at 15 Hz on `/robot01/camera/compressed` (BEST_EFFORT QoS)
- Captures raw SGBRG10P (pGAA) Bayer frames, unpacks 10-bit packed data with NumPy, and debayers to colour with OpenCV
- Re-applies sensor exposure and gain controls on startup to survive OpenCV's V4L2 format negotiation
- Configurable parameters: `device`, `subdev`, `fps`, `jpeg_quality`, `exposure`, `analogue_gain`

#### Controller (Web Console)
- **Camera Feed panel**: live MJPEG stream served at `/api/camera/stream`, displayed left of the controls
- Two-column layout: camera on the left, Operating Mode and Manual Control stacked on the right at equal height
- MJPEG stream bridges the ROS2 spin thread to the asyncio event loop via `queue.Queue` and `run_in_executor`

### Bug Fixes

- None

---

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
