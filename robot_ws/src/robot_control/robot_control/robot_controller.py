import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from std_msgs.msg import Bool
from sensor_msgs.msg import Range
import time


DEFAULT_AVOID_RANGE = 15  # cm
DEFAULT_CONTROL_PERIOD = 0.2  # seconds between controller updates
DEFAULT_TURN_SPEED = 0.85  # Angular speed
DEFAULT_TURN_TIME_SEC = 1.0
DEFAULT_FORWARD_SPEED = 0.8  # Linear speed
DEFAULT_REVERSE_SPEED = 0.6  # Linear speed


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

        # Set member variables
        self._mode = "go_forward"
        self._turn_iterations = round(self._turn_time / self._control_period)
        self._turn_counter = 0

        # Set up subscriptions
        self.get_logger().info("Subscribing to topics...")
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

        self.get_logger().info("robot_control init complete!")

    def _range_msg_callback(self, msg: Range):
        if msg.range <= self._avoid_range:
            self._mode = "avoid_obstacle_back"
            self.get_logger().info("Obstacle too close - avoiding!")
        elif self._mode == "avoid_obstacle_back":
            self._mode = "avoid_obstacle_right"
            self.get_logger().info("Distance - Turn right")
        elif self._mode == "avoid_obstacle_right":
            if self._turn_counter < self._turn_iterations:
                self._turn_counter = self._turn_counter + 1
                return
            self._turn_counter = 0
            self._mode = "go_forward"
            self.get_logger().info("Obstacle cleared. Go forward ...")

    def stop(self):
        cmd = Twist()
        cmd.linear.x = 0.0
        cmd.angular.z = 0.0
        self.get_logger().info("Stopping!")
        self.publisher_.publish(cmd)

    def control_loop(self):
        cmd = Twist()
        if self._mode == "avoid_obstacle_back":
            # Back away slowly
            self.get_logger().info("I'm avoiding an obstacle... go back ...")
            cmd.linear.x = -self._reverse_speed
            cmd.angular.z = 0.0
            self.publisher_.publish(cmd)
        elif self._mode == "avoid_obstacle_right":
            # Turn right
            self.get_logger().info("I'm avoiding an obstacle... turn right ...")
            cmd.linear.x = self._forward_speed
            cmd.angular.z = -self._turn_speed
            self.publisher_.publish(cmd)
        elif self._mode == "go_forward":
            # Go Forward
            cmd.angular.z = 0.0
            cmd.linear.x = self._forward_speed
            self.publisher_.publish(cmd)
        else:
            self.get_logger().warn("Unrecognised mode: %s", self._mode)
            return


def main(args=None):
    rclpy.init(args=args)

    controller = RobotController()

    rclpy.spin(controller)

    controller.stop()
    controller.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
