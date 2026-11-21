#!/usr/bin/env python3
"""Phase 4 gate (CPU only): tools/qa_hybrid.py on real three.js frames + real lock + real flight, with a SYNTHETIC layer (a mechanism test: real layers are gated in Phase 3).
  python3 phase4/test_qa.py [workdir]
Positive: Q1 flight range 316-330 -> QA PASS.  Q2 layer range 201-210 (synthetic named-mask layer) -> QA PASS.
Negative (each must be CAUGHT): N1 a pixel outside the mask changed in a final frame, N2 a layer PNG changed after assembly, N3 a base still changed after assembly, N4 the flight changed after the lock export,
N5 final.mp4 replaced by a base-only encode (video is not the composite), N6 a blank base frame."""
import json, shutil, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT / "tools")); import layers as LY, final_video as FV
W = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/p4"); ep = W / "ep"; res = []
def ok(n, c, m=""): res.append(bool(c)); print("PASS" if c else "FAIL", n, m)
def sh(c): return subprocess.run(c, capture_output=True, text=True)
def qa(): p = sh([sys.executable, str(ROOT / "tools/qa_hybrid.py"), str(ep)]); return p.returncode, p.stdout
def failed(out): return [l for l in out.splitlines() if l.startswith("- **FAIL**")]
shutil.rmtree(W, ignore_errors=True); shutil.copytree(ROOT / "templates/film_flight_example", ep, ignore=shutil.ignore_patterns("out")); film = ep / "film.json"; node = ROOT / "templates/threejs_film/render.mjs"
sh([sys.executable, str(ROOT / "tools/film_plan.py"), "check", str(film)])
fr = list(range(201, 211)) + list(range(316, 331)); sh(["node", str(node), str(film), "--frames", ",".join(map(str, fr)), "--scale", "0.666667", "--no-captions"]); sh(["node", str(node), str(film), "--export-lock"])
# synthetic layer on the clock: alpha = soft ellipse over the clock post region, idmask = its footprint
S = LY.spec_of(ep, "clock_reflect"); od = ep / "out/layers/clock_reflect"; od.mkdir(parents=True, exist_ok=True)
yy, xx = np.mgrid[0:1280, 0:720]; ell = (((xx - 520) / 90.0) ** 2 + ((yy - 640) / 260.0) ** 2) < 1
for f in range(201, 211):
    L = np.zeros((1280, 720, 4), np.uint8); L[ell, 0] = 40; L[ell, 1] = 40; L[ell, 2] = 40; L[ell, 3] = 255; Image.fromarray(L).save(od / ("layer_%05d.png" % f))
    I = np.zeros((1280, 720, 4), np.uint8); I[ell] = 255; Image.fromarray(I).save(od / ("idmask_%05d.png" % f))
ih = LY.inputs_hash(ep, "clock_reflect", 720, 1280); (od / "manifest.json").write_text(json.dumps({"inputs_sha1": ih})); (od / "layer_report.json").write_text(json.dumps({"PASS": True, "gates": {"A synthetic": True}}))
# Q1 flight range
FV.assemble(ep, 316, 330); rc, out = qa(); ok("Q1 flight range QA PASS", rc == 0, "; ".join(failed(out)))
ok("Q1 flight gates actually ran (not skipped)", "flight gates (registration" in out and "- **PASS** 2 THREEJS | flight gates" in out)
# Q2 layer range
FV.assemble(ep, 201, 210); rc, out = qa(); ok("Q2 layer range QA PASS", rc == 0, "; ".join(failed(out))); good = {p.name: p.read_bytes() for p in (ep / "out/final").glob("*.mp4")}
# N1 outside-mask pixel
fp = ep / "out/final/frames/f_00205.png"; keep = fp.read_bytes(); im = np.asarray(Image.open(fp)).copy(); im[10, 10] ^= 8; Image.fromarray(im).save(fp); rc, out = qa(); ok("N1 changed pixel outside the mask is caught", rc == 1 and any("outside" in l or "recomputed" in l for l in failed(out))); fp.write_bytes(keep)
# N2 layer png changed after assembly
lp = od / "layer_00204.png"; keep = lp.read_bytes(); L = np.asarray(Image.open(lp)).copy(); L[640, 520, 0] = 200; Image.fromarray(L).save(lp); rc, out = qa(); ok("N2 layer PNG changed after assembly is caught", rc == 1 and any("changed since assembly" in l or "FRESH" in l for l in failed(out))); lp.write_bytes(keep)
# N3 base still changed
sp = ep / "out/stills/f_00203.png"; keep = sp.read_bytes(); b = bytearray(keep); b[-30] ^= 1; sp.write_bytes(bytes(b)); rc, out = qa(); ok("N3 base still changed after assembly is caught", rc == 1 and bool(failed(out))); sp.write_bytes(keep)
# N5 video is not the composite
tmp = W / "base_only"; tmp.mkdir()
for f in range(201, 211): shutil.copy(ep / "out/stills" / ("f_%05d.png" % f), tmp / ("f_%05d.png" % f))
sh(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "30", "-start_number", "201", "-i", str(tmp / "f_%05d.png"), "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-an", str(ep / "out/final/final.mp4")])
rc, out = qa(); ok("N5 video that is not the composite is caught (PSNR)", rc == 1 and any("PSNR" in l for l in failed(out)), "; ".join(failed(out))[:160]); (ep / "out/final/final.mp4").write_bytes(good["final.mp4"])
# N6 blank base
Image.fromarray(np.zeros((1280, 720, 3), np.uint8)).save(ep / "out/stills/f_00207.png"); rc, out = qa(); ok("N6 blank base frame is caught", rc == 1 and any("blank" in l for l in failed(out))); sp = ep / "out/stills/f_00207.png"
# N4 flight changed after the lock export
sp.write_bytes(keep) if False else None
fj = json.loads(film.read_text()); fj["flights"][0]["fly"] = 9; film.write_text(json.dumps(fj)); sh([sys.executable, str(ROOT / "tools/film_plan.py"), "check", str(film)]); rc, out = qa(); ok("N4 flight changed after the lock export is caught", rc == 1 and any("lock fresh" in l for l in failed(out)))
print("GATE", "PASS" if all(res) else "FAIL"); sys.exit(0 if all(res) else 1)
