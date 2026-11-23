# Horror packs

> Fused guide. Script paths like `scripts/x.py` are relative to the **ai-blender-animation-skill skill root**; all Python helpers live in one flat `scripts/` folder (shared `_bpyx.py`). Node helpers are in `scripts/node/`. Where two sources disagree, prefer the Blender 5.x rules in SKILL.md.

Sections: `horror-style`, `psx-horror-style`, `indie-horror-aesthetics`, `analog-found-footage-horror`, `body-horror-style`, `cosmic-eldritch-horror`, `folk-horror-style`, `mascot-puppet-horror`, `liminal-space-style`, `dream-weirdcore-style`


---

## ◆ horror-style  _(source: arjun988)_

> Psychological horror art direction for Blender assets inspired by Silent Hill, Resident Evil, Chilla's Art, Fear to Fathom, and Iron Lung. Use for sparse industrial environments, analog aesthetics, and tension-driven lighting.

## Horror Style Specialist

Psychological tension over jump scares. Environmental storytelling. Sparse detail. Industrial decay.

### When to Use

- Horror game environments and props
- Psychological tension scenes
- Analog/liminal aesthetic assets
- Industrial decay settings
- Limited visibility compositions

### Design Philosophy

Inspired by: Fear to Fathom, Chilla's Art, Puppet Combo, Silent Hill, Resident Evil, Iron Lung

**Core tenets:**
1. **Less is more** — Absence creates tension
2. **Familiar made wrong** — Recognizable spaces with subtle wrongness
3. **Light as enemy** — Darkness hides; light reveals uncomfortably
4. **Industrial analog** — CRT screens, fluorescent hum, concrete, rust
5. **Environmental narrative** — Story told through objects, not exposition

### Visual Language

| Element | Horror Treatment |
|---------|------------------|
| Architecture | Brutalist, institutional, repetitive |
| Materials | Stained concrete, peeling paint, rust, yellowed plastic |
| Lighting | Single source, flickering, cold fluorescent |
| Detail density | Sparse foreground, empty midground, obscured background |
| Color | Desaturated, sickly greens, cold blues, blood accent sparingly |
| Scale | Slightly wrong proportions (low ceilings, narrow corridors) |

### Modeling Guidelines

- **Corridors:** Narrow (1.2–1.5m) for claustrophobia
- **Ceilings:** Low (2.2–2.4m institutional)
- **Doors:** Slightly oversized or undersized — uncanny
- **Detail:** Concentrate on hero interactive objects; walls mostly bare
- **Damage:** Water stains > bullet holes; neglect > destruction
- **Technology:** 80s–90s analog — CRT monitors, tape recorders, rotary phones

### Sparse Detail Rule

```
Foreground: 1–2 narrative objects (key, note, blood stain)
Midground: Architectural structure only
Background: Fog/darkness obscures incomplete geometry
```

Do not over-model backgrounds visible only in darkness.

### Lighting (Horror)

Coordinate with lighting skill:
- High contrast ratio (8:1 minimum key:fill)
- Visible light source meshes (bare bulb, fluorescent tube)
- Volumetric fog mandatory for depth
- Color temperature clash: warm interior vs cold exterior
- Flicker animation on 1–2 lights only

### Audio-Visual Sync Points

Design geometry supporting:
- Long empty hallways (footstep echo)
- Door slow-open clearance
- Corner blind spots
- Mirror/reflection placements

### Material Palette

| Material | Parameters |
|----------|------------|
| Stained concrete | Roughness 0.9, desaturated gray-green |
| Peeling paint | Vertex color mask, exposed concrete under |
| Rust metal | Roughness 0.85, dark orange-brown |
| Yellowed plastic | Subsurface slight, warm yellow |
| CRT screen | Emission: green/phosphor, low intensity |
| Blood (sparingly) | Dark dried red, roughness 0.7 |

### Reference Mood Board Targets

- Empty school hallways after hours
- Abandoned medical facilities
- Submarine interiors (Iron Lung)
- Fog-shrouded streets with single streetlight
- Apartment with one room lit by TV glow

### Polycount Approach

