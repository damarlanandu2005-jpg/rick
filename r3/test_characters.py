#!/usr/bin/env python3
"""R3 tests: the 2D character-production stage (spec, views, performance, cards, registry/casting, validation, gate and R2-review integration, real fixture).  python3 r3/test_characters.py"""
import copy, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(ROOT / "r2"))
import characters as CH, creative_gates as CG, approval as AP, review as RV, fixture as FX, assets
from PIL import Image
fails = []
CG.MAX_WARN = 99; CG.WS_MIN = 3.0   # TEST ONLY (real canyon: 5 WARN, 3.30 w/s); production values are asserted in r1/test_gates.py
def t(name, ok): print(("PASS " if ok else "FAIL ") + name); (ok or fails.append(name))
has = lambda bad, w: any(w in x for x in bad)
def fresh():
    d = FX.copy_episode(); FX.with_characters(d); return d
def jl(p): return json.load(open(p))
def jw(p, o): json.dump(o, open(p, "w"))
def spec_edit(d, fn):
    p = d / "creative/characters.json"; S = jl(p); fn(S["characters"]["eng"]); jw(p, S)
def rec_edit(d, fn):
    p = d / "creative/character_production.json"; R = jl(p); fn(R); jw(p, R)
d = fresh()
# ---- R3B spec / R3G validation
t("valid production character: validate() is clean", CH.validate(d) == [])
t("G6 PASS through the creative gates", CG.g6(d)[0] == "PASS")
d = fresh(); (d / "creative/characters.json").unlink(); t("missing spec -> problem", has(CH.validate(d), "character spec missing"))
d = fresh(); (d / "creative/characters.json").write_text("{nope"); t("malformed spec -> problem", has(CH.validate(d), "malformed"))
d = fresh(); jw(d / "creative/characters.json", {"schema": "other", "characters": {}}); t("wrong spec schema -> problem", has(CH.validate(d), "malformed"))
d = fresh(); S = jl(d / "creative/characters.json"); S["characters"] = {}; jw(d / "creative/characters.json", S); t("missing character: a cast slot with no spec -> problem", has(CH.validate(d), "missing character: no spec"))
d = fresh(); S = jl(d / "creative/characters.json"); S["characters"]["ghost"] = copy.deepcopy(S["characters"]["eng"]); jw(d / "creative/characters.json", S); t("spec for a slot film.json does not cast -> problem", has(CH.validate(d), "does not cast"))
for f in ("role", "outfit", "traits", "character", "version"): d = fresh(); spec_edit(d, lambda c, f=f: c.pop(f)); t("spec without %s -> problem" % f, CH.validate(d) != [])
d = fresh(); spec_edit(d, lambda c: c.update(views_required=["front", "side"])); t("reducing the required view set is refused", has(CH.validate(d), "cannot be reduced"))
d = fresh(); spec_edit(d, lambda c: c.update(reference_beats=[99])); t("a reference beat that is not on the board -> problem (reference -> requirements)", has(CH.validate(d), "reference_beats"))
d = fresh(); spec_edit(d, lambda c: c.update(reference_beats=[])); t("no reference link at all -> problem", has(CH.validate(d), "reference_beats"))
# ---- registry / casting
d = fresh(); spec_edit(d, lambda c: c.update(character="char_nobody")); t("missing character in the registry -> problem", has(CH.validate(d), "is not in the registry"))
d = fresh(); spec_edit(d, lambda c: c.update(character="char_lady")); b = CH.validate(d); t("wrong character assigned to a cast slot (lady spec, stationmaster cast) -> problem", has(b, "wrong character in this cast slot"))
d = fresh(); spec_edit(d, lambda c: c.update(version="2.0")); t("wrong character version -> problem", has(CH.validate(d), "wrong character version"))
reg0 = CH.REG; tmpreg = Path(tempfile.mkdtemp()) / "registry.json"; R = json.load(open(reg0)); [a["character"].update(status="candidate") for a in R["assets"] if a["name"] == "char_stationmaster"]; jw(tmpreg, R); CH.REG = tmpreg
d = fresh(); b = CH.validate(d); CH.REG = reg0; t("an UNAPPROVED (candidate) character cannot be cast in production", has(b, "unapproved character"))
R = json.load(open(reg0)); [a.update(version="1.1") for a in R["assets"] if a["name"] == "char_stationmaster"]; jw(tmpreg, R); CH.REG = tmpreg; d = fresh(); b = CH.validate(d); CH.REG = reg0; t("a registry version bump makes the cast version wrong/stale", has(b, "wrong character version"))
R = json.load(open(reg0)); [a["character"].update(approval_note="edited") for a in R["assets"] if a["name"] == "char_stationmaster"]; jw(tmpreg, R); CH.REG = tmpreg; b = CH.validate(fresh()); CH.REG = reg0; t("a changed registry entry makes the build STALE", has(b, "registry entry changed"))
t("registry holds Ricks' approved characters verified against today's rig", {"char_stationmaster", "char_lady", "char_dad", "char_inspector"} <= {a["name"] for a in json.load(open(reg0))["assets"] if a["category"] == "character" and a["character"]["status"] == "approved"})
t("registry holds the Western kid as a CANDIDATE (no approved views exist for form:kid)", [a["character"]["status"] for a in json.load(open(reg0))["assets"] if a["name"] == "char_kid"] == ["candidate"])
t("assets.py check passes with character entries", assets.check() == [])
# ---- R3C views
for v in CH.VIEWS: d = fresh(); (d / "creative/characters/eng" / (v + ".png")).unlink(); t("missing required view %s -> problem" % v, has(CH.validate(d), "missing required view %s" % v))
d = fresh(); (d / "creative/characters/eng/side.png").write_bytes(b"not a png"); t("corrupted view -> unreadable", has(CH.validate(d), "unreadable"))
d = fresh(); shutil.copy(d / "creative/characters/eng/side.png", d / "creative/characters/eng/front.png"); b = CH.validate(d); t("a swapped view -> wrong hash and identity not preserved", has(b, "wrong hash") and has(b, "identity is not preserved"))
d = fresh(); Image.new("RGB", (800, 1500), (200, 0, 0)).save(d / "creative/characters/eng/front.png"); rec_edit(d, lambda R: R["characters"]["eng"]["views"]["front"].update(sha1=CH.sha(d / "creative/characters/eng/front.png"))); t("a forged record over a different drawing is still caught by the pixel diff against the approved view", has(CH.validate(d), "identity is not preserved"))
d = fresh(); Image.new("RGB", (400, 750), (255, 255, 255)).save(d / "creative/characters/eng/front.png"); rec_edit(d, lambda R: R["characters"]["eng"]["views"]["front"].update(sha1=CH.sha(d / "creative/characters/eng/front.png"))); t("a view of the wrong size -> problem", has(CH.validate(d), "expected [800, 1500]"))
R = jl(d / "creative/character_production.json"); t("views are tied to the registry: golden hash and a 0.0 % diff recorded", all(v["golden_diff_pct"] == 0.0 and v["golden_sha1"] for v in jl(fresh() / "creative/character_production.json")["characters"]["eng"]["views"].values()))
# ---- staleness
d = fresh(); orig = CH.package_sha1; CH.package_sha1 = lambda: "0" * 40; b = CH.validate(d); CH.package_sha1 = orig; t("stale: the character package changed after the build", has(b, "character package"))
d = fresh(); spec_edit(d, lambda c: c.update(role="a different role")); t("stale: the spec changed after the build", has(CH.validate(d), "spec or the film.json cast entry changed"))
d = fresh(); F = jl(d / "film.json"); F["cast"]["eng"]["height"] = 1.6; jw(d / "film.json", F); t("stale: the film.json cast entry changed", has(CH.validate(d), "STALE"))
d = fresh(); P = jl(d / "out/plan/performance_baked.json"); P["eng"][0]["f1"] += 1; jw(d / "out/plan/performance_baked.json", P); t("stale: the baked performance changed", has(CH.validate(d), "baked performance changed"))
d = fresh(); (d / "creative/reference_board.json").write_text(json.dumps({"beats": [{"id": 1, "frames": ["a", "b"]}, {"id": 2, "frames": ["a", "b"]}], "department_index": {"x": 1}})); t("stale: the reference board changed after the characters were built", has(CH.validate(d), "reference board changed"))
d = fresh(); rec_edit(d, lambda R: R.update(resolution=[1080, 1920])); t("resolution other than 720x1280 @ 30 -> problem (no 1080p)", has(CH.validate(d), "720x1280"))
# ---- R3D performance
d = fresh(); P = jl(d / "out/plan/performance_baked.json"); del P["eng"]; jw(d / "out/plan/performance_baked.json", P); t("incomplete performance: no baked performance for the slot", has(CH.validate(d), "incomplete performance"))
d = fresh(); P = jl(d / "out/plan/performance_baked.json"); P["eng"][0]["state"]["pose"] = "bogus_pose"; jw(d / "out/plan/performance_baked.json", P); t("incomplete performance: a pose that is not a Ricks pose", has(CH.validate(d), "bogus_pose is not a Ricks pose"))
d = fresh(); P = jl(d / "out/plan/performance_baked.json"); P["eng"][0]["state"]["pose"] = "m:nothing/Z"; jw(d / "out/plan/performance_baked.json", P); t("a motion id that is not in the Ricks motion library -> problem", has(CH.validate(d), "motion"))
d = fresh(); spec_edit(d, lambda c: c.update(expressions_required=["terrified"])); t("incomplete performance: a required expression is never performed", has(CH.validate(d), "required expressions never performed"))
d = fresh(); spec_edit(d, lambda c: c.update(poses_required=["flinch"])); t("incomplete performance: a required pose is never performed", has(CH.validate(d), "required poses never performed"))
d = fresh(); rec_edit(d, lambda R: R["characters"]["eng"]["performance"]["probe"]["warnings"].append("unknown face")); t("the rig's own warning while drawing the performance fails G6", has(CH.validate(d), "the rig warned"))
d = fresh(); rec_edit(d, lambda R: R["characters"]["eng"]["performance"].pop("probe")); t("a performance never probed through the rig fails", has(CH.validate(d), "never probed"))
txt = (fresh() / "creative/character_production.json").read_text(); t("timing stays subordinate: the record holds no time fields, only a hash of the baked performance", not any(k in txt for k in ('"seconds"', '"f0"', '"f1"', '"at"', '"start"', '"duration"')) and "slot_sha1" in txt)
P = jl(d / "out/plan/performance_baked.json"); ps = CH.perf_summary(P, "eng"); t("performance summary reads the baked file (poses/faces/frames), nothing is re-timed", ps["frames"] == sum(e["f1"] - e["f0"] + 1 for e in P["eng"]) and "kneel_work" in ps["poses"])
# ---- R3E cards
d = fresh(); next((d / "out/characters/cards/eng").glob("s0003.png")).unlink(); t("missing card -> problem", has(CH.validate(d), "missing card"))
d = fresh(); (d / "out/characters/cards/eng/s0002.png").write_bytes(b"\x89PNG broken"); t("corrupted card -> problem", has(CH.validate(d), "corrupted card"))
d = fresh(); f = d / "out/characters/cards/eng/s0002.png"; im = Image.open(f); im.load(); im2 = im.copy(); im2.putpixel((5, 5), (255, 0, 0, 255)); im2.save(f); t("a card changed after the build -> wrong hash", has(CH.validate(d), "wrong hash"))
d = fresh(); (d / "out/characters/cards/eng/index.json").write_text((d / "out/characters/cards/eng/index.json").read_text() + " "); t("a changed card index -> wrong hash", has(CH.validate(d), "wrong hash for index.json"))
d = fresh(); f = d / "out/characters/cards/eng/s0002.png"; Image.new("RGBA", (1600, 3000), (255, 255, 255, 255)).save(f); rec_edit(d, lambda R: [x.update(sha1=CH.sha(f)) for x in R["characters"]["eng"]["cards"]["images"] if x["file"] == "s0002.png"]); t("a card with no transparent background -> problem", has(CH.validate(d), "fully opaque"))
d = fresh(); f = d / "out/characters/cards/eng/s0002.png"; Image.new("RGBA", (1600, 3000), (0, 0, 0, 0)).save(f); rec_edit(d, lambda R: [x.update(sha1=CH.sha(f)) for x in R["characters"]["eng"]["cards"]["images"] if x["file"] == "s0002.png"]); t("a card with no visible figure -> problem", has(CH.validate(d), "fully transparent"))
d = fresh(); f = d / "out/characters/cards/eng/s0002.png"; Image.new("RGBA", (800, 1500), (0, 0, 0, 0)).save(f); rec_edit(d, lambda R: [x.update(sha1=CH.sha(f)) for x in R["characters"]["eng"]["cards"]["images"] if x["file"] == "s0002.png"]); t("a card whose size differs from its index -> problem", has(CH.validate(d), "the index says"))
d = fresh(); ip = d / "out/characters/cards/eng/index.json"; I = jl(ip); I["who"] = "lady"; jw(ip, I); rec_edit(d, lambda R: R["characters"]["eng"]["cards"].update(index_sha1=CH.sha(ip))); t("cards that belong to another character -> problem", has(CH.validate(d), "another character"))
d = fresh(); ip = d / "out/characters/cards/eng/index.json"; I = jl(ip); I["px"] = [600, 1000]; jw(ip, I); rec_edit(d, lambda R: R["characters"]["eng"]["cards"].update(index_sha1=CH.sha(ip))); b = CH.validate(d); t("cards below the 1280 px production height would be upscaled at 720x1280 -> problem", has(b, "below the 1280 px"))
d = fresh(); ip = d / "out/characters/cards/eng/index.json"; I = jl(ip); I["images"][0]["keys"] = ["eng|front|1|stand|nonexistent||||||||"]; I["images"] = I["images"][:1]; jw(ip, I); rec_edit(d, lambda R: (R["characters"]["eng"]["cards"].update(index_sha1=CH.sha(ip)), R["characters"]["eng"]["cards"].update(images=R["characters"]["eng"]["cards"]["images"][:1]))); t("cards that do not cover the baked performance -> problem", has(CH.validate(d), "do not cover the baked performance"))
R = jl(fresh() / "creative/character_production.json")["characters"]["eng"]["cards"]; t("cards: deterministic naming s0001.., sha1 per drawing, lock path mapped", [x["file"] for x in R["images"]] == ["s%04d.png" % i for i in range(1, R["count"] + 1)] and all(len(x["sha1"]) == 40 for x in R["images"]) and R["lock_path"] == "out/lock/cards/eng")
# ---- the card -> lock seam
d = fresh(); (d / "out/lock").mkdir(parents=True); shutil.copytree(d / "out/characters/cards", d / "out/lock/cards"); t("lock cards identical to the approved cards -> check-lock PASS", CH.lock_problems(d) == [])
f = d / "out/lock/cards/eng/s0004.png"; im = Image.open(f); im.load(); im = im.copy(); im.putpixel((9, 9), (1, 2, 3, 255)); im.save(f); t("a lock that drew a different card than the approved one -> FAIL", has(CH.lock_problems(d), "different s0004.png"))
d = fresh(); t("no lock yet -> reported, not a pass", has(CH.lock_problems(d), "no lock cards"))
# ---- R3H gate integration + approval
d = fresh(); (d / "creative/characters/eng/back.png").write_bytes(b"x"); r = subprocess.run([sys.executable, str(ROOT / "tools/creative_gates.py"), str(d)], capture_output=True, text=True); t("creative_gates.py CLI reports G6 FAIL on a corrupted character", "G6  Characters" in r.stdout and "FAIL" in [l for l in r.stdout.splitlines() if l.startswith("G6")][0])
a = fresh(); b = fresh(); t("approval's character hash is the real character evidence (spec + record + contact sheet)", AP.current(a)["character_sheets_sha1"] == CH.evidence_sha(a) and CH.evidence_sha(a) is not None)
rec_edit(b, lambda R: R.update(film="changed")); t("changing the character record changes the hash approval signs", AP.current(a)["character_sheets_sha1"] != AP.current(b)["character_sheets_sha1"])
# ---- R3I review integration (R2 judge sees the characters)
d = FX.complete_episode(); S = jl(d / "creative/STORYBOARD.json"); req = RV.required_panels(d, S); t("the judge's required panels include a character panel per cast slot", "char_eng" in req and len(req) == len(S["panels"]) + 1)
t("G8 PASS with the character panel scored", RV.g8(d)[0] == "PASS")
J = jl(d / "creative/JUDGE.json"); t("the judge record names the character evidence it read", J["characters_sha1"] == CH.evidence_sha(d) and J["evidence_read"]["characters_sha1"] == J["characters_sha1"] and "char_eng" in J["panels"])
d2 = FX.complete_episode(); r = FX.judge_result(d2, score=9.0); r["panels"].pop("char_eng"); (d2 / "creative/JUDGE.json").unlink(); (d2 / "creative/review_history.json").write_text("[]"); m = None
f = d2 / "creative/_r.json"; jw(f, r)
try: RV.judge_record(d2, f)
except SystemExit as e: m = str(e.code)
t("a judgment that skips the character panel is REFUSED", m and "panel set differs" in m)
d3 = FX.complete_episode(); r = FX.judge_result(d3, ctx="judge-x"); r["panels"]["char_eng"]["score"] = 8.4; (d3 / "creative/JUDGE.json").unlink(); (d3 / "creative/review_history.json").write_text("[]"); f = d3 / "creative/_r.json"; jw(f, r); RV.judge_record(d3, f); t("a character panel at 8.4 fails the creative review (threshold unchanged)", RV.g8(d3)[0] == "FAIL" and has(RV.g8_problems(d3)[0], "char_eng"))
d4 = FX.complete_episode(); rec_edit(d4, lambda R: R.update(film="re-built after the judge")); t("G8 FAILs when the characters changed after the judgment (stale review)", has(RV.g8_problems(d4)[0], "character evidence"))
d5 = FX.complete_episode(); AP.create(d5, "owner", AP.FLAGS); t("the human approves; the judge never does (approval created only by the owner call)", AP.check(d5) == [] and jl(d5 / "approval.json")["reviewer"] == "owner")
rec_edit(d5, lambda R: R.update(film="x")); t("a character change after approval invalidates the approval", AP.check(d5) != [])
j = RV.history(d5); t("judge brief lists the character criteria and evidence", (lambda: (subprocess.run([sys.executable, str(ROOT / "tools/review.py"), "judge-brief", str(d5)], capture_output=True), "CONTACT_SHEET" in (d5 / "creative/JUDGE_BRIEF.md").read_text() and "char_eng" in (d5 / "creative/JUDGE_BRIEF.md").read_text())[1])())
# ---- R3J reference is creative input only, never a render-time dependency
src = "".join((ROOT / "templates/threejs_film" / n).read_text() for n in ("render.mjs", "render_gpu.mjs", "film.js", "puppets.mjs", "poses.mjs")); t("no renderer reads the reference board or reference video", "reference_board" not in src and "references/video" not in src)
# ---- R3L resolution
t("production target constants are 720x1280 @ 30", CH.PROD == (720, 1280) and CH.FPS == 30)
# ---- R3K real fixture: the whole flow on a real canyon copy (real rig drawings, real cards, real lock)
d = FX.copy_episode(); FX.with_characters(d)
t("real fixture: spec -> views -> performance -> cards -> record -> validation PASS", CH.validate(d) == [])
env = dict(os.environ, RICKS_UNAPPROVED_TEST_RUN="1"); r = subprocess.run(["node", str(ROOT / "templates/threejs_film/render.mjs"), str(d / "film.json"), "--export-lock"], capture_output=True, text=True, env=env, timeout=300)
t("real fixture: the real lock export draws exactly the approved cards (byte for byte)", r.returncode == 0 and CH.lock_problems(d) == [])
im = Image.open(d / "creative/characters/CONTACT_SHEET.png"); t("real fixture: contact sheet exists for the judge (views + sample cards)", im.size[0] >= 1000)
print("\n%d FAIL" % len(fails)); sys.exit(1 if fails else 0)
