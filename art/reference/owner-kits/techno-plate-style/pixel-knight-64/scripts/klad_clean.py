"""klad_clean.py: let `klad check` drive the clean-up of m2/knight.klad, then export with klad.
Fixes only what klad lists as standing out: lone pixels in a flat field, one-pixel bands, doubled outline corners."""
import json, os, subprocess, sys
K = os.environ.get('KLAD', '/home/claude/klad_src/target/linux/release/klad')
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'm2'); B = os.path.join(D, 'knight.klad')
VIEWS = ['front', 'left', 'back', 'right']


def k(*a, inp=None, ok=True):
    r = subprocess.run([K, *a], input=inp, capture_output=True, text=True)
    if r.returncode and ok:
        print('klad', a[:4], 'failed:', r.stderr.strip()[:300]); sys.exit(1)
    return r.stdout


def grid(f):
    j = json.loads(k('pixels', B, 'l1', '--frame', str(f), '--json'))
    leg = j['legend']
    name = {}
    for e in (leg if isinstance(leg, list) else [dict(char=c, **(v if isinstance(v, dict) else {'name': v})) for c, v in leg.items()]):
        name[e.get('char') or e.get('character')] = e.get('name')
    return [[name.get(ch) for ch in row] for row in j['rows']]


pal = [e['name'] for e in json.loads(k('palette', B, '--json'))]
done = {'stray': 0, 'banding': 0, 'corner': 0}
for rnd in range(4):
    F = [x for x in json.loads(k('check', B, '--all', '--json'))['findings'] if not x.get('minor')]
    ops = []
    grids = {f: grid(f) for f in range(4)}
    for x in F:
        f = x['frame']; g = grids[f]; (x0, y0), (x1, y1) = x['at'], x['to']
        cells = [[xx, yy] for yy in range(min(y0, y1), max(y0, y1) + 1) for xx in range(min(x0, x1), max(x0, x1) + 1)]
        if x['kind'] == 'stray':
            cnt = {}
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x0 + dx, y0 + dy
                if 0 <= xx < 64 and 0 <= yy < 64 and g[yy][xx]:
                    cnt[g[yy][xx]] = cnt.get(g[yy][xx], 0) + 1
            if cnt:
                ops.append({'op': 'pixel', 'layer': 'l1', 'frame': f, 'color': max(cnt, key=cnt.get), 'cells': cells}); done['stray'] += 1
        elif x['kind'] == 'banding' and ' between ' in x['note']:
            a, b = x['note'].split(' between ')[1].split(' and ')
            to = b if a == 'ink' else a if b == 'ink' else min(a, b, key=pal.index)
            ops.append({'op': 'pixel', 'layer': 'l1', 'frame': f, 'color': to, 'cells': cells}); done['banding'] += 1
        elif x['kind'] == 'corner' and x['color'] == 'ink':
            nb = [g[y0 + dy][x0 + dx] if 0 <= x0 + dx < 64 and 0 <= y0 + dy < 64 else None for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            if None in nb and all(n in (None, 'ink') for n in nb):
                ops.append({'op': 'pixel', 'layer': 'l1', 'frame': f, 'erase': True, 'cells': cells}); done['corner'] += 1
    if not ops:
        break
    k('apply', B, inp='\n'.join(json.dumps(o) for o in ops) + '\n')
left = [x for x in json.loads(k('check', B, '--all', '--json'))['findings'] if not x.get('minor')]
kinds = {}
for x in left:
    kinds[x['kind']] = kinds.get(x['kind'], 0) + 1
print('klad check fixes applied:', done, '| still listed (left on purpose or not auto-fixable):', kinds)
out = os.path.join(D, 'out'); os.makedirs(out, exist_ok=True)
for f, v in enumerate(VIEWS):
    k('export', B, '--frame', str(f), '--scale', '1', '-o', f'{out}/knight_{v}_1x.png')
k('export', B, '--sheet', 'all', '--scale', '1', '-o', f'{out}/knight_4view_1x.png')
k('export', B, '--sheet', 'all', '--scale', '8', '-o', f'{out}/knight_4view_8x.png')
k('export', B, '--aseprite', '-o', f'{out}/knight.aseprite')
print(sorted(os.listdir(out)))
