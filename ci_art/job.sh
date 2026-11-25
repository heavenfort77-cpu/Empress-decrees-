#!/bin/bash
# SUITANIM recolour + robe fix round (owner 25 Nov): suit cloth tints and cord rows to the one school colour mapping (klad repaints the
# cord rows of suit_lamellar; outside them the approved sheet is kept), za/zh robes follow the legs more at the front. Gates: builder,
# silhouettes, clip gates (frozen clips, robe flare, weight scope) with mutations, colour gates with mutations, tex_check, shots, sheets.
set -u
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/.."
O=$OUT; mkdir -p $O/suits $O/models/suits $O/tex $O/src
step() { echo "== $1 $(date +%H:%M:%S)"; }
step "textures (klad)"
mkdir -p /tmp/approved_tex && cp assets/tex/suit_lamellar.png assets/tex/suit_cloth.png assets/tex/suit_bronze.png /tmp/approved_tex/
mkdir -p /tmp/sops && python3 art/tools/suit_tex.py /tmp/sops > /dev/null
python3 art/tools/suit_paint.py $KLAD /tmp/sops /tmp/ssrc /tmp/stex /tmp/sstrip suit_lamellar 2>&1 | tail -2
python3 - <<'PY'
import numpy as np
from PIL import Image
a = np.asarray(Image.open('/tmp/approved_tex/suit_lamellar.png').convert('RGB')); k = np.asarray(Image.open('/tmp/stex/suit_lamellar.png').convert('RGB'))
n = int((a[:736] != k[:736]).any(2).sum()); c = a.copy(); c[736:] = k[736:]
Image.fromarray(c).save('assets/tex/suit_lamellar.png'); print(f'klad repaint: {n} pixels outside the cord rows differ from the approved sheet; shipped = approved rows 0-735 + klad cord rows 736-1023')
PY
cp assets/tex/suit_lamellar.png $O/tex/; cp /tmp/stex/suit_lamellar.png $O/tex/suit_lamellar_klad_full.png; cp -r /tmp/ssrc/suit_lamellar.klad $O/src/ 2>/dev/null
# tex_check on the one sheet this round changes (suit_bronze has a known parked brush-scale fail from FIXB and is byte-identical here)
python3 art/tools/tex_check.py assets/tex 2>&1 | grep -i "suit_lamellar" | tee $O/suits/tex_check.txt
step "build"
$BPY art/tools/suit_blender.py -- /tmp/suits all > $O/suits/blender.log 2>&1; grep -E "^(PASS|FAIL)|of .* pass|Error|Traceback|line [0-9]" $O/suits/blender.log | tee $O/suits/gates.txt
python3 art/tools/suit_sil.py /tmp/suits $O/suits/sil 2>&1 | tee $O/suits/sil.txt
node art/tools/suit_clip_signfix.mjs /tmp/suits 2>&1 | tee $O/suits/signfix.txt
cp /tmp/suits/*.glb /tmp/suits/suits_info.json $O/models/suits/
step "clip gates"
node art/tools/suit_clip_check.mjs /tmp/suits assets/models/suits /tmp/suits/suits_info.json --mutate --precalm=ci_art/precalm 2>&1 | tee $O/suits/clip_gates.txt
step "shots"
cp /tmp/suits/*.glb assets/models/suits/
node art/tools/suitanim_shoot.mjs /tmp/ashots /tmp/suits/suits_info.json 2>&1 | tee $O/suits/shots.txt | grep -v " ok$" || true
step "colour gates"
python3 art/tools/suit_colour_check.py /tmp/suits assets/tex /tmp/approved_tex /tmp/ashots --mutate 2>&1 | tee $O/suits/colour_gates.txt
python3 art/tools/suitanim_sheet.py /tmp/ashots $O/suits/sheets
mkdir -p $O/suits/strips && for f in /tmp/ashots/*_strip_*.png /tmp/ashots/lineup_colour*.png /tmp/ashots/lineup_clothid.png; do python3 -c "import sys;from PIL import Image;Image.open(sys.argv[1]).convert('RGB').save(sys.argv[2],quality=88)" $f $O/suits/strips/$(basename ${f%.png}).jpg; done
cp /tmp/ashots/lineup_colour.png /tmp/ashots/lineup_clothid.png $O/suits/ 2>/dev/null
git checkout -- assets art 2>/dev/null; git status --short | grep -v '^??' | head -5
du -sh $O; echo "RESULT done"
