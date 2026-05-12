# EVOART-O — Version Compatibility & Nav2 Release Info

## System Foundation

| Component | Version | Notes |
|-----------|---------|-------|
| **Ubuntu** | 22.04.5 LTS (Jammy) | Long-term support until April 2027 |
| **Linux Kernel** | 6.8.0-111-generic | HWE kernel |
| **Python** | 3.10.12 | Default for Jammy |
| **ROS 2** | **Humble Hawksbill** | LTS — EOL: May 2027 |
| **ROS 2 Core (rclpy)** | 3.3.21 | Build: 2026-03-10 |

---

## Nav2 (Navigation 2) — Release Model

| Detail | Value |
|--------|-------|
| **Nav2 Version** | **1.1.20** |
| **Release Branch** | `humble` (LTS backport branch) |
| **Release Model** | Rolling bugfix releases on the Humble branch |
| **Build Date** | 2026-03-26 (latest sync) |
| **Upstream Repo** | [ros-navigation/navigation2](https://github.com/ros-navigation/navigation2) |

### Nav2 Packages Used by EVOART-O

| Package | Version | Role in EVOART-O |
|---------|---------|-----------------|
| `nav2_planner` | 1.1.20 | Path planning (NavFn / SmacPlanner) |
| `nav2_controller` | 1.1.20 | Path following — **MPPI Controller** |
| `nav2_bt_navigator` | 1.1.20 | Behavior Tree based mission orchestration |
| `nav2_behaviors` | 1.1.20 | Recovery behaviors (spin, backup, wait) |
| `nav2_velocity_smoother` | 1.1.20 | Smooth velocity commands |
| `nav2_lifecycle_manager` | 1.1.20 | Lifecycle management for all Nav2 nodes |
| `nav2_mppi_controller` | 1.1.20 | MPPI local controller plugin |
| `nav2_behavior_tree` | 1.1.20 | BT library dependency |
| `nav2_msgs` | 1.1.20 | Nav2 message/service definitions |
| `nav2_route` | 1.1.20 | Route server |
| `nav2_costmap_2d` | 1.1.20 | 2D costmap (obstacle layer, inflation) |
| `nav2_map_server` | 1.1.20 | Static map serving |
| `nav2_amcl` | 1.1.20 | Adaptive Monte Carlo Localization |

> [!NOTE]
> Nav2 **1.1.x** is the Humble-specific release line. The main development branch (Iron/Rolling) is at 1.2.x+. Version 1.1.20 includes all critical bugfixes backported to Humble.

---

## Gazebo Simulation Stack

| Component | Version | Notes |
|-----------|---------|-------|
| **Gazebo (Ignition)** | **Fortress 6.16.0** | LTS release, paired with ROS 2 Humble |
| **ros_gz_bridge** | 0.244.23 | ROS↔Gazebo message bridge |
| **ros_gz_sim** | 0.244.23 | Gazebo launch integration |

> [!IMPORTANT]
> This project uses **Ignition Fortress (v6)**, NOT Gazebo Harmonic (v8). Message types must use `ignition.msgs.*` format, NOT `gz.msgs.*`. This is explicitly noted in `sim.launch.py`.

### Ignition Fortress ↔ ROS 2 Humble Compatibility

| Ignition Fortress | ROS 2 Humble | Status |
|--------------------|-------------|--------|
| `ign gazebo` (v6) | `ros_gz` 0.244.x | ✅ Official pairing |

---

## SLAM & Localization

| Component | Version |
|-----------|---------|
| **SLAM Toolbox** | 2.6.10 | 
| **Robot State Publisher** | 3.0.3 |

---

## Visualization

| Component | Version |
|-----------|---------|
| **RViz2** | 11.2.26 |

---

## Version Compatibility Matrix

```
┌─────────────────────────────────────────────────────┐
│              Ubuntu 22.04 LTS (Jammy)               │
│                  Python 3.10.12                     │
├─────────────────────────────────────────────────────┤
│            ROS 2 Humble Hawksbill (LTS)             │
│                  rclpy 3.3.21                       │
├──────────────────┬──────────────────────────────────┤
│   Nav2 1.1.20    │   Ignition Fortress 6.16.0      │
│   (Humble LTS)   │   ros_gz 0.244.23               │
├──────────────────┼──────────────────────────────────┤
│ SLAM Toolbox     │   RViz2 11.2.26                  │
│ 2.6.10           │                                  │
└──────────────────┴──────────────────────────────────┘
```

> [!TIP]
> All components are on the **Humble LTS** track. This is the recommended and officially supported combination. Everything is version-compatible.

---

## Nav2 Release Model Explained

Nav2 follows a **per-ROS-distro branching model**:

1. **Main branch** → targets ROS 2 Rolling (bleeding edge)
2. **Distro branches** (e.g., `humble`, `iron`) → receive bugfixes and minor features backported from main
3. **Release cadence** → bugfix releases are cut roughly monthly via the ROS buildfarm
4. **Version scheme**: `1.1.x` = Humble line, `1.2.x` = Iron line, `1.3.x` = Jazzy line

Your system is on **Nav2 1.1.20** which is a mature, stable release with 20 patch releases worth of bugfixes since the initial Humble release.

### Key Nav2 Features Available in 1.1.20 (Humble)
- ✅ MPPI Controller (Model Predictive Path Integral)
- ✅ Velocity Smoother
- ✅ SmacPlanner (Hybrid-A*, 2D, Lattice)
- ✅ Regulated Pure Pursuit
- ✅ Behavior Trees with custom XML
- ✅ Route Server
- ✅ Collision Monitor
- ✅ Graceful Controller
- ✅ Constrained Smoother

---

## EVOART-O Custom Packages

| Package | Version | Build System |
|---------|---------|-------------|
| `evoart_interfaces` | 0.0.1 | ament_cmake |
| `evoart_description` | — | ament_cmake (URDF/Xacro) |
| `evoart_brain` | 0.0.1 | ament_cmake |
| `evoart_bringup` | 0.0.1 | ament_cmake |
