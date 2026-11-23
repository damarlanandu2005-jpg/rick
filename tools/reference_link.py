#!/usr/bin/env python3
"""R5: the REFERENCE-DRIVEN creative chain. The reference board is a creative input before the lock and the QA answer key after; it is never read by the renderer.
No second schema: creative/reference_board.json keeps its R1 form ({beats:[{id,kind,frames,...}], department_index}); a frame may now be a dict {file, sha1, film, t, kind, take} pointing at a real image file
under creative/ (the legacy string form still validates exactly as before). "R5 mode" = the board has at least one image frame; only then do the checks below apply, so R1-R4 episodes are unchanged.
  reference_link.py check <ep>     board images present + hashed, picture plan / characters / assets link to board beats and frames
  reference_link.py sheets <ep>    reference -> intended picture -> actual storyboard comparison sheets (out/reference_compare/ref_<beat>.png), built from creative/refs and out/storyboard_panels
Hash rule (approval, judge, storyboard): board_sha(ep) = sha1 of reference_board.json when no image frames, else a combine of the json and every image file's bytes."""
import hashlib, json, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parent
sha = lambda p: hashlib.sha1(Path(p).read_bytes()).hexdigest()
def load(ep):
    p = Path(ep) / "creative/reference_board.json"
    try: return json.load(open(p))
    except Exception: return None
def images(B):
    """-> [(beat id, frame dict)] for every image frame of the board."""
    return [(b.get("id"), f) for b in (B or {}).get("beats", []) for f in (b.get("frames") or []) if isinstance(f, dict)]
def r5_mode(ep):
    B = load(ep); return bool(B) and bool(images(B))
def board_sha(ep):
    ep = Path(ep); p = ep / "creative/reference_board.json"
    if not p.is_file(): return None
    B = load(ep)
    if not B or not images(B): return sha(p)
    parts = ["board.json:" + sha(p)]
    for _, f in sorted(images(B), key=lambda x: str(x[1].get("file"))):
        q = ep / "creative" / str(f.get("file")); parts.append("%s:%s" % (f.get("file"), sha(q) if q.is_file() else "MISSING"))
    return hashlib.sha1("|".join(parts).encode()).hexdigest()
def image_problems(ep):
    """Every image frame exists, is a real picture, matches its recorded sha1 (a replaced or edited reference makes the board stale), has film/t/kind/take evidence."""
    from PIL import Image
    ep = Path(ep); B = load(ep); bad = []
    for bid, f in images(B):
        q = ep / "creative" / str(f.get("file"))
        for k in ("file", "sha1", "film", "t", "kind", "take"):
            if f.get(k) in (None, ""): bad.append("beat %s frame %s: field %s missing" % (bid, f.get("file"), k))
        if not q.is_file(): bad.append("beat %s: reference image %s missing" % (bid, f.get("file"))); continue
        if f.get("sha1") and sha(q) != f["sha1"]: bad.append("beat %s: reference image %s changed (sha1 differs): the board is stale" % (bid, f.get("file"))); continue
        try:
            with Image.open(q) as im: w, h = im.size
            if w < 200 or h < 300: bad.append("beat %s: reference image %s is only %dx%d" % (bid, f.get("file"), w, h))
        except Exception: bad.append("beat %s: reference image %s is not a readable picture" % (bid, f.get("file")))
    for b in (B or {}).get("beats", []):
        n = sum(1 for f in b.get("frames") or [] if isinstance(f, dict))
        if n and n < 2: bad.append("beat %s has %d image frame(s), need >= 2" % (b.get("id"), n))
    return bad
def plan_rows(ep):
    """-> [(row id text, ref cell)] from PICTURE_PLAN.md (the `ref` column = the last cell of a row with 9 cells)."""
    p = Path(ep) / "creative/PICTURE_PLAN.md"; out = []
    if not p.is_file(): return out
    for l in p.read_text().splitlines():
        if re.match(r"\|\s*\d+", l):
            c = [x.strip() for x in l.strip().strip("|").split("|")]; out.append((c[0], c[8] if len(c) >= 9 else None))
    return out
