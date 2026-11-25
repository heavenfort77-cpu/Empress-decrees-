#!/usr/bin/env python3
"""Animate sprite 2b itself, frame by frame, the way klad's pixel skill describes: start from the drawing,
move whole clusters by whole pixels to make the next frame, write each frame into a klad animation,
then let klad redraw the outline and check it. No 3D is used here; 2b's own pixels are the source.
Run: python3 klad_frames.py"""
import json, os, shutil, subprocess, sys

# ---------------- CONFIG: tune by hand ----------------
K = os.environ.get('KLAD', '/home/claude/klad/src/target/linux/release/klad')
F = 96; FPS = 6
RAMPS = [('steel', '#8f99a6', 5), ('gun', '#3e4550', 3), ('brass', '#b8923e', 4), ('cloth', '#2f4a33', 3), ('leather', '#8a2f24', 2), ('glow', '#5fe6f0', 2)]
LEG_L = (35, 43); LEG_R = (52, 60)      # columns of the viewer's left and right leg
BLADE = (44, 51)                        # columns of the sword blade between the legs
LEGS_TOP = 52                           # first row below the sword guard
KNEE = (66, 68)                         # rows removed to lift a foot (the leg shortens at the knee)
WAIST_ROW = 47                          # row removed when the body sinks 1 px
TIP_FROM = 81                           # in walk and battle the sword is off the ground: the blade ends in a taper from this row
# -------------------------------------------------------
lines = open('base_2b.grid').read().split('\n'); k = lines.index('')
legend = lines[:k]; code = {l.split(' = ')[1]: l.split(' = ')[0] for l in legend}
base = [list(r) for r in lines[k + 1:] if r]
copy = lambda g: [r[:] for r in g]

def sink(g, n=1):
    """The body above the waist sinks n px: remove waist rows and shift everything above down."""
    for _ in range(n):
        for y in range(WAIST_ROW, 0, -1): g[y] = g[y - 1][:]
        g[0] = ['.'] * F
    return g
def lift(g, cols, n=3, dx=0):
    """Lift one foot n px: the leg shortens at the knee and the shin and foot move up (and dx sideways)."""
    x0, x1 = cols
    col = [[g[y][x] for y in range(F)] for x in range(x0, x1 + 1)]
    for c in col:
        lower = c[KNEE[0] + n:]                               # shin and foot
        c[KNEE[0]:] = lower + ['.'] * n
    for i, x in enumerate(range(x0, x1 + 1)):
        for y in range(F): g[y][x] = col[i][y]
    if dx:
        for y in range(KNEE[0], F):
            seg = g[y][x0:x1 + 1]; g[y][x0:x1 + 1] = ['.'] * len(seg)
            for i, ch in enumerate(seg):
                if ch != '.' and 0 <= x0 + i + dx < F: g[y][x0 + i + dx] = ch
    return g
def lean(g, dx):
    """The body above the legs shifts dx px sideways."""
    for y in range(LEGS_TOP):
        row = g[y]; g[y] = (['.'] * dx + row[:F - dx]) if dx > 0 else (row[-dx:] + ['.'] * (-dx))
    return g
def raise_sword(g):
    """Sword off the ground: the blade ends in a short taper instead of reaching the floor."""
    x0, x1 = BLADE
    for y in range(TIP_FROM, F):
        keep = max(0, (x1 - x0 + 1) - 2 * (y - TIP_FROM + 1))
        for x in range(x0, x1 + 1):
            if not (x0 + (x1 - x0 + 1 - keep) // 2 <= x < x0 + (x1 - x0 + 1 - keep) // 2 + keep): g[y][x] = '.'
    return g
def spread(g, n=2):
    """Legs apart by n px each."""
    for (x0, x1), d in ((LEG_L, -n), (LEG_R, n)):
        for y in range(LEGS_TOP, F):
            seg = g[y][x0:x1 + 1]; g[y][x0:x1 + 1] = ['.'] * len(seg)
            for i, ch in enumerate(seg):
                if ch != '.': g[y][x0 + i + d] = ch
    return g
def brighten(g):
    """Lights flare: every dim light pixel becomes a bright one."""
    a, b = code.get('glow-1'), code.get('glow-2')
    return [[b if ch == a else ch for ch in r] for r in g] if a and b else g

def walk(d):                                                   # d = -1 walks toward the viewer's left, +1 toward the right
    first, second = (LEG_L, LEG_R) if d < 0 else (LEG_R, LEG_L)
    return [sink(raise_sword(copy(base))), lean(lift(raise_sword(copy(base)), first, 3, d), d),
            sink(raise_sword(copy(base))), lean(lift(raise_sword(copy(base)), second, 3, d), d)]
ANIMS = {
    'idle': [copy(base), sink(copy(base)), brighten(sink(copy(base))), sink(copy(base))],
    'walk_left': walk(-1), 'walk_right': walk(1),
    'battle': [brighten(sink(spread(raise_sword(copy(base))), 2))],
}
def run(*a): return subprocess.run([K, *a], capture_output=True, text=True)
os.makedirs('out', exist_ok=True); os.makedirs('tmp', exist_ok=True); report = []
for anim, frames in ANIMS.items():
    b = f'out/{anim}.klad'; shutil.rmtree(b, ignore_errors=True)
    run('new', b, '--pixel', f'{F}x{F}', '--frames', str(len(frames)), '--fps', str(FPS)); run('palette', b, '--add', '#14161c', '--name', 'ink')
    for n, col, st in RAMPS: run('palette', b, '--ramp', n, '--base', col, '--steps', str(st))
    for i, g in enumerate(frames):
        open(f'tmp/{anim}_{i}.grid', 'w').write('\n'.join(legend) + '\n\n' + '\n'.join(''.join(r) for r in g) + '\n')
        if i: run('add', b, 'cel', '--in', 'l1', f'frame={i}')
        a = run('pixel', b, 'l1', '--frame', str(i), '--grid', f'tmp/{anim}_{i}.grid'); o = run('pixel', b, 'l1', '--frame', str(i), '--color', 'ink', '--outline')
        if a.returncode or o.returncode: print('klad error', anim, i, (a.stderr or o.stderr)[:300]); sys.exit(1)
        for _ in range(6):                                     # doubled corners in the outline
            c = [x['at'] for x in json.loads(run('check', b, '--frame', str(i), '--json').stdout)['findings'] if x['kind'] == 'corner' and x['color'] == 'ink']
            if not c: break
            run('pixel', b, 'l1', '--frame', str(i), '--erase', '--cells', ' '.join(f'{x},{y}' for x, y in c))
        kinds = {}
        for x in json.loads(run('check', b, '--frame', str(i), '--json').stdout)['findings']: kinds[x['kind']] = kinds.get(x['kind'], 0) + 1
        report.append((anim, i, kinds)); run('export', b, '--frame', str(i), '--scale', '1', '-o', f'out/{anim}_{i}.png')
    if len(frames) > 1: run('export', b, '--gif', 'all', '--scale', '3', '-o', f'out/{anim}_3x.gif')
for anim, i, kinds in report: print(f'{anim}_{i} klad check:', kinds)
