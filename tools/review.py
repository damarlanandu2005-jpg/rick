#!/usr/bin/env python3
"""R2: creative review stage (blueprint sections 14 and 18, gate G8). Reuses the Ricks storyboard/animatic tools (render.mjs --storyboard / --animatic) and the Ricks
storyboard-judge + studio-director agents; invents no planning, camera or timing schema. Every artifact is tied to the plan (film.json sha1) and the baked plan.
  review.py storyboard <ep> [--version N] [--builder CTX]            render.mjs --storyboard -> creative/STORYBOARD.json (stations derived from camera_baked.json, panels hashed)
  review.py animatic   <ep> [--step 3] [--hook-seconds 3] [--builder CTX]   render.mjs --animatic -> out/animatic.mp4 (whole-film rough) + out/animatic_hook.mp4 (hook-partial) -> creative/ANIMATIC.json
  review.py judge-brief <ep>                                        writes creative/JUDGE_BRIEF.md: what a FRESH-context judge reads and the result format
  review.py judge-record <ep> <result.json>                         validates the judge's panel scores, COMPUTES PASS/FAIL (>= 8.5 on every panel), enforces the one-fix-round rule -> creative/JUDGE.json
  review.py check <ep>                                              G8, verbose (exit 1 on FAIL)
  review.py new-version <ep> --owner NAME --reason TEXT             owner-only reset after the fix round is exhausted (archives the history; never run by the pipeline)
The judge is review evidence. It never writes approval.json; the human owner does (tools/approval.py create)."""
import argparse, datetime, hashlib, json, re, shutil, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parent; sys.path.insert(0, str(HERE)); import approval as AP, frames as FR
THRESHOLD = 8.5; MAX_JUDGED = 2          # one judged version + at most ONE fix round (blueprint section 14)
HOOK_S = 3.0; STEP = 3
SB, AN, JD, HIST = "STORYBOARD.json", "ANIMATIC.json", "JUDGE.json", "review_history.json"
now = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
def sha(p): return hashlib.sha1(Path(p).read_bytes()).hexdigest()
def cdir(ep): return Path(ep) / "creative"
def load(p):
    try: return json.load(open(p)), None
    except FileNotFoundError: return None, "missing"
    except Exception as e: return None, "malformed (%s)" % str(e)[:60]
def plan_hashes(ep):
    H = AP.current(ep); return H["plan_sha1"], H["baked_sha1"]
def derive_stations(ep):
    """Deterministic stations from the baked camera: one per (take, station); START = first rest frame, END = last rest frame (a pass without rest shows its first frame), as film.js window.stations()."""
    fr = json.load(open(Path(ep) / "out/plan/camera_baked.json"))["frames"]; g = {}
    for c in fr: g.setdefault((c["take"], c["station"]), []).append(c)
    out = []
    for i, ((take, st), cs) in enumerate(g.items(), 1):
        rest = [c["f"] for c in cs if c.get("state") == "rest"] or [cs[0]["f"]]
        out.append(dict(id="s%02d" % i, take=take, station=st, start=rest[0], end=rest[-1], framing=cs[0].get("framing"), lens=cs[0].get("lens"), passes=not [1 for c in cs if c.get("state") == "rest"]))
    return out
def panel_ids(S): return [p["id"] for p in S["panels"]]
def required_panels(ep, S):
    """Every storyboard panel plus one character panel per film.json cast slot (R3I): the judge scores the characters with the same Ricks storyboard-judge framework (role, reference board, consistency, outfit, readable at 720x1280, expressions, staging)."""
    cast = json.load(open(Path(ep) / "film.json")).get("cast") or {}; return panel_ids(S) + ["char_%s" % k for k in cast]
def char_sha(ep):
    import characters as CH; return CH.evidence_sha(ep)
