#!/usr/bin/env python3
"""Asset registry (hybrid Phase 3). library/assets/registry.json; a Blender asset is reusable only if registered.
  assets.py list | check | show <name>
check: every entry has name (unique, snake_case), category, source, version, dependencies, license, preview (file exists), blender representation
(bpy_builder: file exists and defines the entry function; lock_nodes: place + node names). Exit 1 on any problem."""
import json, re, sys, ast
from pathlib import Path
import os
ROOT = Path(__file__).resolve().parent.parent; REG = Path(os.environ["RICKS_REGISTRY"]) if os.environ.get("RICKS_REGISTRY") else ROOT / "library/assets/registry.json"   # RICKS_REGISTRY: tests/harness only (a temp copy of the registry)
def load(): return json.load(open(REG))["assets"]
def character_problems(c):
    import hashlib
    bad = []; [bad.append("character.%s missing" % k) for k in ("puppet", "status", "views") if not c.get(k)]
    if c.get("status") not in ("approved", "candidate"): bad.append("status must be approved or candidate")
    if c.get("status") == "approved" and not (c.get("approved_by") and c.get("approval_note")): bad.append("an approved character needs approved_by and approval_note")
    for v in ("front", "34", "side", "back"):
        e = (c.get("views") or {}).get(v)
        if not e: bad.append("view %s missing (the locked view set is front, 34, side, back)" % v); continue
        f = ROOT / e["file"]
        if not f.is_file(): bad.append("view %s file missing" % v)
        elif hashlib.sha1(f.read_bytes()).hexdigest() != e["sha1"]: bad.append("view %s file changed (sha1 differs)" % v)
    return bad
def check():
    bad = []; seen = set()
    for a in load():
        n = a.get("name", "?"); ischar = a.get("category") == "character"; miss = [k for k in ("name", "category", "source", "version", "dependencies", "license", "preview", "character" if ischar else "blender") if not a.get(k)]
        if miss: bad.append("%s: missing %s" % (n, miss)); continue
        if not re.fullmatch(r"[a-z][a-z0-9_]*", n) or n in seen: bad.append("%s: name not unique snake_case" % n)
        seen.add(n)
        if not (ROOT / a["preview"]).is_file(): bad.append("%s: preview file missing" % n)
        if ischar:   # R3: a locked 2D Ricks character (puppet) with its approved four views; no Blender representation (characters stay 2D puppet cards)
            c = a["character"]; bad += ["%s: %s" % (n, x) for x in character_problems(c)]; continue
        bad += ["%s: %s" % (n, x) for x in glb_problems(a)]
        b = a["blender"]
        if b.get("kind") == "bpy_builder":
            f = ROOT / b["file"]
            if not f.is_file(): bad.append("%s: builder file missing" % n)
            elif b["entry"] not in [x.name for x in ast.parse(f.read_text()).body if isinstance(x, ast.FunctionDef)]: bad.append("%s: builder has no function %s" % (n, b["entry"]))
        elif b.get("kind") == "lock_nodes":
            if not (b.get("place") and b.get("nodes")): bad.append("%s: lock_nodes needs place and nodes" % n)
        else: bad.append("%s: unknown blender representation %r" % (n, b.get("kind")))
    return bad

# ---- R4: GLB assets (requirement + glb blocks live IN the registry entry; no second planning schema) -------------------------------------------------------------------------------------
def glb_problems(a, strict_status=False):
    """Registry-level GLB validation for one entry: requirement/glb blocks well-formed, file present, sha1 + contract fresh, GLB contract met. [] when the entry has no glb block (a requirement alone is fine)."""
    import glb as G
    bad = []; g = a.get("glb"); rq = a.get("requirement")
    if not g and not rq: return bad
    if g and not rq: bad.append("requirement block missing (a GLB asset must state what it is for: role, reference beats, materials, anchors, scale)")
    if rq:
        for k in ("role", "reference_beats", "visual_properties", "materials", "anchors", "scale", "orientation", "provenance"):
            if k not in rq or rq[k] in (None, "", []) and k not in ("anchors",): bad.append("requirement.%s missing" % k)
        if (rq.get("scale") or {}).get("height_m") is None: bad.append("requirement.scale.height_m missing")
    if not g: return bad
    for k in ("file", "sha1", "status", "contract", "source_blender"):
        if not g.get(k): bad.append("glb.%s missing" % k)
    if g.get("status") not in ("approved", "candidate"): bad.append("glb.status must be approved or candidate")
    if g.get("status") == "approved" and not (g.get("approved_by") and g.get("approval_note")): bad.append("an approved GLB asset needs approved_by and approval_note")
    f = ROOT / g["file"] if g.get("file") else None
    if not f or not f.is_file(): bad.append("GLB file missing: %s" % g.get("file")); return bad
    bad += G.problems(f, rq, g.get("contract"), g.get("sha1"))
    return bad
