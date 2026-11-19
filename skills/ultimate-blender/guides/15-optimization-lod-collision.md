# Game optimization, LODs & collision

> Fused guide. Script paths like `scripts/x.py` are relative to the **ultimate-blender skill root**; all Python helpers live in one flat `scripts/` folder (shared `_bpyx.py`). Node helpers are in `scripts/node/`. Where two sources disagree, prefer the Blender 5.x rules in SKILL.md.

Sections: `blender-game-optimization`, `asset-optimization`, `lod-pipeline`, `collision-proxy`


---

## ◆ blender-game-optimization  _(source: el4cteo)_

> Optimize Blender assets for real-time engines - triangle/material/texture/bone budgets per platform (mobile, Roblox, web, VR, console, PC), LOD chains, decimation modes, mesh cleanup, draw-call reduction (material merging, atlases, trim sheets), instancing, vertex-split costs, collision proxies, texture memory. Use when an asset is too heavy, before export, or when targeting a platform budget.

## Game Optimization

The execution model is in `blender-core` (→ SKILL.md). Always re-run `blender-asset-qa` (→ guides/17-qa-review.md) after optimizing.

### Procedure
1. **Measure**: `scripts/mesh_stats.py -- --objects ... --budget mobile|roblox|web|vr|console|pc`. It returns tris, estimated draw calls, materials, texture VRAM, bones, and the over-budget items.
2. **Clean**: `make_lods.py --cleanup` (merge by distance 0.1 mm, dissolve degenerate, delete loose). Remove hidden faces: back-to-back faces and faces under other parts (`qa_check` → `back_to_back`, plus manual xray).
3. **Reduce in this order** (cheapest visual loss first): hidden/interior geometry → unnecessary edge loops on flat areas (Limited Dissolve 1–5°) → over-segmented cylinders → Decimate → bake detail to normals (`blender-texture-baking` (→ guides/08-materials-texturing-baking.md)).
4. **Materials**: merge to 1–2 per asset (atlas / trim sheet / shared tiling material). Each material slot per mesh is roughly one draw call.
5. **LODs**: `scripts/make_lods.py -- --objects SM_X --rename` creates `_LOD1.._LOD3` at 50/25/12.5%. Check every LOD silhouette with `look`/`review_shots`.
6. **Re-measure**, then QA, then export (`blender-export-pipelines` (→ guides/16-export-engines.md)).

### Budgets (guidance per asset, 2026)
| Platform | Hero char tris | Prop tris | Mats/asset | Max texture | Bones |
|---|---|---|---|---|---|
| Mobile | 5–15k | 0.3–3k | 1–2 | 1024 | ≤75 |
| Roblox | body ≤10,742 (head 4k, torso 1.75k, limb 1,248); accessory/clothing 4k | ≤20k per MeshPart | 1 (SurfaceAppearance) | 1024 (PBR), 4k max | R15 + optional |
| Web (three.js/Babylon) | 10–30k | 1–10k | 1–2 | 2048 | ≤100 |
| Standalone VR (Quest) | 10–40k | 1–10k | 1–3 | 2048 | ≤100 |
| Console / PC | 50–150k | 5–50k | 2–6 | 4096 | 150–300 |
| UE5 Nanite (static) | — | millions OK | few | 4096+ | n/a |
Whole-scene limits matter more than single assets: mobile ≈ 100–300k tris visible and < 100–200 draw calls; PC ≈ millions of tris and < 2–5k draw calls.

### Decimate modes
| Mode | Use | Notes |
|---|---|---|
| `COLLAPSE` (ratio) | organic, scans, LODs | `use_symmetry`, vertex group factor to protect faces/hands; triangulates |
| `UNSUBDIV` (iterations) | meshes made by subdividing quads | restores the quad grid cleanly |
| `DISSOLVE` (planar, angle) | hard-surface / CAD | delimit `{"SEAM","SHARP","MATERIAL","UV"}`; keeps the silhouette, makes n-gons → triangulate on export |
Protect UV seams and silhouette: decimate a copy, then compare. If UVs tear at LOD1, the ratio is too aggressive for that topology, so re-unwrap or use a manual LOD.

### The hidden cost: vertex splits
GPU vertex count = unique (position, normal, UV, color) combinations. Every UV seam and hard edge **duplicates** vertices, so engine vertex counts are often 1.5–3× Blender's. Minimize seams where they aren't needed, keep hard edges = seams (so the split happens once), and don't add vertex colors or extra UV sets you don't use.

### LOD rules
- Halve the tris per level. Switch at screen size ~0.5 / 0.25 / 0.125 (UE "Screen Size", Unity LOD Group %, Godot `lod_bias` auto).
- LODs keep the same materials (or fewer: merge them at LOD2+), same pivot, same bounds.
- Skeletal LODs: remove finger/face bones at LOD2+ (the engine bone-reduction tools handle this). Keep the skinning on the same skeleton.
- Far LOD / foliage: impostor/billboard. Unreal Nanite (static, opaque/masked) and Godot's auto mesh LOD can replace a hand-made chain.
- Roblox: no manual LODs. `RenderFidelity=Automatic` does it. Keep each MeshPart ≤ 20k tris and use a simple `CollisionFidelity` (Box/Hull) for non-walkable parts.

