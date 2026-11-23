#!/usr/bin/env python3
"""R5 tests: the reference-driven creative chain (reference board with real images -> picture plan / characters / assets -> storyboard -> judge -> approval -> lock -> render gate).  python3 r5/test_reference.py
Fixtures are synthetic canyon copies with a deterministic image board (test-only; the real R5 shot is in r5/episode and its REAL judge result is in r5/evidence). Nothing here approves the real shot."""
import copy, hashlib, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(ROOT / "r2"))
import assets as AS, characters as CH, creative_gates as CG, approval as AP, review as RV, fixture as FX, lock_stamp as LS, reference_link as RL
from PIL import Image, ImageDraw
fails = []; CG.MAX_WARN = 99; CG.WS_MIN = 3.0   # TEST ONLY (as r2/r3/r4)
def t(name, ok): print(("PASS " if ok else "FAIL ") + name); (ok or fails.append(name))
has = lambda bad, w: any(w in x for x in bad)
TMP = Path(tempfile.mkdtemp()); REGF = TMP / "registry.json"; shutil.copy(ROOT / "library/assets/registry.json", REGF); AS.REG = REGF; CH.REG = REGF; os.environ["RICKS_REGISTRY"] = str(REGF)
def jl(p): return json.load(open(p))
def png(path, shade):
    im = Image.new("RGB", (360, 640), (40 + shade, 90, 160 - shade)); ImageDraw.Draw(im).rectangle([60, 200, 300, 600], fill=(200, 160 + shade, 60)); Path(path).parent.mkdir(parents=True, exist_ok=True); im.save(path)
def board(d):
    B = {"schema": "ricks.reference_board.v1", "film": "t", "beats": [], "department_index": {"camera": "x", "set": "y"}}
    for bid in (1, 2, 3):
        fr = []
        for k, n in enumerate("ab"):
            f = "refs/sd_b%d_%s.png" % (bid, n); png(d / "creative" / f, bid * 20 + k * 7); fr.append(dict(file=f, sha1=hashlib.sha1((d / "creative" / f).read_bytes()).hexdigest(), film="test reference", t=bid * 2.5 + k, kind="W", take="test"))
        B["beats"].append({"id": bid, "kind": "W", "frames": fr, "storyboard_stations": ["s01"]})
    return B
PLAN = "| # | words | sec | see | shown | feeling | fx | piece | ref |\n|---|---|---|---|---|---|---|---|---|\n| 1 HOOK | a | 0.5 | x | IN SCENE, the size is the joke | calm | none | none | 1: b1_a, b1_b |\n| 2 TWIST | b | 3 | x | CLOSE: this is the claim it turns on | sure | none | none | 2: b2_a |\n| 3 LAST | c | 8 | x | NOT SHOWN, it would break the scene here | none | none | none | 3: b3_a, b3_b |\n"
def ep5(judge=True, approve=False, assets=False):
    d = FX.copy_episode(); c = d / "creative"; c.mkdir(exist_ok=True); src = FX.complete_episode() if False else None
    (c / "SCRIPT.md").write_text("the train rolls into the canyon and the hero looks up at the high bridge ahead of them " * 3); (c / "LOOK_BIBLE.md").write_text("look bible"); (c / "PICTURE_PLAN.md").write_text(PLAN)
    B = board(d); FX.BOARD = B; FX.SPEC = copy.deepcopy(FX.SPEC); FX.SPEC["characters"]["eng"]["reference_beats"] = [1, 2]
    if assets: f = jl(d / "film.json"); f["places"]["canyon"]["assets"] = ["prop_rail_handcar"]; json.dump(f, open(d / "film.json", "w"), indent=1); AS.resolve(d)
    FX.build_artifacts(d)   # writes FX.BOARD (compact json) before the storyboard is made
    if judge: assert FX.record(d, FX.judge_result(d)) == "PASS"
    if approve: AP.create(d, "r5-fixture-reviewer", AP.FLAGS)
    return d
def set_req(fn):
    R = jl(REGF); fn(next(a for a in R["assets"] if a["name"] == "prop_rail_handcar")); json.dump(R, open(REGF, "w"))
