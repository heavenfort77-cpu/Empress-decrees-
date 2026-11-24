# 反贼 rebel units (worker W5; study art/Guard-Rebels-Study.md; docs/BURNING-PALACE.md "Third side"): 太平道 rebels in yellow headbands
# and patched bootleg 甲. People on legs (the guard rolls on treads), hemp cloth weighted by automatic weights (bone heat), plates and
# weapons rigid. Types: 黄巾力士 ls (mob; one body, nine school weapons and the school patch colour), 符水道人 fs (talisman-water healer),
# 死士 ss (crouched assassin, yellow glint tell), 渠帅 qs (leader, yellow pennant). Windups = CONFIG.GUARD.moves / FANZEI.bootleg (read only).
# Materials: rbCloth (assets/tex/fodder_trim.png), rbPatch (same sheet, patch row; tinted per school by instance colour), rbGlint (死士 tell).
# Usage: BPY rebel_build.py OUTDIR [TYPES]   -> OUTDIR/<type>.glb, OUTDIR/rebel_gates.json, OUTDIR/preview/*.npz
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fodder_base as B
from fodder_base import loft, spheroid, prism, tube, path_tube, rect, ngon, blade, rot_for, clip, Q

ARGS = [a for a in sys.argv[sys.argv.index('--') + 1:]] if '--' in sys.argv else sys.argv[1:]
OUT = ARGS[0] if ARGS else '/tmp/rebels'
TYPES = ARGS[1].split(',') if len(ARGS) > 1 else ['ls', 'fs', 'ss', 'qs']

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Attack windups, s: 力士 bootleg moves 0.8 (mo and yinyang 1.0, zongheng 0.9: the game time-scales the clip), talisman 0.8, lunge 0.6, cleave 0.6.
WINDUP = {'ls': 0.8, 'fs': 0.8, 'ss': 0.6, 'qs': 0.6}
# Strike and recover after the windup, s.
STRIKE, RECOVER = 0.16, 0.5
# Unit radius from CONFIG.GUARD.types r, m.
RADIUS = {'ls': 0.45, 'fs': 0.45, 'ss': 0.45, 'qs': 0.55}
# Body height band without weapons or pennant, m (the 死士 crouches).
HEIGHT = {'ls': (1.4, 1.85), 'fs': (1.5, 1.9), 'ss': (0.9, 1.35), 'qs': (1.6, 2.1)}
# Leader scale (渠帅 is the biggest rebel).
QS_SCALE = 1.12
# School order (CONFIG.SCHOOLS) and the patch colour per school (CONFIG.COL.schools, the colour the suits wear in the game today).
SCHOOLS = ['ru', 'dao', 'fa', 'mo', 'yinyang', 'za', 'ming', 'zongheng', 'nong']
SCHOOL_COL = [0xb05a2a, 0xd5a03a, 0x6a6a6a, 0x8a2a3a, 0x3a3a3a, 0xe8e8f0, 0xc060a0, 0x40c0c0, 0x9a6ad5]
CL, PT, GL = 'rbCloth', 'rbPatch', 'rbGlint'


