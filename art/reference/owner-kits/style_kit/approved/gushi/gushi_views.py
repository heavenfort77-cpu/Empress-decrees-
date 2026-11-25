"""蛊师: four idle views at 96. Front = the approved front (gushi96.py). Side template faces right: the vessel is a circle with its window
edge-on at the front, the head leans forward, the abdomen sac trails backward, reverse-knee legs, thin limbs. The LEFT view shows the
character's left side (three small pods, left arms); the RIGHT view shows the right side (one big pod). Both are drawn facing right and the
left one is mirrored as data. Back = front mirrored: a dorsal shell with a split seam and ribs, an amber vent, no window, no lenses.
Run: python3 gushi_views.py -> out/gs_idle_*_1x.png, out/gs_lineup_3x.png (pass/fail only)
"""
import sys
import tianbing96_v5 as F
import tianbing96_views as V
import gushi96 as G
import anim_runner as R

seg, circ_at = G.seg, G.circ_at


def leg(dx, far):
    r = "legL" if far else "legR"
    P = lambda p: (p[0] + dx, p[1])
    return [(r, "g", seg(P((48, 72)), P((57, 79)), 7), False), (r, "g", seg(P((57, 79)), P((48, 89)), 5), False),
            (r, "g", [(P((44, 88))[0], 88), (P((58, 88))[0], 88), (P((61, 91))[0], 91), (P((44, 91))[0], 91)], False),
            (r, "b", [(P((57, 89))[0], 89), (P((61, 89))[0], 89), (P((60, 91))[0], 91), (P((57, 91))[0], 91)], True),
            (r, "b", [(P((54, 76))[0], 76), (P((60, 76))[0], 76), (P((59, 80))[0], 80), (P((54, 80))[0], 80)], True)]


# abdomen: hangs under and a little behind the vessel (not a tail), three ring bands
ABDOMEN = [("skirt", "g", [(44, 60), (54, 62), (56, 70), (52, 80), (44, 84), (32, 84), (27, 78), (28, 68), (34, 61)], False),
           ("skirt", "b", seg((31, 67), (55, 67), 1.6), True), ("skirt", "b", seg((29, 74), (55, 74), 1.6), True),
           ("skirt", "b", seg((32, 80), (51, 80), 1.6), True)]
# the vessel: bone ribs, a hatch ring with an amber intake port (the life-steal intake), a rivet seam; window edge-on at the front
VESSEL = [("torso", "f", circ_at(47, 46, 18, 32), True), ("torso", "g", circ_at(47, 46, 17, 32), False),
          ("torso", "b", seg((34, 38), (58, 38), 2), True), ("torso", "b", seg((34, 56), (58, 56), 2), True),   # bone ribs
          ("torso", "f", seg((40, 32), (40, 61), 1), True),                                               # dark seam
          ("torso", "b", circ_at(46, 47, 6), False), ("torso", "f", circ_at(46, 47, 4), True),            # hatch ring
          ("torso", "v", circ_at(46, 47, 2), False),                                                      # amber intake port
          ("torso", "b", [(58, 38), (62, 40), (64, 46), (62, 52), (58, 54), (60, 46)], False),            # window rim, edge-on
          ("torso", "f", [(59, 41), (62, 43), (62, 49), (59, 51)], True),
          ("torso", "v", [(60, 43), (62, 45), (62, 48), (60, 49)], False),                                # the survivor, a sliver
          ("torso", "b", [(44, 29), (54, 29), (56, 33), (42, 33)], True)]
# head: dome on a short neck; antennae sweep BACK and up, clear of the dome, so the head is not a hood
HEAD = [("head", "b", seg((47, 10), (42, 5), 2), True), ("head", "b", seg((42, 5), (34, 2), 2), True),
        ("head", "b", seg((50, 9), (46, 3), 2), True), ("head", "b", seg((46, 3), (39, 1), 2), True),
        ("head", "f", [(48, 22), (53, 22), (53, 30), (48, 30)], True),
        ("head", "g", [(46, 22), (46, 15), (49, 10), (56, 10), (59, 15), (58, 22)], False),
        ("head", "f", [(54, 14), (59, 14), (59, 19), (54, 19)], True), ("head", "v", [(55, 15), (58, 15), (58, 18), (55, 18)], False),
        ("head", "b", [(55, 21), (58, 21), (58, 26), (56, 25)], False)]


def arms(near, wrist_up):
    w = 70 if wrist_up else 69
    a = "armR" if near else "armL"; h = "hand"
    o = 0 if near else -5
    return [(a, "g", seg((52 + o, 40), (62 + o, 35), 4), False), (a, "g", seg((62 + o, 35), (w + o, 27), 4), False),
            (h, "b", seg((w + o, 27), (w - 2 + o, 19), 3), False), (h, "b", seg((w + o, 27), (w + 4 + o, 20), 3), False),
            (a, "g", seg((50 + o, 52), (58 + o, 58), 4), False), (a, "g", seg((58 + o, 58), (60 + o, 70), 4), False),
            (h, "b", seg((60 + o, 70), (58 + o, 78), 3), False), (h, "b", seg((60 + o, 70), (63 + o, 78), 3), False)]


