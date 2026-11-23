#!/usr/bin/env python3
"""Asset registry (hybrid Phase 3; R4 GLB seam; R7 reusable library). library/assets/registry.json is the ONE registry; a Blender asset is reusable only if registered.
  assets.py list | check | show <id>[@ver]
check: every entry has name (snake_case), category, source, version, dependencies, license, preview (file exists), blender representation
(bpy_builder: file exists and defines the entry function; lock_nodes: place + node names); (name, version) unique; no GLB registered twice. Exit 1 on any problem.

R7 (reusable asset/capability library; extends the R4 seam in place, no second registry, schema or planner):
  identity   one registry entry per <id>@<version>. A version is IMMUTABLE once approved: a changed GLB/material/anchor/transform/contract is a NEW version (new-version), never an edit.
  lifecycle  glb.status  candidate -> validated -> approved -> deprecated
             candidate   registered by register-glb (never production)
             validated   assets.py validate: the TECHNICAL contract passed (GLB, identity, transforms, mat: materials, anchors, bounds, the real three.js loader, deterministic rebuild).
                         Technical only: it is NOT a creative approval.
             approved    assets.py approve-glb --by --note: the OWNER's explicit creative approval of a VALIDATED version (refused otherwise). The pipeline never calls it.
             deprecated  assets.py deprecate: stays in history; a film selects it only with "allow_deprecated": true.
             "locked/referenceable" is not a stored state: it is an approved version that a film's lock froze (lock.json approved.assets, tools/lock_stamp.py).
             status, owner, approval, validation, deprecation and evidence fields are METADATA (LIFECYCLE_META): they change no picture, so they never stale a film's evidence.
  capabilities  entry "capabilities": only what the existing Ricks kit implements for registry GLB assets (CAPABILITIES); anything else is refused (NOT_IMPLEMENTED).
  film.json  places.<p>.assets: "id@ver" (as R4) or {"id", "version", "needs": [capability...], "allow_deprecated", "name", "at", "rot", "scale"}: the FILM owns the shot placement,
             the registry owns the reusable asset. film.js places an entry that has "at" and adds its anchors to the place anchors as "<name>.<anchor>".
  assets.py require | register-glb | validate | approve-glb | deprecate | new-version | resolve | validate-film | gate | package | find | record-evidence   (see each function)"""
import json, re, sys, ast, os, hashlib, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent; REG = Path(os.environ["RICKS_REGISTRY"]) if os.environ.get("RICKS_REGISTRY") else ROOT / "library/assets/registry.json"   # RICKS_REGISTRY: tests/harness only (a temp copy of the registry)
STATUSES = ("candidate", "validated", "approved", "deprecated")
LIFECYCLE_META = ("status", "approved_by", "approval_note", "approved_at", "owner", "validation", "deprecated_by", "deprecation_note", "deprecated_at", "superseded_by", "evidence")
CAPABILITIES = {   # name -> what in the EXISTING kit makes it real (and what its evidence is)
    "static_prop": "placed in a three.js set by the R4 seam (set module ctx.asset(id, {at, rot, scale}) or a film.json places.<p>.assets placement); evidence: the validate loader probe",
    "anchor_target": "its named anchors join the place anchors as <instance>.<anchor> (film.js), the namespace read by window.visibility / propPos (framing), card_shade practical lights "
                     "(lights[].anchor) and held3d tip_at; spec {\"anchors\": [...]}; evidence: the validate loader probe projects each anchor exactly where the placed GLB puts it",
}
NOT_IMPLEMENTED = {   # asked for, but no tested Ricks machinery exists for a registry GLB asset (R7 does not invent it)
    "grippable": "a character holding a registry GLB is not implemented: Ricks held props (film.json held3d) are JS builders (sets/props.js)",
    "held": "see grippable", "throwable": "flights (flights.js) play a kit object, not a registry GLB", "rollable": "no rolling motion contract exists",
    "openable": "no articulated-part contract exists", "breakable": "no destruction system exists", "vehicle": "no vehicle motion contract exists",
    "mechanical": "no moving-part contract exists", "interactive": "too vague: name the existing interaction (anchor_target)", "surface": "no stand-on/put-on contract exists",
    "hero_prop": "a creative role (requirement.role), not a technical capability",
}
now = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
def load(): return json.load(open(REG))["assets"]
def _save(R): json.dump(R, open(REG, "w"), indent=1); open(REG, "a").write("\n")
def key(a): return "%s@%s" % (a.get("name"), a.get("version"))
def parse_ref(s): i, _, v = str(s).partition("@"); return i, (v or None)
def versions(n, reg=None): return [a for a in (reg if reg is not None else load()) if a.get("name") == n]
def entry(n, v=None, reg=None):
    """The registry entry <n>@<v>. With no version: the entry only if exactly ONE version exists (several versions = ambiguous = None: a film must pin one)."""
    vs = versions(n, reg)
    if v is not None: return next((a for a in vs if str(a.get("version")) == str(v)), None)
    return vs[0] if len(vs) == 1 else None
