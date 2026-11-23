#!/usr/bin/env python3
"""TEST_FIXTURE_ONLY (R7). Two INDEPENDENT film fixtures that REUSE the same library asset version from ONE registry copy (the "library world" of a test run).
Nothing here is a creative pass: the scripts, pictures-plans and judge results are the R6 mechanical stand-ins (r6/fixture_mech.py), the approvals are labelled TEST_FIXTURE_ONLY harness
approvals of a registry COPY (the committed registry is never changed), and every film is stamped production:false by tools/approval.py.
What IS real: the Blender-built GLB (library/assets/glb), the registry entry and its technical validation, tools/assets.py resolve, the three.js loader seam (asset_glb.js) and film.js placement,
the real storyboard and animatic (tools/review.py -> render.mjs --storyboard / --animatic), approval.py, the lock export (render.mjs --export-lock) and tools/lock_stamp.py.
  world(tmp)                     -> registry copy at <tmp>/registry.json; the lantern GLB copied to <tmp>/glb/... (so tamper tests never touch the repo); lantern + handcar owner-approved by the HARNESS
  film(tmp, "film_a" | "film_b") -> a complete episode up to a stamped lock (no final render)"""
import argparse, copy, json, os, shutil, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent; sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "r2"), str(ROOT / "r6")]
import fixture_mech as FM
LANTERN = "prop_oil_lantern"; HANDCAR = "prop_rail_handcar"
PLACEMENT = {"film_a": dict(name="lantern", at=[0.7, -0.6, 0.0], rot=0, scale=1.0), "film_b": dict(name="lantern", at=[-0.6, -0.5, 0.0], rot=35, scale=1.4)}
HARNESS = dict(by="TEST_FIXTURE_ONLY harness (R7)", note="TEST_FIXTURE_ONLY: not an owner approval; a registry COPY for the R7 reuse test")
def env(tmp): return dict(os.environ, RICKS_REGISTRY=str(Path(tmp) / "registry.json"))
def use(tmp):
    import assets as AS, characters as CH
    os.environ["RICKS_REGISTRY"] = str(Path(tmp) / "registry.json"); AS.REG = Path(os.environ["RICKS_REGISTRY"]); CH.REG = AS.REG
def world(tmp, approve=(LANTERN + "@1.0", HANDCAR + "@1.0")):
    tmp = Path(tmp); tmp.mkdir(parents=True, exist_ok=True); R = json.load(open(ROOT / "library/assets/registry.json"))
    for a in R["assets"]:
        g = a.get("glb")
        if not isinstance(g, dict) or not g.get("file"): continue
        if a["name"] == LANTERN:   # the reused asset lives in the test world (a byte-identical copy at the same id/version path) so tampering never touches the repository
            dst = tmp / "glb" / LANTERN / str(a["version"]) / (LANTERN + ".glb"); dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy(ROOT / g["file"], dst); g["file"] = str(dst)
        else: g["file"] = str(ROOT / g["file"])
        if a["name"] in (LANTERN, HANDCAR): a["requirement"]["reference_beats"] = [1]   # both fixture boards have beat 1
    json.dump(R, open(tmp / "registry.json", "w"), indent=1); use(tmp)
    import assets as AS
    for ref in approve: AS.approve_glb(argparse.Namespace(id=ref, **HARNESS))
    return tmp / "registry.json"
