# Lighting, camera, look-dev & time of day

> Fused guide. Script paths like `scripts/x.py` are relative to the **ultimate-blender skill root**; all Python helpers live in one flat `scripts/` folder (shared `_bpyx.py`). Node helpers are in `scripts/node/`. Where two sources disagree, prefer the Blender 5.x rules in SKILL.md.

Sections: `blender-lighting-lookdev`, `lighting`, `lookdev`, `camera-cinematography`, `blender-time-of-day`


---

## ◆ blender-lighting-lookdev  _(source: el4cteo)_

> Lighting, cameras and look-dev in Blender 5.3 - studio 3-point and product lighting, HDRI environments, sun/sky exteriors, interiors, light linking, physically based light units, camera focal lengths/composition/DOF, cyclorama backdrops, looping turntables for asset presentation. Use when presenting assets, setting up scenes for rendering, or judging materials under consistent light.

## Lighting & Look-dev

The execution model is in `blender-core` (→ SKILL.md). Render settings are in `blender-rendering` (→ guides/14-rendering-compositing.md). Full time-of-day, night and fog environments are in `blender-time-of-day` (→ guides/13-lighting-camera-lookdev.md).

### One call: presentation scene
```
scripts/turntable.py -- --objects Hero --rig studio --backdrop --frames 120 --lens 85
scripts/turntable.py -- --objects Hero --rig both --hdri //hdri/studio_small_09_2k.exr --hdri-strength 0.8
```
This builds a camera framed to the bounding sphere (on the narrower frame axis), a key/fill/rim area-light rig scaled to the asset, an optional 18%-grey cyclorama, and a pivot that orbits camera + lights + backdrop in a seamless loop. **The asset itself isn't modified.** Everything lives in the `LD_Lookdev` collection, and re-running replaces it. Set the render resolution **before** running, because framing depends on the aspect ratio.

### Lighting recipes
| Situation | Setup |
|---|---|
| Asset / product review | 3-point: key 45° side, 30–40° up; fill opposite at ⅓ power and lower; rim behind for silhouette. Large soft area lights (size ≈ object), neutral grey backdrop, Khronos PBR Neutral view |
| Reflective product (metal, glass, car paint) | large softboxes/strip lights *reflected* in the surface, plus a black/white gradient environment. Shape the reflections, not the illumination |
| Exterior day | Sun light (angle 0.5° for sharp, 2–5° for softer) + sky (`ShaderNodeTexSky`, `sky_type` `MULTIPLE_SCATTERING`/`SINGLE_SCATTERING`; 5.x replaced "Nishita"; `PREETHAM`/`HOSEK_WILKIE` legacy) with `sun_elevation`/`sun_rotation` matching the Sun light (5.3: `sun_disc` now emits light, so turn it off when a Sun lamp is the sun), or an HDRI of the matching time of day |
| Interior | HDRI/sky through the windows + portal area lights in the openings, bounces ≥ 4, then practical lights (lamps) at real wattage |
| Character / portrait | soft key from above-front, a reflector-like fill, rim or hair light, an eye catchlight. 85–135 mm lens |
| Stylized / game screenshot | match the engine: one directional + ambient/HDRI, no fancy GI, so it looks like it will in-game |
- **HDRI**: Poly Haven (CC0) via the blender-mcp `search_assets`/`import_asset`, or `ShaderNodeTexEnvironment` + Mapping (Z rotation aligns the sun). Strength 0.5–1.5. Clamp sun hotspots if they cause fireflies.
- **Light linking** (4.0+, Cycles + EEVEE): set `light_obj.light_linking.receiver_collection` / `blocker_collection` (on the light **object**) to light only what you choose, like a hero rim that doesn't touch the backdrop. Portals: `light.cycles.is_portal = True` on area lights in window openings.
- **Units**: point/spot/area in Watts (a 60 W bulb ≈ point light 40–60 W in Blender), sun in W/m² (irradiance; 1000 ≈ physical midday, but use 3–10 with AgX for natural results), emission strength ≈ W/m². Keep lights physically plausible and control the overall image with exposure.
- **Shadows**: light size controls softness. A bigger, closer light is softer. Contact shadows should exist where objects touch, so check that nothing floats (`blender-asset-qa` (→ guides/17-qa-review.md) `ground_z`).

