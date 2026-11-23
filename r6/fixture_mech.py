#!/usr/bin/env python3
"""TEST_FIXTURE_ONLY (R5 mechanical closure / R6 positive path). A SYNTHETIC production fixture that exists ONLY to prove approval -> lock -> final render -> composite -> MP4 -> QA mechanically.
It is NOT the rejected "Hat Toss" (different script, film, set wrapper, picture plan) and it is NEVER a creative pass: every creative artifact is a stand-in, the judge result is synthetic and the approval is a test-harness approval.
Everything it exercises is the existing code (characters.py build, review.py, approval.py create, assets.py, creative_gates.py, pipeline.py); it adds no second approval or judge system.
Markers: creative/TEST_FIXTURE_ONLY.json (read by tools/approval.py -> approval.json carries production:false + test_fixture_only:true; the pipeline stamps every output production:false).
  python3 r6/fixture_mech.py <dir>     builds <dir>/ep and <dir>/registry.json (a registry COPY with the barrel flipped to approved by 'TEST_FIXTURE_ONLY harness'; the committed registry is never changed)"""
import copy, hashlib, json, os, re, shutil, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(ROOT / "r2"))
from PIL import Image, ImageDraw
SCRIPT = "The engineer kneels by the dusty track at noon and taps one rusty rail twice. Then he looks up at the canyon, so deep that nobody ever sees the bottom. He just grins, because the train is already coming. And the only thing he truly fears is a late schedule, so he checks his watch."
ASSET = "prop_rail_handcar"
FILM = {"title": "CANYON RAIL: first 10 s of a railroad short, recreated through the hybrid pipeline (Phase 8 second-script test; the script is read from a reference short's captions, not fact-checked)", "fps": 30, "size": [1080, 1920], "words": "voice/words.json", "camera_idea": {"name": "The long cut", "why": "One engineer on a track in a canyon cut: the camera starts at the rail with the train behind him, rises as he stands to read the walls, then leaves him and flows out along the track to the edge of the canyon and over the void.", "signature": "The flow: after the word canyon the camera never rests again, it runs out over the trestle into the blue."}, "cast": {"eng": {"puppet": "stationmaster", "height": 1.75, "heads_tall": 2.9}}, "places": {"canyon": {"set": "canyon_rail", "light": "day", "backdrop": 5.5}}, "props": {"train": {"pos": [0, 8, 1.2], "kind": "train"}, "trestle": {"pos": [0, 32, -0.2], "kind": "trestle"}, "rail": {"pos": [0.72, 0, 0.1], "kind": "rail"}}, "takes": [{"id": "t1", "place": "canyon", "stations": [{"at": 0, "pos": [-1.24, -2.56, 0.86], "aim": [0, 0, 1.15], "lens": 28, "subject": "eng", "framing": "M", "hold": 1.7}, {"at": ["canyon", 1], "lead": 16, "pos": [2.24, 7.51, 3.03], "aim": [2.6, 19.6, -8], "lens": 28, "framing": "W", "shows": ["trestle"], "word": "canyon", "hold": 0.4, "travel": 2.9, "via": [[-0.3, 7.0, 5.6]], "subject": "eng"}, {"at": ["grins", 1], "lead": 10, "pos": [1.96, -2.37, 0.58], "aim": [0, 0, 1.25], "lens": 28, "subject": "eng", "framing": "W", "word": "grins", "travel": 2.9, "hold": 0.5}]}], "kicks": [], "acts": [{"who": "eng", "at": 0, "pos": [0, 0, 0], "view": "front", "dir": 1, "pose": "kneel_work", "face": "standard"}, {"who": "eng", "at": ["taps", 1], "pose": "kneel_hammer_hit", "face": "cool"}, {"who": "eng", "at": ["Then", 1], "pose": "stand", "face": "sus"}, {"who": "eng", "at": ["canyon", 1], "pose": "point_out", "face": "standard"}, {"who": "eng", "at": ["grins", 1], "pose": "hands_hips", "face": "proud"}, {"who": "eng", "at": ["fears", 1], "pose": "stand", "face": "sus"}, {"who": "eng", "at": ["checks", 1], "pose": "point_out", "face": "cool"}, {"who": "eng", "at": ["late", 1], "pose": "stand", "face": "standard"}, {"who": "eng", "at": ["coming", 1], "pose": "stand", "face": "sus"}, {"who": "eng", "at": ["schedule", 1], "pose": "hands_hips", "face": "proud"}], "sentences": [{"text": "The engineer kneels by the dusty track at noon and taps one rusty rail twice.", "words": [0, 14], "subject": "eng"}, {"text": "Then he looks up at the canyon, so deep that nobody ever sees the bottom.", "words": [15, 29], "subject": "eng", "nouns": [{"word": "canyon", "show": "trestle"}]}, {"text": "He just grins, because the train is already coming.", "words": [30, 38], "subject": "eng", "show": ["train"]}, {"text": "And the only thing he truly fears is a late schedule, so he checks his watch.", "words": [39, 54], "subject": "eng"}], "fx": [{"at": ["taps", 1], "kind": "sparks", "on": "rail"}, {"at": ["train", 1], "kind": "whistle", "on": "train"}], "moods": [{"at": ["canyon", 1], "look": "cold_blue"}], "sound": [], "flights": [], "layers": []}
FILM.update(title="TEST_FIXTURE_ONLY: mechanical closure fixture (synthetic, not a creative film)", words="voice/words.json")
FILM["cast"] = {"eng": {"puppet": "stationmaster", "height": 1.75, "heads_tall": 2.9}}
FILM["places"] = {"canyon": {"set": "canyon_rail", "light": "day", "backdrop": 5.5, "assets": [ASSET + "@1.0"]}}
FILM["camera_idea"] = {"name": "The patient orbit", "why": "synthetic fixture: a slow orbit round one engineer on a canyon rail", "signature": "one orbit, no cuts"}
SPEC = {"schema": "ricks.character_spec.v1", "film": "test_fixture_only", "characters": {"eng": {"character": "char_stationmaster", "version": "1.0", "role": "TEST_FIXTURE_ONLY stand-in: a railway engineer on a canyon rail", "traits": ["kneels to work", "points at the canyon"], "outfit": "stationmaster uniform, locked cast outfit", "views_required": ["front", "34", "side", "back"], "expressions_required": ["standard", "cool", "sus", "proud"], "poses_required": ["kneel_work", "kneel_hammer_hit", "stand", "point_out", "hands_hips"], "reference_beats": [1, 2]}}}
PLAN = ("TEST_FIXTURE_ONLY synthetic picture plan\n\n| # | words | sec | see | shown | feeling | fx | piece | ref |\n|---|---|---|---|---|---|---|---|---|\n"
        "| 1 HOOK | The engineer kneels by the dusty track | 0.5 | medium on the engineer | IN SCENE, the size is the joke | calm | sparks | the handcar | 1: b1_a, b1_b |\n"
        "| 2 TWIST | Then he looks up at the canyon | 3 | wide, the canyon behind him | CLOSE: the canyon is the claim it turns on | awe | none | none | 2: b2_a, b2_b |\n"
        "| 3 LAST | He just grins, the train is coming | 7 | wide again | NOT SHOWN, it would break the awe here | still | none | none | 3: b3_a, b3_b |\n")
