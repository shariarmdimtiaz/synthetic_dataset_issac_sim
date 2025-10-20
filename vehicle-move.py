# Isaac Sim 5.x — Curve Follow the Object/Vehicle (Bezier/Freehand)

from pxr import Usd, UsdGeom, Gf
import omni.usd, omni.timeline, math


# ===== Settings =====
OBJ_PATH       = "/World/hyundai_tucson"
CURVE_PATH     = "/World/BasisCurves"
DIVS           = 240
WORLD_UP       = Gf.Vec3d(0, 1, 0)
LOCAL_FORWARD  = "+Z"
LOCAL_UP       = "+Y"
START_FRAME    = None


#