def _lookup(n, v=None, reg=None): return entry(n, v, reg)
def glb_path(g): return ROOT / g["file"] if g and g.get("file") else None
def sha(p): return hashlib.sha1(Path(p).read_bytes()).hexdigest()
def contract_sha(c): return hashlib.sha1(json.dumps(c, sort_keys=True).encode()).hexdigest()
def character_problems(c):
    bad = []; [bad.append("character.%s missing" % k) for k in ("puppet", "status", "views") if not c.get(k)]
    if c.get("status") not in ("approved", "candidate"): bad.append("status must be approved or candidate")
    if c.get("status") == "approved" and not (c.get("approved_by") and c.get("approval_note")): bad.append("an approved character needs approved_by and approval_note")
    for v in ("front", "34", "side", "back"):
        e = (c.get("views") or {}).get(v)
        if not e: bad.append("view %s missing (the locked view set is front, 34, side, back)" % v); continue
        f = ROOT / e["file"]
        if not f.is_file(): bad.append("view %s file missing" % v)
        elif sha(f) != e["sha1"]: bad.append("view %s file changed (sha1 differs)" % v)
    return bad
def check(reg=None):
    bad = []; seen = set(); names = {}; glbs = {}
    for a in (reg if reg is not None else load()):
        n = a.get("name", "?"); ischar = a.get("category") == "character"; miss = [k for k in ("name", "category", "source", "version", "dependencies", "license", "preview", "character" if ischar else "blender") if not a.get(k)]
        if miss: bad.append("%s: missing %s" % (n, miss)); continue
        if not re.fullmatch(r"[a-z][a-z0-9_]*", n): bad.append("%s: name not snake_case" % n)
        if not re.fullmatch(r"\d+(\.\d+)*", str(a["version"])): bad.append("%s: version %r is not a dotted number" % (n, a["version"]))
        if key(a) in seen: bad.append("%s: duplicate registry entry (the same id@version twice)" % key(a))
        seen.add(key(a)); names.setdefault(n, []).append(a)
        if not (ROOT / a["preview"]).is_file(): bad.append("%s: preview file missing" % n)
        if ischar:   # R3: a locked 2D Ricks character (puppet) with its approved four views; no Blender representation (characters stay 2D puppet cards; R7 never moves them)
            c = a["character"]; bad += ["%s: %s" % (n, x) for x in character_problems(c)]; continue
        bad += ["%s: %s" % (key(a), x) for x in glb_problems(a) + lifecycle_problems(a) + capability_problems(a)]
        g = a.get("glb") or {}
        if g.get("sha1"):
            if g["sha1"] in glbs: bad.append("%s: the same GLB (sha1 %s) is already registered as %s (duplicate registry entry)" % (key(a), g["sha1"][:10], glbs[g["sha1"]]))
            glbs[g["sha1"]] = key(a)
        b = a["blender"]
        if b.get("kind") == "bpy_builder":
            f = ROOT / b["file"]
            if not f.is_file(): bad.append("%s: builder file missing" % n)
            elif b["entry"] not in [x.name for x in ast.parse(f.read_text()).body if isinstance(x, ast.FunctionDef)]: bad.append("%s: builder has no function %s" % (n, b["entry"]))
        elif b.get("kind") == "lock_nodes":
            if not (b.get("place") and b.get("nodes")): bad.append("%s: lock_nodes needs place and nodes" % n)
        else: bad.append("%s: unknown blender representation %r" % (n, b.get("kind")))
    for n, vs in names.items():
        if len(vs) > 1 and any(a.get("category") == "character" for a in vs): bad.append("%s: a character has one registry entry (R3); versions of characters are not R7 assets" % n)
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
    if g.get("status") not in STATUSES: bad.append("glb.status must be one of %s" % "|".join(STATUSES))
    if g.get("status") == "approved" and not (g.get("approved_by") and g.get("approval_note")): bad.append("an approved GLB asset needs approved_by and approval_note")
    f = glb_path(g)
    if not f or not f.is_file(): bad.append("GLB file missing: %s" % g.get("file")); return bad
    want = "%s/%s/%s.glb" % (a.get("name"), a.get("version"), a.get("name"))
    if not str(g["file"]).replace("\\", "/").endswith(want): bad.append("identity: the GLB file %s is not stored as .../%s (id/version/id.glb)" % (g["file"], want))
    bad += G.problems(f, rq, g.get("contract"), g.get("sha1"))
    return bad
