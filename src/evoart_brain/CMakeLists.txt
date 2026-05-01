cmake_minimum_required(VERSION 3.8)
project(evoart_brain)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(nav2_behavior_tree REQUIRED)
find_package(behaviortree_cpp REQUIRED)
find_package(evoart_interfaces REQUIRED)

# Install configuration directories
install(DIRECTORY
  config
  behavior_trees
  DESTINATION share/${PROJECT_NAME}
)

# Install Python nodes
install(PROGRAMS
  src/yolo_node.py
  src/aks_bridge_node.py
  src/safety_stop_node.py
  src/traffic_light_node.py
  src/mock_perception_node.py
  src/geojson_navigator_node.py
  src/odom_tf_broadcaster.py
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
