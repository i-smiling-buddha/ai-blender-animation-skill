# Environments, vegetation, set dressing & scene assembly

> Fused guide. Script paths like `scripts/x.py` are relative to the **ai-blender-animation-skill skill root**; all Python helpers live in one flat `scripts/` folder (shared `_bpyx.py`). Node helpers are in `scripts/node/`. Where two sources disagree, prefer the Blender 5.x rules in SKILL.md.

Sections: `blender-environment-kits`, `environment-artist`, `vegetation-artist`, `set-dressing`, `scene-assembly`


---

## ◆ blender-environment-kits  _(source: el4cteo)_

> Game environments in Blender 5.3 - terrain from noise or heightmaps (erosion, terraces, play areas, slope/height materials, 16-bit heightmaps + splat maps for UE/Unity), biome scatter by slope/height/mask with Poisson spacing, modular kit metrics and validation (grid, pivots, seams, texel density). Use for levels, landscapes, forests, modular buildings, dungeons.

## Environment kits

The execution model is in `blender-core` (→ SKILL.md). Custom GN tools are in `blender-geometry-nodes` (→ guides/09-geometry-nodes.md), materials in `blender-texturing` (→ guides/08-materials-texturing-baking.md) (trims, vertex blends), and mood/weather in `blender-time-of-day` (→ guides/13-lighting-camera-lookdev.md)/`blender-weather-fx` (→ guides/12-simulation-vfx-weather.md).

### One call each
```
scripts/terrain.py -- --size 400 --res 513 --height 60 --type ridged --erosion 30 --flatten 0 0 40 --material
scripts/terrain.py -- --heightmap //hm.png --size 1000 --res 1009 --height 120 --export-splat //T_Splat.png
scripts/scatter.py -- --target Terrain --collection Trees --density 0.02 --min-distance 5 --max-slope 25 --height-max 45
scripts/scatter.py -- --target Terrain --collection Rocks --density 0.05 --max-slope 70 --align 0.8 --name ENV_Rocks
scripts/kit_check.py -- --objects SM_Wall_4m SM_Floor_4m SM_Door_4m --grid 0.5 --fix
```

### Terrain (terrain.py)
- Grid of `--res`² verts over `--size` m. Use **2^n + 1** for Unity (513/1025/2049, `.raw` 16-bit LE) and UE Landscape's recommended sizes (505/1009/2017/4033, 16-bit PNG). Above 1025, tile it.
- `--type fbm` (rolling), `ridged` (mountains), `hills` (hetero terrain). `--scale` = feature size m. `--erosion N` = thermal erosion steps (talus 33°): slopes relax and debris fills valleys. `--terrace` m = stepped flats. `--flatten X Y R` = a level play/build area blended back with a smoothstep.
- Writes `ENV_Slope` (deg/90) and `ENV_Height` (0–1) point attributes. `--material` builds grass/rock/snow from them: rock above 35°, snow above 75% height on slopes below ~40°, with noise-broken edges.
- Engines: `--export-heightmap` (PNG = 16-bit gray, `.raw` = 16-bit little-endian, row 0 = −Y edge; flip vertically in Unity if mirrored) plus `heightmap_z_scale_m` for the import Z scale. `--export-splat` = 16-bit RGBA weights (R grass, G rock, B snow, sum 1) for terrain layers. Both are written Raw (no display transform): measured round-trip error < 0.001.

### Scatter (scatter.py)
- One GN modifier per layer: Poisson disk (`--density` per m² max, `--min-distance` m), kept where the **interpolated surface normal** is within `--max-slope` and Z is inside `--height-min/max` (object space). `--mask` = vertex group or float attribute as density factor (paint it, or use `ENV_Height`).
- Collection children are instanced at their own origins with random yaw, `--scale` range, and `--align` (0 = upright trees, 0.6–1 = rocks hugging the slope). The source collection is excluded from the view layer.
- The result checks every instance against the real surface (`slope_max_deg`, `height_range`) and counts per source. Instances stay instances. `--realize` only when an exporter or boolean needs real mesh.
- Densities: forest trees 0.01–0.05/m² (min distance 4–8 m), bushes 0.05–0.2, rocks 0.01–0.1, grass clumps 2–20/m² (near camera only). Layer big → small: trees, then bushes masked away from trunks, then grass.
- Engines: glTF `export_gpu_instances=True` (EXT_mesh_gpu_instancing), or `--export-points file.json` (world transforms, Z-up m, wxyz quats) for UE foliage/PCG or Unity instancing scripts. FBX needs realized geometry or one object per instance.