# ---------------- R2A storyboard
def make_storyboard_doc(ep, version=1, builder="builder", panel_dir=None):
    """Pure (no rendering): the storyboard document from the baked plan and the panel PNGs render.mjs --storyboard wrote."""
    ep = Path(ep); ph, bh = plan_hashes(ep); n = FR.film_frame_count(ep); st = derive_stations(ep); pd = Path(panel_dir or ep / "out/storyboard_panels"); panels = []
    for s in st:
        for kind, f in (("start", s["start"]), ("end", s["end"])):
            m = sorted(pd.glob("%s_%s_f%d.png" % (s["id"], kind, f)))
            if not m: raise SystemExit("storyboard panel missing for %s %s frame %d in %s" % (s["id"], kind, f, pd))
            panels.append(dict(id="%s_%s" % (s["id"], kind), station=s["id"], kind=kind.upper(), frame=f, file=str(m[0].relative_to(ep)), sha1=sha(m[0])))
    return dict(schema="ricks.storyboard.v1", film=json.load(open(ep / "film.json")).get("title") or ep.name, version=version, plan_sha1=ph, baked_sha1=bh, n_frames=n, fps=json.load(open(ep / "out/plan/camera_baked.json"))["fps"], built_by=dict(tool="render.mjs --storyboard", context_id=builder), stations=st, panels=panels)
def validate_storyboard(ep):
    ep = Path(ep); S, e = load(cdir(ep) / SB)
    if e: return None, ["storyboard %s (creative/%s)" % (e, SB)]
    bad = []
    for k in ("schema", "film", "version", "plan_sha1", "baked_sha1", "n_frames", "fps", "built_by", "stations", "panels"):
        if k not in S: bad.append("malformed: field %s missing" % k)
    if bad or S["schema"] != "ricks.storyboard.v1" or not isinstance(S["stations"], list) or not isinstance(S["panels"], list) or not S["panels"] or not isinstance(S.get("built_by"), dict) or not S["built_by"].get("context_id"): return S, bad + ["malformed storyboard"] if not bad else bad
    ph, bh = plan_hashes(ep)
    if S["plan_sha1"] != ph: bad.append("STALE: storyboard was generated from a different film.json (wrong plan)")
    if S["baked_sha1"] != bh: bad.append("STALE: baked plan changed since the storyboard")
    try: N = FR.film_frame_count(ep); st = derive_stations(ep)
    except SystemExit as x: return S, bad + [str(x)]
    if S["n_frames"] != N: bad.append("storyboard n_frames %s != film %d" % (S["n_frames"], N))
    if [(s["take"], s["station"], s["start"], s["end"]) for s in S["stations"]] != [(s["take"], s["station"], s["start"], s["end"]) for s in st]: bad.append("storyboard stations do not match the baked camera")
    ids = set(panel_ids(S))
    for s in st:
        for k in ("start", "end"):
            if "%s_%s" % (s["id"], k) not in ids: bad.append("no %s panel for station %s" % (k.upper(), s["id"]))
    for p in S["panels"]:
        f = ep / p.get("file", "")
        if not p.get("file") or not f.is_file(): bad.append("panel file missing: %s" % p.get("id")); continue
        if sha(f) != p.get("sha1"): bad.append("panel %s file changed after the storyboard was recorded" % p["id"])
        if not (0 <= p.get("frame", -1) < N): bad.append("panel %s frame outside 0..%d" % (p["id"], N - 1))
    return S, bad
# ---------------- R2B animatic
def _count_frames(mp4):
    r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(mp4)], capture_output=True, text=True)
    try: return int(r.stdout.strip().split()[0])
    except Exception: return -1
