"""slice01/blender_slice.py  --  GLUE ONLY, runs INSIDE Blender (background):

    blender -b --factory-startup --python-exit-code 1 -P slice01/blender_slice.py -- \
        --repo <repo root> --blend <casino_eevee.blend> --lock <out>/lock --out <out> --config slice01/config.json

What it does, in order (every step fails loudly with a line starting SLICE_ERROR):
 1. opens the casino .blend (never saves over it)
 2. freezes the casino camera at one frame (the casino's own camera, lens and focus; its animation is removed)
 3. finds the casino's 3D test character by its material names, measures it, hides it for render
 4. writes the real card scale and position into <lock>/cards/hero/index.json
 5. builds the card with the EXISTING blender_look.from_lock.card() (PNG sequence on a camera-facing plane,
    lit Principled + Emission 0.5, alpha through Transparent)
 6. sets a LOW-COST preview (resolution %, samples, frame stride, Freestyle off), saves a copy of the prepared scene
 7. renders the frame range with per-frame timing, checks the GPU is not software, writes slice_report.json
It does NOT touch the casino's lights, materials or world. No final-quality render is possible from here.
"""
import bpy, sys, os, json, time, argparse, statistics, hashlib, traceback
from mathutils import Vector

def die(msg):
    print("SLICE_ERROR " + msg, flush=True); sys.exit(1)

def parse():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    for k in ("--repo", "--blend", "--lock", "--out", "--config"): ap.add_argument(k, required=True)
    ap.add_argument("--stride", type=int, default=0); ap.add_argument("--res-pct", type=int, default=0); ap.add_argument("--samples", type=int, default=0)
    ap.add_argument("--allow-software", action="store_true"); ap.add_argument("--resume", action="store_true"); ap.add_argument("--no-render", action="store_true")
    return ap.parse_args(a)

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    return h.hexdigest()

def gl_info():
    import gpu
    p = gpu.platform; d = {"vendor": p.vendor_get(), "renderer": p.renderer_get(), "version": p.version_get()}
    try: d["device_type"] = p.device_type_get()
    except Exception as e: d["device_type"] = "unavailable: %r" % (e,)
    return d

def gl_verdict(d):
    t = (str(d.get("vendor")) + " " + str(d.get("renderer"))).lower()
    if any(k in t for k in ("llvmpipe", "softpipe", "swrast", "lavapipe", "software", "mesa")) or str(d.get("device_type")).upper() == "SOFTWARE": return "SOFTWARE"
    return "NVIDIA_GPU" if "nvidia" in t else "OTHER_GPU"

def bbox_world(objs, dg):
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in objs:
        eo = o.evaluated_get(dg); mw = eo.matrix_world
        for c in eo.bound_box:
            v = mw @ Vector(c); lo = Vector(map(min, lo, v)); hi = Vector(map(max, hi, v))
    return lo, hi

def mat_base(name): return name.split(".")[0]

