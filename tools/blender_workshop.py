#!/usr/bin/env python3
"""R4 Blender ASSET WORKSHOP (small, no engine). Blender makes/modifies assets, materials, anchors and exports GLB; it is not the film's set assembler (three.js is) and not the registry (assets.py is).
  blender_workshop.py plan <id>            reuse-first report: registry entry, requirement, existing GLB, builder state -> what to do (reuse | modify | procedural | custom)
  blender_workshop.py build <id> [--force] [--registry FILE] [--out DIR]
        locate the registry entry's bpy_builder -> run it in headless Blender (bpy) -> export a DETERMINISTIC GLB (Y up, applied transforms, extras) -> validate it against the registry requirement with tools/glb.py
        -> write library/assets/glb/<id>/<version>/<id>.glb (+ .contract.json) and print the JSON result. It never registers or approves (assets.py register-glb / approve-glb are explicit owner actions).
Order (R4C): reuse first (a valid GLB whose builder + blender version are unchanged is reused, no rebuild) -> modify an existing builder -> procedural builder -> custom."""
import hashlib, json, sys, time, subprocess, os
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT / "tools"))
import assets as A, glb as G
def entry(i, reg=None):
    for a in (json.load(open(reg))["assets"] if reg else A.load()):
        if a["name"] == i: return a
    raise SystemExit("asset %r is not in the registry (add its entry with a requirement first: assets.py require)" % i)
def builder_sha(e): return hashlib.sha1((ROOT / e["blender"]["file"]).read_bytes()).hexdigest()
def plan(i, reg=None):
    e = entry(i, reg); g = e.get("glb") or {}; f = ROOT / g["file"] if g.get("file") else None
    if not e.get("requirement"): return dict(id=i, action="custom", why="no requirement block: write it first (assets.py require)")
    if f and f.is_file() and g.get("builder_sha1") == builder_sha(e): return dict(id=i, action="reuse", why="GLB exists and its builder is unchanged", glb=g["file"], sha1=g.get("sha1"))
    if f and f.is_file(): return dict(id=i, action="modify", why="GLB exists but the builder changed since it was exported: rebuild (new version recommended)", glb=g["file"])
    if e["blender"].get("kind") == "bpy_builder": return dict(id=i, action="procedural", why="a builder exists, no GLB yet: build it")
    return dict(id=i, action="custom", why="no builder")
def _preview(png):
    import bpy, math, mathutils
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'; sc.render.resolution_x = 640; sc.render.resolution_y = 480
    cam = bpy.data.objects.new('prev_cam', bpy.data.cameras.new('prev_cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.location = (3.4, -3.0, 2.3)
    cam.rotation_euler = (mathutils.Vector((0, 0, 0.75)) - cam.location).to_track_quat('-Z', 'Y').to_euler(); sc.render.filepath = str(png); bpy.ops.render.render(write_still=True)
def build(i, force=False, reg=None, out=None, prev=None):
    e = entry(i, reg); p = plan(i, reg)
    if p["action"] == "reuse" and not force: return dict(p, reused=True)
    import bpy, importlib.util, tempfile
    b = e["blender"]; f = ROOT / b["file"]
    if not f.is_file(): raise SystemExit("builder file missing: %s" % b["file"])
    spec = importlib.util.spec_from_file_location("ws_" + i, f); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    t0 = time.perf_counter(); bpy.ops.wm.read_factory_settings(use_empty=True); getattr(m, b["entry"])(); t_build = time.perf_counter() - t0
    dst = Path(out) if out else ROOT / "library/assets/glb" / i / str(e["version"]); dst.mkdir(parents=True, exist_ok=True); path = dst / (i + ".glb")
    t1 = time.perf_counter()
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", export_yup=True, export_apply=True, export_extras=True, export_cameras=False, export_lights=False, export_animations=False, export_image_format="NONE")
    t_export = time.perf_counter() - t1
    if prev: _preview(prev)
    s = G.summarize(path); c = G.contract_of(path); (dst / (i + ".contract.json")).write_text(json.dumps(c, indent=1, sort_keys=True))
    probs = G.problems(path, e.get("requirement"))
    return dict(id=i, version=e["version"], action=p["action"], glb=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path), sha1=s["sha1"], bytes=s["bytes"], builder_sha1=builder_sha(e),
                blender_version=bpy.app.version_string, build_s=round(t_build, 3), export_s=round(t_export, 3), problems=probs, contract=c)
if __name__ == "__main__":
    a = sys.argv[1:]; reg = a[a.index("--registry") + 1] if "--registry" in a else None; out = a[a.index("--out") + 1] if "--out" in a else None; prev = a[a.index("--preview") + 1] if "--preview" in a else None
    if not a or a[0] not in ("plan", "build") or len(a) < 2: print(__doc__); sys.exit(2)
    r = plan(a[1], reg) if a[0] == "plan" else build(a[1], "--force" in a, reg, out, prev)
    print(json.dumps(r, indent=1)); sys.exit(1 if r.get("problems") else 0)
