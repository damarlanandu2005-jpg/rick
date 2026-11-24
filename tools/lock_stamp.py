#!/usr/bin/env python3
"""R4M: the lock freezes EXACTLY what was approved (no new lock format: an `approved` block inside the existing out/lock/lock.json).
  lock_stamp.py stamp <ep>    after `render.mjs --export-lock`: record the approval.json sha1, the exact GLB asset (id, version, sha1) and the exact character card hashes (R3 sequencing: approved character package ->
                              pre-lock cards -> storyboard/animatic/judge -> human approval -> approval.json -> the lock references the approved card hashes -> final render; nothing circular)
  lock_stamp.py check <ep>    fail closed: the lock must carry that block; approval.json unchanged; every declared asset present in the lock's set GLB with the approved id/version/sha1 (node extras) and its `mat:` names intact;
                              the cards equal the approved card hashes; no asset is in the lock that the film did not declare (no silent substitution). An asset change after approval => approval.py check is STALE (asset_versions) and so is this."""
import hashlib, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parent; sys.path.insert(0, str(HERE))
sha = lambda p: hashlib.sha1(Path(p).read_bytes()).hexdigest()
def mat_kept(name, mats):
    """A mat: name survives the three.js lock export if it is present exactly, or - by the Ricks naming convention - when the same set uses that library material in more than one colour the exporter adds the
    colour (mat:<lib>.<rrggbb>): then the LIBRARY name is kept and, for a name that already carries a colour, that colour must still be present. (This is the one documented naming limitation of R4H.)"""
    if name in mats: return True
    lib, _, col = name.partition(".")
    return any(m == name or (m.partition(".")[0] == lib and (not col or m.partition(".")[2] == col)) for m in mats)
def lock_assets(ep):
    """-> {asset id: {version, sha1, materials:set}} actually present in the lock's set GLBs (node extras.asset written by the three.js loader seam)."""
    import glb as G
    out = {}
    for f in sorted((Path(ep) / "out/lock/sets").glob("*.glb")):
        J, _ = G.read(f); nodes = J.get("nodes", []); mats = [m.get("name") for m in J.get("materials", [])]
        for n in nodes:
            x = (n.get("extras") or {}).get("asset")
            if x and x.get("id"): out[x["id"]] = dict(version=x.get("version"), sha1=x.get("sha1"), set=f.name, materials=set(mats))
    return out
def card_hashes(ep):
    import characters as CH
    sp, rp, _, cd, _ = CH.paths(ep); R, e = CH.load(rp); return {} if e else {slot: dict(index_sha1=r["cards"]["index_sha1"], images=[dict(file=x["file"], sha1=x["sha1"]) for x in r["cards"]["images"]]) for slot, r in R["characters"].items()}
def frozen(ep, L=None):
    """R6/A3: what else the lock freezes, as hashes of the FILES/STRUCTURES the render reads (no new format: part of the same `approved` block). camera / performance / timing (words.json + the baked plan) / set (every lock set GLB) / effects (film.json fx, moods, kicks, flights) / lights / highlights.
    Required materials are frozen through the per-asset check below (the `mat:` names inside the lock's set GLBs)."""
    import hashlib as h, approval as AP; ep = Path(ep); pl = ep / "out/plan"; film = json.load(open(ep / "film.json")); L = L or json.load(open(ep / "out/lock/lock.json")); import creative_gates as CG
    j = lambda o: h.sha1(json.dumps(o, sort_keys=True).encode()).hexdigest(); fz = lambda p: sha(p) if Path(p).is_file() else None
    return dict(camera=fz(pl / "camera_baked.json"), performance=fz(pl / "performance_baked.json"), flights=fz(pl / "flights_baked.json"), timing=dict(words=fz(CG._words_path(ep)), film_json=fz(ep / "film.json")),
                set={f.name: sha(f) for f in sorted((ep / "out/lock/sets").glob("*.glb"))}, effects=j({k: film.get(k) for k in ("fx", "moods", "kicks", "flights")}), lights=j(L.get("lights")), highlights=fz(ep / "out/lock/highlights.json"))
