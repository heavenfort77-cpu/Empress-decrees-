#!/usr/bin/env python3
"""GLB gates for the PIECES round (no Blender): per piece glTF valid (container, chunk sizes, every accessor inside the buffer, indices
inside the vertex count, finite positions), LODs present and ordered inside the triangle budgets, materials all in the table
(art/tools/pieces_mats.json), and for the rigged pieces: skinned LOD0 with weights summing to 1, the clips present, moving and looping.
--mutate: one mutation per gate on an in-memory copy of crab.glb; each must turn its gate to FAIL (MUT caught / MUT MISSED).
Usage: python3 pieces_check.py GLBDIR [--mutate]"""
import copy, json, os, struct, sys
import numpy as np

# CONFIG
# Per piece: triangle budgets LOD0/1/2 and the clips the game needs.
SPEC = {'kaymuse': ((10000, 2600, 900), ['idle']), 'crab': ((3000, 1200, 450), ['idle', 'move']), 'wanderer': ((3000, 1200, 450), ['idle', 'move']),
        'plate': ((499, 400, 220), []), 'leader_crown': ((499, 400, 220), []), 'mo_wall': ((499, 400, 220), []), 'decree_mark': ((499, 400, 220), [])}
# A clip moves when some channel's keys differ by more than this; it loops when every channel's last key equals its first within this.
MOVE_EPS, LOOP_EPS = 1e-3, 2e-3
# Shortest clip, s.
CLIP_MIN_S = 0.3
D = sys.argv[1]
TABLE = set(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pieces_mats.json')))) - {'_note'}
COMP = {5120: 'i1', 5121: 'u1', 5122: 'i2', 5123: 'u2', 5125: 'u4', 5126: 'f4'}; NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}

def parse(b):
    if len(b) < 28 or b[:4] != b'glTF': raise ValueError('not a GLB')
    ver, total = struct.unpack_from('<II', b, 4)
    if ver != 2 or total != len(b): raise ValueError(f'header: version {ver}, length {total} against {len(b)} bytes')
    n, kind = struct.unpack_from('<II', b, 12)
    if kind != 0x4E4F534A: raise ValueError('first chunk is not JSON')
    g = json.loads(b[20:20 + n]); o = 20 + n; m, kind2 = struct.unpack_from('<II', b, o)
    if kind2 != 0x004E4942 or o + 8 + m > len(b): raise ValueError('BIN chunk missing or cut')
    return g, bytes(b[o + 8:o + 8 + m])

def acc(g, binb, i):
    a = g['accessors'][i]; bv = g['bufferViews'][a['bufferView']]; n = NC[a['type']]; dt = np.dtype('<' + COMP[a['componentType']])
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0); st = bv.get('byteStride', 0) or dt.itemsize * n
    if off + (a['count'] - 1) * st + dt.itemsize * n > len(binb) or off + (a['count'] - 1) * st + dt.itemsize * n > bv.get('byteOffset', 0) + bv['byteLength']:
        raise ValueError(f'accessor {i} runs past its buffer')
    if st == dt.itemsize * n: return np.frombuffer(binb, dt, a['count'] * n, off).reshape(a['count'], n)
    return np.stack([np.frombuffer(binb, dt, n, off + k * st) for k in range(a['count'])])

