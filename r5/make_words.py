#!/usr/bin/env python3
"""R5E: voice/words.json in the existing Ricks format ([{"w","s","e"}]). No recorded voice exists in this environment (no TTS key, no ASR), so the timing is SCRIPT-TIMED: each word gets a duration from its length,
sentence ends a short breath, then the whole track is scaled to the Ricks pace (4.0 w/s, the middle of the 3.5-4.5 gate). The R1 thresholds are NOT changed; creative_gates G2 judges these numbers like any other words.json.
When the real voice is recorded, voice_prep.py replaces this file and the plan is re-baked (every artifact then goes stale by hash, as it should)."""
import json, re, sys
from pathlib import Path
ep = Path(__file__).resolve().parent / "episode"; txt = [l for l in (ep / "creative/SCRIPT.md").read_text().splitlines() if l and not l.startswith(("#", "Format", "Understandable", "Setup", "Cast"))]
words = " ".join(txt).split(); TARGET = 4.0
raw = []; t = 0.0
for w in words:
    d = 0.10 + 0.045 * len(re.sub(r"\W", "", w)); raw.append([w, t, t + d]); t += d + (0.26 if re.search(r"[.?!]$", w) else 0.05)
span = raw[-1][2]; k = (len(words) / TARGET) / span
out = [{"w": w, "s": round(s * k, 3), "e": round(e * k, 3)} for w, s, e in raw]
(ep / "voice").mkdir(exist_ok=True); json.dump(out, open(ep / "voice/words.json", "w"), indent=0)
print(len(out), "words, %.2f s, %.2f w/s" % (out[-1]["e"], len(out) / (out[-1]["e"] - out[0]["s"])), "longest gap %.2f" % max(b["s"] - a["e"] for a, b in zip(out, out[1:])))