def main():
    A = parse(); cfg = json.load(open(A.config)); B = cfg.get("blender", {})
    stride = A.stride or B.get("frame_stride", 2); res_pct = A.res_pct or B.get("preview_res_pct", 50); samples = A.samples or B.get("preview_samples", 16)
    if not os.path.isfile(A.blend): die("casino blend not found: %s" % A.blend)
    idx_path = os.path.join(A.lock, "cards", "hero", "index.json")
    if not os.path.isfile(idx_path): die("card index not found: %s (run make_cards.mjs first)" % idx_path)
    h0 = sha(A.blend); os.makedirs(A.out, exist_ok=True); R = {"blender": bpy.app.version_string, "blend_sha256": h0, "warnings": []}

    # 1. open
    bpy.ops.wm.open_mainfile(filepath=A.blend, load_ui=False); sc = bpy.context.scene
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    eev = [e for e in engines if "EEVEE" in e.upper()]
    if not eev: die("no EEVEE engine in this Blender build: %s" % engines)
    sc.render.engine = ([e for e in eev if "NEXT" in e.upper()] or sorted(eev))[0]
    R["engine"] = sc.render.engine; R["scene"] = {"name": sc.name, "frames": [sc.frame_start, sc.frame_end], "res": [sc.render.resolution_x, sc.render.resolution_y], "fps": sc.render.fps}

    # 2. camera: the casino's own, frozen at one frame
    cam = bpy.data.objects.get(B["camera_name"]) if B.get("camera_name") else sc.camera
    if cam is None or cam.type != "CAMERA": die("no camera found (set blender.camera_name in the config). Cameras in file: %s" % [o.name for o in bpy.data.objects if o.type == "CAMERA"])
    cf = int(B.get("camera_frame", 75)); lo_f, hi_f = sc.frame_start, sc.frame_end
    if not lo_f <= cf <= hi_f: R["warnings"].append("camera_frame %d outside %d..%d, clamped" % (cf, lo_f, hi_f)); cf = min(max(cf, lo_f), hi_f)
    sc.frame_set(cf); bpy.context.view_layer.update(); mw_cam = cam.matrix_world.copy()

    # 3. the casino's own 3D test character: find by material, measure, hide (the preview uses the 2D card instead)
    mats = set(B.get("character_materials", []))
    chars = [o for o in sc.objects if o.type in {"MESH", "CURVE", "SURFACE", "META", "FONT"} and any(s.material and mat_base(s.material.name) in mats for s in o.material_slots)]
    if not chars:
        have = sorted({mat_base(s.material.name) for o in sc.objects for s in o.material_slots if s.material})
        die("no object uses the character materials %s. Materials in this file: %s. Edit blender.character_materials in the config." % (sorted(mats), have))
    rigs = {m.object for o in chars for m in o.modifiers if m.type == "ARMATURE" and m.object}
    dg = bpy.context.evaluated_depsgraph_get(); lo, hi = bbox_world(chars, dg)
    floor_z = lo.z; fm = B.get("floor_material")
    if fm:
        fl = [o for o in sc.objects if o.type == "MESH" and any(s.material and mat_base(s.material.name) == fm for s in o.material_slots)]
        if fl:
            z = bbox_world(fl, dg)[1].z
            if lo.z - 0.6 <= z <= lo.z + 0.6: floor_z = z
            else: R["warnings"].append("floor material '%s' top z=%.3f is far from character min z=%.3f; using the character's min z" % (fm, z, lo.z))
        else: R["warnings"].append("floor material '%s' not found; using the character's min z" % fm)
    height_m = (hi.z - floor_z) * float(B.get("height_factor", 1.0))
    if not 0.2 <= height_m <= 6: die("character height %.3f m is implausible (bbox z %.3f..%.3f). Check scene units / character_materials." % (height_m, lo.z, hi.z))
    ox, oy, oz = B.get("offset", [0, 0, 0]); cx, cy, cz = (lo.x + hi.x) / 2 + ox, (lo.y + hi.y) / 2 + oy, floor_z + oz
    R["casino_character"] = {"objects": len(chars), "names": sorted(o.name for o in chars)[:25], "armatures": sorted(o.name for o in rigs), "bbox_min": list(lo), "bbox_max": list(hi), "floor_z": floor_z, "height_m": height_m, "card_feet": [cx, cy, cz]}

    # freeze the camera (the card is the subject, so focus on it), hide the casino character
    for idb in (cam, cam.data):
        if idb.animation_data: idb.animation_data_clear()
    for c in list(cam.constraints): cam.constraints.remove(c)
    cam.parent = None; cam.matrix_world = mw_cam
    d = cam.data; d.dof.focus_object = None; d.dof.focus_distance = max(0.3, (Vector((cx, cy, cz + height_m * 0.6)) - mw_cam.translation).length)
    for o in list(chars) + list(rigs): o.hide_render = True; o.hide_viewport = True
    R["camera"] = {"name": cam.name, "frozen_at_frame": cf, "location": list(mw_cam.translation), "lens_mm": d.lens, "dof": d.dof.use_dof, "focus_distance": d.dof.focus_distance}

    # 4. real scale + position into the card index (from_lock.card reads these)
    I = json.load(open(idx_path)); k = height_m / I["figure_px"]; I["metres_per_px"] = k; I["height_m"] = height_m
    for r in I["runs"]: r["pos"] = [cx, cy, cz]
    json.dump(I, open(idx_path, "w")); nframes = max(r["f1"] for r in I["runs"])
    n_png = len([f for f in os.listdir(os.path.dirname(idx_path)) if f.startswith("s") and f.endswith(".png")])
    if n_png != I["images"]: die("card index says %d drawings but %d PNGs exist" % (I["images"], n_png))

    # 5. the card, with the EXISTING Ricks code
    sys.path.insert(0, os.path.join(A.repo, "templates"))
    try: from blender_look import from_lock as FL
    except Exception as e: die("cannot import templates/blender_look/from_lock.py: %r" % (e,))
    try: K = FL.card(sc, A.lock, "hero", cam, self_lit=float(B.get("self_lit", .5)), emit=float(B.get("emit", 1.0)))
    except Exception: print(traceback.format_exc()); die("from_lock.card() failed (traceback above)")
    R["card"] = {"object": K["object"].name, "metres_per_px": k, "card_px": I["px"], "frames": nframes, "drawings": I["images"], "runs": len(I["runs"])}

    # 6. low-cost preview settings (casino lights, materials and world are untouched)
    sc.frame_start, sc.frame_end, sc.frame_step = 1, nframes, stride; sc.render.fps = cfg.get("fps", 30)
    sc.render.resolution_percentage = res_pct; sc.render.use_freestyle = False
    try: sc.render.use_motion_blur = False
    except Exception: pass
    try: sc.eevee.taa_render_samples = samples
    except Exception as e: R["warnings"].append("could not set samples: %r" % (e,))
    fdir = os.path.join(A.out, "frames"); os.makedirs(fdir, exist_ok=True)
    sc.render.image_settings.file_format = "PNG"; sc.render.use_file_extension = True; sc.render.filepath = os.path.join(fdir, "f_####")
    sc.render.use_overwrite = not A.resume; sc.render.use_placeholder = A.resume
    R["preview"] = {"res_pct": res_pct, "px": [sc.render.resolution_x * res_pct // 100, sc.render.resolution_y * res_pct // 100], "samples": samples, "stride": stride, "frames_planned": len(range(1, nframes + 1, stride)), "output_fps": sc.render.fps / stride}
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(A.out, "slice01_scene.blend"), copy=True)
    if A.no_render:
        R["no_render"] = True; json.dump(R, open(os.path.join(A.out, "slice_report.json"), "w"), indent=1, default=str); print("SLICE_REPORT " + json.dumps(R, default=str)); return

    # 7. render with timing
    T, rows = {}, []
    def pre(scene, *a): T["t"] = time.perf_counter(); T["f"] = scene.frame_current
    def post(scene, *a):
        rows.append({"frame": T["f"], "seconds": round(time.perf_counter() - T["t"], 3)}); print("FRAME", T["f"], rows[-1]["seconds"], flush=True)
        if len(rows) == 1:
            g = gl_info(); R["gl"] = g; R["gl_verdict"] = gl_verdict(g); print("GL_INFO", json.dumps(g), flush=True)
            if R["gl_verdict"] == "SOFTWARE" and not A.allow_software:
                print("SLICE_ERROR software rendering (no GPU). Timing would be meaningless. Aborting; use --allow-software to override.", flush=True); os._exit(2)
    bpy.app.handlers.render_pre.append(pre); bpy.app.handlers.render_post.append(post)
    t0 = time.perf_counter(); bpy.ops.render.render(animation=True); wall = time.perf_counter() - t0
    ts = [r["seconds"] for r in rows]; rest = ts[1:] or ts; srt = sorted(ts)
    have = sorted(f for f in os.listdir(fdir) if f.startswith("f_") and f.endswith(".png"))
    R["timing"] = {"frames_rendered": len(rows), "wall_s": round(wall, 2), "first_frame_s": ts[0] if ts else None, "mean_excl_first_s": round(statistics.mean(rest), 3) if rest else None,
                   "median_s": round(statistics.median(ts), 3) if ts else None, "p90_s": srt[min(len(srt) - 1, int(.9 * len(srt)))] if srt else None, "max_s": max(ts) if ts else None, "per_frame": rows}
    R["frames_on_disk"] = len(have); R["casino_blend_unchanged"] = sha(A.blend) == h0
    json.dump(R, open(os.path.join(A.out, "slice_report.json"), "w"), indent=1, default=str); print("SLICE_REPORT " + json.dumps({k: v for k, v in R.items() if k != "timing"} | {"timing": {k: v for k, v in R["timing"].items() if k != "per_frame"}}, default=str))

try: main()
except SystemExit: raise
except Exception:
    traceback.print_exc(); print("SLICE_ERROR unexpected exception (traceback above)", flush=True); sys.exit(1)
