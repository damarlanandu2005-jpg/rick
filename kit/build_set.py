"""kit/build_set.py -- builds a SET from a recipe (kit/recipes/<place>.json) with the parts library. Interface used by fulltest/blender_full.py:
    build(scene, cfg, keep_clear, log) -> {"parts": [...], "errors": [...], "tally": {types, instances, counts, types_ok, instances_ok}}
Each step is wrapped so one failing decoration is reported, never fatal. The density gate (30 kinds, 600 objects, Ricks DENSITY_RULES) is measured, not assumed."""
import json, math, random, os
from pathlib import Path
import bpy
from blender_look import materials as M, lights, scatter as SC
from . import parts as P, kitlib as K
RECIPES = Path(__file__).resolve().parent / "recipes"

def build(scene, cfg, keep_clear=(), log=print):
    R = json.loads((RECIPES / ("%s.json" % cfg.get("preset", "western_noon"))).read_text()); W = float(cfg.get("half_width", R["half_width"])); rng = random.Random(cfg.get("seed", R["seed"]))
    tex = cfg.get("tex_dir", ""); out = {"parts": [], "errors": []}; SC.TALLY.clear(); SH = {}; ex = list(keep_clear) + [(0.4, 0.5, 2.0)]; lots = []
    def step(name, fn):
        try: fn(); out["parts"].append(name)
        except Exception as e:
            import traceback; out["errors"].append("%s: %r" % (name, e)); log("STREET_STEP_FAILED %s\n%s" % (name, traceback.format_exc()[-700:]))
    def prep(): SH.update(P.shared(scene, tex))
    def ground():
        mb = SC.MB("Ground", [M.get("plaster", color=P.C["sand"], rough=.92, vary=.22, height=("noise", 5, .6)), M.get("wet_mud_puddle", color=P.C["dirt"], wet=.08), M.get("matte", color=P.C["rut"])])
        mb.box((0, 110, -.06), (400, 420, .12), 0); mb.box((0, 60, .008), (2 * W + .2, 150, .02), 1)
        for sx in (-1.3, 1.3): mb.box((sx, 60, .02), (.45, 150, .012), 2)
        SC.place(scene, mb.mesh(), (0, 0, 0), kind="ground")
    def buildings():
        S = R["street"]
        for sd, key in ((-1, "styles_left"), (1, "styles_right")):
            y = S["y_start"] + (0 if sd < 0 else 1.5); i = 0
            while y < S["y_end"]:
                w = S["widths"][(i + (0 if sd < 0 else 2)) % len(S["widths"])]; st = S[key][i % len(S[key])]
                try: P.building(scene, sd, y, w, st, W, rng, tex, SH)
                except Exception as e: out["errors"].append("building %s: %r" % (st, e)); log("STREET_STEP_FAILED building %s %r" % (st, e))
                lots.append((sd, y, w, st)); gap = rng.uniform(*S["gap"]); n = int(gap // 2.0)
                for k in range(n): SC.place(scene, SH["fence"], (sd * (W - .6), y + w + .4 + k * 2.1 + 1.0, .3), rz=math.pi / 2, kind="fence")
                y += w + gap; i += 1
    def street_props():
        sp = R["street_props"]; lm = R["landmarks"]
        for k in range(sp["hitch_posts"]): sd = -1 if k % 2 == 0 else 1; SC.place(scene, SH["hitch_post"], (sd * (W - 2.9), 14 + k * 9.5, 0), rz=math.pi / 2, kind="hitch_post")
        for k in range(sp["troughs"]): sd = 1 if k % 2 == 0 else -1; SC.place(scene, SH["trough"], (sd * (W - 2.6), 20 + k * 13, 0), rz=math.pi / 2, kind="trough")
        for k in range(sp["wheels"]): SC.place(scene, SH["wheel"], (-(W - 2.2) + k * 3.0, 24 + k * 14, 0), rz=.4 * k, kind="wheel_prop")
        for (x, y, rz) in lm["wagons"]: P.wagon(scene, x, y, rz + math.pi / 2)
        x, y = lm["wanted_board"]; mb = SC.MB("wanted_board", [M.get("wood_grain", color=P.C["wood"])]); mb.box((0, 0, .9), (.08, 1.0, 1.4), 0); mb.box((0, -.45, .45), (.1, .08, .9), 0); mb.box((0, .45, .45), (.1, .08, .9), 0)
        SC.place(scene, mb.mesh(), (x, y, 0), kind="wanted_board"); pm = K.sign_mat(tex, "poster_wanted.png", .15)
        if pm is not None: K.panel(scene, "poster", .6, .9, (x - .06, y, 1.0), pm, 1, "poster", SC.TALLY)
    def poles():
        mb = SC.MB("Poles", [M.get("wood_grain", color=P.C["brown"])]); wb = SC.MB("Wires", [M.get("metal", color=(40, 40, 44))]); tops = []
        for k, y in enumerate(range(10, 80, 18)):
            x = -(W - 2.3) if k % 2 == 0 else (W - 2.3); mb.box((x, y, 3.4), (.22, .22, 6.8), 0); mb.box((x, y, 6.2), (.2, 2.2, .2), 0); mb.box((x, y, 5.6), (.16, 1.6, .14), 0); tops.append((x, y))
        for a, b in zip(tops, tops[1:]):
            for dy in (-.9, 0, .9): wb.rod((a[0], a[1] + dy, 6.2), (b[0], b[1] + dy, 6.2), .012)
        SC.place(scene, mb.mesh(), (0, 0, 0), kind="telegraph_pole"); SC.place(scene, wb.mesh(), (0, 0, 0), kind="wires")
    def landmarks():
        L = R["landmarks"]; P.water_tower(scene, *L["water_tower"]); out["windmill"] = P.windmill(scene, L["windmill"][0], L["windmill"][1], 1 if L["windmill"][0] > 0 else -1); out["flag"] = P.flag(scene, *L["flag"])
        P.church(scene, L["church_y"]); sm = K.sign_mat(tex, "sign_church.png")
        if sm is not None: K.panel(scene, "sign_church", 2.6, .65, (0.0, L["church_y"] - 8.2, 4.4), sm, 1, "sign_church", SC.TALLY).rotation_euler = (0, 0, math.pi / 2)
    def desert():
        D = R["desert"]; mm = SC.MB("Mesas", [M.get("brick", color=P.C["mesa"], rough=.9, vary=.25), M.get("brick", color=P.C["mesa2"], rough=.9, vary=.25)])
        for i, (x, y, w, d, h) in enumerate([(-90, 300, 80, 40, 30), (-20, 330, 110, 40, 22), (70, 310, 90, 40, 36), (150, 340, 120, 40, 26), (-160, 330, 90, 40, 20)][:D["mesas"]]):
            mm.box((x, y, h / 2), (w, d, h), 0, rz=rng.uniform(-.15, .15)); mm.box((x, y, h * .6), (w * 1.02, d * 1.02, h * .08), 1, rz=0)
        SC.place(scene, mm.mesh(), (0, 0, 0), kind="mesa")
        for (x0, x1, y0, y1) in ((-60, -W - 10, 6, 150), (W + 10, 60, 6, 150), (-40, 40, W * 0 + 100, 190)):
            for nm, key, n in (("rock", "rock", D["rock_clusters"] // 3), ("saguaro", "saguaro", D["saguaro"] // 3), ("barrel_cactus", "barrel_cactus", D["barrel_cactus"] // 3), ("dead_tree", "dead_tree", D["dead_trees"] // 3), ("skull", "skull", D["skulls"] // 3)):
                for _ in range(max(1, n)):
                    c = (rng.uniform(min(x0, x1), max(x0, x1)), rng.uniform(y0, y1), 0)
                    if nm == "rock": SC.cluster3(scene, SH[key], c, 1.6, rng, "rock", (1.3, .9, .6))
                    else: SC.place(scene, SH[key], c, rz=rng.uniform(0, 6.28), s=rng.uniform(.8, 1.3), kind=nm)
        for _ in range(2): SC.place(scene, SH["skull"], (rng.uniform(-3, 3), rng.uniform(78, 84), 0), rz=rng.uniform(0, 6.28), kind="skull")
    def clouds():
        cm = M.cloud_soft((.98, .98, 1.0), (.62, .72, .92))
        for i, (x, z, w) in enumerate([(-80, 90, 110), (40, 110, 140), (120, 80, 100), (-20, 70, 80), (-150, 120, 120)]): lights.cloud(scene, (x, 260, z), w, cm, seed=i + 1, n=14)
    def scatter():
        sc_ = R["scatter"]; SC.field(scene, SH["tuft"], (-(W - 2), W - 2, 3, 75), sc_["tufts"], rng, ex, "tuft", (.7, 1.4)); SC.field(scene, SH["pebble"], (-(W - 2), W - 2, 3, 80), sc_["pebbles"], rng, ex, "pebble", (.6, 1.6))
        SC.field(scene, SH["dry_bush"], (-(W - 2), W - 2, 6, 80), sc_["bushes"], rng, ex + [(0, y, 1.6) for y in range(6, 80, 6)], "dry_bush", (.8, 1.4))
    def motion():
        if out.get("windmill") is not None: K.spin_driver(out["windmill"], "frame*0.09", 0)
        if out.get("flag") is not None: K.spin_driver(out["flag"], "sin(frame*0.33)*0.35", 2)
    for n, f in (("prep", prep), ("ground", ground), ("buildings", buildings), ("street_props", street_props), ("poles", poles), ("landmarks", landmarks), ("desert", desert), ("clouds", clouds), ("scatter", scatter), ("motion", motion)): step(n, f)
    out["tally"] = SC.TALLY.report(R["density"]["kinds"], R["density"]["instances"]); out["lots"] = len(lots); return out
