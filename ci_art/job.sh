# W1c art job (runner): build the twelve giants (gates), check the patina sheet, shoot the review set, make sheets and silhouette gates.
set -o pipefail
R=$(pwd)
$BPY art/tools/giant_blender.py assets/models/giants/giants.glb 2>&1 | grep -E "^(PASS|FAIL)|pass$|wrote|Error|rror" | tee "$OUT/gates.txt"
$BPY art/tools/giant_tex_check.py assets/tex/bronze_trim_patina.png | tee -a "$OUT/gates.txt"
node art/tools/giant_shoot.mjs "$OUT/shots" full 2>&1 | tee "$OUT/shots.log" | grep -v " ok " || true
$BPY art/tools/giant_sheets.py "$OUT/shots" "$OUT/sheets" 2>&1 | tee "$OUT/sheet_gates.txt"
cp assets/models/giants/giants.glb "$OUT/"
# keep the sheets; raw shots as JPEG (giant 0 all, others play awake / dormant only) to keep ci-out small
cd "$OUT/shots" && $BPY - <<'PY'
import os
from PIL import Image
for f in sorted(os.listdir('.')):
    if not f.endswith('.png'): continue
    keep = f.startswith('g00_') or f.endswith('_play_awake.png') or f.endswith('_play_dormant.png')
    if keep: Image.open(f).convert('RGB').save(f[:-4] + '.jpg', quality=82)
    os.remove(f)
PY
cd "$R"; du -sh "$OUT"