def lifecycle_problems(a):
    """R7 lifecycle consistency of one GLB entry (the records, not the bytes: glb_problems checks those)."""
    g = a.get("glb") or {}; s = g.get("status"); bad = []
    if not g: return bad
    v = g.get("validation")
    if s in ("validated", "approved"):
        if not isinstance(v, dict) or v.get("PASS") is not True: bad.append("status %s needs a passing technical validation record (assets.py validate)" % s)
        elif v.get("sha1") != g.get("sha1") or v.get("contract_sha1") != contract_sha(g.get("contract")): bad.append("the validation record is STALE: it validated sha1 %s, the registered GLB is %s" % (str(v.get("sha1"))[:10], str(g.get("sha1"))[:10]))
    if s == "deprecated" and not (g.get("deprecated_by") and g.get("deprecation_note")): bad.append("a deprecated version needs deprecated_by and deprecation_note")
    return bad
def capability_problems(a):
    """A declared capability must be one the kit implements for registry GLBs, and its spec must be met by the registered contract."""
    caps = a.get("capabilities"); bad = []
    if caps is None: return bad
    if not isinstance(caps, dict): return ["capabilities must be an object {name: spec}"]
    con = ((a.get("glb") or {}).get("contract") or {}); req = a.get("requirement") or {}
    for name, spec in caps.items():
        if name in NOT_IMPLEMENTED: bad.append("unsupported capability %r: %s" % (name, NOT_IMPLEMENTED[name])); continue
        if name not in CAPABILITIES: bad.append("unknown capability %r (implemented: %s)" % (name, ", ".join(CAPABILITIES))); continue
        if name == "anchor_target":
            an = (spec or {}).get("anchors") or []
            if not an: bad.append("anchor_target needs {\"anchors\": [...]}")
            for k in an:
                if k not in (req.get("anchors") or []): bad.append("anchor_target anchor %s is not a required anchor of the asset" % k)
                if con and k not in (con.get("anchors") or {}): bad.append("anchor_target anchor %s is not in the GLB contract" % k)
    return bad
def film_asset_specs(ep):
    """-> [{place, id, version, needs, allow_deprecated, placement}] from film.json places.<p>.assets ('id', 'id@version' or an object)."""
    f = json.load(open(Path(ep) / "film.json")); out = []
    for pn, pl in (f.get("places") or {}).items():
        for x in pl.get("assets") or []:
            if isinstance(x, dict):
                out.append(dict(place=pn, id=x.get("id"), version=str(x["version"]) if x.get("version") is not None else None, needs=list(x.get("needs") or []), allow_deprecated=x.get("allow_deprecated") is True,
                                placement={k: x[k] for k in ("name", "at", "rot", "scale") if k in x}))
            else:
                i, v = parse_ref(x); out.append(dict(place=pn, id=i, version=v, needs=[], allow_deprecated=False, placement={}))
    return out
def film_assets(ep):
    """-> [(place, id, version-or-None)] declared in film.json places.<p>.assets."""
    return [(s["place"], s["id"], s["version"]) for s in film_asset_specs(ep)]
def resolve_problems(ep, reg=None, allow_candidate=False):
    """Fail-closed: every declared asset must exist in the registry (id, the pinned version), have a valid fresh GLB, support every capability the film needs, not be deprecated
    (unless the film allows it) and be APPROVED (candidate/validated allowed only for review drafts and the named test mode). Returns (problems, baked-dict)."""
    bad = []; baked = {}; R = reg if reg is not None else load()
    for s in film_asset_specs(ep):
        pn, i, v = s["place"], s["id"], s["version"]
        if not i: bad.append("%s: an asset entry has no id" % pn); continue
        vs = versions(i, R)
        if not vs: bad.append("%s: asset id %r is not in the registry" % (pn, i)); continue
        a = entry(i, v, R)
        if not a:
            bad.append(("%s: asset %s version %s requested, registry has %s" % (pn, i, v, ", ".join(sorted(str(x["version"]) for x in vs)))) if v else ("%s: asset %s has %d versions in the registry: pin one (%s@<version>)" % (pn, i, len(vs), i))); continue
        if a.get("category") == "character": bad.append("%s: %s is a character (characters come from film.json cast, not places.assets)" % (pn, i)); continue
        if not a.get("glb"): bad.append("%s: asset %s has no GLB registered (run blender_workshop build + assets.py register-glb)" % (pn, i)); continue
        if i in baked and baked[i]["version"] != str(a["version"]): bad.append("%s: asset %s is declared at two versions in one film" % (pn, i)); continue
        pr = glb_problems(a) + lifecycle_problems(a) + capability_problems(a)
        if pr: bad += ["%s: asset %s: %s" % (pn, key(a), x) for x in pr]; continue
        caps = a.get("capabilities") or {}
        for nd in s["needs"]:
            if nd not in caps: bad.append("%s: asset %s does not support the capability %r the film needs (declared: %s)%s" % (pn, key(a), nd, ", ".join(caps) or "none", " - " + NOT_IMPLEMENTED[nd] if nd in NOT_IMPLEMENTED else ""))
        if s["placement"] and "static_prop" not in caps: bad.append("%s: film.json places asset %s but it does not declare the static_prop capability" % (pn, key(a)))
        st = a["glb"]["status"]
        if st == "deprecated" and not s["allow_deprecated"]: bad.append("%s: asset %s is DEPRECATED (%s); a new film selects it only with \"allow_deprecated\": true" % (pn, key(a), a["glb"].get("deprecation_note"))); continue
        if st not in ("approved", "deprecated") and not allow_candidate: bad.append("%s: asset %s v%s is not approved (status %s); the owner approves it explicitly (assets.py approve-glb)" % (pn, i, a["version"], st)); continue
        if st == "deprecated" and not a["glb"].get("approved_by"): bad.append("%s: asset %s was deprecated without ever being approved" % (pn, key(a))); continue
        g = a["glb"]; baked[i] = dict(version=str(a["version"]), file=g["file"], sha1=g["sha1"], bytes=g.get("bytes"), status=st, contract=g["contract"], source_blender=g["source_blender"], builder_sha1=g.get("builder_sha1"))
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
        doc["assets"][i] = dict(version=e["version"], url="out/assets/%s/%s/%s.glb" % (i, e["version"], i), sha1=e["sha1"], bytes=e["bytes"], contract=e["contract"], source_blender=e["source_blender"])   # R6/A8: NO approval status here: candidate -> approved is metadata, the GLB bytes/version/contract are the picture
    pf.write_text(json.dumps(doc, indent=1, sort_keys=True)); return []
