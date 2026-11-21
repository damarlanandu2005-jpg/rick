#!/usr/bin/env python3
"""ONE command for an episode, creative steps separated from scripted ones (hybrid Phase 6).
  python3 tools/pipeline.py <ep> [--frames a-b|all] [--blender <blender>] [--gpu-backend opengl] [--renderer auto|cpu|gpu] [--accept-layers] [--res 720x1280]

CREATIVE (LLM / human; NOT run by this script; each leaves a file this script reads):
  C1 script + picture plan -> <ep>/film.json (the single plan table; layers[] and flights[] are entries in it)
  C2 look / layer decisions -> film.json layers[]; C3 layer review of out/layers/<id>/before_after_sheet -> out/layers/<id>/review.json {"keep": true|false, "by": ..., "note": ...}
SCRIPTED (deterministic, hash-cached, gated; stops at the first FAIL):
  1 plan   film_plan.py check (bakes camera/performance/flights/layers)      5 layers  tools/layers.py run per layer (one Blender process each, cached)
  2 base   three.js stills at 720x1280 (cached by a key of every input)        6 review  reads review.json (--accept-layers writes keep=true by '--accept-layers', flagged)
  3 lock   --export-lock (cached)                                             7 final   tools/final_video.py (base + kept layers -> mp4, silent)
  4 flight phase2/gate_flight.py when a flight is in the range               8 qa      tools/qa_hybrid.py (plan, three.js, blender, composite, video)
Writes <ep>/out/pipeline/pipeline_report.json (per stage: status, seconds, cache hit)."""
import argparse, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parent; sys.path.insert(0, str(HERE)); import layers as LY, final_video as FV
REPORT = []
def stage(name, kind, status, secs=0.0, note=""): REPORT.append(dict(stage=name, kind=kind, status=status, seconds=round(secs, 2), note=note)); print("%-8s %-9s %-6s %7.1fs  %s" % (name, kind, status, secs, note), flush=True)
def sh(cmd, log, env=None):
    t = time.perf_counter(); p = subprocess.run(cmd, capture_output=True, text=True, errors="replace", env=env); Path(log).write_text("$ " + " ".join(map(str, cmd)) + "\n" + p.stdout + "\n" + p.stderr); return p.returncode, time.perf_counter() - t, p
def sha_files(paths):
    h = hashlib.sha1()
    for p in sorted(paths):
        if Path(p).is_file(): h.update(str(Path(p).name).encode()); h.update(Path(p).read_bytes())
    return h.hexdigest()
def kit_key(ep, W, H, renderer):
    kit = ROOT / "templates/threejs_film"; files = [kit / n for n in ("film.js", "render.mjs", "render_gpu.mjs", "flights.js", "puppets.mjs", "look3d.mjs")] + list((kit / "sets").glob("*.js")) + list((ep / "sets").glob("*.js")) + [ep / "film.json"] + list((ep / "out/plan").glob("*_baked.json")) + list(ep.glob("*.json"))
    return sha_files(set(files)) + "|%dx%d|%s" % (W, H, renderer)
def done(code, name): 
    if code: finish(); sys.exit("STOP: stage %s FAILED (see out/pipeline/%s.log). Diagnose, fix, rerun; later stages were not run." % (name, name))
def finish():
    json.dump(REPORT, open(OUT / "pipeline_report.json", "w"), indent=1)
