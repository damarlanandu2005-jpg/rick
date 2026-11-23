#!/usr/bin/env python3
"""R4 tests: Blender asset workshop -> GLB contract -> registry -> three.js loader seam -> storyboard/animatic/judge -> approval -> lock.  python3 r4/test_assets.py
A temp COPY of the registry (handcar flipped to approved, labelled test harness) is used; the committed registry is never changed by the tests."""
import copy, hashlib, json, os, shutil, struct, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(ROOT / "r2"))
import assets as AS, glb as G, characters as CH, creative_gates as CG, approval as AP, review as RV, fixture as FX, lock_stamp as LS
from PIL import Image, ImageChops
fails = []; CG.MAX_WARN = 99; CG.WS_MIN = 3.0   # TEST ONLY (as r2/r3)
def t(name, ok): print(("PASS " if ok else "FAIL ") + name); (ok or fails.append(name))
has = lambda bad, w: any(w in x for x in bad)
ID = "prop_rail_handcar"; TMP = Path(tempfile.mkdtemp()); REGF = TMP / "registry.json"; shutil.copy(ROOT / "library/assets/registry.json", REGF); AS.REG = REGF; CH.REG = REGF
def reg(): return json.load(open(REGF))
def save(R): json.dump(R, open(REGF, "w"))
def ent(R): return next(a for a in R["assets"] if a["name"] == ID)
R0 = reg(); e0 = ent(R0); t("the committed registry entry is a CANDIDATE (the pipeline never approves)", json.load(open(ROOT / "library/assets/registry.json")) and next(a for a in json.load(open(ROOT / "library/assets/registry.json"))["assets"] if a["name"] == ID)["glb"]["status"] == "candidate")
ent(R0)["glb"].update(status="approved", approved_by="r4-test-harness", approval_note="TEST HARNESS approval, not an owner approval"); save(R0)
def episode(assets=("%s@1.0" % ID,)):
    d = FX.copy_episode(); f = json.load(open(d / "film.json")); f["places"]["canyon"]["assets"] = list(assets); json.dump(f, open(d / "film.json", "w"), indent=1); return d
def mutate(fn):
    R = reg(); fn(ent(R)); save(R)
def restore(): save(R0)
def rewrite_glb(src, dst, fn):
    J, BIN = G.read(src); fn(J); jb = json.dumps(J, separators=(",", ":")).encode(); jb += b" " * (-len(jb) % 4); out = struct.pack("<II", len(jb), 0x4E4F534A) + jb
    if BIN is not None: out += struct.pack("<II", len(BIN), 0x004E4942) + BIN
    Path(dst).write_bytes(b"glTF" + struct.pack("<II", 2, 12 + len(out)) + out)
def point_at(path, **kw):
    def f(a): g = a["glb"]; g["file"] = str(path); g["sha1"] = hashlib.sha1(Path(path).read_bytes()).hexdigest(); g["bytes"] = Path(path).stat().st_size; g.update(kw)
    mutate(f)
