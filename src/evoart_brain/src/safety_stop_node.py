#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from evoart_interfaces.msg import YoloDetection
import time

class SafetyStopNode(Node):
    def __init__(self):
        super().__init__('safety_stop_node')
        
        # Subscribe to intended driving commands (from Nav2 or Teleop)
        self.cmd_sub = self.create_subscription(
            Twist,
            '/cmd_vel_nav',
            self.cmd_callback,
            10
        )
        
        # Subscribe to YOLO vision
        self.yolo_sub = self.create_subscription(
            YoloDetection,
            '/yolo/detections',
            self.yolo_callback,
            10
        )
        
        # Publisher to the actual motor controller / gazebo
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        self.person_detected_time = 0.0
        self.get_logger().info("Pedestrian Safety Reflex Online! Listening to /yolo/detections.")

    def yolo_callback(self, msg):
        # Check if the detected object is a person
        if msg.class_name == 'person':
            # Calculate bounding box area to estimate proximity
            # bbox is [x1, y1, x2, y2]
            width = msg.bbox[2] - msg.bbox[0]
            height = msg.bbox[3] - msg.bbox[1]
            area = width * height
            
            # If the person takes up a significant portion of the camera view, they are close
            # Using 40000 to correspond exactly to PEDESTRIAN_CLOSE_RANGE (2.0m)
            if area > 40000:
                self.person_detected_time = time.time()
                self.get_logger().warn(f"EMERGENCY BRAKE! Pedestrian detected very close! (Area: {area})")

    def cmd_callback(self, msg):
        # If a person was detected within the last 1.0 second, apply the brakes
        if time.time() - self.person_detected_time < 1.0:
            brake_msg = Twist()
            brake_msg.linear.x = 0.0
            brake_msg.angular.z = 0.0
            self.cmd_pub.publish(brake_msg)
        else:
            # Path is clear, pass the driving command through to the motors
            self.cmd_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = SafetyStopNode()
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
