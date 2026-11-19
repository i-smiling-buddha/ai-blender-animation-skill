# Rendering & compositing

> Fused guide. Script paths like `scripts/x.py` are relative to the **ultimate-blender skill root**; all Python helpers live in one flat `scripts/` folder (shared `_bpyx.py`). Node helpers are in `scripts/node/`. Where two sources disagree, prefer the Blender 5.x rules in SKILL.md.

Sections: `blender-rendering`, `rendering`, `compositing`


---

## ◆ blender-rendering  _(source: el4cteo)_

> Render with Blender 5.3 Cycles/EEVEE/Workbench - quality presets, GPU setup, adaptive sampling, denoising, light paths, color management (AgX, Khronos PBR Neutral, ACES), PNG/EXR/MP4 output, passes, the 5.0 compositor API, CLI and multi-camera batch rendering. Use for any still, animation or turntable render.

## Rendering

The execution model is in `blender-core` (→ SKILL.md). Scene lighting and cameras are in `blender-lighting-lookdev` (→ guides/13-lighting-camera-lookdev.md).

### One call
```
scripts/render_batch.py -- --engine CYCLES --preset final --res 1920 1080 --out //render/hero_#### --frames 1
scripts/render_batch.py -- --preset preview --frames 1-120 --format MP4 --out //render/turntable
scripts/render_batch.py -- --cameras CamA CamB CamC --format EXR_MULTI --out //render/shots/
```
Presets: `preview` (Cycles 64 spp, threshold 0.05, 50% res; EEVEE 16), `final` (512 spp, 0.01; EEVEE 128 + raytracing), `product` (1024 spp, transparent background). GPU is picked automatically (OptiX > CUDA > HIP > Metal > oneAPI), and the denoiser matches (OptiX or OpenImageDenoise).

### Engine choice
| Engine | Use | Notes |
|---|---|---|
| Cycles | final quality, product, archviz, glass/SSS/caustics, baking | path tracer; set the GPU; adaptive sampling + denoise |
| EEVEE (5.x, ex-"Next") | fast look-dev, stylized, motion graphics, previews | ray-traced reflections/GI (`use_raytracing`), virtual shadow maps; needs a GPU even headless |
| Workbench | playblasts, clay/matcap reviews, QA sheets | instant, no lighting accuracy |
Engine ids: `CYCLES`, `BLENDER_EEVEE`, `BLENDER_WORKBENCH`.

### Cycles quality levers (ordered by impact)
1. **Adaptive sampling** (`adaptive_threshold` 0.01 final / 0.05 preview) + **denoise** (OIDN with albedo+normal passes, `denoising_input_passes="RGB_ALBEDO_NORMAL"`). Raising samples alone is the least efficient fix.
2. **Light paths**: interiors need diffuse bounces ≥ 4. Product shots: total 12, glossy 4, transmission 8–12 for glass. Clamp indirect 5–10 kills fireflies at a small energy cost.
3. **Light tree** (`use_light_tree`, on) for many lights. **Path guiding** (CPU only) for difficult indirect light.
4. Fewer, larger lights beat many small ones. Emissive meshes are noisier than area lights.
5. Persistent data (`render.use_persistent_data`) speeds up animations and turntables. Use `simplify` (max subdivision, texture limit) for previews.
6. 5.2: **texture cache** (`render.use_texture_cache`, `use_auto_generate_texture_cache`) cuts memory in texture-heavy scenes by generating `.tx` mip tiles.

### Color management (decide once per project)
- **AgX** (default): photographic, handles bright highlights. Looks: `AgX - Punchy`, `- Base Contrast`...
- **Khronos PBR Neutral**: shows albedo faithfully. Use it for product/e-commerce and asset reviews, and to match three.js `NeutralToneMapping`.
- **Standard**: graphics/UI/texture output that must match pixel values.
- **ACES 1.3 / 2.0**: VFX pipelines (plates, other DCCs).
- Use exposure (`view_settings.exposure`), not light power, for global brightness tweaks. Display device sRGB, or Display P3 / Rec.2100 for HDR delivery.

### Output formats
- Stills: PNG 8/16-bit (RGBA when the film is transparent) or JPEG for web previews.
- Comp/VFX: **EXR multilayer** (`EXR_MULTI`, DWAA 16-bit) with passes (Denoising Data, Cryptomatte, AO, Mist, Z). 5.0 renamed passes: `Diffuse Color`, `Depth`, etc.
- Video: render **frames first** (PNG/EXR), then encode (FFmpeg or the VSE), because a crash mid-MP4 loses everything. Direct MP4 is fine for previews. Set `image_settings.media_type` **before** `file_format` (5.0+).
- Transparent: `film_transparent=True` + PNG/EXR. A glass-only alpha needs `film_transparent_glass`.

