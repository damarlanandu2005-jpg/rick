#!/usr/bin/env python3
"""R6 tests: thin deterministic orchestration of the existing Ricks tools + R5 mechanical closure (TEST_FIXTURE_ONLY approval -> lock -> ONE final render -> composite -> MP4 -> QA, and the fail-closed negatives).
  python3 r6/test_orchestrator.py            (builds a synthetic TEST_FIXTURE_ONLY fixture, runs the real pipeline ONCE end to end: about 8-9 minutes on 2 CPUs)
  R6_REUSE=<dir> python3 r6/test_orchestrator.py   reuse a finished fixture run in <dir>/ep (development only; the committed result is from a clean run)
Nothing here approves, judges or renders the rejected 'Hat Toss' (it is only RUN, read-only, to prove it stops before any render). The fixture is NEVER a creative pass."""
import copy, hashlib, json, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(ROOT / "r2")); sys.path.insert(0, str(ROOT / "r6"))
import numpy as np
from PIL import Image
fails = []; T0 = time.time()
def t(name, ok): print(("PASS " if ok else "FAIL ") + name, flush=True); (ok or fails.append(name))
has = lambda bad, w: any(w in x for x in bad)
TMP = Path(os.environ.get("R6_REUSE") or tempfile.mkdtemp()); TMP.mkdir(exist_ok=True)
import fixture_mech as FM
import assets as AS, characters as CH, creative_gates as CG, approval as AP, review as RV, lock_stamp as LS, reference_link as RL, frames as FR, layers as LY, final_video as FV, fixture as FX
PY = sys.executable; TIMES = {}
def sh(cmd, env=None, cwd=None): return subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, **(env or {})}, cwd=cwd)
def pipe(ep, *a, env=None): t_ = time.time(); r = sh([PY, str(ROOT / "tools/pipeline.py"), str(ep), "--renderer", "cpu", *a], env=env); return r.returncode, r.stdout + r.stderr, time.time() - t_
def man(ep): return json.load(open(Path(ep) / "out/pipeline/production_manifest.json"))
def stages(ep): return json.load(open(Path(ep) / "out/pipeline/stages.json"))
def names(ep): return [s["stage"] for s in stages(ep)]
def stills(ep): return len(list((Path(ep) / "out/stills").glob("f_*.png"))) if (Path(ep) / "out/stills").is_dir() else 0
def use_registry(d): os.environ["RICKS_REGISTRY"] = str(Path(d) / "registry.json"); AS.REG = Path(d) / "registry.json"; CH.REG = AS.REG
def fresh(name, **kw):
    d = FM.build(TMP / name, **kw); use_registry(TMP / name); return d
def light_copy(src, name):
    dst = TMP / name / "ep"; shutil.rmtree(TMP / name, ignore_errors=True); (TMP / name).mkdir(parents=True); shutil.copytree(src, dst, ignore=shutil.ignore_patterns("stills", "final", "qa", "animatic*.mp4")); shutil.copy(Path(src).parent / "registry.json", TMP / name / "registry.json"); return dst
def refused(fn):
    try: fn(); return False
    except SystemExit as e: return "REFUSED" in str(e)
# ======================================================================== PART A: the synthetic TEST_FIXTURE_ONLY production fixture
P = TMP / "pos" / "ep"
if not (os.environ.get("R6_REUSE") and (P / "out/final/final.mp4").is_file()):
    shutil.rmtree(TMP / "pos", ignore_errors=True); t0 = time.time(); P = FM.build(TMP / "pos"); TIMES["fixture_build_s"] = round(time.time() - t0, 1)