def g7(ep):
    """G7 Assets/sets: SKIP when the film declares no GLB assets; else PASS only if every declared asset resolves (id, version, valid GLB, approved)."""
    d = film_assets(ep)
    if not d: return "SKIP", "no GLB assets declared in film.json places.<p>.assets"
    bad, baked = resolve_problems(ep)
    return ("FAIL", "; ".join(bad)[:300]) if bad else ("PASS", "%d declared asset(s) resolved: %s" % (len(d), ", ".join("%s v%s" % (i, baked[i]["version"]) for _, i, _v in d)))

# ---- owner / workshop actions (explicit; the pipeline calls none of them) -------------------------------------------------------------------------------------------------------------
def _find(R, ref):
    i, v = parse_ref(ref); e = entry(i, v, R["assets"])
    if not e: sys.exit("asset %s not in the registry%s" % (ref, " (several versions: pin one)" if not v and len(versions(i, R["assets"])) > 1 else ""))
    return e
def require(a):
    """require <id> <requirement.json> --category C --source S [--builder FILE --entry E] [--preview P] [--version V]: add (or refresh) the registry entry's requirement (R4B). Registry IS the plan: edited in place.
    An APPROVED version's requirement is frozen (R7): make a new version."""
    R = json.load(open(REG)); rq = json.load(open(a.requirement)); e = entry(a.id, a.version, R["assets"])
    if e and ((e.get("glb") or {}).get("status") in ("approved", "deprecated")): sys.exit("REFUSED: %s is %s and immutable; make a new version (assets.py new-version)" % (key(e), e["glb"]["status"]))
    if not e:
        e = dict(name=a.id, category=a.category, source=a.source, version=a.version, dependencies=["film.json places.<p>.assets", "out/plan/assets_baked.json"], license="original work, same terms as this repository", preview=a.preview, blender=dict(kind="bpy_builder", file=a.builder, entry=a.entry)); R["assets"].append(e)
    e["requirement"] = rq; _save(R); print("requirement recorded for %s" % key(e))
def register_glb(a):
    """register-glb <id>[@ver] <workshop-result.json>: record the workshop's GLB in the registry as status candidate (explicit production action). Never approves.
    R7: refused for an approved/deprecated version (immutable: new-version) and for a GLB already registered under another id@version (no duplicates)."""
    R = json.load(open(REG)); e = _find(R, a.id)
    if (e.get("glb") or {}).get("status") in ("approved", "deprecated"): sys.exit("REFUSED: %s is %s: an approved version is immutable. Make a new version (assets.py new-version %s <ver> --from %s)" % (key(e), e["glb"]["status"], e["name"], e["version"]))
    r = json.load(open(a.result))
    if r.get("problems"): sys.exit("workshop result has problems: %s" % r["problems"])
    if str(r.get("version")) != str(e["version"]) or r.get("id") != e["name"]: sys.exit("REFUSED: the workshop result is %s@%s, not %s" % (r.get("id"), r.get("version"), key(e)))
    dup = [key(x) for x in R["assets"] if x is not e and (x.get("glb") or {}).get("sha1") == r["sha1"]]
    if dup: sys.exit("REFUSED: this GLB (sha1 %s) is already registered as %s (duplicate registry entry)" % (r["sha1"][:10], dup[0]))
    e["glb"] = dict(file=r["glb"], sha1=r["sha1"], bytes=r["bytes"], status="candidate", contract=r["contract"], source_blender=e["blender"]["file"], builder_sha1=r["builder_sha1"], blender_version=r["blender_version"], owner=(e.get("glb") or {}).get("owner") or getattr(a, "owner", None))
    pr = glb_problems(e)
    if pr: sys.exit("registered GLB fails the contract: %s" % pr)
    _save(R); print("GLB registered (candidate): %s sha1 %s" % (key(e), r["sha1"][:12]))
