import sys
from PIL import Image
# usage: zoom.py in.png out.png scale [x0 y0 x1 y1]
im = Image.open(sys.argv[1]).convert('RGBA'); k = int(sys.argv[3])
if len(sys.argv) > 4:
    im = im.crop(tuple(int(v) for v in sys.argv[4:8]))
bg = Image.new('RGBA', im.size, (86, 92, 104, 255)); bg.alpha_composite(im)
bg.resize((bg.width * k, bg.height * k), Image.NEAREST).save(sys.argv[2])
