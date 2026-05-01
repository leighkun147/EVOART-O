#!/usr/bin/env python3
"""
EVOART-O Odometry TF Broadcaster
====================================
Ultra-simple node that subscribes to /odom and publishes the
odom → base_link transform. Replaces the EKF for simulation use
where the Gazebo AckermannSteering plugin provides accurate odom
but does NOT publish TF.

Why not use EKF? The EKF adds complexity and can fail when sim time
synchronization is imperfect. This node just works.
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped


class OdomTfBroadcaster(Node):
    def __init__(self):
        super().__init__('odom_tf_broadcaster')
        self.tf_broadcaster = TransformBroadcaster(self)
        self.subscription = self.create_subscription(
            Odometry, '/odom', self.odom_callback, 10
        )
        self.get_logger().info('Odom→base_link TF broadcaster online!')

    def odom_callback(self, msg: Odometry):
        t = TransformStamped()
        t.header.stamp = msg.header.stamp
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        t.transform.translation.z = msg.pose.pose.position.z
        t.transform.rotation = msg.pose.pose.orientation
        self.tf_broadcaster.sendTransform(t)


def main(args=None):
    rclpy.init(args=args)
    node = OdomTfBroadcaster()
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
