# Export: Unity, Unreal, Godot, Roblox, web

> Fused guide. Script paths like `scripts/x.py` are relative to the **ai-blender-animation-skill skill root**; all Python helpers live in one flat `scripts/` folder (shared `_bpyx.py`). Node helpers are in `scripts/node/`. Where two sources disagree, prefer the Blender 5.x rules in SKILL.md.

Sections: `blender-export-pipelines`, `export-pipeline`, `unity-export`, `unreal-export`, `godot-export`, `threejs-export`


---

## ◆ blender-export-pipelines  _(source: el4cteo)_

> Export from Blender 5.3 with verified presets - Roblox (FBX/glTF, cages, R15, SurfaceAppearance), Unity (FBX, Humanoid), Unreal (FBX skeletal, Nanite, UCX), Godot/web (GLB, meshopt/Draco, WebP), USD. Scale/axes, smoothing, tangents, leaf bones, clips, batch export, post-export verification. Use whenever an asset leaves Blender.

## Export Pipelines

The execution model is in `blender-core` (→ SKILL.md). Run `blender-asset-qa` (→ guides/17-qa-review.md) (and `blender-game-optimization` (→ guides/15-optimization-lod-collision.md) for budgets) **before** exporting.

### One call
```
scripts/export_asset.py -- --preset unreal_skeletal --objects SK_Hero --out //export/SK_Hero.fbx
scripts/export_asset.py -- --preset web --collection Export --out //export/scene.glb
scripts/export_asset.py -- --preset unity --objects SM_A SM_B SM_C --batch --out //export/x.fbx   # one file each, at origin
```
Presets: `roblox`, `roblox_gltf`, `unity`, `unity_skeletal`, `unreal`, `unreal_skeletal`, `godot`, `web`, `gltf`, `usd`. Pass any exporter kwarg with `--set key=value`. Every preset is tested with a round-trip that keeps scale and avoids a 100× armature scale.

### Engine reference (load only the one you need)
- [../refs/blender-export-pipelines/roblox.md](../refs/blender-export-pipelines/roblox.md): MeshParts, avatar bodies (R15), accessories, layered clothing cages, SurfaceAppearance, limits
- [../refs/blender-export-pipelines/unity.md](../refs/blender-export-pipelines/unity.md): FBX settings, Humanoid rigs, URP/HDRP maps, animation clips
- [../refs/blender-export-pipelines/unreal.md](../refs/blender-export-pipelines/unreal.md): static/skeletal FBX, root bone, collision UCX, LODs, Nanite, ORM/DirectX
- [../refs/blender-export-pipelines/godot-web.md](../refs/blender-export-pipelines/godot-web.md): glTF/GLB, import suffixes, three.js/Babylon, compression, KHR extensions

### Universal pre-export checklist
1. **Scale**: scene unit scale 1.0, objects at scale 1, rotation applied (except intentional object transforms). The presets handle unit conversion.
2. **Pivot/origin** where the engine expects it: props at the bottom-center, characters at the world origin between the feet, facing **-Y** (Blender front). Every preset converts that to the engine's forward.
3. **Modifiers**: the presets export the evaluated mesh. Mirror, bevel and weighted normals are kept; booleans become real geometry.
4. **Normals**: custom/weighted normals export. Smooth shading, plus hard edges marked sharp.
5. **Triangulation**: FBX presets triangulate (`use_triangles`) so the bake and engine tangents match. glTF always triangulates.
6. **Materials**: image-texture → Principled chains only, with names `M_*` and textures `T_*`. Procedural nodes don't export, so bake them first.
7. **Armature**: deform bones only, no leaf bones, rest pose = bind pose, 4 weights per vertex max, and the root at the origin.
8. **Animation**: one action per clip, named `Rig_Clip`. Bake constraints/IK to keys (`blender-animation` (→ guides/11-rigging-animation.md)). FBX exports the active/NLA action per preset settings; glTF `ACTIONS` mode exports every action that has a slot for the armature.
9. **Naming**: unique, ASCII, no spaces. Engines key materials/meshes by name across reimports.

### Format choice
| Need | Format |
|---|---|
| Unity, Unreal (most stable for skeletal) | FBX |
| Godot, web, Roblox (supported), Unreal 5.x Interchange, Blender↔Blender | glTF 2.0 (`.glb`) |
| Film/VFX, Omniverse, Apple AR (`.usdz`), layout interchange | USD |
| Static geometry for printing/CAD | OBJ / STL (`wm.obj_export`, `wm.stl_export`) |
| Point caches / deforming sims | Alembic (`wm.alembic_export`) |

