# Sculpting & creatures

> Fused guide. Script paths like `scripts/x.py` are relative to the **ultimate-blender skill root**; all Python helpers live in one flat `scripts/` folder (shared `_bpyx.py`). Node helpers are in `scripts/node/`. Where two sources disagree, prefer the Blender 5.x rules in SKILL.md.

Sections: `blender-sculpting`, `sculpting`, `creature-artist`


---

## ◆ blender-sculpting  _(source: el4cteo)_

> Sculpting in Blender 5.3 - base-to-detail workflow, voxel remesh, dyntopo, multires, 5.x brush types, masks/face sets, symmetry, plus headless-safe procedural ops for agents (remesh, symmetrize, multires, inflate, noise detail, smooth) and the sculpt-to-game handoff. Use for organic models, characters, creatures, rocks and bake sources.

## Sculpting

The execution model is in `blender-core` (→ SKILL.md). The handoff goes to `blender-retopology-uv` (→ guides/07-retopology-uv.md) → `blender-texture-baking` (→ guides/08-materials-texturing-baking.md).

### Agents: what you can and can't do
- **Sculpt Mode operators crash Blender in background mode** (`-b`), including `mesh_filter`. Never enter Sculpt Mode headless.
- Headless or MCP: use `scripts/sculpt_ops.py` for object-level ops: `remesh=SIZE`, `symmetrize=+X`, `multires=N`, `inflate=D`, `detail=STR,SCALE`, `smooth=N`, `apply`. Combine these with Geometry Nodes (`blender-geometry-nodes` (→ guides/09-geometry-nodes.md): SDF grid booleans/fillets, noise displacement) and shape modeling for procedural organic forms.
- Live sessions with a UI: brush strokes via `bpy.ops.sculpt.brush_stroke(stroke=[...])` need a 3D View region override and are fragile. Prefer procedural ops, then show the user with `look`. Hand detailed brushwork to the human.

### Professional workflow
1. **Base mesh / blockout**: primitives, metaballs, Skin modifier, or a low-poly base at real scale. Proportions first: compare with references and check against a human 1.75 m.
2. **Unify**: voxel remesh (`remesh=0.02` for a 2 m character, smaller for detail) fuses parts and gives even density. Repeat it while the big forms change.
3. **Primary forms** at low resolution (Grab, Snake Hook, Clay Strips, Inflate, Smooth). **Secondary** (muscle groups, folds) at medium resolution. **Tertiary** (pores, scratches, fabric weave) with Multires levels 4–6, or as normal/displacement maps.
4. **Dynamic topology** (`sculpt.dynamic_topology_toggle`): adds detail where you stroke. Good for concept sculpting, bad for final topology and multires (it destroys UVs/multires). Use voxel remesh + multires for production.
5. **Multires**: subdivide (`multires_subdivide`, Catmull-Clark) on a clean quad base (after retopo) to sculpt high detail that bakes back to the base level (`blender-texture-baking` (→ guides/08-materials-texturing-baking.md), multires bake or high→low).
6. **Handoff**: export the high (or keep it in-file), retopo to `_low`, UV, bake normal/AO/curvature, then texture.

### Brushes (5.x: brushes are assets in the Essentials library)
| Purpose | `sculpt_brush_type` |
|---|---|
| Build volume | `CLAY_STRIPS`, `CLAY`, `CLAY_THUMB`, `LAYER`, `INFLATE`, `BLOB` |
| Shape / move | `GRAB`, `SNAKE_HOOK`, `ELASTIC_DEFORM`, `POSE`, `BOUNDARY`, `CLOTH`, `NUDGE`, `ROTATE`, `THUMB` |
| Details / edges | `DRAW`, `DRAW_SHARP`, `CREASE`, `PINCH` |
| Flatten / hard surface | `PLANE` (flatten/fill/scrape), `MULTIPLANE_SCRAPE` |
| Clean up | `SMOOTH`, `SIMPLIFY` (dyntopo), `DISPLACEMENT_ERASER`/`SMEAR` (multires) |
| Masking / grouping | `MASK`, `DRAW_FACE_SETS`; Expand (`sculpt.expand`), mask from cavity |
5.0 renamed `brush.sculpt_tool` → `sculpt_brush_type`. 5.1 folded the stroke options into `brush.stroke_method` (`DOTS`, `DRAG_DOT`, `SPACE`, `AIRBRUSH`, `ANCHORED`, `LINE`, `CURVE`). 5.2 moved automasking to `brush.mesh_automasking_settings` / `paint.mesh_automasking_settings`.

