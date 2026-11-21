"""PHASE 1C (= 1B with ONE change: reflection strength GAIN 0.5 on the key light and the sky): ONE Blender enhancement layer = specular/reflection of the clock post and rim ONLY, from the Ricks lock.
blender -b --factory-startup -P layer_reflect.py -- <repo> <episode_dir> <out_dir> <f0> <f1> <mode> <W> <H>
  mode layer  : reflection-only layer (RGBA). Hero = the four NAMED lock objects clock_post, clock_foot, clock_neck, clock_drum (lock_id 203-206),
                checked by name AND lock_id. Hero material: black base (no diffuse), dielectric specular only. Every other set slot and the character
                cards are Holdout (cards keep their drawing alpha). Light/sky come from the LOCK's per-place lights (the three.js sun direction, sun colour,
                sky top/horizon), so the reflection shows the same sky and sun as the base.
  mode idmask : the same geometry, hero = flat white emission: the INTENDED mask (alpha). One PNG per frame.
  mode align  : flat-emission picture of the whole set + cards (frame (f0+f1)//2) for the pixel-alignment check, as in Phase 1.
Ricks files are not modified. Blender DOF off (the base has its own post DOF).
"""
import bpy, sys, os, json, time, math, hashlib
A = sys.argv[sys.argv.index("--") + 1:]
repo, ep, out, f0, f1, mode, W, H = A[0], A[1], A[2], int(A[3]), int(A[4]), A[5], int(A[6]), int(A[7])
SAMPLES = int(os.environ.get("P1_SAMPLES", "64"))
GAIN = 0.5      # the only change vs Phase 1B: reflection strength. Phase 1B added +0.089 mean luminance at gain 1.0; the specular term is linear in light, so 0.5 is chosen to land near +0.045 (threshold +0.06), fixed before the run
sys.path.insert(0, os.path.join(repo, "templates"))
from blender_look import from_lock as FL, lights as LT
from mathutils import Vector
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
lock = json.load(open(os.path.join(ep, "out", "lock", "lock.json"), encoding="utf-8"))
place = lock["places"][0]["name"]; preset = lock["places"][0].get("light", "morning"); LL = lock["lights"][place]
HERO = {"clock_post": 203, "clock_foot": 204, "clock_neck": 205, "clock_drum": 206}      # names and lock_ids read from the lock's set glb (all painted_metal_chipped)

def gpu_info():
    try:
        import gpu; p = gpu.platform; return {"vendor": p.vendor_get(), "renderer": p.renderer_get(), "version": p.version_get(), "backend": str(p.backend_type_get())}
    except Exception as e: return {"error": repr(e)}
def lin(hexs): return tuple(((int(hexs[i:i + 2], 16) / 255) ** 2.2) for i in (1, 3, 5))

t_build = time.perf_counter()
K = FL.build(sc, ep, place=place, preset=preset, samples=SAMPLES, res=100, motion_blur=False)
build_s = time.perf_counter() - t_build
r = sc.render; r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100
r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGBA"; r.image_settings.color_depth = "8"; r.use_file_extension = False
cam = K["camera"]; cam.data.dof.use_dof = False
objs = [o for o in K["set"] if o.type == "MESH"]
base_name = lambda o: o.name.split(".")[0] if o.name.rsplit(".", 1)[-1].isdigit() else o.name

