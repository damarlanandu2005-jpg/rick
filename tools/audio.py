#!/usr/bin/env python3
"""R8: the minimal production audio layer (engineering only; Ricks' sound-designer agent stays the creative authority for WHICH sounds and WHERE).
Ricks provides the sound methodology (agents/sound-designer.md, CB_RULES sec. 6, WORKFLOW step 10) and the cue list: film.json "sound" -> out/plan/sound_events.json (tools/film_plan.py,
word-anchored). It has no executable mix in this repository (the build_mix.py it names is not here) and the final video was silent. R8 provides the missing engineering audio layer
required to operationalize the project's sound-design requirements: validate -> mix -> FFmpeg mux onto the approved, already rendered final.mp4 -> decoded QA. It is NOT a DAW,
TTS, music generator, ducking/mastering suite or loudness normaliser.

film.json (the plan stays the ONE authority; no second schema, no second clock):
  "audio": {"required": ["voice", ...], "sfx_dir": "sound/sfx", "gain_db_range": [-60, 12], "max_peak_dbfs": -1.0, "silence_dbfs": -60.0, "bitrate": "192k", "sync_tol_ms": 2.0}
           (absent = the film declares no audio: the delivery stays the silent final.mp4 and the pipeline's sound stage is SKIP)
  "sound": [{"at": <word anchor | frame>, "name": str, "gain": dB,                         <- the existing Ricks cue (R1-R7 unchanged)
             "type": voice|music|sfx|ambience (default sfx), "file": path in the episode   <- R8, optional (an sfx without "file" is <sfx_dir>/<name>.wav|mp3|flac|ogg|m4a)
             "dur": s | "until": <word anchor | "end">, "offset": s into the source, "fade_in": s, "fade_out": s}]
  Start = the cue's FRAME (film_plan.fr, the existing timing): sample = frame * 48000 / 30 exactly (1600 per frame). Voice starts at frame 0 (words.json times are voice times; never re-timed).
Fail closed (no silent substitution, looping or truncation): missing / undecodable file, unknown type or field, non-numeric / negative / inverted timing, a source shorter than its region,
an event past the film end, a gain outside the range, a missing required type, a mix whose peak exceeds max_peak_dbfs, a silent mix.
  audio.py check <ep>          validate only (cheap; allowed before approval)
  audio.py mix <ep> [out.wav]  validate + mix (cheap preview; allowed before approval; never a delivery)
  audio.py mux <ep>            G9 + lock gated (final_video.production_gate): mix + mux onto out/final/final.mp4 (video stream COPIED, never re-rendered) -> out/final/final_video.mp4
  audio.py qa <ep>             decodes the delivered MP4 itself: streams, size, fps, frame count, picture == final.mp4, audio length, level, A/V sync (cross-correlation)"""
import hashlib, json, math, subprocess, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
SR = 48000; TYPES = ("voice", "music", "sfx", "ambience")
DEFAULTS = dict(required=[], sfx_dir="sound/sfx", gain_db_range=[-60.0, 12.0], max_peak_dbfs=-1.0, silence_dbfs=-60.0, bitrate="192k", sync_tol_ms=2.0)
CUE_KEYS = {"t", "name", "gain", "frame", "type", "file", "dur", "end_frame", "offset", "fade_in", "fade_out", "loop"}
EXTS = (".wav", ".mp3", ".flac", ".ogg", ".m4a")
def sha(p): return hashlib.sha1(Path(p).read_bytes()).hexdigest()
def num(x): return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
def config(ep):
    F = json.load(open(Path(ep) / "film.json")); a = F.get("audio")
    return (None if a is None else {**DEFAULTS, **a}), F
