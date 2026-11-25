"""Model 1 generator (cocolito method): python3 gen_m1.py  -> out_m1/"""
import os, sys
from pxkit import Cv, up, sheet
import knight

# ============================== CONFIG (tune by hand) ==============================
CONFIG = {
    'light': (-0.50, -0.62, 0.60),      # from upper left, toward the viewer
    'shade_range': (-0.25, 0.98),       # intensity mapped onto each ramp
    'shade_gamma': 1.25,
    'part_shadow': 2,                   # tones a part darkens the part under it (0 = off)
    'glow': 'glow',
    'despeckle': True,                  # lone mid-tone pixels join their neighbours
    'keep_single': ['glow', 'brass', 'grip'],
    'outline_order': ['gun', 'cloth', 'grip', 'brass', 'steel', 'glow'],  # darkest wins
    'ramps': {                          # tone 0 = outline, then dark to light
        'steel': ['#161b27', '#2f394b', '#4c5a70', '#74839a', '#a3afc0', '#d0d8e2', '#f7fafc'],
        'gun':   ['#0b0d14', '#181c28', '#272e3f', '#3a4459', '#55627a'],
        'brass': ['#3a2408', '#7a4e12', '#b9801c', '#e9b53a', '#ffe79a'],
        'glow':  ['#0e5a70', '#2aa9c4', '#7fe6f2', '#d6fbff', '#f7fafc'],
        'cloth': ['#0d2618', '#1a4029', '#2a5e3d', '#3d7d52', '#58a06c'],
        'grip':  ['#3d0c0c', '#7a1a1a', '#b83a2c', '#e0664a'],
    },
}
# ===================================================================================

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out_m1')


def render(view):
    c = Cv(CONFIG)
    getattr(knight, view)(c)
    c.part_shadow(); c.despeckle(); c.outline()
    return c


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    views = sys.argv[1:] or ['front', 'left', 'back', 'right']
    ims = []
    for v in views:
        im = render(v).image()
        im.save(f'{OUT}/knight_{v}_1x.png'); ims.append(im)
    s = sheet(ims, bg=(0, 0, 0, 0)); s.save(f'{OUT}/knight_4view_1x.png')
    up(sheet(ims), 8).save(f'{OUT}/knight_4view_8x.png')
    up(sheet(ims), 3).save(f'{OUT}/knight_4view_3x.png')
    print('wrote', views)
