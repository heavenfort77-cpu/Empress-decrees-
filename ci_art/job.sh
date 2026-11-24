#!/bin/bash
# W2 runner job: rebuild every W2 asset from source on a clean runner and prove the gates (art tool, not shipped).
# env: $BPY python with bpy, $KLAD klad binary, $OUT results folder.
set -u
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$OUT/shots" "$OUT/passes" /tmp/ops
cp -r assets/tex /tmp/tex_committed
N=$(python3 -c "import sys;sys.argv=['x','/tmp/x'];sys.path.insert(0,'art/tools');import arch_tex;print(','.join(f.__name__ for f in arch_tex.ALL))")
echo "== textures: $N"
python3 art/tools/arch_tex.py /tmp/ops 1024 | tee "$OUT/ops.txt"
python3 art/tools/paint_palace.py "$KLAD" /tmp/ops /tmp/src assets/tex "$OUT/passes" "$N"
python3 - <<'PY' | tee "$OUT/repro.txt"
import numpy as np, os
from PIL import Image
for f in sorted(os.listdir('/tmp/tex_committed')):
    a = np.asarray(Image.open('/tmp/tex_committed/' + f).convert('RGBA')).astype(int); b = np.asarray(Image.open('assets/tex/' + f).convert('RGBA')).astype(int)
    print(f, 'mean abs diff vs committed', round(float(np.abs(a - b).mean()), 3))
PY
echo "== tex_check"; python3 art/tools/tex_check.py assets/tex 1 4 | tee "$OUT/tex_check.txt" | grep -E "FAIL|pass$"
echo "== tex_check mutation"; python3 art/tools/tex_check_mut.py assets/tex | tee "$OUT/tex_mut.txt" | tail -1
echo "== meshes"; $BPY art/tools/arch_blender.py "$PWD/assets/models/arch" 2>&1 | grep -E "^(PASS|FAIL)|pass$|Error|Traceback" | tee "$OUT/arch_gates.txt" | grep -E "FAIL|pass$|Error"
cp assets/models/arch/arch_report.json "$OUT/" 2>/dev/null; rm -f assets/models/arch/arch_report.json
for m in uv budget dims; do echo "mesh gate mutation $m: $(ARCH_MUT=$m $BPY art/tools/arch_blender.py /tmp/mut_$m 2>&1 | grep -c '^FAIL') FAIL lines (must be > 0)"; done | tee "$OUT/arch_mut.txt"
echo "== shots"; node art/tools/shoot_arch.mjs "$OUT/shots" all 2>&1 | tee "$OUT/shots.txt" | tail -3
python3 art/tools/arch_sheets.py "$OUT/shots" "$OUT/sheets" | tee "$OUT/sheets.txt"
ls assets/models/arch | tee "$OUT/glbs.txt" | wc -l
echo "RESULT done"
