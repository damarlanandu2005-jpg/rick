"""Blender representation of the flight_coin prop: build(radius, color_hex) -> the object, named flight_coin (what the lock motion and the layer gate match by name). Procedural, no external file."""
import bpy
def build(radius=0.07, color=(1.0, 0.0, 0.84, 1.0)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=32, ring_count=16); o = bpy.context.active_object; o.name = "flight_coin"
    m = bpy.data.materials.new("flight_coin"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = color
    out = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], out.inputs[0]); o.data.materials.append(m); return o
