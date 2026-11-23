# Retopology & UVs

> Fused guide. Script paths like `scripts/x.py` are relative to the **ai-blender-animation-skill skill root**; all Python helpers live in one flat `scripts/` folder (shared `_bpyx.py`). Node helpers are in `scripts/node/`. Where two sources disagree, prefer the Blender 5.x rules in SKILL.md.

Sections: `blender-retopology-uv`, `retopology`, `uv-workflow`


---

## ◆ blender-retopology-uv  _(source: el4cteo)_

> Retopology and UVs in Blender 5.3 - auto retopo (Quadriflow, Decimate, planar), deformation edge flow, seams, unwrap (Angle Based, Minimum Stretch, Smart), pixel-margin packing, texel density measure/set, lightmap UV2, UDIMs, mirrored UVs. Use to turn sculpts/scans/AI meshes into game meshes or prep UVs for texturing/baking.

## Retopology & UVs

The execution model is in `blender-core` (→ SKILL.md).

### Retopology
**Automatic** (`scripts/auto_retopo.py -- --objects Sculpt --tris 8000 --method ...`) makes `<name>_low` and leaves the source hidden:
| Method | Use for | Notes |
|---|---|---|
| `quadriflow` | organic props, static characters, scans | clean quads. Voxel-remeshes first so the input is manifold (retries on the source if that fails); UVs are lost (re-unwrap) |
| `decimate` | background props, LODs, AI-generated meshes | keeps UVs/shape, gives triangles. Fast |
| `planar` | hard-surface CAD/boolean results | dissolves flat areas; keeps seams/sharp/material/UV borders |

**Manual** (hero characters, anything that deforms). Set up a new mesh object with a Shrinkwrap modifier (`PROJECT`, target = sculpt), snapping to `FACE_PROJECT` + `use_snap_project`, and the source in a different viewport color/x-ray. Clean loops with `mesh.relax_edge_loops` / `space_edge_loops_evenly` (LoopTools, built in since 5.3). Auto retopo isn't good enough for deforming hero meshes, because the edge flow below matters.

#### Edge flow rules for deforming meshes
- Concentric loops around the eyes and mouth (≥3 rings). The nasolabial loop flows from the nose wing to the mouth corner.
- **3 loops** at every bending joint (elbow, knee, finger knuckles), plus a loop on each side to keep volume. The shoulder needs extra loops for raising the arm.
- Keep poles (3/5-edge verts) out of bending areas. Put them on flat, stiff regions (chest, back of skull).
- Distribute quads evenly, with density where deformation and silhouette need it. Use triangles only in hidden, non-deforming spots.
- Character tri budgets in 2026: mobile 5–15k, Roblox body ≤ 10.7k total, console/PC third-person 30–80k, hero/cinematic 100k+. Check the target in `blender-game-optimization` (→ guides/15-optimization-lod-collision.md).

### UVs
1. **Seams**: hide them (under arms, inner legs, back of the head, under parts), follow hard edges, cut cylinders on the back side. Rule for game meshes: every hard edge (>~60°, `sharp_edge`) **must** be a UV seam, or the normal map shows artifacts. `scripts/uv_pack.py --seams-from-sharp 60` does this.
2. **Unwrap**: `--method seams` (Angle Based with marked seams), `--method min_stretch` (SLIM, 4.3+, least distortion on organics), `--method smart` (hard-surface/auto, `--angle 66`).
3. **Straighten** rectangular islands (Follow Active Quads, live only) so trims and pixel grids line up.
4. **Average island scale + pack** with margin in pixels: 2k → 8 px, 4k → 16 px, mobile 1k → 4 px. `--shape CONCAVE` gives the tightest pack (slow headless). The default `AABB` is instant.
5. **Texel density** (`scripts/texel_density.py --res 2048`): keep `spread` ≤ 1.3 within an asset. Set it with `--set <px/m>`; if `fits_0_1` is false, change res or density.
6. QA: `blender-asset-qa` (→ guides/17-qa-review.md) reports zero-area UV faces and overlap %.

#### Texel density targets (px/m; studio baselines, not laws)
| Context | px/m |
|---|---|
| First-person hero / weapons | 1024–2048 |
| First-person environment | 512–1024 |
| Third-person games | 512 (console/PC), 256 (mobile) |
| Top-down / strategy | 128–256 |
| Roblox | ~256–512 per texture: 5×5 studs → 256², 10×10 → 512², 20×20 → 1024² |
Everything in the same scene should share one density. The exception is hero assets, kept within 2x.