def approve_glb(a):
    """approve-glb <id>[@ver] --by NAME --note TEXT: the OWNER's explicit creative approval of a VALIDATED version. The pipeline never calls this.
    Refused unless the technical validation record is passing and fresh for these exact bytes (R7: validated first; validation alone is never approval)."""
    R = json.load(open(REG)); e = _find(R, a.id)
    if not e.get("glb"): sys.exit("asset %s has no registered GLB" % key(e))
    g = e["glb"]
    if g.get("status") == "deprecated": sys.exit("REFUSED: %s is deprecated" % key(e))
    if g.get("status") not in ("validated", "approved"): sys.exit("REFUSED: %s is %s: run the technical validation first (assets.py validate %s); validated is not approved, approval is the owner's next step" % (key(e), g.get("status"), key(e)))
    pr = glb_problems(e) + lifecycle_problems(dict(e, glb=dict(g, status="validated")))
    if pr: sys.exit("REFUSED: %s fails its technical contract now: %s" % (key(e), pr[:3]))
    if not (a.by and a.note): sys.exit("REFUSED: approval needs --by and --note")
    g.update(status="approved", approved_by=a.by, approval_note=a.note, approved_at=now()); _save(R); print("approved %s (sha1 %s) by %s" % (key(e), g["sha1"][:12], a.by))
def deprecate(a):
    """deprecate <id>@<ver> --by NAME --note TEXT [--superseded-by VER]: the owner retires a version. Nothing is deleted; the GLB, record and history stay reproducible."""
    R = json.load(open(REG)); e = _find(R, a.id); g = e.get("glb")
    if not g: sys.exit("asset %s has no registered GLB" % key(e))
    g.update(status="deprecated", deprecated_by=a.by, deprecation_note=a.note, deprecated_at=now(), **({"superseded_by": a.superseded_by} if a.superseded_by else {})); _save(R); print("deprecated %s" % key(e))
def new_version(a):
    """new-version <id> <ver> --from <oldver> [--builder FILE] [--entry E]: a NEW version entry copied from an existing one (identity, requirement, capabilities, builder), WITHOUT its GLB.
    The old version is untouched (immutable, still reproducible from its own builder)."""
    R = json.load(open(REG)); old = entry(a.id, getattr(a, "from"), R["assets"])
    if not old: sys.exit("asset %s@%s not in the registry" % (a.id, getattr(a, "from")))
    if entry(a.id, a.ver, R["assets"]): sys.exit("REFUSED: %s@%s already exists (duplicate registry entry)" % (a.id, a.ver))
    import copy; e = copy.deepcopy(old); e["version"] = a.ver; e.pop("glb", None)
    if a.builder: e["blender"] = dict(kind="bpy_builder", file=a.builder, entry=a.entry or "build")
    e["source"] = (old.get("source") or "") + " | new version %s of %s@%s" % (a.ver, a.id, getattr(a, "from"))
    R["assets"].append(e); _save(R); print("new version %s (from %s@%s): build it, register-glb, validate, approve" % (key(e), a.id, getattr(a, "from")))
