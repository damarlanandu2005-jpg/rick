#!/usr/bin/env python3
"""R7 tests: the reusable Ricks asset/capability library (the R4 Blender -> GLB -> registry -> three.js seam, made reusable and governed). ONE registry (library/assets/registry.json).
  python3 r7/test_library.py              builds the TEST_FIXTURE_ONLY library world (a registry COPY) and two independent films that reuse the same asset version, up to a stamped lock
                                          (real Blender build, real three.js storyboard + animatic, no final render): about 8 minutes on 2 CPUs
  R7_REUSE=<dir> python3 r7/test_library.py   reuse a finished world in <dir> (development only)
Nothing here approves anything in the committed registry; every approval is a labelled TEST_FIXTURE_ONLY harness approval of a registry copy, and every film is production:false."""
import argparse, copy, hashlib, json, os, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent; sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "r2"), str(ROOT / "r6"), str(ROOT / "r7")]
fails = []; T0 = time.time(); TIMES = {}
def t(name, ok): print(("PASS " if ok else "FAIL ") + name, flush=True); (ok or fails.append(name))
has = lambda bad, w: any(w in x for x in bad)
PY = sys.executable; LAN = "prop_oil_lantern"; V1 = LAN + "@1.0"
import fixture_lib as FL
import assets as AS, approval as AP, lock_stamp as LS, glb as G, characters as CH
COMMITTED = ROOT / "library/assets/registry.json"; COMMITTED_SHA = hashlib.sha1(COMMITTED.read_bytes()).hexdigest()
def sha(p): return hashlib.sha1(Path(p).read_bytes()).hexdigest()
def sh(cmd, env=None): return subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, **(env or {})})
def exits(fn, *a):
    try: fn(*a); return None
    except SystemExit as e: return str(e)
def ns(**k): return argparse.Namespace(**k)
W = Path(os.environ.get("R7_REUSE") or tempfile.mkdtemp(prefix="r7_")); WREG = W / "registry.json"
def use(reg=WREG): os.environ["RICKS_REGISTRY"] = str(reg); AS.REG = Path(reg); CH.REG = AS.REG
def scratch(name, mut=None):
    """A registry copy of the test world for one mutation test (the world itself stays intact)."""
    p = W / ("reg_" + name + ".json"); shutil.copy(WREG, p); use(p)
    if mut:
        R = json.load(open(p)); e = AS.entry(LAN, "1.0", R["assets"]); mut(e, R); json.dump(R, open(p, "w"), indent=1)
    return p
def film_copy(src, name):
    d = W / "copies" / name; shutil.rmtree(d, ignore_errors=True); shutil.copytree(src, d, ignore=shutil.ignore_patterns("animatic*.mp4", "stills", ".puppet_cache")); return d
def pipe(ep, reg):
    e = {k: v for k, v in os.environ.items() if k != "RICKS_UNAPPROVED_TEST_RUN"}; e["RICKS_REGISTRY"] = str(reg)
    r = subprocess.run([PY, str(ROOT / "tools/pipeline.py"), str(ep), "--renderer", "cpu"], capture_output=True, text=True, env=e); return r.returncode, r.stdout + r.stderr
def stills(ep): return len(list((Path(ep) / "out/stills").glob("f_*.png"))) if (Path(ep) / "out/stills").is_dir() else 0
def renders(ep, reg, *args):
    return subprocess.run(["node", str(ROOT / "templates/threejs_film/render.mjs"), str(Path(ep) / "film.json"), *args], capture_output=True, text=True, env={**{k: v for k, v in os.environ.items() if k != "RICKS_UNAPPROVED_TEST_RUN"}, "RICKS_REGISTRY": str(reg)})

# ====================================================================== the Blender workshop (real bpy): deterministic build of the second asset, timings
lib_glb = ROOT / "library/assets/glb" / LAN / "1.0" / (LAN + ".glb"); lib_mtime = lib_glb.stat().st_mtime_ns
builds = []
for k in (1, 2):
    o = W / "rebuild" / str(k); r = sh([PY, str(ROOT / "tools/blender_workshop.py"), "build", V1, "--force", "--out", str(o)], env={"RICKS_REGISTRY": str(COMMITTED)})
    builds.append(json.loads(r.stdout[r.stdout.index("{"):]))
