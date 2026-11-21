#!/usr/bin/env python3
"""Phase 3 CPU gate: layer spec bake + hash invalidation (no Blender).  python3 phase3/test_layers_cpu.py [workdir]
T1 spec gate passes / a bad spec fails   T2 deterministic bake (same ints twice)   T3 status MISSING -> FRESH (manifest written) -> STALE (a base still changes)
T4 STALE-LOCK when a hashed plan file changes after the lock export   T5 named objects exist in the lock glb (every layer object is a node name)"""
import json, os, shutil, subprocess, sys, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT / "tools")); import layers as LY
W = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/p3_cpu"); ep = W / "ep"; res = []
def ok(n, c, m=""): res.append(bool(c)); print("PASS" if c else "FAIL", n, m)
def sh(c): return subprocess.run(c, capture_output=True, text=True)
shutil.rmtree(W, ignore_errors=True); shutil.copytree(ROOT / "templates/film_flight_example", ep, ignore=shutil.ignore_patterns("out")); film = ep / "film.json"; node = ROOT / "templates/threejs_film/render.mjs"
p = sh([sys.executable, str(ROOT / "tools/film_plan.py"), "check", str(film)]); ok("T1 spec gate passes", "layers" in p.stdout and "0 FAIL" in p.stdout); b1 = (ep / "out/plan/layers_baked.json").read_text()
bad = json.loads(film.read_text()); bad["layers"][0]["objects"] = []; (W / "bad.json").write_text(json.dumps(bad)); shutil.copy(W / "bad.json", ep / "bad_film.json")
pb = sh([sys.executable, str(ROOT / "tools/film_plan.py"), "check", str(ep / "bad_film.json")]); ok("T1 bad spec (no objects) FAILS", "FAIL layers" in pb.stdout, pb.stdout.strip().splitlines()[-1])
sh([sys.executable, str(ROOT / "tools/film_plan.py"), "check", str(film)]); ok("T2 bake deterministic", b1 == (ep / "out/plan/layers_baked.json").read_text())
fr = ",".join(str(f) for f in range(201, 211)); sh(["node", str(node), str(film), "--frames", fr, "--scale", "0.666667", "--no-captions"]); sh(["node", str(node), str(film), "--export-lock"])
ok("T3a status MISSING", LY.status(str(ep))["clock_reflect"] == "MISSING")
ih = LY.inputs_hash(str(ep), "clock_reflect", 720, 1280); m = ep / "out/layers/clock_reflect"; m.mkdir(parents=True, exist_ok=True); (m / "manifest.json").write_text(json.dumps({"inputs_sha1": ih}))
ok("T3b status FRESH", LY.status(str(ep))["clock_reflect"] == "FRESH")
s = ep / "out/stills/f_00205.png"; d = bytearray(s.read_bytes()); d[-20] ^= 1; s.write_bytes(bytes(d)); ok("T3c status STALE after a base still changes", LY.status(str(ep))["clock_reflect"] == "STALE")
fj = json.loads(film.read_text()); fj["flights"][0]["fly"] = 9; film.write_text(json.dumps(fj)); sh([sys.executable, str(ROOT / "tools/film_plan.py"), "check", str(film)])
ok("T4 STALE-LOCK after the flight changes post-export", LY.status(str(ep))["clock_reflect"].startswith("STALE-LOCK"), LY.status(str(ep))["clock_reflect"])
glb = (ep / "out/lock/sets/platform.glb").read_bytes(); n = struct.unpack("<I", glb[12:16])[0]; js = json.loads(glb[20:20 + n]); names = {x.get("name", "").split(".")[0] for x in js["nodes"]}
ok("T5 named objects exist in the lock glb", all(o in names for o in json.loads((ep / "out/plan/layers_baked.json").read_text())["clock_reflect"]["objects"]))
print("GATE", "PASS" if all(res) else "FAIL"); sys.exit(0 if all(res) else 1)
