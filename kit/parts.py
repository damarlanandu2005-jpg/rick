"""kit/parts.py -- the Western parts library. Every part is built from primitives (scatter.MB) with the LOCKED Ricks materials (materials.get).
Nothing is imported or downloaded. Rules it follows (KIT_SPEC.md): hero buildings carry real detail (frames, mullions, shutters, rails, doors, lanterns),
clusters are big/medium/small never lines, every kind is counted in scatter.TALLY so the set check can enforce 30 kinds / 600 objects."""
import math, random
from blender_look import materials as M, lights, scatter as SC
from . import kitlib as K

C = dict(sand=(228, 186, 122), dirt=(176, 140, 96), rut=(142, 108, 74), blue=(86, 122, 188), red=(178, 64, 50), tan=(216, 178, 122), brown=(140, 94, 62), cream=(232, 216, 178), teal=(72, 152, 150),
         wood=(150, 104, 66), dark=(58, 42, 36), glass=(60, 92, 140), roof=(122, 84, 66), mesa=(206, 108, 62), mesa2=(226, 140, 84), dry=(206, 176, 96), cactus=(96, 142, 78), stone=(160, 152, 140), white=(236, 230, 214), hay=(222, 188, 96))
# style = what makes the building THIS building (hero detail), sign = texture name
STYLES = {
    "saloon":     dict(storeys=2, balcony=True, swing=True, sign="saloon", h=6.6, wall="red", trim="cream"),
    "hotel":      dict(storeys=2, balcony=True, sign="hotel", h=6.8, wall="blue", trim="cream"),
    "general":    dict(storeys=1, sign="general", h=5.2, wall="tan", trim="brown", stock=True),
    "bank":       dict(storeys=1, columns=True, bars=True, sign="bank", h=5.6, wall="stone", trim="cream"),
    "jail":       dict(storeys=1, bars=True, sign="jail", h=5.0, wall="stone", trim="brown"),
    "barber":     dict(storeys=1, pole=True, sign="barber", h=5.0, wall="teal", trim="cream"),
    "livery":     dict(storeys=1, bigdoors=True, sign="livery", h=5.8, wall="brown", trim="tan"),
    "undertaker": dict(storeys=1, sign="undertaker", h=5.4, wall="brown", trim="dark"),
}
def mats(wall, trim):
    return [M.get("plaster", color=C[wall], rough=.85, vary=.18, height=("noise", 16, .4)), M.get("wood_grain", color=C[trim], rough=.6), M.get("matte", color=C["glass"], rough=.2),
            M.get("roof_tile", color=C["roof"]), M.get("wood_grain", color=C["dark"]), M.get("metal", color=(70, 70, 74))]