e0 = AS.entry(LAN, "1.0", json.load(open(COMMITTED))["assets"]); g0 = e0["glb"]
TIMES.update(blender_build_s=builds[0]["build_s"], glb_export_s=builds[0]["export_s"], glb_bytes=builds[0]["bytes"])
t("28 deterministic rebuild: the lantern rebuilt twice in Blender %s gives the same bytes, equal to the registered sha1 %s" % (builds[0]["blender_version"], g0["sha1"][:10]), builds[0]["sha1"] == builds[1]["sha1"] == g0["sha1"] and not builds[0]["problems"])
t("16/22 the workshop's reuse-first plan says REUSE (valid GLB, builder unchanged): a film never triggers a rebuild", json.loads(sh([PY, str(ROOT / "tools/blender_workshop.py"), "plan", V1], env={"RICKS_REGISTRY": str(COMMITTED)}).stdout)["action"] == "reuse")
src = (ROOT / e0["blender"]["file"]).read_text()
t("13 material contract (Blender): the builder names its materials by the Ricks library convention mat:<lib>[.rrggbb]", all(m in src for m in e0["requirement"]["materials"]))
t("14 anchor contract (Blender): the builder makes mesh-less Empties 'grip' and 'flame' (the Ricks held-prop anchor names)", "_empty(\"grip\"" in src and "_empty(\"flame\"" in src)

# ====================================================================== the committed registry: ONE registry, lifecycle, the second asset
R0 = json.load(open(COMMITTED))["assets"]
t("1 registry schema: the committed registry passes assets.py check (identity, (id, version) unique, GLB contract, lifecycle, capabilities)", AS.check(R0) == [])
others = [p for p in (ROOT / "library").rglob("*.json") if re.search(r"(assets?_?v2|production_assets|asset_catalog|catalog|registry)", p.name) and p != COMMITTED]
t("1 exactly ONE authoritative registry: no second asset registry / catalog / manifest exists in library/", others == [])
bad_entry = copy.deepcopy(R0); [x.update(version="v1") for x in bad_entry if x["name"] == LAN]; t("1 a malformed entry (version 'v1') is reported", has(AS.check(bad_entry), "is not a dotted number"))
t("16 second asset registered: prop_oil_lantern@1.0 (Blender builder, GLB in library/assets/glb/<id>/<ver>/, preview, requirement)", g0["file"] == "library/assets/glb/prop_oil_lantern/1.0/prop_oil_lantern.glb" and (ROOT / e0["preview"]).is_file() and e0["blender"]["kind"] == "bpy_builder")
v0 = g0["validation"]; ch0 = v0["checks"]
t("3 validated asset: the committed lantern is VALIDATED (technical PASS: contract, identity, loader, deterministic rebuild), NOT approved", g0["status"] == "validated" and v0["PASS"] and v0["sha1"] == g0["sha1"] and ch0["loader"]["ok"] and ch0["determinism"]["ok"] and not g0.get("approved_by"))
t("25 (R7 rule) TECHNICAL VALIDATION is never CREATIVE APPROVAL: no committed GLB asset is approved, the validation record says so", all((a.get("glb") or {}).get("status") != "approved" for a in R0) and "NOT a creative approval" in v0["tool"])
t("16 the loader check used the EXISTING three.js seam (asset_glb.js through render.mjs): it fetched, hash-checked and parsed the GLB", ch0["loader"]["exit"] == 0 and ch0["loader"]["bytes"] == g0["bytes"] and ch0["loader"]["parse_ms"] is not None and not ch0["loader"]["errors"])
src_seam = (ROOT / "templates/threejs_film/asset_glb.js").read_text(); kit = "".join(p.read_text() for p in (ROOT / "templates/threejs_film").glob("*.js") if p.name != "asset_glb.js")
t("16 loader contract: asset_glb.js is the ONLY GLB loader of the kit (no other GLTFLoader use), and it throws on a wrong hash (no placeholder)", "GLTFLoader" not in kit.replace("vendor/GLTFLoader.js", "") and "is not the approved" in src_seam and "There is no placeholder" in src_seam)
TIMES.update(threejs_fetch_hash_ms=ch0["loader"]["fetch_hash_ms"], threejs_parse_ms=ch0["loader"]["parse_ms"], loader_probe_s=ch0["loader"]["seconds"], validate_rebuild_s=ch0["determinism"]["seconds"])
t("17 capability declaration: the lantern declares static_prop + anchor_target {grip, flame}; every declared capability is in the implemented vocabulary with evidence", set(e0["capabilities"]) == {"static_prop", "anchor_target"} and e0["capabilities"]["anchor_target"]["anchors"] == ["grip", "flame"] and set(ch0["loader"]["anchors"]) == {"grip", "flame"} and all(v["max_err_frac"] <= 0.002 and v["frames_seen"] > 0 for v in ch0["loader"]["anchors"].values()))
t("10 characters stay R3: no character entry has a GLB, capabilities or several versions", all(not a.get("glb") and not a.get("capabilities") for a in R0 if a["category"] == "character"))