### Verify after export (required)
- The script returns `ok`, the file size, and for `.glb` a parsed summary (meshes, materials, images, animations, skins, tris, extensions). Compare it with what you expected.
- For FBX/USD: re-import into an empty scene (`import_scene.fbx` / `wm.usd_import`) and check `dimensions`, the armature scale (must be 1, not 100) and the action count.
- In the engine: scale against a reference (UE mannequin 180 cm, Unity capsule 2 m, Roblox character 5 studs), normals/smoothing, the normal map's green channel, and animation root motion.

### Collection exporters (re-export in one click, 4.2+)
See `blender-scene-setup` (→ guides/01-scene-pipeline.md): `collection.exporters` stores the format + settings per collection, and `bpy.ops.wm.collection_export_all()` re-exports everything.

### Gotchas
- FBX `use_tspace` fails silently on n-gons. Triangulate first (the presets do).
- `bake_space_transform` (Apply Transform) is experimental. Use it for Unity static meshes only, never with armatures.
- glTF exports **actions** linked through slots/NLA. An action with no user on the armature is skipped (`export_animation_mode` options: `ACTIONS`, `ACTIVE_ACTIONS`, `NLA_TRACKS`, `SCENE`, `BROADCAST`).
- glTF needs image textures in PNG/JPEG/WebP. EXR/TIFF get converted (`export_image_format`).
- 5.3 glTF: `export_image_add_webp`/`export_image_webp_fallback` became `export_image_add_compressed_images` + `export_compressed_images_type` (`WEBP`/`KTX2`) + `export_compressed_images_fallback`. `at_collection_center` became `collection_center_mode`. Point clouds export (`export_pointclouds`).
- Linked library data exports fine, but make it local or override it if you need to modify it first.
- Shape keys: FBX exports them as blendshapes, glTF as morph targets (`export_morph`). Modifiers before the Armature modifier can block shape-key export in FBX (apply them first).


---

## ◆ export-pipeline  _(source: arjun988)_

> Production export from Blender to FBX, GLTF, OBJ, USD, and Alembic with scale, pivot, rotation, normals, materials, animation, and collision verification via MCP.

## Export Pipeline

Verified, engine-ready exports. Correct scale, axis, pivots, and data.

### When to Use

- Final asset delivery
- Engine import preparation
- Animation/rig export
- Batch export of modular kits

### Pre-Export Gate

**Required:** asset-optimization validation PASS before export.

### Workflow

```
Validation PASS → Export Settings → Test Export → Engine Verify
    → Fix Issues → Final Export → Documentation
```

### Format Selection

| Format | Best For |
|--------|----------|
| FBX | Unreal, Unity (legacy), animation |
| GLTF/GLB | Web, Godot, modern Unity |
| OBJ | Static mesh interchange (no rig) |
| USD | Pipelines, VFX, multi-asset |
| Alembic | VFX caches, sculpt animation |

### FBX Settings (Game Default)

```
Scale: 1.0
Apply Scalings: FBX All
Forward: -Z Forward
Up: Y Up
Apply Unit: ON
Mesh: ON
Armature: ON (if rigged)
Bake Animation: ON (if animated)
Path Mode: Copy (embed textures)
```

### GLTF Settings

```
Format: GLB (single file) or GLTF Separate
Include: Selected Objects
Transform: +Y Up
Compression: Draco (if supported by engine)
```

### Export Verification Matrix

| Check | Method |
|-------|--------|
| Scale | Measure known dimension in engine |
| Pivot | Verify floor contact / grip point |
| Forward axis | Compare to engine convention |
| Normals | Check shading in engine |
| Materials | Verify slot count and textures |
| Animation | Play action in engine |
| Collision | Import COL_ mesh separately |

### Engine-Specific Notes

#### Unreal Engine
- Scale 1.0 = 1cm in UE (confirm project; may need 0.01 export scale)
- Import normals and tangents
- Separate collision mesh import
- LOD naming for auto-LOD: `SM_Asset_LOD0`

#### Unity
- Scale 1.0 typically correct
- GLTF preferred for modern pipelines
- Humanoid rig mapping for characters

#### Godot
- GLTF/GLB preferred
- +Y up default

### Collision Export

```
1. Export render mesh separately from collision
2. Collision: simple convex or box
3. Name: SM_Asset_COL
4. No materials on collision mesh
5. Apply transforms before export
```

### Animation Export

- Single action per export file (or document action list)
- Sample rate: 30fps default
- Bake constraints before export
- Include armature + skinned mesh in same file
- No unapplied scale on rig

### Batch Export (Modular Kits)

```
1. Select COL_Export collection
2. Export each module OR combined atlas per project spec
3. Maintain consistent origin per module type
4. Document grid snap points in README
```

### MCP Integration

1. Select export collection via MCP
2. Configure export settings via MCP
3. Execute export via MCP
4. Verify output file exists
5. Log export settings in delivery documentation