def check(key, b):
    """-> {gate: (ok, text)}"""
    out = {}; budget, clips = SPEC[key]
    try:
        g, binb = parse(b); meshes = {}
        for nd in g['nodes']:
            if 'mesh' not in nd: continue
            t = 0
            for p in g['meshes'][nd['mesh']]['primitives']:
                idx = acc(g, binb, p['indices']); pos = acc(g, binb, p['attributes']['POSITION'])
                if idx.max() >= len(pos): raise ValueError(f"{nd['name']}: index {idx.max()} past {len(pos)} vertices")
                if not np.isfinite(pos).all(): raise ValueError(f"{nd['name']}: non-finite position")
                t += g['accessors'][p['indices']]['count'] // 3
            meshes[nd['name']] = (t, nd)
        for a in g.get('animations', []):
            for s in a['samplers']: acc(g, binb, s['input']); acc(g, binb, s['output'])
        out['valid'] = (True, f'{key} glTF valid: {len(b)} bytes, {len(meshes)} meshes, {len(g["accessors"])} accessors inside the buffer')
    except Exception as e:
        out['valid'] = (False, f'{key} glTF valid: {type(e).__name__} {e}'); return out
    ts = [meshes.get(f'{key}_lod{i}', (0, None))[0] for i in range(3)]
    out['lods'] = (all(ts) and ts[0] > ts[1] > ts[2], f'{key} LODs present and ordered: lod0 {ts[0]}, lod1 {ts[1]}, lod2 {ts[2]} tris')
    out['tris'] = (all(0 < t <= lim for t, lim in zip(ts, budget)), f'{key} tris {ts} inside the budgets {list(budget)}')
    names = sorted({m['name'] for m in g.get('materials', [])}); unk = [n for n in names if n not in TABLE]
    out['mats'] = (bool(names) and not unk, f'{key} materials {names} all in pieces_mats.json' + (f' (unknown {unk})' if unk else ''))
    if clips:
        nd = meshes.get(f'{key}_lod0', (0, {}))[1] or {}; ok = 'skin' in nd; bad = -1
        if ok:
            bad = 0
            for p in g['meshes'][nd['mesh']]['primitives']:
                w = acc(g, binb, p['attributes']['WEIGHTS_0']).astype(float)
                if g['accessors'][p['attributes']['WEIGHTS_0']]['componentType'] != 5126: w = w / np.iinfo(COMP[g['accessors'][p['attributes']['WEIGHTS_0']]['componentType']]).max
                bad += int((abs(w.sum(1) - 1) > 0.02).sum())
        out['skin'] = (ok and bad == 0, f'{key}_lod0 skinned, weights sum 1 ({bad} bad vertices)')
        an = {a['name']: a for a in g.get('animations', [])}; miss = [c for c in clips if c not in an]
        out['clips'] = (not miss, f'{key} clips {sorted(an)} (needs {clips})')
        mv, lp, txt = True, True, []
        for c in clips:
            if c not in an: mv = lp = False; continue
            a = an[c]; dur = max(float(acc(g, binb, s['input']).max()) for s in a['samplers']); amp = 0.0; gap = 0.0
            for ch in a['channels']:
                s = a['samplers'][ch['sampler']]; o = acc(g, binb, s['output']).astype(float)
                if s.get('interpolation') == 'CUBICSPLINE': o = o.reshape(-1, 3, o.shape[1])[:, 1]
                amp = max(amp, float(abs(o - o[0]).max()))
                e = abs(o[-1] - o[0]).max() if ch['target']['path'] != 'rotation' else min(abs(o[-1] - o[0]).max(), abs(o[-1] + o[0]).max())
                gap = max(gap, float(e))
            mv &= amp > MOVE_EPS and dur >= CLIP_MIN_S and len(a['channels']) > 0; lp &= gap <= LOOP_EPS
            txt.append(f'{c} {len(a["channels"])} channels {dur:.2f} s, key range {amp:.3f}, loop gap {gap:.4f}')
        out['moves'] = (mv, f'{key} clips move: ' + '; '.join(txt)); out['loops'] = (lp, f'{key} clips loop (first key = last key within {LOOP_EPS})')
    return out

fails = n = 0
for key in SPEC:
    f = f'{D}/{key}.glb'
    if not os.path.exists(f): n += 1; fails += 1; print(f'FAIL {key} GLB missing ({f})'); continue
    for gate, (ok, text) in check(key, open(f, 'rb').read()).items():
        n += 1; fails += not ok; print(('PASS ' if ok else 'FAIL ') + text)
print(f'{n - fails} of {n} pass')

