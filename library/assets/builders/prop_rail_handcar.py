"""Blender asset: prop_rail_handcar, a pump handcar for the canyon railroad (R4 real asset). Procedural, no external file. Metres, Blender Z up, origin at the base (wheel treads on z = 0),
the long axis along Y (the track direction), wheels on the rails at x = +-0.72. Materials follow the Ricks library names: mat:<library name>[.rrggbb] (one colour per name; a library name used in two colours
carries the colour after the dot). Anchors are Empties named like the Ricks held-prop anchors: grip_left / grip_right (the two pump-handle ends, for the 'box'-style two-hand grip).
Details (Hard Rule 2, five specific): planked deck with a gap between boards, spoked wheels with hubs and flanges, a pivoted walking beam with two upright pump handles, a connecting rod to a crank, a brake lever,
a front lantern on a pole, a leather-strapped toolbox with a hammer, a name plate. build() -> the list of created objects."""
import math, bpy
RAIL_X = 0.72
def _mat(name, hexcol):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes.get("Principled BSDF")
    r, g, bl = (int(hexcol[i:i + 2], 16) / 255 for i in (1, 3, 5)); lin = lambda c: ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
    b.inputs["Base Color"].default_value = (lin(r), lin(g), lin(bl), 1); b.inputs["Roughness"].default_value = 0.75
    return m
def _box(name, size, at, mat, role, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=at, rotation=rot); o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True); o.data.materials.append(mat); o["role"] = role; o.data.name = name + "_mesh"; return o
def _cyl(name, r, depth, at, mat, role, axis="x", seg=24):
    rot = {"x": (0, math.pi / 2, 0), "y": (math.pi / 2, 0, 0), "z": (0, 0, 0)}[axis]
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=seg, location=at, rotation=rot); o = bpy.context.active_object; o.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True); o.data.materials.append(mat); o["role"] = role; o.data.name = name + "_mesh"; return o
def _empty(name, at):
    o = bpy.data.objects.new(name, None); o.location = at; o.empty_display_type = "PLAIN_AXES"; bpy.context.collection.objects.link(o); return o
def build():
    wood = _mat("mat:wood_grain", "#a0723e"); frame = _mat("mat:painted_metal_chipped.3a3d46", "#3a3d46"); red = _mat("mat:painted_metal_chipped.b4332a", "#b4332a")
    metal = _mat("mat:metal", "#5b636b"); lamp = _mat("mat:emissive_lamp", "#ffd27a"); bag = _mat("mat:burlap", "#8a6f4a"); plate = _mat("mat:sign_flat", "#e4d5ac"); objs = []
    R = 0.22; AX = R + 0.03                                                    # wheel radius; axle height
    for i in range(7):                                                  # deck planks with gaps
        objs.append(_box("deck_plank_%d" % (i + 1), (1.16, 0.18, 0.05), (0, -0.54 + i * 0.18, 0.46), wood, "wood"))
    for sx, n in ((-1, "left"), (1, "right")): objs.append(_box("frame_beam_%s" % n, (0.07, 1.46, 0.09), (sx * 0.50, 0, 0.395), frame, "metal"))
    for y, n in ((-0.58, "front"), (0.58, "rear")): objs.append(_box("cross_bolster_%s" % n, (1.12, 0.09, 0.07), (0, y, 0.395), frame, "metal"))
    for y, n in ((-0.55, "front"), (0.55, "rear")):
        objs.append(_cyl("axle_%s" % n, 0.03, 1.56, (0, y, AX), metal, "metal", "x", 12))
        for sx, s in ((-1, "left"), (1, "right")):
            objs.append(_cyl("wheel_%s_%s" % (n, s), R, 0.035, (sx * RAIL_X, y, AX), metal, "metal", "x", 32))
            objs.append(_cyl("wheel_flange_%s_%s" % (n, s), R + 0.03, 0.012, (sx * (RAIL_X - sx * 0.0), y, AX), metal, "metal", "x", 32))
            objs.append(_cyl("wheel_hub_%s_%s" % (n, s), 0.055, 0.075, (sx * RAIL_X, y, AX), frame, "metal", "x", 16))
            for k in range(6):
                a = k * math.pi / 3; objs.append(_box("wheel_spoke_%s_%s_%d" % (n, s, k + 1), (0.012, 0.018, R * 0.82), (sx * RAIL_X + sx * 0.02, y + math.sin(a) * R * 0.45, AX + math.cos(a) * R * 0.45), metal, "metal", (a, 0, 0)))
    for sx, n in ((-1, "left"), (1, "right")): objs.append(_box("axle_box_%s" % n, (0.08, 0.1, 0.07), (sx * 0.62, -0.55, 0.30), frame, "metal"))
    objs.append(_box("pivot_post", (0.1, 0.1, 0.5), (0, 0, 0.74), frame, "metal"))
    objs.append(_cyl("pivot_pin", 0.035, 0.16, (0, 0, 1.0), metal, "metal", "x", 12))
    objs.append(_box("walking_beam", (0.08, 1.7, 0.09), (0, 0, 1.0), red, "metal"))
    for y, n in ((-0.85, "front"), (0.85, "rear")):
        objs.append(_box("pump_handle_%s" % n, (0.05, 0.05, 0.34), (0, y, 1.17), wood, "wood"))
        objs.append(_box("pump_grip_%s" % n, (0.34, 0.05, 0.05), (0, y, 1.34), wood, "wood"))
    objs.append(_box("connecting_rod", (0.03, 0.03, 0.62), (0, 0.28, 0.72), metal, "metal", (math.radians(20), 0, 0)))
    objs.append(_cyl("crank_disc", 0.09, 0.03, (0, 0.44, 0.46 - 0.025 + 0.0), metal, "metal", "x", 20))
    objs.append(_box("brake_lever", (0.04, 0.04, 0.46), (0.55, 0.22, 0.70), red, "metal", (0, math.radians(14), 0)))
    objs.append(_cyl("lantern_pole", 0.015, 0.7, (-0.5, -0.74, 0.82), frame, "metal", "z", 8))
    objs.append(_cyl("lantern_lens", 0.07, 0.11, (-0.5, -0.74, 1.2), lamp, "lamp", "z", 16)); objs.append(_cyl("lantern_cap", 0.085, 0.025, (-0.5, -0.74, 1.265), frame, "metal", "z", 16))
    objs.append(_box("toolbox", (0.34, 0.22, 0.17), (0.28, 0.46, 0.57), bag, "cloth")); objs.append(_box("toolbox_strap", (0.36, 0.04, 0.19), (0.28, 0.46, 0.57), frame, "metal"))
    objs.append(_box("hammer_handle", (0.035, 0.30, 0.035), (-0.28, 0.42, 0.515), wood, "wood", (0, 0, math.radians(18)))); objs.append(_box("hammer_head", (0.09, 0.05, 0.05), (-0.34, 0.55, 0.515), metal, "metal", (0, 0, math.radians(18))))
    objs.append(_box("name_plate", (0.5, 0.012, 0.13), (0, -0.78, 0.40), plate, "sign"))
    objs.append(_box("coupler_bar", (0.06, 0.28, 0.06), (0, -0.88, 0.36), frame, "metal"))
    objs.append(_empty("grip_left", (0.0, -0.85, 1.34))); objs.append(_empty("grip_right", (0.0, 0.85, 1.34)))   # Ricks anchor names (film.js held3d 'box' kind: grip_left / grip_right)
    return objs
