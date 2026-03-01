import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from RPi import GPIO
import time


DEFAULT_PIN_A_FWD = 10
DEFAULT_PIN_A_REV = 9
DEFAULT_PIN_B_FWD = 8
DEFAULT_PIN_B_REV = 7
DEFAULT_PWM_FREQUENCY = 20  # Hz
DEFAULT_FULL_SPEED_DUTY_CYCLE = 40  # %


class CamjamMovement(Node):
    def __init__(self):
        super().__init__("camjam_controller")

        # Declare and set parameters
        self.declare_parameter("motor_a_forward_pin", DEFAULT_PIN_A_FWD)
        self.declare_parameter("motor_a_reverse_pin", DEFAULT_PIN_A_REV)
        self.declare_parameter("motor_b_forward_pin", DEFAULT_PIN_B_FWD)
        self.declare_parameter("motor_b_reverse_pin", DEFAULT_PIN_B_REV)
        self.declare_parameter("pwm_frequency", DEFAULT_PWM_FREQUENCY)
        self.declare_parameter("max_duty_cycle", DEFAULT_FULL_SPEED_DUTY_CYCLE)
        motor_a_pin_fwd = self.get_parameter("motor_a_forward_pin").value
        motor_a_pin_rev = self.get_parameter("motor_a_reverse_pin").value
        motor_b_pin_fwd = self.get_parameter("motor_b_forward_pin").value
        motor_b_pin_rev = self.get_parameter("motor_b_reverse_pin").value
        pwm_frequency = self.get_parameter("pwm_frequency").value
        self._full_speed_duty_cycle = self.get_parameter("max_duty_cycle").value

        # Set up motors
        self.get_logger().info("Setting up motor pins...")
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(motor_a_pin_fwd, GPIO.OUT)
        GPIO.setup(motor_a_pin_rev, GPIO.OUT)
        GPIO.setup(motor_b_pin_fwd, GPIO.OUT)
        GPIO.setup(motor_b_pin_rev, GPIO.OUT)
        self._motor_a_fwd = GPIO.PWM(motor_a_pin_fwd, pwm_frequency)
        self._motor_a_rev = GPIO.PWM(motor_a_pin_rev, pwm_frequency)
        self._motor_b_fwd = GPIO.PWM(motor_b_pin_fwd, pwm_frequency)
        self._motor_b_rev = GPIO.PWM(motor_b_pin_rev, pwm_frequency)
        self._motor_a_fwd.start(0)
        self._motor_a_rev.start(0)
        self._motor_b_fwd.start(0)
        self._motor_b_rev.start(0)

        self.get_logger().info("Subscribing to topics...")
        self.vel_sub_ = self.create_subscription(
            Twist,
            "cmd_vel",
            self._vel_callback,
            10
        )
        self.get_logger().info("Camjam movement init complete!")

    def _vel_callback(self, msg: Twist):
        fwd = msg.linear.x
        turn = msg.angular.z
        right = min(1, fwd - turn / 2)
        left = min(1, fwd + turn / 2)
        left = int(left * self._full_speed_duty_cycle)
        right = int(right * self._full_speed_duty_cycle)

        if left >= 0:
            self._motor_b_fwd.ChangeDutyCycle(left)
            self._motor_b_rev.ChangeDutyCycle(0)
        else:
            self._motor_b_fwd.ChangeDutyCycle(0)
            self._motor_b_rev.ChangeDutyCycle(-left)

        if right >= 0:
            self._motor_a_fwd.ChangeDutyCycle(right)
            self._motor_a_rev.ChangeDutyCycle(0)
        else:
            self._motor_a_fwd.ChangeDutyCycle(0)
            self._motor_a_rev.ChangeDutyCycle(-right)


def main(args=None):
    rclpy.init(args=args)

    movement = CamjamMovement()

    rclpy.spin(movement)

    movement.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
