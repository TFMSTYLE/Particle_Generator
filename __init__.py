# SPDX-FileCopyrightText: 2025-2026 The French Monkey
# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "Particle",
    "author": "The French Monkey",
    "version": (1, 0, 2),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Particle",
    "description": "Generate parametric particle",
    "category": "Add Mesh",
    "license": "GPL-3.0-or-later",
}

import bpy, math, random
from math import sin, cos, tau

try:
    from . import relay_updater
except ImportError:  # the Addon Collection has its own updates
    relay_updater = None

# ------------------------------------------------------------------------
# Geometry Nodes Instancer
# ------------------------------------------------------------------------

def ensure_gn_instancer(obj, scale_min=0.6, scale_max=1.2):
    group_name = "PG_Instancer"
    ng = bpy.data.node_groups.get(group_name)
    if not ng:
        ng = bpy.data.node_groups.new(group_name, "GeometryNodeTree")

        iface = ng.interface
        iface.clear()
        iface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        iface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

        nodes = ng.nodes
        links = ng.links
        nodes.clear()

        n_in = nodes.new("NodeGroupInput");  n_in.location = (-600, 0)
        n_out = nodes.new("NodeGroupOutput"); n_out.location = (800, 0); n_out.is_active_output = True

        n_m2p = nodes.new("GeometryNodeMeshToPoints")
        n_m2p.location = (-400, 0)
        n_m2p.mode = "VERTICES"

        n_ico = nodes.new("GeometryNodeMeshIcoSphere")
        n_ico.location = (-150, -100)
        n_ico.inputs["Subdivisions"].default_value = 1
        n_ico.inputs["Radius"].default_value = 0.03  

        n_rand = nodes.new("FunctionNodeRandomValue")
        n_rand.location = (100, 150)
        n_rand.data_type = 'FLOAT'
        n_rand.inputs["Min"].default_value = scale_min
        n_rand.inputs["Max"].default_value = scale_max

        n_inst = nodes.new("GeometryNodeInstanceOnPoints"); n_inst.location = (250, 0)
        n_real = nodes.new("GeometryNodeRealizeInstances"); n_real.location = (450, 0)

        n_setmat = nodes.new("GeometryNodeSetMaterial"); n_setmat.location = (650, 0)

        links.new(n_in.outputs[0], n_m2p.inputs["Mesh"])
        links.new(n_m2p.outputs["Points"], n_inst.inputs["Points"])
        links.new(n_ico.outputs["Mesh"], n_inst.inputs["Instance"])
        links.new(n_rand.outputs["Value"], n_inst.inputs["Scale"])
        links.new(n_inst.outputs["Instances"], n_real.inputs["Geometry"])
        links.new(n_real.outputs["Geometry"], n_setmat.inputs["Geometry"])
        links.new(n_setmat.outputs["Geometry"], n_out.inputs[0])

        ng.interface_update(bpy.context)

    mod = next((m for m in obj.modifiers if m.type == "NODES" and m.node_group == ng), None)
    if not mod:
        mod = obj.modifiers.new("PG_Instancer", "NODES")
        mod.node_group = ng

    rand_node = next((n for n in ng.nodes if n.type == "RANDOM_VALUE"), None)
    mat_node = next((n for n in ng.nodes if n.type == "SET_MATERIAL"), None)

    if rand_node:
        rand_node.inputs["Min"].default_value = scale_min
        rand_node.inputs["Max"].default_value = scale_max

    if mat_node:
        mat = bpy.data.materials.get("ParticleMaterial")
        if not mat:
            mat = bpy.data.materials.new("ParticleMaterial")
        mat_node.inputs["Material"].default_value = mat

# ------------------------------------------------------------------------
# Pattern Generators
# ------------------------------------------------------------------------

def build_points(name, positions):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(positions, [], [])
    mesh.update()
    return mesh

def pattern_galaxy(count, radius, arms, spin, noise, seed):
    rng = random.Random(seed)
    pts = []
    for i in range(count):
        arm = i % max(1, arms)
        angle = (i / count) * spin * tau + (arm / arms) * tau
        r = (i / count) * radius
        x = r * cos(angle) + rng.uniform(-noise, noise)
        y = r * sin(angle) + rng.uniform(-noise, noise)
        z = rng.uniform(-noise, noise) * 0.5
        pts.append((x, y, z))
    return pts

