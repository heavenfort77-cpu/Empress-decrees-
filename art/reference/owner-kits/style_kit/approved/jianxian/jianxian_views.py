"""剑仙: four idle views at 96. Front = the approved front (jianxian96.py). Side template faces right: the held sword (断锋) is in the
character's right hand, so the RIGHT view shows it near; the LEFT view shows the empty open left hand near and the sword hand far.
The three floating swords (定锋, 引锋, 归锋) sit behind the back in a fan (to the left of the body in the facing-right data), the same
in both side views (declared simplification). Back = front mirrored: no face, plain back plate, and the fan drawn over the back.
Run: python3 jianxian_views.py -> out/jx_idle_*_1x.png, out/jx_lineup4_3x.png (pass/fail only)
"""
import sys
import tianbing96_v5 as F
import tianbing96_views as V
import jianxian96 as J
import anim_runner as R

FLOAT_R = ("bladeA", "bladeB", "bladeC", "ringC")
SWORD_R = ("sword", "hand")


def fan(centre, angs, r0=8, du=3):
    """the three whole floating swords, same drawing as the front (J), any centre and angles (C, A, B)"""
    sw = J.sw
    out = []
    FCd, FAd, FBd = (dict(base=centre, ang=a) for a in angs)

    def hilt(Fd, region):
        return [(region, "b", sw(Fd["base"], Fd["ang"], [(-1.2, r0 + 1.5), (1.2, r0 + 1.5), (1.2, r0 + 7), (-1.2, r0 + 7)]), True),
                (region, "s", sw(Fd["base"], Fd["ang"], [(0, r0 - 0.5), (1.8, r0 + 1), (0, r0 + 2.5), (-1.8, r0 + 1)]), False),
                (region, "s", sw(Fd["base"], Fd["ang"], [(-3, r0 + 7), (3, r0 + 7), (2.5, r0 + 9), (-2.5, r0 + 9)]), False)]
    out += [("bladeB", "s", sw(FBd["base"], FBd["ang"], [(-2, 13), (2, 13), (2, 22), (3.5, 25), (6, 29), (2.5, 28), (-0.5, 26), (-2, 22)], du=du), False),
            ("bladeB", "f", sw(FBd["base"], FBd["ang"], [(-0.5, 15), (0.5, 15), (0.5, 22), (-0.5, 22)], du=du), True)] + hilt(FBd, "bladeB")
    out += [("bladeA", "s", sw(FAd["base"], FAd["ang"], [(-2.5, 13), (2.5, 13), (3.5, 22), (3, 30), (0, 37), (-3, 30), (-3.5, 22)], du=du), False),
            ("bladeA", "f", sw(FAd["base"], FAd["ang"], [(-0.5, 15), (0.5, 15), (0.5, 31), (-0.5, 31)], du=du), True)] + hilt(FAd, "bladeA")
    out += [("bladeC", "s", sw(FCd["base"], FCd["ang"], [(-2, 13), (2, 13), (2, 33), (0, 38), (-2, 33)], du=du), False),
            ("ringC", "s", sw(FCd["base"], FCd["ang"], [(-5.5, 26), (-3, 23), (3, 23), (5.5, 26), (5.5, 31), (3, 34), (-3, 34), (-5.5, 31)], du=du), False),
            ("ringC", "f", sw(FCd["base"], FCd["ang"], [(-3.5, 26.5), (-2, 25), (2, 25), (3.5, 26.5), (3.5, 30.5), (2, 32), (-2, 32), (-3.5, 30.5)], du=du), True),
            ("bladeC", "s", sw(FCd["base"], FCd["ang"], [(-2, 22), (2, 22), (2, 33), (0, 38), (-2, 33)], du=du), False),
            ("bladeC", "f", sw(FCd["base"], FCd["ang"], [(-0.5, 15), (0.5, 15), (0.5, 22), (-0.5, 22)], du=du), True)] + hilt(FCd, "bladeC")
    return out


# ---------- side pieces (facing right) ----------
def leg(dx, far):
    r = "legL" if far else "legR"
    pl = lambda p: [(x + dx, y) for x, y in p]
    return [(r, "g", pl([(43, 58), (51, 58), (50, 73), (44, 73)]), False),
            (r, "s", pl([(43, 71), (51, 71), (50, 77), (44, 77)]), False),                   # knee
            (r, "g", pl([(44, 77), (50, 77), (49, 87), (45, 87)]), False),
            (r, "g", pl([(43, 87), (55, 87), (58, 90), (58, 91), (42, 91), (42, 89)]), False),   # pointed foot, toe forward
            (r, "v", pl([(54, 90), (57, 90), (58, 91), (54, 91)]), True)]


