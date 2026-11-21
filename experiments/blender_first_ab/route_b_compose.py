"""ROUTE B, CPU side: grade.py (existing) on the raw Blender frame, then the JS overlay (captions + 2D effects, render.mjs --overlay) laid over. No new look code.
  route_b_compose.py <raw_dir> <overlay_dir> <out_dir> <preset> <ranges>
The vignette is fitted ONCE per range on its first frame (grade.fit_vig) and held for the whole range (grade.py: never per frame, it would flicker)."""
import sys, os, json, time
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates", "blender_look"))
import grade as G
raw, ov, out, preset, ranges = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], [tuple(map(int, r.split("-"))) for r in sys.argv[5].split(",")]
os.makedirs(out, exist_ok=True); rep = {"preset": preset, "vignette": {}, "frame_s": []}
for a, b in ranges:
    f0 = np.asarray(Image.open(os.path.join(raw, "b_%05d.png" % a)).convert("RGB")).astype(np.float32) / 255; v = G.fit_vig(f0, preset, G.P[preset].get("vig_target", .67)); rep["vignette"]["%d-%d" % (a, b)] = v
    for f in range(a, b + 1):
        t = time.perf_counter(); x = np.asarray(Image.open(os.path.join(raw, "b_%05d.png" % f)).convert("RGB")).astype(np.float32) / 255; g = G.grade(x, preset, v)
        o = np.asarray(Image.open(os.path.join(ov, "o_%05d.png" % f)).convert("RGBA")).astype(np.float32) / 255; assert o.shape[:2] == g.shape[:2], "overlay %s vs picture %s" % (o.shape, g.shape)
        res = o[..., :3] * o[..., 3:4] + g * (1 - o[..., 3:4]); Image.fromarray((np.clip(res, 0, 1) * 255 + .5).astype(np.uint8)).save(os.path.join(out, "f_%05d.png" % f)); rep["frame_s"].append(round(time.perf_counter() - t, 3))
json.dump(rep, open(os.path.join(out, "compose_timing.json"), "w"), indent=1); print("compose done", len(rep["frame_s"]), "frames, mean %.2f s/frame" % (sum(rep["frame_s"]) / len(rep["frame_s"])))
