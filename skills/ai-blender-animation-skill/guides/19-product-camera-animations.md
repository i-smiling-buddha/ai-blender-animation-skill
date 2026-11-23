# Product showcase camera animations

> Fused guide. Script paths like `scripts/x.py` are relative to the **ai-blender-animation-skill skill root**; all Python helpers live in one flat `scripts/` folder (shared `_bpyx.py`). Node helpers are in `scripts/node/`. Where two sources disagree, prefer the Blender 5.x rules in SKILL.md.

Sections: `turntable`, `slow-zoom`, `dolly-rotate`, `crane-shot`, `dynamic-full-loop`, `perfect-loop`, `product-polish`


---

## ◆ turntable  _(source: kevinbadi)_

> 360-degree turntable camera orbit around a 3D product. Classic product showcase animation.

### Turntable Camera Animation

Orbits the camera 360 degrees around the product for a clean product showcase. Starts front-facing and loops seamlessly.

### When to Use

- User wants a product turntable / spin video
- User says "rotate around", "orbit", "showcase all angles", "turntable"
- Default go-to for product showcase videos

### Prerequisites

- **Blender MCP**: Connected (blender-mcp addon on port 9876)
- **3D model**: Already imported in the Blender scene
- **Output folder**: `~/Desktop/Blender Videos/` (create if needed)
- **ffmpeg**: Installed for video encoding

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `duration` | `5` | Video length in seconds |
| `fps` | `24` | Frames per second |
| `camera_distance` | `4.5` | Distance from object center |
| `camera_height` | `2.0` | Camera height above object |
| `camera_lens` | `50` | Focal length in mm |
| `transparent_bg` | `true` | Transparent background |
| `output_format` | `mov` | `mov` (ProRes 4444 w/ alpha) or `webm` (VP9 alpha) |

### Flow

#### Step 1: Detect Front Face

Render 4 low-res test frames from different camera positions to find the front of the product. Ask the user which angle is the front.

```python
import bpy, math
from mathutils import Vector

obj = bpy.data.objects['<OBJECT_NAME>']
bbox = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
center = sum(bbox, Vector()) / 8

RADIUS = 4.5
HEIGHT = 2.0

## Create temp camera
bpy.ops.object.camera_add()
cam = bpy.context.active_object
cam.name = 'TempCam'
bpy.context.scene.camera = cam

## Add track constraint to center
bpy.ops.object.empty_add(type='PLAIN_AXES', location=center)
target = bpy.context.active_object
target.name = 'TempTarget'

cam.constraints.new(type='TRACK_TO').target = target

## Render 4 angles
positions = {
    'front': (center.x, center.y - RADIUS, HEIGHT),
    'right': (center.x + RADIUS, center.y, HEIGHT),
    'back': (center.x, center.y + RADIUS, HEIGHT),
    'left': (center.x - RADIUS, center.y, HEIGHT),
}
for label, pos in positions.items():
    cam.location = pos
    bpy.context.scene.render.filepath = f'<OUTPUT>/facing_{label}.png'
    bpy.ops.render.render(write_still=True)
```

Show all 4 images to the user and ask which is the front.

#### Step 2: Set Up Camera Rig

```python
import bpy, math

## Create target empty at object center
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
target = bpy.context.active_object
target.name = 'TurntableTarget'

## Create camera at front-facing position (determined from Step 1)
## Default front = -Y axis
bpy.ops.object.camera_add(location=(0, -CAMERA_DISTANCE, CAMERA_HEIGHT))
cam = bpy.context.active_object
cam.name = 'TurntableCamera'
cam.data.lens = 50

## Track to target
track = cam.constraints.new(type='TRACK_TO')
track.target = target
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

## Parent camera to target for orbit
bpy.ops.object.select_all(action='DESELECT')
cam.select_set(True)
target.select_set(True)
bpy.context.view_layer.objects.active = target
bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

bpy.context.scene.camera = cam
```

#### Step 3: Animate 360 Rotation

```python
import bpy, math

TOTAL_FRAMES = DURATION * FPS  # e.g. 5 * 24 = 120

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = TOTAL_FRAMES
scene.render.fps = FPS

target = bpy.data.objects['TurntableTarget']
target.rotation_euler = (0, 0, 0)
target.keyframe_insert(data_path='rotation_euler', frame=1)
target.rotation_euler = (0, 0, math.radians(360))
target.keyframe_insert(data_path='rotation_euler', frame=TOTAL_FRAMES + 1)

## IMPORTANT: Linear interpolation for constant speed
## Blender 5.1 uses layered actions:
action = target.animation_data.action
strip = action.layers[0].strips[0]
for cb in strip.channelbags:
    for fc in cb.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
```