### Special cases
- **Mirrored/stacked UVs** save space but break unique bakes. Move the duplicate islands exactly +1 U (outside 0–1) during baking, then move them back. Their normal maps must be mirror-safe (tangent space handles it in engines with MikkTSpace).
- **Lightmap UV2** (`--lightmap`, gives `UVMap_Lightmap`): no overlaps, every island inside 0–1, generous margin. Unreal/Unity can generate their own; ship one only if the engine pipeline wants it. Keep UV0 active for texturing.
- **UDIMs** (film/hero): islands in tiles 1001+ (U offset 1 per tile). Texture node image `source="TILED"`. Game engines mostly don't support UDIMs.
- **Trim sheets**: unwrap the strips, then scale/move the islands onto the trim rows (V positions from the trim layout). Islands may exceed 0–1 in U for tiling.
- **Roblox**: exactly one UV set, all inside 0–1. Overlaps are allowed.

### Gotchas
- 5.0+: UV selection is shared across UV maps (`.uv_select_*` attributes). Old `BMLoopUV.select` code fails.
- `uv.*` operators run in Edit Mode and act on selected faces. Select everything first (scripts handle this).
- Headless `uv.pack_islands` with `CONCAVE`/`CONVEX` + rotation can take 2–25 s even on tiny meshes. Use `AABB` while iterating.
- Unwrap warning "failed to solve island": the island has no seams (closed shape). Add seams.
- Apply scale before measuring texel density, or the density reads wrong (the scripts use world space and already account for scale).


---

## ◆ retopology  _(source: arjun988)_

> Production retopology for animation-ready, low-poly, quad-dominant meshes with proper edge loops and efficient polygon flow. Use after sculpting or high-poly modeling before rigging and UV work in Blender via MCP.

## Retopology

Clean, purposeful topology for deformation, UVs, and performance. Quad-dominant. Animation-ready.

### When to Use

- After sculpting high-poly characters/creatures
- Before rigging any deforming mesh
- Poly reduction while preserving silhouette
- Fixing topology from boolean or scan cleanup

### Workflow

```
High-Poly Reference → Guide Setup → Block Retopo → Loop Refinement
    → Pole Placement → Triangle Cleanup → Validation → UV Handoff
```

### Retopology Methods

| Method | Best For | Speed |
|--------|----------|-------|
| Manual (Poly Build tool) | Hero characters | Slow, best quality |
| Shrinkwrap retopo | Creatures, organic | Medium |
| Quad Remesh (voxel) | Quick blockout retopo | Fast, needs cleanup |
| Instant Meshes (external) | Background assets | Fast |
| Symmetry retopo | Bilateral characters | Medium |

**Production default:** Manual with shrinkwrap for hero; Quad Remesh + cleanup for background.

### Edge Loop Rules

- Loops follow muscle/deformation direction
- One loop per major form change
- Maintain even edge length in deformation zones
- Redirect loops at poles (minimum 3 edges meeting)
- Hide poles at back of head, armpits, groin

### Pole Management

| Location | Acceptable | Avoid |
|----------|------------|-------|
| Top of head | 3–5 pole | — |
| Inner eye corner | Redirect pole | Pole directly at corner |
| Shoulder | 3-edge pole hidden | Star pattern on deltoid |
| Back of knee | Pole in crease | Pole on front of knee |

### Triangle Policy

- Triangles OK on non-deforming static mesh
- Convert tris to quads on face, joints, fingers
- No n-gons on deforming surfaces
- Tris at hidden areas (scalp under hair, mouth interior)

### Polycount Targets

See `../refs/shared/polycount-budgets.md`. Retopo is where budget is enforced.

### Shrinkwrap Retopo Setup

```
1. Duplicate high-poly to reference collection (hidden in render)
2. Create retopo mesh with Poly Build / manual extrude
3. Shrinkwrap modifier → Target: high-poly
4. Snap to face with project individual elements
5. Validate shrinkwrap distance (no intersection)
```

### Validation Checklist

- [ ] Quad-dominant on all deformation areas
- [ ] Edge loops support planned rig joints
- [ ] No non-manifold geometry
- [ ] Silhouette matches high-poly reference
- [ ] Polycount within budget
- [ ] Poles placed at acceptable locations
- [ ] Mesh manifold and watertight (if required)

### MCP Integration

1. Create retopo mesh object via MCP
2. Apply shrinkwrap modifier via MCP
3. Query face/edge count during retopo
4. Compare silhouette via MCP render/query
5. Transfer to `COL_Geo_LowPoly` collection

### Constraints

