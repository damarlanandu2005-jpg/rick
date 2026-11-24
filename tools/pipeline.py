#!/usr/bin/env python3
"""R6: THIN, DETERMINISTIC ORCHESTRATION of the existing Ricks production methodology. It invents nothing: stories, scripts, words, picture plans, look bibles, character/asset choices, film.json, the judge and the human approval are
EXPLICIT creative inputs (missing or stale = FAIL, never regenerated); every other stage calls an existing tool (film_plan.py, creative_gates.py, review.py, approval.py, assets.py, characters.py, render.mjs, lock_stamp.py, layers.py, final_video.py, qa_hybrid.py).
  python3 tools/pipeline.py <ep> [--frames a-b|all] [--build-review] [--blender <blender>] [--gpu-backend opengl] [--renderer auto|cpu|gpu] [--accept-layers] [--res 720x1280] [--unapproved-test-run]

STAGE GRAPH (authoritative order; the first failure/wait stops the run, nothing downstream runs, no expensive render):
  0 inputs  -> 1 plan -> G1..G7 -> 2 storyboard -> 3 animatic -> 4 judge -> G8 -> HUMAN APPROVAL (G9) -> 5 assets -> 6 lock (+cards, freeze) -> 7 base (three.js, the only expensive render) -> flight -> 8 layers (optional Blender)
  -> 9 final (composite + mp4) -> 10 QA -> 11 sound (R8: validate, mix, mux; SKIP for a film with no audio) -> 12 delivery QA (decoded MP4).   Each stage records owner, input/output hashes, cache key, status, seconds, failure reason in out/pipeline/stages.json; one manifest per run in out/pipeline/production_manifest.json.
CACHE / RESUME: the base render and the lock are cached by a key of every input INCLUDING the approval, the lock and the mode; a changed upstream artifact changes the key and invalidates everything below it. storyboard/animatic/judge are never regenerated when valid, never faked when stale.
MODES: production (default: production:true, needs judge + approval + lock + QA) vs --unapproved-test-run (named test mode, production:false, stamps NOT_A_PRODUCTION_RENDER.txt). A TEST_FIXTURE_ONLY episode runs every gate for real but is stamped production:false.
CREATIVE (LLM / human; NOT run by this script): C1 script + picture plan -> film.json; C2 look / layer decisions -> film.json layers[]; C3 layer review -> out/layers/<id>/review.json {"keep": true|false, "by": ..., "note": ...}; the independent judge; the human approval."""
import argparse, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parent; sys.path.insert(0, str(HERE)); import layers as LY, final_video as FV
from frames import film_frame_count, parse_range, is_full, scope_label
REPORT = []; ORDER = ["0 inputs", "1 plan", "G1", "G2", "G3", "G4", "G5", "G6", "G7", "2 storyboard", "3 animatic", "4 judge", "G8", "G9", "5 assets", "6 lock", "6b cards", "6c lock freeze", "7 base", "8 flight", "8 layers", "9 final", "10 qa"]
DELIVERY = ["11 sound", "12 delivery qa"]   # R8: the audio delivery stages come AFTER the R6 sequence above (which ends at the silent picture QA)
TEST_ENV = "RICKS_UNAPPROVED_TEST_RUN"; OUT = None; EP = None; MODE = {"production": True, "test_mode": False, "fixture": False}; RUN = {"expensive_render_executed": False, "base_frames_rendered": 0, "failed_stage": None, "waiting": None}
def stage(name, owner, status, secs=0.0, note="", inputs=None, outputs=None, key=None, reason=None):
    REPORT.append(dict(stage=name, owner=owner, status=status, seconds=round(secs, 2), note=note, inputs=inputs or {}, outputs=outputs or {}, cache_key=key, failure_reason=reason if reason is not None else (note if status in ("FAIL", "WAIT") else None)))
    print("%-14s %-24s %-8s %7.1fs  %s" % (name, owner[:24], status, secs, note[:150]), flush=True)
def sh(cmd, log, env=None):
    t = time.perf_counter(); p = subprocess.run(cmd, capture_output=True, text=True, errors="replace", env=env); Path(log).write_text("$ " + " ".join(map(str, cmd)) + "\n" + p.stdout + "\n" + p.stderr); return p.returncode, time.perf_counter() - t, p
