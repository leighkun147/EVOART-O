#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial
import struct
import math
import time

class AksBridgeNode(Node):
    def __init__(self):
        super().__init__('aks_bridge_node')
        
        self.declare_parameter('serial_port', '/dev/AKS')
        self.declare_parameter('baud_rate', 115200)
        self.declare_parameter('wheelbase', 1.425)  # meters
        self.declare_parameter('max_steering_angle', 22.5)  # degrees
        
        port = self.get_parameter('serial_port').value
        baud = self.get_parameter('baud_rate').value
        self.wheelbase = self.get_parameter('wheelbase').value
        self.max_steering_angle = self.get_parameter('max_steering_angle').value
        
        # Connect to UART
        try:
            self.serial_conn = serial.Serial(port, baud, timeout=0.1)
            self.get_logger().info(f"Successfully connected to AKS Motor Controller on {port} at {baud} baud.")
        except serial.SerialException as e:
            self.get_logger().error(f"Failed to connect to UART port {port}: {e}")
            self.get_logger().warn("Running in simulation/dry-run mode (no physical UART connection).")
            self.serial_conn = None
            
        self.cmd_vel_sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )
        
    def calculate_crc8(self, data):
        """Simple CRC-8 algorithm for checksum"""
        crc = 0x00
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x07
                else:
                    crc <<= 1
                crc &= 0xFF
        return crc

    def cmd_vel_callback(self, msg):
        linear_vel = msg.linear.x
        angular_vel = msg.angular.z
        
        # Calculate Ackermann Steering Angle
        # tan(theta) = wheelbase / turning_radius
        # turning_radius = linear_vel / angular_vel
        # Therefore, tan(theta) = (wheelbase * angular_vel) / linear_vel
        if abs(linear_vel) > 0.01:
            steering_rad = math.atan((self.wheelbase * angular_vel) / linear_vel)
        else:
            # If not moving forward, map angular velocity directly to steering
            # Assuming max angular velocity yields max steering
            steering_rad = math.copysign(1.0, angular_vel) * math.radians(self.max_steering_angle) if angular_vel != 0 else 0.0
            
        steering_deg = math.degrees(steering_rad)
        
        # Clamp steering angle to physical limits
        steering_deg = max(min(steering_deg, self.max_steering_angle), -self.max_steering_angle)
        
        self.send_uart_packet(linear_vel, steering_deg)

    def send_uart_packet(self, speed, steering):
        """
        Constructs and sends a 32-byte packet to the AKS board.
        Packet Structure (Example 32 bytes):
        [0:2]   Header (0xAA 0x55)
        [2]     Command Type (0x01 = Drive)
        [3:7]   Speed (Float32, Little Endian)
        [7:11]  Steering (Float32, Little Endian)
        [11:30] Reserved/Padding
        [30]    CRC-8 Checksum
        [31]    Footer (0xFF)
        """
        header = b'\xAA\x55'
        cmd_type = struct.pack('B', 0x01)
        payload = struct.pack('<ff', speed, steering)
        padding = bytes([0x00] * 19)
        
        data_to_crc = header + cmd_type + payload + padding
        crc = self.calculate_crc8(data_to_crc)
        
        packet = data_to_crc + struct.pack('B', crc) + b'\xFF'
        
        if len(packet) != 32:
            self.get_logger().error(f"Packet size mismatch! Expected 32, got {len(packet)}")
            return
            
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write(packet)
            except Exception as e:
                self.get_logger().error(f"UART write failed: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = AksBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.serial_conn and node.serial_conn.is_open:
            # Send stop command before shutting down
            node.send_uart_packet(0.0, 0.0)
            node.serial_conn.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