#### Step 4: Set Up Lighting

```python
import bpy, math

## Warm sunset lighting on LIGHTS only (not on materials/world)
bpy.ops.object.light_add(type='AREA', location=(3, -3, 4))
k = bpy.context.active_object; k.name='GoldenKey'
k.data.energy = 2000; k.data.size = 3.0
k.data.color = (1.0, 0.78, 0.45)
k.rotation_euler = (math.radians(45), 0, math.radians(25))

bpy.ops.object.light_add(type='AREA', location=(-3, -2, 3))
f = bpy.context.active_object; f.name='WarmFill'
f.data.energy = 1000; f.data.size = 5.0
f.data.color = (1.0, 0.75, 0.4)
f.rotation_euler = (math.radians(40), 0, math.radians(-30))

bpy.ops.object.light_add(type='AREA', location=(0, 0, 5))
oh = bpy.context.active_object; oh.name='OverheadWash'
oh.data.energy = 800; oh.data.size = 8.0
oh.data.color = (1.0, 0.92, 0.75)

bpy.ops.object.light_add(type='AREA', location=(0, 4, 2))
r = bpy.context.active_object; r.name='WarmRim'
r.data.energy = 800; r.data.size = 3.0
r.data.color = (1.0, 0.65, 0.3)
r.rotation_euler = (math.radians(-40), 0, math.radians(180))

bpy.ops.object.light_add(type='AREA', location=(4, 0, 0.5))
sw = bpy.context.active_object; sw.name='SideGlow'
sw.data.energy = 600; sw.data.size = 2.0
sw.data.color = (1.0, 0.8, 0.5)
sw.rotation_euler = (math.radians(5), 0, math.radians(90))
```

#### Step 5: Render

```python
import bpy, os

scene = bpy.context.scene
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.film_transparent = True
scene.render.engine = 'CYCLES'  # better metallic reflections
scene.cycles.samples = 64
scene.cycles.use_denoising = True
scene.cycles.device = 'GPU'
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'

## Neutral world for subtle reflections (not colored)
if not scene.world:
    scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get('Background')
bg.inputs['Color'].default_value = (0.95, 0.95, 0.95, 1)
bg.inputs['Strength'].default_value = 0.3

frames_dir = os.path.expanduser('~/Desktop/Blender Videos/turntable_frames/')
os.makedirs(frames_dir, exist_ok=True)
scene.render.filepath = frames_dir

bpy.ops.render.render(animation=True)
```

#### Step 6: Encode Video

MCP will timeout during render. Poll frames directory until all frames exist, then encode:

```bash
## ProRes 4444 with alpha (transparent)
ffmpeg -y -framerate 24 \
  -i "~/Desktop/Blender Videos/turntable_frames/%04d.png" \
  -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le \
  "~/Desktop/Blender Videos/turntable.mov"
```

### Blender 5.1 Notes

- Render engine enum: `BLENDER_EEVEE` (not `BLENDER_EEVEE_NEXT`)
- No FFMPEG output format — render PNG sequence + encode with ffmpeg
- Layered actions API: `action.layers[0].strips[0].channelbags` to access fcurves
- `film_transparent = True` for transparent background
- Warm color goes on the LIGHTS, not on the world/materials


---

## ◆ slow-zoom  _(source: kevinbadi)_

> Cinematic slow push-in zoom toward a hero detail on the product. Creates a reveal effect.

### Slow Zoom Camera Animation

Camera slowly pushes in from a wide establishing shot to a tight close-up on a hero detail (logo, texture, feature). Includes subtle dolly zoom (focal length shift) for cinematic compression.

### When to Use

- User wants a "reveal" or "hero shot"
- User says "zoom in", "push in", "close-up on the logo", "cinematic reveal"
- Highlighting a specific detail or feature on the product

### Prerequisites

- **Blender MCP**: Connected
- **3D model**: Already imported in the Blender scene
- **Output folder**: `~/Desktop/Blender Videos/`
- **ffmpeg**: Installed

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `duration` | `5` | Video length in seconds |
| `fps` | `24` | Frames per second |
| `start_distance` | `4.0` | Starting camera distance |
| `end_distance` | `1.8` | Ending camera distance (close-up) |
| `start_height` | `3.0` | Starting camera height |
| `end_height` | `1.2` | Ending camera height |
| `start_lens` | `35` | Starting focal length (wide) |
| `end_lens` | `65` | Ending focal length (tight) |
| `focus_point` | `(0,0,0.1)` | Point to zoom toward (e.g. logo center) |
| `transparent_bg` | `true` | Transparent background |

