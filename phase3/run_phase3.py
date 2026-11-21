#!/usr/bin/env python3
"""PHASE 3 one command: CPU test (spec, bake, hashes) -> plan -> three.js base 201-210 @720x1280 -> lock -> layers.py run (ONE Blender process: layer + idmask + align) -> composite -> per-type gate -> second run must be a CACHE HIT -> asset registry check.
  python3 phase3/run_phase3.py --blender <blender> [--gpu-backend opengl] [--out /content/p3_out]"""
import argparse, json, shutil, subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parent; sys.path.insert(0, str(ROOT / "tools")); import layers as LY
def run(cmd, log, ok=(0,)):
    t = time.perf_counter(); p = subprocess.run(cmd, capture_output=True, text=True, errors="replace"); Path(log).write_text("$ " + " ".join(map(str, cmd)) + "\n" + p.stdout + "\n" + p.stderr)
    if p.returncode not in ok: print((p.stdout + p.stderr)[-1800:]); raise SystemExit("FAILED: " + " ".join(map(str, cmd))[:200])
    return round(time.perf_counter() - t, 2), p.returncode
ap = argparse.ArgumentParser(); ap.add_argument("--blender", required=True); ap.add_argument("--gpu-backend", default="opengl"); ap.add_argument("--out", default="/content/p3_out"); a = ap.parse_args()
W, H = 720, 1280; out = Path(a.out); shutil.rmtree(out, ignore_errors=True); (out / "logs").mkdir(parents=True); logs = out / "logs"; T = {}; G = {}
T["cpu_test_s"], rc = run([sys.executable, str(HERE / "test_layers_cpu.py"), str(out / "cpu")], logs / "cpu_test.log", ok=(0, 1)); G["P3-A CPU: spec gate, deterministic bake, hash invalidation, named objects in glb"] = rc == 0
ep = out / "ep"; shutil.copytree(ROOT / "templates/film_flight_example", ep, ignore=shutil.ignore_patterns("out")); film = ep / "film.json"; node = ROOT / "templates/threejs_film/render.mjs"
run([sys.executable, str(ROOT / "tools/film_plan.py"), "check", str(film)], logs / "plan.log")
T["threejs_base_s"], _ = run(["node", str(node), str(film), "--frames", ",".join(str(f) for f in range(201, 211)), "--scale", "0.666667", "--no-captions"], logs / "base.log")
T["lock_export_s"], _ = run(["node", str(node), str(film), "--export-lock"], logs / "lock.log")
t = time.perf_counter(); R1 = LY.run(str(ep), "clock_reflect", a.blender, a.gpu_backend, W, H); T["layer_run_s"] = round(time.perf_counter() - t, 2)
for k, v in R1["gates"].items(): G["P3-B " + k] = v
t = time.perf_counter(); R2 = LY.run(str(ep), "clock_reflect", a.blender, a.gpu_backend, W, H); T["second_run_s"] = round(time.perf_counter() - t, 2); G["P3-C second run is a cache hit (<5 s)"] = T["second_run_s"] < 5
st = LY.status(str(ep)); G["P3-D status FRESH after run"] = st["clock_reflect"] == "FRESH"
ar = subprocess.run([sys.executable, str(ROOT / "tools/assets.py"), "check"], capture_output=True, text=True); G["P3-E asset registry check"] = ar.returncode == 0
gates = {k: v for k, v in G.items()}; rep = {"stage_wall_s": T, "gates": gates, "layer_report": R1, "status": st, "registry": ar.stdout.strip(), "PHASE3": "PASS" if all(gates.values()) else "FAIL", "C": "visual contribution: review before_after_sheet.png (not auto-passed)"}
(out / "phase3_report.json").write_text(json.dumps(rep, indent=1, default=str)); print(json.dumps(rep, indent=1, default=str)); sys.exit(0 if rep["PHASE3"] == "PASS" else 1)
