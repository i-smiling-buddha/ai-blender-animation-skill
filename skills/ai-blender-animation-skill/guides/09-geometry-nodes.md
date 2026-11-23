# Geometry Nodes

> Fused guide. Script paths like `scripts/x.py` are relative to the **ai-blender-animation-skill skill root**; all Python helpers live in one flat `scripts/` folder (shared `_bpyx.py`). Node helpers are in `scripts/node/`. Where two sources disagree, prefer the Blender 5.x rules in SKILL.md.

Sections: `blender-geometry-nodes`, `geometry-nodes`


---

## ◆ blender-geometry-nodes  _(source: el4cteo)_

> Geometry Nodes in Blender 5.3 - fields, domains, attributes, instancing, zones (simulation/repeat/for-each), closures/bundles, lists, SDF grids, node tools, baking, plus a JSON-to-node-tree builder and socket inspector. Use for scattering, procedural assets/environments, parametric tools and modifier inputs.

## Geometry Nodes

The execution model is in `blender-core` (→ SKILL.md). Build trees with `scripts/gn_builder.py`, a compact JSON spec that's far cheaper than raw bpy. Look up exact socket names first, because they change between versions:
```
scripts/gn_builder.py -- --describe GeometryNodeDistributePointsOnFaces GeometryNodeInstanceOnPoints
scripts/gn_builder.py -- --spec scatter.json --apply Ground --set Density=20 Seed=3 Mask=@paint_mask
```
`--set Name=@attr` feeds a modifier input from a named attribute. The result reports evaluated vert/face counts and node warnings. The spec format is in the script docstring; full examples are in [../refs/blender-geometry-nodes/recipes.md](../refs/blender-geometry-nodes/recipes.md).

### Core concepts (get these right or nothing works)
- **Geometry** flows left→right through sockets with **circle** shapes. **Fields** (diamond sockets) are functions evaluated per element **on the node that consumes them**, in that node's domain/context.
- **Domains**: Point, Edge, Face, Face Corner, Spline, Instance, Layer. `Capture Attribute` freezes a field at a point in the graph (before topology changes), and `Evaluate on Domain` converts between domains.
- **Attributes**: built-ins (`position`, `normal`, `sharp_face`, `material_index`, `UVMap`...) plus named ones via `Store Named Attribute`. Named attributes persist after the modifier. That's how GN data reaches shaders (Attribute node) and exporters (glTF `export_attributes`, which exports names starting with `_`).
- **Instances** are cheap (one mesh, many transforms). **Realize Instances** only when you must edit per-instance geometry or export a single mesh. Realize as late as possible.
- Inputs exposed on the group interface become **modifier inputs** (5.2: `mod.properties.inputs.<identifier>.value`). Panels group them, menu sockets give enums.

### Zones and advanced types
| Feature | Nodes | Use |
|---|---|---|
| Simulation zone | `GeometryNodeSimulationInput/Output` (paired) | per-frame state: growth, particles, erosion; bake to keep |
| Repeat zone | `GeometryNodeRepeatInput/Output` | iterate N times (L-systems, relaxation, recursive subdivision) |
| For Each Element | `GeometryNodeForeachGeometryElementInput/Output` | run a sub-graph per element (per building lot, per island) |
| Closures / Bundles (5.0+) | `NodeClosureInput/Output`, `NodeCombineBundle`/`NodeSeparateBundle`, Evaluate Closure | pass functions/structured data around; reusable "strategy" node groups |
| Lists (5.2) | `GeometryNodeFieldToList`, `ListGetItem`, `ListLength`, `SortList`, `FilterList` | real arrays, not fields |
| Grids/SDF (4.x–5.x) | `MeshToSDFGrid`, `SDFGridBoolean`, `SDFGridFillet`, `SDFGridOffset`, `GridToMesh` | smooth booleans, remeshing, fillets, voxel effects |
| Grids/lists/curves (5.3) | `GridSolvePoisson`, `RasterizePoints`, `GridTopologyBoolean`, `GridDeactivateVoxels`, `GetGridNames`, `CombineList`, `ConstructCurves`, `GeometryMaterials`, `FunctionNodeGetVectorComponent` | fluid-like/voxel effects, fixed small lists, curves from position lists |
| Physics (5.2, experimental) | `GeometryNodeXPBDSolver` + bundles | node-based cloth/hair, see `blender-simulation` (→ guides/12-simulation-vfx-weather.md) |
| Gizmos | `GizmoLinear/Dial/Transform` | viewport handles for inputs |
Zones need `input.pair_with_output(output)` (spec key `pairs`), plus items on the output node (`repeat_items`, `state_items`, ...; spec 4th node field).

### Procedure
1. Sketch the data flow: source geometry → selection/masks (fields) → generate/instance → transform/randomize → realize/merge → set materials/shading → output.
2. `--describe` every node type you'll use, then write the spec and build. Check `node_warnings` and the evaluated counts.
3. Expose only meaningful inputs (density, seed, scale range, materials), with min/max set.
4. Look at it (`look`), check `blender-asset-qa` (→ guides/17-qa-review.md) if the result will be exported (realized geometry), and check `blender-game-optimization` (→ guides/15-optimization-lod-collision.md) for instance counts and tris.
5. Ship: either keep it procedural (the .blend/asset library), or apply the modifier / `visual_geometry_to_objects` for exporters.

