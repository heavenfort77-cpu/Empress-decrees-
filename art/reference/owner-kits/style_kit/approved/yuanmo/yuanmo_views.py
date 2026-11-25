"""猿魔: four idle views per growth stage at 96 (and 64 via tianbing64_views). Front = the approved yuanmo_stages front. Side template faces
right in stage-3 coordinates and is re-plotted per stage with the same K as the front: the trapezius hump rises behind the low-set head,
the brow and muzzle jut forward, the near arm is long with a bent elbow, the far arm shows behind, short bowed legs. RIGHT view shows the
right side (fist raised round the staff); LEFT view shows the left side (fist knuckled on the ground, gold cuff), drawn facing right and
mirrored as data. Back = front mirrored minus the face parts plus a spine ridge and a back plate between the humps.
Run: python3 yuanmo_views.py <stage> [96|64] -> out/ym{S}_idle_*_1x.png, out/ym{S}_lineup_3x.png (pass/fail only)
"""
import sys
import tianbing96_v5 as F
import tianbing96_views as V
import gushi96 as G
import yuanmo_stages as Y
import anim_runner as R

seg, circ_at = G.seg, G.circ_at
STAGE = {"n": 3, "size": "96"}


def K(): return Y.CONFIG["STAGES"][STAGE["n"]]["K"]
def P(parts): return [(r, rp, [(Y.BX(x, K()), Y.BY(y, K())) for x, y in pl], fl) for r, rp, pl, fl in parts]
def PD(details): return [(c, Y.BX(x0, K()), Y.BY(y0, K()), Y.BX(x1, K()), Y.BY(y1, K())) for c, x0, y0, x1, y1 in details]
def PS(studs): return [(c, Y.BX(x, K()), Y.BY(y, K())) for c, x, y in studs]


TOE_EXTRA = {"px": 0}   # 64 only: extra toe lead so the foot still points the facing way after the K*0.655 replot


def leg(dx, far):
    r = "legL" if far else "legR"
    S = lambda p: (p[0] + dx, p[1])
    return [(r, "g", seg(S((44, 64)), S((38, 78)), 12), False), (r, "g", seg(S((38, 78)), S((44, 86)), 11), False),
            (r, "g", [S((34, 85)), S((54, 85)), S((58 + TOE_EXTRA["px"], 91)), S((33, 91))], False)] + \
           ([(r, "b", [S((34, 76)), S((42, 76)), S((42, 79)), S((34, 79))], True)] if STAGE["n"] >= 2 else [])


def near_arm(left):
    """near arm: right view = raised fist on the staff; left view = long arm knuckled on the ground with the gold cuff"""
    if left:
        return [("armR", "g", seg((46, 32), (64, 52), 11), False), ("armR", "g", circ_at(64, 53, 6, 16), False),
                ("armR", "g", seg((64, 54), (62, 80), 13), False), ("armR", "b", [(55, 66), (70, 66), (70, 70), (55, 70)], False),
                *([("armR", "b", [(56, 74), (69, 74), (69, 76), (56, 76)], True)] if STAGE["n"] >= 2 else []),
                ("hand", "g", [(56, 80), (70, 80), (71, 88), (68, 91), (58, 91), (55, 88)], False), ("hand", "b", [(57, 87), (69, 87), (69, 88), (57, 88)], True)]
    return [("staff", "s", seg((82, 12), (82, 90), 5), False), ("staff", "b", [(79, 70), (85, 70), (85, 73), (79, 73)], True),
            ("armR", "g", seg((46, 32), (72, 52), 11), False), ("armR", "g", circ_at(73, 53, 6, 16), False), ("armR", "g", seg((73, 54), (80, 60), 12), False),
            *([("armR", "b", [(72, 56), (82, 58), (81, 60), (71, 58)], True)] if STAGE["n"] >= 2 else []),
            ("hand", "g", [(74, 58), (87, 58), (88, 64), (86, 67), (75, 67), (73, 64)], False), ("hand", "b", [(75, 62), (86, 62), (86, 63), (75, 63)], True),
            ("staff", "b", [(79, 88), (85, 88), (86, 91), (78, 91)], False)]