def sha1(p): return hashlib.sha1(Path(p).read_bytes()).hexdigest() if Path(p).is_file() else None
def sha_files(paths):
    h = hashlib.sha1()
    for p in sorted(paths):
        if Path(p).is_file(): h.update(str(Path(p).name).encode()); h.update(Path(p).read_bytes())
    return h.hexdigest()
def kit_key(ep, W, H, renderer):
    kit = ROOT / "templates/threejs_film"; files = [kit / n for n in ("film.js", "render.mjs", "render_gpu.mjs", "flights.js", "puppets.mjs", "look3d.mjs")] + list((kit / "sets").glob("*.js")) + list((ep / "sets").glob("*.js")) + [ep / "film.json", ep / "out/lock/lock.json"] + list((ep / "out/plan").glob("*_baked.json")) + list(ep.glob("*.json"))
    return sha_files(set(files)) + "|%dx%d|%s|%s" % (W, H, renderer, "test" if MODE["test_mode"] else "production")   # mode is part of the key: a test run's stills can never be reused as production
def commit():
    r = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True); d = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=no"], capture_output=True, text=True)
    return (r.stdout.strip() or None), bool(d.stdout.strip())
def manifest(ep, final_status):
    """ONE manifest per run: evidence, not a plan (no second schema). Hashes are of the files as they are NOW."""
    import approval as AP, characters as CH, reference_link as RL; c = ep / "creative"; cm, dirty = commit(); H = AP.current(ep) if (ep / "film.json").is_file() else {}; pl = ep / "out/plan"; fm = ep / "out/final/final_manifest.json"; qa = ep / "out/qa/qa_report.json"
    bp = ROOT / "docs/PRODUCTION_BLUEPRINT_LOCKED.md"; vf = ROOT / "ricks_reference/VERSION"
    M = dict(run_id=hashlib.sha1((str(time.time()) + str(ep)).encode()).hexdigest()[:12], film_id=(json.load(open(ep / "film.json")).get("title") if (ep / "film.json").is_file() else None), production=bool(MODE["production"] and final_status == "PASS"), mode="production" if MODE["production"] else ("TEST_FIXTURE_ONLY" if MODE["fixture"] else "unapproved-test-run"), declared_production=MODE["production"], status=final_status,
             commit=cm, working_tree_dirty=dirty, blueprint_sha1=sha1(bp), blueprint_status="LOCKED" if "STATUS: LOCKED" in bp.read_text() else None, ricks_version=(vf.read_text().strip() if vf.is_file() else None), ricks_reference_files=len(list((ROOT / "ricks_reference").glob("*.md"))) if (ROOT / "ricks_reference").is_dir() else 0,
             hashes=dict(reference=H.get("reference_board_sha1"), script=sha1(c / "SCRIPT.md"), words=sha1(AP.CG._words_path(ep)) if (ep / "film.json").is_file() else None, picture_plan=H.get("picture_plan_sha1"), look_bible=H.get("look_bible_sha1"), characters=H.get("character_sheets_sha1"), assets=H.get("asset_versions"), film_json=H.get("plan_sha1"), bake=H.get("baked_sha1"), storyboard=H.get("storyboard_sha1"), animatic=H.get("animatic_sha1"), judge=sha1(c / "JUDGE.json"), approval=sha1(ep / "approval.json"), lock=sha1(ep / "out/lock/lock.json")),
             render=dict(expensive_render_executed=RUN["expensive_render_executed"], base_frames_rendered=RUN["base_frames_rendered"], stills_dir_frames=len(list((ep / "out/stills").glob("f_*.png"))) if (ep / "out/stills").is_dir() else 0),
             final_mp4_sha1=sha1(ep / "out/final/final.mp4"), final_manifest_production=(json.load(open(fm)).get("production") if fm.is_file() else None), qa=(dict(PASS=json.load(open(qa)).get("PASS"), full_film=json.load(open(qa)).get("full_film")) if qa.is_file() else None), failed_stage=RUN["failed_stage"], waiting_for=RUN["waiting"], stages=REPORT)
    (OUT / "production_manifest.json").write_text(json.dumps(M, indent=1)); return M
def finish(status="FAIL"):
    json.dump(REPORT, open(OUT / "pipeline_report.json", "w"), indent=1); (OUT / "stages.json").write_text(json.dumps(REPORT, indent=1)); manifest(EP, status)