def _lookup(n, v=None, reg=None):
    for a in (reg if reg is not None else load()):
        if a["name"] == n: return a
def film_assets(ep):
    """-> [(place, id, version-or-None)] declared in film.json places.<p>.assets ('id' or 'id@version')."""
    f = json.load(open(Path(ep) / "film.json")); out = []
    for pn, pl in (f.get("places") or {}).items():
        for x in pl.get("assets") or []:
            i, _, v = str(x).partition("@"); out.append((pn, i, v or None))
    return out
def resolve_problems(ep, reg=None, allow_candidate=False):
    """Fail-closed: every declared asset must exist in the registry (id, version), have a valid fresh GLB, and be APPROVED (candidate allowed only for review drafts). Returns (problems, baked-dict)."""
    bad = []; baked = {}; R = reg if reg is not None else load()
    for pn, i, v in film_assets(ep):
        a = _lookup(i, reg=R)
        if not a: bad.append("%s: asset id %r is not in the registry" % (pn, i)); continue
        if v and str(a["version"]) != v: bad.append("%s: asset %s version %s requested, registry has %s" % (pn, i, v, a["version"])); continue
        if a.get("category") == "character": bad.append("%s: %s is a character (characters come from film.json cast, not places.assets)" % (pn, i)); continue
        if not a.get("glb"): bad.append("%s: asset %s has no GLB registered (run blender_workshop build + assets.py register-glb)" % (pn, i)); continue
        pr = glb_problems(a)
        if pr: bad += ["%s: asset %s: %s" % (pn, i, x) for x in pr]; continue
        if a["glb"]["status"] != "approved" and not allow_candidate: bad.append("%s: asset %s v%s is not approved (status %s); the owner approves it explicitly (assets.py approve-glb)" % (pn, i, a["version"], a["glb"]["status"])); continue
        g = a["glb"]; baked[i] = dict(version=str(a["version"]), file=g["file"], sha1=g["sha1"], bytes=g.get("bytes"), status=g["status"], contract=g["contract"], source_blender=g["source_blender"], builder_sha1=g.get("builder_sha1"))
    return bad, baked
def resolve(ep, reg=None, allow_candidate=False):
    """Validate + stage: copy each GLB to <ep>/out/assets/<id>/<ver>/<id>.glb and write out/plan/assets_baked.json (the loader's only input). With no declared assets the baked file is removed. Returns problems."""
    import shutil
    ep = Path(ep); bad, baked = resolve_problems(ep, reg, allow_candidate); pf = ep / "out/plan/assets_baked.json"; shutil.rmtree(ep / "out/assets", ignore_errors=True)
    if bad or not baked:
        pf.unlink(missing_ok=True); return bad
    pf.parent.mkdir(parents=True, exist_ok=True); doc = {"schema": "ricks.assets_baked.v1", "assets": {}}
    for i, e in baked.items():
        d = ep / "out/assets" / i / e["version"]; d.mkdir(parents=True, exist_ok=True); shutil.copy(ROOT / e["file"], d / (i + ".glb"))
        doc["assets"][i] = dict(version=e["version"], url="out/assets/%s/%s/%s.glb" % (i, e["version"], i), sha1=e["sha1"], bytes=e["bytes"], status=e["status"], contract=e["contract"], source_blender=e["source_blender"])
    pf.write_text(json.dumps(doc, indent=1, sort_keys=True)); return []
def g7(ep):
    """G7 Assets/sets: SKIP when the film declares no GLB assets; else PASS only if every declared asset resolves (id, version, valid GLB, approved)."""
    d = film_assets(ep)
    if not d: return "SKIP", "no GLB assets declared in film.json places.<p>.assets"
    bad, _ = resolve_problems(ep)
    return ("FAIL", "; ".join(bad)[:300]) if bad else ("PASS", "%d declared asset(s) resolved: %s" % (len(d), ", ".join("%s v%s" % (i, _lookup(i)["version"]) for _, i, _v in d)))
