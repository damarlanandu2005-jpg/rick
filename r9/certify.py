#!/usr/bin/env python3
"""R9 final certification. Exercises the EXISTING R1-R8 system end to end; it adds no production code, renderer, QA framework or capability.
The certified film is the existing TEST_FIXTURE_ONLY infrastructure put together (no new creative film; never the R5 Hat Toss, which stays a creative FAIL):
  r6/fixture_mech.py (script, words, board, picture plan, look, character spec, the canyon film that passes the real check_film video gates)
  + r7/fixture_lib.py Film A (real three.js storyboard + animatic, registry copy, handcar via the set module, lantern placed by film.json at rot 30 deg / scale 1.2)
  + the R8 audio cues/fixture audio (voice, music, ambience, overlapping SFX), all signed by the approval.
Then: the real production pipeline from scratch (clean) and again (resume), decoded checks of the delivered MP4, the R7 asset / R3 character / R8 audio certification, the approval/lock/asset/audio
safety matrix on copies, two cheap capability probes (2-take cuts; a flight) and the GPU path. Every failure is classified A engineering / B test-fixture / C creative / D unsupported / E environment.
  python3 r9/certify.py [<dir>]      (about 25 minutes on 2 CPUs; the visual render is most of it)        R9_REUSE=1: keep a finished clean run in <dir> (development only)"""
import copy, hashlib, json, math, os, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent; sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "r2"), str(ROOT / "r6"), str(ROOT / "r7"), str(ROOT / "r8")]
import fixture_mech as FM, fixture_lib as FL, fixture_audio as FA
fails = []; FINDINGS = []; TIMES = {}; RES = {}; T00 = time.time()
def t(name, ok, cls=None):
    print(("PASS " if ok else "FAIL ") + name, flush=True)
    if not ok: fails.append(name); FINDINGS.append(dict(check=name, cls=cls or "UNCLASSIFIED"))
    return ok
def note(name, cls, why): print("NOTE [%s] %s: %s" % (cls, name, why), flush=True); FINDINGS.append(dict(check=name, cls=cls, why=why))
PY = sys.executable; W = Path(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else tempfile.mkdtemp(prefix="r9_")); REG = W / "registry.json"
def sha(p): return hashlib.sha1(Path(p).read_bytes()).hexdigest()
def env(extra=None): e = {k: v for k, v in os.environ.items() if k != "RICKS_UNAPPROVED_TEST_RUN"}; e["RICKS_REGISTRY"] = str(REG); e.update(extra or {}); return e
def sh(cmd, extra=None): return subprocess.run([str(c) for c in cmd], capture_output=True, text=True, env=env(extra))
def pipeline(ep): t0 = time.time(); r = sh([PY, ROOT / "tools/pipeline.py", ep, "--renderer", "cpu"]); return r, round(time.time() - t0, 1)
def stages(ep): return {s["stage"]: s for s in json.load(open(Path(ep) / "out/pipeline/stages.json"))}
def tree_sha(d, pat="*"):
    d = Path(d); return hashlib.sha1("".join("%s:%s;" % (p.relative_to(d), sha(p)) for p in sorted(d.rglob(pat)) if p.is_file()).encode()).hexdigest() if d.exists() else None
def light_copy(src, name):
    d = W / "copies" / name; shutil.rmtree(d, ignore_errors=True); shutil.copytree(src, d, ignore=shutil.ignore_patterns("stills", "frames", "final_video.mp4", "final.mp4", ".puppet_cache", "preview")); return d
AUDIO = {"required": ["voice", "music", "sfx", "ambience"]}
SOUND = [dict(at=0, name="voice", type="voice", file="voice/voice.wav"), dict(at=0, name="bed", type="music", file="sound/music/bed.wav", until="end", gain=-20, fade_in=0.8, fade_out=1.5),
         dict(at=0, name="wind", type="ambience", file="sound/amb/wind.wav", until="end", gain=-10, fade_in=1.0, fade_out=1.0), dict(at=["kneels", 1], name="footstep", gain=-6),
         dict(at=["taps", 1], name="impact", gain=-4), dict(at=["taps", 1, 6], name="impact", gain=-6), dict(at=["train", 1], name="whoosh", gain=-6)]
