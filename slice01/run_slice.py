#!/usr/bin/env python3
"""slice01/run_slice.py  --  the ONE entry point for the vertical-slice test.

    python3 slice01/run_slice.py --blender /path/to/blender [--gpu-backend opengl] [--out slice01/out]

Steps: preflight -> cards (Node, existing Ricks puppet rig) -> Blender (casino scene + card, low-cost EEVEE preview)
       -> ffmpeg preview + contact sheet -> PASS/FAIL report.   Add --no-render to stop before any rendering.
It only connects existing pieces; it never does a final-quality render.
"""
import argparse, json, os, re, shutil, struct, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent; ROOT = HERE.parent
NEED = ["templates/motion_styles/rig.mjs", "templates/motion_styles/moves/emo_think.mjs", "templates/motion_styles/moves/emo_happy.mjs",
        "templates/motion_styles/moves/emo_scared.mjs", "templates/vector2d_characters/code/char2d.mjs", "templates/vector2d_characters/code/bodies.mjs",
        "templates/blender_look/from_lock.py", "templates/blender_look/materials.py", "templates/blender_look/look.py", "templates/blender_look/render.py",
        "slice01/make_cards.mjs", "slice01/blender_slice.py", "slice01/config.json"]

def node_env():
    env = os.environ.copy()
    if Path("/opt/npm-tools/node_modules").is_dir(): env.setdefault("NODE_PATH", "/opt/npm-tools/node_modules")   # the global playwright of some sandboxes
    return env

def sh(cmd, **kw): return subprocess.run(cmd, capture_output=True, text=True, **kw)

def preflight(a):
    errs = []
    for f in NEED:
        if not (ROOT / f).is_file(): errs.append("missing repo file: %s  (is this the ricks-2d-core branch?)" % f)
    if not Path(a.blend).is_file(): errs.append("casino blend not found: %s" % a.blend)
    node = shutil.which("node")
    if not node: errs.append("node not found. Install Node 18+ (Colab: see the notebook's Node cell).")
    else:
        v = sh([node, "--version"]).stdout.strip()
        try:
            if int(v.lstrip("v").split(".")[0]) < 18: errs.append("node %s is too old; need 18+" % v)
        except ValueError: pass
        r = sh([node, "-e", "require('playwright')"], cwd=str(HERE), env=node_env())
        if r.returncode != 0:
            if a.install_node_deps:
                print("installing playwright (npm install + chromium) ...")
                for c in (["npm", "install", "--no-audit", "--no-fund"], ["npx", "playwright", "install", "--with-deps", "chromium"]):
                    rr = subprocess.run(c, cwd=str(HERE))
                    if rr.returncode != 0: errs.append("failed: %s" % " ".join(c))
            else: errs.append("playwright not resolvable from slice01/. Run: cd slice01 && npm install && npx playwright install --with-deps chromium   (or pass --install-node-deps)")
    if not shutil.which("ffmpeg"): errs.append("ffmpeg not found on PATH")
    if not a.no_blender_check:
        b = Path(a.blender) if a.blender else None
        if not b or not (b.is_file() and os.access(b, os.X_OK)): errs.append("blender binary not found/executable: %s (use --blender)" % a.blender)
    return errs

def png_info(p):
    with open(p, "rb") as f: h = f.read(26)
    if h[:8] != b"\x89PNG\r\n\x1a\n": return None
    w, hh = struct.unpack(">II", h[16:24]); return w, hh, h[25]      # colour type 6 = RGBA

