# Batch 17a gates on the decoded images and models. Usage: metrics.py REPO STAGE OUT. Prints one line per gate and RESULT; writes OUT/manifest_pick.json.
# T1 every texture encodes and loads; T2 desk PSNR >= 35 dB and mean dE2000 <= 2 vs the source PNG (ETC1S first, UASTC + zstd if ETC1S fails);
# T3 the same for the phone set vs its 512 px source; T4 alpha cards: pixels whose alpha crosses 0.5 <= 1%; T5 tex_check ratchet (no FAIL on a
# decoded image that the source does not have); T6 the GPU route (KTX2Loader's own format choice) loads every picked file with a full mip chain.
# M1-M6 models: compressed and loaded; triangles per mesh equal; bounds within 2 mm; clips equal (name, duration within 1 ms); joints equal;
# vertices within 2 mm in the rest pose and at 0 and half of every clip; UVs within 1/2048. Mutants must each fail the gate named.
import sys, json, os, glob, subprocess, shutil
import numpy as np
from PIL import Image
R, S, O = sys.argv[1:4]
def load_raw(tag):
    p = f'{O}/{tag}.rgba'
    if not os.path.exists(p): return None
    return np.fromfile(p, np.uint8)
def lab(rgb):
    c = rgb / 255.0; c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]); xyz = c @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)
def de2000(a, b):
    L1, a1, b1 = a[..., 0], a[..., 1], a[..., 2]; L2, a2, b2 = b[..., 0], b[..., 1], b[..., 2]
    C1, C2 = np.hypot(a1, b1), np.hypot(a2, b2); Cm = (C1 + C2) / 2; G = 0.5 * (1 - np.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2; C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p, h2p = np.degrees(np.arctan2(b1, a1p)) % 360, np.degrees(np.arctan2(b2, a2p)) % 360
    dL, dC = L2 - L1, C2p - C1p; dh = h2p - h1p; dh = np.where(dh > 180, dh - 360, np.where(dh < -180, dh + 360, dh)); dh = np.where(C1p * C2p == 0, 0, dh)
    dH = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dh / 2)); Lm, Cmp = (L1 + L2) / 2, (C1p + C2p) / 2
    hs = h1p + h2p; hm = np.where(C1p * C2p == 0, hs, np.where(np.abs(h1p - h2p) <= 180, hs / 2, np.where(hs < 360, (hs + 360) / 2, (hs - 360) / 2)))
    T = 1 - 0.17 * np.cos(np.radians(hm - 30)) + 0.24 * np.cos(np.radians(2 * hm)) + 0.32 * np.cos(np.radians(3 * hm + 6)) - 0.2 * np.cos(np.radians(4 * hm - 63))
    SL = 1 + 0.015 * (Lm - 50) ** 2 / np.sqrt(20 + (Lm - 50) ** 2); SC = 1 + 0.045 * Cmp; SH = 1 + 0.015 * Cmp * T
    RT = -2 * np.sqrt(Cmp ** 7 / (Cmp ** 7 + 25 ** 7)) * np.sin(np.radians(60 * np.exp(-((hm - 275) / 25) ** 2)))
    return np.sqrt((dL / SL) ** 2 + (dC / SC) ** 2 + (dH / SH) ** 2 + RT * (dC / SC) * (dH / SH))
def compare(src_png, tag):
    s = np.asarray(Image.open(src_png).convert('RGBA')).astype(np.float64); h, w = s.shape[:2]
    raw = load_raw(tag)
    if raw is None or raw.size != w * h * 4: return None
    d = raw.reshape(h, w, 4).astype(np.float64); best = None
    for orient, dd in (('top-first', d), ('bottom-first', d[::-1])):
        mse = np.mean((dd[..., :3] - s[..., :3]) ** 2); psnr = 99.0 if mse == 0 else 10 * np.log10(255 ** 2 / mse)
        if best is None or psnr > best['psnr']: best = {'psnr': psnr, 'orient': orient, 'img': dd}
    dd = best['img']; e = de2000(lab(s[..., :3]), lab(dd[..., :3]))
    best['de'] = float(e.mean()); best['de95'] = float(np.percentile(e, 95))
    has_a = s[..., 3].min() < 255
    best['aflip'] = float(np.mean((s[..., 3] >= 128) != (dd[..., 3] >= 128))) if has_a else 0.0
    best['has_alpha'] = bool(has_a)
    return best