# ====================================================================== the test world: registry copy + Film A + Film B (real storyboard, animatic, judge evidence, approval, lock)
if not (os.environ.get("R7_REUSE") and (W / "film_b/out/lock/lock.json").is_file()):
    FL.world(W); A, TA = FL.film(W, "film_a"); B, TB = FL.film(W, "film_b"); TIMES.update(film_a=TA, film_b=TB)
else: A, B = W / "film_a", W / "film_b"
use()
t("30 the committed registry was never changed by the test world (all approvals are in a registry COPY)", sha(COMMITTED) == COMMITTED_SHA)
ew = AS.entry(LAN, "1.0"); gw = ew["glb"]
t("4 approved asset: approve-glb (the real owner action, run by the labelled TEST_FIXTURE_ONLY harness) moved validated -> approved with by/note/at", gw["status"] == "approved" and "TEST_FIXTURE_ONLY" in gw["approved_by"] and gw["approved_at"])
for nm, d in (("A", A), ("B", B)):
    S = json.load(open(d / "creative/STORYBOARD.json")); An = json.load(open(d / "creative/ANIMATIC.json")); L = json.load(open(d / "out/lock/lock.json"))["approved"]["assets"]
    t("2%s Film %s: the real three.js storyboard (%d panels) and animatic record %s sha1 %s" % ("1" if nm == "A" else "2", nm, len(S["panels"]), V1, gw["sha1"][:10]), S["assets"][LAN] == dict(version="1.0", sha1=gw["sha1"]) and An["assets"][LAN] == dict(version="1.0", sha1=gw["sha1"]) and S["built_by"]["tool"] == "render.mjs --storyboard")
    t("25 Film %s: the lock records the exact asset version + GLB sha1, and lock_stamp check passes" % nm, L[LAN]["glb_sha1"] == gw["sha1"] and L[LAN]["version"] == "1.0" and LS.problems(d) == [])
    t("21/22 Film %s: the lock's set GLB carries the lantern (no placeholder) with its mat: names" % nm, LS.lock_assets(d)[LAN]["sha1"] == gw["sha1"] and all(LS.mat_kept(m, LS.lock_assets(d)[LAN]["materials"]) for m in ew["requirement"]["materials"]))
    t("28 (integration) Film %s: judge evidence carries assets_sha1 and an asset_%s panel; approval is valid and stamped production:false (TEST_FIXTURE_ONLY)" % (nm, LAN), json.load(open(d / "creative/JUDGE.json"))["evidence_read"].get("assets_sha1") and any(p.startswith("asset_" + LAN) for p in json.load(open(d / "creative/JUDGE.json"))["panels"]) and AP.check(d) == [] and json.load(open(d / "approval.json"))["production"] is False)
t("22 Film A and Film B resolve the SAME registry id/version and the SAME GLB sha1 (one registry entry, no duplicate)", json.load(open(A / "out/plan/assets_baked.json"))["assets"][LAN] == json.load(open(B / "out/plan/assets_baked.json"))["assets"][LAN] and len(AS.versions(LAN)) == 1)
t("22 no rebuild: the library GLB file was not rewritten while the two films were made (mtime unchanged), the films only COPY it (out/assets)", lib_glb.stat().st_mtime_ns == lib_mtime and sha(A / "out/assets" / LAN / "1.0" / (LAN + ".glb")) == sha(B / "out/assets" / LAN / "1.0" / (LAN + ".glb")) == gw["sha1"])
t("10 metadata-only: the two films signed the SAME registry-entry hash for the lantern (asset_versions), although it was approved between the validation and the films", json.load(open(A / "approval.json"))["asset_versions"][LAN] == json.load(open(B / "approval.json"))["asset_versions"][LAN])
_x = copy.deepcopy(ew); _x["requirement"] = e0["requirement"]; _x["glb"]["file"] = g0["file"]   # same entry as committed except the lifecycle metadata (and the world's test-only file location / beat link)
t("10 metadata-only: candidate -> validated -> approved (+ owner, validation, approval fields) does not change the signed hash", AP.asset_entry_sha(e0) == AP.asset_entry_sha(_x) and g0["status"] == "validated" and _x["glb"]["status"] == "approved")
TIMES["reuse_resolve_s"] = (TIMES.get("film_b") or {}).get("resolve_s")
# ---- the asset is SEEN in both films (ray test with occlusion) and its anchors land where the placement puts them
for nm, d in (("A", A), ("B", B)):
    r = renders(d, WREG, "--object-visibility", "lantern.lamp_globe,lantern.fuel_tank", "--vis-frames", "0-429"); V = json.load(open(d / "out/plan/object_visibility.json"))["frames"]; seen = sum(1 for x in V if x["hits"] > 0)
    t("29 Film %s: the lantern is really SEEN in the three.js picture (ray grid, occlusion counted) on %d of %d frames" % (nm, seen, len(V)), r.returncode == 0 and seen > 0)
    r = renders(d, WREG, "--visibility"); V = json.load(open(d / "out/plan/visibility.json"))["frames"]
    for k in ("grip", "flame"):
        pairs = [(x.get("lantern." + k), x.get("expect." + k)) for x in V]; both = [(a, b) for a, b in pairs if a and b]; err = max((max(abs(a["x"] - b["x"]), abs(a["y"] - b["y"])) for a, b in both), default=9)
        t("14 Film %s anchor contract: Blender '%s' -> GLB -> three.js place anchor 'lantern.%s' -> Ricks framing (window.visibility / propPos): on screen %d frames, max error %.4f of the frame" % (nm, k, k, len(both), err), len(both) > 0 and err <= 0.002 and not any(b and not a for a, b in pairs))
