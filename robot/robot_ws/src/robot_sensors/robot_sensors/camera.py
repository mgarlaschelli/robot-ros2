import subprocess
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

import cv2
from sensor_msgs.msg import CompressedImage

_CAMERA_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
)

# V4L2_PIX_FMT_SGBRG10P = 'pGAA' — packed 10-bit GBRG Bayer.
# Matches the format configured by the camera setup script, so VIDIOC_S_FMT
# requests the same format already set → no pipeline disruption.
_FOURCC_pGAA = cv2.VideoWriter_fourcc('p', 'G', 'A', 'A')


def debayer_pGAA(raw: np.ndarray, width: int, height: int) -> np.ndarray:
    """
    Unpack SGBRG10P (pGAA) packed 10-bit Bayer and debayer to BGR uint8.

    pGAA layout: every 4 pixels in 5 bytes.
      byte[0..3] = high 8 bits of pixels 0..3
      byte[4]    = low 2 bits packed as [P0[1:0] P1[1:0] P2[1:0] P3[1:0]]

    We extract only the high 8 bits for fast processing (good enough for JPEG).
    """
    flat = raw.reshape(-1)[:width * height * 10 // 8]
    groups = flat.reshape(height, width // 4, 5)   # (H, W/4, 5)
    bayer_8 = np.ascontiguousarray(groups[:, :, :4]).reshape(height, width)
    return cv2.cvtColor(bayer_8, cv2.COLOR_BayerGB2BGR)


class CameraPublisher(Node):
    def __init__(self):
        super().__init__('camera_publisher')

        self.declare_parameter('device', '/dev/video0')
        self.declare_parameter('subdev', '/dev/v4l-subdev0')
        self.declare_parameter('width', 640)
        self.declare_parameter('height', 480)
        self.declare_parameter('fps', 15)
        self.declare_parameter('jpeg_quality', 80)
        self.declare_parameter('exposure', 500)
        self.declare_parameter('analogue_gain', 1023)

        device = self.get_parameter('device').value
        self._subdev = self.get_parameter('subdev').value
        self._width = self.get_parameter('width').value
        self._height = self.get_parameter('height').value
        fps = self.get_parameter('fps').value
        self._jpeg_quality = self.get_parameter('jpeg_quality').value
        self._exposure = self.get_parameter('exposure').value
        self._analogue_gain = self.get_parameter('analogue_gain').value

        self.get_logger().info(
            f'Opening {device} at {self._width}x{self._height} {fps}fps'
        )

        self._cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
        # Request pGAA (= SGBRG10P) — the same format the setup script configured.
        # Calling VIDIOC_S_FMT with the current format leaves the pipeline intact.
        self._cap.set(cv2.CAP_PROP_FOURCC, _FOURCC_pGAA)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        self._cap.set(cv2.CAP_PROP_FPS, fps)
        # Return raw bytes — OpenCV cannot decode 10-bit packed Bayer natively.
        self._cap.set(cv2.CAP_PROP_CONVERT_RGB, 0)

        if not self._cap.isOpened():
            self.get_logger().error(f'Failed to open {device}')
            raise RuntimeError(f'Cannot open camera {device}')

        # Log the negotiated format to aid debugging.
        raw_fourcc = int(self._cap.get(cv2.CAP_PROP_FOURCC))
        fmt = ''.join(chr((raw_fourcc >> (i * 8)) & 0xFF) for i in range(4))
        self.get_logger().info(f'Negotiated format: {fmt!r}')

        # Re-apply sensor controls — some drivers reset them on VIDIOC_S_FMT.
        self._restore_controls()

        self._pub = self.create_publisher(CompressedImage, 'camera/compressed', _CAMERA_QOS)
        self.create_timer(1.0 / fps, self._timer_callback)
        self.get_logger().info('Camera node ready')

    def _restore_controls(self):
        """Re-apply sensor exposure and gain after OpenCV format negotiation."""
        for cmd in [
            ['v4l2-ctl', '-d', self._subdev, f'--set-ctrl=exposure={self._exposure}'],
            ['v4l2-ctl', '-d', self._subdev, f'--set-ctrl=analogue_gain={self._analogue_gain}'],
        ]:
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                self.get_logger().warn(f'{" ".join(cmd)} → {r.stderr.strip()}')

    def _timer_callback(self):
        ret, frame = self._cap.read()
        if not ret or frame is None:
            self.get_logger().warn('Failed to read frame')
            return

        try:
            bgr = debayer_pGAA(frame, self._width, self._height)
        except Exception as e:
            self.get_logger().warn(f'Debayer error (frame shape={frame.shape}): {e}')
            return

        ok, buf = cv2.imencode(
            '.jpg', bgr, [cv2.IMWRITE_JPEG_QUALITY, self._jpeg_quality]
        )
        if not ok:
            return

        msg = CompressedImage()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.format = 'jpeg'
        msg.data = buf.tobytes()
        self._pub.publish(msg)

    def destroy_node(self):
        self._cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CameraPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
