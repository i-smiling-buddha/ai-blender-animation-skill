"""Render the README hero image with ultimate-blender's own scripts (Blender 5.3, Cycles CPU)."""
import sys, os, math
SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills", "ultimate-blender", "scripts")
sys.path.insert(0, SCRIPTS)
import bpy
import build_pbr_material, smart_material, turntable, apply_stack  # noqa: E401

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def add(op, name, **kw):
    op(**kw); ob = bpy.context.active_object; ob.name = name; return ob

# pedestal + hero objects
ped = add(bpy.ops.mesh.primitive_cylinder_add, "Pedestal", radius=1.6, depth=0.4, location=(0, 0, -0.2), vertices=96)
monkey = add(bpy.ops.mesh.primitive_monkey_add, "Hero", location=(0, 0, 0.9))
monkey.rotation_euler = (math.radians(-10), 0, math.radians(20))
monkey.modifiers.new("Sub", "SUBSURF").levels = 2
bpy.ops.object.shade_smooth()
crate = add(bpy.ops.mesh.primitive_cube_add, "Crate", size=0.7, location=(1.15, -0.55, 0.35))
crate.rotation_euler = (0, 0, math.radians(25))
orb = add(bpy.ops.mesh.primitive_uv_sphere_add, "Orb", radius=0.32, location=(-1.1, -0.5, 0.32), segments=64, ring_count=32)
bpy.ops.object.shade_smooth()
for ob in (crate,):
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
apply_stack.run(objects=["Crate"], preset="midpoly")

build_pbr_material.run(name="M_Gold", preset="gold", objects=["Hero"])
build_pbr_material.run(name="M_Ped", color=(0.06, 0.06, 0.08), objects=["Pedestal"])
build_pbr_material.run(name="M_Crate", color=(0.9, 0.35, 0.05), objects=["Crate"])
# (wear needs mid-poly curvature; skipped on this low-poly crate)
build_pbr_material.run(name="M_Orb", color=(0.15, 0.45, 1.0), objects=["Orb"])

tt = turntable.run(objects=["Hero", "Crate", "Orb", "Pedestal"], rig="studio", frames=1, lens=50.0)
print("turntable:", {k: tt[k] for k in list(tt)[:6]})

# dark backdrop world
w = sc.world or bpy.data.worlds.new("W"); sc.world = w
bg = next((n for n in w.node_tree.nodes if n.type == "BACKGROUND"), None)
if bg:
    bg.inputs["Color"].default_value = (0.01, 0.01, 0.02, 1); bg.inputs["Strength"].default_value = 1.0

sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 96
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.film_transparent = True
sc.frame_set(1)
cam = sc.camera
# frame hero on the right part of the image
cam.data.shift_x = -0.22
sc.render.filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hero.png")
bpy.ops.render.render(write_still=True)
print("rendered", os.path.getsize(sc.render.filepath))