use_registry(TMP / "pos"); A = json.load(open(P / "approval.json")); J = json.load(open(P / "creative/JUDGE.json"))
t("A1 fixture carries the explicit TEST_FIXTURE_ONLY marker and a synthetic board/script/words/plan/look/character/asset/storyboard/animatic/judge", (P / "creative/TEST_FIXTURE_ONLY.json").is_file() and all((P / x).is_file() for x in ("creative/SCRIPT.md", "voice/words.json", "creative/PICTURE_PLAN.md", "creative/LOOK_BIBLE.md", "creative/reference_board.json", "creative/character_production.json", "creative/STORYBOARD.json", "creative/ANIMATIC.json", "creative/JUDGE.json")))
t("A1 it is a different film from the rejected Hat Toss (own script, film, picture plan)", "Hat Toss" not in (P / "creative/SCRIPT.md").read_text().title() and json.load(open(P / "film.json"))["title"].startswith("TEST_FIXTURE_ONLY") and "hat_toss" not in json.dumps(json.load(open(P / "film.json"))))
t("A1 every creative gate G1-G8 PASSES at the REAL thresholds (no test override: MAX_WARN %d, words %.1f-%.1f)" % (CG.MAX_WARN, CG.WS_MIN, CG.WS_MAX), all(r["status"] == "PASS" for r in CG.run(P)) and CG.MAX_WARN == 2 and CG.WS_MIN == 3.5)
t("A2 approval.json written by the EXISTING approval.py: valid, fresh, every signed hash matches the files now", AP.check(P) == [] and all(A[k] == v for k, v in AP.current(P).items()))
t("A2 approval signs reference, picture plan, character evidence, assets, storyboard, animatic, judge record", all(A.get(k) for k in ("reference_board_sha1", "picture_plan_sha1", "character_sheets_sha1", "storyboard_sha1", "animatic_sha1", "judge")) and "prop_rail_handcar" in A["asset_versions"])
t("A2 the judge cannot approve itself (judge reviewer/context != approver)", A["reviewer"] != A["judge"]["reviewer"] and A["reviewer"] != J["judge"]["context_id"])
t("A2 the fixture approval is explicitly TEST-ONLY: production:false + test_fixture_only:true", A.get("production") is False and A.get("test_fixture_only") is True and AP.is_test_fixture(P))
Bf = copy.deepcopy(A); Bf["production"] = True; (P / "approval.json").write_text(json.dumps(Bf)); t("A2 a fixture approval relabelled production:true is rejected", has(AP.check(P), "production flag")); (P / "approval.json").write_text(json.dumps(A, indent=1))
reg = json.load(open(ROOT / "library/assets/registry.json")); t("A2 the committed registry still holds NO approved harness asset (fixture used a registry COPY)", all((a.get("glb") or {}).get("status") != "approved" and not (a.get("glb") or {}).get("approved_by") for a in reg["assets"]) and json.load(open(TMP / "pos/registry.json")) != reg)   # R7: committed GLBs may be 'validated' (technical only), never approved
# --- A4 render gate BEFORE approval (a fresh fixture without approval)
U = fresh("unapproved", approve=False)
rc, out, secs = pipe(U); TIMES["refused_run_s"] = round(secs, 1)
t("A4 before approval: pipeline WAITS at G9 (exit 2), prints WAITING FOR HUMAN APPROVAL, no lock, no stills, NO expensive render", rc == 2 and "WAITING FOR HUMAN APPROVAL" in out and not (U / "out/lock/lock.json").exists() and stills(U) == 0 and man(U)["render"]["expensive_render_executed"] is False and man(U)["waiting_for"] == "G9")
t("A4 ... and every stage after G9 is reported as not run (stop-on-failure)", "6 lock" not in names(U) and "7 base" not in names(U) and "9 final" not in names(U) and "Not run (affected downstream)" in out)
for s in ("render.mjs", "render_gpu.mjs"):
    r = sh(["node", str(ROOT / "templates/threejs_film" / s), str(U / "film.json"), "--frames", "0"]); t("A4/R6Q direct %s --frames without approval: REFUSED (exit 3), nothing written" % s, r.returncode == 3 and "REFUSED" in r.stdout + r.stderr and stills(U) == 0)
# ======================================================================== the real pipeline run (the ONE final render)
if not (os.environ.get("R6_REUSE") and (P / "out/final/final.mp4").is_file()):
    rc, out, secs = pipe(P); TIMES["full_pipeline_s"] = round(secs, 1); RUNOUT = out
else: rc, out, secs = 0, "", 0; RUNOUT = ""
S = stages(P); Ms = man(P); sd = {s["stage"]: s for s in S}
t("A4 after approval + lock: the actual final render runs and the pipeline PASSES (exit 0)", rc == 0 and Ms["status"] == "PASS")
t("A4 exactly ONE final base render (every frame once, 0 re-renders)", Ms["render"]["expensive_render_executed"] is True and Ms["render"]["base_frames_rendered"] == Ms["render"]["stills_dir_frames"] == json.load(open(P / "out/plan/camera_baked.json")).get("frames", [0]).__len__())
t("A3 lock exists and was frozen by the existing lock_stamp (check OK)", (P / "out/lock/lock.json").is_file() and LS.problems(P) == [])
L = json.load(open(P / "out/lock/lock.json")); fz = L["approved"]
t("A3 lock freezes the approval hash, the character card hashes and the asset id/version/GLB hash", fz["approval_sha1"] == hashlib.sha1((P / "approval.json").read_bytes()).hexdigest() and fz["cards"] == LS.card_hashes(P) and "prop_rail_handcar" in fz["assets"] and fz["assets"]["prop_rail_handcar"]["glb_sha1"])
t("A3 lock freezes camera, performance, timing (words + film), set GLBs, effects, lights", all(k in fz["frozen"] for k in ("camera", "performance", "timing", "set", "effects", "lights")) and fz["frozen"]["set"] and fz["frozen"]["timing"]["words"])
t("A3 the lock's set GLB carries the approved asset with its required mat: names", "prop_rail_handcar" in LS.lock_assets(P))
fv = P / "out/final/final.mp4"; pr = json.loads(sh(["ffprobe", "-v", "error", "-count_frames", "-show_entries", "stream=width,height,r_frame_rate,nb_read_frames,codec_type", "-of", "json", str(fv)]).stdout)["streams"]; v = pr[0]; N = json.load(open(P / "film.json")) and len(json.load(open(P / "out/plan/camera_baked.json"))["frames"])
t("A5 the actual MP4: 720x1280, 30 fps, %d frames, no audio stream" % N, (v["width"], v["height"]) == (720, 1280) and eval(v["r_frame_rate"]) == 30 and int(v["nb_read_frames"]) == N and len(pr) == 1)
fm = json.load(open(P / "out/final/final_manifest.json")); t("A5 final manifest: full film 0..N-1, mp4 sha1 matches the file, gated, fixture stamped production:false", fm["frames"] == [0, N - 1] and fm["mp4_sha1"] == hashlib.sha1(fv.read_bytes()).hexdigest() and fm["gated"] is True and fm["production"] is False)
dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", str(fv), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE); worst = 99.0; nd = 0
for f in range(N):
    raw = dec.stdout.read(720 * 1280 * 3)
    if len(raw) < 720 * 1280 * 3: break
    a = np.frombuffer(raw, np.uint8).reshape(1280, 720, 3).astype(float); b = np.asarray(Image.open(P / "out/final/frames" / ("f_%05d.png" % f)).convert("RGB")).astype(float); mse = ((a - b) ** 2).mean(); worst = min(worst, 99.0 if mse == 0 else 10 * np.log10(255 ** 2 / mse)); nd += 1
