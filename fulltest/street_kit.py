"""fulltest/street_kit.py -- the Western street, built by code inside Blender with the EXISTING Ricks look code
(blender_look: materials.get, scatter.MB/place/blades/field, lights.cloud). Presets only change colours and layout numbers; every step
is wrapped by the caller so one failing decoration is reported, not fatal. Street axis = +Y, street width 14 m (x -7..7)."""
import math, random
import bpy
from mathutils import Vector
from blender_look import materials as M, lights, scatter as SC

C = dict(sand=(228, 186, 122), blue=(86, 122, 188), red=(178, 64, 50), tan=(216, 178, 122), brown=(140, 94, 62), cream=(232, 216, 178), teal=(72, 152, 150),
         wood=(150, 104, 66), dark=(58, 42, 36), glass=(60, 92, 140), roof=(122, 84, 66), mesa=(206, 108, 62), dry=(206, 176, 96), cactus=(96, 142, 78))
# (side, y0, width, height, wall, trim) side -1 = left of the camera when looking down +Y
PRESETS = {"western_noon": [
    (-1, 6, 8, 5.2, "blue", "cream"), (-1, 15, 9, 6.4, "red", "cream"), (-1, 25, 7, 5.0, "tan", "brown"), (-1, 33, 9, 6.0, "teal", "cream"), (-1, 43, 8, 5.4, "brown", "tan"), (-1, 52, 9, 6.2, "blue", "cream"), (-1, 62, 8, 5.0, "tan", "brown"), (-1, 71, 9, 6.0, "red", "cream"),
    (1, 6, 9, 5.6, "brown", "tan"), (1, 16, 8, 6.2, "blue", "cream"), (1, 25, 9, 5.0, "red", "cream"), (1, 35, 8, 6.4, "tan", "brown"), (1, 44, 9, 5.4, "teal", "cream"), (1, 54, 8, 6.0, "brown", "tan"), (1, 63, 9, 5.2, "blue", "cream"), (1, 73, 8, 6.2, "tan", "brown")]}

