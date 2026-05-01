"""
EVOART-O Unified Full Simulation Launch
==========================================
Zero-Manual-Effort launcher:

  1. Gazebo Harmonic city world + vehicle spawn + ROS↔GZ bridge
  2. Static map→odom TF (identity)
  3. Odom TF Broadcaster (odom→base_link from /odom messages)
  4. Mock Perception + Traffic Light Sim + Safety Stop
  5. SLAM Toolbox (mapping)
  6. Full Nav2 Stack
  7. GeoJSON Route Navigator

TF Chain:
  map → odom           (static_transform_publisher)
  odom → base_link     (odom_tf_broadcaster.py from /odom)
  base_link → chassis  (robot_state_publisher from URDF)
  chassis → velodyne   (robot_state_publisher from URDF)

Usage:
  source install/setup.bash
  ros2 launch evoart_bringup sim_full.launch.py
"""

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
    slam_params = os.path.join(pkg_brain, 'config', 'slam_params.yaml')
    bt_xml = os.path.join(pkg_brain, 'behavior_trees', 'taxi_logic.xml')
    route_file = os.path.join(pkg_brain, 'config', 'route.geojson')

    use_sim_time = SetParameter(name='use_sim_time', value=True)

    # ═══ LAYER 1: Gazebo Simulation ═══
    sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'sim.launch.py')
        )
    )

    # ═══ LAYER 2: TF Foundation ═══
    # Static map→odom (identity). SLAM will refine later.
    static_map_to_odom = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_map_to_odom',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom'],
        output='screen'
    )

    # odom→base_link from /odom messages.
    # The Gazebo Ackermann plugin publishes /odom DATA but NOT TF.
    # This tiny node bridges that gap.
    odom_tf_node = Node(
        package='evoart_brain',
        executable='odom_tf_broadcaster.py',
        name='odom_tf_broadcaster',
        output='screen'
    )

    # ═══ LAYER 3: Perception & Reflexes ═══
    mock_perception_node = TimerAction(
        period=5.0,
        actions=[
            Node(
                package='evoart_brain',
                executable='mock_perception_node.py',
                name='mock_perception',
                output='screen'
            )
        ]
    )

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

    # ═══ LAYER 4: SLAM (mapping) ═══
    slam_node = TimerAction(
        period=10.0,
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

    # ═══ LAYER 5: Nav2 Stack ═══
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

    nav2_delayed = TimerAction(
        period=15.0,
        actions=[
            nav2_planner,
            nav2_controller,
            nav2_bt_navigator,
            nav2_behaviors,
            nav2_velocity_smoother,
            nav2_lifecycle_manager,
        ]
    )

    # ═══ LAYER 6: GeoJSON Route Navigator ═══
    geojson_navigator = TimerAction(
        period=30.0,
        actions=[
            Node(
                package='evoart_brain',
                executable='geojson_navigator_node.py',
                name='geojson_navigator',
                output='screen',
                parameters=[{
                    'route_file': route_file,
                    'goal_frame': 'map',
                    'wait_at_waypoint': 2.0,
                }]
            )
        ]
    )

    return LaunchDescription([
        use_sim_time,
        # Layer 1: Simulation
        sim_launch,
        # Layer 2: TF (must start immediately)
        static_map_to_odom,
        odom_tf_node,
        # Layer 3: Perception & Reflexes
        safety_node,
        traffic_light_node,
        mock_perception_node,
        # Layer 4: Mapping
        slam_node,
        # Layer 5: Navigation
        nav2_delayed,
        # Layer 6: Mission
        geojson_navigator,
    ])
