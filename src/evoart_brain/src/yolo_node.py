#!/home/leykun/Desktop/EVOART-O/.venv/bin/python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2
import numpy as np

# Import our custom messages
from evoart_interfaces.msg import YoloDetection, TrafficStatus

class YoloPerceptionNode(Node):
    def __init__(self):
        super().__init__('yolo_perception_node')
        
        # Load the YOLOv8 model
        # Using the nano model for performance. In production, this would be the 
        # custom TEKNOFEST 22-class trained model path.
        self.get_logger().info("Loading YOLOv8 model...")
        self.model = YOLO("yolov8n.pt")
        self.get_logger().info("YOLOv8 model loaded successfully.")

        self.bridge = CvBridge()

        # Subscriptions
        self.image_sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )

        # Publishers
        self.detection_pub = self.create_publisher(YoloDetection, '/yolo/detections', 10)
        self.traffic_pub = self.create_publisher(TrafficStatus, '/yolo/traffic_lights', 10)
        
        # Optional: Publisher for debugging visual output
        self.debug_image_pub = self.create_publisher(Image, '/yolo/debug_image', 10)

    def determine_light_color(self, cv_image, box):
        """
        Heuristic to determine the color of a traffic light.
        Cropping the bounding box and looking for brightest red/green/yellow pixels.
        """
        x1, y1, x2, y2 = box
        crop = cv_image[y1:y2, x1:x2]
        if crop.size == 0:
            return "UNKNOWN"
            
        hsv_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        
        # Define ranges for Red, Green, Yellow
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([179, 255, 255])
        
        lower_green = np.array([40, 100, 100])
        upper_green = np.array([90, 255, 255])
        
        lower_yellow = np.array([15, 100, 100])
        upper_yellow = np.array([35, 255, 255])
        
        mask_red = cv2.inRange(hsv_crop, lower_red1, upper_red1) + cv2.inRange(hsv_crop, lower_red2, upper_red2)
        mask_green = cv2.inRange(hsv_crop, lower_green, upper_green)
        mask_yellow = cv2.inRange(hsv_crop, lower_yellow, upper_yellow)
        
        red_pixels = cv2.countNonZero(mask_red)
        green_pixels = cv2.countNonZero(mask_green)
        yellow_pixels = cv2.countNonZero(mask_yellow)
        
        max_pixels = max(red_pixels, green_pixels, yellow_pixels)
        if max_pixels < 5:  # Noise threshold
            return "UNKNOWN"
            
        if max_pixels == red_pixels:
            return "RED"
        elif max_pixels == green_pixels:
            return "GREEN"
        else:
            return "YELLOW"

    def image_callback(self, msg):
        try:
            # Convert ROS Image message to OpenCV image
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except Exception as e:
            self.get_logger().error(f"Failed to convert image: {e}")
            return

        # Run YOLO inference
        results = self.model(cv_image, verbose=False)

        # We assume one image per batch
        for r in results:
            boxes = r.boxes
            for box in boxes:
                # Extract coordinates, score, and class
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                class_name = self.model.names[cls]

                # Publish raw detection
                det_msg = YoloDetection()
                det_msg.class_name = class_name
                det_msg.score = conf
                det_msg.bbox = [x1, y1, x2, y2]
                self.detection_pub.publish(det_msg)

                # Specifically handle Traffic Lights & Stop Signs for the Behavior Tree
                if class_name == 'traffic light':
                    color = self.determine_light_color(cv_image, (x1, y1, x2, y2))
                    ts_msg = TrafficStatus()
                    ts_msg.light_state = color
                    ts_msg.sign_type = "traffic_light"
                    ts_msg.stop_required = (color == "RED" or color == "YELLOW")
                    self.traffic_pub.publish(ts_msg)
                
                elif class_name == 'stop sign':
                    ts_msg = TrafficStatus()
                    ts_msg.light_state = "NONE"
                    ts_msg.sign_type = "stop_sign"
                    ts_msg.stop_required = True
                    self.traffic_pub.publish(ts_msg)

            # Publish annotated debug image
            if self.debug_image_pub.get_subscription_count() > 0:
                annotated_frame = r.plot()
                debug_msg = self.bridge.cv2_to_imgmsg(annotated_frame, "bgr8")
                self.debug_image_pub.publish(debug_msg)

def main(args=None):
    rclpy.init(args=args)
    node = YoloPerceptionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
