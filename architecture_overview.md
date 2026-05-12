# EVOART-O System Architecture Overview

This document explains the "who's who" in the EVOART-O codebase. It maps the virtual environment, the car's body, and its decision-making "brain" to specific files.

---

## 🌍 1. The Environment (The World)
The simulation environment defines the physics and visual world the car exists in.

*   **World & Static Obstacles:** `src/evoart_bringup/worlds/teknofest_city.sdf`
    *   Defines roads, buildings, intersections, and static objects like fire hydrants.
*   **Dynamic Actors (Pedestrians):** `src/evoart_brain/src/mock_perception_node.py`
    *   Provides ground-truth positions of pedestrians and traffic light states to the car's sensors.
*   **Launch Control:** `src/evoart_bringup/launch/sim.launch.py`
    *   The "on switch" that loads the world and spawns the vehicle.

---

## 🧠 2. The "Situation Room" (Thinking Mode)
This layer handles high-level decision making and visualization in RViz.

*   **Behavior Logic:** `src/evoart_brain/behavior_trees/taxi_logic.xml`
    *   The core decision-making tree (e.g., stop at red lights, handle recoveries).
*   **Navigation Planning:** `src/evoart_brain/config/nav2_params.yaml`
    *   Configures the Nav2 stack, which draws the paths and manages costmaps (obstacles).
*   **Visualization Layout:** `src/evoart_bringup/rviz/view.rviz`
    *   Tells RViz exactly what sensors and data to display in the UI.

---

## 🏎️ 3. The Car Model (Body & Sensors)
The physical structure and visual appearance of the robotaxi.

*   **Vehicle DNA (URDF):** `src/evoart_description/urdf/evoart.xacro`
    *   Defines wheelbase, steering limits, joint properties, and sensor mounts.
*   **Sensors:** Defined within the URDF.
    *   **LiDAR:** VLP-16 (for 3D obstacle detection).
    *   **Camera:** ZED 2i (for visual perception).

---

## 🕹️ 4. Driving & Control Logic
The chain of command that moves the car from Point A to Point B.

1.  **The GPS (Navigator):** `src/evoart_brain/src/geojson_navigator_node.py`
    *   Reads `route.geojson` and feeds sequential waypoints to the navigation system.
2.  **The Pilot (Nav2 Controller):** Configured in `nav2_params.yaml`.
    *   Calculates the exact steering angle and velocity needed to reach the next waypoint.
3.  **The Safety Filter (Brakes):** `src/evoart_brain/src/safety_stop_node.py`
    *   Sits between the Pilot and the Motors. It will override any driving command and stop the car if it detects a pedestrian in the path.

---

## 📋 Summary Table

| Component | Responsibility | Package |
| :--- | :--- | :--- |
| **World** | Roads, Buildings, Lights | `evoart_bringup` |
| **Brain** | High-level Decisions | `evoart_brain` |
| **GPS** | Route Following | `evoart_brain` |
| **Pilot** | Steering & Throttle | `nav2` |
| **Brakes** | Emergency Overrides | `evoart_brain` |
| **Body** | 3D Model & Sensors | `evoart_description` |
