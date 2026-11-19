# Props, vehicles & archviz

> Fused guide. Script paths like `scripts/x.py` are relative to the **ultimate-blender skill root**; all Python helpers live in one flat `scripts/` folder (shared `_bpyx.py`). Node helpers are in `scripts/node/`. Where two sources disagree, prefer the Blender 5.x rules in SKILL.md.

Sections: `prop-artist`, `vehicle-artist`, `archviz`


---

## ◆ prop-artist  _(source: arjun988)_

> Everyday and hero prop modeling for furniture, tools, household objects, kitbash parts, and readable game props. Use when hard-surface is too sci-fi/mechanical and the asset is a grounded prop.

## Prop Artist

Grounded, readable props. Silhouette first. Real-world scale. Kitbash-friendly parts.

### When to Use

- Furniture, tools, containers, electronics, household objects
- Hero interactive props and background set dressing pieces
- Kitbash libraries (handles, brackets, panels, fasteners)
- When hard-surface sci-fi language would feel wrong

### Design Principles

1. **Real-world scale** — Measure against human (door 2.0–2.1m, chair seat ~0.45m)
2. **Silhouette readability** — Reads at game camera distance
3. **Wear hierarchy** — Contact edges dirty; protected faces cleaner
4. **Part logic** — Separate meshes where materials or LODs differ
5. **Pivot correctness** — Floor contact, grip, hinge, or socket as needed

### Workflow

```
Reference → Scale blockout → Primary volumes → Secondary forms
  → Edge bevels → Wear/damage → UVs → Materials → Optimize → Export
```

### Prop Tiers

| Tier | Tris (guide) | Detail | Use |
|------|--------------|--------|-----|
| Hero | 2k–8k | Full bevels, unique wear | Interactables, close-ups |
| Standard | 500–2k | Clean forms, shared mats | Midground |
| Background | 100–500 | Block forms, atlas mats | Far / dense dressing |

### Kitbash Rules

- Name parts `SM_KB_[Category]_[Part]`
- Keep origins at logical attach points
- Prefer modular dimensions (0.05 / 0.1 / 0.25m grid)
- Collection: `COL_Kitbash_[Set]`

### Material Guidance

- Limit unique materials; atlas where possible
- Separate glass / emissive / opaque when needed for engine
- Wear via roughness/AO, not only albedo dirt

### Handoff

- UVs → `uv-workflow` (→ guides/07-retopology-uv.md)
- Look → `materials` (→ guides/08-materials-texturing-baking.md) / `lookdev` (→ guides/13-lighting-camera-lookdev.md)
- Placement → `set-dressing` (→ guides/10-environments-vegetation.md)
- Ship → `asset-optimization` (→ guides/15-optimization-lod-collision.md) → `export-pipeline` (→ guides/16-export-engines.md) or engine export skill

### Constraints

#### MUST DO
- Set real-world scale before detailing
- Place pivot intentionally
- Match prop tier to camera distance

#### MUST NOT DO
- Over-greeble everyday objects
- Use sci-fi panel language on mundane props
- Skip collision planning for interactables

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Prop Tiers | `../refs/prop-artist/prop-tiers.md` | When needed |
| Kitbash Library | `../refs/prop-artist/kitbash-library.md` | When needed |
| Everyday Prop Checklist | `../refs/prop-artist/everyday-prop-checklist.md` | When needed |


---

## ◆ vehicle-artist  _(source: arjun988)_

> Dedicated vehicle modeling for cars, trucks, aircraft, ships, boats, mechs, and transit assets with proportion, panel flow, and game LOD awareness in Blender via MCP.

## Vehicle Artist

Proportion-driven vehicles. Clear body language. Manufacturing panel flow. Engine-ready LODs.

### When to Use

- Cars, trucks, bikes, aircraft, boats, ships
- Mechs and large mechanical walkers
- Transit / industrial vehicles
- When vehicle work should not live under generic hard-surface

### Design Principles

