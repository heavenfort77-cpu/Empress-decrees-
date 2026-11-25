#!/bin/bash
# SUITANIM art job (robe round: calm robe binding for dao/za/zh, robe-flare and weight-scope gates; OLD = the delivered 64b7bd5 GLBs) (owner 25 Nov): run, hit and death clips for the nine school suits. Builder gates (budgets, weights, rig, reach,
# death floor solve, GLB re-read with all clips), silhouette gates (unchanged rest/windup), clip gates in three r171 on the rebuilt GLBs
# and mutations, contact strips (plus a play-size run strip) and play-size shots, sheets. All results in $OUT.
set -u
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/.."
O=$OUT; mkdir -p $O/suits $O/models/suits
step() { echo "== $1 $(date +%H:%M:%S)"; }
step "build"
$BPY art/tools/suit_blender.py -- /tmp/suits all > $O/suits/blender.log 2>&1; grep -E "^(PASS|FAIL)|of .* pass|Error|Traceback|line [0-9]" $O/suits/blender.log | tee $O/suits/gates.txt
python3 art/tools/suit_sil.py /tmp/suits $O/suits/sil 2>&1 | tee $O/suits/sil.txt
node art/tools/suit_clip_signfix.mjs /tmp/suits 2>&1 | tee $O/suits/signfix.txt
cp /tmp/suits/*.glb /tmp/suits/suits_info.json $O/models/suits/
step "clip gates: rebuilt"
node art/tools/suit_clip_check.mjs /tmp/suits assets/models/suits /tmp/suits/suits_info.json --mutate 2>&1 | tee $O/suits/clip_gates.txt
step "shots"
cp /tmp/suits/*.glb assets/models/suits/
node art/tools/suitanim_shoot.mjs /tmp/ashots /tmp/suits/suits_info.json 2>&1 | tee $O/suits/shots.txt | grep -v " ok$" || true
python3 art/tools/suitanim_sheet.py /tmp/ashots $O/suits/sheets
mkdir -p $O/suits/strips && for f in /tmp/ashots/*_strip_*.png; do python3 -c "import sys;from PIL import Image;Image.open(sys.argv[1]).convert('RGB').save(sys.argv[2],quality=85)" $f $O/suits/strips/$(basename ${f%.png}).jpg; done
git checkout -- assets art 2>/dev/null; git status --short | grep -v '^??' | head -5
du -sh $O; echo "RESULT done"
