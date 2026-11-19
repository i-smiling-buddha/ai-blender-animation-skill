# Modeling, hard-surface & procedural modeling

> Fused guide. Script paths like `scripts/x.py` are relative to the **ultimate-blender skill root**; all Python helpers live in one flat `scripts/` folder (shared `_bpyx.py`). Node helpers are in `scripts/node/`. Where two sources disagree, prefer the Blender 5.x rules in SKILL.md.

Sections: `blender-hardsurface-modeling`, `blender-modeler`, `hard-surface`, `procedural-modeling`


---

## ◆ blender-hardsurface-modeling  _(source: el4cteo)_

> Hard-surface and prop modeling in Blender 5.3 - blockout-to-detail flow, non-destructive modifier stacks (Mirror, Boolean Exact/Manifold, Bevel, Weighted Normal, Smooth by Angle), mid-poly vs subdivision vs high-to-low workflows, shading/custom normals, cylinder segment budgets, edge attributes from Python. Use for weapons, vehicles, props, architecture, mechanical parts.

## Hard-Surface Modeling

The execution model is in `blender-core` (→ SKILL.md). Run `blender-asset-qa` (→ guides/17-qa-review.md) after every modeling pass.

### Pick the workflow first
| Workflow | When | Output |
|---|---|---|
| **Mid-poly** (bevel + weighted normals, no bake) | modern games, props seen up close, fast iteration | game mesh directly; tiling materials/trim sheets |
| **High → low** (high via booleans+bevel or subd, low baked) | hero assets, unique textures, tight tri budgets | `_high` + `_low` → `blender-texture-baking` (→ guides/08-materials-texturing-baking.md) |
| **Subdivision** (support loops/creases + Subsurf) | renders, product viz, film | smooth surfaces, edges held by loops/creases |

### Procedure
1. **Blockout** at real scale (`ob.dimensions`) from primitives. Settle the silhouette and proportions before any detail. Check against references.
2. **Apply scale** (`transform_apply(scale=True)`) before bevels, booleans or solidify, because modifier distances use object space.
3. **Primary → secondary → tertiary** forms. Booleans for cuts and panels, then bevels. Small tertiary details go in normal maps/decals, or into the high-poly as "floaters" for baking.
4. **UV the base mesh now** (mid-poly). Bevel/Boolean modifiers propagate UVs, but after bevels no edge is sharp enough to auto-seam. Then **build the stack** with `scripts/apply_stack.py -- --objects Body --preset midpoly --cutters Cut1 Cut2`. Order: Mirror → Booleans → Bevel → Weighted Normal → (Triangulate at export).
5. **Shading check**: smooth shading + Weighted Normal (keep sharp). There must be no gradients across flat faces. View with a matcap or `look` in `solid` shading.
6. **QA** with `blender-asset-qa` (→ guides/17-qa-review.md), then apply the stack only on an export copy (`--apply`), keeping the editable source.

### Stack rules
- **Booleans**: put cutters in a `Cutters` collection with display `WIRE` and `hide_render=True`. Solver: `EXACT` (robust default), `MANIFOLD` (much faster, but inputs must be closed manifold), `FLOAT` (legacy fast, fragile with coplanar faces). With many cutters, use `operand_type="COLLECTION"`.
- Avoid coplanar boolean faces: extend cutters slightly past the surface. They also cause z-fighting.
- **Bevel**: `limit_method="ANGLE"` (30°), or `"WEIGHT"` with a `bevel_weight_edge` attribute for hand-picked edges. Turn on `use_clamp_overlap`, `harden_normals=True`, `miter_outer="MITER_ARC"`. Width ≈ 0.5–2% of the part's size, kept consistent across the asset.
- **Weighted Normal** after Bevel: `mode="FACE_AREA"`, `keep_sharp=True`, weight 50. Needs smooth faces (remove the `sharp_face` attribute or call `shade_smooth`).
- **Smooth by Angle** (4.1+, replaces auto smooth): `bpy.ops.object.shade_auto_smooth(angle=rad)` adds a GN modifier, or `shade_smooth_by_angle` sets `sharp_edge` destructively.
- **Mirror**: `use_clip=True`, `use_mirror_merge=True`. Model one half only at x ≥ 0.
- **Subdivision**: hold edges with support loops (a loop 1–5% of the face width from the edge) or `crease_edge` (0–1). Turn on `use_limit_surface`. Don't use creases if the asset goes to an engine.
- **Triangulate** only for export/baking (`keep_custom_normals=True`, `BEAUTY`). Triangulating the bake mesh and the export mesh identically keeps normal maps synced.

