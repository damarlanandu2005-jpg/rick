#!/usr/bin/env python3
"""Hybrid QA (Phase 4): inspects the ACTUAL composite and the final video, in five stages, and reuses the Ricks checkers instead of re-implementing them.
  qa_hybrid.py <ep> [--res 720x1280] [--no-film-check] [--frame-checks]
  1 PLAN       film_plan.py check (41+ gates; 0 FAIL), baked files present                                   [Ricks film_plan]
  2 THREEJS    every base still: right size, not blank, no NaN; lock fresh; flights: gate_flight.py          [Ricks lock hashes; phase2 gate]
  3 BLENDER    every layer over the range: FRESH, gate PASS, one PNG per frame, alpha present; flight motion in the lock
  4 COMPOSITE  final frames == recomputed base + layer x alpha from CURRENT inputs (hash-checked, so a stale input is caught); outside every layer's named mask the final frame == the base
  5 VIDEO      ffprobe size/fps/frames/no audio == manifest; decoded frames == composite PNGs (PSNR >= 35 dB: the video IS the composite); full-film video: tools/check_film.py   [Ricks check_film]
Only what Ricks lacked is new: stages 3-5 (they need the hybrid manifests). Writes <ep>/out/qa/qa_report.json + qa_report.md. Exit 1 on any FAIL. SKIPs are listed with their reason, never hidden."""
import argparse, hashlib, json, math, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent; ROOT = HERE.parent; sys.path.insert(0, str(HERE)); import layers as LY
from frames import check_range, is_full, scope_label, exact_set
R = []
def add(stage, name, ok, value="", note=""): R.append(dict(stage=stage, name=name, status=("PASS" if ok else "FAIL") if ok is not None else "SKIP", value=value, note=note))
def sha(p): return hashlib.sha1(Path(p).read_bytes()).hexdigest()
def dilate(m, n=1):
    for _ in range(n):
        o = m.copy(); o[1:] |= m[:-1]; o[:-1] |= m[1:]; o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]; o[1:, 1:] |= m[:-1, :-1]; o[:-1, :-1] |= m[1:, 1:]; o[1:, :-1] |= m[:-1, 1:]; o[:-1, 1:] |= m[1:, :-1]; m = o
    return m
def probe(mp4):
    p = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_entries", "stream=codec_type,width,height,r_frame_rate,nb_read_frames", "-of", "json", str(mp4)], capture_output=True, text=True); return json.loads(p.stdout)["streams"]
