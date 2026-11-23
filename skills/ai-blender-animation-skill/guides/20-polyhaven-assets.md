# Poly Haven HDRIs, textures & studio scenes

> Fused guide. Script paths like `scripts/x.py` are relative to the **ai-blender-animation-skill skill root**; all Python helpers live in one flat `scripts/` folder (shared `_bpyx.py`). Node helpers are in `scripts/node/`. Where two sources disagree, prefer the Blender 5.x rules in SKILL.md.

Sections: `polyhaven-studio-setup`, `polyhaven-scene-builder`, `polyhaven-hdri-showcase`, `polyhaven-texture-apply`, `polyhaven-material-swap`


---

## ◆ polyhaven-studio-setup  _(source: kevinbadi)_

> Set up a professional product photography studio in Blender using PolyHaven HDRIs and PBR ground materials. Trigger when asked to create a studio setup, add HDRI lighting, set up product photography, or create a showroom scene.

## PolyHaven Studio Setup

One-command product photography studio. Downloads a PolyHaven HDRI for environment lighting and optionally adds a PBR ground plane — dramatically better reflections than manual lights.

### Prerequisites

- **Blender** (4.x+) with **Blender MCP addon** active on port 9876
- **PolyHaven** enabled in the addon sidebar

### How to Run

```bash
node scripts/node/polyhaven-studio-setup.js --hdri studio_small_09
node scripts/node/polyhaven-studio-setup.js --hdri sunset --ground concrete_wall_003 --resolution 2k
node scripts/node/polyhaven-studio-setup.js --list-hdris
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--hdri` | PolyHaven HDRI asset ID | `studio_small_09` |
| `--ground` | PolyHaven texture ID for ground plane (optional) | none |
| `--resolution` | Asset resolution: 1k, 2k, 4k | `2k` |
| `--strength` | HDRI background strength | `1.0` |
| `--rotation` | HDRI rotation in degrees | `0` |
| `--ground-size` | Ground plane size | `10` |
| `--port` | Blender MCP port | `9876` |
| `--list-hdris` | List popular studio HDRIs | false |

### Popular Studio HDRIs

- `studio_small_09` — Clean white studio
- `studio_small_08` — Warm studio
- `photo_studio_loft_hall` — Loft photography studio
- `industrial_sunset_02_puresky` — Golden hour
- `kloppenheim_06_puresky` — Outdoor overcast
- `royal_esplanade` — Grand interior


---

## ◆ polyhaven-scene-builder  _(source: kevinbadi)_

> Build complete product scenes using PolyHaven assets — HDRI environment, textured ground/pedestal, and optional props from the 3D model library. Trigger when asked to build a product scene, create a showcase setup, add a pedestal, or compose a product shot.

## PolyHaven Scene Builder

Builds a full product photography scene around your 3D model: HDRI environment, textured ground plane or pedestal, and optional prop models from PolyHaven's free library.

### How to Run

```bash
node scripts/node/polyhaven-scene-builder.js --hdri studio_small_09 --ground marble_01 --pedestal
node scripts/node/polyhaven-scene-builder.js --hdri royal_esplanade --ground wood_cabinet_worn_long --props "potted_plant_04"
node scripts/node/polyhaven-scene-builder.js --preset showroom
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--hdri` | PolyHaven HDRI asset ID | `studio_small_09` |
| `--ground` | PolyHaven texture for ground | none |
| `--pedestal` | Add a cylindrical pedestal under the product | `false` |
| `--pedestal-texture` | Texture for the pedestal | same as ground |
| `--props` | Comma-separated PolyHaven model IDs to add | none |
| `--resolution` | Asset resolution: 1k, 2k, 4k | `2k` |
| `--preset` | Quick preset: showroom, outdoor, minimal, dramatic | none |
| `--port` | Blender MCP port | `9876` |

### Presets

- **showroom** — `studio_small_09` HDRI + marble ground + pedestal
- **outdoor** — `kloppenheim_06_puresky` HDRI + concrete ground
- **minimal** — `studio_small_03` HDRI + no ground (floating product)
- **dramatic** — `industrial_sunset_02_puresky` HDRI + dark concrete + pedestal


---

## ◆ polyhaven-hdri-showcase  _(source: kevinbadi)_

