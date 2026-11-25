#!/bin/bash
# PIECES round 3 (owner 25 Nov 13:08 and 14:13; lead notes on run 45557912570): art for everything still drawn as plain shapes: Kaymuse (pieces_kaymuse.py), the crab and the wanderer
# (pieces_creatures.py), the plate pickup, leader crown, 墨 wall and decree mark (pieces_small.py). Steps: build (Blender gates), builder
# mutations (wrong CONFIG values must fail their gates), GLB gates with mutations (pieces_check.py), review shots in three (pieces_shoot.mjs:
# close-ups, play size beside in-game art, masks, silhouettes), play-size measures with mutations (pieces_measure.py) and sheets
# (pieces_sheets.py). Writes to $OUT; leaves the tree as checked out (the built GLBs go to ci-out, not into the tree).
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
$BPY -c "import bpy, numpy, PIL" 2>/dev/null || miss "bpy python imports (bpy numpy PIL)"
python3 -c "import numpy, PIL, scipy, json" 2>/dev/null || miss "python3 imports (numpy PIL scipy)"
node -e "import('playwright').then(m=>m.chromium.executablePath()).then(p=>require('fs').existsSync(p)||process.exit(1)).catch(()=>process.exit(1))" || miss "playwright chromium"
for f in $T/prop_kit.py $T/pieces_kit.py $T/pieces_kaymuse.py $T/pieces_creatures.py $T/pieces_small.py $T/pieces_check.py $T/pieces_measure.py $T/pieces_sheets.py $T/pieces_shoot.mjs \
         $T/pieces_mats.json art/pieces/floor_candidate.png art/viewer/pieces.html art/viewer/vendor/loaders/GLTFLoader.js lib/three.module.min.js lib/three.core.min.js \
         assets/models/arch/throne_dais.glb assets/models/ding.glb assets/models/suits/mo.glb assets/models/suits/fa.glb assets/models/guard/zu.glb; do [ -s "$f" ] || miss "input $f"; done