### Modular kits (kit_check.py)
- **Metrics first**: pick a grid (0.5 m snap, 1/2/4 m modules) and keep it everywhere. Walls 3–4 m tall interior (player ~1.8 m eye 1.6 m, doors ≥ 1 × 2.2 m), floors 4 × 4 m, stairs 0.18 m rise / 0.28 m run. UE works in cm (×100 on import), Unity in m.
- **Pivot** convention (`--pivot corner` default, `bottom-center`, `center`) so pieces snap by increments. Footprint lengths are multiples of the grid. Thinner-than-a-cell dims (wall thickness, trims) may be off-grid.
- Open edges only on the piece's outer faces (seams); holes inside are errors. Seam verts must be on the grid so neighbours weld visually. Texel density within 25% of the kit median (`--texture` px). `SM_` names (`--prefix`).
- `--fix` applies rotation/scale and moves each origin to the pivot without moving geometry. Linked duplicates share mesh data, so fix the source once.
- Break repetition with trims and decals (`blender-texturing` (→ guides/08-materials-texturing-baking.md)), vertex-color blends, and rotated/mirrored variants (mirrors flip normals, so check with `blender-asset-qa` (→ guides/17-qa-review.md)). Hide seams with trim pieces over joints.

### Gotchas
- Apply terrain/kit scale before scattering. Densities and slopes are world-based.
- Scatter height is in the target's object space. Keep terrains at the origin or offset `--height-*`.
- Huge Poisson counts are slow. Scatter per tile/area, or lower the density in the viewport and raise it for renders.
- Validate terrain + scatter with `blender-asset-qa` (→ guides/17-qa-review.md) (floating instances on cliffs, z-fighting decals) and `blender-game-optimization` (→ guides/15-optimization-lod-collision.md) (instances, LODs, draw calls).


---

## ◆ environment-artist  _(source: arjun988)_

> AAA environment art for modular kits, buildings, terrain, vegetation, architecture, and scene composition. Use for game-optimized environments, storytelling through space, and modular asset pipelines in Blender via MCP.

## Environment Artist

Modular, scalable environment production for games. Storytelling through space. Performance-conscious.

### When to Use

- Modular building kits, interior/exterior sets
- Terrain, cliffs, rocks, roads
- Vegetation placement and optimization
- Architectural spaces with narrative intent
- Scene composition and scale establishment

### Core Principles

1. **Modularity** — Pieces snap to grid; reusable across scenes
2. **Storytelling** — Environment communicates history and mood
3. **Scale** — Human reference always present
4. **Performance** — Instancing, LODs, texture atlases
5. **Composition** — Guide player eye with shapes and value

### Modular Kit Workflow

```
Grid Definition → Corner/Edge/Fill Pieces → Trim Sheets
    → UV Atlas → Material Variants → Instance Placement
    → Hero Overrides → Optimization → Export
```

### Grid Standards

| Kit Type | Grid Unit | Snap |
|----------|-----------|------|
| Interior walls | 2m or 4m | 0.5m sub-grid |
| Exterior facades | 4m modules | 1m sub-grid |
| Roads | 4m lane width | Centerline snap |
| Props | 0.5m | Free placement |

Name modules: `SM_Env_[Type]_[Role]_[Size]`
Example: `SM_Env_Wall_Corner_2m`

### Kit Piece Categories

| Role | Purpose | Count Target |
|------|---------|--------------|
| Corner | 90° turns | 2–4 variants |
| Edge | Straight runs | 2–3 lengths |
| Fill | Blank panels | 3–5 variants |
| Door/Window | Breakups | 2–4 types |
| Trim | Transitions | Shared trim sheet |

### Terrain & Natural Forms

- Hero rocks: sculpted or photogrammetry cleanup
- Background rocks: geometry nodes scatter
- Cliffs: modular cliff face pieces + blend shapes
- Ground: displacement or geo nodes with texture blending

