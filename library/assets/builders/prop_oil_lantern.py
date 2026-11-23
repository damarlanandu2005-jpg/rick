"""Blender asset: prop_oil_lantern (R7): a Western hurricane oil lantern, a small reusable library prop for any night/interior/rail set. Procedural, no external file.
Metres, Blender Z up, origin at the base centre (the tank stands on z = 0). Materials by Ricks library name (mat:<lib>[.rrggbb]); the globe is a lamp (role 'lamp', name '*globe*')
so the kit's lamp bloom picks it up. Anchors (mesh-less Empties, the Ricks held-prop anchor names): 'grip' at the top of the wire bail (where a hand would hold it),
'flame' at the wick inside the globe (where a practical light sits). Details: round fuel tank with a filler cap, burner collar with a wick knob, glass globe,
four guard wires, vented top cap with a chimney, wire bail. build() -> objects."""
import math, bpy
def _mat(name, hexcol, rough=0.7):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes.get("Principled BSDF")
    r, g, bl = (int(hexcol[i:i + 2], 16) / 255 for i in (1, 3, 5)); lin = lambda c: ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
    b.inputs["Base Color"].default_value = (lin(r), lin(g), lin(bl), 1); b.inputs["Roughness"].default_value = rough; return m
def _fin(o, name, mat, role): o.name = name; o.data.name = name + "_mesh"; o.data.materials.append(mat); o["role"] = role; return o
def _apply(o): bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.object.transform_apply(location=False, rotation=True, scale=True); return o
def _cyl(name, r, depth, at, mat, role, seg=24, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=seg, location=at, rotation=rot); return _fin(_apply(bpy.context.active_object), name, mat, role)
def _cone(name, r1, r2, depth, at, mat, role, seg=24):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=depth, vertices=seg, location=at); return _fin(_apply(bpy.context.active_object), name, mat, role)
def _ring(name, R, r, at, mat, role, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=32, minor_segments=8, location=at, rotation=rot); return _fin(_apply(bpy.context.active_object), name, mat, role)
def _empty(name, at):
    e = bpy.data.objects.new(name, None); e.location = at; e.empty_display_type = "PLAIN_AXES"; bpy.context.collection.objects.link(e); return e
def build():
    green = _mat("mat:painted_metal_chipped.2f5a3e", "#2f5a3e"); tin = _mat("mat:metal", "#a7adb3", 0.35); glow = _mat("mat:emissive_lamp.ffd27a", "#ffd27a", 0.2); objs = []
    objs.append(_cyl("fuel_tank", 0.075, 0.07, (0, 0, 0.035), green, "metal"))
    objs.append(_cyl("filler_cap", 0.012, 0.016, (0.05, 0, 0.078), tin, "metal", 12))
    objs.append(_cyl("burner_collar", 0.048, 0.022, (0, 0, 0.081), tin, "metal"))
    objs.append(_cyl("wick_knob", 0.01, 0.03, (0, -0.06, 0.084), tin, "metal", 12, rot=(math.pi / 2, 0, 0)))
    objs.append(_cyl("lamp_globe", 0.058, 0.08, (0, 0, 0.157), glow, "lamp"))                       # the bulbous glass: a barrel of three pieces (cylinder + two cones; a UV sphere exported
    objs.append(_cone("lamp_globe_top", 0.058, 0.036, 0.025, (0, 0, 0.2095), glow, "lamp"))         # with a non-deterministic triangle order, which the R4 determinism rule forbids)
    objs.append(_cone("lamp_globe_base", 0.036, 0.058, 0.025, (0, 0, 0.1045), glow, "lamp"))
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2; objs.append(_cyl("guard_wire_%d" % (k + 1), 0.0035, 0.13, (0.066 * math.cos(a), 0.066 * math.sin(a), 0.157), tin, "metal", 8))
    objs.append(_cone("top_cap", 0.07, 0.03, 0.04, (0, 0, 0.242), green, "metal"))
    objs.append(_cyl("chimney_vent", 0.022, 0.03, (0, 0, 0.277), green, "metal", 16))
    objs.append(_ring("wire_bail", 0.075, 0.004, (0, 0, 0.262), tin, "metal", rot=(math.pi / 2, 0, 0)))
    objs.append(_empty("grip", (0, 0, 0.333)))        # the top of the bail ring (0.262 + 0.075 - 0.004)
    objs.append(_empty("flame", (0, 0, 0.13)))        # the wick, inside the globe
    return objs