### Draw calls and batching
- **Merge** static meshes that share a material and are always seen together (join objects). **Don't merge** across large areas, because that defeats frustum/occlusion culling.
- **Instancing**: repeated objects as linked duplicates (Alt+D, shared mesh) or collection instances. They export as instances (glTF `EXT_mesh_gpu_instancing` with `export_gpu_instances`) or as one mesh + transforms in the engine.
- **Atlases/trim sheets**: put many props on one texture set. Trim sheets let walls, panels and pipes share one 2k material.
- **Texture memory** (upper bound, uncompressed RGBA8 + mips): 1k = 5.3 MB, 2k = 21 MB, 4k = 85 MB. Engines compress (BC7/ASTC ≈ 4–8×). Pack grayscale maps into ORM channels to cut it 3×.

### Collision
Keep collision separate and simple: boxes/convex hulls of ≤ 32–255 verts. UE `UCX_<Mesh>_##`, Godot `-colonly`/`-convcolonly` suffix, Unity MeshCollider on a simplified mesh, Roblox `CollisionFidelity`. Never use the render mesh as a physics mesh for anything that moves.

### Rig and animation cost
Limit to 4 influences per vertex (`vertex_group_limit_total(limit=4)` + normalize). Remove non-deforming bones from the export (`use_armature_deform_only`). Bake constraints and drivers to keys. Shape keys cost memory per vertex, so drop unused ones and keep only deltas (glTF sparse accessors handle this).

### Gotchas
- Decimate on meshes with unapplied modifiers: `make_lods.py` evaluates them first. Other paths need you to apply them.
- Join (`Ctrl+J`) merges materials and UV maps by **name**. Rename the UV maps identically first, or the UVs get lost.
- The `Weld` modifier is the non-destructive merge by distance. Use `mode="CONNECTED"` to avoid welding separate parts.
- Triangulate before measuring if the engine will. Quads already count as 2 tris in the stats.


---

## ◆ asset-optimization  _(source: arjun988)_

> Validates and optimizes Blender assets for polycount, topology, UV efficiency, material count, naming, collections, and game-ready performance. Use before export on all production assets via MCP.

## Asset Optimization

Enforce budgets. Clean geometry. Game-ready validation gate before export.

### When to Use

- Before every export
- After modeling complete
- LOD generation
- Scene-wide performance audit
- Pre-delivery validation

### Workflow

```
Audit → Identify Issues → Fix → Re-Audit → LOD Generation → Validation Report
```

### Audit Checklist

Run via MCP scene queries where possible:

#### Geometry
- [ ] Triangle count vs budget (`../refs/shared/polycount-budgets.md`)
- [ ] Duplicate vertices merged
- [ ] Loose geometry removed
- [ ] Non-manifold fixed
- [ ] Interior faces deleted
- [ ] Applied transforms (scale 1,1,1)

#### UVs
- [ ] Pack efficiency > 75%
- [ ] Texel density consistent
- [ ] No unintended overlaps

#### Materials
- [ ] Count within budget
- [ ] No unused slots
- [ ] Names follow `MAT_` convention

#### Organization
- [ ] All objects named `SM_` prefix
- [ ] Collections organized per convention
- [ ] Collision meshes in `COL_Collision`

### Optimization Techniques

| Issue | Fix |
|-------|-----|
| Over budget | Remove unseen geo, decimate, bake detail |
| High triangle count on flat surfaces | Reduce subdiv/bevel segments |
| Many draw calls | Merge materials; atlas textures |
| Repeated geometry | Convert to instances |
| Heavy modifiers | Apply and merge strategically |

### LOD Generation

```
LOD0: Full detail (hero)
LOD1: 50% tris — remove micro-bevels, small greebles
LOD2: 25% tris — decimate modifier; preserve silhouette
LOD3: 10% tris — impostor/card or simple proxy
```

Naming: `SM_Asset_LOD0`, `SM_Asset_LOD1`, etc.

Use Decimate modifier:
- Planar mode for hard surface
- Collapse mode for organic
- Always verify silhouette after decimate

### Modifier Cleanup

Before export:
1. Apply stack OR export with modifiers per engine support
2. Remove unused modifiers
3. Collapse mirror/array if instances not needed
4. Document which modifiers remain live

### Scene Audit Report Template

```markdown
### Optimization Report: [Asset/Scene]

**Total Triangles:** [count] (budget: [target])
**Draw Calls (materials):** [count]
**Objects:** [count]
**Issues Fixed:** [list]

#### Per-Object Breakdown
| Object | Tris | Materials | Status |
|--------|------|-----------|--------|
| SM_... | ... | ... | PASS/FAIL |
```

### MCP Integration

1. Query polycount per object via MCP
2. Query material count via MCP
3. Run cleanup operations via MCP
4. Generate LOD duplicates via MCP
5. Validate naming conventions via MCP scene tree