fails, lines = [], []
def gate(name, ok, detail): lines.append(f'{"PASS" if ok else "FAIL"} {name}: {detail}'); (None if ok else fails.append(name))
src = {st: sorted(os.path.basename(f)[:-4] for f in glob.glob(f'{S}/src/{st}/*.png')) for st in ('desk', 'phone')}
pick, rep = {}, []
gpu = {r['tag']: r for r in json.load(open(f'{O}/tex_gpu.json'))['rows']}
rgba = {r['tag']: r for r in json.load(open(f'{O}/tex_rgba.json'))['rows']}
t1bad, t2bad, t3bad, t4bad = [], [], [], []
os.makedirs(f'{O}/decoded', exist_ok=True)
for st in ('desk', 'phone'):
    for n in src[st]:
        res = {}
        for mode in ('etc1s', 'uastc'):
            tag = f'{st}/{mode}/{n}'
            if not rgba.get('rgba/' + tag, {}).get('ok'): t1bad.append(tag); continue
            c = compare(f'{S}/src/{st}/{n}.png', 'rgba/' + tag)
            if c is None: t1bad.append(tag); continue
            c['ok'] = c['psnr'] >= 35 and c['de'] <= 2 and c['aflip'] <= 0.01; res[mode] = c
        m = 'etc1s' if res.get('etc1s', {}).get('ok') else 'uastc'
        c = res.get(m)
        if c is None: (t2bad if st == 'desk' else t3bad).append(f'{n} not decoded'); continue
        pick[f'{st}/{n}'] = {'mode': m, 'psnr': round(c['psnr'], 2), 'de': round(c['de'], 3), 'de95': round(c['de95'], 2), 'aflip': round(c['aflip'], 4), 'orient': c['orient'], 'bytes': os.path.getsize(f'{S}/{st}/{m}/{n}.ktx2'),
                             'etc1s': {k: round(v, 3) for k, v in res.get('etc1s', {}).items() if k in ('psnr', 'de', 'aflip')}}
        if not (c['psnr'] >= 35 and c['de'] <= 2): (t2bad if st == 'desk' else t3bad).append(f'{n} {m} psnr {c["psnr"]:.1f} dE {c["de"]:.2f}')
        if c['has_alpha'] and c['aflip'] > 0.01: t4bad.append(f'{st}/{n} {c["aflip"]:.4f}')
        if st == 'desk': Image.fromarray(c['img'].astype(np.uint8)[..., :3] if not c['has_alpha'] else c['img'].astype(np.uint8)).save(f'{O}/decoded/{n}.png')
gate('T1 encode + load (rgba route)', not t1bad, f'{sum(len(v) for v in src.values()) * 2 - len(t1bad)} of {sum(len(v) for v in src.values()) * 2}' + (' bad ' + ' '.join(t1bad[:8]) if t1bad else ''))
gate('T2 desk PSNR >= 35 and dE <= 2', not t2bad, f'{len(src["desk"]) - len(t2bad)} of {len(src["desk"])}' + (' bad ' + '; '.join(t2bad) if t2bad else ''))
gate('T3 phone PSNR >= 35 and dE <= 2', not t3bad, f'{len(src["phone"]) - len(t3bad)} of {len(src["phone"])}' + (' bad ' + '; '.join(t3bad) if t3bad else ''))
na = sum(1 for k, v in pick.items() if v['aflip'] > 0 or 'card' in k or k.split('/')[1] in ('garden_plants', 'school_standards', 'signal_flags', 'star_inlay'))
nalpha = sum(1 for k, v in pick.items() if k.startswith('desk/') and np.asarray(Image.open(f'{S}/src/desk/{k[5:]}.png').convert('RGBA'))[..., 3].min() < 255)
gate('T4 alpha flips <= 1%', not t4bad and nalpha >= 6, f'{nalpha} alpha textures (desk) checked; worst ' + str(max([v['aflip'] for v in pick.values()] + [0])) + (' bad ' + ' '.join(t4bad) if t4bad else ''))
def texcheck(d):
    r = subprocess.run([sys.executable, f'{R}/art/tools/tex_check.py', d], capture_output=True, text=True); return set(l.strip() for l in r.stdout.splitlines() if l.startswith('FAIL')), r.stdout