### Delivery Documentation Template

```markdown
### Export Package: [Asset Name]

**Format:** FBX / GLTF
**Scale:** 1 Blender unit = 1 meter
**Forward:** -Y / +X (document actual)
**Files:**
- SM_Asset.fbx
- T_Asset_BC.png, T_Asset_N.png, ...

**Import Notes:**
- [Engine-specific steps]

**Validation:** PASS — [date]
```

### Constraints

#### MUST DO
- Pass asset-optimization before export
- Apply transforms on export objects
- Test import in target engine
- Document scale and axis conventions
- Export collision separately for games

#### MUST NOT DO
- Export with unapplied scale
- Export without validation
- Mix collision and render in same export without documentation
- Assume default FBX settings work for all engines
- Export all modifiers without testing engine result

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Engine import | `../refs/export-pipeline/engine-import.md` | First import test |
| Validation | `../refs/shared/validation-checklist.md` | Pre-export gate |


---

## ◆ unity-export  _(source: arjun988)_

> Unity-specific Blender export for scale, axis, materials, humanoid/generic rigs, LODs, and collision import via MCP.

## Unity Export

Unity-ready transforms, materials, LODs, and collision. Prefer GLB/GLTF for modern; FBX for legacy/animation.

### When to Use

- Shipping assets to Unity
- Humanoid character export
- Prefab-oriented mesh splits and LODs

### Pre-Flight

1. `asset-optimization` (→ guides/15-optimization-lod-collision.md) PASS
2. `lod-pipeline` (→ guides/15-optimization-lod-collision.md) if LODs required
3. `collision-proxy` (→ guides/15-optimization-lod-collision.md) if physics required
4. Apply transforms; correct pivots

### Recommended Formats

| Case | Format |
|------|--------|
| Static mesh modern | GLB |
| Animated / humanoid | FBX |
| Simple props | GLB or FBX |

### Transform Defaults

```
Unit: Meters (Unity 1 unit = 1m)
Forward: -Z (Blender) → verify in Unity
Scale Factor: 1.0 (fix if model tiny/huge)
```

### Materials

- Prefer single material slots matching Unity workflow
- Metallic-Roughness for GLTF
- Embed or provide textures beside FBX
- Name materials `MAT_` consistently

### Characters

- T-pose or A-pose per project
- Root bone at origin; hips correctly placed
- Humanoid: clear bone naming; test Avatar mapping
- Export animations as separate clips when needed

### LODs & Collision

- LOD Group naming: `SM_Name_LOD0..N` or Unity LOD Group meshes
- Collision: convex meshes or Unity primitive colliders from proxies
- See `collision-proxy` (→ guides/15-optimization-lod-collision.md) for UCX-style naming if using FBX conventions

### Verify in Unity

- [ ] Scale vs reference cube
- [ ] Pivot / prefab placement
- [ ] Normals / tangents
- [ ] Materials assigned
- [ ] LOD transitions
- [ ] Animator clips (if any)

### Constraints

#### MUST DO
- Validate before export
- Document scale factor used
- Test import once before declaring done

#### MUST NOT DO
- Assume FBX settings without project convention
- Leave unused high-poly LODs in prefab

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Unity Checklist | `../refs/unity-export/unity-checklist.md` | When needed |
| Unity Materials | `../refs/unity-export/unity-materials.md` | When needed |


---

## ◆ unreal-export  _(source: arjun988)_

> Unreal Engine-specific Blender export for FBX scale, LODs, UCX collision, sockets, materials, and skeletal mesh workflows via MCP.

## Unreal Export

UE-ready FBX. Correct centimeter scale awareness. UCX collision. LOD and socket naming.

### When to Use

- Static mesh or skeletal mesh to Unreal
- UCX/UCLX collision export
- LOD chain import
- Socket / pivot setup for gameplay

### Pre-Flight

1. `asset-optimization` (→ guides/15-optimization-lod-collision.md) PASS
2. `lod-pipeline` (→ guides/15-optimization-lod-collision.md) for LOD0–N
3. `collision-proxy` (→ guides/15-optimization-lod-collision.md) for UCX meshes
4. Apply scale; pivots at intended UE origin

### Scale Note

Unreal is centimeter-based. Common approaches:
- Model in meters in Blender, export FBX with unit conversion / 0.01 awareness per project pipeline
- Or work to project-documented scale and verify with a 100cm reference

**Always measure a known edge after import.**

### FBX Defaults (Static)

```
Selected Objects
Apply Scalings: FBX All
Forward: -Z Forward
Up: Y Up
Mesh: ON
Smoothing: Face
```

### Naming for UE