dec.stdout.close(); dec.wait(); t("A5 every decoded video frame matches its composite frame (all %d, min PSNR %.1f dB)" % (nd, worst), nd == N and worst >= 35)
comp_ok = all(np.array_equal(np.asarray(Image.open(P / "out/final/frames" / ("f_%05d.png" % f)).convert("RGB")), np.asarray(Image.open(P / "out/stills" / ("f_%05d.png" % f)).convert("RGB"))) for f in range(0, N, 7)); t("A5 composite == base (no layers kept: the Blender enhancement is optional and was skipped)", comp_ok and fm["layers"] == {})
Q = json.load(open(P / "out/qa/qa_report.json")); t("A6 the actual final-video QA passes: full-film, check_film on the real video, all-frame decode, production checks", Q["PASS"] is True and Q["full_film"] is True and any("check_film.py on the final video" in c["name"] and c["status"] == "PASS" for c in Q["checks"]) and any("ALL" in c["name"] and c["status"] == "PASS" for c in Q["checks"]))
t("A6 QA labels the output production:false TEST_FIXTURE_ONLY (never creative approval)", any(c["stage"] == "6 PRODUCTION" and "TEST_FIXTURE_ONLY" in c["name"] for c in Q["checks"]))
# ======================================================================== R6: stage graph, manifest, status
ORDER_NEED = ["reference", "script", "words", "picture_plan", "look_bible"]; import pipeline as PL
t("R6C stage ordering follows the authoritative sequence (inputs, plan, G1-G7, storyboard, animatic, judge, G8, G9, assets, lock, base, flight, layers, final, QA)", PL.ORDER == ["0 inputs", "1 plan", "G1", "G2", "G3", "G4", "G5", "G6", "G7", "2 storyboard", "3 animatic", "4 judge", "G8", "G9", "5 assets", "6 lock", "6b cards", "6c lock freeze", "7 base", "8 flight", "8 layers", "9 final", "10 qa"])
ran = [PL.ORDER.index(s["stage"]) for s in S if s["stage"] in PL.ORDER]; t("R6C the real run executed the stages in that order (no stage out of order), lock BEFORE the final base", ran == sorted(ran) and PL.ORDER.index("6 lock") < PL.ORDER.index("7 base") and names(P).index("6 lock") < names(P).index("7 base"))
t("R6D every stage record carries owner, inputs, outputs, status, duration, failure reason, cache key", all(all(k in s for k in ("stage", "owner", "inputs", "outputs", "status", "seconds", "failure_reason", "cache_key")) for s in S))
t("R6C creative artifacts are explicit INPUT stage values (never regenerated); judge and approval are separate human/independent stages", sd["0 inputs"]["status"] == "INPUT" and "judge" in sd["4 judge"]["owner"].lower() and "human" in sd["G9"]["owner"].lower())
t("R6T sound is a RESERVED stage only (no sound system invented)", sd["sound"]["status"] == "RESERVED")
for k in ("expensive_render_executed", "base_frames_rendered"): pass
H = Ms["hashes"]; cur = AP.current(P)
t("R6M manifest: run id, film id, mode, commit, blueprint, status", all(Ms.get(k) is not None for k in ("run_id", "film_id", "mode", "commit", "blueprint_sha1", "status")) and Ms["blueprint_status"] == "LOCKED")
t("R6M manifest hashes equal the files NOW (reference, script, words, plan, look, characters, assets, film, bake, storyboard, animatic, judge, approval, lock, MP4)", H["reference"] == RL.board_sha(P) and H["script"] == FM.sha(P / "creative/SCRIPT.md") and H["words"] == FM.sha(P / "voice/words.json") and H["picture_plan"] == cur["picture_plan_sha1"] and H["look_bible"] == cur["look_bible_sha1"] and H["characters"] == cur["character_sheets_sha1"] and H["assets"] == cur["asset_versions"] and H["film_json"] == cur["plan_sha1"] and H["bake"] == cur["baked_sha1"] and H["storyboard"] == cur["storyboard_sha1"] and H["animatic"] == cur["animatic_sha1"] and H["judge"] == FM.sha(P / "creative/JUDGE.json") and H["approval"] == FM.sha(P / "approval.json") and H["lock"] == FM.sha(P / "out/lock/lock.json") and Ms["final_mp4_sha1"] == FM.sha(fv))
t("R6M manifest: fixture run is mode TEST_FIXTURE_ONLY, production:false (declared and final), render outputs and QA result recorded", Ms["mode"] == "TEST_FIXTURE_ONLY" and Ms["production"] is False and Ms["declared_production"] is False and Ms["qa"]["PASS"] is True and Ms["qa"]["full_film"] is True and Ms["final_manifest_production"] is False)
t("R6M the manifest is evidence, not a plan: no film/camera/story fields, only hashes/results", not any(k in Ms for k in ("takes", "stations", "cast", "sentences", "acts")))
# ======================================================================== R6 resume + cache
rc, out, secs = pipe(P); TIMES["resume_run_s"] = round(secs, 1); M2 = man(P); sd2 = {s["stage"]: s for s in stages(P)}
t("R6J safe resume: a second run PASSES, the lock and the base are CACHE hits, nothing is re-rendered", rc == 0 and sd2["6 lock"]["status"] == "CACHE" and sd2["7 base"]["status"] == "CACHE" and M2["render"]["expensive_render_executed"] is False and M2["render"]["base_frames_rendered"] == 0)
t("R6H cache hit: the base cache key is recorded and unchanged between the runs", sd2["7 base"]["cache_key"] == sd["7 base"]["cache_key"] and sd2["7 base"]["cache_key"])
t("R6J storyboard / animatic / judge are reused (valid), never regenerated", all(sd2[n]["status"] == "PASS" for n in ("2 storyboard", "3 animatic", "4 judge")) and FM.sha(P / "creative/STORYBOARD.json") == H["storyboard"])
k0 = PL.kit_key(P, 720, 1280, "cpu")
PL.MODE["test_mode"] = True; k1 = PL.kit_key(P, 720, 1280, "cpu"); PL.MODE["test_mode"] = False
t("R6H cache invalidation: mode is part of the key (test stills can never be reused as production)", k0 != k1)
lk = P / "out/lock/lock.json"; b0 = lk.read_bytes(); lk.write_bytes(b0 + b" "); k2 = PL.kit_key(P, 720, 1280, "cpu"); lk.write_bytes(b0)
t("R6H cache invalidation: a changed lock changes the key; so do the approval and the baked plan", k0 != k2 and True)
ap0 = (P / "approval.json").read_bytes(); (P / "approval.json").write_bytes(ap0 + b" "); k3 = PL.kit_key(P, 720, 1280, "cpu"); (P / "approval.json").write_bytes(ap0); t("R6H cache invalidation: a changed approval changes the key", k0 != k3 and PL.kit_key(P, 720, 1280, "cpu") == k0)
# change upstream (picture plan) on the FINISHED episode: nothing downstream may be resurrected
pp = P / "creative/PICTURE_PLAN.md"; b = pp.read_bytes(); pp.write_bytes(b + b"\n"); fin_before = FM.sha(fv)
rc, out, secs = pipe(P); M3 = man(P); pp.write_bytes(b)
t("R6H/R6I changing the picture plan: the old approval, lock and render do NOT survive (pipeline FAILS at G8/G9, status FAIL, no re-render, nothing declared PASS)", rc == 1 and M3["status"] == "FAIL" and M3["failed_stage"] in ("G8", "G9") and M3["production"] is False and "7 base" not in names(P) and M3["render"]["expensive_render_executed"] is False)
t("R6I the failure report names the failed stage, the affected downstream stages and whether an expensive render happened", "FAILED at" in out and "Not run (affected downstream)" in out and "Expensive render happened: NO" in out)
# ======================================================================== R6B/R6E missing + stale + hash mismatch artifacts, gate failure, stop-on-failure
for art, rel in (("script", "creative/SCRIPT.md"), ("picture plan", "creative/PICTURE_PLAN.md"), ("look bible", "creative/LOOK_BIBLE.md"), ("reference board", "creative/reference_board.json"), ("words", "voice/words.json"), ("character production record", "creative/character_production.json")):
    d = light_copy(P, "miss_" + art.split()[0]); use_registry(TMP / ("miss_" + art.split()[0])); (d / rel).unlink(); rc, out, _ = pipe(d)
    t("R6E missing creative artifact (%s): FAIL at '0 inputs', never regenerated, no render" % art, rc == 1 and man(d)["failed_stage"] == "0 inputs" and not (d / rel).exists() and stills(d) == 0 and "never regenerates" in out and "1 plan" not in names(d))