### Vegetation

| Type | Approach | Poly Budget |
|------|----------|-------------|
| Hero tree | Hand model + cards | 5k–15k tris |
| Mid tree | Simplified + impostor LOD | 2k–5k tris |
| Bush | Cards + cluster | 500–2k tris |
| Grass | Cards or geo nodes scatter | 2–50 tris per blade |

Use geometry nodes for scatter; see geometry-nodes skill.

### Architecture

**Interior:**
- Ceiling height: 2.4m–3.5m standard
- Door: 2.1m × 0.9m
- Window sill: 0.9m from floor
- Corridors: minimum 1.5m playable width

**Exterior:**
- Floor count readable in silhouette
- Roof forms distinguish building type
- Weathering tells climate story

### Composition Guidelines

- **Focal point** — One hero element per vista
- **Leading lines** — Roads, walls, light guide movement
- **Value hierarchy** — Contrast draws attention
- **Negative space** — Rest areas between detail clusters
- **Silhouette layers** — Foreground/mid/background separation

### Storytelling Details

| Detail | Narrative Signal |
|--------|------------------|
| Peeling paint | Neglect, age |
| Barricades | Conflict, danger |
| Personal items | Former inhabitants |
| Damage patterns | Event history |
| Lighting state | Occupied vs abandoned |

### Game Optimization

- Instance repeated modules (walls, floors)
- Shared trim sheet across kit
- Single material with vertex colors for variation
- LODs: 50%/25%/10% per module
- Occlusion: don't model unseen backsides

### MCP Integration

1. Create modular pieces with exact dimensions via MCP
2. Set up collection instances for kit preview
3. Scatter vegetation via geometry nodes (MCP)
4. Query total scene polycount
5. Organize export collections by kit type

### Constraints

#### MUST DO
- Design for grid snapping from blockout
- Create minimum viable kit before hero pieces
- Use instancing for all repeated geometry
- Maintain consistent texel density across kit
- Include scale reference human figure

#### MUST NOT DO
- Unique geometry for every wall segment
- Ignore backface culling opportunities
- Over-detail background-only areas
- Mix grid sizes within same kit
- Skip LOD planning

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Modular kit design | `../refs/environment-artist/modular-kits.md` | Kit creation |
| Composition | `../refs/environment-artist/composition.md` | Scene layout |
| Pipeline | `../refs/shared/asset-pipeline.md` | Phase context |

### Style Integration

| Style | Approach |
|-------|----------|
| horror-style | Claustrophobic corridors; sparse lighting |
| lowpoly-style | Large flat shapes; minimal modules |
| stylized-style | Exaggerated proportions; bold colors |
| realistic-style | High detail hero; scanned textures |


---

## ◆ vegetation-artist  _(source: arjun988)_

> Vegetation and foliage authoring for Blender including trees, plants, grass cards, canopy LODs, and game-friendly leaf atlases via MCP.

## Vegetation Artist

Believable plants. Card efficiency. Wind-ready pivots. Canopy LODs.

### When to Use

- Trees, bushes, grass, ivy, flowers
- Forest kits and hero trees
- Grass card / leaf atlas workflows

### Path Decision

```
Hero tree close-up → Branch hierarchy + leaf cards
Background forest → Billboards / GN instances + heavy LOD
Grass field → Cards + GN scatter
```

### Workflow

```
Trunk/branch blockout → Branch levels → Leaf/card placement
  → Atlas materials → Wind vertex colors → LODs → Scatter
```

### Game Plant Structure

| Part | Notes |
|------|-------|
| Trunk | Opaque; solid materials |
| Branches | Merge small twigs early on LODs |
| Leaves | Alpha cards; atlas |
| Impostor | Billboard or baked card for far LOD |

### Atlas Rules

- Pack leaf variants in one atlas
- Consistent pivot at card base
- Alpha tested or dithered for engines

### Wind Prep

- Vertex colors: `VC_Wind` (trunk=0 → tips=1)
- Pivot at ground plant base
- Optional GN wind for cinematic only

### Constraints

#### MUST DO
- Plan LODs with canopy silhouette
- Keep leaf alpha cheap
- Ground pivot correct for scatter

