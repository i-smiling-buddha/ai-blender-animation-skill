"""Smoke-test every ultimate-blender script against real Blender (pip install bpy==5.3.0).

Each test starts from an empty factory scene, builds a tiny fixture, calls the
script's run(**kw) and checks that it returns a dict without raising.

    python tests/smoke_test.py            # all
    python tests/smoke_test.py qa_check   # some
"""
import os, sys, json, tempfile, traceback, importlib, time

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "skills", "ultimate-blender", "scripts")
sys.path.insert(0, SCRIPTS)
import bpy  # noqa: E402

TMP = tempfile.mkdtemp(prefix="ub_smoke_")


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def cube(name="Box", size=1.0, loc=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=size, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    return ob


def sphere(name="Ball", loc=(0, 0, 0), seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    return ob


def plane(name="Ground", size=10.0):
    bpy.ops.mesh.primitive_plane_add(size=size)
    ob = bpy.context.active_object
    ob.name = name
    return ob


def arm(name="Rig", bones=3):
    a = bpy.data.armatures.new(name)
    ob = bpy.data.objects.new(name, a)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    prev = None
    names = ["Hips", "Spine", "Chest", "Neck", "Head"][:bones]
    for i, n in enumerate(names):
        b = a.edit_bones.new(n)
        b.head = (0, 0, i * 0.5)
        b.tail = (0, 0, i * 0.5 + 0.5)
        if prev:
            b.parent = prev
            b.use_connect = True
        prev = b
    bpy.ops.object.mode_set(mode="OBJECT")
    return ob


def animated_rig(name="Rig", frames=24):
    ob = arm(name)
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, frames
    pb = ob.pose.bones["Spine"]
    pb.rotation_mode = "XYZ"
    for f, ang in ((1, 0.0), (frames // 2, 0.4), (frames, 0.0)):
        pb.rotation_euler = (ang, 0, 0)
        pb.keyframe_insert("rotation_euler", frame=f)
    return ob


def skinned():
    rig = arm()
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.5, location=(0, 0, 0.75), vertices=16)
    body = bpy.context.active_object
    body.name = "Body"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return rig, body


def save_blend(name):
    p = os.path.join(TMP, name)
    bpy.ops.wm.save_as_mainfile(filepath=p, copy=True)
    return p


def write_png(path, size=8):
    img = bpy.data.images.new(os.path.basename(path), size, size)
    img.pixels = [0.5] * (size * size * 4)
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    return path


# name -> callable returning kwargs (scene is already fresh)
def t_env_report():
    return {}

def t_scene_audit():
    cube(); return {}

def t_apply_stack():
    cube(); return {"objects": ["Box"]}

def t_auto_retopo():
    sphere(seg=64); return {"objects": ["Ball"], "method": "decimate", "tris": 500}

def t_uv_pack():
    cube(); return {"objects": ["Box"]}

def t_texel_density():
    cube(); bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.uv.smart_project(); bpy.ops.object.mode_set(mode="OBJECT")
    return {"objects": ["Box"]}

def t_build_pbr_material():
    cube(); return {"name": "M_Test", "objects": ["Box"], "color": (0.8, 0.2, 0.1)}

def t_smart_material():
    ob = cube()
    m = bpy.data.materials.new("M_Base"); ob.data.materials.append(m)
    return {"objects": ["Box"], "wear": 0.5, "grime": 0.3}

def t_decal():
    cube(); return {"target": "Box", "at": (0, -0.6, 0), "color": (1, 0, 0), "size": 0.3}

def t_bake_maps():
    ob = cube()
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.uv.smart_project(); bpy.ops.object.mode_set(mode="OBJECT")
    m = bpy.data.materials.new("M_Bake"); ob.data.materials.append(m)
    return {"low": "Box", "maps": ["ao"], "res": 64, "samples": 4, "out": TMP}

def t_gn_builder():
    cube()
    spec = {"name": "GN_Test", "tree": "geometry",
            "inputs": [["Geometry", "GEOMETRY"], ["Height", "FLOAT", 2.0]], "outputs": [["Geometry", "GEOMETRY"]],
            "nodes": {"t": ["GeometryNodeTransform"]},
            "links": [["in.Geometry", "t.Geometry"], ["t.Geometry", "out.Geometry"]]}
    return {"spec": spec, "apply_to": "Box", "set": ["Height=3"]}

def t_mesh_stats():
    cube(); sphere(loc=(3, 0, 0)); return {}

def t_make_lods():
    sphere(seg=48); return {"objects": ["Ball"], "ratios": [0.5, 0.25]}

def t_qa_check():
    cube(); return {"objects": ["Box"]}

def t_review_shots():
    cube(); return {"objects": ["Box"], "out": os.path.join(TMP, "review.png"), "res": 128}

def t_export_asset():
    cube(); return {"preset": "gltf", "objects": ["Box"], "out": os.path.join(TMP, "box.glb")}

def t_kit_check():
    ob = cube(size=1.0, loc=(0.5, 0.5, 0.5)); ob.name = "SM_Wall"; return {"objects": ["SM_Wall"]}

def t_terrain():
    return {"size": 20.0, "res": 33, "height": 3.0}

def t_scatter():
    plane()
    col = bpy.data.collections.new("Rocks"); bpy.context.scene.collection.children.link(col)
    r = bpy.data.objects.new("Rock", bpy.data.meshes.new("Rock")); col.objects.link(r)
    return {"target": "Ground", "collection": "Rocks", "density": 0.5}

def t_sculpt_ops():
    sphere(); return {"objects": ["Ball"], "ops": ["remesh=0.1", "smooth=2"]}

def t_turntable():
    cube(); return {"objects": ["Box"], "frames": 24}

def t_scene_mood():
    cube(); return {"time": "sunset", "mood": "horror"}

def t_toon_setup():
    ob = cube(); ob.data.materials.append(bpy.data.materials.new("M_Toon")); return {"objects": ["Box"]}

def t_surface_weather():
    ob = cube(); ob.data.materials.append(bpy.data.materials.new("M_Wet")); return {"objects": ["Box"], "wetness": 0.6}

def t_precipitation():
    plane(); return {"type": "rain", "ground": "Ground"}  # str on purpose (MCP style)

def t_lightning():
    return {"flashes": 1}

def t_sim_setup():
    cube(loc=(0, 0, 3)); plane(); return {"rigid": True, "active": ["Box"], "passive": ["Ground"]}

def t_render_batch():
    cube()
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); bpy.context.scene.collection.objects.link(cam)
    cam.location = (4, -4, 3); cam.rotation_euler = (1.1, 0, 0.78); bpy.context.scene.camera = cam
    return {"engine": "BLENDER_WORKBENCH", "res": (64, 64), "out": os.path.join(TMP, "r_####")}

def t_garment():
    _, body = skinned()
    return {"body": "Body", "zmin": 1.4, "zmax": 1.6, "name": "Shirt"}

def t_shapekeys():
    sphere(); return {"mesh": "Ball", "create": "visemes"}

def t_bind_mesh():
    skinned(); return {"armature": "Rig", "meshes": ["Body"]}

def t_rig_check():
    rig, body = skinned()
    mod = body.modifiers.new("Armature", "ARMATURE"); mod.object = rig; body.parent = rig
    for b in rig.data.bones:
        body.vertex_groups.new(name=b.name)
    return {"armature": "Rig", "meshes": ["Body"]}

def t_stress_poses():
    arm(bones=5); return {"armature": "Rig"}

def t_loop_check():
    animated_rig(); return {"object": "Rig"}

def t_bake_action():
    src = animated_rig("Ctrl")
    tgt = arm("Game")
    return {"source": "Ctrl", "target": "Game"}

def t_retarget():
    animated_rig("Mocap"); arm("Target"); return {"source": "Mocap", "target": "Target"}

def t_rigify_build():
    return {"add": "human"}

def t_groom():
    sphere(); return {"surface": "Ball", "density": 50.0, "children": 0.0}

def t_vse_edit():
    a = write_png(os.path.join(TMP, "a.png")); b = write_png(os.path.join(TMP, "b.png"))
    return {"clips": [a, b], "still_seconds": 1.0}

def t_track_camera():
    return None  # needs real footage: skipped

def t_batch_process():
    cube(); p = save_blend("in.blend"); fresh()
    return {"inp": [p], "op": "report"}

TESTS = {k[2:]: v for k, v in sorted(globals().items()) if k.startswith("t_")}


def main(only):
    results = {}
    for name, fx in TESTS.items():
        if only and name not in only:
            continue
        fresh()
        t0 = time.time()
        try:
            kw = fx()
            if kw is None:
                results[name] = ("SKIP", "needs external input")
                continue
            mod = importlib.import_module(name)
            out = mod.run(**kw)
            ok = isinstance(out, dict) and not out.get("error")
            results[name] = ("PASS" if ok else "FAIL", json.dumps(out, default=str)[:300])
        except SystemExit as e:
            results[name] = ("FAIL", f"SystemExit {e}")
        except Exception as e:  # noqa: BLE001
            results[name] = ("FAIL", "".join(traceback.format_exception_only(type(e), e)).strip()[:400])
        results[name] += (round(time.time() - t0, 1),)
    width = max(map(len, results)) if results else 0
    for n, (st, msg, *dt) in results.items():
        print(f"{st:4} {n:<{width}} {dt[0] if dt else ''}s  {msg if st != 'PASS' else ''}")
    fails = [n for n, r in results.items() if r[0] == "FAIL"]
    print(f"\n{len(results) - len(fails)}/{len(results)} ok (incl. skips), {len(fails)} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(set(sys.argv[1:])))
