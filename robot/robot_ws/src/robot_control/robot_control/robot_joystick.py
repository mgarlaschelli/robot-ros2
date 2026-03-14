import sys

import pygame
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist


DEADZONE = 0.1
DEFAULT_PUBLISH_RATE = 20.0  # Hz — matches the 0.02 s loop in the reference implementation


class RobotJoystick(Node):
    def __init__(self):
        super().__init__("robot_joystick")

        self.declare_parameter("publish_rate", DEFAULT_PUBLISH_RATE)
        self.declare_parameter("deadzone", DEADZONE)
        self._publish_rate = self.get_parameter("publish_rate").value
        self._deadzone = self.get_parameter("deadzone").value

        self._pub = self.create_publisher(Twist, "joy_cmd_vel", 10)

        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            self.get_logger().error("No joystick found. Shutting down.")
            raise RuntimeError("No joystick found")

        self._joystick = pygame.joystick.Joystick(0)
        self._joystick.init()
        self.get_logger().info(f"Joystick connected: {self._joystick.get_name()}")

        self._timer = self.create_timer(1.0 / self._publish_rate, self._publish_loop)
        self.get_logger().info("robot_joystick init complete.")

    def _apply_deadzone(self, value: float) -> float:
        return 0.0 if abs(value) < self._deadzone else value

    def _publish_loop(self):
        pygame.event.pump()

        # Button 1 (B) — emergency stop
        if self._joystick.get_button(1):
            self.get_logger().info("Emergency stop!")
            self._pub.publish(Twist())
            return

        # Left stick: axis 1 = forward/backward (up is negative, so invert)
        #             axis 0 = left/right steering
        linear = self._apply_deadzone(-self._joystick.get_axis(1))
        # ROS convention: positive angular.z = turn left, so invert horizontal axis
        angular = self._apply_deadzone(-self._joystick.get_axis(0))

        cmd = Twist()
        cmd.linear.x = linear   # -1.0 (full reverse) … +1.0 (full forward)
        cmd.angular.z = angular  # -1.0 (full right)  … +1.0 (full left)
        self._pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)

    try:
        node = RobotJoystick()
    except RuntimeError:
        rclpy.shutdown()
        sys.exit(1)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node._pub.publish(Twist())  # zero velocity on exit
        node.destroy_node()
        pygame.quit()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
