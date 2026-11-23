"""Shared synthetic fixtures for R2/R1 tests: valid storyboard, animatic and judge artifacts for a copied example episode, with no rendering of the real scene
(panel PNGs are tiny stand-ins; animatic videos are ffmpeg test patterns with the exact expected frame counts)."""
import json, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT / "tools"))
import review as RV, frames as FR, characters as CH
def copy_episode(src="templates/film_canyon_example"):
    d = Path(tempfile.mkdtemp()) / "ep"; shutil.copytree(ROOT / src, d); (d / "creative").mkdir(exist_ok=True)
    subprocess.run([sys.executable, str(ROOT / "tools/film_plan.py"), "check", str(d / "film.json")], capture_output=True); return d
BOARD = {"beats": [{"id": 1, "kind": "wide", "frames": ["a", "b"]}], "department_index": {"set": "x"}}
SPEC = {"schema": "ricks.character_spec.v1", "film": "canyon", "characters": {"eng": {"character": "char_stationmaster", "version": "1.0", "role": "railway engineer repairing the track", "traits": ["kneels to work", "holds a hammer", "points at the bridge"], "outfit": "stationmaster uniform, locked cast outfit", "views_required": ["front", "34", "side", "back"], "expressions_required": ["standard"], "poses_required": ["kneel_work", "point_out"], "reference_beats": [1]}}}
def with_characters(d, cache=[None]):
    """Real R3 character products for the canyon copy (real views, probe and cards), built ONCE per test run and copied into each fixture episode."""
    d = Path(d); c = d / "creative"; c.mkdir(exist_ok=True); (c / "reference_board.json").write_text(json.dumps(BOARD)); (c / "characters.json").write_text(json.dumps(SPEC))
    if cache[0] is None:
        b = copy_episode(); (b / "creative").mkdir(exist_ok=True); (b / "creative/reference_board.json").write_text(json.dumps(BOARD)); (b / "creative/characters.json").write_text(json.dumps(SPEC)); CH.build(b); cache[0] = b
    b = cache[0]; shutil.copy(b / "creative/character_production.json", c / "character_production.json"); shutil.rmtree(c / "characters", ignore_errors=True); shutil.copytree(b / "creative/characters", c / "characters")
    shutil.rmtree(d / "out/characters", ignore_errors=True); shutil.copytree(b / "out/characters", d / "out/characters")
def make_panels(d):
    pd = d / "out/storyboard_panels"; shutil.rmtree(pd, ignore_errors=True); pd.mkdir(parents=True)
    for s in RV.derive_stations(d):
        for k in ("start", "end"): (pd / ("%s_%s_f%d.png" % (s["id"], k, s[k]))).write_bytes(("png %s %s %d" % (s["id"], k, s[k])).encode())
def make_video(path, count, fps=10):
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=64x64:rate=%d" % fps, "-frames:v", str(count), "-pix_fmt", "yuv420p", str(path)], capture_output=True, text=True); assert r.returncode == 0, r.stderr
def build_artifacts(d, builder="creator-ctx", version=1, step=3, hook_s=3.0):
    with_characters(d); N = FR.film_frame_count(d); make_panels(d); (d / "creative").mkdir(exist_ok=True)
    (d / "creative/STORYBOARD.json").write_text(json.dumps(RV.make_storyboard_doc(d, version, builder), indent=1))
    out = d / "out"; whole, hook = out / "animatic.mp4", out / "animatic_hook.mp4"; make_video(whole, len(RV.expected_set(0, N - 1, step)) * step, 30)
    fps = json.load(open(out / "plan/camera_baked.json"))["fps"]; k = max(1, int(-(-hook_s * fps // step))); make_video(hook, k * step, 30)
    D = RV.make_animatic_doc(d, whole, hook, step, hook_s, builder); h = D["artifacts"][1]; h["frame_set"].update(last=(k - 1) * step, count=k); h["video_frames"] = k * step; h["label"] = "HOOK-PARTIAL, frames 0-%d of 0-%d: NOT a full-film review" % ((k - 1) * step, N - 1)
    (d / "creative/ANIMATIC.json").write_text(json.dumps(D, indent=1))
def judge_result(d, score=9.0, low=None, ctx="judge-ctx-1", jid="storyboard-judge#1", film="PASS", sd="PASS"):
    S = json.load(open(d / "creative/STORYBOARD.json")); sb, an = RV.sha(d / "creative/STORYBOARD.json"), RV.sha(d / "creative/ANIMATIC.json")
    P = {i: {"score": (low or {}).get(i, score), "rationale": "reads clearly", "fix": "none" if (low or {}).get(i, score) >= 8.5 else "raise the aim 0.2 m"} for i in RV.required_panels(d, S)}
    return {"judge": {"id": jid, "context_id": ctx, "kind": "fresh-context", "agents": ["storyboard-judge", "studio-director"]}, "evidence_read": {"storyboard_sha1": sb, "animatic_sha1": an, "characters_sha1": RV.char_sha(d)}, "panels": P, "film_level": {"verdict": film, "notes": "ok"}, "studio_director": {"verdict": sd, "note": "ok"}}
def record(d, res):
    f = d / "creative/_result.json"; f.write_text(json.dumps(res)); return RV.judge_record(d, f)
def complete_episode():
    """A canyon copy with every creative input G1-G6 needs plus REAL-format R2 artifacts (synthetic pictures) and a PASSING judge record. Test-only allowances (CG.WS_MIN, CG.MAX_WARN) are set by the caller because the real canyon is 3.30 w/s and 5 WARN."""
    d = copy_episode(); c = d / "creative"
    (c / "SCRIPT.md").write_text("the train rolls into the canyon and the hero looks up at the high bridge ahead of them " * 3)
    (c / "PICTURE_PLAN.md").write_text("| # | words | sec | see | shown | feeling | fx | piece |\n|---|---|---|---|---|---|---|---|\n| 1 HOOK | a | 0.5 | x | IN SCENE, the size is the joke | calm | none | none |\n| 2 TWIST | b | 3 | x | CLOSE: this is the claim it turns on | sure | none | none |\n| 3 LAST | c | 8 | x | NOT SHOWN, it would break the scene here | none | none | none |\n")
    (c / "LOOK_BIBLE.md").write_text("look bible")
    build_artifacts(d); assert record(d, judge_result(d)) == "PASS"; return d
