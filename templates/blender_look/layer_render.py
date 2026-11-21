"""Blender enhancement layer, one process per layer (hybrid Phase 3). Generalised from the frozen Phase 1C script (phase1c/layer_reflect.py), same materials and passes.
  blender -b --factory-startup -P layer_render.py -- <repo> <episode_dir> <out_dir> <layer_id> <W> <H>
Reads out/plan/layers_baked.json[layer_id] (type, place, objects, frames, gain) and the lock. The mask is the NAMED lock objects (every name must exist in the lock glb, lock_id checked
against the lock's own ids when present); nothing is selected by material tag. Writes in <out_dir>: layer_#####.png (RGBA layer), idmask_#####.png (the intended mask),
align_#####.png + align_camera.json (registration pass), layer_timing.json, idmask_timing.json. Types: reflection (proven, Phase 1C). Characters are Holdout (cards keep their drawing alpha)."""
import bpy, sys, os, json, time, math, hashlib, re
A = sys.argv[sys.argv.index("--") + 1:]; repo, ep, out, lid, W, H = A[0], A[1], A[2], A[3], int(A[4]), int(A[5])
sys.path.insert(0, os.path.join(repo, "templates"))
from blender_look import from_lock as FL, lights as LT
from mathutils import Vector
os.makedirs(out, exist_ok=True); sc = bpy.context.scene
SPEC = json.load(open(os.path.join(ep, "out", "plan", "layers_baked.json")))[lid]; assert SPEC["type"] == "reflection", "layer type %r has no proven recipe" % SPEC["type"]
f0, f1 = SPEC["frames"]; GAIN = float(SPEC.get("gain", 0.5)); NAMES = list(SPEC["objects"]); SAMPLES = int(os.environ.get("P1_SAMPLES", "64"))
lock = json.load(open(os.path.join(ep, "out", "lock", "lock.json"), encoding="utf-8")); place = SPEC["place"]
pl = [p for p in lock["places"] if p["name"] == place][0]; preset = pl.get("light", "morning"); LL = lock["lights"][place]
def lin(h): return tuple(((int(h[i:i + 2], 16) / 255) ** 2.2) for i in (1, 3, 5))
def gpu_info():
    try:
        import gpu; p = gpu.platform; return {"vendor": p.vendor_get(), "renderer": p.renderer_get(), "version": p.version_get(), "backend": str(p.backend_type_get())}
    except Exception as e: return {"error": repr(e)}
t0 = time.perf_counter(); K = FL.build(sc, ep, place=place, preset=preset, samples=SAMPLES, res=100, motion_blur=False); build_s = time.perf_counter() - t0
r = sc.render; r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100; r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGBA"; r.image_settings.color_depth = "8"; r.use_file_extension = False
cam = K["camera"]; cam.data.dof.use_dof = False
objs = [o for o in K["set"] if o.type == "MESH"]; base_name = lambda o: re.sub(r"_\d{2,}$", "", o.name.split(".")[0] if o.name.rsplit(".", 1)[-1].isdigit() else o.name)   # three.js names repeats name, name_02, name_03; Blender adds .001: both are the same named object kind
hero = [o for o in objs if base_name(o) in NAMES]; found = sorted(set(base_name(o) for o in hero)); assert found == sorted(NAMES), "named objects not found in the lock set: missing %s" % sorted(set(NAMES) - set(found))
def mat(name, build):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(build(nt).outputs[0], o.inputs[0]); return m
def spec_node(nt):
    p = nt.nodes.new("ShaderNodeBsdfPrincipled"); I = p.inputs; I["Base Color"].default_value = (0, 0, 0, 1); I["Metallic"].default_value = 0.0; I["Roughness"].default_value = 0.2; I["IOR"].default_value = 1.5
    if "Specular IOR Level" in I: I["Specular IOR Level"].default_value = 0.5
    for k in ("Coat Weight", "Sheen Weight", "Emission Strength", "Subsurface Weight", "Transmission Weight"):
        if k in I: I[k].default_value = 0.0
    return p
def id_node(nt): e = nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value = (1, 1, 1, 1); e.inputs[1].default_value = 1.0; return e
HOLD, SPEC_M, ID_M = mat("HOLD", lambda nt: nt.nodes.new("ShaderNodeHoldout")), mat("LAYER_SPEC", spec_node), mat("LAYER_ID", id_node)
def assign(hero_mat):
    hs = set(hero)
    for ob in objs:
        for s in ob.material_slots: s.material = hero_mat if ob in hs else HOLD
