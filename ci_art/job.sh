#!/bin/bash
# FACES round 2 job (owner GO 25 Nov 10:47, order 10:52; samples only, nothing goes into the game): 4 builds (guard zu, giant 00 x now 0
# and mask M) through art/tools/faces_sample.py, viewer shots with contrast probes, one sheet per character. Everything lands in $OUT.
# PREFLIGHT first (tools, imports, inputs, output folders, clean tree); a file ci_art/PREFLIGHT_ONLY stops the job after it.
# The preflight also imports faces_kit and evaluates both mask fields once.
set -u
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/.."
O=$OUT
step() { echo "== $1 $(date +%H:%M:%S)"; }
die() { echo "PREFLIGHT FAIL $1"; exit 1; }
step "preflight"
for t in node npx python3; do command -v "$t" >/dev/null || die "tool $t"; done
$BPY -c "import bpy, numpy, PIL, mathutils, bmesh; print('bpy', bpy.app.version_string)" || die "python imports (bpy numpy PIL)"
python3 -c "import PIL, json" || die "python3 imports (PIL)"
node -e "import('playwright').then(p => p.chromium.executablePath()).then(e => require('fs').existsSync(e) || process.exit(1))" || die "playwright chromium"
for f in art/tools/guard_build.py art/tools/fodder_base.py art/tools/giant_blender.py art/tools/tread_kit.py \
         art/tools/faces_sample.py art/tools/faces_kit.py art/tools/faces_shoot.mjs art/tools/faces_sheet.py \
         art/viewer/faces.html art/viewer/vendor/loaders/GLTFLoader.js lib/three.module.min.js \
         assets/tex/hall_floor.png assets/tex/bronze_trim_brass.png assets/tex/fodder_trim.png assets/tex/tread_belt.png; do
  [ -s "$f" ] || die "input $f"; done
grep -q "def face(g, H, lod):" art/tools/giant_blender.py || die "giant face() anchor"
grep -q "^def head(d, cap='knot'):" art/tools/guard_build.py || die "guard head() anchor"
python3 -c "import sys; sys.path.insert(0, 'art/tools'); import faces_kit as K; [K.SHAPES[g][1](0.36, 0.56) for g in ('zu', 'g00')]; print('faces_kit ok')" || die "faces_kit"
mkdir -p $O/logs $O/glb $O/shots $O/sheets art/faces/glb /tmp/fshots || die "mkdir"
[ -z "$(git ls-files | grep -E '\.pyc$|__pycache__')" ] || die "tracked .pyc files"
[ -z "$(git status --porcelain --untracked-files=no)" ] || die "tracked files modified before the job"
echo "PREFLIGHT PASS"
if [ -f ci_art/PREFLIGHT_ONLY ]; then echo "RESULT preflight only"; exit 0; fi
step "builds"
for c in g00 zu; do for o in 0 M; do echo "$c $o"; done; done | xargs -P 2 -L 1 bash -c \
  '$BPY art/tools/faces_sample.py -- $0 $1 art/faces/glb > '"$O"'/logs/build_$0_$1.log 2>&1; echo "built $0 $1 exit $?"'
for f in $O/logs/build_*.log; do echo "## $(basename $f .log)"; grep -E "^(PASS|FAIL|SUMMARY|FACES)|of [0-9]+ pass|Traceback|Error" $f | grep -v "^PASS" ; done | tee $O/builds_gates.txt
cp art/faces/glb/*.glb art/faces/glb/*_stats.json $O/glb/ 2>/dev/null; ls art/faces/glb | wc -l
n=$(grep -h "^FAIL" $O/builds_gates.txt | wc -l); echo "builder FAIL lines $n"
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
rm -rf art/faces/glb
git status --short | grep -v '^??' | head -5
nf=$(cat $O/builds_gates.txt $O/sheets/gates.txt | grep -c "^FAIL"); np=$(grep -c "^PASS" $O/sheets/gates.txt)
du -sh $O; echo "RESULT done: sheet PASS $np, FAIL lines (builders + sheet) $nf"
