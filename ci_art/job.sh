#!/bin/bash
# COLOUR (owner 25 Nov 13:1x: characters must read on the floor, 'not one mess'; art/Colour-Clarity-Study.md). ONE art round:
# 1 hall floor repainted in klad to the study's targets (floor_calibrate.py on palace_tex.py floor(), seed 101 kept), 2 lifted candidates of
# the corridor tiles and garden ground (TEX_GAIN, not replacing the approved files), 3 the Qin proposal suit sheet (SUIT_QIN=1, new file
# suit_lamellar_qin.png), 4 gates with mutations (tex_check, floor_rule_check, trim_check), 5 shots of nine suits + guard + rebel on the
# old and new floor with and without rim / trim (colour_shoot.mjs), 6 measures and sheets (colour_measure.py).
# No model is rebuilt; no game file is touched. Writes to $OUT; leaves the tree as checked out.
set -u
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/.."
O=$OUT; mkdir -p $O
T=art/tools
step() { echo "== $1 $(date +%H:%M:%S)"; }
step "preflight"
# lead RULE 25 Nov (RUNNERS.md): tools, imports, inputs, output folders and a clean tree, checked in the first minute; any miss fails the job
PF=0; miss() { echo "PREFLIGHT FAIL: $1"; PF=1; }
for t in node python3 git; do command -v $t >/dev/null || miss "tool $t"; done
[ -x "${KLAD:-}" ] && $KLAD --version >/dev/null 2>&1 || miss "klad binary (\$KLAD)"
python3 -c "import numpy, PIL, scipy, json" 2>/dev/null || miss "python3 imports (numpy PIL scipy)"
node -e "import('playwright').then(m=>m.chromium.executablePath()).then(p=>require('fs').existsSync(p)||process.exit(1)).catch(()=>process.exit(1))" || miss "playwright chromium"
for f in $T/palace_tex.py $T/paint_palace.py $T/arch_tex.py $T/suit_tex.py $T/suit_paint.py $T/tex_check.py $T/tex_check_mut.py $T/floor_rule_check.py \
         $T/floor_calibrate.py $T/trim_check.py $T/colour_shoot.mjs $T/colour_measure.py art/viewer/colour.html art/viewer/vendor/loaders/GLTFLoader.js \
         art/viewer/vendor/utils/BufferGeometryUtils.js lib/three.module.min.js lib/three.core.min.js art/round2/tex/hall_floor.png \
         assets/tex/hall_floor.png assets/tex/stone_paving.png assets/tex/floor_tiles.png assets/tex/garden_ground.png assets/tex/timber.png \
         assets/tex/suit_lamellar.png assets/tex/suit_cloth.png assets/tex/suit_bronze.png assets/tex/bronze_trim_brass.png assets/tex/fodder_trim.png \
         assets/tex/tread_belt.png assets/models/guard/zu.glb assets/models/rebels/ls.glb; do [ -s "$f" ] || miss "input $f"; done
for id in fa ru dao mo yy za ming zh nong; do [ -s assets/models/suits/$id.glb ] || miss "input assets/models/suits/$id.glb"; done
cmp -s art/round2/tex/hall_floor.png assets/tex/hall_floor.png || miss "assets/tex/hall_floor.png is not the round 2 floor (the job paints the new one itself)"
python3 -c "import sys; sys.path.insert(0,'$T'); import floor_rule_check" 2>/dev/null || miss "floor_rule_check import"
mkdir -p /tmp/fl/ops /tmp/fl/src /tmp/fl/out /tmp/fl/strip /tmp/cand/ops /tmp/cand/src /tmp/cand/out /tmp/cand/strip /tmp/sq/ops /tmp/sq/src /tmp/sq/out /tmp/sq/strip \
         /tmp/colshots /tmp/texall art/colour/cand $O/tex $O/src $O/cand $O/gates $O/sheets $O/shots || miss "mkdir outputs"
