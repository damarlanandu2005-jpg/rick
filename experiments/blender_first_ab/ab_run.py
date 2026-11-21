#!/usr/bin/env python3
"""Blender-first A/B experiment runner (Colab, T4). Harness only: it calls the EXISTING tools; the only new Route-B code is route_b_render.py + route_b_compose.py.
  ab_run.py --blender <bin> [--gpu-backend opengl] [--out /content/ab_out] [--ranges 0-149,201-210,316-330] [--seed 20260522] [--only A|B|sheets]
Route A = tools/pipeline.py (three.js base + the existing Blender layer + JS effects), once per range in its own episode copy (same film.json, nothing modified).
Route B = Blender full frame (from_lock/look) + grade.py + render.mjs --overlay (captions / 2D fx), see CRITERIA.md.
Outputs: out/judge_pack/ (blind X/Y sheets, crops, videos; NO identities) and out/ANSWER_KEY_do_not_open_until_judged.json; timing + sharpness + effects matrix + code count in out/evidence/."""
import argparse, json, os, random, shutil, statistics, subprocess, sys, threading, time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parent; ROOT = HERE.parent.parent
ap = argparse.ArgumentParser(); ap.add_argument("--blender", required=True); ap.add_argument("--gpu-backend", default="opengl"); ap.add_argument("--out", default="/content/ab_out"); ap.add_argument("--ranges", default="0-149,201-210,316-330")
ap.add_argument("--seed", type=int, default=20260522); ap.add_argument("--only", default="all"); ap.add_argument("--renderer", default="cpu"); ap.add_argument("--res", default="720x1280"); a = ap.parse_args()
W, H = map(int, a.res.split("x")); OUT = Path(a.out); EV = OUT / "evidence"; JP = OUT / "judge_pack"; RANGES = [tuple(map(int, r.split("-"))) for r in a.ranges.split(",")]; RS = [("%d-%d" % r) for r in RANGES]
SRC = ROOT / "templates/film_western_example"; NODE = ROOT / "templates/threejs_film"; FPS = 30
for d in (OUT, EV, JP): d.mkdir(parents=True, exist_ok=True)
def sh(cmd, log, env=None, cwd=None):
    t = time.perf_counter(); p = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, errors="replace", env=env, cwd=cwd); Path(log).write_text(p.stdout + p.stderr); return p.returncode, time.perf_counter() - t, p
def stats(v): v = sorted(v); n = len(v); return {"n": n, "mean": round(sum(v) / n, 3), "median": round(statistics.median(v), 3), "p90": round(v[min(n - 1, int(np.ceil(0.9 * n)) - 1)], 3), "total": round(sum(v), 2), "min": v[0], "max": v[-1]}
def mkep(name):
    ep = OUT / name; shutil.rmtree(ep, ignore_errors=True); shutil.copytree(SRC, ep, ignore=shutil.ignore_patterns("out")); return ep
def lines(p): return sum(1 for l in Path(p).read_text().splitlines() if l.strip() and not l.strip().startswith("#"))
def rd(p): return np.asarray(Image.open(p).convert("RGB"))
T = json.load(open(EV / "timing.json")) if (EV / "timing.json").exists() else {}
def save_T(): json.dump(T, open(EV / "timing.json", "w"), indent=1)
# ------------------------------------------------------------------ Route A: the existing hybrid, one episode copy per range
def route_a():
    T["A"] = {}
    for r in RS:
        ep = mkep("epA_" + r); t = time.perf_counter()
        rc, secs, p = sh([sys.executable, ROOT / "tools/pipeline.py", ep, "--frames", r, "--blender", a.blender, "--gpu-backend", a.gpu_backend, "--renderer", a.renderer, "--accept-layers", "--res", a.res], EV / ("routeA_%s.log" % r))
        rep = json.load(open(ep / "out/pipeline/pipeline_report.json")) if (ep / "out/pipeline/pipeline_report.json").exists() else []
        n = int(r.split("-")[1]) - int(r.split("-")[0]) + 1; base = next((x for x in rep if x["stage"] == "2 base"), {}); lay = [x for x in rep if x["stage"] == "5 layers"]
        T["A"][r] = {"pipeline_rc": rc, "wall_s": round(secs, 1), "frames": n, "base_s": base.get("seconds"), "base_s_per_frame": round(base["seconds"] / n, 3) if base.get("seconds") else None, "base_status": base.get("status"),
                     "layers": [x for x in lay], "stages": rep, "final_exists": (ep / "out/final/frames").is_dir() and len(list((ep / "out/final/frames").glob("*.png"))) == n}
        save_T(); print("A", r, T["A"][r]["wall_s"], "s rc", rc, flush=True)