# shared rebel body -----------------------------------------------------------------------------------------------------
def body(d, hunch=0.1, chest=0.24, belly=0.22, robe=False, patch=True, hood=False, pelvis=0.9, tl=0.5, kf=0.02, knot=True, tunic='hemp', mantle=False, limb=1.0):
    """a man in hemp: tunic (cloth), trousers (cloth), sleeves (cloth); skin head and hands; yellow headband with two tails; straw sandals;
    a rope belt; bootleg plates (one shoulder, a chest plate) where patch=True (patch material = school colour)."""
    pz = pelvis; sz = pz + tl  # shoulder height (tl = torso length; the 死士 crouches with a short, bent torso)
    hf = hunch  # how far the shoulders and head sit forward
    # tunic from the hips to the shoulders (or a robe to the ankles)
    if robe:
        loft('robe', [(0.06, 0.0, 0.32, 0.28, 0), (0.4, 0.0, 0.27, 0.22, 0), (pz, 0.01, belly, belly * 0.8, 0), (pz + 0.3, hf * 0.6, chest, chest * 0.7, 0),
                      (sz - 0.04, hf, chest * 0.92, chest * 0.62, 0), (sz + 0.04, hf, 0.1, 0.08, 0)], CL, 'spine', 'hemp', n_exp=2.2, M=16, cloth=True)
    else:
        # round 2 (concepts 5203 / 5204, reference only): the tunic runs to the knee and flares, belted at the waist
        loft('tunic', [(pz * 0.52, 0.02, belly + 0.08, belly * 0.95, 0), (pz - 0.12, 0.01, belly + 0.04, belly * 0.88, 0), (pz, 0.01, belly, belly * 0.85, 0),
                       (pz + 0.25, hf * 0.5 + 0.02, chest, chest * 0.78, 0), (sz - 0.04, hf, chest * 0.95, chest * 0.66, 0), (sz + 0.04, hf, 0.1, 0.08, 0)],
             CL, 'spine', tunic, n_exp=2.2, M=16, cloth=True)
        for side, s in (('R', 1), ('L', -1)):  # trousers, wrapped at the shin
            tube(f'leg_{side}', (s * 0.11, 0, pz - 0.05), (s * 0.12, kf, pz * 0.5), 0.11 * limb, 0.085 * limb, CL, f'thigh_{side}', 'hemp', sides=8, cloth=True)
            tube(f'shin_{side}', (s * 0.12, kf, pz * 0.5), (s * 0.12, 0.0, 0.1), 0.085 * limb, 0.06 * limb, CL, f'shin_{side}', 'rope', sides=8, cloth=True)
    for side, s in (('R', 1), ('L', -1)):
        foot = (s * 0.12, 0.06, 0.04)
        loft(f'foot_{side}', [(0.0, 0.06, 0.055, 0.12, s * 0.12), (0.07, 0.04, 0.05, 0.09, s * 0.12)], CL, f'foot_{side}', 'plates', n_exp=2.4, M=10)
    # arms: cloth sleeves to the elbow, skin forearms and fists
    for side, s in (('R', 1), ('L', -1)):
        sh = (s * (chest + 0.02), hf, sz - 0.04); el = (s * (chest + 0.08), hf + 0.04, sz - 0.32)
        tube(f'sleeve_{side}', sh, el, 0.095 * limb, 0.09 * limb, CL, f'uarm_{side}', tunic, sides=8, cloth=True)
        tube(f'forearm_{side}', el, ARM[side], 0.068 * limb, 0.055 * limb, CL, f'farm_{side}', 'skin', sides=6)
        spheroid(f'hand_{side}', ARM[side], (0.065, 0.07, 0.065), CL, f'farm_{side}', 'skin', segs=(8, 6))
    loft('belt', [(pz - 0.02, 0.01, belly + 0.035, belly * 0.85 + 0.035, 0), (pz + 0.04, 0.01, belly + 0.03, belly * 0.85 + 0.03, 0)], CL, 'pelvis', 'rope', n_exp=2.2, M=14, cap=False)
    # head: skin, forward of the shoulders (hunched), dark topknot; the yellow headband ring and two tails flying behind
    hz = sz + 0.2
    spheroid('head', (0, hf + 0.03, hz), (0.095, 0.105, 0.115), CL, 'head', 'skin', segs=(10, 8))
    if hood:
        loft('hood', [(hz - 0.14, hf - 0.02, 0.15, 0.15, 0), (hz, hf - 0.01, 0.13, 0.14, 0), (hz + 0.1, hf, 0.1, 0.11, 0), (hz + 0.16, hf - 0.02, 0.03, 0.03, 0)],
             CL, 'head', 'dark', n_exp=2.0, M=12)
        prism('veil', [(-0.1, -0.05), (0.1, -0.05), (0.08, 0.04), (-0.08, 0.04)], (0, hf + 0.1, hz - 0.04), (0, hf + 0.14, hz - 0.05), CL, 'head', 'dark')
    elif knot:
        spheroid('knot', (0, hf - 0.02, hz + 0.13), (0.05, 0.05, 0.05), CL, 'head', 'dark', segs=(8, 5))
    loft('band', [(hz + 0.02, hf + 0.03, 0.105 + (0.03 if hood else 0), 0.115 + (0.03 if hood else 0), 0), (hz + 0.07, hf + 0.03, 0.1 + (0.03 if hood else 0), 0.11 + (0.03 if hood else 0), 0)],
         CL, 'head', 'yellow', n_exp=2.0, M=12, cap=False)
    for s in (-1, 1):  # two tails, 0.3 m, out and down behind the head: the 黄巾 mark from behind and above
        prism(f'btail_{s}', [(-0.04, -0.008), (0.04, -0.008), (0.04, 0.008), (-0.04, 0.008)], (s * 0.03, hf - 0.09, hz + 0.04), (s * 0.08, hf - 0.3, hz - 0.22),
              CL, 'tail', 'yellow', scale_b=0.7)
    if mantle:  # a ragged hemp mantle over the shoulders (cloth): its torn points break the outline, the opposite of the guard's smooth bell
        loft('mantle', [(sz + 0.06, hf, 0.12, 0.1, 0), (sz - 0.02, hf, chest + 0.06, chest * 0.78, 0), (sz - 0.3, hf - 0.03, chest + 0.1, chest * 0.84, 0)],
             CL, 'spine', 'rope', n_exp=2.0, M=14, cloth=True)
        n = 9 if d else 6
        for k in range(n):
            a = math.pi * 0.15 + k * math.pi * 1.7 / (n - 1)  # around the back and sides, open at the chest
            x, f = math.sin(a) * (chest + 0.13), -math.cos(a) * (chest * 0.85) + hf - 0.02
            x, f = math.sin(a) * (chest + 0.1), -math.cos(a) * (chest * 0.84) + hf - 0.03
            L = 0.18 + 0.08 * ((k * 7) % 3)
            prism(f'rag_{k}', blade(0.12, 0.03), (x, f, sz - 0.28), (x * 1.08, f * 1.08, sz - 0.28 - L), CL, 'spine', 'rope', scale_b=0.15, cloth=True)
    if patch:  # bootleg plates: a chest plate and the left shoulder plate in the school colour, a mismatched plate on the right shoulder
        prism('cplate', [(-0.14, -0.13), (0.14, -0.13), (0.16, 0.1), (0.06, 0.15), (-0.06, 0.15), (-0.16, 0.1)], (0, hf * 0.7 + chest * 0.74, pz + 0.3),
              (0, hf * 0.7 + chest * 0.74 + 0.04, pz + 0.31), PT, 'spine', 'patch')
        loft('pauld_L', [(sz - 0.14, hf, 0.11, 0.12, -(chest + 0.03)), (sz - 0.04, hf, 0.13, 0.13, -(chest + 0.02)), (sz + 0.04, hf, 0.08, 0.09, -chest)], PT, 'uarm_L', 'patch', n_exp=2.0, M=10)
        loft('pauld_R', [(sz - 0.1, hf, 0.09, 0.1, chest + 0.02), (sz - 0.03, hf, 0.11, 0.11, chest + 0.02), (sz + 0.03, hf, 0.06, 0.07, chest)], CL, 'uarm_R', 'plates', n_exp=2.6, M=10)
        if d:
            for k in range(3):  # rope ties across the chest plate
                prism(f'tie_{k}', rect(0.3, 0.02), (0, hf * 0.7 + chest * 0.74 + 0.04, pz + 0.22 + k * 0.08), (0, hf * 0.7 + chest * 0.74 + 0.055, pz + 0.22 + k * 0.08), CL, 'spine', 'rope')