#### MUST NOT DO
- Unique leaf mesh per leaf on game trees
- Skip impostor for dense forests

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Leaf Atlas | `../refs/vegetation-artist/leaf-atlas.md` | When needed |
| Tree Lod | `../refs/vegetation-artist/tree-lod.md` | When needed |
| Wind Vertex Colors | `../refs/vegetation-artist/wind-vertex-colors.md` | When needed |


---

## ◆ set-dressing  _(source: arjun988)_

> Set dressing and environmental storytelling placement for interiors and exteriors using prop density, narrative clusters, and readability rules via MCP.

## Set Dressing

Story through placement. Controlled clutter. Readable clusters.

### When to Use

- Interior/exterior dressing passes
- Narrative prop clusters
- Avoiding empty or overstuffed spaces
- After modular layout is locked

### Workflow

```
Layout locked → Hero narrative props → Secondary clusters
  → Background filler → Decals/wear → Lighting check → QA
```

### Density Rules

| Zone | Density |
|------|---------|
| Hero interact zone | High intent, low noise |
| Midground | Supporting story clusters |
| Background | Sparse; silhouette only |
| Traversal path | Clearance for player/camera |

### Cluster Method

1. Pick a story beat (meal abandoned, workbench used, escape rushed)
2. Place 3–7 props that sell the beat
3. Add 1–2 wear/decal cues
4. Stop — do not fill every surface

### Prop Sources

- `prop-artist` (→ guides/03-props-vehicles-archviz.md) for unique pieces
- Kitbash / modular libraries for filler
- Instance repeats; vary rotation/scale slightly

### Horror / Sparse Styles

- Fewer props, more meaning
- Negative space intentional
- Coordinate with `horror-style` (→ styles/horror.md) / `psx-horror-style` (→ styles/horror.md)

### Constraints

#### MUST DO
- Dress after greybox navigation works
- Keep player/camera paths clear
- Instance repeated meshes

#### MUST NOT DO
- Uniform clutter wallpaper
- Block doors/windows without story reason

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Story Clusters | `../refs/set-dressing/story-clusters.md` | When needed |
| Density Map | `../refs/set-dressing/density-map.md` | When needed |


---

## ◆ scene-assembly  _(source: arjun988)_

> Large scene layout in Blender with collections, linking, overrides, streaming-friendly organization, and set assembly via MCP.

## Scene Assembly

Layouts that scale. Clear collections. Linking/overrides for big sets.

### When to Use

- Levels, dioramas, cinematic sets
- Assembling modular kits into spaces
- Library linking / collection instances
- Outliner structure for team scenes

### Workflow

```
Block layout (greybox) → Modular assemble → Set dressing
  → Lighting volumes → Cameras → QA pass → Optimize visibility
```

### Collection Structure

```
COL_Layout
COL_Modular_Geo
COL_SetDressing
COL_Lights
COL_Cameras
COL_FX
COL_Collision
COL_Trash / COL_Ref
```

### Linking Strategy

| Approach | When |
|----------|------|
| Collection instance | Repeated modular pieces |
| Library link + override | Shared hero assets across scenes |
| Append | One-off ownership transfer |

Prefer non-destructive linking for repeated kits.

### Layout Rules

1. Greybox scale and navigation first
2. Snap to grid for modular kits
3. Hide heavy collections while dressing
4. Keep world origin meaningful (level zero)

### Performance Hygiene

- Instance repeated meshes
- Cull unseen interiors
- Separate streaming volumes if game-oriented
- Avoid unique high materials on every duplicate

### Handoff

- Dressing → `set-dressing` (→ guides/10-environments-vegetation.md)
- Mood → `lighting` (→ guides/13-lighting-camera-lookdev.md) + style skill
- Gate → `qa-review` (→ guides/17-qa-review.md)

### Constraints

#### MUST DO
- Establish collection hierarchy early
- Greybox before final dressing
- Name cameras and light groups

#### MUST NOT DO
- Dump everything in Scene Collection
- Apply library overrides casually without need
- Duplicate hero meshes instead of instancing

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Collection Template | `../refs/scene-assembly/collection-template.md` | When needed |
| Linking Overrides | `../refs/scene-assembly/linking-overrides.md` | When needed |
