#!/usr/bin/env python3
"""Asset registry (hybrid Phase 3). library/assets/registry.json; a Blender asset is reusable only if registered.
  assets.py list | check | show <name>
check: every entry has name (unique, snake_case), category, source, version, dependencies, license, preview (file exists), blender representation
(bpy_builder: file exists and defines the entry function; lock_nodes: place + node names). Exit 1 on any problem."""
import json, re, sys, ast
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent; REG = ROOT / "library/assets/registry.json"
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
        b = a["blender"]
        if b.get("kind") == "bpy_builder":
            f = ROOT / b["file"]
            if not f.is_file(): bad.append("%s: builder file missing" % n)
            elif b["entry"] not in [x.name for x in ast.parse(f.read_text()).body if isinstance(x, ast.FunctionDef)]: bad.append("%s: builder has no function %s" % (n, b["entry"]))
        elif b.get("kind") == "lock_nodes":
            if not (b.get("place") and b.get("nodes")): bad.append("%s: lock_nodes needs place and nodes" % n)
        else: bad.append("%s: unknown blender representation %r" % (n, b.get("kind")))
    return bad
if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else "list"
    if c == "list": [print("%-16s %-14s v%s  %s" % (a["name"], a["category"], a["version"], a["blender"]["kind"])) for a in load()]
    elif c == "show": print(json.dumps([a for a in load() if a["name"] == sys.argv[2]], indent=1))
    else:
        bad = check(); print("\n".join(bad) or "registry OK (%d assets)" % len(load())); sys.exit(1 if bad else 0)