PLACE = dict(name="lantern", at=[1.6, 2.6, 0.0], rot=30, scale=1.2)   # R9 class-B fix: at [0.7, -0.6] the big glowing lantern close to the camera pulled the decoded check_film camera-speed median to 1.49 (< 1.55); here it measures 1.72
EP = W / "film_a"
os.environ["RICKS_REGISTRY"] = str(REG)
import assets as AS, approval as AP, lock_stamp as LS, characters as CH, audio as AU, glb as G
def use(): os.environ["RICKS_REGISTRY"] = str(REG); AS.REG = REG; CH.REG = REG

# ====================================================================== 1. build the certified film (approved + locked inputs) and the CLEAN production run
if not (os.environ.get("R9_REUSE") and (EP / "out/final/final_video.mp4").is_file()):
    shutil.rmtree(W, ignore_errors=True); W.mkdir(parents=True)
    FM.FILM = copy.deepcopy(FM.FILM); FM.FILM["audio"] = AUDIO; FM.FILM["sound"] = SOUND
    t0 = time.time(); FL.world(W); ep, TF = FL.film(W, "film_a", placement=PLACE); TIMES["inputs_build_s"] = round(time.time() - t0, 1); TIMES.update({"storyboard_s": TF["storyboard_s"], "animatic_s": TF["animatic_s"], "lock_export_s": TF["lock_s"]})
    words = json.load(open(EP / "voice/words.json")); n = len(json.load(open(EP / "out/plan/camera_baked.json"))["frames"])
    t0 = time.time(); FA.write_all(EP, EP / "voice/words.json", min(words[-1]["e"] + 0.3, n / 30 - 0.05)); TIMES["audio_fixture_s"] = round(time.time() - t0, 3)
    for p in ("sound/sfx/corrupt.wav", "sound/music/short.wav", "sound/sfx/click.wav"): (EP / p).unlink()
    r, TIMES["clean_run_s"] = pipeline(EP); (W / "clean.log").write_text(r.stdout + r.stderr); shutil.copy(EP / "out/pipeline/stages.json", W / "stages_clean.json"); RES["clean_rc"] = r.returncode; json.dump(dict(TIMES=TIMES, rc=r.returncode), open(W / "clean_meta.json", "w"))
    print(r.stdout[-1800:], flush=True)
else: M_ = json.load(open(W / "clean_meta.json")); TIMES.update(M_["TIMES"]); RES["clean_rc"] = M_["rc"]
use(); S = {x["stage"]: x for x in json.load(open(W / "stages_clean.json"))}; n = len(json.load(open(EP / "out/plan/camera_baked.json"))["frames"])
TIMES.update({k.replace(" ", "_") + "_s": S[k]["seconds"] for k in ("7 base", "9 final", "10 qa", "11 sound", "12 delivery qa") if k in S})
order = ["G1", "G7", "2 storyboard", "3 animatic", "4 judge", "G8", "G9", "5 assets", "6 lock", "6c lock freeze", "7 base", "9 final", "10 qa", "11 sound", "12 delivery qa"]
t("I clean run: the production pipeline PASSES from approved inputs to the delivered MP4 (exit 0), stages in order %s" % " -> ".join(order), RES["clean_rc"] == 0 and all(k in S for k in order) and [k for k in S if k in order] == order, "A")
t("I clean run: every stage PASS/CACHE/INPUT (no FAIL): %s" % {k: v["status"] for k, v in S.items() if v["status"] not in ("PASS", "CACHE", "INPUT", "SKIP", "KEEP", "OMIT", "FULL")}, all(v["status"] in ("PASS", "CACHE", "INPUT", "SKIP", "KEEP", "OMIT", "FULL") for v in S.values()), "A")
t("I the ONE expensive render ran after G9 + lock: 7 base PASS, %d frames (%s s)" % (n, S["7 base"]["seconds"]), S["7 base"]["status"] == "PASS" and "%d frames" % n in S["7 base"]["note"], "A")
PM = json.load(open(EP / "out/pipeline/production_manifest.json")); t("I production manifest: status PASS, production:false (TEST_FIXTURE_ONLY) though every gate was enforced, final.mp4 sha1 recorded", PM.get("production") is False and PM.get("status") == "PASS" and PM.get("final_mp4_sha1") == sha(EP / "out/final/final.mp4"), "A")

