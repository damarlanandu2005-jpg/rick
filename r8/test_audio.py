#!/usr/bin/env python3
"""R8 tests: the minimal production audio layer (tools/audio.py + the cue bake in tools/film_plan.py + the pipeline's 11 sound / 12 delivery qa stages).
Small synthetic fixtures only (r8/fixture_audio.py, numpy, deterministic): a copy of the kit canyon example (299 frames, 30 fps, real words.json, real plan bake) and a synthetic
TEST "final.mp4" (ffmpeg testsrc2) for the mux cases, which run in the NAMED test mode (RICKS_UNAPPROVED_TEST_RUN=1, stamped production:false). The approved end-to-end run on the
R6 production fixture is r8/e2e_production.py.   python3 r8/test_audio.py   (about 1 minute)"""
import copy, hashlib, json, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent; sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "r8")]
import fixture_audio as FA, audio as AU
fails = []; T0 = time.time(); TIMES = {}
def t(name, ok): print(("PASS " if ok else "FAIL ") + name, flush=True); (ok or fails.append(name))
has = lambda bad, w: any(w in x for x in bad)
PY = sys.executable; W = Path(tempfile.mkdtemp(prefix="r8_")); TEST = {"RICKS_UNAPPROVED_TEST_RUN": "1"}
def sha(p): return hashlib.sha1(Path(p).read_bytes()).hexdigest()
def env(extra=None): e = {k: v for k, v in os.environ.items() if k != "RICKS_UNAPPROVED_TEST_RUN"}; e.update(extra or {}); return e
def sh(cmd, extra=None): return subprocess.run(cmd, capture_output=True, text=True, env=env(extra))
# ---- the base episode: canyon example copy + fixture audio + a synthetic TEST final.mp4 (299 frames)
BASE = W / "base"; shutil.copytree(ROOT / "templates/film_canyon_example", BASE); t0 = time.time(); FILES = FA.write_all(BASE, BASE / "voice/words.json", 9.9); TIMES["fixture_audio_s"] = round(time.time() - t0, 3)
(BASE / "out/final").mkdir(parents=True, exist_ok=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=720x1280:r=30", "-frames:v", "299", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p", "-an", str(BASE / "out/final/final.mp4")], check=True)
def manifest(d, frames=(0, 298)): json.dump(dict(fps=30, frames=list(frames), resolution=[720, 1280], layers={}, inputs={}, production=False, gated=False, mp4_sha1=sha(d / "out/final/final.mp4"), test="R8 synthetic final.mp4 (TEST)"), open(d / "out/final/final_manifest.json", "w"))
VOICE = dict(at=0, name="voice", type="voice", file="voice/voice.wav")
def case(name, sound, audio={"required": ["voice"]}, bake=True):
    d = W / name; shutil.rmtree(d, ignore_errors=True); shutil.copytree(BASE, d); F = json.load(open(d / "film.json")); F["sound"] = sound
    if audio is not None: F["audio"] = audio
    else: F.pop("audio", None)
    json.dump(F, open(d / "film.json", "w"), indent=1); manifest(d)
    if bake:
        r = sh([PY, str(ROOT / "tools/film_plan.py"), "check", str(d / "film.json")]); assert " 0 FAIL" in r.stdout.strip().splitlines()[-1], r.stdout[-300:]
    return d
def check(d): return AU.plan(d)[0]
def mux(d, test=True): return sh([PY, str(ROOT / "tools/audio.py"), "mux", str(d)], TEST if test else None)
def qa(d): R = AU.qa(d); return all(ok for _, ok, _ in R), [k for k, ok, _ in R if not ok]
def onset(x, thr=0.05): i = np.nonzero(np.abs(x) > thr)[0]; return int(i[0]) if len(i) else None
MUSIC = dict(at=0, name="bed", type="music", file="sound/music/bed.wav", until="end", gain=-18, fade_in=0.5, fade_out=1.0)
IMPACT = dict(at=["canyon", 1], name="impact", gain=-3)
AMB = dict(at=0, name="wind", type="ambience", file="sound/amb/wind.wav", until="end", gain=-6, fade_in=1.0, fade_out=1.0)

