# Characters, clothing & facial shape keys

> Fused guide. Script paths like `scripts/x.py` are relative to the **ai-blender-animation-skill skill root**; all Python helpers live in one flat `scripts/` folder (shared `_bpyx.py`). Node helpers are in `scripts/node/`. Where two sources disagree, prefer the Blender 5.x rules in SKILL.md.

Sections: `character-artist`, `character-archetypes`, `blender-clothing`, `blender-facial-shapekeys`


---

## ◆ character-artist  _(source: arjun988)_

> AAA character modeling for human anatomy, stylization, facial topology, clothing, hair, and animation-ready meshes. Use for game characters, facial expressions, and production character assets in Blender via MCP.

## Character Artist

Production character modeling with animation-ready topology. Anatomy-accurate or intentionally stylized.

### When to Use

- Human/humanoid character creation
- Facial topology for expressions
- Clothing and accessory modeling
- Hair card systems or stylized hair
- Character proportion and stylization

### Workflow

```
Reference → Proportion Blockout → Body Forms → Limb Connection
    → Facial Features → Edge Loop Planning → Detail Pass
    → Clothing (separate mesh) → UV Handoff → Rig Handoff
```

### Proportion Standards

| Type | Head Units | Notes |
|------|------------|-------|
| Realistic adult | 7.5–8 heads | Hero characters |
| Stylized | 4–6 heads | Exaggerated features |
| Heroic | 8–9 heads | Action games |

Always block proportions before detail.

### Edge Loop Strategy

Critical loop locations:
- Eyes: concentric loops for blink/expression
- Mouth: 3-loop minimum for lip deformation
- Jaw: loop following jaw line for open/close
- Shoulders: deltoid loop for arm raise
- Elbows/knees: 3-loop pinching pattern
- Hips: loop for leg spread

See `../refs/character-artist/facial-topology.md` for face-specific loops.

### Facial Structure

- Eye socket: recessed; brow ridge defined
- Nose: bridge width matches inner eye distance (realistic)
- Mouth: lower lip fuller than upper (realistic)
- Ear: aligns eye brow to nose base
- Skull underlying forms visible in stylization

### Clothing Workflow

1. Model body first (or use mannequin)
2. Duplicate body faces for clothing base
3. Solidify/extrude for cloth thickness
4. Separate mesh: `SM_Char_[Name]_Body`, `SM_Char_[Name]_Cloth_[Piece]`
5. Cloth does NOT share UVs with body
6. Weight paint transfers from body (via rigging skill)

### Hair Approaches

| Method | Use Case | Skill |
|--------|----------|-------|
| Hair cards | Game-realistic | uv-workflow + texture-workflow |
| Strand curves | Cinematic | particle/curve systems |
| Stylized mesh | Lowpoly/stylized | blender-modeler |
| Sculpted | Hero bake | sculpting → retopology |

### Animation-Ready Requirements

- Quad-dominant topology on deformation zones
- No poles on primary deformation areas (relocate to hidden zones)
- Even edge length in face/neck/joints
- Separate objects for swap-able parts (head, hands, gear)

### MCP Integration

1. Create base mannequin/blockout via MCP
2. Build body with mirror modifier via MCP
3. Query topology (face count, edge flow) at checkpoints
4. Separate clothing meshes via MCP
5. Organize character collection hierarchy

### Constraints

#### MUST DO
- Establish proportions before facial detail
- Plan edge loops for planned deformations
- Separate clothing/accessories as unique meshes
- Match style skill direction (stylized vs realistic)
- Validate topology before rigging handoff

#### MUST NOT DO
- Triangles on primary deformation surfaces
- Poles at corner of mouth or inner eye
- Single mesh for body + hard surface armor (separate)
- Skip reference for facial likeness work
- Over-poly face before LOD planning

### Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Facial topology | `../refs/character-artist/facial-topology.md` | Face modeling |
| Body proportions | `../refs/character-artist/body-proportions.md` | Blockout |
| Pipeline | `../refs/shared/asset-pipeline.md` | Phase context |

### Style Integration

| Style | Adjustment |
|-------|------------|
| realistic-style | Full anatomy; 8-head proportion |
| stylized-style | Exaggerated features; 4–5 heads |
| lowpoly-style | Minimal loops; painted detail |
| horror-style | Uncanny proportions; asymmetry |


---

## ◆ character-archetypes  _(source: arjun988)_

> Character archetype art direction for Blender covering fantasy races, horror creatures, roles (knight, assassin, detective), and body types (mecha, android, chibi, etc.).

## Character Archetypes

Use this skill to lock silhouette, materials, and proportion language for a role/race before modeling.

### Load refs for family
Fantasy ancestries · Horror undead/monsters · Sci-fi bodytypes · Role kits (knight, ninja, detective, etc.)


---

## ◆ blender-clothing  _(source: el4cteo)_

> Game clothing in Blender 5.3 - garments from body regions (ease offset, thickness), skin-weight transfer, hiding covered body faces, cloth-sim draping for folds, body-morph shape keys on garments, layered clothing, pose-aware poke-through checks, sim-to-game-mesh cleanup. Use for shirts, pants, armor, outfits, layered or swappable clothing.

