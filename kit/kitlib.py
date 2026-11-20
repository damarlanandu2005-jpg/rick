"""kit/kitlib.py -- small Blender helpers shared by the parts library (conventions taken from the casino build: textured faces are separate
zero-thickness panels set slightly in front of a solid; materials are cached; every drawn surface has UVs)."""
import os, math, bpy
from blender_look import materials as M

_img_mats = {}
def sign_mat(tex_dir, png, emit=0.22):
    key = (tex_dir, png)
    if key in _img_mats: return _img_mats[key]
    path = os.path.join(tex_dir or "", png)
    if not os.path.isfile(path): return None
    m = bpy.data.materials.new("sign_" + png); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"]); nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Roughness"].default_value = 0.7; b.inputs["Emission Strength"].default_value = emit
    m.use_backface_culling = False; _img_mats[key] = m; return m

def panel(scene, name, w, h, loc, mat, side, kind=None, tally=None):
    """quad on a plane x = const facing the street centre (side -1 = building on the camera's left, so it faces +x). Text reads left to right as seen from the street."""
    me = bpy.data.meshes.new(name)
    v = [(0, -w / 2, -h / 2), (0, w / 2, -h / 2), (0, w / 2, h / 2), (0, -w / 2, h / 2)]
    me.from_pydata(v, [], [(0, 1, 2, 3)] if side < 0 else [(3, 2, 1, 0)])
    uv = me.uv_layers.new(); us = [(0, 0), (1, 0), (1, 1), (0, 1)]
    for lp in me.loops:
        u, vv = us[me.polygons[0].vertices[lp.index - me.polygons[0].loop_start]]; uv.data[lp.index].uv = (u if side < 0 else 1 - u, vv)
    if mat is not None: me.materials.append(mat)
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob); ob.location = loc
    if tally is not None: tally.add(kind or name)
    return ob

def spin_driver(ob, expr, axis=0):
    """motion without keyframe API differences: a scripted-expression driver on rotation (frame is the scene frame)"""
    fc = ob.driver_add("rotation_euler", axis); fc.driver.type = "SCRIPTED"; fc.driver.expression = expr; return fc
