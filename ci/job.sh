#!/bin/bash
# INT 17c real-GPU job (macOS runner). PREFLIGHT first (tools, imports, inputs, outputs, clean tree; fails in the first minute), then the probe and the gates.
set -euo pipefail
if [ "${1:-}" = preflight ]; then
  echo PREFLIGHT start
  command -v node >/dev/null || { echo "PREFLIGHT missing node"; exit 1; }
  node -e "require('playwright').chromium.executablePath() && console.log('chromium ok')"
  for f in index.html index_base.html ci_probe/perfgpu.mjs ci_probe/gates17c.mjs ci_probe/scenes.txt src/chars.js src/palace_art.js src/fx/fxevent.js lib/jsm/loaders/GLTFLoader.js lib/jsm/libs/meshopt_decoder.module.js assets/c/manifest.json art/suits/anim/suits_info.json assets/vfx/vfx.json; do
    test -f "$f" || { echo "PREFLIGHT missing $f"; exit 1; }; done
  node --check ci_probe/perfgpu.mjs; node --check ci_probe/gates17c.mjs
  grep -q "perfRing" index.html || { echo "PREFLIGHT index.html has no perfRing hook"; exit 1; }
  mkdir -p out && test -w out
  test -z "$(git status --porcelain --untracked-files=no)" || { echo "PREFLIGHT tree not clean"; git status --porcelain --untracked-files=no | head; exit 1; }
  echo PREFLIGHT PASS; exit 0
fi
(while true; do echo "T $(date +%s)"; top -l 2 -s 1 -n 6 -o cpu -stats pid,command,cpu,state | tail -7; done) > top.txt 2>&1 &
TP=$!
PURGE=${PURGE:-1} node ci_probe/perfgpu.mjs 2>&1 | tee perf.txt || true
kill $TP || true
node ci_probe/gates17c.mjs perf.txt 2>&1 | tee gates.txt
