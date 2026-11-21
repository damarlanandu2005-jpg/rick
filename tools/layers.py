#!/usr/bin/env python3
"""Blender enhancement layers: hash-checked, cached, gated (hybrid Phase 3).
  layers.py status <ep>                       CPU: per layer, is out/layers/<id>/manifest.json fresh against its inputs?
  layers.py run <ep> <layer_id> --blender B [--gpu-backend opengl] [--res 720x1280]   one Blender process, composite onto the three.js stills, per-type gate
Inputs hashed (any change = stale, nothing silently reused): the layer spec (layers_baked.json entry), lock.json (carries the sha1 of camera/performance/flights and the lights),
the place glb, the Blender-side scripts, the resolution, and the base stills of the frame range. A layer is only composited if from_lock.read accepts the lock (camera/performance/flights unchanged).
Reuses phase1b/compose_1b.py for the composite and metrics (rule: base + layer_rgb x alpha in display space)."""
import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = [ROOT / "templates/blender_look/layer_render.py", ROOT / "templates/blender_look/from_lock.py", ROOT / "templates/blender_look/lights.py"]
# per-type gates = the Phase 1C thresholds, fixed in advance (A outside the named mask nothing changes, B brightness added, D time, E registration)
GATES = {"reflection": dict(A_outside_diff_max=0, B_mean_lum_added_max=0.06, D_steady_s_max=15.0, E_edge_shift_px_max=0.5, E_fov_diff_deg_max=0.01)}
def sha(p): return hashlib.sha1(open(p, "rb").read()).hexdigest()
def spec_of(ep, lid): return json.load(open(Path(ep) / "out/plan/layers_baked.json"))[lid]
def inputs_hash(ep, lid, W, H):
    ep = Path(ep); S = spec_of(ep, lid); f0, f1 = S["frames"]; h = hashlib.sha1(); h.update(json.dumps(S, sort_keys=True).encode()); h.update(("%dx%d" % (W, H)).encode())
    h.update(sha(ep / "out/lock/lock.json").encode()); h.update(sha(ep / "out/lock/sets" / (S["place"] + ".glb")).encode())
    for s in SCRIPTS: h.update(sha(s).encode())
    for f in range(f0, f1 + 1):
        p = ep / "out/stills" / ("f_%05d.png" % f)
        if p.exists(): h.update(sha(p).encode())
    return h.hexdigest()
def visible(ep, lid, min_hits=5):
    """CPU pre-check before any Blender time: are the layer's NAMED objects really seen (ray grid through the three.js scene, occlusion counted) on every frame of the range?
    Returns (ok, per-frame hits). A layer whose objects are buried, occluded or out of frame renders an empty mask: that is a plan error, caught here."""
    ep = Path(ep); S = spec_of(ep, lid); f0, f1 = S["frames"]
    p = subprocess.run(["node", str(ROOT / "templates/threejs_film/render.mjs"), str(ep / "film.json"), "--object-visibility", ",".join(S["objects"]), "--vis-frames", "%d-%d" % (f0, f1)], capture_output=True, text=True)
    if p.returncode: raise SystemExit("object visibility check failed: " + (p.stdout + p.stderr)[-400:])
    rows = json.load(open(ep / "out/plan/object_visibility.json"))["frames"]; hits = [r["hits"] for r in rows]; return all(h >= min_hits for h in hits), hits
def lock_fresh(ep):
    L = json.load(open(Path(ep) / "out/lock/lock.json")); bad = [n for n, w in (L.get("sha1") or {}).items() if sha(Path(ep) / "out/plan" / n) != w]
    return bad
def status(ep, W=720, H=1280):
    res = {}
    for lid in json.load(open(Path(ep) / "out/plan/layers_baked.json")):
        m = Path(ep) / "out/layers" / lid / "manifest.json"; stale = lock_fresh(ep)
        if stale: res[lid] = "STALE-LOCK (%s changed after the lock was exported)" % ",".join(stale)
        elif not m.exists(): res[lid] = "MISSING"
        else: res[lid] = "FRESH" if json.load(open(m)).get("inputs_sha1") == inputs_hash(ep, lid, W, H) else "STALE"
    return res
