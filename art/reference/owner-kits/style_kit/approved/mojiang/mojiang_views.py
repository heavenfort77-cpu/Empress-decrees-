"""墨将: four idle views (front, left, back, right) at 96. Front = the approved front (mojiang96.py).
Side template faces right: crossbow seen from the side (long stock, vertical limb at the front, loaded bolt, magazine box on a post),
end-on mallet head, plumb bob hanging at the belt front. Right view: mallet arm near. Left view: rope-coil arm near, mallet in the far hand behind.
Back = front mirrored minus visor, square, ink line and plumb bob, plus the winch-drum rack (rope drums and a crank) on the back.
Head box matches the front (x 37-58, rows 20-38). Run: python3 mojiang_views.py [96] -> out/mo_idle_*_1x.png, out/mo_lineup_{1,3}x.png
"""
import sys
import tianbing96_v5 as F
import tianbing96_views as V
import mojiang96 as M
import anim_runner as R


def leg(dx, far):
    r = "legL" if far else "legR"
    pl = lambda p: [(x + dx, y) for x, y in p]
    return [(r, "g", pl([(40, 74), (52, 74), (51, 86), (41, 86)]), False),
            (r, "s", pl([(39, 73), (53, 73), (52, 78), (40, 78)]), False),
            (r, "v", pl([(41, 81), (52, 81), (52, 83), (41, 83)]), True),
            (r, "g", pl([(36, 86), (55, 86), (58, 90), (58, 91), (35, 91), (35, 89)]), False),
            (r, "b", pl([(57, 88), (63, 90), (63, 91), (57, 91)]), True),        # toe stake, forward
            (r, "b", pl([(31, 88), (36, 89), (36, 91), (30, 91)]), True)]        # heel stake


SKIRT_S = [("skirt", "g", [(39, 58), (56, 58), (62, 70), (34, 70)], False), ("skirt", "b", [(38, 56), (57, 56), (57, 59), (38, 59)], True)]
for a, b in ((34, 38), (41, 45), (48, 52), (56, 60)):
    SKIRT_S.append(("skirt", "g", [(a, 69), (b, 69), (b, 74), (a, 74)], False))
TORSO_S = [("torso", "f", [(37, 36), (59, 36), (57, 50), (54, 58), (41, 58), (38, 50)], True),
           ("torso", "g", [(38, 37), (58, 37), (56, 50), (53, 56), (42, 56), (39, 50)], False),
           ("torso", "b", [(39, 43), (58, 43), (57, 44), (40, 44)], True),
           ("torso", "b", [(40, 49), (56, 49), (55, 50), (41, 50)], True),
           ("torso", "v", [(55, 38), (56, 38), (56, 57), (55, 57)], True),                 # ink line, at the front edge
           ("neck", "g", [(43, 34), (52, 34), (52, 40), (43, 40)], False)]
PLUMB_S = [("torso", "v", [(56, 58), (57, 58), (57, 64), (56, 64)], True),
           ("torso", "v", [(57, 63), (60, 68), (57, 74), (54, 68)], False)]
PAULDRON_S = [("pauR", "g", [(41, 34), (48, 31), (55, 33), (57, 40), (53, 47), (44, 48), (40, 42)], False),
              ("pauR", "v", [(41, 41), (56, 41), (56, 43), (41, 43)], True)]
BOW_S = [("bow", "b", [(43, 32), (49, 32), (49, 40), (43, 40)], False),                    # post and magazine box
         ("bow", "v", [(43, 36), (49, 36), (49, 37), (43, 37)], True),
         ("bow", "b", [(37, 28), (62, 26), (62, 31), (37, 31)], False),                    # stock
         ("bow", "b", [(61, 12), (65, 17), (67, 29), (65, 41), (61, 46), (63, 40), (64, 29), (63, 18)], False),   # limb, edge-on
         ("bow", "s", [(62, 13), (63, 13), (63, 45), (62, 45)], True),                     # string
         ("bow", "s", [(46, 24), (48, 24), (48, 28), (46, 28)], True),                     # bolt in the magazine
         ("bow", "s", [(50, 26), (66, 26), (68, 27.5), (66, 29), (50, 29)], False)]        # loaded bolt, pointing forward