ARM = {'R': (0.3, 0.3, 0.95), 'L': (-0.3, 0.26, 1.0)}  # hands (set per type before the body is built)

def rebel_bones(hunch=0.1, chest=0.24, pelvis=0.9, wtip=None, extra=(), tl=0.5, kf=0.02):
    pz = pelvis; sz = pz + tl; hf = hunch; hz = sz + 0.2
    b = [('root', (0, 0, 0), (0, 0, 0.1), None), ('pelvis', (0, 0, pz - 0.1), (0, 0, pz + 0.05), 'root'), ('spine', (0, 0, pz + 0.05), (0, hf, sz), 'pelvis'),
         ('head', (0, hf, sz + 0.04), (0, hf + 0.03, hz + 0.15), 'spine'), ('tail', (0, hf - 0.09, hz + 0.04), (0, hf - 0.3, hz - 0.22), 'head')]
    for side, s in (('R', 1), ('L', -1)):
        b += [(f'thigh_{side}', (s * 0.11, 0, pz - 0.05), (s * 0.12, kf, pz * 0.5), 'pelvis'), (f'shin_{side}', (s * 0.12, kf, pz * 0.5), (s * 0.12, 0.0, 0.1), f'thigh_{side}'),
              (f'foot_{side}', (s * 0.12, 0.0, 0.1), (s * 0.12, 0.16, 0.03), f'shin_{side}'),
              (f'uarm_{side}', (s * (chest + 0.02), hf, sz - 0.04), (s * (chest + 0.08), hf + 0.04, sz - 0.32), 'spine'),
              (f'farm_{side}', (s * (chest + 0.08), hf + 0.04, sz - 0.32), ARM[side], f'uarm_{side}')]
    if wtip: b.append(('weapon', ARM['R'], wtip, 'farm_R'))
    return b + list(extra)


# shared rebel clips ----------------------------------------------------------------------------------------------------
def walk_idle(arm, crouch=False, idle_extra=None, idle_scl=None):
    R = lambda b, w, a, p=None: rot_for(arm, b, w, a, p)
    idle = {'spine': [(0, (0, 0, 0)), (1.0, R('spine', 'fwd', 3)), (2.0, (0, 0, 0))], 'head': [(0, (0, 0, 0)), (0.8, R('head', 'right', 12, (0, 0.3, 1.6))), (1.6, R('head', 'left', 8, (0, 0.3, 1.6))), (2.0, (0, 0, 0))],
            'tail': [(0, (0, 0, 0)), (1.0, R('tail', 'up', 8)), (2.0, (0, 0, 0))]}
    sw = 22 if not crouch else 14
    move = {'thigh_R': [(0, R('thigh_R', 'fwd', sw)), (0.5, R('thigh_R', 'back', sw)), (1.0, R('thigh_R', 'fwd', sw))],
            'thigh_L': [(0, R('thigh_L', 'back', sw)), (0.5, R('thigh_L', 'fwd', sw)), (1.0, R('thigh_L', 'back', sw))],
            'shin_R': [(0, (0, 0, 0)), (0.25, R('shin_R', 'back', 30)), (0.5, (0, 0, 0)), (1.0, (0, 0, 0))],
            'shin_L': [(0, (0, 0, 0)), (0.5, (0, 0, 0)), (0.75, R('shin_L', 'back', 30)), (1.0, (0, 0, 0))],
            'uarm_L': [(0, R('uarm_L', 'fwd', 16)), (0.5, R('uarm_L', 'back', 16)), (1.0, R('uarm_L', 'fwd', 16))],
            'spine': [(0, R('spine', 'fwd', 6)), (0.25, R('spine', 'fwd', 8)), (0.5, R('spine', 'fwd', 6)), (0.75, R('spine', 'fwd', 8)), (1.0, R('spine', 'fwd', 6))],
            'tail': [(0, R('tail', 'up', 14)), (0.5, R('tail', 'up', 22)), (1.0, R('tail', 'up', 14))]}
    mloc = {'pelvis': [(0, (0, 0, 0)), (0.25, (0, 0, 0.03)), (0.5, (0, 0, 0)), (0.75, (0, 0, 0.03)), (1.0, (0, 0, 0))]}
    if idle_extra: idle.update(idle_extra)
    return clip(arm, 'idle', idle, scl=idle_scl), clip(arm, 'move', move, loc=mloc, scl=idle_scl)


