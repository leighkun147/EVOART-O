# EVOART-O IP-7 System Specification (Version 1)

> **Status**: Active | **Work Packet**: WP-7 Decision Logic & Autonomous Simulation
> **Date**: 2026-04-30 | **Lead**: Leykun

---

## 1. System Identity & Dependencies

| Property | Value |
|---|---|
| **Project Name** | EVOART-O |
| **ROS 2 Distribution** | Jazzy (Ubuntu 24.04) |
| **Architecture** | Ackermann-steering (car-like, non-holonomic) |
| **Coordinate Frame** | Global origin at Gazebo world origin $(0, 0, 0)$ |
| **Simulation Engine** | Gazebo Harmonic (`gz-sim`) |

### Mandatory Dependencies

| Package | Purpose |
|---|---|
| `nav2_behavior_tree` | BT engine for decision logic |
| `nav2_smac_planner` | Hybrid-A* planner with Dubin curves |
| `nav2_mppi_controller` | Model Predictive Path Integral controller |
| `behaviortree_cpp` | C++ BT runtime |
| `evoart_interfaces` | Custom `TrafficStatus.msg` and `YoloDetection.msg` |
| `nav2_msgs` | `NavigateToPose` action for GeoJSON navigator |
| `slam_toolbox` | Online async SLAM for map generation |
| `robot_localization` | EKF sensor fusion |

---

## 2. Physical & Kinematic Constraints

| Parameter | Symbol | Value | Unit |
|---|---|---|---|
| Wheelbase | $L$ | $1.425$ | m |
| Track Width | $W$ | $1.05$ | m |
| Wheel Radius | $r$ | $0.293$ | m |
| Min Turning Radius | $R$ | $1.5$ | m |
| **Max Velocity** | $V_{max}$ | **$1.39$** | m/s |
| Max Reverse Velocity | $V_{rev}$ | $-0.5$ | m/s |
| Steering Limit | $\delta_{max}$ | $\pm 22.5°$ ($0.3927$ rad) | degrees |
| Max Acceleration | $a_{max}$ | $2.5$ | m/s² |
| Max Deceleration | $a_{dec}$ | $-2.5$ | m/s² |
| Chassis Dimensions | — | $2.0 \times 1.05 \times 0.5$ | m |
| Vehicle Mass | $m$ | $50.0$ | kg |

> [!IMPORTANT]
> The minimum turning radius $R = 1.5\text{m}$ **must be strictly enforced** in the SmacPlannerHybrid configuration. The MPPI controller's `AckermannConstraints.min_turning_r` must match.

---

## 3. Communication Interfaces (`evoart_interfaces`)

### Message Definitions

**`TrafficStatus.msg`**
```
string light_state    # RED | GREEN | YELLOW | NONE
string sign_type      # traffic_light | stop_sign
bool stop_required    # true if vehicle must stop
```

**`YoloDetection.msg`**
```
string class_name     # COCO class name (person, stop sign, traffic light, etc.)
float32 score         # Detection confidence [0.0, 1.0]
int32[4] bbox         # Bounding box [x1, y1, x2, y2] in pixels
```

### Topic Map

| Topic | Message Type | Publisher | Subscriber(s) |
|---|---|---|---|
| `/yolo/detections` | `YoloDetection` | Mock Perception / YOLO Node | Safety Stop |
| `/yolo/traffic_lights` | `TrafficStatus` | Mock Perception / YOLO Node | Behavior Tree |
| `/traffic_light/status` | `TrafficStatus` | Traffic Light Simulator | Mock Perception |
| `/cmd_vel_nav` | `Twist` | Nav2 / Teleop | Safety Stop |
| `/cmd_vel` | `Twist` | Safety Stop | Gazebo Bridge |
| `/odom` | `Odometry` | Gazebo Bridge | EKF, SLAM, Nav2 |
| `/scan` | `LaserScan` | Gazebo Bridge | SLAM, Nav2 Costmaps |
| `/camera/image_raw` | `Image` | Gazebo Bridge | YOLO Node |