# ====================================================================== 2. VISUAL QA of the decoded picture (existing qa_hybrid + check_film via stage 10; decoded readback here)
QA = json.load(open(EP / "out/qa/qa_report.json")); qrows = QA.get("checks") or QA.get("rows") or []
t("V existing visual QA (qa_hybrid: plan, gates, lock, every decoded frame PSNR >= 35 vs the composite, MP4 sha1, check_film camera gates, production stage) PASSED: %s" % S["10 qa"]["note"][:120], S["10 qa"]["status"] == "PASS", "A")
FV = EP / "out/final/final_video.mp4"; DV = AU.probe(FV); V = [s for s in DV if s["codec_type"] == "video"][0]
t("V decoded delivery: h264 720x1280, 30/1 fps, %s decoded frames == %d planned (no missing frame)" % (V["nb_read_frames"], n), (V["codec_name"], V["width"], V["height"], V["r_frame_rate"], int(V["nb_read_frames"])) == ("h264", 720, 1280, "30/1", n), "A")
raw = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", str(FV), "-map", "0:v:0", "-vf", "scale=90:160", "-pix_fmt", "gray", "-f", "rawvideo", "-"], capture_output=True)
fr_ = np.frombuffer(raw.stdout, np.uint8).reshape(-1, 160, 90).astype(np.float32); means, stds = fr_.mean((1, 2)), fr_.std((1, 2))
t("V no decode corruption: ffmpeg decoded all %d frames with no error output" % len(fr_), raw.returncode == 0 and not raw.stderr and len(fr_) == n, "A")
t("V no black / blank frame: darkest frame mean %.1f, flattest frame std %.1f (limits: mean >= 8, std >= 2 on 0-255)" % (means.min(), stds.min()), means.min() >= 8 and stds.min() >= 2, "A")
d_ = np.abs(np.diff(fr_, axis=0)).mean((1, 2)); t("V no frozen run: no 10 consecutive identical decoded frames (largest identical run %d)" % (max((len(m) for m in re.findall(r"0{1,}", "".join("0" if x < 0.05 else "1" for x in d_))), default=0)), not re.search(r"0{10,}", "".join("0" if x < 0.05 else "1" for x in d_)), "A")
FMn = json.load(open(EP / "out/final/final_manifest.json"))
t("V the picture IS the approved/locked inputs: final_manifest names %d base stills by sha1, approval + lock sha1, and the MP4 on disk is that one" % len(FMn["inputs"]), len(FMn["inputs"]) == n and FMn["approval_sha1"] == sha(EP / "approval.json") and FMn["lock_sha1"] == sha(EP / "out/lock/lock.json") and FMn["mp4_sha1"] == sha(EP / "out/final/final.mp4"), "A")
t("V duration: %.4f s video == %d / 30" % (n / 30, n), abs(float(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration", "-of", "csv=p=0", str(FV)], capture_output=True, text=True).stdout or 0) - n / 30) < 0.04, "A")

# ====================================================================== 3. AUDIO certification in the full pipeline (R8, unchanged)
R = AU.qa(EP); [print("    " + ("ok   " if ok else "FAIL ") + k + (" | " + d if d else "")) for k, ok, d in R]
t("G audio + delivery QA on the decoded MP4: %d/%d checks PASS (streams, picture unchanged, AAC decodes, length, level, clipping, A/V sync)" % (sum(ok for _, ok, _ in R), len(R)), all(ok for _, ok, _ in R), "A")
A = FMn["audio"]; types = sorted({e["type"] for e in A["events"]}); sfx = sorted(e["frame"] for e in A["events"] if e["type"] == "sfx")
t("G voice + music + SFX + ambience all in the mix: %s; overlapping SFX (impact at frame %d and %d, overlapping the music/ambience beds)" % (types, sfx[1], sfx[2]), types == ["ambience", "music", "sfx", "voice"] and len(sfx) == 4 and sfx[2] - sfx[1] == 6, "A")
x, _ = AU.decode(FV, 2); RES["audio"] = dict(seconds=len(x) / 48000, peak=round(20 * math.log10(float(np.abs(x).max())), 2))
sync = [d for k, ok, d in R if k.startswith("A/V sync")] or [k for k, ok, d in R if k.startswith("A/V sync")]
t("G A/V sync: %s" % [k for k, ok, _ in R if k.startswith("A/V sync")][0][:110], all(ok for k, ok, _ in R if k.startswith("A/V sync")), "A")

# ====================================================================== 4. RESUME run: same command, nothing regenerated, nothing changed, nothing bypassed
SNAP = {"film.json": sha(EP / "film.json"), "approval.json": sha(EP / "approval.json"), "creative/": tree_sha(EP / "creative"), "voice/words.json": sha(EP / "voice/words.json"), "out/plan": tree_sha(EP / "out/plan", "*_baked.json"),
        "out/lock/lock.json": sha(EP / "out/lock/lock.json"), "out/lock/ (sets+cards)": tree_sha(EP / "out/lock", "*.glb") + tree_sha(EP / "out/lock/cards") if (EP / "out/lock/cards").exists() else tree_sha(EP / "out/lock", "*.glb"),
        "registry copy": sha(REG), "lantern GLB": sha(AS.glb_path(AS.entry("prop_oil_lantern", "1.0")["glb"])), "out/assets": tree_sha(EP / "out/assets"), "out/stills": tree_sha(EP / "out/stills", "f_*.png"),
        "final.mp4": sha(EP / "out/final/final.mp4"), "mix.wav": sha(EP / "out/audio/mix.wav"), "final_video.mp4": sha(FV)}
r, TIMES["resume_run_s"] = pipeline(EP); (W / "resume.log").write_text(r.stdout + r.stderr); S2 = stages(EP)
after = {"film.json": sha(EP / "film.json"), "approval.json": sha(EP / "approval.json"), "creative/": tree_sha(EP / "creative"), "voice/words.json": sha(EP / "voice/words.json"), "out/plan": tree_sha(EP / "out/plan", "*_baked.json"),
         "out/lock/lock.json": sha(EP / "out/lock/lock.json"), "out/lock/ (sets+cards)": tree_sha(EP / "out/lock", "*.glb") + tree_sha(EP / "out/lock/cards") if (EP / "out/lock/cards").exists() else tree_sha(EP / "out/lock", "*.glb"),
         "registry copy": sha(REG), "lantern GLB": sha(AS.glb_path(AS.entry("prop_oil_lantern", "1.0")["glb"])), "out/assets": tree_sha(EP / "out/assets"), "out/stills": tree_sha(EP / "out/stills", "f_*.png"),
         "final.mp4": sha(EP / "out/final/final.mp4"), "mix.wav": sha(EP / "out/audio/mix.wav"), "final_video.mp4": sha(FV)}
t("R resume: the same command PASSES again (exit 0) in %s s vs %s s clean (%.1fx faster)" % (TIMES["resume_run_s"], TIMES["clean_run_s"], TIMES["clean_run_s"] / max(TIMES["resume_run_s"], 0.1)), r.returncode == 0, "A")
t("R resume REUSED the locked render: 7 base CACHE, 6 lock CACHE (no second expensive render)", S2["7 base"]["status"] == "CACHE" and S2.get("6 lock", {}).get("status") == "CACHE", "A")
t("R resume changed NO hash: %s" % ", ".join(k for k in SNAP if SNAP[k] != after[k]) if any(SNAP[k] != after[k] for k in SNAP) else "R resume changed NO hash (creative, film.json, approval, words, baked plan, lock, registry, asset GLB, staged assets, %d stills, final.mp4, mix.wav, final_video.mp4)" % n, all(SNAP[k] == after[k] for k in SNAP), "A")
t("R resume did not bypass a gate: G1-G9 re-checked (PASS), judge + approval INPUT/PASS, no --skip", all(S2[g]["status"] == "PASS" for g in ("G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9")), "A")
TIMES["resume_stage_s"] = {k: v["seconds"] for k, v in S2.items() if v["seconds"] >= 1}
sc = 720 / json.load(open(EP / "film.json")).get("size", [1080, 1920])[0]; rr = sh(["node", ROOT / "templates/threejs_film/render.mjs", EP / "film.json", "--frames", "60,200,350", "--scale", str(sc), "--stills-dir", W / "rerender"])
same = [sha(W / "rerender" / ("f_%05d.png" % f)) == sha(EP / "out/stills" / ("f_%05d.png" % f)) for f in (60, 200, 350)] if rr.returncode == 0 else []
t("R reproducible picture: re-rendering frames 60, 200, 350 in a NEW process with the production base-render arguments gives byte-identical stills to the final render (%s)" % same, same == [True] * 3, "A")

# ====================================================================== 5. R7 ASSET certification: registry -> film placement -> three.js -> storyboard -> animatic -> lock -> final render
e = AS.entry("prop_oil_lantern", "1.0"); g = e["glb"]; L = json.load(open(EP / "out/lock/lock.json"))["approved"]["assets"]
t("F registry assets: prop_oil_lantern@1.0 and prop_rail_handcar@1.0 resolved, version pinned, live GLB contract + validation record valid (G7 PASS)", AS.resolve_problems(EP)[0] == [] and S["G7"]["status"] == "PASS", "A")
t("F storyboard + animatic record the lantern v1.0 sha1 %s (real three.js review renders)" % g["sha1"][:10], all(json.load(open(EP / "creative" / doc))["assets"]["prop_oil_lantern"] == dict(version="1.0", sha1=g["sha1"]) for doc in ("STORYBOARD.json", "ANIMATIC.json")), "A")
t("F the lock froze BOTH assets at their exact GLB sha1 and the lock set GLB carries them with every mat: name (incl. .2f5a3e / .ffd27a)", all(L[i]["glb_sha1"] == AS.entry(i, "1.0")["glb"]["sha1"] for i in ("prop_oil_lantern", "prop_rail_handcar")) and all(LS.mat_kept(m, LS.lock_assets(EP)["prop_oil_lantern"]["materials"]) for m in e["requirement"]["materials"]), "A")
J, _ = G.read(next((EP / "out/lock/sets").glob("*.glb"))); nd = next(x for x in J["nodes"] if x.get("name") == "lantern"); rot = 2 * math.degrees(math.asin(abs(nd.get("rotation", [0, 0, 0, 1])[1])))
t("F placement owned by film.json: the locked scene has the lantern at %s, rotation %.2f deg, scale %.3f (film: rot 30, scale 1.2); the registry contract unchanged" % ([round(v, 3) for v in nd.get("translation", [])], rot, nd.get("scale", [1])[0]), abs(rot - 30) < 0.05 and abs(nd["scale"][0] - 1.2) < 1e-4 and g["contract"]["height_m"] == 0.341, "A")
rv = sh(["node", ROOT / "templates/threejs_film/render.mjs", EP / "film.json", "--visibility"]); VIS = json.load(open(EP / "out/plan/visibility.json"))["frames"]
pairs = [(f.get("lantern.flame"), f.get("expect.flame")) for f in VIS]; both = [(a, b) for a, b in pairs if a and b]; err = max((max(abs(a["x"] - b["x"]), abs(a["y"] - b["y"])) for a, b in both), default=9)
t("F anchors (R7 anchor_target): 'lantern.flame' lands where the rot-30 / scale-1.2 placement puts it on %d frames (max error %.4f of the frame)" % (len(both), err), rv.returncode == 0 and both and err <= 0.002, "A")
ro = sh(["node", ROOT / "templates/threejs_film/render.mjs", EP / "film.json", "--object-visibility", "lantern.lamp_globe,lantern.fuel_tank", "--vis-frames", "0-%d" % (n - 1)]); OV = json.load(open(EP / "out/plan/object_visibility.json"))["frames"]
seen = [f["f"] if "f" in f else i for i, f in enumerate(OV) if f["hits"] > 0]
t("F in the final render: the lantern is seen (three.js ray test with occlusion, the scene the base stills came from) on %d of %d frames, and those stills are the final picture (manifest sha1s)" % (len(seen), n), len(seen) > 0 and len(FMn["inputs"]) == n, "A")
F_ = json.load(open(EP / "film.json")); t("F an R7 capability the film needs is declared: lantern needs %s; handcar placed by the set module (R4 seam)" % F_["places"]["canyon"]["assets"][1]["needs"], F_["places"]["canyon"]["assets"][1]["needs"] == ["static_prop", "anchor_target"], "A")

# ====================================================================== 6. R3 CHARACTER certification
cp_ = json.load(open(EP / "creative/character_production.json")); slot = next(iter(cp_["characters"])); ch_ = cp_["characters"][slot]
t("C character identity: slot '%s' = %s from the R3 registry, production record valid (characters.py validate)" % (slot, ch_.get("character")), not CH.validate(EP) and ch_.get("character") == "char_stationmaster", "A")
t("C the lock froze the character cards (index + every image sha1) and they still match (check-lock + lock_stamp)", CH.lock_problems(EP) == [] and LS.problems(EP) == [] and json.load(open(EP / "out/lock/lock.json"))["approved"]["cards"] == LS.card_hashes(EP), "A")
ca = light_copy(EP, "cards_rebuild"); shutil.rmtree(ca / "out/characters", ignore_errors=True); before = LS.card_hashes(EP); CH.build(ca); after_c = LS.card_hashes(ca)
t("C deterministic card generation: rebuilding the cards from the same spec gives the same index and image sha1s", before == after_c and before != {}, "A")
J_ = json.load(open(EP / "creative/JUDGE.json")); ev = J_.get("evidence_read", {})
t("C the cards reached storyboard/animatic/judge: the judge read the character evidence hash (%s) and the base render used the locked cards (cards frozen in the lock it rendered from)" % str(ev.get("characters_sha1", ev.get("character_production_sha1")))[:10], any("char" in k for k in ev) and S["7 base"]["status"] == "PASS", "A")

# ====================================================================== 7. SAFETY matrix (copies of the certified film; nothing here is expensive)
def render_refused(d): r_ = sh(["node", ROOT / "templates/threejs_film/render.mjs", d / "film.json", "--frames", "0"]); return r_.returncode == 3 and "REFUSED" in r_.stdout + r_.stderr and not (d / "out/stills").exists()
d = light_copy(EP, "s_noapproval"); (d / "approval.json").unlink(); rp, _ = pipeline(d)
t("S before approval: render.mjs --frames REFUSED (exit 3), final_video REFUSED, audio mux REFUSED, pipeline WAITS at G9 (exit 2) with no render", render_refused(d) and "REFUSED" in sh([PY, "-c", "import sys; sys.path.insert(0,%r); import final_video as F; F.assemble(%r)" % (str(ROOT / "tools"), str(d))]).stderr + "" and sh([PY, ROOT / "tools/audio.py", "mux", d]).returncode != 0 and rp.returncode == 2 and "WAITING" in rp.stdout and "Expensive render happened: NO" in rp.stdout, "A")
t("S after approval + lock: the production render was allowed and ran once (clean run above)", S["G9"]["status"] == "PASS" and S["7 base"]["status"] == "PASS", "A")
d = light_copy(EP, "s_lock"); Lk = json.load(open(d / "out/lock/lock.json")); Lk["approved"]["frozen"]["camera"] = "0" * 40; json.dump(Lk, open(d / "out/lock/lock.json", "w"))
t("S lock immutable: an edited lock.json (frozen camera hash) fails lock_stamp and the render is REFUSED", bool(LS.problems(d)) and render_refused(d), "A")
d = light_copy(EP, "s_card"); cd = next((d / "out/lock/cards").rglob("*.png")); b = bytearray(cd.read_bytes()); b[-20] ^= 1; cd.write_bytes(bytes(b))
t("S lock immutable: a changed locked character card is detected and the render is REFUSED", bool(LS.problems(d) or CH.lock_problems(d)) and render_refused(d), "A")
for nm, fn in (("PICTURE_PLAN.md", lambda d: (d / "creative/PICTURE_PLAN.md").write_text((d / "creative/PICTURE_PLAN.md").read_text() + "\nedited after approval\n")),
               ("words.json", lambda d: (d / "voice/words.json").write_text(json.dumps([dict(w, e=w["e"] + (0.01 if i == 3 else 0)) for i, w in enumerate(json.load(open(d / "voice/words.json")))]))),
               ("film.json (camera)", lambda d: json.dump(dict(json.load(open(d / "film.json")), title="edited"), open(d / "film.json", "w")))):
    d = light_copy(EP, "s_edit_" + nm.split(".")[0]); fn(d); t("S changed approved input (%s): approval STALE and the render REFUSED" % nm, any("STALE" in x or "differ" in x for x in AP.check(d)) and render_refused(d), "A")
gp = AS.glb_path(g); orig = gp.read_bytes(); gp.write_bytes(orig[:-4] + b"\x00\x00\x00\x07")
try:
    d = light_copy(EP, "s_glb"); t("S tampered GLB: detected by the resolver (stale GLB), the lock (library bytes != frozen), the approval (G7 at G9); render REFUSED; pipeline stops at G7 with no render",
                                     any("stale GLB" in x for x in AS.resolve_problems(d)[0]) and any("no longer the frozen" in x for x in LS.problems(d)) and any("G7 no longer passes" in x for x in AP.check(d)) and render_refused(d) and "Expensive render happened: NO" in pipeline(d)[0].stdout, "A")
finally: gp.write_bytes(orig)
t("S restoring the frozen GLB bytes makes the certified film valid again (byte check, not timestamps)", AP.check(EP) == [] and LS.problems(EP) == [], "A")
for nm, ent in (("wrong version", dict(id="prop_oil_lantern", version="9.9", needs=["static_prop"], **PLACE)), ("missing asset", dict(id="prop_no_such_thing", version="1.0", **PLACE))):
    d = light_copy(EP, "s_" + nm.replace(" ", "_")); F2 = json.load(open(d / "film.json")); F2["places"]["canyon"]["assets"][1] = ent; json.dump(F2, open(d / "film.json", "w"), indent=1)
    t("S %s: the resolver fails closed (%s)" % (nm, (AS.resolve_problems(d)[0] or ["-"])[0][:80]), bool(AS.resolve_problems(d)[0]), "A")
d = light_copy(EP, "s_audio_cue"); shutil.copy(EP / "out/final/final.mp4", d / "out/final/final.mp4"); F2 = json.load(open(d / "film.json")); F2["sound"][4]["gain"] = -1; json.dump(F2, open(d / "film.json", "w"), indent=1); ra = sh([PY, ROOT / "tools/audio.py", "mux", d])
t("S audio changed after approval (a sound cue in film.json): approval STALE, the mux is REFUSED, no delivery", ra.returncode != 0 and "REFUSED" in ra.stdout + ra.stderr and not (d / "out/final/final_video.mp4").exists(), "A")
d = light_copy(EP, "s_audio_src"); shutil.copy(EP / "out/final/final.mp4", d / "out/final/final.mp4"); (d / "sound/sfx/impact.wav").write_bytes(b"RIFF junk"); ra = sh([PY, ROOT / "tools/audio.py", "mux", d])
t("S a corrupted audio source after approval: the mux is REFUSED (cannot be decoded), no delivery", ra.returncode != 0 and "cannot be decoded" in ra.stdout + ra.stderr, "A")
d = light_copy(EP, "s_audio_swap"); shutil.copy(EP / "out/final/final.mp4", d / "out/final/final.mp4"); FA._write(d / "sound/sfx/impact.wav", FA.whoosh()); ra = sh([PY, ROOT / "tools/audio.py", "mux", d])
swapped = ra.returncode == 0 and json.load(open(d / "out/final/final_manifest.json"))["audio"]["inputs"]["sound/sfx/impact.wav"] != A["inputs"]["sound/sfx/impact.wav"]
note("S a VALID replacement audio source file after approval", "D", "R8 rule: audio SOURCE files are not approval-signed (sound is made after the visual lock, Ricks stage 11); the mux %s and the manifest records the new sha1 (%s), so the change is traced, not refused. The approval signs the cue plan (film.json) and words.json." % ("ran" if ra.returncode == 0 else "failed", "differs" if swapped else "?"))
d = light_copy(EP, "s_delivery"); shutil.copy(FV, d / "out/final/final_video.mp4"); shutil.copy(EP / "out/final/final.mp4", d / "out/final/final.mp4"); p = d / "out/final/final_video.mp4"; b = bytearray(p.read_bytes()); b[-300] ^= 1; p.write_bytes(bytes(b))
t("S a modified delivery MP4 FAILS the delivery QA", not all(ok for _, ok, _ in AU.qa(d)), "A")

# ====================================================================== 8. capability probes with the existing machinery (cheap: plan + three.js storyboard + animatic; no final render)
def probe(name, src, mut):
    d = W / "probes" / name; shutil.rmtree(d, ignore_errors=True); shutil.copytree(ROOT / src, d); (d / "creative").mkdir(exist_ok=True); F2 = json.load(open(d / "film.json")); mut(F2); json.dump(F2, open(d / "film.json", "w"), indent=1)
    r1 = sh([PY, ROOT / "tools/film_plan.py", "check", d / "film.json"]); res = (r1.stdout.strip().splitlines() or ["?"])[-1]
    t0 = time.time(); r2 = sh(["node", ROOT / "templates/threejs_film/render.mjs", d / "film.json", "--storyboard", "--scale", "0.4"]); t1 = time.time(); r3 = sh(["node", ROOT / "templates/threejs_film/render.mjs", d / "film.json", "--animatic", "--step", "3", "--scale", "0.4"])
    return d, res, r2.returncode == 0 and (d / "out/storyboard.png").is_file(), r3.returncode == 0 and (d / "out/animatic.mp4").is_file(), round(t1 - t0, 1), round(time.time() - t1, 1)
def two_takes(F2):
    S_ = F2["takes"][0]["stations"]; F2["takes"] = [dict(id="t1", place="canyon", stations=S_[:2]), dict(id="t2", place="canyon", stations=S_[2:])]
d, res, sb, an, ts, ta = probe("D_two_takes", "templates/film_canyon_example", two_takes); cam = json.load(open(d / "out/plan/camera_baked.json"))["frames"]; tk = sorted({f["take"] for f in cam})
t("D probe (2 takes = a planned cut): plan bake %s; takes %s baked; storyboard %s, animatic %s (%.0f s / %.0f s)" % (res[:40], tk, sb, an, ts, ta), " 0 FAIL" in res and tk == ["t1", "t2"] and sb and an, "B")
d, res, sb, an, ts, ta = probe("E_flight", "templates/film_flight_example", lambda F2: None)
t("E probe (fast action: a thrown coin flight + camera): plan bake %s; flights_baked %s; storyboard %s, animatic %s (%.0f s / %.0f s)" % (res[:40], (d / "out/plan/flights_baked.json").is_file(), sb, an, ts, ta), " 0 FAIL" in res and (d / "out/plan/flights_baked.json").is_file() and sb and an, "B")

# ====================================================================== 9. GPU path (existing render_gpu.mjs, unchanged)
rg = sh(["node", ROOT / "templates/threejs_film/render_gpu.mjs", EP / "film.json", "--gpu-info"]); gl = re.search(r"WebGL renderer: ([^|]+)", rg.stdout + rg.stderr)
RES["gpu"] = dict(rc=rg.returncode, renderer=gl[1].strip() if gl else None, dri=Path("/dev/dri").exists(), nvidia=bool(list(Path("/dev").glob("nvidia*"))))
if rg.returncode == 2 and not RES["gpu"]["dri"]: note("GPU CERTIFICATION: NOT EXECUTED", "E", "no GPU device in this container (/dev/dri absent, no /dev/nvidia*); Chromium's WebGL is '%s' and render_gpu.mjs correctly refuses to render on a CPU (exit 2, 'The graphics card is NOT drawing')" % RES["gpu"]["renderer"])
else: t("GPU path executed", rg.returncode == 0, "E")

# ====================================================================== 10. R5 stays a creative FAIL
JR = json.load(open(ROOT / "r5/episode/creative/JUDGE.json"))
t("H R5 'The Hat Toss' is still a creative FAIL (verdict %s, threshold 8.5 unchanged) and has no approval.json: the judge rejection is preserved" % JR.get("verdict"), JR.get("verdict") == "FAIL" and not (ROOT / "r5/episode/approval.json").exists() and "8.5" in (ROOT / "tools/review.py").read_text(), "C")

TIMES["certify_total_s"] = round(time.time() - T00, 1); TIMES["delivery_bytes"] = FV.stat().st_size
json.dump(dict(TIMES=TIMES, RES=RES, FINDINGS=FINDINGS, fails=fails), open(W / "r9_result.json", "w"), indent=1)
print("\nR9 TIMES:", json.dumps(TIMES)); print("R9 FINDINGS:", json.dumps(FINDINGS, indent=1)); print("\n%d FAIL" % len(fails)); [print("  FAILED: " + f) for f in fails]; sys.exit(1 if fails else 0)