def shared(scene, tex_dir=None):
    """every repeated prop is ONE mesh, instanced many times"""
    wood, dark, hay = M.get("wood_grain", color=C["wood"]), M.get("wood_grain", color=C["dark"]), M.get("burlap", color=C["hay"])
    st, cac, dry, bark = M.get("stone", color=C["stone"]), M.get("foliage", color=C["cactus"]), M.get("blade", color=C["dry"]), M.get("bark", color=(110, 84, 62))
    out = {}
    def mk(name, mats_, fn): mb = SC.MB(name, mats_); fn(mb); out[name] = mb.mesh()
    mk("barrel", [wood, M.get("metal", color=(70, 70, 74))], lambda b: (b.cyl((0, 0, .45), .35, .9, 0, 14), b.cyl((0, 0, .22), .365, .05, 1, 14), b.cyl((0, 0, .68), .365, .05, 1, 14)))
    mk("crate", [wood, dark], lambda b: (b.box((0, 0, .3), (.8, .6, .6), 0), b.box((0, -.31, .3), (.8, .03, .08), 1), b.box((0, 0, .61), (.84, .64, .04), 1)))
    mk("haybale", [hay, dark], lambda b: (b.box((0, 0, .27), (.9, .5, .54), 0), b.box((0, 0, .27), (.92, .06, .56), 1)))
    mk("bench", [wood, dark], lambda b: (b.box((0, 0, .45), (1.6, .42, .06), 0), b.box((0, .2, .75), (1.6, .05, .4), 0), b.box((.7, 0, .22), (.08, .4, .44), 1), b.box((-.7, 0, .22), (.08, .4, .44), 1)))
    mk("trough", [wood, dark], lambda b: (b.box((0, 0, .45), (2.4, .7, .5), 0), b.box((-1.1, 0, .2), (.1, .6, .4), 1), b.box((1.1, 0, .2), (.1, .6, .4), 1)))
    mk("hitch_post", [wood], lambda b: (b.box((-.9, 0, .6), (.14, .14, 1.2), 0), b.box((.9, 0, .6), (.14, .14, 1.2), 0), b.box((0, 0, 1.0), (1.9, .1, .1), 0)))
    mk("fence", [wood, dark], lambda b: ([b.box((-1 + i * .25, 0, .45), (.1, .04, .9 + .06 * (i % 2)), 0) for i in range(9)], b.box((0, .03, .3), (2.1, .04, .08), 1), b.box((0, .03, .7), (2.1, .04, .08), 1)))
    mk("wheel", [wood, M.get("metal", color=(70, 70, 74))], lambda b: (b.cyl((0, 0, .5), .5, .06, 1, 20, r2=.5, rot=(0, math.pi / 2, 0)), [b.rod((0, 0, .5), (0, .46 * math.cos(a), .5 + .46 * math.sin(a)), .02, 0) for a in [i * math.pi / 4 for i in range(8)]]))
    mk("lantern", [dark], lambda b: (b.box((0, 0, 0), (.16, .16, .26), 0), b.rod((0, 0, .13), (0, 0, .4), .01, 0)))
    out["lantern_glow"] = (lambda b: (b.sph((0, 0, 0), (.07, .07, .11), 0), b.mesh())[1])(SC.MB("lantern_glow", [M.emissive_lamp((255, 190, 100), 2.6)]))
    mk("rock", [st], lambda b: (b.ico((0, 0, .25), .5, 0, 2, (1.2, 1, .7)), b.ico((.5, .25, .15), .28, 0, 1, (1, 1, .7))))
    mk("pebble", [st], lambda b: b.ico((0, 0, .03), .08, 0, 1, (1.3, 1, .6)))
    mk("dry_bush", [dry, bark], lambda b: ([b.rod((0, 0, 0), (.25 * math.cos(a), .25 * math.sin(a), .35 + .1 * (i % 3)), .012, 1) for i, a in enumerate([k * 0.9 for k in range(7)])], b.ico((0, 0, .3), .28, 0, 1, (1, 1, .7))))
    mk("saguaro", [cac], lambda b: (b.cyl((0, 0, 1.4), .22, 2.8, 0, 12, r2=.2), b.sph((0, 0, 2.8), (.22, .22, .22), 0, 10, 6), b.cyl((.5, 0, 1.3), .14, .8, 0, 10, rot=(0, math.pi / 2, 0)), b.cyl((.8, 0, 1.75), .14, .9, 0, 10), b.sph((.8, 0, 2.2), (.14, .14, .14), 0, 8, 5),
                                    b.cyl((-.45, 0, 1.0), .13, .7, 0, 10, rot=(0, math.pi / 2, 0)), b.cyl((-.72, 0, 1.4), .13, .8, 0, 10), b.sph((-.72, 0, 1.8), (.13, .13, .13), 0, 8, 5)))
    mk("barrel_cactus", [cac], lambda b: b.ico((0, 0, .3), .32, 0, 2, (1, 1, 1.15)))
    mk("skull", [M.get("matte", color=(232, 226, 208))], lambda b: (b.ico((0, 0, .12), .14, 0, 1, (1.3, .9, .8)), b.cyl((.2, 0, .12), .03, .22, 0, 6, r2=.005, rot=(0, math.pi / 2, 0)), b.cyl((-.2, 0, .12), .03, .22, 0, 6, r2=.005, rot=(0, -math.pi / 2, 0))))
    mk("dead_tree", [bark], lambda b: (b.cyl((0, 0, 1.4), .16, 2.8, 0, 8, r2=.07), b.rod((0, 0, 1.8), (.9, .2, 2.7), .05), b.rod((0, 0, 2.2), (-.8, -.2, 3.1), .045), b.rod((.5, .1, 2.25), (1.0, .5, 2.4), .03), b.rod((-.45, -.1, 2.6), (-.9, -.5, 2.7), .03)))
    out["tuft"] = SC.blades("Tuft", M.get("blade", color=C["dry"]), n=11, h=.34)
    return out

