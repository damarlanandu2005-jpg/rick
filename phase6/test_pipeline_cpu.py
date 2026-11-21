#!/usr/bin/env python3
"""Phase 6 CPU gate: tools/pipeline.py (no Blender).  python3 phase6/test_pipeline_cpu.py [workdir]
P1 first run: every scripted stage PASS, final.mp4 + QA PASS, creative stage reported as INPUT   P2 second run: base and lock are CACHE hits (< 10 s total)
P3 an input that changes (film.json) invalidates the base cache: the base is re-rendered (not CACHE)   P4 a failing stage STOPS the run: a broken layer spec fails stage 1, nothing later is run, exit code != 0
P5 a layer without review.json is omitted from the final (creative decision is data, not a default)"""
import json, shutil, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent; W = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/p6_cpu"); ep = W / "ep"; res = []
def ok(n, c, m=""): res.append(bool(c)); print("PASS" if c else "FAIL", n, m)
def pipe(): t = time.perf_counter(); p = subprocess.run([sys.executable, str(ROOT / "tools/pipeline.py"), str(ep), "--frames", "0-9", "--renderer", "cpu"], capture_output=True, text=True); return p, time.perf_counter() - t
def rep(): return {r["stage"]: r for r in json.loads((ep / "out/pipeline/pipeline_report.json").read_text())}
shutil.rmtree(W, ignore_errors=True); shutil.copytree(ROOT / "templates/film_western_example", ep, ignore=shutil.ignore_patterns("out"))
p, t = pipe(); r = rep(); ok("P1 first run PASS end to end", p.returncode == 0 and r["8 qa"]["status"] == "PASS" and (ep / "out/final/final.mp4").exists() and r["C1-C3"]["kind"] == "creative" and r["C1-C3"]["status"] == "INPUT", "%.0fs" % t)
ok("P1 scripted/creative are labelled", {x["kind"] for x in r.values()} == {"creative", "scripted"})
p, t = pipe(); r = rep(); ok("P2 second run: base and lock are cache hits", r["2 base"]["status"] == "CACHE" and r["3 lock"]["status"] == "CACHE" and t < 10, "%.1fs" % t)
f = json.loads((ep / "film.json").read_text()); f["title"] += " (edited)"; (ep / "film.json").write_text(json.dumps(f)); p, t = pipe(); r = rep(); ok("P3 changed film.json invalidates the base cache", r["2 base"]["status"] == "PASS" and p.returncode == 0, "%.0fs" % t)
ok("P5 unreviewed layer omitted from the final", json.loads((ep / "out/final/final_manifest.json").read_text())["layers"] == {})
f = json.loads((ep / "film.json").read_text()); f["layers"][0]["objects"] = []; (ep / "film.json").write_text(json.dumps(f)); p, t = pipe(); r = rep()
ok("P4 a failing stage stops the run", p.returncode != 0 and r["1 plan"]["status"] == "FAIL" and "2 base" not in r and "8 qa" not in r, "stages run: %s" % list(r))
print("GATE", "PASS" if all(res) else "FAIL"); sys.exit(0 if all(res) else 1)
