#!/usr/bin/env python3
"""Front and back of the knight, hand-placed pixel by pixel in the reference sprite's technique, built in klad.
Read off the reference grid: plates run light to dark from the viewer's left, a dark line between plates, a dark waist band,
notched skirt hem, brass bands with one bright pixel, far-side parts one tone darker, no outline round cloth, brass or the darkest steel.
Only the viewer's left half is typed; the right half is mirrored, relit from the left and darkened one step.
Run: python3 draw_views.py"""
import os, shutil, subprocess, sys
# ---------------- CONFIG ----------------
K = os.environ.get('KLAD', '/home/claude/klad/src/target/linux/release/klad')
F, TOP, LEFT = 64, 2, 17                 # frame, first row, first column of the typed half (15 wide)
CODE = {'#': 'ink', '1': 'steel-1', '2': 'steel-2', '3': 'steel-3', '4': 'steel-4', '5': 'steel-5', 'a': 'brass-1', 'b': 'brass-2', 'c': 'brass-3',
        'g': 'cloth-1', 'G': 'cloth-2', '*': 'glow-1', 'r': 'leather-1'}
HEX = {'ink': '#1b1d2e', 'steel-1': '#3a4560', 'steel-2': '#5f6d8c', 'steel-3': '#8f9db8', 'steel-4': '#c5cfdd', 'steel-5': '#f4f7fb', 'brass-1': '#8c5a1e',
       'brass-2': '#d99a2b', 'brass-3': '#ffd765', 'cloth-1': '#25503a', 'cloth-2': '#3f8454', 'glow-1': '#a8f4ee', 'leather-1': '#b8403a'}
FAR = {'5': '4', '4': '3', '3': '2', '2': '1', '1': '1', 'c': 'b'}     # the side away from the light
NO_OUTLINE = set('abcgG1*')              # outline is left off where it would only touch these
BLADE = dict(x=31, y_base=30, y_tip=3, lean=3)         # rows climbed per pixel of lean; front leans to the viewer's right, back shows the tip only
# ----------------------------------------
FRONT = """
....22.........
....212........
.....212.......
......2122.....
.......2122.455
........212#445
.........2#4445
.........#44444
.........#b3444
.........#3####
........##**#33
....bcb.#233#34
....212..#22#44
....212..#2#444
....212...##333
....212...#5#5#
...4555...#1221
.455544433#####
4555444333#4554
4554444333#4544
44******33#4b**
4444433332#4b**
3444333322#34bb
3333332222#3434
bbcbbbbbba#3434
.344332#3434343
.344332#3434343
.233322#2323232
.344433#2323232
..234443##2abbc
...#234443b#454
....##2344b#343
........#bcb#23
.......#454444a
......#34343433
.......3#3#3#3#
.......344432gG
.......344432gG
.......344432gG
.......344432gG
.......234432gG
.......bcbbbagG
......45554432g
......3441*432.
......2333332..
.......122221..
.......344332..
.......344332..
.......344332..
.......343332..
.......233322..
.......233222..
.......bcbbba..
......23544432.
.....45443322..
....3433334332.
....2333343322.
....22#22#221..
""".split()
BACK = list(FRONT)
for i, r in {6: ".........2#4444", 7: ".........#4444#", 8: ".........#34443", 9: ".....bcb.#3344#", 10: ".....212.#33333", 11: ".....212.#2333#",
             12: ".....212.#22332", 13: ".....212..#2222", 14: ".....212..#1221", 15: ".....212..#bbbb", 16: "..455212..#1221",
             17: ".4555444#######", 18: "45554443#234443", 19: "45544443#233bbb", 20: "44444433#23b***", 21: "44444333#23b***", 22: "34443332#223bbb",
             23: "33333222#222222", 24: "bbcbbbba#222222", 25: ".344332#1111111", 26: ".344332#3444332", 27: ".344332#3444332", 28: ".233322#2333222",
             29: "..2332..#222222", 30: "...22...#bcbbbb", 31: ".......#4544443", 32: ".......#4444333", 33: ".......#4444333", 34: "......#34343433",
             43: "......34433432."}.items(): BACK[i] = r
def full(rows):
    g = [['.'] * F for _ in range(F)]
    for i, r in enumerate(rows):
        assert len(r) == 15, (i, r)
        m = list(r[::-1]); j = 0
        while j < 15:                                          # relight the mirrored half: runs of steel, light first, one step darker
            if m[j] in '12345':
                k = j
                while k < 15 and m[k] in '12345': k += 1
                run = m[j:k] if j == 0 else sorted(m[j:k], reverse=True)
                m[j:k] = [FAR[c] for c in run]; j = k
            else: m[j] = FAR.get(m[j], m[j]); j += 1
        for x, c in enumerate(list(r) + m): g[TOP + i][LEFT + x] = c
    return g
def blade(g, front):
    for y in range(BLADE['y_tip'], BLADE['y_base'] + 1):
        d = round((BLADE['y_base'] - y) / BLADE['lean'])
        if front:
            x = BLADE['x'] + d
            for dx, c in ((-1, '#'), (0, '5'), (1, '3')):
                if c != '#' or g[y][x + dx] != '.': g[y][x + dx] = c
        else:
            x = BLADE['x'] - d
            for dx, c in ((0, '5'), (1, '3')):
                if g[y][x + dx] == '.' and y < TOP + 16: g[y][x + dx] = c
def run(*a): return subprocess.run([K, *a], capture_output=True, text=True)
os.makedirs('out', exist_ok=True); os.makedirs('tmp', exist_ok=True)
for name, rows in (('front', FRONT), ('back', BACK)):
    g = full(rows)
    if name == 'front': blade(g, True)                        # from behind the body hides the blade
    used = sorted({c for r in g for c in r if c != '.'}); abc = 'abcdefghijklmnopqrstuvwxyz'; code = {c: abc[i] for i, c in enumerate(used)}
    open(f'tmp/{name}.grid', 'w').write('\n'.join(f'{code[c]} = {CODE[c]}' for c in used) + '\n\n' + '\n'.join(''.join(code.get(c, '.') for c in r) for r in g) + '\n')
    b = f'out/knight_{name}.klad'; shutil.rmtree(b, ignore_errors=True); run('new', b, '--pixel', f'{F}x{F}')
    for n, h in HEX.items(): run('palette', b, '--add', h, '--name', n)
    a = run('pixel', b, 'l1', '--grid', f'tmp/{name}.grid'); o = run('pixel', b, 'l1', '--color', 'ink', '--outline')
    if a.returncode or o.returncode: print('klad error', name, (a.stderr or o.stderr)[:300]); sys.exit(1)
    opens = []                                                 # open the outline where it only touches cloth, brass, glow or the darkest steel
    for y in range(F):
        for x in range(F):
            if g[y][x] != '.': continue
            nb = [g[y + dy][x + dx] for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)) if 0 <= y + dy < F and 0 <= x + dx < F and g[y + dy][x + dx] != '.']
            if nb and all(c in NO_OUTLINE for c in nb): opens.append((x, y))
    if opens: run('pixel', b, 'l1', '--erase', '--cells', ' '.join(f'{x},{y}' for x, y in opens))
    run('export', b, '--scale', '1', '-o', f'out/knight_{name}_1x.png'); run('export', b, '--scale', '6', '-o', f'out/knight_{name}_6x.png')
    print(name, 'outline cells opened:', len(opens), '| klad check:', run('check', b).stdout.split('\n')[0])
