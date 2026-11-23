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
def stamp(ep):
    import approval as AP, assets as AS
    ep = Path(ep); bad = AP.check(ep)
    if bad: return ["cannot stamp an unapproved/stale episode: " + "; ".join(bad[:3])]
    lk = ep / "out/lock/lock.json"
    if not lk.is_file(): return ["no lock yet (render.mjs --export-lock first)"]
    L = json.load(open(lk)); A = json.load(open(ep / "approval.json")); decl = {i for _, i, _v in AS.film_assets(ep)}
    L["approved"] = dict(approval_sha1=sha(ep / "approval.json"), assets={i: dict(version=A["asset_versions"][i]["version"], glb_sha1=AS._lookup(i)["glb"]["sha1"], registry_sha1=A["asset_versions"][i]["sha1"]) for i in sorted(decl)}, cards=card_hashes(ep))
    lk.write_text(json.dumps(L)); return []
def problems(ep):
    import approval as AP, assets as AS
    ep = Path(ep); lk = ep / "out/lock/lock.json"
    if not lk.is_file(): return ["no lock"]
    L = json.load(open(lk)); a = L.get("approved"); bad = []
    if not a: return ["the lock carries no approved block (lock_stamp.py stamp): it does not say what it froze"]
    if a["approval_sha1"] != sha(ep / "approval.json"): bad.append("approval.json changed after the lock was stamped")
    decl = {i for _, i, _v in AS.film_assets(ep)}
    if set(a["assets"]) != decl: bad.append("lock asset set %s != declared %s" % (sorted(a["assets"]), sorted(decl)))
    present = lock_assets(ep)
    for i in sorted(decl):
        e = AS._lookup(i); fz = a["assets"].get(i)
        if not e or not fz: bad.append("asset %s not frozen in the lock" % i); continue
        if fz["glb_sha1"] != (e.get("glb") or {}).get("sha1") or fz["version"] != str(e["version"]): bad.append("asset %s changed in the registry after the lock froze it (frozen v%s %s)" % (i, fz["version"], fz["glb_sha1"][:10]))
        p = present.get(i)
        if not p: bad.append("asset %s is not in the lock's set GLB (silent substitution or a missing asset)" % i); continue
        if p["sha1"] != fz["glb_sha1"] or p["version"] != fz["version"]: bad.append("the lock's set GLB carries asset %s v%s sha1 %s, not the frozen v%s %s" % (i, p["version"], str(p["sha1"])[:10], fz["version"], fz["glb_sha1"][:10]))
        miss = sorted(m for m in e["requirement"]["materials"] if not mat_kept(m, p["materials"]))
        if miss: bad.append("lock set GLB lost mat: names of asset %s: %s" % (i, miss))
    for i in present:
        if i not in decl: bad.append("lock contains undeclared asset %s" % i)
    if a["cards"] != card_hashes(ep): bad.append("the lock's frozen card hashes differ from the approved character cards")
    return bad
if __name__ == "__main__":
    c, ep = sys.argv[1], sys.argv[2]; bad = {"stamp": stamp, "check": problems}[c](ep)
    print("\n".join("- " + x for x in bad) or "lock %s OK" % c); sys.exit(1 if bad else 0)
