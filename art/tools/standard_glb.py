#!/usr/bin/env python3
"""Re-read check of assets/models/standard.glb (C12 school emblem standard) without Blender: what the game would load.
PASS/FAIL per rule: LOD0 skinned on 4 joints, LOD1/LOD2 static; triangles per LOD; banner material alpha-tested (alphaMode MASK, cutoff
0.5, double sided, no BLEND anywhere); height in the hall range (glTF y up); banner UVs inside atlas cell 0; skin weights sum 1 on every
vertex; clip 'idle' 2.0 s, only cloth joints animated (the pole channel, if written, is constant); extras: nine schools in CONFIG order.
Usage: python3 standard_glb.py FILE.glb [--mut blend|skin|clip|uv|schools]   (--mut breaks the parsed file on purpose: must FAIL)
"""
import json, struct, sys

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Triangle limits: LOD0 (300 rigid + 48 card), LOD1, LOD2.
TRIS = (348, 130, 45)
# Height range, m; clip length, s; atlas cell (u, v) span.
HEIGHT, LOOP, CELL = (3.0, 4.0), 2.0, (0.2, 0.5)
SCHOOLS = 'ru,dao,fa,mo,yinyang,za,ming,zongheng,nong'

f = sys.argv[1]; MUT = sys.argv[sys.argv.index('--mut') + 1] if '--mut' in sys.argv else ''
b = open(f, 'rb').read(); jl = struct.unpack_from('<I', b, 12)[0]; g = json.loads(b[20:20 + jl])
binc = b[20 + jl + 8:]
A = g['accessors']; BV = g['bufferViews']
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}; CT = {5126: ('f', 4, None), 5121: ('B', 1, 255.0), 5123: ('H', 2, 65535.0), 5125: ('I', 4, None)}


def read(i):
    a = A[i]; bv = BV[a['bufferView']]; fmt, sz, norm = CT[a['componentType']]; n = NC[a['type']]
    stride = bv.get('byteStride', sz * n); off = bv.get('byteOffset', 0) + a.get('byteOffset', 0); out = []
    for k in range(a['count']):
        v = struct.unpack_from('<' + fmt * n, binc, off + k * stride); out.append([x / norm for x in v] if norm and a.get('normalized', fmt != 'I') else list(v))
    return out


if MUT == 'blend': [m.update(alphaMode='BLEND') for m in g['materials'] if m.get('name') == 'palBanner']
if MUT == 'skin': [n.pop('skin', None) for n in g['nodes']]
if MUT == 'clip': g['animations'] = []
if MUT == 'schools': [n['extras'].update(schools='ru,dao') for n in g['nodes'] if n.get('extras', {}).get('schools')]
fails = n_ = 0
def rule(ok, line):
    global fails, n_
    n_ += 1; fails += not ok; print(('PASS ' if ok else 'FAIL ') + 'glb ' + line)

nodes = {n.get('name'): n for n in g['nodes']}
mats = g.get('materials', [])
def tris(node): return sum((A[p['indices']]['count'] if 'indices' in p else A[p['attributes']['POSITION']]['count']) // 3 for p in g['meshes'][node['mesh']]['primitives'])
l0, l1, l2 = nodes.get('standard_lod0'), nodes.get('standard_lod1'), nodes.get('standard_lod2')
skin = g['skins'][l0['skin']] if l0 and 'skin' in l0 else None
rule(bool(skin) and len(skin['joints']) == 4, f'standard_lod0 skinned on {len(skin["joints"]) if skin else 0} joints (pole + 3 cloth)')
rule(bool(l1 and l2) and 'skin' not in l1 and 'skin' not in l2, 'standard_lod1 and standard_lod2 present, static')
for node, lim, nm in ((l0, TRIS[0], 'lod0'), (l1, TRIS[1], 'lod1'), (l2, TRIS[2], 'lod2')):
    t = tris(node) if node else 10 ** 6; rule(t <= lim, f'{nm} tris {t} (max {lim})')
ban = [m for m in mats if m.get('name') == 'palBanner']
rule(len(ban) == 1 and ban[0].get('alphaMode') == 'MASK' and ban[0].get('alphaCutoff') == 0.5 and ban[0].get('doubleSided') is True
     and not any(m.get('alphaMode') == 'BLEND' for m in mats), f'banner alpha-tested: {[(m.get("name"), m.get("alphaMode", "OPAQUE"), m.get("alphaCutoff")) for m in ban]}, no BLEND material')
ys = [p['attributes']['POSITION'] for p in g['meshes'][l0['mesh']]['primitives']]
top = max(A[i]['max'][1] for i in ys); bot = min(A[i]['min'][1] for i in ys)
rule(HEIGHT[0] <= top <= HEIGHT[1] and abs(bot) < 0.01, f'height {top:.2f} m (range {HEIGHT}), foot {bot:.3f}')
bi = [k for k, m in enumerate(mats) if m.get('name') == 'palBanner']
for node, nm in ((l0, 'lod0'), (l1, 'lod1'), (l2, 'lod2')):
    uv = [x for p in g['meshes'][node['mesh']]['primitives'] if p.get('material') in bi for x in read(p['attributes']['TEXCOORD_0'])]
    if MUT == 'uv': uv = [[u * 1.4, v] for u, v in uv]
    us = [u for u, v in uv]; vs = [v for u, v in uv]
    rule(bool(uv) and min(us) >= -1e-4 and max(us) <= CELL[0] + 1e-4 and min(vs) >= -1e-4 and max(vs) <= CELL[1] + 1e-4,
         f'{nm} banner UVs in cell 0: u {min(us or [0]):.3f}-{max(us or [0]):.3f}, v {min(vs or [0]):.3f}-{max(vs or [0]):.3f}')
wbad = 0; nv = 0
for p in g['meshes'][l0['mesh']]['primitives']:
    if 'WEIGHTS_0' not in p['attributes']: wbad += A[p['attributes']['POSITION']]['count']; continue
    for w in read(p['attributes']['WEIGHTS_0']): nv += 1; wbad += abs(sum(w) - 1) > 0.01
rule(wbad == 0 and nv > 0, f'lod0 skin weights sum 1 on {nv - wbad} of {nv} vertices (4 per vertex max by format)')
an = {a['name']: a for a in g.get('animations', [])}; idle = an.get('idle')
if idle:
    dur = max(A[s['input']]['max'][0] for s in idle['samplers']); jn = {j: g['nodes'][j]['name'] for j in skin['joints']} if skin else {}
    moving = set()
    for ch in idle['channels']:
        out = read(idle['samplers'][ch['sampler']]['output'])
        if max(max(abs(a - b) for a, b in zip(o, out[0])) for o in out) > 1e-5: moving.add(g['nodes'][ch['target']['node']]['name'])
    rule(abs(dur - LOOP) <= 0.04 and moving and all(m.startswith('cloth_') for m in moving), f'clip idle {dur:.2f} s (loop {LOOP}), animated joints {sorted(moving)} (pole still)')
else:
    rule(False, f'clip idle missing (clips {sorted(an)})')
ex = [n.get('extras', {}) for n in g['nodes'] if n.get('extras', {}).get('schools')]
rule(bool(ex) and ex[0]['schools'] == SCHOOLS and ex[0].get('atlas') == 'assets/tex/school_standards.png', f'extras schools {ex[0]["schools"] if ex else None} atlas {ex[0].get("atlas") if ex else None}')
print(f'{n_ - fails} of {n_} pass')