### Rules of thumb
- Sculpt at **real scale**, with scale applied. Brush radius is in screen space but strength and remesh sizes depend on scale.
- Use symmetry (`mesh.use_mirror_x`, radial: `mesh.radial_symmetry`) on characters until the asymmetry pass at the end.
- Face Sets organise parts (head, torso, hands). Hide them and mask by face set to isolate.
- Watch density: a 2 m character at voxel 0.005 is already millions of polys. Keep viewport FPS usable and work up in levels.
- Silhouette first. Check from several angles in flat matcap (`look` shading `solid`) before adding detail.
- Floaters/kitbash for hard-surface details on organic models: separate objects, combined at bake time.
- Before baking, run `blender-asset-qa` (→ guides/17-qa-review.md) on the high (no inverted parts, no huge self-intersections in the bake range).

### References
[../refs/blender-sculpting/forms-and-bake-sources.md](../refs/blender-sculpting/forms-and-bake-sources.md): human proportions in meters and heads, form order (primary → tertiary), hard-surface sculpting (trim gestures, mask extract, face sets, mesh filters), multires rebuild/reshape, and preparing a high-poly bake source (density, cage, naming, exploding). Load it before character, creature or bake-source work.

### Gotchas
- `voxel_remesh` destroys UVs, vertex groups (unless preserve attributes) and multires levels. Do it before UVs/rigging.
- Multires + topology changes don't mix: never edit the base topology after subdividing (apply the base or rebuild).
- `symmetrize` on a non-centered object mirrors across the **object's local axis**. Center the origin on the symmetry plane first.
- Sculpting on shape keys: enable `use_shape_key_edit_mode` and sculpt on the active key (facial work, `blender-facial-shapekeys` (→ guides/05-characters-clothing-face.md)).


---

## ◆ sculpting  _(source: arjun988)_

> Blender sculpting for organic and hard surface detail using Dyntopo, multiresolution, brushes, alpha workflow, wrinkles, and damage. Use when high-frequency surface detail is needed before retopology in Blender via MCP.

## Sculpting

High-frequency surface detail pass. Know when to sculpt vs model vs bake.

### When to Sculpt

| Sculpt | Don't Sculpt |
|--------|--------------|
| Organic wrinkles, pores | Hard surface panel lines |
| Creature skin detail | Modular kit pieces |
| Damage, wear, dents | Anything needing clean UVs directly |
| Character likeness refinement | Lowpoly style assets |
| Hero asset micro-detail | Background props |

### Workflow

```
Base Mesh → Multires or Dyntopo → Primary Forms → Secondary Detail
    → Tertiary/Micro → Bake Maps → Retopology (if game asset)
```

### Dyntopo vs Multiresolution

| Method | Use When | Avoid When |
|--------|----------|------------|
| Multires | Controlled detail levels; bake workflow | Need to preserve base topology exactly |
| Dyntopo | Freeform exploration; damage pass | Need predictable polycount |
| Voxel Remesh | Reset topology mid-sculpt | Fine detail already established |

**Default:** Multires for production; Dyntopo for exploration passes only.

### Brush Selection

| Brush | Purpose |
|-------|---------|
| Draw | General buildup |
| Clay Strips | Muscle/form definition |
| Crease | Wrinkles, folds, hard lines |
| Grab | Large form adjustments |
| Inflate/Deflate | Volume control |
| Scrape | Planar flattening (hard surface sculpt) |
| Dam Standard | Sharp damage, scratches |
| Layer | Non-destructive detail (if available) |

### Detail Pass Order

1. **Primary** — Major form corrections (Grab, Clay)
2. **Secondary** — Muscle, folds (Clay Strips, Crease)
3. **Tertiary** — Skin texture, scales (Draw, Alpha)
4. **Micro** — Pores, fine scratches (Alpha, Dam Standard)

### Alpha Workflow

- Use tileable alphas for skin, leather, rock
- Stamp at consistent scale for texel coherence
- Combine alphas with different brush strengths
- Bake alpha detail to normal map for game assets

### Hard Surface Sculpting

- Scrape brush for planar surfaces
- Crease for panel line softening
- Dam Standard for impact damage
- Trim brushes for precise cuts (if addon available)
- Always retopologize or rebake after hard surface sculpt

### Damage & Wear

| Damage Type | Technique |
|-------------|-----------|
| Scratches | Dam Standard, light strokes |
| Dents | Inflate negative + smooth |
| Chipped edges | Scrape + Crease |
| Rust bubbles | Small Draw buildup |
| Fabric wear | Crease along stress points |

### Performance

- Hide unrelated objects during sculpt
- Use matcap for fast feedback
- Subdivide only active area (face, hands)
- Bake and reduce multires for viewport performance

### MCP Integration

1. Duplicate base mesh to sculpt collection via MCP
2. Add multires modifier via MCP
3. Query polycount at each subdivision level
4. Export high-poly for bake handoff
5. Keep sculpt mesh separate from game mesh

