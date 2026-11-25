#!/bin/sh
# PREFLIGHT (lead RULE 25 Nov, /home/claude/RUNNERS.md): fail in the first minute if any tool, import, input or output folder is missing,
# or if tracked build files would block the ci-out push. Usage: sh ci_probe/chr_preflight.sh <out dir>
set -e
OUT=${1:-chr_out}
fail() { echo "PREFLIGHT FAIL $*"; exit 1; }
for t in node git; do command -v $t >/dev/null || fail "tool $t"; done
node -e "import('playwright').then(async (m) => { const p = m.chromium.executablePath(); require('fs').accessSync(p); console.log('chromium ' + p); }).catch((e) => { console.log('PREFLIGHT FAIL playwright ' + e.message); process.exit(1); })"
for f in src/chars.js ci_probe/chars.html ci_probe/chrperf.mjs tests_draft/chars-static.mjs tests_draft/chars-checks.mjs tests_draft/chars-page-checks.mjs \
  lib/three.module.min.js lib/three.core.min.js lib/jsm/loaders/GLTFLoader.js lib/jsm/loaders/KTX2Loader.js lib/jsm/libs/meshopt_decoder.module.js \
  lib/jsm/libs/basis/basis_transcoder.js lib/jsm/libs/basis/basis_transcoder.wasm art/suits/anim/suits_info.json index.html assets/c/desk/hall_floor.ktx2; do
  [ -s "$f" ] || fail "input $f"; done
for id in ru dao fa mo yy za ming zh nong; do [ -s assets/models/suits/$id.glb ] || fail "input suit $id"; done
for f in guard/zu guard/nu guard/dun guard/che guard/wz rebels/ls rebels/fs rebels/ss rebels/qs apex/tiger apex/stalker apex/howler giants/giants; do [ -s assets/c/models/$f.glb ] || fail "input $f"; done
for s in suit_lamellar suit_bronze suit_cloth bronze_trim_brass bronze_trim_patina fodder_trim tread_belt apex_patina; do [ -s assets/c/desk/$s.ktx2 ] || [ -s assets/tex/$s.png ] || fail "sheet $s"; done
mkdir -p "$OUT/shots" || fail "mkdir $OUT"
[ -z "$(git ls-files | grep -E '\.pyc$|__pycache__|chr_out/|node_modules/')" ] || fail "tracked build files"
[ -z "$(git status --porcelain --untracked-files=no)" ] || fail "tree not clean: $(git status --porcelain --untracked-files=no | head -3)"
echo "PREFLIGHT PASS"
