#!/usr/bin/env python3
"""TEST_FIXTURE_ONLY (R8): tiny deterministic synthetic audio for the engineering tests. Generated with numpy and written with the standard wave module, so the bytes do not depend on an
encoder version. Nothing here is downloaded, sampled or copyrighted, and none of it is a sound design: a "voice" is a tone burst per word of words.json, "music" a held chord, the SFX are
seeded noise/tone shapes, the "ambience" smoothed seeded noise. Production sounds come from CB's library (Ricks CB_RULES sec. 6), never from this file.
  write_all(dir, words_json, voice_len_s) -> {name: path}"""
import json, wave
from pathlib import Path
import numpy as np
SR = 48000
def _write(p, x, ch=1):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True); y = np.clip(np.round(np.asarray(x, np.float64) * 32767), -32767, 32767).astype("<i2")
    with wave.open(str(p), "wb") as w: w.setnchannels(ch); w.setsampwidth(2); w.setframerate(SR); w.writeframes(y.tobytes())
    return p
def _t(sec): return np.arange(int(round(sec * SR))) / SR
def _ramp(n, k=480): r = np.ones(n); k = min(k, n // 2); r[:k] = np.linspace(0, 1, k); r[n - k:] = np.linspace(1, 0, k); return r
def voice(words, length):
    x = np.zeros(int(round(length * SR)))
    for w in words:
        a, b = int(w["s"] * SR), min(int(w["e"] * SR), len(x))
        if b - a > 960: tt = np.arange(b - a) / SR; x[a:b] += 0.3 * (np.sin(2 * np.pi * 180 * tt) + 0.4 * np.sin(2 * np.pi * 360 * tt)) / 1.4 * _ramp(b - a)
    return x
def music(sec): tt = _t(sec); return 0.12 * sum(np.sin(2 * np.pi * f * tt) for f in (220.0, 277.18, 329.63)) / 3
def noise(sec, seed): return np.random.default_rng(seed).uniform(-1, 1, int(round(sec * SR)))
def impact(): n = noise(0.25, 1); return 0.5 * n * np.exp(-_t(0.25) * 18)
def whoosh(): n = np.convolve(noise(0.5, 2), np.ones(24) / 24, "same"); return 1.6 * n * np.sin(np.pi * _t(0.5) / 0.5) ** 2
def footstep(): tt = _t(0.08); return 0.45 * np.sin(2 * np.pi * 90 * tt) * np.exp(-tt * 60)
def click(): x = np.zeros(int(0.05 * SR)); x[0] = 0.6; x[1:200] = 0.6 * np.exp(-np.arange(1, 200) / 40.0); return x   # a sharp onset for the sync test
def ambience(sec): n = np.convolve(noise(sec, 3), np.ones(64) / 64, "same"); return 0.25 * n
def write_all(d, words_json, voice_len):
    d = Path(d); words = json.load(open(words_json))
    out = dict(voice=_write(d / "voice/voice.wav", voice(words, voice_len)), music=_write(d / "sound/music/bed.wav", music(16.0)), music_short=_write(d / "sound/music/short.wav", music(2.0)),
               impact=_write(d / "sound/sfx/impact.wav", impact()), whoosh=_write(d / "sound/sfx/whoosh.wav", whoosh()), footstep=_write(d / "sound/sfx/footstep.wav", footstep()),
               click=_write(d / "sound/sfx/click.wav", click()), ambience=_write(d / "sound/amb/wind.wav", ambience(16.0)))
    c = d / "sound/sfx/corrupt.wav"; c.write_bytes(b"RIFF\x24\x00\x00\x00WAVEfmt " + bytes(range(64)) * 4); out["corrupt"] = c
    return out