SRC = ROOT / e0["glb"]["file"]
# ---- R4C/D workshop + GLB contract
s = G.summarize(SRC)
t("GLB: valid, no contract problems", G.problems(SRC, e0["requirement"], e0["glb"]["contract"], e0["glb"]["sha1"]) == [])
t("GLB: every required mat: name present", set(e0["requirement"]["materials"]) <= set(s["materials"]) and all(m.startswith("mat:") for m in s["materials"]))
t("GLB: anchors grip_left/grip_right present", {"grip_left", "grip_right"} <= set(s["anchors"]))
t("GLB: Y up, origin at the base, height matches the requirement", abs(s["bbox_min"][1]) < 1e-3 and abs((s["bbox_max"][1] - s["bbox_min"][1]) - e0["requirement"]["scale"]["height_m"]) < 0.02)
t("GLB: registry sha1 is the file's sha1", s["sha1"] == e0["glb"]["sha1"])
r = subprocess.run([sys.executable, str(ROOT / "tools/blender_workshop.py"), "build", ID, "--force", "--out", str(TMP / "w1")], capture_output=True, text=True); t("workshop build exits 0 with no problems", r.returncode == 0)
r2 = subprocess.run([sys.executable, str(ROOT / "tools/blender_workshop.py"), "build", ID, "--force", "--out", str(TMP / "w2")], capture_output=True, text=True)
h = lambda o: hashlib.sha1((TMP / o / (ID + ".glb")).read_bytes()).hexdigest()
t("workshop export is DETERMINISTIC (two Blender runs, same bytes)", h("w1") == h("w2") == e0["glb"]["sha1"])
p = json.loads(subprocess.run([sys.executable, str(ROOT / "tools/blender_workshop.py"), "plan", ID], capture_output=True, text=True).stdout); t("workshop plan: reuse first (unchanged builder -> reuse)", p["action"] == "reuse")
rb = json.loads(subprocess.run([sys.executable, str(ROOT / "tools/blender_workshop.py"), "build", ID], capture_output=True, text=True).stdout); t("workshop build reuses instead of rebuilding", rb.get("reused") is True)
t("registry check passes with the real asset", AS.check() == [])
# ---- R4J fail-closed validation
d = episode(); t("valid approved asset: resolve is clean and stages GLB + assets_baked.json", AS.resolve(d) == [] and (d / "out/plan/assets_baked.json").is_file() and (d / "out/assets" / ID / "1.0" / (ID + ".glb")).is_file())
t("staged GLB is byte-identical to the registry GLB", hashlib.sha1((d / "out/assets" / ID / "1.0" / (ID + ".glb")).read_bytes()).hexdigest() == e0["glb"]["sha1"])
t("G7 PASS for a valid approved asset", AS.g7(d)[0] == "PASS")
d0 = FX.copy_episode(); t("G7 SKIP when the film declares no assets, and assets_baked.json is absent", AS.g7(d0)[0] == "SKIP" and AS.resolve(d0) == [] and not (d0 / "out/plan/assets_baked.json").exists())
d = episode(["nope_asset"]); b = AS.resolve(d); t("missing asset (not in the registry) -> fail, no placeholder", has(b, "not in the registry") and not (d / "out/plan/assets_baked.json").exists())
d = episode(["char_stationmaster"]); t("wrong ID: a character id in places.assets -> fail", has(AS.resolve(d), "is a character"))
d = episode(["%s@9.9" % ID]); t("wrong version -> fail", has(AS.resolve(d), "version 9.9 requested"))
mutate(lambda e: e["glb"].update(file="library/assets/glb/none/none.glb")); d = episode(); t("missing GLB file -> fail", has(AS.resolve(d), "GLB file missing")); restore()
bad = TMP / "bad.glb"; bad.write_bytes(b"not a glb at all"); point_at(bad); d = episode(); t("malformed GLB (garbage) -> fail", has(AS.resolve(d), "malformed") or has(AS.resolve(d), "bad magic")); restore()
tr = TMP / "trunc.glb"; tr.write_bytes(SRC.read_bytes()[:-500]); point_at(tr); d = episode(); t("malformed GLB (truncated) -> fail", AS.resolve(d) != []); restore()
mutate(lambda e: e["glb"].update(sha1="0" * 40)); d = episode(); t("stale hash (registry sha1 != file) -> fail", has(AS.resolve(d), "sha1") or has(AS.resolve(d), "stale") or has(AS.resolve(d), "hash")); restore()
def nomat(J): [m.update(name=m["name"].replace("mat:", "xx:")) for m in J["materials"]]
f = TMP / "nomat.glb"; rewrite_glb(SRC, f, nomat); point_at(f); d = episode(); t("missing mat: name -> fail", has(AS.resolve(d), "mat:")); restore()
def dropmat(J): J["materials"] = [m for m in J["materials"] if m["name"] != "mat:burlap"]; [pr.pop("material") for m in J["meshes"] for pr in m["primitives"] if pr.get("material", -1) >= len(J["materials"]) or True and False]
def renmat(J):
    for m in J["materials"]:
        if m["name"] == "mat:burlap": m["name"] = "mat:cloth_other"