# 黄巾力士 (the mob): hunched and bulky; nine school weapons (shape cue) plus the school patch colour -----------------------------------------
LS_HUNCH = 0.12
def ls_body(d):
    ARM.update(R=(0.32, 0.3, 0.98), L=(-0.3, 0.24, 1.02)); body(d, hunch=LS_HUNCH, chest=0.25, belly=0.24, mantle=True, limb=1.15)

def wpn_ru(d):  # 儒: a straight sword in hand and a bow slung across the back
    g = ARM['R']; tube('w_blade', (g[0], g[1] + 0.03, g[2] + 0.06), (g[0] + 0.04, g[1] + 0.1, g[2] + 0.8), 0.035, 0.01, CL, 'weapon', 'metal', sides=4)
    prism('w_guard', rect(0.16, 0.035), (g[0], g[1], g[2] + 0.04), (g[0], g[1] + 0.04, g[2] + 0.045), CL, 'weapon', 'metal')
    arc = [(math.sin(a) * 0.36, -0.2 - math.cos(a) * 0.08, 1.12 + math.sin(a) * 0.32 + 0.12) for a in [math.radians(x) for x in range(-80, 81, 20 if d else 40)]]
    path_tube('w_bow', arc, 0.022, CL, 'spine', 'plates', sides=5)

def wpn_dao(d):  # 道: a big palm-leaf fan (the water-turn push) and a gourd at the hip
    g = ARM['R']; tube('w_handle', (g[0], g[1], g[2] - 0.08), (g[0], g[1] + 0.02, g[2] + 0.3), 0.022, 0.02, CL, 'weapon', 'plates', sides=5)
    prism('w_fan', ngon(0.24, 10 if d else 6), (g[0], g[1] - 0.005, g[2] + 0.52), (g[0], g[1] + 0.025, g[2] + 0.52), CL, 'weapon', 'rope', up=(0, 0, 1))
    spheroid('w_gourd', (-0.22, 0.12, 0.8), (0.07, 0.07, 0.09), CL, 'pelvis', 'yellow', segs=(8, 6))
    spheroid('w_gourd2', (-0.22, 0.12, 0.92), (0.045, 0.045, 0.05), CL, 'pelvis', 'yellow', segs=(8, 5))

def wpn_fa(d):  # 法: the executioner's axe (钺): a short haft and a broad crescent blade
    g = ARM['R']; tube('w_haft', (g[0], g[1], g[2] - 0.25), (g[0], g[1] + 0.02, g[2] + 0.62), 0.025, 0.022, CL, 'weapon', 'plates', sides=5)
    prism('w_axe', [(-0.02, -0.16), (0.12, -0.2), (0.2, -0.06), (0.22, 0.06), (0.14, 0.2), (-0.02, 0.16)], (g[0] + 0.01, g[1] - 0.02, g[2] + 0.5), (g[0] + 0.01, g[1] + 0.06, g[2] + 0.5),
          CL, 'weapon', 'metal', up=(0, 0, 1))

def wpn_mo(d):  # 墨: a crude crossbow held level (a copy of the guard's), the prod tied with rope
    g = ARM['R']; prism('w_stock', rect(0.05, 0.06), (g[0] - 0.1, g[1] - 0.15, g[2]), (g[0] - 0.12, g[1] + 0.4, g[2] + 0.02), CL, 'weapon', 'plates')
    arc = [(g[0] - 0.12 + math.sin(a) * 0.4, g[1] + 0.32 - (1 - math.cos(a)) * 0.25, g[2] + 0.02) for a in [math.radians(x) for x in range(-70, 71, 35)]]
    path_tube('w_prod', arc, 0.028, CL, 'weapon', 'rope', sides=5)

def wpn_yinyang(d):  # 阴阳: a staff topped by a round two-tone disc
    g = ARM['R']; tube('w_staff', (g[0], g[1], g[2] - 0.75), (g[0], g[1] + 0.03, g[2] + 0.72), 0.025, 0.022, CL, 'weapon', 'plates', sides=5)
    c = (g[0], g[1] + 0.03, g[2] + 0.95)
    prism('w_yin', [(math.cos(a) * 0.22, math.sin(a) * 0.22) for a in [math.pi / 2 + k * math.pi / (6 if d else 3) for k in range((6 if d else 3) + 1)]], (c[0], c[1] - 0.015, c[2]), (c[0], c[1] + 0.015, c[2]), CL, 'weapon', 'dark', up=(0, 0, 1))
    prism('w_yang', [(math.cos(a) * 0.22, math.sin(a) * 0.22) for a in [-math.pi / 2 + k * math.pi / (6 if d else 3) for k in range((6 if d else 3) + 1)]], (c[0], c[1] - 0.015, c[2]), (c[0], c[1] + 0.015, c[2]), CL, 'weapon', 'skin', up=(0, 0, 1))

