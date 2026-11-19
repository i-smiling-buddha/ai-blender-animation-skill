---
name: ultimate-blender
description: All-in-one Blender 5.x skill for any Blender, bpy, .blend or 3D-asset task. Covers modeling, sculpting, retopo/UV, PBR, baking, rigging, animation, sims, VFX, lighting, rendering, game export, product turntables, Poly Haven, photo-to-3D, 90+ art styles. Drives Blender via blender-mcp or headless CLI.
license: MIT (see THIRD_PARTY_NOTICES.md for upstream terms)
compatibility: Blender 5.2 LTS or newer (verified on 5.3). Optional blender-mcp server (uvx blender-mcp, port 9876) for live sessions. Node.js for scripts/node. MESHY_API_KEY for photo-to-3D.
metadata:
  author: Fused by Smiling Buddha · DESITechnology
  version: "1.0.0"
  sources: kevinbadi/blender-skills, arjun988/blender-skills, el4cteo/blender-skills
---

# Ultimate Blender

One skill that fuses three packs: **el4cteo** (tested bpy scripts + Blender 5.x rules), **arjun988** (Technical Art Director workflow, 90+ specialist and style guides) and **kevinbadi** (product camera animations, Poly Haven, Meshy photo-to-3D, Three.js export).

How to use this file: read it first, then open **only** the guide(s) in the routing table that match the task. Don't load every guide. Each guide has sections from every source pack for that topic. All paths are relative to this skill's folder (`<skill_root>`).

## 1. Director workflow (every new asset)
```
ANALYZE → PLAN → BRIEF → EXECUTE → VALIDATE → DELIVER
```
1. **Analyze**: asset purpose (hero / standard / background), target (game / cinematic / portfolio / product video), platform (mobile / console / PC / web / Roblox), style, animation (static / rigged / animated), export format.
2. **Plan**: pick guides from the routing table (section 4), and set the poly and texture budgets (`refs/shared/polycount-budgets.md`).
3. **Brief**: for anything bigger than a quick edit, write a short production brief before touching Blender: asset, budgets, guides used, phases, export target.
4. **Execute**: run small steps through MCP or headless (section 2). Use the bundled scripts before writing new code.
5. **Validate**: follow section 5. This step is required.
6. **Deliver**: export, then report numbers and file paths.

**Reference image attached?** Follow `refs/shared/reference-image-match.md`: fill in `refs/shared/reference-analysis-template.md`, match the camera before micro-detail, loop on screenshot comparisons, then check against `refs/shared/visual-match-checklist.md`.
Full director playbook, with briefs, multi-skill recipes and decision trees: `refs/director-full.md`.
Naming: `refs/shared/naming-conventions.md` · Pipeline: `refs/shared/asset-pipeline.md` · MCP: `refs/shared/mcp-integration.md`, `refs/shared/mcp-tools.md`.

## 2. Execute
**Live (blender-mcp `execute_blender_code`)**: work in small steps and print only what you need. To call a bundled script:
```python
import sys, importlib; sys.path.insert(0, r"<skill_root>/scripts")
import qa_check; importlib.reload(qa_check); print(qa_check.run(objects=["Chair"]))
```
Each MCP call runs in a fresh namespace, so re-`import` every time. Use `reload` only after editing a script.

**Headless (shell, no MCP needed)**. This prints only the script's JSON:
```
python <skill_root>/scripts/run_in_blender.py --blend in.blend <skill_root>/scripts/<script.py> -- --objects Chair --save out.blend
python <skill_root>/scripts/run_in_blender.py --expr "import bpy; print(len(bpy.data.objects))"
```
**Windows**: prefer PowerShell. In Git Bash, prefix with `MSYS_NO_PATHCONV=1` and use `$(cygpath -m ~/.claude/skills)/ultimate-blender/...`. `blender.exe` must be on PATH, or pass its path.
**First call in a session**: run `scripts/env_report.py` (version, engines, GPU, add-ons, units, color management).
**Node helpers** (kevinbadi; they talk to blender-mcp on port 9876): `node <skill_root>/scripts/node/<name>.js --help`.