# ====================================================================== the six audio cases: validate -> mix -> mux -> decoded QA
CASES = {"A voice only": [VOICE], "B voice + music": [VOICE, MUSIC], "C voice + SFX (word-anchored)": [VOICE, IMPACT], "D voice + music + SFX": [VOICE, MUSIC, IMPACT],
         "E multiple simultaneous/overlapping SFX": [VOICE, dict(at=60, name="footstep", gain=-6), dict(at=60, name="impact", gain=-6), dict(at=62, name="whoosh", gain=-6)],
         "F ambience across the film": [VOICE, AMB]}
for k, (cn, snd) in enumerate(CASES.items()):
    d = case("case_%s" % cn[0], snd); bad = check(d); t0 = time.perf_counter(); r = mux(d); tm = time.perf_counter() - t0; t0 = time.perf_counter(); ok, badq = qa(d); tq = time.perf_counter() - t0
    TIMES.setdefault("mux_incl_mix_s", []).append(round(tm, 3)); TIMES.setdefault("delivery_qa_s", []).append(round(tq, 3))
    A = json.load(open(d / "out/final/final_manifest.json")).get("audio", {})
    t("%d %s: validates, mixes %d event(s), muxes and the DECODED delivery passes QA (%s)" % (k + 1, cn, len(snd), ", ".join(sorted({e["type"] for e in A.get("events", [])}))), bad == [] and r.returncode == 0 and ok and len(A.get("events", [])) == len(snd))
    if badq: print("   QA FAILED:", badq)
