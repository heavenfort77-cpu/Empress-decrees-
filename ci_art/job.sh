# Route proof: Blender rig test, klad version, one viewer shot.
set -e
$BPY art/tools/rig_test.py | grep -E "^(rigid|auto|RESULT)" | tee $OUT/rig.txt
$KLAD --version | tee $OUT/klad.txt
cp art/tools/rig_test.py /tmp/ && cp art/rigtest_*.glb $OUT/ 2>/dev/null || true
node art/tools/shoot_viewer.mjs $OUT/shots > $OUT/shots.txt 2>&1 || true
ls $OUT/shots | head
