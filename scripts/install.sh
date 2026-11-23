#!/bin/sh
# Install ai-blender-animation-skill into ~/.claude/skills (Claude Code) and ~/.agents/skills (Codex, Cursor, Gemini CLI...)
set -e
SRC="$(cd "$(dirname "$0")/.." && pwd)/skills/ai-blender-animation-skill"
for d in "$HOME/.claude/skills" "$HOME/.agents/skills"; do
  mkdir -p "$d" && cp -R "$SRC" "$d/" && echo "Installed -> $d/ai-blender-animation-skill"
done
