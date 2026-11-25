#!/bin/bash
# FACES sample job (owner 25 Nov 09:44 "i hate the face"; samples only, nothing goes into the game): klad face textures, 15 builds
# (suit fa, guard zu, giant 00 x options 0 A B C D) through art/tools/faces_sample.py, viewer shots, one sheet per character.
# Everything lands in $OUT. PREFLIGHT first (lead rule 25 Nov 09:5x): tools, imports, inputs, output folders, clean tree; a file
# ci_art/PREFLIGHT_ONLY stops the job after the preflight (1-minute proof of the job script).
set -u
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/.."
O=$OUT
step() { echo "== $1 $(date +%H:%M:%S)"; }
die() { echo "PREFLIGHT FAIL $1"; exit 1; }
step "preflight"
for t in node npx python3 "$KLAD"; do command -v "$t" >/dev/null || die "tool $t"; done
$BPY -c "import bpy, numpy, PIL, mathutils, bmesh; print('bpy', bpy.app.version_string)" || die "python imports (bpy numpy PIL)"
python3 -c "import PIL, json" || die "python3 imports (PIL)"
node -e "import('playwright').then(p => p.chromium.executablePath()).then(e => require('fs').existsSync(e) || process.exit(1))" || die "playwright chromium"
for f in art/tools/suit_blender.py art/tools/guard_build.py art/tools/fodder_base.py art/tools/giant_blender.py art/tools/tread_kit.py \
         art/tools/faces_sample.py art/tools/faces_kit.py art/tools/faces_tex.py art/tools/faces_shoot.mjs art/tools/faces_sheet.py \
         art/viewer/faces.html art/viewer/vendor/loaders/GLTFLoader.js lib/three.module.min.js \
         assets/tex/hall_floor.png assets/tex/suit_lamellar.png assets/tex/suit_bronze.png assets/tex/suit_cloth.png \
         assets/tex/bronze_trim_brass.png assets/tex/fodder_trim.png assets/tex/tread_belt.png; do
  [ -s "$f" ] || die "input $f"; done
grep -q "loft('mask', \[((0, 0.11, hz(0.02))" art/tools/suit_blender.py || die "suit builder mask anchor (faces_sample.py cut point)"
grep -q "def face(g, H, lod):" art/tools/giant_blender.py || die "giant face() anchor"
mkdir -p $O/tex $O/tex_passes $O/src $O/logs $O/glb $O/shots $O/sheets art/faces/glb art/faces/tex /tmp/fops /tmp/fshots || die "mkdir"
[ -z "$(git ls-files | grep -E '\.pyc$|__pycache__')" ] || die "tracked .pyc files"
[ -z "$(git status --porcelain --untracked-files=no)" ] || die "tracked files modified before the job"
echo "PREFLIGHT PASS"
if [ -f ci_art/PREFLIGHT_ONLY ]; then echo "RESULT preflight only"; exit 0; fi
step "textures (klad)"
python3 art/tools/faces_tex.py /tmp/fops | tee $O/logs/tex_ops.txt
python3 art/tools/faces_tex.py --paint "$KLAD" /tmp/fops $O/src art/faces/tex $O/tex_passes 2>&1 | tee $O/logs/tex_paint.txt
cp art/faces/tex/*.png $O/tex/
step "builds"
for c in g00 fa zu; do for o in 0 A B C D; do echo "$c $o"; done; done | xargs -P 3 -L 1 bash -c \
  '$BPY art/tools/faces_sample.py -- $0 $1 art/faces/glb > '"$O"'/logs/build_$0_$1.log 2>&1; echo "built $0 $1 exit $?"'
for f in $O/logs/build_*.log; do echo "## $(basename $f .log)"; grep -E "^(PASS|FAIL|SUMMARY|FACES)|of [0-9]+ pass|Traceback|Error" $f | grep -v "^PASS" ; done | tee $O/builds_gates.txt
cp art/faces/glb/*.glb art/faces/glb/*_stats.json $O/glb/ 2>/dev/null; ls art/faces/glb | wc -l
step "shots"
node art/tools/faces_shoot.mjs /tmp/fshots 2>&1 | tee $O/logs/shots.txt | grep -v " ok " || true
python3 - /tmp/fshots $O/shots <<'PY'
import sys, os
from PIL import Image
s, d = sys.argv[1:3]; n = 0
for f in sorted(os.listdir(s)):
    if f.endswith('.png'): Image.open(os.path.join(s, f)).convert('RGB').save(os.path.join(d, f[:-4] + '.jpg'), quality=88); n += 1
print('jpg', n)
PY
cp /tmp/fshots/shots.json $O/shots/
step "sheets"
python3 art/tools/faces_sheet.py /tmp/fshots art/faces/glb $O/sheets 2>&1 | tee $O/sheets/gates.txt
rm -rf art/faces/glb art/faces/tex
git status --short | grep -v '^??' | head -5
du -sh $O; echo "RESULT done"
