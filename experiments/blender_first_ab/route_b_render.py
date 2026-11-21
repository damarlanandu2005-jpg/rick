"""ROUTE B, Blender side: the existing look pass, full frame. NO new renderer: from_lock.build (set, 3D cards, camera, focus on the subject) + look.apply_look (the place's preset) + lock motion for moving set nodes.
  blender -b --factory-startup -P route_b_render.py -- <repo> <episode_dir> <out_dir> <W> <H> <ranges e.g. 0-149,201-210,316-330>
Writes <out_dir>/raw/b_#####.png (no grade, no overlay) and routeB_timing.json (cold build, first frame, per-frame seconds per range, GPU, settings, material report).
Settings are the shipped ones except: resolution 720x1280 (build sets 1440x2560) and motion blur OFF (Ricks: characters are never blurred)."""
import bpy, sys, os, json, time
A = sys.argv[sys.argv.index("--") + 1:]; repo, ep, out, W, H = A[0], A[1], A[2], int(A[3]), int(A[4]); ranges = [tuple(map(int, r.split("-"))) for r in A[5].split(",")]
sys.path.insert(0, os.path.join(repo, "templates"))
from blender_look import from_lock as FL, lock_motion as LM
os.makedirs(os.path.join(out, "raw"), exist_ok=True); sc = bpy.context.scene
lock = json.load(open(os.path.join(ep, "out", "lock", "lock.json"), encoding="utf-8")); P = lock["places"][0]; place = P["name"]; preset = P.get("light", "day")
def gpu_info():
    try:
        import gpu; p = gpu.platform; return {"vendor": p.vendor_get(), "renderer": p.renderer_get(), "version": p.version_get(), "backend": str(p.backend_type_get())}
    except Exception as e: return {"error": repr(e)}
SAMPLES = int(os.environ.get("RB_SAMPLES", "64"))
t0 = time.perf_counter(); K = FL.build(sc, ep, place=place, preset=preset, samples=SAMPLES, res=100, motion_blur=False); build_s = time.perf_counter() - t0
r = sc.render; r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100; r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGB"; r.image_settings.color_depth = "8"; r.use_file_extension = False
t1 = time.perf_counter(); moved = {}
if os.path.exists(os.path.join(ep, "out", "lock", "motion", place + ".json")):
    moved = LM.apply(K["set"], os.path.join(ep, "out", "lock"), place)          # moving set nodes (the coin flight, the flag, ...) frame for frame, as in the hybrid Phase 2
motion_s = time.perf_counter() - t1
rep = {"blender": bpy.app.version_string, "engine": sc.render.engine, "samples": sc.eevee.taa_render_samples, "resolution": [W, H], "preset": preset, "place": place, "build_s": round(build_s, 2), "lock_motion_s": round(motion_s, 2), "moved_nodes": len(moved),
       "settings": {"film_filter_size_px": r.filter_size, "view_transform": sc.view_settings.view_transform, "motion_blur": r.use_motion_blur, "dof": sc.camera.data.dof.use_dof, "fstop": sc.camera.data.dof.aperture_fstop, "raytracing": sc.eevee.use_raytracing, "card_texture_interpolation": "Cubic (from_lock.card)"},
       "materials": K["materials"], "n_set_objects": len(K["set"]), "gpu": gpu_info(), "ranges": {}}
for a, b in ranges:
    ts = []
    for f in range(a, b + 1):
        sc.frame_set(f); r.filepath = os.path.join(out, "raw", "b_%05d.png" % f); t = time.perf_counter(); bpy.ops.render.render(write_still=True); ts.append(round(time.perf_counter() - t, 3)); print("B", f, ts[-1], flush=True)
    rep["ranges"]["%d-%d" % (a, b)] = ts
json.dump(rep, open(os.path.join(out, "routeB_timing.json"), "w"), indent=1); print("ROUTE_B_DONE")
