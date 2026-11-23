#!/usr/bin/env python3
"""Minimal, dependency-free GLB reader + the R4 GLB CONTRACT checker (no glTF library: the registry only needs identity, geometry bounds, transforms, materials, anchors).
Contract (the Ricks conventions, nothing new): metres; glTF Y up (Blender Z up exported with the standard Y-up option); origin at the asset's base (min Y = 0); transforms APPLIED (mesh nodes have unit scale
and identity rotation); every mesh primitive has a material named mat:<library name>[.rrggbb] (templates/threejs_film/film.js 'THE LOCK'); anchors are mesh-less nodes named exactly as the Ricks held-prop anchors
(grip, tip, grip_left, grip_right, ...) positioned group-local; object names stable and unique; export deterministic (same Blender scene -> same bytes).
  glb.py <file.glb>        print the parsed summary"""
import json, math, struct, sys
from pathlib import Path
class GlbError(Exception): pass
def read(path):
    b = Path(path).read_bytes()
    if len(b) < 20 or b[:4] != b"glTF": raise GlbError("not a GLB (bad magic)")
    ver, ln = struct.unpack("<II", b[4:12])
    if ver != 2: raise GlbError("glTF version %d (need 2)" % ver)
    if ln != len(b): raise GlbError("GLB length field %d != file size %d (truncated or padded)" % (ln, len(b)))
    o = 12; J = None; BIN = None
    while o + 8 <= len(b):
        cl, ct = struct.unpack("<II", b[o:o + 8]); data = b[o + 8:o + 8 + cl]
        if len(data) != cl: raise GlbError("chunk runs past the end of the file")
        if ct == 0x4E4F534A: 
            try: J = json.loads(data.decode("utf-8"))
            except Exception as e: raise GlbError("JSON chunk is not valid JSON (%s)" % str(e)[:40])
        elif ct == 0x004E4942: BIN = data
        o += 8 + cl
    if J is None: raise GlbError("no JSON chunk")
    return J, BIN
def _mat(t, r, s):
    x, y, z, w = r; R = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    return [[R[i][0] * s[0], R[i][1] * s[1], R[i][2] * s[2], t[i]] for i in range(3)] + [[0, 0, 0, 1]]
def _mul(a, b): return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
def _node_m(n):
    if "matrix" in n: m = n["matrix"]; return [[m[c * 4 + r] for c in range(4)] for r in range(4)]
    return _mat(n.get("translation", [0, 0, 0]), n.get("rotation", [0, 0, 0, 1]), n.get("scale", [1, 1, 1]))
def summarize(path):
    """-> dict: nodes (name, mesh, translation/rotation/scale, extras), materials per mesh, anchors (world positions of mesh-less leaf nodes), bbox_min/max (world, Y up), sha1."""
    import hashlib
    J, BIN = read(path); nodes = J.get("nodes", []); meshes = J.get("meshes", []); mats = J.get("materials", []); acc = J.get("accessors", [])
    if not J.get("scenes") or not nodes: raise GlbError("no scene or no nodes")
    out = dict(nodes=[], materials=set(), mesh_materials={}, anchors={}, sha1=hashlib.sha1(Path(path).read_bytes()).hexdigest(), bytes=Path(path).stat().st_size, generator=(J.get("asset") or {}).get("generator"), roles={})
    lo = [1e9] * 3; hi = [-1e9] * 3; names = []
    def walk(i, M):
        n = nodes[i]; W = _mul(M, _node_m(n)); nm = n.get("name", "node%d" % i); names.append(nm)
        out["nodes"].append(dict(name=nm, mesh=n.get("mesh"), t=n.get("translation", [0, 0, 0]), r=n.get("rotation", [0, 0, 0, 1]), s=n.get("scale", [1, 1, 1]), extras=n.get("extras")))
        if "mesh" in n:
            for pr in meshes[n["mesh"]]["primitives"]:
                mi = pr.get("material"); mn = mats[mi].get("name") if mi is not None and mi < len(mats) else None
                out["mesh_materials"].setdefault(nm, []).append(mn); out["materials"].add(mn)
                a = acc[pr["attributes"]["POSITION"]]; mn_, mx_ = a.get("min"), a.get("max")
                if not mn_ or not mx_: raise GlbError("POSITION accessor has no min/max")
                for cx in (mn_[0], mx_[0]):
                    for cy in (mn_[1], mx_[1]):
                        for cz in (mn_[2], mx_[2]):
                            p = [sum(W[r][c] * v for c, v in enumerate((cx, cy, cz, 1))) for r in range(3)]
                            for k in range(3): lo[k] = min(lo[k], p[k]); hi[k] = max(hi[k], p[k])
            if isinstance(n.get("extras"), dict) and n["extras"].get("role"): out["roles"][nm] = n["extras"]["role"]
        elif not n.get("children"): out["anchors"][nm] = [round(W[r][3], 5) for r in range(3)]
        for c in n.get("children", []): walk(c, W)
    I = [[1 if i == j else 0 for j in range(4)] for i in range(4)]
    for r in J["scenes"][J.get("scene", 0)]["nodes"]: walk(r, I)
    if lo[0] > hi[0]: raise GlbError("no geometry")
    out.update(bbox_min=[round(v, 5) for v in lo], bbox_max=[round(v, 5) for v in hi], names=names); out["materials"] = sorted(m for m in out["materials"] if m is not None) + (["<unnamed>"] if None in out["materials"] else []); return out