> Render the same product across multiple HDRI environments and output a comparison grid. Trigger when asked to compare lighting setups, test different environments, show product in multiple settings, or create an HDRI comparison.

## PolyHaven HDRI Showcase

Renders your product across multiple PolyHaven HDRI environments and saves each as an image — perfect for picking the best lighting for your product shots or creating a showcase grid.

### How to Run

```bash
node scripts/node/polyhaven-hdri-showcase.js --output ~/Desktop/hdri-compare
node scripts/node/polyhaven-hdri-showcase.js --hdris "studio_small_09,royal_esplanade,industrial_sunset_02_puresky" --output ~/Desktop
node scripts/node/polyhaven-hdri-showcase.js --preset studios --output ~/Desktop/studios
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output` | Output directory for rendered images | **required** |
| `--hdris` | Comma-separated HDRI IDs to compare | default set of 6 |
| `--preset` | HDRI set: studios, outdoor, dramatic, all | none |
| `--resolution` | HDRI resolution: 1k, 2k | `1k` |
| `--render-width` | Render image width | `1920` |
| `--render-height` | Render image height | `1080` |
| `--samples` | Render samples | `64` |
| `--port` | Blender MCP port | `9876` |


---

## ◆ polyhaven-texture-apply  _(source: kevinbadi)_

> Apply realistic PBR textures from PolyHaven to any Blender object. Supports metals, wood, concrete, fabric, and more. Trigger when asked to texture an object, apply a material from PolyHaven, make something look like metal/wood/marble, or change object surface.

## PolyHaven Texture Apply

Downloads a full PBR texture set (diffuse, roughness, normal, displacement) from PolyHaven and applies it to a specific object in the Blender scene.

### How to Run

```bash
node scripts/node/polyhaven-texture-apply.js --object Mesh_0 --texture brushed_metal
node scripts/node/polyhaven-texture-apply.js --object Cube --texture marble_01 --resolution 2k
node scripts/node/polyhaven-texture-apply.js --search metal
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--object` | Blender object name to apply texture to | **required** |
| `--texture` | PolyHaven texture asset ID | **required** |
| `--resolution` | Texture resolution: 1k, 2k, 4k | `2k` |
| `--scale` | UV mapping scale | `1.0` |
| `--port` | Blender MCP port | `9876` |
| `--search` | Search PolyHaven textures by keyword | none |

### Popular Textures

- `brushed_metal` — Brushed aluminum/steel
- `carbon_fiber` — Carbon fiber weave
- `marble_01` — White marble
- `wood_cabinet_worn_long` — Aged wood
- `concrete_wall_003` — Raw concrete
- `leather_red_02` — Red leather
- `fabric_pattern_07` — Woven fabric


---

## ◆ polyhaven-material-swap  _(source: kevinbadi)_

> Cycle through multiple PolyHaven materials on a product and render each variant. Great for showing color/finish options. Trigger when asked to show material variants, swap textures, create color options, show finish comparisons, or render product in different materials.

## PolyHaven Material Swap

Applies multiple PolyHaven PBR textures to the same object one by one and renders each — perfect for showing product finish variants (matte black, glossy white, brushed metal, marble, etc.).

### How to Run

```bash
node scripts/node/polyhaven-material-swap.js --object Mesh_0 --textures "marble_01,brushed_metal,carbon_fiber" --output ~/Desktop/variants
node scripts/node/polyhaven-material-swap.js --object Mesh_0 --preset metals --output ~/Desktop/metals
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--object` | Blender object name | **required** |
| `--textures` | Comma-separated PolyHaven texture IDs | **required** (or use --preset) |
| `--output` | Output directory for rendered images | **required** |
| `--preset` | Texture set: metals, woods, stones, fabrics | none |
| `--resolution` | Texture resolution: 1k, 2k | `2k` |
| `--render-width` | Render image width | `1920` |
| `--render-height` | Render image height | `1080` |
| `--samples` | Render samples | `64` |
| `--port` | Blender MCP port | `9876` |

### Presets

- **metals** — brushed_metal, rusty_metal, painted_metal_02, corrugated_iron
- **woods** — wood_cabinet_worn_long, plywood, bark_brown_02, wood_floor
- **stones** — marble_01, concrete_wall_003, rock_face, gravel_floor_02
- **fabrics** — fabric_pattern_07, leather_red_02, denim_fabric, burlap_01
