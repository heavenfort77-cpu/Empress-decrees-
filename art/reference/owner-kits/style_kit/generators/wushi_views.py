"""巫师: four views (front, left, back, right) and the stun-cast attack, at 96 or 64.
Front data is the approved front (wushi96.py). Side template faces right; the left view is drawn facing right and
mirrored as data. Back = front mirrored, minus the mask, mirror and shield face, plus the back of the hood and mantle.
Attack = the ge-lance driven at the target with a soul-fire burst (the stun), same machinery as the 天兵 thrust.
Run: python3 wushi_views.py [96|64]  -> out/ws_* or out/ws64_*  (pass/fail only)
"""
import sys
import tianbing96_v5 as F
import tianbing96_views as V
import wushi96 as W

SOUL = ("#6ff0c8", "#aebfcc", "#3b2f42")   # burst / speed-line colours: soul-fire, steel, black


def lance(fx):   # same shape as the front lance, shaft column centred on fx
    d = fx - 68
    return [(r, rp, [(x + d, y) for x, y in pl], fl) for r, rp, pl, fl in W.PARTS if r == "halberd"]


def legs_side():
    far = [("legL", "f", [(42, 66), (49, 66), (48, 88), (42, 88)], True),
           ("legL", "g", [(43, 68), (48, 68), (47, 86), (43, 86)], False),
           ("legL", "s", [(41, 73), (49, 73), (49, 78), (41, 78)], False),
           ("legL", "g", [(42, 79), (48, 79), (48, 86), (43, 86)], False),
           ("legL", "g", [(39, 86), (49, 86), (52, 91), (39, 91)], False),
           ("legL", "b", [(47, 89), (52, 89), (52, 91), (47, 91)], True)]
    near = [("legR", rp, [(x + 8, y) for x, y in pl], fl) for _, rp, pl, fl in far]
    return far, near


HEAD_S = [   # same box as the front head: x 35-60, rows 8-30
    ("head", "g", [(36, 15), (41, 8), (45, 11), (50, 10), (55, 12), (59, 16), (60, 24), (57, 30), (39, 30), (35, 24)], False),
    ("head", "v", [(40, 10), (42, 9), (44, 12), (41, 13)], True),                         # inner ear
    ("head", "v", [(50, 15), (59, 16), (60, 23), (57, 28), (50, 28), (48, 22)], False),   # mask, at the front
]
MANTLE_S = [("mantle", "g", [(38, 29), (54, 29), (60, 33), (61, 40), (58, 46), (56, 52), (52, 49), (48, 54), (44, 50),
                              (40, 55), (36, 51), (32, 56), (30, 48), (31, 36)], False)]   # hem trails behind
TORSO_S = [("torso", "f", [(41, 30), (56, 30), (56, 62), (41, 62)], True),
           ("torso", "v", [(42, 31), (57, 32), (59, 44), (57, 62), (43, 62), (41, 48)], False),
           ("torso", "b", [(57, 36), (60, 36), (60, 44), (57, 44)], False)]                # rite mirror, edge-on
SKIRT_BACK = [("skirt", "g", [(39, 53), (52, 53), (51, 72), (38, 70)], False)]
SKIRT_FRONT = [("skirt", "b", [(41, 50), (59, 50), (59, 53), (41, 53)], False),
               ("skirt", "v", [(52, 53), (59, 53), (60, 74), (55, 76), (52, 74)], False)]
SIDE_DETAILS = [
    ("b3", 54, 18, 55, 19), ("b3", 55, 22, 56, 23),          # two of the four eyes, one above the other
    ("out", 51, 16, 56, 16), ("out", 53, 26, 58, 26), ("b3", 57, 27, 57, 27),
    ("glow", 59, 39, 59, 41), ("out", 55, 55, 55, 73), ("out", 44, 61, 55, 61),
]
SIDE_STUDS = [("g3", 40, 33), ("g3", 52, 31), ("g3", 34, 44), ("g3", 37, 50), ("g3", 45, 47), ("g3", 56, 41),
              ("b3", 44, 51), ("b3", 54, 51), ("s3", 45, 75), ("s3", 52, 75), ("g3", 46, 81), ("g3", 53, 81),
              ("b3", 42, 88), ("b3", 50, 88), ("g3", 39, 14), ("v2", 52, 18), ("v2", 58, 20), ("v2", 44, 36),
              ("v2", 46, 58), ("g3", 33, 52), ("g3", 49, 51), ("s3", 43, 84), ("s3", 51, 84), ("g3", 57, 30)]


