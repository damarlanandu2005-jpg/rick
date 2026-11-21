"""PHASE 2 Blender side. blender -b --factory-startup -P flight_blender.py -- <repo> <ep> <out> <W> <H> <frames comma list>
The lock's set + camera via from_lock.build, the lock's motion via lock_motion.apply (frame for frame), then ONLY the flight object is shown (emission, everything else hidden),
rendered with film_transparent. Writes flight_blender.json: per frame the Blender world position of the flight object, its projection through the Blender camera, and the alpha centroid of the render."""
import bpy, sys, os, json, time
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
A = sys.argv[sys.argv.index("--") + 1:]; repo, ep, out, W, H = A[0], A[1], A[2], int(A[3]), int(A[4]); frames = [int(x) for x in A[5].split(",")]
sys.path.insert(0, os.path.join(repo, "templates"))
from blender_look import from_lock as FL, lock_motion as LM
os.makedirs(out, exist_ok=True); sc = bpy.context.scene
lock = json.load(open(os.path.join(ep, "out", "lock", "lock.json"), encoding="utf-8")); place = lock["places"][0]["name"]; preset = lock["places"][0].get("light", "morning")
t0 = time.perf_counter(); K = FL.build(sc, ep, place=place, preset=preset, samples=16, res=100, motion_blur=False); build_s = time.perf_counter() - t0
r = sc.render; r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100; r.film_transparent = True
r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGBA"; r.use_file_extension = False
cam = K["camera"]; cam.data.dof.use_dof = False; sc.view_settings.view_transform = "Standard"
t1 = time.perf_counter(); moved = LM.apply(K["set"], os.path.join(ep, "out", "lock"), place); motion_s = time.perf_counter() - t1
for c in K["cards"].values(): bpy.data.objects.remove(c["object"], do_unlink=True)     # card visibility is keyframed (hide_render), so a static hide would be overridden by frame_set: remove them, this gate measures the flight object alone
flights = [o for o in K["set"] if o.name.startswith("flight_")]; assert flights, "no flight_* object in the imported lock set"
for o in bpy.data.objects:
    if o.type in ("MESH", "EMPTY", "LIGHT") and o not in flights and o.type != "CAMERA": o.hide_render = True
for o in bpy.data.objects:
    if o.type == "MESH" and o not in flights: o.hide_render = True
for fo in flights:
    m = bpy.data.materials.new("flight_emit"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (1, 0, .84, 1); o_ = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o_.inputs[0])
    fo.data.materials.clear(); fo.data.materials.append(m)
if sc.world and sc.world.use_nodes: sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0
res = {"W": W, "H": H, "build_s": round(build_s, 2), "motion_s": round(motion_s, 2), "moved_nodes": moved, "frames": {}}
fo = flights[0]
for f in frames:
    sc.frame_set(f); bpy.context.view_layer.update()
    p = fo.matrix_world.translation.copy(); v = world_to_camera_view(sc, cam, p)
    path = os.path.join(out, "flight_%05d.png" % f); sc.render.filepath = path; t = time.perf_counter(); bpy.ops.render.render(write_still=True); dt = time.perf_counter() - t
    img = bpy.data.images.load(path); a = np.array(img.pixels[:], dtype=np.float32).reshape(H, W, 4)[::-1, :, 3]; bpy.data.images.remove(img)
    ys, xs = np.nonzero(a > .5); c = [float(xs.mean() + .5), float(ys.mean() + .5)] if len(xs) else None
    res["frames"][str(f)] = {"world": [round(x, 5) for x in p], "proj_px": [round(v.x * W, 3), round((1 - v.y) * H, 3)], "alpha_centroid_px": c, "alpha_px": int(len(xs)), "render_s": round(dt, 3), "scale": [round(x, 6) for x in fo.scale]}
json.dump(res, open(os.path.join(out, "flight_blender.json"), "w"), indent=1); print("flight_blender done", len(frames), "frames")
