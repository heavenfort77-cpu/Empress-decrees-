# Mutation round for checks.py (VFXP, 25 Nov): each mutant breaks one thing on a copy of the assets; the named gate must FAIL.
# Usage: python3 -I mutate.py <assets dir> <floor png> <vfx_map.json>
import sys, json, os, shutil, subprocess, tempfile
import numpy as np
from PIL import Image
A, FLOOR, MAP = sys.argv[1:4]; HERE = os.path.dirname(os.path.abspath(__file__))
M = json.load(open(f'{A}/vfx.json'))

def cell(e, i):
    cw, ch = e['cellPx']; x = e['originPx'][0] + (i % e['cols']) * e['stridePx'][0]; y = e['originPx'][1] + (i // e['cols']) * e['stridePx'][1]
    return slice(y, y + ch), slice(x, x + cw)

def edit_atlas(d, k, fn):
    e = M['effects'][k]; p = f'{d}/{M["atlases"][e["atlas"]]["file"]}'; a = np.array(Image.open(p)); fn(a, e); Image.fromarray(a).save(p)

def m_loop_blank(d, m):
    e = M['effects']['ring']; edit_atlas(d, 'ring', lambda a, e: a.__setitem__((*cell(e, e['loop'][0] + 1), 1), 0))
def m_border(d, m):
    def f(a, e): ys, xs = cell(e, 2); a[ys.start, xs.start + 5:xs.start + 30, 1] = 255
    edit_atlas(d, 'burst', f)
def m_windup(d, m): m['items'][[i['id'] for i in m['items']].index('claw')]['windup'] = 0.3
def m_dark_tell(d, m):
    def f(a, e):
        for i in range(e['loop'][0], e['loop'][1]): ys, xs = cell(e, i); a[ys, xs, 0] = np.minimum(a[ys, xs, 0], 128)
    edit_atlas(d, 'ring', f)
def m_face(d, m):
    def f(a, e):
        ys, xs = cell(e, 5); t = e['texelM']; cy = int(e['pivotPx'][1] - 1.7 / t); cx = e['pivotPx'][0]
        a[ys.start + cy - 2:ys.start + cy + 2, xs.start + cx - 2:xs.start + cx + 2, 1] = 255
    edit_atlas(d, 'aura', f)
def m_not_empty(d, m):
    def f(a, e):
        ysp, xsp = cell(e, 3); ysl, xsl = cell(e, e['frames'] - 1); a[ysl, xsl] = a[ysp, xsp]
    edit_atlas(d, 'smoke', f)
def m_json(d, m): os.remove(f'{d}/fx_thrust.json')
def m_no_tell(d, m): m['items'][[i['id'] for i in m['items']].index('g_volley')].pop('tell')

MUTS = [('timing', m_loop_blank), ('cells', m_border), ('map', m_windup), ('floor_read', m_dark_tell), ('face', m_face), ('timing', m_not_empty), ('json', m_json), ('map', m_no_tell)]
caught = 0
for want, fn in MUTS:
    d = tempfile.mkdtemp(); shutil.copytree(A, d, dirs_exist_ok=True); m = json.load(open(MAP)); fn(d, m); mp = f'{d}/map.json'; json.dump(m, open(mp, 'w'))
    out = subprocess.run([sys.executable, '-I', f'{HERE}/checks.py', d, FLOOR, mp], capture_output=True, text=True).stdout
    ok = f'GATE {want} FAIL' in out; caught += ok
    print(f'MUT {fn.__name__} -> {want} {"CAUGHT" if ok else "MISSED"}'); shutil.rmtree(d)
print(f'MUTATIONS {caught} of {len(MUTS)} caught')
