#!/usr/bin/env bash
# Rebuild the diorama + Clawd from the Blender scripts and compress them for the web.
#   BLENDER_PY=/path/to/python-with-bpy npm run world
# bpy (Blender as a Python module) needs Python 3.11:  uv venv -p 3.11 .bpy && uv pip install -p .bpy bpy
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${BLENDER_PY:-.bpy/bin/python}"
RAW="$(mktemp -d)"
trap 'rm -rf "$RAW"' EXIT

# ONLY=6 npm run world  -> rebuild a single region; NOBAKE=1 skips the Cycles lightmap bake
mkdir -p public/world/lm
if [ -n "${NOBAKE:-}" ]; then
  "$PY" blender/build_all.py "$RAW" public/world/world.json "${ONLY:--}"
else
  "$PY" blender/build_all.py "$RAW" public/world/world.json "${ONLY:--}" public/world/lm
fi
[ -n "${ONLY:-}" ] && [ "$ONLY" != "-" ] || "$PY" blender/clawd.py "$RAW/clawd.glb"
for f in "$RAW"/*.glb; do
  name="$(basename "$f")"
  npx --no-install gltf-transform optimize "$f" "public/world/$name" \
    --compress meshopt --texture-compress false --simplify false \
    --join false --flatten false --instance false --palette false --prune false >/dev/null
done
du -ch public/world/*.glb public/world/lm/*.webp | tail -1
# Path-traced postcards are slow (~1 min each on CPU), so they're a separate step:
#   npm run postcards