def validate(ref, rebuild=True):
    """validate <id>[@ver]: the TECHNICAL gate, run by the tool (never a creative judgement). Checks: registry identity/version, GLB contract (glb.py: magic, geometry, unique names, applied transforms,
    mat: materials, origin at base, required materials/anchors, scale, bounds), declared capabilities, the REAL three.js loader (render.mjs --visibility on a copy of the kit canyon example with the asset
    placed by film.json: the page loads, hash-checks and parses it with templates/threejs_film/asset_glb.js; every anchor_target anchor must project where the placed GLB puts it) and a deterministic
    REBUILD in Blender (blender_workshop.py build --force into a temp folder: same bytes). PASS -> status candidate -> validated (an approved version stays approved). Writes glb.validation."""
    import subprocess, tempfile, time, shutil
    R = json.load(open(REG)); e = _find(R, ref); g = e.get("glb")
    if not g: sys.exit("asset %s has no registered GLB" % key(e))
    checks = {}; t0 = time.perf_counter()
    checks["registry_identity"] = [x for x in check(R["assets"]) if x.startswith(key(e) + ":") and "validation record" not in x and "status validated needs" not in x and "status approved needs" not in x]
    checks["glb_contract"] = glb_problems(e); checks["capabilities"] = capability_problems(e)
    tmp = Path(tempfile.mkdtemp(prefix="r7val_")); lo = dict(ok=False)
    if not checks["glb_contract"]:
        d = tmp / "ep"; shutil.copytree(ROOT / "templates/film_canyon_example", d); F = json.load(open(d / "film.json"))
        an = ((e.get("capabilities") or {}).get("anchor_target") or {}).get("anchors") or []
        F["places"]["canyon"]["assets"] = [dict(id=e["name"], version=str(e["version"]), name="probe", at=[0.9, 0.4, 0.0], rot=0, scale=1, needs=list((e.get("capabilities") or {}).keys()))]
        exp = {}
        for k in an:
            p = g["contract"]["anchors"][k]; exp[k] = [0.9 + p[0], 0.4 - p[2], 0.0 + p[1]]            # glTF Y up group-local -> plan (x, -z, y) + placement at (rot 0, scale 1)
            F.setdefault("props", {})["probe.%s" % k] = {}; F["props"]["expect.%s" % k] = dict(pos=exp[k], h=0)
        json.dump(F, open(d / "film.json", "w"), indent=1)
        env = dict(os.environ, RICKS_REGISTRY=str(REG)); subprocess.run([sys.executable, str(ROOT / "tools/film_plan.py"), "check", str(d / "film.json")], capture_output=True, env=env)
        rb = resolve(d, allow_candidate=True)
        if rb: lo.update(problems=rb)
        else:
            t1 = time.perf_counter(); p = subprocess.run(["node", str(ROOT / "templates/threejs_film/render.mjs"), str(d / "film.json"), "--visibility"], capture_output=True, text=True, env=env); lo["seconds"] = round(time.perf_counter() - t1, 2)
            st = re.search(r"asset %s: (\d+) bytes, fetch\+hash ([\d.]+) ms, parse ([\d.]+) ms" % e["name"], p.stdout); errs = [l for l in (p.stdout + p.stderr).splitlines() if "[page error]" in l or "Error" in l]
            lo.update(exit=p.returncode, bytes=int(st[1]) if st else None, fetch_hash_ms=float(st[2]) if st else None, parse_ms=float(st[3]) if st else None, errors=errs[:3])
            ok = p.returncode == 0 and st is not None and not errs; anc = {}
            if ok and an:
                V = json.load(open(d / "out/plan/visibility.json"))["frames"]
                for k in an:
                    pairs = [(fr.get("probe.%s" % k), fr.get("expect.%s" % k)) for fr in V]; seen = [(a_, b_) for a_, b_ in pairs if a_ and b_]; err = max((max(abs(a_["x"] - b_["x"]), abs(a_["y"] - b_["y"])) for a_, b_ in seen), default=None)
                    anc[k] = dict(frames_seen=len(seen), max_err_frac=err, missing_frames=sum(1 for a_, b_ in pairs if b_ and not a_)); ok = ok and len(seen) > 0 and err is not None and err <= 0.002 and anc[k]["missing_frames"] == 0
            lo.update(ok=ok, anchors=anc)
    checks["loader"] = lo
    det = dict(ok=False)
    if rebuild and e["blender"].get("kind") == "bpy_builder" and not checks["glb_contract"]:
        t1 = time.perf_counter(); p = subprocess.run([sys.executable, str(ROOT / "tools/blender_workshop.py"), "build", key(e), "--force", "--registry", str(REG), "--out", str(tmp / "rebuild")], capture_output=True, text=True)
        try: r = json.loads(p.stdout[p.stdout.index("{"):])
        except Exception: r = {}
        det.update(seconds=round(time.perf_counter() - t1, 2), rebuilt_sha1=r.get("sha1"), registered_sha1=g["sha1"], blender_version=r.get("blender_version"), builder_unchanged=r.get("builder_sha1") == g.get("builder_sha1"), ok=r.get("sha1") == g["sha1"])
    elif not rebuild: det.update(skipped="--no-rebuild (validation cannot PASS without it)")
    checks["determinism"] = det; shutil.rmtree(tmp, ignore_errors=True)
    PASS = not checks["registry_identity"] and not checks["glb_contract"] and not checks["capabilities"] and checks["loader"].get("ok") is True and det.get("ok") is True
    R = json.load(open(REG)); e = _find(R, ref); g = e["glb"]
    g["validation"] = dict(PASS=PASS, sha1=g["sha1"], contract_sha1=contract_sha(g["contract"]), at=now(), tool="tools/assets.py validate (technical only; NOT a creative approval)", seconds=round(time.perf_counter() - t0, 2), checks=checks)
    if PASS and g.get("status") == "candidate": g["status"] = "validated"
    if not PASS and g.get("status") == "validated": g["status"] = "candidate"
    _save(R); return PASS, g["validation"]