srcdir = f'{O}/srcpng'; os.makedirs(srcdir, exist_ok=True)
for n in src['desk']: shutil.copy(f'{S}/src/desk/{n}.png', f'{srcdir}/{n}.png')
fs, _ = texcheck(srcdir); fd, outd = texcheck(f'{O}/decoded'); new = sorted(fd - fs)
gate('T5 tex_check ratchet (decoded vs source)', not new and len(os.listdir(f'{O}/decoded')) == len(src['desk']) and len(src['desk']) > 0, f'source FAIL lines {len(fs)}, decoded {len(fd)}, new {len(new)}' + (' : ' + ' | '.join(new[:6]) if new else ''))
t6bad = []
for k, v in pick.items():
    st, n = k.split('/'); g = gpu.get(f'gpu/{st}/{v["mode"]}/{n}')
    w = Image.open(f'{S}/src/{st}/{n}.png').size[0]; want = int(np.log2(w)) + 1
    if not g or not g.get('ok') or g.get('mips', 0) < want or g.get('err'): t6bad.append(f'{k} {g and (g.get("mips"), g.get("err"), g.get("ok"))}')
caps = json.load(open(f'{O}/caps_gpu.json'))
fmts = sorted(set(str(gpu[t]['format']) for t in gpu if gpu[t].get('ok')))
gate('T6 GPU route loads every picked file with full mips', not t6bad and len(pick) == len(src['desk']) + len(src['phone']) and len(pick) > 0, f'{len(pick) - len(t6bad)} of {len(pick)}; formats {fmts}; caps ' + json.dumps({k: caps[k] for k in caps if k != 'workerConfig'}) + (' bad ' + '; '.join(t6bad[:6]) if t6bad else ''))
# Texture mutants
mm = {}
for f in sorted(glob.glob(f'{S}/mut/*.ktx2')):
    t = os.path.basename(f)[:-5]; kind, n = t.split('__')
    c = compare(f'{S}/src/desk/{n}.png', f'rgba/mut/{t}'); g = gpu.get(f'gpu/mut/{t}', {})
    if kind in ('q1', 'swap'): caught = c is not None and not (c['psnr'] >= 35 and c['de'] <= 2); gname = 'T2'
    elif kind == 'noalpha': caught = c is not None and c['aflip'] > 0.01; gname = 'T4'
    elif kind == 'nomip': caught = g.get('mips', 0) < 11; gname = 'T6'
    elif kind == 'poster':
        d = f'{O}/mutdec'; os.makedirs(d, exist_ok=True); Image.fromarray(c['img'].astype(np.uint8)[..., :3]).save(f'{d}/{n}.png'); fm, _ = texcheck(d)
        caught = bool(set(l for l in fm if n in l) - fs); gname = 'T5'
    mm[t] = (gname, caught)
