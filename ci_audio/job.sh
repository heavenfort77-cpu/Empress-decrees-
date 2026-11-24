#!/bin/bash
# AUDIO run: static check of src/audio/sound.js, offline renders in headless Chromium, gates + mutations, phone previews. Writes to $OUT.
cd "$(dirname "$0")/.."
echo "== static"; node ci_audio/static.mjs
echo "== render"; node ci_audio/render.mjs "$OUT"
echo "== gates"; python ci_audio/analyze.py "$OUT"
# Desktop one-shots and the mutation material are only needed for the gates; the phone set and both ramps are kept for listening.
rm -rf "$OUT/mut" "$OUT"/wav/desktop/[!l]*.wav
du -sh "$OUT" | sed 's/^/OUT size /'