f = TMP / "dropmat.glb"; rewrite_glb(SRC, f, renmat); point_at(f); d = episode(); t("missing required material -> fail", has(AS.resolve(d), "missing required material")); restore()
def noanchor(J): [n.update(name="gone_" + n["name"]) for n in J["nodes"] if n.get("name") in ("grip_left",)]
f = TMP / "noanchor.glb"; rewrite_glb(SRC, f, noanchor); point_at(f); d = episode(); t("missing anchor -> fail", has(AS.resolve(d), "missing required anchor")); restore()
def scaled(J):
    for n in J["nodes"]:
        if "mesh" in n: n["scale"] = [2, 2, 2]
f = TMP / "scaled.glb"; rewrite_glb(SRC, f, scaled); point_at(f); d = episode(); b = AS.resolve(d); t("incorrect scale (GLB 2x) -> fail", has(b, "incorrect scale")); t("incorrect transform (non-unit node scale) -> fail", has(b, "transform not applied")); restore()
mutate(lambda e: e["requirement"]["scale"].update(height_m=2.5)); d = episode(); t("scale mismatch against the requirement -> fail", has(AS.resolve(d), "incorrect scale")); restore()
mutate(lambda e: e["glb"]["contract"].update(height_m=3.0, bbox_m=[9, 9, 9])); d = episode(); t("registry/contract mismatch -> fail", AS.resolve(d) != []); restore()
mutate(lambda e: e["glb"].update(status="candidate")); d = episode(); t("unapproved (candidate) asset -> strict resolve fails, G7 FAIL", has(AS.resolve(d), "not approved") and AS.g7(d)[0] == "FAIL"); t("candidate allowed only for review drafts (allow_candidate)", AS.resolve(d, allow_candidate=True) == []); restore()
mutate(lambda e: e["glb"].pop("approved_by")); t("approved without approved_by -> registry check fails", AS.check() != []); restore()
mutate(lambda e: e.pop("requirement")); t("asset with a GLB but no requirement is not silently accepted", has(AS.resolve(episode()), "requirement block missing")); restore()
# ---- R4F loader seam in the real three.js page
def render(d, frame=0):
    r = subprocess.run(["node", str(ROOT / "templates/threejs_film/render.mjs"), str(d / "film.json"), "--frames", str(frame), "--scale", "0.4", "--stills-dir", str(d / "out/preview")], capture_output=True, text=True); return r, d / ("out/preview/f_%05d.png" % frame)   # R6: an un-approved episode may only render a PREVIEW (--stills-dir)
def with_set(d):
    (d / "sets").mkdir(exist_ok=True); s = (ROOT / "templates/threejs_film/sets/canyon_rail.js").read_text().replace("export function build(", "export async function build(").replace("  return { anchors: {", "  const handcar = await ctx.asset('%s', { at: [0, 1.4, 0.07] }); window.__handcar = handcar.anchors_plan;\n  return { anchors: {" % ID, 1); (d / "sets/canyon_rail.js").write_text(s)
d = episode(); with_set(d); AS.resolve(d); r, png = render(d); dw = d
b0 = FX.copy_episode(); r0, png0 = render(b0)
t("three.js: set loads the asset by registry id and renders", r.returncode == 0 and png.is_file())
if png.is_file() and png0.is_file():
    diff = ImageChops.difference(Image.open(png).convert("RGB"), Image.open(png0).convert("RGB")).convert("L").point(lambda v: 255 if v > 24 else 0); n = sum(1 for v in diff.getdata() if v); t("the asset is VISIBLY in the picture (%d px differ from the same frame without it)" % n, n > 2000)