### Topology rules
- **N-gons**: fine on flat, non-deforming faces in mid-poly/game meshes. Never use them on curved surfaces or anything that subdivides or deforms.
- **Poles** (5+ edges) should sit on flat areas, never on a curvature peak or bevel.
- **Cylinder segments by on-screen size**: small (bolts) 6–8, medium (handles) 12–16, large (barrels) 24–32, hero/close-up 48+. Use multiples of 4 or 8 so booleans/mirrors line up with existing loops.
- **No long, thin triangles** across visible curved areas (shading and LOD artifacts).
- **Panel lines**: inset + extrude in (mid-poly) or a boolean groove on the high-poly, then bake.
- Spend density where the silhouette needs it, not on flat faces.

### Edge/face attributes from Python (4.0+ names)
```python
me = ob.data
bw = me.attributes.get("bevel_weight_edge") or me.attributes.new("bevel_weight_edge", "FLOAT", "EDGE")
cr = me.attributes.get("crease_edge") or me.attributes.new("crease_edge", "FLOAT", "EDGE")
sh = me.attributes.get("sharp_edge") or me.attributes.new("sharp_edge", "BOOLEAN", "EDGE")
bw.data[edge_index].value = 1.0; sh.data[edge_index].value = True
me.edges[edge_index].use_seam = True          # seams are still an edge property
```
Select sharp edges by angle in bmesh: `e.calc_face_angle(0) > math.radians(30)`.

### Gotchas
- A bevel that looks blobby or flips usually means unapplied/non-uniform scale or overlapping geometry (turn on clamp).
- A Boolean that returns nothing or garbage: the cutter isn't closed/manifold (Exact copes, Manifold fails), or its normals are inverted.
- Weighted Normal has no effect: faces are flat-shaded, or an earlier modifier destroyed the custom normals.
- 5.2: the GN `Mesh Bevel` node exists for procedural bevels inside node trees (`blender-geometry-nodes` (→ guides/09-geometry-nodes.md)).
- 5.3: LoopTools is built in (`mesh.relax_edge_loops`, `curve_edge_loops_between_selected`, `fit_edge_loops_to_annotation`, `space_edge_loops_evenly`). `mesh.primitive_quad_sphere_add(segments=4)` gives an all-quad cube-sphere: no pinched poles, so it subdivides and bevels cleanly.
- Trim-sheet/mid-poly assets: UVs go to the trim strips (`blender-retopology-uv` (→ guides/07-retopology-uv.md)) and materials tile (`blender-pbr-materials` (→ guides/08-materials-texturing-baking.md)).


---

## ◆ blender-modeler  _(source: arjun988)_

> Core Blender modeling specialist for Edit Mode, modifiers, collections, precision modeling, and scene organization. Use for general 3D modeling, blockouts, cleanup, non-destructive workflows, and scene structure in Blender via MCP.

## Blender Modeler

Foundation modeling skill for all Blender geometry work. Non-destructive by default. MCP-first execution.

### When to Use

- Blockouts and primary/secondary shape passes
- General mesh editing not covered by discipline specialists
- Scene organization, collections, instances
- Modifier stack management
- Cleanup: merge, normals, loose geometry
- Precision modeling with snapping and numeric input

### Core Workflow

```
1. Scene Setup     → Collections, scale reference, naming
2. Blockout        → Primitives, mirror, array
3. Shape Refinement → Edit mode or modifier-based edits
4. Modifier Stack  → Non-destructive detail
5. Cleanup         → Merge, normals, manifold check
6. Handoff         → UV/materials or discipline specialist
```

### Scene Organization

Establish via MCP immediately:

```
COL_Project
├── COL_Reference      # Scale refs, ortho images
├── COL_Blockout       # Temporary blockout meshes
├── COL_Geo            # Final geometry
├── COL_Collision      # Proxy meshes
└── COL_Instances      # Empties/collections for instancing
```

Naming: `../refs/shared/naming-conventions.md`

### Modifier Stack Philosophy

Preferred order (bottom to top):

```
1. Mirror          # Symmetry
2. Array           # Repetition
3. Solidify        # Thickness
4. Boolean         # Cuts (prefer live booleans until export)
5. Bevel           # Edge detail
6. Weighted Normal # Hard surface shading
7. Subdivision     # Only when topology supports it
```

**Rules:**
- Keep booleans live until export prep
- Apply mirror only when topology is finalized
- Never stack multiple subsurf without supporting loops
- Document modifier purpose in object custom properties if complex

### Edit Mode Essentials

| Operation | Use When |
|-----------|----------|
| Extrude (E) | Adding depth from faces |
| Inset (I) | Panel lines, frames |
| Loop Cut (Ctrl+R) | Adding resolution |
| Knife (K) | Custom cuts |
| Merge by Distance | Cleanup duplicates |
| Recalculate Normals | Fix shading issues |

Via MCP: execute equivalent operations; don't narrate UI.

### Precision Modeling

- Enable snapping to grid/vertex/edge as appropriate
- Use numeric input for exact dimensions
- Set cursor to world origin for modular alignment
- Apply scale before boolean operations
- Use orthographic views for architectural accuracy

### Instancing Strategy

| Method | Use Case |
|--------|----------|
| Linked Duplicate (Alt+D) | Identical props with variation potential |
| Collection Instance | Modular kit pieces |
| Geometry Nodes | Procedural scatter (see geometry-nodes) |
| Array Modifier | Linear repetition |

Prefer instances over duplicate geometry for repeated elements.

### Custom Normals

- Enable Auto Smooth with appropriate angle (30°–60° hard surface)
- Weighted Normal modifier for hard surface without extra geo
- Mark sharp edges explicitly for bevel control
- Clear custom split normals before retopology handoff

### Cleanup Checklist

- [ ] Merge by distance (threshold: 0.0001m default)
- [ ] Remove loose geometry
- [ ] Delete interior faces
- [ ] Recalculate outside normals
- [ ] Apply scale if modifiers depend on it
- [ ] Verify manifold (no holes unless intentional)
- [ ] Check triangle count vs budget

### MCP Integration

```
1. Create mesh objects via MCP
2. Apply modifiers via MCP
3. Query polycount after each major edit
4. Organize into collections via MCP
5. Duplicate to backup collection before destructive ops
```

See `../refs/shared/mcp-integration.md`

### Constraints

#### MUST DO
- Non-destructive workflow until export phase
- Name objects `SM_` prefix immediately
- Keep blockout separate from final geo
- Apply transforms before boolean/export
- Validate topology before handoff

#### MUST NOT DO
- Delete blockout before silhouette approved
- Apply all modifiers prematurely
- Leave default names (Cube.001)
- Model without scale reference
- Skip cleanup pass

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Modifier deep dive | `../refs/blender-modeler/modifier-stack.md` | Complex modifier chains |
| Scene organization | `../refs/blender-modeler/scene-organization.md` | Large scenes |
| Pipeline | `../refs/shared/asset-pipeline.md` | Phase context |

### Handoff Points

| To Skill | When |
|----------|------|
| hard-surface | Mechanical/sci-fi detail pass |
| environment-artist | Modular environment pieces |
| character-artist | Organic human forms |
| uv-workflow | Topology locked, ready for UVs |
| asset-optimization | Pre-export performance pass |


---

## ◆ hard-surface  _(source: arjun988)_

> AAA hard surface modeling for sci-fi, industrial, military, vehicles, weapons, robotics, and mechanical props. Use for boolean/bevel workflows, panel lines, greebles, chamfers, and manufacturing-accurate surfaces in Blender via MCP.

## Hard Surface Artist

