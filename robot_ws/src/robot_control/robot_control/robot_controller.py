import rclpy
from rclpy.node import Node
from enum import Enum

from geometry_msgs.msg import Twist
from sensor_msgs.msg import Range
from std_msgs.msg import String
from std_srvs.srv import Trigger


DEFAULT_AVOID_RANGE = 15  # cm
DEFAULT_CONTROL_PERIOD = 0.2  # seconds between controller updates
DEFAULT_TURN_SPEED = 0.85  # Angular speed
DEFAULT_TURN_TIME_SEC = 1.0
DEFAULT_FORWARD_SPEED = 0.8  # Linear speed
DEFAULT_REVERSE_SPEED = 0.6  # Linear speed


class OperatingMode(Enum):
    STAND_BY = "STAND_BY"
    PATROL = "PATROL"
    MANUAL = "MANUAL"


class RobotController(Node):
    def __init__(self):
        super().__init__("robot_controller")

        # Declare and set parameters
        self.declare_parameter("avoid_range", DEFAULT_AVOID_RANGE)
        self.declare_parameter("control_period", DEFAULT_CONTROL_PERIOD)
        self.declare_parameter("turn_speed", DEFAULT_TURN_SPEED)
        self.declare_parameter("turn_time", DEFAULT_TURN_TIME_SEC)
        self.declare_parameter("forward_speed", DEFAULT_FORWARD_SPEED)
        self.declare_parameter("reverse_speed", DEFAULT_REVERSE_SPEED)

        self._avoid_range = self.get_parameter("avoid_range").value
        self._control_period = self.get_parameter("control_period").value
        self._turn_speed = self.get_parameter("turn_speed").value
        self._turn_time = self.get_parameter("turn_time").value
        self._forward_speed = self.get_parameter("forward_speed").value
        self._reverse_speed = self.get_parameter("reverse_speed").value

        # Top-level operating mode — starts in STAND_BY
        self._operating_mode = OperatingMode.STAND_BY

        # Latest joystick command (used in MANUAL mode)
        self._joy_cmd = Twist()

        # Patrol inner state machine
        self._patrol_state = "go_forward"
        self._turn_iterations = round(self._turn_time / self._control_period)
        self._turn_counter = 0

        # Publishers
        self.get_logger().info("Setting up publishers...")
        self._cmd_vel_pub = self.create_publisher(Twist, "cmd_vel", 10)
        self._mode_pub = self.create_publisher(String, "controller/mode", 10)

        # Subscriptions
        self.get_logger().info("Subscribing to topics...")
        self.range_sub_ = self.create_subscription(
            Range,
            "distance",
            self._range_msg_callback,
            10
        )
        self.create_subscription(
            Twist,
            "joy_cmd_vel",
            self._joy_cmd_callback,
            10
        )

        # Services to switch operating mode
        self.get_logger().info("Setting up mode services...")
        self.create_service(Trigger, "controller/set_standby", self._set_standby_cb)
        self.create_service(Trigger, "controller/set_patrol", self._set_patrol_cb)
        self.create_service(Trigger, "controller/set_manual", self._set_manual_cb)

        # Control loop timer
        self.get_logger().info("Setting up timer...")
        self.timer = self.create_timer(self._control_period, self._control_loop)

        self.get_logger().info(
            f"robot_control init complete. Operating mode: {self._operating_mode.value}"
        )

    # ------------------------------------------------------------------
    # Mode switching
    # ------------------------------------------------------------------

    def _switch_mode(self, new_mode: OperatingMode) -> tuple[bool, str]:
        if new_mode == self._operating_mode:
            msg = f"Already in {self._operating_mode.value}, ignoring request."
            self.get_logger().info(msg)
            return True, msg

        self.get_logger().info(
            f"Operating mode: {self._operating_mode.value} → {new_mode.value}"
        )
        self._operating_mode = new_mode

        if new_mode == OperatingMode.STAND_BY:
            self.stop()
        elif new_mode == OperatingMode.PATROL:
            self._patrol_state = "go_forward"
            self._turn_counter = 0

        mode_msg = String()
        mode_msg.data = new_mode.value
        self._mode_pub.publish(mode_msg)

        return True, f"Switched to {new_mode.value}"

    def _set_standby_cb(self, request, response):
        response.success, response.message = self._switch_mode(OperatingMode.STAND_BY)
        return response

    def _set_patrol_cb(self, request, response):
        response.success, response.message = self._switch_mode(OperatingMode.PATROL)
        return response

    def _set_manual_cb(self, request, response):
        response.success, response.message = self._switch_mode(OperatingMode.MANUAL)
        return response

    # ------------------------------------------------------------------
    # Sensor / joystick callbacks
    # ------------------------------------------------------------------

    def _joy_cmd_callback(self, msg: Twist):
        self._joy_cmd = msg

    def _range_msg_callback(self, msg: Range):
        if self._operating_mode != OperatingMode.PATROL:
            return

        if msg.range <= self._avoid_range:
            self._patrol_state = "avoid_obstacle_back"
            self.get_logger().info("Obstacle too close - avoiding!")
        elif self._patrol_state == "avoid_obstacle_back":
            self._patrol_state = "avoid_obstacle_right"
            self.get_logger().info("Distance cleared - turning right")
        elif self._patrol_state == "avoid_obstacle_right":
            if self._turn_counter < self._turn_iterations:
                self._turn_counter += 1
                return
            self._turn_counter = 0
            self._patrol_state = "go_forward"
            self.get_logger().info("Obstacle cleared. Going forward ...")

    # ------------------------------------------------------------------
    # Control loop
    # ------------------------------------------------------------------

    def stop(self):
        cmd = Twist()
        self._cmd_vel_pub.publish(cmd)
        self.get_logger().info("Robot stopped.")

    def _control_loop(self):
        if self._operating_mode == OperatingMode.STAND_BY:
            return

        if self._operating_mode == OperatingMode.MANUAL:
            self._cmd_vel_pub.publish(self._joy_cmd)
            return

        # PATROL
        cmd = Twist()
        if self._patrol_state == "avoid_obstacle_back":
            self.get_logger().info("Avoiding obstacle — reversing ...")
            cmd.linear.x = -self._reverse_speed
        elif self._patrol_state == "avoid_obstacle_right":
            self.get_logger().info("Avoiding obstacle — turning right ...")
            cmd.linear.x = self._forward_speed
            cmd.angular.z = -self._turn_speed
        elif self._patrol_state == "go_forward":
            cmd.linear.x = self._forward_speed
        else:
            self.get_logger().warn("Unrecognised patrol state: %s", self._patrol_state)
            return

        self._cmd_vel_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)

    controller = RobotController()

    rclpy.spin(controller)

    controller.stop()
    controller.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
