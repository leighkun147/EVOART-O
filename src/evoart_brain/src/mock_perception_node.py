#!/usr/bin/env python3
"""
EVOART-O Mock Perception Node (Ground-Truth Simulator)
=========================================================
Replaces the live YOLO model with deterministic, ground-truth perception
data derived from the vehicle's known position in the Gazebo world.

This node:
  1. Subscribes to /odom to know the vehicle's position.
  2. Checks proximity to known pedestrian actor waypoints.
  3. Checks proximity to known traffic light positions.
  4. Publishes YoloDetection and TrafficStatus messages exactly as the
     real YOLO node would — the downstream Safety Stop and Behavior Tree
     nodes cannot tell the difference.

Why: Running live YOLO inference during early navigation testing wastes
GPU cycles and introduces non-deterministic latency. This node gives us
repeatable, physics-accurate perception for route testing.
"""

import math
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from evoart_interfaces.msg import YoloDetection, TrafficStatus


# ── Ground-truth positions from teknofest_city.sdf ──
# Pedestrian actor trajectories (center of their patrol path)
PEDESTRIAN_POSITIONS = [
    (5.0, 0.0),    # pedestrian_0: crosses E-W road at x=5
    (0.0, 10.0),   # pedestrian_1: crosses N-S road at y=10
    (20.0, 20.0),  # pedestrian_2: crosses at northern road
]

# Traffic light positions from the SDF
TRAFFIC_LIGHT_POSITIONS = [
    (-3.0, 3.0),     # traffic_light_0
    (17.0, 3.0),     # traffic_light_1
    (23.0, -3.0),    # traffic_light_2
    (-3.0, 23.0),    # traffic_light_3
    (37.0, 3.0),     # traffic_light_4
]

# Stop sign positions from the SDF
STOP_SIGN_POSITIONS = [
    (-2.0, -3.0),
    (18.0, -3.0),
    (22.0, 3.0),
    (-2.0, 17.0),
    (38.0, -3.0),
]

# Detection thresholds (meters) — IP-7 Spec: 3-5m trigger radius
PEDESTRIAN_DETECT_RANGE = 8.0    # Camera FOV range
PEDESTRIAN_CLOSE_RANGE = 3.0     # Emergency brake range
TRAFFIC_LIGHT_DETECT_RANGE = 5.0  # IP-7: 3-5m trigger zone
STOP_SIGN_DETECT_RANGE = 5.0      # IP-7: 3-5m trigger zone


class MockPerceptionNode(Node):
    """Publishes ground-truth detections based on vehicle odometry."""

    def __init__(self):
        super().__init__('mock_perception')

        # Odometry subscription
        self.odom_sub = self.create_subscription(
            Odometry, '/odom', self.odom_callback, 10
        )

        # Publishers — same topics as the real YOLO node
        self.detection_pub = self.create_publisher(
            YoloDetection, '/yolo/detections', 10
        )
        self.traffic_pub = self.create_publisher(
            TrafficStatus, '/yolo/traffic_lights', 10
        )

        # Vehicle position
        self.x = 0.0
        self.y = 0.0

        # Traffic light state machine (shared with traffic_light_node.py)
        # We subscribe to it instead of duplicating
        self.traffic_state_sub = self.create_subscription(
            TrafficStatus, '/traffic_light/status',
            self.traffic_state_callback, 10
        )
        self.current_light_state = "GREEN"
        self.current_stop_required = False

        # Publish at 10 Hz (IP-7 spec: consistent 10Hz stream)
        self.timer = self.create_timer(0.1, self.tick)

        self.get_logger().info(
            "Mock Perception Online! "
            f"Tracking {len(PEDESTRIAN_POSITIONS)} pedestrians, "
            f"{len(TRAFFIC_LIGHT_POSITIONS)} traffic lights, "
            f"{len(STOP_SIGN_POSITIONS)} stop signs."
        )

    def odom_callback(self, msg: Odometry):
        """Update vehicle position from odometry."""
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y

    def traffic_state_callback(self, msg: TrafficStatus):
        """Receive ground-truth traffic light state from the simulator."""
        self.current_light_state = msg.light_state
        self.current_stop_required = msg.stop_required

    def _distance_to(self, px: float, py: float) -> float:
        return math.hypot(self.x - px, self.y - py)

    def _range_to_bbox_area(self, distance: float, close_range: float) -> int:
        """
        Convert a physical distance to a simulated bounding box area.
        At close_range, the person fills ~20% of the 640x480 frame.
        Area falls off with the square of distance.
        """
        if distance <= 0.5:
            return 60000  # Very close
        ratio = (close_range / distance) ** 2
        return int(60000 * min(ratio, 1.0))

    def tick(self):
        """Scan all known objects and publish detections."""

        # ── Pedestrians ──
        for i, (px, py) in enumerate(PEDESTRIAN_POSITIONS):
            dist = self._distance_to(px, py)
            if dist < PEDESTRIAN_DETECT_RANGE:
                area = self._range_to_bbox_area(dist, PEDESTRIAN_CLOSE_RANGE)
                # Simulate a bounding box centered in the frame
                cx, cy = 320, 240
                half_w = int(math.sqrt(area) / 2)
                half_h = int(math.sqrt(area) * 0.75)

                det = YoloDetection()
                det.class_name = 'person'
                det.score = max(0.3, min(0.99, 1.0 - dist / PEDESTRIAN_DETECT_RANGE))
                det.bbox = [
                    cx - half_w, cy - half_h,
                    cx + half_w, cy + half_h
                ]
                self.detection_pub.publish(det)

                if dist < PEDESTRIAN_CLOSE_RANGE:
                    self.get_logger().warn(
                        f"[MOCK] Pedestrian {i} at {dist:.1f}m — bbox area {area}"
                    )

        # ── Traffic Lights ──
        for i, (tx, ty) in enumerate(TRAFFIC_LIGHT_POSITIONS):
            dist = self._distance_to(tx, ty)
            if dist < TRAFFIC_LIGHT_DETECT_RANGE:
                # Publish as both a detection and a traffic status
                det = YoloDetection()
                det.class_name = 'traffic light'
                det.score = max(0.4, min(0.95, 1.0 - dist / TRAFFIC_LIGHT_DETECT_RANGE))
                det.bbox = [300, 50, 340, 150]
                self.detection_pub.publish(det)

                ts = TrafficStatus()
                ts.light_state = self.current_light_state
                ts.sign_type = "traffic_light"
                ts.stop_required = self.current_stop_required
                self.traffic_pub.publish(ts)

        # ── Stop Signs ──
        for i, (sx, sy) in enumerate(STOP_SIGN_POSITIONS):
            dist = self._distance_to(sx, sy)
            if dist < STOP_SIGN_DETECT_RANGE:
                det = YoloDetection()
                det.class_name = 'stop sign'
                det.score = max(0.5, min(0.98, 1.0 - dist / STOP_SIGN_DETECT_RANGE))
                det.bbox = [280, 100, 360, 200]
                self.detection_pub.publish(det)

                ts = TrafficStatus()
                ts.light_state = "NONE"
                ts.sign_type = "stop_sign"
                ts.stop_required = True
                self.traffic_pub.publish(ts)


def main(args=None):
    rclpy.init(args=args)
    node = MockPerceptionNode()
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
