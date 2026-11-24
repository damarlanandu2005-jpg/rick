"""Blender asset: prop_track_buckled (production 1 "The Gap"): a 6 m piece of CONTINUOUS (gapless) standard-gauge track that has buckled sideways in the heat:
both rails bend into an S (0.42 m peak sideways), the sleepers dragged along and twisted. Ends are straight and on the centre line so it joins plain track.
Metres, Z up, Y along the track, origin at the base centre. Anchor: 'kink' (top of the near rail at the largest sideways bend). build() -> objects."""
import math, bpy
# ---- geometry helpers (inlined so the builder file alone fixes the GLB: pure from_pydata triangles, no exporter triangulation) ----
def mat(name, hexcol, rough=0.6):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes.get("Principled BSDF")
    r, g, bl = (int(hexcol[i:i + 2], 16) / 255 for i in (1, 3, 5)); lin = lambda c: ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
    b.inputs["Base Color"].default_value = (lin(r), lin(g), lin(bl), 1); b.inputs["Roughness"].default_value = rough; return m
def obj(name, verts, tris, material, role):
    me = bpy.data.meshes.new(name + "_mesh"); me.from_pydata([tuple(round(c, 6) for c in v) for v in verts], [], tris); me.update(); me.materials.append(material)
    o = bpy.data.objects.new(name, me); o["role"] = role; bpy.context.collection.objects.link(o); return o
def quad(a, b, c, d): return [(a, b, c), (a, c, d)]
def box(cx, cy, z0, w, d, h, ang=0.0):
    """axis box centred (cx, cy), bottom z0, width w (x), depth d (y), height h, rotated ang about Z -> (verts, tris)"""
    ca, sa = math.cos(ang), math.sin(ang); V = []
    for z in (z0, z0 + h):
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            x, y = sx * w / 2, sy * d / 2; V.append((cx + x * ca - y * sa, cy + x * sa + y * ca, z))
    T = quad(0, 3, 2, 1) + quad(4, 5, 6, 7) + quad(0, 1, 5, 4) + quad(1, 2, 6, 5) + quad(2, 3, 7, 6) + quad(3, 0, 4, 7); return V, T
def merge(parts):
    V, T = [], []
    for v, t in parts: o = len(V); V += v; T += [(a + o, b + o, c + o) for a, b, c in t]
    return V, T
# rail cross-section: flange, web, head (x half-width, z0, z1) - a simplified flat-bottom rail 0.17 m tall
PROFILE = ((0.07, 0.0, 0.025), (0.016, 0.025, 0.13), (0.036, 0.13, 0.17))
def rail(path, z0):
    """a rail swept along a list of (x, y) points (tangent from neighbours): three rectangular tubes with end caps -> (verts, tris)"""
    parts = []
    n = len(path)
    for hw, a, b in PROFILE:
        V, T = [], []
        for i, (x, y) in enumerate(path):
            p0, p1 = path[max(i - 1, 0)], path[min(i + 1, n - 1)]; tx, ty = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(tx, ty) or 1; nx, ny = ty / L, -tx / L
            for s, z in ((-1, a), (1, a), (1, b), (-1, b)): V.append((x + s * hw * nx, y + s * hw * ny, z0 + z))
        for i in range(n - 1):
            k, m = 4 * i, 4 * (i + 1)
            for j in range(4): T += quad(k + j, k + (j + 1) % 4, m + (j + 1) % 4, m + j)
        T += quad(0, 3, 2, 1) + quad(4 * (n - 1), 4 * (n - 1) + 1, 4 * (n - 1) + 2, 4 * (n - 1) + 3)
        parts.append((V, T))
    return merge(parts)
def cyl_x(cx, cy, cz, r, length, seg=8):
    """a bolt: an octagonal prism along X -> (verts, tris)"""
    V = [(cx + sx * length / 2, cy + r * math.cos(2 * math.pi * k / seg), cz + r * math.sin(2 * math.pi * k / seg)) for sx in (-1, 1) for k in range(seg)]
    T = []
    for k in range(seg): T += quad(k, (k + 1) % seg, seg + (k + 1) % seg, seg + k)
    for k in range(1, seg - 1): T += [(0, k + 1, k), (seg, seg + k, seg + k + 1)]
    return V, T
def empty(name, at):
    e = bpy.data.objects.new(name, None); e.location = at; e.empty_display_type = "PLAIN_AXES"; bpy.context.collection.objects.link(e); return e

GAUGE = 0.72; SLEEPER_H = 0.12; L = 6.0; A = 0.42; N = 61
def dx(y): u = (y + L / 2) / L; return A * math.sin(2 * math.pi * u) * math.sin(math.pi * u) ** 2   # 0 with zero slope at both ends, an S in between
def build():
    steel = mat("mat:metal.9aa0a6", "#9aa0a6", 0.35); wood = mat("mat:wood_grain.6b4a2e", "#6b4a2e", 0.8); objs = []
    ys = [-L / 2 + L * i / (N - 1) for i in range(N)]
    sl = []
    for k in range(9):
        y = -L / 2 + 0.35 + 0.66 * k; slope = (dx(y + 0.01) - dx(y - 0.01)) / 0.02
        sl.append(box(dx(y), y, 0, 2.5, 0.24, SLEEPER_H, math.atan(slope) * 0.8))
    objs.append(obj("sleepers", *merge(sl), wood, "wood"))
    for side, nm in ((-1, "near"), (1, "far")):
        objs.append(obj("rail_%s" % nm, *rail([(dx(y) + side * GAUGE, y) for y in ys], SLEEPER_H), steel, "metal"))
    yk = max(ys, key=lambda y: abs(dx(y)))
    objs.append(empty("kink", (round(dx(yk) - GAUGE, 4), round(yk, 4), SLEEPER_H + 0.17)))
    return objs