def validate_cards(lock):
    d = Path(lock) / "cards" / "hero"; errs = []; ip = d / "index.json"
    if not ip.is_file(): return ["no index.json in %s" % d], {}
    I = json.loads(ip.read_text())
    for k in ("metres_per_px", "px", "ground_px", "runs", "images", "figure_px"):
        if k not in I: errs.append("index.json lacks '%s'" % k)
    if errs: return errs, I
    n = I["images"]; pngs = sorted(d.glob("s*.png"))
    if len(pngs) != n: errs.append("index says %d drawings, %d PNGs on disk" % (n, len(pngs)))
    for i in range(1, n + 1):
        if not (d / ("s%04d.png" % i)).is_file(): errs.append("missing s%04d.png (the Blender sequence needs consecutive numbers)" % i); break
    bad = 0
    for p in pngs[:: max(1, n // 25)]:
        pi = png_info(p)
        if pi is None or pi[2] != 6 or [pi[0], pi[1]] != I["px"]: bad += 1
    if bad: errs.append("%d sampled PNGs are not RGBA %dx%d" % (bad, *I["px"]))
    runs = sorted(I["runs"], key=lambda r: r["f0"]); exp = 1
    for r in runs:
        if r["f0"] != exp: errs.append("runs leave a gap/overlap at frame %d" % exp); break
        if not 1 <= r["img"] <= n: errs.append("run image %s out of range 1..%d" % (r["img"], n)); break
        exp = r["f1"] + 1
    I["_frames"] = exp - 1
    return errs, I

def stream(cmd, log, env=None, every=10):
    print("[run]", " ".join(str(c) for c in cmd), flush=True); n = noise = 0; lines = []
    p = subprocess.Popen([str(c) for c in cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace", bufsize=1, env=env)
    with open(log, "w") as lf:
        for line in p.stdout:
            lf.write(line); lines.append(line.rstrip("\n"))
            if "EGL Error" in line: noise += 1; continue
            if line.startswith("FRAME"):
                n += 1
                if n % every == 1: print("  " + line.rstrip(), flush=True)
            elif re.search(r"SLICE_|GL_INFO|Traceback|Error|error:", line): print(line.rstrip(), flush=True)
    return p.wait(), lines, noise

def check(rows, name, ok, detail=""): rows.append((name, bool(ok), detail)); print("  [%s] %s %s" % ("PASS" if ok else "FAIL", name, detail), flush=True)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--blender", default=os.environ.get("BLENDER") or shutil.which("blender")); ap.add_argument("--blend", default=str(HERE / "assets" / "casino_eevee.blend"))
    ap.add_argument("--out", default=str(HERE / "out")); ap.add_argument("--config", default=str(HERE / "config.json")); ap.add_argument("--gpu-backend", default=None)
    ap.add_argument("--stride", type=int, default=0); ap.add_argument("--res-pct", type=int, default=0); ap.add_argument("--samples", type=int, default=0)
    ap.add_argument("--resume", action="store_true", help="keep already rendered frames"); ap.add_argument("--allow-software", action="store_true")
    ap.add_argument("--no-render", action="store_true", help="build the scene and stop (no rendering)"); ap.add_argument("--cards-only", action="store_true")
    ap.add_argument("--install-node-deps", action="store_true"); ap.add_argument("--no-blender-check", action="store_true")
    a = ap.parse_args(); out = Path(a.out); out.mkdir(parents=True, exist_ok=True); lock = out / "lock"; rows = []; t_all = time.time()
    print("== slice01 preflight"); errs = preflight(a)
    if a.cards_only: errs = [e for e in errs if "blender" not in e.lower()]
    if errs: print("\nPREFLIGHT FAILED:"); [print("  - " + e) for e in errs]; return 2
    print("  ok")

    print("== 1. cards (existing Ricks rig -> transparent PNG sequence)")
    if not a.resume or not (lock / "cards" / "hero" / "index.json").is_file():
        rc, lines, _ = stream(["node", HERE / "make_cards.mjs", a.config, lock], out / "cards.log", env=node_env())
        if rc != 0: print("CARDS FAILED. last lines:"); [print("  " + l) for l in lines[-8:]]; return 3
    e, I = validate_cards(lock); check(rows, "cards valid (RGBA PNGs, consecutive, no frame gaps)", not e, "; ".join(e))
    cr = json.loads((lock / "cards_report.json").read_text()) if (lock / "cards_report.json").is_file() else {}
    check(rows, "cards cover the full timeline", I.get("_frames") == cr.get("frames"), "%s frames, %s distinct drawings, card %s" % (cr.get("frames"), cr.get("distinct_drawings"), cr.get("card_px")))
    if e or a.cards_only: write(rows, out, cr, {}, t_all); return 0 if not e else 3

    print("== 2. Blender (casino scene + card, low-cost EEVEE preview)")
    cmd = [a.blender, "-b", "--factory-startup", "--python-exit-code", "1"] + (["--gpu-backend", a.gpu_backend] if a.gpu_backend else []) + \
          ["-P", HERE / "blender_slice.py", "--", "--repo", ROOT, "--blend", a.blend, "--lock", lock, "--out", out, "--config", a.config]
    for k, v in (("--stride", a.stride), ("--res-pct", a.res_pct), ("--samples", a.samples)):
        if v: cmd += [k, v]
    cmd += [x for x, f in (("--resume", a.resume), ("--allow-software", a.allow_software), ("--no-render", a.no_render)) if f]
    rc, lines, noise = stream(cmd, out / "blender.log")
    sl = [l for l in lines if l.startswith("SLICE_ERROR")]
    rp = out / "slice_report.json"; R = json.loads(rp.read_text()) if rp.is_file() else {}
    check(rows, "Blender ran without error", rc == 0 and not sl, (sl[0] if sl else "exit %s, EGL noise lines hidden: %d" % (rc, noise)))
    if rc != 0 or sl or not R: print("\nSee %s (last 15 lines):" % (out / "blender.log")); [print("  " + l) for l in lines[-15:]]; write(rows, out, cr, R, t_all); return 4
    cc = R.get("casino_character", {}); check(rows, "casino 3D character found and hidden", cc.get("objects", 0) > 0, "%s objects, height %.2f m, card feet %s" % (cc.get("objects"), cc.get("height_m", 0), [round(x, 2) for x in cc.get("card_feet", [])]))
    check(rows, "card built from existing from_lock.card()", bool(R.get("card")), json.dumps(R.get("card", {})))
    check(rows, "casino .blend untouched", R.get("casino_blend_unchanged", True) is not False)
    if a.no_render: write(rows, out, cr, R, t_all); print("\n--no-render: scene saved to %s" % (out / "slice01_scene.blend")); return 0

    pv = R.get("preview", {}); tm = R.get("timing", {})
    check(rows, "GPU (not software)", R.get("gl_verdict") in ("NVIDIA_GPU", "OTHER_GPU") or a.allow_software, "%s | %s" % (R.get("gl_verdict"), (R.get("gl") or {}).get("renderer")))
    check(rows, "all planned frames rendered", R.get("frames_on_disk") == pv.get("frames_planned"), "%s of %s" % (R.get("frames_on_disk"), pv.get("frames_planned")))

    print("== 3. ffmpeg preview + contact sheet")
    fr = out / "frames"; mp4 = out / "preview.mp4"; ofps = pv.get("output_fps", 15)
    r = sh(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(ofps), "-pattern_type", "glob", "-i", str(fr / "f_*.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", str(mp4)])
    check(rows, "preview.mp4 encoded", r.returncode == 0 and mp4.is_file() and mp4.stat().st_size > 0, r.stderr.strip()[-200:])
    nf = R.get("frames_on_disk", 0) or 1
    sh(["ffmpeg", "-y", "-loglevel", "error", "-pattern_type", "glob", "-i", str(fr / "f_*.png"), "-vf", "select='not(mod(n,%d))',scale=240:-1,tile=6x2" % max(1, nf // 12), "-frames:v", "1", str(out / "contact_sheet.jpg")])
    write(rows, out, cr, R, t_all); return 0 if all(ok for _, ok, _ in rows) else 5

def write(rows, out, cr, R, t_all):
    tm = R.get("timing", {}); pv = R.get("preview", {}); L = ["# slice01 report", "", "| check | result | detail |", "|---|---|---|"]
    L += ["| %s | %s | %s |" % (n, "PASS" if ok else "**FAIL**", d.replace("|", "/")) for n, ok, d in rows]
    if tm.get("mean_excl_first_s"):
        m = tm["mean_excl_first_s"]; px = (pv.get("px") or [360, 640]); ratio = (1080 * 1920) / (px[0] * px[1]); n12 = int(12 * 30)
        L += ["", "## Timing (measured on this machine)", "- preview: %s px, %s samples, stride %s -> %s frames; mean %.2fs/frame (excl. first), median %.2fs, p90 %.2fs, first %.2fs, wall %.0fs" % (pv.get("px"), pv.get("samples"), pv.get("stride"), tm.get("frames_rendered"), m, tm.get("median_s"), tm.get("p90_s"), tm.get("first_frame_s"), tm.get("wall_s")),
              "- ESTIMATE ONLY (not measured): the same 12 s at every frame (stride 1) = %.0f min at preview settings; at 1080x1920 the pixel count is x%.1f, so roughly %.0f min if cost scaled with pixels (samples and volumetrics would change it)." % (n12 * m / 60, ratio, n12 * m * ratio / 60)]
    if R.get("warnings"): L += ["", "## Warnings"] + ["- " + w for w in R["warnings"]]
    L += ["", "Total wall time of this run: %.0fs. Output folder: %s" % (time.time() - t_all, out)]
    (out / "slice_report.md").write_text("\n".join(L)); print("\n" + "\n".join(L))

if __name__ == "__main__": sys.exit(main())