HEAD_S = [("head", "v", [(46, 6), (48, 6), (44, 19), (42, 19)], False), ("head", "v", [(47, 6), (49, 6), (51, 19), (49, 19)], False),
          ("head", "v", [(46, 3), (50, 3), (51, 6), (50, 9), (46, 9), (45, 6)], False),
          ("head", "g", [(37, 38), (37, 29), (40, 24), (44, 21), (48, 20), (52, 21), (56, 24), (58, 29), (58, 38)], False),
          ("head", "f", [(50, 30), (58, 30), (58, 35), (50, 35)], True)]
for a, b in ((40, 42), (45, 47), (50, 52)):
    HEAD_S.append(("head", "s", [(a, 18), (b, 18), (b, 24), (a, 24)], False))
HEAD_S.append(("head", "b", [(37, 36), (58, 36), (58, 38), (37, 38)], True))
SIDE_DETAILS = [("glow", 47, 5, 48, 6), ("out", 47, 6, 47, 6), ("v2", 51, 32, 57, 32), ("glow", 56, 32, 58, 33),
                ("v1", 54, 41, 54, 41), ("v1", 54, 45, 54, 45), ("v1", 54, 52, 54, 52), ("glow", 56, 67, 57, 69),
                ("out", 45, 59, 45, 69), ("out", 36, 60, 36, 68)]
SIDE_STUDS = [("g3", 40, 39), ("g3", 52, 39), ("b3", 43, 43), ("b3", 52, 43), ("g3", 42, 47), ("g3", 50, 54), ("s3", 42, 75), ("s3", 49, 75),
              ("g3", 41, 62), ("g3", 52, 62), ("g3", 44, 66), ("g3", 57, 66), ("v2", 44, 82), ("v2", 50, 82), ("g3", 43, 37), ("g3", 46, 45),
              ("b3", 40, 29), ("b3", 52, 29), ("b3", 58, 27), ("s3", 64, 20), ("s3", 64, 38), ("b3", 45, 34), ("g3", 40, 26), ("g3", 55, 28),
              ("s3", 41, 20), ("s3", 51, 20), ("g3", 39, 33), ("g3", 46, 36), ("g3", 53, 35), ("s3", 49, 21), ("g3", 38, 66), ("g3", 48, 63),
              ("b3", 38, 90), ("b3", 60, 90), ("g3", 45, 84), ("g3", 40, 85), ("s3", 54, 78), ("g3", 38, 31), ("g3", 56, 37), ("s3", 41, 77),
              ("g3", 44, 52), ("g3", 40, 52), ("s3", 66, 27), ("v2", 47, 5), ("b3", 52, 44), ("g3", 42, 70), ("g3", 52, 71)]


def mallet_end(cx, cy, flat_ring=True):   # cylinder head seen end-on
    pts = [(cx - 3, cy - 7), (cx + 4, cy - 7), (cx + 8, cy - 3), (cx + 8, cy + 3), (cx + 4, cy + 7), (cx - 3, cy + 7), (cx - 7, cy + 3), (cx - 7, cy - 3)]
    return [("mallet", "s", pts, False),
            ("mallet", "v", [(cx - 4, cy - 1), (cx + 5, cy - 1), (cx + 5, cy + 1), (cx - 4, cy + 1)], True)]


def side_right():   # mallet arm near
    arm = [("armR", "g", [(46, 46), (53, 46), (55, 56), (48, 56)], False),
           ("armR", "s", [(46, 55), (56, 55), (56, 60), (46, 60)], False),
           ("mallet", "b", [(56, 58), (59, 58), (59, 82), (56, 82)], True)] + mallet_end(58, 81) + [
           ("armR", "s", [(53, 60), (63, 60), (63, 66), (53, 66)], False)]
    parts = (leg(-4, True) + leg(2, False) + SKIRT_S + TORSO_S + PLUMB_S + PAULDRON_S + BOW_S + arm + HEAD_S)
    return dict(parts=parts, details=SIDE_DETAILS, studs=SIDE_STUDS + [("s3", 60, 78), ("s3", 55, 84), ("b3", 57, 70)],
                flip=False, shoulder=(50, 48), fist=(58, 63), hipfix=False)