## 3. Blender 5.x rules (these override older advice in any guide)
- **Data API over operators**: use `bpy.data`, `bmesh`, `mesh.attributes`, and `foreach_get/set` with numpy. Operators need context, and background mode has no 3D View.
- **Unavoidable operator**: `with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]): bpy.ops...`, then check for `{'FINISHED'}`.
- **Edit Mode**: `ob.data` is stale while in Edit Mode. Use `bmesh.from_edit_mesh` + `update_edit_mesh`, or switch to OBJECT mode first.
- **Nodes**: find them by `type` (`"BSDF_PRINCIPLED"`), never by `name`, because names are localized.
- **Enums**: read them from `bl_rna.properties[p].enum_items`. For dynamic enums (`render.engine`, `view_transform`), assign inside `try/except TypeError`.
- **Engines**: `BLENDER_EEVEE`, `CYCLES`, `BLENDER_WORKBENCH`. GPU: `scene.cycles.device="GPU"` + the preferences `compute_device_type`.
- **Evaluated mesh**: `ob.evaluated_get(dg).to_mesh()`, then always `to_mesh_clear()`. Call `view_layer.update()` before reading `matrix_world`.
- **Freed data**: collect names before removing or applying anything, and never reuse the old Python reference.
- **Names**: never trust "Cube.001". Rename explicitly and look objects up with `bpy.data.objects[name]`.
- **Scale**: 1 unit = 1 m. Apply rotation and scale before bevels, rigging, physics, baking and export.
- **Live sessions are the user's work**: never `read_factory_settings`, never delete data you didn't create, and save a backup (`save_as_mainfile(copy=True)`) before destructive batch edits.
- **Background GPU**: call `gpu.init()` (5.2+). `bgl` no longer exists. Sculpt Mode crashes in `-b`, so use `scripts/sculpt_ops.py`.
- **5.x API breaks**: `action.fcurves` → channelbags · `scene.node_tree` → `scene.compositing_node_group` · `material.use_nodes` deprecated · `mod["Socket_2"]` → `mod.properties.inputs.Socket_2.value` · `BLENDER_EEVEE_NEXT` → `BLENDER_EEVEE` · Boolean `FAST` → `FLOAT` · bone layers → bone collections · `bl_info` → `blender_manifest.toml` · 5.3: compositor effects stack, VSE `EXPAND` → `RIPPLE`. Full table: `refs/blender-core/api-changes-5x.md`. Code patterns: `refs/blender-core/bpy-patterns.md`.

