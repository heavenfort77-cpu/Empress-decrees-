#!/bin/bash
# FIXB runner job (25 Nov, owner picks 02:1x-02:2x), round 2: repaint the changed textures in klad, prove the approved plaster unchanged, rebuild the
# architecture, tally and mercury GLBs, run every gate and mutation, shoot the rooms and props (brass sheet), measure on screen, make
# the review sheets, and hand back the deliverables in $OUT/deliver (art tool, not shipped).
# env: $BPY python with bpy, $KLAD klad binary, $OUT results folder.
set -u
export PYTHONDONTWRITEBYTECODE=1
NEW=mercury_matcap,signal_flags,pond_water,star_inlay
mkdir -p "$OUT/passes" "$OUT/deliver/tex" "$OUT/deliver/src" "$OUT/deliver/models/arch" /tmp/ops
echo "== paint $NEW"
python3 art/tools/arch_tex.py /tmp/ops 1024 $NEW | tee "$OUT/ops.txt"
python3 art/tools/paint_palace.py "$KLAD" /tmp/ops art/src assets/tex "$OUT/passes" "$NEW"
echo "== repaint check: approved hall_wall with PLASTER_K unset is unchanged"
mkdir -p /tmp/ops0; python3 art/tools/palace_tex.py /tmp/ops0 > /dev/null; python3 art/tools/paint_palace.py "$KLAD" /tmp/ops0 /tmp/src0 /tmp/tex0 /tmp/p0 hall_wall > /dev/null
python3 - <<'PY' | tee "$OUT/repro.txt"
import numpy as np
from PIL import Image
a = np.asarray(Image.open('assets/tex/hall_wall.png').convert('RGB')).astype(int); b = np.asarray(Image.open('/tmp/tex0/hall_wall.png').convert('RGB')).astype(int)
print('hall_wall repaint (PLASTER_K unset) mean abs diff vs committed', round(float(np.abs(a - b).mean()), 3))
for n, p in (('hall_wall approved', 'assets/tex/hall_wall.png'), ('mural_wall approved-matched', 'assets/tex/mural_wall.png')):
    c = np.asarray(Image.open(p).convert('RGB')).astype(float); r = (170, 750) if n.startswith('hall') else (450, 750); L = c[r[0]:r[1]] @ [0.2126, 0.7152, 0.0722]
    print(f'{n}: plaster mean lum {L.mean():.1f} (rows {r[0]}-{r[1]})')
PY
echo "== tex_check"; python3 art/tools/tex_check.py assets/tex 1 4 | tee "$OUT/tex_check.txt" | grep -E "FAIL|pass$"
echo "== tex_check mutation"; python3 art/tools/tex_check_mut.py assets/tex | tee "$OUT/tex_mut.txt" | grep -E "MISSED|caught$"
echo "== meshes"
cp -r assets/models/arch assets/models/arch_r2
$BPY art/tools/arch_blender.py "$PWD/assets/models/arch" 2>&1 | grep -E "^(PASS|FAIL)|pass$|Error|Traceback" | tee "$OUT/arch_gates.txt" | grep -E "FAIL|pass$|Error|throne|slip_rack|dais"
cp assets/models/arch/arch_report.json "$OUT/"; rm -f assets/models/arch/arch_report.json
for m in uv budget dims dais rack; do echo "mesh gate mutation $m: $(ARCH_MUT=$m $BPY art/tools/arch_blender.py /tmp/mut_$m 2>&1 | grep -c '^FAIL') FAIL lines (must be > 0)"; done | tee "$OUT/arch_mut.txt"
$BPY art/tools/tally_blender.py "$PWD/assets/models/tally.glb" 2>&1 | grep -E "^(PASS|FAIL)|pass$|Error|Traceback" | tee "$OUT/tally_gates.txt"
for m in budget stripes; do echo "tally gate mutation $m: $(TALLY_MUT=$m $BPY art/tools/tally_blender.py /tmp/tally_mut_$m.glb 2>&1 | grep -c '^FAIL') FAIL lines (must be > 0)"; done | tee "$OUT/tally_mut.txt"
$BPY art/tools/merc_blender.py "$PWD/assets/models/merc.glb" 2>&1 | grep -E "^(PASS|FAIL)|pass$|Error|Traceback" | tee "$OUT/merc_gates.txt"
echo "== shots"; node art/tools/fixb_shoot.mjs "$OUT/shots" 2>&1 | tee "$OUT/shots.txt" | grep -c " ok$"
grep -v " ok$" "$OUT/shots.txt" | head -20
echo "== on-screen gates"; python3 art/tools/fixb_measure.py "$OUT/shots" | tee "$OUT/measure.txt"
echo "== on-screen gate mutations"; python3 art/tools/fixb_measure.py "$OUT/shots" mut | tee "$OUT/measure_mut.txt" | grep -E "MISSED|caught$"
echo "== sheets"; python3 art/tools/fixb_sheets.py "$OUT/shots" assets/tex "$OUT/sheets"
cp art/tools/fixb_shoot.mjs "$OUT/" 2>/dev/null
# deliverables back to the session (committed from there): textures, klad sources, candidates, GLBs
for n in ${NEW//,/ }; do cp assets/tex/$n.png "$OUT/deliver/tex/"; cp -r art/src/$n.klad "$OUT/deliver/src/"; done
cp assets/models/arch/*.glb "$OUT/deliver/models/arch/"; cp assets/models/tally.glb assets/models/merc.glb "$OUT/deliver/models/"
# shots to jpg (masks stay png, they are tiny)
python3 - "$OUT/shots" <<'PY'
import os, sys
from PIL import Image
d = sys.argv[1]
for f in os.listdir(d):
    if f.endswith('.png') and not f.startswith('mask_'):
        Image.open(f'{d}/{f}').convert('RGB').save(f'{d}/{f[:-4]}.jpg', quality=85); os.remove(f'{d}/{f}')
PY
echo "RESULT done"
# leave the checkout clean (the workflow switches to ci-out after this script)
git checkout -q -- . && git clean -qfd assets art