Vb = json.load(open(B / "out/plan/visibility.json"))["frames"]; cerr = max((abs(x["lantern.flame"]["y"] - x["control.flame"]["y"]) for x in Vb if x.get("lantern.flame") and x.get("control.flame")), default=0)
t("14 the anchor check DISCRIMINATES: an expectation that ignores Film B's scale 1.4 misses the real anchor by %.3f of the frame (> 0.002)" % cerr, cerr > 0.002)
t("23 placement independence (Film B scale 1.4): the grip anchor sits 1.4x higher than in Film A, the registry contract unchanged", abs(json.load(open(B / "film.json"))["props"]["expect.grip"]["pos"][2] - 1.4 * gw["contract"]["anchors"]["grip"][1]) < 1e-3 and gw["contract"] == g0["contract"])
def lock_node(d, inst="lantern"):
    J, _ = G.read(next((d / "out/lock/sets").glob("*.glb"))); return next(n for n in J["nodes"] if n.get("name") == inst)
na, nb = lock_node(A), lock_node(B)
t("19/23 placement independence: Film A and Film B lock the SAME asset at DIFFERENT transforms (A scale 1 rot 0, B scale 1.4 rot 35 deg); the asset bytes are identical", abs(nb.get("scale", [1])[0] - 1.4) < 1e-4 and abs(na.get("scale", [1, 1, 1])[0] - 1) < 1e-4 and abs(2 * __import__("math").degrees(__import__("math").asin(abs(nb["rotation"][1]))) - 35) < 0.05 and na.get("translation") != nb.get("translation"))
TIMES["films_s"] = round(time.time() - T0, 1)

# ====================================================================== R7 asset gate + package + search
gt = AS.gate(V1, [A, B]); t("24 R7 asset gate on the world: TECHNICAL, GOVERNANCE and PRODUCTION all PASS with the two films as evidence (no creative score)", not any(gt.values()))
use(COMMITTED); gc = AS.gate(V1, [A, B]); use()
t("24 R7 asset gate on the COMMITTED registry: GOVERNANCE FAILS (validated, not owner-approved); technical PASS", gc["technical"] == [] and has(gc["governance"], "not approved"))
t("24 R7 asset gate with no film evidence: PRODUCTION FAILS (at least one real storyboard/animatic + lock needed)", has(AS.gate(V1)["production"], "no film evidence"))
r = sh([PY, str(ROOT / "tools/assets.py"), "gate", V1, str(A), str(B)], env={"RICKS_REGISTRY": str(WREG)}); t("25 the gate CLI prints 'CREATIVE APPROVAL: not assessed' (technical/governance/production only)", r.returncode == 0 and "CREATIVE APPROVAL: not assessed" in r.stdout)
P = AS.package(V1); t("11 reusable asset package answers what/version/owner/validated/approved/GLB/materials/anchors/bounds/environments/interactions/evidence (computed view, no file)",
  all(P.get(k) not in (None, [], {}) for k in ("what", "version", "owner", "glb", "materials", "anchors", "bounds_m", "environments", "capabilities", "interactions", "evidence")) and P["technically_validated"] and P["approved"] and P["glb"]["sha1"] == gw["sha1"])