Horror benefits from lowpoly-style efficiency:
- Simple geometry + strong lighting = effective horror
- See lowpoly-style for budget alignment
- Budget saved on geo → spend on lighting/volumetrics

### MCP Integration

1. Build sparse environment layouts via MCP
2. Place single-source lighting via MCP
3. Assign desaturated materials via MCP
4. Validate sightlines and blind corners via camera MCP
5. Keep background collections low-poly/hidden in fog

### Constraints

#### MUST DO
- Prioritize atmosphere over detail
- Design readable paths with unsettling alternatives
- Use environmental storytelling objects sparingly
- Coordinate with lighting skill always
- Test scene from player eye height (1.6m)

#### MUST NOT DO
- Over-detail every surface
- Bright even lighting
- Jump-scare gore everywhere
- Modern smartphone/tech unless anachronism intentional
- Dense vegetation (breaks institutional mood unless forest horror)

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Environment layouts | `../refs/horror-style/horror-layouts.md` | Level blockout |
| Analog props | `../refs/horror-style/analog-props.md` | Prop list |

### Related Horror Packs
- `psx-horror-style` (→ styles/horror.md), `cosmic-eldritch-horror` (→ styles/horror.md), `body-horror-style` (→ styles/horror.md), `analog-found-footage-horror` (→ styles/horror.md)
- `liminal-space-style` (→ styles/horror.md), `folk-horror-style` (→ styles/horror.md), `mascot-puppet-horror` (→ styles/horror.md), `dream-weirdcore-style` (→ styles/horror.md)
- `indie-horror-aesthetics` (→ styles/horror.md)


---

## ◆ psx-horror-style  _(source: arjun988)_

> PS1/PSX-era horror art direction combining low-poly affine textures, limited color depth, fog, and psychological horror staging for Blender assets.

## PSX Horror Style

Crunchy low-poly horror. Affine textures. Fog. Limited palette. Tension over fidelity.

### When to Use

- PS1-era horror game looks
- Puppet Combo / retro survival horror vibes
- When `horror-style` (→ styles/horror.md) needs explicit PSX constraints

### Core Tenets

1. **Low poly, high dread** — Few tris, strong shapes
2. **Texture crunch** — Low-res, nearest filtering feel
3. **Vertex / affine warping cues** — Subtle wobble optional
4. **Fog + darkness** — Hide draw distance sins
5. **Analog grit** — VHS/CRT via compositing sparingly

### Vs Related Styles

| Skill | Role |
|-------|------|
| `horror-style` (→ styles/horror.md) | Broad psychological horror direction |
| `lowpoly-style` (→ styles/art-styles.md) | General PS1/PS2 / Lethal Company |
| `psx-horror-style` | Horror + PSX crunch specifically |

### Modeling

- 100–800 tris for many props
- Characters chunky; faces minimal
- Interiors modular, repetitive, oppressive

### Materials / Textures

- 64–256px textures common
- Limited palette; indexed feel
- Flat shading or very low smooth
- Emissive screens as narrative props

### Lighting & Camera

- Single practical lights; deep shadows
- Low camera, narrow spaces
- Fog/mist mandatory for depth
- Optional handheld noise (`camera-cinematography` (→ guides/13-lighting-camera-lookdev.md))

### Compositing Extras

- Slight blur / chromatic aberration
- Posterize / crush colors carefully
- Film grain / VHS overlay subtle

### Constraints

#### MUST DO
- Keep poly and texture budgets intentionally low
- Prioritize fog, sound-design-friendly spaces
- Stage sparse narrative props

#### MUST NOT DO
- Modern PBR microdetail as primary look
- Bright clean global illumination

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Psx Horror Budgets | `../refs/psx-horror-style/psx-horror-budgets.md` | When needed |
| Psx Horror Palette | `../refs/psx-horror-style/psx-horror-palette.md` | When needed |


---

## ◆ indie-horror-aesthetics  _(source: arjun988)_

> Indie horror aesthetic pack for Blender covering Silent Hill, Fear to Fathom, Puppet Combo, corporate horror, cabin/forest/hospital horror, and related looks.

