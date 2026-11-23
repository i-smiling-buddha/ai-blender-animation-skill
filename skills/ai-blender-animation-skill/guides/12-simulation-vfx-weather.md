# Simulation, VFX & weather

> Fused guide. Script paths like `scripts/x.py` are relative to the **ai-blender-animation-skill skill root**; all Python helpers live in one flat `scripts/` folder (shared `_bpyx.py`). Node helpers are in `scripts/node/`. Where two sources disagree, prefer the Blender 5.x rules in SKILL.md.

Sections: `blender-simulation`, `physics-sim`, `cloth-sim`, `vfx-fx`, `blender-weather-fx`


---

## ◆ blender-simulation  _(source: el4cteo)_

> Physics in Blender 5.3 - rigid bodies (density mass, shapes, bake to keys), classic cloth presets and pinning, new node-based Cloth/Hair Dynamics (XPBD, Collider, effectors), Mantaflow fluids, hair curves, GN simulation zones, headless baking. Use for destruction, drapes, flags, falling objects, liquids, smoke, hair motion.

## Simulation

The execution model is in `blender-core` (→ SKILL.md). Procedural sim zones are in `blender-geometry-nodes` (→ guides/09-geometry-nodes.md).

### One call
```
scripts/sim_setup.py -- --rigid --active Crate1 Crate2 --passive Floor --density 500 --frames 1 120 --bake --to-keys
scripts/sim_setup.py -- --cloth Flag --preset cotton --pin Pin --colliders Pole --bake
scripts/sim_setup.py -- --gn-cloth Sheet --colliders Table --set Bendiness=0.5 Stretchiness=0.1 --bake
```
`--bake` steps through every frame in order (this works headless for point caches **and** GN simulation zones) and reports final positions and `min_z`, so you can verify contact. `--to-keys` turns rigid-body motion into keyframes for engines.

### Choose the solver
| Need | Use |
|---|---|
| Falling/stacking/destruction | Rigid Body (Bullet). Pre-fracture with Cell Fracture (extension) or GN Voronoi |
| Clothing, flags, drapes (production-proven) | Classic **Cloth** modifier + Collision modifiers |
| New node-based cloth/hair, custom forces, procedural setups | **Cloth Dynamics (Experimental)** / **Hair Dynamics** assets (5.2, XPBD) |
| Liquids, smoke, fire | Mantaflow fluid domain + flow/effector (`fluid.bake_all`) |
| Hair grooms | Curves objects + hair node assets (`procedural_hair_node_assets`), Hair Dynamics for motion |
| Growth, trails, custom per-frame logic | GN Simulation zone |
| Soft jiggle for games | bones with spring/jiggle in-engine, or Wiggle-style constraints baked to keys |

### Rigid bodies
- Real scale and real mass matter: mass = volume × density (wood 500–700, concrete 2400, steel 7850, plastic 950 kg/m³). The script computes it.
- Collision shape: `CONVEX_HULL` for dynamic objects (fast, stable), `MESH` only for **passive** concave colliders, and primitives (`BOX`, `SPHERE`, `CAPSULE`) when they fit.
- Stability: substeps 10 and iterations 10 (set by the script). Use a small collision margin (1 mm). Avoid objects starting interpenetrated.
- Export: bake to keyframes (`--to-keys`; the built-in `rigidbody.bake_to_keyframes` needs a UI, so the script samples `matrix_world` itself), then export the actions (`blender-export-pipelines` (→ guides/16-export-engines.md)).

