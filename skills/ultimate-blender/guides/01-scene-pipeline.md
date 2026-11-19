# Scene setup, pipeline automation & add-ons

> Fused guide. Script paths like `scripts/x.py` are relative to the **ultimate-blender skill root**; all Python helpers live in one flat `scripts/` folder (shared `_bpyx.py`). Node helpers are in `scripts/node/`. Where two sources disagree, prefer the Blender 5.x rules in SKILL.md.

Sections: `blender-scene-setup`, `blender-pipeline-automation`, `blender-addon-development`


---

## ◆ blender-scene-setup  _(source: el4cteo)_

> Set up and audit Blender scenes the way studios do - units and real-world scale, collection layout, naming conventions (SM_/SK_/T_/M_), origins, linking vs appending, library overrides, asset libraries and catalogs, collection exporters, orphan/path cleanup. Use when starting a project, organizing a .blend, or before handoff/export.

## Scene Setup & Hygiene

The execution model and verification steps are in `blender-core` (→ SKILL.md).

### Procedure
1. Run `scripts/scene_audit.py` (add `--fix purge scale paths` only on files you own). It reports units, unapplied/negative scale, default names, objects in the scene root, missing images, orphans and far-off origins.
2. Set units: Metric, Unit Scale **1.0**, Length meters. Keep 1.0 even for Unreal/Roblox, because exporters handle the conversion (see `blender-export-pipelines` (→ guides/16-export-engines.md)).
3. Build the collection layout (below). Every object must be in a named collection, never the scene root.
4. Name everything with the conventions below. Rename after every duplicate or join so no `.001` suffixes remain.
5. Set origins: props at the bottom-center (they sit on the ground at Z=0), characters at world origin between the feet, doors/hinges at the pivot.
6. Apply rotation and scale on meshes (Ctrl+A). Keep location unless the asset should export at the origin.
7. Re-run the audit. It's done when `issues` is empty or every remaining issue is intentional and explained.

### Collection layout (one asset per .blend, or one collection per asset)
```
ASSET_Crate
├── Crate_high      # sculpt / subdiv source (exclude from export)
├── Crate_low       # game mesh(es) SM_Crate, SM_Crate_LOD1..
├── Crate_bake      # cages, bake helpers
├── Crate_collision # UCX_SM_Crate_00 (UE) / Crate-col (Godot)
└── Crate_ref       # reference images/blockout (hide_render)
```
Use **Collection Exporters** (4.2+) to define the export once per collection, then re-export with one call:
```python
with bpy.context.temp_override(collection=col):
    bpy.ops.collection.exporter_add(name="IO_FH_gltf2")
ex = col.exporters[-1]; ex.export_properties.filepath = "//export/SM_Crate.glb"
with bpy.context.temp_override(collection=col):
    bpy.ops.collection.exporter_export(index=len(col.exporters) - 1)
```
`bpy.ops.wm.collection_export_all()` re-runs every collection exporter. 5.3: glTF exporters set the origin with `collection_center_mode` (`WORLD_ORIGIN`, `CENTER_MASS`, `OBJECT_POSITION`, `INSTANCE_OFFSET`). Collections also get one **importer** (USD only, `collection.importer_add` / `importer_import`) whose settings are saved in the .blend.

### Naming conventions (Unreal-style, accepted by all engines)
| Type | Pattern | Example |
|---|---|---|
| Static mesh | `SM_<Name>[_LOD#]` | `SM_Crate_LOD1` |
| Skeletal mesh / rig | `SK_<Name>` / `RIG_<Name>` (armature object `Armature` or `root`) | `SK_Hero` |
| Material | `M_<Name>` / instance `MI_<Name>` | `M_Wood_Oak` |
| Texture | `T_<Name>_<Suffix>`: `_BC` base color, `_N` normal, `_ORM` (R=AO G=Rough B=Metal), `_E` emissive, `_M` mask | `T_Crate_ORM` |
| Collision | UE `UCX_<Mesh>_##`, Godot suffix `-col`/`-colonly`/`-convcolonly` | `UCX_SM_Crate_00` |
| Bones/sides | `.L`/`.R` suffix (Blender mirror tools depend on it) | `upper_arm.L` |
| Actions | `<Rig>_<Clip>` | `Hero_Run` |
Use ASCII only, no spaces, and PascalCase or snake_case consistently across the project.