def sha(p): return hashlib.sha1(Path(p).read_bytes()).hexdigest()
def words(path):
    ws = SCRIPT.split(); raw = []; t = 0.0
    for w in ws: d = 0.10 + 0.045 * len(re.sub(r"\W", "", w)); raw.append([w, t, t + d]); t += d + (0.26 if re.search(r"[.?!]$", w) else 0.05)
    k = (len(ws) / 4.0) / raw[-1][2]; out = [{"w": w, "s": round(s * k, 3), "e": round(e * k, 3)} for w, s, e in raw]; Path(path).parent.mkdir(parents=True, exist_ok=True); json.dump(out, open(path, "w"), indent=0); return out
def board(d):
    B = {"schema": "ricks.reference_board.v1", "film": "TEST_FIXTURE_ONLY", "note": "SYNTHETIC generated colour cards, not real reference frames", "beats": [], "department_index": {"camera": "synthetic", "set": "synthetic"}}
    for bid in (1, 2, 3):
        fr = []
        for k, n in enumerate("ab"):
            f = "refs/sd_b%d_%s.png" % (bid, n); p = d / "creative" / f; p.parent.mkdir(parents=True, exist_ok=True); im = Image.new("RGB", (360, 640), (60 + bid * 30, 100, 170 - bid * 20)); ImageDraw.Draw(im).rectangle([100 + k * 30, 220, 260 + k * 30, 600], fill=(210, 170, 70)); im.save(p)
            fr.append(dict(file=f, sha1=sha(p), film="TEST_FIXTURE_ONLY synthetic", t=bid * 2.5 + k, kind="W", take="synthetic"))
        B["beats"].append({"id": bid, "kind": "W", "frames": fr, "storyboard_stations": ["s01"]})
    return B
