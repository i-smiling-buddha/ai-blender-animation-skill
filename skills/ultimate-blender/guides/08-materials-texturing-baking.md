# PBR materials, texturing & baking

> Fused guide. Script paths like `scripts/x.py` are relative to the **ultimate-blender skill root**; all Python helpers live in one flat `scripts/` folder (shared `_bpyx.py`). Node helpers are in `scripts/node/`. Where two sources disagree, prefer the Blender 5.x rules in SKILL.md.

Sections: `blender-pbr-materials`, `materials`, `blender-texturing`, `texture-workflow`, `blender-texture-baking`


---

## ◆ blender-pbr-materials  _(source: el4cteo)_

> Physically based materials in Blender 5.3 - metal/roughness rules, Principled BSDF inputs, color spaces (sRGB vs Non-Color), measured albedo/F0 values, texture-set auto-wiring, ORM channel packing, DirectX vs OpenGL normals, alpha modes, displacement, view transforms (AgX, Khronos PBR Neutral), engine-ready material rules. Use when creating, fixing, or exporting materials and textures.

## PBR Materials

The execution model is in `blender-core` (→ SKILL.md). Measured values are in [../refs/blender-pbr-materials/pbr-values.md](../refs/blender-pbr-materials/pbr-values.md).

### Fast paths
- Texture set → material: `scripts/build_pbr_material.py -- --name M_Crate --textures //tex/crate --objects SM_Crate`. It detects maps by filename (Poly Haven, ambientCG, Substance, UE suffixes), sets color spaces, splits ORM, flips DirectX normals, and routes AO to glTF.
- Solid physically-plausible material: `--preset gold|iron|plastic|rubber|wood|glass|skin|...` with an optional `--color R G B` (sRGB).

### The rules (violations are what make renders look "CG")
1. **Metallic is binary**: 0 (dielectric) or 1 (raw metal). Use in-between values only on transition pixels (dust or rust edges on metal). Painted metal counts as dielectric.
2. **Base color = albedo with no lighting**: no baked shadows/AO/highlights. Dielectric range is sRGB ~30–240 (linear 0.012–0.87): charcoal ≈ 50, fresh snow ≈ 240. Metals: base color = F0 reflectance, sRGB 180–255, never dark.
3. **Roughness carries the realism**. Break it up with grunge, smudges and wear. A constant roughness value looks fake; vary it ±0.1–0.2 across a surface.
4. **Color spaces**: Base Color and Emission use `sRGB`. Roughness, Metallic, Normal, AO, Height, Opacity and ORM use `Non-Color`. A wrong color space is the #1 bug (washed-out normals, wrong roughness).
5. **Specular**: leave `IOR` 1.5 and `Specular IOR Level` 0.5 for almost all dielectrics. Change IOR only for known materials (water 1.33, glass 1.5, diamond 2.42).
6. **Normal maps**: Blender, glTF, Unity and Roblox use **OpenGL** (Y+). Unreal and Substance's DirectX preset use **DirectX** (Y-), so flip G when converting. The bake and the target must use the same tangent basis (MikkTSpace) and the same triangulation.
7. **AO**: the Principled BSDF has no AO input. For engines, ship AO in the ORM red channel. For Cycles renders, don't multiply AO into base color, because the renderer computes occlusion.

### Principled BSDF (5.2) quick map
`Base Color`, `Metallic`, `Roughness`, `IOR`, `Alpha`, `Normal`, `Thin Wall` (5.2: leaves/paper/fabric sheets without volume), `Subsurface Weight/Radius/Scale` (skin, wax; Scale in meters ≈ 0.005–0.02 for skin), `Specular IOR Level`, `Specular Tint`, `Anisotropic`, `Transmission Weight` (glass/liquids), `Coat Weight/Roughness/Normal` (car paint, varnish), `Sheen Weight` (cloth, velvet), `Emission Color/Strength` (strength in W/m²-ish units; 1–10 for screens, 50+ for bulbs), `Thin Film Thickness/IOR` (soap, oil, coated lenses), `Diffuse Roughness`, `Transmission Dispersion Scale/Abbe Number` (5.3: gems, prisms; Abbe ≈ 64 crown glass, 55 diamond, 30–40 flint glass; lower = more color fringing). 5.3 transmission also follows `Anisotropic`.

