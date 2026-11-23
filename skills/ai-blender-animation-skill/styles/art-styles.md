# Art styles (stylized, NPR, retro, anime...)

> Fused guide. Script paths like `scripts/x.py` are relative to the **ai-blender-animation-skill skill root**; all Python helpers live in one flat `scripts/` folder (shared `_bpyx.py`). Node helpers are in `scripts/node/`. Where two sources disagree, prefer the Blender 5.x rules in SKILL.md.

Sections: `blender-stylized-npr`, `stylized-style`, `realistic-style`, `lowpoly-style`, `anime-style`, `manga-style`, `chibi-style`, `cartoon-style`, `comic-book-style`, `hand-painted-style`, `painterly-style`, `pixel-art-style`, `voxel-style`, `isometric-style`, `hd-2d-style`, `retro-8bit-style`, `retro-16bit-style`, `vector-style`, `minimalist-style`, `noir-style`, `stop-motion-craft-style`, `frutiger-aero-style`, `visual-console-eras`


---

## ◆ blender-stylized-npr  _(source: el4cteo)_

> Stylized / NPR looks in Blender 5.3 - toon and cel shading (bands, shadow tint, rim, hard specular), anime faces with custom normals, inverted-hull outlines with smoothed outline normals for game engines, Line Art and Freestyle lines, Grease Pencil drawing, unlit export. Use for anime, cartoon, comic, cel-shaded or outlined styles.

## Stylized / NPR

The execution model is in `blender-core` (→ SKILL.md). Base colors still come from `blender-pbr-materials` (→ guides/08-materials-texturing-baking.md)/`blender-texturing` (→ guides/08-materials-texturing-baking.md). This skill replaces how they're lit.

### One call each
```
scripts/toon_setup.py -- --objects Hero Sword --bands 2 --rim 0.4 --outline 0.004
scripts/toon_setup.py -- --objects Hero --bands 3 --spec 0.3 --smooth-normals      # + engine outline data
scripts/toon_setup.py -- --objects Hero --lighting scene                           # EEVEE: all lights + cast shadows
scripts/toon_setup.py -- --line-art --outline 0                                    # scene-wide Line Art
scripts/toon_setup.py -- --objects Hero Sword --remove --line-art                  # exact restore
```

