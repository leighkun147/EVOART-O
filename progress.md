# EVOART-O Project Progress

This document tracks the progress of the EVOART-O Autonomous RoboTaxi setup for the 2026 TEKNOFEST competition.

## Completed Tasks

### 1. Project Documentation
- [x] Analyzed the TEKNOFEST 2026 specifications and team management documentation.
- [x] Generated a comprehensive `README.md` containing competition lap matrices, exact scoring algorithms, 22-class detection goals, team structure, and software architecture.

### 2. The Nervous System (`evoart_interfaces`)
- [x] Created `YoloDetection.msg` for bounding boxes, scores, and classifications.
- [x] Created `TrafficStatus.msg` for traffic light states and sign rules.
- [x] Configured `CMakeLists.txt` with `rosidl_generate_interfaces`.
- [x] Created a valid `package.xml` defining build and runtime message dependencies.
- [x] Verified build success for the interfaces package.

### 3. The Navigation Brain (`evoart_brain`)
- [x] Populated `config/nav2_params.yaml` with the `SmacPlannerHybrid` and `MPPIController` configurations, adhering to the 1.425m Ackermann wheelbase and 1.5m turning radius.
- [x] Authored the `behavior_trees/robotaxi_bt.xml` file with fallback rules for traffic lights and recovery pipelines.
- [x] Updated `package.xml` to include critical dependencies: `nav2_behavior_tree`, `behaviortree_cpp_v3`, and `evoart_interfaces`.

### 4. Build Validation
- [x] Successfully ran `colcon build --packages-up-to evoart_brain` without fatal errors.

### 5. Digital Twin and Simulation Bringup (`evoart_description` & `evoart_bringup`)
- [x] Defined the 3D Robot Geometry (`evoart.xacro`) with precise competition constraints (1.425m wheelbase, 1.05m track width).
- [x] Attached the Velodyne VLP-16 (LiDAR) and ZED 2i (Stereo Camera) sensor arrays (`sensors.xacro`).
- [x] Engineered the `sim.launch.py` and `rviz.launch.py` launch scripts for seamless 3D simulation booting.

### 6. ROS 2 Jazzy & Gazebo Harmonic Migration
- [x] Fully migrated the architecture away from the deprecated Gazebo Classic to the modern `gz-sim` (Gazebo Harmonic).
- [x] Rewrote URDF sensor tags to match modern SDF 1.9 schema standards.
- [x] Implemented a bidirectional `ros_gz_bridge` to seamlessly pass `/cmd_vel`, `/odom`, `/scan`, and `/camera/image_raw` between the isolated Gazebo transport layer and the ROS 2 network.

### 7. AI Perception and Localization Bringup
- [x] Configured `CMakeLists.txt` for `evoart_brain` to install Python nodes and Behavior Tree XMLs.
- [x] Implemented `yolo_node.py`, which subscribes to the camera feed, runs YOLOv8 inference, and publishes `YoloDetection` and `TrafficStatus` messages.
- [x] Created `ekf.yaml` to fuse the GPS/IMU and wheel odometry into a robust `/odometry/filtered` pose estimate using `robot_localization`.

### 8. Embedded Systems & Hardware Integration (İP-1)
- [x] Developed `aks_bridge_node.py` to translate Nav2 `/cmd_vel` Twist messages into a secure, CRC-8 checked 32-byte UART packet for the STM32 motor controller.
- [x] Implemented mathematically accurate Ackermann steering angle calculation (`atan((wheelbase * angular_vel) / linear_vel)`).

### 9. Master Orchestration and Safety Systems
- [x] Developed `safety_stop_node.py` which intercepts manual or Nav2 driving commands on `/cmd_vel_nav` and forces the car to brake if YOLO detects a close pedestrian.
- [x] Created `bringup.launch.py` to simultaneously launch the Gazebo simulation, the YOLO vision node, and the Safety Reflex system.

## Appendix: `evoart_brain` Package File Manifest

The `evoart_brain` package contains the core intelligence, navigation, and perception logic for the autonomous vehicle. Below is an explanation of its files and their functions:

- **`package.xml`**: Declares ROS 2 package dependencies (such as `nav2_behavior_tree` and our custom `evoart_interfaces`) and metadata required by the `colcon` build system to compile the package correctly.
- **`CMakeLists.txt`**: The build script instructing `ament_cmake` on how to compile the package's C++ nodes and custom Behavior Tree plugins.
- **`behavior_trees/taxi_logic.xml`**: The XML-based Behavior Tree governing the high-level mission logic. It dictates how the RoboTaxi reacts to dynamic scenarios, such as yielding to red traffic lights and triggering recovery pipelines when the vehicle is stuck.
- **`config/nav2_params.yaml`**: The central configuration file for the Navigation 2 stack. It dictates exactly how the `SmacPlannerHybrid` plans paths (respecting the physical 1.425m Ackermann wheelbase and 1.5m minimum turning radius) and how the `MPPIController` avoids dynamic obstacles.
- **`config/amcl_params.yaml`**: The Adaptive Monte Carlo Localization configuration file, crucial for maintaining an estimate of the vehicle's pose, particularly useful as a fallback system during the GPS-denied tunnel crossing.
- **`src/bt_plugins.cpp`**: Custom C++ implementations of Behavior Tree nodes (Action and Condition nodes). These are compiled into plugins and loaded by the BT engine to perform TEKNOFEST-specific actions that standard Nav2 nodes cannot.
- **`src/yolo_node.py`**: A Python-based ROS 2 node that runs the TensorRT/OpenVINO accelerated YOLO model against the ZED 2i camera feed. It is responsible for detecting the 22 required competition classes (signs and traffic lights) and publishing `YoloDetection` messages to the rest of the system.

## Next Steps
- ~~Implement the full Nav2 stack into `bringup.launch.py`~~ ✅ Done
- ~~Test the Behavior Tree recovery pipelines.~~
- Launch the full stack and drive through the city to generate a SLAM map.
- Save the map and transition to AMCL-based localization.
- Test the complete autonomous navigation pipeline with YOLO + BT.

---

### 10. TEKNOFEST City World Integration & Full Nav2 Stack (Session: 2026-04-30)

#### Problem
- The `aws-robomaker-city-world` repository does not exist (HTTP 404).
- The original AWS RoboMaker worlds use Gazebo Classic `.world` format — incompatible with Gazebo Harmonic / `gz-sim`.
- No traffic light model exists on Gazebo Fuel (all naming variations return 404).
- The existing `teknofest_city.sdf` was sparse (6 buildings, 5 stop signs, 1 pedestrian) and referenced a broken `Hospital` model.

#### Solution: Purpose-Built TEKNOFEST City World
- [x] Rewrote `generate_city.py` to produce a rich $80\text{m} \times 60\text{m}$ urban environment:
  - **Road Network**: 5 road surfaces (2 E-W, 3 N-S) with dashed center lane markings forming T-junctions and a 4-way intersection.
  - **9 Buildings**: House 1/2/3, Gas Station, Fast Food, Cafe, Warehouse, Office Building, Apartment — all using verified Gazebo Fuel URIs (HTTP 200 confirmed).
  - **8 Vehicles**: 6 parked (Hatchback variants, SUV, Pickup, Bus) + 2 emergency (Ambulance, Fire Truck).
  - **Street Furniture**: 5 Stop Signs, 4 Construction Cones, 2 Jersey Barriers, 2 Fire Hydrants, 4 Lamp Posts, 2 Speed Limit Signs, 1 Dumpster.
  - **6 Trees**: Oak and Pine for visual richness.
  - **5 Custom Inline Traffic Lights**: Built from scratch as static SDF models with pole, housing, and 3 emissive spheres (red/yellow/green). Placed at 3 main intersections.
  - **3 Animated Pedestrian Actors**: Walking across roads at different locations with scripted trajectory loops.
  - **Physics Tuning**: `max_step_size` increased to $4\text{ms}$ (4× faster), shadows disabled, `ogre2` render engine specified — optimized for Intel Lunar Lake iGPU.

#### Traffic Light Simulator Node
- [x] Created `traffic_light_node.py`: Cycles `GREEN (30s) → YELLOW (5s) → RED (30s)`, publishes `TrafficStatus` on `/traffic_light/status` and `/yolo/traffic_lights`.

#### Full Nav2 Stack Integration
- [x] Expanded `nav2_params.yaml` from 27 lines to a comprehensive configuration:
  - `SmacPlannerHybrid` with DUBIN motion model ($1.5\text{m}$ turning radius).
  - `MPPIController` with Ackermann motion model, 56 time steps, 2000 batch size.
  - Local costmap ($5\text{m} \times 5\text{m}$ rolling window) and global costmap with LiDAR obstacle layers.
  - `VelocitySmoother` with $2.5\text{m/s}^2$ acceleration limits.
  - Full AMCL config with initial pose at spawn coordinates $(2.0, 0.0)$.
- [x] Created `slam_params.yaml` for SLAM Toolbox online async mode ($5\text{cm}$ resolution, loop closure enabled).
- [x] Updated `bringup.launch.py` with 6 orchestrated layers:
  1. Gazebo Simulation
  2. YOLO Perception (5s delay)
  3. Safety Stop + Traffic Light Simulator
  4. EKF Sensor Fusion (`robot_localization`)
  5. SLAM Toolbox (8s delay)
  6. Nav2 Stack (12s delay): planner, controller, BT navigator, behaviors, velocity smoother, lifecycle manager.

