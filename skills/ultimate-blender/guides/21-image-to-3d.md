# Photo → 3D model (Meshy API)

> Fused guide. Script paths like `scripts/x.py` are relative to the **ultimate-blender skill root**; all Python helpers live in one flat `scripts/` folder (shared `_bpyx.py`). Node helpers are in `scripts/node/`. Where two sources disagree, prefer the Blender 5.x rules in SKILL.md.

Sections: `image-to-3d`, `multi-image-to-3d`


---

## ◆ image-to-3d  _(source: kevinbadi)_

> Convert a photo into a 3D model using Meshy API and import it into Blender via MCP.

### Image to 3D Blender Skill

Converts a user-provided photo into a textured 3D model using the Meshy AI API, then imports it into the active Blender scene.

### When to Use

Trigger this skill when:
- User wants to turn a photo/image into a 3D model
- User says "make this 3D", "convert to 3D", "3D model from image"
- User provides an image and wants it in Blender as a 3D object

### Prerequisites

- **Meshy API Key**: Stored in environment variable `MESHY_API_KEY` or passed directly
- **Blender MCP**: Must be connected (blender-mcp addon running on port 9876)
- **Image**: Local file path (.jpg, .jpeg, .png) or publicly accessible URL

### Flow

#### Step 1: Prepare the Image

If the user provides a local file path, base64 encode it:

```bash
BASE64_IMAGE=$(base64 -i "<image_path>")
DATA_URI="data:image/png;base64,${BASE64_IMAGE}"
```

#### Step 2: Create Image-to-3D Task

```bash
curl -s https://api.meshy.ai/openapi/v1/image-to-3d \
  -X POST \
  -H "Authorization: Bearer ${MESHY_API_KEY}" \
  -H 'Content-Type: application/json' \
  -d '{
    "image_url": "<data_uri_or_public_url>",
    "ai_model": "meshy-6",
    "enable_pbr": true,
    "should_remesh": true,
    "should_texture": true,
    "topology": "quad",
    "target_polycount": 30000,
    "target_formats": ["glb"]
  }'
```

Response gives a task ID: `{"result": "<task_id>"}`

#### Step 3: Poll for Completion

```bash
curl -s https://api.meshy.ai/openapi/v1/image-to-3d/<task_id> \
  -H "Authorization: Bearer ${MESHY_API_KEY}"
```

Poll every 10 seconds. Check `status` field:
- `PENDING` — queued
- `IN_PROGRESS` — generating (check `progress` field for %)
- `SUCCEEDED` — done, `model_urls.glb` has the download URL
- `FAILED` — check `task_error.message`

#### Step 4: Download the GLB

```bash
curl -L -o "/Users/kevinbahrabadi/Blender Test/output/<filename>.glb" "<model_urls.glb>"
```

#### Step 5: Import into Blender

Use the Blender MCP `execute_blender_code` tool:

```python
import bpy

## Clear scene (optional, based on user preference)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

## Import GLB
bpy.ops.import_scene.gltf(filepath="/Users/kevinbahrabadi/Blender Test/output/<filename>.glb")

## Center and frame the imported object
bpy.ops.object.select_all(action='SELECT')
bpy.ops.view3d.view_selected()
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `ai_model` | `meshy-6` | Model to use. Options: `meshy-5`, `meshy-6`, `latest` |
| `model_type` | `standard` | `standard` for detail, `lowpoly` for clean game meshes |
| `topology` | `triangle` | `quad` or `triangle` mesh |
| `target_polycount` | `30000` | 100–300,000 polygons |
| `enable_pbr` | `true` | Generate metallic/roughness/normal maps |
| `symmetry_mode` | `auto` | `off`, `auto`, or `on` |
| `pose_mode` | `""` | `a-pose`, `t-pose`, or empty |
| `should_texture` | `true` | Generate textures (costs extra credits) |
| `remove_lighting` | `true` | Clean textures without baked lighting |

### Output

After completion, the user gets:
- 3D model imported into Blender scene
- Textured with PBR materials (if enabled)
- Ready for rendering, animation, or further editing

### Error Handling

- **402**: Insufficient Meshy credits — inform user
- **429**: Rate limited — wait and retry
- **FAILED status**: Report `task_error.message` to user
- **Blender MCP disconnected**: Ask user to reconnect addon


---

## ◆ multi-image-to-3d  _(source: kevinbadi)_

> Convert multiple photos (1-4 angles) of the same object into a high-accuracy 3D model using Meshy API and import into Blender.

### Multi-Image to 3D Blender Skill

Converts 1-4 photos of the same object (from different angles) into a textured 3D model using Meshy AI's Multi-Image to 3D API, then imports it into the active Blender scene. More angles = more accurate geometry and textures.

### When to Use

Trigger this skill when:
- User provides multiple photos of the same object and wants a 3D model
- User says "multi-angle 3D", "convert these images to 3D", "make a 3D model from these photos"
- User wants a more accurate 3D model than single-image can provide
- User has front/back/side shots of a product, character, or object

### Prerequisites

- **Meshy API Key**: Retrieved from memory (reference_meshy_api.md)
- **Blender MCP**: Must be connected (blender-mcp addon running on port 9876)
- **Images**: 1-4 local file paths (.jpg, .jpeg, .png) or publicly accessible URLs
- **Same object**: All images must depict the same object from different angles

### Flow

#### Step 1: Prepare the Images

For each local file, base64 encode it into a data URI:

```python
import base64, json

