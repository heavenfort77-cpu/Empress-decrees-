#!/bin/bash
# PREP-PAL runner job (branch prep-pal only). Usage: bash ci/job.sh preflight|checks|mutants K/N|perf  [out dir]
# Every mode runs the PREFLIGHT first (tools, imports, inputs, output folder, clean tree) and stops within the first minute if anything is missing.
set -o pipefail
MODE=${1:-preflight}; ARG=${2:-}; OUT=${OUT:-pal_out}
fail() { echo "PREFLIGHT FAIL $*"; exit 1; }
echo "== PREFLIGHT ($MODE)"
for t in node git; do command -v $t >/dev/null || fail "tool $t"; done
node -e "import('playwright').then((m) => { require('fs').accessSync(m.chromium.executablePath()); console.log('chromium ok'); }).catch((e) => { console.log('PREFLIGHT FAIL playwright ' + e.message); process.exit(1); })" || exit 1
for f in src/palace_art.js ci_pal/pal.html ci_pal/checks.mjs ci_pal/layout.mjs ci_pal/palrun.mjs ci_pal/webglmin.html index.html tests/static-check.mjs \
  lib/three.module.min.js lib/three.core.min.js lib/jsm/loaders/GLTFLoader.js lib/jsm/loaders/KTX2Loader.js lib/jsm/libs/meshopt_decoder.module.js \
  lib/jsm/libs/basis/basis_transcoder.js lib/jsm/libs/basis/basis_transcoder.wasm assets/c/manifest.json; do [ -s "$f" ] || fail "input $f"; done
node --check src/palace_art.js && node --check ci_pal/checks.mjs && node --check ci_pal/layout.mjs && node --check ci_pal/palrun.mjs || fail "syntax"
node --input-type=module -e "
import { readFileSync, existsSync } from 'node:fs';
const s = readFileSync('src/palace_art.js', 'utf8'), m = (k) => [...s.slice(s.indexOf(k + ': ['), s.indexOf(']', s.indexOf(k + ': ['))).matchAll(/'([a-z_0-9]+)'/g)].map((x) => x[1]);
const miss = [...m('archFiles').map((n) => 'assets/c/models/arch/' + n + '.glb'), ...m('propFiles').map((n) => 'assets/c/models/' + n + '.glb')].filter((f) => !existsSync(f));
const tex = [...s.matchAll(/(?:tex|burnt): '([a-z_]+)'/g)].map((x) => x[1]).filter((n) => !existsSync('assets/c/desk/' + n + '.ktx2') && !existsSync('assets/c/desk/' + n + '.png'));
if (miss.length || tex.length) { console.log('PREFLIGHT FAIL inputs ' + miss.concat(tex).join(' ')); process.exit(1); }
console.log('inputs ok: ' + (m('archFiles').length + m('propFiles').length) + ' GLBs, textures present');" || exit 1
grep -q "PAL_FULL_ROOMS" index.html || fail "index.html layout data"
mkdir -p "$OUT/shots" || fail "mkdir $OUT"
[ -z "$(git ls-files | grep -E '\.pyc$|__pycache__|pal_out/|node_modules/')" ] || fail "tracked build files"
[ -z "$(git status --porcelain --untracked-files=no)" ] || fail "tree not clean: $(git status --porcelain --untracked-files=no | head -3)"
echo "PREFLIGHT PASS"
case "$MODE" in
  preflight) exit 0 ;;
  checks) { echo "== static"; node tests/static-check.mjs; s=$?; [ $s -eq 0 ] && echo "PASS P0 static-check (src/palace_art.js PERFRAME rules)" || echo "FAIL P0 static-check"; } 2>&1 | tee "$OUT/static.txt"
          OUT=$OUT node ci_pal/palrun.mjs checks 2>&1 | tee "$OUT/checks.txt"; c=$?; grep -q "^PASS P0" "$OUT/static.txt" || c=1; exit $c ;;
  mutants) OUT=$OUT node ci_pal/palrun.mjs mutants "$ARG" 2>&1 | tee "$OUT/mutants.txt" ;;
  perf) OUT=$OUT node ci_pal/palrun.mjs perf 2>&1 | tee "$OUT/perf.txt" ;;
  *) echo "unknown mode $MODE"; exit 2 ;;
esac
