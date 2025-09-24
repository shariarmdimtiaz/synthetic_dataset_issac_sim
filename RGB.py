# Isaac Sim Script Editor - Run inside Isaac Sim
import asyncio, os, csv, numpy as np
from pxr import Usd, UsdGeom, Gf
import omni, omni.timeline
import omni.replicator.core as rep
import imageio.v2 as iio
import matplotlib.cm as cm


# -------- settings --------
OUTPUT_DIR   = r"C:\Project\data"
CAM_PATH     = "/World/Camera"
OBJ_PATH     = "/World/Neo"
RESOLUTION   = (1920, 1440)
FPS          = 30
FRAME_RANGE  = (0, 120)


# ---------- create the output dir --------------
os.makedirs(OUTPUT_DIR, exist_ok=True)
rgb_dir   = os.path.join(OUTPUT_DIR, "rgb");   os.makedirs(rgb_dir, exist_ok=True)
depth_dir = os.path.join(OUTPUT_DIR, "depth"); os.makedirs(depth_dir, exist_ok=True)

