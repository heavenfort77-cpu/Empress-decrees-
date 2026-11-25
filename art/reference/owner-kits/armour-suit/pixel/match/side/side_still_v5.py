#!/usr/bin/env python3
"""Side view of the knight at 64x64, facing right. Proportions come from the 3D render sent through `klad pixelize` (side/prep_render.py);
every pixel is then placed by hand following klad's pixel guide and the reference sprite's technique, and klad outlines, checks and exports it.
Run: python3 side/side_still.py   (from the match folder)"""
import json, os, shutil, subprocess, sys, collections
from PIL import Image
# ---------------- CONFIG ----------------
K = os.environ.get('KLAD', '/home/claude/klad/src/target/linux/release/klad')
F, X0, Y0 = 64, 16, 2
CODE = {'#': 'ink', '1': 'steel-1', '2': 'steel-2', '3': 'steel-3', '4': 'steel-4', '5': 'steel-5', 'a': 'brass-1', 'b': 'brass-2', 'c': 'brass-3',
        'g': 'cloth-1', 'G': 'cloth-2', '*': 'glow-1', 'r': 'leather-1'}
HEX = {'ink': '#1b1d2e', 'steel-1': '#3a4560', 'steel-2': '#5f6d8c', 'steel-3': '#8f9db8', 'steel-4': '#c5cfdd', 'steel-5': '#f4f7fb', 'brass-1': '#8c5a1e',
       'brass-2': '#d99a2b', 'brass-3': '#ffd765', 'cloth-1': '#25503a', 'cloth-2': '#3f8454', 'glow-1': '#a8f4ee', 'leather-1': '#b8403a'}
