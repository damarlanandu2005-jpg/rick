#!/usr/bin/env python3
"""kit/set_check.py -- pre-render check of a RECIPE (no Blender): fails early if the set cannot meet the Ricks density gates by design.
    python3 kit/set_check.py western_noon        exit 1 on ERROR. The real gate is measured after the build (tally in the Blender report)."""
import json, sys
from pathlib import Path
R = Path(__file__).resolve().parent / "recipes"
def check(name):
    r = json.loads((R / (name + ".json")).read_text()); e, w = [], []
    for k in ("half_width", "street", "landmarks", "scatter", "desert", "density"):
        if k not in r: e.append("recipe missing '%s'" % k)
    if e: return e, w
    S = r["street"]; styles = set(S["styles_left"]) | set(S["styles_right"])
    if len(styles) < 6: e.append("only %d building styles, need >= 6 so the street does not repeat" % len(styles))
    lots = 2 * int((S["y_end"] - S["y_start"]) / (sum(S["widths"]) / len(S["widths"]) + sum(S["gap"]) / 2))
    if lots < 10: e.append("about %d lots, a street needs >= 10 to read as a street" % lots)
    est_kinds = 2 * len(styles) + 9 + sum(1 for v in r["scatter"].values()) + sum(1 for v in r["desert"].values() if v) + len(r["landmarks"]) + 6
    est_inst = sum(r["scatter"].values()) + 3 * r["desert"]["rock_clusters"] + r["desert"]["saguaro"] + r["desert"]["barrel_cactus"] + lots * 13
    if est_kinds < r["density"]["kinds"]: w.append("estimated kinds %d < gate %d" % (est_kinds, r["density"]["kinds"]))
    if est_inst < r["density"]["instances"]: e.append("estimated objects %d < gate %d" % (est_inst, r["density"]["instances"]))
    if not r.get("motion"): e.append("no moving things (rule: 2+ per shot)")
    return e, w
if __name__ == "__main__":
    e, w = check(sys.argv[1]); [print("ERROR", x) for x in e]; [print("WARN", x) for x in w]; print("SET CHECK %s: %d error(s), %d warning(s)" % (sys.argv[1], len(e), len(w))); sys.exit(1 if e else 0)