### Camera rules
- Focal length: 24–35 mm environments/interiors (keep verticals straight: camera level, or shift instead of tilting), 50 mm natural, **85–135 mm products and portraits** (no distortion), 200 mm+ compressed telephoto.
- Composition: rule of thirds / centered symmetric for products, horizon off-center, leading lines, headroom. Show the silhouette (3/4 view at slight elevation 10–25°).
- DOF (`cam.data.dof.use_dof`, `focus_object`, `aperture_fstop`): f/2.8–5.6 for products at real scale. DOF depends on scale, so a wrong scene scale ruins it.
- Clip start/end tight around the subject (the script does this), which avoids precision artifacts.
- Sensor fit AUTO uses the larger axis. Portrait renders need framing on the width.

### Look-dev procedure (material approval)
1. Neutral setup: `--rig studio` or a neutral HDRI, grey backdrop, Khronos PBR Neutral or AgX (pick one and keep it).
2. Add a calibration chart object if needed (a grey 18% sphere, a chrome sphere, a Macbeth chart) next to the asset.
3. Turntable at 24–30 fps, 120–240 frames, 85 mm. Render previews with `render_batch.py --preset preview --format MP4`.
4. Check the materials under 2–3 different HDRIs. A good PBR material holds up in all of them (`blender-pbr-materials` (→ guides/08-materials-texturing-baking.md) sanity checks).

### Gotchas
- World lighting is invisible if `world.node_tree` has no Background → World Output link (the script ensures one).
- EEVEE needs `use_raytracing` for good reflections. Light probes (Volume/Sphere/Plane) still help static GI in interiors.
- Area lights that are too small and bright make fireflies in Cycles. Increase the size, decrease the power.
- A turntable that rotates the **asset** changes its transforms and animation data, which is why this rig orbits the camera instead.


---

## ◆ lighting  _(source: arjun988)_

> Cinematic and game lighting in Blender including three-point lighting, HDRI, horror lighting, volumetrics, rim lighting, and mood-driven illumination. Use for look development and scene atmosphere via MCP.

## Lighting Artist

Mood-driven illumination. Guide player attention. Support art direction.

### When to Use

- Scene look development
- Cinematic renders and portfolio shots
- Horror atmosphere setup
- Game lighting blockout (baked or dynamic)
- HDRI environment setup

### Workflow

```
Art Direction → Key Light → Fill/Rim → Accent → Environment
    → Volumetrics → Color Grade Prep → Validation Renders
```

### Three-Point Lighting

| Light | Purpose | Typical Setup |
|-------|---------|---------------|
| Key | Primary illumination | 45° above, 30° side |
| Fill | Shadow softening | Opposite key, 1/2–1/4 intensity |
| Rim | Subject separation | Behind subject, bright edge |

Naming: `LGT_Key_Main`, `LGT_Fill_Soft`, `LGT_Rim_Back`

### Light Types

| Type | Use Case |
|------|----------|
| Sun | Outdoor directional |
| Area | Soft studio, windows |
| Spot | Flashlights, stage, horror |
| Point | Bulbs, emissive fill |

### Color Temperature

| Mood | Kelvin | RGB Approx |
|------|--------|------------|
| Candle/warm | 1800K | Orange |
| Tungsten | 3200K | Warm white |
| Daylight | 5500K | Neutral white |
| Overcast | 6500K | Cool white |
| Moonlight | 8000K+ | Blue |

Horror: mix warm interior tungsten with cold exterior moonlight.

### HDRI Workflow

```
1. Select HDRI matching mood (overcast for horror, clear for hero)
2. Rotate to place brightest area as key
3. Adjust strength (0.5–2.0 typical)
4. Supplement with area lights for subject separation
5. Hide HDRI in background if using solid color/fog
```

### Horror Lighting

See horror-style skill. Key techniques:
- High contrast; deep shadows
- Single source motivation (one visible lamp)
- Flicker via noise modifier on strength
- Volumetric fog for light shafts
- Avoid flat even illumination

### Volumetrics

```
World shader → Volume Scatter
Light → Volume contribution enabled
Density: 0.01–0.1 (subtle to heavy fog)
Anisotropy: 0.3–0.8 for visible light shafts
```

