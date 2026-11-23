#!/usr/bin/env python3
"""PHASE 5+6 Colab run: the Western through tools/pipeline.py with a real Blender layer (lamp_reflect), then the test Short.
  python3 phase6/run_phase6.py --blender <blender> [--gpu-backend opengl] [--frames 0-149|all] [--renderer auto] [--out /content/p6_out]"""
import argparse, json, shutil, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser(); ap.add_argument("--blender", required=True); ap.add_argument("--gpu-backend", default="opengl"); ap.add_argument("--frames", default="201-215"); ap.add_argument("--renderer", default="auto"); ap.add_argument("--out", default="/content/p6_out"); a = ap.parse_args()
out = Path(a.out); shutil.rmtree(out, ignore_errors=True); out.mkdir(parents=True); ep = out / "ep"; shutil.copytree(ROOT / "templates/film_western_example", ep, ignore=shutil.ignore_patterns("out")); T = {}
t = time.perf_counter(); c = subprocess.run([sys.executable, str(ROOT / "phase5/test_western_cpu.py"), str(out / "cpu5")], capture_output=True, text=True); (out / "phase5_cpu.log").write_text(c.stdout + c.stderr); T["phase5_cpu_gate_s"] = round(time.perf_counter() - t, 1); G = {"P5 CPU gate (recipe, density, named objects, flight, QA)": c.returncode == 0}
t = time.perf_counter(); p = subprocess.run([sys.executable, str(ROOT / "tools/pipeline.py"), str(ep), "--frames", a.frames, "--blender", a.blender, "--gpu-backend", a.gpu_backend, "--renderer", a.renderer, "--unapproved-test-run", "--accept-layers"], capture_output=True, text=True); (out / "pipeline.log").write_text(p.stdout + p.stderr); T["pipeline_s"] = round(time.perf_counter() - t, 1)
print(p.stdout[-3000:]); print(p.stderr[-1500:])
rep = json.loads((ep / "out/pipeline/pipeline_report.json").read_text()); G["P6 pipeline end to end (exit 0)"] = p.returncode == 0
for r in rep: G["P6 stage " + r["stage"]] = r["status"] in ("PASS", "CACHE", "INPUT", "KEEP", "SKIP")
lr = ep / "out/layers/lamp_reflect/layer_report.json"; L = json.loads(lr.read_text()) if lr.exists() else None
qa = json.loads((ep / "out/qa/qa_report.json").read_text()) if (ep / "out/qa/qa_report.json").exists() else None
R = {"frames": a.frames, "renderer": a.renderer, "stage_wall_s": T, "gates": G, "pipeline": rep, "layer_report": L, "qa": qa, "PHASE56": "PASS" if all(G.values()) else "FAIL", "C": "layer visual contribution: review before_after_sheet.png (auto-accepted for this test run, flagged in review.json)"}
(out / "phase6_report.json").write_text(json.dumps(R, indent=1, default=str)); print(json.dumps({k: R[k] for k in ("stage_wall_s", "gates", "PHASE56")}, indent=1)); sys.exit(0 if R["PHASE56"] == "PASS" else 1)
