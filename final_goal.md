# Final Goal: Technical Definition of Done

This document specifies the final state of the EVOART-O project. The project is considered complete when the vehicle autonomously navigates the competition track by perfectly synchronizing the following technical components.

## 1. Environment & Physical Reality
The car must successfully navigate the world expressed in:
- **`src/evoart_bringup/worlds/robotaksi_pist_2024.sdf`**
This file defines the physical boundaries, signs, and traffic lights that the car must respect.

## 2. Vehicle Design & Kinematics
The car must operate according to its physical design expressed in:
- **`src/evoart_description/urdf/evoart.xacro`**
This includes its wheelbase, steering limits, and sensor placements (Lidar/Camera).

## 3. Mapping & Localization (Self-Awareness)
The car will acquire mapping information and maintain its global position according to:
- **`src/evoart_brain/config/slam_params.yaml`** (for live mapping)
- **`src/evoart_brain/config/nav2_params.yaml`** (for costmap layers and localization)
The goal is zero-offset alignment between the car's internal map and the SDF world.

## 4. Navigation & Mission Control
The car will execute its mission and calculate trajectories based on:
- **`src/evoart_brain/config/route.geojson`**
This file defines the path centerline and mandatory stop points (Bus Stops).

## 5. Speed & Testing Protocol
- **Test Speed**: For current stress-testing and rapid iteration, the car is configured at **3X Velocity (4.17 m/s)**.
- **Original Speed**: The final production speed remains **1.39 m/s** (as per the original Gazebo plugin cap).
- **Goal**: The navigation stack must be robust enough to handle the 3X speed before we revert to the original velocity for the final competition run.

## 6. Definition of Completion
We are finished when the car can launch, map the environment, localize itself, and reach its destination in the 2024 SDF world—all while maintaining the stability and safety logic defined in the configuration files above.