def downstream(name): S_ = ORDER + DELIVERY; return S_[S_.index(name) + 1:] if name in S_ else []
def stop(name, status, why, code=1):
    """The first meaningful failure (or wait) stops everything: report the failed stage, the affected downstream stages and whether any expensive render happened."""
    RUN["failed_stage" if status == "FAIL" else "waiting"] = name; ds = [x for x in downstream(name)]
    print("\n%s at %s: %s\nSTOPPED. Not run (affected downstream): %s\nExpensive render happened: %s" % ("FAILED" if status == "FAIL" else "WAITING", name, why, ", ".join(ds) or "-", "YES" if RUN["expensive_render_executed"] else "NO"), flush=True)
    finish("FAIL" if status == "FAIL" else "WAITING"); sys.exit(code)
def done(code, name, why=""):
    if code: stop(name, "FAIL", why or "see out/pipeline/%s.log" % name)
def main():
    global OUT, EP
    ap = argparse.ArgumentParser(); ap.add_argument("ep"); ap.add_argument("--frames", default="all"); ap.add_argument("--blender"); ap.add_argument("--gpu-backend", default="opengl"); ap.add_argument("--renderer", default="auto", choices=["auto", "cpu", "gpu"])
    ap.add_argument("--accept-layers", action="store_true"); ap.add_argument("--build-review", action="store_true", help="when the storyboard / animatic do not exist yet, make them with the existing review.py (cheap three.js preview renders); never makes a judge result or an approval")
    ap.add_argument("--unapproved-test-run", action="store_true", help="NAMED TEST MODE (legacy example films / tests only): skip G1-G9; everything is stamped production:false and NOT_A_PRODUCTION_RENDER.txt"); ap.add_argument("--res", default="720x1280"); a = ap.parse_args()
    if a.accept_layers and not a.unapproved_test_run: sys.exit("REFUSED: --accept-layers would approve a creative layer decision from a flag. A layer is kept only by a human/director review.json; the flag exists for the named --unapproved-test-run (production:false) only.")
    ep = Path(a.ep).resolve(); EP = ep; W, H = map(int, a.res.split("x")); OUT = ep / "out/pipeline"; OUT.mkdir(parents=True, exist_ok=True)
    import approval as AP, creative_gates as CG, review as RV, lock_stamp as LS, reference_link as RL, assets as AS
    MODE["test_mode"] = a.unapproved_test_run; MODE["fixture"] = AP.is_test_fixture(ep); MODE["production"] = not a.unapproved_test_run and not MODE["fixture"]
    if a.unapproved_test_run: os.environ[TEST_ENV] = "1"; (OUT / "NOT_A_PRODUCTION_RENDER.txt").write_text("rendered with --unapproved-test-run: creative gates and approval.json were NOT enforced; production:false\n")
    else:
        os.environ.pop(TEST_ENV, None)      # R6L: a stray environment flag can never turn a production (or fixture) run into an unapproved one
        (OUT / "NOT_A_PRODUCTION_RENDER.txt").unlink(missing_ok=True)
        if MODE["fixture"]: (OUT / "TEST_FIXTURE_ONLY.txt").write_text("TEST_FIXTURE_ONLY: every gate enforced for real, but the fixture is synthetic; production:false, never creative approval\n")
    film = ep / "film.json"; node = ROOT / "templates/threejs_film"; c = ep / "creative"
    # ---- 0 inputs: the creative artifacts are explicit inputs; the orchestrator never regenerates them. Missing = FAIL.
    t = time.perf_counter(); fj = json.load(open(film)) if film.is_file() else {}
    arts = {"reference": c / "reference_board.json", "script": c / "SCRIPT.md", "words": (ep / fj.get("words", "voice/words.json")), "picture_plan": c / "PICTURE_PLAN.md", "look_bible": c / "LOOK_BIBLE.md", "character_selection": c / "characters.json", "character_production": c / "character_production.json", "film.json": film}
    miss = [k for k, v in arts.items() if not v.is_file()]; ins = {k: sha1(v) for k, v in arts.items()}; ins["reference"] = RL.board_sha(ep) if arts["reference"].is_file() else None
    if a.unapproved_test_run: miss = [k for k in miss if k == "film.json"]      # test mode: legacy example films carry only film.json
    stage("0 inputs", "Ricks creative workflow", "FAIL" if miss else "INPUT", time.perf_counter() - t, ("missing creative artifact(s): %s (the orchestrator never regenerates them)" % ", ".join(miss)) if miss else "%d creative artifacts present" % len([v for v in ins.values() if v]), inputs=ins)
    if miss: stop("0 inputs", "FAIL", "missing creative artifact(s): " + ", ".join(miss))
    rc, t, p = sh([sys.executable, str(HERE / "film_plan.py"), "check", str(film)], OUT / "plan.log"); last = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else ""; ok = rc == 0 and " 0 FAIL" in last
    stage("1 plan", "Ricks film_plan (bake)", "PASS" if ok else "FAIL", t, last[:90], inputs={"film.json": ins["film.json"], "words": ins["words"]}, outputs={n: sha1(ep / "out/plan" / n) for n in ("camera_baked.json", "performance_baked.json")}); done(0 if ok else 1, "1 plan", last[:120])
    try: n = film_frame_count(ep); f0, f1 = parse_range(a.frames, n)
    except SystemExit as e: stop("1 plan", "FAIL", str(e))
    frames = list(range(f0, f1 + 1)); stage("0 scope", "R1 frame semantics", "FULL" if is_full(f0, f1, n) else "PARTIAL", 0, scope_label(f0, f1, n))   # valid indices 0..N-1; 0-N is an error; a partial range is labelled partial
    if not a.unapproved_test_run:
        # ---- G1..G7 (existing creative_gates.py, in order, stop at the first FAIL)
        R = CG.run(ep); G = {r["gate"]: r for r in R}
        for g in ("G1", "G2", "G3", "G4", "G5", "G6", "G7"):
            r = G[g]; stage(g, "creative_gates " + r["name"], r["status"], 0, r["note"][:140]); (r["status"] == "FAIL") and stop(g, "FAIL", r["note"][:200])
        # ---- storyboard -> animatic -> judge -> G8: the review evidence (existing review.py). Valid ones are reused; missing ones are built only with --build-review; a stale one is a FAIL (a changed work needs an owner `review.py new-version`)
        for nm, fn, cmd in (("2 storyboard", RV.validate_storyboard, "storyboard"), ("3 animatic", RV.validate_animatic, "animatic")):
            t = time.perf_counter(); _, bad = fn(ep); fname = "STORYBOARD.json" if cmd == "storyboard" else "ANIMATIC.json"
            if bad and not (c / fname).is_file() and a.build_review:
                rc, t2, p = sh([sys.executable, str(HERE / "review.py"), cmd, str(ep), "--builder", "pipeline-builder-ctx"], OUT / ("%s.log" % cmd)); t += t2; _, bad = fn(ep)
            stage(nm, "Ricks/three.js (review.py)", "FAIL" if bad else "PASS", time.perf_counter() - t, ("; ".join(bad))[:150] if bad else "valid and current", outputs={fname: sha1(c / fname)}); bad and stop(nm, "FAIL", "; ".join(bad)[:220] + ("" if (c / fname).is_file() else " (make it: python3 tools/review.py %s <ep>, or rerun with --build-review)" % cmd))
        J = c / "JUDGE.json"
        if not J.is_file(): stage("4 judge", "Ricks independent judge", "WAIT", 0, "no judge record: run the fresh-context storyboard-judge / studio-director (review.py judge-brief)"); stop("4 judge", "WAIT", "WAITING FOR THE INDEPENDENT JUDGE (G8); the orchestrator never judges", 2)
        jr = json.load(open(J)); stage("4 judge", "Ricks independent judge", "PASS" if jr.get("result") == "PASS" else "FAIL", 0, "result %s, min panel %s, threshold %s" % (jr.get("result"), min([v.get("score", 0) if isinstance(v, dict) else v for v in (jr.get("panels") or {"-": 0}).values()]), jr.get("threshold")), outputs={"JUDGE.json": sha1(J)}); jr.get("result") != "PASS" and stop("4 judge", "FAIL", "the independent judge result is %s (G8): no approval can follow" % jr.get("result"))
        r = G["G8"]; stage("G8", "review.py g8", r["status"], 0, r["note"][:150]); r["status"] != "PASS" and stop("G8", "FAIL", r["note"][:200])
        # ---- G9: HUMAN approval. Never created here.
        t = time.perf_counter(); bad = AP.check(ep)
        if bad and not (ep / "approval.json").is_file(): stage("G9", "human approval", "WAIT", time.perf_counter() - t, bad[0][:100]); stop("G9", "WAIT", "WAITING FOR HUMAN APPROVAL (python3 tools/approval.py create <ep> --reviewer NAME --approve ...); no lock, no render", 2)
        stage("G9", "human approval (approval.py)", "FAIL" if bad else "PASS", time.perf_counter() - t, "; ".join(x.strip("- ") for x in bad[:3])[:160] if bad else "valid and fresh", inputs={"approval.json": sha1(ep / "approval.json")}); bad and stop("G9", "FAIL", "; ".join(bad[:3]))
    else: stage("G1-G9", "TEST MODE", "BYPASS", 0, "NOT A PRODUCTION RENDER (--unapproved-test-run): creative gates, judge and approval were NOT enforced; production:false")
    # ---- 5 assets (existing assets.py resolve; production needs APPROVED assets, test mode may use a candidate)
    rc, t, p = sh([sys.executable, str(HERE / "assets.py"), "resolve", str(ep)] + (["--allow-candidate"] if a.unapproved_test_run else []), OUT / "assets.log"); stage("5 assets", "Blender/GLB registry (assets.py)", "PASS" if rc == 0 else "FAIL", t, " | ".join(l[:80] for l in p.stdout.splitlines()[:2])[:160], outputs={"assets_baked.json": sha1(ep / "out/plan/assets_baked.json")}); done(rc, "5 assets", p.stdout.strip()[:160])
    rend = "gpu" if a.renderer == "gpu" else "cpu"; key = kit_key(ep, W, H, a.renderer)
    # ---- 6 lock (existing --export-lock; refuses without a valid approval) BEFORE the final three.js base render
    lk = ep / "out/lock/lock.json"; lkey = ep / "out/lock/_key.json"; lkk = hashlib.sha1((sha_files([film, ep / "approval.json"] + list((ep / "out/plan").glob("*_baked.json"))) + str(MODE["test_mode"])).encode()).hexdigest()
    if lk.exists() and not LY.lock_fresh(ep) and lkey.exists() and json.load(open(lkey)).get("key") == lkk: stage("6 lock", "existing lock (render.mjs)", "CACHE", 0, "", key=lkk, outputs={"lock.json": sha1(lk)})
    else:
        rc, t, p = sh(["node", str(node / "render.mjs"), str(film), "--export-lock"], OUT / "lock.log"); stage("6 lock", "existing lock (render.mjs)", "PASS" if rc == 0 else "FAIL", t, "" if rc == 0 else (p.stdout + p.stderr).strip().splitlines()[-1][:140], key=lkk, outputs={"lock.json": sha1(lk)}); done(rc, "6 lock", (p.stdout + p.stderr).strip()[-200:]); lkey.write_text(json.dumps({"key": lkk}))
    if not a.unapproved_test_run:   # R3: the cards the lock drew must be the approved character cards, byte for byte
        rc, t, p = sh([sys.executable, str(HERE / "characters.py"), "check-lock", str(ep)], OUT / "character_lock.log"); stage("6b cards", "characters.py", "PASS" if rc == 0 else "FAIL", t, " | ".join(l.strip("- ") for l in p.stdout.splitlines()[1:3])[:140]); done(rc, "6b cards", p.stdout.strip()[:160])
        rc, t, p = sh([sys.executable, str(HERE / "lock_stamp.py"), "stamp", str(ep)], OUT / "lock_stamp.log"); rc2, t2, p2 = sh([sys.executable, str(HERE / "lock_stamp.py"), "check", str(ep)], OUT / "lock_check.log")
        stage("6c lock freeze", "lock_stamp.py", "PASS" if rc == 0 and rc2 == 0 else "FAIL", t + t2, " | ".join(l.strip("- ") for l in (p.stdout + p2.stdout).splitlines()[:2])[:160], outputs={"lock.json": sha1(lk)}); done(rc or rc2, "6c lock freeze", (p.stdout + p2.stdout).strip()[:200])
    key = kit_key(ep, W, H, a.renderer)    # the key now includes the frozen lock
    # ---- 7 base: the only expensive render. Cached by a key of every input; a changed key re-renders the whole range, nothing half-stale. The renderer itself refuses without approval + lock.
    kp = ep / "out/stills/_base_key.json"; st = ep / "out/stills"; st.mkdir(parents=True, exist_ok=True)
    have = all((st / ("f_%05d.png" % f)).exists() for f in frames); fresh = kp.exists() and json.load(open(kp)).get("key") == key
    if have and fresh: stage("7 base", "three.js (final base)", "CACHE", 0, "%d frames" % len(frames), key=key)
    else:
        for q in st.glob("f_*.png"): q.unlink()
        script = "render_gpu.mjs" if a.renderer in ("gpu", "auto") else "render.mjs"; sc = W / json.load(open(film)).get("size", [1080, 1920])[0]; args = ["--frames", ("%d-%d" % (f0, f1)) if script == "render_gpu.mjs" else ",".join(map(str, frames)), "--scale", str(sc)]
        RUN["expensive_render_executed"] = True; rc, t, p = sh(["node", str(node / script), str(film)] + args, OUT / "base.log")
        if rc != 0 and a.renderer == "auto" and "REFUSED" not in p.stdout + p.stderr: script = "render.mjs"; rc, t2, p = sh(["node", str(node / script), str(film), "--frames", ",".join(map(str, frames)), "--scale", str(sc)], OUT / "base_cpu_fallback.log"); t += t2; rend = "cpu(fallback)"
        elif rc == 0: rend = "gpu" if script == "render_gpu.mjs" else "cpu"
        ok = rc == 0 and all((st / ("f_%05d.png" % f)).exists() for f in frames); RUN["base_frames_rendered"] = len([f for f in frames if (st / ("f_%05d.png" % f)).exists()])
        stage("7 base", "three.js (final base)", "PASS" if ok else "FAIL", t, "%d frames, %s, %.2f s/frame" % (len(frames), rend, t / max(1, len(frames))) if ok else (p.stdout + p.stderr).strip().splitlines()[-1][:140], key=key); done(0 if ok else 1, "7 base", (p.stdout + p.stderr)[-200:]); kp.write_text(json.dumps({"key": key, "renderer": rend}))
    fl = ep / "out/plan/flights_baked.json"
    if fl.exists():
        fb = json.load(open(fl)); inr = [f for f in range(f0, f1 + 1) if any(v["leave"] <= f < v["hit"] for v in fb.values())]
        if inr: rc, t, p = sh([sys.executable, str(ROOT / "phase2/gate_flight.py"), str(ep), "--stills", ",".join(map(str, inr))], OUT / "flight.log"); stage("8 flight", "phase2/layers (optional)", "PASS" if rc == 0 else "FAIL", t, p.stdout.strip().splitlines()[-1]); done(rc, "flight")
        else: stage("8 flight", "phase2/layers (optional)", "SKIP", 0, "no flight in range")
    else: stage("8 flight", "phase2/layers (optional)", "SKIP", 0, "no flights")
    LP = ep / "out/plan/layers_baked.json"; lay = {k: v for k, v in (json.load(open(LP)) if LP.exists() else {}).items() if not (v["frames"][1] < f0 or v["frames"][0] > f1)}
    for lid, S in lay.items():
        if not a.blender: stage("8 layers", "phase2/layers (optional)", "SKIP", 0, "%s: no --blender (layer will be omitted from the final)" % lid); continue
        if S["frames"][0] < f0 or S["frames"][1] > f1: stage("8 layers", "phase2/layers (optional)", "FAIL", 0, "%s frames %s are not inside the rendered range" % (lid, S["frames"])); done(1, "layers")
        t = time.perf_counter(); vok, vh = LY.visible(str(ep), lid); stage("8a visible", "phase2/layers (optional)", "PASS" if vok else "FAIL", time.perf_counter() - t, "%s: named objects seen, rays per frame %s" % (lid, vh)); done(0 if vok else 1, "layers")
        was = LY.status(str(ep), W, H).get(lid); t = time.perf_counter()
        try: r = LY.run(str(ep), lid, a.blender, a.gpu_backend, W, H)
        except SystemExit as e: stage("8 layers", "phase2/layers (optional)", "FAIL", time.perf_counter() - t, "%s: %s" % (lid, e)); done(1, "layers")
        stage("8 layers", "phase2/layers (optional)", ("CACHE" if was == "FRESH" else "PASS") if r["PASS"] else "FAIL", time.perf_counter() - t, "%s gates %s" % (lid, json.dumps({k[:1]: v for k, v in r["gates"].items()}))); done(0 if r["PASS"] else 1, "layers")
        rv = ep / "out/layers" / lid / "review.json"
        if a.accept_layers and not rv.exists(): rv.write_text(json.dumps({"keep": True, "by": "--accept-layers (not a creative review: flagged)", "note": "auto-accepted for a test run"}))
        stage("8b review", "human/director review.json", "KEEP" if rv.exists() and json.load(open(rv)).get("keep") else "OMIT", 0, "%s: %s" % (lid, "review.json " + (json.load(open(rv)).get("by", "") if rv.exists() else "missing (layer will be omitted: Ricks keeps a layer only if it clearly adds)")))
    t = time.perf_counter(); fin = ep / "out/final/final.mp4"
    try: mp4, M = FV.assemble(ep, f0, f1, W, H); stage("9 final", "existing compositor + ffmpeg", "PASS", time.perf_counter() - t, "%s, layers %s, production:%s" % (mp4.name, list(M["layers"]), M["production"]), outputs={"final.mp4": sha1(mp4), "final_manifest.json": sha1(ep / "out/final/final_manifest.json")})
    except SystemExit as e: stage("9 final", "existing compositor + ffmpeg", "FAIL", time.perf_counter() - t, str(e)); done(1, "9 final", str(e))
    if a.unapproved_test_run:
        fm = ep / "out/final/final_manifest.json"; Mm = json.load(open(fm)); Mm.update(production=False, mode="unapproved-test-run"); fm.write_text(json.dumps(Mm, indent=1))
    rc, t, p = sh([sys.executable, str(HERE / "qa_hybrid.py"), str(ep), "--res", a.res], OUT / "qa.log"); stage("10 qa", "Ricks QA + enforcement (qa_hybrid.py)", "PASS" if rc == 0 else "FAIL", t, ("; ".join(l for l in p.stdout.splitlines() if l.startswith("- **FAIL**")) or "all checks PASS")[:200], outputs={"qa_report.json": sha1(ep / "out/qa/qa_report.json")})
    if rc: stop("10 qa", "FAIL", "QA FAILED (see %s)" % (ep / "out/qa/qa_report.md"))
    # R8: audio AFTER the approved, locked, rendered and QA'd picture: validate -> mix -> mux (video stream copied) -> decoded delivery QA. A film with no "audio" block stays silent (SKIP).
    import audio as AU; t = time.perf_counter(); cfg, _F = AU.config(ep); dlv = ep / "out/final/final.mp4"
    full = json.load(open(ep / "out/final/final_manifest.json")).get("frames") == [0, AU.film_frames(ep) - 1]
    if cfg is not None and not full: stage("11 sound", "R8 audio layer (tools/audio.py; cues from Ricks film.json sound)", "SKIP", 0, "PARTIAL range: a delivery with audio needs the whole film (never a full PASS)")
    elif cfg is None: stage("11 sound", "R8 audio layer (tools/audio.py; cues from Ricks film.json sound)", "SKIP", 0, "film.json declares no audio: the delivery is the silent final.mp4")
    else:
        try: dv, A = AU.mux(ep)
        except SystemExit as e: stage("11 sound", "R8 audio layer (tools/audio.py; cues from Ricks film.json sound)", "FAIL", time.perf_counter() - t, str(e)[:300]); stop("11 sound", "FAIL", str(e)[:300])
        stage("11 sound", "R8 audio layer (tools/audio.py; cues from Ricks film.json sound)", "PASS", time.perf_counter() - t, "%d events, mix peak %s dBFS, rms %s dBFS, production:%s" % (len(A["events"]), A["mix"]["peak_dbfs"], A["mix"]["rms_dbfs"], A["production"]),
              inputs=dict(A["inputs"], **{"final.mp4": sha1(ep / "out/final/final.mp4")}), outputs={"mix.wav": A["mix"]["sha1"], "final_video.mp4": A["delivery"]["sha1"]})
        t = time.perf_counter(); R = AU.qa(ep); bad = [k for k, ok, _ in R if not ok]
        stage("12 delivery qa", "R8 decoded delivery QA (tools/audio.py qa)", "PASS" if not bad else "FAIL", time.perf_counter() - t, ("; ".join(bad) or "%d checks PASS on the decoded MP4" % len(R))[:300], outputs={"final_video.mp4": A["delivery"]["sha1"]})
        if bad: stop("12 delivery qa", "FAIL", "delivery QA FAILED: " + "; ".join(bad)[:300])
        dlv = dv
    finish("PASS"); print("\nFINAL VIDEO:", dlv, "(production:%s)" % ("true" if MODE["production"] else "false"))
if __name__ == "__main__": main()