def decode(path, ch=1):
    """Full decode with ffmpeg to float32 at 48 kHz -> (samples [n, ch], error). Decoding everything is the readability test."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", str(path), "-vn", "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"], capture_output=True)
    if r.returncode or not r.stdout: return None, (r.stderr.decode(errors="replace").strip().splitlines() or ["no audio decoded"])[-1][:160]
    return np.frombuffer(r.stdout, np.float32).reshape(-1, ch), None
def film_frames(ep): return len(json.load(open(Path(ep) / "out/plan/camera_baked.json"))["frames"])
def plan(ep):
    """-> (problems, events, cfg, n_frames). events carry exact sample positions; nothing is guessed or repaired."""
    ep = Path(ep); cfg, F = config(ep)
    if cfg is None: return [], [], None, None
    bad = []; fps = F["fps"]; n = film_frames(ep); total = n * SR // fps
    if fps != 30: bad.append("fps %s: the production FPS is 30 (no second FPS)" % fps)
    for k in cfg:
        if k not in DEFAULTS: bad.append("audio.%s: unknown audio setting" % k)
    for r_ in cfg["required"]:
        if r_ not in TYPES: bad.append("audio.required: unknown type %r" % r_)
    lo, hi = cfg["gain_db_range"]; evs = []
    se = ep / "out/plan/sound_events.json"
    if not se.is_file(): return bad + ["out/plan/sound_events.json missing: run film_plan.py check (the cue bake)"], [], cfg, n
    for i, e in enumerate(json.load(open(se))):
        eid = "cue %d %r" % (i, e.get("name")); ty = e.get("type", "sfx"); fr = e.get("frame", round(e["t"] * fps) if num(e.get("t")) else None); P = lambda m: bad.append("%s: %s" % (eid, m))
        extra = set(e) - CUE_KEYS
        if extra: P("unknown cue field(s) %s" % sorted(extra)); continue
        if ty not in TYPES: P("unknown event type %r (voice|music|sfx|ambience)" % ty); continue
        if "loop" in e: P("looping is not supported (no silent loop): supply a source as long as the region"); continue
        nums = {k: e[k] for k in ("gain", "dur", "offset", "fade_in", "fade_out") if k in e}
        badn = [k for k, v in nums.items() if not num(v)]
        if badn or not isinstance(fr, int) or isinstance(fr, bool) or ("end_frame" in e and not isinstance(e["end_frame"], int)): P("invalid numeric value(s) %s" % (badn or ["frame/end_frame"])); continue
        if fr < 0: P("negative start (frame %d)" % fr); continue
        if fr >= n: P("starts at frame %d, after the film ends (frame %d)" % (fr, n - 1)); continue
        if "dur" in e and "end_frame" in e: P("give dur OR until, not both"); continue
        if "dur" in e and e["dur"] <= 0: P("%s duration %s" % ("negative" if e["dur"] < 0 else "zero", e["dur"])); continue
        if "end_frame" in e and e["end_frame"] <= fr: P("end before start (until frame %d <= start frame %d)" % (e["end_frame"], fr)); continue
        off = nums.get("offset", 0.0); fi = nums.get("fade_in", 0.0); fo = nums.get("fade_out", 0.0); g = nums.get("gain", 0.0)
        if off < 0 or fi < 0 or fo < 0: P("negative offset/fade"); continue
        if not lo <= g <= hi: P("invalid gain %s dB (allowed %s..%s dB, audio.gain_db_range)" % (g, lo, hi)); continue
        if ty == "voice" and (fr != 0 or off != 0): P("voice must start at frame 0 with offset 0 (words.json times ARE the voice times; Ricks never re-times the voice)"); continue
        f = (ep / e["file"]) if e.get("file") else next((ep / cfg["sfx_dir"] / (e["name"] + x) for x in EXTS if (ep / cfg["sfx_dir"] / (e["name"] + x)).is_file()), None)
        if f is None or not f.is_file(): P("ERROR: referenced audio file does not exist (%s)" % (e.get("file") or "%s/%s.*" % (cfg["sfx_dir"], e["name"]))); continue
        x, err = decode(f)
        if err: P("ERROR: audio file cannot be decoded (%s: %s)" % (f.name, err)); continue
        src = len(x); o = int(round(off * SR))
        ns = ((e["end_frame"] - fr) * SR // fps) if "end_frame" in e else int(round(e["dur"] * SR)) if "dur" in e else src - o
        if ns <= 0: P("offset %.3f s is past the end of the source (%.3f s)" % (off, src / SR)); continue
        if o + ns > src: P("source %s is %.3f s, shorter than the requested region %.3f-%.3f s (no silent looping or padding)" % (f.name, src / SR, off, off + ns / SR)); continue
        st = fr * SR // fps
        if st + ns > total: P("extends past the film end: %.3f-%.3f s, film is %.3f s (no silent truncation)" % (st / SR, (st + ns) / SR, total / SR)); continue
        if (fi + fo) * SR > ns + 1: P("fade_in + fade_out (%.3f s) longer than the event (%.3f s)" % (fi + fo, ns / SR)); continue
        evs.append(dict(id=i, name=e["name"], type=ty, file=str(f.relative_to(ep)) if f.is_relative_to(ep) else str(f), sha1=sha(f), frame=fr, start_sample=st, offset_sample=o, n_samples=ns,
                        gain_db=g, fade_in_samples=int(round(fi * SR)), fade_out_samples=int(round(fo * SR)), source_samples=src))
    for r_ in cfg["required"]:
        if r_ in TYPES and not any(v["type"] == r_ for v in evs): bad.append("missing required audio: %s (audio.required)" % r_)
    return bad, evs, cfg, n
def mix(ep, out=None):
    """Validate, then mix every event at its exact sample onto a silent bed of exactly n_frames * 1600 samples (48 kHz stereo float WAV, bit-exact flags). -> (wav, stats). Raises SystemExit on any problem."""
    ep = Path(ep); bad, evs, cfg, n = plan(ep)
    if cfg is None: raise SystemExit("film.json declares no audio (no \"audio\" block)")
    if bad: raise SystemExit("audio validation FAILED: " + "; ".join(bad))
    fps = json.load(open(ep / "film.json"))["fps"]; total = n * SR // fps; out = Path(out) if out else ep / "out/audio/mix.wav"; out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-v", "error", "-nostdin", "-f", "lavfi", "-i", "anullsrc=r=%d:cl=stereo" % SR]; fl = ["[0:a]atrim=end_sample=%d[bed]" % total]
    for k, v in enumerate(evs):
        cmd += ["-i", str(ep / v["file"]) if not Path(v["file"]).is_absolute() else v["file"]]
        ch = "[%d:a]aresample=%d,aformat=sample_fmts=fltp:channel_layouts=stereo,atrim=start_sample=%d:end_sample=%d,asetpts=N/SR/TB,volume=%sdB" % (k + 1, SR, v["offset_sample"], v["offset_sample"] + v["n_samples"], repr(float(v["gain_db"])))
        if v["fade_in_samples"]: ch += ",afade=t=in:ss=0:ns=%d" % v["fade_in_samples"]
        if v["fade_out_samples"]: ch += ",afade=t=out:start_sample=%d:nb_samples=%d" % (v["n_samples"] - v["fade_out_samples"], v["fade_out_samples"])
        fl.append(ch + ",adelay=delays=%dS:all=1[e%d]" % (v["start_sample"], k))
    fl.append("[bed]" + "".join("[e%d]" % k for k in range(len(evs))) + "amix=inputs=%d:duration=first:normalize=0:dropout_transition=0,atrim=end_sample=%d[mix]" % (len(evs) + 1, total))
    r = subprocess.run(cmd + ["-filter_complex", ";".join(fl), "-map", "[mix]", "-c:a", "pcm_f32le", "-ar", str(SR), "-ac", "2", "-fflags", "+bitexact", "-flags:a", "+bitexact", str(out)], capture_output=True, text=True)
    if r.returncode: raise SystemExit("ffmpeg mix failed: " + r.stderr[-400:])
    x, err = decode(out, 2)
    if err: raise SystemExit("the mix cannot be decoded: " + err)
    pk = float(np.abs(x).max()) if len(x) else 0.0; rms = float(np.sqrt(np.mean(x.astype(np.float64) ** 2))) if len(x) else 0.0; db = lambda v: round(20 * math.log10(v), 2) if v > 0 else -math.inf
    st = dict(file=str(out.relative_to(ep)) if out.is_relative_to(ep) else str(out), sha1=sha(out), samples=len(x), expected_samples=total, peak_dbfs=db(pk), rms_dbfs=db(rms), events=len(evs))
    if len(x) != total: raise SystemExit("mix length %d samples != film %d samples" % (len(x), total))
    if db(pk) > cfg["max_peak_dbfs"]: raise SystemExit("mix peak %.2f dBFS exceeds audio.max_peak_dbfs %.2f (clipping/overload risk): lower a gain" % (db(pk), cfg["max_peak_dbfs"]))
    if db(rms) < cfg["silence_dbfs"]: raise SystemExit("the mix is silent (RMS %s dBFS < audio.silence_dbfs %s) although audio was declared" % (db(rms), cfg["silence_dbfs"]))
    return out, dict(st, events_detail=evs, config=cfg)
def mux(ep):
    """The delivery: only after the approved, locked, rendered final.mp4 (whole film). Video stream COPIED; the audio is the validated mix in AAC. Updates final_manifest.json["audio"]."""
    import final_video as FV, approval as AP
    ep = Path(ep); cfg, F = config(ep)
    if cfg is None: raise SystemExit("film.json declares no audio (no \"audio\" block): nothing to mux")
    gated = FV.production_gate(ep)   # REFUSED without approval + lock (only RICKS_UNAPPROVED_TEST_RUN=1 bypasses, stamped production:false)
    fin = ep / "out/final/final.mp4"; mf = ep / "out/final/final_manifest.json"
    if not (fin.is_file() and mf.is_file()): raise SystemExit("REFUSED: no rendered final video (out/final/final.mp4 + final_manifest.json): audio comes after the one final render")
    M = json.load(open(mf)); n = film_frames(ep)
    if M.get("mp4_sha1") != sha(fin): raise SystemExit("REFUSED: out/final/final.mp4 is not the assembled video (sha1 differs from final_manifest.json)")
    if M.get("frames") != [0, n - 1]: raise SystemExit("REFUSED: final.mp4 is a PARTIAL range %s; a delivery needs the whole film 0-%d" % (M.get("frames"), n - 1))
    wav, st = mix(ep); dv = ep / "out/final/final_video.mp4"
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-nostdin", "-i", str(fin), "-i", str(wav), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", cfg["bitrate"], "-ar", str(SR), "-ac", "2",
                        "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact", str(dv)], capture_output=True, text=True)
    if r.returncode: raise SystemExit("ffmpeg mux failed: " + r.stderr[-400:])
    M["audio"] = dict(config=cfg, inputs={v["file"]: v["sha1"] for v in st["events_detail"]}, events=st["events_detail"], mix={k: st[k] for k in ("file", "sha1", "samples", "peak_dbfs", "rms_dbfs")},
                      delivery=dict(file="out/final/final_video.mp4", sha1=sha(dv), bytes=dv.stat().st_size, video_from="final.mp4 (stream copy, mp4_sha1 %s)" % M["mp4_sha1"][:12]),
                      production=bool(gated and M.get("production") and not AP.is_test_fixture(ep)), gated=gated)
    json.dump(M, open(mf, "w"), indent=1); return dv, M["audio"]
def probe(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate,nb_read_frames,sample_rate,channels,duration", "-of", "json", str(p)], capture_output=True, text=True)
    return json.loads(r.stdout or "{}").get("streams", []) if r.returncode == 0 else None
def qa(ep):
    """Checks on the ACTUAL delivered file (decoded), never on the mux exit code. -> [(name, ok, detail)]"""
    ep = Path(ep); dv = ep / "out/final/final_video.mp4"; fin = ep / "out/final/final.mp4"; R = []; add = lambda k, ok, d="": R.append((k, bool(ok), d))
    cfg, F = config(ep); n = film_frames(ep); fps = F["fps"]; M = json.load(open(ep / "out/final/final_manifest.json")); A = M.get("audio") or {}
    add("delivery file exists and is non-zero", dv.is_file() and dv.stat().st_size > 0, str(dv.stat().st_size if dv.is_file() else 0) + " bytes")
    if not R[-1][1]: return R
    add("delivery sha1 == final_manifest audio.delivery (the muxed file, unmodified)", (A.get("delivery") or {}).get("sha1") == sha(dv))
    S = probe(dv); add("ffprobe reads the MP4", S is not None)
    if not S: return R
    V = [s for s in S if s["codec_type"] == "video"]; Au = [s for s in S if s["codec_type"] == "audio"]
    W, H = M["resolution"]; add("exactly one video stream: h264 %dx%d at %d fps" % (W, H, fps), len(V) == 1 and V[0]["codec_name"] == "h264" and (V[0]["width"], V[0]["height"]) == (W, H) and V[0]["r_frame_rate"] == "%d/1" % fps, str(V and {k: V[0].get(k) for k in ("codec_name", "width", "height", "r_frame_rate")}))
    add("decoded video frame count == film %d frames" % n, len(V) == 1 and int(V[0].get("nb_read_frames", -1)) == n, str(V and V[0].get("nb_read_frames")))
    md5 = lambda p: subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", str(p), "-map", "0:v:0", "-f", "md5", "-"], capture_output=True, text=True).stdout.strip()
    add("the picture is UNCHANGED: decoded video == decoded final.mp4 (no re-render, no re-encode)", md5(dv) == md5(fin) != "")
    add("exactly one audio stream: aac 48 kHz stereo", len(Au) == 1 and Au[0]["codec_name"] == "aac" and Au[0].get("sample_rate") == str(SR) and Au[0].get("channels") == 2, str(Au and {k: Au[0].get(k) for k in ("codec_name", "sample_rate", "channels")}))
    if len(Au) != 1: return R
    x, err = decode(dv, 2); add("the audio stream decodes completely", err is None, err or "")
    if err: return R
    want = n * SR // fps; d = len(x) - want; add("audio length == video length within 1 frame (%d samples)" % (SR // fps), abs(d) <= SR // fps, "audio %.4f s, video %.4f s (%+d samples)" % (len(x) / SR, n / fps, d))
    pk = float(np.abs(x).max()); rms = float(np.sqrt(np.mean(x.astype(np.float64) ** 2))); db = lambda v: 20 * math.log10(v) if v > 0 else -math.inf
    add("not silent (RMS %.1f dBFS >= %s)" % (db(rms), cfg["silence_dbfs"]), db(rms) >= cfg["silence_dbfs"])
    add("no digital clipping in the decoded audio (peak %.2f dBFS < 0)" % db(pk), pk < 1.0)
    mw = ep / A.get("mix", {}).get("file", "out/audio/mix.wav"); y, e2 = decode(mw, 2) if mw.is_file() else (None, "mix.wav missing")
    if y is None: add("A/V sync: mix.wav available", False, e2); return R
    a_, b_ = x[:want, 0].astype(np.float64), y[:want, 0].astype(np.float64); L = SR // 10; m = min(len(a_), len(b_))
    nf = 1 << int(math.ceil(math.log2(2 * m))); c = np.fft.irfft(np.fft.rfft(a_[:m], nf) * np.conj(np.fft.rfft(b_[:m], nf)), nf); lags = np.r_[c[:L + 1], c[-L:]]; li = int(np.argmax(lags)); lag = li if li <= L else li - len(lags)
    corr = float(lags[li] / (np.sqrt(np.sum(a_[:m] ** 2) * np.sum(b_[:m] ** 2)) + 1e-12))
    add("A/V sync: the delivered audio lines up with the frame-exact mix (lag %+.2f ms <= %s ms, correlation %.3f >= 0.9)" % (1000 * lag / SR, cfg["sync_tol_ms"], corr), abs(1000 * lag / SR) <= cfg["sync_tol_ms"] and corr >= 0.9)
    add("production flag: %s (approval + lock gated: %s)" % (A.get("production"), A.get("gated")), A.get("production") == bool(A.get("gated") and M.get("production")))
    return R
if __name__ == "__main__":
    c, ep = sys.argv[1], sys.argv[2]
    if c == "check":
        bad, evs, cfg, n = plan(ep)
        print("no audio declared" if cfg is None else "\n".join(bad) or "audio OK: %d event(s), %s" % (len(evs), ", ".join("%s@%d" % (v["name"], v["frame"]) for v in evs))); sys.exit(1 if bad else 0)
    if c == "mix": w, st = mix(ep, sys.argv[3] if len(sys.argv) > 3 else None); print("mix ->", w, {k: st[k] for k in ("sha1", "samples", "peak_dbfs", "rms_dbfs", "events")}); sys.exit(0)
    if c == "mux": dv, A = mux(ep); print("delivery ->", dv, "production:%s" % A["production"]); sys.exit(0)
    if c == "qa":
        R = qa(ep); [print(("PASS " if ok else "FAIL ") + k + (" | " + d if d else "")) for k, ok, d in R]; sys.exit(0 if all(ok for _, ok, _ in R) else 1)
    sys.exit(__doc__)