def side_right():   # lance arm near; shield on the far arm, edge-on ahead of the chest
    far, near = legs_side()
    parts = ([("shield", "b", [(58, 40), (63, 42), (64, 52), (63, 60), (58, 62), (57, 52)], False)]
             + far + SKIRT_BACK + near + TORSO_S + SKIRT_FRONT + MANTLE_S + HEAD_S + lance(67) + [
                 ("armR", "f", [(57, 44), (64, 44), (68, 60), (61, 61)], True),
                 ("armR", "g", [(58, 45), (63, 45), (67, 59), (62, 60)], False),
                 ("armR", "b", [(60, 53), (66, 53), (66, 55), (60, 55)], True),
                 ("armR", "s", [(62, 60), (72, 60), (72, 67), (67, 69), (62, 66)], False)])
    studs = SIDE_STUDS + [("s3", 68, 7), ("s3", 75, 16), ("s3", 65, 62), ("b3", 61, 45), ("g3", 60, 48)]
    return dict(parts=parts, details=SIDE_DETAILS, studs=studs, flip=False, shoulder=(59, 45), fist=(67, 64),
                hipfix=False, attack="ATTACK_SIDE")


def side_left():    # shield arm near (shield edge-on in front); lance in the far hand behind
    far, near = legs_side()
    parts = (lance(36) + [("armR", "s", [(31, 60), (41, 60), (41, 67), (36, 69), (31, 66)], False)]
             + far + SKIRT_BACK + near + TORSO_S + SKIRT_FRONT + MANTLE_S + HEAD_S + [
                 ("armL", "s", [(52, 40), (59, 40), (59, 46), (52, 46)], False),
                 ("shield", "b", [(58, 38), (64, 40), (65, 52), (64, 62), (58, 64), (57, 52)], False),
                 ("shield", "v", [(60, 42), (62, 43), (63, 52), (62, 60), (60, 61)], True)])
    studs = SIDE_STUDS + [("s3", 37, 7), ("b3", 61, 39), ("b3", 61, 63), ("s3", 33, 62), ("g3", 55, 41)]
    return dict(parts=parts, details=SIDE_DETAILS, studs=studs, flip=True, shoulder=(39, 45), fist=(36, 64),
                hipfix=False, attack="ATTACK_SIDE")


def back():
    drop_v = {("head", 1), ("torso", 3)}   # the mask and the rite mirror face forward
    parts = []
    for i, p in enumerate(W.PARTS):
        r, rp, pl, fl = p
        if r == "head" and rp == "v" and len(pl) == 6:
            continue                                      # mask
        if r == "torso" and rp == "b":
            continue                                      # rite mirror
        if r == "shield" and rp == "v":
            parts.append((r, "g", pl, fl)); continue      # back of the shield: black leather
        parts.append(p)
    parts += [("mantle", "g", [(37, 30), (58, 30), (59, 56), (55, 52), (51, 57), (47, 53), (43, 57), (39, 52), (36, 56)], False)]
    details = [("out", 47, 32, 48, 52), ("out", 40, 40, 44, 40), ("out", 51, 40, 55, 40), ("out", 47, 55, 48, 74),
               ("b3", 27, 49, 28, 50), ("out", 44, 16, 51, 16), ("out", 47, 17, 48, 27)]
    studs = [s for s in W.STUDS if not (38 <= s[1] <= 57 and 15 <= s[2] <= 28)] + [
        ("g3", 41, 34), ("g3", 54, 34), ("g3", 40, 47), ("g3", 55, 47), ("b3", 47, 31), ("g3", 44, 20), ("g3", 51, 20)]
    return dict(parts=parts, details=details, studs=studs, flip=True, shoulder=(67, 47), fist=(68, 65),
                hipfix=False, attack="ATTACK_FRONT", spear_front=False)


def setup(size="96"):
    F.CONFIG["PAL"] = dict(W.CONFIG["PAL"]); F.CONFIG["RAMP"] = dict(W.CONFIG["RAMP"])
    for r in ("mantle", "shield"):
        if r not in V.BODY:
            V.BODY.append(r)
    V.VIEWS.clear()
    V.VIEWS.update({
        "front": dict(parts=W.PARTS, details=W.DETAILS, studs=W.STUDS, flip=False, shoulder=(67, 47), fist=(68, 65),
                      hipfix=False, attack="ATTACK_FRONT"),
        "left": side_left(), "back": back(), "right": side_right(),
    })
    V.CONFIG["SMEAR"] = SOUL
    V.CONFIG["TIP_BURST"] = True
    V.CONFIG["PREFIX"] = "ws"
    if size == "64":
        import tianbing64_views as T64
        T64.setup()
        V.CONFIG["PREFIX"] = "ws64"


if __name__ == "__main__":
    setup(sys.argv[1] if len(sys.argv) > 1 else "96")
    V.main()