FAR_ARM = [("armL", "g", seg((34, 32), (24, 56), 10), False), ("armL", "g", circ_at(23, 57, 5, 14), False), ("armL", "g", seg((23, 58), (28, 82), 11), False),
           ("hand", "g", [(22, 81), (34, 81), (35, 88), (33, 91), (24, 91), (21, 88)], False)]
BODY = [("skirt", "g", [(34, 58), (58, 58), (60, 66), (56, 72), (36, 72), (32, 66)], False), ("skirt", "b", [(33, 63), (59, 63), (59, 64), (33, 64)], True),
        ("torso", "g", [(26, 18), (36, 12), (50, 14), (58, 24), (62, 38), (60, 50), (54, 60), (34, 62), (24, 52), (20, 34)], False),
        ("torso", "g", [(46, 44), (60, 46), (62, 54), (54, 60), (44, 56)], False),                       # pectoral plate
        ("pauL", "g", circ_at(36, 26, 11, 22), False), ("pauL", "b", circ_at(36, 26, 5, 14), False)]       # near deltoid


def head(stage):
    """side head, in front of the hump: dome, brow ledge, sensor slit, jutting muzzle. +10 x from the front stamp, so the face leads"""
    g = stage - 1
    mw, md = 6 + g, 9 + g * 2
    H = [("head", "g", [(50, 36), (56, 30), (68, 30), (74, 36), (74, 46), (66, 52), (54, 50), (50, 44)], False),
         ("head", "g", [(56, 36), (78, 36), (79, 40), (55, 40)], False),                                       # brow ledge
         ("head", "f", [(62, 40), (76, 40), (76, 44), (62, 44)], True),                                           # sensor slit
         ("head", "s", [(60, 44), (70 + mw, 44), (72 + mw, 48), (70 + mw, 44 + md), (60, 44 + md)], False),      # muzzle
         ("head", "f", [(66, 44 + md - 3), (70 + mw - 1, 44 + md - 3), (70 + mw - 1, 44 + md - 2), (66, 44 + md - 2)], True),
         ("head", "b", [(54, 33), (73, 33), (74, 36), (54, 36)], False), ("head", "b", [(50, 35), (54, 35), (54, 41), (50, 41)], False)]
    if stage == 2: H += [("head", "b", [(58, 28), (62, 28), (62, 32), (58, 32)], False)]
    if stage == 3: H += [("head", "b", [(58, 32), (64, 32), (62, 24), (60, 21), (59, 24)], False)]
    return H


def ridge(stage):
    if stage < 3: return []
    return [("torso", "b", [(26, 20), (30, 18), (26, 8), (24, 10)], False), ("torso", "b", [(34, 14), (38, 13), (36, 3), (34, 4)], False),
            ("torso", "b", [(44, 14), (48, 14), (48, 4), (46, 4)], False),
            ("torso", "b", [(44, 46), (60, 48), (61, 50), (44, 48)], True)]                                     # stage 3: dorsal ridge spikes, gold pectoral rim


def horns(stage):
    s_ = 1
    if stage == 1: return [("pauL", "b", [(32, 16), (38, 16), (37, 13), (33, 13)], False)]
    return [("pauL", "b", [(30, 17), (38, 16), (42, 6), (38, 8)], False)]


def side_parts(left):
    st = STAGE["n"]
    base = FAR_ARM + leg(-6, True) + BODY + ridge(st) + horns(st) + leg(2, False) + near_arm(left) + head(st)
    out = []
    for r, rp, pl, fl in base:
        if r == "staff" and rp == "s":
            pl = [(x, max(y, Y.CONFIG["STAGES"][st]["staff"])) if y < 30 else (x, y) for x, y in pl]
        out.append((r, rp, pl, fl))
    if not left:
        t = Y.CONFIG["STAGES"][st]["staff"]
        out.insert([i for i, p in enumerate(out) if p[0] == "staff"][1] + 1, ("staff", "b", [(80, t - 4), (84, t - 4), (85, t + 1), (79, t + 1)], False))
    return P(out)


