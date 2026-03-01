import rclpy
from rclpy.node import Node

from std_msgs.msg import Bool
from RPi import GPIO
import time

DEFAULT_PIN_LINE_SENSOR = 25


class LineSensorPublisher(Node):
    def __init__(self):
        super().__init__("line_sensor_publisher")

        # Declare and set parameters
        self.declare_parameter("line_sensor_pin", DEFAULT_PIN_LINE_SENSOR)
        self._line_sensor_pin = self.get_parameter("line_sensor_pin").value

        # Pin setup
        self.get_logger().info("Setting up pins for line sensor")
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self._line_sensor_pin, GPIO.IN)

        self.get_logger().info("Pins ready, initialising publisher...")
        self.publisher_ = self.create_publisher(Bool, "line_detected", 10)
        timer_period = 0.01
        self.timer = self.create_timer(timer_period, self.timer_callback)

        self.get_logger().info("line_sensor_publisher init complete!")

    def _is_line_detected(self) -> bool:
        return GPIO.input(self._line_sensor_pin) == 0

    def timer_callback(self):
        msg = Bool()
        msg.data = self._is_line_detected()
        self.publisher_.publish(msg)


def main(args=None):
    rclpy.init(args=args)

    line_sensor = LineSensorPublisher()

    rclpy.spin(line_sensor)

    line_sensor.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