def expected_set(first, last, step): return list(range(first, last + 1, step))
def make_animatic_doc(ep, whole_mp4, hook_mp4, step=STEP, hook_s=HOOK_S, builder="builder"):
    ep = Path(ep); ph, bh = plan_hashes(ep); N = FR.film_frame_count(ep); fps = json.load(open(ep / "out/plan/camera_baked.json"))["fps"]; hk = min(N - 1, int(round(hook_s * fps)) - 1)
    def art(kind, mp4, first, last):
        return dict(kind=kind, video=str(Path(mp4).relative_to(ep)), video_sha1=sha(mp4), video_frames=_count_frames(mp4), frames_per_sample=step, frame_set=dict(first=first, last=last, step=step, count=len(expected_set(first, last, step))), covers_whole_film=(first == 0 and last == N - 1), label=("WHOLE-FILM ROUGH, frames 0-%d" % (N - 1)) if kind == "whole-film-rough" else "HOOK-PARTIAL, frames %d-%d of 0-%d: NOT a full-film review" % (first, last, N - 1))
    return dict(schema="ricks.animatic.v1", film=json.load(open(ep / "film.json")).get("title") or ep.name, plan_sha1=ph, baked_sha1=bh, n_frames=N, fps=fps, built_by=dict(tool="render.mjs --animatic", context_id=builder), artifacts=[art("whole-film-rough", whole_mp4, 0, N - 1), art("hook-partial", hook_mp4, 0, hk)])
def validate_animatic(ep):
    ep = Path(ep); A, e = load(cdir(ep) / AN)
    if e: return None, ["animatic %s (creative/%s)" % (e, AN)]
    bad = []
    for k in ("schema", "film", "plan_sha1", "baked_sha1", "n_frames", "fps", "built_by", "artifacts"):
        if k not in A: bad.append("malformed: field %s missing" % k)
    if bad or A["schema"] != "ricks.animatic.v1" or not isinstance(A["artifacts"], list) or not isinstance(A.get("built_by"), dict) or not A["built_by"].get("context_id"): return A, bad or ["malformed animatic"]
    ph, bh = plan_hashes(ep)
    if A["plan_sha1"] != ph: bad.append("STALE: animatic was made from a different film.json (wrong plan)")
    if A["baked_sha1"] != bh: bad.append("STALE: baked plan (camera/timing) changed since the animatic")
    try: N = FR.film_frame_count(ep)
    except SystemExit as x: return A, bad + [str(x)]
    if A["n_frames"] != N: bad.append("animatic n_frames %s != film %d" % (A["n_frames"], N))
    kinds = {}
    for a in A["artifacts"]:
        k = a.get("kind"); kinds[k] = a
        try: fs = a["frame_set"]; first, last, step = fs["first"], fs["last"], fs["step"]; assert 0 <= first <= last <= N - 1 and step >= 1
        except Exception: bad.append("%s: frame_set malformed or outside 0..%d (wrong frame set)" % (k, N - 1)); continue
        whole = first == 0 and last == N - 1
        if k == "whole-film-rough" and not whole: bad.append("whole-film-rough does not cover frames 0-%d (wrong frame set)" % (N - 1))
        if k == "hook-partial" and (whole or "NOT a full-film" not in a.get("label", "")): bad.append("hook-partial must be a strict part of the film and labelled NOT a full-film review")
        if k not in ("whole-film-rough", "hook-partial"): bad.append("unknown animatic kind %r" % k)
        if a.get("covers_whole_film") != whole: bad.append("%s: covers_whole_film is wrong" % k)
        v = ep / a.get("video", "")
        if not a.get("video") or not v.is_file(): bad.append("%s: video file missing" % k); continue
        if sha(v) != a.get("video_sha1"): bad.append("%s: video changed after it was recorded" % k)
        exp = len(expected_set(first, last, step)) * step   # render.mjs --animatic holds each sampled frame `step` video frames (-r fps), so the video length stays real time
        if a.get("video_frames") != exp or _count_frames(v) != exp: bad.append("%s: video has %s frames, the frame set %d-%d step %d expects %d (wrong frame set)" % (k, _count_frames(v), first, last, step, exp))
    if "whole-film-rough" not in kinds: bad.append("no whole-film rough: a hook alone is not a full-film review")
    if "hook-partial" not in kinds: bad.append("no hook animatic")
    return A, bad
# ---------------- R2C/R2D judge
def history(ep):
    H, e = load(cdir(ep) / HIST); return (H if isinstance(H, list) else []) if not (e and e != "missing") else None
