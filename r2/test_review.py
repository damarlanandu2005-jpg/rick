#!/usr/bin/env python3
"""R2 tests: storyboard (R2A), animatic (R2B), judge (R2C), one-fix-round (R2D), G8 (R2E), approval integration (R2F), pipeline chain (R2G).  python3 r2/test_review.py"""
import json, os, shutil, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(ROOT / "r2"))
import review as RV, approval as AP, creative_gates as CG, fixture as FX
fails = []; quiet = lambda f, *a, **k: f(*a, **k)
def t(name, ok): print(("PASS " if ok else "FAIL ") + name); (ok or fails.append(name))
def exits(fn, *a):
    try: fn(*a); return None
    except SystemExit as e: return str(e.code) if e.code not in (0, None) else ""
def rec(d, res): return exits(FX.record, d, res)
def has(bad, word): return any(word in x for x in bad)
CG.MAX_WARN = 99; CG.WS_MIN = 3.0      # TEST ONLY (real canyon: 5 WARN, 3.30 w/s). The production values are asserted in r1/test_gates.py
mk = lambda: FX.copy_episode()
def valid(): d = mk(); FX.build_artifacts(d); return d
# ---- R2A storyboard
d = mk(); S, b = RV.validate_storyboard(d); t("A missing storyboard -> problem", S is None and has(b, "missing"))
d = valid(); S, b = RV.validate_storyboard(d); t("A valid storyboard has no problems", b == [] and len(S["panels"]) == 2 * len(S["stations"]))
t("A stations are derived from the baked camera (4 stations, 8 panels on the canyon)", len(S["stations"]) == 4 and len(S["panels"]) == 8)
d1, d2 = valid(), valid(); t("A deterministic: same plan -> identical storyboard document", (d1 / "creative/STORYBOARD.json").read_text().replace(str(d1), "") == (d2 / "creative/STORYBOARD.json").read_text().replace(str(d2), "") or json.load(open(d1 / "creative/STORYBOARD.json")) == json.load(open(d2 / "creative/STORYBOARD.json")))
d = valid(); (d / "creative/STORYBOARD.json").write_text("{not json"); t("A malformed JSON -> problem", has(RV.validate_storyboard(d)[1], "malformed"))
d = valid(); X = json.load(open(d / "creative/STORYBOARD.json")); del X["panels"]; json.dump(X, open(d / "creative/STORYBOARD.json", "w")); t("A malformed (missing field) -> problem", has(RV.validate_storyboard(d)[1], "malformed"))
d = valid(); X = json.load(open(d / "creative/STORYBOARD.json")); X["panels"] = X["panels"][:-1]; json.dump(X, open(d / "creative/STORYBOARD.json", "w")); t("A a station without its END panel -> problem", has(RV.validate_storyboard(d)[1], "no END panel"))
d = valid(); p = d / "film.json"; p.write_bytes(p.read_bytes() + b" "); t("A stale storyboard (film.json changed) -> STALE", has(RV.validate_storyboard(d)[1], "STALE"))
d = valid(); w = FX.copy_episode("templates/film_western_example"); shutil.copy(d / "creative/STORYBOARD.json", w / "creative/STORYBOARD.json"); t("A storyboard generated from the wrong plan -> STALE/mismatch", has(RV.validate_storyboard(w)[1], "STALE") or has(RV.validate_storyboard(w)[1], "n_frames"))
d = valid(); f = next((d / "out/storyboard_panels").glob("*.png")); f.write_bytes(b"swapped"); t("A tampered panel file -> problem", has(RV.validate_storyboard(d)[1], "changed after"))
d = valid(); next((d / "out/storyboard_panels").glob("*.png")).unlink(); t("A missing panel file -> problem", has(RV.validate_storyboard(d)[1], "panel file missing"))
d = mk(); FX.make_panels(d); next((d / "out/storyboard_panels").glob("s01_end*")).unlink(); t("A make_storyboard_doc refuses when render left a panel out", exits(RV.make_storyboard_doc, d) is not None)
# ---- R2B animatic
d = mk(); A, b = RV.validate_animatic(d); t("B missing animatic -> problem", A is None and has(b, "missing"))
d = valid(); A, b = RV.validate_animatic(d); t("B valid animatic has no problems", b == [])
t("B whole-film rough covers frames 0-298 and is labelled whole film", A["artifacts"][0]["covers_whole_film"] and "WHOLE-FILM" in A["artifacts"][0]["label"])
t("B hook artifact is labelled HOOK-PARTIAL, NOT a full-film review", not A["artifacts"][1]["covers_whole_film"] and "NOT a full-film review" in A["artifacts"][1]["label"])
d = valid(); p = d / "film.json"; p.write_bytes(p.read_bytes() + b" "); t("B stale animatic (plan changed) -> STALE", has(RV.validate_animatic(d)[1], "STALE"))
d = valid(); X = json.load(open(d / "creative/ANIMATIC.json")); X["plan_sha1"] = "0" * 40; json.dump(X, open(d / "creative/ANIMATIC.json", "w")); t("B wrong plan hash -> STALE", has(RV.validate_animatic(d)[1], "wrong plan"))
d = valid(); X = json.load(open(d / "creative/ANIMATIC.json")); X["baked_sha1"] = "0" * 40; json.dump(X, open(d / "creative/ANIMATIC.json", "w")); t("B wrong baked-plan hash -> STALE", has(RV.validate_animatic(d)[1], "STALE"))
d = valid(); FX.make_video(d / "out/animatic.mp4", 50, 30); X = json.load(open(d / "creative/ANIMATIC.json")); X["artifacts"][0]["video_sha1"] = RV.sha(d / "out/animatic.mp4"); json.dump(X, open(d / "creative/ANIMATIC.json", "w")); t("B wrong frame set (video has 50 frames, expects 300) -> problem", has(RV.validate_animatic(d)[1], "wrong frame set"))
d = valid(); X = json.load(open(d / "creative/ANIMATIC.json")); X["artifacts"][0]["frame_set"]["last"] = 100; json.dump(X, open(d / "creative/ANIMATIC.json", "w")); t("B whole-film rough that stops at frame 100 -> problem", has(RV.validate_animatic(d)[1], "whole-film-rough does not cover"))
d = valid(); X = json.load(open(d / "creative/ANIMATIC.json")); X["artifacts"][0]["frame_set"]["last"] = 299; json.dump(X, open(d / "creative/ANIMATIC.json", "w")); t("B frame set reaching N (0-299) -> problem (frame semantics)", has(RV.validate_animatic(d)[1], "outside 0..298"))
d = valid(); X = json.load(open(d / "creative/ANIMATIC.json")); X["artifacts"] = X["artifacts"][1:]; json.dump(X, open(d / "creative/ANIMATIC.json", "w")); b = RV.validate_animatic(d)[1]; t("B hook only (no whole-film rough) -> problem: a hook is not a full-film review", has(b, "no whole-film rough"))
d = valid(); X = json.load(open(d / "creative/ANIMATIC.json")); X["artifacts"][1]["label"] = "whole film"; json.dump(X, open(d / "creative/ANIMATIC.json", "w")); t("B hook mislabelled as a full review -> problem", has(RV.validate_animatic(d)[1], "labelled NOT"))
d = valid(); (d / "out/animatic.mp4").write_bytes(b"x"); t("B video swapped after recording -> problem", has(RV.validate_animatic(d)[1], "changed after") or has(RV.validate_animatic(d)[1], "frame"))
# ---- R2C judge
d = valid(); t("C a passing judgment is recorded as PASS", rec(d, FX.judge_result(d)) == "" or RV.history(d)[-1]["result"] == "PASS")
J = json.load(open(d / "creative/JUDGE.json")); t("C judge artifact holds every required field", all(k in J for k in ("version", "plan_sha1", "storyboard_sha1", "animatic_sha1", "judge", "timestamp", "panels", "result", "fix_round", "verdict", "reviewer", "score", "fix_list_sha1")) and all("rationale" in v for v in J["panels"].values()))
d = valid(); S = json.load(open(d / "creative/STORYBOARD.json")); one = RV.panel_ids(S)[3]; rec(d, FX.judge_result(d, low={one: 8.4})); J = json.load(open(d / "creative/JUDGE.json")); t("C ONE panel at 8.4 -> FAIL (threshold 8.5 on every panel)", J["result"] == "FAIL" and one in J["below_threshold"])
d = valid(); rec(d, FX.judge_result(d, score=8.5)); t("C every panel exactly 8.5 -> PASS", json.load(open(d / "creative/JUDGE.json"))["result"] == "PASS")
d = valid(); rec(d, FX.judge_result(d, film="FAIL")); t("C film-level FAIL -> FAIL", json.load(open(d / "creative/JUDGE.json"))["result"] == "FAIL")
d = valid(); rec(d, FX.judge_result(d, sd="BACK")); t("C studio-director BACK -> FAIL", json.load(open(d / "creative/JUDGE.json"))["result"] == "FAIL")
d = valid(); r = FX.judge_result(d); r["result"] = "PASS"; r["panels"][RV.panel_ids(json.load(open(d / "creative/STORYBOARD.json")))[0]]["score"] = 3; rec(d, r); t("C the judge cannot declare its own result (computed)", json.load(open(d / "creative/JUDGE.json"))["result"] == "FAIL")
d = valid(); m = rec(d, FX.judge_result(d, ctx="creator-ctx")); t("C judge in the builder's context -> REFUSED (cannot judge its own work)", m and "fresh context" in m and not (d / "creative/JUDGE.json").exists())
d = valid(); m = rec(d, FX.judge_result(d, jid="creator-ctx")); t("C judge id equals builder id -> REFUSED", m and "builder id" in m)
d = valid(); r = FX.judge_result(d); r["evidence_read"]["animatic_sha1"] = "0" * 40; m = rec(d, r); t("C judge that did not read the current evidence -> REFUSED", m and "did not read" in m)
d = valid(); r = FX.judge_result(d); r["panels"].pop(next(iter(r["panels"]))); m = rec(d, r); t("C a missing required panel -> REFUSED", m and "panel set differs" in m)
d = valid(); r = FX.judge_result(d); r["panels"]["bogus"] = {"score": 9, "rationale": "x"}; m = rec(d, r); t("C an unknown extra panel -> REFUSED", m and "panel set differs" in m)
d = valid(); r = FX.judge_result(d); r["panels"][next(iter(r["panels"]))]["rationale"] = ""; m = rec(d, r); t("C a score without rationale -> REFUSED", m and "rationale" in m)
d = mk(); m = exits(RV.judge_record, d, d / "nothing.json"); t("C judging with no evidence -> REFUSED", m is not None)
# ---- R2D one fix round
d = valid(); rec(d, FX.judge_result(d, score=7.0)); H = RV.history(d); t("D version 1 FAIL recorded at fix_round 0", len(H) == 1 and H[0]["result"] == "FAIL" and json.load(open(d / "creative/JUDGE.json"))["fix_round"] == 0)
m = rec(d, FX.judge_result(d, ctx="judge-ctx-2")); t("D re-judging with NO change after a FAIL -> REFUSED (a fix round must change the work)", m and "nothing changed" in m)
FX.build_artifacts(d, version=2); m = rec(d, FX.judge_result(d, ctx="judge-ctx-2")); J = json.load(open(d / "creative/JUDGE.json")); t("D version 2 (the one fix round) is judged at fix_round 1 and may PASS", m is None and J["fix_round"] == 1 and J["result"] == "PASS")
d = valid(); rec(d, FX.judge_result(d, score=7.0)); FX.build_artifacts(d, version=2); rec(d, FX.judge_result(d, score=7.0, ctx="judge-ctx-2")); t("D version 2 FAIL recorded (fix round used)", [h["result"] for h in RV.history(d)] == ["FAIL", "FAIL"])
FX.build_artifacts(d, version=3, builder="creator-ctx-3"); m = rec(d, FX.judge_result(d, score=9.5, ctx="judge-ctx-3")); t("D version 3 is REFUSED even with perfect scores (fail closed)", m and "fix round is used" in m and len(RV.history(d)) == 2)
bad, _ = RV.g8_problems(d); t("D G8 fails closed after two FAILs (more than one fix round)", has(bad, "fix-round") or has(bad, "below") or has(bad, "9 scores"))
RV.new_version(d, "owner", "new creative direction"); t("D only an owner reset reopens judging (history archived, not deleted)", RV.history(d) == [] and list((d / "creative").glob("review_history_archive_*.json")) != [])
FX.build_artifacts(d, version=3, builder="creator-ctx-3"); (d / "creative/JUDGE.json").unlink(); m = rec(d, FX.judge_result(d, ctx="judge-ctx-3")); t("D after the owner reset a fresh version is judged at fix_round 0", m is None and json.load(open(d / "creative/JUDGE.json"))["fix_round"] == 0)
d = valid(); rec(d, FX.judge_result(d)); FX.build_artifacts(d, version=2); m = rec(d, FX.judge_result(d, ctx="judge-ctx-2")); t("D after a PASS, a changed storyboard can be judged again only inside the limit (2 total)", m is None and len(RV.history(d)) == 2)
# ---- R2E G8
d = valid(); rec(d, FX.judge_result(d)); s, note = RV.g8(d); t("E G8 PASS on a fully valid, judged, fresh episode", s == "PASS")
d = valid(); s, note = RV.g8(d); t("E G8 FAIL when files exist but there is no judge record (existence alone is not a pass)", s == "FAIL" and "judge record missing" in note)
d = valid(); rec(d, FX.judge_result(d)); p = d / "creative/JUDGE.json"; J = json.load(open(p)); k = next(iter(J["panels"])); J["panels"][k]["score"] = 8.4; json.dump(J, open(p, "w")); t("E G8 recomputes scores: a hand-edited 8.4 is caught", RV.g8(d)[0] == "FAIL")
d = valid(); rec(d, FX.judge_result(d)); p = d / "creative/JUDGE.json"; J = json.load(open(p)); J["judge"]["context_id"] = "creator-ctx"; json.dump(J, open(p, "w")); t("E G8 FAILs a judge that shares the builder's context", has(RV.g8_problems(d)[0], "independence"))
d = valid(); rec(d, FX.judge_result(d)); FX.build_artifacts(d, version=2); t("E G8 FAILs when the storyboard was regenerated (changed) after the judgment (stale review)", has(RV.g8_problems(d)[0], "11 stale"))
d = valid(); rec(d, FX.judge_result(d)); FX.build_artifacts(d); t("E regenerating an identical storyboard from the same plan is deterministic: the judgment stays valid", RV.g8(d)[0] == "PASS")
d = valid(); rec(d, FX.judge_result(d)); p = d / "film.json"; p.write_bytes(p.read_bytes() + b" "); t("E G8 FAILs when the plan changed after judging (stale)", RV.g8(d)[0] == "FAIL" and has(RV.g8_problems(d)[0], "STALE"))
d = valid(); rec(d, FX.judge_result(d)); p = d / "creative/JUDGE.json"; J = json.load(open(p)); J["fix_round"] = 1; json.dump(J, open(p, "w")); t("E G8 FAILs a judge record whose fix_round contradicts the history", has(RV.g8_problems(d)[0], "fix-round"))
d = valid(); rec(d, FX.judge_result(d)); (d / "creative/review_history.json").unlink(); t("E G8 FAILs without the review history", has(RV.g8_problems(d)[0], "fix-round"))
d = valid(); rec(d, FX.judge_result(d)); p = d / "creative/JUDGE.json"; J = json.load(open(p)); J["storyboard_sha1"] = "0" * 40; json.dump(J, open(p, "w")); t("E G8 FAILs a judge record pointing at other evidence", RV.g8(d)[0] == "FAIL")
d = valid(); rec(d, FX.judge_result(d)); X = json.load(open(d / "creative/ANIMATIC.json")); X["artifacts"] = X["artifacts"][1:]; json.dump(X, open(d / "creative/ANIMATIC.json", "w")); t("E G8 FAILs when only the hook exists", RV.g8(d)[0] == "FAIL")
# ---- R2F approval integration
d = FX.complete_episode(); t("F G1-G8 all PASS (G7 SKIP) on the complete synthetic episode", {r["gate"]: r["status"] for r in CG.run(d)}["G8"] == "PASS")
t("F nothing in the review flow created approval.json", not (d / "approval.json").exists())
AP.create(d, "owner", AP.FLAGS); t("F the human creates approval.json and it checks clean", AP.check(d) == [])
A = json.load(open(d / "approval.json")); t("F approval copies the judge record fields from the real JUDGE.json", A["judge"]["verdict"] == "PASS" and A["judge"]["reviewer"] == "storyboard-judge#1" and A["reviewer"] == "owner")
p = d / "creative/JUDGE.json"; J = json.load(open(p)); old = p.read_text(); k = next(iter(J["panels"])); J["panels"][k]["score"] = 5; p.write_text(json.dumps(J)); t("F G9 re-checks G8: a judge record altered AFTER approval invalidates it", any("G8 no longer passes" in x for x in AP.check(d))); p.write_text(old); t("F restoring the record makes the approval valid again", AP.check(d) == [])
(d / "approval.json").unlink()
for who in ("judge-ctx-1", "storyboard-judge#1"):
    m = exits(AP.create, d, who, AP.FLAGS); t("F the judge (%s) as the approver -> REFUSED, no approval.json left" % who, m is not None and "judge cannot be the approver" in m and not (d / "approval.json").exists())