# ------------------------------------------------------------------ Route B: overlay (JS, 2D only) + Blender full frame (T4) + CPU grade/compose
def gpu_sampler(stop, rows):
    p = subprocess.Popen(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits", "-lms", "500"], stdout=subprocess.PIPE, text=True)
    while not stop.is_set():
        l = p.stdout.readline()
        if not l: break
        try: u, m, tot = [float(x) for x in l.split(",")]; rows.append((u, m, tot))
        except ValueError: pass
    p.terminate()
def route_b():
    ep = mkep("epB"); B = OUT / "routeB"; shutil.rmtree(B, ignore_errors=True); B.mkdir(); film = ep / "film.json"; T["B"] = {}
    rc, s, p = sh([sys.executable, ROOT / "tools/film_plan.py", "check", film], EV / "routeB_plan.log"); assert rc == 0, "plan check failed"
    rc, s, p = sh(["node", NODE / "render.mjs", film, "--export-lock"], EV / "routeB_lock.log"); assert rc == 0, "lock export failed"; T["B"]["lock_export_s"] = round(s, 1)
    sc = W / json.load(open(film)).get("size", [1080, 1920])[0]; T["B"]["overlay_s"] = {}
    for r in RS:
        rc, s, p = sh(["node", NODE / "render.mjs", film, "--overlay", "--range", r, "--scale", str(sc)], EV / ("routeB_overlay_%s.log" % r)); assert rc == 0, "overlay failed " + r; T["B"]["overlay_s"][r] = round(s, 1)
    rc, s, p = sh(["node", NODE / "render.mjs", film, "--visibility"], EV / "routeB_visibility.log"); shutil.copy(ep / "out/plan/visibility.json", EV / "visibility.json")
    stop = threading.Event(); rows = []; th = threading.Thread(target=gpu_sampler, args=(stop, rows), daemon=True); th.start(); idle = list(rows)
    t = time.perf_counter(); cmd = [a.blender, "-b", "--factory-startup", "--python-exit-code", "1"] + (["--gpu-backend", a.gpu_backend] if a.gpu_backend else []) + ["-P", HERE / "route_b_render.py", "--", ROOT, ep, B, W, H, ",".join(RS)]
    rc, s, p = sh(cmd, EV / "routeB_blender.log"); stop.set(); th.join(2); assert rc == 0, "Blender Route B failed: see routeB_blender.log"
    R = json.load(open(B / "routeB_timing.json")); allf = [x for r in RS for x in R["ranges"][r]]
    T["B"]["blender_process_wall_s"] = round(s, 1); T["B"]["cold_build_s"] = R["build_s"]; T["B"]["lock_motion_s"] = R["lock_motion_s"]; T["B"]["first_frame_s"] = allf[0]; T["B"]["per_frame"] = stats(allf); T["B"]["steady_per_frame_excl_first"] = stats(allf[1:]); T["B"]["per_range"] = {r: stats(R["ranges"][r]) for r in RS}
    T["B"]["cold_start_to_first_frame_s"] = round(R["build_s"] + R["lock_motion_s"] + allf[0], 2)
    if rows: u = [x[0] for x in rows]; m = [x[1] for x in rows]; T["B"]["gpu"] = {"samples": len(rows), "util_pct_mean": round(sum(u) / len(u), 1), "util_pct_p90": round(sorted(u)[int(.9 * len(u)) - 1], 1), "util_pct_max": max(u), "vram_mib_peak": max(m), "vram_mib_total": rows[0][2]}
    T["B"]["render_info"] = {k: R[k] for k in ("blender", "engine", "samples", "resolution", "preset", "settings", "materials", "gpu", "moved_nodes")}
    rc, s, p = sh([sys.executable, HERE / "route_b_compose.py", B / "raw", ep / "out/overlay", B / "final", R["preset"], ",".join(RS)], EV / "routeB_compose.log"); assert rc == 0, "compose failed: " + p.stderr[-400:]
    C = json.load(open(B / "final/compose_timing.json")); T["B"]["compose_cpu_s_per_frame"] = stats(C["frame_s"]); T["B"]["vignette"] = C["vignette"]; T["B"]["total_per_frame_blender_plus_compose_mean"] = round(T["B"]["per_frame"]["mean"] + T["B"]["compose_cpu_s_per_frame"]["mean"], 3)
    T["lock_sha1"] = {"B": __import__("hashlib").sha1((ep / "out/lock/lock.json").read_bytes()).hexdigest()}
    for r in RS:
        a0, b0 = map(int, r.split("-")); d = B / ("frames_" + r); d.mkdir(); [shutil.move(str(B / "final" / ("f_%05d.png" % f)), d / ("f_%05d.png" % f)) for f in range(a0, b0 + 1)]
    save_T(); print("B done", T["B"]["per_frame"], flush=True)
# ------------------------------------------------------------------ videos, blind sheets, sharpness, matrix, code count
def frame_dir(route, r): return (OUT / ("epA_" + r) / "out/final/frames") if route == "A" else (OUT / "routeB" / ("frames_" + r))
def mp4(route, r, dst):
    a0 = int(r.split("-")[0]); subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-start_number", str(a0), "-i", str(frame_dir(route, r) / "f_%05d.png"), "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", "-an", str(dst)], check=True)
def font(): return None
def sheets():
    rnd = random.Random(a.seed); key = {"seed": a.seed, "note": "X/Y per range: which route each label is. DO NOT OPEN until you have written your judgment.", "ranges": {}}
    vis = json.load(open(EV / "visibility.json"))["frames"] if (EV / "visibility.json").exists() else None
    for r in RS:
        a0, b0 = map(int, r.split("-")); n = b0 - a0 + 1; pick = sorted({a0 + int(round(i * (n - 1) / 5)) for i in range(6)}); order = ["A", "B"]; rnd.shuffle(order); lab = {"X": order[0], "Y": order[1]}; key["ranges"][r] = lab
        tw = 360; th = int(tw * H / W); pad = 6; sheet = Image.new("RGB", (2 * tw + 3 * pad, len(pick) * (th + pad) + pad + 22), (20, 20, 20)); d = ImageDraw.Draw(sheet); d.text((pad + tw // 2 - 4, 4), "X", fill=(255, 255, 255)); d.text((2 * pad + tw + tw // 2 - 4, 4), "Y", fill=(255, 255, 255))
        for i, f in enumerate(pick):
            for j, L in enumerate("XY"):
                sheet.paste(Image.open(frame_dir(lab[L], r) / ("f_%05d.png" % f)).convert("RGB").resize((tw, th), Image.LANCZOS), (pad + j * (tw + pad), 22 + pad + i * (th + pad)))
        sheet.save(JP / ("sheet_range_%s_blind.png" % r))
        # 1:1 crops of the first visible character per picked frame (the sharpness / filtering judgement), same X/Y labels
        if vis:
            crops = []
            for f in pick:
                v = vis[f]; who = next((k for k, x in v.items() if x and "h" in x), None)
                if not who: continue
                x = v[who]; hh = int(x["h"] * H); cx, cy = int(x["x"] * W), int(x["y"] * H); bw = max(160, int(hh * .8)); bh = max(160, hh); box = (max(0, cx - bw // 2), max(0, cy - bh // 2), min(W, cx + bw // 2), min(H, cy + bh // 2)); crops.append((f, who, box))
            if crops:
                cw = max(b[2] - b[0] for _, _, b in crops); ch = max(b[3] - b[1] for _, _, b in crops); S = Image.new("RGB", (2 * cw + 3 * pad, len(crops) * (ch + pad) + pad), (20, 20, 20))
                for i, (f, who, box) in enumerate(crops):
                    for j, L in enumerate("XY"): S.paste(Image.open(frame_dir(lab[L], r) / ("f_%05d.png" % f)).convert("RGB").crop(box), (pad + j * (cw + pad), pad + i * (ch + pad)))
                S.save(JP / ("crops_1to1_range_%s_blind.png" % r))
        for L in "XY": mp4(lab[L], r, JP / ("range_%s_%s.mp4" % (r, L)))
    json.dump(key, open(OUT / "ANSWER_KEY_do_not_open_until_judged.json", "w"), indent=1); (JP / "JUDGE_ME.md").write_text(JUDGE)
JUDGE = """# Blind judgement (two routes per range, labelled X and Y; identities are in a separate file you must not open yet)
Files: sheet_range_*_blind.png (overview), crops_1to1_range_*_blind.png (1:1 character crops), range_*_X.mp4 / range_*_Y.mp4. Watch the videos at full size, not only the sheets.
For EACH range and EACH item write: X better / Y better / same / not comparable. Judge art direction only; never a pixel metric.
1. Character presentation: characters not unintentionally blurred, outline crisp (use the 1:1 crops).
2. Camera, framing, composition.
3. Lighting quality and intentional lighting direction.
4. Materials and important highlights.
5. Depth-of-field behaviour (characters crisp, far set soft).
6. Motion and flight readability (the coin, the chase).
7. The 2D effects Ricks expects (glints, flashes, captions).
8. The overall finished coded-frame look.
Then: which range-by-range overall would you ship as a YouTube Short? Write it down BEFORE opening ANSWER_KEY_do_not_open_until_judged.json.
"""
def lap(g): return np.abs(4 * g[1:-1, 1:-1] - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:])
def sharpness():
    """Character-region sharpness, B vs A, same frame, same box (visibility.json projection). Metric = mean-square Laplacian of luminance + mean gradient magnitude. Evidence for the card-filtering question; the judgement is still the 1:1 crops."""
    vis = json.load(open(EV / "visibility.json"))["frames"]; out = {"metric": "var(Laplacian) and mean |gradient| of luminance inside the character box; ratio = B/A", "flag_if_ratio_below": 0.85, "ranges": {}}
    for r in RS:
        a0, b0 = map(int, r.split("-")); per = {}
        for f in range(a0, b0 + 1, max(1, (b0 - a0) // 14)):
            for who, x in vis[f].items():
                if not x or "h" not in x: continue
                hh = int(x["h"] * H); cx, cy = int(x["x"] * W), int(x["y"] * H); bw, bh = max(80, int(hh * .6)), max(120, hh); x0, x1, y0, y1 = max(1, cx - bw // 2), min(W - 1, cx + bw // 2), max(1, cy - bh // 2), min(H - 1, cy + bh // 2)
                if x1 - x0 < 40 or y1 - y0 < 40: continue
                m = {}
                for route in "AB":
                    g = rd(frame_dir(route, r) / ("f_%05d.png" % f)).astype(np.float32) @ np.array([.2126, .7152, .0722], np.float32); c = g[y0:y1, x0:x1]; gy, gx = np.gradient(c); m[route] = (float(lap(c).var()), float(np.hypot(gx, gy).mean()))
                if m["A"][0] > 1e-6: per.setdefault(who, []).append({"f": f, "lap_ratio": round(m["B"][0] / m["A"][0], 3), "grad_ratio": round(m["B"][1] / max(1e-6, m["A"][1]), 3)})
        out["ranges"][r] = {who: {"samples": len(v), "median_lap_ratio": round(statistics.median(x["lap_ratio"] for x in v), 3), "median_grad_ratio": round(statistics.median(x["grad_ratio"] for x in v), 3), "frac_below_flag": round(sum(x["lap_ratio"] < .85 for x in v) / len(v), 2), "rows": v} for who, v in per.items()}
    json.dump(out, open(EV / "card_sharpness.json", "w"), indent=1); return out
MATRIX = [  # (effect, owner in A per source, owner in B per source, what to look for)  - code facts from reading film.js / render.mjs / look.py / grade.py; the OBSERVED column is for the judge
 ("bloom", "three.js post (film.js bloom pass) + in-scene lamp/sun bloom sprites", "Blender EEVEE/look + grade.py CPU bloom (threshold 0.8)", "highlights glow, not clipped haze"),
 ("dust motes", "three.js post (look_dust, 520 particles by day)", "NOT in Blender or overlay (expected absent)", "motes present/absent in a still-camera moment"),
 ("vignette", "three.js post (~0.7)", "grade.py vignette fitted once per range (never per frame)", "edge darkening, no flicker across the range"),
 ("depth of field", "three.js post: far set + near-lens soft, characters always crisp", "Blender camera DOF f/5.6 focused on the subject card", "non-subject characters: crisp (A) vs blurred (B)?"),
 ("lens glints", "JS overlay layer (lens glints)", "JS overlay layer (render.mjs --overlay), same code", "identical in both unless composited differently"),
 ("flashes / 2D fx / bolts", "JS drawFx in overlay()", "JS overlay layer, same code", "position and timing identical; edge quality over the graded picture"),
 ("captions", "JS overlay()", "JS overlay layer, laid over AFTER the grade", "legibility, no colour shift by the grade"),
 ("held props", "three.js props", "Blender props (lock set glb, library materials by tag)", "attached to the hand? occlusion by the card?"),
 ("reflections", "three.js env + Blender lamp_reflect layer (201-210 only)", "Blender EEVEE screen-space raytracing", "glass / lamp glints, in-focus objects only"),
 ("shadows", "three.js shadow maps", "EEVEE shadows (PRESET sun, not the lock's sun)", "contact shadows under characters; direction vs the base"),
 ("character cards (sharpness)", "three.js plane, sprite filtering", "Blender plane, Cubic interpolation + film filter 2.2 px", "1:1 crops: edge softness, linework, halos"),
 ("materials", "three.js set materials", "materials.py library by mat: tag (unknown -> matte)", "wood / dirt / metal read as the same objects?"),
 ("sky / haze / time-of-day", "three.js sky + fog", "look.apply_look preset 'day' (sky, key/fill sun, haze)", "colour temperature, horizon"),
 ("motion blur", "none", "OFF (Route B run with motion_blur=False: characters never blurred)", "—"),
 ("flight (coin) 316-330", "flights.js", "lock_motion.apply on the set node, same baked flight", "same arc, same frames, readable"),
]
def matrix():
    L = ["# Effect matrix (separate from the A/B verdict)", "", "Columns 2-3 are code facts read from the source (film.js, render.mjs, look.py, grade.py, from_lock.py). Column 5 is for the human judge, filled in after the blind judgement. Nothing here is scored by a pixel metric.", "", "| effect | owner in Route A | owner in Route B | look for | observed (judge) |", "|---|---|---|---|---|"]
    L += ["| %s | %s | %s | %s |  |" % x for x in MATRIX]; (EV / "effects_matrix.md").write_text("\n".join(L) + "\n")
def codecount():
    new = ["experiments/blender_first_ab/route_b_render.py", "experiments/blender_first_ab/route_b_compose.py"]; harness = ["experiments/blender_first_ab/ab_run.py"]
    reused = ["templates/blender_look/from_lock.py", "templates/blender_look/look.py", "templates/blender_look/grade.py", "templates/blender_look/render.py", "templates/blender_look/materials.py", "templates/blender_look/lock_motion.py", "templates/threejs_film/render.mjs"]
    d = {"NEW Route-B code (counted; non-blank, non-comment lines)": {f: lines(ROOT / f) for f in new}, "harness shared by both routes (reported, not Route-B)": {f: lines(ROOT / f) for f in harness}, "existing reused, NOT counted": {f: lines(ROOT / f) for f in reused}}
    d["new_route_b_total"] = sum(d["NEW Route-B code (counted; non-blank, non-comment lines)"].values()); json.dump(d, open(EV / "code_count.json", "w"), indent=1); return d
if a.only in ("all", "A"): route_a()
if a.only in ("all", "B"): route_b()
if a.only in ("all", "sheets"):
    T = json.load(open(EV / "timing.json")); a_lock = {}
    for r in RS: p = OUT / ("epA_" + r) / "out/lock/lock.json"; a_lock[r] = __import__("hashlib").sha1(p.read_bytes()).hexdigest() if p.exists() else None
    T.setdefault("lock_sha1", {})["A"] = a_lock; save_T(); matrix(); cc = codecount(); sh_ = sharpness(); sheets()
    print("new Route-B code lines:", cc["new_route_b_total"]); print("sharpness (median Laplacian ratio B/A):", {r: {w: v["median_lap_ratio"] for w, v in d.items()} for r, d in sh_["ranges"].items()})
    print("JUDGE the sheets in", JP, "BEFORE opening", OUT / "ANSWER_KEY_do_not_open_until_judged.json")