### Game vs Cinematic

| Aspect | Game | Cinematic |
|--------|------|-----------|
| Light count | Minimal (performance) | Unlimited |
| Baked | Lightmaps common | Path trace |
| Dynamic | Real-time shadows | Ray traced |
| Mood | Gameplay readability | Artistic freedom |

### MCP Integration

1. Create lights with naming convention via MCP
2. Set color, intensity, angle via MCP
3. Configure world HDRI via MCP
4. Query light count and types
5. Organize in `COL_Lights` collection

### Constraints

#### MUST DO
- Motivate every light source (visible fixture or logical source)
- Name lights `LGT_[Role]_[Descriptor]`
- Test readability of gameplay-critical areas
- Match lighting to style skill (horror, realistic, etc.)
- Separate lighting collections from geometry

#### MUST NOT DO
- Flat ambient without direction
- Over-light horror scenes
- Ignore color temperature consistency
- Place lights without purpose
- Skip volumetric consideration for mood scenes

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Horror setups | `../refs/lighting/horror-lighting-setups.md` | Horror scenes |
| Cinematic rigs | `../refs/lighting/cinematic-light-rigs.md` | Portfolio renders |


---

## ◆ lookdev  _(source: arjun988)_

> Look development loop for Blender assets combining materials, lighting, camera, and screenshot comparison until shading reads correctly via MCP.

## Lookdev

Material + light + camera loop. Screenshot compare. Stop when it reads.

### When to Use

- Finalizing asset shading before export/portfolio
- Turntable / grey shader checks
- Matching material references
- Bridging `materials` (→ guides/08-materials-texturing-baking.md) and `lighting` (→ guides/13-lighting-camera-lookdev.md) intentionally

### Workflow

```
Clay/grey pass → Base materials → Neutral light rig
  → Beauty light → Screenshot → Gap list → Iterate (≤3–5)
  → Optional grade → QA
```

### Standard Rigs

| Rig | Use |
|-----|-----|
| Neutral 3-point | Evaluate materials fairly |
| HDRI studio | Product / character |
| In-situ scene lights | Final context |

Keep a reusable `COL_Lookdev_Lights` + `CAM_Lookdev_*`.

### Checklist

- [ ] Values read in grayscale
- [ ] Specular roughness believable
- [ ] Edges catch light (bevels/normals)
- [ ] Emissive under control
- [ ] No pure black / pure white traps unless stylized
- [ ] Matches reference palette if provided

### Iteration Rule

Each pass: change one major variable (material OR light OR camera), then screenshot.

### Constraints

#### MUST DO
- Grey pass before fancy textures when forms unsure
- Capture screenshots each iteration
- Hand off to `qa-review` (→ guides/17-qa-review.md) before ship

#### MUST NOT DO
- Fix modeling problems only with roughness maps
- Infinite tweak loops without gap list

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Lookdev Rig | `../refs/lookdev/lookdev-rig.md` | When needed |
| Lookdev Checklist | `../refs/lookdev/lookdev-checklist.md` | When needed |


---

## ◆ camera-cinematography  _(source: arjun988)_

> Cinematic camera work in Blender including framing, lenses, composition, camera animation, and shot language beyond basic rendering setup via MCP.

## Camera Cinematography

Intentional framing. Lens language. Motivated camera moves. Shot-ready cameras.

### When to Use

- Cinematic stills and turntables with purpose
- Animated camera moves (dolly, crane, orbit, handheld)
- Matching reference camera / lens feel
- Shot layout for lookdev and portfolio

### Workflow

```
Shot intent → Camera + target empty → Lens/FOV → Composition
  → Focus/DoF → Move (if animated) → Viewport check → Render/comp
```

### Naming

- `CAM_[Shot]_[Angle]`
- `EMPTY_CamTarget_[Shot]`
- Collection: `COL_Cameras`

### Lens Guide

| Feel | Focal (FF equiv) | Notes |
|------|------------------|-------|
| Wide establishing | 18–28mm | Distortion; watch edges |
| Story / product | 35–50mm | Natural |
| Portrait / hero | 85–135mm | Compression |
| Tele drama | 150mm+ | Flat space |

Sensor fit and resolution affect FOV — set camera sensor intentionally.

### Composition Checklist

