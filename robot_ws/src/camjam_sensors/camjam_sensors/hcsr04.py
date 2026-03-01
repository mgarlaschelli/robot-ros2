import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Range
from RPi import GPIO
import time
from typing import Optional

DEFAULT_PIN_TRIGGER = 17
DEFAULT_PIN_ECHO = 18


class HcSr04Publisher(Node):
    def __init__(self):
        super().__init__("hc_sr04_publisher")

        # Declare and set parameters
        self.declare_parameter("trigger_pin", DEFAULT_PIN_TRIGGER)
        self.declare_parameter("echo_pin", DEFAULT_PIN_ECHO)
        self._pin_trigger = self.get_parameter("trigger_pin").value
        self._pin_echo = self.get_parameter("echo_pin").value

        # Pin setup
        self.get_logger().info("Setting up pins for sensor")
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self._pin_trigger, GPIO.OUT)
        GPIO.setup(self._pin_echo, GPIO.IN)
        time.sleep(0.5)

        self.get_logger().info("Pins ready, initialising publisher...")
        self.publisher_ = self.create_publisher(Range, "distance", 10)
        timer_period = 0.25
        self.timer = self.create_timer(timer_period, self.timer_callback)

        self.get_logger().info("Distance sensor init complete!")

    def _read_distance(self) -> Optional[float]:
        # Send 10us pulse to trigger
        GPIO.output(self._pin_trigger, True)
        time.sleep(0.00001)
        GPIO.output(self._pin_trigger, False)

        # Reset start time until echo is high
        start_time = time.time()
        while GPIO.input(self._pin_echo) == 0:
            start_time = time.time()

        # Stop when echo pin is low again
        stop_time = start_time
        while GPIO.input(self._pin_echo) == 1:
            stop_time = time.time()
            # If pulse takes too long to return, we missed it from object being too close
            if stop_time - start_time >= 0.04:
                self._logger.warn("Object is too close to see! Dropping...")
                return None

        # Calculate pulse length
        elapsed = stop_time - start_time
        distance = elapsed * 34326
        distance = distance / 2

        return distance

    def timer_callback(self):
        msg = Range()
        msg.range = self._read_distance()
        if msg.range is not None:
            self.publisher_.publish(msg)


def main(args=None):
    rclpy.init(args=args)

    hcsr04 = HcSr04Publisher()

    rclpy.spin(hcsr04)

    hcsr04.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
