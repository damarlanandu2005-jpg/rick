#!/usr/bin/env python3
"""Phase 5 CPU gate: the Western runs through the SAME pipeline (no separate architecture).  python3 phase5/test_western_cpu.py [workdir]
W1 episode recipe == kit/recipes/western_noon.json   W2 plan gates 0 FAIL (layers + flights included)   W3 three.js base 720x1280 + lock export
W4 density: >=600 mesh objects and >=30 kinds (the kit's rule, read from the recipe)   W5 every named layer object exists in the lock glb
W6 flight on the western street: gate_flight PASS   W7 final_video + qa_hybrid PASS on the flight range (plan/three.js/blender/composite/video stages)"""
import json, re, shutil, struct, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent; W = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/p5_cpu"); ep = W / "ep"; res = []
def ok(n, c, m=""): res.append(bool(c)); print("PASS" if c else "FAIL", n, m)
def sh(c): return subprocess.run(c, capture_output=True, text=True)
shutil.rmtree(W, ignore_errors=True); shutil.copytree(ROOT / "templates/film_western_example", ep, ignore=shutil.ignore_patterns("out")); film = ep / "film.json"; node = ROOT / "templates/threejs_film/render.mjs"
ok("W1 episode recipe == kit recipe", (ep / "western_noon.json").read_bytes() == (ROOT / "kit/recipes/western_noon.json").read_bytes())
p = sh([sys.executable, str(ROOT / "tools/film_plan.py"), "check", str(film)]); ok("W2 plan gates 0 FAIL", " 0 FAIL" in p.stdout.splitlines()[-1], p.stdout.splitlines()[-1][:60])
fr = list(range(0, 10)) + list(range(316, 331)); sh(["node", str(node), str(film), "--frames", ",".join(map(str, fr)), "--scale", "0.666667", "--no-captions"]); q = sh(["node", str(node), str(film), "--export-lock"]); ok("W3 base + lock export", q.returncode == 0 and (ep / "out/lock/lock.json").exists())
glb = (ep / "out/lock/sets/platform.glb").read_bytes(); js = json.loads(glb[20:20 + struct.unpack("<I", glb[12:16])[0]]); nodes = [x for x in js["nodes"] if "mesh" in x]; kinds = {re.sub(r"_\d{2,}$", "", x["name"]) for x in nodes}
R = json.loads((ep / "western_noon.json").read_text())["density"]; ok("W4 density (recipe: %d kinds, %d instances)" % (R["kinds"], R["instances"]), len(kinds) >= R["kinds"] and len(nodes) >= R["instances"], "%d kinds, %d objects" % (len(kinds), len(nodes)))
L = json.loads((ep / "out/plan/layers_baked.json").read_text()); need = {o for v in L.values() for o in v["objects"]}; ok("W5 layer objects exist in the lock glb", need <= kinds, "missing %s" % sorted(need - kinds))
g = sh([sys.executable, str(ROOT / "phase2/gate_flight.py"), str(ep), "--stills", ",".join(map(str, range(320, 329)))]); ok("W6 flight gates on the western street", g.returncode == 0, g.stdout.strip().splitlines()[-1])
sys.path.insert(0, str(ROOT / "tools")); import final_video as FV; FV.assemble(ep, 316, 330); z = sh([sys.executable, str(ROOT / "tools/qa_hybrid.py"), str(ep)]); ok("W7 final video + QA PASS (flight range)", z.returncode == 0, "; ".join(l for l in z.stdout.splitlines() if "FAIL" in l)[:200])
print("GATE", "PASS" if all(res) else "FAIL"); sys.exit(0 if all(res) else 1)
