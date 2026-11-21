"""PHASE 1 seam experiment: ONE Blender enhancement layer (metal reflections) from the Ricks lock, nothing else.

Runs inside Blender:  blender -b --factory-startup -P layer_metal.py -- <repo> <episode_dir> <out_dir> <f0> <f1> <mode>
  mode "layer": the existing templates/blender_look/from_lock.build() path (camera, cards, set, library materials, 'morning' look),
                then: every NON-metal set slot and every card becomes a Holdout (cards keep their drawing's alpha), so the RGBA frame
                holds only the metal parts that are visible to the camera. Writes layer_#####.png and layer_timing.json.
  mode "align": same build(), but every material is a flat emission colour and the world is black: a flat picture of the same geometry
                and cards for the pixel-alignment test. Writes align_#####.png (middle frame) and align_camera.json.
Nothing from Ricks is edited. The only choices made here: Blender DOF off for the layer (the base has its own post DOF), PNG RGBA at the lock size.
"""
import bpy, sys, os, json, time, math, hashlib
A = sys.argv[sys.argv.index("--") + 1:]
repo, ep, out, f0, f1, mode = A[0], A[1], A[2], int(A[3]), int(A[4]), A[5]
SAMPLES = int(os.environ.get("P1_SAMPLES", "64"))
sys.path.insert(0, os.path.join(repo, "templates"))
from blender_look import from_lock as FL
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
lock = json.load(open(os.path.join(ep, "out", "lock", "lock.json"), encoding="utf-8"))
place = lock["places"][0]["name"]; preset = lock["places"][0].get("light", "morning"); W, H = lock["size"]

def gpu_info():
    try:
        import gpu; p = gpu.platform; return {"vendor": p.vendor_get(), "renderer": p.renderer_get(), "version": p.version_get(), "backend": str(p.backend_type_get())}
    except Exception as e: return {"error": repr(e)}

t_build = time.perf_counter()
K = FL.build(sc, ep, place=place, preset=preset, samples=SAMPLES, res=100, motion_blur=False)
build_s = time.perf_counter() - t_build
r = sc.render; r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100       # from_lock/render.py hard-code 1440x2560 (same 9:16); the lock says 1080x1920
r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGBA"; r.image_settings.color_depth = "8"; r.use_file_extension = False
cam = K["camera"]; cam.data.dof.use_dof = False
objs = [o for o in K["set"] if o.type == "MESH"]

def is_metal(m): return m is not None and (m.name.startswith("metal_") or m.name.startswith("painted_metal"))

if mode == "layer":
    r.film_transparent = True
    hm = bpy.data.materials.new("HOLD"); hm.use_nodes = True; nt = hm.node_tree; nt.nodes.clear()
    h = nt.nodes.new("ShaderNodeHoldout"); o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(h.outputs[0], o.inputs[0])
    n_metal = n_hold = 0; metal_names = set()
    for ob in objs:
        keep = False
        for s in ob.material_slots:
            if is_metal(s.material): keep = True; n_metal += 1; metal_names.add(s.material.name)
            else: s.material = hm; n_hold += 1
    for who, cd in K["cards"].items():                              # a card keeps its drawing's alpha: opaque drawing = holdout, transparent = see through to the metal behind
        nt = cd["material"].node_tree; done = 0
        for n in list(nt.nodes):
            if n.bl_idname == "ShaderNodeMixShader" and n.inputs[1].is_linked and n.inputs[1].links[0].from_node.bl_idname == "ShaderNodeBsdfTransparent":
                hd = nt.nodes.new("ShaderNodeHoldout"); nt.links.new(hd.outputs[0], n.inputs[2]); done += 1
        assert done == 1, "card %s: expected one alpha mix, found %d" % (who, done)
    times = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f); r.filepath = os.path.join(out, "layer_%05d.png" % f)
        t = time.perf_counter(); bpy.ops.render.render(write_still=True); times.append(round(time.perf_counter() - t, 3))
        print("LAYER_FRAME", f, times[-1])
    rep = dict(blender=bpy.app.version_string, engine=sc.render.engine, samples=SAMPLES, resolution=[W, H], frames=[f0, f1], n_frames=len(times),
               build_s=round(build_s, 2), frame_s=times, first_frame_s=times[0], rest_avg_s=round(sum(times[1:]) / max(1, len(times) - 1), 3), total_render_s=round(sum(times), 2),
               avg_s_per_frame=round(sum(times) / len(times), 3), gpu=gpu_info(), preset=preset, place=place, metal_slots_kept=n_metal, holdout_slots=n_hold,
               metal_materials=sorted(metal_names), set_materials=K["materials"], dof_in_blender=False)
    json.dump(rep, open(os.path.join(out, "layer_timing.json"), "w"), indent=1); print("LAYER_DONE", json.dumps({k: rep[k] for k in ("avg_s_per_frame", "first_frame_s", "total_render_s")}))
else:
    r.film_transparent = False
    sc.view_settings.view_transform = "Standard"
    if sc.world and getattr(sc.world, "node_tree", None):
        for n in sc.world.node_tree.nodes:
            if n.bl_idname == "ShaderNodeBackground": n.inputs[1].default_value = 0.0
    cache = {}
    def flat(key):
        if key in cache: return cache[key]
        c = [(int(hashlib.md5((key + s).encode()).hexdigest()[:2], 16) / 255) for s in "rgb"]
        m = bpy.data.materials.new("A_" + key); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
        e = nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value = (c[0], c[1], c[2], 1); e.inputs[1].default_value = 1.0
        o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o.inputs[0]); cache[key] = m; return m
    for ob in objs:
        for s in ob.material_slots: s.material = flat(ob.data.name)
    for who, cd in K["cards"].items():
        for n in cd["material"].node_tree.nodes:
            if n.bl_idname == "ShaderNodeMixShader" and n.inputs[1].is_linked and n.inputs[1].links[0].from_node.bl_idname == "ShaderNodeBsdfPrincipled": n.inputs[0].default_value = 1.0   # all emission: the drawing, unlit
    fm = (f0 + f1) // 2; sc.frame_set(fm); bpy.context.view_layer.update(); r.filepath = os.path.join(out, "align_%05d.png" % fm)
    t = time.perf_counter(); bpy.ops.render.render(write_still=True); dt = round(time.perf_counter() - t, 3)
    pos = list(cam.matrix_world.translation); bk = [c for c in json.load(open(os.path.join(ep, "out", "plan", "camera_baked.json")))["frames"] if c["f"] == fm][0]
    rep = dict(frame=fm, render_s=dt, blender_fov_v_deg=round(math.degrees(cam.data.angle_y), 4), baked_fov_v_deg=bk["fov_v"], blender_pos=[round(v, 4) for v in pos], baked_pos=bk["pos"],
               sensor_fit=cam.data.sensor_fit, sensor_h=cam.data.sensor_height, lens_mm=round(cam.data.lens, 4), res=[r.resolution_x, r.resolution_y], aspect=round(r.resolution_x / r.resolution_y, 5),
               aspect_baked=round(W / H, 5), cards=list(K["cards"].keys()))
    json.dump(rep, open(os.path.join(out, "align_camera.json"), "w"), indent=1); print("ALIGN_DONE", json.dumps(rep))