if mode in ("layer", "idmask"):
    # --- the lock's light and sky, not the preset's: the reflection must show what the three.js base lights with ---
    for o in list(bpy.data.objects):
        if o.type == "LIGHT" and o.name.startswith("Fill"): bpy.data.objects.remove(o, do_unlink=True)
    pos3 = LL["dir"]; toward = Vector((pos3[0], -pos3[2], pos3[1]))                    # three.js (x,y,z) -> plan/Blender (x,-z,y), as the lock's T2B
    for o in bpy.data.objects:
        if o.type == "LIGHT" and o.name.startswith("Key"):
            o.rotation_euler = toward.normalized().to_track_quat("Z", "Y").to_euler(); o.data.color = lin(LL["sun"]); o.data.energy *= GAIN
    LT.sky(sc, [(0, lin(LL["hor"])), (.65, lin(LL["top"]))], False, GAIN)
    r.film_transparent = True
    # --- hero by NAME and lock_id ---
    hero = [o for o in objs if base_name(o) in HERO]; found = sorted(base_name(o) for o in hero)
    assert found == sorted(HERO), "hero objects not found by name: %s" % found
    for o in hero:
        lid = o.get("lock_id"); assert lid is None or int(lid) == HERO[base_name(o)], "lock_id mismatch on %s: %s" % (o.name, lid)
    hm = bpy.data.materials.new("HOLD"); hm.use_nodes = True; nt = hm.node_tree; nt.nodes.clear(); h = nt.nodes.new("ShaderNodeHoldout"); o_ = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(h.outputs[0], o_.inputs[0])
    sm = bpy.data.materials.new("HERO_SPEC" if mode == "layer" else "HERO_ID"); sm.use_nodes = True; nt = sm.node_tree; nt.nodes.clear(); o_ = nt.nodes.new("ShaderNodeOutputMaterial")
    if mode == "layer":
        p = nt.nodes.new("ShaderNodeBsdfPrincipled"); I = p.inputs
        I["Base Color"].default_value = (0, 0, 0, 1); I["Metallic"].default_value = 0.0; I["Roughness"].default_value = 0.2; I["IOR"].default_value = 1.5
        for k in ("Specular IOR Level",): 
            if k in I: I[k].default_value = 0.5
        for k in ("Coat Weight", "Sheen Weight", "Emission Strength", "Subsurface Weight", "Transmission Weight"):
            if k in I: I[k].default_value = 0.0
        nt.links.new(p.outputs[0], o_.inputs[0])
    else:
        e = nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value = (1, 1, 1, 1); e.inputs[1].default_value = 1.0; nt.links.new(e.outputs[0], o_.inputs[0])
    hero_set = set(hero)
    for ob in objs:
        for s in ob.material_slots: s.material = sm if ob in hero_set else hm
    for who, cd in K["cards"].items():
        nt = cd["material"].node_tree; done = 0
        for n in list(nt.nodes):
            if n.bl_idname == "ShaderNodeMixShader" and n.inputs[1].is_linked and n.inputs[1].links[0].from_node.bl_idname == "ShaderNodeBsdfTransparent":
                hd = nt.nodes.new("ShaderNodeHoldout"); nt.links.new(hd.outputs[0], n.inputs[2]); done += 1
        assert done == 1, "card %s alpha mix not found" % who
    if mode == "idmask": sc.view_settings.view_transform = "Standard"; sc.eevee.taa_render_samples = 16
    times = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f); r.filepath = os.path.join(out, ("layer_%05d.png" if mode == "layer" else "idmask_%05d.png") % f)
        t = time.perf_counter(); bpy.ops.render.render(write_still=True); times.append(round(time.perf_counter() - t, 3)); print(mode.upper(), f, times[-1])
    rep = dict(blender=bpy.app.version_string, engine=sc.render.engine, samples=sc.eevee.taa_render_samples, resolution=[W, H], frames=[f0, f1], n_frames=len(times), build_s=round(build_s, 2), frame_s=times,
               cold_first_frame_s=times[0], steady_mean_s=round(sum(times[1:]) / max(1, len(times) - 1), 3), steady_max_s=max(times[1:]) if len(times) > 1 else None, total_render_s=round(sum(times), 2),
               gpu=gpu_info(), preset=preset, place=place, hero=sorted(HERO), hero_objects_found=[o.name for o in hero], lock_lights=LL, gain=GAIN, dof_in_blender=False)
    json.dump(rep, open(os.path.join(out, "%s_timing.json" % mode), "w"), indent=1); print("%s_DONE" % mode.upper(), json.dumps({k: rep[k] for k in ("cold_first_frame_s", "steady_mean_s", "total_render_s")}))
else:
    r.film_transparent = False; sc.view_settings.view_transform = "Standard"
    if sc.world and getattr(sc.world, "node_tree", None):
        for n in sc.world.node_tree.nodes:
            if n.bl_idname == "ShaderNodeBackground": n.inputs[1].default_value = 0.0
    cache = {}
    def flat(key):
        if key in cache: return cache[key]
        c = [(int(hashlib.md5((key + s).encode()).hexdigest()[:2], 16) / 255) for s in "rgb"]
        m = bpy.data.materials.new("A_" + key); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); e = nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value = (c[0], c[1], c[2], 1); e.inputs[1].default_value = 1.0
        o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o.inputs[0]); cache[key] = m; return m
    for ob in objs:
        for s in ob.material_slots: s.material = flat(ob.data.name)
    for who, cd in K["cards"].items():
        for n in cd["material"].node_tree.nodes:
            if n.bl_idname == "ShaderNodeMixShader" and n.inputs[1].is_linked and n.inputs[1].links[0].from_node.bl_idname == "ShaderNodeBsdfPrincipled": n.inputs[0].default_value = 1.0
    fm = (f0 + f1) // 2; sc.frame_set(fm); bpy.context.view_layer.update(); r.filepath = os.path.join(out, "align_%05d.png" % fm)
    t = time.perf_counter(); bpy.ops.render.render(write_still=True); dt = round(time.perf_counter() - t, 3)
    pos = list(cam.matrix_world.translation); bk = [c for c in json.load(open(os.path.join(ep, "out", "plan", "camera_baked.json")))["frames"] if c["f"] == fm][0]
    rep = dict(frame=fm, render_s=dt, blender_fov_v_deg=round(math.degrees(cam.data.angle_y), 4), baked_fov_v_deg=bk["fov_v"], blender_pos=[round(v, 4) for v in pos], baked_pos=bk["pos"], res=[r.resolution_x, r.resolution_y],
               aspect=round(r.resolution_x / r.resolution_y, 5), aspect_baked=round(1080 / 1920, 5), sensor_fit=cam.data.sensor_fit)
    json.dump(rep, open(os.path.join(out, "align_camera.json"), "w"), indent=1); print("ALIGN_DONE", json.dumps(rep))