#### MUST DO
- Retopo before rigging deforming meshes
- Preserve silhouette vs high-poly reference
- Plan loops for facial expressions (characters)
- Enforce polycount budget
- Validate manifold before UV pass

#### MUST NOT DO
- Auto-retopo without manual cleanup (hero assets)
- Leave n-gons on deformation surfaces
- Skip validation against reference
- Retopo without knowing rig requirements
- Uniform density (more density at face/hands)

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Facial retopo | `../refs/retopology/facial-retopo.md` | Character faces |
| Game vs cinematic | `../refs/retopology/game-cinematic-topo.md` | Budget decisions |


---

## ◆ uv-workflow  _(source: arjun988)_

> Production UV unwrapping for seam placement, UV packing, texel density, UDIM, lightmap UVs, and modular UV layouts. Use when preparing meshes for texturing and engine export in Blender via MCP.

## UV Workflow

Efficient UV layouts with consistent texel density. Seams at hidden edges. Engine-ready.

### When to Use

- After topology locked, before texturing
- Modular kit UV atlas planning
- Lightmap UV channel setup
- UDIM workflows for hero assets

### Workflow

```
UV Planning → Seam Marking → Unwrap → Texel Density Check
    → Pack → Mirror/Overlap Decision → Lightmap UV (if needed) → Validation
```

### Seam Placement Rules

Place seams at:
- Back of head, spine centerline
- Inner arms, inner legs
- Bottom of chin, underside of objects
- Panel edges on hard surface (construction seams)
- Hidden areas under clothing/overlaps

Never place seams on:
- Face (front)
- Primary gameplay-visible surfaces
- Deforming joint centers (relocate to nearby hidden area)

### Texel Density

**Formula:** `Texel Density = Texture Resolution / UV Island Size in UV space`

Target consistency across visible surfaces:

| Asset Tier | Target TD (px/m) |
|------------|------------------|
| Hero | 512–1024 px/m |
| Standard | 256–512 px/m |
| Background | 128–256 px/m |

Use same density for modular kit pieces sharing atlas.

### Unwrap Methods

| Method | Use When |
|--------|----------|
| Smart UV Project | Quick blockout UVs only |
| Follow Active Quads | Strip UVs (roads, limbs) |
| Cube Project | Boxy hard surface |
| Lightmap Pack | Lightmap channel |
| Manual seam + Unwrap | Production default |

### UV Packing

- Margin: 0.002–0.01 UV units (engine dependent)
- Rotate islands for maximum packing efficiency
- Group islands by material ID
- Keep related islands near each other in UV space
- Use UVPackmaster or native pack for production

### Mirrored UVs

- Mirror UVs for symmetrical characters (save texture space)
- Offset mirrored islands slightly if engine requires unique bakes
- Mark mirrored halves in object naming: `_L` / `_R` meshes if separate

### UDIM Workflow

For hero assets exceeding single 4K texture:
- Tile 1001: head
- Tile 1002: torso
- Tile 1003: limbs
- Document tile assignment in production brief

### Lightmap UVs

Second UV channel requirements:
- No overlapping islands
- Consistent texel density less critical
- Larger margin (0.02+) for light bleed prevention
- Pack separately from texture UVs

### Modular UV Atlas

```
1. Plan shared atlas resolution (2048/4096)
2. Assign UV islands per module to atlas regions
3. Trim sheet regions for repeating detail
4. Vertex color variation for module differentiation
5. Document atlas layout for texture artist
```

### MCP Integration

1. Mark seams via MCP if supported
2. Execute unwrap via MCP
3. Query UV island count and pack efficiency
4. Assign UV channels via MCP
5. Validate no overlapping UVs (except intentional mirror)

### Validation Checklist

- [ ] No unintended overlapping UVs
- [ ] Consistent texel density on visible surfaces
- [ ] Seams hidden at gameplay angles
- [ ] UV islands within 0–1 (or UDIM tiles assigned)
- [ ] Lightmap channel separate if required
- [ ] Pack efficiency > 75%

### Constraints

#### MUST DO
- Plan UVs before final modeling (topology informed by UV needs)
- Maintain texel density consistency
- Hide seams at logical construction edges
- Create lightmap UVs for baked lighting pipelines
- Document atlas layout for modular kits

#### MUST NOT DO
- Smart UV Project as final production UVs
- Overlapping UVs on unique surface detail (unless mirrored)
- Inconsistent texel density on same asset tier
- Seams across faces or primary visible surfaces
- Skip packing margins

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Texel density calc | `../refs/uv-workflow/texel-density.md` | Hero assets |
| Trim sheets | `../refs/uv-workflow/trim-sheets.md` | Modular kits |