| Type | Pattern |
|------|---------|
| Static mesh | `SM_Name` |
| Skeletal | `SK_Name` |
| Skeleton | `SKEL_Name` |
| LOD | `SM_Name_LOD0` … |
| Collision | `UCX_SM_Name_01` |
| Socket empty | `SOCKET_Name` |

### Collision

- Prefer convex UCX pieces over complex mesh colliders
- Multiple UCX meshes supported
- See `collision-proxy` (→ guides/15-optimization-lod-collision.md)

### Skeletal

- UE mannequin-oriented proportions when required
- Root bone; no leftover Blender deform leftovers
- Export morph targets if needed (shape keys)

### Verify in Unreal

- [ ] Scale (door ~200cm, character ~180cm)
- [ ] Collision wireframe
- [ ] LODs auto-detected
- [ ] Materials / texture sampling
- [ ] Sockets transform

### Constraints

#### MUST DO
- Confirm scale with known-dimension test
- Prefix collision with `UCX_`
- Validate LODs and materials after import

#### MUST NOT DO
- Export without collision plan for physics actors
- Mix unit systems undocumented

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Unreal Checklist | `../refs/unreal-export/unreal-checklist.md` | When needed |
| Ucx Naming | `../refs/unreal-export/ucx-naming.md` | When needed |


---

## ◆ godot-export  _(source: arjun988)_

> Godot-specific Blender export favoring GLTF/GLB with correct scale, materials, animation clips, and collision shapes via MCP.

## Godot Export

GLTF/GLB first. Clean nodes. Godot-friendly materials and animation.

### When to Use

- Shipping meshes/animations to Godot 4.x
- GLB single-file props and characters
- Simple collision companions

### Pre-Flight

1. `asset-optimization` (→ guides/15-optimization-lod-collision.md) PASS
2. Apply transforms; Y-up friendly hierarchy
3. Materials metallic-roughness compatible

### Format

| Case | Format |
|------|--------|
| Default | GLB |
| Editable sidecar textures | GLTF separate |

### Settings

```
Format: GLB
+Y Up
Apply Modifiers: ON (when final)
Animation: include when needed
```

### Hierarchy

- Root empty or object named for scene root
- Avoid deep useless empties
- Keep collision meshes clearly named `COL_` / `UCX_` style

### Materials

- Principled BSDF → GLTF PBR
- Pack images or keep relative paths consistent
- Emission only where intended

### Animation

- NLA or actions exported as clips
- Name actions `AN_[Clip]`
- Root motion documented if used

### Verify in Godot

- [ ] Scale
- [ ] Import materials
- [ ] Animation libraries
- [ ] Collision shapes

### Constraints

#### MUST DO
- Prefer GLB unless project says otherwise
- Test import once
- Keep naming consistent with `naming-conventions.md`

#### MUST NOT DO
- Rely on Blender-only shader nodes that do not export

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Godot Checklist | `../refs/godot-export/godot-checklist.md` | When needed |


---

## ◆ threejs-export  _(source: kevinbadi)_

> Export the current Blender scene as a GLB and generate a ready-to-use Three.js HTML viewer with orbit controls, lighting, and auto-rotation. Trigger when asked to export for web, create a Three.js viewer, make a 3D model interactive for a website, or export from Blender for the web.

## Blender Three.js Export

Exports the current Blender scene as a compressed GLB and generates a standalone HTML file with a Three.js viewer. The viewer includes orbit controls, studio lighting, auto-rotation, and responsive sizing — ready to drop into any website.

### Prerequisites

- **Blender** (4.x+) running with the **Blender MCP addon** active on port 9876
- A scene loaded in Blender (e.g. after running `blender-product-polish`)

### How to Run

```bash
node scripts/node/blender-threejs-export.js --output ~/Desktop/my-product
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output` | Output directory for the GLB + HTML files | **required** |
| `--name` | File name (without extension) | `model` |
| `--port` | Blender MCP port | `9876` |
| `--no-rotate` | Disable auto-rotation | `false` |
| `--bg` | Background color hex | `#111111` |
| `--embed` | Base64-embed the GLB into the HTML (single file) | `false` |

### Output

```
output-dir/
  model.glb          # Compressed GLB export from Blender
  model.html         # Standalone Three.js viewer (CDN imports, no build step)
```

### Viewer Features

- **Orbit controls** — click and drag to rotate, scroll to zoom, right-click to pan
- **Auto-rotation** — slow spin to showcase the product (disable with `--no-rotate`)
- **Studio lighting** — 3-point light setup matching the Blender polish look
- **Responsive** — fills container, works on mobile
- **Zero dependencies** — uses Three.js from CDN via import maps, no npm/build needed
- **Drop-in ready** — open the HTML directly or embed in any page