def contract_of(path):
    """The contract a freshly exported GLB DEFINES (written into the registry by the owner/production registration step)."""
    s = summarize(path); bb = [round(s["bbox_max"][k] - s["bbox_min"][k], 4) for k in range(3)]
    return dict(up="Y", units="m", materials=s["materials"], anchors=s["anchors"], roles=s["roles"], bbox_m=bb, height_m=bb[1], base_y=s["bbox_min"][1], nodes=sorted(n["name"] for n in s["nodes"]))
def problems(path, req=None, contract=None, sha1=None, tol_pct=1.0, anchor_tol=0.002):
    """Fail-closed validation of a GLB against its registry contract/requirement. Returns a list of human-readable problems (empty = valid)."""
    bad = []
    try: s = summarize(path)
    except FileNotFoundError: return ["GLB file missing"]
    except GlbError as e: return ["malformed GLB: %s" % e]
    except Exception as e: return ["malformed GLB: %s" % str(e)[:60]]
    if sha1 and s["sha1"] != sha1: bad.append("stale GLB: sha1 %s... is not the registered %s..." % (s["sha1"][:10], sha1[:10]))
    names = [n["name"] for n in s["nodes"]]
    if len(names) != len(set(names)): bad.append("object names are not unique: %s" % sorted({n for n in names if names.count(n) > 1})[:3])
    for n in s["nodes"]:
        if n["mesh"] is not None and (any(abs(v - 1) > 1e-4 for v in n["s"]) or any(abs(v) > 1e-4 for v in n["r"][:3])): bad.append("transform not applied on mesh node %s (scale %s rotation %s)" % (n["name"], [round(v, 3) for v in n["s"]], [round(v, 3) for v in n["r"]]))
    un = [m for ms in s["mesh_materials"].values() for m in ms if m is None]
    if un: bad.append("a mesh has no material (material assignment lost)")
    for mesh, ms in s["mesh_materials"].items():
        for m in ms:
            if m is not None and not m.startswith("mat:"): bad.append("mesh %s: material %r has no mat: name" % (mesh, m))
    if abs(s["bbox_min"][1]) > 0.01: bad.append("origin is not at the base: min Y is %.3f m" % s["bbox_min"][1])
    h = s["bbox_max"][1] - s["bbox_min"][1]
    if req:
        rm = req.get("materials") or []; miss = sorted(set(rm) - set(s["materials"]))
        if miss: bad.append("missing required material(s): %s" % miss)
        if rm and len(set(s["materials"])) < len(rm): bad.append("the asset collapsed to %d material(s), %d required" % (len(set(s["materials"])), len(rm)))
        ra = req.get("anchors") or []; ma = sorted(set(ra) - set(s["anchors"]))
        if ma: bad.append("missing required anchor(s): %s" % ma)
        sc = req.get("scale") or {}
        if sc.get("height_m") and abs(h - sc["height_m"]) > sc["height_m"] * sc.get("tol_pct", tol_pct) / 100: bad.append("incorrect scale: height %.3f m, required %.3f m +-%s%%" % (h, sc["height_m"], sc.get("tol_pct", tol_pct)))
    if contract:
        miss = sorted(set(contract.get("materials", [])) - set(s["materials"]))
        if miss: bad.append("contract material(s) missing from the GLB: %s" % miss)
        for k, p in (contract.get("anchors") or {}).items():
            q = s["anchors"].get(k)
            if q is None: bad.append("contract anchor %s missing from the GLB" % k)
            elif max(abs(q[i] - p[i]) for i in range(3)) > anchor_tol: bad.append("anchor %s moved: %s, contract %s" % (k, q, p))
        ch = contract.get("height_m")
        if ch and abs(h - ch) > ch * tol_pct / 100: bad.append("transform/scale drift: height %.3f m, contract %.3f m" % (h, ch))
        for k, v in zip("xyz", contract.get("bbox_m", [])):
            got = s["bbox_max"]["xyz".index(k)] - s["bbox_min"]["xyz".index(k)]
            if v and abs(got - v) > max(v * tol_pct / 100, 0.003): bad.append("bounding box %s is %.3f m, contract %.3f m" % (k, got, v))
    return bad
if __name__ == "__main__":
    s = summarize(sys.argv[1]); print(json.dumps({k: s[k] for k in ("sha1", "bytes", "generator", "materials", "anchors", "bbox_min", "bbox_max")}, indent=1))