def pattern_sphere(count, radius, thickness, noise, seed):
    rng = random.Random(seed)
    pts = []
    for _ in range(count):
        u = rng.random(); v = rng.random()
        theta = 2 * tau * u; phi = math.acos(2 * v - 1)
        r = radius - rng.random() * thickness
        x = r * sin(phi) * cos(theta) + rng.uniform(-noise, noise)
        y = r * sin(phi) * sin(theta) + rng.uniform(-noise, noise)
        z = r * cos(phi) + rng.uniform(-noise, noise)
        pts.append((x, y, z))
    return pts

def pattern_ring(count, radius, thickness, noise, seed):
    rng = random.Random(seed)
    pts = []
    for _ in range(count):
        a = rng.random() * tau
        r = radius + rng.uniform(-noise, noise) * 0.2
        x = r * cos(a)
        y = r * sin(a)
        z = rng.uniform(-thickness, thickness) * 0.5
        pts.append((x, y, z))
    return pts

def pattern_cloud(count, radius, thickness, noise, seed):
    rng = random.Random(seed)
    pts = []
    for _ in range(count):

        theta = rng.random() * tau
        phi = math.acos(2 * rng.random() - 1)

        r = radius * (rng.random() ** (1/3))
        x = r * sin(phi) * cos(theta)
        y = r * sin(phi) * sin(theta)
        z = r * cos(phi) * (thickness * 0.5) 

        x += rng.uniform(-noise, noise)
        y += rng.uniform(-noise, noise)
        z += rng.uniform(-noise * 0.5, noise * 0.5)

        pts.append((x, y, z))
    return pts

# ------------------------------------------------------------------------
# Rebuild / Generate
# ------------------------------------------------------------------------

def rebuild_particles(obj):
    if not obj or obj.type != "MESH": return False
    ptype = obj["ptype"]
    count = obj["count"]; radius = obj["radius"]; noise = obj["noise"]; seed = obj["seed"]
    arms = obj["arms"]; spin = obj["spin"]; thickness = obj["thickness"]
    scale_min = obj["scale_min"]; scale_max = obj["scale_max"]

    if ptype == "GALAXY":
        pts = pattern_galaxy(count, radius, arms, spin, noise, seed)
    elif ptype == "RING":
        pts = pattern_ring(count, radius, thickness, noise, seed)
    elif ptype == "CLOUD":
        pts = pattern_cloud(count, radius, thickness, noise, seed)
    else:
        pts = pattern_sphere(count, radius, thickness, noise, seed)

    mesh = build_points("ParticlePoints", pts)
    old = obj.data; obj.data = mesh
    if old and old.users == 0: bpy.data.meshes.remove(old)
    ensure_gn_instancer(obj, scale_min, scale_max)
    return True

def generate_particles(context):
    p = context.scene.pgen_props
    obj = context.active_object
    keys = ("ptype","count","radius","thickness","noise","seed","arms","spin",
            "scale_min","scale_max")

    if obj and obj.type=="MESH" and "particle_generator" in obj and obj.select_get():
        for k in keys: obj[k]=getattr(p,k)
        rebuild_particles(obj)
        obj.name=obj.data.name=f"Particles_{p.ptype}"
        return obj

    mesh=bpy.data.meshes.new("ParticlePoints")
    new_obj=bpy.data.objects.new(f"Particles_{p.ptype}", mesh)
    context.collection.objects.link(new_obj)
    context.view_layer.objects.active=new_obj
    new_obj.select_set(True)
    for k in keys: new_obj[k]=getattr(p,k)
    new_obj["particle_generator"]=True
    rebuild_particles(new_obj)
    return new_obj

# ------------------------------------------------------------------------
# Live Update
# ------------------------------------------------------------------------

def update_particles(self, context):
    p = context.scene.pgen_props
    if not p.live_update:
        return

    o = context.active_object
    if not o or "particle_generator" not in o:
        return

    for k in (
        "ptype", "count", "radius", "thickness", "noise", "seed",
        "arms", "spin", "scale_min", "scale_max"
    ):
        o[k] = getattr(p, k)

    rebuild_particles(o)

    o.name = o.data.name = f"Particles_{p.ptype}"

