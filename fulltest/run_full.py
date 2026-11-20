#!/usr/bin/env python3
"""fulltest/run_full.py -- the ONE entry point for the Pass A test (0-14 s of the reference, silent).
    python3 fulltest/run_full.py --blender /path/to/blender --gpu-backend opengl --out /content/full_out [--mode stills|preview|both] [--script fulltest/script_passA.json]
Steps: preflight -> cards (Node, existing Ricks puppet rig, existing cast outfits) -> Blender stills (one per shot, cheap) -> [preview frames] -> ffmpeg -> report.
Never a final-quality render. Failures print FULL_ERROR with the cause."""
import argparse, json, os, shutil, subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parent
NEED = ["templates/motion_styles/rig.mjs", "templates/motion_styles/moves/idle.mjs", "templates/motion_styles/moves/emo_angry.mjs", "templates/motion_styles/moves/emo_scared.mjs",
        "templates/vector2d_characters/code/sheets/sheet05.mjs", "templates/blender_look/from_lock.py", "templates/blender_look/materials.py", "templates/blender_look/look.py",
        "fulltest/make_cards_multi.mjs", "fulltest/post.py", "fulltest/moves/aim_gun.mjs", "templates/blender_look/grade.py", "fulltest/cast_western.mjs", "fulltest/street_kit.py", "fulltest/blender_full.py", "fulltest/script_passA.json"]
def fail(m): print("FULL_ERROR " + m); sys.exit(1)
def node_env():
    env = os.environ.copy(); pw = ROOT / "slice01" / "node_modules" / "playwright"
    if pw.is_dir(): env["PLAYWRIGHT_DIR"] = str(pw)
    elif Path("/opt/npm-tools/node_modules").is_dir(): env.setdefault("NODE_PATH", "/opt/npm-tools/node_modules")
    return env