d2 = episode(); with_set(d2); AS.resolve(d2); g = d2 / "out/assets" / ID / "1.0" / (ID + ".glb"); g.write_bytes(g.read_bytes()[:-1] + b"\x00"); r2, p2 = render(d2); t("three.js: a tampered staged GLB (sha1 mismatch) fails closed: no frame is rendered", r2.returncode != 0 or not p2.is_file())
d3 = episode(); with_set(d3); r3, p3 = render(d3); t("three.js: no staged asset (assets_baked.json missing) fails closed", r3.returncode != 0 or not p3.is_file())
d4 = episode(); with_set(d4); (d4 / "sets/canyon_rail.js").write_text((d4 / "sets/canyon_rail.js").read_text().replace("ctx.asset('%s'" % ID, "ctx.asset('other_asset'")); AS.resolve(d4); r4_, p4 = render(d4); t("three.js: an undeclared/wrong asset id fails closed (no placeholder)", r4_.returncode != 0 or not p4.is_file())
# ---- R4G/H placement, scale, anchors, material round trip (through the lock GLB, below) and R4K/L/M integration
def approved_episode():
    src = FX.complete_episode(); d = FX.copy_episode(); (d / "creative").mkdir(exist_ok=True)
    for n in ("SCRIPT.md", "PICTURE_PLAN.md", "LOOK_BIBLE.md"): shutil.copy(src / "creative" / n, d / "creative" / n)
    f = json.load(open(d / "film.json")); f["places"]["canyon"]["assets"] = [ID]; json.dump(f, open(d / "film.json", "w"), indent=1); with_set(d); AS.resolve(d); FX.build_artifacts(d)
    return d