reg = scratch("evidence"); AS.record_evidence(V1, A); AS.record_evidence(V1, B); e = AS.entry(LAN, "1.0")
t("11 record-evidence appends the two films' storyboard/animatic/lock hashes as metadata (the signed entry hash is unchanged)", len(e["glb"]["evidence"]) == 2 and AP.asset_entry_sha(e) == AP.asset_entry_sha(ew))
t("11 record-evidence refuses a film that does not carry the asset", exits(AS.record_evidence, "prop_rail_handcar@1.0", B) is not None); use()
t("26 search: find approved / by category / by capability / by id+version (the registry, no database)", [x["ref"] for x in AS.find(status="approved")] == ["prop_rail_handcar@1.0", V1] and V1 in [x["ref"] for x in AS.find(category="prop/set")] and [x["ref"] for x in AS.find(capability="anchor_target", ident=LAN, version="1.0")] == [V1])

# ====================================================================== lifecycle, resolver negatives (registry copies; fail closed)
def resolve_with(d, reg, **kw): use(reg); r = AS.resolve_problems(d, **kw)[0]; use(); return r
reg = scratch("cand", lambda e, R: e["glb"].update(status="candidate", approved_by=None, approval_note=None, approved_at=None))
t("2 candidate asset: refused in production (G7), allowed only for review drafts / the named test mode", has(resolve_with(B, reg), "is not approved (status candidate)") and resolve_with(B, reg, allow_candidate=True) == [])
use(reg); m = exits(AS.approve_glb, ns(id=V1, by="x", note="y")); use(); t("3 a candidate cannot be approved directly: validate first (approve-glb REFUSED)", m is not None and "run the technical validation first" in m)
reg = scratch("valid", lambda e, R: e["glb"].update(status="validated", approved_by=None, approval_note=None, approved_at=None))
t("3/19 validated is not approved: production resolve refuses a validated asset", has(resolve_with(B, reg), "is not approved (status validated)"))
reg = scratch("noval", lambda e, R: e["glb"].pop("validation"))
t("3 an 'approved' entry without a passing technical validation record is rejected (lifecycle order enforced)", has(resolve_with(B, reg), "needs a passing technical validation record"))
cp = film_copy(B, "film_b_cand"); reg = scratch("cand_pipe", lambda e, R: e["glb"].update(status="candidate")); rc, out = pipe(cp, reg)
t("19 production pipeline with a CANDIDATE asset: stops at G7, 0 expensive renders", rc == 1 and json.load(open(cp / "out/pipeline/production_manifest.json"))["failed_stage"] == "G7" and stills(cp) == 0 and "Expensive render happened: NO" in out)
reg = scratch("dep"); use(reg); AS.deprecate(ns(id=V1, by="owner-stand-in", note="superseded in the R7 test", superseded_by=None)); use()
t("5 deprecated asset: refused for a film unless it says allow_deprecated", has(resolve_with(B, reg), "is DEPRECATED"))
cpd = film_copy(B, "film_b_dep"); F = json.load(open(cpd / "film.json")); F["places"]["yard"]["assets"][0]["allow_deprecated"] = True; json.dump(F, open(cpd / "film.json", "w"))
t("5 deprecated asset: allowed with an explicit \"allow_deprecated\": true; nothing deleted (entry + GLB still there)", resolve_with(cpd, reg) == [] and AS.glb_path(AS.entry(LAN, "1.0", json.load(open(reg))["assets"])["glb"]).is_file())
use(reg); m = exits(AS.approve_glb, ns(id=V1, by="x", note="y")); use(); t("5 a deprecated version cannot be re-approved", m is not None and "deprecated" in m)
def film_with(entries, name):
    d = film_copy(B, name); F = json.load(open(d / "film.json")); F["places"]["yard"]["assets"] = entries; json.dump(F, open(d / "film.json", "w")); return d
t("6 missing asset: an id that is not in the registry fails closed", has(resolve_with(film_with(["prop_no_such_thing@1.0"], "miss"), WREG), "is not in the registry"))
t("7 wrong version: lantern@9.9 fails closed and names the registered versions", has(resolve_with(film_with([LAN + "@9.9"], "wver"), WREG), "version 9.9 requested, registry has 1.0"))
reg = scratch("hash", lambda e, R: e["glb"].update(sha1="0" * 40)); t("8 wrong hash: a registry sha1 that the GLB bytes do not match fails closed (stale GLB)", has(resolve_with(B, reg), "stale GLB"))
need = lambda caps: film_with([dict(id=LAN, version="1.0", name="lantern", at=[0, 0, 0], needs=caps)], "need_" + "_".join(caps))
t("18 unsupported capability: a film that NEEDS 'throwable' is refused with the reason (flights play kit objects, not registry GLBs)", has(resolve_with(need(["throwable"]), WREG), "does not support the capability 'throwable'") and has(resolve_with(need(["throwable"]), WREG), "flights"))
t("18 unsupported capability: 'grippable' is refused (Ricks held props are JS builders; a held registry GLB is NOT implemented)", has(resolve_with(need(["grippable"]), WREG), "held props"))
reg = scratch("capdecl", lambda e, R: e["capabilities"].update(throwable={})); t("18 declaring an unimplemented capability in the registry is itself rejected (check + resolve)", has(AS.check(json.load(open(reg))["assets"]), "unsupported capability 'throwable'") and has(resolve_with(B, reg), "unsupported capability"))
reg = scratch("capanc", lambda e, R: e["capabilities"]["anchor_target"].update(anchors=["grip", "muzzle"])); t("17 a capability without evidence is rejected: anchor_target 'muzzle' is not an anchor of the asset", has(AS.check(json.load(open(reg))["assets"]), "anchor_target anchor muzzle"))
reg = scratch("nostatic", lambda e, R: e["capabilities"].pop("static_prop")); t("17 a film PLACEMENT needs the static_prop capability", has(resolve_with(B, reg), "does not declare the static_prop capability"))
use()