def judge_validate_input(ep, R, S, A):
    """The judge's raw result (a dict) -> problems. The judge supplies scores and reasons only; PASS/FAIL is computed here."""
    bad = []; J = R.get("judge") or {}
    for k in ("id", "context_id"): J.get(k) or bad.append("judge.%s missing" % k)
    builders = {S["built_by"]["context_id"], A["built_by"]["context_id"]}
    if J.get("context_id") in builders: bad.append("judge context_id equals a builder context: the judge must run in a fresh context and cannot judge its own work")
    if J.get("id") in builders: bad.append("judge id equals a builder id")
    er = R.get("evidence_read") or {}
    sbh, anh, chh = sha(cdir(ep) / SB), sha(cdir(ep) / AN), char_sha(ep)
    if er.get("storyboard_sha1") != sbh or er.get("animatic_sha1") != anh: bad.append("judge did not read the current storyboard/animatic (evidence_read hashes differ)")
    if chh is None or er.get("characters_sha1") != chh: bad.append("judge did not read the current character evidence (characters_sha1 differs or the characters are not built)")
    P = R.get("panels") or {}; need = set(required_panels(ep, S))
    if set(P) != need: bad.append("panel set differs: missing %s extra %s" % (sorted(need - set(P))[:4], sorted(set(P) - need)[:4]))
    for k, v in P.items():
        try: ok = 0 <= float(v["score"]) <= 10 and str(v.get("rationale", "")).strip()
        except Exception: ok = False
        if not ok: bad.append("panel %s: score (0-10) and rationale required" % k)
    if (R.get("film_level") or {}).get("verdict") not in ("PASS", "FAIL"): bad.append("film_level.verdict must be PASS or FAIL")
    if (R.get("studio_director") or {}).get("verdict") not in ("PASS", "BACK"): bad.append("studio_director.verdict must be PASS or BACK")
    return bad
def compute_result(R, S):
    P = R["panels"]; low = {k: v["score"] for k, v in P.items() if float(v["score"]) < THRESHOLD}
    ok = not low and R["film_level"]["verdict"] == "PASS" and R["studio_director"]["verdict"] == "PASS"
    return ("PASS" if ok else "FAIL"), low
def judge_record(ep, resfile):
    ep = Path(ep); S, b1 = validate_storyboard(ep); A, b2 = validate_animatic(ep)
    if b1 or b2: sys.exit("REFUSED: the evidence is not valid, nothing to judge: " + "; ".join(b1 + b2)[:300])
    R = json.load(open(resfile)); bad = judge_validate_input(ep, R, S, A)
    if bad: sys.exit("REFUSED: " + "; ".join(bad)[:500])
    H = history(ep)
    if H is None: sys.exit("REFUSED: review_history.json is malformed")
    if len(H) >= MAX_JUDGED: sys.exit("REFUSED (fail closed): %d judged versions already; the one permitted fix round is used. Only the owner can open a new version (review.py new-version)." % len(H))
    key = (S["plan_sha1"], sha(cdir(ep) / SB), sha(cdir(ep) / AN))
    if H and H[-1]["result"] == "PASS": sys.exit("REFUSED: the last judged version already PASSED; the human approval step is next (judge again only after a creative change)") if (H[-1]["plan_sha1"], H[-1]["storyboard_sha1"], H[-1]["animatic_sha1"]) == key else None
    if H and (H[-1]["plan_sha1"], H[-1]["storyboard_sha1"], H[-1]["animatic_sha1"]) == key: sys.exit("REFUSED: nothing changed since the failed judgment; a fix round must change the work")
    res, low = compute_result(R, S); fix_round = sum(1 for h in H if h["result"] == "FAIL"); ts = now(); fixes = json.dumps({k: v.get("fix") for k, v in R["panels"].items() if v.get("fix")}, sort_keys=True)
    J = dict(schema="ricks.judge.v1", film=S["film"], version=S["version"], fix_round=fix_round, plan_sha1=S["plan_sha1"], baked_sha1=S["baked_sha1"], storyboard_sha1=key[1], animatic_sha1=key[2], characters_sha1=char_sha(ep), judge=R["judge"], builders=sorted({S["built_by"]["context_id"], A["built_by"]["context_id"]}), evidence_read=R["evidence_read"], timestamp=ts,
             threshold=THRESHOLD, panels=R["panels"], film_level=R["film_level"], studio_director=R["studio_director"], min_panel_score=min(float(v["score"]) for v in R["panels"].values()), below_threshold=low, result=res,
             reviewer=R["judge"]["id"], score={k: float(v["score"]) for k, v in R["panels"].items()}, verdict=res, fix_list_sha1=hashlib.sha1(fixes.encode()).hexdigest())   # last four: the fields approval.json copies (section 19)
    (cdir(ep) / JD).write_text(json.dumps(J, indent=1)); H.append(dict(version=S["version"], fix_round=fix_round, plan_sha1=key[0], storyboard_sha1=key[1], animatic_sha1=key[2], result=res, judge_context_id=R["judge"]["context_id"], timestamp=ts)); (cdir(ep) / HIST).write_text(json.dumps(H, indent=1))
    print("judge recorded: %s (fix round %d, min panel %.1f, threshold %.1f)%s" % (res, fix_round, J["min_panel_score"], THRESHOLD, "" if res == "PASS" else "  fix list in creative/JUDGE.json"))
    return res