if '--mutate' in sys.argv and os.path.exists(f'{D}/crab.glb'):
    src = open(f'{D}/crab.glb', 'rb').read(); g0, bin0 = parse(src)
    def pack(g, binb):
        j = json.dumps(g, separators=(',', ':')).encode(); j += b' ' * (-len(j) % 4); binb = bytes(binb) + b'\0' * (-len(binb) % 4)
        return b'glTF' + struct.pack('<II', 2, 28 + len(j) + len(binb)) + struct.pack('<II', len(j), 0x4E4F534A) + j + struct.pack('<II', len(binb), 0x004E4942) + binb
    def lod0(g): return next(nd for nd in g['nodes'] if nd.get('name') == 'crab_lod0')
    def m_cut(): return src[:-120]
    def m_index():
        g = copy.deepcopy(g0); bb = bytearray(bin0); a = g['accessors'][g['meshes'][lod0(g)['mesh']]['primitives'][0]['indices']]; bv = g['bufferViews'][a['bufferView']]
        off = bv.get('byteOffset', 0) + a.get('byteOffset', 0); bb[off:off + np.dtype(COMP[a['componentType']]).itemsize] = b'\xff' * np.dtype(COMP[a['componentType']]).itemsize
        return pack(g, bb)
    def m_lod():
        g = copy.deepcopy(g0); next(nd for nd in g['nodes'] if nd.get('name') == 'crab_lod2')['name'] = 'crab_far'; return pack(g, bin0)
    def m_tris():
        g = copy.deepcopy(g0); nd = next(nd for nd in g['nodes'] if nd.get('name') == 'crab_lod1'); l0 = lod0(g); l0['mesh'], nd['mesh'] = nd['mesh'], l0['mesh']; l0.pop('skin', None)
        prs = g['meshes'][nd['mesh']]['primitives']; g['meshes'][nd['mesh']]['primitives'] = prs * 2; return pack(g, bin0)   # LOD1 now carries LOD0's mesh twice: over its budget
    def m_mat():
        g = copy.deepcopy(g0); g['materials'][0]['name'] = 'palMystery'; return pack(g, bin0)
    def m_skin():
        g = copy.deepcopy(g0); lod0(g).pop('skin'); return pack(g, bin0)
    def m_clip():
        g = copy.deepcopy(g0); g['animations'] = [a for a in g['animations'] if a['name'] != 'move']; return pack(g, bin0)
    def keys(g, bb, name, fn):
        for a in g['animations']:
            if a['name'] != name: continue
            for s in a['samplers']:
                ac = g['accessors'][s['output']]; bv = g['bufferViews'][ac['bufferView']]; off = bv.get('byteOffset', 0) + ac.get('byteOffset', 0); n = NC[ac['type']]
                o = np.frombuffer(bytes(bb[off:off + ac['count'] * n * 4]), '<f4').reshape(ac['count'], n).copy(); o = fn(o); bb[off:off + o.size * 4] = o.astype('<f4').tobytes()
    def m_frozen():
        g = copy.deepcopy(g0); bb = bytearray(bin0)
        def fr(o): o[:] = o[0]; return o
        keys(g, bb, 'move', fr); return pack(g, bb)
    def m_noloop():
        g = copy.deepcopy(g0); bb = bytearray(bin0)
        def nl(o): o[-1] = o[len(o) // 3]; return o
        keys(g, bb, 'move', nl); return pack(g, bb)
    caught = 0; muts = [('valid', 'file cut by 120 bytes', m_cut), ('valid', 'an index past the vertex count', m_index), ('lods', 'LOD2 renamed away', m_lod), ('tris', 'LOD1 carrying twice the LOD0 mesh', m_tris),
                        ('mats', 'a material not in the table', m_mat), ('skin', 'LOD0 skin removed', m_skin), ('clips', 'move clip removed', m_clip), ('moves', 'move clip frozen on its first key', m_frozen),
                        ('loops', 'move clip ends on another pose', m_noloop)]
    for gate, what, fn in muts:
        try: res = check('crab', fn()).get(gate, (False, 'gate did not run'))
        except Exception as e: res = (True, f'mutation crashed: {e}')
        hit = not res[0]; caught += hit; print(('MUT caught: ' if hit else 'MUT MISSED: ') + f'{gate} gate against {what} -> {res[1][:110]}')
    print(f'{caught} of {len(muts)} mutations caught')
