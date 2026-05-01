#!/usr/bin/env python3
"""
EVOART-O GeoJSON Route Navigator
===================================
Parses a GeoJSON LineString route file and sends sequential Nav2
goal poses to drive the vehicle from Point A through all waypoints
to Point B.

GeoJSON coordinates are interpreted as local (x, y) positions in the
Gazebo simulation frame (meters), NOT as GPS lat/lon. For the real
competition, a coordinate transform from WGS84 → local would be added.

Usage:
  The node reads the route file path from the 'route_file' parameter,
  waits for the Nav2 action server, then sends goals one by one.
"""

import json
import math

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
from action_msgs.msg import GoalStatus


class GeoJsonNavigator(Node):
    """Reads a GeoJSON route and sends waypoints to Nav2."""

    def __init__(self):
        super().__init__('geojson_navigator')

        # Parameters
        self.declare_parameter('route_file', '')
        self.declare_parameter('goal_frame', 'map')
        self.declare_parameter('wait_at_waypoint', 2.0)  # seconds to pause at each waypoint

        route_file = self.get_parameter('route_file').get_parameter_value().string_value
        self.goal_frame = self.get_parameter('goal_frame').get_parameter_value().string_value
        self.wait_duration = self.get_parameter('wait_at_waypoint').get_parameter_value().double_value

        if not route_file:
            self.get_logger().error("No route_file parameter provided! Shutting down.")
            raise SystemExit(1)

        # Parse the GeoJSON route
        self.waypoints = self._load_geojson(route_file)
        if not self.waypoints:
            self.get_logger().error("No waypoints found in GeoJSON! Shutting down.")
            raise SystemExit(1)

        self.get_logger().info(
            f"GeoJSON Navigator loaded {len(self.waypoints)} waypoints from: {route_file}"
        )
        for i, (x, y) in enumerate(self.waypoints):
            label = "START" if i == 0 else ("END" if i == len(self.waypoints) - 1 else f"WP-{i}")
            self.get_logger().info(f"  [{label}] x={x:.1f}, y={y:.1f}")

        # Nav2 action client
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.current_wp_index = 0

        # Wait for Nav2 to be ready, then start navigation
        self.get_logger().info("Waiting for Nav2 navigate_to_pose action server...")
        self.startup_timer = self.create_timer(2.0, self._check_nav2_ready)

    def _load_geojson(self, filepath: str) -> list[tuple[float, float]]:
        """Parse GeoJSON and extract LineString coordinates as (x, y) tuples."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.get_logger().error(f"Failed to load GeoJSON: {e}")
            return []

        waypoints = []
        for feature in data.get('features', []):
            geom = feature.get('geometry', {})
            if geom.get('type') == 'LineString':
                for coord in geom.get('coordinates', []):
                    # GeoJSON convention: [x, y] (or [lon, lat])
                    # In our local frame: [x_meters, y_meters]
                    waypoints.append((float(coord[0]), float(coord[1])))
            elif geom.get('type') == 'Point':
                coord = geom.get('coordinates', [])
                if len(coord) >= 2:
                    waypoints.append((float(coord[0]), float(coord[1])))

        return waypoints

    def _check_nav2_ready(self):
        """Poll until Nav2 action server is available."""
        if self.nav_client.wait_for_server(timeout_sec=0.5):
            self.get_logger().info("Nav2 is ready! Starting route execution...")
            self.startup_timer.cancel()
            self._send_next_goal()
        else:
            self.get_logger().info("Still waiting for Nav2...")

    def _send_next_goal(self):
        """Send the next waypoint as a Nav2 goal."""
        if self.current_wp_index >= len(self.waypoints):
            self.get_logger().info("═══ ROUTE COMPLETE! All waypoints reached. ═══")
            return

        x, y = self.waypoints[self.current_wp_index]

        # Calculate yaw towards the NEXT waypoint (or 0 if last)
        yaw = 0.0
        if self.current_wp_index < len(self.waypoints) - 1:
            nx, ny = self.waypoints[self.current_wp_index + 1]
            yaw = math.atan2(ny - y, nx - x)

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = PoseStamped()
        goal_msg.pose.header.frame_id = self.goal_frame
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.position.z = 0.0

        # Convert yaw to quaternion (rotation around z-axis only)
        goal_msg.pose.pose.orientation.x = 0.0
        goal_msg.pose.pose.orientation.y = 0.0
        goal_msg.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal_msg.pose.pose.orientation.w = math.cos(yaw / 2.0)

        wp_label = f"[{self.current_wp_index + 1}/{len(self.waypoints)}]"
        self.get_logger().info(
            f"Navigating to waypoint {wp_label}: "
            f"x={x:.1f}, y={y:.1f}, yaw={math.degrees(yaw):.0f}°"
        )

        send_goal_future = self.nav_client.send_goal_async(
            goal_msg,
            feedback_callback=self._feedback_callback
        )
        send_goal_future.add_done_callback(self._goal_response_callback)

    def _goal_response_callback(self, future):
        """Handle goal acceptance/rejection."""
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("Goal was rejected by Nav2!")
            return

        self.get_logger().info("Goal accepted by Nav2, executing...")
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._goal_result_callback)

    def _feedback_callback(self, feedback_msg):
        """Log navigation progress."""
        feedback = feedback_msg.feedback
        remaining = feedback.distance_remaining
        if remaining > 0:
            self.get_logger().info(
                f"  Distance remaining: {remaining:.1f}m",
                throttle_duration_sec=5.0
            )

    def _goal_result_callback(self, future):
        """Handle goal completion — advance to next waypoint."""
        result = future.result()
        status = result.status

        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info(
                f"✅ Waypoint {self.current_wp_index + 1} reached!"
            )
            self.current_wp_index += 1

            # Brief pause at waypoint (e.g., for stop sign compliance)
            if self.current_wp_index < len(self.waypoints):
                self.create_timer(
                    self.wait_duration,
                    lambda: self._send_next_goal(),
                    # One-shot timer
                ).cancel()
                self._send_next_goal()
        else:
            self.get_logger().warn(
                f"⚠ Goal failed with status {status}. Retrying..."
            )
            # Retry the same waypoint
            self._send_next_goal()


def main(args=None):
    rclpy.init(args=args)
    try:
        node = GeoJsonNavigator()
        rclpy.spin(node)
    except SystemExit:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