def gate(ref, films=()):
    """The R7 asset gate (subordinate to the Ricks gates; no creative score): TECHNICAL (live GLB contract + fresh passing validation incl. loader + determinism), GOVERNANCE (registry entry,
    owner, status approved, approval evidence), PRODUCTION (for each given film: the storyboard and animatic recorded this exact version/sha1, the lock froze it and its set GLB carries it).
    -> dict(section -> problems). CREATIVE APPROVAL is never concluded here: it is the owner's approve-glb + the film's judge."""
    R = load(); i, v = parse_ref(ref); e = entry(i, v, R); out = dict(technical=[], governance=[], production=[])
    if not e: out["governance"].append("%s is not in the registry (or several versions and none pinned)" % ref); return out
    g = e.get("glb") or {}
    out["technical"] = glb_problems(e) + capability_problems(e) + [x for x in lifecycle_problems(dict(e, glb=dict(g, status="validated"))) if g]
    if not g: out["technical"].append("no GLB registered")
    val = g.get("validation") or {}; ch = val.get("checks") or {}
    if val and not (ch.get("loader") or {}).get("ok"): out["technical"].append("loader check did not pass")
    if val and not (ch.get("determinism") or {}).get("ok"): out["technical"].append("deterministic rebuild did not pass")
    if not g.get("owner"): out["governance"].append("no owner recorded (glb.owner)")
    if g.get("status") != "approved": out["governance"].append("status is %s, not approved (validated is technical only; approval is the owner's)" % g.get("status"))
    elif not (g.get("approved_by") and g.get("approval_note") and g.get("approved_at")): out["governance"].append("approval evidence incomplete (approved_by, approval_note, approved_at)")
    if not films: out["production"].append("no film evidence given (at least one real storyboard/animatic integration and a lock that froze this version)")
    for ep in films:
        out["production"] += ["%s: %s" % (Path(ep).name if Path(ep).name != "ep" else Path(ep).parent.name, x) for x in film_evidence_problems(ep, e)]
    return out
def film_evidence_problems(ep, e):
    """One film's production evidence for asset version e: storyboard + animatic record it, the lock froze its exact GLB sha1 and the lock's set GLB carries it (no placeholder)."""
    import lock_stamp as LS
    ep = Path(ep); bad = []; i = e["name"]; g = e.get("glb") or {}
    for doc in ("STORYBOARD.json", "ANIMATIC.json"):
        p = ep / "creative" / doc
        if not p.is_file(): bad.append("%s missing" % doc); continue
        ev = (json.load(open(p)).get("assets") or {}).get(i)
        if not ev or str(ev.get("version")) != str(e["version"]) or ev.get("sha1") != g.get("sha1"): bad.append("%s does not record %s sha1 %s" % (doc, key(e), str(g.get("sha1"))[:10]))
    lk = ep / "out/lock/lock.json"
    if not lk.is_file(): bad.append("no lock"); return bad
    fz = ((json.load(open(lk)).get("approved") or {}).get("assets") or {}).get(i)
    if not fz or fz.get("glb_sha1") != g.get("sha1") or str(fz.get("version")) != str(e["version"]): bad.append("the lock did not freeze %s at sha1 %s" % (key(e), str(g.get("sha1"))[:10]))
    p = LS.lock_assets(ep).get(i)
    if not p or p.get("sha1") != g.get("sha1"): bad.append("the lock's set GLB does not carry %s (placeholder or missing)" % key(e))
    return bad
def package(ref):
    """The reusable asset PACKAGE: a computed view of ONE registry entry (+ its GLB), no file and no second schema."""
    i, v = parse_ref(ref); e = entry(i, v)
    if not e: sys.exit("%s is not in the registry (or several versions: pin one)" % ref)
    g = e.get("glb") or {}; c = g.get("contract") or {}; val = g.get("validation") or {}
    return {"what": dict(id=e["name"], category=e["category"], role=(e.get("requirement") or {}).get("role"), visual=(e.get("requirement") or {}).get("visual_properties")),
            "version": str(e["version"]), "all_versions": {str(x["version"]): (x.get("glb") or {}).get("status") for x in versions(i)}, "owner": g.get("owner"),
            "technically_validated": bool(val.get("PASS") and val.get("sha1") == g.get("sha1")), "status": g.get("status"),
            "approved": g.get("status") == "approved", "approved_by": g.get("approved_by"), "approval_note": g.get("approval_note"),
            "glb": dict(file=g.get("file"), sha1=g.get("sha1"), bytes=g.get("bytes"), builder=e["blender"].get("file"), blender_version=g.get("blender_version")),
            "materials": c.get("materials"), "anchors": c.get("anchors"), "bounds_m": dict(bbox=c.get("bbox_m"), height=c.get("height_m"), base_y=c.get("base_y"), up=c.get("up"), units=c.get("units")),
            "environments": e.get("environments") or [], "capabilities": e.get("capabilities") or {}, "interactions": {k: v_ for k, v_ in (e.get("capabilities") or {}).items() if k != "static_prop"},
            "evidence": dict(validation=dict(PASS=val.get("PASS"), at=val.get("at"), loader=(val.get("checks") or {}).get("loader"), determinism=(val.get("checks") or {}).get("determinism")) if val else None,
                             films=g.get("evidence") or [], reference_beats=(e.get("requirement") or {}).get("reference_beats"))}