### Engine export rules
| Target | Maps | Packing | Normal |
|---|---|---|---|
| glTF / web / Godot | baseColor(+alpha), metallicRoughness, normal, occlusion, emissive | glTF: **R=AO G=Rough B=Metal** (ORM) | OpenGL |
| Unreal | BaseColor, Normal, ORM | R=AO G=Rough B=Metal | DirectX (UE flips on import if the texture is marked) |
| Unity URP/HDRP | BaseMap, Normal, MetallicSmoothness / HDRP MaskMap | URP: R=Metal A=**Smoothness** (1-rough). HDRP Mask: R=Metal G=AO B=DetailMask A=Smoothness | OpenGL |
| Roblox SurfaceAppearance | ColorMap(+alpha), NormalMap, MetalnessMap, RoughnessMap, EmissiveMaskContent | separate grayscale maps, no packing | OpenGL, tangent space |
- Only image-texture → BSDF chains export. Procedural nodes, Mix nodes and math become nothing in engines, so bake them first (`blender-texture-baking` (→ guides/08-materials-texturing-baking.md)).
- One material per texture set. Every extra material is an extra draw call (`blender-game-optimization` (→ guides/15-optimization-lod-collision.md)).
- Power-of-two textures (512/1024/2048/4096). Use PNG/TGA for data maps, never JPEG for normals.

### Alpha
`mat.surface_render_method = "DITHERED"` (cutout/alpha-clip, sorts correctly, good for foliage/hair cards) or `"BLENDED"` (true transparency, glass/UI). Connect `Alpha`. glTF exports CLIP/BLEND from the alpha setup. Prefer dithered/clip for games.

### Displacement
Height map → `Displacement` node → Material Output `Displacement`. `mat.displacement_method`: `BUMP` (shading only, everywhere), `BOTH`/`DISPLACEMENT` (Cycles, needs dense or adaptively subdivided geometry: Subdivision modifier `use_adaptive_subdivision`). Scale is in meters; midlevel 0.5 for 8-bit, 0 for 32-bit EXR.

### View transform (judge materials under the right one)
`scene.view_settings.view_transform`: **AgX** (default, photographic), **Khronos PBR Neutral** (what-you-see-is-the-albedo; use for asset/product review and glTF parity), **Standard** (UI/graphics/textures that must match pixels), ACES 1.3/2.0 (VFX pipelines). Never bake or author textures while looking through Filmic/AgX with an extreme "Look".

### Procedural → texture
Procedural setups (noise/voronoi wear, curvature masks via `Geometry > Pointiness` (Cycles) or `Ambient Occlusion` node, edge wear via `Bevel` node normals) are fine for renders. For engines, bake them to the texture set (`blender-texture-baking` (→ guides/08-materials-texturing-baking.md)). Node Wrangler (bundled) `Ctrl+Shift+T` does the same as `build_pbr_material.py`, but needs the UI.

### Gotchas
- `material.use_nodes` is deprecated in 5.x. New materials already have Principled + Output.
- `mat.diffuse_color` only affects the viewport (Solid mode/workbench), not renders or export.
- Images loaded headless need `image.colorspace_settings.name` set **before** baking or export.
- Shared texture images used by several materials: change the color space once, because it's per image.


---

## ◆ materials  _(source: arjun988)_

> Blender PBR and stylized material creation for metal, wood, concrete, fabric, glass, dirt, rust, and procedural shaders. Use for look development, material reuse, and production shading in Blender via MCP.

## Materials

Production shading with material reuse. PBR-accurate or intentionally stylized. Minimal unique materials.

### When to Use

- Look development after UVs
- Procedural material creation
- Master material library setup
- Material variation from shared masters
- Engine export material preparation

### Workflow

```
Master Materials → Instance Variations → Object Assignment
    → Vertex Color/Mask Setup → Validation → Export Prep
```

### Master Material Library

Create reusable masters in `MAT_` prefix:

| Master | Base Setup |
|--------|------------|
| MAT_Metal_Base | Principled: Metallic 1, adjustable Roughness |
| MAT_Plastic_Base | Principled: Metallic 0, Specular 0.5 |
| MAT_Fabric_Base | Principled + Sheen |
| MAT_Glass_Base | Principled: Transmission 1, IOR 1.45 |
| MAT_Emissive_Base | Principled: Emission strength variable |
| MAT_Organic_Base | Subsurface scattering enabled |

Instance variations: duplicate master, adjust parameters only.

### PBR Value Ranges

