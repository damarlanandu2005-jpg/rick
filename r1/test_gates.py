#!/usr/bin/env python3
"""R1b regression tests: creative gates + approval.json refuse rule. Run: python3 r1/test_gates.py"""
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT / "tools"))
import creative_gates as CG, approval as AP
sys.path.insert(0, str(ROOT / "r2")); import fixture as FX
fails = []
def t(name, ok): print(("PASS " if ok else "FAIL ") + name); (ok or fails.append(name))
SRC = ROOT / "templates/film_canyon_example"
def episode(): return FX.complete_episode()
def status(d): return {r["gate"]: r["status"] for r in CG.run(d)}
CG.MAX_WARN = 99; CG.WS_MIN = 3.0   # TEST ONLY: the real canyon fixture has 5 WARN and 3.30 w/s; production keeps MAX_WARN = 2, WS_MIN = 3.5 (both asserted below)
d = episode(); s = status(d)
t("G1..G4,G6,G8 PASS on a complete creative folder", all(s[g] == "PASS" for g in ("G1", "G2", "G3", "G4", "G6", "G8")))
t("G7 is SKIP (R4 part), never PASS", s["G7"] == "SKIP")
t("G5 PASS with the test-only warn allowance", s["G5"] == "PASS")
CG.MAX_WARN = 2; CG.WS_MIN = 3.5; t("production allowances: G5 FAIL (5 WARN) and G2 FAIL (3.30 w/s) on the canyon fixture", status(d)["G5"] == "FAIL" and status(d)["G2"] == "FAIL"); CG.MAX_WARN = 99; CG.WS_MIN = 3.0
for name, mut, gate in [("script missing", lambda: (d / "creative/SCRIPT.md").unlink(), "G1"), ("board beat with 1 ref", lambda: (d / "creative/reference_board.json").write_text(json.dumps({"beats": [{"id": 1, "frames": ["a"]}], "department_index": {"x": 1}})), "G3"),
                        ("picture plan row without reason", lambda: (d / "creative/PICTURE_PLAN.md").write_text("| 1 HOOK | a | 1 | x | CLOSE | c | n | n |\n| 2 TWIST | | | | IN SCENE | | | |\n| 3 LAST | | | | IN SCENE | | | |\n"), "G4"),
                        ("a character view file corrupted (R3 G6 validates the real views)", lambda: (d / "creative/characters/eng/front.png").write_bytes(b"x"), "G6"), ("storyboard missing", lambda: (d / "creative/STORYBOARD.json").unlink(), "G8")]:
    d = episode(); mut(); t("%s -> %s FAIL" % (name, gate), status(d)[gate] == "FAIL")
d = episode(); W = json.load(open(d / "voice/words.json")); json.dump([dict(w=x["w"], s=x["s"] * 3, e=x["e"] * 3) for x in W], open(d / "voice/words.json", "w")); t("G2 FAILs when speech is too slow", status(d)["G2"] == "FAIL")
# approval
d = episode(); t("no approval.json -> refused", AP.check(d) != [] and "missing" in AP.check(d)[0])
if status(d)["G5"] == "PASS":
    AP.create(d, "owner", AP.FLAGS); t("create -> check is clean", AP.check(d) == [])
    for fname in ("film.json", "creative/PICTURE_PLAN.md", "creative/LOOK_BIBLE.md", "creative/STORYBOARD.json", "creative/ANIMATIC.json", "creative/reference_board.json", "out/plan/camera_baked.json"):
        p = d / fname; old = p.read_bytes(); p.write_bytes(old + b" ")
        t("changing %s makes approval STALE" % fname, any("STALE" in x for x in AP.check(d)) or any("changed" in x for x in AP.check(d))); p.write_bytes(old)
    t("restoring the file makes it fresh again", AP.check(d) == [])
    A = json.load(open(d / "approval.json")); A["approvals"]["look"]["value"] = False; json.dump(A, open(d / "approval.json", "w")); t("a false approval flag -> refused", any("look" in x for x in AP.check(d)))
    A["approvals"]["look"]["value"] = True; A["judge"]["reviewer"] = A["reviewer"]; json.dump(A, open(d / "approval.json", "w")); t("judge == approver -> refused", any("judge" in x for x in AP.check(d)))
    A = json.load(open(d / "approval.json")); del A["animatic_sha1"]; json.dump(A, open(d / "approval.json", "w")); t("missing required field -> refused", any("animatic_sha1" in x for x in AP.check(d)))
else: print("SKIP approval freshness tests: fixture plan check is not clean (G5 %s)" % status(d)["G5"]); fails.append("fixture G5 not clean")
d = episode(); (d / "creative/STORYBOARD.json").unlink()
try: AP.create(d, "owner", AP.FLAGS); ok = False
except SystemExit as e: ok = "REFUSED" in str(e.code)
t("create refuses when a creative gate FAILs", ok and not (d / "approval.json").exists())
d = episode()
try: AP.create(d, "owner", ["creative"]); ok = False
except SystemExit as e: ok = "REFUSED" in str(e.code)
t("create refuses unless all six approvals are named", ok)
# pipeline + renderer refuse without approval (no rendering happens: they stop at G9 / the guard)
d = episode(); r = subprocess.run([sys.executable, str(ROOT / "tools/pipeline.py"), str(d)], capture_output=True, text=True); t("pipeline STOPs before any base render without approval (at G1-G8 or G9)", r.returncode != 0 and ("G9" in r.stdout or "G1-G8" in r.stdout) and "STOP" in (r.stderr + r.stdout) and "2 base" not in r.stdout and not (d / "out/stills/_base_key.json").exists())
env = dict(os.environ); env.pop("RICKS_UNAPPROVED_TEST_RUN", None); r = subprocess.run(["node", str(ROOT / "templates/threejs_film/render.mjs"), str(d / "film.json"), "--export-lock"], capture_output=True, text=True, env=env, timeout=120); t("render.mjs --export-lock refuses without approval (exit 3)", r.returncode == 3 and "REFUSED" in r.stderr)
print("\n%d FAIL" % len(fails)); sys.exit(1 if fails else 0)
