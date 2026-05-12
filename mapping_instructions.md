# Phase 2: The SLAM Mapping Run

It's time to build the static map. The "Brain" (`geojson_navigator`) has been temporarily disconnected from the steering wheel so it won't fight you for control while you map the track.

## Why are we doing this?
Right now, the Global Planner is driving **"blind."** It only uses a rolling 6-meter window based on live laser scans. Because it doesn't know what the track looks like beyond 6 meters, it draws straight lines directly to the destination—often right through walls!
By manually driving the track and generating a 2D Static Map, we give the Global Planner the entire track layout *before* the car even starts moving. This allows the planner to instantly calculate a perfect, curved, collision-free path from Point A to Point B that perfectly stays inside the lane.

Please follow these exact steps to drive your car and generate the map:

### 1. Launch the Simulation (Terminal 1)
Run your usual command. Gazebo and RViz will open, and SLAM will start building a map, but the car will sit still.

```bash
source .venv/bin/activate
source install/setup.bash
ros2 launch evoart_bringup sim_full.launch.py
```

### 2. Drive the Car (Terminal 2)
Open a brand new terminal, activate your workspace, and launch the manual teleop node. We will map your keyboard straight to the Nav2 controller topic:

```bash
source .venv/bin/activate
source install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=cmd_vel_nav
```

> **Controls:** Use `i` (forward), `,` (reverse), and `j`/`l` (steer) to drive the car around the track. Drive at a reasonable speed to give the laser scanner time to accurately map the walls.

### 3. Save the Map (Terminal 3)
Once you have driven a full lap and you can see the track layout fully mapped in RViz, open a third terminal and run this command to save the snapshot:

```bash
source .venv/bin/activate
source install/setup.bash
ros2 run nav2_map_server map_saver_cli -f teknofest_2024
```

*(This will generate `teknofest_2024.yaml` and `teknofest_2024.pgm` in your current directory).*
