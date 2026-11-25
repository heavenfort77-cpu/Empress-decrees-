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
# ----------------------------------------
# Pose and big shapes follow the reference: striding, far leg dark behind, blade carried upright in front, long swept horns, one clear glow strip.
D = '.'; B = '43'
SIDE = [
 "..11...................4........", "...121.................43.......", ".....121...............43.......", "..11...121.............43.......",
 "...121...121...........43.......", ".....121...121.........43.......", ".......121#45544333#...43.......", "........1#4454443333##.43.......",
 ".........#34444b33***4.43.......", "bc.......#333333322344.43.......", "12.bc....#233333222334.43.......", "12.12.....#22222######.43.......",
 "12.12.....#11221#5#5##.43.......", "12.12......#######.....43.......", "12.12...4555544443#....43.......",
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
 "....gGG#" + "3444332" + "#G" + D * 15,
 "....gGG2#" + "3444332" + "#g" + D * 14,
 "....gGG22#" + "3444332" + "#" + D * 14,
 "....gGG122#" + "3444332" + "#" + D * 13,
 "...gGG1222#" + "bcbbbbba" + D * 13,
 "...gG12221#" + "34b*b4432" + "#" + D * 11,
 "....g1222#" + "3445544332" + "#" + D * 11,
 "....#11221#" + "34443332" + "#" + D * 12,
 "...a22211.#" + "2333322" + "#" + D * 13,
 "..2122111..#" + "122221" + "#" + D * 13,
 "..2332111..." + "3444332" + D * 13,
 "..1222221..a" + "34443332" + D * 12,
 "..1122221..a" + "34443322" + D * 12,
 "..1112222..a" + "33443322" + D * 12,
 "..11112222.." + "23333222" + D * 12,
 "..111122221." + "455544443" + D * 11,
 "..1111222221.." + "34444333" + D * 10,
 "..11112222221." + "234444333" + D * 9,
 "...111122222." + "2344443#443#" + D * 7,
 ".....1111222." + "23444433443344#" + D * 4,
 D * 13 + "2233333333334445" + D * 3,
 D * 13 + "1122222222222334455",
 D * 13 + "11111222222222233" + D * 2,
 D * 13 + "1111111111111111" + D * 3,
]
BLADE = {(X0 + 23 + dx, Y0 + y) for y in range(0, 21) for dx in (0, 1)}
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
    opens = [(x, y) for y in range(F) for x in range(F) if g[y][x] == '.' and (nb := [g[y + dy][x + dx] for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)) if 0 <= y + dy < F and 0 <= x + dx < F and g[y + dy][x + dx] != '.']) and all(c in NO_OUTLINE for c in nb)]
    opens += [(x, y) for y in range(F) for x in range(F) if g[y][x] == '.' and (x, y) not in opens and (nb := [(x + dx, y + dy) for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)) if 0 <= y + dy < F and 0 <= x + dx < F and g[y + dy][x + dx] != '.']) and all(p in BLADE for p in nb)]   # the bare blade has no outline
    if opens: run('pixel', bundle, 'l1', '--erase', '--cells', ' '.join(f'{x},{y}' for x, y in opens))
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