### Classic cloth
- Presets (from Blender's): cotton, denim, leather, rubber, silk. The mesh needs even quad density (2–5 cm edges for clothing). Use a subdivided plane or retopologized garment, never ngons.
- **Pinning**: vertex group with weight 1 = pinned (`settings.vertex_group_mass`). Animate pinned verts with hooks/armature.
- Collisions: colliders get a `COLLISION` modifier (thickness 1–5 mm), plus self-collision for folds. Raise `quality` (steps) for fast motion.
- Apply cloth as a shape (`modifier_apply_as_shapekey`) or bake to an Alembic/point cache for render. Games: bake to bones, or apply a static drape.

### Node-based dynamics (5.2, experimental)
- Assets live in `datafiles/assets/nodes/geometry_nodes_dynamics_assets.blend`: `Cloth Dynamics (Experimental)`, `Hair Dynamics`, `Collider`, `Set Effector`, `Custom Force`, `Custom Effector`. The script appends them.
- Cloth inputs include `Pin Group` (attribute), `Stretchiness`, `Bendiness`, `Substeps` (5), `Constraint Steps` (15), `Mass`, `Friction`, `Collision Radius`, `Linear Damping`, `Gravity`, `Tearing` (+ mode/threshold), `Effectors Collection`, `Effectors` (bundle).
- Colliders: put a `Collider` modifier on each collider object and add those objects to the collection fed into `Effectors Collection` (the script does both).
- Hair: Add → Empty Hair sets up the surface + `Capture Rest Geometry`. Hair Dynamics reads the rest/deformed surface through geometry bundles.
- Limits (5.2): no self-collision yet, no built-in wind/turbulence (build a `Custom Force`). Interfaces may change, so pin the Blender version in production.
- The solver itself (`GeometryNodeXPBDSolver`) takes a `World` bundle, `Delta Time`, `Substeps`, `Constraint Iterations`. Building directly on it is advanced; start from the assets.

### Fluids (Mantaflow) quick setup
Domain object (`FLUID` modifier `fluid_type="DOMAIN"`, `domain_type="LIQUID"|"GAS"`), resolution 64 preview / 128–256 final, cache directory set and `cache_type="ALL"` for headless; flow objects `fluid_type="FLOW"` (`flow_type` LIQUID/SMOKE/FIRE, `flow_behavior` INFLOW/GEOMETRY); obstacles `EFFECTOR`. Bake with `bpy.ops.fluid.bake_all()` under a context override with the domain active. This is slow. Test at low resolution first.

### Rules
- Simulations are frame-rate and scale dependent. Set `scene.render.fps` and the scale before tuning.
- Always bake before rendering/exporting, and never rely on viewport playback order.
- GN simulation zones: bake per modifier (`mod.bakes`, `object.geometry_node_bake_single`), or step frames sequentially (script) in background.
- Point caches in background: stepping frames from `frame_start` fills the cache. `ptcache.bake_all(bake=True)` needs a valid context.
- Verify with `look(mode="frames")` plus the numbers (`min_z` ≈ the collider top = contact, no tunnelling).

### Gotchas
- Objects tunnelling through colliders: thin colliders, too few substeps, or too-fast motion. Thicken, raise substeps/quality, or use a bigger collision distance.
- Exploding cloth at frame 1: starting interpenetration or a zero-area face. Run `blender-asset-qa` (→ guides/17-qa-review.md), offset the start.
- Rigid body world cache ranges are separate from the scene range (the script syncs them).
- Changing anything (frame range, settings) invalidates caches. Re-bake.


---

## ◆ physics-sim  _(source: arjun988)_

> Rigid body, soft body, and destruction setups in Blender including constraints, cell fracture debris, and baked caches via MCP.

## Physics Sim

Stable rigid/soft body setups. Motivated destruction. Baked caches.

### When to Use

- Rigid body interactions and collapses
- Soft body jiggle / rubber / simple soft props
- Destruction and debris (cell fracture / pre-cut shards)
- Pre-vis physics before VFX polish

### Workflow

```
Simplify collision meshes → Assign rigid/soft bodies
  → Constraints → Passive settings → Bake → Art-direct → Export cache
```

### Rigid Body Quick Rules

| Role | Settings notes |
|------|----------------|
| Active | Moving debris / props |
| Passive | Floors, walls, heavy anchors |
| Convex hull | Fast, approximate |
| Mesh | Accurate, heavier |

- Apply scale before sim
- Use margin appropriate to scale
- Collection: `COL_Physics_[Shot]`

### Constraints

- Hinge / fixed / motor for mechanical links
- Breakable constraints for destruction beats
- Name: `RBCON_[Object]_[Type]`

### Destruction Approach

```
1. Pre-cut shards (cell fracture or manual)
2. Island meshes as active rigid bodies
3. Passive shell until trigger frame
4. Animate trigger (force / keyframed activation)
5. Bake → cleanup interpenetrations
```

### Soft Body

- Prefer for simple soft props; use `cloth-sim` (→ guides/12-simulation-vfx-weather.md) for garments
- Goal weights to retain shape
- Soft + collision object required

### Bake / Export

- Bake to cache before render
- Alembic/USD for cinematic debris
- For games: bake key poses or flipbook; rarely live Blender physics

### Constraints

#### MUST DO
- Apply scale; use simplified colliders
- Bake before final delivery
- Trigger destruction intentionally (frame)

#### MUST NOT DO
- High-res sculpt meshes as active colliders
- Unbounded shard counts
- Leave sims unbaked for final renders

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Rigid Body Presets | `../refs/physics-sim/rigid-body-presets.md` | When needed |
| Destruction Pipeline | `../refs/physics-sim/destruction-pipeline.md` | When needed |
| Sim Bake Checklist | `../refs/physics-sim/sim-bake-checklist.md` | When needed |


---

## ◆ cloth-sim  _(source: arjun988)_

> Garment blockout, cloth simulation, pin groups, and bake to shape keys or caches for characters and props in Blender via MCP.

## Cloth Sim

Garment blockout → sim → art-direct → bake. Stable pins. Engine-friendly caches/shape keys.

### When to Use

- Dresses, capes, coats, flags, banners
- Character clothing that needs drape
- Baking sim to shape keys or Alembic/USD caches
- Pre-roll settling before animation export

### Workflow

```
Garment mesh (quad-friendly) → Vertex groups (pin/collide)
  → Cloth modifier settings → Collision objects
  → Pre-roll settle → Sim pass → Art-direct fixes
  → Bake shape keys / cache → Cleanup → Export
```

### Mesh Prep

- Quads preferred; even density on deforming areas
- Avoid long skinny triangles on folds
- Apply scale before sim
- Separate garment from body collider

### Vertex Groups

| Group | Purpose |
|-------|---------|
| `PIN_Cloth` | Anchors (waist, shoulders, collar) |
| `COL_Ignore` | Optional non-colliding regions |
| `STIFF_High` | Belts, seams that should resist stretch |

### Settings Starters

| Look | Quality | Speed | Bending |
|------|---------|-------|---------|
| Soft dress | 8–12 | 1.0 | Low |
| Stiff coat | 5–8 | 1.0 | Higher |
| Flag/cape | 8–10 | 1.0–1.5 | Low–mid |

Tune mass and air viscosity for scale. Always run a settle pre-roll.

### Bake Targets

| Target | Use |
|--------|-----|
| Shape keys | Game poses / few frames |
| Alembic/USD | Cinematic caches |
| Armature weights | If converting to deform-only |

### Constraints

#### MUST DO
- Apply scale; define pin groups before long sims
- Collide against simplified body capsule/mesh
- Art-direct after sim (sculpt/corrective keys)

#### MUST NOT DO
- Sim hero cloth on ultra-dense sculpt meshes
- Skip pre-roll (starts mid-air / exploding)
- Export raw unstable caches

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Cloth Settings Presets | `../refs/cloth-sim/cloth-settings-presets.md` | When needed |
| Pin And Collide | `../refs/cloth-sim/pin-and-collide.md` | When needed |
| Bake Targets | `../refs/cloth-sim/bake-targets.md` | When needed |


---

## ◆ vfx-fx  _(source: arjun988)_

> Cinematic and game VFX in Blender including smoke, fire, particles, trails, and Geometry Nodes FX setups via MCP.

## VFX / FX

Readable effects. Controlled simulation domains. Game sprites vs cinematic volumes.

### When to Use

- Smoke, fire, dust, sparks, debris
- Magic / sci-fi energy FX
- Muzzle flashes, trails, impacts
- Geometry Nodes driven particle systems

### Path Decision

```
Game real-time → Meshes/cards/ribbons + emissive mats (+ GN)
Cinematic     → Mantaflow / particles / GN → render → comp
Hybrid        → Sim in Blender → bake flipbooks/meshes for engine
```

### Workflow

```
Brief (silhouette + timing) → Proxy emitter → Sim/GN prototype
  → Art-direct motion → Materials/lights → Cache → Render/comp or export
```

### Effect Types

| Type | Blender Approach |
|------|------------------|
| Smoke/fire | Mantaflow domain + flow; keep domain tight |
| Sparks | Particle Newtonian + collision + trail |
| Debris | Rigid body shards (`physics-sim` (→ guides/12-simulation-vfx-weather.md)) |
| Magic ribbons | Curves / GN extrude + emissive |
| Dust hit | Short particle burst + soft sprites |

### Domain Rules (Volume)

- Domain only as large as needed
- Resolution from low → high after motion approved
- Open borders intentionally; avoid wasted empty voxels
- Collection: `COL_FX_[Shot]`

### Naming

- Emitters: `FX_Emit_[Name]`
- Domains: `FX_Domain_[Name]`
- Caches: document frame range in brief

### Game Export Notes

- Prefer mesh cards / GN instances over volume export
- Atlas flipbooks when baking fire/smoke for engines
- Keep pivot at logical spawn point

### Constraints

#### MUST DO
- Approve motion at low res before high-res sim
- Light FX intentionally (emissive + key)
- Cache before final render

#### MUST NOT DO
- Huge empty domains
- Unbounded particle counts
- Skip timing brief (start/peak/end frames)

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Fx Timing Brief | `../refs/vfx-fx/fx-timing-brief.md` | When needed |
| Volume Domain Rules | `../refs/vfx-fx/volume-domain-rules.md` | When needed |
| Game Fx Export | `../refs/vfx-fx/game-fx-export.md` | When needed |


---

## ◆ blender-weather-fx  _(source: el4cteo)_

> Weather effects in Blender 5.3 - looping Geometry Nodes rain, snow, dust, ash and embers with ground hits and splashes, wet surfaces, puddles with animated ripples, wall streaks, snow cover (shader + real snow geometry), storm lightning with multi-stroke flashes and bolts, engine-ready weather masks. Use for rain, storm, snow, wet street, puddle, dust or ember scenes.

## Weather FX

The execution model is in `blender-core` (→ SKILL.md). Sky, sun/moon, fog and mood come from `blender-time-of-day` (→ guides/13-lighting-camera-lookdev.md), so run `scene_mood.py` first, then add weather. Rendering settings are in `blender-rendering` (→ guides/14-rendering-compositing.md).

### One call each
```
scripts/precipitation.py -- --type rain --intensity heavy --ground Street Roofs --wind 2 0
scripts/surface_weather.py -- --objects Street Car Walls --wetness 0.7 --puddles 0.4 --ripples 1 --streaks 0.5
scripts/lightning.py -- --flashes 2 --strokes 3
scripts/precipitation.py -- --type snow --intensity moderate --ground Terrain
scripts/surface_weather.py -- --objects Terrain Roofs --snow 0.8 --snow-depth 0.06
scripts/surface_weather.py -- --objects Street Car Walls --remove     # exact restore
```
A rainy night: `scene_mood.py --time night --fog-visibility 250` → rain → wetness + puddles → lightning. Rain and puddles at night are what sell a wet scene: wet surfaces reflect every practical light.

### precipitation.py (rain, snow, dust, ash, embers)
- Builds a GN modifier on `ENV_Weather_<Type>`. Its box covers what the camera sees across the frame range: world-fixed, so moving cameras don't drag the rain. With no camera, it covers a 18 m box. The floor is the lowest top of `--ground`.
- **Seamless loop with no simulation**: each particle lives N whole times per loop (`Lives`), so the last frame + 1 equals the first frame exactly. It renders any frame on its own and works headless.
- **Real speeds**: rain 7 m/s (9 at heavy/storm), snow 1, ash 0.6, dust 0.15, embers rise at 1.5, combined with `--wind X Y` (m/s).
- **Ground**: a raycast against the `--ground` objects stops particles at the first hit (roofs, awnings, streets). Rain spawns splash crowns lasting 80 ms at each hit, aligned to the surface normal.
- **Streaks, not motion blur**: rain is a 3-sided streak of length = speed × ½ frame (a 180° shutter), aligned to the travel direction. Motion blur off is cheaper and looks the same.
- Particles closer than 1.5 m to the camera are hidden (`Near Clear`), because huge blobs ruin shots. The viewport shows 10% (`Viewport Fraction`), renders show 100%.
- Density per intensity (particles/m³): rain 5/15/40/80, snow 10/30/80/160. Override with `--density`. The count is capped by `--max-count` (400k), and the result warns when it caps.
- All values remain modifier inputs (Count, Speed, Wind, Lives, Particle Size, Streak Length, Sway, Ground, Splash...), so tweak them there instead of re-running.

### surface_weather.py (wet, puddles, ripples, streaks, snow)
- Puts one `ENV_Weather` shader group in front of each Principled BSDF and records the originals on the material. `--remove` restores links and values exactly.
- **Wet** (Lagarde model): porous albedo darkens (up to 55% × `--porosity`), roughness drops, and a water film is added as **Coat**. Use porosity 0.6–0.9 for asphalt, concrete, wood and fabric, and 0.1–0.2 for metal, glass and plastic.
- **Puddles**: domain-warped world-space noise on up-facing faces. Coverage ≈ `--puddles`, feature size `--scale` (m, default 3). Inside a puddle: full coat, mirror coat roughness 0.02, and a flattened base normal, because water fills the cracks.
- **Ripples**: expanding rings, one per ~17 cm cell, driven by a `frame` driver (a simple expression, so it works without auto-run scripts). They only show inside puddles.
- **Streaks**: vertical noise on walls adds coat runs.
- **Snow**: up-facing coverage with a noisy edge, albedo 0.9, roughness 0.6 and a fine bump. `--snow-depth` adds real thickness with the `ENV_SnowCover` GN modifier: up-facing faces are subdivided and extruded upward by a noise height that is never zero, so there's no z-fighting. It uses the `ENV_M_Snow` material with subsurface.
- `--vertex-mask` writes the `ENV_Weather` color attribute (R puddles, G snow, B walls) for engine shaders.

### lightning.py
- A strike is 3 return strokes ~50 ms apart (at least 2 frames apart, so the flicker reads at 24 fps), each a peak followed by a 2-frame decay. `--strokes`, `--flashes` or `--frames` set the timing. The flash is a cool `ENV_Storm_Flash` sun (12° soft) keyed against the scene's key light (×2.5).
- `ENV_Storm_Bolt` is a branching emissive curve (midpoint displacement plus 4 branches), keyed with the flash. By default it is 300 m away, in frame and off-center. The world background strength flashes too (`--no-sky` to skip).
- Keys use LINEAR interpolation (flashes must snap, not ease).

### Rules
- **Rain is visible only when backlit or side-lit** against a darker background: put a practical or bright sky behind it. Front-lit rain disappears.
- Combine layers: fog (atmosphere) + rain streaks (mid) + splashes/ripples (ground) + wet reflections. Any one alone looks fake.
- Real scale is mandatory: speeds, densities and puddle sizes are in meters (`blender-scene-setup` (→ guides/01-scene-pipeline.md)).
- Check with a render at the final resolution. Rain density and streak visibility don't show in the viewport (10% count, no fog).
- Run `blender-asset-qa` (→ guides/17-qa-review.md) on the snow geometry if the asset will be exported.

### Games and real-time
Weather is an engine system (Unreal Niagara, Unity VFX Graph, Roblox ParticleEmitter). From Blender, export the **masks**: the vertex color attribute (`--vertex-mask`) or baked textures (`blender-texture-baking` (→ guides/08-materials-texturing-baking.md) self-bake of the wet material), plus snow cover meshes. Details are in [../refs/blender-weather-fx/realtime-engines.md](../refs/blender-weather-fx/realtime-engines.md). Physical values and the look library are in [../refs/blender-weather-fx/weather-values.md](../refs/blender-weather-fx/weather-values.md).

### Gotchas
- GN particles are instances, so `object.data` stays empty. Read results through the evaluated depsgraph (`depsgraph.object_instances`).
- Background (`-b`) evaluation counts as the viewport for the `Is Viewport` node, so a headless test sees 10% of the count. Renders get 100%.
- Ground objects are linked into the `ENV_Weather_<Type>_Ground` collection (linked, not moved).
- `surface_weather` changes shared materials: every object using that material gets wet. Duplicate materials first to limit it.
- Coat appears in both engines. EEVEE needs raytracing on (`eevee.use_raytracing`) for good puddle reflections.