Production hard surface modeling with manufacturing logic. Readable surfaces. Clean modifier stacks. MCP-first.

### When to Use

- Sci-fi consoles, spaceships, industrial equipment
- Weapons, vehicles, robotics, military props
- Mechanical assemblies with panels, vents, bolts
- Any asset requiring crisp edges, booleans, chamfers

### Design Principles

1. **Primary forms first** — Silhouette reads at distance
2. **Manufacturing logic** — Panel breaks follow construction seams
3. **Surface hierarchy** — Primary > Secondary > Tertiary > Micro (greebles)
4. **Functional readability** — Every form suggests purpose
5. **Edge consistency** — Uniform bevel widths per detail tier

### Workflow

```
Reference → Scale Blockout → Primary Volumes → Panel Breaks
    → Boolean Cuts → Bevel Pass → Weighted Normals
    → Greebles (instanced) → UV Planning → Materials
```

### Boolean Workflow

```
1. Block primary forms (no booleans yet)
2. Create cutter objects on separate collection COL_Booleans
3. Apply scale on all operands
4. Boolean Difference/Union — keep LIVE
5. Fix intersection artifacts with manual cleanup if needed
6. Bevel AFTER boolean in modifier stack
7. Apply booleans only at export prep
```

**Boolean rules:**
- Cutter objects named `SM_Cutter_[Feature]`
- Prefer exact solver for mechanical work
- Avoid booleans on curved surfaces without adequate topology
- Duplicate mesh before first boolean as backup

### Bevel Workflow

| Detail Tier | Bevel Width | Segments |
|-------------|-------------|----------|
| Primary edges | 0.005–0.02m | 2–3 |
| Panel lines | 0.001–0.003m | 1–2 |
| Micro detail | 0.0005–0.001m | 1 |

- Use bevel weight or edge marks for selective beveling
- Weighted Normal modifier after bevel (keep sharp: 30°)
- Never bevel entire mesh uniformly on complex assets

### Panel Lines

Techniques (prefer non-destructive):
1. Inset faces + slight extrude inward
2. Knife cuts on flat panels
3. Boolean with thin cutter boxes
4. Normal map detail for distant panels

Place panel lines at:
- Structural boundaries
- Access hatches, maintenance points
- Material transitions
- Manufacturing seam locations

### Greebles

- Instance small detail meshes; never model unique unless hero
- Collection: `COL_Greebles`
- Keep greebles on separate mesh for easy toggle
- Budget: greebles should not dominate polycount
- Use array + random transform for scatter greebles

### Hard Edge Management

```
Sharp edges → Mark Sharp or Bevel Weight = 1.0
Soft transitions → Bevel Weight = 0.0–0.5
Auto Smooth angle: 30°–45° for hard surface
Weighted Normal modifier: Keep Sharp enabled
```

### Manufacturing Reference

| Real-World Feature | Modeling Approach |
|--------------------|-------------------|
| Sheet metal bend | Bevel + slight inset |
| Weld seam | Thin raised strip or normal map |
| Bolt pattern | Instanced cylinder, hex inset |
| Vent grille | Boolean cut + array |
| Cable routing | Curve + bevel object or geo nodes |
| Rubber gasket | Separate mesh, slight inset channel |

### Vehicle / Spaceship Specifics

> Prefer **vehicle-artist** for cars, ships, aircraft, and mechs. Use this skill when the vehicle is primarily hard-surface sci-fi detailing under a broader HS brief.

- Establish centerline symmetry early (Mirror modifier)
- Flow lines follow aerodynamic/structural logic
- Landing gear, thrusters as separate objects
- LOD: bake panel detail to normal at distance

### Weapon Specifics

- Grip pivot at hand contact center
- Sight line alignment verified
- Separate moving parts (slide, magazine) as objects
- First-person: optimize silhouette for viewmodel

### MCP Integration

Execute via MCP:
1. Create blockout primitives
2. Apply mirror/array modifiers
3. Execute boolean operations
4. Apply bevel and weighted normal
5. Instance greeble collections
6. Query polycount per phase

### Constraints

