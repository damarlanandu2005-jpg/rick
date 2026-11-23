#!/usr/bin/env python3
"""R1a regression tests: frame semantics. Run: python3 r1/test_frames.py  (no renderer needed)."""
import json, sys, tempfile, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT / "tools"))
import frames as F
fails = []
def t(name, ok):
    print(("PASS " if ok else "FAIL ") + name); (ok or fails.append(name))
def raises(fn, *a):
    try: fn(*a); return False
    except SystemExit as e: return e.code == 2
def ep(n):
    d = Path(tempfile.mkdtemp()); (d / "out/plan").mkdir(parents=True); json.dump({"frames": [{"f": i} for i in range(n)]}, open(d / "out/plan/camera_baked.json", "w")); return d
for N in (299, 460, 1):
    t("N=%d all = 0..N-1" % N, F.parse_range("all", N) == (0, N - 1))
    t("N=%d 0-%d is the full film" % (N, N - 1), F.parse_range("0-%d" % (N - 1), N) == (0, N - 1) and F.is_full(0, N - 1, N))
    t("N=%d 0-%d is an ERROR (off by one)" % (N, N), raises(F.parse_range, "0-%d" % N, N))
    t("N=%d far outside is an ERROR" % N, raises(F.parse_range, "5-%d" % (N + 100), N))
N = 299
t("partial 0-298 minus one is partial", not F.is_full(0, 297, N) and "PARTIAL" in F.scope_label(0, 297, N) and "NOT a full-film PASS" in F.scope_label(0, 297, N).replace("not a", "NOT a"))
t("partial 10-20 is partial", not F.is_full(10, 20, N))
t("full label says FULL FILM", F.scope_label(0, 298, N).startswith("FULL FILM"))
for bad in ("a-b", "5", "", "-3", "3-", "1-2-3", "10-5"): t("malformed/backwards '%s' is an ERROR" % bad, raises(F.parse_range, bad, N))
t("check_range rejects f1==N", raises(F.check_range, 0, N, N)); t("check_range rejects None", raises(F.check_range, None, 5, N)); t("check_range accepts 0..N-1", not raises(F.check_range, 0, N - 1, N))
d = ep(299); t("film_frame_count reads baked camera", F.film_frame_count(d) == 299)
t("missing baked plan is an ERROR", raises(F.film_frame_count, Path(tempfile.mkdtemp())))
d2 = ep(3); json.dump({"frames": [{"f": 0}, {"f": 2}, {"f": 3}]}, open(d2 / "out/plan/camera_baked.json", "w")); t("non-contiguous baked indices are an ERROR", raises(F.film_frame_count, d2))
fd = Path(tempfile.mkdtemp())
for i in (0, 1, 3): (fd / ("f_%05d.png" % i)).write_bytes(b"x")
t("exact_set finds missing 2 and extra 3 for 0-2", F.exact_set(fd, "f_", 0, 2) == ([2], [3]))
t("exact_set 0-1: nothing missing, frame 3 is extra (outside range)", F.exact_set(fd, "f_", 0, 1) == ([], [3]))
r = subprocess.run([sys.executable, str(ROOT / "tools/frames.py"), str(d), "0-299"], capture_output=True, text=True); t("CLI 0-299 on N=299 exits 2 with message", r.returncode == 2 and "outside the film" in r.stderr)
r = subprocess.run([sys.executable, str(ROOT / "tools/frames.py"), str(d), "0-298"], capture_output=True, text=True); t("CLI 0-298 on N=299 prints full", r.returncode == 0 and r.stdout.split() == ["0", "298", "299", "full"])
# final_video.assemble must reject an out-of-range request before touching anything
import final_video as FV
try:
    dd = ep(5); json.dump({"fps": 30}, open(dd / "film.json", "w")); FV.assemble(dd, 0, 5); ok = False
except SystemExit as e: ok = e.code == 2
except Exception: ok = False
t("final_video.assemble(0, N) -> frame range error", ok)
print("\n%d FAIL" % len(fails)); sys.exit(1 if fails else 0)