def wpn_za(d):  # 杂: a seal hammer: a pole and a big square seal block with a knob
    g = ARM['R']; tube('w_pole', (g[0], g[1], g[2] - 0.2), (g[0], g[1] + 0.02, g[2] + 0.7), 0.024, 0.022, CL, 'weapon', 'plates', sides=5)
    loft('w_seal', [(g[2] + 0.7, g[1] + 0.02, 0.13, 0.13, g[0]), (g[2] + 0.9, g[1] + 0.02, 0.13, 0.13, g[0])], CL, 'weapon', 'metal', n_exp=4.0, M=12)
    spheroid('w_knob', (g[0], g[1] + 0.02, g[2] + 0.96), (0.06, 0.06, 0.06), CL, 'weapon', 'metal', segs=(6, 4))

def wpn_ming(d):  # 名: a bronze wheel held up to throw (rim and four spokes)
    g = ARM['R']; c = (g[0] + 0.02, g[1] + 0.02, g[2] + 0.34); r = 0.28; n = 12 if d else 8
    rim = [(c[0] + math.cos(a) * r, c[1], c[2] + math.sin(a) * r) for a in [k * math.tau / n for k in range(n + 1)]]
    path_tube('w_rim', rim, 0.03, CL, 'weapon', 'metal', sides=5)
    for k in range(2):
        a = k * math.pi / 2 + math.pi / 4
        tube(f'w_spoke{k}', (c[0] + math.cos(a) * r, c[1], c[2] + math.sin(a) * r), (c[0] - math.cos(a) * r, c[1], c[2] - math.sin(a) * r), 0.018, 0.018, CL, 'weapon', 'metal', sides=4)

def wpn_zongheng(d):  # 纵横: the envoy's tally staff (节): a tall staff with three stacked tufts
    g = ARM['R']; tube('w_staff', (g[0], g[1], g[2] - 0.8), (g[0], g[1] + 0.03, g[2] + 0.95), 0.024, 0.02, CL, 'weapon', 'plates', sides=5)
    for k in range(3):
        spheroid(f'w_tuft{k}', (g[0], g[1] + 0.03, g[2] + 0.55 + k * 0.17), (0.09 - k * 0.012, 0.09 - k * 0.012, 0.075), CL, 'weapon', 'rope', segs=(8, 5))

def wpn_nong(d):  # 农: a plough-hoe: a long handle and a broad blade at right angles
    g = ARM['R']; top = (g[0], g[1] + 0.06, g[2] + 0.85)
    tube('w_handle', (g[0], g[1] - 0.02, g[2] - 0.4), top, 0.025, 0.022, CL, 'weapon', 'plates', sides=5)
    prism('w_hoe', [(-0.11, 0), (0.11, 0), (0.13, 0.02), (-0.13, 0.02)], (top[0], top[1] - 0.02, top[2] - 0.02), (top[0], top[1] + 0.26, top[2] - 0.16), CL, 'weapon', 'metal', scale_b=1.2)

WEAPONS = {'ru': wpn_ru, 'dao': wpn_dao, 'fa': wpn_fa, 'mo': wpn_mo, 'yinyang': wpn_yinyang, 'za': wpn_za, 'ming': wpn_ming, 'zongheng': wpn_zongheng, 'nong': wpn_nong}
LS_TIP = (0.36, 0.34, 1.75)  # the weapon bone runs from the hand up the weapon (about the length of the longest school weapon head)

def ls_weapon(school):
    def f(d):
        ls_body_arm_only(); WEAPONS[school](d)
    return f

def ls_body_arm_only(): ARM.update(R=(0.32, 0.3, 0.98), L=(-0.3, 0.24, 1.02))

def ls_clips(arm):
    R = lambda b, w, a, p=None: rot_for(arm, b, w, a, p); w = WINDUP['ls']; s = w + STRIKE
    i, m = walk_idle(arm)
    # the bootleg windup: weapon raised high over the head and the body leaning back (one readable pose for every school copy)
    keys = {'uarm_R': [(0, (0, 0, 0)), (w, R('uarm_R', 'up', 120)), (s, R('uarm_R', 'fwd', 40)), (s + RECOVER, (0, 0, 0))],
            'farm_R': [(0, (0, 0, 0)), (w, R('farm_R', 'up', 25)), (s, (0, 0, 0)), (s + RECOVER, (0, 0, 0))],
            'spine': [(0, (0, 0, 0)), (w, R('spine', 'back', 14)), (s, R('spine', 'fwd', 18)), (s + RECOVER, (0, 0, 0))],
            'thigh_L': [(0, (0, 0, 0)), (w, R('thigh_L', 'fwd', 20)), (s, R('thigh_L', 'fwd', 26)), (s + RECOVER, (0, 0, 0))],
            'tail': [(0, (0, 0, 0)), (w, R('tail', 'up', 10)), (s, R('tail', 'up', 25)), (s + RECOVER, (0, 0, 0))]}
    return {'idle': i, 'move': m, 'attack': clip(arm, 'attack', keys)}, None, w, 'weapon'