def building(scene, sd, y0, w, style, W, rng, tex_dir, SH, tally_kind=None):
    S = STYLES[style]; h = S["h"]; depth = 9.0; yc = y0 + w / 2; P = lambda d, y, z: (sd * (W - d), y, z)
    mb = SC.MB("bld_" + style, mats(S["wall"], S["trim"]))   # 0 wall 1 trim 2 glass 3 roof 4 dark 5 metal
    mb.box((sd * (W + depth / 2), yc, h / 2), (depth, w, h), 0)
    mb.box(P(-.15, yc, h + .8), (.3, w, 1.6), 0); mb.box(P(0, yc, h + 1.62), (.5, w * 1.02, .22), 1); mb.box(P(-.1, yc, h + .02), (.45, w * 1.01, .12), 1)          # false front, cornice, base moulding
    mb.box(P(.95, yc, .15), (1.9, w, .3), 1)                                                                                                                      # boardwalk
    for k in range(int(w // 1.1)): mb.box(P(.95, y0 + .5 + k * 1.1, .31), (1.88, .03, .02), 4)                                                                     # plank seams
    np_ = max(2, int(w // 2.4) + 1)
    for k in range(np_): mb.box(P(1.65, y0 + .4 + k * (w - .8) / (np_ - 1), 1.6), (.2, .2, 3.2), 1); mb.box(P(1.65, y0 + .4 + k * (w - .8) / (np_ - 1), 3.05), (.34, .3, .1), 1)   # porch posts + brackets
    mb.box(P(.8, yc, 3.3), (2.1, w, .18), 3)                                                                                                                      # porch roof
    top = 3.4
    if S.get("balcony"):
        mb.box(P(.8, yc, 3.52), (2.1, w, .1), 1)
        for k in range(int(w / .45) + 1): mb.box(P(1.75, y0 + .2 + k * .45, 4.0), (.05, .05, .9), 1)                                                               # balusters
        mb.box(P(1.75, yc, 4.5), (.1, w, .08), 1); mb.box(P(1.75, yc, 3.6), (.08, w, .06), 1)
        n2 = max(2, int(w // 2.7))
        for i in range(n2):
            yw = y0 + (i + .5) * w / n2; mb.box(P(.04, yw, 5.0), (.08, .95, 1.3), 2); mb.box(P(.07, yw, 5.0), (.1, .06, 1.34), 4); mb.box(P(.07, yw, 5.0), (.1, 1.0, .06), 4)
            for sx in (-.62, .62): mb.box(P(.06, yw + sx, 5.0), (.08, .3, 1.34), 4)                                                                                # 2nd storey windows + mullions + shutters
        mb.box(P(.04, yc + w * .3, 4.5), (.1, .9, 2.0), 1)                                                                                                         # balcony door
    n = max(2, int(w // 2.7)); dy = yc
    for i in range(n):
        yw = y0 + (i + .5) * w / n
        if abs(yw - dy) < 1.3: continue
        mb.box(P(.04, yw, 2.0), (.08, 1.0, 1.35), 2); mb.box(P(.07, yw, 2.0), (.1, .06, 1.38), 4); mb.box(P(.07, yw, 2.0), (.1, 1.04, .06), 4)                         # glass + mullions
        mb.box(P(.07, yw, 2.72), (.12, 1.2, .1), 1); mb.box(P(.09, yw, 1.3), (.2, 1.2, .1), 1)                                                                       # lintel, sill
        for sx in (-.66, .66): mb.box(P(.06, yw + sx, 2.0), (.08, .3, 1.4), 4)                                                                                     # shutters
        if S.get("bars"): [mb.rod(P(.12, yw - .45 + j * .15, 1.35), P(.12, yw - .45 + j * .15, 2.7), .012, 5) for j in range(7)]
    mb.box(P(.05, dy, 1.15), (.1, 1.1, 2.2), 1); mb.box(P(.08, dy, 2.35), (.12, 1.35, .12), 4); mb.box(P(.08, dy - .62, 1.15), (.12, .12, 2.3), 4); mb.box(P(.08, dy + .62, 1.15), (.12, .12, 2.3), 4)   # door + frame
    mb.box(P(.12, dy + .38, 1.1), (.05, .05, .05), 5)
    if S.get("swing"): [mb.box(P(.35, dy + sx, 1.4), (.06, .6, 1.0), 1) for sx in (-.31, .31)]
    if S.get("columns"): [mb.cyl(P(1.5, y0 + .6 + k * (w - 1.2) / 3, 1.7), .17, 3.4, 1, 14) for k in range(4)] + [mb.box(P(1.1, yc, 3.75), (1.5, w * .8, .35), 1)]
    if S.get("bigdoors"): mb.box(P(.07, dy, 1.6), (.12, 2.6, 3.2), 4); mb.box(P(.1, dy, 1.6), (.06, .08, 3.2), 1); mb.box(P(.1, dy, 4.4), (.12, 1.2, 1.4), 4)
    if S.get("pole"):
        px = P(1.4, y0 + 1.0, 0)[0]; mb.cyl((px, y0 + 1.0, 1.0), .09, 2.0, 1, 10); mb.sph((px, y0 + 1.0, 2.05), (.12, .12, .12), 5, 8, 6)
        for k in range(5): mb.box((px, y0 + 1.0, .3 + k * .38), (.2, .2, .12), 0, rz=.0)
    mb.cyl((sd * (W + 3), y0 + w * .75, h + 1.0), .22, 1.4, 5, 10); mb.box((sd * (W + 3), y0 + w * .75, h + .3), (.5, .5, .5), 4)                                  # stovepipe + base
    SC.place(scene, mb.mesh(), (0, 0, 0), kind="bld_" + style)
    sm = K.sign_mat(tex_dir, "sign_%s.png" % S["sign"])
    if sm is None: sm = M.get("wood_grain", color=C["dark"])
    K.panel(scene, "sign_" + style, w * .78, 1.15, (sd * (W - .02), yc, h + .8), sm, sd, "sign_" + style, SC.TALLY)
    for yy in (y0 + .5, y0 + w - .5): SC.place(scene, SH["lantern"], P(1.6, yy, 2.95), kind="lantern"); SC.place(scene, SH["lantern_glow"], P(1.6, yy, 2.95), kind="lantern_glow")
    SC.place(scene, SH["bench"], P(1.0, y0 + w * .22, 0.3), rz=math.pi / 2 if sd < 0 else -math.pi / 2, kind="bench")
    SC.cluster3(scene, SH["barrel"], P(1.2, y0 + w * .85, .3), 0.8, rng, "barrel", (1, .8, .7)); SC.cluster3(scene, SH["crate"], P(1.2, y0 + w * .5 + 1.4, .3), 0.7, rng, "crate", (1, .85, .7))
    if S.get("stock"): SC.cluster3(scene, SH["haybale"], P(1.0, y0 + w * .62, .3), .7, rng, "haybale", (1, .9, .8))

def church(scene, y):
    mb = SC.MB("church", [M.get("plaster", color=C["white"], rough=.85, vary=.15), M.get("wood_grain", color=C["brown"]), M.get("matte", color=(30, 30, 40), rough=.3), M.get("roof_tile", color=C["roof"]), M.get("wood_grain", color=C["dark"])])
    mb.box((0, y, 3.5), (9, 11, 7), 0); mb.box((0, y, 7.45), (9.6, 11.6, .5), 3)                                  # nave + roof slab
    mb.box((0, y - 6.5, 5.25), (3.2, 3.2, 10.5), 0); mb.cyl((0, y - 6.5, 12.2), 2.4, 3.4, 3, 4, r2=0.01, rot=(0, 0, math.pi / 4))   # bell tower + steeple
    mb.box((0, y - 8.12, 8.6), (1.4, .1, 1.4), 2); mb.box((0, y - 6.5, 14.4), (.12, .12, 1.6), 1); mb.box((0, y - 6.5, 14.75), (.12, 1.0, .12), 1)      # belfry opening, cross
    mb.box((0, y - 8.12, 1.6), (1.6, .14, 3.2), 4)
    for sx in (-4.55, 4.55):
        for k in range(3): mb.box((sx, y - 3.0 + k * 3.0, 3.6), (.12, 1.0, 2.2), 2)
    SC.place(scene, mb.mesh(), (0, 0, 0), kind="church")

def water_tower(scene, x, y):
    mb = SC.MB("water_tower", [M.get("wood_grain", color=C["wood"]), M.get("wood_grain", color=C["dark"]), M.get("roof_tile", color=C["roof"]), M.get("metal", color=(70, 70, 74))])
    for sx, sy in ((-1.4, -1.4), (1.4, -1.4), (1.4, 1.4), (-1.4, 1.4)): mb.rod((x + sx, y + sy, 0), (x + sx * .85, y + sy * .85, 8.0), .12, 1, 6)
    for z in (2.5, 5.0): mb.box((x, y - 1.2, z), (2.6, .08, .1), 1); mb.box((x, y + 1.2, z), (2.6, .08, .1), 1); mb.box((x - 1.2, y, z), (.08, 2.6, .1), 1); mb.box((x + 1.2, y, z), (.08, 2.6, .1), 1)
    mb.cyl((x, y, 9.6), 2.0, 3.2, 0, 16); [mb.cyl((x, y, 8.4 + i * .8), 2.03, .07, 3, 16) for i in range(4)]; mb.cyl((x, y, 11.9), 2.2, 1.4, 2, 16, r2=.05); mb.rod((x + 2.1, y, 3.0), (x + 2.1, y, 9.6), .04, 3)
    SC.place(scene, mb.mesh(), (0, 0, 0), kind="water_tower")

def windmill(scene, x, y, sd):
    mb = SC.MB("windmill_tower", [M.get("wood_grain", color=C["wood"]), M.get("metal", color=(70, 70, 74))])
    for sx, sy in ((-.9, -.9), (.9, -.9), (.9, .9), (-.9, .9)): mb.rod((x + sx, y + sy, 0), (x + sx * .3, y + sy * .3, 8.0), .08, 0, 6)
    mb.box((x, y, 8.3), (.8, .5, .5), 1); mb.box((x - sd * .6, y, 8.3), (.3, .15, .5), 1); SC.place(scene, mb.mesh(), (0, 0, 0), kind="windmill_tower")
    bl = SC.MB("windmill_blades", [M.get("metal", color=(210, 206, 196))])
    for k in range(8):
        a = k * math.pi / 4; bl.box((0, 1.6 * math.cos(a), 1.6 * math.sin(a)), (.04, .5, .5), 0, rx=a); bl.rod((0, 0, 0), (0, 2.4 * math.cos(a), 2.4 * math.sin(a)), .03, 0)
    return SC.place(scene, bl.mesh(), (x - sd * .8, y, 8.3), kind="windmill_blades")      # hub faces the street; caller spins it with a driver

def wagon(scene, x, y, rz):
    mb = SC.MB("wagon", [M.get("wood_grain", color=C["wood"]), M.get("wood_grain", color=C["dark"]), M.get("canvas", color=(220, 212, 186)), M.get("metal", color=(70, 70, 74))])
    mb.box((0, 0, .85), (3.0, 1.5, .5), 0); mb.box((0, .78, 1.2), (3.0, .06, .5), 1); mb.box((0, -.78, 1.2), (3.0, .06, .5), 1); mb.box((1.55, 0, 1.2), (.06, 1.5, .5), 1)
    for k in range(4): mb.box((-1.2 + k * .8, 0, 1.7), (.05, 1.5, .1), 1)      # canvas bows
    mb.box((0, 0, 1.85), (2.9, 1.5, .08), 2); mb.rod((-1.6, 0, .85), (-3.2, 0, .7), .05, 1)
    for wx in (-1.0, 1.0):
        for wy in (-.85, .85): mb.cyl((wx, wy, .62), .62, .08, 1, 18, rot=(math.pi / 2, 0, 0)); [mb.rod((wx, wy, .62), (wx + .56 * math.cos(a), wy, .62 + .56 * math.sin(a)), .02, 0) for a in [i * math.pi / 4 for i in range(8)]]
    SC.place(scene, mb.mesh(), (x, y, 0), rz=rz, kind="wagon")

def flag(scene, x, y):
    mb = SC.MB("flagpole", [M.get("metal", color=(200, 200, 204))]); mb.cyl((x, y, 4.5), .06, 9.0, 0, 8); mb.sph((x, y, 9.05), (.1, .1, .1), 0, 8, 6); SC.place(scene, mb.mesh(), (0, 0, 0), kind="flagpole")
    fb = SC.MB("flag", [M.get("cloth", color=(176, 40, 44)), M.get("cloth", color=(236, 236, 236))]); fb.box((0, .7, 0), (.03, 1.4, .9), 0); fb.box((0, .7, 0), (.035, 1.4, .3), 1)
    o = SC.place(scene, fb.mesh(), (x, y, 8.4), kind="flag"); return o