for x in bronze_trim_brass suit_cloth rammed_earth timber river_stone hall_floor suit_lamellar suit_bronze fodder_trim tread_belt stone_paving pillar; do [ -s assets/tex/$x.png ] || miss "input assets/tex/$x.png"; done
$BPY -c "import sys; sys.argv=['x']; sys.path.insert(0,'art/tools'); import pieces_kit, pieces_kaymuse, pieces_creatures, pieces_small" >/dev/null 2>$O/preflight_import.txt || miss "builders import under bpy ($(tail -1 $O/preflight_import.txt))"
mkdir -p /tmp/pieces /tmp/pmut /tmp/pshots $O/models $O/sheets $O/gates || miss "mkdir outputs"
[ ! -e assets/models/pieces ] || miss "assets/models/pieces already exists"
[ -z "$(git ls-files '*.pyc' '__pycache__/*')" ] || miss "tracked .pyc files"
[ -z "$(git status --porcelain --untracked-files=no)" ] || miss "tracked files modified before the job"
[ $PF = 0 ] && echo "PREFLIGHT PASS" || { echo "RESULT preflight failed"; exit 1; }
if [ -f ci_art/PREFLIGHT_ONLY ]; then echo "RESULT preflight only (proof run)"; exit 0; fi
KEEP="^(PASS|FAIL)|of .* pass|Error|Traceback|line [0-9]"
step "build"
$BPY $T/pieces_kaymuse.py /tmp/pieces/kaymuse.glb > $O/gates/build_kaymuse.log 2>&1
$BPY $T/pieces_creatures.py /tmp/pieces > $O/gates/build_creatures.log 2>&1
$BPY $T/pieces_small.py /tmp/pieces > $O/gates/build_small.log 2>&1
cat $O/gates/build_kaymuse.log $O/gates/build_creatures.log $O/gates/build_small.log | grep -E "$KEEP" | tee $O/gates/build_gates.txt
cp /tmp/pieces/*.glb $O/models/ 2>/dev/null; ls -la /tmp/pieces
step "builder mutations"
# a wrong CONFIG value must fail its gate: (builder, output, PIECES_MUT, the FAIL line expected)
mut() { PIECES_MUT="$3" $BPY $T/$1 $2 > /tmp/pmut/log.txt 2>&1; if grep -q "^FAIL $4" /tmp/pmut/log.txt; then echo "MUT caught: $1 with $3 -> $(grep -m1 "^FAIL $4" /tmp/pmut/log.txt | cut -c1-120)"; else echo "MUT MISSED: $1 with $3 (no line 'FAIL $4')"; fi; }
{ mut pieces_kaymuse.py /tmp/pmut/kaymuse.glb "LIPS_MAT='kmSkin'" "kaymuse lower face"
  mut pieces_kaymuse.py /tmp/pmut/kaymuse.glb "STR_LEN=0.35" "kaymuse 冕 veil"
  mut pieces_kaymuse.py /tmp/pmut/kaymuse.glb "TORSO=[(0.60,0.0,0.37,0.27),(0.72,-0.01,0.39,0.27),(0.95,-0.02,0.45,0.26),(1.10,-0.02,0.47,0.24),(1.18,-0.02,0.40,0.21),(1.23,-0.02,0.20,0.15)]" "kaymuse reads as a woman"
  mut pieces_kaymuse.py /tmp/pmut/kaymuse.glb "BOARD_REAR=0.50" "kaymuse crown: board"
  mut pieces_kaymuse.py /tmp/pmut/kaymuse.glb "FINGER=0.0001;HAND_C=(0.3,0.1,0.9)" "kaymuse hands"
  mut pieces_kaymuse.py /tmp/pmut/kaymuse.glb "BUDGET=(1000,2600,900)" "kaymuse_lod0 tris"
  mut pieces_kaymuse.py /tmp/pmut/kaymuse.glb "REST_X=2.4" "kaymuse sits within"
  mut pieces_creatures.py /tmp/pmut "C_KNEE=(0.84,1.35)" "crab .* low and wide"
  mut pieces_creatures.py /tmp/pmut "W_HIP=(1.1,-0.05,1.40)" "wanderer .* tall and narrow"
  mut pieces_creatures.py /tmp/pmut "C_MOVE=(0.6,0.0,0.0,0.0,0.0,0.0)" "crab clip move"
  mut pieces_creatures.py /tmp/pmut "C_MOVE=(0.6,2.0,1.0,0.0,0.0,16.0)" "crab move reads apart"
  mut pieces_creatures.py /tmp/pmut "C_STUDS=(4,0.665,0.03)" "crab lid relief"
  mut pieces_creatures.py /tmp/pmut "DK='pcBlack'" "crab is bronze"
  mut pieces_creatures.py /tmp/pmut "C_FINGER_B=[(0.63,0.78,0.83),(0.60,0.96,0.85),(0.52,1.06,0.83)]" "crab pincers"
  mut pieces_creatures.py /tmp/pmut "W_LEG_W=(0.16,0.03,0.075)" "wanderer limbs"
  mut pieces_creatures.py /tmp/pmut "W_BILL=((0.0,0.58,2.585),(0.0,0.8,2.56))" "wanderer bill"
  mut pieces_creatures.py /tmp/pmut "W_WHEEL=(0.40,0.12,0.04,15,6,0.16)" "wanderer hip wheels"
  mut pieces_creatures.py /tmp/pmut "SHELL_W=0.0" "crab is bronze"
  mut pieces_small.py /tmp/pmut "PL_LEN=1.2" "plate [0-9]"
  mut pieces_small.py /tmp/pmut "PL_HW=(0.29,0.08)" "plate reads as armour"
  mut pieces_small.py /tmp/pmut "CR_LID=1" "leader crown reads"
  mut pieces_small.py /tmp/pmut "CR_POINTS=[(0,0.17,0.9),(-38,0.14,0.22),(38,0.14,0.22),(-66,0.10,0.14),(66,0.10,0.14)]" "leader crown [0-9]"
  mut pieces_small.py /tmp/pmut "MW_BRACES=3" "墨 wall frame"
  mut pieces_small.py /tmp/pmut "MW_POSTS=(-1.88,-0.63,0.63,1.88)" "墨 wall frame"
  mut pieces_small.py /tmp/pmut "MW_POSTS=(-2.7,-0.9,0.55,2.7)" "墨 wall [0-9]"
  mut pieces_small.py /tmp/pmut "DM_SIGIL=[(-0.045,0.028,0.034,0.034,0),(0.045,0.028,0.034,0.034,0),(-0.052,0.066,0.06,0.018,28),(0.052,0.066,0.06,0.018,-28),(0.0,-0.006,0.02,0.07,0),(0.0,-0.066,0.13,0.02,0),(-0.05,-0.042,0.02,0.03,0),(0.05,-0.042,0.02,0.03,0)]" "decree seal sigil"; } 2>&1 | tee $O/gates/build_mutations.txt
step "glb gates"
python3 $T/pieces_check.py /tmp/pieces --mutate 2>&1 | tee $O/gates/glb_gates.txt
step "shots"
mkdir -p assets/models/pieces && cp /tmp/pieces/*.glb assets/models/pieces/
node $T/pieces_shoot.mjs /tmp/pshots 2>&1 | tee $O/gates/shots.txt
step "measures and sheets"
python3 $T/pieces_measure.py /tmp/pshots --mutate 2>&1 | tee $O/gates/measures.txt
python3 $T/pieces_sheets.py /tmp/pshots $O/sheets 2>&1 | tee $O/gates/sheets.txt
rm -rf assets/models/pieces; git status --short | grep -v '^??' | head -5
echo "== summary"; cat $O/gates/build_gates.txt $O/gates/build_mutations.txt $O/gates/glb_gates.txt $O/gates/shots.txt $O/gates/measures.txt $O/gates/sheets.txt 2>/dev/null | grep -E "^FAIL|MUT MISSED|of .* pass|mutations caught|Traceback" | tee $O/summary.txt
nf=$(grep -c "^FAIL\|MUT MISSED\|Traceback" $O/summary.txt); echo "FAIL lines: $nf" | tee -a $O/summary.txt
du -sh $O; echo "RESULT done"
