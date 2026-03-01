import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from std_msgs.msg import Bool
from sensor_msgs.msg import Range
import time


DEFAULT_AVOID_RANGE = 15  # cm
DEFAULT_SEARCH_INCREMENT = 100  # line sensor readings
DEFAULT_STARTING_SEARCH_SIZE = 50  # line sensor readings
DEFAULT_CONTROL_PERIOD = 0.2  # seconds between controller updates
DEFAULT_TURN_SPEED = 0.85  # Angular speed
DEFAULT_FOLLOW_SPEED = 0.8  # Linear speed
DEFAULT_REVERSE_SPEED = 0.6  # Linear speed


class CamjamController(Node):
    def __init__(self):
        super().__init__("camjam_controller")

        # Declare and set parameters
        self.declare_parameter("avoid_range", DEFAULT_AVOID_RANGE)
        self.declare_parameter("search_increment", DEFAULT_SEARCH_INCREMENT)
        self.declare_parameter("starting_search_size", DEFAULT_STARTING_SEARCH_SIZE)
        self.declare_parameter("control_period", DEFAULT_CONTROL_PERIOD)
        self.declare_parameter("turn_speed", DEFAULT_TURN_SPEED)
        self.declare_parameter("follow_speed", DEFAULT_FOLLOW_SPEED)
        self.declare_parameter("reverse_speed", DEFAULT_REVERSE_SPEED)

        self._avoid_range = self.get_parameter("avoid_range").value
        self._search_increment = self.get_parameter("search_increment").value
        self._starting_search_size = self.get_parameter("starting_search_size").value
        self._control_period = self.get_parameter("control_period").value
        self._turn_speed = self.get_parameter("turn_speed").value
        self._follow_speed = self.get_parameter("follow_speed").value
        self._reverse_speed = self.get_parameter("reverse_speed").value

        # Set member variables
        self._mode = "find_line"
        self._search_direction = "right"
        self._line_miss_count = 0
        self._direction_change_limit = self._starting_search_size

        # Set up subscriptions
        self.get_logger().info("Subscribing to topics...")
        self.line_sub_ = self.create_subscription(
            Bool,
            "line_detected",
            self._line_msg_callback,
            10
        )
        self.range_sub_ = self.create_subscription(
            Range,
            "distance",
            self._range_msg_callback,
            10
        )

        self.get_logger().info("Setting up velocity command publisher...")
        self.publisher_ = self.create_publisher(Twist, "cmd_vel", 10)

        # Create timer to call function to control robot
        self.get_logger().info("Setting up timer...")
        timer_period = self._control_period
        self.timer = self.create_timer(timer_period, self.control_loop)

        self.get_logger().info("camjam_control init complete!")

    def _line_msg_callback(self, msg: Bool):
        # If we're avoiding obstacles, continue with that!
        if self._mode not in ["find_line", "follow_line"]:
            return
        if msg.data:
            if self._mode == "find_line":
                self.get_logger().info("Found line! Following...")
            self._line_miss_count = 0
            self._mode = "follow_line"
        else:
            if self._mode == "follow_line":
                self.get_logger().info("Lost line! Finding...")
                self._direction_change_limit = self._starting_search_size
            self._line_miss_count += 1
            self._mode = "find_line"

    def _range_msg_callback(self, msg: Range):
        if msg.range <= self._avoid_range:
            self._mode = "avoid_obstacle"
            self.get_logger().info("Obstacle too close - avoiding!")
        elif self._mode == "avoid_obstacle":
            self._mode = "find_line"
            self._direction_change_limit = self._starting_search_size
            self.get_logger().info("Obstacle cleared. Looking for line...")

    def stop(self):
        cmd = Twist()
        cmd.linear.x = 0
        cmd.linear.z = 0
        self.get_logger().info("Stopping!")
        self.publisher_.publish(cmd)

    def control_loop(self):
        cmd = Twist()
        if self._mode == "avoid_obstacle":
            # Back away slowly
            cmd.linear.x = -self._reverse_speed
            self.get_logger().info("I'm avoiding an obstacle...")
        elif self._mode == "find_line":
            if self._line_miss_count >= self._direction_change_limit:
                self._line_miss_count = 0
                if self._search_direction == "right":
                    self.get_logger().info("Trying left...")
                    self._search_direction = "left"
                else:
                    self.get_logger().info("Trying right...")
                    self._search_direction = "right"
                self._direction_change_limit += self._search_increment
            if self._search_direction == "left":
                cmd.angular.z = self._turn_speed
            else:
                cmd.angular.z = -self._turn_speed
        elif self._mode == "follow_line":
            # Follow the line!
            cmd.linear.x = self._follow_speed
        else:
            self.get_logger().warn("Unrecognised mode: %s", self._mode)
            return

        self.publisher_.publish(cmd)


def main(args=None):
    rclpy.init(args=args)

    controller = CamjamController()

    rclpy.spin(controller)

    controller.stop()
    controller.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
