#!/bin/sh
# Install ultimate-blender into ~/.claude/skills (Claude Code) and ~/.agents/skills (Codex, Cursor, Gemini CLI...)
set -e
SRC="$(cd "$(dirname "$0")/.." && pwd)/skills/ultimate-blender"
for d in "$HOME/.claude/skills" "$HOME/.agents/skills"; do
  mkdir -p "$d" && cp -R "$SRC" "$d/" && echo "Installed -> $d/ultimate-blender"
done
