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
DATA_ROOT_DIR = Path("C:/Users/User/Desktop/ehrms/20262/Simulation/data")
asset_path = str(DATA_ROOT_DIR / "usd" / "jetson_scene.usd")
stage_utils.add_reference_to_stage(usd_path=asset_path, path="/SceneAsset")

# Create dome light
dome_light = DomeLight("/World/DomeLight")
dome_light.set_intensities(1000)

# ==============================
# build map from .pgm file
# ==============================

import json
from PIL import Image
import numpy as np
from pxr import Gf, UsdGeom, UsdPhysics
import omni.usd

# Load map configuration
CONFIG_PATH = DATA_ROOT_DIR / "map_config" / "map.json"
with CONFIG_PATH.open("r", encoding="utf-8") as f:
    config = json.load(f)

image_path = CONFIG_PATH.parent / config["map_path"]
resolution = float(config["pixel_resolution"])
wall_height = float(config["wall_height"])
wall_thickness = float(config["wall_thickness"])
origin_x, origin_y, origin_yaw = config["origin"]

image = np.asarray(
    Image.open(image_path).convert("L")
)

height_px, width_px = image.shape
map_width = width_px * resolution
map_height = height_px * resolution

print(f'[INFO] Map size: {map_height,map_width}')

# Convert image into occupied cells
occupied = image < 100




print("[INFO] Map generation complete.")

# ========================================
# Simulation runs until GUI window closed
# ========================================

while simulation_app.is_running():
    simulation_app.update()

simulation_app.close()