- [ ] Subject readable in silhouette
- [ ] Headroom / lead room intentional
- [ ] Horizon level (unless motivated)
- [ ] Foreground / mid / background depth
- [ ] Avoid tangent mergers on edges

### Camera Animation

| Move | Use |
|------|-----|
| Orbit | Product / character showcase |
| Dolly in | Reveal / tension |
| Crane | Scale / establishing |
| Handheld noise | Documentary / horror unease |
| Locked off | Archviz / product purity |

Animate camera + target empties; prefer slow ease-in/out.

### DoF

- Focus on primary subject empty
- F-stop for style: shallow for hero, deeper for environments
- Preview in Eevee; final in Cycles if needed

### Constraints

#### MUST DO
- Name cameras and targets
- Match aspect ratio to delivery
- Check framing at start, mid, end of moves

#### MUST NOT DO
- Default 50mm for every shot without intent
- Animate FOV wildly unless motivated
- Crop critical silhouette out of frame

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Lens And Composition | `../refs/camera-cinematography/lens-and-composition.md` | When needed |
| Camera Move Library | `../refs/camera-cinematography/camera-move-library.md` | When needed |
| Dof Guide | `../refs/camera-cinematography/dof-guide.md` | When needed |


---

## ◆ blender-time-of-day  _(source: el4cteo)_

> Time of day and atmosphere in Blender 5.3 - measured sky + sun for dawn, morning, noon, golden hour, sunset, blue hour, overcast, night/moonlight with stars and city glow, exposure balance, height fog from visibility, god rays, Cycles vs EEVEE volumes, compositor grade, stylized moods (cyberpunk neon, horror, underwater, desert). Use for any day/night, sunset, foggy or mood lighting scene.

## Time of Day & Atmosphere

The execution model is in `blender-core` (→ SKILL.md). Studio and product lighting are in `blender-lighting-lookdev` (→ guides/13-lighting-camera-lookdev.md), render settings in `blender-rendering` (→ guides/14-rendering-compositing.md), and rain, snow, wetness and lightning in `blender-weather-fx` (→ guides/12-simulation-vfx-weather.md).

### One call
```
scripts/scene_mood.py -- --time golden                       # sun 6 deg, warm, long shadows
scripts/scene_mood.py -- --time night --fog-visibility 250   # moonlight + stars + haze
scripts/scene_mood.py -- --time noon --overcast 0.8          # soft grey day
scripts/scene_mood.py -- --mood cyberpunk                    # moonless, neon rim pair, fog, bloom
scripts/scene_mood.py -- --time morning --fog-visibility 120 --fog-height 4   # valley fog
```
Times: `noon morning afternoon golden sunrise sunset blue_hour night moonless`. Moods: `cyberpunk horror underwater desert` (each sets defaults that explicit flags override). Override the sun with `--elevation DEG` (negative = below the horizon) and `--heading DEG` (0 = +Y, 90 = +X). If you leave out `--heading`, the sun sits 135° from the camera's view direction, which gives side/back light that shows form. Front light looks flat.

The script builds `ENV_World`, the `ENV_Mood` collection (sun or moon, fog box, accent lights) and, for moods, `ENV_Grade` (a compositor tree). Your objects are untouched, and re-running replaces everything it made. It returns the key light's strength, color and elevation, the exposure, and any warnings.

