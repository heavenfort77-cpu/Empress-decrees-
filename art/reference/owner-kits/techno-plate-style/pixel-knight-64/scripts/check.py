"""check.py <dir> : PASS/FAIL per view, failing lines only. Limits are this sprite's own targets (64 px frame)."""
import sys, numpy as np
from PIL import Image
from collections import deque
d = sys.argv[1]; ok_all = True
LIM = dict(h=(58, 63), colours=28, iso=6.0)
rows = {}
for v in ('front', 'left', 'back', 'right'):
    a = np.array(Image.open(f'{d}/knight_{v}_1x.png').convert('RGBA')); fails = []
    if a.shape[:2] != (64, 64): fails.append(f'size {a.shape}')
    al = a[..., 3]
    if ((al > 0) & (al < 255)).any(): fails.append('semi-transparent pixels')
    op = al == 255; ys, xs = np.nonzero(op)
    h = ys.max() - ys.min() + 1
    if not LIM['h'][0] <= h <= LIM['h'][1]: fails.append(f'height {h}')
    rows[v] = ys.max()
    cols = {tuple(p) for p in a[op]}
    if len(cols) > LIM['colours']: fails.append(f'colours {len(cols)}')
    key = (a[..., 0].astype(int) << 16) | (a[..., 1].astype(int) << 8) | a[..., 2]; key[~op] = -1
    iso = 0
    for y, x in zip(ys, xs):
        same = False
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < 64 and 0 <= xx < 64 and key[yy, xx] == key[y, x]: same = True; break
        iso += not same
    pc = 100 * iso / len(ys)
    if pc > LIM['iso']: fails.append(f'isolated {pc:.1f}%')
    seen = np.zeros_like(op); q = deque([(ys[0], xs[0])]); seen[ys[0], xs[0]] = True; n = 0
    while q:
        y, x = q.popleft(); n += 1
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                yy, xx = y + dy, x + dx
                if 0 <= yy < 64 and 0 <= xx < 64 and op[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True; q.append((yy, xx))
    if n != len(ys): fails.append(f'not one piece ({len(ys) - n} px loose)')
    if xs.min() == 0 or xs.max() == 63 or ys.max() == 63: fails.append('touches frame side/bottom')
    print(f'{v:5s} {"PASS" if not fails else "FAIL"}  h={h} colours={len(cols)} isolated={pc:.1f}% top_row={ys.min()} foot_row={ys.max()}', *fails)
    ok_all &= not fails
if len(set(rows.values())) != 1: print('FAIL feet rows differ', rows); ok_all = False
print('ALL PASS' if ok_all else 'SOME FAIL')