### Flow

#### Step 1: Identify Focus Point

Ask user what detail to zoom into, or default to object center. Use `AskUserQuestion` if unclear.

#### Step 2: Set Up Camera

```python
import bpy, math

## Focus target
bpy.ops.object.empty_add(type='PLAIN_AXES', location=FOCUS_POINT)
tgt = bpy.context.active_object
tgt.name = 'ZoomTarget'

## Camera
bpy.ops.object.camera_add(location=(START_X, -START_DISTANCE, START_HEIGHT))
cam = bpy.context.active_object
cam.name = 'SlowZoomCam'
cam.data.lens = START_LENS

track = cam.constraints.new(type='TRACK_TO')
track.target = tgt
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

bpy.context.scene.camera = cam
```

#### Step 3: Animate Push-In

```python
import bpy

TOTAL_FRAMES = DURATION * FPS
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = TOTAL_FRAMES
scene.render.fps = FPS

## Start wide
cam.location = (1.5, -START_DISTANCE, START_HEIGHT)
cam.keyframe_insert(data_path='location', frame=1)
cam.data.lens = START_LENS
cam.data.keyframe_insert(data_path='lens', frame=1)

## End tight
cam.location = (0.3, -END_DISTANCE, END_HEIGHT)
cam.keyframe_insert(data_path='location', frame=TOTAL_FRAMES)
cam.data.lens = END_LENS
cam.data.keyframe_insert(data_path='lens', frame=TOTAL_FRAMES)

## Keep default BEZIER interpolation for smooth ease in/out
```

#### Step 4: Lighting + Render

Use the same golden hour lighting setup as turntable skill. Render as PNG sequence with Cycles, encode with ffmpeg to ProRes 4444.

```bash
ffmpeg -y -framerate 24 \
  -i "~/Desktop/Blender Videos/slowzoom_frames/%04d.png" \
  -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le \
  "~/Desktop/Blender Videos/slow_zoom.mov"
```

### Tips

- The focal length shift (35mm to 65mm) creates a subtle dolly zoom / Hitchcock effect
- BEZIER interpolation gives smooth ease-in/out — don't use LINEAR for this animation
- Offset the start position slightly on X (e.g. 1.5) for a more cinematic diagonal approach


---

## ◆ dolly-rotate  _(source: kevinbadi)_

> Camera moves forward while rotating around the product. More dynamic than a straight zoom.

### Dolly + Rotate Camera Animation

Camera dollies forward while simultaneously rotating around the product, creating a dynamic sweeping reveal that's more engaging than a straight zoom or static orbit.

### When to Use

- User wants a "dynamic" or "sweeping" shot
- User says "dolly", "move and rotate", "sweeping reveal"
- More cinematic than a simple turntable

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `duration` | `5` | Video length in seconds |
| `fps` | `24` | Frames per second |
| `rotation_degrees` | `90` | How far to rotate during the dolly |
| `start_distance` | `4.0` | Starting distance |
| `end_distance` | `2.5` | Ending distance |
| `start_height` | `2.0` | Starting height |
| `end_height` | `1.5` | Ending height |

### Flow

#### Step 1: Set Up Camera Rig

```python
import bpy, math

bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0.05))
tgt = bpy.context.active_object
tgt.name = 'DollyTarget'

bpy.ops.object.camera_add(location=(2.5, -START_DISTANCE, START_HEIGHT))
cam = bpy.context.active_object
cam.name = 'DollyCam'
cam.data.lens = 40

trk = cam.constraints.new(type='TRACK_TO')
trk.target = tgt
trk.track_axis = 'TRACK_NEGATIVE_Z'
trk.up_axis = 'UP_Y'

## Parent camera to target for orbital rotation
bpy.ops.object.select_all(action='DESELECT')
cam.select_set(True)
tgt.select_set(True)
bpy.context.view_layer.objects.active = tgt
bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

bpy.context.scene.camera = cam
```

#### Step 2: Animate Dolly + Rotation