### Compositor (5.0+ API)
```python
ng = bpy.data.node_groups.new("Comp", "CompositorNodeTree"); scene.compositing_node_group = ng
ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
rl, glare, out = ng.nodes.new("CompositorNodeRLayers"), ng.nodes.new("CompositorNodeGlare"), ng.nodes.new("NodeGroupOutput")
ng.links.new(rl.outputs["Image"], glare.inputs["Image"]); ng.links.new(glare.outputs["Image"], out.inputs[0])
```
There's no Composite node anymore: the group output is the final image. Many node options are now **input sockets** (Glare `Type`, `Threshold`, `Strength`), so `--describe` them with `scripts/gn_builder.py`. File Output node: `directory`, `file_name`, `file_output_items`.
5.3: the compositor is an **effects stack** (`scene.compositor_effects`, each with its own `node_group`, `enable_for_render`/`enable_for_preview`). `scene.compositing_node_group` still gets/sets the active effect's group. The Essentials **Bloom** node group restores the old EEVEE bloom.

### CLI rendering (render farms, CI)
- `blender -b scene.blend -E CYCLES -o //out/frame_#### -F PNG -s 1 -e 120 -a` renders an animation. `-f 10` renders a single frame. Python args go after `--`.
- `-- --cycles-device OPTIX` (or CUDA/HIP/METAL/ONEAPI) selects the device without Python.
- Split frames across machines with `-s/-e`, or with Placeholders + No Overwrite (`render.use_placeholder`, `use_overwrite=False`) on shared storage.

### Gotchas
- `scene.render.engine` enum under-reports (add-on engines). Assign in try/except (the script does).
- EEVEE in background still needs a GPU context. In CI without a GPU, use Cycles CPU or Workbench.
- `bpy.ops.render.render(write_still=True)` writes `render.filepath`. Without `write_still`, the result only lives in `Render Result`.
- Noise in glass/caustics: enable caustics only if needed (`caustics_refractive`), raise transmission bounces, or fake it with Thin Wall (5.2) for windows.
- Fireflies: clamp indirect, a filter glossy / blur glossy (`blur_glossy` 0.5–1), and bigger light sources.


---

## ◆ rendering  _(source: arjun988)_

> Blender rendering with Cycles and Eevee including sampling, denoising, camera setup, render passes, color management, and render optimization. Use for final output and look validation via MCP.

## Rendering

Appropriate engine selection. Optimized settings. Production render passes.

### When to Use

- Final portfolio/cinematic renders
- Look development validation
- Render pass output for compositing
- Game asset preview renders (Turntable)
- Style validation (realistic vs stylized)

### Engine Selection

| Engine | Use When |
|--------|----------|
| Cycles | Final quality, realistic, portfolio |
| Eevee | Real-time preview, stylized, game look dev |
| Eevee Next | Improved real-time quality (Blender 4+) |

### Workflow

```
Camera Setup → Render Settings → Sample Tests → Full Render
    → Pass Output → Color Management → Delivery
```

### Camera Setup

Naming: `CAM_[Shot]_[Number]`
- Focal length: 35mm (environment), 85mm (hero detail), 24mm (wide horror)
- Depth of field: subject distance focused
- Composition: rule of thirds; leading lines
- Turntable: empty parent rotating 360° for asset preview

### Cycles Settings

| Setting | Preview | Production |
|---------|---------|------------|
| Samples | 64–128 | 512–2048 |
| Denoise | OpenImageDenoise | OpenImageDenoise |
| Max bounces | 8 | 12 |
| Caustics | Off (default) | On if glass/water hero |

### Eevee Settings

| Setting | Value |
|---------|-------|
| Screen Space Reflections | On for metals |
| Ambient Occlusion | On |
| Bloom | Stylized/ emissive scenes |
| Shadow resolution | 2048+ |
| Contact Shadows | Ground contact |

### Render Passes

| Pass | Use |
|------|-----|
| Combined | Final composite |
| Diffuse Direct/Indirect | Relighting |
| Glossy | Reflection control |
| Normal | Compositing effects |
| AO | Contact shadow enhancement |
| Z (Depth) | DOF, fog in comp |
| Cryptomatte | Object masking |
| Emission | Screen glow effects |