### toon_setup.py
- Inserts an `NPR_Toon` emission group between each material's Principled base color and the output, and records the original surface link for `--remove`. Re-running updates values in place.
- **`--lighting key`** (default, Cycles + EEVEE): shading = N·L against one sun (`--light`; `NPR_Key` is created if there's none). Drivers follow the sun's rotation, so rotate the sun to art-direct the shadow shape. This is how engine toon shaders work, and the look matches after export.
- **`--lighting scene`**: Shader to RGB on a white diffuse, so every light and cast shadow shapes the bands. **EEVEE only.** Measured: in Cycles, Shader to RGB returns a constant regardless of light (identical render at 0, 3 and 10 W/m² sun).
- Bands: 2 (lit/shadow, classic anime) or 3 (adds a mid band 0.45 above `--threshold`). `--softness` (0.02) is the half-width of the band edge, so 0 aliases. `--shadow-tint` multiplies the base color: use cool and saturated (0.6, 0.55, 0.75), never grey/black, because grey shadows read as dirty.
- `--rim` (0–1) adds a lit-side rim, and `--spec` (0–1) a hard Blinn highlight disc (0.2–0.4 for hair/metal, 0 for skin).
- Sets **view transform Standard**: AgX/Filmic desaturate and compress flat colors, so the albedo you pick is the pixel you get only under Standard. The original is restored on `--remove`.

### Outlines (pros use several at once)
| Method | Where it works | Notes |
|---|---|---|
| Inverted hull (`--outline`, m) | Cycles, EEVEE, engines | Solidify outward, flipped normals, outline slot, Backfacing→transparent. Width 2–6 mm on a 1.75 m character. `--outline-group` = vertex group for width (taper toward tips, 0 inside the mouth) |
| `--smooth-normals` | engine outline shaders | `NPR_OutlineNormal` corner color = position-welded normal in tangent space (0.5 + 0.5n). Hard edges/UV splits no longer open gaps. Decode `n = TBN·(c·2−1)` |
| Line Art (`--line-art`, Grease Pencil) | renders | contour + crease + intersection from the camera. Needs a scene camera. `--line-radius` (m) |
| Freestyle | renders | `scene.render.use_freestyle = True`, `line_thickness` px. Slowest, most options |
Known hull limits: lines at intersections and inner creases are missing (use Line Art for those in renders), and hard-edged meshes split the hull. In Blender, merge by distance before the Solidify. In engines, use `--smooth-normals`.

### Anime faces and hair
- Face shadows from real normals look blotchy. Transfer **custom normals** from a simple ellipsoid proxy: a Data Transfer modifier with `use_loop_data=True`, `data_types_loops={'CUSTOM_NORMAL'}`, `loop_mapping='POLYINTERP_NEAREST'` (no auto smooth needed since 4.1), masked by a face vertex group. Engines import the custom normals (FBX/glTF export normals).
- For a stylized nose/cheek shadow, many games use an SDF face shadow texture sampled with the light angle in-engine. Author it as a grayscale threshold map, not in the node tree.
- Hair: a strong `--spec` plus a hand-painted highlight band ("angel ring") in the base color texture.

### Grease Pencil (5.x API)
```python
gp = bpy.data.grease_pencils.new("Ink"); ob = bpy.data.objects.new("Ink", gp); scene.collection.objects.link(ob)
mat = bpy.data.materials.new("Ink"); bpy.data.materials.create_gpencil_data(mat); gp.materials.append(mat)
drawing = gp.layers.new("Lines").frames.new(1).drawing
drawing.add_strokes([3]); s = drawing.strokes[0]
for i, p in enumerate(s.points): p.position, p.radius = (i * 0.5, 0, 0), 0.01   # radius in m
```
Strokes expose `cyclic`, `material_index`, `fill_id`, `hide_stroke`. Raw attributes: `drawing.attributes` (`position`, `radius`). `GreasePencilv3`/`grease_pencils_v3` are gone (5.0). 5.2 Line Art can emit fill strokes (`fill_strokes`).

### To game engines
Node toon shading doesn't export. Export the base color textures and rebuild the toon ramp in the engine (UE material/post-process, Unity URP toon shader, Godot `ShaderMaterial`), driven by the same sun direction. Ship the hull as a second material slot (apply the modifier), or as `NPR_OutlineNormal` for a shader outline pass.
For flat, unlit assets in glTF, use a **Background** shader, or Light Path *Is Camera Ray* mixing Transparent→Background: both export as `KHR_materials_unlit`. Emission exports as emissive on a black base, not unlit (measured).

### Gotchas
- Apply scale before `--outline`: Solidify thickness is in object space.
- Bloom and AO fight the flat look. Keep the world dim and uniform, and use one key light plus maybe a rim light.
- `--lighting scene` bands shift with light energy (luminance 0.3 ≈ threshold 0). Raise/lower `--threshold` instead of the light power.


---

## ◆ stylized-style  _(source: arjun988)_

> Stylized art direction for Blender with shape language, exaggeration, color harmony, NPR rendering, and hand-painted asset workflows. Use for non-photorealistic game and animation projects.

## Stylized Style Specialist

Deliberate shape language. Exaggerated proportions. Color harmony. NPR rendering.

### When to Use

- Non-photorealistic games
- Hand-painted texture workflows
- Animated/stylized characters
- Fantasy environments with art direction
- Toon/cel-shaded rendering

### Core Principles

1. **Shape language** — Circles=friendly, squares=stable, triangles=danger
2. **Exaggeration** — Push proportions beyond realistic
3. **Color harmony** — Limited palette; intentional accent colors
4. **Silhouette clarity** — Strong readable shapes
5. **Detail in texture** — Not micro-geometry

### Shape Language

| Shape | Association | Use |
|-------|-------------|-----|
| Circle/Oval | Friendly, approachable | Heroes, cute creatures |
| Square/Rectangle | Stable, reliable | Architecture, guards |
| Triangle | Dynamic, dangerous | Villains, spikes, roofs |

Combine shapes consistently per character/faction.

### Proportion Exaggeration

| Feature | Stylized Approach |
|---------|-------------------|
| Head | 25–40% of height (chibi to semi-realistic) |
| Hands | Larger for expressiveness |
| Eyes | Enlarged for emotion |
| Limbs | Tapered; simplified joints |
| Weapons | Oversized for readability |

### Color Harmony

**Triadic:** Three equidistant hues — vibrant, balanced
**Complementary:** Opposite hues — high contrast accents
**Analogous:** Adjacent hues — harmonious environments

Rules:
- Limit palette to 3–5 core colors + neutrals
- Reserve saturated accents for interactive elements
- Desaturate backgrounds; saturate foreground subjects

### Material Approach

- Hand-painted albedo priority over PBR accuracy
- Flat or stepped roughness (not continuous PBR)
- Rim lighting built into texture (not just shader)
- Subsurface on skin: exaggerated warm tones
- No photoreal micro-detail

### NPR Rendering

Coordinate with rendering skill:
- Toon BSDF or Shader to RGB setups
- Stepped lighting (2–3 bands)
- Outline pass: inverted hull or Freestyle
- Bloom on emissive accents
- Flat ambient forbidden — maintain form readability

### Hand-Painted Texture Workflow

```
1. Flat base color blocks
2. Define light/shadow shapes (not gradients from bake)
3. Edge highlights (warm) and shadows (cool)
4. Detail pass: minimal; suggestive not literal
5. Ambient occlusion painted, not baked
```

### Character Stylization

- Simplified anatomy; avoid uncanny valley
- Hair as solid shapes or card clusters
- Clothing folds: painted, not simulated
- Facial features: large eyes, small nose (style dependent)

### Environment Stylization

- Exaggerated verticality in forests/mountains
- Architecture: oversized elements (doors, windows)
- Vegetation: puff/cloud shapes (not botanical accuracy)
- Water: stylized foam patterns

### MCP Integration

1. Block exaggerated proportions via MCP
2. Assign stylized materials via MCP
3. Configure NPR render settings via MCP
4. Validate silhouette with flat shading via MCP
5. Limit geometry detail per stylized budgets

### Constraints

#### MUST DO
- Define shape language per asset/faction
- Maintain color palette consistency
- Exaggerate intentionally, not accidentally
- Paint detail in textures
- Test NPR render early

#### MUST NOT DO
- Mix photoreal PBR with stylized shapes without intent
- Micro-detail geometry (use texture)
- Realistic proportions unless semi-stylized target
- Full PBR roughness accuracy
- Skip outline/rim if NPR project requires

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| NPR shader setup | `../refs/stylized-style/npr-shaders.md` | Rendering setup |
| Color palettes | `../refs/stylized-style/palette-examples.md` | Art direction |

### Related Style Packs
- `cartoon-style` (→ styles/art-styles.md), `anime-style` (→ styles/art-styles.md), `comic-book-style` (→ styles/art-styles.md), `manga-style` (→ styles/art-styles.md), `hand-painted-style` (→ styles/art-styles.md), `painterly-style` (→ styles/art-styles.md)
- `chibi-style` (→ styles/art-styles.md), `pixel-art-style` (→ styles/art-styles.md), `hd-2d-style` (→ styles/art-styles.md), `stop-motion-craft-style` (→ styles/art-styles.md)


---

## ◆ realistic-style  _(source: arjun988)_

> Photorealistic AAA art direction for Blender including photogrammetry cleanup, real-world scale, high-poly workflows, PBR accuracy, and scan optimization. Use for cinematic and AAA game realism.

## Realistic Style Specialist

Physically accurate materials. Real-world scale. High-poly to baked low-poly pipeline. AAA standards.

### When to Use

- AAA game assets requiring realism
- Cinematic renders
- Photogrammetry scan cleanup
- Product visualization
- Architectural visualization

### Core Standards

1. **Real-world scale** — 1 Blender unit = 1 meter; verify all dimensions
2. **PBR accuracy** — Physically plausible material values
3. **High-poly to low-poly** — Sculpt/scan → bake → game mesh
4. **Micro-detail via textures** — Not geometry at distance
5. **Reference-driven** — Match real-world photography

### Scale Verification

| Reference | Dimension |
|-----------|-----------|
| Door height | 2.03–2.13m |
| Human eye height | 1.6–1.7m |
| Hand width | 0.08–0.1m |
| Brick | 0.065 × 0.215m |
| Car height | 1.4–1.6m |

Always place scale reference in scene.

### High-Poly Workflow

```
Scan/Sculpt High-Poly → Cleanup → UV Low-Poly → Bake Maps
    → PBR Texturing → Engine Export
```

Polycount on high-poly: unlimited for bake source; never exported to game.

### Photogrammetry Cleanup

| Issue | Fix |
|-------|-----|
| Scan holes | Fill with sculpt/mesh patch |
| Floating geometry | Delete; rebuild clean |
| Decimation artifacts | Remesh problematic areas |
| Color variation | Rebake albedo; neutralize lighting |
| Wrong scale | Measure known feature; rescale |

### PBR Accuracy

| Material | Albedo | Roughness | Metallic |
|----------|--------|-----------|----------|
| Fresh concrete | 0.5 gray | 0.85 | 0 |
| Polished chrome | 0.8 | 0.05 | 1 |
| Human skin | photographic | 0.4–0.6 | 0 |
| Clean glass | 0.9 | 0 | 0 (transmission) |
| Old iron | 0.3 dark | 0.7 | 1 |

Use photographic reference for albedo; never guess saturated colors.

### Micro-Detail Strategy

| Distance | Detail Method |
|----------|---------------|
| Hero close-up | Geometry + normal + roughness |
| Mid distance | Normal + roughness maps |
| Far distance | Albedo + roughness only |
| Background | Decal/card detail |

### AAA Asset Checklist

- [ ] Real-world scale verified
- [ ] High-poly source archived
- [ ] Clean low-poly with efficient UVs
- [ ] 2K–4K textures on hero (per budget)
- [ ] ORM packed for engine
- [ ] LODs generated
- [ ] Turntable render approved
- [ ] Engine import verified

### Cinematic vs Game Realism

| Aspect | Cinematic | Game |
|--------|-----------|------|
| Polycount | Higher hero | Strict LOD |
| Textures | 4K–8K | 2K max typical |
| Materials | Complex shaders | Standard PBR |
| Lighting | HDRI + area | Baked + dynamic |
| Detail | Full geometry | Baked normal |

### MCP Integration

1. Import/cleanup scan meshes via MCP
2. Setup bake high/low pairs via MCP
3. Assign PBR materials with accurate values via MCP
4. Query dimensions for scale validation via MCP
5. Export with full texture set via export-pipeline

### Constraints

#### MUST DO
- Reference real-world photography
- Verify scale with known dimensions
- Bake micro-detail to normal maps
- Use physically plausible PBR values
- Archive high-poly source

#### MUST NOT DO
- Export high-poly to game engine
- Saturated albedo without reference
- Skip LOD generation for game assets
- Ignore photogrammetry artifacts
- Mix stylized proportions

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| PBR values | `../refs/realistic-style/pbr-values.md` | Material setup |
| Scan cleanup | `../refs/realistic-style/scan-cleanup.md` | Photogrammetry |

### Related
- Photoreal path stays here; for era crunch use `visual-console-eras` (→ styles/art-styles.md) or `lowpoly-style` (→ styles/art-styles.md).


---

## ◆ lowpoly-style  _(source: arjun988)_

> Low-poly art direction for Blender inspired by PS1/PS2, Lethal Company, Mouthwashing, and Fear to Fathom. Use for readable silhouettes, minimal polygons, simple materials, and strong atmosphere.

## Low Poly Style Specialist

Readable silhouettes. Large shapes. Minimal polygons. Atmosphere over detail.

### When to Use

- Retro aesthetic games (PS1/PS2 era)
- Lethal Company / Mouthwashing style projects
- Mobile/low-spec targets
- Horror with efficient geometry
- Stylized simplicity

### Core Rules

1. **Readable silhouettes** — Shape reads at distance without detail
2. **Minimal polygons** — Every face must earn its place
3. **Large shapes** — Primary forms dominate; micro-detail forbidden
4. **Simple materials** — Flat or lightly textured; 512px default
5. **Limited texture sizes** — 256–512px most assets; 1024 hero only
6. **Strong atmosphere** — Lighting and fog carry visual weight

### Polygon Guidelines

| Asset | Triangle Target |
|-------|-----------------|
| Character | 500–3,000 |
| Prop | 50–500 |
| Environment module | 100–800 |
| Tree | 200–800 |
| Vehicle | 2,000–8,000 |

See `../refs/shared/polycount-budgets.md` — apply 50–90% reduction.

### Modeling Approach

- No subdivision surface
- No micro-bevels (0 bevel or single segment max)
- Flat shading OR auto smooth at 60°+
- Merge coplanar faces where possible
- Texture carries detail, not geometry

### PS1 Authenticity (Optional)

| Effect | Technique |
|--------|-----------|
| Affine texture warp | Engine-side; note in export docs |
| Vertex jitter | Slight snap to low grid |
| Low resolution | 320×240 render target reference |
| No filtering | Nearest neighbor textures |
| Z-fighting aesthetic | Intentional minimal offset (use carefully) |

### PS2 Era

- Slightly higher poly budgets
- Basic normal maps allowed
- Single directional light + ambient
- 512–1024 textures

### Material Approach

- Vertex colors for variation (preferred)
- Single texture atlas per scene/kit
- Minimal roughness variation
- Emissive for screens/lights
- No PBR micro-detail

### Silhouette Test

Before approving any asset:
1. Solid flat color material
2. View at gameplay distance
3. Silhouette must communicate identity
4. If unreadable → simplify geometry, not add detail

### Lethal Company Influence

- Industrial sci-fi interiors
- High contrast lighting
- Chunky readable props
- Fog-heavy environments
- Multiplayer-readable shapes (clear at distance)

### Mouthwashing Influence

- Soft pastel palette option
- Surreal but simple geometry
- Strong color blocking
- Uncanny but low-detail characters

### MCP Integration

1. Create low-poly blockouts via MCP
2. Enforce face count limits via MCP queries
3. Assign flat materials via MCP
4. Validate triangle budgets continuously
5. Skip subdiv/bevel modifiers entirely

### Constraints

#### MUST DO
- Enforce strict poly budgets
- Prioritize silhouette over surface detail
- Use vertex colors and atlases
- Test at gameplay camera distance
- Coordinate atmosphere with lighting skill

#### MUST NOT DO
- Subdivision surfaces
- High-resolution textures on background assets
- Micro-bevels or weighted normal stacks
- Sculpting detail (bake workflow unnecessary)
- Exceed triangle budgets "just a little"

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| PS1 techniques | `../refs/lowpoly-style/ps1-aesthetic.md` | Retro authentic look |
| Asset budgets | `../refs/shared/polycount-budgets.md` | Budget setting |


---

## ◆ anime-style  _(source: arjun988)_

> Anime and cel-shaded art direction for Blender with hard color breaks, toon shaders, clean silhouettes, and anime proportion language.

## Anime Style

Hard color breaks. Clean silhouettes. Cel shading. Anime proportion language.

### When to Use

- Anime / cel-shaded characters and props
- Toon shader lookdev
- Hard shadow graphic looks (not soft PBR)

### Core Tenets

1. **Flat tonal regions** — 2–4 value steps max per material
2. **Hard shadow terminators** — Specular as graphic shapes
3. **Line / silhouette clarity** — Optional freestyle or inverted hull
4. **Proportion language** — Eyes, hair masses, simplified anatomy
5. **Palette discipline** — Limited hues; accent sparingly

### Shading Approach

| Method | Use |
|--------|-----|
| Shader Toon / ColorRamp on diffuse | Fast Eevee/Cycles toon |
| Emission + ramp | Graphic unlit regions |
| Freestyle / grease pencil lines | Contours |
| Solidify inverted hull | Thick outlines |

### Modeling Notes

- Simplify secondary forms; hair as masses
- Creases where color breaks need support
- Avoid noisy micro detail fighting flat shading

### Lighting

- Single clear key for graphic shadows
- Rim optional for separation
- Avoid heavy soft GI wash unless intentional

### Vs stylized-style

- `stylized-style` (→ styles/art-styles.md) = broad NPR / hand-painted
- `anime-style` = cel breaks, anime proportions, toon stack

### Constraints

#### MUST DO
- Limit value steps
- Keep silhouette iconic
- Test with toon lighting early

#### MUST NOT DO
- Full PBR roughness noise as primary look
- Over-subsurface that melts cel breaks

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Cel Shader Setup | `../refs/anime-style/cel-shader-setup.md` | When needed |
| Anime Proportion | `../refs/anime-style/anime-proportion.md` | When needed |


---

## ◆ manga-style  _(source: arjun988)_

> Manga-inspired art direction for Blender emphasizing monochrome value design, speed lines, screentone feel, and manga panel staging.

## Manga Style

Value-first. Screentone feel. Panel staging. Distinct from full-color anime.

### Tenets
1. Design in grayscale values first
2. Screentone / hatch textures sparingly
3. Speed lines and emphasis FX
4. Expressive faces / eyes per demographic
5. Black-heavy compositions OK

### Vs anime-style
Anime = color cel; Manga = print value language (can still be 3D color with manga staging).


---

## ◆ chibi-style  _(source: arjun988)_

> Chibi and SD proportion art direction for Blender characters with oversized heads, simplified anatomy, and cute silhouette rules.

## Chibi Style

Big head. Short body. Maximum appeal silhouette.

### Ratios
Head often 1/2 to 1/3 of total height. Simplify fingers. Large eyes optional by genre.


---

## ◆ cartoon-style  _(source: arjun988)_

> Cartoon art direction for Blender with squash-stretch readable shapes, bold colors, and graphic silhouettes for games and animation.

## Cartoon Style

Bold shapes. Graphic color. Readability over realism.

### When to Use
- Cartoon games / animated props and characters
- Exaggerated silhouettes and expressions
- When anime cel language is too specific

### Tenets
1. Silhouette first
2. Exaggerated proportions
3. Limited palette, bold accents
4. Soft or graphic shading (project choice)
5. Detail in shapes, not micro-PBR

### Handoff
`character-artist` (→ guides/05-characters-clothing-face.md) / `prop-artist` (→ guides/03-props-vehicles-archviz.md) → `materials` (→ guides/08-materials-texturing-baking.md) → `lookdev` (→ guides/13-lighting-camera-lookdev.md)

### Reference Guide
| Topic | Reference |
|-------|-----------|
| Shape language | `../refs/cartoon-style/cartoon-shape-language.md` |


---

## ◆ comic-book-style  _(source: arjun988)_

> Comic book and graphic-novel art direction for Blender with ink-line emphasis, halftone cues, and high-contrast framing.

## Comic Book Style

Ink-ready contrast. Panel-friendly staging. Halftone optional.

### Tenets
1. High contrast lighting for ink read
2. Strong contour / crease support
3. Limited screentone / hatch language in textures or comp
4. Hero poses and camera angles
5. Speeds lines / impacts as FX meshes when needed

### Reference Guide
| Topic | Reference |
|-------|-----------|
| Ink & tone | `../refs/comic-book-style/ink-tone.md` |


---

## ◆ hand-painted-style  _(source: arjun988)_

> Hand-painted texture art direction for Blender with brushwork albedo, soft value transitions, and stylized PBR restraint.

## Hand Painted Style

Brushwork in albedo. Geometry supports paint, not microdetail.

### Tenets
1. Paint values in albedo
2. Low roughness variation unless wet/metal accents
3. Soft bevels for paint catch
4. Atlas-friendly for kits
5. Avoid photoreal photo-bashed noise


---

## ◆ painterly-style  _(source: arjun988)_

> Painterly art direction spanning watercolor and oil-painting looks for Blender using soft edges, pigment texture, and illustrative lighting.

## Painterly Style

Pigment feel. Soft edges. Illustration lighting.

### Sublooks
- Watercolor: paper grain, bleeds, light washes
- Oil: thicker strokes, richer impasto suggestion in texture

### Tenets
1. Soft terminators
2. Pigment/paper overlays in mat or comp
3. Limited harsh specular
4. Composition like a canvas, not a game HUD shot


---

## ◆ pixel-art-style  _(source: arjun988)_

> Pixel-art and texel-constrained art direction for Blender assets destined for pixel rendering, low-res textures, or HD-2D-adjacent pixel reads.

## Pixel Art Style

Texel discipline. Crisp pixels. Limited palette.

### Tenets
1. Declare target texel size / texture res
2. Nearest filtering intent
3. Limited palette
4. Avoid thin triangles that shimmer
5. Ortho or locked angles help readability

### Reference Guide
| Topic | Reference |
|-------|-----------|
| Texel rules | `../refs/pixel-art-style/texel-rules.md` |


---

## ◆ voxel-style  _(source: arjun988)_

> Voxel and Minecraft-adjacent art direction for Blender with block grid modeling, limited palettes, and chunk-friendly assets.

## Voxel Style

Block grid language. Limited palette. Chunk-friendly forms.

### When to Use

- Minecraft-adjacent / voxel game assets
- Blockout aesthetic as final style
- Grid-snapped props and characters

### Core Tenets

1. **Grid snap** — Occupancy on explicit voxel size (e.g. 0.1 / 1.0m)
2. **No diagonal organic bevels** — Cubes and stepped forms
3. **Palette atlas** — Few colors; readable blocks
4. **Silhouette via steps** — Not smooth curves
5. **Chunk modularity** — Pieces fit tile sizes

### Workflow

```
Choose voxel size → Block occupancy → Merge cubes
  → Palette materials → Optional GN instance → Export
```

### Modeling Tips

- Start from cubes; boolean union / merge by distance
- Characters: stepped limbs, clear head block
- Avoid subdivision surface (breaks voxel language)
- Remesh to blocks only if converting from smooth

### Materials

- Flat colors or nearest-neighbor textures
- Atlas preferred
- Emission for glow blocks sparingly

### Vs lowpoly-style

- `lowpoly-style` (→ styles/art-styles.md) allows irregular low tris / PS1 vibes
- `voxel-style` enforces grid occupancy aesthetic

### Constraints

#### MUST DO
- Declare voxel size in brief
- Snap consistently
- Keep palette small

#### MUST NOT DO
- Smooth shading that hides block edges (unless intentional glass)
- Organic sculpt detail

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Voxel Grid | `../refs/voxel-style/voxel-grid.md` | When needed |
| Voxel Characters | `../refs/voxel-style/voxel-characters.md` | When needed |


---

## ◆ isometric-style  _(source: arjun988)_

> Isometric and strategy-game art direction for Blender including diorama framing, true-iso camera setup, readable silhouettes, and tile asset rules.

## Isometric Style

Readable dioramas. True iso framing. Tile-aware assets.

### When to Use

- Strategy / sim / city-builder assets
- Isometric diorama renders
- Orthographic hero presentations

### Camera Setup

```
Camera type: Orthographic
Rotation: typically 54.736° / 30° patterns (true iso) OR project-specific dimetric
Scale: frame subject with padding for UI
CAM_Iso_[Shot]
```

Match project’s exact iso angles — do not invent per asset.

### Asset Rules

1. **Readable from iso angle first** — Not perspective hero camera
2. **Tile footprint** — Document cell size (e.g. 1×1, 2×2)
3. **Height clarity** — Vertical read without confusion
4. **Edge contrast** — Separate from ground plane
5. **LOD for dense maps** — Far tiles cheaper

### Modeling

- Avoid detail only visible from ground FPS view
- Strong top/side planes
- Anchor pivot to tile corner or center per kit standard

### Presentation

- Soft key + cool fill common for dioramas
- Slight AO / ground shadow for lift
- Optional `compositing` (→ guides/14-rendering-compositing.md) grade for portfolio

### Constraints

#### MUST DO
- Lock camera angle for the set
- Document tile size and pivot rule
- Check readability at game ortho scale

#### MUST NOT DO
- Detail undersides invisible in iso
- Mix perspective cameras into iso kits without reason

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Iso Camera | `../refs/isometric-style/iso-camera.md` | When needed |
| Tile Footprints | `../refs/isometric-style/tile-footprints.md` | When needed |


---

## ◆ hd-2d-style  _(source: arjun988)_

> HD-2D art direction combining pixel characters/sprites with 3D environments, depth of field, and theatrical lighting.

## HD-2D Style

Pixel actors. 3D stage. Tilted theatrical camera. Creamy DoF.

### Tenets
1. Characters: pixel/billboard or texel-locked
2. Environments: soft 3D with painted textures
3. Strong DoF / god rays
4. Ortho-leaning perspective
5. Warm theatrical keys


---

## ◆ retro-8bit-style  _(source: arjun988)_

> Retro 8-bit art direction for Blender-assisted pixel/low-res aesthetics inspired by NES-era constraints.

## Retro 8-bit Style

Severe palette limits. Chunky read. Sprite logic.

### Constraints
Very low color count, high contrast characters, simple props, avoid gradients unless dithered.


---

## ◆ retro-16bit-style  _(source: arjun988)_

> Retro 16-bit art direction for Blender-assisted SNES/Genesis-era color richness, dither cues, and sprite-like clarity.

## Retro 16-bit Style

Richer palettes than 8-bit. Dither/gradient cues. Still texel-disciplined.


---

## ◆ vector-style  _(source: arjun988)_

> Vector-clean art direction for Blender with flat fills, sharp silhouettes, and UI-like graphic clarity.

## Vector Style

Flat fills. Clean edges. Iconic shapes. Almost no gradients unless intentional.


---

## ◆ minimalist-style  _(source: arjun988)_

> Minimalist and abstract-leaning art direction for Blender with reduced forms, limited palettes, and negative space.

## Minimalist Style

Reduce until it breaks — then add one thing back.

### Tenets
1. Few shapes
2. Few colors
3. Negative space intentional
4. Typography-like clarity of form
5. Abstract OK if brief asks


---

## ◆ noir-style  _(source: arjun988)_

> Noir art direction for Blender with high-contrast lighting, wet streets, silhouettes, and monochrome or limited-color grading.

## Noir Style

Shadows as design. Silhouettes. Wet ground mirrors. Limited color or mono.

### Tenets
1. Motivated hard keys / blinds / neon slash
2. Negative fill
3. Smoke/fog shafts
4. Costume readable in silhouette
5. Grade crushed but detailed shadows


---

## ◆ stop-motion-craft-style  _(source: arjun988)_

> Stop-motion and craft aesthetics for Blender including claymation, paper craft, and handmade physical-material cues.

## Stop Motion / Craft Style

Handmade physicality. Imperfect edges. Material honesty.

### Sublooks
Claymation, paper craft, felt/plush, wooden puppet

### Tenets
1. Visible craft seams / fingerprints (subtle)
2. Real-world craft materials
3. Slight irregularity in forms
4. Practical light feel
5. Step-like motion if animating (optional)


---

## ◆ frutiger-aero-style  _(source: arjun988)_

> Frutiger Aero art direction for Blender with glossy skeuomorphism, aqua UI cues, nature-tech optimism, and mid-2000s futurism.

## Frutiger Aero

Glossy bubbles. Fresh greens/blues. Nature + tech optimism. Soft skeuomorphic forms.


---

## ◆ visual-console-eras  _(source: arjun988)_

> Visual era art direction for Blender covering PS1–PS5 stylistic cues, retro arcade, DOS, CRT, VHS, and film-grain presentation.

## Visual Console / Media Eras

Match era constraints: polycount, texture filtering, lighting model, and post stack.
