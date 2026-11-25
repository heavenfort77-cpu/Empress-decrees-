#!/bin/bash
# Re-encode named textures whose PNG source changed after 17a (manifest check 1709 names them as stale), with the 17a settings of the manifest
# entry's mode (uastc: --uastc_quality 2 --zcmp 18; etc1s: --clevel 4 --qlevel 255), desk = the PNG as painted, phone = 512 px (prep.py).
# Runs on a GitHub runner (ci-run cmd mode). Usage: reencode.sh OUTBRANCH name [name...]. The new .ktx2 files and the manifest (bytes, sha256,
# source_sha256 updated; psnr/de left from 17a and marked stale_metrics) are pushed to OUTBRANCH (a ci-* branch), never to batches-3-5.
set -euo pipefail
OUT=$1; shift
python3 -m pip install -q --disable-pip-version-check pillow numpy 2>&1 | tail -2 || true
echo PREFLIGHT start; command -v python3 git curl sha256sum >/dev/null; python3 -c "import PIL, numpy"; test -f assets/c/manifest.json; echo PREFLIGHT PASS
curl -fsSL -o /tmp/ktx.deb https://github.com/KhronosGroup/KTX-Software/releases/download/v4.3.2/KTX-Software-4.3.2-Linux-x86_64.deb
sudo dpkg -i /tmp/ktx.deb >/dev/null; toktx --version
S=/tmp/stage; mkdir -p $S/src/desk $S/src/phone
for n in "$@"; do
  python3 - "$n" "$S/src" <<'PY'
import sys, numpy as np
from PIL import Image
n, S = sys.argv[1], sys.argv[2]
im = Image.open(f'assets/tex/{n}.png'); im = im.convert('RGBA') if im.mode in ('RGBA', 'LA', 'P') else im.convert('RGB')
if im.mode == 'RGBA' and np.asarray(im)[..., 3].min() == 255: im = im.convert('RGB')
im.save(f'{S}/desk/{n}.png'); w, h = im.size; k = min(1.0, 512 / max(w, h))
(im.resize((int(w * k), int(h * k)), Image.LANCZOS) if k < 1 else im).save(f'{S}/phone/{n}.png'); print('PREP', n, im.mode, im.size)
PY
  for set in desk phone; do
    mode=$(python3 -c "import json,sys; print(json.load(open('assets/c/manifest.json'))['files']['assets/c/$set/$n.ktx2']['mode'])")
    if [ "$mode" = uastc ]; then toktx --t2 --encode uastc --uastc_quality 2 --zcmp 18 --genmipmap --assign_oetf srgb "assets/c/$set/$n.ktx2" "$S/src/$set/$n.png"
    else toktx --t2 --encode etc1s --clevel 4 --qlevel 255 --genmipmap --assign_oetf srgb "assets/c/$set/$n.ktx2" "$S/src/$set/$n.png"; fi
    echo "ENC $set $n $mode $(stat -c %s assets/c/$set/$n.ktx2) bytes"
  done
done
python3 - "$@" <<'PY'
import json, sys, hashlib, os
M = json.load(open('assets/c/manifest.json')); h = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
for n in sys.argv[1:]:
    for s in ('desk', 'phone'):
        k = f'assets/c/{s}/{n}.ktx2'; e = M['files'][k]
        e['bytes'] = os.path.getsize(k); e['sha256'] = h(k); e['source_sha256'] = h(e['source']); e['stale_metrics'] = True
        print('MANIFEST', k, e['sha256'][:12], e['source_sha256'][:12])
json.dump(M, open('assets/c/manifest.json', 'w'), indent=1)
PY
git config user.name Claude; git config user.email noreply@anthropic.com
git checkout -q -B "$OUT"; git add assets/c; git commit -qm "re-encode $* (source changed after 17a)"; git push -q -f origin "$OUT"; echo "PUSHED $OUT $(git rev-parse --short HEAD)"
