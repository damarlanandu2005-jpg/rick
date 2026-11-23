#!/usr/bin/env python3
"""approval.json (blueprint section 19, gate G9). The owner's signature on exactly these files; any change makes it stale.
  python3 tools/approval.py check  <ep>                       exit 0 only if valid and fresh (the refuse rule used by pipeline.py and render.mjs --export-lock)
  python3 tools/approval.py create <ep> --reviewer NAME --approve creative,storyboard,characters,assets,camera,look
create refuses unless creative gates G1-G6 and G8 PASS (G7 may SKIP only for its R4 part) and the judge is not the approver. It is run ONLY on the owner's instruction.
Bypass for legacy example films / tests (never production): --unapproved-test-run on pipeline.py (stamps NOT A PRODUCTION RENDER)."""
import argparse, datetime, hashlib, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parent; sys.path.insert(0, str(HERE)); import creative_gates as CG
FLAGS = ["creative", "storyboard", "characters", "assets", "camera", "look"]
BAKED = ["camera_baked.json", "performance_baked.json", "flights_baked.json", "layers_baked.json", "assets_baked.json"]
def sha(p): return hashlib.sha1(Path(p).read_bytes()).hexdigest()
def _combine(items): return hashlib.sha1("|".join("%s:%s" % kv for kv in sorted(items)).encode()).hexdigest()
def current(ep):
    """The hashes of the files as they are NOW. A missing required file gives None (which can never equal a stored hash)."""
    ep = Path(ep); c = ep / "creative"; H = {}
    f = lambda p: sha(p) if Path(p).is_file() else None
    H["plan_sha1"] = f(ep / "film.json"); H["picture_plan_sha1"] = f(c / "PICTURE_PLAN.md"); H["look_bible_sha1"] = f(c / "LOOK_BIBLE.md"); H["storyboard_sha1"] = f(c / "STORYBOARD.json"); H["animatic_sha1"] = f(c / "ANIMATIC.json")
    H["reference_board_sha1"] = f(c / "reference_board.json")
    pl = ep / "out/plan"; H["baked_sha1"] = _combine([(n, sha(pl / n)) for n in BAKED if (pl / n).is_file()]) if (pl / "camera_baked.json").is_file() and (pl / "performance_baked.json").is_file() else None
    import characters as CH; H["character_sheets_sha1"] = CH.evidence_sha(ep)   # R3: spec + production record (views, performance, card hashes) + contact sheet
    import assets as AS; reg = AS.load()
    used = {i for _, i, _v in AS.film_assets(ep)} if (ep / "film.json").is_file() else set()
    cj = ep / "creative/characters.json"
    if cj.is_file(): used |= {str(v.get("character")) for v in (json.load(open(cj)).get("characters") or {}).values()}
    H["asset_versions"] = {a["name"]: {"version": a["version"], "sha1": hashlib.sha1(json.dumps(a, sort_keys=True).encode()).hexdigest()} for a in reg if a["name"] in used}   # R4: the assets THIS film uses (declared GLB assets + its cast characters), so registering an unrelated asset does not stale an approval
    return H
def check(ep):
    """-> list of problems; empty list means approved and fresh."""
    p = Path(ep) / "approval.json"
    if not p.is_file(): return ["approval.json is missing (no approval = no expensive render)"]
    try: A = json.load(open(p))
    except Exception as e: return ["approval.json is not valid JSON: %s" % e]
    bad = []; need = ["film", "plan_sha1", "baked_sha1", "picture_plan_sha1", "reference_board_sha1", "look_bible_sha1", "character_sheets_sha1", "storyboard_sha1", "animatic_sha1", "judge", "approvals", "reviewer", "approved_at"]
    bad += ["missing field %s" % k for k in need if A.get(k) in (None, "", {})]
    if not isinstance(A.get("asset_versions"), dict): bad.append("missing field asset_versions")   # {} is valid: a film may use no registry assets
    if bad: return bad
    H = current(ep)
    for k, v in H.items():
        if v is None: bad.append("%s: the file it hashes is missing now" % k)
        elif A[k] != v: bad.append("STALE %s: the file changed after approval" % k)
    ap = A["approvals"]
    for k in FLAGS:
        e = ap.get(k)
        if not isinstance(e, dict) or e.get("value") is not True or not e.get("reviewer") or not e.get("at"): bad.append("approval flag %s is not true with reviewer and timestamp" % k)
    import review as RV; g8b, _ = RV.g8_problems(ep); bad += ["G8 no longer passes: " + x for x in g8b[:3]]   # R2: the judged evidence must still be current at G9
    j = A["judge"]
    if not all(j.get(k) for k in ("reviewer", "score", "verdict", "fix_list_sha1")): bad.append("judge record incomplete")
    elif A["reviewer"] in (j["reviewer"], (json.load(open(Path(ep) / "creative/JUDGE.json")).get("judge") or {}).get("context_id")): bad.append("the judge cannot be the approver (section 14)")
    return bad
def create(ep, reviewer, approve):
    ep = Path(ep); R = CG.run(ep); bad = [r["gate"] + " " + r["note"] for r in R if r["status"] == "FAIL" or (r["status"] == "SKIP" and r["gate"] != "G7")]
    if bad: sys.exit("REFUSED: creative gates are not all PASS: " + " | ".join(bad))
    if sorted(approve) != sorted(FLAGS): sys.exit("REFUSED: --approve must name all of %s" % ",".join(FLAGS))
    J = json.load(open(ep / "creative/JUDGE.json")); J.get("result") == "PASS" or sys.exit("REFUSED: judge result is not PASS"); now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    A = dict(film=json.load(open(ep / "film.json")).get("title") or ep.name, **current(ep), judge=dict(reviewer=J.get("reviewer"), score=J.get("score"), verdict=J.get("verdict"), fix_list_sha1=J.get("fix_list_sha1")),
             approvals={k: dict(value=True, reviewer=reviewer, at=now) for k in FLAGS}, reviewer=reviewer, approved_at=now)
    (ep / "approval.json").write_text(json.dumps(A, indent=1)); b = check(ep)
    if b: (ep / "approval.json").unlink(); sys.exit("REFUSED: " + "; ".join(b))
    print("approval.json written for", A["film"], "by", reviewer)
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["check", "create"]); ap.add_argument("ep"); ap.add_argument("--reviewer"); ap.add_argument("--approve", default=""); a = ap.parse_args()
    if a.cmd == "check":
        b = check(a.ep); print("APPROVAL: " + ("VALID and fresh" if not b else "REFUSED")); [print("  -", x) for x in b]; sys.exit(1 if b else 0)
    if not a.reviewer: sys.exit("--reviewer required")
    create(a.ep, a.reviewer, [x for x in a.approve.split(",") if x])
