#!/bin/bash
# FIX-A art job (owner picks 25 Nov 02:1x-02:2x): tread strip and selftests, cubs (Howler reshape, scrolling tread belts), guard
# (tread belts, chariot without canopy), rebels (non-school patch colours, bigger glint), giants (slimmer body, stronger motifs 02 05 07 08),
# suits (7.5 heads); builder gates, silhouette gates, GLB re-read, viewer shots and sheets. Everything lands in $OUT.
set -u
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/.."
O=$OUT; mkdir -p $O/checks $O/apex $O/guard $O/giants $O/suits $O/models/apex $O/models/guard $O/models/rebels $O/models/giants $O/models/suits
step() { echo "== $1 $(date +%H:%M:%S)"; }
jpg() { python3 - "$@" <<'PY'
import sys, os
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]; os.makedirs(dst, exist_ok=True); n = 0
for f in sys.argv[3:]:
    p = os.path.join(src, f + '.png')
    if os.path.exists(p): Image.open(p).convert('RGB').save(os.path.join(dst, f + '.jpg'), quality=85); n += 1
print('jpg', n, 'of', len(sys.argv) - 3, '->', dst)
PY
}
step "checks"
python3 art/tools/tread_tex.py --check assets/tex/tread_belt.png --mutate | tee $O/checks/tread_tex.txt
python3 art/tools/tread_kit.py | tee $O/checks/tread_kit.txt
python3 art/tools/rebel_patch_check.py --mutate | tee $O/checks/rebel_patch.txt
step "cubs"
$BPY art/tools/apex_cubs.py -- assets/models/apex $O/apex/cubs_gates.json 2>&1 | grep -E "^(PASS|FAIL)|of [0-9]+ pass|wrote|Error|Traceback|line [0-9]" | tee $O/apex/cubs_gates.txt
cp assets/models/apex/stalker.glb assets/models/apex/howler.glb $O/models/apex/
step "guard"
$BPY art/tools/guard_build.py /tmp/gb 2>&1 | grep -E "^(PASS|FAIL|SUMMARY|wrote|Traceback|  File|[A-Za-z]*Error)" | tee $O/guard/guard_build.txt
step "rebels"
$BPY art/tools/rebel_build.py /tmp/rb 2>&1 | grep -E "^(PASS|FAIL|SUMMARY|wrote|Traceback|  File|[A-Za-z]*Error)" | tee $O/guard/rebel_build.txt
cp /tmp/gb/*.glb assets/models/guard/ && cp /tmp/rb/*.glb assets/models/rebels/
cp /tmp/gb/*.glb /tmp/gb/guard_gates.json $O/models/guard/; cp /tmp/rb/*.glb /tmp/rb/rebel_gates.json $O/models/rebels/
python3 art/tools/glb_info.py assets/models/guard/*.glb assets/models/rebels/*.glb | tee $O/guard/glb_info.txt
mkdir -p /tmp/pall && cp /tmp/gb/preview/*.npz /tmp/rb/preview/*.npz /tmp/pall/
python3 art/tools/fodder_preview.py /tmp/gb/preview $O/guard/preview_guard zu,nu,dun,che,wz | tee $O/guard/sil_guard.txt
python3 art/tools/fodder_preview.py /tmp/rb/preview $O/guard/preview_rebels ls_ru,fs,ss,qs | tee $O/guard/sil_rebels.txt
python3 art/tools/fodder_preview.py /tmp/pall $O/guard/preview_all zu,nu,dun,che,wz,ls_ru,fs,ss,qs | tee $O/guard/sil_all.txt
python3 art/tools/fodder_preview.py /tmp/rb/preview $O/guard/preview_schools $(python3 -c "print(','.join('ls_'+s+'_wonly' for s in 'ru dao fa mo yinyang za ming zongheng nong'.split()))") --fight | tee $O/guard/sil_schools.txt
step "giants"
$BPY art/tools/giant_blender.py assets/models/giants/giants.glb 2>&1 | grep -E "^(PASS|FAIL)|pass$|wrote|Error|rror" | tee $O/giants/gates.txt
python3 art/tools/giant_tex_check.py assets/tex/bronze_trim_patina.png | tee -a $O/giants/gates.txt
cp assets/models/giants/giants.glb $O/models/giants/
node art/tools/giant_shoot.mjs /tmp/gshots full 2>&1 | tee $O/giants/shots.log | grep -v " ok " || true
python3 art/tools/giant_sheets.py /tmp/gshots /tmp/gsheets 2>&1 | tee $O/giants/sheet_gates.txt
jpg /tmp/gsheets $O/giants/sheets $(cd /tmp/gsheets && ls *.png | sed 's/\.png$//')
jpg /tmp/gshots $O/giants/shots $(for i in 00 01 02 03 04 05 06 07 08 09 10 11; do echo g${i}_play_awake g${i}_play_dormant; done) g02_slam_windup g05_slam_windup g07_slam_windup g08_slam_windup
step "suits"
$BPY art/tools/suit_blender.py -- /tmp/suits all > $O/suits/blender.log 2>&1; grep -E "^(PASS|FAIL)|of .* pass|Error|Traceback" $O/suits/blender.log | tee $O/suits/gates.txt
python3 art/tools/suit_sil.py /tmp/suits $O/suits/sil 2>&1 | tee $O/suits/sil.txt
cp /tmp/suits/*.glb assets/models/suits/ && cp /tmp/suits/*.glb /tmp/suits/suits_info.json $O/models/suits/
node art/tools/suit_shoot.mjs /tmp/sshots /tmp/suits/suits_info.json 2>&1 | tee $O/suits/shots.txt | grep -v " ok" || true
python3 art/tools/suit_sheet.py /tmp/sshots /tmp/ssheets
jpg /tmp/ssheets $O/suits/sheets $(cd /tmp/ssheets && ls *.png | sed 's/\.png$//')
jpg /tmp/sshots $O/suits lineup_play lineup_wide lineup_sil_front fa_34 ru_34 mo_34
step "apex shots"
node art/tools/apex_shoot.mjs /tmp/ashots 2>&1 | tee $O/apex/shots.txt | grep -v " ok$" || true
python3 art/tools/apex_sheet.py /tmp/ashots /tmp/asheets art/apex/concepts | tee -a $O/apex/shots.txt
jpg /tmp/asheets $O/apex cubs_sheet play_sheet
jpg /tmp/ashots $O/apex howler_front howler_34 howler_side howler_back howler_attack_windup howler_move howler_sil howler_lods stalker_34 stalker_sil play
step "fodder shots"
node art/tools/shoot_fodder.mjs /tmp/fshots 2>&1 | tee $O/guard/shots.txt | grep -v " ok " || true
jpg /tmp/fshots $O/guard/viewer lineup_guard lineup_guard_wide lineup_guard_sil lineup_rebels schools che_turn_0 che_turn_35 che_turn_90 che_tell che_lods che_scroll_0 che_scroll_half che_scroll_link zu_turn_35 ss_tell ss_turn_35 ls_turn_35
# tracked models and textures were rebuilt above (copies are in $OUT); restore them so the ci-out step can switch branches
git checkout -- assets art 2>/dev/null; git status --short | grep -v '^??' | head -5
du -sh $O; echo "RESULT done"
