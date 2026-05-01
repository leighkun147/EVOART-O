# EVOART-O — Autonomous RoboTaxi for TEKNOFEST 2026

<div align="center">
  <h3>🏆 TEKNOFEST 2026 Robotaksi Passenger Autonomous Vehicle Competition (Original Vehicle Category)</h3>
  <p>A next-generation, fully autonomous vehicle stack built on <strong>ROS 2 Jazzy</strong>, featuring deep learning perception, LiDAR-SLAM, MPPI control, and Behavior Tree mission logic.</p>

  <br/>

  | Component | Technology |
  |---|---|
  | **ROS 2** | Jazzy (Ubuntu 24.04) |
  | **Simulator** | Gazebo Harmonic (`gz-sim`) |
  | **Navigation** | Nav2 (SmacPlannerHybrid + MPPI) |
  | **Perception** | YOLOv8n / Mock Ground-Truth |
  | **Mapping** | SLAM Toolbox (Online Async) |
  | **Decision** | Behavior Trees (BT.CPP) |
</div>

---

## 📖 Table of Contents

1. [Quick Start (For Teammates)](#-quick-start-for-teammates)
2. [Prerequisites & Environment Setup](#-prerequisites--environment-setup)
3. [Building the Workspace](#-building-the-workspace)
4. [Running the Simulation](#-running-the-simulation)
5. [Troubleshooting](#-troubleshooting)
6. [Project Architecture](#-project-architecture)
7. [Vehicle Specifications](#-vehicle-specifications)
8. [Competition Overview](#-competition-overview)
9. [Work Packets & Team Organization](#-work-packets--team-organization)
10. [Roadmap](#-roadmap)

---

## 🚀 Quick Start (For Teammates)

> **If you just cloned this repo and want to test the simulation, follow these steps exactly.**

```bash
# 1. Clone and enter the project
git clone https://github.com/leighkun147/EVOART-O.git
cd EVOART-O

# 2. Create the Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install ROS 2 dependencies
sudo apt update
rosdep update
rosdep install --from-paths src --ignore-src -r -y

# 4. Build all packages
colcon build --packages-up-to evoart_bringup

# 5. Source the workspace
source install/setup.bash

# 6. Launch the full autonomous simulation
ros2 launch evoart_bringup sim_full.launch.py
```

**That's it — one terminal, zero manual effort.** The simulation will:
- Start Gazebo with the TEKNOFEST city world
- Spawn the vehicle at position (2, 0)
- Activate mock perception, traffic lights, and safety systems
- Start SLAM Toolbox for mapping
- Launch the full Nav2 navigation stack
- Begin autonomous route execution through the city

### Optional: Launch RViz2 Visualization

In a **separate terminal**:
```bash
cd ~/Desktop/EVOART-O
source install/setup.bash
env -u GTK_PATH ros2 launch evoart_bringup rviz.launch.py
```

> **Note:** The `env -u GTK_PATH` prefix is required to prevent a GTK theme conflict between the system and ROS 2. Without it, RViz may crash on startup.

---

## 🔧 Prerequisites & Environment Setup

### System Requirements

| Requirement | Version |
|---|---|
| **Ubuntu** | 24.04 LTS (Noble) |
| **ROS 2** | Jazzy Jalisco |
| **Gazebo** | Harmonic (gz-sim 8.x) |
| **Python** | 3.12+ |
| **RAM** | 8 GB minimum, 16 GB recommended |
| **GPU** | Intel Lunar Lake iGPU or NVIDIA (for YOLO) |

### Install ROS 2 Jazzy

Follow the [official ROS 2 Jazzy installation guide](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html), then:

```bash
sudo apt install ros-jazzy-desktop
sudo apt install ros-jazzy-navigation2 ros-jazzy-nav2-bringup
sudo apt install ros-jazzy-slam-toolbox
sudo apt install ros-jazzy-robot-localization
sudo apt install ros-jazzy-ros-gz
sudo apt install ros-jazzy-xacro
sudo apt install python3-colcon-common-extensions
```

### Virtual Environment (MANDATORY)

> ⚠️ **CRITICAL RULE: Never use global `pip install`.** All Python dependencies MUST be installed inside the virtual environment. This prevents breaking system packages and ROS 2 tools.

```bash
# Create the virtual environment (run once)
cd ~/Desktop/EVOART-O
python3 -m venv .venv

# Activate it (run EVERY TIME you open a new terminal)
source .venv/bin/activate

# Install Python dependencies inside .venv
pip install ultralytics opencv-python-headless numpy
```

### Verify Your Setup

```bash
# Check ROS 2
ros2 --version          # Should show "jazzy"

# Check Gazebo
gz sim --version        # Should show Harmonic (8.x)

# Check Nav2
ros2 pkg list | grep nav2   # Should list nav2_* packages
```

---

## 🏗️ Building the Workspace

```bash
cd ~/Desktop/EVOART-O

# Install missing ROS dependencies automatically
rosdep install --from-paths src --ignore-src -r -y

# Build all 4 packages
colcon build --packages-up-to evoart_bringup

# Source the workspace overlay
source install/setup.bash
```

### Build Individual Packages

```bash
# Rebuild only the packages you changed
colcon build --packages-select evoart_brain evoart_bringup

# Always re-source after building
source install/setup.bash
```

### Expected Build Output
```
Starting >>> evoart_interfaces
Starting >>> evoart_description
Finished <<< evoart_description [0.14s]
Finished <<< evoart_interfaces [1.22s]
Starting >>> evoart_brain
Finished <<< evoart_brain [0.09s]
Starting >>> evoart_bringup
Finished <<< evoart_bringup [0.07s]

Summary: 4 packages finished [1.52s]
```

---

## 🎮 Running the Simulation

### Option A: Full Autonomous Stack (Recommended)

This launches **everything** — Gazebo, perception, navigation, and route execution:

```bash
source install/setup.bash
ros2 launch evoart_bringup sim_full.launch.py
```

**What starts and when:**

| Time | Component | What it does |
|---|---|---|
| 0s | Gazebo + Bridge | Loads city, spawns car, creates ROS↔GZ bridge |
| 0s | Static TF | Publishes `map → odom` transform |
| 0s | Odom TF | Publishes `odom → base_link` from /odom |
| 0s | Safety + Traffic | Safety stop reflex + traffic light state machine |
| 5s | Mock Perception | Ground-truth proxy (no GPU needed) |
| 10s | SLAM Toolbox | Starts building occupancy grid from LiDAR |
| 15s | Nav2 Stack | Planner, controller, BT, behaviors, smoother |
| 30s | GeoJSON Navigator | Sends route waypoints to Nav2 |

### Option B: Gazebo Only (For Manual Testing)

```bash
source install/setup.bash
ros2 launch evoart_bringup sim.launch.py
```

Then manually send velocity commands:
```bash
# In another terminal
source install/setup.bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 1.0}}" --rate 10
```

### Option C: Real Vehicle (Competition Mode)

```bash
source install/setup.bash
ros2 launch evoart_bringup bringup.launch.py
```

This uses the real YOLO perception node instead of mock perception.

### Viewing in RViz2

```bash
# In a SEPARATE terminal
cd ~/Desktop/EVOART-O
source install/setup.bash
env -u GTK_PATH ros2 launch evoart_bringup rviz.launch.py
```

---

## 🔍 Troubleshooting

### "Timed out waiting for transform from base_link to map"

**This is the TF chain issue.** It means one of the transforms is missing. Debug it:

```bash
# Terminal 2: Check if Gazebo is sending odometry data
source install/setup.bash
ros2 topic hz /odom        # Should show ~50 Hz
ros2 topic hz /clock        # Should show ~250 Hz (physics clock)
ros2 topic hz /scan         # Should show ~10 Hz (LiDAR)

# Check the full TF tree
ros2 run tf2_ros tf2_echo map base_link
```

**If `/odom` shows 0 Hz:** Gazebo physics isn't running. Make sure the Gazebo GUI window stays open — closing it kills the physics.

**If `/clock` shows 0 Hz:** The clock bridge is broken. Rebuild: `colcon build --packages-select evoart_bringup`

### "Package not found" errors

You forgot to source the workspace:
```bash
source ~/Desktop/EVOART-O/install/setup.bash
```

### Gazebo texture warnings (`Could not resolve file`)

These are **cosmetic only** — missing textures on downloaded Fuel models. The physics and sensors work fine. Ignore them.

### RViz crashes on launch

Use the GTK workaround:
```bash
env -u GTK_PATH ros2 launch evoart_bringup rviz.launch.py
```

### YOLO node NNPACK warnings

```
NNPACK: unsupported hardware
```
This is normal on Intel iGPU. PyTorch falls back to standard CPU inference. Performance is slightly slower but functional.

---

## 📐 Project Architecture

### Package Structure

```
EVOART-O/
├── src/
│   ├── evoart_interfaces/        # Custom ROS 2 messages
│   │   └── msg/
│   │       ├── TrafficStatus.msg     # light_state, sign_type, stop_required
│   │       └── YoloDetection.msg     # class_name, score, bbox[4]
│   │
│   ├── evoart_description/       # Vehicle model (URDF/Xacro)
│   │   └── urdf/
│   │       ├── evoart.xacro          # Ackermann chassis + wheels
│   │       └── sensors.xacro         # Camera (ZED 2i) + LiDAR (VLP-16)
│   │
│   ├── evoart_brain/             # Intelligence & Navigation
│   │   ├── src/
│   │   │   ├── yolo_node.py              # Live YOLO perception
│   │   │   ├── mock_perception_node.py   # Ground-truth proxy (simulation)
│   │   │   ├── safety_stop_node.py       # Pedestrian emergency brake
│   │   │   ├── traffic_light_node.py     # Traffic light state simulator
│   │   │   ├── geojson_navigator_node.py # Route file → Nav2 goals
│   │   │   ├── odom_tf_broadcaster.py    # Publishes odom→base_link TF
│   │   │   └── aks_bridge_node.py        # UART bridge to STM32
│   │   ├── config/
│   │   │   ├── nav2_params.yaml          # Full Nav2 configuration
│   │   │   ├── slam_params.yaml          # SLAM Toolbox configuration
│   │   │   ├── ekf.yaml                  # EKF sensor fusion (future)
│   │   │   └── route.geojson             # City route waypoints
│   │   └── behavior_trees/
│   │       └── taxi_logic.xml            # Behavior Tree XML
│   │
│   └── evoart_bringup/           # Launch & World Files
│       ├── launch/
│       │   ├── sim.launch.py             # Gazebo only
│       │   ├── sim_full.launch.py        # Full autonomous stack
│       │   ├── bringup.launch.py         # Real vehicle mode
│       │   └── rviz.launch.py            # Visualization
│       ├── scripts/
│       │   └── generate_city.py          # City world SDF generator
│       └── worlds/
│           └── teknofest_city.sdf        # 80m×60m urban environment
│
├── version-1-spec.md             # IP-7 System Specification
├── progress.md                   # Development log
└── .gitignore
```

### TF Tree (Transform Chain)

```
map                    ← static_transform_publisher (identity)
 └── odom              ← odom_tf_broadcaster.py (from /odom)
      └── base_link    ← robot_state_publisher (URDF)
           └── chassis
                ├── velodyne       (LiDAR sensor)
                ├── camera_link    (ZED 2i camera)
                ├── front_left_steer → front_left_wheel
                ├── front_right_steer → front_right_wheel
                ├── rear_left_wheel
                └── rear_right_wheel
```

### Topic Architecture

```
Gazebo ─────┬── /odom ──────────→ Odom TF Broadcaster → /tf
            ├── /scan ──────────→ SLAM Toolbox → /map
            ├── /camera/image ──→ YOLO Node → /yolo/detections
            ├── /clock ─────────→ All nodes (sim time)
            └── /cmd_vel ←──────── Safety Stop ←── Nav2 (/cmd_vel_nav)
                                       ↑
                                 Mock Perception
                                 (proximity-based)
```

---

## 🚗 Vehicle Specifications

| Parameter | Symbol | Value |
|---|---|---|
| Wheelbase | $L$ | 1.425 m |
| Track Width | $W$ | 1.05 m |
| Wheel Radius | $r$ | 0.293 m |
| Min Turning Radius | $R$ | 1.5 m |
| Max Velocity | $V_{max}$ | 1.39 m/s |
| Max Steering | $\delta$ | ±22.5° |
| Mass | $m$ | 50 kg |
| Footprint | — | 2.0 × 1.05 m |

---

## 🏆 Competition Overview

EVOART-O competes in the **TEKNOFEST 2026 Robotaksi** challenge — a structured urban track with 3 laps featuring traffic lights, signs, pedestrians, static/dynamic obstacles, passenger zones, and GPS-denied tunnels.

### Scoring Highlights

| Action | Points |
|---|---|
| Stop at Red Light (0-5m) | +60 |
| Move on Green (<5s) | +40 |
| Traffic Sign Compliance | +50 |
| Passenger Pick-up/Drop-off | +70 |
| Parking Success | +80 |
| GPS-Denied Tunnel | +200 |
| Red Light Violation | -30 |
| Sign Violation | -50 |
| Lane Departure | **Disqualification** |

### 22-Class Detection Requirement
The YOLO model must identify 19 TEKNOFEST-specific traffic signs + 3 traffic light states (Red, Yellow, Green).

---

## 👥 Work Packets & Team Organization

**11 members** (10 Software + 1 Electrical Engineering):

| İP | Work Packet | Owners |
|---|---|---|
| İP-1 | AKS ↔ PC UART Bridge | EE Team |
| İP-2 | Sensor Fusion & EKF | Localization Team |
| İP-3 | Cartographer SLAM & Mapping | Localization Team |
| İP-4 | GPS-Denied Localization (Tunnel) | Localization Team |
| İP-5 | YOLOv8n Training & ROS 2 Integration | AI Team |
| İP-6 | Nav2 Configuration & Tuning | Navigation Team |
| İP-7 | Competition Tasks & Behavior Trees | Navigation Team |
| İP-8 | Simulation Setup & Execution | Simulation Team |
| İP-9 | Vehicle Assembly & Compliance | All Teams |
| İP-10 | End-to-End Integration Testing | All Teams |

---

## 🗺️ Roadmap

| Milestone | Date | Status |
|---|---|---|
| TYF Submission | March 26, 2026 | ✅ |
| ROS 2 Jazzy Migration | April 30, 2026 | ✅ |
| Simulation Environment | April 30, 2026 | ✅ |
| Nav2 + BT Integration | May 2026 | 🔄 In Progress |
| KTR Submission | May 15, 2026 | 📋 Pending |
| SLAM Map Generation | May 2026 | 📋 Pending |
| YOLO Fine-Tuning | June 2026 | 📋 Pending |
| Autonomous Test Video | July 01, 2026 | 📋 Pending |
| Simulation Video | July 15, 2026 | 📋 Pending |
| **TEKNOFEST Finals** | **August 2026** | 🏁 |

---

<div align="center">
  <sub>Developed by the EVOART-O Team for TEKNOFEST 2026 Robotaksi Passenger Autonomous Vehicle Competition.</sub>
</div>