#### MUST DO
- Maintain manufacturing plausibility
- Keep modifier stack non-destructive until export
- Use instancing for repeated mechanical detail
- Verify silhouette at 45° increments
- Apply scale before booleans

#### MUST NOT DO
- Boolean on unsubdivided curved surfaces without support
- Uniform bevel on entire complex mesh
- Model every bolt uniquely
- Skip weighted normals on hard surface
- Exceed polycount budget with micro-detail

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Boolean deep dive | `../refs/hard-surface/boolean-workflow.md` | Complex cuts |
| Greeble library | `../refs/hard-surface/greeble-patterns.md` | Detail pass |
| Pipeline | `../refs/shared/asset-pipeline.md` | Phase context |

### Style Integration

| Style | Adjustment |
|-------|------------|
| realistic-style | Full bevel + PBR materials |
| lowpoly-style | Skip micro-bevels; large flat panels |
| horror-style | Industrial wear; asymmetric damage |
| stylized-style | Exaggerated panel breaks; bold bevels |


---

## ◆ procedural-modeling  _(source: arjun988)_

> Procedural asset creation for rocks, buildings, vegetation, roads, terrain, pipes, cables, and sci-fi panels using Geometry Nodes and modifier-based workflows in Blender via MCP.

## Procedural Modeling

Parametric assets with art-directable variation. Geometry Nodes priority. Bake for game export.

### When to Use

- Rocks, cliffs, terrain features
- Modular building generation
- Road and path systems
- Pipe/cable networks
- Sci-fi panel arrays
- Vegetation placement systems

### Workflow

```
Define Parameters → Build Procedural System → Validate Variations
    → Realize/Bake → Optimize → Export
```

### System Categories

| System | Primary Tool | Output |
|--------|--------------|--------|
| Rocks | Geo Nodes + noise | Static mesh |
| Buildings | Geo Nodes stack | Modular pieces |
| Roads | Curve + Geo Nodes | Mesh strip |
| Pipes | Curve to mesh | Network |
| Vegetation | Scatter GN | Instanced/baked |
| Sci-fi panels | Array + random | Trim sheet geo |

### Rock Generation

```
Base shape (ico sphere) → Displace (multi-scale noise)
    → Decimate → Subdivide (selective) → Weighted Normal
    → Variation: seed input controls all noise
```

Expose: `seed`, `scale`, `roughness`, `density`

### Building Generation

```
Footprint curve → Extrude floors → Window boolean pattern
    → Balcony probability → Roof type switch → Material ID
```

Output separate meshes per floor module for game kits.

### Road Systems

```
Centerline curve → Resample → Cross-section profile
    → Bridge blend at intersections → UV follow curve
```

### Pipe/Cable Networks

```
Node graph points → Connect minimum spanning → Curve segments
    → Profile sweep → Collision offset → Clamp size range
```

### Sci-Fi Panels

```
Grid subdivide → Random inset/extrude → Bevel
    → Panel index → Material variation
    → Bake to trim sheet layout
```

### Variation Testing

Test at parameter extremes:
- Minimum scale/density
- Maximum scale/density
- Seed 0, 42, 9999 (reproducibility check)

### Game Export Decision

| Approach | When |
|----------|------|
| Keep procedural in Blender only | Iteration phase |
| Realize single variant | Standard game prop |
| Bake multiple seeds as LOD variants | Background variety |
| Export node group to engine | Only if engine supports |

### MCP Integration

1. Build procedural systems via MCP
2. Set seed/density parameters via MCP
3. Realize geometry via MCP
4. Query output polycount per variation
5. Export realized meshes

### Constraints

#### MUST DO
- Expose seed for reproducibility
- Test min/max parameter bounds
- Realize before game engine export
- Optimize after realize (asset-optimization)
- Document parameter ranges in production brief

#### MUST NOT DO
- Export unrealsized geometry nodes to game without validation
- Infinite variation without performance testing
- Procedural where manual hero quality required
- Skip UV planning on procedural output
- Hardcode random without seed control

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Geo nodes patterns | `../geometry-nodes/SKILL.md` | Node setup |
| Environment integration | `../environment-artist/SKILL.md` | Scene placement |