NO_OUTLINE = set('abcgG*r')
LOW = 99                                 # below this row the darkest steel (soles, far leg shadow) also goes without outline
# ----------------------------------------
# Pose and big shapes follow the reference: striding, far leg dark behind, blade carried upright in front, long swept horns, one clear glow strip.
D = '.'; B = '43'
SIDE = [
 "..11...................4........", "...121.................43.......", ".....121...............43.......", "..11...121.............43.......",
 "...121...121...........43.......", ".....121...121.........43.......", ".......121#45544333#...43.......", "........1#4454443333##.43.......",
 ".........#34444b33***4.43.......", "bc.......#333333322344.43.......", "12.bc....#233333222334.43.......", "12.12.....#233332#####.43.......",
 "12.12.....#22332#5#5#3.43.......", "12.12......#2222###....43.......", "12.12........#221#.....43.......", "12.12...4555544443#....43.......",
 "12.12.455554444443332#.43.......", "12.124555444444333322#.43.......", "12.124444444******332#.43.......", "####.3333333333322222#.43.......",
 ".bb.." + "bbc" + "b" * 11 + "aa" + ".." + B + D * 7,
 "b**b..#" + "233333332222" + "#..." + B + D * 7,
 "b**b..#" + "223333322221" + "#." + "abcbba" + D * 5,
 ".bb...#" + "12222222221" + "1222" + "4543" + D * 6,
 "......#" + "11111111111" + "1122" + "3432" + D * 6,
 ".......#1222#" + "3443" + "#...." + "#rr#" + D * 6,
 ".......#1122#" + "3443" + "4444" + "b" + "4544" + D * 6,
 ".......#1122#" + "33b*" + "3332" + "b" + "3433" + D * 6,
 ".......#1111#" + "22bb" + "2222" + "a" + "2322" + D * 6,
 ".......#" + "bbcbbba" + "########" + "bc" + D * 7,
 "......#" + "454444433332" + "#" + D * 12,
 ".....#" + "4544444333322" + "#" + D * 12,
 ".....#" + "4444343333222" + "#" + D * 12,
 "....#" + "34343433232322" + "#" + D * 12,
 "....##" + "3#3#3#3#2#2#2" + "##" + D * 11,
 "......gGG.#3444332#G............",
 "......gGG22#3444332#g...........",
 "......gGG22#3444332#g...........",
 "......gGG122#3444332#...........",
 ".....gGG1222#bcbbbbba...........",
 ".....gGG22322#34b*b432#.........",
 ".....gG222211#3455544332........",
 "......g122221#344433322#........",
 "......#111111#2333322#..........",
 ".....b2222211.#1222221#.........",
 "...2332211....a3444332..........",
 "..23332211.....a3444332.........",
 "..23322211.....a34443322........",
 "..22322211.....a34443322........",
 "..22222211......33443322........",
 "..22222221......455544443.......",
 "..11222211.......#34544432......",
 "..111222211......3454433222.....",
 "..111122221......3444433322.....",
 "..1111222211.....34333343344444.",
 "..11111222211....23333#4333#4544",
 "....111112221....222233233334455",
 "......1111111.....1222222223333.",
]
BLADE = {(X0 + 23 + dx, Y0 + y) for y in range(0, 22) for dx in (0, 1)}
def run(*a): return subprocess.run([K, *a], capture_output=True, text=True)
def build(rows, bundle, png):
    g = [['.'] * F for _ in range(F)]
    for i, r in enumerate(rows):
        assert len(r) == 32, (i, len(r), r)
        for x, c in enumerate(r):
            if c != '.': g[Y0 + i][X0 + x] = c
    used = sorted({c for r in g for c in r if c != '.'}); abc = 'abcdefghijklmnopqrstuvwxyz'; code = {c: abc[j] for j, c in enumerate(used)}
    os.makedirs('tmp', exist_ok=True)
    open('tmp/s.grid', 'w').write('\n'.join(f'{code[c]} = {CODE[c]}' for c in used) + '\n\n' + '\n'.join(''.join(code.get(c, '.') for c in r) for r in g) + '\n')
    shutil.rmtree(bundle, ignore_errors=True); run('new', bundle, '--pixel', f'{F}x{F}')
    for n, h in HEX.items(): run('palette', bundle, '--add', h, '--name', n)
    a = run('pixel', bundle, 'l1', '--grid', 'tmp/s.grid'); o = run('pixel', bundle, 'l1', '--color', 'ink', '--outline')
    if a.returncode or o.returncode: print('klad error', (a.stderr or o.stderr)[:300]); sys.exit(1)
    def bare(x, y):                                                              # an edge that needs no outline drawn beside it
        c = g[y][x]
        return c in NO_OUTLINE or c == '#' or (x, y) in BLADE or (c == '1' and y >= Y0 + LOW) or (c in '12' and x < X0 + 5 and y < Y0 + 20)
    opens = [(x, y) for y in range(F) for x in range(F) if g[y][x] == '.' and (nb := [(x + dx, y + dy) for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)) if 0 <= y + dy < F and 0 <= x + dx < F and g[y + dy][x + dx] != '.']) and all(bare(*p) for p in nb)]
    if opens: run('pixel', bundle, 'l1', '--erase', '--cells', ' '.join(f'{x},{y}' for x, y in opens))
    for _ in range(3):                                                           # clean-up pass: klad's doubled corners on the outline are removed
        c = [tuple(x['at']) for x in json.loads(run('check', bundle, '--json').stdout)['findings'] if x['kind'] == 'corner' and x.get('color') == 'ink' and g[x['at'][1]][x['at'][0]] == '.']
        if not c: break
        run('pixel', bundle, 'l1', '--erase', '--cells', ' '.join(f'{x},{y}' for x, y in c))
    run('export', bundle, '--scale', '1', '-o', png)
    f = json.loads(run('check', bundle, '--json').stdout)['findings']
    return collections.Counter(x['kind'] for x in f), f
if __name__ == '__main__':
    os.makedirs('side/out', exist_ok=True)
    kinds, f = build(SIDE, 'side/out/knight_side.klad', 'side/out/knight_side_1x.png'); print('klad check by kind:', dict(kinds))
    print('corner/banding/jagged notes:', [(x['kind'], x.get('at'), x.get('color')) for x in f if x['kind'] != 'stray'][:40])
    Image.open('side/out/knight_side_1x.png').resize((384, 384), Image.NEAREST).save('side/out/knight_side_6x.png')
    ref = Image.open('ref_native.png').convert('RGBA'); px = Image.open('side/render_px_1x.png').convert('RGBA'); me = Image.open('side/out/knight_side_1x.png').convert('RGBA')
    S = 6; W = Image.new('RGB', (3 * 64 * S, 64 * S), (0x7c, 0x84, 0x90)); c = Image.new('RGBA', (64, 64)); c.paste(ref, (18, 1))
    for i, im in enumerate((c, px, me)): im = im.resize((64 * S, 64 * S), Image.NEAREST); W.paste(im, (i * 64 * S, 0), im)
    W.save('side/out/compare_side.png')
