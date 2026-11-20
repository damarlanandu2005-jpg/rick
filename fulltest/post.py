#!/usr/bin/env python3
"""fulltest/post.py -- GLUE: dissolves between shots + the EXISTING Ricks grade (templates/blender_look/grade.py) on the rendered preview frames.
    python3 fulltest/post.py --script fulltest/script_passA.json --frames <out>/frames --out <out>/frames_post --stride 2
Script keys used: shots[].sec, transitions[{between:[a,b], type:'dissolve', sec}], grade ('day'|...|null).
A dissolve blends the last N rendered frames of shot a with the first N of shot b (the pair is replaced by N blended frames)."""
import argparse, json, os, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT / "templates"))
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--script", required=True); ap.add_argument("--frames", required=True); ap.add_argument("--out", required=True); ap.add_argument("--stride", type=int, default=2); a = ap.parse_args()
    S = json.loads(Path(a.script).read_text()); fps = S.get("fps", 30); shots = S["shots"]; frames = Path(a.frames)
    starts, f = [], 1
    for sh in shots: starts.append(f); f += round(sh["sec"] * fps)
    total = f - 1; have = {int(p.stem.split("_")[1]) for p in frames.glob("f_*.png")}
    seq = [n for n in range(1, total + 1, a.stride) if n in have]
    if not seq: print("FULL_ERROR post: no frames in %s" % frames); sys.exit(1)
    shot_of = {}; 
    for i, sh in enumerate(shots):
        for n in seq:
            if starts[i] <= n < starts[i] + round(sh["sec"] * fps): shot_of[n] = sh["id"]
    items = [("f", n) for n in seq]                                     # ("f", frame) or ("x", [frameA, frameB, w])
    for tr in S.get("transitions", []):
        if tr.get("type") != "dissolve": continue
        sa, sb = tr["between"]; N = max(1, round(tr.get("sec", .5) * fps / a.stride))
        fa = [n for n in seq if shot_of.get(n) == sa][-N:]; fb = [n for n in seq if shot_of.get(n) == sb][:N]
        if len(fa) < N or len(fb) < N: print("note: dissolve %s->%s skipped (shots shorter than %d rendered frames)" % (sa, sb, N)); continue
        ia = items.index(("f", fa[0])); items = items[:ia] + [("x", (x, y, (k + 1) / (N + 1))) for k, (x, y) in enumerate(zip(fa, fb))] + [i for i in items[ia:] if i[0] == "f" and i[1] not in fa and i[1] not in fb]
    preset = S.get("grade"); G = None
    if preset:
        try:
            from blender_look import grade as G
            if preset not in G.P: print("note: grade preset %s unknown, skipped" % preset); G = None
        except Exception as e: print("note: grade not applied: %r" % (e,)); G = None
    out = Path(a.out); shutil.rmtree(out, ignore_errors=True); out.mkdir(parents=True)
    ld = lambda n: np.asarray(Image.open(frames / ("f_%04d.png" % n)).convert("RGB")).astype(np.float32) / 255
    for i, (k, v) in enumerate(items, 1):
        arr = ld(v) if k == "f" else (1 - v[2]) * ld(v[0]) + v[2] * ld(v[1])
        if G is not None: arr = G.grade(arr, preset)
        Image.fromarray((np.clip(arr, 0, 1) * 255 + .5).astype(np.uint8)).save(out / ("p_%04d.png" % i))
    print("POST_REPORT " + json.dumps({"in_frames": len(seq), "out_frames": len(items), "dissolves": sum(1 for k, _ in items if k == "x"), "grade": preset if G is not None else None}))
main()