def new_version(ep, owner, reason):
    ep = Path(ep); H = history(ep) or []; arch = cdir(ep) / ("review_history_archive_%s.json" % now().replace(":", "")); arch.write_text(json.dumps(dict(owner=owner, reason=reason, at=now(), history=H), indent=1)); (cdir(ep) / HIST).write_text("[]"); print("owner", owner, "opened a new version; old history archived in", arch.name)
# ---------------- R2E G8
def g8_problems(ep):
    """The eleven G8 checks. Returns (problems, info)."""
    ep = Path(ep); bad = []; S, b = validate_storyboard(ep); bad += ["[1-3 storyboard] " + x for x in b]; A, b = validate_animatic(ep); bad += ["[4-6 animatic] " + x for x in b]
    J, e = load(cdir(ep) / JD)
    if e: return bad + ["[7 judge] judge record %s (creative/%s)" % (e, JD)], None
    if S is None or A is None or "built_by" not in (S or {}) or "built_by" not in (A or {}): return bad + ["[7 judge] cannot verify the judge without a valid storyboard and animatic"], J
    try:
        for k in ("judge", "panels", "film_level", "studio_director", "evidence_read", "fix_round", "plan_sha1", "storyboard_sha1", "animatic_sha1", "baked_sha1", "characters_sha1"): J[k]
    except Exception: return bad + ["[7 judge] judge record malformed"], J
    ph, bh = plan_hashes(ep)
    if (J["plan_sha1"], J["baked_sha1"]) != (ph, bh): bad.append("[11 stale] judge record is for a different plan/baked plan")
    if J["storyboard_sha1"] != sha(cdir(ep) / SB) or J["animatic_sha1"] != sha(cdir(ep) / AN): bad.append("[11 stale] judge record is for a different storyboard/animatic")
    if J["characters_sha1"] != char_sha(ep): bad.append("[11 stale] judge record is for different character evidence")
    builders = {S["built_by"]["context_id"], A["built_by"]["context_id"]}
    if J["judge"].get("context_id") in builders or J["judge"].get("id") in builders or not J["judge"].get("context_id"): bad.append("[8 independence] judge shares a context/identity with the builder")
    if J["evidence_read"].get("storyboard_sha1") != J["storyboard_sha1"] or J["evidence_read"].get("animatic_sha1") != J["animatic_sha1"] or J["evidence_read"].get("characters_sha1") != J["characters_sha1"]: bad.append("[8 independence] judge did not read the evidence it scored")
    P = J["panels"]; need = set(required_panels(ep, S)) if S.get("panels") else set()
    if set(P) != need: bad.append("[9 scores] required panel set differs: missing %s" % sorted(need - set(P))[:4])
    low = []
    for k in need & set(P):
        try: sc = float(P[k]["score"])
        except Exception: sc = -1
        if sc < THRESHOLD: low.append("%s=%s" % (k, P[k].get("score") if isinstance(P[k], dict) else "?"))
    if low: bad.append("[9 scores] panels below %.1f: %s" % (THRESHOLD, ", ".join(low[:8])))
    if J["film_level"].get("verdict") != "PASS": bad.append("[9 scores] film-level verdict is not PASS")
    if J["studio_director"].get("verdict") != "PASS": bad.append("[9 scores] studio-director verdict is not PASS")
    if J.get("result") != "PASS" or J.get("verdict") != "PASS": bad.append("[9 scores] judge result is %s" % J.get("result"))
    H = history(ep)
    if H is None or not H: bad.append("[10 fix-round] review_history.json missing or malformed")
    else:
        fails = [h for h in H if h["result"] == "FAIL"]
        if len(H) > MAX_JUDGED or len(fails) >= MAX_JUDGED: bad.append("[10 fix-round] %d judged versions / %d failures: more than one fix round" % (len(H), len(fails)))
        elif J["fix_round"] != len([h for h in H[:-1] if h["result"] == "FAIL"]) or J["fix_round"] > 1: bad.append("[10 fix-round] judge record fix_round %s does not match the history" % J["fix_round"])
        elif (H[-1]["storyboard_sha1"], H[-1]["animatic_sha1"], H[-1]["plan_sha1"], H[-1]["result"]) != (J["storyboard_sha1"], J["animatic_sha1"], J["plan_sha1"], J["result"]): bad.append("[10 fix-round] judge record is not the latest history entry")
    return bad, J
