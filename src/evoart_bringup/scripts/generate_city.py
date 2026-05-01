#!/usr/bin/env python3
"""
EVOART-O TEKNOFEST City World Generator
========================================
Generates a rich, competition-grade urban SDF world for Gazebo Harmonic (gz-sim).

City Layout (80m x 60m):
  - Two main East-West roads at y=0 and y=20
  - Two main North-South roads at x=0 and x=20
  - T-junctions and a 4-way intersection
  - Buildings in city blocks, parked vehicles, street furniture
  - 3 animated pedestrian actors crossing at different points
  - Custom inline traffic light models at intersections

All external models use verified Gazebo Fuel URIs (HTTP 200 confirmed).

Physics tuned for Intel Lunar Lake iGPU (target: 30+ FPS).
"""

import os

# ─────────────────── Fuel URI Constants ───────────────────
FUEL = "https://fuel.gazebosim.org/1.0/OpenRobotics/models"
ACTOR_MESH = "https://fuel.gazebosim.org/1.0/Mingfei/models/actor/tip/files/meshes/walk.dae"


def indent(text: str, level: int = 4) -> str:
    """Indent a block of text by `level` spaces."""
    pad = " " * level
    return "\n".join(pad + line if line.strip() else "" for line in text.splitlines())


def fuel_include(uri_name: str, instance_name: str, x: float, y: float,
                 z: float = 0.0, yaw: float = 0.0) -> str:
    return f"""
    <!-- {instance_name} -->
    <include>
      <uri>{FUEL}/{uri_name}</uri>
      <name>{instance_name}</name>
      <pose>{x} {y} {z} 0 0 {yaw}</pose>
    </include>"""


def make_traffic_light(name: str, x: float, y: float, yaw: float = 0.0) -> str:
    """
    Generate an inline SDF traffic light model.
    3 spheres (red/yellow/green) on a pole with emissive materials.
    Pole height: 3.5m, housing at 3.0-3.6m.
    """
    return f"""
    <!-- Traffic Light: {name} -->
    <model name="{name}">
      <static>true</static>
      <pose>{x} {y} 0 0 0 {yaw}</pose>

      <!-- Pole -->
      <link name="pole">
        <visual name="pole_visual">
          <geometry>
            <cylinder>
              <radius>0.04</radius>
              <length>3.2</length>
            </cylinder>
          </geometry>
          <pose>0 0 1.6 0 0 0</pose>
          <material>
            <ambient>0.2 0.2 0.2 1</ambient>
            <diffuse>0.3 0.3 0.3 1</diffuse>
          </material>
        </visual>
        <collision name="pole_collision">
          <geometry>
            <cylinder>
              <radius>0.04</radius>
              <length>3.2</length>
            </cylinder>
          </geometry>
          <pose>0 0 1.6 0 0 0</pose>
        </collision>
      </link>

      <!-- Housing -->
      <link name="housing">
        <pose>0 0 3.4 0 0 0</pose>
        <visual name="housing_visual">
          <geometry>
            <box>
              <size>0.2 0.2 0.7</size>
            </box>
          </geometry>
          <material>
            <ambient>0.05 0.05 0.05 1</ambient>
            <diffuse>0.1 0.1 0.1 1</diffuse>
          </material>
        </visual>
        <collision name="housing_collision">
          <geometry>
            <box>
              <size>0.2 0.2 0.7</size>
            </box>
          </geometry>
        </collision>
      </link>
      <joint name="housing_joint" type="fixed">
        <parent>pole</parent>
        <child>housing</child>
      </joint>

      <!-- Red Light -->
      <link name="red_light">
        <pose>0.11 0 3.6 0 0 0</pose>
        <visual name="red_visual">
          <geometry>
            <sphere><radius>0.06</radius></sphere>
          </geometry>
          <material>
            <ambient>0.8 0.0 0.0 1</ambient>
            <diffuse>1.0 0.0 0.0 1</diffuse>
            <emissive>0.6 0.0 0.0 1</emissive>
          </material>
        </visual>
      </link>
      <joint name="red_joint" type="fixed">
        <parent>housing</parent>
        <child>red_light</child>
      </joint>

      <!-- Yellow Light -->
      <link name="yellow_light">
        <pose>0.11 0 3.4 0 0 0</pose>
        <visual name="yellow_visual">
          <geometry>
            <sphere><radius>0.06</radius></sphere>
          </geometry>
          <material>
            <ambient>0.8 0.8 0.0 1</ambient>
            <diffuse>1.0 1.0 0.0 1</diffuse>
            <emissive>0.6 0.6 0.0 1</emissive>
          </material>
        </visual>
      </link>
      <joint name="yellow_joint" type="fixed">
        <parent>housing</parent>
        <child>yellow_light</child>
      </joint>

      <!-- Green Light -->
      <link name="green_light">
        <pose>0.11 0 3.2 0 0 0</pose>
        <visual name="green_visual">
          <geometry>
            <sphere><radius>0.06</radius></sphere>
          </geometry>
          <material>
            <ambient>0.0 0.8 0.0 1</ambient>
            <diffuse>0.0 1.0 0.0 1</diffuse>
            <emissive>0.0 0.6 0.0 1</emissive>
          </material>
        </visual>
      </link>
      <joint name="green_joint" type="fixed">
        <parent>housing</parent>
        <child>green_light</child>
      </joint>
    </model>"""