# 符水道人 talisman-water healer: long robe (bell), daoist crown, a staff with a gourd and yellow talisman strips; heal mark from behind ----
FS_TIP = (0.3, 0.34, 2.0)
def fs_build(d):
    ARM.update(R=(0.3, 0.26, 1.02), L=(-0.26, 0.22, 1.08)); body(d, hunch=0.04, chest=0.21, belly=0.21, robe=True, patch=False, knot=False)
    g = ARM['R']
    tube('staff', (g[0], g[1], 0.05), FS_TIP, 0.025, 0.02, CL, 'weapon', 'plates', sides=6)
    spheroid('gourd', (FS_TIP[0] + 0.06, FS_TIP[1], FS_TIP[2] - 0.22), (0.075, 0.075, 0.09), CL, 'weapon', 'yellow', segs=(8, 6))
    spheroid('gourd2', (FS_TIP[0] + 0.06, FS_TIP[1], FS_TIP[2] - 0.1), (0.05, 0.05, 0.05), CL, 'weapon', 'yellow', segs=(8, 5))
    for k in range(4 if d else 2):  # talisman strips hanging from a cross-tie near the top (paper: yellow, no readable script)
        x = FS_TIP[0] - 0.14 + k * (0.09 if d else 0.2)
        prism(f'talis_{k}', rect(0.05, 0.008), (x, FS_TIP[1] + 0.02, FS_TIP[2] - 0.05), (x, FS_TIP[1] + 0.02, FS_TIP[2] - 0.4), CL, 'weapon', 'yellow', up=(0, -1, 0))
    prism('tie', rect(0.32, 0.02), (FS_TIP[0] - 0.16, FS_TIP[1] + 0.02, FS_TIP[2] - 0.05), (FS_TIP[0] + 0.16, FS_TIP[1] + 0.02, FS_TIP[2] - 0.05), CL, 'weapon', 'rope', up=(0, 0, 1))
    # a bowl of talisman water in the left hand and the daoist crown on the knot
    loft('bowl', [(ARM['L'][2] + 0.02, ARM['L'][1], 0.06, 0.06, ARM['L'][0]), (ARM['L'][2] + 0.08, ARM['L'][1], 0.1, 0.1, ARM['L'][0])], CL, 'farm_L', 'plates', n_exp=2.0, M=10)
    prism('crown', [(-0.06, -0.03), (0.06, -0.03), (0.035, 0.03), (-0.035, 0.03)], (0, 0.0, 1.72), (0, 0.0, 1.84), CL, 'head', 'dark', scale_b=0.7)
    # a yellow sash over the robe
    prism('sash', rect(0.06, 0.02), (0.18, 0.2, 1.38), (-0.2, 0.2, 0.88), CL, 'spine', 'yellow')

def fs_clips(arm):
    R = lambda b, w, a, p=None: rot_for(arm, b, w, a, p); w = WINDUP['fs']; s = w + STRIKE
    i, m = walk_idle(arm)
    keys = {'uarm_R': [(0, (0, 0, 0)), (w, R('uarm_R', 'up', 70)), (s, R('uarm_R', 'up', 40)), (s + RECOVER, (0, 0, 0))],
            'uarm_L': [(0, (0, 0, 0)), (w, R('uarm_L', 'up', 60)), (s, R('uarm_L', 'fwd', 50)), (s + RECOVER, (0, 0, 0))],
            'spine': [(0, (0, 0, 0)), (w, R('spine', 'back', 10)), (s, R('spine', 'fwd', 8)), (s + RECOVER, (0, 0, 0))],
            'weapon': [(0, (0, 0, 0)), (w, R('weapon', 'back', 15)), (s, R('weapon', 'fwd', 25)), (s + RECOVER, (0, 0, 0))]}
    return {'idle': i, 'move': m, 'attack': clip(arm, 'attack', keys)}, None, w, 'weapon'


# 死士 assassin: low crouch, hood and veil in dark cloth, two short blades held back; the yellow glint on the blades is the tell -------------
SS_PZ, SS_HUNCH, SS_TL, SS_KF = 0.6, 0.28, 0.38, 0.24
SS_TIP = (0.36, -0.2, 0.62)
def ss_build(d):
    ARM.update(R=(0.34, 0.08, 0.72), L=(-0.34, 0.1, 0.74)); body(d, hunch=SS_HUNCH, chest=0.2, belly=0.18, patch=False, hood=True, pelvis=SS_PZ, tl=SS_TL, kf=SS_KF, tunic='dark')
    for side, s, tip in (('R', 1, SS_TIP), ('L', -1, (-0.36, -0.18, 0.66))):
        g = ARM[side]; bone = 'weapon' if side == 'R' else 'farm_L'
        prism(f'knife_{side}', blade(0.05, 0.012), g, tip, CL, bone, 'metal', scale_b=0.1)
        # glint cards: a small four-point star on each blade, scaled 0 at rest and 1 through the windup (rbGlint, bright yellow)
        c = tuple((a + b) / 2 for a, b in zip(g, tip))
        for k, up in enumerate([(0, 0, 1), (1, 0, 0)] if d else []):  # a four-point star 0.28 m across (25 px at the fight framing); LOD0 only (static LODs cannot hide it)
            prism(f'glint_{side}{k}', blade(0.28, 0.06), (c[0], c[1] - 0.01, c[2]), (c[0], c[1] + 0.01, c[2]), GL, 'glint_' + side, 'glint', up=up)

def ss_bones():
    gR = ((0.34 + SS_TIP[0]) / 2, (0.08 + SS_TIP[1]) / 2, (0.72 + SS_TIP[2]) / 2); gL = ((-0.34 - 0.36) / 2, (0.1 - 0.18) / 2, (0.74 + 0.66) / 2)
    return rebel_bones(SS_HUNCH, 0.2, SS_PZ, wtip=SS_TIP, tl=SS_TL, kf=SS_KF, extra=[('glint_R', gR, (gR[0], gR[1], gR[2] + 0.1), 'weapon'), ('glint_L', gL, (gL[0], gL[1], gL[2] + 0.1), 'farm_L')])