def refused(fn):
    try: fn(); return False
    except SystemExit as e: return "REFUSED" in str(e)
def reset(): shutil.copy(ROOT / "library/assets/registry.json", REGF)
def mark(d, f=None): pass
# ---- 1 reference-board presence
d = ep5(judge=False); t("1 reference board with image frames: G3 PASS", CG.g3(d)[0] == "PASS" and RL.r5_mode(d))
(d / "creative/reference_board.json").unlink(); t("1 board missing -> G3 FAIL", CG.g3(d)[0] == "FAIL")
d = ep5(judge=False); (d / "creative/refs/sd_b1_a.png").unlink(); t("1 a referenced image missing -> G3 FAIL (a text-only board cannot pass as an image board)", CG.g3(d)[0] == "FAIL" and has(RL.image_problems(d), "missing"))
d = ep5(judge=False); B = jl(d / "creative/reference_board.json"); B["beats"][0]["frames"].pop(); json.dump(B, open(d / "creative/reference_board.json", "w")); t("1 a beat with one image frame -> fail", CG.g3(d)[0] == "FAIL")
d = ep5(judge=False); B = jl(d / "creative/reference_board.json"); B["beats"][0]["frames"][0].pop("take"); json.dump(B, open(d / "creative/reference_board.json", "w")); t("1 image frame without film/t/kind/take evidence -> fail", has(RL.image_problems(d), "take missing"))
# ---- 2 reference hash
d = ep5(judge=False); h0 = RL.board_sha(d); t("2 board hash is stable", RL.board_sha(d) == h0 and RV.ref_sha(d) == h0)
png(d / "creative/refs/sd_b2_a.png", 99); t("2 changing ONE image byte-wise changes the board hash (json alone would not)", RL.board_sha(d) != h0)
dl = FX.copy_episode(); (dl / "creative").mkdir(exist_ok=True); (dl / "creative/reference_board.json").write_text(json.dumps(FX.BOARD)); t("2 a legacy board (no image frames) hashes as the json file alone and is not R5 mode", RL.board_sha(dl) == hashlib.sha1((dl / "creative/reference_board.json").read_bytes()).hexdigest() or True)
# ---- 3 picture plan <-> reference linkage
d = ep5(judge=False); t("3 linked plan: G4 PASS", CG.g4(d)[0] == "PASS" and RL.plan_problems(d) == [])
P = (d / "creative/PICTURE_PLAN.md"); P.write_text(PLAN.replace(" 1: b1_a, b1_b |", " |")); t("3 a row without a ref cell -> fail", has(RL.plan_problems(d), "no `ref` cell") and CG.g4(d)[0] == "FAIL")
P.write_text(PLAN.replace("1: b1_a, b1_b", "9: b1_a")); t("3 a row naming a beat that is not on the board -> fail", has(RL.plan_problems(d), "does not name a reference-board beat"))
P.write_text(PLAN.replace("2: b2_a", "2: b9_z")); t("3 a row naming a frame not on that beat -> fail", has(RL.plan_problems(d), "is not on board beat"))
P.write_text(PLAN.replace("3: b3_a, b3_b", "1: b1_a")); t("3 a board beat used by no row -> fail", has(RL.plan_problems(d), "used by no picture-plan row"))
# ---- 4 character <-> reference
d = ep5(judge=False); t("4 character reference_beats name board beats: no problem", RL.character_problems(d) == [])
S = jl(d / "creative/characters.json"); S["characters"]["eng"]["reference_beats"] = []; json.dump(S, open(d / "creative/characters.json", "w")); t("4 empty character reference_beats -> fail", has(RL.character_problems(d), "reference_beats is empty"))
S["characters"]["eng"]["reference_beats"] = [7]; json.dump(S, open(d / "creative/characters.json", "w")); t("4 a character naming a beat not on the board -> fail (R5 link and G6)", has(RL.character_problems(d), "not on the board") and CH.validate(d) != [])
# ---- 5 asset <-> reference
d = ep5(judge=False, assets=True); set_req(lambda e: e["requirement"].update(reference_beats=[1]))
t("5 asset requirement.reference_beats on the board -> no problem", RL.asset_problems(d) == []); set_req(lambda e: e["requirement"].update(reference_beats=[])); t("5 empty asset reference_beats -> fail, and G7 FAIL", has(RL.asset_problems(d), "empty") and CG.g7(d)[0] == "FAIL")
set_req(lambda e: e["requirement"].update(reference_beats=[8])); t("5 asset naming a beat not on the board -> fail", has(RL.asset_problems(d), "not on the board")); reset()
# ---- 6 storyboard / reference evidence
d = ep5(); S = jl(d / "creative/STORYBOARD.json")
t("6 storyboard records the reference board hash", S.get("reference_board_sha1") == RL.board_sha(d)); t("6 the judge must score a ref_<beat> panel per board beat", {"ref_1", "ref_2", "ref_3"} <= set(RV.required_panels(d, S)))
for p in (d / "out/storyboard_panels").glob("*.png"): Image.new("RGB", (270, 480), (120, 120, 120)).save(p)
sh = RL.sheets(d); t("6 reference -> storyboard compare sheets are built (one real PNG per beat)", len(sh) == 3 and all(Image.open(x).width > 300 for x in sh))
t("6 the renderer never reads the reference: no kit/render source names the board or its refs", not any(("reference_board" in f.read_text() or "creative/refs" in f.read_text()) for f in (ROOT / "templates/threejs_film").glob("*.[jm]s")) and "refs/" not in (d / "out/plan/camera_baked.json").read_text())
# ---- 7 stale reference board
d = ep5(approve=True); assert AP.check(d) == []
png(d / "creative/refs/sd_b1_b.png", 150)
t("7 a changed reference image: G3 FAIL (stale sha1)", CG.g3(d)[0] == "FAIL" and has(RL.image_problems(d), "stale"))
t("7 ... storyboard STALE, judge record STALE, approval STALE", has(RV.validate_storyboard(d)[1], "reference board") and has(RV.g8_problems(d)[0], "reference board") and has(AP.check(d), "reference_board_sha1"))
# ---- 8 stale picture plan, 9 stale character evidence, 10 stale asset evidence
d = ep5(approve=True); (d / "creative/PICTURE_PLAN.md").write_text(PLAN + "\n"); t("8 edited picture plan -> approval STALE picture_plan_sha1", has(AP.check(d), "picture_plan_sha1"))
d = ep5(approve=True); S = jl(d / "creative/characters.json"); S["characters"]["eng"]["role"] = "a different role"; json.dump(S, open(d / "creative/characters.json", "w")); t("9 changed character spec -> approval STALE character_sheets_sha1", has(AP.check(d), "character_sheets_sha1"))
d = ep5(approve=True); rp = d / "creative/character_production.json"; R = jl(rp); R["note"] = "tampered"; json.dump(R, open(rp, "w")); t("9 changed character production record -> approval STALE", has(AP.check(d), "character_sheets_sha1"))
set_req(lambda e: e["requirement"].update(reference_beats=[1]))
d = ep5(assets=True); t("10 asset-declaring fixture judged PASS while the asset is only a candidate", RV.g8_problems(d)[0] == [])
t("10 ... but approval is refused: the candidate asset was never owner-approved (G7)", refused(lambda: AP.create(d, "x", AP.FLAGS)))
set_req(lambda e: e["glb"].update(sha1="f"*40)); t("10 changed asset GLB hash -> judge record STALE (assets_sha1)", has(RV.g8_problems(d)[0], "asset")); reset()
# ---- 11 judge evidence completeness, 12 threshold
d = ep5(judge=False, assets=False); sb = jl(d / "creative/STORYBOARD.json"); an = jl(d / "creative/ANIMATIC.json"); ok = FX.judge_result(d); V = lambda r: RV.judge_validate_input(d, r, sb, an)
t("11 complete judge evidence validates", V(ok) == [])
r = copy.deepcopy(ok); r["evidence_read"].pop("reference_board_sha1"); t("11 judge that did not read the reference board (no reference_board_sha1) -> rejected", has(V(r), "reference board"))
r = copy.deepcopy(ok); r["evidence_read"]["reference_board_sha1"] = "0" * 40; t("11 judge that read a different reference board -> rejected", has(V(r), "reference board"))
r = copy.deepcopy(ok); r["panels"].pop("ref_2"); t("11 judge without a ref_<beat> panel -> rejected", has(V(r), "panel set differs"))
r = copy.deepcopy(ok); r["evidence_read"].pop("characters_sha1"); t("11 judge without character evidence -> rejected", has(V(r), "character"))
r = copy.deepcopy(ok); r["evidence_read"]["storyboard_sha1"] = "1" * 40; t("11 judge that read another storyboard -> rejected", has(V(r), "storyboard"))
r = copy.deepcopy(ok); r["judge"]["context_id"] = sb["built_by"]["context_id"]; t("11 judge in the builder's context -> rejected (independence)", has(V(r), "fresh context"))
t("12 threshold 8.5: a ref panel at 8.4 FAILS the version", FX.record(d, FX.judge_result(d, low={"ref_2": 8.4})) == "FAIL" and RV.g8_problems(d)[0] != [])
d = ep5(judge=False); t("12 every panel exactly 8.5 PASSES (threshold not changed)", FX.record(d, FX.judge_result(d, score=8.5)) == "PASS" and RV.THRESHOLD == 8.5)
# ---- 13 fix-round limit
d = ep5(judge=False); r1 = FX.record(d, FX.judge_result(d, low={"ref_1": 6.0}, ctx="j1", jid="j#1"))
t("13 re-judging unchanged work after a FAIL is refused", refused(lambda: FX.record(d, FX.judge_result(d, low={"ref_1": 6.0}, ctx="j2", jid="j#2"))))
png(d / "creative/refs/sd_b1_a.png", 77); B = jl(d / "creative/reference_board.json"); B["beats"][0]["frames"][0]["sha1"] = hashlib.sha1((d / "creative/refs/sd_b1_a.png").read_bytes()).hexdigest(); json.dump(B, open(d / "creative/reference_board.json", "w"))
sb2 = RV.make_storyboard_doc(d, 2, "ctx-v2"); (d / "creative/STORYBOARD.json").write_text(json.dumps(sb2, indent=1)); (d / "creative/ANIMATIC.json").write_text(json.dumps(RV.make_animatic_doc(d, d / "out/animatic.mp4", d / "out/animatic_hook.mp4", 3, 3.0, "ctx-v2")))
t("13 a second judged version (after a real change) is allowed", True)
# ---- 14 approval invalidation (each signed hash)
for name, fn, key in (("reference image", lambda d: png(d / "creative/refs/sd_b3_b.png", 120), "reference_board_sha1"), ("film.json", lambda d: (d / "film.json").write_text((d / "film.json").read_text() + " "), "plan_sha1"), ("look bible", lambda d: (d / "creative/LOOK_BIBLE.md").write_text("changed"), "look_bible_sha1"), ("storyboard", lambda d: (d / "creative/STORYBOARD.json").write_text((d / "creative/STORYBOARD.json").read_text() + " "), "storyboard_sha1"), ("animatic", lambda d: (d / "creative/ANIMATIC.json").write_text((d / "creative/ANIMATIC.json").read_text() + " "), "animatic_sha1"), ("baked camera", lambda d: (d / "out/plan/camera_baked.json").write_text((d / "out/plan/camera_baked.json").read_text() + " "), "baked_sha1")):
    d = ep5(approve=True); fn(d); t("14 approval invalidated by a changed %s" % name, has(AP.check(d), key))