# pods on the abdomen, bigger and set apart so they can be counted: left three, right one big
PODS_L = [("pauL", "g", circ_at(34, 70, 5.5), False), ("pauL", "b", circ_at(34, 70, 3.4), False), ("pauL", "v", circ_at(34, 70, 1.6), False),
          ("pauL", "g", circ_at(47, 74, 5), False), ("pauL", "b", circ_at(47, 74, 3), False), ("pauL", "v", circ_at(47, 74, 1.4), False),
          ("pauL", "g", circ_at(38, 80, 4.2), False), ("pauL", "b", circ_at(38, 80, 2.4), False), ("pauL", "v", circ_at(38, 80, 1), False)]
POD_R = [("pauR", "g", circ_at(40, 74, 8), False), ("pauR", "b", circ_at(40, 74, 5.4), False), ("pauR", "v", circ_at(40, 74, 2.8), False)]
SIDE_DETAILS = [("glow", 56, 16, 57, 16), ("out", 50, 33, 52, 33), ("glow", 46, 46, 46, 46), ("out", 38, 44, 38, 50)]
SIDE_STUDS = [("g3", 40, 36), ("g3", 52, 36), ("g3", 36, 46), ("g3", 56, 56), ("g3", 44, 56), ("g3", 48, 40), ("g3", 52, 60), ("g3", 34, 64),
              ("g3", 54, 66), ("g3", 29, 72), ("g3", 53, 78), ("g3", 34, 83), ("g3", 47, 83), ("g3", 36, 36), ("g3", 36, 58), ("g3", 56, 44),
              ("g3", 54, 14), ("g3", 51, 18), ("b3", 36, 3), ("g3", 66, 34), ("g3", 56, 66), ("g3", 52, 46), ("g3", 40, 52), ("g3", 46, 36),
              ("g3", 58, 36), ("g3", 44, 82), ("v2", 61, 44), ("g3", 59, 62), ("g3", 60, 84), ("g3", 47, 54)]


def side_right():
    parts = (arms(False, False) + leg(-4, True) + ABDOMEN + POD_R + leg(0, False) + arms(True, False) + VESSEL + HEAD)
    return dict(parts=parts, details=SIDE_DETAILS, studs=SIDE_STUDS, flip=False, shoulder=(52, 40), fist=(60, 70), hipfix=False)


def side_left():
    parts = (arms(False, True) + leg(-4, True) + ABDOMEN + PODS_L + leg(0, False) + arms(True, True) + VESSEL + HEAD)
    return dict(parts=parts, details=SIDE_DETAILS, studs=SIDE_STUDS, flip=True, shoulder=(52, 40), fist=(60, 70), hipfix=False)


def back():
    keep = []
    torso_n = 0
    for r, rp, pl, fl in G.PARTS:
        if r == "torso":
            torso_n += 1
            if torso_n in (3, 4, 5, 6, 7):
                continue                                    # window rim, dark chamber, beetle, its head (front only)
        if r == "head" and (rp in ("v",) or (rp == "f" and pl[0][1] == 14) or (rp == "b" and pl[0][1] == 21) or (rp == "b" and pl[1][1] == 21)):
            continue                                        # lenses, visor, mandibles
        keep.append((r, rp, pl, fl))
    shell = [("torso", "f", [(47, 31), (48, 31), (48, 61), (47, 61)], True),                         # split seam of the dorsal shell
             ("torso", "b", seg((36, 40), (45, 36), 2), True), ("torso", "b", seg((59, 40), (50, 36), 2), True),
             ("torso", "b", seg((34, 50), (45, 46), 2), True), ("torso", "b", seg((61, 50), (50, 46), 2), True),
             ("torso", "b", seg((36, 59), (45, 55), 2), True), ("torso", "b", seg((59, 59), (50, 55), 2), True),
             ("torso", "v", [(44, 52), (47, 52), (47, 56), (44, 56)], False), ("torso", "v", [(48, 52), (51, 52), (51, 56), (48, 56)], False)]   # amber vents
    # drawn just after the vessel in the front data order: vessel parts are the torso parts; put the shell after them, before upper arms
    out = []
    placed = False
    for p in keep:
        out.append(p)
        if p[0] == "torso" and p[3] is False and p[1] == "b" and p[2][0] == (42, 29):
            out += shell; placed = True
    if not placed: out += shell
    details = [("out", 47, 62, 48, 78)]
    studs = [s for s in G.STUDS if not (41 <= s[1] <= 55 and 38 <= s[2] <= 52) and not (43 <= s[1] <= 52 and 14 <= s[2] <= 20)] + [("g3", 40, 44), ("g3", 55, 44), ("g3", 42, 56), ("g3", 53, 56), ("g3", 44, 16), ("g3", 51, 16)]
    return dict(parts=out, details=details, studs=studs, flip=True, shoulder=(66, 38), fist=(76, 70), hipfix=False)


def setup(size="96"):
    F.CONFIG["PAL"] = dict(G.CONFIG["PAL"]); F.CONFIG["RAMP"] = dict(G.CONFIG["RAMP"])
    V.VIEWS.clear()
    V.VIEWS.update({"front": G.VIEW, "left": side_left(), "back": back(), "right": side_right()})
    V.CONFIG["PREFIX"] = "gs"
    V.CONFIG["HEIGHT"] = (72, 95)
    if size == "64":
        import tianbing64_views as T64
        T64.setup()
        V.CONFIG["PREFIX"] = "gs64"
        V.CONFIG["HEIGHT"] = (58, 63)


def frame_fn(name, spec, size):
    return {}


if __name__ == "__main__":
    size = sys.argv[1] if len(sys.argv) > 1 else "96"
    setup(size)
    R.run(V.CONFIG["PREFIX"], size, {}, frame_fn)
