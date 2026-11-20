#!/usr/bin/env python3
"""fulltest/compile_intent.py -- turns the DIRECTOR's intent spec (words, no coordinates) into the detailed shot script the renderer reads.
    python3 fulltest/compile_intent.py fulltest/intent_passA.json fulltest/script_passA.json
Vocabulary (see DIRECTOR_PLAYBOOK.md): size ewide|wide|full|medium|cu|ecu, focus face|chest|belt|feet, angle low|eye|high, side left|center|right,
at left|center|right, dist near|mid|far|vfar, lens wide|normal|tele, move static|push|pull|tilt_up, fx bullet(across|toward)|tumbleweed.
All numbers come from the rules in RULES below, in ONE place, and are checked by validate_plan.py."""
import json, sys, math, copy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); import shotmath as SM
RULES = {
    "stage_cam": (0.4, 0.5), "dist_m": {"near": 5.5, "mid": 12.0, "far": 24.0, "vfar": 40.0}, "at_x": {"left": -0.55, "center": 0.0, "right": 0.55},
    "lens": {"wide": 24, "normal": 30, "tele": 36}, "angle_el": {"low": -18, "eye": 1, "high": 14}, "cam_z": {"low": 0.55, "eye": 1.5, "high": 2.6},
    "side_az": {"left": -12, "center": 0, "right": 12}, "size_vis": {"full": 1.8, "medium": 0.9, "cu": 0.6, "ecu": 0.32}, "focus_center": {"face": 0.86, "chest": 0.66, "belt": 0.45, "feet": 0.1},
    "push_frac": {"small": 0.12, "medium": 0.2}, "push_m": {"small": 0.6, "medium": 1.4}, "lead_dx": 0.32, "bullet_frac": 0.08, "bullet_len_m": 0.35, "street_half_width": 5.4}
def compile_intent(I):
    R = RULES; cast = I["cast"]; shots = []; notes = []
    for sh in I["shots"]:
        sid, size, ang, side = sh["id"], sh.get("size", "medium"), sh.get("angle", "eye"), sh.get("side", "center")
        lens = R["lens"][sh.get("lens", "wide" if size in ("ewide", "wide") else "normal")]
        chars = []
        for c in sh.get("cast", []):
            d = R["dist_m"][c.get("dist", "mid")]; x = R["stage_cam"][0] + R["at_x"][c.get("at", "center")] * d * 0.2
            chars.append({"id": c["id"], "pos": [round(x, 2), round(R["stage_cam"][1] + d, 2)], "move": c["move"], "style": c.get("style", "A")} | ({"flip": True} if c.get("flip") else {}))
        subj = sh.get("subject"); mv = sh.get("move", "static"); amount = sh.get("amount", "small")
        if subj:
            cam = {"target": subj, "visible_frac": R["size_vis"].get(size, 0.9), "center_frac": R["focus_center"][sh.get("focus", "chest")], "az": R["side_az"][side], "el": R["angle_el"][ang], "lens": lens}
            if size == "full": cam["center_frac"] = 0.5
            if mv in ("push", "pull"): cam["push"] = R["push_frac"][amount] * (1 if mv == "push" else -1)
            if mv == "tilt_up": cam["aim_dz"] = 0.08
            if sh.get("lead") in ("left", "right"): cam["aim_dx"] = R["lead_dx"] * (1 if sh["lead"] == "right" else -1)
        else:
            far = max((R["dist_m"][c.get("dist", "mid")] for c in sh.get("cast", [])), default=R["dist_m"]["far"]); cx = R["stage_cam"][0]
            cam = {"pos": [cx, R["stage_cam"][1] + (1.0 if ang != "low" else 0.5), R["cam_z"][ang]], "aim": [0.0, R["stage_cam"][1] + far, 1.3 + (0.3 if ang == "low" else 0.2)], "lens": lens}
            if mv in ("push", "pull"): cam["push"] = R["push_m"][amount] * (1 if mv == "push" else -1)
        fx = []
        for f in sh.get("fx", []):
            if f["type"] == "bullet":
                dd = (0.55 * (subj and R["size_vis"].get(size, .9) * 1.8 / (2 * SM.tan_v(lens)) or 0)) or 6.0        # in front of the subject's card, never behind it
                hv = 2 * dd * SM.tan_v(lens); sc = round(R["bullet_frac"] * hv / R["bullet_len_m"], 2)
                if f.get("path", "across") == "across": fx.append({"type": "bullet", "from_screen": [0.9, -0.1, round(dd, 2)], "to_screen": [-0.9, -0.3, round(dd, 2)], "scale": sc})
                else:
                    d_far, d_near = 14.0, 2.5; sc = round(R["bullet_frac"] * 2 * ((d_far + d_near) / 2) * SM.tan_v(lens) / R["bullet_len_m"], 2)
                    fx.append({"type": "bullet", "from_screen": [0.4, -0.1, d_far], "to_screen": [-0.5, -0.5, d_near], "scale": sc})
            elif f["type"] == "tumbleweed":
                y = R["stage_cam"][1] + R["dist_m"]["mid"] - 2; fx.append({"type": "tumbleweed", "from": [5.0, y, 0.35], "to": [-5.0, y - 2, 0.35]})
            else: notes.append("shot %s: unknown fx type %s (dropped)" % (sid, f["type"]))
        shots.append({"id": sid, "sec": sh["sec"], "note": sh.get("note", ""), "cam": cam, "chars": chars} | ({"fx": fx} if fx else {}))
    S = {"name": I["name"], "fps": I.get("fps", 30), "note": "COMPILED by compile_intent.py from the intent spec. Do not hand-edit; change the intent or RULES.", "cast": cast,
         "street": {"preset": I.get("place", "western_noon"), "seed": I.get("seed", 3), "half_width": R["street_half_width"]}, "shots": shots, "render": I.get("render", {})}
    for k in ("transitions", "grade"):
        if k in I: S[k] = I[k]
    return S, notes
if __name__ == "__main__":
    I = json.loads(Path(sys.argv[1]).read_text()); S, notes = compile_intent(I); Path(sys.argv[2]).write_text(json.dumps(S, indent=1))
    for n in notes: print("note:", n)
    print("COMPILED %d shots -> %s" % (len(S["shots"]), sys.argv[2]))