### Rules
- Randomness: always expose a `Seed`, and use `Random Value` with the ID/Index field so results stay stable when counts change.
- Scale-independent setups use `Object Info` (Relative) and real units. Apply the object scale or read it explicitly.
- Materials: `Set Material` inside the tree. The material must exist in the file, and instances keep their own materials.
- Shading: GN output loses auto-smooth unless you add `Set Shade Smooth` + (5.x) the `Smooth by Angle` essentials group, or store `sharp_edge`.
- UVs: primitives output `UVMap` via their UV output. Store it with `Store Named Attribute` (Face Corner, 2D Vector, name `UVMap`) or it's dropped.
- Performance: avoid realizing millions of instances, prefer Points + instances for scatter, use `Merge by Distance` sparingly, and simulation zones need baking for playback/export (`object.geometry_node_bake_single` or modifier `bakes`).
- Node tools (`ng.is_tool = True`, `is_mode_edit` etc.) turn a group into an operator in the 3D View menus, for editing workflows.

### Gotchas
- 5.2: `mod["Socket_2"]` no longer works. Use `getattr(mod.properties.inputs, ident).value`, and `.type = "ATTRIBUTE"` + `.attribute_name` for attribute inputs. Compare and Random Value **sockets changed**: Random Value now has single dynamic `Min`/`Max`/`Value` sockets typed by `data_type`. Link by name, and `--describe` when unsure.
- 5.3: Import PLY's output is `Geometry` (was `Mesh`) and is a point cloud for Gaussian-splat files. Curve to Mesh adds `Miter Scale`; Realize Instances adds `Preserve Normals` (negative-scale instances).
- Sockets that are disabled for the current mode/data type are still in `node.inputs` with the same name. The builder picks the **enabled** one. Set `data_type`/`mode` props first (the builder sets props before links).
- `nt.interface.new_socket(...)` is the 4.0+ API (`ng.inputs.new` is gone).
- Exporters see the **evaluated** mesh. Instances become glTF instancing (`export_gpu_instances`) or are realized on export.


---

## ◆ geometry-nodes  _(source: arjun988)_

> Blender Geometry Nodes for procedural modeling, scatter systems, vegetation, buildings, pipes, cables, and reusable node groups. Use for procedural asset generation and instancing pipelines via MCP.

## Geometry Nodes

Reusable procedural systems. Parametric assets. Performance-aware instancing.

### When to Use

- Scatter systems (rocks, vegetation, debris)
- Parametric buildings, roads, pipes, cables
- Procedural variation without unique modeling
- Kit assembly with randomization
- Non-destructive iteration on large scenes

### Workflow

```
Define Parameters → Build Node Tree → Create Node Group (GN_)
    → Test Variations → Bake/Instance Decision → Export Integration
```

### Node Group Standards

- Prefix: `GN_[System]_[Descriptor]`
- Expose only necessary inputs (seed, density, scale range)
- Document input ranges in group name or custom properties
- Version node groups: `GN_Scatter_Rocks_v02`

### Core Patterns

#### Scatter System
```
Mesh Surface → Distribute Points on Faces → Instance on Points
    → Randomize Rotation (Z) → Randomize Scale → Realize (optional)
```

#### Building Generator
```
Floor Count (input) → Repeat Mesh → Stack Instances
    → Window Cut Pattern → Material Variation → Output
```

#### Cable/Pipe Routing
```
Curve Input → Curve to Mesh (profile) → Subdivide → Set Material
    → Multiple curves from single path node
```

#### Rock Formation
```
Ico Sphere → Displace (noise) → Decimate → Instance Scatter
```

### Randomization

| Parameter | Typical Range |
|-----------|---------------|
| Scale | 0.8–1.2 (uniform or per-axis) |
| Rotation Z | 0–360° |
| Density | 0.1–2.0 per m² |
| Seed | Integer for reproducibility |

Always expose seed as group input for art direction iteration.

### Performance Rules

| Scenario | Approach |
|----------|----------|
| Game export | Realize instances → decimate → export mesh |
| Background scatter | Keep instanced; limit count |
| Hero procedural | Bake to static mesh for engine |
| Viewport preview | Limit instance count attribute |

### Reusable Systems Library

| Group | Purpose |
|-------|---------|
| GN_Scatter_Objects | Generic surface scatter |
| GN_Array_Modular | Linear modular repetition |
| GN_Curve_Pipe | Pipe/cable along curve |
| GN_Wall_Variant | Parametric wall sections |
| GN_Vegetation_Cluster | Tree/bush clustering |

### MCP Integration

1. Create geometry nodes modifier via MCP
2. Configure group inputs via MCP
3. Query instance count and final polycount
4. Realize geometry for export via MCP
5. Organize GN objects in dedicated collection

### Integration with Export

Before export:
1. Apply geometry nodes modifier OR
2. Realize instances and merge OR
3. Export as instances if engine supports (Unreal HISM)

Document which approach per target engine.

### Constraints

#### MUST DO
- Create reusable node groups, not one-off trees
- Expose seed and density as inputs
- Test at min/max parameter extremes
- Realize/bake before game export unless engine supports instances
- Name groups with `GN_` prefix

#### MUST NOT DO
- Million-instance scatter without LOD/culling plan
- Nested realize operations (performance killer)
- Hardcode values that should be inputs
- Export procedural without polycount validation
- Skip variation testing at boundary values

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Scatter recipes | `../refs/geometry-nodes/scatter-systems.md` | Environment scatter |
| Building generators | `../refs/geometry-nodes/building-generators.md` | Architectural procedural |
