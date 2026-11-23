#!/usr/bin/env python3
"""PHASE 7: the complete Western Short (all frames, 720x1280, 30 fps) through the EXISTING hybrid pipeline, no new rendering architecture, no new layers.
  python3 phase7/run_full.py [--blender B --gpu-backend opengl] [--renderer cpu] [--out /content/p7_out] [--frames all]
Measures: total pipeline time, cold start (process start -> first base still), per-frame base times (from consecutive still mtimes: no renderer change), stage times.
Collects: every QA check not PASS (status, value, note; classification A/B/C/D is made by a human reading the list, never by this script), a review pack (contact sheets, 1:1 character crops, frame-to-frame motion/flicker series), the layer before/after sheet."""
import argparse, json, os, shutil, statistics, subprocess, sys, time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser(); ap.add_argument("--blender"); ap.add_argument("--gpu-backend", default="opengl"); ap.add_argument("--renderer", default="cpu"); ap.add_argument("--out", default="/content/p7_out"); ap.add_argument("--frames", default="all"); ap.add_argument("--res", default="720x1280"); a = ap.parse_args()
W, H = map(int, a.res.split("x")); out = Path(a.out); shutil.rmtree(out, ignore_errors=True); out.mkdir(parents=True); ep = out / "ep"; shutil.copytree(ROOT / "templates/film_western_example", ep, ignore=shutil.ignore_patterns("out"))
cmd = [sys.executable, str(ROOT / "tools/pipeline.py"), str(ep), "--frames", a.frames, "--renderer", a.renderer, "--res", a.res, "--unapproved-test-run", "--accept-layers"] + (["--blender", a.blender, "--gpu-backend", a.gpu_backend] if a.blender else [])
t0 = time.time(); p = subprocess.run(cmd, capture_output=True, text=True, errors="replace"); wall = time.time() - t0; (out / "pipeline.log").write_text(p.stdout + p.stderr); print(p.stdout[-2500:]); print(p.stderr[-1000:])
R = {"command": " ".join(cmd), "pipeline_rc": p.returncode, "total_pipeline_wall_s": round(wall, 1), "resolution": [W, H]}
rp = ep / "out/pipeline/pipeline_report.json"; rep = json.load(open(rp)) if rp.exists() else []; R["stages"] = rep
st = sorted((ep / "out/stills").glob("f_*.png"), key=lambda q: q.name); mt = [q.stat().st_mtime for q in st]
if len(mt) > 2:
    d = [mt[i] - mt[i - 1] for i in range(1, len(mt))]; d.sort(); n = len(d); R["base"] = {"frames": len(st), "cold_start_s_process_to_first_still": round(mt[0] - t0, 1), "per_frame_s": {"mean": round(sum(d) / n, 3), "median": round(statistics.median(d), 3), "p90": round(d[int(np.ceil(.9 * n)) - 1], 3), "max": round(d[-1], 3)}, "stage_s": next((x["seconds"] for x in rep if x["stage"] == "2 base"), None)}
qp = ep / "out/qa/qa_report.json"; qa = json.load(open(qp)) if qp.exists() else {"PASS": None, "checks": []}; bad = [c for c in qa["checks"] if c["status"] not in ("PASS",)]
R["qa"] = {"PASS": qa["PASS"], "n_checks": len(qa["checks"]), "n_pass": sum(c["status"] == "PASS" for c in qa["checks"]), "n_fail": sum(c["status"] == "FAIL" for c in qa["checks"]), "n_skip": sum(c["status"] == "SKIP" for c in qa["checks"]), "n_warn": sum(c["status"] == "WARN" for c in qa["checks"]), "non_pass": bad}
pl = ep / "out/pipeline/plan.log"; R["plan_warns"] = [l for l in pl.read_text().splitlines() if "WARN" in l] if pl.exists() else []
fd = ep / "out/final/frames"; fr = sorted(fd.glob("f_*.png")); rev = out / "review"; rev.mkdir()
if fr:
    G = [np.asarray(Image.open(q).convert("RGB")).astype(np.float32) for q in fr]; lum = [float(g.mean()) for g in G]; diff = [0.0] + [float(np.abs(G[i] - G[i - 1]).mean()) for i in range(1, len(G))]
    R["temporal"] = {"frames": len(fr), "mean_luma_series_step_max": round(max(abs(lum[i] - lum[i - 1]) for i in range(1, len(lum))), 3), "frame_diff_mean": round(float(np.mean(diff)), 3), "frame_diff_p99": round(float(np.percentile(diff, 99)), 3),
                      "largest_frame_diffs": [[int(i), round(diff[i], 2)] for i in np.argsort(diff)[::-1][:12]]}
    json.dump({"luma": lum, "diff": diff}, open(rev / "temporal_series.json", "w"))
    tw, th = 240, int(240 * H / W); per = 12
    for s in range(0, len(fr), 15 * per):
        idx = list(range(s, min(len(fr), s + 15 * per), 15)); sh = Image.new("RGB", (per * tw, th + 14), (20, 20, 20)); d = ImageDraw.Draw(sh)
        for j, i in enumerate(idx): sh.paste(Image.fromarray(G[i].astype(np.uint8)).resize((tw, th), Image.LANCZOS), (j * tw, 14)); d.text((j * tw + 4, 1), "f%d" % i, fill=(255, 255, 255))
        sh.save(rev / ("contact_f%04d.png" % s))
    for i in sorted({0, 40, 90, 140, 200, 205, 260, 320, 350, 400, 455}):
        if i < len(fr): Image.fromarray(G[i].astype(np.uint8)).save(rev / ("full_f%04d.png" % i))
for f in ("out/final/final.mp4", "out/final/final_manifest.json", "out/qa/qa_report.md", "out/qa/qa_report.json"):
    if (ep / f).exists(): shutil.copy(ep / f, rev / Path(f).name)
for q in (ep / "out/qa/film_check").glob("*") if (ep / "out/qa/film_check").exists() else []:
    if q.is_file(): shutil.copy(q, rev / ("film_check_" + q.name))
lr = ep / "out/layers/lamp_reflect"
if lr.exists():
    for q in list((lr / "result").glob("before_after_sheet.png")) + [lr / "layer_report.json"]:
        if q.exists(): shutil.copy(q, rev / q.name)
    R["layer_lamp_reflect"] = json.load(open(lr / "layer_report.json")) if (lr / "layer_report.json").exists() else None
else: R["layer_lamp_reflect"] = "not rendered (no --blender)"
mp = ep / "out/final/final.mp4"
if mp.exists():
    dec = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp), "-f", "null", "-"], capture_output=True, text=True); R["mp4_decode_errors"] = dec.stderr.strip()[-400:] or "none"; R["mp4_bytes"] = mp.stat().st_size
json.dump(R, open(out / "phase7_report.json", "w"), indent=1, default=str); print(json.dumps({k: R.get(k) for k in ("pipeline_rc", "total_pipeline_wall_s", "base", "temporal")}, indent=1, default=str)); print("QA", {k: R["qa"][k] for k in ("PASS", "n_checks", "n_pass", "n_fail", "n_skip", "n_warn")}); [print("  ", c["status"], c["stage"], c["name"], "|", c["value"][:100], "|", c["note"][:120]) for c in bad]
sys.exit(0 if p.returncode == 0 else 1)