def g8(ep):
    bad, J = g8_problems(ep)
    return ("FAIL", "; ".join(bad)[:700]) if bad else ("PASS", "storyboard + whole-film rough + hook valid and current; judge %s fresh-context, every panel >= %.1f (min %.1f), fix round %d" % (J["judge"]["id"], THRESHOLD, J["min_panel_score"], J["fix_round"]))
# ---------------- CLI
def run_node(ep, *args):
    r = subprocess.run(["node", str(ROOT / "templates/threejs_film/render.mjs"), str(Path(ep) / "film.json"), *args], capture_output=True, text=True)
    if r.returncode: sys.exit("render.mjs %s failed:\n%s" % (" ".join(args), (r.stdout + r.stderr)[-600:]))
    return r
def need_plan(ep):
    r = subprocess.run([sys.executable, str(HERE / "film_plan.py"), "check", str(Path(ep) / "film.json")], capture_output=True, text=True)
    if r.returncode: sys.exit("film_plan check failed; bake the plan first:\n" + r.stdout[-300:])
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["storyboard", "animatic", "judge-brief", "judge-record", "check", "new-version"]); ap.add_argument("ep"); ap.add_argument("result", nargs="?")
    ap.add_argument("--version", type=int, default=1); ap.add_argument("--builder", default="builder"); ap.add_argument("--step", type=int, default=STEP); ap.add_argument("--hook-seconds", type=float, default=HOOK_S); ap.add_argument("--owner"); ap.add_argument("--reason"); a = ap.parse_args(); ep = Path(a.ep); cdir(ep).mkdir(exist_ok=True)
    if a.cmd == "storyboard":
        need_plan(ep); run_node(ep, "--storyboard"); (cdir(ep) / SB).write_text(json.dumps(make_storyboard_doc(ep, a.version, a.builder), indent=1)); print("creative/%s written (%d panels)" % (SB, len(json.load(open(cdir(ep) / SB))["panels"])))
    elif a.cmd == "animatic":
        need_plan(ep); out = ep / "out"; run_node(ep, "--animatic", "--step", str(a.step)); mp4 = out / "animatic.mp4"; hook = out / "animatic_hook.mp4"; fps = json.load(open(out / "plan/camera_baked.json"))["fps"]; k = max(1, int(-(-a.hook_seconds * fps // a.step)))   # sampled frames in the hook
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp4), "-frames:v", str(k * a.step), "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(hook)], capture_output=True, text=True)
        if r.returncode: sys.exit("ffmpeg hook trim failed: " + r.stderr[-300:])
        D = make_animatic_doc(ep, mp4, hook, a.step, a.hook_seconds, a.builder); h = D["artifacts"][1]["frame_set"]; h["last"] = (k - 1) * a.step; h["count"] = k; D["artifacts"][1]["label"] = "HOOK-PARTIAL, frames 0-%d of 0-%d: NOT a full-film review" % (h["last"], D["n_frames"] - 1); D["artifacts"][1]["video_frames"] = _count_frames(hook); (cdir(ep) / AN).write_text(json.dumps(D, indent=1)); print("creative/%s written: %s | %s" % (AN, D["artifacts"][0]["label"], D["artifacts"][1]["label"]))
    elif a.cmd == "judge-brief":
        S, b1 = validate_storyboard(ep); A, b2 = validate_animatic(ep)
        if b1 or b2: sys.exit("evidence not valid: " + "; ".join(b1 + b2)[:300])
        (cdir(ep) / "JUDGE_BRIEF.md").write_text("""# Judge brief: %s (version %s)
Run in a FRESH context (a new agent that has not seen the build): Ricks `storyboard-judge` (panels) then `studio-director` (film-level verdict). Do not invent a quality framework; use ricks_reference/agents/storyboard-judge.md and rules/dept/*.md.
Evidence (read these, score the PICTURES): storyboard `creative/STORYBOARD.json` (sha1 %s) with panel PNGs %s; whole-film rough `%s`; hook `%s` (animatic sha1 %s). Also SCRIPT.md, PICTURE_PLAN.md, LOOK_BIBLE.md, reference_board.json, out/plan/plan_report.md.
Builder contexts (you must NOT be one of them): %s.
Write result.json: {"judge": {"id": "...", "context_id": "<your own fresh context id>", "kind": "fresh-context", "agents": ["storyboard-judge","studio-director"]},
 "evidence_read": {"storyboard_sha1": "%s", "animatic_sha1": "%s", "characters_sha1": "%s"},
 "panels": {%s},   // one entry per required panel id: {"score": 0-10, "rationale": "...", "fix": "one concrete fix"}
 "film_level": {"verdict": "PASS|FAIL", "notes": "..."}, "studio_director": {"verdict": "PASS|BACK", "note": "..."}}
Character panels (char_<slot>): look at creative/characters/CONTACT_SHEET.png (four views + sample cards per slot), creative/characters.json (role, traits, outfit, reference beats) and creative/character_production.json; score with the same storyboard-judge framework: does the character match the role, match the reference board, stay consistent across views and cards, wear the right outfit, read at 720x1280 phone size, perform expressions that support the story, and is it staged as the picture plan says. Required panel ids: %s. Target: 8.5+ on EVERY required panel. Then run: python3 tools/review.py judge-record <ep> result.json (PASS/FAIL is computed, not declared). You never write approval.json.
""" % (S["film"], S["version"], sha(cdir(ep) / SB), "creative -> " + ", ".join(sorted({str(Path(p["file"]).parent) for p in S["panels"]})), A["artifacts"][0]["video"], A["artifacts"][1]["video"], sha(cdir(ep) / AN), sorted({S["built_by"]["context_id"], A["built_by"]["context_id"]}), sha(cdir(ep) / SB), sha(cdir(ep) / AN), char_sha(ep), ", ".join('"%s": {...}' % i for i in required_panels(ep, S)[:2]) + ", ...", ", ".join(required_panels(ep, S)))); print("creative/JUDGE_BRIEF.md written")
    elif a.cmd == "judge-record":
        if not a.result: sys.exit("usage: review.py judge-record <ep> <result.json>")
        sys.exit(0 if judge_record(ep, a.result) == "PASS" else 1)
    elif a.cmd == "check":
        bad, J = g8_problems(ep); print("G8: " + ("PASS" if not bad else "FAIL")); [print("  -", x) for x in bad]; sys.exit(1 if bad else 0)
    elif a.cmd == "new-version":
        if not (a.owner and a.reason): sys.exit("--owner and --reason are required (owner action)")
        new_version(ep, a.owner, a.reason)
if __name__ == "__main__": main()
