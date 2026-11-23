#!/usr/bin/env python3
"""Creative gates G1-G8 (blueprint section 18), enforced before any expensive render. R1: structural, honest checks.
  python3 tools/creative_gates.py <ep> [--json]      exit 1 if any gate FAILs (SKIP is reported, never counted as a pass)

Episode layout (R1 implementation detail, class C; documented in docs/IMPLEMENTATION.md):
  <ep>/film.json  <ep>/voice/words.json (film.json "words" may override)  <ep>/creative/SCRIPT.md  PICTURE_PLAN.md  LOOK_BIBLE.md
  <ep>/creative/reference_board.json   {"beats":[{"id","kind","frames":[>=2 refs]}], "department_index":{dept: note}}
  <ep>/creative/characters.json        {"check_views":"PASS","casting":{char: note},"sheets":[files]}   (a recorded result: check_views.mjs writes golden files, so it is not auto-run here)
  <ep>/creative/STORYBOARD.json  ANIMATIC.json  JUDGE.json   (built by R2; until then G8 FAILs and no production approval can be issued)
A gate is PASS, FAIL, or SKIP(reason). The thresholds below are R1 choices where the blueprint says only "in bands" / "no long gaps"; they are named so the owner can change them."""
import json, re, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parent
WS_MIN, WS_MAX, MAX_GAP_S, MAX_WARN, MIN_REFS = 3.5, 4.5, 1.5, 2, 2
VERDICT = {"CLOSE", "IN SCENE", "NOT SHOWN"}
def _words_path(ep):
    f = Path(ep) / "film.json"; w = json.load(open(f)).get("words", "voice/words.json") if f.exists() else "voice/words.json"; return Path(ep) / w
def g1(ep):
    p = Path(ep) / "creative/SCRIPT.md"
    if not p.is_file() or len(p.read_text().split()) < 20: return "FAIL", "creative/SCRIPT.md missing or empty"
    return "PASS", "script present; band check (script_stats) and 'first line is an action' are human-reviewed, recorded in approval.json approvals.creative"
def g2(ep):
    p = _words_path(ep)
    if not p.is_file(): return "FAIL", "%s missing" % p.name
    W = json.load(open(p))
    if len(W) < 2: return "FAIL", "words.json has %d words" % len(W)
    dur = W[-1]["e"] - W[0]["s"]; ws = len(W) / dur if dur > 0 else 0; gaps = [(W[i + 1]["s"] - W[i]["e"], i) for i in range(len(W) - 1)]; g = max(gaps)
    bad = []
    if not WS_MIN <= ws <= WS_MAX: bad.append("%.2f w/s outside %.1f-%.1f" % (ws, WS_MIN, WS_MAX))
    if g[0] > MAX_GAP_S: bad.append("gap %.2f s after word #%d > %.1f s" % (g[0], g[1], MAX_GAP_S))
    return ("FAIL", "; ".join(bad)) if bad else ("PASS", "%.2f w/s, longest gap %.2f s" % (ws, g[0]))
def g3(ep):
    p = Path(ep) / "creative/reference_board.json"
    if not p.is_file(): return "FAIL", "creative/reference_board.json missing"
    B = json.load(open(p)); beats = B.get("beats") or []; bad = ["beat %s has %d refs" % (b.get("id", "?"), len(b.get("frames") or [])) for b in beats if len(b.get("frames") or []) < MIN_REFS]
    if not beats: bad.append("no beats")
    if not B.get("department_index"): bad.append("department_index empty")
    return ("FAIL", "; ".join(bad[:6])) if bad else ("PASS", "%d beats, each >= %d refs, department index filled" % (len(beats), MIN_REFS))
