"""The knight as flat shapes, shared by both pixel methods so they draw the same design.
kind, material, mode, shape. Half shapes sit on the viewer's left and are mirrored about x = 47.5.
Materials: S steel, D dark steel, B brass, U undersuit, C cloth, L leather, G glow."""
import numpy as np
from PIL import Image, ImageDraw
F = 96
def R(x0, y0, x1, y1): return ('rect', x0, y0, x1, y1)
def rast(shape):
    im = Image.new('L', (F, F), 0); d = ImageDraw.Draw(im)
    d.rectangle(shape[1:], fill=255) if isinstance(shape, tuple) else d.polygon(shape, fill=255)
    return np.array(im) > 0
# kind, material, mode, shape. Half shapes sit on the viewer's left and are mirrored about x = 47.5.
P = [
 ('pair', 'D', 'plain', R(33, 17, 38, 24)), ('pair', 'G', 'flat3', R(34, 19, 37, 19)),                      # pack vents
 ('pair', 'S', 'flute', [(35, 52), (44, 52), (44, 66), (36, 66)]),                                           # thighs
 ('pair', 'S', 'plain', [(36, 71), (44, 71), (43, 86), (37, 86)]),                                           # greaves
 ('pair', 'G', 'flat3', R(40, 75, 40, 81)),                                                                  # shin lights
 ('pair', 'S', 'plain', [(35, 64), (44, 64), (45, 68), (44, 72), (36, 72), (34, 68)]),                       # knees
 ('pair', 'B', 'flat2', R(36, 72, 44, 72)), ('pair', 'G', 'flat4', R(39, 67, 40, 68)),
 ('pair', 'D', 'lames', [(31, 86), (44, 86), (44, 93), (29, 93)]),                                           # sabatons
 ('sym', 'C', 'flute', [(42, 52), (47, 52), (47, 64), (44, 62)]),                                            # cloth
 ('pair', 'S', 'lames', [(27, 34), (34, 34), (34, 45), (28, 45)]),                                           # upper arms
 ('pair', 'U', 'ribs', R(28, 45, 34, 47)),
 ('sym', 'S', 'flute', [(36, 24), (47, 24), (47, 42), (39, 42), (36, 37)]),                                  # breastplate
 ('sym', 'D', 'plain', [(41, 22), (47, 24), (47, 26), (40, 26)]),                                            # gorget
 ('sym', 'B', 'plain', R(45, 27, 47, 30)), ('sym', 'G', 'flat4', R(46, 28, 47, 29)),                         # chest core
 ('sym', 'B', 'plain', R(38, 42, 47, 44)),                                                                   # belt
 ('sym', 'S', 'lames', [(36, 45), (47, 45), (47, 52), (34, 52)]),                                            # fauld
 ('pair', 'G', 'flat3', R(38, 55, 39, 55)), ('pair', 'G', 'flat3', R(40, 56, 40, 56)), ('pair', 'G', 'flat3', R(41, 55, 42, 55)),   # thigh chevrons
 ('pair', 'S', 'plain', [(22, 29), (26, 23), (35, 22), (39, 25), (39, 33), (34, 37), (24, 36), (21, 33)]),   # pauldrons
 ('pair', 'S', 'plain', [(23, 33), (34, 34), (34, 37), (24, 36)]),
 ('pair', 'G', 'flat3', R(24, 31, 29, 31)),                                                                  # pauldron light strip
 ('pair', 'B', 'plain', [(36, 27), (38, 26), (40, 28), (39, 31), (37, 31)]),                                 # rondels
 ('sym', 'S', 'plain', [(45, 54), (47, 54), (47, 93), (46, 90), (45, 86)]),                                  # blade
 ('sym', 'G', 'flat3', R(47, 56, 47, 87)),
 ('sym', 'B', 'plain', [(36, 51), (47, 51), (47, 53), (37, 53)]),                                            # guard
 ('pair', 'S', 'plain', [(27, 47), (33, 44), (42, 43), (42, 50), (34, 52), (28, 52)]),                       # forearms and cuffs
 ('pair', 'B', 'flat2', [(33, 44), (34, 44), (35, 52), (34, 52)]),                                           # cuff rims
 ('pair', 'S', 'plain', [(26, 43), (31, 42), (33, 46), (30, 50), (26, 48)]),                                 # elbow cops
 ('sym', 'L', 'flat2', R(47, 36, 47, 50)),                                                                   # leather grip
 ('sym', 'S', 'flute', R(42, 44, 46, 50)),                                                                   # lower fist
 ('sym', 'S', 'flute', R(43, 37, 46, 42)),                                                                   # upper fist
 ('sym', 'B', 'plain', R(46, 32, 47, 35)),                                                                   # pommel
 ('pair', 'D', 'plain', [(40, 12), (42, 9), (39, 5), (37, 2), (36, 3), (37, 7), (38, 11)]),                  # horns
 ('sym', 'S', 'plain', [(46, 10), (47, 4), (47, 10)]),                                                       # crest blade
 ('pair', 'S', 'plain', [(41, 15), (36, 13), (40, 17)]), ('pair', 'S', 'plain', [(41, 18), (37, 18), (41, 20)]),   # cheek flares
 ('sym', 'S', 'plain', [(41, 13), (43, 10), (47, 9), (47, 22), (45, 24), (43, 21), (41, 18)]),               # beast mask
 ('pair', 'D', 'flat1', [(42, 14), (46, 15), (46, 16), (42, 15)]),                                           # brow
 ('pair', 'G', 'flat4', R(43, 16, 44, 16)), ('pair', 'G', 'flat3', R(45, 17, 45, 17)),                       # slanted eyes
 ('pair', 'G', 'flat3', R(44, 20, 44, 20)), ('pair', 'G', 'flat3', R(45, 21, 45, 21)), ('pair', 'G', 'flat3', R(46, 20, 46, 20)), ('sym', 'G', 'flat3', R(47, 21, 47, 21)),   # jagged grin
 ('sym', 'S', 'plain', R(47, 24, 47, 27)), ('pair', 'S', 'plain', R(44, 23, 44, 25)),                        # jaw tines
]
# shadow shapes under overhangs (one step darker), as the pixel skill asks: shade the form, not the outline
SHADOWS = [R(36, 24, 59, 25), [(39, 26), (40, 26), (40, 34), (38, 36)], [(56, 26), (57, 26), (59, 36), (57, 34)],   # under the head and inside each pauldron
           R(27, 37, 34, 38), R(61, 37, 68, 38), R(35, 53, 44, 53), R(51, 53, 60, 53), R(36, 73, 43, 73), R(52, 73, 59, 73)]

