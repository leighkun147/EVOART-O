import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node, SetParameter
import xacro

def generate_launch_description():
    pkg_description = get_package_share_directory('evoart_description')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    pkg_bringup = get_package_share_directory('evoart_bringup')

    xacro_file = os.path.join(pkg_description, 'urdf', 'evoart.xacro')
    doc = xacro.process_file(xacro_file)
    robot_description = {'robot_description': doc.toxml()}

    # ── Global sim time ──
    use_sim_time = SetParameter(name='use_sim_time', value=True)

    # ── Robot State Publisher ──
    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description]
    )

    # ── Gazebo Harmonic ──
    world_path = os.path.join(pkg_bringup, 'worlds', 'teknofest_city.sdf')
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r {world_path}'}.items()
    )

    # ── Spawn vehicle on the road ──
    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'evoart',
            '-topic', 'robot_description',
            '-x', '2.0',
            '-y', '0.0',
            '-z', '0.5',
        ],
        output='screen'
    )

    # ── ROS↔Gazebo Bridge ──
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            # Clock (CRITICAL: required for use_sim_time)
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            # ROS → Gazebo
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            # Gazebo → ROS
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
            '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
        ],
        output='screen'
    )

    return LaunchDescription([
        use_sim_time,
        rsp,
        gazebo,
        spawn,
        bridge
    ])
