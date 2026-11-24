# W5 art job (guard and rebels): klad sheet, texture checks, Blender builds with gates, GLB checks, preview sheets, three.js viewer shots.
set -u
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/.."
mkdir -p /tmp/ops "$OUT/tex_passes"
step() { echo "== $1"; }
step "klad fodder_trim"
python3 art/tools/fodder_tex.py /tmp/ops && python3 art/tools/paint_palace.py "$KLAD" /tmp/ops art/src assets/tex "$OUT/tex_passes" fodder_trim
step "tex_check"
python3 art/tools/tex_check.py assets/tex | tee "$OUT/tex_check.txt"
step "guard build"
$BPY art/tools/guard_build.py /tmp/gb 2>&1 | grep -E "^(PASS|FAIL|SUMMARY|wrote|Traceback|  File|[A-Za-z]*Error)" | tee "$OUT/guard_build.txt"
step "rebel build"
$BPY art/tools/rebel_build.py /tmp/rb 2>&1 | grep -E "^(PASS|FAIL|SUMMARY|wrote|Traceback|  File|[A-Za-z]*Error)" | tee "$OUT/rebel_build.txt"
mkdir -p assets/models/guard assets/models/rebels "$OUT/models/guard" "$OUT/models/rebels"
cp /tmp/gb/*.glb assets/models/guard/ && cp /tmp/rb/*.glb assets/models/rebels/
cp /tmp/gb/*.glb /tmp/gb/guard_gates.json "$OUT/models/guard/"; cp /tmp/rb/*.glb /tmp/rb/rebel_gates.json "$OUT/models/rebels/"
step "glb check"
python3 art/tools/glb_info.py assets/models/guard/*.glb assets/models/rebels/*.glb | tee "$OUT/glb_info.txt"
step "preview sheets and silhouette gates"
mkdir -p /tmp/pall && cp /tmp/gb/preview/*.npz /tmp/rb/preview/*.npz /tmp/pall/
python3 art/tools/fodder_preview.py /tmp/gb/preview "$OUT/preview_guard" zu,nu,dun,che,wz | tee "$OUT/sil_guard.txt"
python3 art/tools/fodder_preview.py /tmp/rb/preview "$OUT/preview_rebels" ls_ru,fs,ss,qs | tee "$OUT/sil_rebels.txt"
python3 art/tools/fodder_preview.py /tmp/pall "$OUT/preview_all" zu,nu,dun,che,wz,ls_ru,fs,ss,qs | tee "$OUT/sil_all.txt"
python3 art/tools/fodder_preview.py /tmp/rb/preview "$OUT/preview_schools" $(python3 -c "print(','.join('ls_'+s+'_wonly' for s in 'ru dao fa mo yinyang za ming zongheng nong'.split()))") --fight | tee "$OUT/sil_schools.txt"
step "viewer shots"
node art/tools/shoot_fodder.mjs "$OUT/shots" 2>&1 | tee "$OUT/shots.txt"
cp assets/tex/fodder_trim.png "$OUT/" && cp -r art/src/fodder_trim.klad "$OUT/" 2>/dev/null
git checkout -- art/tools/__pycache__ 2>/dev/null; git status --short | head -5
echo "RESULT done"
