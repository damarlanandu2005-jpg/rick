#!/usr/bin/env python3
"""PHASE 1 hybrid seam proof, one command. Uses the Ricks pieces unchanged:
  film_plan.py check -> render.mjs --frames (three.js base) -> render.mjs --export-lock -> blender: layer_metal.py layer + align -> compose_compare.py
usage: python3 phase1/run_phase1.py --blender /path/to/blender --gpu-backend opengl --out /content/p1_out [--frames 201-210] [--skip-blender]
The environment (LD_LIBRARY_PATH / EGL for the T4, PLAYWRIGHT_DIR) is inherited from the caller. Prints one compact JSON report."""
import argparse, json, os, shutil, subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parent

def run(cmd, log, env=None, timeout=3600):
    t = time.perf_counter(); p = subprocess.run(cmd, capture_output=True, text=True, errors="replace", env=env, timeout=timeout)
    Path(log).write_text("$ " + " ".join(map(str, cmd)) + "\n" + p.stdout + "\n" + p.stderr); dt = round(time.perf_counter() - t, 2)
    if p.returncode != 0: print((p.stdout + p.stderr)[-1500:]); raise SystemExit("FAILED (%s): %s" % (p.returncode, " ".join(map(str, cmd))[:200]))
    return dt, p.stdout

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--blender", required=True); ap.add_argument("--gpu-backend", default="opengl"); ap.add_argument("--out", default="/content/p1_out")
    ap.add_argument("--frames", default="201-210"); ap.add_argument("--skip-blender", action="store_true"); a = ap.parse_args()
    f0, f1 = map(int, a.frames.split("-")); out = Path(a.out); ep = out / "ep"; logs = out / "logs"; shutil.rmtree(out, ignore_errors=True); logs.mkdir(parents=True)
    shutil.copytree(ROOT / "templates" / "film_example", ep); T = {}; R = {"frames": [f0, f1]}
    node = ROOT / "templates" / "threejs_film" / "render.mjs"; film = ep / "film.json"
    T["plan_check_s"], _ = run([sys.executable, str(ROOT / "tools" / "film_plan.py"), "check", str(film)], logs / "plan.log")
    T["threejs_base_frames_s"], _ = run(["node", str(node), str(film), "--frames", ",".join(str(f) for f in range(f0, f1 + 1)), "--scale", "1", "--no-captions"], logs / "base.log")
    T["lock_export_s"], _ = run(["node", str(node), str(film), "--export-lock"], logs / "lock.log")
    R["gpu_nvidia_smi"] = subprocess.run("nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader", shell=True, capture_output=True, text=True).stdout.strip()
    if not a.skip_blender:
        bl = [a.blender, "-b", "--factory-startup", "--python-exit-code", "1", "--gpu-backend", a.gpu_backend, "-P", str(HERE / "layer_metal.py"), "--", str(ROOT), str(ep), str(out), str(f0), str(f1)]
        T["blender_layer_wall_s"], _ = run(bl + ["layer"], logs / "blender_layer.log"); T["blender_align_wall_s"], _ = run(bl + ["align"], logs / "blender_align.log")
        T["compose_s"], _ = run([sys.executable, str(HERE / "compose_compare.py"), "--base", str(ep / "out" / "stills"), "--layer", str(out), "--align", str(next(out.glob("align_*.png"))), "--camera", str(out / "align_camera.json"), "--out", str(out / "result"), "--frames", a.frames], logs / "compose.log")
        R["layer_timing"] = json.loads((out / "layer_timing.json").read_text()); R["compose"] = json.loads((out / "result" / "compose_report.json").read_text())
    R["stage_wall_s"] = T; (out / "phase1_report.json").write_text(json.dumps(R, indent=1)); print(json.dumps(R, indent=1))

if __name__ == "__main__": main()
