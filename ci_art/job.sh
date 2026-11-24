# W3 suits round job: klad sheets -> tex checks -> Blender build (nine suits) -> silhouette gates -> viewer shots. Results in $OUT.
set -o pipefail
mkdir -p /tmp/ops && python art/tools/suit_tex.py /tmp/ops 2>&1 | tee $OUT/tex_ops.txt
python art/tools/suit_paint.py $KLAD /tmp/ops $OUT/src $OUT/tex $OUT/strips 2>&1 | tee $OUT/paint.txt
python art/tools/tex_check.py $OUT/tex 2>&1 | tee $OUT/tex_check.txt
mkdir -p assets/tex assets/models/suits && cp $OUT/tex/*.png assets/tex/
$BPY art/tools/suit_blender.py -- $OUT/models all > $OUT/blender.log 2>&1; grep -E "^(PASS|FAIL)|of .* pass|Error|Traceback" $OUT/blender.log | tee $OUT/gates.txt
python art/tools/suit_sil.py $OUT/models $OUT/sil 2>&1 | tee $OUT/sil.txt
cp $OUT/models/*.glb assets/models/suits/
node art/tools/suit_shoot.mjs $OUT/shots $OUT/models/suits_info.json 2>&1 | tee $OUT/shots.txt
ls $OUT/shots | wc -l
echo JOB DONE
