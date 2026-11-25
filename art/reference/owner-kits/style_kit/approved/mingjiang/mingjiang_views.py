"""冥将: four idle views (front, left, back, right) at 96. Front = the approved front (mingjiang96.py, sickle).
Side template faces right; the left view is the same template with its own near arm (open hand) and the sickle trailing
in the far hand behind; both are drawn facing right and mirrored as data. Back = front mirrored, minus the sensor eye,
ribs and hood opening, with the cloak drawn over the body. Hood box matches the front (x 38-58, rows 8-32).
Run: python3 mingjiang_views.py -> out/mj_idle_*_1x.png, out/mj_lineup_{1,3}x.png (pass/fail only)
"""
import sys
import tianbing96_v5 as F
import tianbing96_views as V
import mingjiang96 as M
import anim_runner as R

# ---------- shared side pieces (facing right) ----------
CLOAK_S = [("cloak", "g", [(46, 29), (54, 31), (57, 40), (55, 56), (52, 70), (50, 86), (45, 80), (42, 91), (38, 82), (34, 90),
                           (30, 80), (26, 86), (26, 72), (29, 56), (35, 40), (41, 30)], False)]


def leg(dx, far):
    r = "legL" if far else "legR"
    pl = lambda p: [(x + dx, y) for x, y in p]
    return [(r, "f", pl([(43, 58), (51, 58), (52, 74), (44, 76)]), True),
            (r, "u", pl([(44, 60), (50, 60), (51, 73), (45, 74)]), False),
            (r, "s", pl([(43, 73), (53, 73), (53, 78), (43, 78)]), False),
            (r, "u", pl([(44, 78), (51, 78), (50, 87), (45, 87)]), False),
            (r, "u", pl([(43, 87), (55, 87), (58, 91), (43, 91)]), False),
            (r, "b", pl([(53, 89), (57, 89), (58, 91), (53, 91)]), True)]


TORSO_S = [("torso", "f", [(41, 32), (55, 32), (55, 58), (41, 58)], True),
           ("torso", "u", [(42, 33), (54, 33), (54, 56), (48, 58), (42, 56)], False),
           ("torso", "b", [(47, 37), (55, 37), (55, 38), (47, 38)], True),
           ("torso", "b", [(47, 47), (55, 47), (55, 48), (47, 48)], True),
           ("torso", "s", [(53, 39), (57, 40), (57, 50), (53, 51)], False),        # sensor ring, edge-on at the front
           ("torso", "v", [(55, 41), (57, 42), (57, 48), (55, 49)], False),        # the eye, a sliver
           ("skirt", "b", [(41, 54), (55, 54), (55, 57), (41, 57)], True)]
FLAP_S = [("pauR", "g", [(43, 31), (51, 31), (53, 44), (52, 60), (49, 72), (45, 66), (42, 74), (39, 62), (40, 44)], False)]
HEAD_S = [("head", "g", [(40, 28), (40, 22), (41, 16), (43, 11), (44, 8), (49, 10), (54, 14), (57, 20), (58, 26), (54, 32), (42, 32)], False),
          ("head", "f", [(50, 17), (55, 18), (57, 25), (54, 31), (49, 31), (47, 24)], True)]
SIDE_DETAILS = [("glow", 56, 43, 56, 46), ("v2", 56, 41, 56, 42), ("b1", 52, 19, 56, 19), ("out", 46, 40, 46, 52),
                ("out", 36, 59, 37, 74), ("out", 44, 13, 46, 24)]
SIDE_STUDS = [("g3", 44, 20), ("g3", 52, 13), ("g3", 56, 24), ("g3", 41, 24), ("g3", 45, 14), ("g3", 46, 34), ("g3", 52, 34),
              ("b3", 49, 37), ("b3", 52, 47), ("s3", 44, 75), ("s3", 51, 75), ("g3", 50, 62), ("g3", 45, 62),
              ("g3", 33, 50), ("g3", 28, 70), ("g3", 31, 84), ("g3", 40, 86), ("g3", 48, 82), ("g3", 36, 44),
              ("g3", 29, 62), ("g3", 52, 52), ("g3", 40, 44), ("g3", 38, 70), ("g3", 34, 76), ("g3", 47, 70),
              ("b3", 46, 90), ("b3", 54, 90), ("g3", 50, 44), ("g3", 43, 55), ("g3", 27, 80), ("g3", 43, 66)]


def arm_near_right():
    return [("armR", "f", [(47, 38), (53, 38), (58, 52), (52, 54)], True),
            ("armR", "g", [(48, 39), (52, 39), (56, 51), (52, 52)], False),
            ("armR", "s", [(53, 52), (59, 52), (61, 60), (55, 62)], False)]


SICKLE_FWD = [("axe", "s", [(59, 48), (62, 48), (63, 68), (60, 68)], True),                                    # short haft
              ("axe", "v", [(58, 46), (63, 46), (63, 49), (58, 49)], False),                                   # butt cap glow
              ("axe", "s", [(60, 66), (66, 66), (72, 69), (76, 75), (75, 81), (71, 86), (67, 87), (69, 81), (70, 77),
                            (67, 73), (62, 73), (60, 72)], False),                                              # hook, opening forward
              ("axe", "f", [(64, 68), (69, 70), (72, 75), (71, 79)], True),
              ("axe", "b", [(59, 56), (64, 56), (64, 60), (59, 60)], True),
              ("armR", "s", [(55, 55), (65, 55), (66, 62), (62, 64), (56, 61)], False)]                         # fist