```python
TOTAL_FRAMES = DURATION * FPS

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = TOTAL_FRAMES
scene.render.fps = FPS

## Frame 1: start position
tgt.rotation_euler = (0, 0, 0)
tgt.keyframe_insert(data_path='rotation_euler', frame=1)
cam.location = (2.5, -START_DISTANCE, START_HEIGHT)
cam.keyframe_insert(data_path='location', frame=1)
cam.data.lens = 40
cam.data.keyframe_insert(data_path='lens', frame=1)

## End: rotated + closer
tgt.rotation_euler = (0, 0, math.radians(ROTATION_DEGREES))
tgt.keyframe_insert(data_path='rotation_euler', frame=TOTAL_FRAMES)
cam.location = (1.5, -END_DISTANCE, END_HEIGHT)
cam.keyframe_insert(data_path='location', frame=TOTAL_FRAMES)
cam.data.lens = 50
cam.data.keyframe_insert(data_path='lens', frame=TOTAL_FRAMES)

## Default BEZIER interpolation for smooth cinematic feel
```

#### Step 3: Render + Encode

Same as turntable — PNG sequence with Cycles, encode to ProRes 4444.

```bash
ffmpeg -y -framerate 24 \
  -i "~/Desktop/Blender Videos/dolly_rotate_frames/%04d.png" \
  -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le \
  "~/Desktop/Blender Videos/dolly_rotate.mov"
```


---

## ◆ crane-shot  _(source: kevinbadi)_

> Camera starts low and rises up to reveal the full product. Great for dramatic product reveals on a pedestal.

### Crane Shot Camera Animation

Camera begins at a low angle looking up at the product, then smoothly rises to reveal the full product from above. Creates a dramatic unveiling effect.

### When to Use

- User wants a "reveal" or "unveil" shot
- User says "crane", "rise up", "low to high", "dramatic reveal"
- Product on a pedestal or platform

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `duration` | `5` | Video length in seconds |
| `fps` | `24` | Frames per second |
| `start_height` | `-0.2` | Starting height (below product level) |
| `end_height` | `3.5` | Ending height (above product) |
| `start_distance` | `3.0` | Starting distance |
| `end_distance` | `4.0` | Ending distance (pulls back as it rises) |

### Flow

#### Step 1: Set Up Camera

```python
import bpy, math

bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0.05))
tgt = bpy.context.active_object
tgt.name = 'CraneTarget'

bpy.ops.object.camera_add(location=(1.0, -START_DISTANCE, START_HEIGHT))
cam = bpy.context.active_object
cam.name = 'CraneCam'
cam.data.lens = 45

trk = cam.constraints.new(type='TRACK_TO')
trk.target = tgt
trk.track_axis = 'TRACK_NEGATIVE_Z'
trk.up_axis = 'UP_Y'

bpy.context.scene.camera = cam
```

#### Step 2: Animate Crane Movement

```python
TOTAL_FRAMES = DURATION * FPS

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = TOTAL_FRAMES
scene.render.fps = FPS

## Start low
cam.location = (1.0, -START_DISTANCE, START_HEIGHT)
cam.keyframe_insert(data_path='location', frame=1)
cam.data.lens = 45
cam.data.keyframe_insert(data_path='lens', frame=1)

## Rise up and pull back
cam.location = (1.5, -END_DISTANCE, END_HEIGHT)
cam.keyframe_insert(data_path='location', frame=TOTAL_FRAMES)
cam.data.lens = 35
cam.data.keyframe_insert(data_path='lens', frame=TOTAL_FRAMES)

## BEZIER for smooth crane motion
```

#### Step 3: Render + Encode

Same pipeline — Cycles, PNG sequence, ffmpeg ProRes 4444.

```bash
ffmpeg -y -framerate 24 \
  -i "~/Desktop/Blender Videos/crane_frames/%04d.png" \
  -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le \
  "~/Desktop/Blender Videos/crane_shot.mov"
```


---

## ◆ dynamic-full-loop  _(source: kevinbadi)_

> Dynamic camera loop with speed ramping - slow reveals on each face, fast whips between. Shows all sides including top and bottom.

### Dynamic Full Loop Camera Animation

Camera orbits the product on multiple axes with speed ramping — slow motion when revealing each side of the product, fast whip transitions between faces. Shows front, sides, back, top, and bottom.

### When to Use

- User wants to "show every angle" with dynamic motion
- User says "full loop", "speed ramp", "show all sides", "dynamic spin"
- Social media / marketing hero video

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `duration` | `10` | Video length in seconds (longer due to speed ramps) |
| `fps` | `24` | Frames per second |
| `camera_distance` | `4.0` | Camera distance from center |
| `camera_height` | `1.8` | Camera height |