## Clothing

The execution model is in `blender-core` (→ SKILL.md). The rig and weights are in `blender-character-rigging` (→ guides/11-rigging-animation.md), classic cloth settings in `blender-simulation` (→ guides/12-simulation-vfx-weather.md), and Roblox layered clothing cages in `blender-export-pipelines` (→ guides/16-export-engines.md) (../refs/blender-clothing/roblox.md).

### One call each
```
scripts/garment.py -- --body Body --group Torso --name Shirt --hide-body
scripts/garment.py -- --body Body --zmin 0.45 --zmax 1.05 --name Pants --offset 0.01 --drape 40 --morphs
scripts/garment.py -- --body Body --group Torso --name Armor --offset 0.02 --thickness 0.008
scripts/garment.py -- --check Shirt --body Body          # pose the rig first: checks the current pose
```

### How pros build game clothing
1. **Shape**: start from the body (extract + offset) for fitted clothes, or from flat patterns sewn by cloth sim (Marvelous Designer or Blender cloth with sewing springs) for loose ones. Simulate on the body in its **rest pose** (A/T).
2. **Game mesh**: retopo the high/sim result to clean, even quads with loops at the joints (elbows, knees, shoulders get 3 loops), then UV it. Bake folds into normal maps (`blender-texture-baking` (→ guides/08-materials-texturing-baking.md)) so the low mesh stays light.
3. **Skin**: copy weights from the body (same bones, same influences), clean them (limit 4, normalize, drop < 0.001), then blend toward smoother weights only on loose parts (skirts, coats) and add extra bones for those.
4. **Hide what's covered**: delete body faces under the garment (save tris, stop poke-through) or mask them per outfit. Keep one ring of skin under cuffs and collars.
5. **Verify in motion**: stress poses (`blender-character-rigging` (→ guides/11-rigging-animation.md) `stress_poses.py`), then `--check` in each. Fix by easing (offset), smoothing the body there, weight tweaks, or hiding.

### garment.py
- Region: `--group` (body vertex group, weight > 0.5) or a world `--zmin/--zmax` band. The faces are copied in world space and pushed out along the vertex normals by `--offset` (ease: 5–10 mm fitted cotton, 10–20 mm jackets, 15–30 mm armor). Then `Solidify` adds `--thickness` (2–4 mm fabric, 5–10 mm leather/armor), growing outward. UVs carry over from the body.
- Weights: Data Transfer (`POLYINTERP_NEAREST`, all groups by name), applied, limited to `--max-influences`, normalized and cleaned. The body's Armature modifier is added and parented to the rig.
- `--hide-body`: `Hidden_<name>` vertex group (the region shrunk by one ring) + an inverted Mask modifier on the body. Swappable outfits toggle masks. For export, delete those faces on a body copy instead.
- `--drape N`: classic cloth (cotton-ish: mass 0.15, tension 15, bending 0.5, quality 8). The top 8% is pinned, the body collides at 3 mm, it settles N frames, then the result is applied. That gives gravity folds on loose areas. Use 30–60 frames.
- `--morphs`: for each body shape key, a same-named garment shape key, via Surface Deform bound in the rest pose and applied as a shape key per morph. Engines drive body and garment keys together (fat/thin, muscle, breathing). Measured: a 30% body morph pokes through 346 verts. With the matching garment key, 0.
- **Poke check** (also run at the end of every build): casts along each body vertex normal. If the garment is hit inward before outward (or sits < 0.5 mm away), it's poke-through. Verts that hit no garment within 0.1 m aren't covered and are ignored. It reports `covered_verts`, `poke_verts` and `poke_max_m`, uses the **evaluated** pose, and respects the body masks.

### Layered clothing
- Order from the skin out: underwear/base → shirt → vest → jacket → armor. Each layer offsets from the one below (run `garment.py --body Shirt` for a vest over the shirt) and copies weights from the body, not from the layer below.
- Interpenetration between layers in motion usually comes from mismatched weights. Copying all layers from the same body keeps them moving together.
- Roblox layered clothing needs `<Name>_InnerCage` + `<Name>_OuterCage` built from Roblox's template cages (same vert order/UVs). Other engines (UE Mutable/Unity) blend shape keys or use body-hiding masks. Same principle.

### Gotchas
- `shape_key_add()` creates keys at value 1.0 (measured). Set `.value = 0` when authoring morphs from Python.
- Surface Deform for **morphs only**: if left live together with an Armature modifier, the pose is applied twice. `--morphs` removes it after baking the keys.
- Apply the body's scale before building. Offsets and thickness are in meters.
- Cloth sims need the body's collision mesh at a modest resolution. Decimate a proxy for the collision if the body is > 50k verts.
- Run `blender-asset-qa` (→ guides/17-qa-review.md) on the final garment (z-fighting with the body, floating parts, normals) and check its tris against `blender-game-optimization` (→ guides/15-optimization-lod-collision.md) budgets.


---

## ◆ blender-facial-shapekeys  _(source: el4cteo)_