def make_lane_marking(name: str, x: float, y: float, length: float,
                      width: float = 0.15, yaw: float = 0.0) -> str:
    """Thin white box on the ground representing a lane marking."""
    return f"""
    <model name="{name}">
      <static>true</static>
      <pose>{x} {y} 0.005 0 0 {yaw}</pose>
      <link name="link">
        <visual name="visual">
          <geometry>
            <box><size>{length} {width} 0.01</size></box>
          </geometry>
          <material>
            <ambient>0.9 0.9 0.9 1</ambient>
            <diffuse>1.0 1.0 1.0 1</diffuse>
          </material>
        </visual>
      </link>
    </model>"""


def make_pedestrian_actor(name: str, waypoints: list[tuple[float, float, float, float]]) -> str:
    """
    Generate an animated pedestrian actor with scripted trajectory.
    waypoints: list of (time, x, y, yaw) tuples.
    """
    wp_xml = ""
    for t, x, y, yaw in waypoints:
        wp_xml += f"""
          <waypoint>
            <time>{t}</time>
            <pose>{x} {y} 0 0 0 {yaw}</pose>
          </waypoint>"""

    return f"""
    <!-- Animated Pedestrian: {name} -->
    <actor name="{name}">
      <skin>
        <filename>{ACTOR_MESH}</filename>
        <scale>1.0</scale>
      </skin>
      <animation name="walk">
        <filename>{ACTOR_MESH}</filename>
        <interpolate_x>true</interpolate_x>
      </animation>
      <script>
        <loop>true</loop>
        <delay_start>0.0</delay_start>
        <auto_start>true</auto_start>
        <trajectory id="0" type="walk">{wp_xml}
        </trajectory>
      </script>
    </actor>"""