### Flow

#### Step 1: Set Up Camera Rig

```python
import bpy, math

bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
tgt = bpy.context.active_object
tgt.name = 'DynamicTarget'

bpy.ops.object.camera_add(location=(0, -CAMERA_DISTANCE, CAMERA_HEIGHT))
cam = bpy.context.active_object
cam.name = 'DynamicCam'
cam.data.lens = 45

trk = cam.constraints.new(type='TRACK_TO')
trk.target = tgt
trk.track_axis = 'TRACK_NEGATIVE_Z'
trk.up_axis = 'UP_Y'

## Parent camera to target
bpy.ops.object.select_all(action='DESELECT')
cam.select_set(True)
tgt.select_set(True)
bpy.context.view_layer.objects.active = tgt
bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

bpy.context.scene.camera = cam
```

#### Step 2: Animate with Speed Ramping

The key is BEZIER interpolation with keyframes clustered for slow/fast:
- Close keyframes with small rotation change = SLOW (lingering on a face)
- Wide keyframes with large rotation change = FAST (whip transition)

```python
TOTAL_FRAMES = DURATION * FPS  # 240 at 10s/24fps

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = TOTAL_FRAMES
scene.render.fps = FPS

## Z rotation (horizontal orbit) - speed ramp pattern
## SLOW on each face, FAST whip between
kf_z = [
    (1,   0),      # front start
    (30,  10),     # slow drift on front
    (45,  90),     # FAST whip to right
    (75,  100),    # slow on right
    (90,  180),    # FAST whip to back
    (120, 190),    # slow on back
    (135, 270),    # FAST whip to left
    (165, 280),    # slow on left
    (180, 330),    # FAST whip toward front
    (210, 340),    # slow near bottom
    (225, 355),    # FAST settle
    (240, 360),    # back to front
]

## X rotation (vertical tilt - over/under)
kf_x = [
    (1,   0),
    (30,  0),
    (75,  15),     # slight tilt on right
    (120, 0),      # level on back
    (135, -20),    # tilt down on left
    (165, -45),    # going under
    (180, -60),    # under/bottom view
    (210, -30),    # coming back up
    (240, 0),      # level again
]

for f, d in kf_z:
    tgt.rotation_euler[2] = math.radians(d)
    tgt.keyframe_insert(data_path='rotation_euler', index=2, frame=f)

for f, d in kf_x:
    tgt.rotation_euler[0] = math.radians(d)
    tgt.keyframe_insert(data_path='rotation_euler', index=0, frame=f)

## BEZIER interpolation for speed ramp easing
action = tgt.animation_data.action
strip = action.layers[0].strips[0]
for cb in strip.channelbags:
    for fc in cb.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
            kp.easing = 'AUTO'
```

#### Step 3: Render + Encode

```bash
ffmpeg -y -framerate 24 \
  -i "~/Desktop/Blender Videos/dynamic_loop_frames/%04d.png" \
  -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le \
  "~/Desktop/Blender Videos/dynamic_full_loop.mov"
```

### Notes

- This animation is longer (10s) due to the speed ramps needing time to breathe
- If Blender freezes on large meshes, encode whatever frames completed — partial render is usable
- The speed ramp effect comes from BEZIER curves with uneven keyframe spacing


---

## ◆ perfect-loop  _(source: kevinbadi)_

> Seamless looping 360-degree turntable. First and last frames match perfectly for infinite loop playback.

### Perfect Loop Camera Animation

A seamless 360-degree turntable where the last frame connects perfectly to the first frame, creating an infinite loop. Ideal for website backgrounds, social media, and product page embeds.

### When to Use

- User wants a "looping" or "seamless" animation
- User says "perfect loop", "infinite loop", "GIF", "looping turntable"
- Website product embed, social media loop

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `duration` | `5` | Video length in seconds |
| `fps` | `24` | Frames per second |
| `camera_distance` | `4.0` | Distance from object |
| `camera_height` | `2.0` | Camera height |
| `camera_lens` | `50` | Focal length |

### Flow

#### Step 1: Set Up Camera Rig