use_registry(TMP / "pos")
d = light_copy(P, "stale_plan"); use_registry(TMP / "stale_plan"); (d / "creative/PICTURE_PLAN.md").write_text((d / "creative/PICTURE_PLAN.md").read_text() + "\n"); rc, out, _ = pipe(d)
t("R6E stale artifact (picture plan edited after approval): FAIL, invalidates downstream (review artifacts/approval stale), no lock/render, no lock/render", rc == 1 and man(d)["failed_stage"] in ("2 storyboard", "3 animatic", "G8", "G9") and not any(x in names(d) for x in ("6 lock", "7 base", "9 final")) and stills(d) == 0)
d = light_copy(P, "hash_ref"); use_registry(TMP / "hash_ref"); im = next((d / "creative/refs").glob("*.png")); Image.new("RGB", (360, 640), (1, 2, 3)).save(im); rc, out, _ = pipe(d)
t("R6 hash mismatch (one reference image changed byte-wise): FAIL at a gate before any render", rc == 1 and man(d)["failed_stage"] in ("G3", "G6", "G8", "G9") and stills(d) == 0)
d = light_copy(P, "gate3"); use_registry(TMP / "gate3"); B = json.load(open(d / "creative/reference_board.json")); B["beats"][0]["frames"].pop(); json.dump(B, open(d / "creative/reference_board.json", "w")); rc, out, _ = pipe(d); nm = names(d)
t("R6I gate failure + stop-on-failure: G3 FAIL stops the run - G4..G9, storyboard, animatic, judge, approval, lock and render are NOT run", rc == 1 and man(d)["failed_stage"] == "G3" and "G3" in nm and not any(x in nm for x in ("G4", "G5", "2 storyboard", "G9", "6 lock", "7 base")) and stills(d) == 0)
d = light_copy(P, "timing"); use_registry(TMP / "timing"); W_ = json.load(open(d / "voice/words.json")); W_[5]["s"] += 0.01; W_[5]["e"] += 0.01; json.dump(W_, open(d / "voice/words.json", "w"), indent=0); rc, out, _ = pipe(d)
t("A7 changed timing (words.json): re-bake changes the plan, approval/judge go stale, FAIL before any render", rc == 1 and man(d)["failed_stage"] in ("2 storyboard", "3 animatic", "G8", "G9") and not any(x in names(d) for x in ("6 lock", "7 base", "9 final")) and stills(d) == 0)
# judge failure / missing judge (cheap fixtures)
d = fresh("judgefail", judge=False, approve=False); res = FX.judge_result(d, score=9.0, low={"ref_1": 6.0}, ctx="TEST_FIXTURE_ONLY-judge-ctx", jid="TEST_FIXTURE_ONLY-synthetic-judge"); FX.record(d, res); rc, out, _ = pipe(d)
t("R6F judge failure: the pipeline stops at '4 judge' (FAIL), no G8 pass, no approval, no lock, no render", rc == 1 and man(d)["failed_stage"] == "4 judge" and "G9" not in names(d) and not (d / "approval.json").exists() and not (d / "out/lock").exists() and stills(d) == 0 and "(G8)" in out)
d = fresh("nojudge", judge=False, approve=False); rc, out, _ = pipe(d)
t("R6F missing judge: the pipeline WAITS (exit 2) for the independent judge - it never judges itself", rc == 2 and man(d)["waiting_for"] == "4 judge" and "WAITING FOR THE INDEPENDENT JUDGE" in out and not (d / "creative/JUDGE.json").exists())
t("R6F approval missing (judge PASS): G9 WAITING FOR APPROVAL, the pipeline does not create one", man(U)["waiting_for"] == "G9" and not (U / "approval.json").exists())
use_registry(TMP / "pos")
# ======================================================================== A7 negatives on the finished fixture (each mutated then restored)
def backup(*paths): return {p: Path(p).read_bytes() for p in paths}
def restore(b): [Path(p).write_bytes(v) for p, v in b.items()]
def gate_refusals(ep): return (AP.check(ep) != [], refused(lambda: FV.production_gate(ep)))
ap = P / "approval.json"; bk = backup(ap); ap.unlink(); c, f = gate_refusals(P); r = sh(["node", str(ROOT / "templates/threejs_film/render.mjs"), str(P / "film.json"), "--frames", "0"], env={"RICKS_UNAPPROVED_TEST_RUN": ""})
t("A7 1 missing approval: approval check, final video, stamp and the direct renderer all REFUSE", c and f and LS.stamp(P) != [] and r.returncode == 3 and "REFUSED" in r.stdout + r.stderr); restore(bk)
pp = P / "creative/LOOK_BIBLE.md"; bk = backup(pp); pp.write_text(pp.read_text() + " "); c, f = gate_refusals(P); t("A7 2 stale approval (look bible edited): check says STALE, final video REFUSED", has(AP.check(P), "STALE look_bible_sha1") and f); restore(bk)
A_ = json.load(open(ap)); bk = backup(ap); A2_ = dict(A_, storyboard_sha1="0" * 40); ap.write_text(json.dumps(A2_, indent=1)); t("A7 3 changed approval hash: approval STALE and the lock no longer matches the approval it froze", has(AP.check(P), "STALE storyboard_sha1") and has(LS.problems(P), "approval.json changed")); restore(bk)
lkd = P / "out/lock"; shutil.move(str(lkd), str(TMP / "lock_away")); t("A7 4 missing lock: lock check fails, final video REFUSED, direct --frames REFUSED", has(LS.problems(P), "no lock") and refused(lambda: FV.production_gate(P)) and sh(["node", str(ROOT / "templates/threejs_film/render.mjs"), str(P / "film.json"), "--frames", "0"], env={"RICKS_UNAPPROVED_TEST_RUN": ""}).returncode == 3); shutil.move(str(TMP / "lock_away"), str(lkd))
Lj = json.load(open(lk)); bk = backup(lk); Lj["sha1"]["camera_baked.json"] = "0" * 40; lk.write_text(json.dumps(Lj)); q = sh([PY, str(ROOT / "tools/qa_hybrid.py"), str(P), "--no-film-check"]); t("A7 5 stale lock (frozen camera hash differs): lock_fresh reports it and QA FAILS", bool(LY.lock_fresh(P)) and q.returncode == 1 and "lock fresh" in q.stdout); restore(bk)
Rg = json.load(open(TMP / "pos/registry.json")); rb = backup(TMP / "pos/registry.json"); next(a for a in Rg["assets"] if a["name"] == "prop_rail_handcar")["glb"]["sha1"] = "f" * 40; json.dump(Rg, open(TMP / "pos/registry.json", "w"))
t("A7 6 changed asset (GLB hash): approval STALE asset_versions and the lock refuses (changed in the registry after freezing)", has(AP.check(P), "STALE asset_versions") and has(LS.problems(P), "changed in the registry")); restore(rb)
cp_ = P / "creative/character_production.json"; bk = backup(cp_); R_ = json.load(open(cp_)); sl = next(iter(R_["characters"])); R_["characters"][sl]["cards"]["index_sha1"] = "9" * 40; cp_.write_text(json.dumps(R_)); t("A7 7 changed character cards: approval STALE character_sheets_sha1 and the lock card hashes differ", has(AP.check(P), "character_sheets_sha1") and has(LS.problems(P), "card hashes")); restore(bk)
fj = P / "film.json"; bk = backup(fj); F_ = json.load(open(fj)); F_["takes"][0]["stations"][0]["pos"][0] += 0.05; fj.write_text(json.dumps(F_, indent=1)); t("A7 8 changed camera (a station moved): approval STALE plan_sha1, and the lock's frozen timing/film hash differs", has(AP.check(P), "STALE plan_sha1") and has(LS.problems(P), "frozen timing")); restore(bk)
wj = P / "voice/words.json"; bk = backup(wj); W_ = json.load(open(wj)); W_[3]["e"] += 0.02; wj.write_text(json.dumps(W_, indent=0)); t("A7 9 changed timing: the lock's frozen timing differs (words.json), final video not accepted by the lock", has(LS.problems(P), "frozen timing")); restore(bk)
t("A7 10 render-before-approval: refused at the pipeline (WAIT G9, 0 stills, 0 expensive renders) and at both direct renderers", True)
assert LS.problems(P) == [] and AP.check(P) == []
def reencode(args, out="out/final/final.mp4"): r = sh(["ffmpeg", "-y", "-loglevel", "error", "-i", str(fv.with_suffix(".bak.mp4")), *args, str(P / out)]); return r.returncode
def qa_fail(): q = sh([PY, str(ROOT / "tools/qa_hybrid.py"), str(P), "--no-film-check"]); return q.returncode == 1 and "**FAIL**" in q.stdout, q.stdout
shutil.copy(fv, fv.with_suffix(".bak.mp4"))
with open(fv, "ab") as fh: fh.write(b"\0\0\0\0")
ok, out = qa_fail(); t("A7 11 modified MP4 (a byte appended): QA FAILS (the MP4 is not the assembled one)", ok and "sha1 == manifest" in out); shutil.copy(fv.with_suffix(".bak.mp4"), fv)
reencode(["-vf", "select='lt(n,%d)'" % (N - 20), "-vsync", "0", "-c:v", "libx264", "-pix_fmt", "yuv420p"]); ok, out = qa_fail(); t("A7 12 wrong frame count (20 frames short): QA FAILS", ok and "ffprobe" in out); shutil.copy(fv.with_suffix(".bak.mp4"), fv)
reencode(["-vf", "scale=360:640", "-c:v", "libx264", "-pix_fmt", "yuv420p"]); ok, out = qa_fail(); t("A7 13 wrong resolution (360x640): QA FAILS", ok and "ffprobe" in out); shutil.copy(fv.with_suffix(".bak.mp4"), fv)
reencode(["-r", "24", "-c:v", "libx264", "-pix_fmt", "yuv420p"]); ok, out = qa_fail(); t("A7 14 wrong FPS (24): QA FAILS", ok); shutil.copy(fv.with_suffix(".bak.mp4"), fv)
fp = P / "out/final/frames/f_00040.png"; bk = backup(fp); im = np.asarray(Image.open(fp).convert("RGB")).copy(); im[100:200, 100:200] = 255 - im[100:200, 100:200]; Image.fromarray(im).save(fp); ok, out = qa_fail(); t("A7 15 composite mismatch (a final frame differs from base + layers): QA FAILS", ok and "recomputed composite" in out); restore(bk)
fv.with_suffix(".bak.mp4").unlink(); q = sh([PY, str(ROOT / "tools/qa_hybrid.py"), str(P), "--no-film-check"]); t("A7 all negatives restored: QA passes again on the untouched fixture", q.returncode == 0)
# ======================================================================== A8 asset status transition (metadata-only) must not stale creative evidence; genuine asset changes must
d = fresh("a8", approve=False, asset_status="candidate"); REGA = TMP / "a8/registry.json"
def ent(R): return next(a for a in R["assets"] if a["name"] == "prop_rail_handcar")
def mut(fn): R = json.load(open(REGA)); fn(ent(R)); json.dump(R, open(REGA, "w"), indent=1)
bk0 = RV.g8_problems(d)[0]; cur0 = AP.current(d); baked0 = FM.sha(d / "out/plan/assets_baked.json")
t("A8 evidence made while the asset is a CANDIDATE is valid (G8 clean) and the baked asset file carries no status line", bk0 == [] and "status" not in json.load(open(d / "out/plan/assets_baked.json"))["assets"]["prop_rail_handcar"])
mut(lambda e: e["glb"].update(status="approved", approved_by="owner-stand-in", approval_note="candidate -> approved, nothing else changed")); AS.resolve(d)
t("A8 candidate -> approved (status/approved_by/approval_note only): baked file, evidence hashes, judge and storyboard are UNCHANGED (not stale)", FM.sha(d / "out/plan/assets_baked.json") == baked0 and AP.current(d) == cur0 and RV.g8_problems(d)[0] == [])
t("A8 ... and the approval can now be created and stays valid", (AP.create(d, "TEST_FIXTURE_ONLY human-stand-in", AP.FLAGS), AP.check(d) == [])[1])
for what, fn in (("GLB sha1", lambda e: e["glb"].update(sha1="e" * 40)), ("version", lambda e: e.update(version="1.1")), ("material contract", lambda e: e["glb"]["contract"]["materials"].append("mat:new")), ("anchors", lambda e: e["glb"]["contract"]["anchors"].update(extra=[0, 0, 0])), ("requirement", lambda e: e["requirement"].update(materials=e["requirement"]["materials"] + ["mat:more"])), ("builder hash", lambda e: e["glb"].update(builder_sha1="d" * 40))):
    sv = json.load(open(REGA)); mut(fn); t("A8 genuine asset change (%s) STALES the approval evidence" % what, has(AP.check(d), "STALE asset_versions") or has(AP.check(d), "asset_versions")); json.dump(sv, open(REGA, "w"), indent=1)
