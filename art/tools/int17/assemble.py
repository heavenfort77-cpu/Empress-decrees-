# Batch 17a: build assets/c from a runner's encodes and its per-texture picks. Usage: assemble.py REPO RUNDIR PICKJSON RUNID
# desk/<name>.ktx2 and phone/<name>.ktx2 = the picked mode (ETC1S if it passed every gate, else UASTC, else UASTC q4); a texture no KTX2 mode
# passed ships as the PNG (desk: the source; phone: the 512 px Lanczos source), so it is exact. models/ = every compressed GLB except the suits
# (their sources changed in SUITANIM 64b7bd5; they are encoded in 17f). manifest.json: file, bytes, sha256, source, source sha256, mode, numbers.
import sys, os, json, hashlib, shutil, glob
from PIL import Image
R, D, P, RUN = sys.argv[1:5]
pick = json.load(open(P)); out = f'{R}/assets/c'; shutil.rmtree(out, ignore_errors=True)
sha = lambda f: hashlib.sha256(open(f, 'rb').read()).hexdigest()
man = {'run': RUN, 'files': {}}
for k, v in sorted(pick.items()):
    st, n = k.split('/'); src = f'{R}/assets/tex/{n}.png'; os.makedirs(f'{out}/{st}', exist_ok=True)
    ok = v['mode'] != 'png'
    if ok: dst = f'{out}/{st}/{n}.ktx2'; shutil.copy(f'{D}/{st}/{v["mode"]}/{n}.ktx2', dst); mode = v['mode']
    else:
        dst = f'{out}/{st}/{n}.png'; im = Image.open(src); im = im.convert('RGBA') if im.mode in ('RGBA', 'P', 'LA') else im.convert('RGB')
        w, h = im.size; kk = min(1.0, 512 / max(w, h)) if st == 'phone' else 1.0
        (im.resize((int(w * kk), int(h * kk)), Image.LANCZOS) if kk < 1 else im).save(dst); mode = 'png'
    man['files'][os.path.relpath(dst, R)] = {'bytes': os.path.getsize(dst), 'sha256': sha(dst), 'source': os.path.relpath(src, R), 'source_sha256': sha(src), 'mode': mode,
                                           'psnr': v['psnr'], 'de': v['de'], 'tried': v.get('tried')}
for f in sorted(glob.glob(f'{D}/models/**/*.glb', recursive=True)):
    rel = os.path.relpath(f, f'{D}/models')
    if rel.startswith('suits/'): continue
    dst = f'{out}/models/{rel}'; os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy(f, dst); src = f'{R}/assets/models/{rel}'
    man['files'][os.path.relpath(dst, R)] = {'bytes': os.path.getsize(dst), 'sha256': sha(dst), 'source': os.path.relpath(src, R), 'source_sha256': sha(src), 'mode': 'meshopt'}
json.dump(man, open(f'{out}/manifest.json', 'w'), indent=1, ensure_ascii=False)
tot = lambda pre: sum(v['bytes'] for k, v in man['files'].items() if k.startswith('assets/c/' + pre))
print('ASSEMBLED', len(man['files']), 'files; desk', round(tot('desk') / 1e6, 2), 'MB, phone', round(tot('phone') / 1e6, 2), 'MB, models', round(tot('models') / 1e6, 2), 'MB; png picks', [k for k, v in man['files'].items() if v['mode'] == 'png'])