def registry_copy(tmp, status="approved"):
    """A registry COPY: the barrel is flipped to approved by a labelled TEST_FIXTURE_ONLY harness (the pipeline never approves; the committed registry stays a candidate)."""
    R = json.load(open(ROOT / "library/assets/registry.json")); a = next(x for x in R["assets"] if x["name"] == ASSET)
    if status == "approved": a["glb"].update(status="approved", approved_by="TEST_FIXTURE_ONLY harness", approval_note="TEST_FIXTURE_ONLY: not an owner approval")
    a["requirement"].update(reference_beats=[1])
    for x in R["assets"]:
        if x["glb"].get("file") if isinstance(x.get("glb"), dict) else False: x["glb"]["file"] = str(ROOT / x["glb"]["file"]) if not Path(x["glb"]["file"]).is_absolute() else x["glb"]["file"]
    p = Path(tmp) / "registry.json"; json.dump(R, open(p, "w"), indent=1); return p
def build(tmp, approve=True, judge=True, reviewer="TEST_FIXTURE_ONLY human-stand-in", asset_status="approved"):
    tmp = Path(tmp); tmp.mkdir(parents=True, exist_ok=True); d = tmp / "ep"; shutil.rmtree(d, ignore_errors=True); (d / "creative").mkdir(parents=True)
    os.environ["RICKS_REGISTRY"] = str(registry_copy(tmp, asset_status))
    import assets as AS, characters as CH, approval as AP, review as RV, fixture as FX, importlib; AS.REG = Path(os.environ["RICKS_REGISTRY"]); CH.REG = AS.REG
    c = d / "creative"; (c / "TEST_FIXTURE_ONLY.json").write_text(json.dumps({"TEST_FIXTURE_ONLY": True, "never_a_creative_pass": True, "production": False, "why": "mechanical proof of approval -> lock -> render -> composite -> MP4 -> QA"}, indent=1))
    (c / "SCRIPT.md").write_text("TEST_FIXTURE_ONLY synthetic script\n\n" + SCRIPT + "\n"); (c / "LOOK_BIBLE.md").write_text("TEST_FIXTURE_ONLY synthetic look bible: cold canyon light, one engineer, one handcar.\n"); (c / "PICTURE_PLAN.md").write_text(PLAN)
    (d / "sets").mkdir(); st = (ROOT / "templates/threejs_film/sets/canyon_rail.js").read_text().replace("export function build(", "export async function build(").replace("  return { anchors: {", "  const handcar = await ctx.asset('%s', { at: [0, 1.4, 0.07] }); window.__handcar = handcar.anchors_plan;\n  return { anchors: {" % ASSET, 1); (d / "sets/canyon_rail.js").write_text(st)   # the kit canyon set + the registry handcar by id (same seam as r4/test_assets.py)
    json.dump(FILM, open(d / "film.json", "w"), indent=1); words(d / "voice/words.json"); json.dump(SPEC, open(c / "characters.json", "w"), indent=1)
    B = board(d); FX.BOARD = B; FX.SPEC = SPEC; (c / "reference_board.json").write_text(json.dumps(B))
    import subprocess; r = subprocess.run([sys.executable, str(ROOT / "tools/film_plan.py"), "check", str(d / "film.json")], capture_output=True, text=True); last = r.stdout.strip().splitlines()[-1]
    if " 0 FAIL" not in last: sys.exit("fixture plan bake: " + last)
    bad = AS.resolve(d, allow_candidate=(asset_status != "approved"))
    if bad: sys.exit("fixture asset resolve: %s" % bad)
    CH.build(d); FX.with_characters = lambda d_: None                                  # the REAL R3 character build (views, probe, cards) for THIS film; fixture.py's canyon cache is not used
    FX.build_artifacts(d, builder="TEST_FIXTURE_ONLY-builder-ctx")                      # stand-in panels + ffmpeg test-pattern animatics + REAL-format storyboard/animatic documents
    if judge:
        res = FX.judge_result(d, score=9.0, ctx="TEST_FIXTURE_ONLY-judge-ctx", jid="TEST_FIXTURE_ONLY-synthetic-judge"); res["film_level"]["notes"] = "TEST_FIXTURE_ONLY synthetic judge PASS: mechanical test, not a creative judgement"
        assert FX.record(d, res) == "PASS"
    if approve: AP.create(d, reviewer, AP.FLAGS)
    return d
if __name__ == "__main__":
    d = build(sys.argv[1]); print("fixture ->", d)
