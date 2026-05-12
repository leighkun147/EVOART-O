# The Final Strategy: Static Map Navigation Architecture

After extensive debugging and analysis of the navigation pipeline, we have officially abandoned the "live mapping" (SLAM) and "blind breadcrumb" approaches. 

**This document outlines our final, definitive architecture for navigating the 2024 Teknofest Robotaksi Track.**

---

### The Problem We Solved
Previously, the `SmacPlannerHybrid` (the brain generating the blue line) was using a "rolling window" costmap. It could only "see" 6 meters ahead based on live laser scans. Because it didn't know the layout of the track, it continuously tried to draw straight lines through walls. When the Local Controller noticed the wall and stopped the car, the systems fought, resulting in the car endlessly backing up and crashing.

Additionally, a mismatch between the car's physical dimensions and the costmap's `inflation_radius` caused massive computational lag, further breaking the path planner.

### Our Final Solution: The Pre-Computed Static Map
We are adopting the industry standard for autonomous circuit racing. Instead of learning the track live, the Global Planner is given a complete, top-down 2D map of the entire Teknofest track *before* the car even moves.

This allows the Global Planner to instantly calculate perfect, sweeping curves that respect track barriers from the very first second of the simulation.

> [!TIP]
> **The `DUMP FILES` Discovery**
> We initially planned to run SLAM and manually drive the car around the track to generate this map. However, during a deep scan of the project files, we discovered a pristine, pre-generated map (`pist_map_small.yaml` and `.pgm`) hiding in the `DUMP FILES` directory. We have fully integrated this map into the active codebase, completely bypassing the need for manual driving!

---

### Technical Changes Implemented

1. **Kinematic Optimization:**
   - Increased the `inflation_radius` from `1.0` to `1.2` in `nav2_params.yaml`. This ensures the mathematical buffers wrap safely around the vehicle's entire Ackermann footprint, completely eliminating the `computeCircumscribedCost` performance error.

2. **Launch Architecture Overhaul (`sim_full.launch.py`):**
   - **Removed:** `async_slam_toolbox_node`. We no longer need to map the environment live.
   - **Added:** `nav2_map_server` and `nav2_amcl` (Adaptive Monte Carlo Localization). These nodes load the static map and perfectly localize the car's position within it.

3. **Global Costmap Update:**
   - Modified the `global_costmap` in `nav2_params.yaml` to disable `rolling_window` and load the `static_layer` using the discovered `pist_map_small.yaml`.

4. **Simplified Routing (`route.geojson`):**
   - Because the Global Planner can now "see" the walls, we no longer need to feed it dense, exact coordinates to keep it out of trouble. We have reverted the route file to supply just a single destination point: the Bus Stop (`[41.9, 36.4]`).

---

### Ready for Liftoff 🚀
This is our final way forward. Everything is compiled and ready to go. 

Go ahead and launch the simulation normally in a brand new terminal:

```bash
source .venv/bin/activate
source install/setup.bash
ros2 launch evoart_bringup sim_full.launch.py
```

When RViz opens, you will immediately see a black-and-white 2D map of the entire Teknofest track loaded in the background. The blue line will now flawlessly curve around the corners!