TORSO_S = [("torso", "f", [(41, 29), (55, 29), (54, 40), (52, 54), (43, 54), (42, 40)], True),
           ("torso", "g", [(42, 30), (54, 30), (53, 40), (51, 52), (44, 52), (43, 40)], False),
           ("torso", "v", [(43, 38), (54, 38), (54, 39), (43, 39)], True),
           ("torso", "v", [(52, 41), (54, 42), (54, 48), (52, 47)], False),                  # the core, edge-on at the front
           ("skirt", "v", [(43, 52), (53, 52), (53, 55), (43, 55)], True)]
SKIRT_S = [("skirt", "f", [(41, 55), (56, 55), (56, 80), (41, 80)], True),
           ("skirt", "g", [(42, 55), (55, 55), (54, 74), (51, 80), (44, 80), (42, 73)], False),
           ("skirt", "v", [(41, 55), (56, 55), (56, 57), (41, 57)], True),
           ("skirt", "b", [(52, 74), (54, 74), (54, 80), (52, 80)], True)]                   # tassel at the front hem
PAULDRON_S = [("pauL", "g", [(40, 28), (41, 21), (47, 24), (53, 27), (53, 33), (42, 33)], False),
              ("pauL", "g", [(40, 32), (53, 31), (53, 40), (46, 43), (40, 39)], False)]
HEAD_S = [("head", "s", [(43, 7), (55, 7), (55, 9), (43, 9)], True),
          ("head", "b", [(42, 9), (44, 9), (44, 14), (42, 14)], True),
          ("head", "s", [(44, 11), (46, 11), (44, 5)], False), ("head", "s", [(47, 11), (50, 11), (48, 1), (49, 1)], False),
          ("head", "v", [(44, 11), (55, 11), (55, 14), (44, 14)], True),
          ("head", "f", [(45, 24), (51, 24), (51, 30), (45, 30)], True),
          ("head", "g", [(44, 14), (53, 14), (56, 18), (55, 22), (52, 25), (46, 25), (43, 22), (42, 18)], False),
          ("head", "v", [(54, 16), (56, 17), (56, 20), (54, 20)], False)]               # forehead sensor, edge-on
SIDE_DETAILS = [("glow", 55, 18, 55, 19), ("v2", 55, 17, 55, 17), ("glow", 53, 43, 53, 46), ("out", 46, 33, 46, 50), ("out", 48, 58, 48, 72),
                ("out", 44, 13, 45, 23)]
SIDE_STUDS = [("g3", 45, 18), ("g3", 52, 17), ("g3", 47, 22), ("g3", 44, 32), ("g3", 52, 33), ("g3", 46, 36), ("g3", 50, 44),
              ("g3", 45, 50), ("s3", 45, 74), ("s3", 51, 74), ("g3", 47, 63), ("g3", 49, 68), ("g3", 45, 82 - 6), ("g3", 43, 29),
              ("g3", 47, 60), ("g3", 49, 54), ("g3", 52, 36), ("g3", 44, 45), ("s3", 47, 75), ("g3", 50, 62), ("g3", 46, 12),
              ("v2", 56, 90), ("g3", 44, 66), ("g3", 52, 60), ("g3", 43, 36), ("g3", 53, 49), ("g3", 48, 80), ("g3", 46, 85)]

# the held sword and its fist: the front's own drawing moved so the fist sits in front of the near shoulder
DX = 43
sword_front = [(r, rp, [(x + DX, y) for x, y in pl], fl) for r, rp, pl, fl in J.PARTS if r in SWORD_R]
SWORD_ARM = [("armR", "g", [(46, 38), (52, 38), (62, 46), (58, 50), (48, 50)], False),     # shoulder strap running forward to the cuff
             ("armR", "g", [(44, 49), (56, 49), (57, 63), (55, 66), (53, 64), (51, 68), (47, 64), (44, 63)], False)]
OPEN_HAND = [("armL", "g", [(44, 38), (52, 38), (54, 50), (46, 50)], False),
             ("armL", "g", [(44, 49), (55, 49), (56, 63), (54, 66), (52, 64), (50, 68), (46, 64), (44, 63)], False),
             ("armL", "v", [(44, 49), (55, 49), (55, 51), (44, 51)], True),
             ("armL", "s", [(46, 64), (53, 64), (54, 71), (51, 77), (47, 77), (45, 71)], False),
             ("armL", "s", [(46, 76), (48, 76), (48, 80), (46, 80)], False), ("armL", "s", [(49, 77), (51, 77), (51, 82), (49, 82)], False)]
