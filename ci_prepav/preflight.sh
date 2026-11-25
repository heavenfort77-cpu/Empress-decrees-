#!/usr/bin/env bash
# PREFLIGHT (lead rule 25 Nov, RUNNERS.md): fail in the first minute when a tool, import, input or output folder is missing, or the tree is dirty.
# Usage: bash ci_prepav/preflight.sh <outdir>
set -u
F=0; ok() { echo "PRE ok   $*"; }; bad() { echo "PRE FAIL $*"; F=1; }
OUT=${1:-o}
# 1. tools
for t in node npx git; do command -v $t >/dev/null && ok "tool $t" || bad "tool $t missing"; done
node -e "import('playwright').then(m=>{const p=m.chromium.executablePath();require('fs').accessSync(p);console.log('PRE ok   chromium '+p)}).catch(e=>{console.log('PRE FAIL chromium '+e.message);process.exit(1)})" || F=1
# 2. imports and syntax of every script the job runs
for f in tests_draft/static-src.mjs tests_draft/fx-map.mjs tests_draft/fx-runtime.mjs tests_draft/mutate.mjs ci_prepav/perfprepav.mjs src/fx/fxevent.js src/fx/cards.js src/fx/fxmap.js src/fx/intensity.js src/audio/sound.js src/audio/options.js; do
  [ -f "$f" ] && node --check "$f" 2>/dev/null && ok "syntax $f" || bad "script $f missing or does not parse"; done
node -e "Promise.all(['./src/fx/fxmap.js','./src/audio/sound.js','./src/audio/options.js','./src/fx/intensity.js'].map(p=>import(p))).then(()=>console.log('PRE ok   module imports')).catch(e=>{console.log('PRE FAIL import '+e.message);process.exit(1)})" || F=1
# 3. inputs read, outputs written
for f in assets/vfx/vfx.json assets/vfx/vfx_soft_a.png assets/vfx/vfx_soft_b.png assets/vfx/vfx_ground.png assets/vfx/vfx_ramps.png art/vfx/vfx_map.json assets/tex/hall_floor.png lib/three.module.min.js probe/prepav/index.html; do
  [ -s "$f" ] && ok "input $f" || bad "input $f missing or empty"; done
mkdir -p "$OUT" && [ -w "$OUT" ] && ok "output $OUT" || bad "output $OUT not writable"
# 4. clean tree, no tracked build files
[ -z "$(git status --porcelain --untracked-files=no)" ] && ok "tree clean" || bad "tracked files modified: $(git status --porcelain --untracked-files=no | head -3 | tr '\n' ' ')"
[ -z "$(git ls-files '*.pyc' '__pycache__/*' 'node_modules/*')" ] && ok "no tracked build files" || bad "tracked build files present"
echo "PREFLIGHT $([ $F = 0 ] && echo PASS || echo FAIL)"
exit $F
