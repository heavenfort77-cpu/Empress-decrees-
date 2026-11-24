#!/bin/bash
# Batch 17a route proof (INT): KTX2 encode/decode round trip, meshopt GLB round trip, mutants. CI file: never on batches-3-5.
set -uo pipefail
R=$PWD; S=$R/stage; mkdir -p "$S/mutsrc"
echo "== tools"
URL=$(curl -fsSL https://api.github.com/repos/KhronosGroup/KTX-Software/releases/latest | python3 -c "import json,sys; a=json.load(sys.stdin)['assets']; print(next(x['browser_download_url'] for x in a if x['name'].endswith('Linux-x86_64.deb')))")
echo "KTX deb $URL"; curl -fsSL -o /tmp/ktx.deb "$URL" && sudo apt-get install -y -qq /tmp/ktx.deb >/dev/null 2>&1; toktx --version || echo "TOKTX MISSING"
mkdir -p /tmp/gt && (cd /tmp/gt && npm init -y >/dev/null && npm install --no-audit --no-fund @gltf-transform/cli@4 @gltf-transform/core@4 >/dev/null 2>&1); export GT=/tmp/gt/node_modules/.bin/gltf-transform; $GT --version || echo "GT MISSING"
cp art/tools/int17/mut_models.mjs /tmp/gt/ && (cd /tmp/gt && node mut_models.mjs "$R" "$S/mutsrc")
echo "== encode"; T0=$(date +%s)
bash art/tools/int17/encode.sh "$R" "$S" mut 2>&1 | grep -v "^PREP" | tail -60
echo "encode wall $(( $(date +%s) - T0 )) s"; tail -20 "$S/gt.log" 2>/dev/null
echo "== decode"; node art/tools/int17/check.mjs "$R" "$S" "$S/dec" 2>&1 | tail -20
echo "== gates"; python3 art/tools/int17/metrics.py "$R" "$S" "$S/dec" 2>&1 | tail -40
mkdir -p "$OUT/c" && cp -r "$S/desk" "$S/phone" "$S/models" "$OUT/c/" && cp "$S/dec"/*.json "$OUT/" 2>/dev/null; cp -r "$S/dec/decoded" "$OUT/decoded_desk" 2>/dev/null; true
