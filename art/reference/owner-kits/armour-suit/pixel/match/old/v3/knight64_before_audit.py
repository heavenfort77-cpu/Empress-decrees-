#!/usr/bin/env python3
"""Knight at 64x64 from the four 3D renders: front and back stills, idle and walk, every frame redrawn pixel by pixel and built in klad.
Research used (klad `skill pixel` animation rules + Saint11 walk/idle rules):
 few strong poses (idle <= 6, walk 6); walk = contact, down, passing per step, body lowest on 'down' and highest on 'passing';
 keep volume (parts change by whole rows, never thin out); less than a pixel = move the shading (highlight shift, glow dim);
 no jitter (each frame is the still's text with only the named rows changed); cloth and blade tip trail the body by one frame;
 judge as a GIF at speed. Nothing here is a moved layer or a rig: each frame is its own grid of pixels handed to klad.
Run: python3 knight64.py"""
import os, shutil, subprocess, sys
import numpy as np
from PIL import Image
# ---------------- CONFIG ----------------
K = os.environ.get('KLAD', '/home/claude/klad/src/target/linux/release/klad')
F, TOP, LEFT = 64, 3, 17
GROUND = TOP + 57                        # row of the soles
FPS = {'idle': 6, 'walk': 8}
JUMP = {'idle': 45, 'walk': 90}           # most pixels allowed to change between two frames, % of the sprite (a walk shifts the whole body)
WALK = dict(bob=[0, 1, -1, 0, 1, -1], sway=[0, -1, -1, 0, 1, 1], L=['fwd', 'plant', 'plant', 'back', 'back', 'lift'], R=['back', 'back', 'lift', 'fwd', 'plant', 'plant'], tip_lift=3)
IDLE = dict(breath=[0, 1, 2, 2, 1, 0], cloth=[0, 0, 0, 1, 0, 0], eyes=[1, 1, 1, 1, 1, 0])      # 0 rest, 1 highlight shift, 2 chest one row taller
CODE = {'#': 'ink', '1': 'steel-1', '2': 'steel-2', '3': 'steel-3', '4': 'steel-4', '5': 'steel-5', 'a': 'brass-1', 'b': 'brass-2', 'c': 'brass-3',
        'g': 'cloth-1', 'G': 'cloth-2', '*': 'glow-1', 'r': 'leather-1'}
HEX = {'ink': '#1b1d2e', 'steel-1': '#3a4560', 'steel-2': '#5f6d8c', 'steel-3': '#8f9db8', 'steel-4': '#c5cfdd', 'steel-5': '#f4f7fb', 'brass-1': '#8c5a1e',
       'brass-2': '#d99a2b', 'brass-3': '#ffd765', 'cloth-1': '#25503a', 'cloth-2': '#3f8454', 'glow-1': '#a8f4ee', 'leather-1': '#b8403a'}
FAR = {'5': '4', '4': '3', '3': '2', '2': '1', '1': '1', 'c': 'b'}
NO_OUTLINE = set('abcgG1*r')
# ----------------------------------------
FRONT_L = """
..............5
......2.......4
......12......4
......212....45
.......2122.455
........212#445
.........2#4445
.........#44444
.........#b3444
.........#3####
.....54.##**#33
......54#233#34
.....543.#22#44
.......54#2#444
..........##333
..........#5#5#
...4555...#1221
.455544433#####
4555444333#4554
4554444333#4544
44******33#4b**
4444433332#4b**
3444333322#34bc
3333332222#343r
bbcbbbbbba#3#44
.34433b44432#43
.34433b34432#32
.23332b23322#32
.233322#3232#44
..2332.#2222#43
........#bcb#32
.......#4544#32
.......#4bbcbbb
.......#4444333
......#34343433
.......3#3#3#3#
""".split()
def over(rows, d):
    r = list(rows)
    for i, v in d.items(): r[i] = v
    return r
FRONT_R = over(FRONT_L, {25: ".344332#3434#43", 26: ".344332#3434#32", 27: ".233322#2323#32", 28: ".34433b44432#44", 29: ".34433b34432#43", 30: ".23332b23322#32", 31: "..2332.#4544#32"})
BACK_L = over(FRONT_L, {6: ".........2#4444", 7: ".........#4444#", 8: ".........#34443", 9: ".....bcb.#3344#", 10: ".....212.#33333", 11: ".....212.#2333#", 12: ".....212.#22332",
    13: ".....212..#2222", 14: ".....212..#1221", 15: ".....212..#bbbb", 16: "..455212..#1221", 17: ".4555444#######", 18: "45554443#*2b22b", 19: "45544443#*1b11b",
    20: "44444433#*1b11b", 21: "44444333#*1a11a", 22: "34443332#222222", 23: "33333222#23333*", 24: "bbcbbbba#23332*", 25: ".344332#233322*", 26: ".344332#233322*",
    27: "b344332#222222*", 28: "b233322#bcbbbbb", 29: "..2332.#4544443", 30: "...22..#4444333", 31: ".......#4444333", 32: ".......#4444333"})