gate('TM texture mutants caught', all(c for _, c in mm.values()) and len(mm) == 5, ', '.join(f'{k}->{g}:{"caught" if c else "MISSED"}' for k, (g, c) in mm.items()))
# Models
md = json.load(open(f'{O}/models.json')); rows = {r['tag']: r for r in md['rows']}
real = [t for t in rows if not t.startswith('mut/')]
def mgates(r):
    if not r.get('ok'): return {'M1': False}
    a, b = r['a'], r['b']; g = {'M1': True}
    g['M2'] = len(a['meshes']) == len(b['meshes']) and all(x['tris'] == y['tris'] for x, y in zip(a['meshes'], b['meshes']))
    g['M3'] = len(a['meshes']) == len(b['meshes']) and all(max(abs(p - q) for p, q in zip(x['min'] + x['max'], y['min'] + y['max'])) <= 0.002 for x, y in zip(a['meshes'], b['meshes']))
    g['M4'] = len(a['clips']) == len(b['clips']) and all(x[0] == y[0] and abs(x[1] - y[1]) <= 0.001 for x, y in zip(a['clips'], b['clips']))
    g['M5'] = all(x['joints'] == y['joints'] for x, y in zip(a['meshes'], b['meshes']))
    g['M6'] = r['wpos'] <= 0.002
    g['M7'] = r['wuv'] <= 1 / 2048
    return g
allg = {t: mgates(rows[t]) for t in real}
for k, name in (('M1', 'compressed and loaded'), ('M2', 'triangles per mesh equal'), ('M3', 'bounds within 2 mm'), ('M4', 'clips equal'), ('M5', 'joints equal'), ('M6', 'vertices within 2 mm in every pose'), ('M7', 'UVs within 1/2048')):
    bad = [t for t, g in allg.items() if not g.get(k, False)]
    extra = ''
    if k == 'M6': w = max(real, key=lambda t: rows[t].get('wpos', 9)); extra = f'; worst {rows[w].get("wpos", 0) * 1000:.2f} mm ({w} {rows[w].get("wpose", "")})'
    if k == 'M7': w = max(real, key=lambda t: rows[t].get('wuv', 9)); extra = f'; worst {rows[w].get("wuv", 0):.6f} ({w})'
    gate(f'{k} {name}', not bad, f'{len(real) - len(bad)} of {len(real)}{extra}' + (' bad ' + ' '.join(bad[:8]) + ' ' + ' '.join(str(rows[t].get('err', ''))[:80] for t in bad[:2]) if bad else ''))
want = {'decim': 'M2', 'dropclip': 'M4', 'shiftbone': 'M6'}
mres = []
for t, r in rows.items():
    if not t.startswith('mut/'): continue
    kind = t.split('/')[1].split('__')[0]; g = mgates(r); mres.append(f'{kind}->{want[kind]}:{"caught" if not g.get(want[kind], False) else "MISSED"}')
gate('MM model mutants caught', len(mres) == 3 and all('caught' in x for x in mres), ', '.join(mres))
sz_src = sum(os.path.getsize(f) for f in glob.glob(f'{R}/assets/models/**/*.glb', recursive=True)); sz_c = sum(os.path.getsize(f) for f in glob.glob(f'{S}/models/**/*.glb', recursive=True))
gi = f'{S}/models/giants/giants.glb'
lines.append(f'INFO models {sz_src / 1e6:.2f} MB -> {sz_c / 1e6:.2f} MB; giants {os.path.getsize(gi) / 1e6 if os.path.exists(gi) else -1:.2f} MB')
td = sum(v['bytes'] for k, v in pick.items() if k.startswith('desk/')); tp = sum(v['bytes'] for k, v in pick.items() if k.startswith('phone/'))
lines.append(f'INFO textures desk {td / 1e6:.2f} MB, phone {tp / 1e6:.2f} MB (PNG sources {sum(os.path.getsize(f) for f in glob.glob(R + "/assets/tex/*.png")) / 1e6:.2f} MB); modes ' + json.dumps({m: sum(1 for v in pick.values() if v['mode'] == m) for m in ('etc1s', 'uastc')}))
lines.append('INFO orient ' + json.dumps(sorted(set(v['orient'] for v in pick.values()))))
json.dump(pick, open(f'{O}/manifest_pick.json', 'w'), indent=1)
print('\n'.join(lines)); print(f'RESULT {"PASS" if not fails else "FAIL"} gates {len([l for l in lines if l.startswith(("PASS", "FAIL"))]) - len(fails)} of {len([l for l in lines if l.startswith(("PASS", "FAIL"))])}')
