#!/usr/bin/env python3
"""FIXB 25 Nov review sheets (side by side at the same scale, labelled) from fixb_shoot.mjs shots and the textures.
Usage: python3 fixb_sheets.py SHOTDIR TEXDIR OUTDIR"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
S, TX, O = sys.argv[1:4]; os.makedirs(O, exist_ok=True)

def cell(path, w, crop=None):
    im = Image.open(path).convert('RGB')
    if crop: im = im.crop(crop)
    return im.resize((w, round(im.height * w / im.width)))

def sheet(name, rows, w=960):
    """rows: list of rows, each a list of (label, path, crop)"""
    cells = [[(l, cell(p, w, c)) for l, p, c in r if os.path.exists(p)] for r in rows]
    cols = max(len(r) for r in cells); hs = [max(im.height for _, im in r) + 26 for r in cells if r]
    out = Image.new('RGB', (cols * w, sum(hs)), (20, 20, 20)); d = ImageDraw.Draw(out); y = 0
    for r, h in zip([r for r in cells if r], hs):
        for i, (l, im) in enumerate(r):
            out.paste(im, (i * w, y + 26)); d.text((i * w + 6, y + 7), l, fill=(255, 255, 255))
        y += h
    out.save(f'{O}/{name}.jpg', quality=88); print(name, out.size)

s = lambda n: f'{S}/{n}.png'
sheet('plaster_side_by_side', [[('A2 approved (lum 169) hall_wide', s('hall_wide'), None), ('candidate PLASTER_K hall_wide', s('hall_wide_k'), None)],
                              [('approved hall_play', s('hall_play'), None), ('candidate hall_play', s('hall_play_k'), None)],
                              [('A10 mural (matched to A2) corridor_play', s('corridor_play'), None), ('candidate corridor_play', s('corridor_play_k'), None)]])
sheet('core_inlay', [[('core_wide (inlay)', s('core_wide'), None), ('core_wide no inlay', s('core_wide_noinlay'), None)],
                     [('core_play (inlay)', s('core_play'), None), ('core_play no inlay', s('core_play_noinlay'), None)],
                     [('core_play + hazard rings (inlay)', s('core_play_tell'), None), ('core_play + hazard rings, no inlay', s('core_play_tell_noinlay'), None)]])
sheet('core_throne', [[('round 2: dais 2.8 m, throne x1.0', s('core_wide_r2'), None), ('FIXB: dais 1.5 m, throne x1.4', s('core_wide_noinlay'), None)],
                      [('piece throne_dais', s('piece_throne_dais'), None)]])
sheet('hall_racks', [[('round 2 racks 1.6 x 1.8 m', s('hall_wide_r2'), None), ('FIXB racks 2.4 x 2.8 m', s('hall_wide'), None)],
                     [('round 2 burnt', s('hall_burnt_wide_r2'), None), ('FIXB burnt', s('hall_burnt_wide'), None)],
                     [('FIXB hall_play', s('hall_play'), None), ('piece slip_rack', s('piece_slip_rack'), None)]])
sheet('garden', [[('round 2 garden_wide (170 cards, black-lake pond)', s('garden_wide_r2'), None), ('FIXB garden_wide', s('garden_wide'), None)],
                 [('round 2 garden_play', s('garden_play_r2'), None), ('FIXB garden_play', s('garden_play'), None)]])
sheet('flags_court', [[('court_wide', s('court_wide'), None), ('court_play', s('court_play'), None)], [('piece que_pair', s('piece_que_pair'), None)]])
sheet('brass_pieces', [[('pillar (brass sleeve)', s('piece_pillar'), None), ('door (brass bar, masks)', s('piece_door'), None)],
                       [('hall_locked_play', s('hall_locked_play'), None), ('bridge_play (mercury)', s('bridge_play'), None)]])
sheet('tally_round3', [[('round 2 play (500 tris)', 'art/tally/round2/play.png', (560, 260, 1360, 710)), ('round 3 play (brass)', s('tally_play'), (560, 260, 1360, 710))],
                       [('front', s('tally_turn_front'), None), ('3/4', s('tally_turn_34'), None)], [('side', s('tally_turn_side'), None), ('back', s('tally_turn_back'), None)],
                       [('top', s('tally_top'), None), ('lods', s('tally_lods'), None)],
                       [('sil', s('tally_pass_sil'), None), ('flat', s('tally_pass_flat'), None)], [('shade', s('tally_pass_shade'), None), ('tex', s('tally_pass_tex'), None)],
                       [('wide', s('tally_wide'), None)]], w=800)
sheet('merc_round2', [[('round 1 idle', 'art/merc/round1/play_idle.png', (420, 160, 1500, 760)), ('round 2 idle', s('merc_play_idle'), (420, 160, 1500, 760))],
                      [('round 1 warn', 'art/merc/round1/play_warn.png', (420, 160, 1500, 760)), ('round 2 warn', s('merc_play_warn'), (420, 160, 1500, 760))],
                      [('round 1 hot', 'art/merc/round1/play_hot.png', (420, 160, 1500, 760)), ('round 2 hot', s('merc_play_hot'), (420, 160, 1500, 760))],
                      [('close idle', s('merc_close_idle'), None), ('close warn', s('merc_close_warn'), None)]], w=800)
# textures: pond water, star inlay over the approved floor, flags on grey, mercury matcap (each 1024 = 4 m, shown at 512)
fl = Image.open(f'{TX}/hall_floor.png').convert('RGBA'); inl = Image.open(f'{TX}/star_inlay.png').convert('RGBA'); comp = fl.copy(); comp.alpha_composite(inl)
comp.convert('RGB').save(f'{O}/_inlay_over_floor.png')
fg = Image.new('RGBA', (1024, 1024), (128, 128, 128, 255)); fg.alpha_composite(Image.open(f'{TX}/signal_flags.png').convert('RGBA')); fg.convert('RGB').save(f'{O}/_flags_on_grey.png')
sheet('textures', [[('pond_water (4 m)', f'{TX}/pond_water.png', None), ('star_inlay over hall_floor (4 m)', f'{O}/_inlay_over_floor.png', None)],
                   [('signal_flags (CONFIG.SCHOOLS order) on grey', f'{O}/_flags_on_grey.png', None), ('mercury_matcap', f'{TX}/mercury_matcap.png', None)]], w=512)
for f in ('_inlay_over_floor.png', '_flags_on_grey.png'): os.remove(f'{O}/{f}')
