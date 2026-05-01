import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node, SetParameter

def generate_launch_description():
    pkg_bringup = get_package_share_directory('evoart_bringup')
    pkg_brain = get_package_share_directory('evoart_brain')

    nav2_params = os.path.join(pkg_brain, 'config', 'nav2_params.yaml')
    ekf_params = os.path.join(pkg_brain, 'config', 'ekf.yaml')
    slam_params = os.path.join(pkg_brain, 'config', 'slam_params.yaml')
    bt_xml = os.path.join(pkg_brain, 'behavior_trees', 'taxi_logic.xml')

    # ── Global sim time ──
    use_sim_time = SetParameter(name='use_sim_time', value=True)

    # ═══════════════════════════════════════════════════
    # Layer 1: The Body (Gazebo Simulation)
    # ═══════════════════════════════════════════════════
    sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'sim.launch.py')
        )
    )

    # ═══════════════════════════════════════════════════
    # Layer 2: The Eyes (YOLO Perception)
    # ═══════════════════════════════════════════════════
    # Delay to give Gazebo time to bridge the camera topic
    yolo_node = TimerAction(
        period=5.0,
        actions=[
            Node(
                package='evoart_brain',
                executable='yolo_node.py',
                name='yolo_perception',
                output='screen'
            )
        ]
    )

    # ═══════════════════════════════════════════════════
    # Layer 3: The Reflexes (Safety & Traffic Light Sim)
    # ═══════════════════════════════════════════════════
    safety_node = Node(
        package='evoart_brain',
        executable='safety_stop_node.py',
        name='safety_stop',
        output='screen'
    )

    traffic_light_node = Node(
        package='evoart_brain',
        executable='traffic_light_node.py',
        name='traffic_light_sim',
        output='screen',
        parameters=[{
            'green_duration': 30.0,
            'yellow_duration': 5.0,
            'red_duration': 30.0,
        }]
    )

    # ═══════════════════════════════════════════════════
    # Layer 4: The Inner Ear (Sensor Fusion / EKF)
    # ═══════════════════════════════════════════════════
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_params]
    )

    # ═══════════════════════════════════════════════════
    # Layer 5: The Mapper (SLAM Toolbox)
    # ═══════════════════════════════════════════════════
    slam_node = TimerAction(
        period=8.0,
        actions=[
            Node(
                package='slam_toolbox',
                executable='async_slam_toolbox_node',
                name='slam_toolbox',
                output='screen',
                parameters=[slam_params]
            )
        ]
    )

    # ═══════════════════════════════════════════════════
    # Layer 6: The Higher Brain (Nav2 Stack)
    # ═══════════════════════════════════════════════════

    nav2_planner = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=[nav2_params]
    )

    nav2_controller = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[nav2_params]
    )

    nav2_bt_navigator = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=[nav2_params, {'default_bt_xml_filename': bt_xml}]
    )

    nav2_behaviors = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        output='screen',
        parameters=[nav2_params]
    )

    nav2_velocity_smoother = Node(
        package='nav2_velocity_smoother',
        executable='velocity_smoother',
        name='velocity_smoother',
        output='screen',
        parameters=[nav2_params]
    )

    nav2_lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[{
            'autostart': True,
            'node_names': [
                'planner_server',
                'controller_server',
                'bt_navigator',
                'behavior_server',
                'velocity_smoother',
            ]
        }]
    )

    # Delayed Nav2 launch to ensure simulation + SLAM are ready
    nav2_delayed = TimerAction(
        period=12.0,
        actions=[
            nav2_planner,
            nav2_controller,
            nav2_bt_navigator,
            nav2_behaviors,
            nav2_velocity_smoother,
            nav2_lifecycle_manager,
        ]
    )

    return LaunchDescription([
        use_sim_time,
        sim_launch,
        safety_node,
        traffic_light_node,
        yolo_node,
        ekf_node,
        slam_node,
        nav2_delayed,
    ])