def ss_clips(arm):
    R = lambda b, w, a, p=None: rot_for(arm, b, w, a, p); w = WINDUP['ss']; s = w + 0.12
    hide = {'glint_R': [(0, 0.0)], 'glint_L': [(0, 0.0)]}  # glints stay hidden in idle and move
    i, m = walk_idle(arm, crouch=True, idle_scl=hide)
    keys = {'spine': [(0, (0, 0, 0)), (w, R('spine', 'down', 12)), (s, R('spine', 'fwd', 20)), (s + RECOVER, (0, 0, 0))],
            'uarm_R': [(0, (0, 0, 0)), (w, R('uarm_R', 'back', 45)), (s, R('uarm_R', 'fwd', 70)), (s + RECOVER, (0, 0, 0))],
            'uarm_L': [(0, (0, 0, 0)), (w, R('uarm_L', 'back', 45)), (s, R('uarm_L', 'fwd', 70)), (s + RECOVER, (0, 0, 0))],
            'thigh_R': [(0, (0, 0, 0)), (w, R('thigh_R', 'fwd', 25)), (s, R('thigh_R', 'back', 20)), (s + RECOVER, (0, 0, 0))],
            'thigh_L': [(0, (0, 0, 0)), (w, R('thigh_L', 'fwd', 25)), (s, R('thigh_L', 'fwd', 40)), (s + RECOVER, (0, 0, 0))]}
    loc = {'pelvis': [(0, (0, 0, 0)), (w, (0, -0.05, -0.08)), (s, (0, 0.9, 0.05)), (s + RECOVER, (0, 0, 0))]}
    scl = {'glint_R': [(0, 0.0), (0.12, 0.0), (0.2, 1.0), (w, 1.2), (s, 0.0), (s + RECOVER, 0.0)], 'glint_L': [(0, 0.0), (0.12, 0.0), (0.2, 1.0), (w, 1.2), (s, 0.0), (s + RECOVER, 0.0)]}
    return {'idle': i, 'move': m, 'attack': clip(arm, 'attack', keys, loc=loc, scl=scl)}, None, w, 'weapon'


# 渠帅 leader: biggest rebel, yellow cape and sash, a tall yellow pennant on a back pole, a ring-pommel 环首刀; cleave ------------------------
QS_TIP = (0.36, 0.42, 1.9)
def qs_build(d):
    ARM.update(R=(0.32, 0.3, 1.0), L=(-0.3, 0.24, 1.02)); body(d, hunch=0.06, chest=0.27, belly=0.25, tunic='dark', patch=False, limb=1.15)  # 5212: yellow over dark
    for s in (-1, 1):  # his own plates (not a school copy): big mismatched shoulder plates
        loft(f'qpauld_{s}', [(1.32, 0.06, 0.12, 0.13, s * 0.3), (1.42, 0.06, 0.14, 0.14, s * 0.29), (1.5, 0.06, 0.08, 0.09, s * 0.26)], CL, 'uarm_R' if s > 0 else 'uarm_L', 'plates', n_exp=2.4, M=10)
    g = ARM['R']
    tube('blade', (g[0], g[1] + 0.02, g[2] + 0.06), QS_TIP, 0.04, 0.015, CL, 'weapon', 'metal', sides=4)
    loft('ring', [(g[2] - 0.12, g[1], 0.05, 0.05, g[0]), (g[2] - 0.08, g[1], 0.05, 0.05, g[0])], CL, 'weapon', 'metal', n_exp=2.0, M=8)
    # cape from the shoulders down the back (cloth, automatic weights) and a yellow sash
    loft('cape', [(1.44, 0.02, 0.2, 0.15, 0), (1.36, 0.0, 0.33, 0.24, 0), (1.0, -0.02, 0.33, 0.25, 0), (0.55, -0.04, 0.35, 0.27, 0)], CL, 'spine', 'yellow', n_exp=2.0, M=16, cloth=True)
    for s in (-1, 1):  # the robe's open front edges (dark tunic shows between them)
        prism(f'lapel_{s}', rect(0.1, 0.02), (s * 0.12, 0.3, 1.36), (s * 0.15, 0.3, 0.6), CL, 'spine', 'yellow', up=(0, -1, 0), cloth=True)
    prism('sash', rect(0.07, 0.02), (-0.24, 0.27, 1.38), (0.22, 0.27, 0.88), CL, 'spine', 'yellow')
    # pennant pole on the back, a tall yellow swallow-tail pennant (no script: one dark sigil band)
    tube('ppole', (0.12, -0.22, 0.85), (0.12, -0.22, 2.5), 0.028, 0.024, CL, 'banner', 'plates', sides=6)
    prism('pennant', [(0, 0.02), (0.5, 0.0), (0.38, -0.16), (0.5, -0.32), (0, -0.34)], (0.12, -0.23, 2.46), (0.12, -0.21, 2.46), CL, 'banner', 'yellow', up=(0, 0, 1))
    prism('pfinial', blade(0.07, 0.035), (0.12, -0.22, 2.5), (0.12, -0.22, 2.64), CL, 'banner', 'metal', scale_b=0.1)