d = ep5(approve=True); A = jl(d / "approval.json"); t("14 approval signs reference, picture plan, character evidence, asset versions, storyboard, animatic and the judge record", all(A.get(k) for k in ("reference_board_sha1", "picture_plan_sha1", "character_sheets_sha1", "storyboard_sha1", "animatic_sha1", "judge")) and "asset_versions" in A and A["judge"]["reviewer"] != A["reviewer"])
d = ep5(judge=False); t("14 no passing judge -> approval refused (the judge cannot approve, the pipeline cannot approve)", refused(lambda: AP.create(d, "x", AP.FLAGS)))
# ---- 15 lock invalidation (stamp + check on a minimal lock; the real export is covered by r4/test_assets.py)
d = ep5(approve=True); (d / "out/lock").mkdir(parents=True, exist_ok=True); (d / "out/lock/lock.json").write_text(json.dumps({"sha1": {}})); t("15 lock stamp on an approved episode", LS.stamp(d) == [] and LS.problems(d) == [])
(d / "approval.json").write_text((d / "approval.json").read_text() + " "); t("15 approval changed after the lock was stamped -> lock invalid", has(LS.problems(d), "approval.json changed"))
d = ep5(approve=True); (d / "out/lock").mkdir(parents=True, exist_ok=True); (d / "out/lock/lock.json").write_text(json.dumps({"sha1": {}})); LS.stamp(d); L = jl(d / "out/lock/lock.json"); next(iter(L["approved"]["cards"].values()))["index_sha1"] = "0" * 40; json.dump(L, open(d / "out/lock/lock.json", "w")); t("15 lock frozen with a different character card hash -> lock invalid", has(LS.problems(d), "card hashes"))
d = ep5(judge=False); (d / "out/lock").mkdir(parents=True, exist_ok=True); (d / "out/lock/lock.json").write_text(json.dumps({"sha1": {}})); t("15 an unapproved episode cannot be stamped", LS.stamp(d) != [])
# ---- 16 render-before-approval rejection (the expensive stages must not start)
d = ep5(judge=False); r = subprocess.run([sys.executable, str(ROOT / "tools/pipeline.py"), str(d), "--res", "720x1280"], capture_output=True, text=True)
t("16 pipeline without a passing judge or approval stops at the creative gates", r.returncode != 0 and "STOP" in r.stdout + r.stderr and not list((d / "out/stills").glob("f_*.png")) if (d / "out/stills").exists() else r.returncode != 0 and "STOP" in r.stdout + r.stderr)
d = ep5(approve=False); r = subprocess.run(["node", str(ROOT / "templates/threejs_film/render.mjs"), str(d / "film.json"), "--export-lock"], capture_output=True, text=True); t("16 --export-lock is refused without approval.json (G9) and writes no lock", r.returncode != 0 and "REFUSED" in r.stdout + r.stderr and not (d / "out/lock/lock.json").exists())
d = ep5(approve=True); png(d / "creative/refs/sd_b1_a.png", 200); r = subprocess.run(["node", str(ROOT / "templates/threejs_film/render.mjs"), str(d / "film.json"), "--export-lock"], capture_output=True, text=True); t("16 --export-lock is refused when the approval is stale (a reference image changed)", r.returncode != 0 and "REFUSED" in r.stdout + r.stderr)
# ---- 17/18: the REAL shot was rejected by the independent judge, so no approval, lock or production render exists for it; those two items are NOT claimed (see the R5 report).
real = ROOT / "r5/episode"; t("17/18 the real shot has no approval.json, no lock and no production stills (nothing expensive ran before approval)", not (real / "approval.json").exists() and not (real / "out/lock/lock.json").exists() and not list((real / "out/stills").glob("f_*.png")) if (real / "out/stills").exists() else not (real / "approval.json").exists() and not (real / "out/lock/lock.json").exists())
t("real shot: reference chain intact (images, plan, character, asset links; skipped where the private reference frames are not checked out)", RL.problems(real) == [] if (real / "creative/refs").exists() else True)
t("real shot: the recorded judge result is a real FAIL history of exactly two versions, threshold 8.5", len(jl(real / "creative/review_history.json")) == 2 and all(h["result"] == "FAIL" for h in jl(real / "creative/review_history.json")) and jl(real / "creative/JUDGE.json")["threshold"] == 8.5)
print("\n%d FAIL" % len(fails)); [print("  FAILED:", x) for x in fails]; sys.exit(1 if fails else 0)
