"""fulltest/blender_full.py -- GLUE, runs INSIDE Blender (background):
  blender -b --factory-startup --python-exit-code 1 --gpu-backend opengl -P fulltest/blender_full.py -- \
      --repo <repo> --lock <out>/lock --script fulltest/script_passA.json --out <out> --mode stills|preview [--shots 1,4] [--stride N] [--res-pct N] [--samples N]
Builds the street (street_kit.py, Ricks look code), the two cards (EXISTING blender_look.from_lock.card()), one camera framed per shot by
a small deterministic fitter, bullet / tumbleweed props, a contact shadow per character, then renders stills (one per shot, a cheap check)
or the low-cost preview. Failures start with FULL_ERROR. Decoration steps that fail are listed in report 'warnings' and the run goes on."""
import bpy, sys, os, json, time, math, argparse, statistics, traceback
from mathutils import Vector

def die(m): print("FULL_ERROR " + m, flush=True); sys.exit(1)
def parse():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser(); p.add_argument("--repo", required=True); p.add_argument("--lock", required=True); p.add_argument("--script", required=True); p.add_argument("--out", required=True)
    p.add_argument("--mode", choices=["stills", "preview"], default="stills"); p.add_argument("--shots", default=""); p.add_argument("--stride", type=int, default=0); p.add_argument("--res-pct", type=int, default=0); p.add_argument("--samples", type=int, default=0)
    p.add_argument("--allow-software", action="store_true"); return p.parse_args(a)
def gl_info():
    try:
        import gpu; return {"vendor": gpu.platform.vendor_get(), "renderer": gpu.platform.renderer_get(), "version": gpu.platform.version_get(), "device_type": gpu.platform.device_type_get()}
    except Exception as e: return {"error": repr(e)}
def gl_verdict(g):
    t = (str(g.get("renderer", "")) + str(g.get("vendor", ""))).lower()
    return "SOFTWARE" if any(k in t for k in ("llvmpipe", "softpipe", "swrast", "software")) else ("NVIDIA_GPU" if "nvidia" in t else "GPU_OTHER" if t else "UNKNOWN")

def fit_camera(spec, shot_chars, cast, vfov_of):
    """returns (pos0, aim0, pos1, aim1, lens). Target mode frames a character by visible_frac / center_frac of its height; pos/aim mode is explicit."""
    lens = float(spec.get("lens", 30)); vfov = vfov_of(lens); push = float(spec.get("push", 0)); dz = float(spec.get("aim_dz", 0))
    adx = float(spec.get("aim_dx", 0))
    if "target" in spec:
        c = next((x for x in shot_chars if x["id"] == spec["target"]), None)
        if c is None: die("camera target '%s' is not in this shot's chars" % spec["target"])
        H = cast[c["id"]].get("height_m", 1.8); base = Vector((c["pos"][0], c["pos"][1], 0.0))
        A0 = base + Vector((0, 0, spec.get("center_frac", .6) * H)) + Vector((math.cos(math.radians(spec.get("az", 0))), math.sin(math.radians(spec.get("az", 0))), 0)) * adx; V = spec.get("visible_frac", .8) * H; d0 = V / (2 * math.tan(vfov / 2))
        az, el = math.radians(spec.get("az", 0)), math.radians(spec.get("el", 0))
        dirv = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
        A1 = A0 + Vector((0, 0, dz * H)); d1 = d0 * (1 - push)
        return A0 + dirv * d0, A0, A1 + dirv * d1, A1, lens
    if "pos" in spec and "aim" in spec:
        p, a = Vector(spec["pos"]), Vector(spec["aim"]); f = (a - p).normalized()
        return p, a, p + f * push, a + Vector((0, 0, dz)), lens
    die("camera spec needs 'target' or both 'pos' and 'aim': %s" % json.dumps(spec))

def look_euler(pos, aim, prev=None):
    q = (aim - pos).to_track_quat("-Z", "Y"); return q.to_euler("XYZ", prev) if prev is not None else q.to_euler("XYZ")