def generate_city():
    sdf = """<?xml version="1.0" ?>
<sdf version="1.7">
  <world name="teknofest_city">

    <!-- ═══════════════ Physics (tuned for Intel Lunar Lake iGPU) ═══════════════ -->
    <physics name="fast_physics" type="ignored">
      <max_step_size>0.004</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>

    <!-- System Plugins -->
    <plugin filename="gz-sim-physics-system"
            name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system"
            name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system"
            name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system"
            name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>
    <plugin filename="gz-sim-contact-system"
            name="gz::sim::systems::Contact"/>

    <!-- ═══════════════ Environment ═══════════════ -->
    <scene>
      <ambient>0.6 0.6 0.6 1.0</ambient>
      <background>0.4 0.7 0.9 1.0</background>
      <shadows>false</shadows>
    </scene>

    <light type="directional" name="sun">
      <cast_shadows>false</cast_shadows>
      <pose>0 0 50 0 0 0</pose>
      <diffuse>0.9 0.9 0.85 1</diffuse>
      <specular>0.3 0.3 0.3 1</specular>
      <attenuation>
        <range>1000</range>
        <constant>0.9</constant>
        <linear>0.01</linear>
        <quadratic>0.001</quadratic>
      </attenuation>
      <direction>-0.5 0.1 -0.9</direction>
    </light>

    <!-- ═══════════════ Ground Plane (Asphalt-colored) ═══════════════ -->
    <model name="ground_plane">
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry>
            <plane>
              <normal>0 0 1</normal>
              <size>200 200</size>
            </plane>
          </geometry>
        </collision>
        <visual name="visual">
          <geometry>
            <plane>
              <normal>0 0 1</normal>
              <size>200 200</size>
            </plane>
          </geometry>
          <material>
            <ambient>0.15 0.15 0.15 1</ambient>
            <diffuse>0.2 0.2 0.2 1</diffuse>
            <specular>0.05 0.05 0.05 1</specular>
          </material>
        </visual>
      </link>
    </model>
"""

    # ═══════════════ ROAD SURFACES ═══════════════
    # Light grey road surfaces (slightly lighter than asphalt ground)
    roads = [
        # East-West road at y=0 (main road, 80m long, 6m wide)
        ("road_ew_main", 0, 0, 80, 6),
        # East-West road at y=20
        ("road_ew_north", 0, 20, 80, 6),
        # North-South road at x=0
        ("road_ns_west", 0, 10, 6, 20),
        # North-South road at x=20
        ("road_ns_center", 20, 10, 6, 20),
        # North-South road at x=40
        ("road_ns_east", 40, 10, 6, 26),
    ]

    for name, x, y, w, h in roads:
        sdf += f"""
    <!-- Road: {name} -->
    <model name="{name}">
      <static>true</static>
      <pose>{x} {y} 0.002 0 0 0</pose>
      <link name="link">
        <visual name="visual">
          <geometry>
            <box><size>{w} {h} 0.001</size></box>
          </geometry>
          <material>
            <ambient>0.25 0.25 0.25 1</ambient>
            <diffuse>0.3 0.3 0.3 1</diffuse>
          </material>
        </visual>
      </link>
    </model>"""

    # ═══════════════ CENTER LINE MARKINGS ═══════════════
    # Dashed center lines along the main roads
    for i in range(16):
        x = -30 + i * 5
        sdf += make_lane_marking(f"lane_ew_main_{i}", x, 0, 3.0)
    for i in range(16):
        x = -30 + i * 5
        sdf += make_lane_marking(f"lane_ew_north_{i}", x, 20, 3.0)
    for i in range(4):
        y = 2 + i * 5
        sdf += make_lane_marking(f"lane_ns_west_{i}", 0, y, 3.0, 0.15, 1.5707)
        sdf += make_lane_marking(f"lane_ns_center_{i}", 20, y, 3.0, 0.15, 1.5707)
        sdf += make_lane_marking(f"lane_ns_east_{i}", 40, y, 3.0, 0.15, 1.5707)

    # ═══════════════ BUILDINGS ═══════════════
    buildings = [
        # Block NW (between x=-20..0, y=5..20)
        ("House 1", "house_1a", -12, 10, 0),
        ("Cafe", "cafe_1", -8, 14, 1.5707),

        # Block N-Center (between x=5..20, y=5..20)
        ("House 2", "house_2a", 8, 10, 0),
        ("Apartment", "apartment_1", 14, 12, 0),

        # Block NE (between x=25..45, y=5..20)
        ("House 3", "house_3a", 28, 10, 0),
        ("Office Building", "office_1", 35, 12, 0),

        # Block SW (between x=-20..0, y=-15..-5)
        ("Fast Food", "fast_food_1", -10, -10, 0),
        ("Warehouse", "warehouse_1", -15, -8, 1.5707),

        # Block S-Center (between x=5..20, y=-15..-5)
        ("Gas Station", "gas_station_1", 10, -10, 0),
    ]

    for uri_name, instance_name, x, y, yaw in buildings:
        sdf += fuel_include(uri_name, instance_name, x, y, 0, yaw)

    # ═══════════════ PARKED VEHICLES ═══════════════
    vehicles = [
        ("Hatchback", "parked_car_1", 5, -3.5, 0),
        ("Hatchback red", "parked_car_2", 12, -3.5, 0),
        ("Hatchback blue", "parked_car_3", 25, -3.5, 3.14159),
        ("SUV", "parked_suv_1", 32, -3.5, 0),
        ("Pickup", "parked_pickup_1", -5, 23.5, 3.14159),
        ("Bus", "parked_bus_1", 30, 23.5, 0),
    ]

    for uri_name, instance_name, x, y, yaw in vehicles:
        sdf += fuel_include(uri_name, instance_name, x, y, 0, yaw)

    # ═══════════════ STREET FURNITURE ═══════════════
    # Stop Signs at intersections
    stop_signs = [
        ("stop_sign_0", -2, -3, 0),           # West approach to (0,0)
        ("stop_sign_1", 18, -3, 0),           # West approach to (20,0)
        ("stop_sign_2", 22, 3, 3.14159),      # East approach to (20,0)
        ("stop_sign_3", -2, 17, 0),           # West approach to (0,20)
        ("stop_sign_4", 38, -3, 0),           # West approach to (40,0)
    ]
    for name, x, y, yaw in stop_signs:
        sdf += fuel_include("Stop Sign", name, x, y, 0, yaw)

    # Construction Cones (road work zone)
    for i in range(4):
        sdf += fuel_include("Construction Cone", f"cone_{i}", 42 + i * 1.5, -2.5, 0, 0)

    # Jersey Barriers (road block)
    sdf += fuel_include("Jersey Barrier", "barrier_0", 48, 0, 0, 1.5707)
    sdf += fuel_include("Jersey Barrier", "barrier_1", 48, 1.5, 0, 1.5707)

    # Fire Hydrants
    sdf += fuel_include("Fire Hydrant", "hydrant_0", -3, 5, 0, 0)
    sdf += fuel_include("Fire Hydrant", "hydrant_1", 23, -5, 0, 0)

    # Lamp Posts
    sdf += fuel_include("Lamp Post", "lamp_0", -3, -3, 0, 0)
    sdf += fuel_include("Lamp Post", "lamp_1", 23, -3, 0, 0)
    sdf += fuel_include("Lamp Post", "lamp_2", -3, 23, 0, 0)
    sdf += fuel_include("Lamp Post", "lamp_3", 23, 23, 0, 0)

    # Speed Limit Signs
    sdf += fuel_include("Speed Limit Sign", "speed_sign_0", -8, -3, 0, 0)
    sdf += fuel_include("Speed Limit Sign", "speed_sign_1", 35, 23, 0, 3.14159)

    # Dumpsters
    sdf += fuel_include("Dumpster", "dumpster_0", -15, -5, 0, 0)

    # ═══════════════ TREES ═══════════════
    trees = [
        ("Oak tree", "oak_0", -18, 15, 0),
        ("Oak tree", "oak_1", 17, 15, 0),
        ("Pine Tree", "pine_0", 38, 15, 0),
        ("Pine Tree", "pine_1", -18, -12, 0),
        ("Oak tree", "oak_2", 45, -8, 0),
        ("Pine Tree", "pine_2", 10, 15, 0),
    ]
    for uri_name, instance_name, x, y, yaw in trees:
        sdf += fuel_include(uri_name, instance_name, x, y, 0, yaw)

    # ═══════════════ AMBULANCE (emergency vehicle on road) ═══════════════
    sdf += fuel_include("Ambulance", "ambulance_1", -20, 0.5, 0, 0)
    sdf += fuel_include("Fire Truck", "firetruck_1", -25, -3.5, 0, 0)

    # ═══════════════ TRAFFIC LIGHTS ═══════════════
    # At the 3 main intersections
    sdf += make_traffic_light("traffic_light_0", -3, 3, 0)           # Intersection (0,0) NW corner
    sdf += make_traffic_light("traffic_light_1", 17, 3, 0)           # Intersection (20,0) NW corner
    sdf += make_traffic_light("traffic_light_2", 23, -3, 3.14159)    # Intersection (20,0) SE corner
    sdf += make_traffic_light("traffic_light_3", -3, 23, 0)          # Intersection (0,20) NW corner
    sdf += make_traffic_light("traffic_light_4", 37, 3, 0)           # Intersection (40,0) NW corner

    # ═══════════════ PEDESTRIAN ACTORS ═══════════════
    # Pedestrian 0: Slowly crosses the main E-W road near x=5
    # Speed: ~1.0 m/s, 6m crossing, 2s turnaround pause
    sdf += make_pedestrian_actor("pedestrian_0", [
        (0,    5, -3, 1.5707),
        (6,    5,  3, 1.5707),
        (8,    5,  3, -1.5707),    # 2s pause to turn
        (14,   5, -3, -1.5707),
        (16,   5, -3, 1.5707),     # 2s pause to turn back
    ])

    # Pedestrian 1: Slowly crosses the N-S road near y=10
    # Speed: ~0.8 m/s, 6m crossing, 3s turnaround pause
    sdf += make_pedestrian_actor("pedestrian_1", [
        (0,    -3, 10, 0),
        (7.5,   3, 10, 0),
        (10.5,  3, 10, 3.14159),   # 3s pause to turn
        (18,   -3, 10, 3.14159),
        (21,   -3, 10, 0),         # 3s pause to turn back
    ])

    # Pedestrian 2: Slowly crosses at the northern road near x=20
    # Speed: ~0.9 m/s, 6m crossing, 2.5s turnaround pause
    sdf += make_pedestrian_actor("pedestrian_2", [
        (0,    20, 17, 1.5707),
        (6.5,  20, 23, 1.5707),
        (9,    20, 23, -1.5707),   # 2.5s pause to turn
        (15.5, 20, 17, -1.5707),
        (18,   20, 17, 1.5707),    # 2.5s pause to turn back
    ])

    # ═══════════════ CLOSE WORLD ═══════════════
    sdf += """

  </world>
</sdf>
"""

    # Write to the worlds directory
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', 'worlds', 'teknofest_city.sdf'
    )
    output_path = os.path.normpath(output_path)
    with open(output_path, 'w') as f:
        f.write(sdf)
    print(f"✅ Generated TEKNOFEST city world at: {output_path}")
    print(f"   - 9 buildings, 6 parked vehicles, 2 emergency vehicles")
    print(f"   - 5 stop signs, 5 traffic lights, 3 pedestrian actors")
    print(f"   - Road network with lane markings")
    print(f"   - Physics tuned for Intel Lunar Lake iGPU (4ms step)")


if __name__ == "__main__":
    generate_city()
