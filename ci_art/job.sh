#!/bin/bash
# W4 apex run: klad patina sheet, tiger and cubs builders (gates), viewer shots, review sheets. Writes everything to $OUT.
cd "$(dirname "$0")/.."
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$OUT/ops" "$OUT/tex" "$OUT/src" "$OUT/strip" "$OUT/models" "$OUT/shots" "$OUT/sheets"
echo "== klad patina sheet"
python art/tools/apex_tex.py "$OUT/ops" && python art/tools/paint_palace.py "$KLAD" "$OUT/ops" "$OUT/src" "$OUT/tex" "$OUT/strip" apex_patina
cp "$OUT/tex/apex_patina.png" assets/tex/apex_patina.png
cp assets/tex/bronze_trim.png "$OUT/tex/bronze_trim.png"
echo "== tex_check"; python art/tools/tex_check.py "$OUT/tex"
echo "== tiger"; $BPY art/tools/apex_tiger.py assets/models/apex/tiger.glb "$OUT/tiger_gates.json" 2>&1 | grep -E "^(PASS|FAIL)|of [0-9]+ pass|wrote|Error|Traceback|line [0-9]"
echo "== cubs"; $BPY art/tools/apex_cubs.py -- assets/models/apex "$OUT/cubs_gates.json" 2>&1 | grep -E "^(PASS|FAIL)|of [0-9]+ pass|wrote|Error|Traceback|line [0-9]"
cp assets/models/apex/*.glb "$OUT/models/"
echo "== shots"; node art/tools/apex_shoot.mjs "$OUT/shots"
echo "== sheets"; python art/tools/apex_sheet.py "$OUT/shots" "$OUT/sheets" art/apex/concepts
git checkout -q -- . 2>/dev/null; git status --short | grep -v "^??" ; echo "RESULT done"  # tracked files restored so the ci-out commit step can switch branches (run 45439899275 failed there)