### Constraints

#### MUST DO
- Run full validation before export
- Document polycount in production brief
- Create LODs for hero assets in games
- Fix all non-manifold before export
- Output validation report

#### MUST NOT DO
- Export without budget check
- Decimate deforming meshes without testing
- Remove collision proxies
- Skip naming convention validation
- Optimize hero face/hands below animation needs

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Full validation | `../refs/shared/validation-checklist.md` | Final gate |
| Polycount budgets | `../refs/shared/polycount-budgets.md` | Budget setting |
| LOD strategies | `../refs/asset-optimization/lod-strategies.md` | LOD creation |


---

## ◆ lod-pipeline  _(source: arjun988)_

> Dedicated LOD generation, naming, screen-size targets, and validation for game meshes in Blender via MCP.

## LOD Pipeline

Intentional LOD chains. Preserve silhouette. Validate reductions.

### When to Use

- Game assets needing LOD0–N
- Batch LOD for modular kits
- Before Unity/Unreal/Godot export

### Workflow

```
Approve LOD0 → Generate LOD1..N → Fix silhouette breaks
  → Naming → Screen-size table → Export verify
```

### Typical Budgets (guide)

| LOD | Tris vs LOD0 | Keep |
|-----|--------------|------|
| LOD0 | 100% | Full detail |
| LOD1 | 40–60% | Major forms |
| LOD2 | 15–30% | Silhouette |
| LOD3 | 5–10% | Blob / impostor candidate |

Tune per asset importance and camera.

### Generation Methods

1. **Decimate (planar/collapse)** — fast props
2. **Manual retopo low** — hero characters/vehicles
3. **Delete interiors / small parts** — vehicles, buildings
4. **Bake normals from LOD0 → low** — when detail must move to texture

### Naming

```
SM_Asset_LOD0
SM_Asset_LOD1
SM_Asset_LOD2
```

Collection: `COL_LODs_[Asset]`

### Validation Checklist

- [ ] Silhouette matches at intended distance
- [ ] No major holes / inverted normals
- [ ] UVs still valid (or rebaked)
- [ ] Materials slots consistent across LODs
- [ ] Vertex colors/UVs needed by shader preserved
- [ ] LOD transitions planned (screen size %)

### Screen Size Starters

| LOD | Screen size (UE-like guide) |
|-----|-----------------------------|
| LOD0 | 1.0 – 0.5 |
| LOD1 | 0.5 – 0.25 |
| LOD2 | 0.25 – 0.1 |
| LOD3 | 0.1 – 0.0 |

### Constraints

#### MUST DO
- Protect silhouette before poly reduction
- Keep LOD0 as source of truth
- Document budgets in production brief

#### MUST NOT DO
- Blind decimate until unrecognizable
- Different material slot counts across LODs without reason

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Lod Budgets | `../refs/lod-pipeline/lod-budgets.md` | When needed |
| Lod Validation | `../refs/lod-pipeline/lod-validation.md` | When needed |


---

## ◆ collision-proxy  _(source: arjun988)_

> Collision proxy authoring for games including UCX/UHX naming, convex hulls, capsules, and simple collider meshes in Blender via MCP.

## Collision Proxy

Simple, stable colliders. Prefer primitives and convex pieces over render mesh.

### When to Use

- Game physics / blocking volumes
- Unreal UCX export
- Unity mesh or primitive colliders
- Hitboxes for interactables

### Workflow

```
Identify collision needs → Build proxies → Name correctly
  → Test overlaps → Export with render mesh
```

### Collider Types

| Type | Use |
|------|-----|
| Box | Crates, walls, simple props |
| Capsule | Characters, poles |
| Sphere | Balls, soft approximates |
| Convex hull | Organic / irregular single body |
| Multiple convex (UCX) | Vehicles, complex props |

### Unreal Naming

```
UCX_SM_Asset_01
UCX_SM_Asset_02
```

- Must match associated mesh naming rules for auto-association
- Convex only for UCX

### Unity Notes

- Prefer engine primitives when possible
- Mesh colliders: convex toggle for dynamic rigidbodies
- Keep proxy collection exportable

### Authoring Rules

1. Slightly smaller than visual mesh to reduce snagging (project-dependent)
2. No holes; watertight convex pieces
3. Apply scale
4. Origin aligned with render mesh
5. Collection: `COL_Collision_[Asset]`

### Validation

- [ ] Player cannot fall through intended blockers
- [ ] No huge invisible walls beyond mesh
- [ ] Wheel/character capsules oriented correctly
- [ ] Named for target engine

### Constraints

#### MUST DO
- Prefer few simple shapes over one complex mesh
- Match engine naming conventions
- Keep proxies in dedicated collection

#### MUST NOT DO
- Use render LOD0 as physics mesh by default
- Non-convex UCX for Unreal auto-convex workflows

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Collider Recipes | `../refs/collision-proxy/collider-recipes.md` | When needed |
| Engine Naming | `../refs/collision-proxy/engine-naming.md` | When needed |