def build(scene, cfg, keep_clear=(), log=print):
    rng = random.Random(cfg.get("seed", 3)); out = {"parts": [], "errors": []}
    def step(name, fn):
        try: fn(); out["parts"].append(name)
        except Exception as e:
            import traceback; out["errors"].append("%s: %r" % (name, e)); log("STREET_STEP_FAILED %s\n%s" % (name, traceback.format_exc()[-600:]))
    sand = M.get("plaster", color=C["sand"], rough=.92, vary=.22, height=("noise", 5, .6))
    wood = lambda k: M.get("wood_grain", color=C[k])
    def ground():
        mb = SC.MB("Ground", [sand]); mb.box((0, 110, -.06), (90, 380, .12), 0); SC.place(scene, mb.mesh(), (0, 0, 0), kind="ground")
    def buildings():
        for (side, y0, w, h, wall, trim) in PRESETS[cfg.get("preset", "western_noon")]:
            depth = 9.0; mats = [M.get("plaster", color=C[wall], rough=.85, vary=.18, height=("noise", 16, .4)), wood(trim) if trim in ("cream", "tan") else wood("brown"), M.get("matte", color=C["glass"], rough=.2), M.get("roof_tile", color=C["roof"])]
            mats[1] = M.get("wood_grain", color=C[trim], rough=.6)
            mb = SC.MB("Bld", mats); xc = side * (7 + depth / 2); yc = y0 + w / 2
            mb.box((xc, yc, h / 2), (depth, w, h), 0)                                  # body
            mb.box((side * 7.1, yc, h + .75), (.3, w, 1.5), 0); mb.box((side * 7.0, yc, h + 1.55), (.5, w * 1.02, .22), 1)      # false front + cornice
            mb.box((side * 6.1, yc, .15), (1.8, w, .3), 1)                             # boardwalk
            for k in range(max(2, int(w // 2.4) + 1)): mb.box((side * 5.35, y0 + .4 + k * (w - .8) / max(1, int(w // 2.4)), 1.6), (.2, .2, 3.2), 1)   # posts
            mb.box((side * 6.2, yc, 3.3), (2.1, w, .18), 3)                            # porch roof
            n = max(2, int(w // 2.7))
            for i in range(n): xw = side * 6.96; yw = y0 + (i + .5) * w / n; mb.box((xw, yw, 2.0), (.08, 1.0, 1.35), 2); mb.box((xw, yw, 2.72), (.12, 1.2, .1), 1); mb.box((xw, yw, 1.3), (.12, 1.2, .1), 1)
            mb.box((side * 6.96, yc, 1.15), (.1, 1.1, 2.2), 1)                         # door
            mb.box((side * 6.8, yc, h * .72 + 1.0), (.12, w * .62, .75), 1)            # sign board
            SC.place(scene, mb.mesh(), (0, 0, 0), kind="building")
    def poles():
        mat = wood("brown"); mb = SC.MB("Poles", [mat]); tops = []
        for k, y in enumerate(range(10, 80, 18)):
            x = -4.7 if k % 2 == 0 else 4.7; mb.box((x, y, 3.4), (.22, .22, 6.8), 0); mb.box((x, y, 6.2), (.2, 2.2, .2), 0); tops.append((x, y))
        for a, b in zip(tops, tops[1:]):
            for dy in (-.9, 0, .9): mb.rod((a[0], a[1] + dy, 6.2), (b[0], b[1] + dy, 6.2), .012)
        SC.place(scene, mb.mesh(), (0, 0, 0), kind="poles")
    def mesas():
        mat = M.get("brick", color=C["mesa"], rough=.9, vary=.25); mb = SC.MB("Mesas", [mat])
        for i, (x, y, w, d, h) in enumerate([(-90, 300, 80, 40, 30), (-20, 330, 110, 40, 22), (70, 310, 90, 40, 36), (150, 340, 120, 40, 26), (-160, 330, 90, 40, 20)]): mb.box((x, y, h / 2), (w, d, h), 0, rz=rng.uniform(-.15, .15))
        SC.place(scene, mb.mesh(), (0, 0, 0), kind="mesas")
    def clouds():
        cm = M.cloud_soft((.98, .98, 1.0), (.62, .72, .92))
        for i, (x, z, w) in enumerate([(-80, 90, 110), (40, 110, 140), (120, 80, 100), (-20, 70, 80)]): lights.cloud(scene, (x, 260, z), w, cm, seed=i + 1, n=14)
    def props():
        mb = SC.MB("Props", [wood("wood"), M.get("foliage", color=C["cactus"]), M.get("wood_grain", color=C["dark"])])
        for (x, y) in [(-5.6, 9.5), (5.6, 21), (-5.6, 30), (5.6, 40), (-5.6, 55)]: mb.cyl((x, y, .45), .35, .9, 0, 14); mb.box((x + .1, y + .9, .28), (.8, .5, .5), 2, rz=.3)     # barrel + crate
        for (x, y) in [(-5.3, 19.5), (5.3, 50)]: mb.box((x, y, .45), (.9, 2.4, .5), 2); mb.rod((x, y - 1.1, 0), (x, y - 1.1, .9), .06); mb.rod((x, y + 1.1, 0), (x, y + 1.1, .9), .06)      # trough
        for (x, y) in [(-8.5, 5), (8.5, 12), (-10, 20), (9.5, 34)]: mb.cyl((x, y, .8), .18, 1.6, 1, 10); mb.cyl((x - .3, y, 1.1), .1, .6, 1, 8, rot=(0, 1.2, 0)); mb.cyl((x + .3, y, 1.0), .1, .5, 1, 8, rot=(0, -1.2, 0))    # cactus
        SC.place(scene, mb.mesh(), (0, 0, 0), kind="props")
    def grass():
        me = SC.blades("Tuft", M.get("blade", color=C["dry"]), n=11, h=.34); SC.field(scene, me, (-5, 5, 3, 70), 90, rng=rng, exclude=list(keep_clear) + [(0, 0, 1.2)], kind="tuft", size=(.7, 1.4))
    for n, f in (("ground", ground), ("buildings", buildings), ("poles", poles), ("mesas", mesas), ("clouds", clouds), ("props", props), ("grass", grass)): step(n, f)
    return out
