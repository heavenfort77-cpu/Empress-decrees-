#!/bin/bash
# W6 runner job (C12 school emblem standard): klad banner atlas, its checks and mutations; Blender builder gates and mutations; GLB
# re-read and mutations; viewer shots on the brass sheet (owner 25 Nov: brass only); play-size check and mutation; review sheets.
# env: $BPY python with bpy, $KLAD klad binary, $OUT results folder.
set -u
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$OUT/shots" "$OUT/passes" "$OUT/src" "$OUT/sheets" /tmp/ops
echo "== klad atlas"
python3 art/tools/standard_tex.py /tmp/ops
python3 art/tools/paint_palace.py "$KLAD" /tmp/ops "$OUT/src" assets/tex "$OUT/passes" school_standards
cp assets/tex/school_standards.png "$OUT/"
echo "== tex check"; python3 art/tools/standard_check.py tex assets/tex/school_standards.png | tee "$OUT/tex_check.txt"
for m in dup blend flat bleed tongue; do echo "tex mutation $m: $(python3 art/tools/standard_check.py tex assets/tex/school_standards.png --mut $m | grep -c '^FAIL') FAIL lines (must be > 0)"; done | tee "$OUT/tex_mut.txt"
echo "== builder"; $BPY art/tools/standard_blender.py "$PWD/assets/models/standard.glb" 2>&1 | grep -E "^(PASS|FAIL)|of [0-9]+ pass|wrote|INFO|Error|Traceback|line [0-9]" | tee "$OUT/build_gates.txt"
cp assets/models/standard.glb "$OUT/"
for m in tris weights rigid height loop texel fps; do echo "build mutation $m: $(STD_MUT=$m $BPY art/tools/standard_blender.py /tmp/mut_$m.glb 2>&1 | grep -c '^FAIL') FAIL lines (must be > 0)"; done | tee "$OUT/build_mut.txt"
echo "== glb re-read"; python3 art/tools/standard_glb.py assets/models/standard.glb | tee "$OUT/glb_check.txt"
for m in blend skin clip late uv schools; do echo "glb mutation $m: $(python3 art/tools/standard_glb.py assets/models/standard.glb --mut $m | grep -c '^FAIL') FAIL lines (must be > 0)"; done | tee "$OUT/glb_mut.txt"
echo "== shots (brass sheet)"; node art/tools/shoot_viewer.mjs "$OUT/shots" standard sheet=brass 2>&1 | tee "$OUT/shots.txt"
echo "== play-size check"
for m in dup blur; do echo "play mutation $m: $(python3 art/tools/standard_check.py crops "$OUT/shots" assets/tex/school_standards.png --mut $m | grep -c '^FAIL') FAIL lines (must be > 0)"; done | tee "$OUT/play_mut.txt"
python3 art/tools/standard_check.py crops "$OUT/shots" assets/tex/school_standards.png | tee "$OUT/play_check.txt"
echo "== sheets"; python3 art/tools/standard_sheet.py "$OUT/shots" "$OUT/sheets"
# leave the checkout clean (the workflow switches to ci-out after this script)
git checkout -q -- . && git clean -qfd assets art
echo "RESULT done"
