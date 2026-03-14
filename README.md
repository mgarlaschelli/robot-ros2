# robot-ros2

A ROS2 Jazzy autonomous robot control system designed to run on a Raspberry Pi. The robot uses an HC-SR04 ultrasonic distance sensor to detect obstacles and a differential drive motor system for movement.

## Repository Layout

```
robot/      # ROS2 workspace — runs on the Raspberry Pi
controller/ # Web controller — runs on PC via Docker
```

## Robot Architecture

The robot workspace (`robot/robot_ws`) contains two packages:

```
robot_ws/src/
├── robot_sensors/     # HC-SR04 distance sensor publisher
└── robot_control/     # Controller, motor driver, joystick input
```

### Nodes

| Node | Package | Executable | Role |
|---|---|---|---|
| `hc_sr04_publisher` | `robot_sensors` | `distance` | Reads HC-SR04 sensor, publishes distance at 4 Hz |
| `robot_controller` | `robot_control` | `control` | Operating mode state machine, publishes velocity commands at 5 Hz |
| `robot_movement` | `robot_control` | `move` | Translates velocity commands to PWM signals for the motors |
| `robot_joystick` | `robot_control` | `joystick` | Reads Bluetooth joystick input, publishes velocity commands at 20 Hz |

### Topics

| Topic | Type | Publisher → Subscriber |
|---|---|---|
| `/robot01/distance` | `sensor_msgs/Range` | `hc_sr04_publisher` → `robot_controller` |
| `/robot01/cmd_vel` | `geometry_msgs/Twist` | `robot_controller` → `robot_movement` |
| `/robot01/joy_cmd_vel` | `geometry_msgs/Twist` | `robot_joystick` → `robot_controller` |
| `/robot01/controller/mode` | `std_msgs/String` | `robot_controller` → (observers) |

### Services

| Service | Type | Description |
|---|---|---|
| `/robot01/controller/set_standby` | `std_srvs/Trigger` | Switch to STAND_BY mode |
| `/robot01/controller/set_patrol` | `std_srvs/Trigger` | Switch to PATROL mode |
| `/robot01/controller/set_manual` | `std_srvs/Trigger` | Switch to MANUAL mode |

### GPIO Pin Mapping (Raspberry Pi BCM)

| Pin | Role |
|---|---|
| 17 | HC-SR04 Trigger |
| 18 | HC-SR04 Echo |
| 10 | Motor A Forward |
| 9 | Motor A Reverse |
| 8 | Motor B Forward |
| 7 | Motor B Reverse |

### Operating Mode State Machine

`robot_controller` manages a top-level operating mode:

| Mode | Behaviour |
|---|---|
| **STAND_BY** | Motors stopped, all commands ignored. Default on startup. |
| **PATROL** | Autonomous obstacle avoidance (see inner state machine below). |
| **MANUAL** | Forwards joystick commands from `joy_cmd_vel` directly to `cmd_vel`. |

Mode transitions are triggered via ROS2 services and logged at every switch.

### PATROL Inner State Machine

While in PATROL mode, `robot_controller` runs a reactive obstacle avoidance loop:

1. **go_forward** — drives forward at `forward_speed`
2. **avoid_obstacle_back** — triggered when distance ≤ `avoid_range` (default 15 cm); reverses at `reverse_speed`
3. **avoid_obstacle_right** — turns right for `turn_time` seconds at `turn_speed`, then returns to go_forward

---

## Run (on Raspberry Pi)

```bash
source /opt/ros/jazzy/setup.bash
cd robot_ws
source install/setup.bash
```

**Launch all nodes:**

```bash
ros2 launch robot_control robot_control.launch.py
```

**Or run nodes individually:**

```bash
# Terminal 1 — distance sensor
ros2 run robot_sensors distance

# Terminal 2 — controller
ros2 run robot_control control

# Terminal 3 — motor driver
ros2 run robot_control move

# Terminal 4 — joystick (optional, requires Bluetooth joystick connected)
ros2 run robot_control joystick
```

### Switching Modes (CLI)

