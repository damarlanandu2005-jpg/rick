#!/usr/bin/env python3
"""Frame semantics (blueprint section 19, R1). ONE definition used by the pipeline, final assembly and QA.

For a film of N frames (N = len(out/plan/camera_baked.json frames) = film.json `end`, in frames) the valid indices are 0..N-1.
  --frames all        = 0..N-1 (the full film)
  --frames a-b        = inclusive; 0 <= a <= b <= N-1.  b >= N is an ERROR (never clamped, never rendered).
  --frames 0-(N-1)    = the full film
Any partial range is never reported as a full-film PASS (scope_label()). Full-film validators check the EXACT expected frame set.

  python3 tools/frames.py <ep> <spec>      prints "f0 f1 N full|partial" or exits 2 with the reason"""
import json, re, sys
from pathlib import Path
class FrameError(SystemExit):
    """SystemExit with exit code 2; str(e) is the message. Entry points print it (pipeline/QA/final_video let it propagate and the CLI wrappers print it)."""
    def __init__(self, msg): super().__init__(2); self.msg = "FRAME RANGE ERROR: " + msg
    def __str__(self): return self.msg
def film_frame_count(ep):
    """N for an episode: the baked camera frames, which must be exactly the indices 0..N-1."""
    p = Path(ep) / "out/plan/camera_baked.json"
    if not p.exists(): raise FrameError("%s is missing: run `film_plan.py check` first (the frame count comes from the baked plan)" % p)
    fr = json.load(open(p))["frames"]; idx = [r.get("f", i) for i, r in enumerate(fr)] if fr and isinstance(fr[0], dict) else list(range(len(fr)))
    if idx != list(range(len(fr))): raise FrameError("camera_baked.json frame indices are not exactly 0..%d" % (len(fr) - 1))
    if not fr: raise FrameError("camera_baked.json has no frames")
    return len(fr)
def parse_range(spec, n):
    """-> (f0, f1) inclusive. 'all' = (0, n-1). Raises FrameError for anything outside 0..n-1."""
    if n < 1: raise FrameError("film has %d frames" % n)
    if spec is None or str(spec).strip().lower() == "all": return 0, n - 1
    m = re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*", str(spec))
    if not m: raise FrameError("'%s' is not 'all' or 'a-b' (two non-negative integers)" % spec)
    a, b = int(m.group(1)), int(m.group(2))
    if a > b: raise FrameError("range %d-%d runs backwards" % (a, b))
    if b >= n: raise FrameError("range %d-%d is outside the film: it has %d frames, valid indices are 0..%d (the full film is 0-%d)" % (a, b, n, n - 1, n - 1))
    return a, b
def check_range(f0, f1, n):
    """Validate an already-parsed (f0, f1) from a caller (final_video, qa)."""
    if f0 is None or f1 is None or not (0 <= f0 <= f1 <= n - 1): raise FrameError("frames %s-%s are outside the film (valid 0..%d)" % (f0, f1, n - 1))
def is_full(f0, f1, n): return f0 == 0 and f1 == n - 1
def scope_label(f0, f1, n):
    """The words every report must carry, so a partial run can never read as a full-film PASS."""
    return "FULL FILM (frames 0-%d)" % (n - 1) if is_full(f0, f1, n) else "PARTIAL RANGE %d-%d of 0-%d: full-film checks were NOT run, this is not a full-film PASS" % (f0, f1, n - 1)
def exact_set(folder, pattern_prefix, f0, f1, suffix=".png"):
    """Return (missing, extra) index lists of folder/<prefix>NNNNN<suffix> against the expected f0..f1."""
    have = set()
    for q in Path(folder).glob(pattern_prefix + "*" + suffix):
        m = re.fullmatch(re.escape(pattern_prefix) + r"(\d+)" + re.escape(suffix), q.name)
        if m: have.add(int(m.group(1)))
    want = set(range(f0, f1 + 1)); return sorted(want - have), sorted(have - want)
if __name__ == "__main__":
    try: ep, spec = sys.argv[1], sys.argv[2]; n = film_frame_count(ep); f0, f1 = parse_range(spec, n); print(f0, f1, n, "full" if is_full(f0, f1, n) else "partial")
    except FrameError as e: print(e, file=sys.stderr); sys.exit(2)