### Real-world scale reference (meters)
Door 2.0–2.1 × 0.9 · ceiling 2.4–2.7 · table 0.75 · chair seat 0.45 · counter 0.9 · stair rise 0.18 / tread 0.28 · adult human 1.7–1.8 (eyes 1.6) · car 4.5 × 1.8 × 1.5. Roblox: 1 stud ≈ 0.28 m; default character ≈ 5 studs tall. Wrong scale breaks physics, lighting falloff, DOF and texel density, so check `ob.dimensions` first.

### Linking, appending, overrides
- **Append** (`libraries.load(link=False)`) makes a local copy. Use it for one-off reuse.
- **Link** (`link=True`) is read-only, updates from the source and is what pipelines use. To edit a linked collection, add a library override: `ob.override_hierarchy_create(scene, view_layer, do_fully_editable=False)`. Only overridable properties (transforms, pose, and anything marked overridable) can change.
- Keep library paths relative (`//`). Check `bpy.data.libraries` for broken paths.

### Asset libraries
- Mark: `ob.asset_mark(); ob.asset_generate_preview()`. Metadata goes in `ob.asset_data` (`author`, `description`, `license`, `tags.new("wood")`, `catalog_id`).
- Catalogs live in `blender_assets.cats.txt` at the library root, one line per catalog: `UUID:Path/Sub:Simple Name`.
- Register a library with `prefs.filepaths.asset_libraries.new(name=..., directory=...)`. 5.2+: remote libraries via `use_remote_url` + `remote_url`. In 5.2 `active_asset_library` indices are offset by 2 ("All", "Essentials").
- Import method per library: `LINK`, `APPEND`, `APPEND_REUSE` (default; reuses already-appended data).

### Hygiene rules
- Purge orphans before shipping (`bpy.data.orphans_purge(do_recursive=True)`). Use fake users only on purpose.
- Image paths: relative (`file.make_paths_relative`), or pack for single-file delivery (`file.pack_all`).
- Never ship multi-user mesh data that has an unapplied per-object scale. Instances are fine, but bake scale before export.
- Hide helpers with `hide_render=True` **and** exclude them from export collections; viewport hiding alone isn't enough.
- One active scene per file for delivery. Extra scenes confuse exporters (`use_active_scene`).


---

## ◆ blender-pipeline-automation  _(source: el4cteo)_

> Automate Blender 5.3 at scale - headless CLI flags, batch convert/inventory/run-any-skill-script over folders of .blend/.fbx/.glb/.obj/.usd, sharding, bpy pip module, library linking, path management, render-farm and CI patterns. Use for batch jobs, format conversion, library maintenance and pipeline tooling.

## Pipeline Automation

The execution model is in `blender-core` (→ SKILL.md) (`run_in_blender.py` finds Blender and prints only the JSON results).

### Batch one-liners
```
blender -b -P scripts/batch_process.py -- --in "assets/**/*.fbx" --op convert --to glb --out export/
blender -b -P scripts/batch_process.py -- --in library/ --op report                      # inventory JSON lines
blender -b -P scripts/batch_process.py -- --in "src/*.blend" --op script \
    --script ../scripts/qa_check.py --kwargs '{"profile":"game"}'       # QA a whole library
blender -b -P scripts/batch_process.py -- --in src/ --op script --script ../scripts/make_lods.py \
    --kwargs '{"rename":true}' --save-to processed/                                      # LODs for every file
```
Each file is streamed as one JSON line with `ok`, timing and results. Failures don't stop the batch, and the summary lists them. **Parallel**: start N processes with `--shard 0/N` … `--shard N-1/N` (Blender uses one core for Python, so processes scale with CPU/GPU count).

### Headless CLI essentials
| Flag | Meaning |
|---|---|
| `-b` | background, no UI. Put it **first** |
| `file.blend` | open before running scripts. Order matters: args run left to right |
| `-P script.py` / `--python-expr "..."` | run Python |
| `--python-exit-code 1` | non-zero exit if the script raises (CI) |
| `--factory-startup` | ignore user prefs/add-ons (reproducible). Bundled add-ons still load |
| `--addons rigify,io_scene_fbx` | enable specific add-ons |
| `-E CYCLES -o //out/#### -F PNG -s 1 -e 10 -a` / `-f 5` | render (`blender-rendering` (→ guides/14-rendering-compositing.md)) |
| `--command extension build/validate/install-file` | extension tooling (`blender-addon-development` (→ guides/01-scene-pipeline.md)) |
| `-- --my args` | everything after `--` goes to the script (`sys.argv[sys.argv.index("--")+1:]`) |
| `--log "*"`, `--debug-python` | debugging. 5.0 changed the log format, so don't regex progress lines |
Environment variables: `BLENDER_USER_SCRIPTS`, `BLENDER_USER_EXTENSIONS`, `BLENDER_SYSTEM_PYTHON`. Use `OCIO` for custom color configs.