### How it stays physically right
- **Sky**: `ShaderNodeTexSky` `MULTIPLE_SCATTERING` (5.0+; `SINGLE_SCATTERING` is the legacy "Nishita") with `sun_disc=False` (5.3: an enabled sun disc also **lights** the scene, adding a second sun on top of the lamp). A **Sun lamp** is the sun, because it gives sharp shadows in both engines. The lamp's color and its strength relative to the sky come from a table **measured from Blender 5.2's own sky model** (re-checked on 5.3: within 0.1%) at each elevation (sunset sun ≈ `[1.0, 0.22, 0]`, noon ≈ `[1.0, 0.86, 0.68]`). That keeps the sky and the sun consistent.
- **Scale**: noon gives a sun of ≈ 4 W/m² with a grey card at 0.18 under AgX at exposure 0.
- **Exposure balance**: each preset meters a grey card between the ground and a wall facing the sun, then scales the *environment* lights so the card lands at the preset's brightness (noon 1.0, golden 0.85, sunset 0.7, blue hour 0.35, night 0.2, moonless 0.1). Your practical lights keep their usual wattage and read correctly against it.
- **Physical alternative**: `--use-exposure` puts the difference in `view_settings.exposure` instead. The result returns `practical_scale`: multiply your lamp wattages by it to keep the same look.
- **Night**: the moon is a Sun lamp at 0.3 W/m² before scaling (35°, cool `[0.72, 0.82, 1.0]`; moonlight is physically ~4100 K, and it reads blue because of the Purkinje shift). The night dome is a zenith gradient, a city glow at the horizon (sodium orange; magenta for cyberpunk), and stars visible to camera rays only.
- **Fog**: a box volume around the scene and the camera. Density = **3.912 / visibility** (Koschmieder: visibility in meters → extinction per meter). Add `--fog-height` for an exponential ground fog. Exposure compensates for light lost in fog by up to 4 EV, so fog stays dense instead of just dark. The background seen by the camera is blended toward the fog color.

### Fog and volumetrics
| Look | `--fog-visibility` (m) |
|---|---|
| Clear air / distant haze | 5000–20000 |
| Haze, desert dust | 1000–3000 |
| Mist | 500–1000 |
| Fog | 100–500 |
| Dense fog, horror | 20–60 |
| Underwater (clear → murky) | 30 → 8 |
- **God rays** need four things: a strong key (sun/spot), occluders (windows, trees, a gobo), forward scattering (`--fog-anisotropy 0.6–0.85`), and EEVEE `use_volumetric_shadows` (the script turns it on).
- **Cycles 5.x** renders volumes with **null scattering** by default (unbiased, no step size). `scene.cycles.volume_biased=True` brings back ray marching (`volume_step_rate`). Height fog is a heterogeneous volume and is noisier, so give it more samples or denoise.
- **EEVEE** volumes are froxels: `volumetric_tile_size` 4 → 2 for detail, and `volumetric_end` must cover the fog (the script sets it). Very dense fog close to the camera bands, so prefer Cycles for it.
- Cheap distant haze without volumes: the Mist pass (`view_layer.use_pass_mist`, `world.mist_settings.start/depth`) mixed in the compositor.
- Deeper detail is in [../refs/blender-time-of-day/fog-volumetrics.md](../refs/blender-time-of-day/fog-volumetrics.md).

### Rules
- Decide the light direction first (side/back), then the time. Low sun (golden, sunset) = long shadows and warm key against a cool sky fill, which is the most flattering combination.
- Night is not "a blue tint": keep **contrast** (hard moon shadows, pools of warm practicals, dark silhouettes), lower saturation, and add practical sources. See [../refs/blender-time-of-day/night-and-moods.md](../refs/blender-time-of-day/night-and-moods.md).
- Practicals use real color temperatures (`light.use_temperature=True`, `light.temperature`): sodium 2000 K, tungsten 2700 K, warm LED 3000 K, neutral LED 4000 K, neon as emissive tubes. Watts and conversions are in [../refs/blender-time-of-day/light-values.md](../refs/blender-time-of-day/light-values.md).
- Keep the view transform AgX (the script sets it, along with a mood look like `AgX - Punchy`). `--keep-view` preserves yours.
- Verify every mood with a render, not the viewport: fog, stars and bloom only show in rendered output. Use `blender-rendering` (→ guides/14-rendering-compositing.md) `render_batch.py --preset preview`.

### Gotchas
- Below the horizon the sky texture shows a dark "ground". Extend the ground plane or terrain to the horizon, or keep the horizon out of frame.
- The bloom/glare threshold is **scene-linear, before** the view exposure. With `--use-exposure` the script scales the threshold for you.
- The script won't overwrite a compositor tree that isn't `ENV_Grade`; it reports that instead.
- `SunLight.use_nodes` and light node trees are deprecated in 5.x (removal planned for 6.0). Use light color and `temperature` instead.
- The sky texture's `sun_direction` only applies to the legacy Preetham/Hosek models. `sun_rotation` 0 places the sun toward +Y and 90° toward +X (measured).
- Changing the render engine doesn't need a re-run. The script sets both the EEVEE and Cycles volume settings.