FAN_SIDE = fan((41, 43), (6, -20, -46))     # behind the back, spreading up and backward (left in the facing-right data)


def side_right():   # near = right side: the sword fist in front
    parts = (FAN_SIDE + leg(-3, True) + leg(2, False) + SKIRT_S + TORSO_S + PAULDRON_S + SWORD_ARM
             + [p for p in sword_front if p[0] == "sword" and p[1] in ("s", "v")][:3] + [p for p in sword_front if p[0] == "hand"]
             + [p for p in sword_front if p[0] == "sword"][3:] + HEAD_S)
    return dict(parts=parts, details=SIDE_DETAILS + [("out", DX + 12, 40, DX + 22, 40)], studs=SIDE_STUDS, flip=False, shoulder=(50, 40), fist=(61, 40), hipfix=False)


def side_left():   # near = left side: empty open hand; the sword fist is far (behind the body edge)
    far_arm = [("armR", "g", [(46, 38), (52, 38), (62, 46), (58, 50), (48, 50)], False)]
    far = FAN_SIDE + far_arm + [p for p in sword_front if p[0] in SWORD_R]
    parts = far + leg(-3, True) + leg(2, False) + SKIRT_S + TORSO_S + PAULDRON_S + OPEN_HAND + HEAD_S
    return dict(parts=parts, details=SIDE_DETAILS + [("out", DX + 12, 40, DX + 22, 40)], studs=SIDE_STUDS, flip=True, shoulder=(48, 40), fist=(50, 71), hipfix=False)


def back():
    front = J.PARTS
    bodyr = ("legL", "legR", "torso", "skirt", "pauL", "pauR")
    base = []
    for r, rp, pl, fl in front:
        if r in FLOAT_R or r in ("armR", "armL", "handR") or r in SWORD_R:
            continue
        if r == "head":
            if min(y for _, y in pl) >= 13 and rp in ("g", "v"):
                continue                                     # the face and its sensor
            if rp == "f":
                pass
        if r == "torso" and rp == "v" and pl[0][1] >= 40 and len(pl) > 4:
            continue                                         # the core
        base.append((r, rp, pl, fl))
    bodyp = [p for p in base if p[0] in bodyr]
    head = [p for p in base if p[0] == "head"]
    back_head = [("head", "g", [(43, 14), (52, 14), (54, 18), (53, 22), (50, 25), (45, 25), (42, 22), (41, 18)], False),
                 ("head", "b", [(46, 21), (49, 21), (49, 25), (46, 25)], True)]               # crimson tie
    back_plate = [("torso", "s", [(41, 32), (54, 32), (52, 52), (43, 52)], False)]
    arms = [p for p in front if p[0] in ("armR", "armL", "handR") or p[0] in SWORD_R]
    fan_over = fan((66, 44), (-6, 20, 46))
    parts = bodyp + back_plate + fan_over + arms + head[:0] + back_head + head
    details = [("out", 47, 32, 48, 80), ("out", 47, 12, 48, 24), ("out", 40, 41, 42, 41), ("out", 53, 41, 55, 41), ("out", 42, 49, 53, 49)]
    studs = [s for s in J.STUDS if not (41 <= s[1] <= 55 and 14 <= s[2] <= 30)] + [("g3", 44, 20), ("g3", 51, 20), ("g3", 45, 36), ("g3", 52, 44)]
    return dict(parts=parts, details=details, studs=studs, flip=True, shoulder=(66, 40), fist=(68, 70), hipfix=False)


def setup(size="96"):
    F.CONFIG["PAL"] = dict(J.CONFIG["PAL"]); F.CONFIG["RAMP"] = dict(J.CONFIG["RAMP"])
    for r in FLOAT_R + SWORD_R + ("armR", "handR"):
        if r not in V.BODY:
            V.BODY.append(r)
    V.VIEWS.clear()
    V.VIEWS.update({"front": J.VIEW, "left": side_left(), "back": back(), "right": side_right()})
    V.CONFIG["PREFIX"] = "jx"
    if size == "64":
        import tianbing64_views as T64
        T64.setup()
        V.CONFIG["PREFIX"] = "jx64"
        V.CONFIG["HEIGHT"] = (58, 63)


def frame_fn(name, spec, size):
    return {}


if __name__ == "__main__":
    size = sys.argv[1] if len(sys.argv) > 1 else "96"
    setup(size)
    R.run(V.CONFIG["PREFIX"], size, {}, frame_fn)