### Color Management

```
View Transform: AgX (Blender 4+) or Filmic
Look: Medium Contrast (default) or High Contrast (dramatic)
Exposure: Adjust in compositor, not by blowing lights
```

### Render Optimization

- Use render region for test crops
- Adaptive sampling (Cycles)
- Disable unseen objects in render layers
- GPU rendering default when available
- Persistent data for animation sequences

### Asset Turntable Template

```
1. CAM_Turntable at 3/4 height, 45° angle
2. Empty at asset origin → rotate animation 0–360° (120 frames)
3. 3-point lighting rig
4. Render 1280×1280 or project-specified resolution
5. Output PNG sequence or MP4
```

### Reference Image Validation

When matching a photo/concept (`../refs/shared/reference-image-match.md`):

| Setting | Reference match |
|---------|-----------------|
| Hero camera | Match reference angle before grading |
| AgX Look | Base Contrast default; High Contrast if reference is punchy |
| Exposure | 0.15–0.45 typical; hull must read, not clip white |
| Preview playback | EEVEE, motion blur off, `taa_samples` 1–8 |
| Final still | Render at hero `CAM_*` — compare to reference |
| Compare tool | `get_viewport_screenshot` or bpy render still |

Run `../refs/shared/visual-match-checklist.md` before delivery.

### MCP Integration

1. Configure render engine settings via MCP
2. Setup camera via MCP
3. Trigger test render via MCP if supported
4. Query render settings validation
5. Set output paths via MCP

### Constraints

#### MUST DO
- Match render engine to project style
- **Screenshot or render compare** when reference image was provided
- Use denoising for Cycles production renders
- Setup color management before final render
- Render validation turntable for hero assets
- Organize cameras in `COL_Cameras`

#### MUST NOT DO
- Production render without sample test
- Ignore color management (sRGB vs Linear)
- Render at excessive resolution without purpose
- Skip render passes when compositing planned
- Use Cycles for real-time game preview needs

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Pass compositing | `../refs/rendering/render-passes.md` | Multi-pass output |
| NPR/stylized render | `../refs/rendering/npr-rendering.md` | Stylized-style projects |
| Reference image match | `../refs/shared/reference-image-match.md` | Photo/concept attached |
| Visual match validation | `../refs/shared/visual-match-checklist.md` | Before delivery |


---

## ◆ compositing  _(source: arjun988)_

> Blender compositor workflows for beauty stacks, render passes, color grade, glare, and delivery outputs via MCP.

## Compositing

Pass-aware beauty stack. Subtle grade. Delivery-ready outputs.

### When to Use

- Final beauty composites from Cycles/Eevee
- Grade, glare, vignette, chromatic subtlety
- Pass recombination (diffuse, glossy, volume, cryptomatte)
- Shot delivery plates

### Workflow

```
Enable passes → Render multilayer EXR (or needed passes)
  → Compositor graph → Grade → FX (glare/fog glow)
  → Output viewer + File Output → Validate exposure
```

### Recommended Passes

| Pass | Use |
|------|-----|
| Beauty / Combined | Base |
| DiffCol / DiffDir / DiffInd | Relight flexibility |
| GlossDir / GlossCol | Spec control |
| Volume | Smoke/fire isolation |
| Cryptomatte Object/Material | Isolations |
| Mist | Depth grade / fog |

### Beauty Stack (Default)

```
Combined
  → Exposure / Color Balance (AgX-aware)
  → Glare (fog glow / streaks sparingly)
  → Lens distortion (subtle)
  → Vignette (subtle)
  → Output
```

### Grade Rules

1. Fix exposure before creative grade
2. Prefer lift/gamma/gain or color balance over crushed curves
3. Keep skin/product hues plausible
4. Match reference stills with side-by-side

### Outputs

- `OUT_Beauty_[Shot]`
- Optional: `OUT_Alpha`, `OUT_CryptoID`
- Prefer EXR for archival; PNG/JPEG for review

### Constraints

#### MUST DO
- Grade on view transform–aware pipeline (AgX)
- Keep creative FX reversible in node graph
- Document exposure/look settings

#### MUST NOT DO
- Crush blacks to hide lighting problems
- Over-glare every bright pixel
- Flatten multilayer to JPEG as only archive

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Pass Stack | `../refs/compositing/pass-stack.md` | When needed |
| Grade Presets | `../refs/compositing/grade-presets.md` | When needed |
| Delivery Outputs | `../refs/compositing/delivery-outputs.md` | When needed |