d3 = FX.copy_episode(); FX.build_artifacts(d3); rec(d3, FX.judge_result(d3, score=7.0)); (d3 / "creative").mkdir(exist_ok=True); m = exits(AP.create, d3, "owner", AP.FLAGS); t("F a FAILED judge never becomes an approval (create refuses)", m is not None and "REFUSED" in m and not (d3 / "approval.json").exists())
import re; src = (ROOT / "tools/review.py").read_text(); t("F review.py contains no code that writes approval.json", not re.search(r"approval\.json.{0,6}\)?\.write|write_text\([^)]*approval|open\([^)]*approval[^)]*.w.", src))
# ---- R2G pipeline chain: production pipeline must stop before any expensive render for each missing/invalid R2 artifact
def pipeline_stop(d, expect):
    env = dict(os.environ); env.pop("RICKS_UNAPPROVED_TEST_RUN", None); r = subprocess.run([sys.executable, str(ROOT / "tools/pipeline.py"), str(d), "--frames", "0-1", "--renderer", "cpu"], capture_output=True, text=True, env=env)
    import re; return r.returncode != 0 and "STOPPED" in r.stdout and "Expensive render happened: NO" in r.stdout and not re.search(r"^(7 base|9 final)\s+(PASS|FAIL)", r.stdout, re.M) and not (d / "out/stills/_base_key.json").exists()