---

## 4. Work Packet 7: Decision Logic (Behavior Tree)

### Architecture: Reactive Fallback Pattern

```
RecoveryNode (6 retries)
├── PipelineSequence "NavigateWithTrafficRules"
│   ├── Fallback "TrafficLightFallback"    ← HIGH PRIORITY (Safety)
│   │   ├── Condition: TrafficLightCondition
│   │   │   topic=/yolo/traffic_lights
│   │   │   If light_state == RED → FAILURE (triggers Wait)
│   │   └── Wait (duration=1.0s)
│   ├── ComputePathToPose                   ← STANDARD PRIORITY
│   │   planner_id="GridBased"
│   │   Uses SmacPlannerHybrid (Dubin, R=1.5m)
│   └── FollowPath
│       controller_id="FollowPath"
│       Uses MPPIController (Ackermann)
└── ForceSuccess
    └── ClearEntireCostmap
```

### Stop Sign Behavior

When `sign_type == 'stop_sign'` is detected:
1. **Wait** $3.0\text{s}$ at the stop line
2. **Continue** navigation after the wait completes

### Planner Configuration

| Parameter | Value |
|---|---|
| Plugin | `SmacPlannerHybrid` |
| Motion Model | `DUBIN` (forward-only Ackermann) |
| Min Turning Radius | $1.5\text{m}$ |
| Resolution | $0.05\text{m}$ |
| Max Planning Time | $5.0\text{s}$ |

### Controller Configuration

| Parameter | Value |
|---|---|
| Plugin | `MPPIController` |
| Motion Model | `Ackermann` |
| $V_{max}$ | $1.39\text{m/s}$ |
| Time Steps | $56$ |
| Batch Size | $2000$ |
| `AckermannConstraints.min_turning_r` | $1.5\text{m}$ |

---

## 5. Mock Perception Node Specification

### Purpose
Act as a **Ground Truth Proxy** — substitute for the YOLO model during simulation testing.

### Input
- Subscribe to `/odom` (vehicle position from Gazebo bridge)
- Subscribe to `/traffic_light/status` (ground-truth light state)

### Logic
1. Calculate Euclidean distance between vehicle and known **trigger coordinates** (traffic lights, stop signs, pedestrian patrol centers)
2. **Traffic Light Trigger**: If vehicle is within $3.0\text{m}$ - $5.0\text{m}$ of a traffic light position → publish current `light_state` from `/traffic_light/status` to `/yolo/traffic_lights`
3. **Stop Sign Trigger**: If vehicle is within $3.0\text{m}$ - $5.0\text{m}$ of a stop sign → publish `stop_required = true`
4. **Pedestrian Trigger**: If vehicle is within $5.0\text{m}$ of a pedestrian patrol path → publish `YoloDetection` with `class_name='person'` and proportional bbox area

### Output
- Consistent **$10\text{Hz}$** stream of `TrafficStatus` and `YoloDetection` messages

### Known Trigger Coordinates (from SDF)

| Type | Name | Position $(x, y)$ |
|---|---|---|
| Traffic Light | `traffic_light_0` | $(-3, 3)$ |
| Traffic Light | `traffic_light_1` | $(17, 3)$ |
| Traffic Light | `traffic_light_2` | $(23, -3)$ |
| Traffic Light | `traffic_light_3` | $(-3, 23)$ |
| Traffic Light | `traffic_light_4` | $(37, 3)$ |
| Stop Sign | `stop_sign_0` | $(-2, -3)$ |
| Stop Sign | `stop_sign_1` | $(18, -3)$ |
| Stop Sign | `stop_sign_2` | $(22, 3)$ |
| Stop Sign | `stop_sign_3` | $(-2, 17)$ |
| Stop Sign | `stop_sign_4` | $(38, -3)$ |
| Pedestrian | `pedestrian_0` | $(5, 0)$ patrol |
| Pedestrian | `pedestrian_1` | $(0, 10)$ patrol |
| Pedestrian | `pedestrian_2` | $(20, 20)$ patrol |