def film(tmp, name, judge=True, approve=True, lock=True, placement=None):
    """Film A: canyon_rail + the handcar (set module, R4 seam) + the lantern placed by film.json. Film B: the kit platform set + ONLY the lantern, a different placement and anchors used."""
    tmp = Path(tmp); use(tmp); E = env(tmp); T = {}
    import assets as AS, characters as CH, approval as AP, lock_stamp as LS, fixture as FX
    d = tmp / name; shutil.rmtree(d, ignore_errors=True); c = d / "creative"; c.mkdir(parents=True)
    (c / "TEST_FIXTURE_ONLY.json").write_text(json.dumps({"TEST_FIXTURE_ONLY": True, "never_a_creative_pass": True, "production": False, "why": "R7 reusable-asset proof: the same registry asset version in two films"}, indent=1))
    (c / "SCRIPT.md").write_text("TEST_FIXTURE_ONLY synthetic script\n\n" + FM.SCRIPT + "\n"); (c / "LOOK_BIBLE.md").write_text("TEST_FIXTURE_ONLY synthetic look bible (R7 %s)\n" % name); (c / "PICTURE_PLAN.md").write_text(FM.PLAN)
    F = copy.deepcopy(FM.FILM); pl = dict(placement or PLACEMENT[name]); lan = dict(id=LANTERN, version="1.0", needs=["static_prop", "anchor_target"], **pl)
    if name == "film_a":
        F["title"] = "TEST_FIXTURE_ONLY R7 Film A: canyon rail, handcar + library lantern"; F["places"]["canyon"]["assets"] = [HANDCAR + "@1.0", lan]
        (d / "sets").mkdir(); st = (ROOT / "templates/threejs_film/sets/canyon_rail.js").read_text().replace("export function build(", "export async function build(").replace("  return { anchors: {", "  await ctx.asset('%s', { at: [0, 1.4, 0.07] });\n  return { anchors: {" % HANDCAR, 1); (d / "sets/canyon_rail.js").write_text(st)
    else:
        F["title"] = "TEST_FIXTURE_ONLY R7 Film B: station platform, the same library lantern"; F["places"] = {"yard": {"set": "platform", "light": "day", "backdrop": 5.5, "assets": [lan]}}
        for tk in F["takes"]: tk["place"] = "yard"
    import math; s = pl.get("scale", 1); th = math.radians(pl.get("rot", 0)); C = json.load(open(ROOT / "library/assets/glb" / LANTERN / "1.0" / (LANTERN + ".contract.json")))["anchors"]
    F.setdefault("props", {})
    for k, (ax, ay, az) in C.items():   # where film.js must put each anchor: placement of the GLB-local point (glTF Y up) -> plan metres (x, -z, y); an independent check of the seam
        x, z = (ax * math.cos(th) + az * math.sin(th)) * s, (-ax * math.sin(th) + az * math.cos(th)) * s; F["props"]["lantern.%s" % k] = {}; F["props"]["expect.%s" % k] = dict(pos=[round(pl["at"][0] + x, 4), round(pl["at"][1] - z, 4), round(pl["at"][2] + ay * s, 4)], h=0)
        if s != 1: F["props"]["control.%s" % k] = dict(pos=[round(pl["at"][0] + ax, 4), round(pl["at"][1] - az, 4), round(pl["at"][2] + ay, 4)], h=0)   # a WRONG expectation (scale ignored): proves the anchor check can fail
    json.dump(F, open(d / "film.json", "w"), indent=1); FM.words(d / "voice/words.json"); json.dump(FM.SPEC, open(c / "characters.json", "w"), indent=1)
    B = FM.board(d); FX.BOARD = B; FX.SPEC = FM.SPEC; (c / "reference_board.json").write_text(json.dumps(B))
    r = subprocess.run([sys.executable, str(ROOT / "tools/film_plan.py"), "check", str(d / "film.json")], capture_output=True, text=True, env=E); last = r.stdout.strip().splitlines()[-1]
    if " 0 FAIL" not in last: sys.exit("%s plan bake: %s" % (name, last))
    t = time.perf_counter(); bad = AS.resolve(d); T["resolve_s"] = round(time.perf_counter() - t, 3)
    if bad: sys.exit("%s asset resolve: %s" % (name, bad))
    CH.build(d)
    for step in ("storyboard", "animatic"):
        t = time.perf_counter(); r = subprocess.run([sys.executable, str(ROOT / "tools/review.py"), step, str(d), "--builder", "TEST_FIXTURE_ONLY-r7-builder"], capture_output=True, text=True, env=E); T[step + "_s"] = round(time.perf_counter() - t, 2)
        if r.returncode: sys.exit("%s review %s: %s %s" % (name, step, r.stdout[-400:], r.stderr[-400:]))
    if not judge: return d, T
    res = FX.judge_result(d, score=9.0, ctx="TEST_FIXTURE_ONLY-r7-judge-ctx", jid="TEST_FIXTURE_ONLY-r7-synthetic-judge"); res["film_level"]["notes"] = "TEST_FIXTURE_ONLY synthetic judge PASS (R7 mechanical reuse test), not a creative judgement"
    assert FX.record(d, res) == "PASS"
    if not approve: return d, T
    AP.create(d, "TEST_FIXTURE_ONLY human-stand-in", AP.FLAGS)
    if not lock: return d, T
    t = time.perf_counter(); r = subprocess.run(["node", str(ROOT / "templates/threejs_film/render.mjs"), str(d / "film.json"), "--export-lock"], capture_output=True, text=True, env=E); T["lock_s"] = round(time.perf_counter() - t, 2)
    if r.returncode: sys.exit("%s lock export: %s %s" % (name, r.stdout[-500:], r.stderr[-500:]))
    bad = LS.stamp(d)
    if bad: sys.exit("%s lock stamp: %s" % (name, bad))
    return d, T
if __name__ == "__main__":
    tmp = Path(sys.argv[1]); world(tmp)
    for n in ("film_a", "film_b"): d, T = film(tmp, n); print(n, "->", d, T)