for name, mut in [("no storyboard", lambda d: (d / "creative/STORYBOARD.json").unlink()), ("no animatic", lambda d: (d / "creative/ANIMATIC.json").unlink()), ("no judge record", lambda d: (d / "creative/JUDGE.json").unlink()), ("stale plan", lambda d: (d / "film.json").write_bytes((d / "film.json").read_bytes() + b" "))]:
    d = FX.complete_episode(); mut(d); t("G pipeline stops before base render: %s" % name, pipeline_stop(d, "G1-G8"))
d = FX.complete_episode(); t("G pipeline stops before base render on the real canyon thresholds (G2/G5 FAIL, no approval)", pipeline_stop(d, "G1-G8"))
# the same chain at the renderer: --export-lock refuses without a valid approval even when G8 passes
d = FX.complete_episode(); env = dict(os.environ); env.pop("RICKS_UNAPPROVED_TEST_RUN", None); r = subprocess.run(["node", str(ROOT / "templates/threejs_film/render.mjs"), str(d / "film.json"), "--export-lock"], capture_output=True, text=True, env=env, timeout=120); t("G --export-lock refuses without approval.json even when G8 passes", r.returncode == 3)
AP.create(d, "owner", AP.FLAGS); (d / "creative/JUDGE.json").unlink(); r = subprocess.run(["node", str(ROOT / "templates/threejs_film/render.mjs"), str(d / "film.json"), "--export-lock"], capture_output=True, text=True, env=env, timeout=120); t("G --export-lock refuses an approval whose judge evidence disappeared", r.returncode == 3)
print("\n%d FAIL" % len(fails)); sys.exit(1 if fails else 0)