VIEW = {'front': dict(dim=[10], L=FRONT_L, R=FRONT_R, dup=19, alt={16: "..45555...#1221"}, knee="......3441*432.", cloth=['gGGg'] * 6 + ['.gg.']),
        'back': dict(dim=[18, 21], L=BACK_L, R=BACK_L, dup=23, alt={17: "45555444#######"}, knee="......34433432.", cloth=['gGGg', 'gG*g', 'g**g', 'gG*g', 'gG*g', 'gGGg', '.gg.'])}
P = '.......'
THIGH = [P + '344432..'] * 4 + [P + '234432..']; BAND = [P + 'bcbbba..']; NARROW = [P + '122221..']
GREAVE = [P + '344332..'] * 3 + [P + '343332..', P + '233322..', P + '233222..']
BOOT = ["......23544432.", ".....45443322..", "....3433334332.", "....2333343322.", "....22#22#221.."]
BLANK = '.' * 15
def leg(state, n, knee):
    kn = ["......45554432.", knee, "......2333332.."]
    if state == 'plant': r = THIGH + BAND + kn + NARROW + GREAVE + BAND + BOOT
    elif state == 'fwd': r = THIGH + BAND + kn + NARROW + GREAVE[:2] + GREAVE[3:] + BAND + BOOT[:3] + [BOOT[2]] + BOOT[3:]       # foot nearer: bigger boot, shorter shin
    elif state == 'back': r = [''.join(FAR.get(c, c) for c in x) for x in THIGH + BAND + kn + NARROW + GREAVE + BAND + BOOT[:3] + BOOT[4:]] + [BLANK]   # foot behind: smaller, darker, off the ground
    else: r = THIGH[1:] + BAND + kn + NARROW + GREAVE[:1] + GREAVE[3:] + BAND + [BOOT[0], BOOT[1], BOOT[4]]                       # knee up: thigh and shin seen short, foot hanging
    while len(r) > n: r.pop(1 if r[-1] != BLANK or state == 'plant' else -1)
    while len(r) < n: r.insert(1, r[1]) if state in ('plant', 'fwd') else r.append(BLANK)
    return r
def place(g, L, R, y0, xo):
    for i, (l, r) in enumerate(zip(L, R)):
        assert len(l) == 15 and len(r) == 15, (i, l, r)
        m = list(r[::-1]); j = 0
        while j < 15:
            if m[j] in '12345':
                k = j
                while k < 15 and m[k] in '12345': k += 1
                run_ = m[j:k] if j == 0 else sorted(m[j:k], reverse=True)
                m[j:k] = [FAR[c] for c in run_]; j = k
            else: m[j] = FAR.get(m[j], m[j]); j += 1
        for x, c in enumerate(list(l) + m):
            if c != '.': g[y0 + i][LEFT + x + xo] = c
