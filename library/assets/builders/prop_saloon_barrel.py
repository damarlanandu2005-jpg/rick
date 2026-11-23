"""Blender asset: prop_saloon_barrel (R5): a Western whiskey barrel with a tin cup on its lid, for the noon street. Procedural, no external file. Metres, Blender Z up, origin at the base centre.
Materials by Ricks library name (mat:<lib>[.rrggbb]). Anchor: Empty 'elbow_rest' on the lid centre (where a character leans). Five+ specific details: 14 staves with a bulged waist, three iron hoops, a plank lid
with two gaps, a bung and tap plug, a tin cup with a handle, a chalked tally of four strokes. build() -> objects."""
import math, bpy
def _mat(name, hexcol):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes.get("Principled BSDF")
    r, g, bl = (int(hexcol[i:i + 2], 16) / 255 for i in (1, 3, 5)); lin = lambda c: ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
    b.inputs["Base Color"].default_value = (lin(r), lin(g), lin(bl), 1); b.inputs["Roughness"].default_value = 0.8; return m
def _fin(o, name, mat, role): o.name = name; o.data.name = name + "_mesh"; o.data.materials.append(mat); o["role"] = role; return o
def _box(name, size, at, mat, role, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=at, rotation=rot); o = bpy.context.active_object; o.scale = size; bpy.ops.object.transform_apply(location=False, rotation=True, scale=True); return _fin(o, name, mat, role)
def _cyl(name, r, depth, at, mat, role, seg=24):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=seg, location=at); o = bpy.context.active_object; bpy.ops.object.transform_apply(location=False, rotation=True, scale=True); return _fin(o, name, mat, role)
def _ring(name, R, r, at, mat, role):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=32, minor_segments=8, location=at); o = bpy.context.active_object; bpy.ops.object.transform_apply(location=False, rotation=True, scale=True); return _fin(o, name, mat, role)
def build():
    wood = _mat("mat:wood_grain", "#8a5a34"); lid = _mat("mat:wood_grain.a67c4a", "#a67c4a"); iron = _mat("mat:painted_metal_chipped.3a3d46", "#3a3d46"); tin = _mat("mat:metal", "#9aa3ab"); chalk = _mat("mat:sign_flat", "#efe9d8"); objs = []
    H = 0.95; N = 14; Rw = 0.30; Rb = 0.34        # waist radius at the ends, bulge radius at the middle
    for i in range(N):                              # staves: a thin box tilted to follow the bulge, two segments (lower and upper half)
        a = 2 * math.pi * i / N; ca, sa = math.cos(a), math.sin(a); w = 2 * math.pi * Rb / N * 0.92
        for half, z0, rr in ((0, 0.24, (Rw + Rb) / 2), (1, 0.71, (Rw + Rb) / 2)):
            tilt = math.atan2(Rb - Rw, H / 2) * (1 if half == 0 else -1)
            o = _box("stave_%02d_%d" % (i + 1, half), (0.028, w, H / 2 + 0.002), (ca * rr, sa * rr, z0), wood, "wood", (0, 0, 0))
            o.rotation_euler = (0, tilt, a); bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.object.transform_apply(location=False, rotation=True, scale=False); objs.append(o)
    for k, z in enumerate((0.14, 0.475, 0.81)): objs.append(_ring("iron_hoop_%d" % (k + 1), Rb + 0.012 - (0.03 if k != 1 else 0), 0.016, (0, 0, z), iron, "metal"))
    for k, x in enumerate((-0.165, 0.0, 0.165)): objs.append(_box("lid_plank_%d" % (k + 1), (0.145, 0.50 if x else 0.60, 0.035), (x, 0, H + 0.0175), lid, "wood"))
    objs.append(_cyl("bung", 0.032, 0.03, (0.0, -0.1, H + 0.05), iron, "metal", 12))
    objs.append(_cyl("tin_cup", 0.05, 0.085, (0.12, 0.16, H + 0.075), tin, "metal", 20)); objs.append(_box("cup_handle", (0.012, 0.05, 0.05), (0.12, 0.222, H + 0.075), tin, "metal"))
    for k in range(4): objs.append(_box("chalk_tally_%d" % (k + 1), (0.012, 0.008, 0.12), (-0.09 + k * 0.045, -0.2, H + 0.037), chalk, "sign"))
    e = bpy.data.objects.new("elbow_rest", None); e.location = (0.0, 0.0, H + 0.035); e.empty_display_type = "PLAIN_AXES"; bpy.context.collection.objects.link(e); objs.append(e)
    return objs