d = approved_episode()
t("storyboard + animatic record the asset id/version/sha1", RV.validate_storyboard(d)[1] == [] and json.load(open(d / "creative/STORYBOARD.json"))["assets"][ID]["sha1"] == e0["glb"]["sha1"] and json.load(open(d / "creative/ANIMATIC.json"))["assets"][ID]["sha1"] == e0["glb"]["sha1"])
t("the judge must score an asset_<id> panel", "asset_" + ID in RV.required_panels(d, json.load(open(d / "creative/STORYBOARD.json"))))
res = FX.judge_result(d); P = res["panels"]; t("a judge result without the asset panel is rejected", (lambda c: (c["panels"].pop("asset_" + ID), FX.record(d, c) if False else RV.judge_validate_input(d, c, json.load(open(d / "creative/STORYBOARD.json")), json.load(open(d / "creative/ANIMATIC.json"))))[1])(copy.deepcopy(res)) != [])
res2 = copy.deepcopy(res); res2["evidence_read"].pop("assets_sha1"); t("a judge who did not read the current assets (no assets_sha1) is rejected", has(RV.judge_validate_input(d, res2, json.load(open(d / "creative/STORYBOARD.json")), json.load(open(d / "creative/ANIMATIC.json"))), "assets"))
t("judge PASS recorded", FX.record(d, res) == "PASS"); t("G8 PASS with a current asset", RV.g8_problems(d)[0] == [])
t("G1-G8 creative gates: G7 PASS (real) and no FAIL", CG.g7(d)[0] == "PASS" and not [x for x in CG.run(d) if x["status"] == "FAIL"])
AP.create(d, "r4-test-reviewer", AP.FLAGS); t("approval.json created; asset_versions holds ONLY the assets this film uses", AP.check(d) == [] and set(json.load(open(d / "approval.json"))["asset_versions"]) == {ID, "char_stationmaster"})
R = reg(); R["assets"].append(dict(copy.deepcopy(next(a for a in R["assets"] if a["name"] == "flight_coin")), name="unrelated_x")); save(R); t("registering an UNRELATED asset does not stale the approval", AP.check(d) == []); restore()
mutate(lambda e: e.update(version="1.1")); st = AP.check(d); t("an asset version change after approval makes approval STALE and G8 stale", has(st, "asset_versions") or has(st, "STALE")); restore()
mutate(lambda e: e["glb"].update(sha1="f" * 40)); t("an asset hash change after approval: approval STALE, G7 FAIL, storyboard/judge STALE", AP.check(d) != [] and AS.g7(d)[0] == "FAIL" and has(RV.g8_problems(d)[0], "stale") or has(RV.g8_problems(d)[0], "STALE")); restore()
# lock: real export through render.mjs, then freeze + check
rl = subprocess.run(["node", str(ROOT / "templates/threejs_film/render.mjs"), str(d / "film.json"), "--export-lock"], capture_output=True, text=True, env={**os.environ, "RICKS_UNAPPROVED_TEST_RUN": "", "RICKS_REGISTRY": str(REGF)}); t("lock export succeeds for the approved episode", rl.returncode == 0)
la = LS.lock_assets(d) if rl.returncode == 0 else {}
t("lock set GLB carries the exact asset id/version/sha1 (node extras)", la.get(ID, {}).get("sha1") == e0["glb"]["sha1"] and la[ID]["version"] == "1.0")
t("mat: names SURVIVE three.js -> lock GLB (every required material present)", bool(la) and all(LS.mat_kept(m, la[ID]["materials"]) for m in e0["requirement"]["materials"]) and "mat:" + "painted_metal_chipped.b4332a" in la[ID]["materials"])
sg = G.read(d / "out/lock/sets/canyon.glb")[0]; nd = [n for n in sg["nodes"] if (n.get("extras") or {}).get("asset")]
t("lock GLB: the asset is placed (node translation) at the film's place, plan (0,1.4,.07) = three (0,.07,-1.4)", bool(nd) and all(abs(a - b) < 1e-3 for a, b in zip(nd[0].get("translation", [0, 0, 0]), [0, 0.07, -1.4])))
t("lock_stamp: stamp then check OK", LS.stamp(d) == [] and LS.problems(d) == [])
L = json.load(open(d / "out/lock/lock.json")); t("lock.json freezes approval sha, asset hashes and card hashes", L["approved"]["assets"][ID]["glb_sha1"] == e0["glb"]["sha1"] and L["approved"]["cards"] and L["approved"]["approval_sha1"])
mutate(lambda e: e["glb"].update(sha1="e" * 40)); t("asset changed after the lock froze it -> lock check FAILS", has(LS.problems(d), "changed in the registry") or LS.problems(d) != []); restore()
lj = d / "out/lock/lock.json"; Lb = json.load(open(lj)); Lc = copy.deepcopy(Lb); Lc["approved"]["assets"][ID]["glb_sha1"] = "a" * 40; json.dump(Lc, open(lj, "w")); t("silent substitution (lock frozen with another hash) -> fail", has(LS.problems(d), "carries asset") or has(LS.problems(d), "changed")); json.dump(Lb, open(lj, "w"))
Lc = copy.deepcopy(Lb); Lc["approved"].pop("assets"); Lc["approved"]["assets"] = {}; json.dump(Lc, open(lj, "w")); t("a lock that does not freeze a declared asset -> fail", has(LS.problems(d), "lock asset set")); json.dump(Lb, open(lj, "w"))
Lc = copy.deepcopy(Lb); Lc.pop("approved"); json.dump(Lc, open(lj, "w")); t("an unstamped lock -> fail", has(LS.problems(d), "no approved block")); json.dump(Lb, open(lj, "w"))
open(d / "approval.json", "a").write(" "); t("approval.json changed after the stamp -> lock check fails", has(LS.problems(d), "approval.json changed"))
# ---- R4O/P resolution + measurement record
dd = episode(); with_set(dd); AS.resolve(dd); sc = 720 / json.load(open(dd / "film.json")).get("size", [1080, 1920])[0]
rr = subprocess.run(["node", str(ROOT / "templates/threejs_film/render.mjs"), str(dd / "film.json"), "--frames", "0", "--scale", str(sc), "--stills-dir", str(dd / "out/preview")], capture_output=True, text=True); im = Image.open(dd / "out/preview/f_00000.png"); t("720x1280 final-resolution render works with the asset (%dx%d)" % im.size, im.size == (720, 1280))
print("\n%d FAIL" % len(fails)); [print("  FAILED:", x) for x in fails]; sys.exit(1 if fails else 0)