[ -z "$(git ls-files '*.pyc' '__pycache__/*')" ] || miss "tracked .pyc files"
[ -z "$(git status --porcelain --untracked-files=no)" ] || miss "tracked files modified before the job"
[ $PF = 0 ] && echo "PREFLIGHT PASS" || { echo "RESULT preflight failed"; exit 1; }
if [ -f ci_art/PREFLIGHT_ONLY ]; then echo "RESULT preflight only (proof run)"; exit 0; fi
step "hall floor (klad, calibrated to the study targets)"
python3 $T/floor_calibrate.py $KLAD /tmp/fl/ops /tmp/fl/src /tmp/fl/out /tmp/fl/strip 2>&1 | tee $O/gates/floor_calibration.txt
cp /tmp/fl/out/hall_floor.png assets/tex/hall_floor.png && cp /tmp/fl/out/hall_floor.png $O/tex/ && cp -r /tmp/fl/src/hall_floor.klad $O/src/ && cp /tmp/fl/strip/hall_floor_passes.png $O/sheets/ && cp /tmp/fl/ops/calib.json $O/gates/
step "candidates of the other floors (not replacing the approved files)"
TEX_GAIN=1.20 python3 $T/arch_tex.py /tmp/cand/ops 1024 floor_tiles && TEX_GAIN=1.35 python3 $T/arch_tex.py /tmp/cand/ops 1024 garden_ground
python3 $T/paint_palace.py $KLAD /tmp/cand/ops /tmp/cand/src /tmp/cand/out /tmp/cand/strip floor_tiles,garden_ground
cp /tmp/cand/out/floor_tiles.png /tmp/cand/out/garden_ground.png art/colour/cand/ && cp /tmp/cand/out/*.png $O/cand/ && cp -r /tmp/cand/src/*.klad $O/cand/
step "Qin proposal suit sheet"
SUIT_QIN=1 python3 $T/suit_tex.py /tmp/sq/ops && python3 $T/suit_paint.py $KLAD /tmp/sq/ops /tmp/sq/src /tmp/sq/out /tmp/sq/strip suit_lamellar
cp /tmp/sq/out/suit_lamellar.png assets/tex/suit_lamellar_qin.png && cp assets/tex/suit_lamellar_qin.png $O/tex/ && cp -r /tmp/sq/src/suit_lamellar.klad $O/src/suit_lamellar_qin.klad && cp /tmp/sq/strip/suit_lamellar_passes.png $O/sheets/suit_lamellar_qin_passes.png
step "gates"
cp assets/tex/*.png /tmp/texall/ && rm -f /tmp/texall/suit_lamellar_qin.png
python3 $T/tex_check.py /tmp/texall 1 4 > $O/gates/tex_check_full.txt 2>&1; grep -E "^FAIL|hall_floor|star_inlay|of .* pass|Traceback" $O/gates/tex_check_full.txt | tee $O/gates/tex_check.txt
python3 $T/tex_check_mut.py /tmp/texall 2>&1 | grep -E "hall_floor|MISSED|caught$|Traceback" | tee $O/gates/tex_check_mut.txt
python3 $T/floor_rule_check.py assets/tex --mutate floor_tiles=art/colour/cand/floor_tiles.png garden_ground=art/colour/cand/garden_ground.png hall_floor=art/round2/tex/hall_floor.png 2>&1 | sed 's/^FAIL hall_floor_cand/CONTROL round 2 hall floor fails/' | tee $O/gates/floor_rules.txt
python3 $T/trim_check.py assets/tex/suit_lamellar_qin.png --mutate assets/tex/suit_lamellar.png 2>&1 | tee $O/gates/trim.txt
python3 - <<'PY' 2>&1 | tee $O/gates/floor_sheet.txt
import os
from PIL import Image, ImageDraw
O = os.environ['OUT']; old = Image.open('art/round2/tex/hall_floor.png').convert('RGB'); new = Image.open('assets/tex/hall_floor.png').convert('RGB')
s = Image.new('RGB', (1024 * 2 + 12, 26 + 1024 + 26 + 1024), (255, 255, 255)); d = ImageDraw.Draw(s)
d.text((6, 6), 'round 2 hall floor (approved, kept in art/round2), 1:1', fill=(0, 0, 0)); d.text((1042, 6), 'round 3 hall floor (COLOUR), 1:1', fill=(0, 0, 0))
s.paste(old, (0, 26)); s.paste(new, (1036, 26)); d.text((6, 1056), '2 x 2 tiles at half size (seams)', fill=(0, 0, 0))
for k, im in enumerate((old, new)):
    h = im.resize((512, 512), Image.LANCZOS)
    for i in range(2):
        for j in range(2): s.paste(h, (k * 1036 + i * 512, 1076 + j * 512))
s.save(f'{O}/sheets/sheet_floor_texture_old_vs_new.jpg', quality=88); print('floor texture sheet written')
PY
step "shots"
node $T/colour_shoot.mjs /tmp/colshots 2>&1 | tee $O/gates/shots_full.txt | grep -v " ok$" | tee $O/gates/shots.txt
step "measures and sheets"
python3 $T/colour_measure.py /tmp/colshots $O/sheets 2>&1 | tee $O/measures.txt | grep -E "^FAIL|^MUT|^TABLE|FAIL lines|all colour|Traceback"
for f in /tmp/colshots/*.png; do n=$(basename ${f%.png}); case $n in id_*) cp $f $O/shots/;; *) python3 -c "import sys;from PIL import Image;Image.open(sys.argv[1]).convert('RGB').save(sys.argv[2],quality=90)" $f $O/shots/$n.jpg;; esac; done
cp /tmp/colshots/manifest.json $O/shots/
rm -rf art/colour/cand assets/tex/suit_lamellar_qin.png; rmdir art/colour 2>/dev/null; git checkout -- assets art 2>/dev/null; git status --short | head -5
echo "== summary"
cat $O/gates/floor_calibration.txt $O/gates/tex_check.txt $O/gates/tex_check_mut.txt $O/gates/floor_rules.txt $O/gates/trim.txt $O/gates/shots.txt $O/measures.txt 2>/dev/null | grep -E "^FAIL|MUT MISSED|MISSED |of .* pass|caught$|mutations caught|Traceback|^TABLE" | tee $O/summary.txt
nf=$(grep -c "^FAIL\|MUT MISSED\|^MISSED \|Traceback" $O/summary.txt); echo "FAIL lines: $nf" | tee -a $O/summary.txt
du -sh $O; echo "RESULT done"
