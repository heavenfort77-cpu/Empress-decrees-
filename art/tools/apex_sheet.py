#!/usr/bin/env python3
"""Review sheets for the apex and cubs from apex_shoot.mjs shots (W4). Usage: python3 apex_sheet.py SHOTDIR OUTDIR [CONCEPTDIR]"""
import os, sys
from PIL import Image, ImageDraw
S, O = sys.argv[1], sys.argv[2]; C = sys.argv[3] if len(sys.argv) > 3 else None
os.makedirs(O, exist_ok=True)


def sheet(name, rows, h=360):
    ims = []
    for row in rows:
        tiles = []
        for f, label in row:
            p = f if os.path.isabs(f) else os.path.join(S, f + '.png')
            if not os.path.exists(p): continue
            im = Image.open(p).convert('RGB'); im = im.resize((round(im.width * h / im.height), h))
            ImageDraw.Draw(im).rectangle([0, 0, 8 + 7 * len(label), 16], fill=(0, 0, 0)); ImageDraw.Draw(im).text((4, 2), label, fill=(255, 255, 255))
            tiles.append(im)
        if tiles:
            r = Image.new('RGB', (sum(t.width for t in tiles) + 4 * (len(tiles) - 1), h), (255, 255, 255)); x = 0
            for t in tiles: r.paste(t, (x, 0)); x += t.width + 4
            ims.append(r)
    W = max(i.width for i in ims); out = Image.new('RGB', (W, sum(i.height for i in ims) + 4 * (len(ims) - 1)), (255, 255, 255)); y = 0
    for i in ims: out.paste(i, (0, y)); y += i.height + 4
    out.save(os.path.join(O, name)); print('sheet', name, out.size)


cpt = (lambda n: os.path.join(C, f'concept_{n}.png')) if C else (lambda n: '')
sheet('tiger_sheet.png', [
    [(cpt(5107), 'concept 5107 (pick, reference only)'), ('tiger_front', 'front'), ('tiger_34', '3/4'), ('tiger_side', 'side'), ('tiger_back', 'back')],
    [('tiger_dormant_34', 'dormant (patina)'), ('tiger_awake_34', 'awake (brass, glowing inlay)'), ('tiger_pounce_windup', 'pounce windup 0.5 s'), ('tiger_roar_windup', 'roar windup 0.5 s (throat core)'), ('tiger_sil', 'silhouette')],
    [('tiger_wake_0', 'wake 0.0 s'), ('tiger_wake_1.4', 'wake 1.4 s'), ('tiger_wake_2.1', 'wake 2.1 s'), ('tiger_wake_2.6', 'wake 2.6 s'), ('tiger_wake_3', 'wake 3.0 s (plates peel)')],
    [('tiger_lods', 'LOD0 / LOD1 / LOD2')]])
sheet('cubs_sheet.png', [
    [(cpt(5216), 'concept 5216 (Stalker pick)'), ('stalker_front', 'Stalker front'), ('stalker_34', '3/4'), ('stalker_side', 'side'), ('stalker_back', 'back'), ('stalker_attack_windup', 'attack windup 0.5 s')],
    [(cpt(5218), 'concept 5218 (Howler pick)'), ('howler_front', 'Howler front'), ('howler_34', '3/4'), ('howler_side', 'side'), ('howler_back', 'back'), ('howler_attack_windup', 'attack windup 0.5 s')],
    [('stalker_sil', 'Stalker silhouette'), ('howler_sil', 'Howler silhouette'), ('stalker_move', 'Stalker move'), ('howler_move', 'Howler move')],
    [('stalker_lods', 'Stalker LODs'), ('howler_lods', 'Howler LODs')]])
sheet('play_sheet.png', [[('play', 'play size (fight framing 10.5 m): tiger, Stalker, Howler, player box 2.05 m')], [('statue', 'royale: dormant statue beside the player box')]], h=540)
sheet('schools_sheet.png', [[('schools_awake', 'school variants awake (ru dao fa / mo yinyang za / ming zongheng nong)'), ('schools_dormant', 'school variants dormant (statue)')]], h=480)