def run(ep, lid, blender, gpu, W, H):
    ep = Path(ep); S = spec_of(ep, lid); f0, f1 = S["frames"]; od = ep / "out/layers" / lid; od.mkdir(parents=True, exist_ok=True)
    bad = lock_fresh(ep)
    if bad: raise SystemExit("lock is stale: %s changed after --export-lock. Re-export the lock (and get the picture re-approved)." % bad)
    missing = [f for f in range(f0, f1 + 1) if not (ep / "out/stills" / ("f_%05d.png" % f)).exists()]
    if missing: raise SystemExit("base stills missing for frames %s: render them with render.mjs --frames first (same resolution)" % missing[:5])
    ih = inputs_hash(ep, lid, W, H); mp = od / "manifest.json"
    if mp.exists() and json.load(open(mp)).get("inputs_sha1") == ih and (od / "layer_report.json").exists(): print("CACHE HIT", lid); return json.load(open(od / "layer_report.json"))
    t = time.perf_counter(); cmd = [blender, "-b", "--factory-startup", "--python-exit-code", "1"] + (["--gpu-backend", gpu] if gpu else []) + ["-P", str(SCRIPTS[0]), "--", str(ROOT), str(ep), str(od), lid, str(W), str(H)]
    p = subprocess.run(cmd, capture_output=True, text=True, errors="replace"); (od / "blender.log").write_text(p.stdout + p.stderr)
    if p.returncode: print((p.stdout + p.stderr)[-1500:]); raise SystemExit("blender failed")
    return evaluate(ep, lid, od, W, H, round(time.perf_counter() - t, 2))
def evaluate(ep, lid, od, W, H, blender_s):
    """CPU half of run(): composite the layer PNGs in <od> onto the base stills, apply the per-type gate, write layer_report.json + manifest.json (also used by the QA fixtures and by a layer rendered elsewhere)"""
    ep = Path(ep); od = Path(od); S = spec_of(ep, lid); f0, f1 = S["frames"]
    import numpy as _np; from PIL import Image as _I
    empty = [f for f in range(f0, f1 + 1) if not (_np.asarray(_I.open(od / ("idmask_%05d.png" % f)).convert("RGBA"))[..., 3] > 0).any()]
    if empty: raise SystemExit("the named objects %s are not visible in frames %s (the mask is empty: buried, occluded or out of frame). Fix the layer's objects or frames; run tools/layers.py visible first." % (S["objects"], empty[:6]))
    ih = inputs_hash(ep, lid, W, H); al = next(od.glob("align_*.png")); mp = od / "manifest.json"
    cp = subprocess.run([sys.executable, str(ROOT / "phase1b/compose_1b.py"), "--base", str(ep / "out/stills"), "--layer", str(od), "--align", str(al), "--camera", str(od / "align_camera.json"), "--out", str(od / "result"), "--frames", "%d-%d" % (f0, f1)], capture_output=True, text=True)
    if cp.returncode: raise SystemExit("composite failed: " + cp.stderr[-600:])
    C = json.load(open(od / "result/compose_report.json")); T = json.load(open(od / "layer_timing.json")); g = GATES[S["type"]]; sh = C["E_layer_alpha_edges_vs_base_edges_hero_bbox_shift_px"]
    res = {"A outside the named mask nothing changes": C["A_max_outside_diff_8bit_all_frames"] <= g["A_outside_diff_max"],
           "B mean luminance added in mask <= %.2f" % g["B_mean_lum_added_max"]: C["B_mean_lum_added_in_mask_max_over_frames"] <= g["B_mean_lum_added_max"],
           "D steady-state s/frame <= %.0f" % g["D_steady_s_max"]: T["steady_mean_s"] <= g["D_steady_s_max"],
           "E layer edges register with base (<= %.2f px) and camera fov matches" % g["E_edge_shift_px_max"]: max(abs(sh[0]), abs(sh[1])) <= g["E_edge_shift_px_max"] and C["camera"]["fov_diff_deg"] <= g["E_fov_diff_deg_max"]}
    rep = {"layer": lid, "type": S["type"], "frames": [f0, f1], "gates": res, "PASS": all(res.values()), "C visual contribution": "REVIEW before_after_sheet.png (Ricks: kept only if it clearly adds; never auto-passed)",
           "blender_wall_s": blender_s, "steady_s_per_frame": T["steady_mean_s"], "cold_first_frame_s": T["cold_first_frame_s"], "metrics": {k: C[k] for k in C if k != "per_frame"}, "inputs_sha1": ih}
    json.dump(rep, open(od / "layer_report.json", "w"), indent=1); json.dump({"layer": lid, "inputs_sha1": ih, "blender": T["blender"], "resolution": [W, H], "frames": [f0, f1], "spec": S}, open(mp, "w"), indent=1); return rep
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["status", "run", "visible"]); ap.add_argument("ep"); ap.add_argument("layer", nargs="?"); ap.add_argument("--blender"); ap.add_argument("--gpu-backend", default="opengl"); ap.add_argument("--res", default="720x1280"); a = ap.parse_args()
    W, H = map(int, a.res.split("x"))
    if a.cmd == "status": print(json.dumps(status(a.ep, W, H), indent=1))
    elif a.cmd == "visible": print(json.dumps(dict(zip(("ok", "hits_per_frame"), visible(a.ep, a.layer)))))
    else: print(json.dumps(run(a.ep, a.layer, a.blender, a.gpu_backend, W, H), indent=1)); 