| Material | Metallic | Roughness | Notes |
|----------|----------|-----------|-------|
| Polished metal | 1.0 | 0.1–0.3 | |
| Brushed metal | 1.0 | 0.4–0.6 | Anisotropic if available |
| Painted metal | 0.0 | 0.3–0.5 | Base color = paint |
| Plastic | 0.0 | 0.3–0.6 | |
| Rubber | 0.0 | 0.7–0.9 | |
| Concrete | 0.0 | 0.8–0.95 | |
| Wood (raw) | 0.0 | 0.5–0.7 | |
| Glass | 0.0 | 0.0 | Transmission 1 |
| Skin | 0.0 | 0.4–0.6 | Subsurface 0.1–0.3 |
| Fabric | 0.0 | 0.7–0.9 | Sheen |

### Procedural Material Patterns

**Wear mask:** Noise → ColorRamp → Lerp between clean/worn
**Edge wear:** Bevel node → Pointiness or Ambient Occlusion
**Dirt accumulation:** AO inverted → multiply with dirt color
**Rust:** Noise mask on metal → orange/brown color override

### Material Count Budget

| Asset Type | Max Materials |
|------------|---------------|
| Hero prop | 3–5 |
| Standard prop | 1–2 |
| Modular piece | 1 (atlas) |
| Character | 3–8 (body, cloth, eyes, hair) |
| Environment module | 1–2 |

### Vertex Color Usage

- RGB: variation masks (wear, moss, color variation)
- R: wear amount, G: dirt, B: wetness
- Document channel usage in material notes

### Stylized Materials

See stylized-style skill. Key differences:
- Flatten roughness range
- Hand-painted base color priority
- Rim light via Fresnel mix
- NPR toon shaders if project requires

### MCP Integration

1. Create material slots via MCP
2. Assign materials to objects via MCP
3. Set principled BSDF parameters via MCP
4. Query material count per scene
5. Verify material names follow convention

### Constraints

#### MUST DO
- Reuse master materials; instance variations
- Name materials `MAT_[Surface]_[Descriptor]`
- Match PBR values to style skill direction
- Limit material count per asset budget
- Test materials in target lighting setup

#### MUST NOT DO
- Unique material per object (unless hero)
- PBR values outside physically plausible range (realistic style)
- Skip vertex color masks for variation
- Leave default material names
- Finalize materials before UVs complete

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Surface recipes | `../refs/materials/surface-recipes.md` | Specific materials |
| Procedural nodes | `../refs/materials/procedural-patterns.md` | Wear, dirt, variation |


---

## ◆ blender-texturing  _(source: el4cteo)_

> Texture authoring in Blender 5.3 - smart-material layers (edge wear, cavity grime, dust, rust, roughness breakup) from curvature/AO masks, z-fight-safe decal and sticker placement, trim sheets, tiling + vertex-color blends, texture painting, baking the look to game texture sets. Use when a material needs wear, dirt, a decal, trims or hand painting, not just wiring.

## Texturing

The execution model is in `blender-core` (→ SKILL.md). Material wiring and measured values are in `blender-pbr-materials` (→ guides/08-materials-texturing-baking.md), and bakes are in `blender-texture-baking` (→ guides/08-materials-texturing-baking.md). This skill authors the *surface story*: where paint chips, where dirt collects, what's printed on it.

### One call each
```
scripts/smart_material.py -- --objects Crate --wear 0.5 --grime 0.4 --dust 0.3
scripts/smart_material.py -- --objects Crate --rust 0.6 --under-color 0.3 0.29 0.28    # rusty iron
scripts/smart_material.py -- --objects SM_Crate --wear 0.5 --curvature-map //tex/T_Crate_CURV.png --ao-map //tex/T_Crate_AO.png
scripts/decal.py -- --target Wall --at 0 -0.1 1.5 --image //decals/hazard.png --size 0.4
scripts/smart_material.py -- --objects Crate --remove                                  # exact restore
```