def require(a):
    """require <id> <requirement.json> --category C --source S [--builder FILE --entry E] [--preview P] [--version V]: add (or refresh) the registry entry's requirement (R4B). Registry IS the plan: edited in place."""
    R = json.load(open(REG)); rq = json.load(open(a.requirement)); e = next((x for x in R["assets"] if x["name"] == a.id), None)
    if not e:
        e = dict(name=a.id, category=a.category, source=a.source, version=a.version, dependencies=["film.json places.<p>.assets", "out/plan/assets_baked.json"], license="original work, same terms as this repository", preview=a.preview, blender=dict(kind="bpy_builder", file=a.builder, entry=a.entry)); R["assets"].append(e)
    e["requirement"] = rq; json.dump(R, open(REG, "w"), indent=1); open(REG, "a").write("\n"); print("requirement recorded for %s" % a.id)
def register_glb(a):
    """register-glb <id> <workshop-result.json>: record the workshop's GLB in the registry as status candidate (explicit production action). Never approves."""
    R = json.load(open(REG)); e = next((x for x in R["assets"] if x["name"] == a.id), None)
    if not e: sys.exit("asset %s not in the registry" % a.id)
    r = json.load(open(a.result))
    if r.get("problems"): sys.exit("workshop result has problems: %s" % r["problems"])
    e["glb"] = dict(file=r["glb"], sha1=r["sha1"], bytes=r["bytes"], status="candidate", contract=r["contract"], source_blender=e["blender"]["file"], builder_sha1=r["builder_sha1"], blender_version=r["blender_version"])
    pr = glb_problems(e)
    if pr: sys.exit("registered GLB fails the contract: %s" % pr)
    json.dump(R, open(REG, "w"), indent=1); open(REG, "a").write("\n"); print("GLB registered (candidate): %s v%s sha1 %s" % (a.id, e["version"], r["sha1"][:12]))
def approve_glb(a):
    """approve-glb <id> --by NAME --note TEXT: the OWNER's explicit approval of the registered GLB. The pipeline never calls this."""
    R = json.load(open(REG)); e = next((x for x in R["assets"] if x["name"] == a.id), None)
    if not e or not e.get("glb"): sys.exit("asset %s has no registered GLB" % a.id)
    e["glb"].update(status="approved", approved_by=a.by, approval_note=a.note); json.dump(R, open(REG, "w"), indent=1); open(REG, "a").write("\n"); print("approved %s v%s (sha1 %s) by %s" % (a.id, e["version"], e["glb"]["sha1"][:12], a.by))
if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else "list"
    if c in ("require", "register-glb", "approve-glb"):
        import argparse; ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("id")
        if c == "require": ap.add_argument("requirement"); ap.add_argument("--category", default="prop/hero"); ap.add_argument("--source", required=True); ap.add_argument("--builder", required=True); ap.add_argument("--entry", default="build"); ap.add_argument("--preview", required=True); ap.add_argument("--version", default="1.0")
        elif c == "register-glb": ap.add_argument("result")
        else: ap.add_argument("--by", required=True); ap.add_argument("--note", required=True)
        a = ap.parse_args(); {"require": require, "register-glb": register_glb, "approve-glb": approve_glb}[c](a); sys.exit(0)
    if c in ("resolve", "validate-film"):
        bad = resolve(sys.argv[2], allow_candidate="--allow-candidate" in sys.argv) if c == "resolve" else resolve_problems(sys.argv[2])[0]
        print("\n".join(bad) or ("%s: %d asset(s) OK" % (c, len(film_assets(sys.argv[2]))))); sys.exit(1 if bad else 0)
    if c == "list": [print("%-16s %-14s v%s  %s" % (a["name"], a["category"], a["version"], (a.get("blender") or {}).get("kind", "puppet"))) for a in load()]
    elif c == "show": print(json.dumps([a for a in load() if a["name"] == sys.argv[2]], indent=1))
    else:
        bad = check(); print("\n".join(bad) or "registry OK (%d assets)" % len(load())); sys.exit(1 if bad else 0)
