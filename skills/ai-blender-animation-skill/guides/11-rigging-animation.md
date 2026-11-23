# Rigging & animation

> Fused guide. Script paths like `scripts/x.py` are relative to the **ai-blender-animation-skill skill root**; all Python helpers live in one flat `scripts/` folder (shared `_bpyx.py`). Node helpers are in `scripts/node/`. Where two sources disagree, prefer the Blender 5.x rules in SKILL.md.

Sections: `blender-character-rigging`, `rigging`, `blender-animation`, `animation`


---

## ◆ blender-character-rigging  _(source: el4cteo)_

> Character rigging in Blender 5.3 - Rigify metarig fit/generate, bone naming/roll/collections, DEF/MCH/control layers, IK/FK, robust skinning (heat + proxy fallback), weight-painting rules, correctives, engine game skeletons (Unity, Unreal, Roblox R15), rig validation and deformation stress tests. Use for armature, skinning or weights tasks.

## Character Rigging

The execution model is in `blender-core` (→ SKILL.md). Faces and shape keys are in `blender-facial-shapekeys` (→ guides/05-characters-clothing-face.md), animation in `blender-animation` (→ guides/11-rigging-animation.md).

### Pipeline (scripts chain; each returns JSON)
1. **Prepare the mesh**: scale applied, facing **-Y**, feet at Z=0, centered on X=0, symmetric, in T- or A-pose (A-pose 30–45° deforms shoulders better). Run `blender-asset-qa` (→ guides/17-qa-review.md) first.
2. **Metarig**: `scripts/rigify_build.py -- --add basic_human --fit Body` (`human` adds a full face rig; for games use `--no-face` + shape keys).
3. **Place the joints** (the fit only scales). Edit bones in X-ray against the mesh: joints sit at the **pivot of rotation** (inside the volume, not on the surface). The elbow and knee need a slight bend toward their natural direction (elbow back, knee forward) so the IK solves the right way. Symmetrize: `bpy.ops.armature.symmetrize()`. Check with `look` (`shading="xray"`).
4. **Generate**: `--metarig META_Body --generate` gives `RIG_Body` (control rig: FK/IK, IK/FK snapping, tweak bones, bone collections).
5. **Skin**: `scripts/bind_mesh.py -- --armature RIG_Body --meshes Body`. It uses heat weights, switches to the voxel-proxy transfer automatically when heat fails (non-manifold, kitbashed or AI meshes), then cleans to 4 influences and normalizes.
6. **Stress test**: `scripts/stress_poses.py -- --armature RIG_Body`, then `look(mode="frames", frames=[1,10,20,30,40,50])`. Fix collapsing elbows, candy-wrapped forearms, a sunken shoulder or a hip crease (below).
7. **Engine skeleton**: `rigify_build.py -- --rig RIG_Body --game-skeleton` gives `GAME_RIG_Body` = `root` + DEF bones in a clean hierarchy, with `DEF-` stripped, constrained to the control rig and with the meshes re-targeted. Animate with the control rig, then bake to the game skeleton and export it (`blender-animation` (→ guides/11-rigging-animation.md) → `blender-export-pipelines` (→ guides/16-export-engines.md)).
8. **Validate**: `scripts/rig_check.py -- --armature GAME_RIG_Body --profile unity|unreal|roblox [--fix]`.