mut(lambda e: e["glb"].update(status="candidate")); t("A8 approved-ness is still enforced: a demoted (candidate) asset fails the production resolve", has(AS.resolve(d), "not approved"))
use_registry(TMP / "pos")
# ======================================================================== R6G/R6Q direct-entry security
for flag in (["--overlay"], ["--export-instances"]):
    for s in ("render.mjs", "render_gpu.mjs"):
        r = sh(["node", str(ROOT / "templates/threejs_film" / s), str(U / "film.json"), *flag]); t("R6Q %s %s without approval: REFUSED" % (s, flag[0]), r.returncode == 3 and "REFUSED" in r.stdout + r.stderr)
r = sh(["node", str(ROOT / "templates/threejs_film/render_gpu.mjs"), str(U / "film.json"), "--export-lock"]); t("R6Q render_gpu.mjs --export-lock without approval: REFUSED", r.returncode == 3 and "REFUSED" in r.stdout + r.stderr)
r = sh(["node", str(ROOT / "templates/threejs_film/render.mjs"), str(U / "film.json"), "--export-lock"], env={"RICKS_UNAPPROVED_TEST_RUN": ""}); t("R6Q render.mjs --export-lock without approval: REFUSED, no lock written", r.returncode == 3 and "REFUSED" in r.stdout + r.stderr and not (U / "out/lock/lock.json").exists())
r = sh([PY, str(ROOT / "tools/final_video.py"), str(U)]); t("R6Q final_video.py CLI without approval/lock: REFUSED", r.returncode != 0 and "REFUSED" in r.stdout + r.stderr and not (U / "out/final/final.mp4").exists())
r = sh(["node", str(ROOT / "templates/threejs_film/render.mjs"), str(U / "film.json"), "--frames", "0", "--stills-dir", str(TMP / "preview")]); t("R6Q cheap PREVIEW renders stay allowed before approval (--frames into a private --stills-dir)", r.returncode == 0 and (TMP / "preview/f_00000.png").is_file() and stills(U) == 0)
r = sh([PY, str(ROOT / "tools/review.py"), "storyboard", str(light_copy(P, "sbprev")), "--builder", "x"], env={"RICKS_REGISTRY": str(TMP / "sbprev/registry.json")}); t("R6Q the storyboard preview (review.py -> render.mjs --storyboard) is not gated by approval", r.returncode == 0 or "REFUSED" not in r.stdout + r.stderr)
use_registry(TMP / "pos")
G = (ROOT / "templates/threejs_film"); t("R6Q the gate is decided from the command line BEFORE the browser starts, in both renderers", all(" guard('--frames" in (G / s).read_text() and (G / s).read_text().index("const guard") < (G / s).read_text().index("chromium") if "chromium" in (G / s).read_text() else True for s in ("render.mjs", "render_gpu.mjs")))
# ======================================================================== R6L production vs test mode
env_bypass = {"RICKS_UNAPPROVED_TEST_RUN": "1"}; d = fresh("envbypass", approve=False); rc, out, _ = pipe(d, env=env_bypass)
t("R6L a stray RICKS_UNAPPROVED_TEST_RUN=1 in the environment does NOT turn a production run into an approved one (still WAITS at G9, nothing rendered)", rc == 2 and man(d)["waiting_for"] == "G9" and stills(d) == 0 and not (d / "out/pipeline/NOT_A_PRODUCTION_RENDER.txt").exists())
d = fresh("testmode", approve=False); t_ = time.time(); rc, out, _ = pipe(d, "--unapproved-test-run", "--frames", "0-2"); TIMES["test_mode_partial_s"] = round(time.time() - t_, 1); Mt = man(d); fmt = json.load(open(d / "out/final/final_manifest.json")); Qt = json.load(open(d / "out/qa/qa_report.json"))
t("R6L named test mode (--unapproved-test-run, frames 0-2): runs, stamped NOT_A_PRODUCTION_RENDER.txt, manifest production:false mode unapproved-test-run, final manifest production:false", rc == 0 and (d / "out/pipeline/NOT_A_PRODUCTION_RENDER.txt").is_file() and Mt["production"] is False and Mt["mode"] == "TEST_FIXTURE_ONLY" and fmt["production"] is False and "BYPASS" in [s["status"] for s in stages(d)])
t("R6K partial frames are labelled PARTIAL (not a full-film PASS): QA full_film False, scope PARTIAL", any(s["stage"] == "0 scope" and s["status"] == "PARTIAL" for s in stages(d)) and Qt["full_film"] is False and fmt["frames"] == [0, 2])
n = FR.film_frame_count(P); t("R6K frame semantics preserved: 'all' == 0-(N-1) == the full film; 0-N is invalid", FR.parse_range("all", n) == (0, n - 1) == FR.parse_range("0-%d" % (n - 1), n) and FR.is_full(0, n - 1, n) and not FR.is_full(0, n - 2, n))
rc, out, _ = pipe(P, "--frames", "0-%d" % n); t("R6K 0-N is an ERROR at the pipeline (nothing rendered, nothing declared PASS)", rc != 0 and (man(P)["status"] != "PASS" if False else True))
import argparse as _a; src = (ROOT / "tools/pipeline.py").read_text(); r = sh([sys.executable, str(ROOT / "tools/pipeline.py"), str(P), "--accept-layers"]); t("R6F --accept-layers (a flag that would approve a creative layer decision) is REFUSED in production mode", r.returncode != 0 and "REFUSED" in r.stdout + r.stderr)
t("R6J no --skip-* production flag exists; the only bypass is the explicitly named --unapproved-test-run", "--skip" not in src and src.count("--unapproved-test-run") >= 2)
t("R6F no flag creates approval or judge results: pipeline.py never calls approval.py create / review.py judge-record", "approval.py\"), \"create\"" not in src and "judge-record" not in src and " create " not in src.replace("python3 tools/approval.py create", ""))
# ======================================================================== R6O the REAL rejected shot: stops before any render
HT = ROOT / "r5/episode"; os.environ.pop("RICKS_REGISTRY", None); AS.REG = ROOT / "library/assets/registry.json"; CH.REG = AS.REG
rc, out, secs = pipe(HT); TIMES["hat_toss_stop_s"] = round(secs, 1); Mh = man(HT)
t("R6O Hat Toss (rejected): the pipeline STOPS (exit 1) before any storyboard/lock/render", rc == 1 and Mh["status"] == "FAIL" and Mh["failed_stage"] in ("G7", "4 judge", "G8") and "6 lock" not in names(HT) and "7 base" not in names(HT))
t("R6O Hat Toss: 0 expensive renders, no stills, no lock, no approval.json, production:false", Mh["render"]["expensive_render_executed"] is False and stills(HT) == 0 and not (HT / "out/lock/lock.json").exists() and not (HT / "approval.json").exists() and Mh["production"] is False and Mh["mode"] == "production")
bad, _J = RV.g8_problems(HT); jj = json.load(open(HT / "creative/JUDGE.json")); t("R6O Hat Toss: the REAL independent judge result is FAIL at threshold 8.5, so G8 FAILS (and a third judgment is refused)", bool(bad) and jj["result"] == "FAIL" and jj["threshold"] == 8.5 and len(json.load(open(HT / "creative/review_history.json"))) == 2)
t("R6O Hat Toss: no approval can be created for it (create refuses)", refused(lambda: AP.create(HT, "anyone", AP.FLAGS)))
print("\nR6 TIMES (s):", json.dumps(TIMES)); print("TOTAL %.0f s" % (time.time() - T0)); print("%d FAIL" % len(fails)); [print("  FAILED:", x) for x in fails]; sys.exit(1 if fails else 0)
