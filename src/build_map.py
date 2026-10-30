from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless":False})

import isaacsim.core.experimental.utils.stage as stage_utils
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.core.experimental.objects import DomeLight
from pathlib import Path

# Enable `isaacsim.ros2.bridge` extension
import omni.kit.app

ext_manager = omni.kit.app.get_app().get_extension_manager()
ext_manager.set_extension_enabled_immediate(
    "isaacsim.ros2.bridge", True
)

# Load robot scene usd
DATA_ROOT_DIR = Path(__file__).parent.parent / "data"
asset_path = str(DATA_ROOT_DIR / "usd" / "jetson_scene.usd")
stage_utils.add_reference_to_stage(usd_path=asset_path, path="/SceneAsset")

# Create dome light
dome_light = DomeLight("/World/DomeLight")
dome_light.set_intensities(1000)

# ==============================
# build map from .pgm file
# ==============================

import omni.usd

stage = omni.usd.get_context().get_stage()

from pxr import UsdGeom, UsdPhysics, Gf, Sdf
from build_map_helper import build_map, add_wall_segment, pixel_to_world

root_path = "/World/GeneratedMap"
UsdGeom.Xform.Define(stage, root_path)

all_segments, config = build_map(DATA_ROOT_DIR)

resolution = config['resolution']
(origin_x, origin_y, origin_yaw) = config['origin']
default_thickness = float(config['wall_thickness'])
image_height = config['image_shape'][0]

for i, segment in enumerate(all_segments):
    cx_px, cy_px = segment["center_px"]
    
    cx, cy = pixel_to_world(
        cx_px,
        cy_px,
        image_height,
        resolution, 
        origin_x, 
        origin_y, 
    ) 
    
    # Place the wall so its bottom sits on z = 0. 
    height = segment["height_m"] 
    center_z = height / 2.0 
    
    # The estimated width can be noisy; enforce a minimum. 
    thickness = max( 
        segment["width_m"], 
        default_thickness, 
    ) 
    
    add_wall_segment( 
        stage=stage, 
        prim_path=f"{root_path}/Wall_{i:04d}", 
        center=(cx, cy, center_z), 
        length=segment["length_m"], 
        thickness=thickness, 
        height=height, 
        angle_deg=-segment["angle_deg"], 
    )

print("[INFO] Map generation complete.")

# ========================================
# Simulation runs until GUI window closed
# ========================================

while simulation_app.is_running():
    simulation_app.update()

simulation_app.close()