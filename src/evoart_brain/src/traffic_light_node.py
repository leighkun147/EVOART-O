#!/usr/bin/env python3
"""
EVOART-O Traffic Light Simulator Node
=======================================
Simulates a traffic light state machine and publishes TrafficStatus messages
on the same topics the Behavior Tree consumes. In the real competition,
YOLO handles traffic light detection; this node provides ground truth for
simulation-based testing.

Cycle: GREEN (30s) → YELLOW (5s) → RED (30s)
"""

import rclpy
from rclpy.node import Node
from evoart_interfaces.msg import TrafficStatus


class TrafficLightNode(Node):
    """Cyclic traffic light state publisher for simulation testing."""

    # State machine: (state_name, duration_param, stop_required)
    STATES = [
        ("GREEN",  "green_duration",  False),
        ("YELLOW", "yellow_duration", True),
        ("RED",    "red_duration",    True),
    ]

    def __init__(self):
        super().__init__('traffic_light_sim')

        # Declare configurable parameters
        self.declare_parameter('green_duration', 30.0)
        self.declare_parameter('yellow_duration', 5.0)
        self.declare_parameter('red_duration', 30.0)

        # Publishers — publish on both topics so the BT and any other
        # subscribers can consume the data
        self.status_pub = self.create_publisher(
            TrafficStatus, '/traffic_light/status', 10
        )
        self.yolo_traffic_pub = self.create_publisher(
            TrafficStatus, '/yolo/traffic_lights', 10
        )

        # State machine
        self.state_index = 0
        self.elapsed = 0.0
        self.tick_rate = 1.0  # Hz

        # Timer for periodic publishing
        self.timer = self.create_timer(1.0 / self.tick_rate, self.tick)

        state_name = self.STATES[self.state_index][0]
        self.get_logger().info(
            f"Traffic Light Simulator Online! Starting state: {state_name}"
        )

    def _get_current_duration(self) -> float:
        """Get the duration for the current state from parameters."""
        _, param_name, _ = self.STATES[self.state_index]
        return self.get_parameter(param_name).get_parameter_value().double_value

    def tick(self):
        """Advance the state machine and publish the current light state."""
        state_name, _, stop_required = self.STATES[self.state_index]
        duration = self._get_current_duration()

        # Publish current state
        msg = TrafficStatus()
        msg.light_state = state_name
        msg.sign_type = "traffic_light"
        msg.stop_required = stop_required

        self.status_pub.publish(msg)
        self.yolo_traffic_pub.publish(msg)

        # Advance timer
        self.elapsed += 1.0 / self.tick_rate

        # Transition to next state?
        if self.elapsed >= duration:
            self.elapsed = 0.0
            self.state_index = (self.state_index + 1) % len(self.STATES)
            new_state = self.STATES[self.state_index][0]
            self.get_logger().info(f"Traffic light → {new_state}")


def main(args=None):
    rclpy.init(args=args)
    node = TrafficLightNode()
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