### How pros layer a material
Start with a clean base (correct albedo/roughness, `blender-pbr-materials` (→ guides/08-materials-texturing-baking.md)), then stack from the inside out: **base → edge wear → rust → grime → dust**. Each layer has a physical cause:
| Layer | Mask (cause) | Look |
|---|---|---|
| Edge wear | convex curvature (edges get hit) + chip noise | reveals the under-material: bare metal, primer, raw wood |
| Rust | cavities and worn edges + blotch noise | orange-brown, metallic 0, roughness ~0.85 |
| Grime | concave curvature + (1 − AO) (dirt collects where it can't be wiped) | dark, rougher, not metallic |
| Dust | world up-facing normal × patch noise (it settles from above) | light, roughness ~0.9 |
| Breakup | fine noise on roughness (±25%) | the cheapest realism win; never ship a flat roughness value |
Pure curvature looks procedural and even. Always multiply in noise so wear is heavy in some places and absent in others. Less is more: wear 0.2–0.4 reads as "used", and 0.7+ reads as "abandoned".

### smart_material.py
- Inserts one `TX_Layers` group in front of every Principled BSDF (Base Color, Roughness, Metallic) and records the originals, so `--remove` restores links and values exactly. Re-running updates values in place. All layer amounts stay inputs on the group node, so you can tweak them there.
- **Curvature**, live and portable (Cycles + EEVEE, no bake): the `TX_Curvature` point attribute is the mean elevation of the neighbours within `--edge-width` (m, default 0.02). It's density-independent: band ≈ edge width. Set the width to roughly the bevel width (1–3 cm on props, 5–10 cm on buildings). Cost: ~1.5 s per 30k verts.
- It needs **mid-poly density** (bevels/supports). When the median edge is > 4× the edge width, the result carries a `note`: wear would smear across whole faces. On low-poly game meshes, bake from the high (`bake_maps.py --high ... --maps normal ao curvature`) and pass `--curvature-map`/`--ao-map` (loaded as Non-Color, read through `--uv`).
- Noise is in **object space** (`--scale` = feature size in m), so masks stick to the asset when it moves. Mirrored/linked duplicates share the pattern, so vary `--scale` or the object if that shows.
- Colors are sRGB 0–1. Defaults: steel under paint (0.56, 0.57, 0.58, metallic 1, roughness 0.35). For wood under paint, use `--under-color 0.45 0.32 0.2 --under-metallic 0 --under-roughness 0.7`.

### To game engines
Engines don't run Blender node trees. Bake the result into a texture set: `bake_maps.py -- --low SM_Crate --maps basecolor roughness metallic normal --pack-orm` (self-bake, no `--high`). Then `build_pbr_material.py --textures` and export. Check the result with `blender-asset-qa` (→ guides/17-qa-review.md) and a lit `look`.

### Decals (decal.py)
- Places a subdivided plane at the closest surface point to `--at`, oriented to the normal and spun by `--rotation`. A Shrinkwrap (project, above surface) keeps it `--offset` (2 mm) off the surface. It's parented, has no shadow, uses Dithered alpha, and its height follows the image aspect.
- It measures the gap at every triangle like `blender-asset-qa` (→ guides/17-qa-review.md) does, and doubles `--subdiv` (to 128) until flat triangles stop dipping over convex creases. The result reports `gap_min_m`/`gap_max_m`. Never place decals at 0 offset: that's guaranteed z-fighting.
- Games: mesh decals cost a draw call each and need alpha sorting. Merge decals that share an atlas into one mesh, use engine projectors (UE Decal Actor, Unity URP Decal Projector, Godot `Decal`) for dynamic ones, or bake them into the base texture.

### Trim sheets, tiling, painting
Trim sheets, tiling with vertex-color blends, hand/texture painting (5.2 brush assets) and headless pixel writes: [../refs/blender-texturing/trims-tiling-painting.md](../refs/blender-texturing/trims-tiling-painting.md).

### Gotchas
- Mask textures (curvature, AO, roughness, ID) must be **Non-Color**. The script forces it, but hand-made nodes often don't.
- Apply scale before computing curvature or setting `--scale`. Both are world-sized.
- `TX_Curvature` is mesh data. Applying modifiers or remeshing afterward invalidates it, so re-run after topology changes.
- Viewport EEVEE vs Cycles: identical masks (no Bevel/Pointiness/AO shader nodes are used, because those are Cycles-only or screen-space).


---

## ◆ texture-workflow  _(source: arjun988)_

> Production texture workflow for atlases, baking AO/curvature/normal/roughness maps, decals, and texture memory optimization. Use for game-ready texture pipelines in Blender via MCP.

## Texture Workflow

Bake high-poly detail to efficient texture sets. Optimize memory. Engine-ready outputs.

### When to Use

- Baking sculpt detail to normal maps
- Creating texture atlases for modular kits
- PBR texture set generation
- Decal placement and blending
- Texture memory optimization

### Workflow

```
High/Low Poly Setup → Cage Setup → Bake Maps → Composite
    → Atlas Pack → Engine Format Export → Validation
```

### Standard PBR Texture Set

| Map | Format | Notes |
|-----|--------|-------|
| Base Color | sRGB PNG | No embedded AO |
| Normal | Linear PNG | OpenGL convention unless engine specifies |
| Roughness | Linear PNG | Single channel |
| Metallic | Linear PNG | Single channel |
| AO | Linear PNG | Multiply in shader, not base color |
| Height | Linear PNG | Optional parallax |
| Emission | sRGB PNG | Mask-based |
| ORM Packed | Linear PNG | R=AO, G=Roughness, B=Metallic (Unreal) |

Naming: `T_[Asset]_[Map]` per `../refs/shared/naming-conventions.md`

### Bake Setup

```
1. Low-poly mesh with UVs (active)
2. High-poly mesh (sculpt or detail) — selected
3. Cage extrusion: 0.01–0.05m (adjust per asset scale)
4. Ray distance: match cage
5. Bake margin: 16px minimum
6. Anti-aliasing: enabled
```

### Maps to Bake

| Map | Source | Priority |
|-----|--------|----------|
| Normal | High→Low | Required |
| AO | High or low (cavity) | Required |
| Curvature | High sculpt | Wear masks |
| Position | High | Optional (blending) |
| Thickness | Subsurface meshes | Characters |

### Texture Atlas Strategy

Modular kits share one atlas:
```
1. All modules UV'd to shared 0–1 or UDIM space
2. Bake each module to atlas regions
3. Trim sheet areas for repeating detail
4. Single material references atlas
5. Document region map for artists
```

### Decals

- Decal mesh projected on surface
- Separate UV channel or atlas region
- Blend via alpha mask
- Limit decal overdraw in engine

### Memory Optimization

| Technique | Savings |
|-----------|---------|
| ORM packing | 3 textures → 1 |
| Shared atlas | N materials → 1 texture |
| Lower res on hidden surfaces | 50%+ memory |
| BC compression in engine | 4:1 or 6:1 |
| Trim sheets | Reuse detail across assets |

### Resolution Guidelines

See `../refs/shared/polycount-budgets.md` texture section.

### MCP Integration

1. Setup bake objects via MCP
2. Configure bake settings via MCP if supported
3. Export baked images via MCP
4. Assign baked textures to materials via MCP
5. Query texture count and resolution

### Validation Checklist

- [ ] Normal map correct orientation (test in engine)
- [ ] No UV seams visible in bake
- [ ] AO not baked into base color
- [ ] Consistent texel density in final textures
- [ ] Texture resolution within budget
- [ ] Files named per convention
- [ ] sRGB vs Linear correctly assigned

### Constraints

#### MUST DO
- Bake high-poly detail before discarding sculpt
- Use cage for clean normal bakes
- Pack ORM for engine efficiency
- Test normal map orientation in target engine
- Document atlas regions for modular kits

#### MUST NOT DO
- Bake without cage on complex shapes
- Embed AO in base color (PBR standard)
- Exceed texture budget without LOD justification
- Use inconsistent normal map conventions
- Skip margin in bake settings

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Bake troubleshooting | `../refs/texture-workflow/bake-troubleshooting.md` | Bake artifacts |
| ORM packing | `../refs/texture-workflow/orm-packing.md` | Unreal/Unity export |


---

## ◆ blender-texture-baking  _(source: el4cteo)_

> Bake texture maps in Blender 5.3 Cycles - high-to-low normal maps with cage/extrusion, AO, curvature, ID, thickness, base color/roughness/metallic from procedurals, ORM packing, OpenGL vs DirectX, margins, GPU baking, fixing skewing/waviness/seams. Use when transferring sculpt or high-poly detail to game meshes or converting procedural materials to textures.

## Texture Baking (Cycles)

The execution model is in `blender-core` (→ SKILL.md). UVs come from `blender-retopology-uv` (→ guides/07-retopology-uv.md) and materials from `blender-pbr-materials` (→ guides/08-materials-texturing-baking.md).

### One call
```
scripts/bake_maps.py -- --low SM_Crate --high Crate_high Crate_bolts --maps normal ao curvature id \
   --res 2048 --samples 64 --margin-px 16 --pack-orm --out //textures
```
Self-bake (procedural → textures, no `--high`): `--low SM_Crate --maps basecolor roughness metallic normal --pack-orm`.
The script picks the GPU (OptiX/CUDA/HIP/Metal/oneAPI) and falls back to CPU, creates the target images with correct color spaces, cleans up its temporary nodes, and saves `T_<name>_<N|AO|CURV|BC|R|M|ORM...>.png`.

### Preparation checklist (most bake bugs come from this list)
1. **Low poly**: UVs unwrapped, no overlaps (stacked/mirrored islands moved +1 U), padding ≥ 8 px at the bake resolution, scale applied.
2. **Hard edges = UV seams** on the low poly. Use either smooth shading with the bake handling gradients, or hard edges split at seams. Never put a hard edge inside a UV island.
3. **Triangulate the low poly the same way the engine will**, or export the triangulated mesh. Mismatched triangulation shows as shading seams.
4. **High poly** covers the low completely and pokes out of it only a little. Floaters (bolts, panel details) can hover just above the surface, but must stay within the extrusion distance.
5. **Names**: `X_low` / `X_high` pairs. Bake per part, or explode the parts apart (move each pair along an axis) so neighbouring parts don't project onto each other, then put them back.
6. Apply modifiers on the high poly as needed (multires and subd are evaluated automatically).

### Rays: extrusion vs cage
- `--extrusion` (meters) pushes the ray origin outward from the low surface. It must be **greater than the farthest distance the high poly sticks out** of the low. The default is 2% of the low's diagonal; `max_ray_distance` is 2 × extrusion.
- **Cage** (`--cage Crate_cage`): a copy of the low with the same topology, inflated (Displace/"Push"). Use it when uniform extrusion fails (sharp concave corners, thin parts). Edit the cage locally where rays miss.
- Too small: holes or missing details. Too large: other parts of the mesh project in (intersections, "ghosting").

### Map guide
| Map | Space | Notes |
|---|---|---|
| normal | Non-Color, tangent, OpenGL (`--directx` for Unreal) | 16-sample AA is plenty; 8-bit PNG is fine for games |
| ao | Non-Color | 64–256 samples; bake with the high only (no ground) unless contact AO is wanted |
| curvature | Non-Color, 0.5 = flat | derived from the baked normal (convex white / concave dark); drives edge wear |
| id | sRGB | one flat color per high-poly **material**; use materials as masks |
| thickness | Non-Color | AO with inside rays; dark = thin; for SSS/translucency masks |
| basecolor/metallic/opacity | via emission override | reads the Principled inputs of the source materials (also procedural chains) |
| roughness, emit, combined | native Cycles passes | combined = lit result (lightmaps, stylized) |
| position | float | gradient masks |
ORM = R:AO G:Roughness B:Metallic, the glTF/Unreal standard. Unity uses a different packing (`blender-pbr-materials` (→ guides/08-materials-texturing-baking.md)).

### Fixing common artifacts
| Symptom | Cause | Fix |
|---|---|---|
| Wavy lines on cylinders | low poly too low, smoothing gradients | add segments, use a cage, or more support on the low |
| Skewed details (bolts lean) | ray direction follows the averaged low normals | hard edges + seams, a cage, or bake the floater separately |
| Black/garbage areas | rays miss or hit the back faces | raise extrusion, fix flipped normals (`blender-asset-qa` (→ guides/17-qa-review.md)), check high coverage |
| Seams visible in engine | margin too small, hard edge without a seam, different tangents | margin ≥ 16 px @2k, seams at hard edges, export tangents (MikkTSpace) |
| Details from a neighbouring part | parts too close | explode the bake, or bake per object pair |
| Inverted green look in engine | OpenGL/DirectX mismatch | `--directx` for Unreal, or flip G in the texture importer |
| Stepping/banding | 8-bit with large flat gradients | bake to 16-bit (`float_buffer`) and dither on export |

### Baking non-PBR data
- **Vertex colors**: `bake.target = "VERTEX_COLORS"` with an active color attribute (useful for mobile and Roblox-free shading).
- **Lightmaps**: bake `combined` onto UV2 (`--uv-layer UVMap_Lightmap`) with the scene lights.
- **Multires** (no separate high object): `bake.use_multires=True`, `bake.type="NORMALS"|"DISPLACEMENT"|"VECTOR_DISPLACEMENT"`, `bake.use_lores_mesh=True`, then `bpy.ops.object.bake_image()`. The viewport level is the low, the sculpt level is the high.

### Gotchas
- The target image must be the **active** Image Texture node in **every** material of the low object (the script handles this).
- Baking in Cycles uses the active UV map (`--uv-layer` to pick).
- Images aren't saved automatically: `img.save()` or `save_render`. Packed or internal images disappear on reload.
- 5.2: the Cycles texture cache (`.tx`) is for render memory and doesn't affect bake results.
- Run `blender-asset-qa` (→ guides/17-qa-review.md) on low + high first, because flipped normals and floating chunks produce most bake garbage.