# ------------------------------------------------------------------------
# UI
# ------------------------------------------------------------------------

class PGProperties(bpy.types.PropertyGroup):
    live_update: bpy.props.BoolProperty(name="Live Update", default=False)
    ptype: bpy.props.EnumProperty(
        name="Pattern",
        items=[("GALAXY","Galaxy",""),("SPHERE","Sphere",""),
               ("RING","Ring",""),("CLOUD","Cloud","")],
        default="SPHERE", update=update_particles)
    count: bpy.props.IntProperty(name="Particle Count", default=300, min=1, max=100000, subtype='FACTOR', update=update_particles)
    radius: bpy.props.FloatProperty(name="Radius", default=5.0, min=0.001, max=100.0, subtype='FACTOR', update=update_particles)
    thickness: bpy.props.FloatProperty(name="Thickness", default=1.0, min=0.0, max=100.0, subtype='FACTOR', update=update_particles)
    noise: bpy.props.FloatProperty(name="Noise", default=0.5, min=0.0, max=10.0, subtype='FACTOR', update=update_particles)
    seed: bpy.props.IntProperty(name="Seed", default=0, min=0, max=9999, subtype='FACTOR', update=update_particles)
    arms: bpy.props.IntProperty(name="Arms", default=3, min=1, max=12, subtype='FACTOR', update=update_particles)
    spin: bpy.props.FloatProperty(name="Spin", default=2.5, min=0.1, max=20.0, subtype='FACTOR', update=update_particles)
    scale_min: bpy.props.FloatProperty(name="Scale Min", default=0.6, min=0.0, max=10.0, subtype='FACTOR', update=update_particles)
    scale_max: bpy.props.FloatProperty(name="Scale Max", default=1.2, min=0.0, max=10.0, subtype='FACTOR', update=update_particles)

class PG_OT_generate(bpy.types.Operator):
    bl_idname = "pg.generate"
    bl_label = "Generate Particles"
    bl_options = {"REGISTER","UNDO"}
    def execute(self, context):
        generate_particles(context)
        return {"FINISHED"}

# ------------------------------------------------------------------------
# UI
# ------------------------------------------------------------------------

class VIEW3D_PT_particle_generator(bpy.types.Panel):
    bl_label = "Particle"
    bl_idname = "VIEW3D_PT_particle_generator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Particle"

    def draw(self, context):
        if relay_updater:
            relay_updater.draw(self.layout)
        layout = self.layout
        p = context.scene.pgen_props
        o = context.object

        layout.operator("pg.generate", text="Generate Particles", icon="OUTLINER_OB_POINTCLOUD")

        layout.prop(p, "live_update", toggle=True)
        layout.separator(factor=0.5)

        layout.prop(p, "ptype", expand=True)

        layout.prop(p, "count")
        layout.prop(p, "radius")
        layout.prop(p, "thickness")
        layout.prop(p, "noise")
        layout.prop(p, "seed")

        if p.ptype == "GALAXY":
            layout.prop(p, "arms")
            layout.prop(p, "spin")

        layout.separator(factor=0.5)

        layout.label(text="Instance Scale Range:")
        layout.prop(p, "scale_min")
        layout.prop(p, "scale_max")

        layout.separator(factor=0.5)

        if o and o.type == "MESH" and "particle_generator" in o and o.select_get():
            layout.label(text=f"Editing: {o.name}", icon="OUTLINER_OB_POINTCLOUD")
        else:
            layout.label(text="No particle system selected", icon="INFO")

# ------------------------------------------------------------------------
# Registration
# ------------------------------------------------------------------------

classes = (
    PGProperties,
    PG_OT_generate,
    VIEW3D_PT_particle_generator,
)

def register():
    if relay_updater:
        relay_updater.register("blender-particle")
    for c in classes: bpy.utils.register_class(c)
    bpy.types.Scene.pgen_props = bpy.props.PointerProperty(type=PGProperties)

def unregister():
    if relay_updater:
        relay_updater.unregister()
    for c in reversed(classes): bpy.utils.unregister_class(c)
    del bpy.types.Scene.pgen_props

if __name__ == "__main__":
    register()