def frame(view, bob=0, sway=0, legL='plant', legR='plant', breath=0, cloth=0, eyes=1, tip_lift=0):
    v = VIEW[view]; L, R = list(v['L']), list(v['R'])
    if breath >= 1: L, R = over(L, v['alt']), over(R, v['alt'])                 # shoulders swell: the highlight grows one pixel
    if not eyes:                                                                # glow dips for one frame: eyes in front, reactor ends behind
        for i in v['dim']: L[i] = L[i].replace('*', '4', 1); R[i] = R[i].replace('*', '4', 1)
    if breath == 2: L.insert(v['dup'], L[v['dup']]); R.insert(v['dup'], R[v['dup']])   # chest one row taller, head and shoulders ride up
    g = [['.'] * F for _ in range(F)]; ly = TOP + 36 + bob; n = 22 - bob
    place(g, leg(legL, n, v['knee']), leg(legR, n, v['knee']), ly, 0)
    place(g, L, R, ly - len(L), sway)
    for i, row in enumerate(v['cloth']):                                         # cloth hangs from the belt; its lower rows trail
        for dx, c in enumerate(row):
            if c != '.': g[ly + i][30 + dx + sway + (cloth if i >= 4 else 0)] = c
    tip = GROUND - tip_lift + (bob if tip_lift else 0); y0 = ly - 3 if view == 'front' else ly + 7
    for y in range(y0, tip + 1):                                                 # blade, point down; the lower third trails
        x = 31 + sway + (cloth if y > (y0 + 2 * tip) // 3 else 0)
        if y == tip: g[y][x] = '4'
        else: g[y][x] = '5'; g[y][x + 1] = '3'
    return g
ANIMS = {'idle': [dict(breath=IDLE['breath'][i], cloth=IDLE['cloth'][i], eyes=IDLE['eyes'][i]) for i in range(6)],
         'walk': [dict(bob=WALK['bob'][i], sway=WALK['sway'][i], legL=WALK['L'][i], legR=WALK['R'][i], cloth=WALK['sway'][i - 1] - WALK['sway'][i], tip_lift=WALK['tip_lift']) for i in range(6)]}
def run(*a): return subprocess.run([K, *a], capture_output=True, text=True)
os.makedirs('out64', exist_ok=True); os.makedirs('tmp', exist_ok=True); fails = []; sheet = []
for view in ('front', 'back'):
    for anim, frames in ANIMS.items():
        b = f'out64/knight_{view}_{anim}.klad'; shutil.rmtree(b, ignore_errors=True)
        run('new', b, '--pixel', f'{F}x{F}', '--frames', str(len(frames)), '--fps', str(FPS[anim]))
        for nme, h in HEX.items(): run('palette', b, '--add', h, '--name', nme)
        notes = 0; imgs = []
        for i, kw in enumerate(frames):
            g = frame(view, **kw); used = sorted({c for r in g for c in r if c != '.'}); abc = 'abcdefghijklmnopqrstuvwxyz'; code = {c: abc[j] for j, c in enumerate(used)}
            open('tmp/f.grid', 'w').write('\n'.join(f'{code[c]} = {CODE[c]}' for c in used) + '\n\n' + '\n'.join(''.join(code.get(c, '.') for c in r) for r in g) + '\n')
            if i: run('add', b, 'cel', '--in', 'l1', f'frame={i}')
            a = run('pixel', b, 'l1', '--frame', str(i), '--grid', 'tmp/f.grid'); o = run('pixel', b, 'l1', '--frame', str(i), '--color', 'ink', '--outline')
            if a.returncode or o.returncode: print('klad error', view, anim, i, (a.stderr or o.stderr)[:300]); sys.exit(1)
            opens = [(x, y) for y in range(F) for x in range(F) if g[y][x] == '.' and (nb := [g[y + dy][x + dx] for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)) if 0 <= y + dy < F and 0 <= x + dx < F and g[y + dy][x + dx] != '.']) and all(c in NO_OUTLINE for c in nb)]
            if opens: run('pixel', b, 'l1', '--frame', str(i), '--erase', '--cells', ' '.join(f'{x},{y}' for x, y in opens))
            p = f'out64/frames/{view}_{anim}_{i}.png'; os.makedirs('out64/frames', exist_ok=True); run('export', b, '--frame', str(i), '--scale', '1', '-o', p)
            c = run('check', b, '--frame', str(i)).stdout.split('\n')[0]; notes += int(''.join(ch for ch in c.split(':')[-1] if ch.isdigit()) or 0)
            imgs.append(np.array(Image.open(p).convert('RGBA')))
        run('export', b, '--gif', 'all', '--scale', '6', '-o', f'out64/knight_{view}_{anim}_6x.gif'); run('export', b, '--gif', 'all', '--scale', '1', '-o', f'out64/knight_{view}_{anim}_1x.gif')
        run('export', b, '--sheet', 'all', '--scale', '1', '-o', f'out64/knight_{view}_{anim}_sheet.png')
        # gates: palette, edges, soles on the ground row, volume held, every frame differs from the last, loop closes by a small step
        area = [int((m[..., 3] > 0).sum()) for m in imgs]; diff = [int((imgs[i] != imgs[i - 1]).any(-1).sum()) for i in range(len(imgs))]
        for i, m in enumerate(imgs):
            s = m[..., 3] > 0; cols = {tuple(px) for px in m[s][:, :3]}; low = np.nonzero(s.any(1))[0].max()
            semi = int(((m[..., 3] > 0) & (m[..., 3] < 255)).sum())
            bad = [t for t, ok in ((f'colours {len(cols)} > 13', len(cols) <= 13), (f'semi-transparent {semi}', semi == 0), ('touches frame edge', not (s[0].any() or s[-1].any() or s[:, 0].any() or s[:, -1].any())),
                                   (f'lowest row {low} not {GROUND + 1}', low == GROUND + 1), (f'area {area[i]} vs {area[0]} beyond 8%', abs(area[i] - area[0]) <= 0.08 * area[0]),
                                   (f'no change from previous frame', diff[i] > 0), (f'jump {diff[i]} px > {JUMP[anim]}% of sprite', diff[i] <= JUMP[anim] / 100 * area[0])) if not ok]
            if bad: fails.append(f'{view} {anim} frame {i}: ' + '; '.join(bad))
        print(f'{view} {anim}: {len(imgs)} frames, changed px per step {diff}, area {min(area)}-{max(area)}, klad check notes {notes}')
        sheet.append(imgs)
    shutil.copy(f'out64/frames/{view}_idle_0.png', f'out64/knight_{view}_1x.png'); Image.open(f'out64/knight_{view}_1x.png').resize((384, 384), Image.NEAREST).save(f'out64/knight_{view}_6x.png')
S = 4; W = Image.new('RGB', (6 * 40 * S, 4 * 64 * S), (0x7c, 0x84, 0x90))
for r, imgs in enumerate(sheet):
    for c, m in enumerate(imgs): im = Image.fromarray(m).crop((12, 0, 52, 64)).resize((40 * S, 64 * S), Image.NEAREST); W.paste(im, (c * 40 * S, r * 64 * S), im)
W.save('out64/contact_sheet_4x.png'); print('GATES:', 'PASS' if not fails else 'FAIL'); [print(' ', f) for f in fails]