def find(status=None, category=None, capability=None, ident=None, version=None):
    """Search the registry (no database): GLB library assets filtered by status / category (prefix) / capability / id / version."""
    out = []
    for a in load():
        if a.get("category") == "character" or not a.get("glb"): continue
        g = a["glb"]
        if status and g.get("status") != status: continue
        if category and not str(a["category"]).startswith(category): continue
        if capability and capability not in (a.get("capabilities") or {}): continue
        if ident and a["name"] != ident: continue
        if version and str(a["version"]) != str(version): continue
        out.append(dict(ref=key(a), category=a["category"], status=g.get("status"), capabilities=sorted(a.get("capabilities") or {}), sha1=g.get("sha1")))
    return out
def record_evidence(ref, ep):
    """record-evidence <id>@<ver> <ep>: append one film's PRODUCTION evidence to glb.evidence (metadata) after checking it is real (film_evidence_problems)."""
    R = json.load(open(REG)); e = _find(R, ref); bad = film_evidence_problems(ep, e)
    if bad: sys.exit("REFUSED: no production evidence in %s: %s" % (ep, bad[:3]))
    ep = Path(ep); F = json.load(open(ep / "film.json"))
    e["glb"].setdefault("evidence", []).append(dict(film=F.get("title"), storyboard_sha1=sha(ep / "creative/STORYBOARD.json"), animatic_sha1=sha(ep / "creative/ANIMATIC.json"), lock_sha1=sha(ep / "out/lock/lock.json"), at=now()))
    _save(R); print("evidence recorded for %s" % key(e))
if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else "list"
    import argparse
    if c in ("require", "register-glb", "approve-glb", "deprecate", "new-version"):
        ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("id")
        if c == "require": ap.add_argument("requirement"); ap.add_argument("--category", default="prop/hero"); ap.add_argument("--source", required=True); ap.add_argument("--builder", required=True); ap.add_argument("--entry", default="build"); ap.add_argument("--preview", required=True); ap.add_argument("--version", default="1.0")
        elif c == "register-glb": ap.add_argument("result"); ap.add_argument("--owner")
        elif c == "new-version": ap.add_argument("ver"); ap.add_argument("--from", required=True); ap.add_argument("--builder"); ap.add_argument("--entry")
        else: ap.add_argument("--by", required=True); ap.add_argument("--note", required=True); ap.add_argument("--superseded-by")
        a = ap.parse_args(); {"require": require, "register-glb": register_glb, "approve-glb": approve_glb, "deprecate": deprecate, "new-version": new_version}[c](a); sys.exit(0)
    if c in ("resolve", "validate-film"):
        bad = resolve(sys.argv[2], allow_candidate="--allow-candidate" in sys.argv) if c == "resolve" else resolve_problems(sys.argv[2])[0]
        print("\n".join(bad) or ("%s: %d asset(s) OK" % (c, len(film_assets(sys.argv[2]))))); sys.exit(1 if bad else 0)
    if c == "validate":
        ok, v = validate(sys.argv[2], rebuild="--no-rebuild" not in sys.argv); print(json.dumps(v, indent=1)); print("TECHNICAL VALIDATION = %s (creative approval: not assessed; the owner's approve-glb)" % ("PASS" if ok else "FAIL")); sys.exit(0 if ok else 1)
    if c == "gate":
        r = gate(sys.argv[2], [x for x in sys.argv[3:] if not x.startswith("--")])
        for s in ("technical", "governance", "production"): print("%-11s %s" % (s.upper(), "PASS" if not r[s] else "FAIL: " + "; ".join(r[s])[:400]))
        print("CREATIVE APPROVAL: not assessed by this gate (owner approve-glb + the film's judge)"); sys.exit(0 if not any(r.values()) else 1)
    if c == "package": print(json.dumps(package(sys.argv[2]), indent=1)); sys.exit(0)
    if c == "find":
        ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("--status"); ap.add_argument("--category"); ap.add_argument("--capability"); ap.add_argument("--id"); ap.add_argument("--version"); a = ap.parse_args()
        [print("%-28s %-12s %-10s %s" % (x["ref"], x["category"], x["status"], ",".join(x["capabilities"]))) for x in find(a.status, a.category, a.capability, a.id, a.version)]; sys.exit(0)
    if c == "record-evidence": record_evidence(sys.argv[2], sys.argv[3]); sys.exit(0)
    if c == "list": [print("%-20s %-14s v%-5s %-10s %s" % (a["name"], a["category"], a["version"], (a.get("glb") or {}).get("status", "-"), (a.get("blender") or {}).get("kind", "puppet"))) for a in load()]
    elif c == "show": i, v = parse_ref(sys.argv[2]); print(json.dumps([a for a in load() if a["name"] == i and (v is None or str(a["version"]) == v)], indent=1))
    else:
        bad = check(); print("\n".join(bad) or "registry OK (%d entries)" % len(load())); sys.exit(1 if bad else 0)
