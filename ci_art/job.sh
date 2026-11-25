#!/bin/bash
# SUITS fa round 5 (owner GO 25 Nov 10:55): rebuild 法甲 as one sample the owner's-kit way. Steps: atlases (fa_tex.py, gates + mutations),
# build (fa_r5.py on the approved suit_blender.py rig/clip pipeline; build gates), quaternion sign fix, clip gates with mutations
# (suit_clip_check.mjs, fa in rebuilt mode), review shots (fa_shoot.mjs: new fa, round-4 fa, lineups, head close-ups, ID pass) and clip strips
# (suitanim_shoot.mjs), measures with mutations (fa_measure.py: floor contrast via suit_contrast.py, mask vs helm, silhouettes, values) and sheets.
# Nothing outside fa is built; the other eight suits are rendered from their approved GLBs. Writes to $OUT; leaves the tree as checked out.
set -u
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/.."
O=$OUT; mkdir -p $O
step() { echo "== $1 $(date +%H:%M:%S)"; }
step "preflight"
# lead RULE 25 Nov (RUNNERS.md): tools, imports, inputs, output folders and a clean tree, checked in the first minute; any miss fails the job
PF=0; miss() { echo "PREFLIGHT FAIL: $1"; PF=1; }
for t in node python3 git; do command -v $t >/dev/null || miss "tool $t"; done
$BPY -c "import bpy, numpy, PIL" 2>/dev/null || miss "bpy python imports (bpy numpy PIL)"
python3 -c "import numpy, PIL, scipy, json" 2>/dev/null || miss "python3 imports (numpy PIL scipy)"
node -e "import('playwright').then(m=>m.chromium.executablePath()).then(p=>require('fs').existsSync(p)||process.exit(1)).catch(()=>process.exit(1))" || miss "playwright chromium"
for f in art/tools/fa_r5.py art/tools/fa_tex.py art/tools/fa_rows.json art/tools/fa_shoot.mjs art/tools/fa_measure.py art/tools/suit_blender.py \
         art/tools/suit_contrast.py art/tools/suit_clip_signfix.mjs art/tools/suit_clip_check.mjs art/tools/suitanim_shoot.mjs art/viewer/suits.html \
         art/viewer/vendor/loaders/GLTFLoader.js art/viewer/vendor/utils/BufferGeometryUtils.js lib/three.module.min.js lib/three.core.min.js \
         assets/tex/suit_lamellar.png assets/tex/suit_cloth.png assets/tex/suit_bronze.png assets/tex/hall_floor.png; do [ -s "$f" ] || miss "input $f"; done
for id in fa ru dao mo yy za ming zh nong; do [ -s assets/models/suits/$id.glb ] || miss "input assets/models/suits/$id.glb"; done
$BPY -c "import sys; sys.argv=['x']; sys.path.insert(0,'art/tools'); import suit_blender" 2>/dev/null || miss "suit_blender imports under bpy"
mkdir -p /tmp/fatex /tmp/suits /tmp/fashots /tmp/ashots $O/suits $O/models $O/tex $O/sheets || miss "mkdir outputs"
[ -z "$(git ls-files '*.pyc' '__pycache__/*')" ] || miss "tracked .pyc files"
[ -z "$(git status --porcelain --untracked-files=no)" ] || miss "tracked files modified before the job"
[ $PF = 0 ] && echo "PREFLIGHT PASS" || { echo "RESULT preflight failed"; exit 1; }
if [ -f ci_art/PREFLIGHT_ONLY ]; then echo "RESULT preflight only (proof run)"; exit 0; fi
step "atlases"
python3 art/tools/fa_tex.py /tmp/fatex 2>&1 | tee $O/suits/tex_gates.txt
cp /tmp/fatex/suit_fa_*.png assets/tex/ && cp /tmp/fatex/suit_fa_*.png $O/tex/
step "build"
$BPY art/tools/fa_r5.py -- /tmp/suits fa > $O/suits/blender.log 2>&1; grep -E "^(PASS|FAIL)|of .* pass|Error|Traceback|line [0-9]" $O/suits/blender.log | tee $O/suits/gates.txt
node art/tools/suit_clip_signfix.mjs /tmp/suits fa 2>&1 | tee $O/suits/signfix.txt
cp /tmp/suits/fa.glb /tmp/suits/suits_info.json /tmp/suits/fa_r5_metrics.json $O/models/ 2>/dev/null
step "clip gates"
node art/tools/suit_clip_check.mjs /tmp/suits assets/models/suits /tmp/suits/suits_info.json --mutate fa 2>&1 | tee $O/suits/clip_gates.txt
step "shots"
cp assets/models/suits/fa.glb assets/models/suits/fa_old.glb && cp /tmp/suits/fa.glb assets/models/suits/fa.glb
node art/tools/fa_shoot.mjs /tmp/fashots /tmp/suits/suits_info.json 2>&1 | tee $O/suits/shots.txt | grep -v " ok$" || true
node art/tools/suitanim_shoot.mjs /tmp/ashots /tmp/suits/suits_info.json fa 2>&1 | grep -v " ok$" | tee $O/suits/anim_shots.txt || true
mkdir -p $O/sheets/strips && for f in /tmp/ashots/fa_strip_*.png; do [ -f "$f" ] && python3 -c "import sys;from PIL import Image;Image.open(sys.argv[1]).convert('RGB').save(sys.argv[2],quality=88)" $f $O/sheets/strips/$(basename ${f%.png}).jpg; done
step "measures and sheets"
python3 art/tools/fa_measure.py /tmp/fashots /tmp/suits/fa_r5_metrics.json $O/sheets --mutate 2>&1 | tee $O/suits/measures.txt
mkdir -p $O/shots && cp /tmp/fashots/*.png $O/shots/ && mkdir -p $O/shots/old && cp /tmp/fashots/old/*.png $O/shots/old/
rm -f assets/models/suits/fa_old.glb; git checkout -- assets art 2>/dev/null; git status --short | grep -v '^??' | head -5
echo "== summary"; cat $O/suits/tex_gates.txt $O/suits/gates.txt $O/suits/clip_gates.txt $O/suits/measures.txt 2>/dev/null | grep -E "^FAIL|MUT MISSED|of .* pass|mutations|Traceback" | tee $O/summary.txt
nf=$(grep -c "^FAIL\|MUT MISSED\|Traceback" $O/summary.txt); echo "FAIL lines: $nf" | tee -a $O/summary.txt
du -sh $O; echo "RESULT done"
