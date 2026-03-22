import queue
import time
import threading  # still used for _mode_lock and spin thread
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import String
from std_srvs.srv import Trigger

_LATCHED_QOS = QoSProfile(
    depth=1,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    reliability=ReliabilityPolicy.RELIABLE,
    history=HistoryPolicy.KEEP_LAST,
)

_CAMERA_QOS = QoSProfile(
    depth=1,
    durability=DurabilityPolicy.VOLATILE,
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
)

ROBOT_NS = "robot01"


class ControllerNode(Node):
    def __init__(self):
        super().__init__("web_controller")

        self._current_mode = "UNKNOWN"
        self._mode_lock = threading.Lock()
        self._camera_queue: queue.Queue = queue.Queue(maxsize=1)

        # Publisher: joystick velocity commands
        self._joy_pub = self.create_publisher(
            Twist, f"/{ROBOT_NS}/joy_cmd_vel", 10
        )

        # Subscription: current mode feedback — TRANSIENT_LOCAL matches the
        # robot publisher so late joiners receive the last published mode.
        self.create_subscription(
            String,
            f"/{ROBOT_NS}/controller/mode",
            self._mode_callback,
            _LATCHED_QOS,
        )

        # Subscription: camera frames — BEST_EFFORT matches the Pi publisher QoS
        self.create_subscription(
            CompressedImage,
            f'/{ROBOT_NS}/camera/compressed',
            self._camera_callback,
            _CAMERA_QOS,
        )

        # Service clients for mode switching (named _mode_clients to avoid
        # shadowing rclpy Node's internal self._clients list)
        self._mode_clients = {
            "STAND_BY": self.create_client(Trigger, f"/{ROBOT_NS}/controller/set_standby"),
            "PATROL":   self.create_client(Trigger, f"/{ROBOT_NS}/controller/set_patrol"),
            "MANUAL":   self.create_client(Trigger, f"/{ROBOT_NS}/controller/set_manual"),
        }

        self.get_logger().info("web_controller node initialized")

    # ------------------------------------------------------------------
    # Mode subscription callback (runs on spin thread)
    # ------------------------------------------------------------------

    def _mode_callback(self, msg: String):
        with self._mode_lock:
            self._current_mode = msg.data

    def _camera_callback(self, msg: CompressedImage):
        # Drain stale frame so the queue stays at depth 1 (drop old, keep new)
        if self._camera_queue.full():
            try:
                self._camera_queue.get_nowait()
            except queue.Empty:
                pass
        self._camera_queue.put_nowait(bytes(msg.data))

    def get_camera_queue(self) -> queue.Queue:
        return self._camera_queue

    def get_current_mode(self) -> str:
        with self._mode_lock:
            return self._current_mode

    def set_known_mode(self, mode: str):
        with self._mode_lock:
            self._current_mode = mode

    # ------------------------------------------------------------------
    # Joystick publishing (thread-safe: Publisher.publish is thread-safe)
    # ------------------------------------------------------------------

    def publish_joy(self, linear_x: float, angular_z: float):
        cmd = Twist()
        cmd.linear.x = float(linear_x)
        cmd.angular.z = float(angular_z)
        self._joy_pub.publish(cmd)

    # ------------------------------------------------------------------
    # Mode service call
    # Uses a fresh SingleThreadedExecutor to avoid deadlock with the
    # main spin thread. Must be called from a non-spin thread (e.g.
    # FastAPI's thread pool via run_in_executor).
    # ------------------------------------------------------------------

    def call_mode_service(self, mode: str) -> tuple[bool, str]:
        client = self._mode_clients.get(mode)
        if client is None:
            return False, f"Unknown mode: {mode}"

        if not client.wait_for_service(timeout_sec=2.0):
            return False, f"Service not available for mode {mode}"

        future = client.call_async(Trigger.Request())

        # Poll future.done() from this thread while the spin thread processes
        # the response. add_done_callback is unreliable when called from
        # outside the executor thread — polling is the correct cross-thread pattern.
        deadline = time.monotonic() + 5.0
        while not future.done():
            if time.monotonic() > deadline:
                return False, "Service call timed out"
            time.sleep(0.05)

        result = future.result()
        if result is None:
            return False, "Service call failed"
        return result.success, result.message


# ------------------------------------------------------------------
# Module-level singleton — initialised once in FastAPI lifespan
# ------------------------------------------------------------------

_node: ControllerNode | None = None
_spin_thread: threading.Thread | None = None


def start_ros(ros_args=None):
    global _node, _spin_thread
    rclpy.init(args=ros_args)
    _node = ControllerNode()
    _spin_thread = threading.Thread(target=rclpy.spin, args=(_node,), daemon=True)
    _spin_thread.start()


def stop_ros():
    global _node
    if _node:
        _node.destroy_node()
    rclpy.shutdown()


def get_node() -> ControllerNode:
    return _node