def stream(cmd, log, env=None):
    print("[run] " + " ".join(map(str, cmd)), flush=True); lines = []
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace", bufsize=1, env=env)
    for l in p.stdout:
        lines.append(l)
        if any(k in l for k in ("FULL_", "STREET_STEP", "Error", "Traceback", "FRAME 1 ", "GL_INFO")) or l.startswith("  "): print(l.rstrip(), flush=True)
    rc = p.wait(); Path(log).write_text("".join(lines)); return rc, "".join(lines)
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--blender", required=True); ap.add_argument("--gpu-backend", default="opengl"); ap.add_argument("--out", default=str(HERE / "out"))
    ap.add_argument("--mode", choices=["stills", "preview", "both"], default="stills"); ap.add_argument("--script", default=str(HERE / "script_passA.json")); ap.add_argument("--stride", type=int, default=0); ap.add_argument("--res-pct", type=int, default=0)
    a = ap.parse_args(); T0 = time.time(); out = Path(a.out); out.mkdir(parents=True, exist_ok=True); lock = out / "lock"
    miss = [f for f in NEED if not (ROOT / f).is_file()]
    if miss: fail("missing repo files (is this the ricks-2d-core branch?): " + ", ".join(miss))
    for tool in ("node", "ffmpeg"):
        if not shutil.which(tool): fail("%s not found on PATH" % tool)
    if not os.access(a.blender, os.X_OK): fail("blender binary not executable: %s" % a.blender)
    rep = {"checks": []}; ck = lambda n, ok, d="": (rep["checks"].append((n, ok, d)), print("  [%s] %s %s" % ("PASS" if ok else "FAIL", n, d)))
    print("== 1. cards (existing Ricks rig + cast outfits -> PNG sequences)")
    rc, txt = stream(["node", str(HERE / "make_cards_multi.mjs"), a.script, str(lock)], out / "cards.log", node_env())
    if rc != 0: fail("card generation failed, see %s" % (out / "cards.log"))
    cr = json.loads((lock / "cards_report.json").read_text()); ck("cards generated for every character in the script", len(cr["cards"]) == len(json.loads(Path(a.script).read_text())["cast"]), json.dumps(cr["cards"]))
    modes = ["stills", "preview"] if a.mode == "both" else [a.mode]; R = {}
    for m in modes:
        print("== 2. Blender: %s" % m)
        cmd = [a.blender, "-b", "--factory-startup", "--python-exit-code", "1", "--gpu-backend", a.gpu_backend, "-P", str(HERE / "blender_full.py"), "--", "--repo", str(ROOT), "--lock", str(lock), "--script", a.script, "--out", str(out), "--mode", m]
        if a.stride: cmd += ["--stride", str(a.stride)]
        if a.res_pct: cmd += ["--res-pct", str(a.res_pct)]
        rc, txt = stream(cmd, out / ("blender_%s.log" % m)); ck("Blender %s ran without error" % m, rc == 0, "exit %s" % rc)
        if rc != 0: print("--- last log lines ---\n" + "".join(txt.splitlines(True)[-25:])); break
        R[m] = json.loads((out / ("full_report_%s.json" % m)).read_text())
        ck("GPU (not software)", R[m].get("gl_verdict") in ("NVIDIA_GPU", "GPU_OTHER"), str(R[m].get("gl_verdict")))
        ck("no decoration steps failed", not R[m]["warnings"], "; ".join(R[m]["warnings"])[:400])
    if "stills" in R:
        n = len(R["stills"].get("stills", [])); ck("one still per shot rendered", n == len(json.loads(Path(a.script).read_text())["shots"]), "%d stills" % n)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", "1", "-i", str(out / "stills" / "shot_%02d.png"), "-vf", "scale=240:-1,tile=6x2", "-frames:v", "1", str(out / "contact_sheet.jpg")])
        ck("contact sheet written", (out / "contact_sheet.jpg").is_file())
    if "preview" in R:
        fps = R["preview"]["timing"]["preview"]; fr = 30 / max(1, fps["stride"])
        enc = lambda src, dst: subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(fr), "-i", str(src), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "veryfast", str(dst)]).returncode
        ck("preview_raw.mp4 encoded (no dissolve, no grade)", enc(out / "frames" / "f_%04d.png", out / "preview_raw.mp4") == 0)
        pr = subprocess.run([sys.executable, str(HERE / "post.py"), "--script", a.script, "--frames", str(out / "frames"), "--out", str(out / "frames_post"), "--stride", str(fps["stride"])], capture_output=True, text=True)
        print(pr.stdout.strip(), pr.stderr.strip()[-500:]); ck("post (dissolves + existing Ricks grade)", pr.returncode == 0, pr.stdout.strip()[-200:])
        if pr.returncode == 0: ck("preview.mp4 encoded (silent)", enc(out / "frames_post" / "p_%04d.png", out / "preview.mp4") == 0 and (out / "preview.mp4").is_file())
        ck("all planned frames rendered", R["preview"]["frames_on_disk"] == len(range(1, R["preview"]["frames"] + 1, fps["stride"])), "%s of %s" % (R["preview"]["frames_on_disk"], len(range(1, R["preview"]["frames"] + 1, fps["stride"]))))
    lines = ["# fulltest Pass A report", "", "| check | result | detail |", "|---|---|---|"] + ["| %s | %s | %s |" % (n, "PASS" if ok else "FAIL", d) for n, ok, d in rep["checks"]]
    for m, r in R.items():
        t = r["timing"]; lines += ["", "## Timing (%s, measured)" % m, "- %d renders, first %.2fs, mean excl. first %.3fs, max %.2fs%s" % (t["frames_rendered"], t["first_s"] or 0, t["mean_excl_first_s"] or 0, t["max_s"] or 0, ", wall %ss" % r["wall_s"] if "wall_s" in r else ""), "- settings: %s" % json.dumps(t["preview"])]
        lines += ["- camera: " + json.dumps(r["camera"])] if m == "stills" else []
    lines += ["", "Total wall time: %.0fs. Output folder: %s" % (time.time() - T0, out)]; (out / "full_report.md").write_text("\n".join(lines)); print("\n" + "\n".join(lines))
    sys.exit(0 if all(ok for _, ok, _ in rep["checks"]) else 1)
main()