### Handoff to Retopology

Before retopo handoff provide:
- Final sculpt at highest multires level
- Decimated version for retopo reference
- List of deformation zones requiring clean loops
- Baked maps if bake-before-retopo workflow

### Constraints

#### MUST DO
- Start from clean base mesh with good topology
- Work largest to smallest detail
- Duplicate before sculpt destructive changes
- Bake detail for game assets
- Match detail level to camera distance

#### MUST NOT DO
- Sculpt lowpoly-style assets
- Skip retopology for animated game characters
- Subdivide entire mesh to level 6+ uniformly
- Leave dyntopo mesh as final game asset
- Sculpt without reference

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Brush settings | `../refs/sculpting/brush-guide.md` | Detail pass |
| Bake workflow | `../texture-workflow/SKILL.md` | Game asset handoff |


---

## ◆ creature-artist  _(source: arjun988)_

> AAA creature modeling for fantasy, aliens, monsters, and organic creature design with believable anatomy and movement. Use for creature blockouts, muscle flow, bone structure, and animation-ready creature assets in Blender via MCP.

## Creature Artist

Believable creature design grounded in anatomy. Movement-informed topology. Fantasy with physical plausibility.

### When to Use

- Fantasy creatures, monsters, aliens
- Quadrupeds, flying creatures, aquatic forms
- Hybrid designs (part animal, part mechanical)
- Boss creatures, enemies, companions

### Design Principles

1. **Anatomy grounding** — Even fantasy references real biology
2. **Silhouette first** — Unique readable shape
3. **Movement logic** — Skeleton supports intended motion
4. **Muscle flow** — Surface forms follow underlying structure
5. **Storytelling** — Design communicates behavior (predator/prey/scavenger)

### Workflow

```
Reference → Skeleton Blockout → Muscle Masses → Surface Forms
    → Detail (sculpt or model) → Retopology → Rig → Animation Test
```

### Creature Types

| Type | Skeleton Base | Key Forms |
|------|---------------|-----------|
| Quadruped | Dog/horse reference | Shoulder hump, haunches |
| Biped | Human/primate | Upright spine, heel plant |
| Flying | Bat/bird | Wing membrane, keel chest |
| Aquatic | Fish/shark | Lateral line, fin placement |
| Serpentine | Snake | Ribcage segmentation |
| Insectoid | Arthropod | Segmented body, jointed legs |

### Muscle Flow

- Origin → Insertion direction visible in surface
- Flexed areas: compressed forms, overlapping skin
- Extended areas: stretched, thinner surface
- Fat deposits: soft transitions (belly, cheeks)
- Scars/armor: break muscle flow intentionally

### Bone Structure Planning

Before surface modeling:
1. Place joint locations (spine segments, limbs)
2. Verify range of motion at each joint
3. Ensure limb attachment supports gait cycle
4. Head/neck connection supports attack/look poses

### Surface Detail Tiers

| Tier | Detail | Method |
|------|--------|--------|
| Primary | Overall mass | Blockout/sphere modeling |
| Secondary | Muscle groups | Sculpt or extrusion |
| Tertiary | Skin folds, veins | Sculpt |
| Micro | Scales, pores, scars | Sculpt + bake to normal |

### Hybrid Creatures

Mechanical + organic:
- Separate meshes: `SM_Creature_Bio`, `SM_Creature_Mech`
- Hard surface joints at organic/mechanical transition
- Rig: mechanical parts use constraints; organic uses weights

### MCP Integration

1. Create skeleton blockout (armature or mesh guides) via MCP
2. Build primary masses with mirror/sphere modeling
3. Hand off to sculpting for detail pass
4. Query proportions against reference scale figure
5. Organize bio/mechanical collections separately

### Constraints

#### MUST DO
- Reference real anatomy even for fantasy
- Test silhouette from gameplay camera angle
- Plan rig joints during blockout
- Separate hero detail from background creatures
- Retopologize before rigging

#### MUST NOT DO
- Design without movement consideration
- Uniform detail density (hero face/feet get more)
- Skip retopology on sculpted creatures
- Ignore polycount tier (background vs boss)
- Attach limbs without joint clearance

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Quadruped anatomy | `../refs/creature-artist/quadruped-anatomy.md` | Four-legged creatures |
| Flying creatures | `../refs/creature-artist/flying-creatures.md` | Wings, flight |
| Pipeline | `../refs/shared/asset-pipeline.md` | Phase context |

### Style Integration

| Style | Approach |
|-------|----------|
| realistic-style | Grounded anatomy; PBR skin |
| stylized-style | Exaggerated features; bold shapes |
| lowpoly-style | Minimal surface; texture detail |
| horror-style | Uncanny proportions; exposed anatomy |
