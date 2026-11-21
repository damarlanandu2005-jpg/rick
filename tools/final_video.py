#!/usr/bin/env python3
"""Final assembly (hybrid Phase 4/6): three.js base stills + every FRESH, PASSED Blender layer -> out/final/frames + out/final/final.mp4 (silent).
  final_video.py <ep> [--frames a-b] [--res 720x1280]
Composite rule (same as the layer gate, compose_1b): out = base + layer_rgb x layer_alpha, clipped, display space. A layer that is stale or whose gate did not PASS is refused, not skipped.
Writes out/final/final_manifest.json (frames, layers used, sha1 of every input still / layer png) so QA can prove the video is the composite of exactly these inputs."""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent)); import layers as LY
def comp(base_u8, layer_png):
    b = base_u8.astype(np.float32) / 255; L = np.asarray(Image.open(layer_png).convert("RGBA")).astype(np.float32) / 255
    return (np.clip(b + L[..., :3] * L[..., 3:4], 0, 1) * 255 + .5).astype(np.uint8)
def assemble(ep, f0=None, f1=None, W=720, H=1280):
    ep = Path(ep); film = json.load(open(ep / "film.json")); fps = film["fps"]; cam = json.load(open(ep / "out/plan/camera_baked.json"))["frames"]; n = len(cam)
    f0 = 0 if f0 is None else f0; f1 = n - 1 if f1 is None else f1; out = ep / "out/final"; fd = out / "frames"; fd.mkdir(parents=True, exist_ok=True)
    for q in fd.glob("*.png"): q.unlink()
    LP = ep / "out/plan/layers_baked.json"; lay = json.load(open(LP)) if LP.exists() else {}; used = {}
    stale = LY.lock_fresh(ep)
    if stale: raise SystemExit("lock is stale (%s changed after the export)" % stale)
    st = LY.status(str(ep), W, H) if lay else {}
    for lid, S in lay.items():
        if S["frames"][1] < f0 or S["frames"][0] > f1: continue
        rv = ep / "out/layers" / lid / "review.json"          # the creative decision (Ricks: a layer is kept only if it clearly adds): data, written by the director/LLM/human, never by this script
        if not (rv.exists() and json.load(open(rv)).get("keep") is True): print("layer %s omitted: no review.json with keep=true" % lid); continue
        if st[lid] != "FRESH": raise SystemExit("layer %s is %s: re-run tools/layers.py run" % (lid, st[lid]))
        if not json.load(open(ep / "out/layers" / lid / "layer_report.json"))["PASS"]: raise SystemExit("layer %s did not pass its gate" % lid)
        used[lid] = S["frames"]
    man = {"fps": fps, "frames": [f0, f1], "resolution": [W, H], "layers": used, "inputs": {}}
    for f in range(f0, f1 + 1):
        sp = ep / "out/stills" / ("f_%05d.png" % f)
        if not sp.exists(): raise SystemExit("base still missing: frame %d (render the base for this range first)" % f)
        im = np.asarray(Image.open(sp).convert("RGB")); assert im.shape[:2] == (H, W), "base still %d is %s, expected %dx%d" % (f, im.shape[1::-1], W, H)
        man["inputs"][str(f)] = {"base": hashlib.sha1(sp.read_bytes()).hexdigest()}
        for lid, (a, b) in used.items():
            if a <= f <= b: lp = ep / "out/layers" / lid / ("layer_%05d.png" % f); im = comp(im, lp); man["inputs"][str(f)][lid] = hashlib.sha1(lp.read_bytes()).hexdigest()
        Image.fromarray(im).save(fd / ("f_%05d.png" % f))
    mp4 = out / "final.mp4"; r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-start_number", str(f0), "-i", str(fd / "f_%05d.png"), "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", "-an", str(mp4)], capture_output=True, text=True)
    if r.returncode: raise SystemExit("ffmpeg failed: " + r.stderr[-500:])
    json.dump(man, open(out / "final_manifest.json", "w"), indent=1); return mp4, man
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("ep"); ap.add_argument("--frames"); ap.add_argument("--res", default="720x1280"); a = ap.parse_args(); W, H = map(int, a.res.split("x"))
    f0, f1 = (map(int, a.frames.split("-")) if a.frames else (None, None)); mp4, m = assemble(a.ep, f0, f1, W, H); print(mp4, m["frames"], "layers:", list(m["layers"]))