---

## 6. Simulation & Environment Specification

### World
- **Custom TEKNOFEST City World** (Gazebo Harmonic SDF)
- $80\text{m} \times 60\text{m}$ with road network, T-junctions, 4-way intersection
- 9 buildings, 8 vehicles, 5 traffic lights, 5 stop signs, 3 pedestrian actors

### Physics (Intel Lunar Lake iGPU Optimization)

| Parameter | Value | Rationale |
|---|---|---|
| `max_step_size` | $0.004\text{s}$ | 4× faster than default, reduces CPU load |
| `real_time_factor` | $1.0$ | Match wall-clock time |
| Shadows | **Disabled** | Saves ~30% GPU on iGPU |
| Render Engine | `ogre2` | Best compatibility with gz-sim |
| Scene Ambient | $0.6$ | Compensate for no shadows |

### Visualization (RViz2)
- Static occupancy grid (Map) from SLAM
- Global path from SmacPlannerHybrid
- MPPI local trajectory rollouts
- Robot footprint ($2.0 \times 1.05\text{m}$)
- LiDAR point cloud

---

## 7. Operational Workflow ("Solo Lead" Rules)

### Virtual Environment
```bash
source .venv/bin/activate   # All pip installs MUST be inside .venv
```

### Progress Tracking
All changes documented in `progress.md`:
- Current Work Packet status
- Nav2 parameter changes (especially MPPI cost functions)
- Known issues / physics jitter in Gazebo

### Build & Launch
```bash
# Build
colcon build --packages-up-to evoart_bringup

# Full autonomous simulation (zero manual effort)
source install/setup.bash
ros2 launch evoart_bringup sim_full.launch.py
```

---

## 8. GeoJSON Route Format

The route file uses standard GeoJSON with coordinates in **local meters** (not GPS):

```json
{
  "type": "FeatureCollection",
  "features": [{
    "type": "Feature",
    "geometry": {
      "type": "LineString",
      "coordinates": [[x1, y1], [x2, y2], ...]
    }
  }]
}
```

The `geojson_navigator_node.py` converts each coordinate pair to a `NavigateToPose` goal with heading calculated toward the next waypoint.

---

## Appendix: File Manifest

| File | Package | Purpose |
|---|---|---|
| `evoart.xacro` | `evoart_description` | Vehicle URDF ($L=1.425$, $W=1.05$) |
| `sensors.xacro` | `evoart_description` | Camera + LiDAR sensor definitions |
| `sim.launch.py` | `evoart_bringup` | Gazebo + spawn + bridge |
| `bringup.launch.py` | `evoart_bringup` | YOLO + safety + Nav2 (real perception) |
| `sim_full.launch.py` | `evoart_bringup` | Mock perception + Nav2 + GeoJSON (automated) |
| `generate_city.py` | `evoart_bringup` | City world SDF generator |
| `nav2_params.yaml` | `evoart_brain` | Full Nav2 configuration |
| `slam_params.yaml` | `evoart_brain` | SLAM Toolbox configuration |
| `ekf.yaml` | `evoart_brain` | EKF sensor fusion configuration |
| `route.geojson` | `evoart_brain` | A-to-B route waypoints |
| `taxi_logic.xml` | `evoart_brain` | Behavior Tree XML |
| `yolo_node.py` | `evoart_brain` | Live YOLO perception |
| `mock_perception_node.py` | `evoart_brain` | Ground-truth perception proxy |
| `safety_stop_node.py` | `evoart_brain` | Pedestrian emergency brake |
| `traffic_light_node.py` | `evoart_brain` | Traffic light state simulator |
| `geojson_navigator_node.py` | `evoart_brain` | GeoJSON → Nav2 goals |
| `aks_bridge_node.py` | `evoart_brain` | UART bridge to STM32 |