> Facial rigs and shape keys in Blender 5.3 - ARKit 52 blendshapes, visemes for lip-sync, sculpting expressions, splitting symmetric shapes into Left/Right, mirroring, corrective and combination shapes, drivers and control rigs, bone+blendshape hybrids, export to engines (Unity, Unreal, Roblox dynamic heads, VRM/web). Use for faces, expressions, lip-sync, or any shape-key work.

## Facial Rig & Shape Keys

The execution model is in `blender-core` (→ SKILL.md). The body rig is in `blender-character-rigging` (→ guides/11-rigging-animation.md).

### Choose the approach
| Approach | Use | Notes |
|---|---|---|
| **Blendshapes (ARKit 52)** | games, VTubers, mocap (iPhone/Live Link Face), web/VRM | the industry interchange set; each shape is sculpted |
| **Bones** (jaw, eyes, lids, brows, lips) | stylized, low memory, mobile | jaw + eyes as bones are almost always right |
| **Hybrid** | most production game heads | jaw/eye/tongue bones + blendshapes for everything soft |
| **Rigify face** (`human` metarig) | film-style keyframe animation inside Blender | 100+ face bones, heavy for engines |

### Procedure (blendshapes)
1. The head mesh needs clean loops around the eyes and mouth (`blender-retopology-uv` (→ guides/07-retopology-uv.md)), with eyes, teeth and tongue as separate objects parented or weighted to bones.
2. `scripts/shapekeys.py -- --mesh Head --create arkit` (or `--create visemes` for the 15 Oculus visemes) creates empty, correctly named keys.
3. Sculpt each key (live: sculpt mode on the active key, `use_shape_key_edit_mode`). Symmetric expressions can be sculpted once, then `--split eyeBlink` gives `eyeBlinkLeft/Right` with a soft blend across X=0 (`--falloff` m).
4. `--mirror browDownLeft` builds `browDownRight` (topology-independent mirror).
5. `--report` lists unsculpted keys, the max offset per key, and missing ARKit names. A shape is done only when every key moves and nothing is left over.
6. Optional: `--drivers FaceCtrl` adds a controller with 0–1 custom properties driving each key, for keyframing in Blender.
7. Check the extremes and **combinations** (jawOpen + mouthSmile, eyeBlink + eyeSquint) with `look`. Fix them with corrective combination keys driven by the product of two keys.

### Shape key rules
- Shapes are **deltas from Basis**. Never change the Basis topology after creating keys (adding or removing verts destroys every key).
- One action per key. No head or neck movement inside face keys (bones do that). Keep eyelids sliding over the eye surface, not through it (check with `blender-asset-qa` (→ guides/17-qa-review.md) zfighting on lid/eye).
- Range 0–1. `slider_max` can be raised for exaggeration, but engines clamp to 0–1.
- Relative keys (`use_relative=True`, the default) are the only kind that exports.
- Name exactly per spec (case-sensitive): `eyeBlinkLeft`, not `EyeBlink_L`. Engines map by name.
- Keys on meshes with Subdivision: sculpt at level 0, and keep the subdivision modifier **after** the shape keys (they're evaluated first anyway).
- Applying modifiers on a mesh with shape keys fails. Use `modifier_apply_as_shapekey` for deform modifiers, or apply them before creating keys.

### Correctives and combination shapes
- Corrective for a bone pose: sculpt in the posed state, then drive with a `TRANSFORMS` variable (`ROT_X`, `LOCAL_SPACE`, mapped to 0–1).
- Combination: key `jawOpen_mouthSmile` with driver `SCRIPTED` expression `a*b`, from the two key values (`SINGLE_PROP` `key_blocks["jawOpen"].value`). Simple expressions don't need Python auto-run.

### Engine notes
- **Unity**: FBX blendshapes. In the Model importer, set Blend Shape Normals = Calculate (or Import if smoothing was exported). ARKit names map to the AR Foundation face-tracking samples.
- **Unreal**: morph targets ("Import Morph Targets"). Live Link Face / MetaHuman Animator use ARKit names, and the Pose Asset maps the curves. No leaf bones.
- **Roblox dynamic heads**: FACS-based poses with Roblox-specific names, authored as animation frames on a head rig (Creator Hub "Dynamic heads" spec). Build from the official Blender template. ARKit sculpts can be reused by renaming/mapping. Head ≤ 4,000 tris.
- **VRM / web (three-vrm, ReadyPlayerMe-style)**: ARKit 52 + visemes as glTF morph targets (`export_morph=True`). Keep the morph-normal export on only if shading needs it (it doubles the size).
- Drop unused keys before export. Every key costs memory per vertex (glTF sparse accessors help).

### Gotchas
- `ob.shape_key_add(from_mix=False)` copies the Basis. `from_mix=True` bakes the current mix (useful for combos, dangerous by accident).
- `shape_key_mirror(use_topology=False)` needs a mesh symmetric on X. Run it on the **active** key (the script handles this).
- Driver variables on shape keys use the Key ID (`ob.data.shape_keys`), not the mesh: `fc = kb.driver_add("value")`.