def main():
    A = parse(); S = json.load(open(A.script)); FPS = S.get("fps", 30); RS = S.get("render", {}); cast = S["cast"]; shots = S["shots"]
    stride = A.stride or RS.get("frame_stride", 2); res_pct = A.res_pct or RS.get("preview_res_pct", 50); samples = A.samples or (RS.get("still_samples", 24) if A.mode == "stills" else RS.get("preview_samples", 16))
    os.makedirs(A.out, exist_ok=True); R = {"blender": bpy.app.version_string, "mode": A.mode, "warnings": [], "script": S.get("name")}
    sys.path.insert(0, os.path.join(A.repo, "templates")); sys.path.insert(0, os.path.join(A.repo, "fulltest"))
    try:
        from blender_look import look as LOOK, materials as M, render as RN, from_lock as FL, scatter as SC
        import street_kit
    except Exception as e: die("cannot import the Ricks blender_look modules / street_kit: %r" % (e,))
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    # frame table
    n = [round(s["sec"] * FPS) for s in shots]; starts = []; a = 1
    for k in n: starts.append(a); a += k
    total = a - 1; R["frames"] = total

    # 1. look (existing Ricks preset 'day'), then our resolution
    sd = RS.get("sun_dir", [.5, -.3, .8]); LOOK.apply_look(sc, "day", key_dir=tuple(sd), samples=samples, res=100)
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 720, 1280, res_pct; sc.render.fps = FPS
    try: sc.render.use_motion_blur = False
    except Exception: pass
    sc.eevee.taa_render_samples = samples; sc.frame_start, sc.frame_end = 1, total

    # 2. camera object (no DOF at preview cost)
    cd = bpy.data.cameras.new("Cam"); cd.sensor_fit = "VERTICAL"; cd.sensor_height = 24; cd.clip_start = .05; cd.clip_end = 5000; cd.dof.use_dof = False
    cam = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(cam); sc.camera = cam
    vfov_of = lambda lens: 2 * math.atan(12.0 / lens)

    # 2b. characters placed by screen position (pos/aim shots): {"screen": [sx -1..1, depth m]} -> world position in front of that shot's camera
    for sh in shots:
        for c in sh.get("chars", []):
            if "screen" in c:
                cs = sh["cam"]
                if "pos" not in cs: die("shot %s: a char 'screen' placement needs the shot camera in pos/aim mode" % sh["id"])
                p, aim = Vector(cs["pos"]), Vector(cs["aim"]); fwd = Vector((aim.x - p.x, aim.y - p.y, 0)).normalized(); right = Vector((fwd.y, -fwd.x, 0)); sx, dp = c["screen"]
                tvh = 12.0 / float(cs.get("lens", 30)) * 720 / 1280; w = p + fwd * dp + right * (sx * dp * tvh); c["pos"] = [w.x, w.y]
    # 3. street (keep grass off the places characters stand)
    stands = [(c["pos"][0], c["pos"][1], 1.0) for s in shots for c in s.get("chars", [])]
    st = street_kit.build(sc, S.get("street", {}), keep_clear=stands, log=lambda m: print(m, flush=True)); R["street"] = st
    R["warnings"] += ["street: " + e for e in st["errors"]]
    if "ground" not in st["parts"]: die("the street ground failed to build, see STREET_STEP_FAILED above")

    # 4. cards: scale from the index, pos + flip per shot, then the EXISTING from_lock.card()
    cards = {}
    for who, cdef in cast.items():
        ip = os.path.join(A.lock, "cards", who, "index.json")
        if not os.path.isfile(ip): continue
        I = json.load(open(ip))
        for r in I["runs"]:
            if r.get("visible", True):
                sh = shots[r["shot"] - 1]; c = next(x for x in sh["chars"] if x["id"] == who); r["pos"] = [c["pos"][0], c["pos"][1], 0.0]; r["flip"] = bool(c.get("flip", False))
        json.dump(I, open(ip, "w"))
        try: cards[who] = FL.card(sc, A.lock, who, cam, self_lit=.5, emit=1.0)
        except Exception: print(traceback.format_exc()); die("from_lock.card() failed for '%s'" % who)
    R["cards"] = {w: {"object": k["object"].name, "metres_per_px": k["index"]["metres_per_px"], "px": k["index"]["px"]} for w, k in cards.items()}

    # 5. contact shadows (one blob per character per shot, visible only in that shot)
    def blob_mat():
        m = bpy.data.materials.new("ContactShadow"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); L = nt.links.new
        tc = nt.nodes.new("ShaderNodeTexCoord"); sub = nt.nodes.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = (.5, .5, 0); ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0; mr.inputs[2].default_value = .5; mr.inputs[3].default_value = 1; mr.inputs[4].default_value = 0
        sq = nt.nodes.new("ShaderNodeMath"); sq.operation = "POWER"; sq.inputs[1].default_value = 2; ml = nt.nodes.new("ShaderNodeMath"); ml.operation = "MULTIPLY"; ml.inputs[1].default_value = .6
        tr = nt.nodes.new("ShaderNodeBsdfTransparent"); em = nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (0, 0, 0, 1); mix = nt.nodes.new("ShaderNodeMixShader"); out = nt.nodes.new("ShaderNodeOutputMaterial")
        L(tc.outputs["UV"], sub.inputs[0]); L(sub.outputs[0], ln.inputs[0]); L(ln.outputs["Value"], mr.inputs[0]); L(mr.outputs[0], sq.inputs[0]); L(sq.outputs[0], ml.inputs[0]); L(ml.outputs[0], mix.inputs[0]); L(tr.outputs[0], mix.inputs[1]); L(em.outputs[0], mix.inputs[2]); L(mix.outputs[0], out.inputs[0])
        try: m.surface_render_method = "DITHERED"
        except Exception: m.blend_method = "HASHED"
        return m
    try:
        bm_ = blob_mat()
        for si, sh in enumerate(shots):
            for c in sh.get("chars", []):
                w, dpt = .85 * cast[c["id"]].get("height_m", 1.8) / 1.8, .38
                me = bpy.data.meshes.new("CS"); me.from_pydata([(-w/2, -dpt/2, 0), (w/2, -dpt/2, 0), (w/2, dpt/2, 0), (-w/2, dpt/2, 0)], [], [(0, 1, 2, 3)]); uv = me.uv_layers.new()
                for l, p in zip(me.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]): uv.data[l.index].uv = p
                me.materials.append(bm_); ob = bpy.data.objects.new("CS_%s_%d" % (c["id"], sh["id"]), me); sc.collection.objects.link(ob); ob.location = (c["pos"][0], c["pos"][1], .006); ob.visible_shadow = False
                f0, f1 = starts[si], starts[si] + n[si] - 1
                ob.hide_render = True; ob.keyframe_insert("hide_render", frame=1); ob.hide_render = False; ob.keyframe_insert("hide_render", frame=f0); ob.hide_render = True; ob.keyframe_insert("hide_render", frame=f1 + 1)
                if ob.animation_data and ob.animation_data.action:
                    for fc in FL._fcurves(ob.animation_data.action):
                        for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
    except Exception as e: print(traceback.format_exc()); R["warnings"].append("contact shadows failed: %r" % (e,))

    # 6. one camera, framed per shot, hard cuts (CONSTANT between shots, LINEAR within)
    cam_report = []; prev_eul = None; shot_frames = {}
    for si, sh in enumerate(shots):
        f0, f1 = starts[si], starts[si] + n[si] - 1; shot_frames[sh["id"]] = (f0, f1)
        p0, a0, p1, a1, lens = fit_camera(sh["cam"], sh.get("chars", []), cast, vfov_of)
        e0 = look_euler(p0, a0, prev_eul); e1 = look_euler(p1, a1, e0); prev_eul = e1
        for f, p, e in ((f0, p0, e0), (f1, p1, e1)):
            cam.location = p; cam.rotation_euler = e; cd.lens = lens; cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f); cd.keyframe_insert("lens", frame=f)
        cam_report.append({"shot": sh["id"], "frames": [f0, f1], "pos0": [round(x, 2) for x in p0], "aim0": [round(x, 2) for x in a0], "lens": lens})
    for ad in (cam.animation_data, cd.animation_data):
        if ad and ad.action:
            for fc in FL._fcurves(ad.action):
                kps = sorted(fc.keyframe_points, key=lambda k: k.co[0])
                for k in kps: k.interpolation = "LINEAR"
                ends = {v[1] for v in shot_frames.values()}
                for k in kps:
                    if int(k.co[0]) in ends: k.interpolation = "CONSTANT"
    R["camera"] = cam_report

    # 7. props: bullet and tumbleweed (simple meshes, keyframed in the shot)
    def fx_objects():
        for si, sh in enumerate(shots):
            f0, f1 = starts[si], starts[si] + n[si] - 1
            for fx in sh.get("fx", []):
                def pt(key):
                    if key in fx: return Vector(fx[key])
                    sk = key + "_screen"
                    if sk in fx:   # screen space: (x -1..1, y -1..1 of the half frame, depth m) so a prop is visible whatever the lens is
                        sx, sy, dp = fx[sk]; lens_ = float(sh["cam"].get("lens", 30)); tv = 12.0 / lens_; sc.frame_set(f0); bpy.context.view_layer.update(); return cam.matrix_world @ Vector((sx * dp * tv * 720 / 1280, sy * dp * tv, -dp))
                    ck = key + "_cam"
                    if ck in fx:   # camera-space (right, up, forward) at the shot's start
                        r, u, fwd = fx[ck]; sc.frame_set(f0); bpy.context.view_layer.update(); mw = cam.matrix_world; return mw @ Vector((r, u, -fwd))
                    die("fx %s needs '%s' or '%s_cam'" % (fx.get("type"), key, key))
                pa, pb = pt("from"), pt("to"); d = (pb - pa); fs_ = float(fx.get("scale", 1.0))
                if fx["type"] == "bullet":
                    mb = SC.MB("Bullet", [M.get("matte", color=(226, 138, 66), rough=.35), M.get("matte", color=(255, 190, 90), rough=.4)]); mb.cyl((0, 0, 0), .05, .2, 0, 12, rot=(0, 0, 0)); mb.cyl((0, 0, .15), .05, .1, 0, 12, r2=.006); me = mb.mesh()
                    mo = SC.MB("Streak", [M.get("matte", color=(255, 190, 90), rough=.4)]); mo.cyl((0, 0, -.9), .045, 1.6, 0, 10, r2=.003, rot=(math.pi, 0, 0)); sm = mo.mesh()
                    for mesh_, nm in ((me, "Bullet"), (sm, "Streak")):
                        ob = bpy.data.objects.new(nm, mesh_); sc.collection.objects.link(ob); ob.rotation_euler = d.normalized().to_track_quat("Z", "Y").to_euler()
                        ob.scale = (fs_, fs_, fs_); ob.location = pa; ob.keyframe_insert("location", frame=f0); ob.location = pb; ob.keyframe_insert("location", frame=f1)
                        ob.hide_render = True; ob.keyframe_insert("hide_render", frame=1); ob.hide_render = False; ob.keyframe_insert("hide_render", frame=f0); ob.hide_render = True; ob.keyframe_insert("hide_render", frame=f1 + 1)
                        for fc in FL._fcurves(ob.animation_data.action):
                            for kp in fc.keyframe_points: kp.interpolation = "CONSTANT" if "hide" in fc.data_path else "LINEAR"
                elif fx["type"] == "tumbleweed":
                    mb = SC.MB("Tumbleweed", [M.get("bark", color=(170, 130, 74))])
                    for i, (dx, dy, dz, s) in enumerate([(0, 0, 0, .35), (.12, .05, .08, .3), (-.1, .0, .12, .3), (.0, -.1, -.08, .28), (.08, .1, -.1, .26)]): mb.ico((dx, dy, dz), s, 0, 2, (1, 1, 1))
                    ob = bpy.data.objects.new("Tumbleweed", mb.mesh()); sc.collection.objects.link(ob)
                    ob.location = pa; ob.keyframe_insert("location", frame=f0); ob.location = pb; ob.keyframe_insert("location", frame=f1)
                    ob.rotation_euler = (0, 0, 0); ob.keyframe_insert("rotation_euler", frame=f0); ob.rotation_euler = (0, -6.28 * 3 * (1 if d.x > 0 else -1), 0); ob.keyframe_insert("rotation_euler", frame=f1)
                    ob.hide_render = True; ob.keyframe_insert("hide_render", frame=1); ob.hide_render = False; ob.keyframe_insert("hide_render", frame=f0); ob.hide_render = True; ob.keyframe_insert("hide_render", frame=f1 + 1)
                    for fc in FL._fcurves(ob.animation_data.action):
                        for kp in fc.keyframe_points: kp.interpolation = "CONSTANT" if "hide" in fc.data_path else "LINEAR"
                else: R["warnings"].append("unknown fx type %s" % fx.get("type"))
    try: fx_objects()
    except SystemExit: raise
    except Exception as e: print(traceback.format_exc()); R["warnings"].append("fx failed: %r" % (e,))

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(A.out, "fulltest_scene.blend"), copy=True)
    want = {int(x) for x in A.shots.split(",") if x.strip()} if A.shots else {s["id"] for s in shots}
    rows = []; T = {}
    def pre(scene, *a): T["t"] = time.perf_counter(); T["f"] = scene.frame_current
    def post(scene, *a):
        rows.append({"frame": T["f"], "seconds": round(time.perf_counter() - T["t"], 3)}); print("FRAME", T["f"], rows[-1]["seconds"], flush=True)
        if len(rows) == 1:
            g = gl_info(); R["gl"] = g; R["gl_verdict"] = gl_verdict(g); print("GL_INFO", json.dumps(g), flush=True)
            if R["gl_verdict"] == "SOFTWARE" and not A.allow_software: print("FULL_ERROR software rendering (no GPU), aborting", flush=True); os._exit(2)
    bpy.app.handlers.render_pre.append(pre); bpy.app.handlers.render_post.append(post)
    sc.render.image_settings.file_format = "PNG"; sc.render.use_file_extension = True
    if A.mode == "stills":
        d = os.path.join(A.out, "stills"); os.makedirs(d, exist_ok=True)
        for sh in shots:
            if sh["id"] not in want: continue
            f0, f1 = shot_frames[sh["id"]]; f = f0 + (f1 - f0) // 2; sc.frame_set(f); sc.render.filepath = os.path.join(d, "shot_%02d" % sh["id"]); bpy.ops.render.render(write_still=True)
        R["stills"] = sorted(os.listdir(d))
    else:
        fdir = os.path.join(A.out, "frames"); os.makedirs(fdir, exist_ok=True); sc.frame_step = stride; sc.render.filepath = os.path.join(fdir, "f_####")
        t0 = time.perf_counter(); bpy.ops.render.render(animation=True); R["wall_s"] = round(time.perf_counter() - t0, 1); R["frames_on_disk"] = len([f for f in os.listdir(fdir) if f.endswith(".png")])
    ts = [r["seconds"] for r in rows]; rest = ts[1:] or ts
    R["timing"] = {"frames_rendered": len(rows), "first_s": ts[0] if ts else None, "mean_excl_first_s": round(statistics.mean(rest), 3) if rest else None, "max_s": max(ts) if ts else None, "per_frame": rows,
                   "preview": {"res_pct": res_pct, "px": [720 * res_pct // 100, 1280 * res_pct // 100], "samples": samples, "stride": stride}}
    json.dump(R, open(os.path.join(A.out, "full_report_%s.json" % A.mode), "w"), indent=1, default=str)
    print("FULL_REPORT " + json.dumps({k: v for k, v in R.items() if k not in ("timing", "street")} | {"street": {"parts": R["street"]["parts"], "errors": R["street"]["errors"]}} | {"timing": {k: v for k, v in R["timing"].items() if k != "per_frame"}}, default=str))

try: main()
except SystemExit: raise
except Exception: traceback.print_exc(); print("FULL_ERROR unexpected exception (traceback above)", flush=True); sys.exit(1)
