#!/usr/bin/env python3
"""PHASE 1C one command: plan check -> three.js base at 720x1280 -> lock -> Blender layer / idmask / align -> compose_1b. See phase1/run_phase1.py (same pattern)."""
import argparse, json, shutil, subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parent
def run(cmd, log, env=None):
    t = time.perf_counter(); p = subprocess.run(cmd, capture_output=True, text=True, errors="replace", env=env); Path(log).write_text("$ " + " ".join(map(str, cmd)) + "\n" + p.stdout + "\n" + p.stderr)
    if p.returncode: print((p.stdout + p.stderr)[-1500:]); raise SystemExit("FAILED: " + " ".join(map(str, cmd))[:200])
    return round(time.perf_counter() - t, 2)
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--blender", required=True); ap.add_argument("--gpu-backend", default="opengl"); ap.add_argument("--out", default="/content/p1c_out"); ap.add_argument("--frames", default="201-210"); ap.add_argument("--skip-blender", action="store_true"); a = ap.parse_args()
    W, H = 720, 1280; f0, f1 = map(int, a.frames.split("-")); out = Path(a.out); ep = out / "ep"; logs = out / "logs"; shutil.rmtree(out, ignore_errors=True); logs.mkdir(parents=True); shutil.copytree(ROOT / "templates" / "film_example", ep)
    node = ROOT / "templates" / "threejs_film" / "render.mjs"; film = ep / "film.json"; T = {}; R = {"frames": [f0, f1], "resolution": [W, H]}
    T["plan_check_s"] = run([sys.executable, str(ROOT / "tools" / "film_plan.py"), "check", str(film)], logs / "plan.log")
    T["threejs_base_frames_s_wall_incl_startup"] = run(["node", str(node), str(film), "--frames", ",".join(str(f) for f in range(f0, f1 + 1)), "--scale", "0.666667", "--no-captions"], logs / "base.log")
    T["lock_export_s"] = run(["node", str(node), str(film), "--export-lock"], logs / "lock.log")
    R["nvidia_smi"] = subprocess.run("nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader", shell=True, capture_output=True, text=True).stdout.strip()
    R["node"] = subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip()
    pw = subprocess.run("node -e \"console.log(require(process.env.PLAYWRIGHT_DIR||'playwright/package.json').version)\"", shell=True, capture_output=True, text=True).stdout.strip(); R["playwright"] = pw
    if not a.skip_blender:
        bl = [a.blender, "-b", "--factory-startup", "--python-exit-code", "1", "--gpu-backend", a.gpu_backend, "-P", str(HERE / "layer_reflect.py"), "--", str(ROOT), str(ep), str(out), str(f0), str(f1)]
        for m in ("layer", "idmask", "align"): T["blender_%s_wall_s" % m] = run(bl + [m, str(W), str(H)], logs / ("blender_%s.log" % m))
        T["compose_s"] = run([sys.executable, str(HERE / "../phase1b/compose_1b.py"), "--base", str(ep / "out" / "stills"), "--layer", str(out), "--align", str(next(out.glob("align_*.png"))), "--camera", str(out / "align_camera.json"), "--out", str(out / "result"), "--frames", a.frames], logs / "compose.log")
        R["layer_timing"] = json.loads((out / "layer_timing.json").read_text()); R["idmask_timing"] = json.loads((out / "idmask_timing.json").read_text()); R["compose"] = json.loads((out / "result" / "compose_report.json").read_text())
    R["stage_wall_s"] = T; (out / "phase1c_report.json").write_text(json.dumps(R, indent=1)); print(json.dumps(R, indent=1))
if __name__ == "__main__": main()
