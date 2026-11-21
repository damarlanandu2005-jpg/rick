"""Lock motion -> Blender (hybrid Phase 2).  Applies out/lock/motion/<place>.json (per-frame local TRS of the nodes the three.js set moves, flights included)
to the objects from_lock.import_set made, matched by the lock_id custom property AND the node name, frame for frame (no resampling, no new timing).
The conversion is the glTF importer's Y-up -> Z-up rule, kept bpy-free in convert() so a CPU test can check it:
  position (x,y,z)->(x,-z,y)   quaternion (x,y,z,w)->(w,x,-z,y)   scale (x,y,z)->(x,z,y)
"""
import json, os
def convert(trs):
    """trs: [[px,py,pz,qx,qy,qz,qw,sx,sy,sz,opacity], ...] (three.js axes) -> list of (loc, quat_wxyz, scale, opacity) in Blender axes"""
    out = []
    for r in trs:
        px, py, pz, qx, qy, qz, qw, sx, sy, sz, op = r
        out.append(((px, -pz, py), (qw, qx, -qz, qy), (sx, sz, sy), op))
    return out
def load(lock_dir, place): return json.load(open(os.path.join(lock_dir, "motion", place + ".json"), encoding="utf-8"))
def apply(objs, lock_dir, place, f0=None, f1=None, only=None):
    """keyframe every moved node on frames f0..f1 (default: all). only = set of node names to limit to. Returns {name: n_keys}."""
    import bpy
    M = load(lock_dir, place); frames = M["frames"]; done = {}
    by_id = {int(o["lock_id"]): o for o in objs if "lock_id" in o.keys()}
    for lid, node in M["nodes"].items():
        o = by_id.get(int(lid))
        if o is None: raise RuntimeError("lock motion node %s (%s) has no object with that lock_id in the imported set" % (lid, node["name"]))
        if not o.name.startswith(node["name"]): raise RuntimeError("lock_id %s is %s in the lock but %s in Blender" % (lid, node["name"], o.name))
        if only and node["name"] not in only: continue
        o.rotation_mode = "QUATERNION"; n = 0
        for f, (loc, q, sc, op) in zip(frames, convert(node["trs"])):
            if (f0 is not None and f < f0) or (f1 is not None and f > f1): continue
            o.location, o.rotation_quaternion, o.scale = loc, q, sc
            o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_quaternion", frame=f); o.keyframe_insert("scale", frame=f); n += 1
        done[node["name"]] = n
    return done