### Bone rules
- **Layers of a production rig**: `DEF` (deforming, the only ones exported), `ORG` (original metarig copy), `MCH` (mechanism helpers), controls (what animators touch). Never weight to control/MCH bones.
- **Naming**: `.L`/`.R` suffixes (mirror tools, Rigify and `rig_check` depend on them). Unique, ASCII. Bone collections (`arm.collections.new("FK")`, `bcoll.assign(bone)`) replace the old bone layers.
- **Roll**: consistent local axes. Y points down the bone; recalc with `armature.calculate_roll(type="GLOBAL_POS_Z")` for limbs, or per chain. Mirrored bones must have mirrored roll (`rig_check` flags this).
- **Chains**: connected parent→child for limbs. Spine 3–5 bones, neck 1–2. Twist bones on the forearm and upper arm (Rigify's `.001` segments) prevent candy-wrapping.
- The root bone sits at the origin, Y-forward, carries no weights, and is used for root motion.
- **Scale**: armature object scale 1, rotation 0. Apply before skinning. Non-uniform bone scale animation breaks engines.

### Weight painting rules (what pros check)
- ≤ 4 influences per vertex (mobile/Roblox), ≤ 8 on PC if the engine supports it. Always normalized. Weights below 0.01 removed.
- **Smooth falloff across joints**: a 50/50 blend at the joint line, fading over ~1–2 edge loops. A hard 1/0 cut shows a crease; too wide gives rubbery limbs.
- **Elbows/knees**: weight the outer side to the upper bone longer so the joint keeps volume. Add a helper/corrective bone or corrective shape for sharp bends.
- **Shoulders**: blend the clavicle, upper arm and spine. Test arms raised above the head (stress frame 10).
- **Hips**: the thigh-pelvis blend in front stays tight (crease) and soft at the back (glutes).
- **Head/neck**: rigid head (100% head bone above the jawline), smooth neck blend. Props (helmets, armor plates) get 100% weight to a single bone, so they stay rigid with no stretching.
- **Mirror**: paint one side, then `object.vertex_group_mirror(all_groups=True, flip_group_names=True, use_topology=False)`, or work with X-mirror on.
- **Tools** (live): Weight Paint mode with auto-normalize on (5.3 default, with Multi-Paint and Mirror Vertex Groups; brushes `Add Weight`/`Set Weight`, plus automasking), the gradient tool, Smooth (`vertex_group_smooth`), Levels, and `object.data_transfer` from a good mesh (clothing gets its weights from the body).

### Correctives (beyond weights)
Corrective shape keys driven by bone rotation fix elbows, knees and shoulders in hero rigs. Sculpt the fix in the posed state (`modifier_apply_as_shapekey` or the Corrective Shape Keys add-on approach), then drive the key value from the bone's local rotation (driver `TRANSFORMS` var `ROT_X` in `LOCAL_SPACE`, mapped from 0 at rest to 1 at full bend). Games: correctives export as blendshapes. Drive them in the engine (UE Pose Driver / Unity script) or bake them into the animation.

### Engine skeleton specifics
- **Unity Humanoid**: Hips → Spine → Chest → Neck → Head, plus limbs. The game skeleton maps automatically (`rig_check --profile unity` shows the mapping). T-pose bind pose recommended.
- **Unreal**: retarget to the UE5 Mannequin with IK Retargeter. Matching names (`pelvis`, `spine_01`, `thigh_l`...) speeds up chain mapping (`--profile unreal` lists the gaps). No leaf bones.
- **Roblox R15**: a fixed hierarchy and names (`LowerTorso`, `UpperTorso`, `LeftUpperArm`...), `Root > HumanoidRootNode > LowerTorso`, no weights on Root, ≤ 4 influences. Build it manually or from Roblox's Blender template rather than Rigify. Details are in `blender-export-pipelines/references/roblox.md`.

### Gotchas
- `rigify_generate` needs the metarig **selected and active** (`temp_override` isn't enough). The scripts handle this.
- "Bone Heat Weighting: failed to find solution" comes from non-manifold, intersecting parts or tiny scale. `bind_mesh.py` falls back to proxy. Fix the scale first.
- Meshes parented with "Keep Transform" but with unapplied scale get a double transform. Apply the scale before parenting.
- Modifier order: Armature should come **after** shape-key-like deforms and **before** Subdivision/Corrective Smooth (Corrective Smooth after Armature reduces collapsing).
- 5.0: `bone.select` is gone. Use `pose_bone.select` or `edit_bone.select`. `bone.hide` affects edit bones too.


---

## ◆ rigging  _(source: arjun988)_

> Production rigging in Blender with armatures, IK/FK, constraints, weight painting, mechanical rigs, facial rigs, and drivers. Use before animation on deforming assets via MCP.

## Rigging

Functional rigs supporting intended motion. Clean deformation. Engine-compatible bone hierarchies.

### When to Use

- Character/creature deformation rigs
- Mechanical constraint rigs
- Facial expression rigs
- Prop rigs (doors, vehicles, weapons)
- Before any animation work

### Workflow

```
Skeleton Design → Bone Placement → Hierarchy → Constraints/IK
    → Weight Painting → Deformation Test → Export Prep
```

### Armature Naming

Prefix: `ARM_[AssetName]`
Bones: `[side]_[region]_[name]` — e.g., `L_arm_upper`, `spine_01`, `jaw`

### Bone Hierarchy

```
ARM_Character
├── root
├── spine_01 → spine_02 → spine_03
│   ├── L_clavicle → L_arm_upper → L_arm_lower → L_hand
│   └── R_clavicle → R_arm_upper → R_arm_lower → R_hand
├── L_leg_upper → L_leg_lower → L_foot → L_toe
└── R_leg_upper → R_leg_lower → R_foot → R_toe
```

### IK vs FK

| Use IK | Use FK |
|--------|--------|
| Legs (ground contact) | Spine (flexible arc) |
| Arms (hand placement) | Shoulder overlap |
| Feet planting | Finger detail |
| Mechanical reach | Whip/tail motion |

Standard: IK legs, FK spine; switchable arms for game characters.

### Constraints

| Constraint | Use |
|------------|-----|
| IK | Limb positioning |
| Copy Rotation | Mechanical sync |
| Limit Rotation | Joint ranges |
| Stretch To | Tentacles, pistons |
| Child Of | Weapon attach/detach |
| Shrinkwrap | Ground contact (use carefully) |

### Weight Painting

```
1. Automatic weights as starting point only
2. Clean weights: normalize per vertex (max 4 influences)
3. Smooth problematic areas (shoulders, hips)
4. Test extreme poses: T-pose, arms up, crouch, jaw open
5. Gradient weights at joints — no hard 1.0/0.0 at bend center
```

### Mechanical Rigs

- Empty objects as control handles
- Constraints instead of weight painting
- Hinge limits match real joint ranges
- Parent hierarchy mirrors mechanical assembly

### Facial Rigs

| Approach | Use Case |
|----------|----------|
| Bone-based | Game characters |
| Shape keys | Cinematics, dialog |
| Hybrid | Hero game characters |

Minimum game facial: jaw open, blink L/R, brow up/down.

### Drivers

- Gear rotation sync
- Auto eyelid blink
- Weapon reload mechanism
- Procedural antenna/wire motion

### MCP Integration

1. Create armature via MCP
2. Parent mesh with automatic weights via MCP
3. Query bone count and hierarchy
4. Validate weight groups via MCP if supported
5. Export armature with mesh via export-pipeline

### Deformation Test Poses

- T-pose / A-pose (bind pose)
- Arms fully raised
- Deep crouch
- Neck rotation extremes
- Jaw wide open (characters)

### Constraints

#### MUST DO
- Rig after retopology complete
- Name bones consistently
- Limit bone influences to 4 per vertex (game engines)
- Test deformation at extremes before animation
- Document control scheme for animators

#### MUST NOT DO
- Auto weights without cleanup (hero assets)
- Scale bones in bind pose
- Rig before topology validated
- Skip IK pole targets on limbs
- Mix multiple root bones without documentation

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Humanoid rig | `../refs/rigging/humanoid-rig.md` | Characters |
| Mechanical rig | `../refs/rigging/mechanical-rig.md` | Props, vehicles |


---

## ◆ blender-animation  _(source: el4cteo)_

> Animation in Blender 5.3 - slotted/layered actions and the channelbag API, Python keyframing, F-curves, game loops with pop/hitch checks, NLA clips, pose library, mocap/BVH/Mixamo retargeting with auto bone maps, baking control rigs to export skeletons, root motion, per-clip export. Use for any keyframe, action, NLA, mocap, or animation-export task.

## Animation

The execution model is in `blender-core` (→ SKILL.md) (its `../refs/blender-core/bpy-patterns.md` has verified keyframe/driver snippets). Rigs are in `blender-character-rigging` (→ guides/11-rigging-animation.md).

### 5.x data model (what changed)
- An **Action** holds **slots** (one per animated ID) and **layers → strips → channelbags → F-curves**. A single action can animate several objects (e.g. a rig and its camera) through different slots.
- Assign: `ob.animation_data.action = act`, then make sure `ob.animation_data.action_slot` is set (picked automatically when a suitable slot exists; otherwise `act.slots.new(id_type="OBJECT", name=ob.name)`).
- F-curves: `cb = anim_utils.action_ensure_channelbag_for_slot(act, slot)`, then `cb.fcurves.ensure(path, index=i, group_name=...)`. `action.fcurves` **no longer exists**.
- The simplest route is still `pb.keyframe_insert("rotation_quaternion", frame=f)`, which creates the action, slot and channelbag.

### Workflow (keyframe animation, studio style)
1. **Blocking**: key poses on every channel (`CONSTANT` interpolation, `bpy.context.preferences.edit.keyframe_new_interpolation_type`) on golden frames (contact, down, passing, up for walks).
2. **Breakdowns**: add in-betweens that define arcs and spacing.
3. **Spline**: switch to `BEZIER`, fix spacing in the Graph Editor, and clean overshoot. Auto-clamped handles avoid overshoot.
4. **Polish**: offsets/overlap (follow-through on hair, tails, cloth bones), arcs, moving holds (never a perfectly frozen character), and contact stability (feet locked with IK).
5. **Review**: MCP `look(mode="frames", frame_count=8)` or a Workbench playblast (`blender-rendering` (→ guides/14-rendering-compositing.md)).

### Game animation rules
- **One action per clip**, named `<Rig>_<Clip>` or just `<Clip>`, with a fake user so it survives saving.
- **Loops**: first and last frames identical. Export frames 1..N and let the engine drop the duplicate, or exclude the last frame (UE/Unity "loop pose" options). An F-curve `CYCLES` modifier helps preview but **doesn't export**, so bake it. Verify with `scripts/loop_check.py -- --object RIG --action Walk [--root-motion root] [--fix]`: it reports pose **pops** (last ≠ first, per bone, in deg/m) and speed **hitches** across the seam, and `--fix` keys the first-frame values on the last frame (root travel is kept).
- **FPS**: author at 30 (or 24) and let engines resample. Set `scene.render.fps` before importing mocap.
- **Root motion**: the root bone carries the translation (and yaw). The hips keep the bob/sway. `scripts/bake_action.py --root-motion xy` moves the hips' ground motion to the root. In-place clips: the root stays at the origin.
- **Additive/overlay** clips (aim offsets, breathing) are exported as normal clips and marked additive in the engine.
- Keep the bone transform channels the engine expects. **Don't animate bone scale** unless the engine supports it (Roblox and many mobile pipelines don't).

### Bake control rig → export skeleton
```
scripts/bake_action.py -- --list
scripts/bake_action.py -- --source RIG_Body --target GAME_RIG_Body [--actions Walk Run] [--root-motion xy --hips spine]
```
This gives one baked action per clip (`GAME_RIG_Body|Walk`), cleaned, with fake users, plus one muted NLA track per clip (`CLIP_Walk`) so FBX (`bake_anim_use_nla_strips`/all actions) and glTF (`ACTIONS` mode) export every clip. The target's constraints are muted afterward so it plays the baked data; run `--follow` to drive it live again. Self-bake (IK/constraints → keys on the same rig): `--source X --target X`.

### Mocap and retargeting
- Import: `bpy.ops.import_anim.bvh(filepath=..., global_scale=0.01 if cm else 1, rotate_mode="NATIVE", update_scene_fps=True)`, `import_scene.fbx` (Mixamo, `automatic_bone_orientation=True`).
- Retarget: `scripts/retarget.py -- --source Mocap --target GAME_RIG [--map auto|map.json] [--in-place] [--name Walk]`. Each target bone gets the source bone's **world rotation change from rest** on its own rest orientation, so rolls, bone axes, Y-up/cm FBX object transforms and proportions don't matter. The hips travel is scaled by the hips-height ratio. Keys go straight into a new `TARGET|Name` action (quaternion, linear, fake user). Measured on a Mixamo-style rig (Y-up, 0.01 scale, rolled) → Rigify-named rig with 15% longer legs: 17 bones, < 0.1° error.
- The auto map understands Mixamo (`mixamorig:LeftUpLeg`), Rigify `DEF-`/`ORG-`, UE/Unity/BVH-style names, and spine chains of different lengths. Check it first with `--show-map` (`unmapped_key_parts` must be empty), and pass a JSON `{target: source}` for anything custom (fingers, props).
- **Rest poses must match** (T vs A matters most): pose the target's rest like the source's first. Then clean, add root motion, and export with `bake_action.py`.
- Clean mocap: decimate keys (`graph.decimate`, ratio 0.3–0.5), use an F-curve `SMOOTH` modifier or the Butterworth filter (`graph.butterworth_smooth`), and fix foot sliding with IK pins and then bake.
- Production retarget tools: Auto-Rig Pro (paid), Rokoko (free), and the engine-side retargeters (UE IK Retargeter, Unity Humanoid).

### NLA and pose library
- NLA: push actions down as strips (`track.strips.new(name, start, action)`) to layer/blend clips (blend type `REPLACE`/`ADD`/`COMBINE`), and use Tweak mode to edit. Strips need an action slot set when the action has several slots (`strip.action_slot`).
- The pose library (bundled `pose_library`) stores poses as **assets**: `poselib.create_pose_asset(pose_name=...)`, `poselib.apply_pose_asset` / `blend_pose_asset`. Use it for hand shapes, face poses, and a T/A rest pose.

### Shape keys and other properties
Any property can be keyed: `kb.keyframe_insert("value", frame=f)` (shape key), `mat.node_tree.nodes[...].inputs[...].keyframe_insert("default_value")` (materials, which engines usually ignore), custom props `ob.keyframe_insert('["prop"]')`.

### Gotchas
- `pb.matrix = ...` followed by `keyframe_insert` needs the right `scene.frame_set(f)` **first**, or an evaluation overwrites the pose.
- Connected bones (`use_connect`) can't translate. Hips/pelvis must be unconnected from the root.
- `bake_action` with visual keying reads **evaluated** poses, so constraints, IK and drivers are all captured. Mute the target's own constraints afterward (the script does), or they keep overriding the keys.
- Quaternion vs Euler: game bones should use `QUATERNION` (no gimbal lock, smooth slerp). Euler is fine for single-axis controls. Don't mix modes between keys. 5.3 converts existing animation: `pose_bone.convert_rotation_mode("QUATERNION", bake=False)` (also on objects) or `anim.rotation_mode_convert(mode=...)` for the selection.
- glTF sampling: `export_force_sampling` bakes every frame (the safe default). Non-linear F-curve modifiers and drivers only export when sampled.


---

## ◆ animation  _(source: arjun988)_

> Game-ready animation in Blender including walk/run/idle cycles, combat, mechanical animation, camera animation, constraints, Graph Editor, and NLA workflows via MCP.

## Animation

Game-ready motion with clean keyframes. Readable silhouettes in motion. Engine-compatible export.

### When to Use

- Character locomotion (walk, run, idle)
- Combat animations
- Mechanical/prop animation
- Camera animation
- Object animation with constraints

### Workflow

```
Reference → Blocking → Breakdown → Splining → Polish
    → Cycle Validation → NLA Strip → Export
```

### Locomotion Cycles

| Cycle | Key Poses | Frames (30fps) |
|-------|-----------|----------------|
| Walk | Contact, Down, Pass, Up × 2 | 24–32 |
| Run | Contact, Drive, Flight, Recovery | 16–24 |
| Idle | Breathe, weight shift, blink | 60–120 loop |

Naming: `AN_[Char]_[Action]_[Variant]`

### Animation Principles (Applied)

1. **Timing** — Weight through spacing
2. **Arcs** — Natural limb paths
3. **Overlap** — Secondary motion offset
4. **Anticipation** — Wind-up before action
5. **Exaggeration** — Style-dependent (see style skills)

### Mechanical Animation

- Use constraints over bone deformation
- Hinge: Limit Rotation constraint
- Pistons: Stretch-to or Copy Location
- Gears: Driver for synchronized rotation
- Doors: Empty pivot + rotation keyframes

### Graph Editor Workflow

```
1. Block stepped keys (Constant interpolation)
2. Splining: Bezier with auto handles
3. Ease: Weighted handles for acceleration
4. Cycle: Copy first/last frame; verify loop seam
5. Clean: Remove redundant keys
```

### NLA for Game Export

```
1. Action created and named per convention
2. Push down to NLA strip
3. Strip set to Repeat for cycles
4. Single strip active for export
5. Scale: 1.0; no NLA time remapping unless intentional
```

### Camera Animation

- Smooth Bezier interpolation always
- Avoid sudden direction changes
- Match focal length to subject scale
- Camera shake: noise modifier on location (subtle)

### MCP Integration

1. Insert keyframes via MCP if supported
2. Query action names and frame ranges
3. Validate bone/object animation data exists pre-export
4. Set frame range via MCP
5. Export animation with rig via export-pipeline

### Game-Ready Requirements

- [ ] Root motion decision documented (in-place vs root motion)
- [ ] Loop seam invisible (walk/idle/run)
- [ ] No bone scale keyframes (engine issues)
- [ ] Animation length matches engine state machine
- [ ] Facial animation on separate action layer if needed
- [ ] Frame rate: 30fps default (confirm project spec)

### Constraints

#### MUST DO
- Reference video for locomotion
- Block in stepped mode before splining
- Name actions `AN_` prefix
- Test cycle loop before export
- Match animation style to art direction

#### MUST NOT DO
- Linear interpolation on organic motion
- Scale keyframes on rig bones
- Over-animate idle (subtle is better)
- Export without action assigned to NLA
- Skip root motion documentation

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Walk cycle breakdown | `../refs/animation/walk-cycle.md` | Locomotion |
| Combat timing | `../refs/animation/combat-animation.md` | Action games |