```python
import bpy, math

bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
tgt = bpy.context.active_object
tgt.name = 'PerfectLoopTarget'

bpy.ops.object.camera_add(location=(0, -CAMERA_DISTANCE, CAMERA_HEIGHT))
cam = bpy.context.active_object
cam.name = 'PerfectLoopCam'
cam.data.lens = CAMERA_LENS

trk = cam.constraints.new(type='TRACK_TO')
trk.target = tgt
trk.track_axis = 'TRACK_NEGATIVE_Z'
trk.up_axis = 'UP_Y'

bpy.ops.object.select_all(action='DESELECT')
cam.select_set(True)
tgt.select_set(True)
bpy.context.view_layer.objects.active = tgt
bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

bpy.context.scene.camera = cam
```

#### Step 2: Animate Seamless Loop

**Critical**: Keyframe 360 degrees at frame N+1 (one past the last rendered frame). This way frame N and frame 1 are adjacent in the loop, not duplicated.

```python
TOTAL_FRAMES = DURATION * FPS  # 120

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = TOTAL_FRAMES  # render 1-120
scene.render.fps = FPS

tgt.rotation_euler = (0, 0, 0)
tgt.keyframe_insert(data_path='rotation_euler', frame=1)

## 360 at frame 121 — frame 121 is NOT rendered, but ensures
## frame 120 is one step before frame 1, creating seamless loop
tgt.rotation_euler = (0, 0, math.radians(360))
tgt.keyframe_insert(data_path='rotation_euler', frame=TOTAL_FRAMES + 1)

## LINEAR interpolation is CRITICAL for perfect loop
action = tgt.animation_data.action
strip = action.layers[0].strips[0]
for cb in strip.channelbags:
    for fc in cb.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
```

#### Step 3: Render + Encode

```bash
ffmpeg -y -framerate 24 \
  -i "~/Desktop/Blender Videos/perfect_loop_frames/%04d.png" \
  -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le \
  "~/Desktop/Blender Videos/perfect_loop.mov"
```

### Critical Notes

- **LINEAR interpolation only** — BEZIER will cause the loop to stutter at the seam
- **Keyframe at N+1**: Place the 360-degree keyframe one frame PAST the render range
- **No camera movement**: Camera distance, height, and lens must be static (no keyframes on these)
- **Verify loop**: Play the video on repeat to confirm seamless transition
- Good for encoding to looping formats: GIF, WebM, or MP4 with `-loop 0`


---

## ◆ product-polish  _(source: kevinbadi)_

> Import a 3D model (GLB/GLTF) into Blender and apply a sleek, glossy product-shot finish with studio lighting. Trigger when asked to polish a 3D model, make a Meshy AI model look shiny, apply product lighting in Blender, or prepare a 3D asset for product shots.

## Blender Product Polish

Takes a raw 3D model file (typically exported from Meshy AI) and transforms it into a polished, product-shot-ready scene in Blender via the Blender MCP addon.

### Prerequisites

- **Blender** (5.x+) running with the **Blender MCP addon** active on port 9876
- A `.glb` or `.gltf` file to import

### How to Run

```bash
node scripts/node/blender-product-polish.js --file "/path/to/model.glb"
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--file` | Path to the GLB/GLTF file to import | **required** |
| `--port` | Blender MCP port | `9876` |
| `--preset` | Lighting preset: `studio`, `dramatic`, `soft` | `studio` |
| `--roughness` | Surface roughness (0 = mirror, 1 = matte) | `0.02` |
| `--coat` | Clearcoat weight (0-1) | `1.0` |
| `--transmission` | Glass transmission (0-1) | `0.05` |
| `--no-clean` | Keep existing scene objects | `false` |

### What It Does

1. **Clears the scene** (removes default cube, lights, camera)
2. **Imports the GLB/GLTF** model
3. **Strips noisy normal/roughness maps** from Meshy AI exports (these cause dotty reflections)
4. **Applies a glass-like material** — ultra-low roughness, full clearcoat, high IOR
5. **Adds 4-point studio lighting** — key, fill, rim, and bounce lights
6. **Switches to EEVEE with ray tracing** for smooth real-time reflections (no pixelation during camera movement)
7. **Frames the viewport** on the imported model

### Lighting Presets

- **studio** (default): Balanced 4-point setup. Key (350W), Fill (250W), Rim (250W), Bounce (100W). Clean product photography look.
- **dramatic**: Strong key + rim, minimal fill. High contrast, moody.
- **soft**: Even lighting from all sides. Minimal shadows, airy feel.

### Notes

- Meshy AI exports often include normal maps and roughness textures that look pixelated/dotty under strong lighting. This skill disconnects those and uses flat material values instead.
- The skill uses EEVEE (not Cycles) to avoid progressive sampling noise during viewport navigation.
- After running, you can orbit freely in Blender without pixelation.