image_paths = ["front.png", "back.png", "side.png"]  # user-provided paths
image_urls = []

for path in image_paths:
    with open(path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = path.rsplit('.', 1)[-1].lower()
    mime = 'image/jpeg' if ext in ('jpg', 'jpeg') else 'image/png'
    image_urls.append(f"data:{mime};base64,{b64}")
```

#### Step 2: Create Multi-Image-to-3D Task

Write payload to a JSON file (base64 strings are too large for CLI args):

```python
payload = {
    "image_urls": image_urls,  # array of 1-4 data URIs or public URLs
    "ai_model": "meshy-6",
    "enable_pbr": True,
    "should_texture": True,
    "target_formats": ["glb"]
}

with open("output/request.json", "w") as f:
    json.dump(payload, f)
```

Then POST:

```bash
curl -s https://api.meshy.ai/openapi/v1/multi-image-to-3d \
  -X POST \
  -H "Authorization: Bearer ${MESHY_API_KEY}" \
  -H 'Content-Type: application/json' \
  -d @output/request.json
```

Response: `{"result": "<task_id>"}`

#### Step 3: Poll for Completion

```bash
curl -s https://api.meshy.ai/openapi/v1/multi-image-to-3d/<task_id> \
  -H "Authorization: Bearer ${MESHY_API_KEY}"
```

Poll every 15 seconds. Check `status`:
- `PENDING` — queued (check `preceding_tasks` for queue position)
- `IN_PROGRESS` — generating (check `progress` for %)
- `SUCCEEDED` — done, download from `model_urls.glb`
- `FAILED` — check `task_error.message`

#### Step 4: Download the GLB

```bash
curl -L -o "output/<filename>.glb" "<model_urls.glb>"
```

#### Step 5: Import into Blender

Use the Blender MCP `execute_blender_code` tool:

```python
import bpy

## Clear scene (optional)
for obj in bpy.data.objects:
    bpy.data.objects.remove(obj, do_unlink=True)

## Import GLB
bpy.ops.import_scene.gltf(filepath="<path_to_glb>")

## Frame imported object
bpy.ops.object.select_all(action='SELECT')

## Add basic lighting
import math
from mathutils import Vector, Euler
bpy.ops.object.light_add(type='AREA', location=(2, -2, 3))
key = bpy.context.active_object
key.data.energy = 500
key.data.size = 3

## Set viewport to material preview
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'MATERIAL'
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `ai_model` | `meshy-6` | `meshy-5`, `meshy-6`, or `latest` |
| `topology` | `triangle` | `quad` or `triangle` mesh |
| `target_polycount` | `30000` | 100–300,000 polygons |
| `enable_pbr` | `true` | Metallic/roughness/normal maps |
| `symmetry_mode` | `auto` | `off`, `auto`, or `on` |
| `pose_mode` | `""` | `a-pose`, `t-pose`, or empty |
| `should_texture` | `true` | Generate textures |
| `should_remesh` | `false` | Remesh to target polycount/topology |
| `remove_lighting` | `true` | Clean textures without baked lighting |
| `image_enhancement` | `true` | Optimize input images |
| `target_formats` | all | Array: `glb`, `obj`, `fbx`, `stl`, `usdz`, `3mf` |

### Tips for Best Results

- **Different angles**: Front, back, left side, right side work best
- **Consistent lighting**: Same lighting conditions across all photos
- **Clean background**: Plain/white backgrounds help
- **Same object**: All images MUST be the same object
- **2-4 images**: More angles = better accuracy, but diminishing returns past 4

### Error Handling

- **400**: Invalid image count (must be 1-4), bad format, unreachable URL
- **402**: Insufficient Meshy credits
- **429**: Rate limited — wait and retry
- **FAILED status**: Report `task_error.message` to user
