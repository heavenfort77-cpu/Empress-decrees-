"""Model 2 (klad pixel-art workflow): python3 gen_m2.py
Builds m2/knight.klad with klad's own hue-shifted ramps, writes each view as a klad pixel grid (one drawing per frame),
then the caller runs klad check / export. Needs the klad CLI (KLAD env var or the path below)."""
import os, json, subprocess, sys
from pxkit import Cv
import knight

K = os.environ.get('KLAD', '/home/claude/klad_src/target/linux/release/klad')
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'm2')
B = os.path.join(D, 'knight.klad')
VIEWS = ['front', 'left', 'back', 'right']

# ============================== CONFIG (tune by hand) ==============================
BASES = {           # klad builds each ramp round its base colour (cool darks, warm lights)
    'steel': ('#8b9bb4', 5), 'gun': ('#2c3446', 3), 'brass': ('#c98f24', 3),
    'glow': ('#5fd6ea', 3), 'cloth': ('#2f6a45', 3),
}
SINGLES = {'ink': '#10131c', 'shine': '#f4f7fb', 'grip': '#a8322a'}
TONES = {           # which palette colour each tone of each material uses (tone 0 = outline)
    'steel': ['ink', 'steel-1', 'steel-2', 'steel-3', 'steel-4', 'steel-5', 'shine'],
    'gun':   ['ink', 'gun-1', 'gun-2', 'gun-2', 'gun-3'],
    'brass': ['ink', 'brass-1', 'brass-1', 'brass-2', 'brass-3'],
    'glow':  ['ink', 'glow-1', 'glow-2', 'glow-3', 'shine'],
    'cloth': ['ink', 'cloth-1', 'cloth-2', 'cloth-2', 'cloth-3'],
    'grip':  ['ink', 'grip', 'grip', 'grip'],
}
STYLE = dict(light=(-0.50, -0.62, 0.60), shade_range=(-0.30, 1.0), shade_gamma=1.5, part_shadow=1,
             glow='glow', despeckle=True, keep_single=['glow', 'brass', 'grip'],
             outline_order=['gun', 'cloth', 'grip', 'brass', 'steel', 'glow'])
# ===================================================================================


def k(*a, inp=None):
    r = subprocess.run([K, *a], input=inp, capture_output=True, text=True)
    if r.returncode:
        print('klad', a[:3], 'failed:', r.stderr.strip()[:400]); sys.exit(1)
    return r.stdout


def make_bundle():
    os.makedirs(D, exist_ok=True)
    subprocess.run(['rm', '-rf', B])
    k('new', B, '--pixel', '64x64', '--fps', '2', '--frames', '4')
    k('palette', B, '--add', SINGLES['ink'], '--name', 'ink')
    for name, (base, steps) in BASES.items():
        k('palette', B, '--ramp', name, '--base', base, '--steps', str(steps))
    for n in ('shine', 'grip'):
        k('palette', B, '--add', SINGLES[n], '--name', n)
    return {e['name']: e['color'] for e in json.loads(k('palette', B, '--json'))}


def main():
    pal = make_bundle()
    cfg = dict(STYLE, ramps={m: [pal[n] for n in names] for m, names in TONES.items()})
    names = list(pal)
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    legend = {chars[i]: n for i, n in enumerate(names)}
    inv = {n: ch for ch, n in legend.items()}
    ops = []
    plan = {}
    for f, v in enumerate(VIEWS):
        c = Cv(cfg)
        getattr(knight, v)(c)
        c.part_shadow(); c.despeckle(); c.outline()
        rows = []
        for y in range(64):
            row = ''
            for x in range(64):
                mi = c.m[y, x]
                row += '.' if mi < 0 else inv[TONES[c.mats[mi]][c.t[y, x]]]
            rows.append(row)
        plan[v] = rows
        if f:
            ops.append({'op': 'add', 'cel': {'frame': f}, 'in': 'l1'})
        ops.append({'op': 'pixel', 'layer': 'l1', 'frame': f, 'rows': rows, 'legend': legend, 'at': [0, 0]})
    json.dump({'legend': legend, 'palette': pal, 'views': plan}, open(os.path.join(D, 'planned_grids.json'), 'w'), indent=0)
    out = k('apply', B, inp='\n'.join(json.dumps(o) for o in ops) + '\n')
    print('applied', len(ops), 'ops;', len(pal), 'palette colours')


if __name__ == '__main__':
    main()
