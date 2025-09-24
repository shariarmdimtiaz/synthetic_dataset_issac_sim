# Isaac Sim Script Editor - Run inside Isaac Sim
import asyncio, os, csv, numpy as np
from pxr import Usd, UsdGeom, Gf
import omni, omni.timeline
import omni.replicator.core as rep
import imageio.v2 as iio
import matplotlib.cm as cm
import matplotlib

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


#--------- check the camera --------------
os.makedirs(OUTPUT_DIR, exist_ok=True)
rgb_dir   = os.path.join(OUTPUT_DIR, "rgb");   os.makedirs(rgb_dir, exist_ok=True)
depth_dir = os.path.join(OUTPUT_DIR, "depth"); os.makedirs(depth_dir, exist_ok=True)

stage = omni.usd.get_context().get_stage()
cam_prim = stage.GetPrimAtPath(CAM_PATH)
obj_prim = stage.GetPrimAtPath(OBJ_PATH)
assert cam_prim.IsValid() and obj_prim.IsValid()

stage.SetTimeCodesPerSecond(FPS)
cam = UsdGeom.Camera(cam_prim)
cam.GetClippingRangeAttr().Set(Gf.Vec2f(0.02, 1000.0))

#--------- render the scene ------------
render_product = rep.create.render_product(CAM_PATH, RESOLUTION)
rgb_annot   = rep.AnnotatorRegistry.get_annotator("rgb")
depth_annot = rep.AnnotatorRegistry.get_annotator("distance_to_camera")
rgb_annot.attach(render_product); depth_annot.attach(render_product)

timeline = omni.timeline.get_timeline_interface()
timeline.stop()

# ----------check the world coordinate --------
def world_matrix(prim, timeCode):
    return UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(timeCode)
def world_position(prim, timeCode):
    t = world_matrix(prim, timeCode).ExtractTranslation()
    return Gf.Vec3d(t[0], t[1], t[2])
def world_bbox_center(prim, timeCode):
    cache = UsdGeom.BBoxCache(timeCode, [UsdGeom.Tokens.default_], useExtentsHint=False)
    return cache.ComputeWorldBound(prim).ComputeCentroid()

#---------- capture the rgb and depth map --------------
async def capture():
    start_f, end_f = FRAME_RANGE
    csv_path = os.path.join(OUTPUT_DIR, "frame_data.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as fcsv:
        writer = csv.writer(fcsv)
        writer.writerow(["frame","obj_x","obj_y","obj_z","cam_x","cam_y","cam_z","dist"])
        for frame in range(start_f, end_f + 1):
            sec = frame / FPS
            timeline.set_current_time(sec)
            # Replicator rendaring
            await omni.kit.app.get_app().next_update_async()
            await rep.orchestrator.step_async()

            t = Usd.TimeCode(frame)
            cam_pos    = world_position(cam_prim, t)
            obj_center = world_bbox_center(obj_prim, t)
            dist       = (obj_center - cam_pos).GetLength()

            # --- RGB ---
            rgb = rgb_annot.get_data()
            if rgb is not None:
                if rgb.ndim == 4 and rgb.shape[0] == 1: rgb = rgb[0]
                iio.imwrite(os.path.join(rgb_dir, f"rgb_{frame:06d}.png"), rgb[..., :3])

            # --- Depth (with colormap) ---
            depth = depth_annot.get_data()
            if depth is not None:
                depth = np.squeeze(depth).astype(np.float32)
                np.save(os.path.join(depth_dir, f"depth_{frame:06d}.npy"), depth)

                finite = np.isfinite(depth)
                if finite.any():
                    dmin, dmax = np.percentile(depth[finite], [1, 99])
                    dm = np.clip((depth - dmin) / (dmax - dmin + 1e-6), 0, 1)
                else:
                    dm = np.zeros_like(depth)

                # --- Apply color map ---            
                # cmap = matplotlib.colormaps["viridis"]
                depth_rgb = (cmap(dm)[..., :3] * 255).astype(np.uint8)
                iio.imwrite(os.path.join(depth_dir, f"depth_{frame:06d}.png"), depth_rgb)
            # --- CSV ---
            writer.writerow([
                frame,
                f"{obj_center[0]:.6f}", f"{obj_center[1]:.6f}", f"{obj_center[2]:.6f}",
                f"{cam_pos[0]:.6f}",   f"{cam_pos[1]:.6f}",   f"{cam_pos[2]:.6f}",
                f"{dist:.6f}"
            ])
    print(f"[DONE] Saved frames to {OUTPUT_DIR}")

async def driver():
    try:
        task = asyncio.create_task(capture())
        while not task.done():
            await omni.kit.app.get_app().next_update_async()
    finally:
        try: rgb_annot.detach()
        except: pass
        try: depth_annot.detach()
        except: pass
        try:
            rep.orchestrator.stop()
            rep.orchestrator.restop()
        except: pass
# execution
asyncio.ensure_future(driver())