def main():
    global OUT
    ap = argparse.ArgumentParser(); ap.add_argument("ep"); ap.add_argument("--frames", default="all"); ap.add_argument("--blender"); ap.add_argument("--gpu-backend", default="opengl"); ap.add_argument("--renderer", default="auto", choices=["auto", "cpu", "gpu"])
    ap.add_argument("--accept-layers", action="store_true"); ap.add_argument("--res", default="720x1280"); a = ap.parse_args(); ep = Path(a.ep).resolve(); W, H = map(int, a.res.split("x")); OUT = ep / "out/pipeline"; OUT.mkdir(parents=True, exist_ok=True)
    film = ep / "film.json"; stage("C1-C3", "creative", "INPUT" if film.exists() else "MISSING", note="film.json (script, picture plan, layers[], flights[]) is the creative output; layer review = review.json")
    if not film.exists(): finish(); sys.exit("no film.json: the creative step has not produced the plan")
    node = ROOT / "templates/threejs_film"
    rc, t, p = sh([sys.executable, str(HERE / "film_plan.py"), "check", str(film)], OUT / "plan.log"); last = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else ""; stage("1 plan", "scripted", "PASS" if rc == 0 and " 0 FAIL" in last else "FAIL", t, last[:70]); done(0 if rc == 0 and " 0 FAIL" in last else 1, "plan")
    n = len(json.load(open(ep / "out/plan/camera_baked.json"))["frames"]); f0, f1 = (0, n - 1) if a.frames == "all" else map(int, a.frames.split("-")); frames = list(range(f0, f1 + 1))
    # ---- 2 base (cache key of every input; a changed key re-renders the whole range, nothing half-stale)
    rend = "gpu" if a.renderer == "gpu" else "cpu"; key = kit_key(ep, W, H, a.renderer); kp = ep / "out/stills/_base_key.json"; st = ep / "out/stills"; st.mkdir(parents=True, exist_ok=True)
    have = all((st / ("f_%05d.png" % f)).exists() for f in frames); fresh = kp.exists() and json.load(open(kp)).get("key") == key
    if have and fresh: stage("2 base", "scripted", "CACHE", 0, "%d frames" % len(frames))
    else:
        for q in st.glob("f_*.png"): q.unlink()
        script = "render_gpu.mjs" if a.renderer in ("gpu", "auto") else "render.mjs"; args = ["--frames", ("%d-%d" % (f0, f1)) if script == "render_gpu.mjs" else ",".join(map(str, frames)), "--scale", str(W / json.load(open(film)).get("size", [1080, 1920])[0])]
        rc, t, p = sh(["node", str(node / script), str(film)] + args, OUT / "base.log")
        if rc != 0 and a.renderer == "auto": script = "render.mjs"; rc, t2, p = sh(["node", str(node / script), str(film), "--frames", ",".join(map(str, frames)), "--scale", str(W / json.load(open(film)).get("size", [1080, 1920])[0])], OUT / "base_cpu_fallback.log"); t += t2; rend = "cpu(fallback)"
        elif rc == 0: rend = "gpu" if script == "render_gpu.mjs" else "cpu"
        ok = rc == 0 and all((st / ("f_%05d.png" % f)).exists() for f in frames); stage("2 base", "scripted", "PASS" if ok else "FAIL", t, "%d frames, %s, %.2f s/frame" % (len(frames), rend, t / max(1, len(frames)))); done(0 if ok else 1, "base"); kp.write_text(json.dumps({"key": key, "renderer": rend}))
    lk = ep / "out/lock/lock.json"; lkey = ep / "out/lock/_key.json"
    if lk.exists() and not LY.lock_fresh(ep) and lkey.exists() and json.load(open(lkey)).get("key") == key: stage("3 lock", "scripted", "CACHE", 0)
    else:
        rc, t, p = sh(["node", str(node / "render.mjs"), str(film), "--export-lock"], OUT / "lock.log"); stage("3 lock", "scripted", "PASS" if rc == 0 else "FAIL", t); done(rc, "lock"); lkey.write_text(json.dumps({"key": key}))
    fl = ep / "out/plan/flights_baked.json"
    if fl.exists():
        fb = json.load(open(fl)); inr = [f for f in range(f0, f1 + 1) if any(v["leave"] <= f < v["hit"] for v in fb.values())]
        if inr: rc, t, p = sh([sys.executable, str(ROOT / "phase2/gate_flight.py"), str(ep), "--stills", ",".join(map(str, inr))], OUT / "flight.log"); stage("4 flight", "scripted", "PASS" if rc == 0 else "FAIL", t, p.stdout.strip().splitlines()[-1]); done(rc, "flight")
        else: stage("4 flight", "scripted", "SKIP", 0, "no flight in range")
    else: stage("4 flight", "scripted", "SKIP", 0, "no flights")
    LP = ep / "out/plan/layers_baked.json"; lay = {k: v for k, v in (json.load(open(LP)) if LP.exists() else {}).items() if not (v["frames"][1] < f0 or v["frames"][0] > f1)}
    for lid, S in lay.items():
        if not a.blender: stage("5 layers", "scripted", "SKIP", 0, "%s: no --blender (layer will be omitted from the final)" % lid); continue
        if S["frames"][0] < f0 or S["frames"][1] > f1: stage("5 layers", "scripted", "FAIL", 0, "%s frames %s are not inside the rendered range" % (lid, S["frames"])); done(1, "layers")
        t = time.perf_counter(); vok, vh = LY.visible(str(ep), lid); stage("5a visible", "scripted", "PASS" if vok else "FAIL", time.perf_counter() - t, "%s: named objects seen, rays per frame %s" % (lid, vh)); done(0 if vok else 1, "layers")
        was = LY.status(str(ep), W, H).get(lid); t = time.perf_counter()
        try: r = LY.run(str(ep), lid, a.blender, a.gpu_backend, W, H)
        except SystemExit as e: stage("5 layers", "scripted", "FAIL", time.perf_counter() - t, "%s: %s" % (lid, e)); done(1, "layers")
        stage("5 layers", "scripted", ("CACHE" if was == "FRESH" else "PASS") if r["PASS"] else "FAIL", time.perf_counter() - t, "%s gates %s" % (lid, json.dumps({k[:1]: v for k, v in r["gates"].items()}))); done(0 if r["PASS"] else 1, "layers")
        rv = ep / "out/layers" / lid / "review.json"
        if a.accept_layers and not rv.exists(): rv.write_text(json.dumps({"keep": True, "by": "--accept-layers (not a creative review: flagged)", "note": "auto-accepted for a test run"}))
        stage("6 review", "creative", "KEEP" if rv.exists() and json.load(open(rv)).get("keep") else "OMIT", 0, "%s: %s" % (lid, "review.json " + (json.load(open(rv)).get("by", "") if rv.exists() else "missing (layer will be omitted: Ricks keeps a layer only if it clearly adds)")))
    t = time.perf_counter()
    try: mp4, M = FV.assemble(ep, f0, f1, W, H); stage("7 final", "scripted", "PASS", time.perf_counter() - t, "%s, layers %s" % (mp4.name, list(M["layers"])))
    except SystemExit as e: stage("7 final", "scripted", "FAIL", time.perf_counter() - t, str(e)); done(1, "final")
    rc, t, p = sh([sys.executable, str(HERE / "qa_hybrid.py"), str(ep), "--res", a.res], OUT / "qa.log"); stage("8 qa", "scripted", "PASS" if rc == 0 else "FAIL", t, ("; ".join(l for l in p.stdout.splitlines() if l.startswith("- **FAIL**")) or "all checks PASS")[:200]); finish()
    if rc: sys.exit("STOP: QA FAILED (see %s)" % (ep / "out/qa/qa_report.md"))
    print("\nFINAL VIDEO:", ep / "out/final/final.mp4")
if __name__ == "__main__": main()