# ====================================================================== versions, immutability, duplicates
reg = scratch("immut"); use(reg)
m = exits(AS.register_glb, ns(id=V1, result=str(W / "rebuild/1/_r.json"), owner=None)); t("12 immutable version: register-glb into the APPROVED v1 is REFUSED (make a new version)", m is not None and "immutable" in m)
req = W / "req.json"; req.write_text(json.dumps(ew["requirement"])); m = exits(AS.require, ns(id=LAN, requirement=str(req), version="1.0", category="prop/set", source="x", builder="x", entry="build", preview="x"))
t("12 immutable version: the requirement of an approved version cannot be edited", m is not None and "immutable" in m)
m = exits(AS.new_version, ns(id=LAN, ver="1.0", builder=None, entry=None, **{"from": "1.0"})); t("24 duplicate prevention: new-version onto an existing id@version is REFUSED", m is not None and "already exists" in m)
Rd = json.load(open(reg)); Rd["assets"].append(copy.deepcopy(AS.entry(LAN, "1.0", Rd["assets"]))); t("24 duplicate prevention: check() reports the same id@version twice and the same GLB registered twice", has(AS.check(Rd["assets"]), "duplicate registry entry"))
use()
# ---- 18 / 26: tamper the GLB that Film A and Film B froze
v1 = AS.glb_path(gw); orig = v1.read_bytes(); v1.write_bytes(orig[:-4] + b"\x00\x00\x00\x01")
try:
    t("9 tampered GLB: resolve fails closed (stale GLB sha1)", has(AS.resolve_problems(B)[0], "stale GLB") or has(AS.resolve_problems(B)[0], "malformed"))
    t("26 stale lock after the asset bytes changed: lock_stamp check FAILS for BOTH films (library bytes no longer the frozen sha1)", has(LS.problems(A), "no longer the frozen") and has(LS.problems(B), "no longer the frozen"))
    t("26 stale evidence: the approvals of both films are no longer valid (G7 no longer passes at G9)", has(AP.check(A), "G7 no longer passes") and has(AP.check(B), "G7 no longer passes"))
    r = renders(B, WREG, "--frames", "0"); t("26 production render REFUSED until a new version is approved (render.mjs --frames, exit 3, no stills)", r.returncode == 3 and "REFUSED" in r.stdout + r.stderr and stills(B) == 0)
    cpt = film_copy(B, "film_b_tamper"); rc, out = pipe(cpt, WREG); t("26 the pipeline stops before any render (G7), 0 expensive renders", rc == 1 and "Expensive render happened: NO" in out and stills(cpt) == 0)