def plan_problems(ep):
    """Picture plan <-> reference board: every row names a board beat and (when given) frames that exist in that beat; every beat is used by some row."""
    B = load(ep); bad = []
    if not B or not images(B): return bad
    ids = {str(b["id"]): {Path(f["file"]).stem.replace("sd_", "") for f in b["frames"] if isinstance(f, dict)} for b in B["beats"]}; used = set()
    for rid, cell in plan_rows(ep):
        if not cell: bad.append("picture plan row %s has no `ref` cell (reference beat and frames)" % rid); continue
        m = re.match(r"(\d+)\s*:\s*(.*)", cell)
        if not m or m.group(1) not in ids: bad.append("picture plan row %s: ref %r does not name a reference-board beat" % (rid, cell)); continue
        used.add(m.group(1)); fr = [x.strip() for x in m.group(2).split(",") if x.strip()]
        if not fr: bad.append("picture plan row %s: ref names no frame" % rid)
        bad += ["picture plan row %s: ref frame %s is not on board beat %s" % (rid, x, m.group(1)) for x in fr if x not in ids[m.group(1)]]
    bad += ["reference beat %s is used by no picture-plan row" % i for i in sorted(set(ids) - used)]
    return bad
def asset_problems(ep, reg=None):
    """Declared GLB assets <-> board: requirement.reference_beats must name existing board beats."""
    import assets as AS
    B = load(ep); bad = []
    if not B or not images(B): return bad
    ids = {b["id"] for b in B["beats"]}
    for _, i, _v in AS.film_assets(ep):
        a = AS.entry(i, _v); rb = ((a or {}).get("requirement") or {}).get("reference_beats") or []
        if not rb: bad.append("asset %s: requirement.reference_beats is empty (no link to the reference board)" % i)
        bad += ["asset %s: reference beat %s is not on the board" % (i, x) for x in rb if x not in ids]
    return bad
def character_problems(ep):
    """Cast <-> board: every character spec's reference_beats must name board beats (characters.py also checks this; this adds the R5 requirement that the list is non-empty)."""
    B = load(ep); bad = []
    p = Path(ep) / "creative/characters.json"
    if not B or not images(B) or not p.is_file(): return bad
    ids = {b["id"] for b in B["beats"]}
    for slot, c in (json.load(open(p)).get("characters") or {}).items():
        rb = c.get("reference_beats") or []
        if not rb: bad.append("character %s: reference_beats is empty" % slot)
        bad += ["character %s: reference beat %s is not on the board" % (slot, x) for x in rb if x not in ids]
    return bad
def problems(ep): return image_problems(ep) + plan_problems(ep) + asset_problems(ep) + character_problems(ep) if r5_mode(ep) else []
def sheets(ep):
    """reference -> intended picture -> actual storyboard: per board beat one PNG: the beat's reference frames (left), the picture plan rows that cite the beat (text strip), and the storyboard start/end panels of its stations (right)."""
    from PIL import Image, ImageDraw
    ep = Path(ep); B = load(ep); out = ep / "out/reference_compare"; out.mkdir(parents=True, exist_ok=True); made = []
    for b in B["beats"]:
        refs = [Image.open(ep / "creative" / f["file"]).convert("RGB") for f in b["frames"] if isinstance(f, dict)]; boards = []
        for st in b.get("storyboard_stations") or []:
            for kind in ("start", "end"):
                m = sorted((ep / "out/storyboard_panels").glob("%s_%s_f*.png" % (st, kind)))
                if m: boards.append((st + " " + kind, Image.open(m[0]).convert("RGB")))
        th = 480; fit = lambda im: im.resize((int(im.width * th / im.height), th))
        tiles = [("REF " + str(b["id"]), fit(i)) for i in refs] + [(t, fit(i)) for t, i in boards]; W = sum(i.width for _, i in tiles) + 8 * (len(tiles) - 1); sh = Image.new("RGB", (W, th + 24), (30, 30, 34)); x = 0; d = ImageDraw.Draw(sh)
        for i, (t, im) in enumerate(tiles): sh.paste(im, (x, 24)); d.text((x + 4, 6), t + ("   -->" if i == len(refs) - 1 else ""), fill=(255, 235, 120)); x += im.width + 8
        f = out / ("ref_%s.png" % b["id"]); sh.save(f); made.append(f)
    return made
if __name__ == "__main__":
    c, ep = sys.argv[1], sys.argv[2]
    if c == "check": bad = problems(ep); print("\n".join("- " + x for x in bad) or "reference chain OK (%s)" % ("R5 mode" if r5_mode(ep) else "no image frames: legacy board")); sys.exit(1 if bad else 0)
    elif c == "sheets": [print(x) for x in sheets(ep)]