1. **Proportion blockout first** — Wheelbase, cabin, mass distribution
2. **Centerline symmetry** — Mirror early; break only for damage/wear
3. **Panel flow** — Seams follow stamped/assembled construction
4. **Functional readability** — Lights, intakes, doors, wheels read clearly
5. **Separate systems** — Body, wheels, glass, interior, lights as objects

### Workflow

```
Ortho refs → Chassis blockout → Body volumes → Wheel/suspension
  → Panel breaks → Booleans/cutters → Bevels → Glass/lights
  → Interior (LOD-aware) → UVs → Materials → LODs → Collision → Export
```

### Blockout Checklist

- [ ] Overall length / width / height locked
- [ ] Wheel size and stance correct
- [ ] Cabin / canopy silhouette readable
- [ ] Ground clearance intentional
- [ ] Symmetry axis established

### Object Split (Game)

| Object | Why |
|--------|-----|
| `SM_Vehicle_Body` | Main shell |
| `SM_Vehicle_Wheel_*` | Spin / steer |
| `SM_Vehicle_Glass` | Transparency / sorting |
| `SM_Vehicle_Light_*` | Emissive materials |
| `SM_Vehicle_Interior` | Cull on distant LODs |

### LOD Guidance

| LOD | Focus |
|-----|-------|
| LOD0 | Full panels, interior if visible |
| LOD1 | Simplified panels, remove micro |
| LOD2 | Body + wheels + glass only |
| LOD3 | Impostor / ultra-low hull |

Use `lod-pipeline` (→ guides/15-optimization-lod-collision.md) for generation and validation.

### Collision

- Simple convex hulls per major volume
- Wheel capsules/cylinders separate if physics-driven
- See `collision-proxy` (→ guides/15-optimization-lod-collision.md)

### Constraints

#### MUST DO
- Lock proportions before panel detail
- Keep wheels as separate objects when animated
- Plan LODs and collision with body

#### MUST NOT DO
- Detail interior before exterior silhouette
- Boolean chaos without cutter collection
- Single merged mesh for all systems on game vehicles

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Proportion Blockout | `../refs/vehicle-artist/proportion-blockout.md` | When needed |
| Vehicle Object Split | `../refs/vehicle-artist/vehicle-object-split.md` | When needed |
| Vehicle Lod Targets | `../refs/vehicle-artist/vehicle-lod-targets.md` | When needed |


---

## ◆ archviz  _(source: arjun988)_

> Architectural visualization in Blender for interiors/exteriors with real-world scale, camera composition, PBR materials, and still/animation delivery via MCP.

## Archviz

Real-world scale architecture. Clean cameras. Believable materials. Delivery stills.

### When to Use

- Interior/exterior architectural presentations
- Real-estate style stills and simple walkthroughs
- Material/lighting lookdev for spaces

### Workflow

```
CAD/scale check → Greybox → Final modeling → Materials
  → Cameras → Lighting (HDRI + practicals) → Render → Comp
```

### Scale & Modeling

- Millimeter–meter accuracy where specs exist
- Straight verticals; controlled bevels on visible edges
- Separate glass, frames, furniture collections

### Cameras

- Verticals corrected (shift) for exteriors when needed
- 24–35mm interiors common; avoid extreme wide unless intentional
- Use `camera-cinematography` (→ guides/13-lighting-camera-lookdev.md)

### Lighting

- HDRI for exteriors / window light
- Practical lamps as mesh lights
- Soft GI; avoid game-style single harsh key unless styled

### Delivery

- High-res stills; optional depth/mist for comp
- `compositing` (→ guides/14-rendering-compositing.md) for exposure polish
- Keep layered EXR for revisions

### Constraints

#### MUST DO
- Verify real-world scale early
- Lock cameras before heavy grade
- Keep glass/IOR plausible

#### MUST NOT DO
- Game lowpoly shortcuts on hero archviz plates
- Over-saturate materials

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Archviz Camera | `../refs/archviz/archviz-camera.md` | When needed |
| Archviz Lighting | `../refs/archviz/archviz-lighting.md` | When needed |