def qs_clips(arm):
    R = lambda b, w, a, p=None: rot_for(arm, b, w, a, p); w = WINDUP['qs']; s = w + STRIKE
    i, m = walk_idle(arm, idle_extra={'banner': [(0, (0, 0, 0)), (1.0, R('banner', 'left', 4)), (2.0, (0, 0, 0))]})
    keys = {'uarm_R': [(0, (0, 0, 0)), (w, R('uarm_R', 'up', 110)), (s, R('uarm_R', 'left', 60)), (s + RECOVER, (0, 0, 0))],
            'spine': [(0, (0, 0, 0)), (w, R('spine', 'back', 22, (0.3, 0, 1.4))), (s, R('spine', 'fwd', 28, (0.3, 0, 1.4))), (s + RECOVER, (0, 0, 0))],
            'weapon': [(0, (0, 0, 0)), (w, R('weapon', 'back', 40)), (s, R('weapon', 'left', 40)), (s + RECOVER, (0, 0, 0))],
            'thigh_L': [(0, (0, 0, 0)), (w, R('thigh_L', 'fwd', 18)), (s, R('thigh_L', 'fwd', 24)), (s + RECOVER, (0, 0, 0))]}
    return {'idle': i, 'move': m, 'attack': clip(arm, 'attack', keys)}, None, w, 'weapon'


UNITS = {
    'ls': (ls_body, lambda: rebel_bones(LS_HUNCH, 0.25, wtip=LS_TIP), ls_clips, 1.0, True),
    'fs': (fs_build, lambda: rebel_bones(0.04, 0.21, wtip=FS_TIP), fs_clips, 1.0, False),
    'ss': (ss_build, ss_bones, ss_clips, 1.0, False),
    'qs': (qs_build, lambda: rebel_bones(0.06, 0.27, wtip=QS_TIP, extra=[('banner', (0.12, -0.22, 0.85), (0.12, -0.22, 2.5), 'spine')]), qs_clips, QS_SCALE, False),
}

def extra(key):
    def g(G, lod0, arm, info):
        x0, x1, y0, y1, z0, z1 = B.bounds(lod0, ('weapon', 'banner', 'glint_R', 'glint_L', 'tail'))
        hw = max(-x0, x1); r = RADIUS[key]
        G(0.7 * r <= hw <= 1.4 * r, f'body half-width {hw:.2f} m (0.7-1.4 x radius {r})')
        lo, hi = HEIGHT[key]; k = QS_SCALE if key == 'qs' else 1
        G(lo * k <= z1 <= hi * k, f'body height {z1:.2f} m (band {lo * k:.2f}-{hi * k:.2f})')
        X0, X1, Y0, Y1, Z0, Z1 = B.bounds(lod0)
        info.update(top=Z1, body_top=z1, half_width=hw)
        if key == 'ss':  # the glint is hidden at rest and in move, shown through the windup
            sc = {}
            import bpy
            for t in arm.animation_data.nla_tracks: t.mute = True
            for nm in ('idle', 'move', 'attack'):  # each clip's action evaluated alone (as tip_motion does)
                arm.animation_data.action = bpy.data.actions[nm]; vals = []
                for f in (1, 1 + round(0.3 * B.FPS), 1 + round(WINDUP['ss'] * B.FPS)):
                    bpy_scene().frame_set(f); vals.append(arm.pose.bones['glint_R'].scale[0])
                sc[nm] = vals
            arm.animation_data.action = None
            for t in arm.animation_data.nla_tracks: t.mute = False
            bpy_scene().frame_set(1)
            ok = max(sc['idle']) < 0.01 and max(sc['move']) < 0.01 and sc['attack'][0] < 0.01 and min(sc['attack'][1:]) >= 0.99
            G(ok, f'glint hidden in idle/move, shown from 0.2 s to the windup ({sc["attack"][1]:.2f}, {sc["attack"][2]:.2f})')
    return g

def bpy_scene():
    import bpy; return bpy.context.scene

if __name__ == '__main__':
    res = {}
    for k in TYPES:
        build, bones, clips_fn, sc, has_w = UNITS[k]
        Q['scale'] = sc
        res[k] = B.build_unit(k, build, bones(), clips_fn, os.path.join(OUT, f'{k}.glb'), extra(k), weapons={s: ls_weapon(s) for s in SCHOOLS} if has_w else None,
                              extras={'schools': SCHOOLS, 'schoolColours': ['#%06x' % c for c in SCHOOL_COL]} if has_w else None)
        Q['scale'] = 1.0
    if 'qs' in res:
        others = [res[k]['top'] for k in res if k != 'qs']
        if others:
            ok = res['qs']['top'] >= 1.15 * max(others)
            line = f'leader pennant top {res["qs"]["top"]:.2f} m >= 1.15 x tallest squad member {max(others):.2f} m'
            print(('PASS ' if ok else 'FAIL ') + 'qs ' + line); res['qs']['gates'].append((ok, line)); res['qs']['passed'] += ok; res['qs']['checks'] += 1
    json.dump(res, open(os.path.join(OUT, 'rebel_gates.json'), 'w'), indent=1, ensure_ascii=False)
    for k, v in res.items(): print(f'SUMMARY {k} {v["passed"]} of {v["checks"]} tris {v["tris"]} weapons {v["weapon_tris"]} top {v["top"]:.2f} cloth solved {v["solved"]:.0%}')