def side_left():   # rope-coil arm near; mallet in the far hand behind
    far = [("armR", "g", [(35, 46), (42, 46), (40, 58), (34, 58)], False),
           ("armR", "s", [(28, 58), (38, 58), (38, 64), (28, 64)], False),
           ("mallet", "b", [(30, 62), (33, 62), (33, 82), (30, 82)], True)] + mallet_end(31, 81)
    near = [("armL", "g", [(42, 46), (50, 46), (50, 56), (43, 56)], False),
            ("armL", "s", [(42, 55), (52, 55), (53, 60), (42, 60)], False),
            ("armL", "b", [(42, 60), (55, 60), (57, 70), (43, 71)], False)]                # rope coil at the hip
    parts = (far + leg(-4, True) + leg(2, False) + SKIRT_S + TORSO_S + PLUMB_S + PAULDRON_S + BOW_S + near + HEAD_S)
    return dict(parts=parts, details=SIDE_DETAILS, studs=SIDE_STUDS + [("s3", 33, 76), ("s3", 28, 82), ("b3", 48, 66), ("b3", 52, 69)],
                flip=True, shoulder=(38, 48), fist=(33, 62), hipfix=False)


def back():
    bows = [p for p in M.PARTS if p[0] == "bow"]
    legs = [p for p in M.PARTS if p[0] in ("legL", "legR")]
    skirt = [p for p in M.PARTS if p[0] == "skirt"]
    torso = [p for p in M.PARTS if p[0] in ("torso", "neck") and p[1] in ("f", "g") and p[2][0] != (47, 58)]
    torso = [p for p in torso if not (p[0] == "torso" and p[1] == "g" and p[2][0] in ((47, 58),))]
    rest = [p for p in M.PARTS if p[0] in ("pauL", "pauR", "armL", "armR", "mallet")]
    head = [p for p in M.PARTS if p[0] == "head" and p[1] != "f"]
    rack = [("rack", "b", [(34, 40), (61, 40), (61, 55), (34, 55)], False),                 # winch drum, rope wound
            ("rack", "v", [(34, 43), (61, 43), (61, 44), (34, 44)], True), ("rack", "v", [(34, 51), (61, 51), (61, 52), (34, 52)], True),
            ("rack", "s", [(32, 40), (35, 40), (35, 55), (32, 55)], False), ("rack", "s", [(60, 40), (63, 40), (63, 55), (60, 55)], False),
            ("rack", "s", [(46, 34), (49, 34), (49, 41), (46, 41)], False), ("rack", "b", [(44, 32), (51, 32), (51, 35), (44, 35)], True),   # crank
            ("rack", "b", [(38, 57), (57, 57), (57, 60), (38, 60)], True)]                  # rope tail on the belt
    parts = bows + legs + skirt + torso + rack + rest + head
    details = [("out", 47, 60, 48, 72), ("out", 47, 21, 48, 35), ("out", 36, 46, 36, 53), ("out", 59, 46, 59, 53),
               ("glow", 47, 5, 48, 6), ("out", 47, 6, 47, 6)]
    studs = [s for s in M.STUDS if not (36 <= s[1] <= 59 and 36 <= s[2] <= 56) and not (38 <= s[1] <= 57 and 27 <= s[2] <= 37)] + [
        ("g3", 38, 30), ("g3", 56, 30), ("g3", 42, 27), ("g3", 52, 26), ("b3", 40, 47), ("b3", 55, 47), ("g3", 36, 37), ("g3", 58, 37),
        ("s3", 37, 42), ("s3", 58, 53), ("g3", 45, 62), ("g3", 50, 66), ("b3", 40, 42), ("b3", 54, 42)]
    return dict(parts=parts, details=details, studs=studs, flip=True, shoulder=(69, 48), fist=(71, 63), hipfix=False)


def setup(size="96"):
    F.CONFIG["PAL"] = dict(M.CONFIG["PAL"]); F.CONFIG["RAMP"] = dict(M.CONFIG["RAMP"])
    for r in ("bow", "mallet", "rack"):
        if r not in V.BODY:
            V.BODY.append(r)
    V.VIEWS.clear()
    V.VIEWS.update({"front": dict(M.VIEW), "left": side_left(), "back": back(), "right": side_right()})
    V.CONFIG["PREFIX"] = "mo"
    V.CONFIG["HEIGHT"] = (72, 94)
    if size == "64":
        import tianbing64_views as T64
        T64.setup()
        V.CONFIG["PREFIX"] = "mo64"
        V.CONFIG["HEIGHT"] = (56, 62)


def frame_fn(name, spec, size):
    return {}


if __name__ == "__main__":
    size = sys.argv[1] if len(sys.argv) > 1 else "96"
    setup(size)
    R.run(V.CONFIG["PREFIX"], size, {}, frame_fn)