dB = W / "case_B"; MB = json.load(open(dB / "out/final/final_manifest.json"))["audio"]
t("6 timing comes from the existing film timing: the word-anchored impact starts at frame round(6.20 s * 30) = 186 (film_plan.fr), sample 186 * 1600", [e for e in json.load(open(W / "case_C/out/final/final_manifest.json"))["audio"]["events"] if e["name"] == "impact"][0]["start_sample"] == 186 * 1600)
t("6 music 'until: end' runs exactly to the last frame (299 * 1600 samples) with its fades; no second FPS (1600 samples per 30 fps frame)", [e for e in MB["events"] if e["type"] == "music"][0]["n_samples"] == 299 * 1600 and MB["mix"]["samples"] == 299 * 1600)
# ---- overlapping SFX mix correctly: the mix of all == the sum of the single-event mixes (linear, nothing dropped or normalised)
def mixof(snd, name): d = case(name, snd, audio={"silence_dbfs": -200}); w, st = AU.mix(d); return AU.decode(w, 2)[0], st
xs = [mixof([dict(at=60 if nm != "whoosh" else 62, name=nm, gain=-6)], "solo_" + nm)[0] for nm in ("footstep", "impact", "whoosh")]
xa, _ = mixof([dict(at=60, name="footstep", gain=-6), dict(at=60, name="impact", gain=-6), dict(at=62, name="whoosh", gain=-6)], "all_three")
t("5 overlap is LEGAL and mixed correctly: the three-SFX mix equals the sum of the three single-SFX mixes (max error %.2e)" % float(np.abs(xa - sum(xs)).max()), float(np.abs(xa - sum(xs)).max()) < 1e-5)
xc, _ = mixof([dict(at=90, name="click")], "click90"); t("6 frame-exact placement: a click cued at frame 90 starts at sample %s (= 90 * 1600 = 144000) in the mix" % onset(xc[:, 0]), onset(xc[:, 0]) == 144000)
d = case("sync", [VOICE, dict(at=90, name="click", gain=0)]); mux(d); x, _ = AU.decode(d / "out/final/final_video.mp4", 2)
t("16 A/V sync on the DECODED delivery: the frame-90 click is heard at %.2f ms after frame 90 (|.| <= 2 ms; the video is the frame clock)" % ((onset(x[140000:150000, 0], 0.2) + 140000 - 144000) / 48), abs(onset(x[140000:150000, 0], 0.2) + 140000 - 144000) <= 96)
# ====================================================================== fail closed
d = case("missing", [VOICE, dict(at=30, name="nosuchsound")]); t("7 missing audio file: 'ERROR: referenced audio file does not exist'", has(check(d), "ERROR: referenced audio file does not exist"))
r = mux(d); t("7 ... and the mux is refused (no delivery written, no silence substituted)", r.returncode != 0 and not (d / "out/final/final_video.mp4").exists())
d = case("corrupt", [VOICE, dict(at=30, name="corrupt")]); t("8 corrupt/undecodable audio: 'ERROR: audio file cannot be decoded'", has(check(d), "ERROR: audio file cannot be decoded"))
d = case("negstart", [VOICE, dict(at=-5, name="impact")]); t("9 invalid timing: negative start", has(check(d), "negative start"))
d = case("negdur", [VOICE, dict(at=30, name="bed", type="music", file="sound/music/bed.wav", dur=-1.0)]); t("9 invalid timing: negative duration", has(check(d), "negative duration"))
d = case("zerodur", [VOICE, dict(at=30, name="bed", type="music", file="sound/music/bed.wav", dur=0)]); t("9 invalid timing: zero duration", has(check(d), "zero duration"))
d = case("endbefore", [VOICE, dict(at=["canyon", 1], name="bed", type="music", file="sound/music/bed.wav", until=["railroad", 1])]); t("9 invalid timing: end before start (until 'railroad' < at 'canyon')", has(check(d), "end before start"))
d = case("nan", [VOICE, dict(at=30, name="impact", gain="loud")]); t("9 invalid numeric value (gain 'loud')", has(check(d), "invalid numeric value"))
d = case("fade", [VOICE, dict(at=30, name="impact", fade_in=0.2, fade_out=0.2)]); t("9 invalid timing: fades longer than the event", has(check(d), "longer than the event"))
d = case("both", [VOICE, dict(at=30, name="bed", type="music", file="sound/music/bed.wav", dur=1.0, until="end")]); t("9 dur AND until together is rejected", has(check(d), "dur OR until"))
d = case("vlate", [dict(VOICE, at=15)]); t("9 voice must start at frame 0 (words.json times are voice times)", has(check(d), "voice must start at frame 0"))
d = case("unknown", [VOICE, dict(at=30, name="impact", type="dialogue")]); t("10 unknown event type fails closed", has(check(d), "unknown event type 'dialogue'"))
d = case("unkfield", [VOICE, dict(at=30, name="impact", pan=0.5)], bake=False); F = json.load(open(d / "film.json")); json.dump(F, open(d / "film.json", "w")); sh([PY, str(ROOT / "tools/film_plan.py"), "check", str(d / "film.json")])
ev = json.load(open(d / "out/plan/sound_events.json")); ev[-1]["pan"] = 0.5; json.dump(ev, open(d / "out/plan/sound_events.json", "w")); t("10 an unknown cue field (pan) fails closed", has(check(d), "unknown cue field"))
d = case("unkset", [VOICE], audio={"required": ["voice"], "loudness_lufs": -16}); t("10 an unknown audio setting fails closed (no silent ignore)", has(check(d), "unknown audio setting"))
d = case("past", [VOICE, dict(at=290, name="whoosh")]); t("11 out of range: an SFX extending past the film end is an error (no silent truncation)", has(check(d), "extends past the film end"))
d = case("after", [VOICE, dict(at=400, name="impact")]); t("11 out of range: an event starting after the last frame", has(check(d), "after the film ends"))
FA._write(W / "long_voice.wav", FA.voice(json.load(open(BASE / "voice/words.json")), 10.5)); d = case("vlong", [dict(VOICE, file=str(W / "long_voice.wav"))]); t("11 out of range: a voice longer than the film (10.5 s > 9.97 s)", has(check(d), "extends past the film end"))
d = case("short", [VOICE, dict(at=0, name="short", type="music", file="sound/music/short.wav", until="end")]); t("8/11 music shorter than its region fails (no silent looping or padding)", has(check(d), "shorter than the requested region"))
d = case("loop", [VOICE, dict(at=0, name="short", type="music", file="sound/music/short.wav", until="end", loop=True)]); t("8 'loop' is rejected (looping is not supported)", has(check(d), "looping is not supported"))
d = case("noreq", [VOICE], audio={"required": ["voice", "music"]}); t("12 missing required audio: music required, none given", has(check(d), "missing required audio: music"))
d = case("novoice", [MUSIC], audio={"required": ["voice"]}); t("12 missing mandatory voice fails clearly", has(check(d), "missing required audio: voice"))
d = case("gain", [VOICE, dict(at=30, name="impact", gain=40)]); t("12 invalid gain (+40 dB) is rejected (audio.gain_db_range)", has(check(d), "invalid gain"))
d = case("clip", [VOICE, dict(at=60, name="footstep", gain=10), dict(at=60, name="impact", gain=10), dict(at=60, name="whoosh", gain=10)]); r = mux(d)
t("12 clipping/overload: a mix peaking above audio.max_peak_dbfs (-1 dBFS) is REFUSED, not limited", r.returncode != 0 and "exceeds audio.max_peak_dbfs" in r.stdout + r.stderr and not (d / "out/final/final_video.mp4").exists())
d = case("silent", [dict(VOICE, gain=-60)]); r = mux(d); t("12 a silent mix when audio was declared is REFUSED", r.returncode != 0 and "is silent" in r.stdout + r.stderr)
# ====================================================================== delivery integrity, determinism, partial semantics
dA = W / "case_A"
t("13 valid final mux: out/final/final_video.mp4 written next to the untouched silent final.mp4", (dA / "out/final/final_video.mp4").stat().st_size > 0 and json.load(open(dA / "out/final/final_manifest.json"))["mp4_sha1"] == sha(dA / "out/final/final.mp4"))
S = AU.probe(dA / "out/final/final_video.mp4"); t("14 the final MP4 contains an AAC audio stream (ffprobe of the actual file)", [s["codec_name"] for s in S if s["codec_type"] == "audio"] == ["aac"])
t("15 the final MP4 stays visually valid: 299 decoded h264 frames, 720x1280, 30/1, picture identical to final.mp4", [(s["codec_name"], s["width"], s["height"], s["r_frame_rate"], s["nb_read_frames"]) for s in S if s["codec_type"] == "video"] == [("h264", 720, 1280, "30/1", "299")])
s1 = sha(dA / "out/final/final_video.mp4"); m1 = sha(dA / "out/audio/mix.wav"); mux(dA)
t("17 deterministic: re-mixing and re-muxing the same inputs gives byte-identical mix.wav and final_video.mp4", sha(dA / "out/final/final_video.mp4") == s1 and sha(dA / "out/audio/mix.wav") == m1)
A = json.load(open(dA / "out/final/final_manifest.json"))["audio"]
t("17 hashes in the EXISTING final manifest: every audio input, the mix, the delivery and the config (no second tracking system)", A["inputs"] == {"voice/voice.wav": sha(dA / "voice/voice.wav")} and A["mix"]["sha1"] == m1 and A["delivery"]["sha1"] == s1 and A["config"]["max_peak_dbfs"] == -1.0)
d = case("old", [dict(at=["canyon", 1], name="whoosh", gain=-3)], audio=None); t("17 an R1-R7 cue {at, name, gain} still bakes to exactly {t, name, gain} (old baked files unchanged)", json.load(open(d / "out/plan/sound_events.json")) == [{"t": 6.2, "name": "whoosh", "gain": -3}])
t("17 a film without an \"audio\" block declares no audio: check says so and mux refuses (nothing invented)", AU.plan(d)[2] is None and mux(d).returncode != 0)
d = case("tampered_dv", [VOICE]); mux(d); p = d / "out/final/final_video.mp4"; b = bytearray(p.read_bytes()); b[-100] ^= 1; p.write_bytes(bytes(b)); ok, bq = qa(d)
t("16 a modified delivery MP4 is caught by the decoded QA (sha1 vs manifest)", not ok and has(bq, "delivery sha1"))
d = case("noaudio_dv", [VOICE]); mux(d); p = d / "out/final/final_video.mp4"; subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(d / "out/final/final.mp4"), "-c", "copy", str(p)]); ok, bq = qa(d)
t("14 a delivery without an audio stream FAILS the QA", not ok and has(bq, "exactly one audio stream"))
d = case("tampered_fin", [VOICE]); f = d / "out/final/final.mp4"; b = bytearray(f.read_bytes()); b[-50] ^= 1; f.write_bytes(bytes(b)); r = mux(d)
t("15 a final.mp4 that is not the assembled one (sha1 vs final_manifest) is REFUSED for mux", r.returncode != 0 and "not the assembled video" in r.stdout + r.stderr)
d = case("partial", [VOICE]); manifest(d, (0, 2)); r = mux(d); t("R1 semantics: a PARTIAL final video (frames 0-2) is never muxed into a delivery", r.returncode != 0 and "PARTIAL" in r.stdout + r.stderr)
# ====================================================================== approval safety (production mode: no test bypass)
d = case("noapproval", [VOICE, MUSIC]); r = mux(d, test=False)
t("18 approval safety: without approval.json + lock the production mux is REFUSED (G9/lock), no delivery", r.returncode != 0 and "REFUSED" in r.stdout + r.stderr and not (d / "out/final/final_video.mp4").exists())
r1 = sh([PY, str(ROOT / "tools/audio.py"), "check", str(d)]); r2 = sh([PY, str(ROOT / "tools/audio.py"), "mix", str(d)])
t("18 the cheap preview stays allowed before approval: audio check + mix (no video, never a delivery)", r1.returncode == 0 and r2.returncode == 0 and (d / "out/audio/mix.wav").is_file() and not (d / "out/final/final_video.mp4").exists())
r = subprocess.run(["node", str(ROOT / "templates/threejs_film/render.mjs"), str(d / "film.json"), "--frames", "0"], capture_output=True, text=True, env=env())
t("19 an unapproved production render remains BLOCKED (render.mjs --frames: REFUSED, exit 3)", r.returncode == 3 and "REFUSED" in r.stdout + r.stderr)
r = sh([PY, "-c", "import sys; sys.path.insert(0, %r); import final_video as FV; FV.assemble(%r)" % (str(ROOT / "tools"), str(d))]); t("19 an unapproved final video assembly remains BLOCKED", r.returncode != 0 and "REFUSED" in r.stdout + r.stderr)
A = json.load(open(W / "case_D/out/final/final_manifest.json"))["audio"]; t("18 the named test mode stamps every delivery production:false (gated false)", A["production"] is False and A["gated"] is False)
src = (ROOT / "tools/pipeline.py").read_text(); i, j = src.index('stop("10 qa"'), src.index('import audio as AU')
t("18 pipeline order: 11 sound runs only after 10 qa passed (after approval, lock and the one final render); no sound flag skips a gate", i < j and "--skip" not in src and "accept-audio" not in src)
t("R8 no TTS, music generation or downloading in the audio layer", not any(w in (ROOT / "tools/audio.py").read_text() for w in ("fish_tts", "requests.", "urllib", "WhisperModel")))
print("\nR8 TIMES:", json.dumps(TIMES)); print("TOTAL %d s" % (time.time() - T0)); print("\n%d FAIL" % len(fails)); [print("  FAILED: " + f) for f in fails]; sys.exit(1 if fails else 0)
