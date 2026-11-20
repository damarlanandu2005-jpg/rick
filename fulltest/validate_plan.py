#!/usr/bin/env python3
"""fulltest/validate_plan.py -- checks a COMPILED shot script with plain maths (no Blender, no GPU, about a second) BEFORE any render.
    python3 fulltest/validate_plan.py fulltest/script_passA.json
Uses shotmath.py, the same functions the Blender renderer uses. Prints one line per problem: ERROR (will render wrong) or WARN (check by eye).
Catches: character outside the frame or the street, camera inside a character or a wall, prop outside the frame or hidden behind a character card."""
import json, sys, math, copy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); import shotmath as SM
CARD_HALF_W = 0.46      # metres; the puppet cards are about 0.9 m wide
def lerp(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
def validate(S):
    S = copy.deepcopy(S); cast = S["cast"]; W = float(S.get("street", {}).get("half_width", 5.4)); out = []; metrics = {}
    def add(level, shot, msg): out.append({"level": level, "shot": shot, "msg": msg})
    try: SM.resolve_screen_chars(S["shots"])
    except ValueError as e: add("ERROR", "-", str(e)); return out, metrics
    for sh in S["shots"]:
        sid = sh["id"]; chars = sh.get("chars", [])
        try: cam = SM.fit_camera(sh["cam"], chars, cast)
        except ValueError as e: add("ERROR", sid, str(e)); continue
        lens = cam["lens"]; tgt = sh["cam"].get("target")
        for k in ("pos0", "pos1"):
            p = cam[k]
            if abs(p[0]) > W - 0.8 or p[1] < -1 or p[2] < 0.15: add("ERROR", sid, "camera at (%.1f, %.1f, %.1f) is outside the street or underground" % p)
        for c in chars:
            H = cast[c["id"]].get("height_m", 1.8); x, y = c["pos"][:2]
            if abs(x) > W - 0.6 or y < 1 or y > 70: add("ERROR", sid, "%s stands at (%.1f, %.1f), outside the street (|x| <= %.1f, 1 <= y <= 70)" % (c["id"], x, y, W - 0.6))
            for t in (0.0, 0.5, 1.0):
                pos, aim = lerp(cam["pos0"], cam["pos1"], t), lerp(cam["aim0"], cam["aim1"], t)
                zc = (sh['cam'].get('center_frac', .5) if tgt == c['id'] else .5) * H; mid = SM.project((x, y, zc), pos, aim, lens); head = SM.project((x, y, H), pos, aim, lens); feet = SM.project((x, y, 0), pos, aim, lens)
                if mid is None: add("ERROR", sid, "%s is behind the camera" % c["id"]); break
                if mid[2] < 0.5: add("ERROR", sid, "camera is inside %s (%.2f m away)" % (c["id"], mid[2])); break
                if abs(mid[0]) > 0.98 or abs(mid[1]) > 1.0:
                    if not c.get("offscreen_ok"): add("ERROR", sid, "%s is outside the frame (screen x %.2f, y %.2f at t=%.1f)" % (c["id"], mid[0], mid[1], t)); break
                if t == 0.5:
                    fh = (head[1] - feet[1]) / 2 if head and feet else 0; metrics.setdefault(sid, {})[c["id"]] = {"screen_height_frac": round(fh, 2), "depth_m": round(mid[2], 2)}
                    full = tgt == c["id"] and sh["cam"].get("visible_frac", 0) >= 1.2
                    if full and head and (head[1] > 1.0): add("WARN", sid, "%s head is cut off at the top" % c["id"])
                    if full and feet and (feet[1] < -1.0): add("WARN", sid, "%s feet are cut off at the bottom" % c["id"])
                    if 0 < fh < 0.04 and tgt != c["id"]: metrics[sid][c["id"]]["note"] = "tiny in frame (wide shot?)"
        # props
        f0 = None
        for fx in sh.get("fx", []):
            def pw(key):
                if key in fx: return tuple(fx[key])
                if key + "_screen" in fx: sx, sy, dp = fx[key + "_screen"]; return SM.screen_to_world(cam["pos0"], cam["aim0"], lens, sx, sy, dp)
                add("ERROR", sid, "%s needs '%s' or '%s_screen'" % (fx.get("type"), key, key)); return None
            a, b = pw("from"), pw("to")
            if a is None or b is None: continue
            for t in (0.25, 0.5, 0.75):
                p = lerp(a, b, t); pos, aim = lerp(cam["pos0"], cam["pos1"], t), lerp(cam["aim0"], cam["aim1"], t); pr = SM.project(p, pos, aim, lens)
                if t == 0.5 and (pr is None or abs(pr[0]) > 1.0 or abs(pr[1]) > 1.0): add("ERROR", sid, "%s is outside the frame at mid-shot (never visible)" % fx["type"]); break
                if pr is None: continue
                for c in chars:
                    H = cast[c["id"]].get("height_m", 1.8); x, y = c["pos"][:2]
                    l = SM.project((x - CARD_HALF_W, y, 0), pos, aim, lens); r = SM.project((x + CARD_HALF_W, y, 0), pos, aim, lens); hd = SM.project((x, y, H), pos, aim, lens); ct = SM.project((x, y, 0), pos, aim, lens)
                    if not (l and r and hd and ct): continue
                    if pr[2] > ct[2] and min(l[0], r[0]) <= pr[0] <= max(l[0], r[0]) and ct[1] <= pr[1] <= hd[1]:
                        add("ERROR", sid, "%s is hidden behind %s at t=%.2f (prop depth %.2f m, card depth %.2f m)" % (fx["type"], c["id"], t, pr[2], ct[2])); break
            if fx.get("type") == "bullet":
                pr = SM.project(lerp(a, b, .5), lerp(cam["pos0"], cam["pos1"], .5), lerp(cam["aim0"], cam["aim1"], .5), lens)
                if pr:
                    hv = 2 * pr[2] * SM.tan_v(lens); frac = 0.35 * float(fx.get("scale", 1)) / hv
                    if not 0.02 <= frac <= 0.3: add("WARN", sid, "bullet is %.0f%% of the frame height (aim for 3-30%%)" % (frac * 100))
    return out, metrics
if __name__ == "__main__":
    S = json.loads(Path(sys.argv[1]).read_text()); res, m = validate(S); errs = [r for r in res if r["level"] == "ERROR"]
    for r in res: print("%s shot %s: %s" % (r["level"], r["shot"], r["msg"]))
    print("VALIDATE %d shots: %d error(s), %d warning(s)" % (len(S["shots"]), len(errs), len(res) - len(errs))); sys.exit(1 if errs else 0)
