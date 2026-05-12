#!/usr/bin/env python3
"""
EVOART-O Safety Stop Node (Pedestrian Emergency Brake)
========================================================
Listens on /cmd_vel_nav (from Nav2 velocity smoother) and republishes
to /cmd_vel (consumed by Gazebo). If a pedestrian is detected too close,
the node applies an emergency brake (zero velocity).

Topic Chain:
  Nav2 Controller → /cmd_vel_raw → Velocity Smoother → /cmd_vel_nav → THIS NODE → /cmd_vel → Gazebo

IMPORTANT: Uses ROS clock (sim time) instead of wall clock for proper
simulation time synchronization.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from evoart_interfaces.msg import YoloDetection


class SafetyStopNode(Node):
    def __init__(self):
        super().__init__('safety_stop_node')

        # Subscribe to intended driving commands (from Nav2 velocity smoother)
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

        # Use ROS clock (sim time aware) instead of wall clock
        self.person_detected_time = self.get_clock().now()
        self.person_detected = False
        self.brake_duration = 1.0  # seconds

        # Forward timer: even if no /cmd_vel_nav arrives, ensure Gazebo
        # gets commands. This prevents the vehicle from being "stuck"
        # when Nav2 hasn't sent a command yet.
        self.last_cmd = Twist()
        self.forward_timer = self.create_timer(0.05, self.forward_tick)

        self.get_logger().info(
            "Pedestrian Safety Reflex Online! "
            "Listening to /cmd_vel_nav → /cmd_vel"
        )

    def yolo_callback(self, msg):
        # Check if the detected object is a person
        if msg.class_name == 'person':
            # Calculate bounding box area to estimate proximity
            # bbox is [x1, y1, x2, y2]
            width = msg.bbox[2] - msg.bbox[0]
            height = msg.bbox[3] - msg.bbox[1]
            area = width * height

            # If the person takes up a significant portion of the camera view, they are close
            # Assuming a 640x480 camera (307,200 pixels). 15000 is roughly 5% of the screen.
            if area > 15000:
                self.person_detected_time = self.get_clock().now()
                self.person_detected = True
                self.get_logger().warn(
                    f"EMERGENCY BRAKE! Pedestrian detected very close! (Area: {area})"
                )

    def _is_braking(self) -> bool:
        """Check if we should still be braking (within brake_duration of last detection)."""
        if not self.person_detected:
            return False
        elapsed = (self.get_clock().now() - self.person_detected_time).nanoseconds / 1e9
        if elapsed > self.brake_duration:
            self.person_detected = False
            return False
        return True

    def cmd_callback(self, msg):
        """Receive commands from Nav2 velocity smoother."""
        self.last_cmd = msg

    def forward_tick(self):
        """Forward (or brake) the latest command to Gazebo at a steady rate."""
        if self._is_braking():
            brake_msg = Twist()
            brake_msg.linear.x = 0.0
            brake_msg.angular.z = 0.0
            self.cmd_pub.publish(brake_msg)
        else:
            self.cmd_pub.publish(self.last_cmd)


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