```bash
# Switch to PATROL (autonomous obstacle avoidance)
ros2 service call /robot01/controller/set_patrol std_srvs/srv/Trigger "{}"

# Switch to MANUAL (joystick control)
ros2 service call /robot01/controller/set_manual std_srvs/srv/Trigger "{}"

# Switch to STAND_BY (stop)
ros2 service call /robot01/controller/set_standby std_srvs/srv/Trigger "{}"
```

Monitor the current mode:

```bash
ros2 topic echo /robot01/controller/mode
```

---

## Web Controller

A browser-based controller that runs on a PC in Docker. Requires only Docker installed on the host — no ROS2, Python, or Node.js needed locally.

### Structure

```
controller/
├── Dockerfile                  # ros:jazzy + Node.js 20 + FastAPI/uvicorn
├── docker-compose.yml          # network_mode: host (required for DDS)
├── .env                        # ROS_DOMAIN_ID=0
├── scripts/
│   ├── build.sh                # builds frontend + colcon workspace
│   └── entrypoint.sh           # sources ROS2 setup, launches uvicorn
└── controller_ws/src/robot_controller_web/
    ├── robot_controller_web/
    │   ├── ros_node.py         # rclpy node (spin thread, service clients)
    │   └── main.py             # FastAPI app (REST + WebSockets)
    └── frontend/               # React + Vite + TypeScript
        └── src/components/
            ├── ModePanel.tsx   # STAND_BY / PATROL / MANUAL buttons
            └── JoystickPanel.tsx # Arrow buttons + animated joystick dot
```

### API

| Endpoint | Description |
|---|---|
| `POST /api/mode` `{"mode": "STAND_BY\|PATROL\|MANUAL"}` | Call the corresponding ROS2 service |
| `GET /api/mode` | Return current operating mode |
| `WS /ws/joystick` | Stream `{linear_x, angular_z}` → publishes to `/robot01/joy_cmd_vel` |
| `WS /ws/mode` | Push current mode updates to the browser |

### entrypoint.sh

`scripts/entrypoint.sh` is the Docker `ENTRYPOINT` — it is executed automatically by the container on every `docker compose up` or `docker compose run`. **You never run it manually.** It sources `/opt/ros/jazzy/setup.bash` and, if the workspace has been built, sources `controller_ws/install/setup.bash`, then hands off to whatever command the container was started with (e.g. uvicorn).

### First-time build

Open a shell inside the container and run `build.sh`:

```bash
# From the repo root, on the host
docker compose -f controller/docker-compose.yml run --rm controller \
  bash /workspace/scripts/build.sh
```

`build.sh` performs both steps in order:

**Step 1 — React frontend** (`npm run build`)

Run directory: `/workspace/controller_ws/src/robot_controller_web/frontend`

```bash
cd /workspace/controller_ws/src/robot_controller_web/frontend
npm install   # first time only
npm run build # outputs to ../robot_controller_web/static/
```

**Step 2 — ROS2 package** (`colcon build`)

Run directory: `/workspace/controller_ws`

```bash
cd /workspace/controller_ws
colcon build --symlink-install --packages-select robot_controller_web
```

`--symlink-install` means Python source files are symlinked into the install tree, so backend changes are picked up by uvicorn's `--reload` without rebuilding.

### Start

```bash
docker compose -f controller/docker-compose.yml up
```

Open `http://localhost:8000` in your browser.

### Development workflow

| What changed | Where to run | Command |
|---|---|---|
| Python backend (`main.py`, `ros_node.py`) | — | No action — uvicorn `--reload` picks it up automatically |
| React frontend (`frontend/src/**`) | Inside the container, at `controller_ws/src/robot_controller_web/frontend/` | `npm run build` |
| ROS2 package structure (`package.xml`, `setup.py`) | Inside the container, at `controller_ws/` | `colcon build --symlink-install --packages-select robot_controller_web` |

To get a shell inside a running container:

```bash
docker compose -f controller/docker-compose.yml exec controller bash
```

Or start a fresh shell without launching uvicorn:

```bash
docker compose -f controller/docker-compose.yml run --rm controller bash
```

> **Note:** `network_mode: host` is required so DDS multicast can reach the Pi on the same LAN. This works on Linux Docker hosts.

---

## License

MIT — see [LICENSE](LICENSE).