finally: v1.write_bytes(orig)
t("26 restoring the frozen bytes makes both locks and approvals valid again (the check is on bytes, not timestamps)", LS.problems(A) == [] and LS.problems(B) == [] and AP.check(B) == [])
# ---- 27 no placeholder fallback: the three.js seam itself refuses bad bytes / an undeclared id (preview renders, ungated)
cpp = film_copy(B, "film_b_placeholder"); st = cpp / "out/assets" / LAN / "1.0" / (LAN + ".glb"); st.write_bytes(st.read_bytes()[:-4] + b"\x00\x00\x00\x02")
r = renders(cpp, WREG, "--frames", "0", "--scale", "0.25", "--stills-dir", str(cpp / "out/preview")); t("27 no placeholder: a staged GLB whose bytes do not hash to the approved sha1 makes the three.js page THROW (no picture, no stand-in geometry)", r.returncode != 0 and "is not the approved" in r.stdout + r.stderr and not list((cpp / "out/preview").glob("*.png")))
cpu = film_copy(B, "film_b_undeclared"); (cpu / "sets").mkdir(exist_ok=True); s = (ROOT / "templates/threejs_film/sets/platform.js").read_text().replace("export function build(", "export async function build(", 1)
s = re.sub(r"(\n\s*return \{)", "\n  await ctx.asset('prop_rail_handcar', { at: [2, 2, 0] });\\1", s, count=1); (cpu / "sets/platform.js").write_text(s)
r = renders(cpu, WREG, "--frames", "0", "--scale", "0.25", "--stills-dir", str(cpu / "out/preview")); t("27 no placeholder: a set that asks for an asset the film did not declare/resolve THROWS (no silent geometry)", r.returncode != 0 and "not resolved for this film" in r.stdout + r.stderr)
# ---- 11 real asset modification invalidates; 18 v2 is independent and v1 stays reproducible
for what, mut in (("GLB sha1/bytes", lambda e: e["glb"].update(sha1="1" * 40, bytes=1)), ("a material", lambda e: e["glb"]["contract"]["materials"].append("mat:metal.ffffff")), ("an anchor", lambda e: e["glb"]["contract"]["anchors"]["grip"].__setitem__(1, 0.4)),
                  ("the scale/transform", lambda e: e["glb"]["contract"].update(height_m=0.5)), ("the builder", lambda e: e["glb"].update(builder_sha1="2" * 40)), ("a capability", lambda e: e["capabilities"].pop("anchor_target"))):
    x = copy.deepcopy(ew); mut(x); t("11 a REAL change (%s) changes the signed registry-entry hash, so every film's evidence goes stale" % what, AP.asset_entry_sha(x) != AP.asset_entry_sha(ew))
reg = scratch("v2"); use(reg); bld = W / "prop_oil_lantern_v2.py"; bld.write_text((ROOT / e0["blender"]["file"]).read_text().replace('_cyl("lamp_globe", 0.058, 0.08,', '_cyl("lamp_globe", 0.062, 0.08,'))
AS.new_version(ns(id=LAN, ver="2.0", builder=str(bld), entry="build", **{"from": "1.0"}))
r = sh([PY, str(ROOT / "tools/blender_workshop.py"), "build", LAN + "@2.0", "--registry", str(reg), "--out", str(W / "glb" / LAN / "2.0")]); rv2 = json.loads(r.stdout[r.stdout.index("{"):]); (W / "v2.json").write_text(json.dumps(rv2))
AS.register_glb(ns(id=LAN + "@2.0", result=str(W / "v2.json"), owner="Ricks props-hero department")); ok2, val2 = AS.validate(LAN + "@2.0"); AS.approve_glb(ns(id=LAN + "@2.0", **FL.HARNESS))
Rv = json.load(open(reg))["assets"]; e1, e2 = AS.entry(LAN, "1.0", Rv), AS.entry(LAN, "2.0", Rv)
t("18 v2: a new version built from its own builder, registered, technically validated and approved (2 versions of one id in ONE registry)", ok2 and e2["glb"]["status"] == "approved" and len(AS.versions(LAN, Rv)) == 2 and AS.check(Rv) == [])
t("18 v2 is independent: different GLB sha1 and file; v1's entry is byte-for-byte what Film A/B signed", e2["glb"]["sha1"] != e1["glb"]["sha1"] and e2["glb"]["file"] != e1["glb"]["file"] and AP.asset_entry_sha(e1) == json.load(open(B / "approval.json"))["asset_versions"][LAN]["sha1"])
rb = sh([PY, str(ROOT / "tools/blender_workshop.py"), "build", V1, "--force", "--registry", str(reg), "--out", str(W / "v1_again")]); t("18 v1 remains reproducible: rebuilt from ITS builder after v2 exists, same sha1", json.loads(rb.stdout[rb.stdout.index("{"):])["sha1"] == e1["glb"]["sha1"])
t("18 Film B (pinned @1.0) still resolves v1 and its approval + lock stay valid with v2 registered", AS.resolve_problems(B)[0] == [] and AP.check(B) == [] and LS.problems(B) == [])
t("7 a bare id is AMBIGUOUS once two versions exist: the film must pin one (fail closed, no 'latest')", has(AS.resolve_problems(film_with([LAN], "bare"))[0], "pin one"))
m = exits(AS.register_glb, ns(id=LAN + "@2.0", result=str(W / "v2.json"), owner=None)); t("24/12 the approved v2 is immutable too (re-register refused)", m is not None and "immutable" in m)
Rd = json.load(open(reg)); e3 = copy.deepcopy(AS.entry(LAN, "2.0", Rd["assets"])); e3["version"] = "3.0"; Rd["assets"].append(e3); t("24 the same GLB registered under a second version is a duplicate", has(AS.check(Rd["assets"]), "already registered as prop_oil_lantern@2.0"))
use()
# ---- 23 changing Film A's placement touches neither the asset nor Film B
cpa = film_copy(A, "film_a_moved"); F = json.load(open(cpa / "film.json")); F["places"]["canyon"]["assets"][1]["at"] = [1.2, -0.9, 0.0]; json.dump(F, open(cpa / "film.json", "w"), indent=1)
t("23 changing Film A's placement makes Film A's approval STALE (its plan changed) and leaves the registry entry, Film B's approval and lock valid", has(AP.check(cpa), "STALE plan_sha1") and AS.entry(LAN, "1.0") == ew and AP.check(B) == [] and LS.problems(B) == [])
# ---- 15 transform contract (GLB-level), 13 materials survive to the lock
def doctored(name, fn):
    J, BIN = G.read(lib_glb); fn(J); js = json.dumps(J).encode(); js += b" " * (-len(js) % 4); BIN = BIN + b"\x00" * (-len(BIN) % 4)
    out = W / "doctored" / name / "1.0" / (LAN + ".glb"); out.parent.mkdir(parents=True, exist_ok=True); out.write_bytes(b"glTF" + (2).to_bytes(4, "little") + (12 + 8 + len(js) + 8 + len(BIN)).to_bytes(4, "little") + len(js).to_bytes(4, "little") + b"JSON" + js + len(BIN).to_bytes(4, "little") + b"BIN\x00" + BIN); return out
