import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
import cv2
import numpy as np
import color_lib

class CompressedImageViewer(Node):
    def __init__(self, mak):
        super().__init__('compressed_image_viewer')
        self.mak = mak
        self.mak.PrepareWindow()

        self.subscription = self.create_subscription(
            CompressedImage,
            '/camera/image_raw/compressed',
            self.listener_callback,
            10
        )

        self.frame = None
        self.frame_captured = False  # flag to store only the first frame

    def listener_callback(self, msg):
        if not self.frame_captured:
            np_arr = np.frombuffer(msg.data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if frame is not None:
                self.frame = frame.copy()
                self.frame_captured = True

    def process_loop(self):
        if self.frame is None:
            return

        while True:
            self.mak.BruteForce(self.frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

def main(args=None):
    rclpy.init(args=args)
    mak = color_lib.DataMaker()
    node = CompressedImageViewer(mak)

    try:
        while not node.frame_captured:
            rclpy.spin_once(node)
        node.process_loop()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()