def g4(ep):
    p = Path(ep) / "creative/PICTURE_PLAN.md"
    if not p.is_file(): return "FAIL", "creative/PICTURE_PLAN.md missing"
    rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in p.read_text().splitlines() if re.match(r"\|\s*\d+", l)]; bad = []
    for r in rows:
        if len(r) < 5: bad.append("row %s malformed" % r[0]); continue
        m = re.match(r"(CLOSE|IN SCENE|NOT SHOWN)\b[\s:,.\-]*(.*)", r[4], re.I)
        if not m or m.group(1).upper() not in VERDICT: bad.append("row %s: shown cell must start CLOSE / IN SCENE / NOT SHOWN" % r[0])
        elif len(m.group(2).split()) < 3: bad.append("row %s: no reason given" % r[0])
    txt = p.read_text().upper(); [bad.append("no %s row marked" % k) for k in ("HOOK", "TWIST", "LAST") if k not in txt]
    if not rows: bad.append("no table rows")
    return ("FAIL", "; ".join(bad[:6])) if bad else ("PASS", "%d rows, each with a verdict and reason; HOOK/TWIST/LAST marked" % len(rows))
def g5(ep):
    r = subprocess.run([sys.executable, str(HERE / "film_plan.py"), "check", str(Path(ep) / "film.json")], capture_output=True, text=True); last = (r.stdout.strip().splitlines() or [""])[-1]; m = re.search(r"(\d+) FAIL, (\d+) WARN", last)
    if r.returncode or not m: return "FAIL", last[:90] or r.stderr[-120:]
    f, w = int(m.group(1)), int(m.group(2))
    return ("PASS", last[:60]) if f == 0 and w <= MAX_WARN else ("FAIL", "%d FAIL, %d WARN (allowed: 0 FAIL, <= %d WARN with reasons)" % (f, w, MAX_WARN))
def g6(ep):
    p = Path(ep) / "creative/characters.json"
    if not p.is_file(): return "FAIL", "creative/characters.json missing (record the check_views.mjs PASS and the casting)"
    C = json.load(open(p)); bad = []
    if C.get("check_views") != "PASS": bad.append("check_views is not recorded PASS")
    if not C.get("casting"): bad.append("casting empty")
    miss = [s for s in C.get("sheets", []) if not (Path(ep) / s).is_file()]
    if not C.get("sheets"): bad.append("no character sheets listed")
    if miss: bad.append("sheet files missing: %s" % miss[:3])
    return ("FAIL", "; ".join(bad)) if bad else ("PASS", "recorded check_views PASS (attestation; not re-run here), casting and %d sheets present" % len(C["sheets"]))
def g7(ep):
    r = subprocess.run([sys.executable, str(HERE / "assets.py"), "check"], capture_output=True, text=True)
    return ("SKIP", "registry OK; glb presence, density gates and five-details-per-object need the asset seam (R4)") if r.returncode == 0 else ("FAIL", (r.stdout + r.stderr).strip()[-120:])
def g8(ep):
    miss = [n for n in ("STORYBOARD.json", "ANIMATIC.json", "JUDGE.json") if not (Path(ep) / "creative" / n).is_file()]
    return ("FAIL", "not built (R2): %s" % ", ".join(miss)) if miss else ("PASS", "storyboard, animatic and judge record present")
GATES = [("G1", "Script", g1), ("G2", "Words", g2), ("G3", "Reference board", g3), ("G4", "Picture plan", g4), ("G5", "Plan", g5), ("G6", "Characters", g6), ("G7", "Assets/sets", g7), ("G8", "Rough gate", g8)]
def run(ep): return [dict(gate=g, name=n, status=s, note=t) for g, n, fn in GATES for s, t in [fn(ep)]]
if __name__ == "__main__":
    ep = sys.argv[1]; R = run(ep)
    if "--json" in sys.argv: print(json.dumps(R, indent=1))
    else: [print("%-3s %-16s %-5s %s" % (r["gate"], r["name"], r["status"], r["note"])) for r in R]
    nf = sum(r["status"] == "FAIL" for r in R); print("CREATIVE GATES: %d FAIL, %d SKIP, %d PASS" % (nf, sum(r["status"] == "SKIP" for r in R), sum(r["status"] == "PASS" for r in R))); sys.exit(1 if nf else 0)