def scl(J): next(n for n in J["nodes"] if n.get("name") == "fuel_tank")["scale"] = [2, 2, 2]
def lift(J): [n.__setitem__("translation", [t_[0], t_[1] + 0.2, t_[2]]) for n in J["nodes"] for t_ in [n.get("translation", [0, 0, 0])]]
def nomat(J): J["materials"][0]["name"] = "Material.001"
def noanc(J): next(n for n in J["nodes"] if n.get("name") == "flame")["name"] = "flame_x"
ctc, req_ = gw["contract"], ew["requirement"]
t("15 transform contract: a mesh with an un-applied scale is rejected", has(G.problems(doctored("scale", scl), req_, ctc), "transform not applied"))
t("15 transform contract: an origin that is not at the base is rejected", has(G.problems(doctored("lift", lift), req_, ctc), "origin is not at the base"))
t("13 material contract: a material that lost its mat: name is rejected", has(G.problems(doctored("nomat", nomat), req_, ctc), "has no mat: name"))
t("14 anchor contract: a GLB that lost the 'flame' anchor is rejected", has(G.problems(doctored("noanc", noanc), req_, ctc), "missing required anchor(s): ['flame']"))
la = LS.lock_assets(A)[LAN]["materials"] | LS.lock_assets(B)[LAN]["materials"]
t("13 material contract end to end: Blender -> GLB contract -> three.js (storyboard + lock export) keeps every mat: name incl. the colour suffixes .2f5a3e and .ffd27a", sorted(gw["contract"]["materials"]) == sorted(ew["requirement"]["materials"]) and "mat:painted_metal_chipped.2f5a3e" in la and "mat:emissive_lamp.ffd27a" in la)
# ---- 30 production/test distinction
pl_src = (ROOT / "tools/pipeline.py").read_text() + (ROOT / "tools/assets.py").read_text()
t("30 no --accept-assets (or any asset auto-approval) flag exists; the pipeline never calls approve-glb / validate", "--accept-assets" not in pl_src and "approve_glb" not in (ROOT / "tools/pipeline.py").read_text() and "approve-glb\"" not in (ROOT / "tools/pipeline.py").read_text())
t("30 the only asset bypass is the named test mode: pipeline passes --allow-candidate ONLY with --unapproved-test-run (stamped production:false)", re.search(r'\["--allow-candidate"\] if a\.unapproved_test_run', (ROOT / "tools/pipeline.py").read_text()) is not None)
t("30 both films are TEST_FIXTURE_ONLY: approval production:false, test_fixture_only:true; the harness approval is labelled in the registry copy", all(json.load(open(d / "approval.json"))["production"] is False and json.load(open(d / "approval.json"))["test_fixture_only"] is True for d in (A, B)) and "TEST_FIXTURE_ONLY" in gw["approval_note"])
t("30 the committed registry is unchanged by the whole suite", sha(COMMITTED) == COMMITTED_SHA)

print("\nR7 TIMES:", json.dumps(TIMES)); print("TOTAL %d s" % (time.time() - T0))
print("\n%d FAIL" % len(fails)); [print("  FAILED: " + f) for f in fails]; sys.exit(1 if fails else 0)
