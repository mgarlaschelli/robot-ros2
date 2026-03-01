# robot-ros2

A ROS2 Jazzy autonomous robot control system designed to run on a Raspberry Pi. The robot uses an HC-SR04 ultrasonic distance sensor to detect obstacles and a differential drive motor system for movement.

## Architecture

The system is organized as a ROS2 workspace (`robot_ws`) with two packages:

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

## Run

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

### Switching Modes

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

## License

MIT — see [LICENSE](LICENSE).