def stamp(ep):
    import approval as AP, assets as AS
    ep = Path(ep); bad = AP.check(ep)
    if bad: return ["cannot stamp an unapproved/stale episode: " + "; ".join(bad[:3])]
    lk = ep / "out/lock/lock.json"
    if not lk.is_file(): return ["no lock yet (render.mjs --export-lock first)"]
    L = json.load(open(lk)); A = json.load(open(ep / "approval.json")); decl = {i: v for _, i, v in AS.film_assets(ep)}
    L["approved"] = dict(approval_sha1=sha(ep / "approval.json"), assets={i: dict(version=A["asset_versions"][i]["version"], glb_sha1=AS.entry(i, decl[i])["glb"]["sha1"], registry_sha1=A["asset_versions"][i]["sha1"]) for i in sorted(decl)}, cards=card_hashes(ep), frozen=frozen(ep, L))
    lk.write_text(json.dumps(L)); return []
def problems(ep):
    import approval as AP, assets as AS
    ep = Path(ep); lk = ep / "out/lock/lock.json"
    if not lk.is_file(): return ["no lock"]
    L = json.load(open(lk)); a = L.get("approved"); bad = []
    if not a: return ["the lock carries no approved block (lock_stamp.py stamp): it does not say what it froze"]
    if a["approval_sha1"] != sha(ep / "approval.json"): bad.append("approval.json changed after the lock was stamped")
    decl = {i: v for _, i, v in AS.film_assets(ep)}
    if set(a["assets"]) != set(decl): bad.append("lock asset set %s != declared %s" % (sorted(a["assets"]), sorted(decl)))
    present = lock_assets(ep)
    for i in sorted(decl):
        e = AS.entry(i, decl[i]); fz = a["assets"].get(i)
        if not e or not fz: bad.append("asset %s not frozen in the lock" % i); continue
        if fz["glb_sha1"] != (e.get("glb") or {}).get("sha1") or fz["version"] != str(e["version"]): bad.append("asset %s changed in the registry after the lock froze it (frozen v%s %s)" % (i, fz["version"], fz["glb_sha1"][:10]))
        lib = AS.glb_path(e.get("glb")); stg = ep / "out/assets" / i / fz["version"] / (i + ".glb")   # R7: the BYTES must still be the frozen ones, in the library and in the film's staged copy
        if not lib or not lib.is_file() or sha(lib) != fz["glb_sha1"]: bad.append("asset %s: the library GLB bytes are no longer the frozen sha1 %s (modified after the lock: approve a NEW version)" % (i, fz["glb_sha1"][:10]))
        if not stg.is_file() or sha(stg) != fz["glb_sha1"]: bad.append("asset %s: the film's staged GLB %s is missing or not the frozen bytes" % (i, stg.relative_to(ep)))
        p = present.get(i)
        if not p: bad.append("asset %s is not in the lock's set GLB (silent substitution or a missing asset)" % i); continue
        if p["sha1"] != fz["glb_sha1"] or p["version"] != fz["version"]: bad.append("the lock's set GLB carries asset %s v%s sha1 %s, not the frozen v%s %s" % (i, p["version"], str(p["sha1"])[:10], fz["version"], fz["glb_sha1"][:10]))
        miss = sorted(m for m in e["requirement"]["materials"] if not mat_kept(m, p["materials"]))
        if miss: bad.append("lock set GLB lost mat: names of asset %s: %s" % (i, miss))
    for i in present:
        if i not in decl: bad.append("lock contains undeclared asset %s" % i)
    if a["cards"] != card_hashes(ep): bad.append("the lock's frozen card hashes differ from the approved character cards")
    if a["cards"] and (ep / "out/lock/cards").is_dir():   # R9 fix: the lock's own card drawings (out/lock/cards) must still be the approved cards, so EVERY lock consumer (render guard, final video, audio mux) refuses a tampered one, not only the pipeline's 6b stage (a lock without drawings is the pipeline 6b check's job: nothing downstream of the base render can read drawings that do not exist)
        import characters as CH; bad += ["lock cards: " + x for x in CH.lock_problems(ep)]
    fz = a.get("frozen"); cur = frozen(ep, {**L, "lights": L.get("lights")})
    if not fz: bad.append("the lock froze no camera/timing/performance/set/effects/lights block (re-stamp)")
    else:
        for k in ("camera", "performance", "flights", "timing", "set", "effects", "lights", "highlights"):
            if fz.get(k) != cur.get(k): bad.append("lock frozen %s differs from the current %s (changed after the lock froze it)" % (k, k))
    return bad
if __name__ == "__main__":
    c, ep = sys.argv[1], sys.argv[2]; bad = {"stamp": stamp, "check": problems}[c](ep)
    print("\n".join("- " + x for x in bad) or "lock %s OK" % c); sys.exit(1 if bad else 0)
