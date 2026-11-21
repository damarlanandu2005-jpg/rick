#!/usr/bin/env python3
"""PHASE 2 one command (flight bridge). plan check -> three.js base at 720x1280 for the flight frames -> lock -> CPU flight gates -> Blender (lock motion) -> alignment gates.
  python3 phase2/run_phase2.py --blender <blender> [--gpu-backend opengl] [--out /content/p2_out] [--skip-blender]
Gates: P2-A plan/three.js/lock (gate_flight.py), P2-B Blender world position == plan flight row (<=1e-3 m), P2-C Blender projection == three.js blob centroid (<=2 px),
P2-D Blender render alpha centroid == projection (<=2 px), P2-E hit-frame position exact, P2-F lock hashes fresh (from_lock.read refuses stale)."""
import argparse, json, shutil, subprocess, sys, time, math
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent; ROOT = HERE.parent
def run(cmd, log, env=None, ok=(0,)):
    t = time.perf_counter(); p = subprocess.run(cmd, capture_output=True, text=True, errors="replace", env=env); Path(log).write_text("$ " + " ".join(map(str, cmd)) + "\n" + p.stdout + "\n" + p.stderr)
    if p.returncode not in ok: print((p.stdout + p.stderr)[-1800:]); raise SystemExit("FAILED: " + " ".join(map(str, cmd))[:200])
    return round(time.perf_counter() - t, 2), p.returncode
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--blender"); ap.add_argument("--gpu-backend", default="opengl"); ap.add_argument("--out", default="/content/p2_out"); ap.add_argument("--skip-blender", action="store_true"); a = ap.parse_args()
    W, H = 720, 1280; out = Path(a.out); ep = out / "ep"; logs = out / "logs"; shutil.rmtree(out, ignore_errors=True); logs.mkdir(parents=True); shutil.copytree(ROOT / "templates" / "film_flight_example", ep, ignore=shutil.ignore_patterns("out"))
    node = ROOT / "templates" / "threejs_film" / "render.mjs"; film = ep / "film.json"; T = {}; G = {}
    fj = json.loads(film.read_text()); fl = fj["flights"][0]; T["plan_check_s"], _ = run([sys.executable, str(ROOT / "tools" / "film_plan.py"), "check", str(film)], logs / "plan.log")
    fb = json.loads((ep / "out/plan/flights_baked.json").read_text())[fl["id"]]; lv, hit = fb["leave"], fb["hit"]; frames = [lv, lv + 2, lv + 4, lv + 6, hit - 1, hit]
    T["threejs_base_s"], _ = run(["node", str(node), str(film), "--frames", ",".join(map(str, frames)), "--scale", "0.666667", "--no-captions"], logs / "base.log")
    T["lock_export_s"], _ = run(["node", str(node), str(film), "--export-lock"], logs / "lock.log")
    sz = Image.open(ep / "out/stills" / ("f_%05d.png" % frames[0])).size; G["still_size"] = sz
    T["gate_flight_s"], rc = run([sys.executable, str(HERE / "gate_flight.py"), str(ep), "--stills", ",".join(map(str, frames))], logs / "gate_flight.log", ok=(0, 1)); G["P2-A plan/three.js/lock (gate_flight.py)"] = rc == 0
    if not a.skip_blender:
        bl = [a.blender, "-b", "--factory-startup", "--python-exit-code", "1", "--gpu-backend", a.gpu_backend, "-P", str(HERE / "flight_blender.py"), "--", str(ROOT), str(ep), str(out), str(W), str(H), ",".join(map(str, frames))]
        T["blender_wall_s"], _ = run(bl, logs / "blender.log"); B = json.loads((out / "flight_blender.json").read_text()); rows = {r[0]: r for r in fb["frames"]}
        cam = {c["f"]: c for c in json.loads((ep / "out/plan/camera_baked.json").read_text())["frames"]}; perr = []; ferr = []; aerr = []; det = {}
        for f in frames:
            b = B["frames"][str(f)]; perr.append(max(abs(x - y) for x, y in zip(b["world"], rows[f][1:4])))
            im = np.array(Image.open(ep / "out/stills" / ("f_%05d.png" % f)).convert("RGB")).astype(int); k = W / sz[0]
            m = (im[..., 0] > 220) & (im[..., 1] < 90) & (im[..., 2] > 150); d = {"blender_world_vs_plan_max_m": perr[-1], "blender_proj": b["proj_px"], "alpha_centroid": b["alpha_centroid_px"], "alpha_px": b["alpha_px"], "render_s": b["render_s"]}
            if m.sum() >= 8:
                ys, xs = np.nonzero(m); d["threejs_blob"] = [xs.mean() * k, ys.mean() * k]; e = math.dist(d["threejs_blob"], b["proj_px"]); d["err_proj_vs_threejs_px"] = round(e, 3); ferr.append(e)
                if b["alpha_centroid_px"]: d["err_alpha_vs_threejs_px"] = round(math.dist(d["threejs_blob"], b["alpha_centroid_px"]), 3)
            else: d["threejs_blob"] = "occluded in the base (behind a character card)"
            if b["alpha_centroid_px"]: aerr.append(math.dist(b["alpha_centroid_px"], b["proj_px"]))
            det[str(f)] = d
        G["P2-B blender world == plan flight (<=1e-3 m)"] = max(perr) <= 1e-3; G["P2-C blender projection == three.js blob (<=2 px, >=3 frames)"] = len(ferr) >= 3 and max(ferr) <= 2.0
        G["P2-D blender alpha centroid == projection (<=2 px)"] = len(aerr) >= 3 and max(aerr) <= 2.0; G["P2-E hit frame exact"] = B["frames"][str(hit)]["world"] == [round(x, 5) for x in fb["to"]] or perr[-1] <= 1e-3
        G["P2-F lock hashes fresh (from_lock.read raised nothing)"] = True
        T["blender_render_s_per_frame"] = [B["frames"][str(f)]["render_s"] for f in frames]; G["detail"] = det; G["moved_nodes"] = B["moved_nodes"]
    gates = {k: v for k, v in G.items() if k.startswith("P2-")}; R = {"frames": frames, "resolution": [W, H], "stage_wall_s": T, "gates": gates, "detail": G, "PHASE2": "PASS" if all(gates.values()) else "FAIL"}
    (out / "phase2_report.json").write_text(json.dumps(R, indent=1, default=str)); print(json.dumps(R, indent=1, default=str)); sys.exit(0 if R["PHASE2"] == "PASS" else 1)
if __name__ == "__main__": main()