def decode(mp4, idx, W, H):
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(mp4), "-vf", "select=eq(n\\,%d)" % idx, "-vframes", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True); return np.frombuffer(p.stdout, np.uint8).reshape(H, W, 3)
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("ep"); ap.add_argument("--res", default="720x1280"); ap.add_argument("--no-film-check", action="store_true"); ap.add_argument("--frame-checks", action="store_true"); a = ap.parse_args()
    ep = Path(a.ep); W, H = map(int, a.res.split("x")); qa = ep / "out/qa"; qa.mkdir(parents=True, exist_ok=True)
    # ---- 1 PLAN
    p = subprocess.run([sys.executable, str(HERE / "film_plan.py"), "check", str(ep / "film.json")], capture_output=True, text=True); last = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else p.stderr[-200:]
    add("1 PLAN", "film_plan check: 0 FAIL", " 0 FAIL" in last, last.split(".")[0])
    for n in ("camera_baked.json", "performance_baked.json", "sound_events.json"): add("1 PLAN", "baked file " + n, (ep / "out/plan" / n).exists())
    mf = ep / "out/final/final_manifest.json"
    if not mf.exists(): add("5 VIDEO", "final_manifest.json exists (run tools/final_video.py)", False); return finish(ep, qa)
    M = json.load(open(mf)); f0, f1 = M["frames"]; N = len(json.load(open(ep / "out/plan/camera_baked.json"))["frames"])
    try: check_range(f0, f1, N); rng_ok = True
    except SystemExit as e: rng_ok = False; add("1 PLAN", "manifest frame range inside 0..N-1", False, "", str(e))
    if not rng_ok: return finish(ep, qa)
    add("1 PLAN", "scope", None, "", scope_label(f0, f1, N)); miss, extra = exact_set(ep / "out/final/frames", "f_", f0, f1); add("5 VIDEO", "exact frame set %d-%d (no missing, no extra)" % (f0, f1), not miss and not extra, "missing %s extra %s" % (miss[:5], extra[:5]))
    frames = list(range(f0, f1 + 1)); film = json.load(open(ep / "film.json")); fps = film["fps"]
    # ---- 2 THREEJS
    bad = []; lum = []
    for f in frames:
        sp = ep / "out/stills" / ("f_%05d.png" % f)
        if not sp.exists(): bad.append("%d missing" % f); continue
        try: im = np.asarray(Image.open(sp).convert("RGB"))
        except Exception as e: bad.append("%d unreadable (%s)" % (f, type(e).__name__)); continue
        if im.shape[:2] != (H, W): bad.append("%d size %s" % (f, im.shape[1::-1]))
        elif im.std() < 2.0: bad.append("%d blank (std %.2f)" % (f, im.std()))
        else: lum.append(float(im.mean()))
    add("2 THREEJS", "base stills: present, %dx%d, not blank" % (W, H), not bad, "%d frames" % len(frames), "; ".join(bad[:5]))
    stale = LY.lock_fresh(ep) if (ep / "out/lock/lock.json").exists() else ["no lock"]; add("2 THREEJS", "lock fresh (camera/performance/flights sha1 match the plan files)", not stale, "", ",".join(stale))
    fl = ep / "out/plan/flights_baked.json"
    if fl.exists():
        fb = json.load(open(fl)); hits = [v["hit"] for v in fb.values()]; inr = [f for f in frames if any(v["leave"] <= f <= v["hit"] for v in fb.values())]
        if inr:
            g = subprocess.run([sys.executable, str(ROOT / "phase2/gate_flight.py"), str(ep), "--stills", ",".join(map(str, inr))], capture_output=True, text=True); add("2 THREEJS", "flight gates (registration, hit equality, camera, lock) on the range", g.returncode == 0, g.stdout.strip().splitlines()[-1], g.stdout[-400:] if g.returncode else "")
        else: add("2 THREEJS", "flight gates", None, "", "no flight inside frames %d-%d" % (f0, f1))
    else: add("2 THREEJS", "flight gates", None, "", "film has no flights")
    # ---- 3 BLENDER
    for lid, (a0, a1) in M["layers"].items():
        od = ep / "out/layers" / lid; st = LY.status(str(ep), W, H)[lid]; add("3 BLENDER", "layer %s FRESH" % lid, st == "FRESH", st)
        rv = od / "review.json"; add("3 BLENDER", "layer %s reviewed: keep=true (creative decision recorded)" % lid, rv.exists() and json.load(open(rv)).get("keep") is True, str(json.load(open(rv)).get("by", "")) if rv.exists() else "no review.json")
        rp = json.load(open(od / "layer_report.json")); add("3 BLENDER", "layer %s gate PASS" % lid, rp["PASS"], json.dumps({k[:1]: v for k, v in rp["gates"].items()}))
        pngs = [f for f in range(a0, a1 + 1) if (od / ("layer_%05d.png" % f)).exists()]; add("3 BLENDER", "layer %s: one PNG per frame" % lid, len(pngs) == a1 - a0 + 1, "%d/%d" % (len(pngs), a1 - a0 + 1))
        al = [float((np.asarray(Image.open(od / ("layer_%05d.png" % f)).convert("RGBA"))[..., 3] > 0).mean()) for f in pngs[:: max(1, len(pngs) // 4)]]; add("3 BLENDER", "layer %s has alpha (not an empty layer)" % lid, min(al) > 0, "alpha coverage %s" % [round(x, 4) for x in al])
    if fl.exists():
        mo = ep / "out/lock/motion"; names = {n["name"] for q in mo.glob("*.json") for n in json.load(open(q))["nodes"].values()}; add("3 BLENDER", "flight objects are in the lock motion", all(("flight_" + k) in names for k in json.load(open(fl))), ",".join(sorted(x for x in names if x.startswith("flight_"))))
    # ---- 4 COMPOSITE
    fd = ep / "out/final/frames"; bad = []; outside = 0; maxo = 0
    for f in frames:
        inp = M["inputs"][str(f)]
        if sha(ep / "out/stills" / ("f_%05d.png" % f)) != inp["base"]: bad.append("%d base changed since assembly" % f); continue
        base = np.asarray(Image.open(ep / "out/stills" / ("f_%05d.png" % f)).convert("RGB")); fin = np.asarray(Image.open(fd / ("f_%05d.png" % f)).convert("RGB")); inp = M["inputs"][str(f)]
        if sha(ep / "out/stills" / ("f_%05d.png" % f)) != inp["base"]: bad.append("%d base changed since assembly" % f); continue
        exp = base; mask = np.zeros(base.shape[:2], bool)
        for lid, (a0, a1) in M["layers"].items():
            if a0 <= f <= a1:
                lp = ep / "out/layers" / lid / ("layer_%05d.png" % f)
                if sha(lp) != inp[lid]: bad.append("%d layer %s changed since assembly" % (f, lid)); continue
                b = base.astype(np.float32) / 255; L = np.asarray(Image.open(lp).convert("RGBA")).astype(np.float32) / 255; exp = (np.clip(b + L[..., :3] * L[..., 3:4], 0, 1) * 255 + .5).astype(np.uint8)
                mask |= dilate(np.asarray(Image.open(ep / "out/layers" / lid / ("idmask_%05d.png" % f)).convert("RGBA"))[..., 3] > 0, 1)
        d = np.abs(fin.astype(int) - exp.astype(int)).max()
        if d > 0: bad.append("%d final != recomputed composite (max %d)" % (f, d))
        o = np.abs(fin.astype(int) - base.astype(int)).max(axis=2)[~mask]; maxo = max(maxo, int(o.max()) if o.size else 0); outside += int((o > 0).sum())
    add("4 COMPOSITE", "final frames == base + layer x alpha from the CURRENT inputs (hash-checked)", not bad, "%d frames" % len(frames), "; ".join(bad[:5]))
    add("4 COMPOSITE", "outside every layer's named mask the final frame equals the base", outside == 0, "changed px %d, max diff %d" % (outside, maxo))
    # ---- 5 VIDEO
    mp4 = ep / "out/final/final.mp4"; s = probe(mp4); v = [x for x in s if x["codec_type"] == "video"]; au = [x for x in s if x["codec_type"] == "audio"]
    ok = bool(v) and (v[0]["width"], v[0]["height"]) == (W, H) and int(v[0]["nb_read_frames"]) == len(frames) and abs(eval(v[0]["r_frame_rate"]) - fps) < 0.01
    add("5 VIDEO", "ffprobe: %dx%d, %d frames, %g fps" % (W, H, len(frames), fps), ok, json.dumps([{k: x[k] for k in x if k != "codec_type"} for x in v]))
    add("5 VIDEO", "silent for now (no audio stream)", not au)
    pick = sorted(set([0, len(frames) // 2, len(frames) - 1] + [f - f0 for lid, (a0, a1) in M["layers"].items() for f in (a0, (a0 + a1) // 2, a1) if f0 <= f <= f1])); ps = []
    for i in pick:
        dv = decode(mp4, i, W, H).astype(float); fr_ = np.asarray(Image.open(fd / ("f_%05d.png" % (f0 + i))).convert("RGB")).astype(float); mse = ((dv - fr_) ** 2).mean(); ps.append(99.0 if mse == 0 else 10 * math.log10(255 ** 2 / mse))
    add("5 VIDEO", "decoded video frames == composite PNGs (PSNR >= 35 dB)", min(ps) >= 35, "min %.1f dB over frames %s" % (min(ps), [f0 + i for i in pick]))
    full = is_full(f0, f1, N)
    if a.no_film_check or not full: add("5 VIDEO", "check_film.py (camera, plan vs picture, frozen/flicker, faces)", None, "", "needs the full-film video (the plan numbers are whole-film); this video is frames %d-%d" % (f0, f1) if not full else "disabled")
    else:
        if not (ep / "out/plan/visibility.json").exists(): subprocess.run(["node", str(HERE.parent / "templates/threejs_film/render.mjs"), str(ep / "film.json"), "--visibility"], capture_output=True, text=True)   # Phase 7: check_film's face/caption gates need it (engine gap found by the first full-film run)
        c = subprocess.run([sys.executable, str(HERE / "check_film.py"), str(mp4), "--film", str(ep / "film.json"), "--out", str(qa / "film_check")], capture_output=True, text=True); add("5 VIDEO", "check_film.py on the final video", c.returncode == 0, c.stdout.strip().splitlines()[-1] if c.stdout.strip() else c.stderr[-200:])
    if a.frame_checks:
        c = subprocess.run(["node", str(HERE / "frame_checks/check.mjs"), str(ep / "film.json"), "--frames", "%d-%d" % (f0, f1)], capture_output=True, text=True); add("5 VIDEO", "frame_checks/check.mjs (head cut, body side, face covered, feet)", c.returncode == 0, c.stdout.strip().splitlines()[-1] if c.stdout.strip() else c.stderr[-200:])
    else: add("5 VIDEO", "frame_checks/check.mjs (head cut, body side, face covered, feet)", None, "", "needs the GPU render path; run with --frame-checks on a GPU machine")
    return finish(ep, qa)
def finish(ep, qa):
    fails = [r for r in R if r["status"] == "FAIL"]; md = ["# Hybrid QA: %s\n" % (("FAIL (%d)" % len(fails)) if fails else ("PASS (PARTIAL RANGE: not a full-film PASS)" if any(r["name"] == "scope" and "PARTIAL" in r["note"] for r in R) else "PASS"))] + ["- **%s** %s | %s | %s %s" % (r["status"], r["stage"], r["name"], r["value"], ("(" + r["note"] + ")") if r["note"] else "") for r in R]
    (qa / "qa_report.json").write_text(json.dumps({"PASS": not fails, "full_film": not any(r["name"] == "scope" and "PARTIAL" in r["note"] for r in R), "checks": R}, indent=1)); (qa / "qa_report.md").write_text("\n".join(md)); print("\n".join(md)); sys.exit(1 if fails else 0)
if __name__ == "__main__": main()