#### Package Manifest Updates
- [x] Added `traffic_light_node.py` to `evoart_brain` CMakeLists install targets.
- [x] Added `scripts` directory to `evoart_bringup` CMakeLists install targets.
- [x] Added 11 new `exec_depend` entries to `evoart_bringup/package.xml`: Nav2 components, SLAM Toolbox, `robot_localization`.

#### Build Verification
- [x] `colcon build --packages-up-to evoart_bringup` — **4/4 packages succeeded** in 1.91s.

---

### 11. Zero-Manual-Effort Autonomous Simulation (Session: 2026-04-30 #2)

#### Problem
- Running live YOLO inference during route testing wastes GPU and introduces non-deterministic latency.
- No automated A-to-B navigation existed — driving was manual via `ros2 topic pub`.
- The GeoJSON route file was a placeholder square, not aligned to the actual road network.

#### Mock Perception Node (`mock_perception_node.py`)
- [x] Created a ground-truth perception node that reads vehicle `/odom` and checks proximity to known SDF positions:
  - **3 pedestrian actors**: Detects when vehicle is within $15\text{m}$, publishes `YoloDetection` with `class_name='person'` and simulated bounding box areas based on distance.
  - **5 traffic lights**: Subscribes to `/traffic_light/status` for ground-truth state, publishes `TrafficStatus` when within $20\text{m}$.
  - **5 stop signs**: Publishes `YoloDetection` with `class_name='stop sign'` and `stop_required=True` when within $15\text{m}$.
- Zero GPU usage. Publishes at $5\text{Hz}$ simulated camera rate.

#### GeoJSON Route Navigator (`geojson_navigator_node.py`)
- [x] Parses GeoJSON `LineString` coordinates as local $(x, y)$ positions.
- [x] Converts each waypoint to a `NavigateToPose` goal with heading calculated toward the next waypoint.
- [x] Sends goals sequentially via the Nav2 action client, with feedback logging and automatic retry on failure.
- [x] Configurable parameters: `route_file`, `goal_frame`, `wait_at_waypoint`.

#### Updated Route (`route.geojson`)
- [x] Replaced placeholder square route with a realistic city loop: $(2,0) \to (20,0) \to (20,20) \to (0,20) \to (0,0) \to (2,0)$ — follows the actual road network through all 3 main intersections.

#### Unified Launch File (`sim_full.launch.py`)
- [x] Created a single-command launcher with 7 orchestrated layers:
  1. Gazebo simulation (city + vehicle)
  2. Mock Perception (5s delay)
  3. Safety Stop + Traffic Light Simulator
  4. EKF Sensor Fusion
  5. SLAM Toolbox (8s delay)
  6. Full Nav2 Stack (12s delay)
  7. GeoJSON Route Navigator (20s delay — waits for Nav2)

#### Package Updates
- [x] Added `mock_perception_node.py` and `geojson_navigator_node.py` to `evoart_brain` CMakeLists.
- [x] Added `nav2_msgs` to `evoart_brain/package.xml` for `NavigateToPose` action.

#### Build Verification
- [x] `colcon build --packages-up-to evoart_bringup` — **4/4 packages succeeded** in 3.37s.

#### Usage
```bash
source install/setup.bash
ros2 launch evoart_bringup sim_full.launch.py
# That's it. No second terminal needed.
```

---

### 12. IP-7 Specification Compliance & Pedestrian Fix (Session: 2026-04-30 #3)

#### Problem
- Pedestrian actors moved too fast (1.6 m/s) with jerky 0.5s turnaround pauses, causing erratic visual behavior.
- Max vehicle velocity was set to $5.0\text{m/s}$, exceeding the IP-7 spec limit of $1.39\text{m/s}$.
- Mock perception triggered at 15-20m range, far beyond the 3-5m trigger radius in the spec.

#### Fixes Applied
- [x] **Pedestrian trajectories**: Reduced walking speed to $\sim 0.8-1.0\text{m/s}$, shortened patrol distance to $6\text{m}$, increased turnaround pause to $2-3\text{s}$.
- [x] **Nav2 velocity cap**: `vx_max` reduced from $5.0$ to $1.39\text{m/s}$ in both MPPI controller and velocity smoother.
- [x] **Mock perception ranges**: Traffic light/stop sign detection radius reduced from $15-20\text{m}$ to $5\text{m}$ per IP-7 spec. Pedestrian close range from $5\text{m}$ to $3\text{m}$.
- [x] **Mock perception rate**: Increased from $5\text{Hz}$ to $10\text{Hz}$ per IP-7 spec.
- [x] **World regenerated**: `teknofest_city.sdf` rebuilt with fixed pedestrian trajectories.

#### Documentation
- [x] Created `version-1-spec.md` — complete IP-7 System Specification covering kinematic constraints, communication interfaces, BT patterns, mock perception spec, and operational workflow.
