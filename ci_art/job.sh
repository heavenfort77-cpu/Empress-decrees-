#!/bin/bash
# Batch 17a round 4 (INT): gates re-run on the exact files of round 3 (run 45516776477, fetched from ci-out), with the PNG pick for textures no
# KTX2 mode keeps within the gates. Mutants encoded fresh. Suits left out (SUITANIM changed their sources; they are encoded in 17f). CI file only.
set -uo pipefail
R=$PWD; S=$R/stage; mkdir -p "$S/mutsrc"
URL=https://github.com/KhronosGroup/KTX-Software/releases/download/v4.3.2/KTX-Software-4.3.2-Linux-x86_64.deb
curl -fsSL -o /tmp/ktx.deb "$URL" && sudo apt-get install -y -qq /tmp/ktx.deb >/dev/null 2>&1; toktx --version || echo "TOKTX MISSING"
mkdir -p /tmp/gt && (cd /tmp/gt && npm init -y >/dev/null && npm install --no-audit --no-fund @gltf-transform/cli@4 @gltf-transform/core@4 >/dev/null 2>&1); export GT=/tmp/gt/node_modules/.bin/gltf-transform
cp art/tools/int17/mut_models.mjs /tmp/gt/ && (cd /tmp/gt && node mut_models.mjs "$R" "$S/mutsrc")
P=out/art/ci-art-int/45516776477/c
git fetch -q --depth=1 origin ci-out && git checkout -q FETCH_HEAD -- "$P" && cp -r "$P/desk" "$P/phone" "$P/models" "$S/" && rm -rf "$S/models/suits" && git rm -rq --cached out >/dev/null 2>&1; rm -rf out
echo "== re-check of round 3 files: $(find "$S/desk" "$S/phone" -name '*.ktx2' | wc -l) KTX2, $(find "$S/models" -name '*.glb' | wc -l) GLB"
SKIPMAIN=1 bash art/tools/int17/encode.sh "$R" "$S" mut 2>&1 | grep -v "^PREP" | tail -8
echo "== decode"; node art/tools/int17/check.mjs "$R" "$S" "$S/dec" 2>&1 | tail -6
echo "== gates"; python3 art/tools/int17/metrics.py "$R" "$S" "$S/dec" 2>&1 | tail -40
cp "$S/dec"/manifest_pick.json "$S/dec"/models.json "$S/dec"/caps_*.json "$OUT/" 2>/dev/null; true