ORIG = {}
def cards_to(kind):                       # "hold": the card alpha mix shows Holdout instead of its lit colour; "lit": fully self-lit (align pass)
    for who, cd in K["cards"].items():
        nt = cd["material"].node_tree; done = 0
        for n in list(nt.nodes):
            if n.bl_idname == "ShaderNodeMixShader" and n.inputs[1].is_linked:
                fn = n.inputs[1].links[0].from_node.bl_idname
                if kind == "hold" and fn == "ShaderNodeBsdfTransparent": ORIG[who] = (n, n.inputs[2].links[0].from_socket); nt.links.new(nt.nodes.new("ShaderNodeHoldout").outputs[0], n.inputs[2]); done += 1
                if kind == "lit" and fn == "ShaderNodeBsdfPrincipled": n.inputs[0].default_value = 1.0; done += 1
        assert done == 1, "card %s alpha mix not found" % who
def render_range(prefix):
    ts = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f); r.filepath = os.path.join(out, "%s_%05d.png" % (prefix, f)); t = time.perf_counter(); bpy.ops.render.render(write_still=True); ts.append(round(time.perf_counter() - t, 3)); print(prefix.upper(), f, ts[-1])
    return ts
def timing(mode, ts): 
    rep = dict(blender=bpy.app.version_string, engine=sc.render.engine, samples=sc.eevee.taa_render_samples, resolution=[W, H], frames=[f0, f1], n_frames=len(ts), build_s=round(build_s, 2), frame_s=ts, cold_first_frame_s=ts[0],
               steady_mean_s=round(sum(ts[1:]) / max(1, len(ts) - 1), 3), steady_max_s=max(ts[1:]) if len(ts) > 1 else None, total_render_s=round(sum(ts), 2), gpu=gpu_info(), preset=preset, place=place, layer=lid, objects=NAMES, gain=GAIN, dof_in_blender=False)
    json.dump(rep, open(os.path.join(out, "%s_timing.json" % mode), "w"), indent=1)
# ---- layer: the lock's sun and sky (not the preset's), key + sky x gain ----
for o in list(bpy.data.objects):
    if o.type == "LIGHT" and o.name.startswith("Fill"): bpy.data.objects.remove(o, do_unlink=True)
d3 = LL["dir"]; toward = Vector((d3[0], -d3[2], d3[1]))
for o in bpy.data.objects:
    if o.type == "LIGHT" and o.name.startswith("Key"): o.rotation_euler = toward.normalized().to_track_quat("Z", "Y").to_euler(); o.data.color = lin(LL["sun"]); o.data.energy *= GAIN
LT.sky(sc, [(0, lin(LL["hor"])), (.65, lin(LL["top"]))], False, GAIN); r.film_transparent = True
cards_to("hold"); assign(SPEC_M); timing("layer", render_range("layer"))
# ---- idmask: same geometry, the named objects flat white ----
assign(ID_M); sc.view_settings.view_transform = "Standard"; sc.eevee.taa_render_samples = 16; timing("idmask", render_range("idmask"))
# ---- align: every set object + cards flat, opaque background, mid frame ----
r.film_transparent = False
if sc.world and getattr(sc.world, "node_tree", None):
    for n in sc.world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground": n.inputs[1].default_value = 0.0
cache = {}
def flat(key):
    if key not in cache:
        c = [(int(hashlib.md5((key + s).encode()).hexdigest()[:2], 16) / 255) for s in "rgb"]
        def b(nt): e = nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value = (c[0], c[1], c[2], 1); e.inputs[1].default_value = 1.0; return e
        cache[key] = mat("A_" + key, b)
    return cache[key]
for ob in objs:
    for s in ob.material_slots: s.material = flat(ob.data.name)
for who, cd in K["cards"].items():             # put the lit card colour back (the layer passes had Holdout there), fully self-lit as in Phase 1
    n, src = ORIG[who]; nt = cd["material"].node_tree; nt.links.new(src, n.inputs[2]); src.node.inputs[0].default_value = 1.0
fm = (f0 + f1) // 2; sc.frame_set(fm); bpy.context.view_layer.update(); r.filepath = os.path.join(out, "align_%05d.png" % fm); t = time.perf_counter(); bpy.ops.render.render(write_still=True); dt = round(time.perf_counter() - t, 3)
bk = [c for c in json.load(open(os.path.join(ep, "out", "plan", "camera_baked.json")))["frames"] if c["f"] == fm][0]; size = json.load(open(os.path.join(ep, "film.json"))).get("size", [1080, 1920])
json.dump(dict(frame=fm, render_s=dt, blender_fov_v_deg=round(math.degrees(cam.data.angle_y), 4), baked_fov_v_deg=bk["fov_v"], blender_pos=[round(v, 4) for v in cam.matrix_world.translation], baked_pos=bk["pos"], res=[r.resolution_x, r.resolution_y],
          aspect=round(r.resolution_x / r.resolution_y, 5), aspect_baked=round(size[0] / size[1], 5), sensor_fit=cam.data.sensor_fit), open(os.path.join(out, "align_camera.json"), "w"), indent=1); print("LAYER_RENDER_DONE", lid)