def side_details(stage):
    g = stage - 1
    return PD([("v1", 66, 41, 73, 43), ("glow", 72, 41, 73, 41), ("out", 72 + g, 46, 72 + g, 46)])


SIDE_STUDS = [("g3", 38, 28), ("g3", 48, 22), ("g3", 30, 40), ("g3", 56, 56), ("g3", 40, 86), ("g3", 48, 84), ("g3", 36, 48), ("g3", 46, 58),
              ("g3", 58, 36), ("g3", 28, 70), ("g3", 64, 80), ("g3", 60, 64), ("g3", 52, 18), ("g3", 30, 26), ("g3", 24, 58), ("g3", 73, 53), ("b3", 52, 36)]


def side_view(left):
    st = STAGE["n"]
    studs = PS(SIDE_STUDS + ([("v2", 44, 52)] if st >= 1 else []) + ([("v2", 40, 40), ("v2", 54, 24)] if st >= 2 else []) + ([("v2", 32, 22), ("v2", 50, 62)] if st == 3 else []))
    return dict(parts=side_parts(left), details=side_details(st), studs=studs, flip=left, shoulder=(Y.BX(50, K()), Y.BY(30, K())), fist=(Y.BX(80, K()), Y.BY(62, K())), hipfix=False)


def back_view():
    fv = Y.view(STAGE["n"])
    keep = []
    for r, rp, pl, fl in fv["parts"]:
        if r == "head" and (rp in ("s", "f")): continue                                   # muzzle, sensor slit, mouth
        if r == "head" and rp == "b" and len(pl) == 4 and pl[0][0] < 44 and False: continue
        keep.append((r, rp, pl, fl))
    k = K()
    plate = P([("torso", "g", [(40, 14), (55, 14), (58, 30), (56, 50), (39, 50), (37, 30)], False),
               ("torso", "f", [(47, 14), (48, 14), (48, 56), (47, 56)], True),
               ("torso", "b", [(38, 26), (57, 26), (57, 28), (38, 28)], True), ("torso", "b", [(38, 40), (57, 40), (57, 42), (38, 42)], True)])
    out, placed = [], False
    for p in keep:
        if p[0] == "pauL" and not placed: out += plate; placed = True
        out.append(p)
    details = [d for d in fv["details"] if d[0] == "out"] + [("out", Y.BX(47, k), Y.BY(16, k), Y.BX(48, k), Y.BY(54, k))]
    studs = [s for s in fv["studs"] if not (40 <= s[1] <= 56 and Y.BY(14, k) <= s[2] <= Y.BY(62, k))] + PS([("g3", 42, 20), ("g3", 53, 20), ("g3", 42, 46), ("g3", 53, 46)])
    return dict(parts=out, details=details, studs=studs, flip=True, shoulder=fv["shoulder"], fist=fv["fist"], hipfix=False)


def setup(stage, size="96"):
    STAGE["n"] = stage; STAGE["size"] = size; TOE_EXTRA["px"] = 0 if size == "64" else 0
    F.CONFIG["PAL"] = dict(Y.CONFIG["PAL"]); F.CONFIG["RAMP"] = dict(Y.CONFIG["RAMP"])
    V.VIEWS.clear()
    V.VIEWS.update({"front": Y.view(stage), "left": side_view(True), "back": back_view(), "right": side_view(False)})
    V.CONFIG["PREFIX"] = f"ym{stage}"
    V.CONFIG["HEIGHT"] = Y.CONFIG["STAGES"][stage]["H"]
    if size == "64":
        import tianbing64_views as T64
        T64.setup()
        V.CONFIG["PREFIX"] = f"ym{stage}_64"
        lo, hi = Y.CONFIG["STAGES"][stage]["H"]
        V.CONFIG["HEIGHT"] = (round(lo * 59 / 90) - 2, round(hi * 59 / 90) + 2)


def frame_fn(name, spec, size):
    return {}


if __name__ == "__main__":
    stage = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    size = sys.argv[2] if len(sys.argv) > 2 else "96"
    setup(stage, size)
    R.run(V.CONFIG["PREFIX"], size, {}, frame_fn)
