#!/usr/bin/env python3
"""R3: the 2D character-production stage (blueprint G6). Reuses the Ricks character package (templates/vector2d_characters), the locked four views, puppets.svgFor,
poses.mjs, the motion library and the lock's own card drawing (render.mjs --export-cards). Characters stay 2D puppet cards; nothing here draws a character itself.
No second schema: the plan stays film.json (cast slots), timing stays words.json + film.json -> baked performance (this stage only REFERENCES it by hash), the registry is library/assets/registry.json.
  creative/characters.json            authored spec per film.json cast slot: character id + version (registry), role, traits, outfit, views_required, expressions/poses required, reference_beats
  creative/character_production.json  built evidence (views, performance summary, cards, hashes)         [written by `build`]
  library/assets/registry.json        category "character" entries: puppet, status approved|candidate, approved_by, the four approved views with sha1
  characters.py build <ep>            views -> performance probe -> cards (render.mjs --export-cards) -> contact sheet -> production record
  characters.py check <ep>            validation (this is gate G6; fails closed)         characters.py check-lock <ep>   the lock's cards must equal the approved cards
  characters.py register ...          owner action: add an approved (or candidate) character to the registry     characters.py register-golden <name>...  register Ricks' CB-approved views_golden characters after re-verifying them
The pipeline never registers or approves a character; a human does."""
import argparse, hashlib, json, re, subprocess, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parent; REG = Path(__import__("os").environ.get("RICKS_REGISTRY") or ROOT / "library/assets/registry.json"); PKG = ROOT / "templates/vector2d_characters"; KIT = ROOT / "templates/threejs_film"
VIEWS = ["front", "34", "side", "back"]; VIEW_PX = [800, 1500]; PROD = (720, 1280); FPS = 30; DIFF_PCT = 0.05
SPEC, REC = "characters.json", "character_production.json"
def sha(p): return hashlib.sha1(Path(p).read_bytes()).hexdigest()
def sha_json(o): return hashlib.sha1(json.dumps(o, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
def combine(items): return hashlib.sha1("|".join("%s:%s" % kv for kv in sorted(items)).encode()).hexdigest()
def package_sha1():
    fs = sorted(p for p in (PKG / "code").rglob("*.mjs")) + [KIT / "puppets.mjs", KIT / "poses.mjs"]; return combine([(str(p.relative_to(ROOT)), sha(p)) for p in fs])
def load(p):
    try: return json.load(open(p)), None
    except FileNotFoundError: return None, "missing"
    except Exception as e: return None, "malformed (%s)" % str(e)[:50]
def registry(): return json.load(open(REG))
def reg_entry(name):
    for a in registry()["assets"]:
        if a.get("name") == name and a.get("category") == "character": return a
def image_ok(path):
    """-> (PIL image or None, problem)"""
    from PIL import Image
    try:
        with Image.open(path) as im: im.verify()
        im = Image.open(path); im.load(); return im, None
    except Exception as e: return None, "unreadable (%s)" % str(e)[:40]
def diff_pct(a, b):
    import numpy as np
    from PIL import Image
    x = np.asarray(Image.open(a).convert("RGB")).astype(int); y = np.asarray(Image.open(b).convert("RGB")).astype(int)
    if x.shape != y.shape: return 100.0
    return float((np.abs(x - y).sum(2) > 120).mean() * 100)
def valid_poses():
    t = (KIT / "poses.mjs").read_text().split("export const POSES = {")[1].split("\n};")[0]; ps = set(re.findall(r"^\s{2}(\w+):\s*\{", t, re.M))
    lib = ROOT / "templates/motion_styles/library.mjs"; ids = set(re.findall(r"^\s*\['([^']+)'", lib.read_text(), re.M)) if lib.is_file() else set(); return ps, ids
def perf_summary(perf, slot):
    ps, ids = valid_poses(); L = perf.get(slot) or []; poses, faces, views, bad, frames, keys = set(), set(), set(), [], 0, set()
    for e in L:
        st = e.get("state") or {}; frames += e["f1"] - e["f0"] + 1
        if not st.get("visible"): continue
        views.add(st.get("view")); faces.add(st.get("face") or "standard")
        for part in (st.get("pose") or "stand").split("+"):
            poses.add(part)
            if part.startswith("m:"):
                if part[2:].split("@")[0].split("+")[0] not in ids: bad.append("motion %s not in the motion library" % part)
            elif part not in ps: bad.append("pose %s is not a Ricks pose" % part)
        keys.add("|".join(str("" if st.get(k) is None else st.get(k)) for k in ("view", "dir", "pose", "face", "mouth", "blink", "prop", "hand")))
    return dict(frames=frames, poses=sorted(poses), faces=sorted(faces), views=sorted(v for v in views if v), unknown=sorted(set(bad)), state_prefixes=sorted(keys))
def paths(ep): ep = Path(ep); return ep / "creative" / SPEC, ep / "creative" / REC, ep / "out/plan/performance_baked.json", ep / "out/characters/cards", ep / "creative/characters"
def spec_sha(slot, film_cast, spec_slot): return sha_json(dict(slot=slot, cast=film_cast, spec=spec_slot))
def ref_beats(ep):
    B, e = load(Path(ep) / "creative/reference_board.json"); return ({str(b.get("id")) for b in (B or {}).get("beats", [])}, sha(Path(ep) / "creative/reference_board.json") if not e else None)
# ---------------- validation (G6)
def validate(ep):
    ep = Path(ep); bad = []; sp, rp, pp, cdir, vdir = paths(ep); film = json.load(open(ep / "film.json")); cast = film.get("cast") or {}
    S, e = load(sp)
    if e: return ["character spec %s (creative/%s)" % (e, SPEC)]
    if S.get("schema") != "ricks.character_spec.v1" or not isinstance(S.get("characters"), dict): return ["character spec malformed (schema ricks.character_spec.v1 with a characters object)"]
    if not cast: return ["film.json has no cast"]
    C = S["characters"]; beats, board_sha = ref_beats(ep)
    for slot in cast:
        if slot not in C: bad.append("[%s] missing character: no spec for this cast slot" % slot)
    for slot in C:
        if slot not in cast: bad.append("[%s] spec for a slot that film.json does not cast" % slot)
    R, e = load(rp)
    if e: return bad + ["character production record %s (creative/%s): run characters.py build" % (e, REC)]
    perf, e = load(pp)
    if e: return bad + ["performance_baked.json %s: bake the plan first" % e]
    pk = package_sha1()
    if R.get("package_sha1") != pk: bad.append("STALE: the character package (rig, cast, faces, poses) changed since the characters were built")
    if R.get("resolution") != list(PROD) or R.get("fps") != FPS: bad.append("production record is not 720x1280 @ 30")
    if board_sha is None or R.get("reference_board_sha1") != board_sha: bad.append("STALE: the reference board changed (or is missing) since the characters were built")
    for slot, c in C.items():
        if slot not in cast: continue
        t = "[%s] " % slot; sl = bad.append
        for k in ("character", "version", "role", "outfit"):
            if not str(c.get(k) or "").strip(): sl(t + "spec field %s missing" % k)
        if not c.get("traits"): sl(t + "spec traits missing")
        if c.get("views_required") != VIEWS: sl(t + "views_required must be exactly the locked set %s (it cannot be reduced)" % VIEWS)
        if not c.get("reference_beats") or any(str(b) not in beats for b in c.get("reference_beats", [])): sl(t + "reference_beats must name beats of creative/reference_board.json (reference -> character requirements)")
        E = reg_entry(c.get("character"))
        if not E: sl(t + "missing character: %r is not in the registry" % c.get("character")); continue
        Ch = E["character"]
        if Ch.get("puppet") != cast[slot].get("puppet"): sl(t + "wrong character in this cast slot: film.json casts puppet %r but %s is puppet %r" % (cast[slot].get("puppet"), c["character"], Ch.get("puppet")))
        if Ch.get("status") != "approved": sl(t + "unapproved character: %s is %s; only an approved character may be cast in production" % (c["character"], Ch.get("status")))
        if str(E["version"]) != str(c.get("version")): sl(t + "wrong character version: spec %s, registry %s" % (c.get("version"), E["version"]))
        r = (R.get("characters") or {}).get(slot)
        if not r: sl(t + "no production record for this slot: run characters.py build"); continue
        if r.get("character") != c.get("character") or str(r.get("version")) != str(c.get("version")): sl(t + "STALE: production record is for %s v%s" % (r.get("character"), r.get("version")))
        if r.get("spec_sha1") != spec_sha(slot, cast[slot], c): sl(t + "STALE: the spec or the film.json cast entry changed since the build")
        if r.get("registry_entry_sha1") != sha_json(E): sl(t + "STALE: the registry entry changed since the build")
        # views
        for v in VIEWS:
            rv = (r.get("views") or {}).get(v); f = ep / "creative/characters" / slot / (v + ".png")
            if not rv or not f.is_file(): sl(t + "missing required view %s" % v); continue
            im, pr = image_ok(f)
            if pr: sl(t + "view %s %s" % (v, pr)); continue
            if list(im.size) != VIEW_PX: sl(t + "view %s is %s, expected %s" % (v, list(im.size), VIEW_PX))
            if sha(f) != rv.get("sha1"): sl(t + "view %s: wrong hash (file changed after the build)" % v)
            g = ROOT / Ch["views"][v]["file"]
            if g.is_file():
                d = diff_pct(f, g)
                if d > Ch.get("max_diff_pct", DIFF_PCT): sl(t + "view %s differs %.3f %% from the approved picture: the character's identity is not preserved" % (v, d))
        # performance (timing stays subordinate: only a reference to the baked file)
        pf = r.get("performance") or {}; cur = perf_summary(perf, slot)
        if slot not in perf or not cur["frames"]: sl(t + "incomplete performance: no baked performance for this slot")
        else:
            if pf.get("slot_sha1") != sha_json(perf[slot]): sl(t + "STALE: the baked performance changed since the build")
            for u in cur["unknown"]: sl(t + "incomplete performance: " + u)
            miss = sorted(set(c.get("expressions_required") or []) - set(cur["faces"])); miss2 = sorted(set(c.get("poses_required") or []) - set(cur["poses"]))
            if miss: sl(t + "incomplete performance: required expressions never performed: %s" % miss)
            if miss2: sl(t + "incomplete performance: required poses never performed: %s" % miss2)
            if (pf.get("probe") or {}).get("warnings") or (pf.get("probe") or {}).get("errors"): sl(t + "the rig warned while drawing the performance: %s" % ((pf["probe"]["warnings"] + pf["probe"]["errors"])[:2]))
            if "probe" not in pf: sl(t + "performance was never probed through the rig")
        # cards
        cd = r.get("cards") or {}; idxf = cdir / slot / "index.json"
        if not idxf.is_file(): sl(t + "missing card index"); continue
        if sha(idxf) != cd.get("index_sha1"): sl(t + "cards: wrong hash for index.json (changed after the build)")
        I = json.load(open(idxf)); keys = set()
        if I.get("puppet") != cast[slot].get("puppet") or I.get("who") != slot: sl(t + "cards are for another character (%s/%s)" % (I.get("who"), I.get("puppet")))
        shas = {x["file"]: x["sha1"] for x in cd.get("images", [])}
        if len(I.get("images", [])) != len(shas) or not shas: sl(t + "cards: the index lists %d drawings, the record %d" % (len(I.get("images", [])), len(shas)))
        for im_ in I.get("images", []):
            f = cdir / slot / im_["file"]; keys |= {"|".join(k.split("|")[1:9]) for k in im_["keys"]}
            if not f.is_file(): sl(t + "missing card %s" % im_["file"]); continue
            img, pr = image_ok(f)
            if pr: sl(t + "corrupted card %s: %s" % (im_["file"], pr)); continue
            if sha(f) != shas.get(im_["file"]): sl(t + "card %s: wrong hash" % im_["file"]); continue
            if list(img.size) != I["px"]: sl(t + "card %s is %s, the index says %s" % (im_["file"], list(img.size), I["px"]))
            if img.mode != "RGBA": sl(t + "card %s has no transparency" % im_["file"])
            else:
                lo, hi = img.getchannel("A").getextrema()
                if hi == 0 or lo == 255: sl(t + "card %s is fully %s (a character card needs a transparent background and a visible figure)" % (im_["file"], "transparent" if hi == 0 else "opaque"))
        if I["px"][1] < PROD[1]: sl(t + "cards are %d px tall, below the %d px production height: they would be upscaled at 720x1280" % (I["px"][1], PROD[1]))
        if slot in perf and not set(cur["state_prefixes"]) <= keys: sl(t + "cards do not cover the baked performance (%d states have no card)" % len(set(cur["state_prefixes"]) - keys))
    return bad
def g6(ep):
    bad = validate(ep); return ("FAIL", "; ".join(bad)[:700]) if bad else ("PASS", "every cast slot: approved registry character at the cast version, four locked views identical to the approved pictures, performance probed through the rig, transparent cards covering the baked states, nothing stale")
def evidence_sha(ep):
    """The character evidence the judge must have seen: spec + production record + contact sheet."""
    ep = Path(ep); sp, rp, _, _, vdir = paths(ep); cs = vdir / "CONTACT_SHEET.png"
    return combine([("spec", sha(sp)), ("record", sha(rp)), ("sheet", sha(cs) if cs.is_file() else "none")]) if sp.is_file() and rp.is_file() else None
def lock_problems(ep):
    ep = Path(ep); sp, rp, _, cdir, _ = paths(ep); R, e = load(rp); bad = []
    if e: return ["production record %s" % e]
    L = ep / "out/lock/cards"
    if not L.is_dir(): return ["no lock cards yet (out/lock/cards)"]
    for slot, r in R["characters"].items():
        for x in r["cards"]["images"] + [dict(file="index.json", sha1=r["cards"]["index_sha1"])]:
            f = L / slot / x["file"]
            if not f.is_file(): bad.append("[%s] lock is missing %s" % (slot, x["file"]))
            elif sha(f) != x["sha1"]: bad.append("[%s] the lock drew a different %s than the approved card" % (slot, x["file"]))
    return bad
# ---------------- build
def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: sys.exit("%s failed:\n%s" % (" ".join(map(str, cmd[:3])), (r.stdout + r.stderr)[-500:]))
    return r
def contact_sheet(ep, R):
    from PIL import Image
    ep = Path(ep); _, _, _, cdir, vdir = paths(ep); rows = []
    for slot, r in R["characters"].items():
        tiles = [Image.open(ep / "creative/characters" / slot / (v + ".png")).convert("RGBA") for v in VIEWS]
        I = json.load(open(cdir / slot / "index.json")); n = len(I["images"]); pick = sorted({0, n // 2, n - 1}); tiles += [Image.open(cdir / slot / I["images"][i]["file"]).convert("RGBA") for i in pick]; rows.append(tiles)
    th = 375; tw = 200; W = tw * max(len(r) for r in rows); sheet = Image.new("RGB", (W, th * len(rows)), (205, 215, 230))
    for y, tiles in enumerate(rows):
        for x, t in enumerate(tiles):
            t = t.resize((tw, th)) if t.size == (800, 1500) else t.resize((tw, int(t.size[1] * tw / t.size[0]))).crop((0, 0, tw, th)) if t.size[1] * tw / t.size[0] >= th else t.resize((tw, int(t.size[1] * tw / t.size[0])))
            sheet.paste(t, (x * tw, y * th), t if t.mode == "RGBA" else None)
    out = vdir / "CONTACT_SHEET.png"; sheet.save(out); return out
def build(ep):
    ep = Path(ep); sp, rp, pp, cdir, vdir = paths(ep); film = json.load(open(ep / "film.json")); cast = film["cast"]; S, e = load(sp)
    if e: sys.exit("no character spec (creative/%s): the character-artist writes it first" % SPEC)
    sys.path.insert(0, str(HERE)); import frames as FR; FR.film_frame_count(ep)   # the baked plan must exist
    for slot, c in S["characters"].items():
        E = reg_entry(c.get("character"))
        if not E: sys.exit("[%s] %r is not in the registry: register it first (owner action)" % (slot, c.get("character")))
    run(["node", str(HERE / "character_stage.mjs"), str(ep / "film.json"), "--out", str(vdir)]); pr = Path(tempfile.mkdtemp()) / "probe.json"
    run(["node", str(HERE / "character_stage.mjs"), str(ep / "film.json"), "--probe", str(pp), "--out", str(pr)]); probe = json.load(open(pr))
    run(["node", str(KIT / "render.mjs"), str(ep / "film.json"), "--export-cards"]); perf = json.load(open(pp)); chars = {}
    for slot, c in S["characters"].items():
        E = reg_entry(c["character"]); I = json.load(open(cdir / slot / "index.json")); ps = perf_summary(perf, slot)
        chars[slot] = dict(character=c["character"], version=str(c["version"]), puppet=cast[slot]["puppet"], spec_sha1=spec_sha(slot, cast[slot], c), registry_entry_sha1=sha_json(E),
            views={v: dict(file="creative/characters/%s/%s.png" % (slot, v), sha1=sha(vdir / slot / (v + ".png")), golden_sha1=E["character"]["views"][v]["sha1"], golden_diff_pct=round(diff_pct(vdir / slot / (v + ".png"), ROOT / E["character"]["views"][v]["file"]), 4)) for v in VIEWS},
            performance=dict(slot_sha1=sha_json(perf[slot]) if slot in perf else None, frames=ps["frames"], poses=ps["poses"], faces=ps["faces"], views=ps["views"], probe=probe),
            cards=dict(dir="out/characters/cards/%s" % slot, index_sha1=sha(cdir / slot / "index.json"), count=len(I["images"]), px=I["px"], images=[dict(file=x["file"], sha1=sha(cdir / slot / x["file"])) for x in I["images"]], lock_path="out/lock/cards/%s" % slot), status="built")
    _, bsha = ref_beats(ep)
    R = dict(schema="ricks.character_production.v1", film=film.get("title"), package_sha1=package_sha1(), resolution=list(PROD), fps=FPS, reference_board_sha1=bsha, characters=chars)
    rp.write_text(json.dumps(R, indent=1)); sheet = contact_sheet(ep, R); print("character production record written: %d slots; contact sheet %s" % (len(chars), sheet.relative_to(ep)))
# ---------------- registry (owner actions)
def _save(R): REG.write_text(json.dumps(R, indent=1) + "\n")
def register(a):
    R = registry()
    if any(x["name"] == a.id and str(x["version"]) == a.version for x in R["assets"]): sys.exit("%s v%s is already registered" % (a.id, a.version))
    if a.status == "approved" and not (a.approved_by and a.note): sys.exit("--approved-by and --note are required for an approved character")
    views = {}
    for v in VIEWS:
        src = (ROOT / "templates/vector2d_characters/views_golden" / ("%s_%s.png" % (a.golden_name, v))) if a.golden_name else Path(a.views) / (v + ".png")
        if not src.is_file(): sys.exit("view %s missing: %s" % (v, src))
        if a.golden_name: dst = src
        else:
            dst = ROOT / "library/characters" / a.id / a.version / (v + ".png"); dst.parent.mkdir(parents=True, exist_ok=True); dst.write_bytes(src.read_bytes())
        im, pr = image_ok(dst)
        if pr: sys.exit("view %s %s" % (v, pr))
        views[v] = dict(file=str(dst.relative_to(ROOT)), sha1=sha(dst))
    R["assets"].append(dict(name=a.id, category="character", source="puppet:%s (templates/vector2d_characters locked cast)" % a.puppet, version=a.version,
        dependencies=["templates/vector2d_characters/code", "templates/threejs_film/puppets.mjs", "templates/threejs_film/poses.mjs"], license="original work, same terms as this repository", preview=views["front"]["file"],
        character=dict(puppet=a.puppet, status=a.status, approved_by=a.approved_by, approval_note=a.note, views=views, max_diff_pct=DIFF_PCT)))
    _save(R); print("registered %s v%s (%s)" % (a.id, a.version, a.status))
def register_golden(names):
    rows = json.load(open(ROOT / "templates/vector2d_characters/views_golden/rows.json")); by = {c["name"]: c for c in rows["characters"]}; tmp = Path(tempfile.mkdtemp())
    for n in names:
        c = by.get(n) or sys.exit("%s is not a Ricks approved views_golden character" % n)
        if c.get("sheet"): sys.exit("%s needs its episode sheet %s, which is not in this repository: its views cannot be re-verified (not registered)" % (n, c["sheet"]))
        json.dump({"cast": {n: {"puppet": c["puppet"]}}}, open(tmp / (n + ".json"), "w")); run(["node", str(HERE / "character_stage.mjs"), str(tmp / (n + ".json")), "--out", str(tmp / "v")])
        for v in VIEWS:
            d = diff_pct(tmp / "v" / n / (v + ".png"), ROOT / "templates/vector2d_characters/views_golden" / ("%s_%s.png" % (n, v)))
            if d > c.get("allow_pct", DIFF_PCT): sys.exit("%s %s: today's rig draws %.3f %% differently from the approved picture: not registered" % (n, v, d))
        ns = argparse.Namespace(id="char_" + n, puppet=c["puppet"], version="1.0", status="approved", approved_by="CB (Ricks views_golden/rows.json)", note=rows["approved"][:240], golden_name=n, views=None); register(ns)
        R = registry(); [x["character"].update(max_diff_pct=c.get("allow_pct", DIFF_PCT)) for x in R["assets"] if x["name"] == "char_" + n]; _save(R)
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["build", "check", "check-lock", "register", "register-golden"]); ap.add_argument("ep", nargs="*"); ap.add_argument("--id"); ap.add_argument("--puppet"); ap.add_argument("--version", default="1.0")
    ap.add_argument("--status", default="approved", choices=["approved", "candidate"]); ap.add_argument("--approved-by"); ap.add_argument("--note"); ap.add_argument("--golden-name"); ap.add_argument("--views"); a = ap.parse_args()
    if a.cmd == "build": build(a.ep[0])
    elif a.cmd in ("check", "check-lock"):
        bad = validate(a.ep[0]) if a.cmd == "check" else lock_problems(a.ep[0]); print("%s: %s" % ("G6 characters" if a.cmd == "check" else "lock cards", "PASS" if not bad else "FAIL")); [print("  -", x) for x in bad]; sys.exit(1 if bad else 0)
    elif a.cmd == "register":
        if not (a.id and a.puppet and (a.golden_name or a.views)): sys.exit("--id --puppet and --golden-name or --views are required")
        register(a)
    else: register_golden(a.ep)
if __name__ == "__main__": main()
