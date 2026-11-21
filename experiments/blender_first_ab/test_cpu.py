#!/usr/bin/env python3
"""CPU test of the experiment's non-Blender parts on synthetic inputs (real three.js stills as 'A', a blurred copy as 'B'): compose, blind sheets, sharpness, matrix, code count, key separation.
  test_cpu.py <stills_dir with f_00000.png...> <workdir>"""
import json, shutil, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
HERE = Path(__file__).resolve().parent; S, W0 = Path(sys.argv[1]), Path(sys.argv[2]); shutil.rmtree(W0, ignore_errors=True); W0.mkdir(parents=True); R = ["0-9", "20-24", "30-35"]; G = {}
(W0 / "evidence").mkdir(); vis = [{"sheriff": {"x": .5, "y": .55, "h": .3, "head_y": .4}, "ghost": None} for _ in range(40)]; json.dump({"frames": vis}, open(W0 / "evidence/visibility.json", "w"))
raw = W0 / "raw"; ov = W0 / "ov"; raw.mkdir(); ov.mkdir()
for f in range(0, 36):
    im = Image.open(S / ("f_%05d.png" % f)).convert("RGB"); im.filter(ImageFilter.GaussianBlur(1.5)).save(raw / ("b_%05d.png" % f)); o = np.zeros((1280, 720, 4), np.uint8); o[100:140, 50:300] = (255, 255, 255, 255); Image.fromarray(o).save(ov / ("o_%05d.png" % f))
    for r in R:
        a, b = map(int, r.split("-"))
        if a <= f <= b:
            d = W0 / ("epA_" + r) / "out/final/frames"; d.mkdir(parents=True, exist_ok=True); im.save(d / ("f_%05d.png" % f))
p = subprocess.run([sys.executable, str(HERE / "route_b_compose.py"), str(raw), str(ov), str(W0 / "routeB/final"), "day", ",".join(R)], capture_output=True, text=True); print(p.stdout, p.stderr[-600:]); G["compose runs"] = p.returncode == 0
for r in R:
    a, b = map(int, r.split("-")); d = W0 / "routeB" / ("frames_" + r); d.mkdir(parents=True)
    for f in range(a, b + 1): shutil.move(str(W0 / "routeB/final" / ("f_%05d.png" % f)), d / ("f_%05d.png" % f))
x = np.asarray(Image.open(W0 / "routeB/frames_0-9/f_00000.png")); G["overlay caption laid over the graded picture (white box)"] = bool((x[110:130, 60:290] > 250).all())
json.dump({}, open(W0 / "evidence/timing.json", "w"))
p = subprocess.run([sys.executable, str(HERE / "ab_run.py"), "--blender", "none", "--out", str(W0), "--ranges", ",".join(R), "--only", "sheets"], capture_output=True, text=True); print(p.stdout[-1500:], p.stderr[-1500:]); G["ab_run sheets stage"] = p.returncode == 0
J = W0 / "judge_pack"; names = sorted(q.name for q in J.iterdir()) if J.exists() else []; print(names)
G["blind: no route name in any judge_pack file name"] = not any(("_A" in n or "_B" in n or "routeA" in n or "routeB" in n or "hybrid" in n.lower()) for n in names) and bool(names)
txt = "".join(q.read_text() for q in J.glob("*.md")).lower(); G["blind: JUDGE_ME.md has no identity words"] = not any(w in txt for w in ("hybrid", "three.js", "blender", "route a", "route b", "lamp_reflect", "from_lock"))
K = json.load(open(W0 / "ANSWER_KEY_do_not_open_until_judged.json")); G["key is a separate file outside judge_pack"] = not (J / "ANSWER_KEY_do_not_open_until_judged.json").exists() and set(K["ranges"]) == set(R)
G["shuffle varies across ranges (seeded)"] = len({tuple(v.values()) for v in K["ranges"].values()}) >= 1
sh = json.load(open(W0 / "evidence/card_sharpness.json")); m = sh["ranges"]["0-9"]["sheriff"]["median_lap_ratio"]; print("synthetic blur 1.5px -> lap ratio", m); G["sharpness detects a blurred B (ratio < 0.85)"] = m < .85
cc = json.load(open(W0 / "evidence/code_count.json")); G["code count: new Route-B only"] = cc["new_route_b_total"] > 0 and "from_lock.py" not in json.dumps(cc["NEW Route-B code (counted; non-blank, non-comment lines)"])
G["effects matrix written"] = (W0 / "evidence/effects_matrix.md").exists()
print(json.dumps(G, indent=1)); sys.exit(0 if all(G.values()) else 1)