### bpy as a Python module
`pip install bpy==5.3.*` (or `5.2.*` for the LTS) (Python 3.13, matching the Blender release) gives `import bpy` in plain Python, which is handy for pytest/CI/web services. It has no UI and no GPU module by default, and it's large (~300 MB). Version-lock it with the Blender you target. The `bpy` wheel and the CLI behave the same for data API work.

### Library patterns
- **Append/link**: `bpy.data.libraries.load(path, link=...)` (see `blender-core/references/bpy-patterns.md`). 5.2: `data_from.libraries` exposes nested library paths when loading.
- **Write a subset**: `bpy.data.libraries.write(path, {datablocks}, fake_user=True, path_remap="RELATIVE_ALL")` builds asset/library files from a session.
- **Find files**: `bpy.data.file_path_foreach(...)` (5.2 flags: `EXPAND_TOKENS` for UDIMs, `EXPAND_SEQUENCES`, `EXPAND_CACHES`), and `bpy.utils.blend_paths(absolute=True)` lists every external path.
- **Remap/relocate**: `bpy.ops.file.find_missing_files(directory=...)`, `make_paths_relative`, `pack_all`. Libraries: `lib.filepath = new; lib.reload()`.
- **Iterate every ID**: `bpy.data.all_ids` (5.2; order isn't stable in 5.3, so sort by name if output must be deterministic), and `bpy.data.orphans_purge(do_recursive=True)` for cleanup.

### Robustness rules
- One task per process where possible. Long Blender sessions leak (images, undo). `batch_process.py` reuses the process but resets with `read_factory_settings(use_empty=True)` / `open_mainfile`.
- Never write into the source folder by default. Use separate `--out`/`--save-to`, and write with `copy=True`.
- Make scripts idempotent: re-running replaces their own outputs (named prefixes, `exist_ok`).
- Log JSON, not prose: one object per file/job, so agents and CI can parse it cheaply.
- Pin the Blender version (5.2 LTS, or 5.3) for a project. Record `bpy.app.version_string` + hash (`bpy.app.build_hash`) in the outputs.
- Paths: `bpy.path.abspath("//x")` is relative to the **opened** .blend. In headless batches use absolute paths, or set them after `open_mainfile`.
- GPU in containers: Cycles CUDA/OptiX needs the NVIDIA container runtime. Otherwise use CPU. EEVEE needs a GPU/EGL even headless.

### CI recipe (GitHub Actions)
Download the Linux tarball (`https://download.blender.org/release/Blender5.3/blender-5.3.0-linux-x64.tar.xz`), cache it, then `blender -b --factory-startup --python-exit-code 1 -P tests/run_all.py`. This repo's `.github/workflows/ci.yml` is a working example.


---

## ◆ blender-addon-development  _(source: el4cteo)_

> Write Blender 5.3 add-ons as extensions - blender_manifest.toml, operators/panels/menus/property groups/preferences, bpy.props rules after 5.0, undo/redo, modal and timer patterns, gpu drawing (no bgl), bundling Python wheels, CLI validate/build/install, testing headless, extensions platform publishing. Use when creating or fixing a Blender add-on, tool, or UI.

## Add-on (Extension) Development

The execution model is in `blender-core` (→ SKILL.md). Start from `assets/addon_template/` (validated, built, and registered in CI): `blender_manifest.toml`, `__init__.py`, `operators.py`, `ui.py`.

### Procedure
1. Copy the template, then set `id` (lowercase_underscores, permanent), `name`, `tagline` (no trailing period, ≤ 64 chars), `maintainer`, `version` (semver), `license` (SPDX, GPL-3.0-or-later for code using bpy), and `blender_version_min = "4.2.0"` or higher if you use newer APIs (e.g. `"5.2.0"` for the GN `properties.inputs` API).
2. Write classes with the prefix convention `MYTOOL_OT_x` (operator), `_PT_` (panel), `_MT_` (menu), `_PG_` (property group), `_AP_` (preferences), `_UL_` (UI list). `bl_idname` for operators is `my_tool.verb_noun`.
3. Validate and build:
   ```
   blender --command extension validate ./my_tool
   blender --command extension build --source-dir ./my_tool --output-dir ./dist
   blender --command extension install-file -r user_default -e ./dist/my_tool-1.0.0.zip
   ```
4. Test headless: register the package in-process, call operators with `temp_override`, and assert on data (see `tests/test_addon.py` in this repo).

### Rules (extension-era, 5.x)
- **Relative imports only** (`from . import ops`). The package name is decided by Blender, so preferences use `bl_idname = __package__`.
- No `bl_info` (it's ignored for extensions). Everything goes in the manifest.
- **No network or file access at import/register time.** Declare `[permissions]` (`files`, `network`, `clipboard`, `camera`, `microphone`) with a reason. Check `bpy.app.online_access` before any network call.
- **Third-party Python packages**: ship `.whl` files in `./wheels/` and list them under `wheels = [...]`. Never `pip install` at runtime. Platform-specific wheels require `platforms = [...]`.
- **Properties (5.0+)**: `bpy.props` values are attributes, not dict entries (`scene["my_prop"]` no longer reaches them). For read-only props use `options={'READ_ONLY'}`. `get_transform`/`set_transform` adapt values while keeping storage. Register with `PointerProperty(type=PG)` on an ID type, and `del` it on unregister.
- **Operators**: `bl_options={"REGISTER","UNDO"}` for undo plus a redo panel. `poll()` guards the context. Return `{"FINISHED"}`/`{"CANCELLED"}`. `self.report({"WARNING"}, msg)` for user feedback. Don't call other operators in loops if a data API exists.
- **UI**: `layout.use_property_split = True` gives modern alignment. Panels in the N-panel use `bl_region_type="UI"` + `bl_category`. Append menu entries with `VIEW3D_MT_*.append(func)` and remove them on unregister.
- **Unregister** everything in reverse order (classes, props, menus, handlers, timers, keymaps, draw handlers). Leaks break reloading.
- **Drawing** (overlays): `gpu` module + `gpu_extras.batch`. `bgl` was removed in 5.0. Textures come from `gpu.texture.from_image(img)`. For scene-linear images use `draw_texture_2d(..., is_scene_linear_with_rec709_srgb_target=True)`.
- **Long tasks**: a modal operator with a timer (`wm.event_timer_add`), or `bpy.app.timers.register` with chunked work. Never block the UI for seconds.
- **Handlers**: decorate persistent ones with `@bpy.app.handlers.persistent`. Keep them cheap (they run every frame/depsgraph update).
- **Keymaps**: add them to `wm.keyconfigs.addon`, store `(km, kmi)` pairs, and remove them on unregister.
- **Translations / i18n**: `bpy.app.translations.register(__package__, dict)`.

### Publishing (extensions.blender.org)
The Blender ID account uploads the built zip. Requirements: a valid manifest, a GPL-compatible license, no obfuscated code, no bundled binaries without source, and permissions declared. Screenshots/README go on the website listing. Update with a higher `version`.

### Gotchas
- `context.scene` inside a draw function can be `None` in some editors. Guard it.
- Storing Blender data references (`bpy.types.ID`) in Python globals crashes after undo or file load. Store names or `session_uid`, and look them up again.
- `bpy.utils.register_class` fails if annotations use `=` instead of `:` for properties.
- 5.0 made several bundled modules private (`rna_info`, `bl_ui_utils`...). Don't import them.
- 5.1 no longer loads the user site-packages by default. Bundle wheels instead of relying on user installs.
- 5.2: `PreferencesFilePaths.active_asset_library` indices are offset (the "All"/"Essentials" entries come first). `UILayout.template_palette(color=)` is removed. New: `UILayout.link`, `UILayout.textbox`, `bpy.data.all_ids`, `Window.screenshot`.
- 5.3: `bpy.data.all_ids` order is an implementation detail. New: `UILayout.label_multiline()`, `auto_keymap=` on `invoke_popup`/`popover`, `window_manager.undo_stack` (read-only), `constraints.new(type, name=)`, `KDTree(n, dimensions=2)`, `gpu.types.GPUStorageBuf`, and bundled `OpenEXR`/`opentimelineio` modules. Vulkan is the default GPU backend on Windows/Linux, so test `gpu` drawing there.