## Indie Horror Aesthetics

Reference-driven indie horror looks. Pick a lane; don’t mash all at once.

### Load subtype refs
Silent Hill fog/rust; Fear to Fathom domestic analog; Puppet Combo PSX crunch; corporate/empty office; cabin/forest; hospital; urban decay.


---

## ◆ analog-found-footage-horror  _(source: arjun988)_

> Analog, VHS, CRT, and found-footage horror aesthetics for Blender shots including camera imperfections and documentary framing.

## Analog / Found Footage Horror

Documentary camera. Tape damage. Dead channels. Corporate/educational uncanny.

### Tenets
1. Handheld / locked security cam language
2. Timestamp / tracking UI optional (comp)
3. VHS blur, chroma bad, tracking lines
4. Mundane spaces made wrong
5. Less monster, more implication


---

## ◆ body-horror-style  _(source: arjun988)_

> Body horror art direction for Blender focusing on flesh wrongness, mutation, fusion, and visceral material storytelling.

## Body Horror

Flesh as wrong material. Fusion. Mutation. Uncomfortable sympathy.

### Tenets
1. Anatomy almost-right then broken
2. Material transitions: skin→meat→metal→plastic
3. Moist specular sparingly (not gore porn by default)
4. Human recognition remains (uncanny)
5. Coordinate with creature-artist / sculpting


---

## ◆ cosmic-eldritch-horror  _(source: arjun988)_

> Cosmic, eldritch, and Lovecraftian horror art direction for Blender with non-Euclidean cues, impossible scale, and incomprehensible forms.

## Cosmic / Eldritch Horror

Incomprehensible scale. Wrong geometry. Void pressure.

### Tenets
1. Scale mismatch (tiny human vs vast form)
2. Suggestive detail — never fully explain the monster
3. Non-Euclidean architecture cues
4. Color: abyssal blues, sickly golds, void blacks
5. Sound-design-friendly spaces (long falls, vast chambers)


---

## ◆ folk-horror-style  _(source: arjun988)_

> Folk horror art direction for Blender with rural ritual uncanny, pastoral daylight dread, and community-wrongness storytelling.

## Folk Horror

Daylight dread. Pastoral beauty wrong. Ritual objects. Closed communities.

### Tenets
1. Beautiful nature + wrong customs
2. Handmade ritual props
3. Village scale, fields, woods
4. Warm daylight can be scarier than night
5. Symbols repeating


---

## ◆ mascot-puppet-horror  _(source: arjun988)_

> Mascot and puppet horror art direction for Blender with cheerful brand characters made wrong, felt/foam materials, and uncanny performance.

## Mascot / Puppet Horror

Cute brand language corrupted. Felt, foam, plastic eyes. Performance uncanny.

### Tenets
1. Friendly shapes + dead/wrong eyes
2. Craft materials (felt, plush, plastic)
3. Stage/set like children’s show gone wrong
4. Bright palette with one sick shift
5. Often pairs with PSX or analog crunch


---

## ◆ liminal-space-style  _(source: arjun988)_

> Liminal space and Backrooms art direction for Blender with empty transitional architecture, wrong familiarity, and endless repetition.

## Liminal Space / Backrooms

Familiar architecture without people. Repetition. Wrong lighting. Endless continuation.

### Subplaces
Backrooms, empty mall, empty school, poolrooms, hotels, offices

### Tenets
1. Repetitive modular kits
2. Fluorescent hum lighting
3. Stained carpet / yellowed walls (variant-dependent)
4. No narrative clutter — emptiness is the story
5. Soft wrongness over jump scares


---

## ◆ dream-weirdcore-style  _(source: arjun988)_

> Dreamcore, weirdcore, and traumacore-inspired art direction for Blender with nostalgic wrongness, liminal nostalgia, and surreal childhood spaces.

## Dream / Weirdcore Style

Nostalgic spaces. Soft dread. Surreal edits. Childhood UI/objects out of place.

### Tenets
1. Soft fog / bloom
2. Childhood objects oversized or abandoned
3. Text overlays / cryptic captions optional (comp)
4. Unclear geography
5. Emotion > logic