## 4. Routing: task → guide (+ scripts)
| Task | Open | Key scripts |
|---|---|---|
| Units, naming, collections, asset libraries, batch/headless pipelines, add-ons/extensions | `guides/01-scene-pipeline.md` | scene_audit, batch_process, `assets/addon_template` |
| Hard-surface, bevels, booleans, weighted normals, general modeling, procedural modeling | `guides/02-modeling-hardsurface.md` | apply_stack |
| Props, kitbash, furniture, vehicles, mechs, archviz | `guides/03-props-vehicles-archviz.md` | apply_stack, build_pbr_material |
| Sculpting, multires, remesh, creatures, monsters | `guides/04-sculpting-creatures.md` | sculpt_ops |
| Human characters, archetypes, clothing, face rig, ARKit / visemes | `guides/05-characters-clothing-face.md` | garment, shapekeys |
| Hair, fur, hair cards | `guides/06-hair-groom.md` | groom |
| Retopology, UV unwrap, texel density, UDIM, lightmap UV | `guides/07-retopology-uv.md` | auto_retopo, uv_pack, texel_density |
| PBR materials, wear and grime, decals, trim sheets, baking | `guides/08-materials-texturing-baking.md` | build_pbr_material, smart_material, decal, bake_maps |
| Geometry Nodes, procedural generators, scatter | `guides/09-geometry-nodes.md` | gn_builder |
| Terrain, biomes, modular kits, vegetation, set dressing | `guides/10-environments-vegetation.md` | terrain, scatter, kit_check |
| Rigify, skinning, game skeletons, keyframes, NLA, mocap retarget, loops | `guides/11-rigging-animation.md` | rigify_build, bind_mesh, rig_check, stress_poses, retarget, bake_action, loop_check |
| Rigid body, cloth, fluids, destruction, VFX, rain, snow, lightning | `guides/12-simulation-vfx-weather.md` | sim_setup, precipitation, surface_weather, lightning |
| Lighting rigs, HDRI, look-dev, camera, time of day, fog, moods | `guides/13-lighting-camera-lookdev.md` | turntable, scene_mood |
| Cycles/EEVEE settings, batch render, compositor | `guides/14-rendering-compositing.md` | render_batch |
| Poly budgets, LODs, draw calls, collision proxies | `guides/15-optimization-lod-collision.md` | mesh_stats, make_lods |
| Export glTF/FBX/USD for Unity, Unreal, Godot, Roblox, web/Three.js | `guides/16-export-engines.md` | export_asset, node/blender-threejs-export.js |
| QA before delivery (always) | `guides/17-qa-review.md` | qa_check, review_shots |
| Video Sequencer edits, motion tracking, camera solve | `guides/18-video-editing-tracking.md` | vse_edit, track_camera |
| Product videos: turntable, slow zoom, dolly, crane, speed-ramp loop, perfect loop, product polish | `guides/19-product-camera-animations.md` | node/blender-product-polish.js, turntable.py |
| Poly Haven HDRIs, textures, studio/showroom scenes, material variants | `guides/20-polyhaven-assets.md` | node/polyhaven-*.js |
| Photo(s) → textured 3D model (Meshy API, needs `MESHY_API_KEY`) | `guides/21-image-to-3d.md` | then auto_retopo, qa_check |
| End-to-end playbooks (prop, character, Roblox, product shot) | `guides/22-workflow-recipes.md` | |
| Optional external WebSocket toolkit (Mixamo retarget via Dev-GOM add-on) | `guides/23-websocket-toolkit.md` | (not bundled) |

**Style direction**: open one section from these files, not the whole file.
| Style ask | Open |
|---|---|
| Stylized, realistic, low-poly, anime/manga, chibi, cartoon, comic, hand-painted, pixel, voxel, isometric, HD-2D, retro 8/16-bit, noir, toon/NPR, console eras (PS1–PS5, CRT/VHS) | `styles/art-styles.md` |
| Horror, PSX horror, indie, found-footage, body, cosmic, folk, mascot horror, liminal, weirdcore | `styles/horror.md` |
| Fantasy, sci-fi/punk, apocalypse, historical, biomes, cozy, dark/gritty, surreal, brutalist, neon retrofuturism | `styles/worlds-moods.md` |
| Genre art direction: action, card/idle, metroidvania, VN, open world, platformer, racing, RPG, shooter, soulslike, stealth, strategy, survival | `styles/game-genres.md` |

Per-topic deep-dive references sit in `refs/<original-skill-name>/`, and guides link to them directly.

## 5. Verify (required before saying "done")
1. Report numbers, not adjectives: tris, objects, materials, dimensions (`ob.dimensions`) and the output files written.
2. If geometry changed, run `scripts/qa_check.py` (z-fighting, detached parts, non-manifold, flipped normals, scale).
3. Look at the result: MCP `get_viewport_screenshot` / `look`, or headless `scripts/review_shots.py` contact sheets.
4. For game assets, run `scripts/mesh_stats.py` against the platform budget, and go through `refs/shared/validation-checklist.md`.
5. Confirm that exported files exist and their size is non-zero.