def side_right():
    parts = (CLOAK_S + leg(-3, True) + leg(2, False) + TORSO_S + FLAP_S + arm_near_right() + SICKLE_FWD + HEAD_S)
    return dict(parts=parts, details=SIDE_DETAILS, studs=SIDE_STUDS + [("s3", 72, 70), ("s3", 74, 78), ("v2", 60, 47), ("s3", 62, 54), ("g3", 54, 66), ("g3", 56, 40), ("g3", 58, 44), ("s3", 56, 58), ("g3", 48, 56), ("g3", 56, 50), ("g3", 39, 52), ("g3", 55, 28)],
                flip=False, shoulder=(50, 40), fist=(60, 59), hipfix=False)


def side_left():   # near arm = open hand under the flap; sickle trails in the far hand behind the body, hook rearward
    far_sickle = [("axe", "s", [(33, 50), (36, 50), (37, 70), (34, 70)], True),
                  ("axe", "v", [(32, 48), (37, 48), (37, 51), (32, 51)], False),
                  ("axe", "s", [(34, 66), (28, 66), (22, 69), (18, 75), (19, 81), (23, 86), (27, 87), (25, 81), (24, 77), (27, 73), (32, 73), (34, 72)], False),
                  ("axe", "f", [(30, 68), (25, 70), (22, 75), (23, 79)], True),
                  ("axe", "b", [(33, 58), (38, 58), (38, 62), (33, 62)], True),
                  ("armR", "f", [(36, 44), (42, 44), (40, 60), (34, 60)], True),
                  ("armR", "s", [(32, 58), (42, 58), (42, 65), (37, 67), (32, 64)], False)]
    hand = [("armL", "s", [(47, 66), (55, 66), (56, 72), (52, 75), (47, 72)], False)]
    parts = (CLOAK_S + far_sickle + leg(-3, True) + leg(2, False) + TORSO_S + FLAP_S + hand + HEAD_S)
    return dict(parts=parts, details=SIDE_DETAILS, studs=SIDE_STUDS + [("s3", 20, 72), ("s3", 21, 80), ("v2", 35, 49), ("s3", 49, 69)],
                flip=True, shoulder=(40, 44), fist=(37, 62), hipfix=False)


def back():
    keep = []
    for r, rp, pl, fl in M.PARTS:
        if r in ("pauL", "pauR"):
            continue                                        # front flaps
        if r == "torso" and rp in ("b", "s", "v"):
            continue                                        # ribs, sensor ring, eye
        if r == "head" and rp == "f":
            continue                                        # hood opening
        keep.append((r, rp, pl, fl))
    cloak = [p for p in keep if p[0] == "cloak"]
    rest = [p for p in keep if p[0] != "cloak"]
    bodyp = [p for p in rest if p[0] in ("legL", "legR", "torso", "skirt")]
    arms = [p for p in rest if p[0] in ("armL", "armR", "axe")]
    head = [p for p in rest if p[0] == "head"]
    cover = [("cloak", "g", [(40, 30), (55, 30), (60, 38), (63, 52), (66, 66), (62, 74), (63, 84), (57, 78), (52, 86), (47, 79), (42, 87),
                             (37, 78), (32, 84), (31, 74), (28, 66), (31, 52), (35, 38)], False)]
    parts = bodyp + cloak + cover + arms + head
    details = [("out", 47, 32, 48, 80), ("out", 47, 12, 48, 30), ("out", 40, 44, 41, 56), ("out", 54, 44, 55, 56),
               ("out", 38, 78, 40, 78), ("out", 55, 78, 57, 78)]
    studs = [s for s in M.STUDS if not (42 <= s[1] <= 53 and 33 <= s[2] <= 58) and not (41 <= s[1] <= 55 and 17 <= s[2] <= 31)] + [
        ("g3", 44, 36), ("g3", 51, 36), ("g3", 43, 46), ("g3", 52, 46), ("g3", 46, 20), ("g3", 49, 24), ("g3", 45, 28), ("g3", 50, 15),
        ("g3", 44, 54), ("g3", 51, 60), ("g3", 47, 70), ("g3", 40, 72)]
    return dict(parts=parts, details=details, studs=studs, flip=True, shoulder=(61, 40), fist=(70, 62), hipfix=False)


def setup(size="96"):
    F.CONFIG["PAL"] = dict(M.CONFIG["PAL"]); F.CONFIG["RAMP"] = dict(M.CONFIG["RAMP"])
    for r in ("cloak", "axe"):
        if r not in V.BODY:
            V.BODY.append(r)
    V.VIEWS.clear()
    V.VIEWS.update({"front": dict(M.VIEW), "left": side_left(), "back": back(), "right": side_right()})
    V.CONFIG["PREFIX"] = "mj"
    if size == "64":
        import tianbing64_views as T64
        T64.setup()
        V.CONFIG["PREFIX"] = "mj64"
        # a blade stud that would land on a foot pixel in the left-view strike (64 only): drop it
        drop = (T64.X(21), T64.Y(80))
        V.VIEWS["left"]["studs"] = [s for s in V.VIEWS["left"]["studs"] if (s[1], s[2]) != drop]


def frame_fn(name, spec, size):
    return {}


if __name__ == "__main__":
    size = sys.argv[1] if len(sys.argv) > 1 else "96"
    setup(size)
    R.run(V.CONFIG["PREFIX"], size, {}, frame_fn)
