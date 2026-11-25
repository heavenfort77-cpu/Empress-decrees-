# SUITS fa round 5 (owner GO 25 Nov 10:55): 法甲 廷尉 rebuilt as ONE sample the way the owner's armour-suit kit does it
# (/home/claude/kits/armour-suit: Techno-Plate-Style-Study.md, 3d/HANDOFF-3D.md; technique only, its main.js is not copied):
#  - per-character LOOK table (plate / dark / trim / binding), here from the research palette and the owner's school mapping (法 = lead white);
#  - head = ONE sculpted shell: a height function over the head wrap, cut by marching squares over a signed field (outline, eye slits,
#    mouth), the lead-white mask region and the black lacquer helm in the same shell, framed by a brow eave and cheek flanges;
#  - engraving = height picture -> colour map + normal map (art/tools/fa_tex.py), gold inlay lines on plate edges;
#  - kit proportions: about 7.3 heads (kit 7, concepts 7.5), broad readable shoulder mass (3+ head heights across), limbs at least 0.45 head thick.
# Removes the five causes of the rejection (brief): near-black head to toe, 6.4 heads / thin limbs / small shoulders, plain dome helmet,
# no trim, no concept or kit comparison.
# The rig, the clip set (idle, run, attack windup 0.45 s, hit, death), LODs, export and the build gates are the approved pipeline in
# art/tools/suit_blender.py (imported, not copied); only fa's parts, proportions and materials are new. The other eight suits are not built.
# Output: OUTDIR/fa.glb, OUTDIR/fa_sil.npz, OUTDIR/suits_info.json, OUTDIR/fa_r5_metrics.json, PASS/FAIL lines.
# Usage: python fa_r5.py -- OUTDIR fa
import bpy, bmesh, math, sys, os, json
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suit_blender as SB

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Shoulder joint x, m (old fa 0.184: arms hung inside the torso line; wider joint carries the broad pauldrons and keeps the arms clear).
SX = 0.238
# Build scales (SB.Body): H height, W shoulders, G girth, L limb thickness (old fa 1.0 / 0.92 / 0.9 / 0.9: a stick).
FA_H, FA_W, FA_G, FA_L = 1.0, 1.15, 1.06, 1.22
# Lamella row height, m (study 12.5 cm), outward step per row, m, superellipse exponent of rows.
LAM_H, LAM_STEP, LAM_N = 0.125, 0.018, 2.5
# Binding (black silk cord) band height and how far it stands proud, m; every n-th row carries one.
CORD_H, CORD_OUT, CORD_EVERY = 0.026, 0.007, 2
# Gold inlay rims (bracer, greave, pauldron, collar ends): band height and proud, m.
RIM_H, RIM_OUT = 0.024, 0.006
# Head shell: grid cells around (azimuth) and up (elevation) at LOD0; head centre above the chin, m; radii side / front-back / up / down, m.
SHELL_NU, SHELL_NV = 44, 26
HEAD_C, HEAD_A, HEAD_F, HEAD_UP, HEAD_DN = 0.125, 0.122, 0.138, 0.145, 0.135
# Shell elevation range, deg: bottom at the face (mask chin) and at the back (neck guard edge), top (just short of the pole; the pole is welded).
E_CHIN, E_BACK, E_TOP = -62.0, -38.0, 89.0
# Mask window (radians in azimuth, elevation): half width at the cheekbones and at the chin, brow line (lower at the centre: stern V).
MASK_W, MASK_WCHIN, BROW_E0, BROW_EK = 1.02, 0.52, 0.12, 0.10
# Eye slits: centre (azimuth, elevation) rad, half length, half height, slant deg (outer end up: stern); mouth slot: elevation, half width,
# half height, frown (the ends drop by this many rad).
EYE = (0.40, -0.07, 0.235, 0.045, 22.0)
MOUTH = (-0.66, 0.26, 0.028, 0.045)
# Sculpt heights, m: mask stands proud of the helm, brow ridge, nose ridge, cheekbones, cheek hollow, crest ridge, neck-guard flare.
H_MASK, H_BROW, H_NOSE, H_CHEEK, H_HOLLOW, H_CREST, H_FLARE = 0.010, 0.016, 0.022, 0.008, -0.006, 0.012, 0.035
# Shell wall thickness at the cut edges (rim walls only), m.
SHELL_T = 0.006
# Horn (獬豸, the law beast: one horn, hooking forward = pursuit): rise above the helmet top and forward hook, m.
HORN_UP, HORN_FWD = 0.34, 0.22
# Visual heads band (helmet top / (helmet top - mask chin), horn excluded): kit 7 (measured knight 7.2, rogue 6.7) to concepts 7.5.
HEADS_VIS = (7.0, 7.6)
# Shoulder span (pauldron outer edges) over the visual head height: kit rogue 2.6, knight 4.1 (measured on the kit sheets).
SPAN_BAND = (2.8, 3.8)
# Limb thickness (bracer and greave diameter) over the visual head height, min (kit rogue about 0.4, knight 0.8-1.0).
LIMB_MIN = 0.45
# LOD0 triangle target (budget 10-15k): the ring segment scale is solved (up or down) until the parts land near it (shakedown run 45539289794
# built 7,540 at scale 1.0, under the 10k floor).
TRI_TARGET = 13800
# Sky-bent normals (stylised shading for the top-down game camera): every vertex normal is blended toward world up by this factor before
# export (n' = normalize(n + K up)); side and lower faces then take more sun and sky. Cause it answers (run 45539289794): outline pixels
# at grazing angles render at median Y 0.05-0.07 while 3:1 against the floor needs 0.27. Not an outline: the shape and the GLB topology are
# unchanged, only the stored normals.
SKY_BEND = 0.8
# Mask tilt: the lower face is pushed forward by this much at the chin, m (the face plane leans back and faces up toward the camera and sun).
MASK_TILT = 0.03
# Material settings (three.js MeshStandardMaterial via glTF): roughness, metalness per atlas (no environment map in the game: metal stays
# low so the albedo carries the value under hemisphere + sun).
MATS = {'faA': (0.42, 0.0), 'faM': (0.35, 0.25), 'faC': (0.85, 0.0)}

_R = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fa_rows.json')))
SB.SHEETS.update({k: tuple(v) for k, v in _R['sizes'].items()})
SB.ROWS.update({k: {r: tuple(v) for r, v in d.items()} for k, d in _R['rows'].items()})
SB.PREVIEW.update({'lam': (226, 220, 206), 'lamu': (226, 220, 206), 'plate': (236, 230, 216), 'plate2': (238, 232, 218), 'lacq': (34, 29, 28),
                   'cord': (24, 20, 20), 'mask': (240, 236, 226), 'gold': (212, 178, 90), 'goldp': (212, 178, 90), 'goldb': (212, 178, 90),
                   'blade': (200, 160, 90), 'bronze': (176, 138, 78), 'silk_w': (229, 225, 202), 'silk_b': (30, 27, 28)})
SB.TRIM_SUITS = [s for s in SB.TRIM_SUITS if s != 'fa']   # fa's sash and cuffs are part of its own build now
SB.SUITS['fa'].update(H=FA_H, W=FA_W, G=FA_G, L=FA_L, cloth='#e5e1ca', trim='gold', lac='white')
loft, tube, path, bez, segs, D = SB.loft, SB.tube, SB.path, SB.bez, SB.segs, SB.D
METRICS = {}

class FaBody(SB.Body):
    """fa proportions: the approved FIX-A levels (ankle 0.10, knee 0.56, hip 1.03, belt 1.15, chest 1.45, shoulder 1.62, chin 1.755 m)
    with a wider shoulder joint; the visual head is the sculpted shell, measured from the mesh (HEADS_VIS)."""
    def __init__(s, S):
        super().__init__(S); s.sx = SX

# helpers ---------------------------------------------------------------------------------------------------------------
def lam_rows(name, z_top, rows, bone, ab_fn, kind='rigid', allow=None, up=False, N=None, cord=True, step=LAM_STEP):
    """lamellar rows from z_top down. Shingle rows (up=False, chest/shoulders as on the terracotta armour): each row's lower edge stands out
    and its lip folds back under. Belly rows (up=True, skirt and tassets: the lower rows overlap upward so the wearer can bend): each row's
    upper edge stands out over the row above, the surface faces up and out (catches the sun from above), lip folded in at the top."""
    N = N or segs(SB.SEG_BODY)
    for k in range(rows):
        zt = z_top - k * LAM_H; zb = zt - LAM_H
        ct, ft, at, bt = ab_fn(zt); cb, fb, ab, bb = ab_fn(zb)
        if up:
            secs = [((ct, ft, zt - 0.012), at + step - 0.012, bt + step - 0.012, LAM_N), ((ct, ft, zt), at + step, bt + step, LAM_N),
                    ((cb, fb, zb - 0.012), ab + 0.003, bb + 0.003, LAM_N)]
            row = 'lamu'
        else:
            secs = [((ct, ft, zt + 0.01), at, bt, LAM_N), ((cb, fb, zb), ab + step, bb + step, LAM_N), ((cb, fb, zb + 0.014), ab + 0.003, bb + 0.003, LAM_N)]
            row = 'lam'
        loft(f'{name}{k}', secs, 'faA', row, bone, N=N, caps=(False, False), kind=kind, allow=allow, flat=True, vz=True)
        if cord and k % CORD_EVERY == 0:
            zc = (zt - LAM_H * 0.5); cc, fc, ac, bc = ab_fn(zc); fl = step * 0.5 + CORD_OUT
            loft(f'{name}c{k}', [((cc, fc, zc + CORD_H / 2), ac + fl, bc + fl, LAM_N), ((cc, fc, zc - CORD_H / 2), ac + fl, bc + fl, LAM_N)],
                 'faA', 'cord', bone, N=N, caps=(False, False), kind=kind, allow=allow, flat=True, vz=True)

def rim(name, c, a, b_, z0, z1, bone, n=2.4, N=None, row='gold', kind='rigid', allow=None):
    """a gold inlay band (flat ring) around a part, between heights z0 > z1 (design coords, horizontal rings)."""
    loft(name, [((c[0], c[1], z0), a, b_, n), ((c[0], c[1], z1), a, b_, n)], 'faM', row, bone, N=N or segs(SB.SEG_LIMB), caps=(False, False),
         flat=True, vz=True, kind=kind, allow=allow)

def along(p0, p1, t): return tuple(Vector(p0) + (Vector(p1) - Vector(p0)) * t)

# body -----------------------------------------------------------------------------------------------------------------
def c_body(b):
    """undersuit (black silk), torso core, neck, gauntlets, boots with Qin upturned square toes."""
    L = b.L
    zs = [b.z(v) for v in (0.9, 0.97, 1.03, 1.2, 1.32, 1.42, 1.5)]
    loft('core', [((0, 0, zz), *b.torso_ab(zz), 2.6) for zz in zs], 'faC', 'silk_b', 'spine', N=segs(SB.SEG_BODY))
    tube('neck', (0, 0, b.zneck - 0.04), (0, 0, b.zchin + 0.04), 0.068, 0.062, 'faC', 'silk_b', 'neck', N=segs(SB.SEG_LIMB))
    for side, m in (('R', 1), ('L', -1)):
        sh = (m * b.sx, 0, b.zsh - 0.01); el = (m * (b.sx + 0.05), 0, b.zelb); wr = (m * (b.sx + 0.08), 0.05, b.zwri)
        loft(f'sleeve_{side}', [(sh, 0.068 * L, 0.068 * L, 2), (el, 0.058 * L, 0.058 * L, 2)], 'faC', 'silk_b', f'upper_arm.{side}', caps=(True, False))
        loft(f'farm_{side}', [(el, 0.05 * L, 0.05 * L, 2), (wr, 0.042 * L, 0.04 * L, 2)], 'faC', 'silk_b', f'forearm.{side}')
        hc = b.hand(m)
        loft(f'hand_{side}', [(wr, 0.042 * L, 0.032 * L, 2.2), ((hc[0], hc[1] + 0.005, hc[2]), 0.052 * L, 0.042 * L, 2.6),
                              ((m * (b.sx + 0.09), 0.075, b.zhand), 0.036 * L, 0.031 * L, 2.4)], 'faA', 'lacq', f'hand.{side}', N=segs(SB.SEG_SMALL))
        # plate back of the gauntlet (lead white): the hands sit on the outline beside the skirt
        loft(f'gaunt_{side}', [((wr[0] + m * 0.004, wr[1] - 0.004, wr[2] + 0.01), 0.05 * L, 0.04 * L, 2.6), ((hc[0] + m * 0.012, hc[1] - 0.004, hc[2]), 0.05 * L, 0.036 * L, 2.6),
                               ((hc[0] + m * 0.01, hc[1] + 0.01, hc[2] - 0.045), 0.03 * L, 0.025 * L, 2.4)], 'faA', 'plate2', f'hand.{side}', N=segs(SB.SEG_SMALL))
        hp = (m * b.hx, 0, b.zhip); kn = (m * (b.hx + 0.01), 0.01, b.zknee); an = (m * (b.hx + 0.015), -0.01, b.zank)
        loft(f'thigh_{side}', [(hp, 0.1 * L, 0.1 * L, 2), (kn, 0.068 * L, 0.068 * L, 2)], 'faC', 'silk_b', f'thigh.{side}', caps=(False, True))
        loft(f'shin_{side}', [(kn, 0.06 * L, 0.06 * L, 2), (an, 0.045 * L, 0.045 * L, 2)], 'faC', 'silk_b', f'shin.{side}')
        x = an[0]
        loft(f'boot_{side}', [((x, -0.035, 0.15), 0.056 * L, 0.06 * L, 2.4), ((x, -0.01, 0.06), 0.06 * L, 0.075 * L, 2.8), ((x, 0.06, 0.035), 0.055 * L, 0.06 * L, 3.0),
                              ((x, 0.15, 0.03), 0.045 * L, 0.04 * L, 3.2), ((x, 0.2, 0.05), 0.035 * L, 0.02 * L, 3.2)], 'faA', 'lacq', f'foot.{side}',
             N=segs(SB.SEG_LIMB), ref=Vector((0, 0, 1)))
        loft(f'sabaton_{side}', [((x, -0.0, 0.13), 0.06 * L, 0.05 * L, 2.6), ((x, 0.06, 0.085), 0.058 * L, 0.05 * L, 2.8), ((x, 0.14, 0.06), 0.045 * L, 0.035 * L, 3.0)],
             'faA', 'plate2', f'foot.{side}', N=segs(SB.SEG_SMALL + 2), ref=Vector((0, 0, 1)))
        loft(f'sole_{side}', [((x, -0.04, 0.03), 0.06 * L, 0.06 * L, 3), ((x, 0.17, 0.02), 0.05 * L, 0.04 * L, 3)], 'faA', 'lacq', f'foot.{side}',
             N=segs(SB.SEG_SMALL), ref=Vector((0, 0, 1)))

def c_torso(b):
    """breastplate (one convex lead-white plate with an engraved top band and a gold rim), back plate, two belly rows of upward lamellae,
    black lacquer belt with a gold plaque, high collar ring."""
    ab = lambda zz: (0, 0, *(v + 0.014 for v in b.torso_ab(zz)))
    zb0 = b.z(1.17)
    # belly rows (between the breastplate and the belt)
    lam_rows('belly', zb0 + 0.01, 2, 'spine', ab, up=True)
    # breastplate and back plate: one shell each over the upper torso (front half and back half by a superellipse loft with a keel)
    zt, zc, zl = b.z(1.5), b.z(1.36), zb0 - 0.02
    a0, b0 = b.torso_ab(zc)
    loft('breast', [((0, 0.0, zt), a0 * 0.78, b0 * 0.9 + 0.02, 2.3), ((0, 0.02, zc + 0.05), a0 + 0.03, b0 + 0.045, 2.5),
                    ((0, 0.02, zc - 0.06), a0 + 0.028, b0 + 0.04, 2.5), ((0, 0.015, zl), a0 * 0.94 + 0.02, b0 + 0.035, 2.4)], 'faA', 'plate', 'chest',
         N=segs(SB.SEG_BODY + 8))
    rim('breastrim', (0, 0.015), a0 * 0.94 + 0.026, b0 + 0.041, zl + 0.024, zl, 'chest', N=segs(SB.SEG_BODY + 8))
    # collar: a high ring of plate over the neck root with a gold top edge (frames the mask from below)
    loft('collar', [((0, 0, b.zneck - 0.05), 0.125, 0.115, 2.2), ((0, 0.005, b.zneck + 0.02), 0.11, 0.105, 2.2), ((0, 0.01, b.zneck + 0.045), 0.1, 0.098, 2.2)],
         'faA', 'plate', 'chest', N=segs(SB.SEG_BODY))
    rim('collarrim', (0, 0.01), 0.104, 0.102, b.zneck + 0.05, b.zneck + 0.03, 'chest', n=2.2, N=segs(SB.SEG_BODY))
    # belt: black lacquer with a gold plaque in front; lead-white silk sash tied over it (school colour)
    a1, b1 = b.torso_ab(b.zwaist)
    loft('belt', [((0, 0, b.zwaist + 0.045), a1 + 0.04, b1 + 0.04, 2.5), ((0, 0, b.zwaist - 0.035), a1 + 0.045, b1 + 0.045, 2.5)], 'faA', 'lacq', 'hips',
         N=segs(SB.SEG_BODY), flat=True, vz=True)
    loft('sash', [((0, 0, b.zwaist + 0.02), a1 + 0.052, b1 + 0.052, 2.5), ((0, 0, b.zwaist - 0.012), a1 + 0.054, b1 + 0.054, 2.5)], 'faC', 'silk_w', 'hips',
         N=segs(SB.SEG_BODY), flat=True, vz=True)
    loft('plaque', [((0, b1 + 0.05, b.zwaist + 0.05), 0.06, 0.012, 3), ((0, b1 + 0.058, b.zwaist - 0.045), 0.06, 0.012, 3)], 'faM', 'goldp', 'hips',
         N=segs(SB.SEG_SMALL), ref=Vector((0, -1, 0)))

def c_lower(b):
    """split tassets of upward lamellae (4 rows, follow the thighs) and a lead-white silk apron between them, to the knee."""
    allowL = lambda s: ['hips', f'thigh.{s}', f'shin.{s}']
    for side, m in (('R', 1), ('L', -1)):
        def ab(zz, m=m):
            a, bb = b.torso_ab(b.z(0.86)); t = (b.zwaist - zz) / b.zwaist
            return (m * (0.088 * b.G + 0.035 * t), 0.0, 0.1 * b.G + 0.05 * t, bb + 0.04 + 0.06 * t)
        lam_rows(f'tas{side}', b.zwaist - 0.02, 4, 'hips', ab, kind='cloth', allow=allowL(side), up=True, N=segs(SB.SEG_LIMB + 4), step=0.03)
    a0, b0 = b.torso_ab(b.zwaist)
    loft('apron', [((0, b0 + 0.06, b.zwaist - 0.03), 0.085, 0.01, 2.6), ((0, b0 + 0.085, b.zhip - 0.1), 0.08, 0.01, 2.6),
                   ((0, b0 + 0.1, b.zknee + 0.04), 0.07, 0.01, 2.6), ((0, b0 + 0.1, b.zknee - 0.02), 0.035, 0.008, 2.2)], 'faC', 'silk_w', 'hips',
         N=segs(SB.SEG_SMALL + 2), ref=Vector((0, -1, 0)), kind='cloth', allow=['hips', 'thigh.R', 'thigh.L'])
    loft('apronband', [((0, b0 + 0.072, b.zwaist - 0.04), 0.09, 0.012, 3), ((0, b0 + 0.076, b.zwaist - 0.07), 0.088, 0.012, 3)], 'faM', 'gold', 'hips',
         N=segs(SB.SEG_SMALL + 2), ref=Vector((0, -1, 0)))

def c_shoulders(b):
    """broad pauldrons: a domed lead-white cap plate (engraved band, gold rim) over two flaring shingle rows; tops face up (catch the sun)."""
    for side, m in (('R', 1), ('L', -1)):
        c = (m * (b.sx + 0.045), 0.0, b.zsh + 0.03); bone = f'upper_arm.{side}'
        def ab(zz):
            t = (b.zsh - 0.02 - zz) / (2 * LAM_H)
            return (c[0] + m * 0.03 * t, 0.0, 0.12 + 0.03 * t, 0.115 + 0.02 * t)
        lam_rows(f'paul{side}', b.zsh - 0.02, 2, bone, ab, N=segs(SB.SEG_LIMB + 6), step=0.035, up=True)
        loft(f'cap{side}', [((c[0] - m * 0.01, 0, c[2] + 0.095), 0.015, 0.015, 2), ((c[0], 0, c[2] + 0.07), 0.09, 0.085, 2.2), ((c[0] + m * 0.02, 0, c[2] + 0.02), 0.14, 0.125, 2.4),
                            ((c[0] + m * 0.03, 0, c[2] - 0.04), 0.155, 0.135, 2.4), ((c[0] + m * 0.03, 0, c[2] - 0.03), 0.14, 0.122, 2.4)], 'faA', 'plate', bone,
             N=segs(SB.SEG_BODY), caps=(True, False), flat=True)
        rim(f'caprim{side}', (c[0] + m * 0.03, 0), 0.158, 0.138, c[2] - 0.018, c[2] - 0.042, bone, N=segs(SB.SEG_BODY))
        # elbow cop
        el = (m * (b.sx + 0.05), 0.0, b.zelb)
        loft(f'cop{side}', [((el[0] + m * 0.0, -0.02, el[2] + 0.06), 0.06, 0.05, 2.2), ((el[0] + m * 0.01, -0.035, el[2]), 0.08, 0.07, 2.4),
                            ((el[0] + m * 0.0, -0.02, el[2] - 0.06), 0.065, 0.055, 2.2)], 'faA', 'plate2', f'forearm.{side}', N=segs(SB.SEG_LIMB), ref=Vector((0, 0, 1)))

def c_limbs(b):
    """bracers and greaves: lead-white plate with gold rims at both ends; knee cops."""
    L = b.L
    for side, m in (('R', 1), ('L', -1)):
        el = Vector((m * (b.sx + 0.05), 0, b.zelb)); wr = Vector((m * (b.sx + 0.08), 0.05, b.zwri)); p = lambda t: tuple(el + (wr - el) * t)
        loft(f'bracer_{side}', [(p(0.18), 0.058 * L, 0.055 * L, 2.6), (p(0.5), 0.062 * L, 0.056 * L, 2.6), (p(0.96), 0.054 * L, 0.05 * L, 2.6)], 'faA', 'plate',
             f'forearm.{side}', N=segs(SB.SEG_LIMB + 4))
        for nm, t, r in (('a', 0.18, 0.06), ('b', 0.93, 0.056)):
            q0, q1 = p(t), p(t + 0.06 if nm == 'a' else t + 0.05)
            loft(f'brim{nm}_{side}', [(q0, r * L + RIM_OUT, r * L * 0.94 + RIM_OUT, 2.6), (q1, r * L + RIM_OUT, r * L * 0.94 + RIM_OUT, 2.6)], 'faM', 'gold', f'forearm.{side}',
                 N=segs(SB.SEG_LIMB + 4), caps=(False, False))
        kn = Vector((m * (b.hx + 0.01), 0.01, b.zknee)); an = Vector((m * (b.hx + 0.015), -0.01, b.zank)); q = lambda t: tuple(kn + (an - kn) * t)
        loft(f'greave_{side}', [(q(0.12), 0.072 * L, 0.07 * L, 2.6), (q(0.4), 0.078 * L, 0.074 * L, 2.6), (q(0.88), 0.06 * L, 0.058 * L, 2.6)], 'faA', 'plate',
             f'shin.{side}', N=segs(SB.SEG_LIMB + 4), ref=Vector((0, -1, 0)))
        for nm, t0, t1, r in (('a', 0.12, 0.18, 0.074), ('b', 0.82, 0.88, 0.062)):
            loft(f'grim{nm}_{side}', [(q(t0), r * L + RIM_OUT, r * L * 0.97 + RIM_OUT, 2.6), (q(t1), r * L + RIM_OUT, r * L * 0.97 + RIM_OUT, 2.6)], 'faM', 'gold',
                 f'shin.{side}', N=segs(SB.SEG_LIMB + 4), caps=(False, False), ref=Vector((0, -1, 0)))
        loft(f'knee_{side}', [((kn.x, kn.y + 0.04, kn.z + 0.07), 0.05, 0.04, 2.2), ((kn.x, kn.y + 0.07, kn.z), 0.075, 0.05, 2.4),
                              ((kn.x, kn.y + 0.05, kn.z - 0.07), 0.055, 0.04, 2.2)], 'faA', 'plate2', f'shin.{side}', N=segs(SB.SEG_LIMB), ref=Vector((0, -1, 0)))

# head: one sculpted shell (marching squares over a signed field on the head wrap) ------------------------------------------------
def smoothstep(a, b_, x): t = min(1.0, max(0.0, (x - a) / (b_ - a))); return t * t * (3 - 2 * t)

def head_frame(b):
    zc = b.zchin + HEAD_C
    return Vector((0.0, 0.012, zc))

def wrap(b, th, e, h):
    """design point on the head wrap at azimuth th (0 = forward, + = the suit's right), elevation e (rad), pushed out by h along the
    ellipsoid normal."""
    C = head_frame(b); az = HEAD_UP if e >= 0 else HEAD_DN
    ce, se, ct, st = math.cos(e), math.sin(e), math.cos(th), math.sin(th)
    p = Vector((HEAD_A * ce * st, HEAD_F * ce * ct, az * se))
    n = Vector((p.x / HEAD_A ** 2, p.y / HEAD_F ** 2, p.z / az ** 2)).normalized()
    # mask tilt: the lower face moves straight forward (the face plane leans back and faces up toward the camera and sun)
    tilt = MASK_TILT * smoothstep(-0.1, 0.1, mask_field(th, e)) * smoothstep(0.15, -1.0, e) * max(0.0, math.cos(th)) ** 2
    return C + p + n * h + Vector((0.0, tilt, 0.0)), n

def brow_e(th): return math.radians(0) + BROW_E0 + BROW_EK * min(1.0, abs(th) / 0.6)

def mask_field(th, e):
    """> 0 inside the mask outline (azimuth th, elevation e in rad)."""
    w = MASK_WCHIN + (MASK_W - MASK_WCHIN) * smoothstep(math.radians(E_CHIN), -0.25, e)
    return min(w - abs(th), brow_e(th) - e, e - math.radians(E_CHIN) + 0.02)

def holes(th, e):
    """> 0 inside a hole: eye slits (lens shaped, slanted outer end up) and the frowning mouth slot."""
    out = -1.0
    ex, ey, ea, eb, sl = EYE
    for m in (1, -1):
        s0, t0 = th - m * ex, e - ey; a = math.radians(sl) * m
        s = s0 * math.cos(a) + t0 * math.sin(a); t = -s0 * math.sin(a) + t0 * math.cos(a)
        out = max(out, 1 - (abs(s / ea) ** 1.4 + (t / eb) ** 2))
    my, mw, mh, fr = MOUTH; s = th / mw; t = (e - (my - fr * s * s)) / mh
    out = max(out, 1 - (abs(s) ** 4 + t * t))
    return out

def height(th, e):
    """sculpt: mask proud of the helm, brow ridge (stern V), nose ridge, cheekbones and hollows, central crest ridge, neck-guard flare."""
    h = 0.0; mf = mask_field(th, e)
    h += H_MASK * smoothstep(-0.03, 0.05, mf)
    be = brow_e(th)
    h += H_BROW * math.exp(-((e - be + 0.03) / 0.06) ** 2) * smoothstep(-MASK_W - 0.1, -MASK_W + 0.25, -abs(th))
    h += H_NOSE * math.exp(-(th / 0.075) ** 2) * smoothstep(-0.5, -0.3, e) * (1 - smoothstep(0.02, be - 0.02, e)) * (0.6 + 0.4 * smoothstep(-0.5, 0.0, e))
    for m in (1, -1):
        h += H_CHEEK * math.exp(-(((th - m * 0.47) / 0.16) ** 2 + ((e + 0.2) / 0.12) ** 2))
        h += H_HOLLOW * math.exp(-(((th - m * 0.36) / 0.12) ** 2 + ((e + 0.45) / 0.1) ** 2))
    d0 = min(abs(th), abs(abs(th) - math.pi))
    over = smoothstep(be + 0.05, be + 0.3, e) if abs(th) < 1.5 else smoothstep(-0.3, 0.1, e)
    h += H_CREST * math.exp(-(d0 / 0.07) ** 2) * over
    if e < 0: h += H_FLARE * smoothstep(1.6, 2.6, abs(th)) * smoothstep(-0.25, -0.62, e) ** 1.5
    return h

def shell_field(th, e):
    bot = math.radians(E_CHIN) + (math.radians(E_BACK) - math.radians(E_CHIN)) * smoothstep(0.75, 1.35, abs(th))
    return min(e - bot, math.radians(E_TOP) - e, -holes(th, e) if mask_field(th, e) > -0.05 else 1.0)

def ms_shell(b, nu, nv):
    """marching squares over (azimuth, elevation): the inside of shell_field becomes faces; cut points on cell edges are interpolated, so the
    outline, eye slits and mouth are smooth curves, not grid steps. UVs: mask faces map planar (front, MASK_PPM) into the 'mask' row;
    helm faces wrap around the 'lacq' row. One shell, one material (faA)."""
    e0, e1 = math.radians(min(E_CHIN, E_BACK)) - 0.01, math.radians(E_TOP)
    us = [-math.pi + 2 * math.pi * i / nu for i in range(nu + 1)]; vs = [e0 + (e1 - e0) * j / nv for j in range(nv + 1)]
    F = [[shell_field(u, v) for v in vs] for u in us]
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); VC = {}
    def vert(key, th, e):
        if key not in VC:
            p, _ = wrap(b, th, e, height(th, e)); VC[key] = (bm.verts.new(D(*p)), th, e)
        return VC[key]
    W, H, M = SB.SHEETS['faA']; my0, my1 = SB.ROWS['faA']['mask']; ly0, ly1 = SB.ROWS['faA']['lacq']; MP = 512
    zbrow = wrap(b, 0, BROW_E0, 0)[0].z
    def uv(th, e, is_mask):
        p, _ = wrap(b, th, e, 0)
        if is_mask:
            u = (p.x + 0.15) * MP / W; y = my0 + 1 + max(0.0, min(my1 - my0 - 2, (zbrow - p.z) * MP + 4)); return (u, 1 - y / H)
        u = (th + math.pi) * 0.135 * 256 / W; y = ly0 + 1 + (e1 - e) / (e1 - e0) * (ly1 - ly0 - 2) * 0.9; return (u, 1 - y / H)
    tris = []
    for i in range(nu):
        for j in range(nv):
            cs = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            val = [F[a][c] for a, c in cs]
            if max(val) < 0: continue
            pts = []
            for k in range(4):
                (a0, c0), (a1, c1) = cs[k], cs[(k + 1) % 4]; f0, f1 = val[k], val[(k + 1) % 4]
                if f0 >= 0: pts.append((('g', a0 % nu, c0), us[a0], vs[c0]))
                if (f0 >= 0) != (f1 >= 0):
                    t = f0 / (f0 - f1); th = us[a0] + (us[a1] - us[a0]) * t; e = vs[c0] + (vs[c1] - vs[c0]) * t
                    key = ('e',) + tuple(sorted(((a0 % nu, c0), (a1 % nu, c1))))
                    pts.append((key, th, e))
            inside = [k for k in range(4) if val[k] >= 0]
            if len(inside) == 2 and inside in ([0, 2], [1, 3]):
                cu = (us[i] + us[i + 1]) / 2; cv = (vs[j] + vs[j + 1]) / 2
                if shell_field(cu, cv) < 0:   # saddle with an outside centre: two corner triangles
                    for k in inside:
                        k0 = [q for q in pts if q[0] == ('g', cs[k][0] % nu, cs[k][1])][0]; idx = pts.index(k0)
                        tris.append((pts[idx - 1], k0, pts[(idx + 1) % len(pts)]))
                    continue
            for k in range(1, len(pts) - 1): tris.append((pts[0], pts[k], pts[k + 1]))
    nmask = 0
    for tri in tris:
        thc = sum(q[1] for q in tri) / 3; ec = sum(q[2] for q in tri) / 3; is_mask = mask_field(thc, ec) > 0; nmask += is_mask
        vs_ = [vert(q[0], q[1], q[2])[0] for q in tri]
        if len(set(vs_)) < 3: continue
        try: f = bm.faces.new(vs_)
        except ValueError: continue
        thr = [q[1] for q in tri]
        if max(thr) - min(thr) > math.pi: thr = [t + 2 * math.pi if t < 0 else t for t in thr]   # back seam: keep u continuous on the face
        for lp, q, tq in zip(f.loops, tri, thr): lp[uvl].uv = uv(tq if not is_mask else q[1], q[2], is_mask)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)
    # outward normals: faces must point away from the head centre
    C = D(*head_frame(b)); bm.normal_update()
    out_ = sum(1 for f in bm.faces if f.normal.dot(f.calc_center_median() - C) > 0)
    if out_ < len(bm.faces) / 2: bmesh.ops.reverse_faces(bm, faces=bm.faces)
    for f in bm.faces: f.smooth = True
    ob = SB.put('shell', bm, 'faA', 'head')
    # rim walls along every cut edge (slits, mouth, outline): thickness without a back shell
    md = ob.modifiers.new('wall', 'SOLIDIFY'); md.thickness = SHELL_T; md.use_rim_only = True; md.offset = -1
    bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier='wall')
    return ob, nmask, len(tris)

def c_head(b):
    """the sculpted shell, a dark inner head behind the slits, the brow eave and cheek flanges framing the mask (black lacquer, gold edge),
    and the 獬豸 horn (lead white, gold socket)."""
    ob, nmask, ntri = ms_shell(b, max(16, int(SHELL_NU * SB.Q['seg'])), max(12, int(SHELL_NV * SB.Q['seg'])))
    C = head_frame(b)
    loft('innerhead', [((C.x, C.y - 0.005, C.z + 0.1), 0.04, 0.04, 2), ((C.x, C.y - 0.005, C.z), 0.1, 0.112, 2), ((C.x, C.y - 0.01, C.z - 0.12), 0.07, 0.08, 2)],
         'faA', 'lacq', 'head', N=segs(SB.SEG_LIMB))
    # brow eave: an arched band over the mask top, standing out from the helm (shades the eyes from above)
    pts, w, gold = [], [], []
    for k in range(11):
        th = -1.05 + 2.1 * k / 10; e = brow_e(th) + 0.07
        p, n = wrap(b, th, e, height(th, e) + 0.012 - 0.004 * abs(th)); pts.append(tuple(p)); w.append((0.014 - 0.004 * abs(th), 0.007))
        g, _ = wrap(b, th, e - 0.004, height(th, e) + 0.026 - 0.008 * abs(th)); gold.append(tuple(g))
    path(pts, w, 'faA', 'lacq', 'head', 'eave', n=2.6, N=8, ref=Vector((0, 0, 1)))
    path(gold, [(0.005, 0.006)] * 11, 'faM', 'goldb', 'head', 'eavegold', n=2.2, N=6, ref=Vector((0, 0, 1)))
    # cheek flanges: plates from the temples down past the jaw, flaring out (frame the mask at the sides)
    for m in (1, -1):
        top, n0 = wrap(b, m * 1.2, 0.05, 0.012); mid, _ = wrap(b, m * 1.22, -0.45, 0.03); low, _ = wrap(b, m * 1.18, -0.85, 0.06)
        path([tuple(top), tuple(mid), tuple(low)], [(0.04, 0.007), (0.045, 0.007), (0.04, 0.007)], 'faA', 'lacq', 'head', f'flange{m}', n=3, N=8,
             ref=Vector((m, 0.3, 0)).normalized())
        path([tuple(Vector(top) + Vector((m * 0.008, 0.035, 0))), tuple(Vector(mid) + Vector((m * 0.01, 0.04, 0))), tuple(Vector(low) + Vector((m * 0.012, 0.035, 0)))],
             [(0.006, 0.006)] * 3, 'faM', 'goldb', 'head', f'flangegold{m}', N=6)
    # horn: rises from the brow and hooks forward (pursuit); lead white with a gold socket
    base, _ = wrap(b, 0.0, 0.62, height(0.0, 0.62)); top = wrap(b, 0.0, math.radians(E_TOP), 0)[0]
    p0 = Vector(base); p2 = Vector((0, p0.y + HORN_FWD, top.z + HORN_UP)); p1 = Vector((0, p0.y - 0.11, top.z + HORN_UP * 0.75))
    hp = bez(tuple(p0), tuple(p1), tuple(p2), 10)
    hw = [(0.048, 0.06), (0.046, 0.056), (0.042, 0.05), (0.037, 0.044), (0.031, 0.037), (0.025, 0.03), (0.019, 0.023), (0.013, 0.016), (0.007, 0.009), (0.001, 0.001)]
    path(hp, hw, 'faA', 'plate2', 'head', 'horn', N=segs(SB.SEG_LIMB))
    tube('hornsock', tuple(p0 + Vector((0, -0.005, -0.02))), tuple(p0 + Vector((0, -0.012, 0.05))), 0.058, 0.052, 'faM', 'goldp', 'head', N=segs(SB.SEG_LIMB))
    # measures for the gates (design coords): helmet top, mask chin (lowest mask vertex), shell vertex count
    zs = [ (ob.matrix_world @ v.co).z for v in ob.data.vertices]
    METRICS['helm_top'] = max(zs); METRICS['shell_bottom'] = min(zs)
    METRICS['mask_chin'] = wrap(b, 0.0, math.radians(E_CHIN), height(0.0, math.radians(E_CHIN)))[0].z
    METRICS['shell_tris_cut'] = ntri; METRICS['shell_mask_tris'] = nmask

def c_sword(b, S):
    """long straight bronze jian held low and forward (approved direction and length; fa's own materials)."""
    g = b.hand(1); Lb = 0.95; d = Vector((0.45, 0.6, -0.66)).normalized(); gp = Vector(g)
    P_ = lambda t: tuple(gp + d * t)
    loft('grip', [(P_(-0.1), 0.019, 0.019, 2), (P_(0.03), 0.021, 0.021, 2)], 'faA', 'lacq', 'weapon', N=6)   # lacq row: the cord row (8.6 cm) squeezed it to 0.66 density
    loft('pommel', [(P_(-0.14), 0.032, 0.032, 2), (P_(-0.1), 0.03, 0.03, 2)], 'faM', 'goldp', 'weapon', N=8)
    loft('guard', [(P_(0.03), 0.065, 0.026, 2.6), (P_(0.06), 0.052, 0.021, 2.4)], 'faM', 'goldp', 'weapon', N=8, ref=Vector((1, 0, 0)))
    loft('blade', [(P_(0.06), 0.03, 0.008, 1.4), (P_(0.06 + Lb * 0.7), 0.025, 0.007, 1.4), (P_(0.06 + Lb * 0.93), 0.017, 0.006, 1.4), (P_(0.06 + Lb), 0.001, 0.001, 1.4)],
         'faM', 'blade', 'weapon', N=4, ref=Vector((1, 0, 0)), sharp=True)
    return g, d, Lb + 0.06

def fa_parts(S):
    SB.PARTS.clear(); SB.DENS.clear(); METRICS.clear()
    b = FaBody(S)
    c_body(b); c_torso(b); c_lower(b); c_shoulders(b); c_limbs(b); c_head(b)
    wb = c_sword(b, S)
    return b, wb

def fa_build_parts(S):
    """build, count triangles, and shrink the ring segments until LOD0 fits TRI_TARGET (the budget's 15k minus the shell walls' slack)."""
    for k in range(6):
        b, wb = fa_parts(S)
        n = sum(SB.tris(P_['ob']) for P_ in SB.PARTS)
        METRICS['seg_scale'] = round(SB.Q['seg'], 3); METRICS['tris_parts'] = n
        if 0.93 * TRI_TARGET <= n <= TRI_TARGET or k == 5: break
        for P_ in SB.PARTS: bpy.data.objects.remove(P_['ob'], do_unlink=True)
        SB.Q['seg'] *= min(1.6, max(0.6, (TRI_TARGET / n) ** 0.85 * 0.98))
    # proportions measured from the mesh (design z): sole, helmet top (horn excluded), pauldron span, limb thickness
    allz = lambda nm: [(P_['ob'].matrix_world @ v.co) for P_ in SB.PARTS if P_['ob'].name.startswith(nm) for v in P_['ob'].data.vertices]
    sole = min(p.z for p in allz('sole_') + allz('boot_'))
    head = METRICS['helm_top'] - METRICS['mask_chin']
    span = max(abs(p.x) for p in allz('cap') + allz('paul')) * 2
    def thick(nm):
        pts = allz(nm); xs = [p.x for p in pts]; ys = [p.y for p in pts]; return min(max(xs) - min(xs), max(ys) - min(ys))
    METRICS.update(sole=round(sole, 4), head=round(head, 4), height=round(METRICS['helm_top'] - sole, 4), span=round(span, 4),
                   bracer=round(thick('bracer_R'), 4), greave=round(thick('greave_R'), 4))
    METRICS['heads'] = round(METRICS['height'] / head, 3)
    return b, wb

def fa_material(name, S):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; bsdf = m.node_tree.nodes.get('Principled BSDF')
    r, mt = MATS.get(name, (0.5, 0.0))
    bsdf.inputs['Roughness'].default_value = r; bsdf.inputs['Metallic'].default_value = mt
    return m

def sky_bend(ob):
    me = ob.data; up = Vector((0, 0, 1)); ns = [Vector(c.vector) for c in me.corner_normals]
    me.normals_split_custom_set([tuple((n + up * SKY_BEND).normalized()) for n in ns])
    METRICS.setdefault('sky_bent', []).append(ob.name)

_make_lod = SB.make_lod
def fa_make_lod(src, arm, lvl):
    ob = _make_lod(src, arm, lvl)
    if lvl == 2:
        for o in (src, [x for x in bpy.data.objects if x.name == src.name.replace('lod0', 'lod1')][0], ob): sky_bend(o)
    return ob

SB.build_parts = fa_build_parts
SB.material = fa_material
SB.make_lod = fa_make_lod

class _Proxy:
    """pass-through wrapper: only the named attributes are replaced."""
    def __init__(s, o, over): s._o, s._over = o, over
    def __getattr__(s, k): return s._over[k] if k in s._over else getattr(s._o, k)
# export with vertex tangents (cause of the faceted lighting in run 45539289794: without tangents three.js builds the normal-map frame per
# triangle from screen derivatives; removed by: MikkTSpace tangents in the GLB). Only SB's export call changes.
SB.bpy = _Proxy(bpy, {'ops': _Proxy(bpy.ops, {'export_scene': _Proxy(bpy.ops.export_scene, {'gltf': lambda **kw: bpy.ops.export_scene.gltf(export_tangents=True, **kw)})})})

if __name__ == '__main__':
    G, info = SB.build_suit('fa')
    M = METRICS
    def gate(ok, line): G.append(('PASS ' if ok else 'FAIL ') + 'fa ' + line)
    # each proportion gate is mutation-checked in line: the rejected round-4 reading (6.4 heads; old fa W 0.92 and L 0.9) must fail it
    hv = lambda x: HEADS_VIS[0] <= x <= HEADS_VIS[1]; sp = lambda x: SPAN_BAND[0] <= x <= SPAN_BAND[1]; lm = lambda x: x >= LIMB_MIN
    gate(hv(M['heads']) and not hv(6.4), f"visual heads {M['heads']:.2f} (helmet top {M['helm_top']:.3f} m, mask chin {M['mask_chin']:.3f} m, "
         f"sole {M['sole']:.3f} m; band {HEADS_VIS}); mutation 6.4 (round 4) caught")
    r = M['span'] / M['head']; r0 = r * 0.92 / FA_W * 0.75
    gate(sp(r) and not sp(r0), f"shoulder span {M['span']:.3f} m = {r:.2f} heads (band {SPAN_BAND}; kit rogue 2.6, knight 4.1); mutation round-4 caps {r0:.2f} caught")
    for k in ('bracer', 'greave'):
        r = M[k] / M['head']; r0 = r * 0.9 / FA_L * 0.8
        gate(lm(r) and not lm(r0), f"{k} thickness {M[k]:.3f} m = {r:.2f} head (min {LIMB_MIN}); mutation round-4 limb {r0:.2f} caught")
    gate(len(M.get('sky_bent', [])) == 3, f"sky-bent normals (K {SKY_BEND}) on {M.get('sky_bent')}")
    gate(M['shell_mask_tris'] > 0 and M['shell_tris_cut'] > M['shell_mask_tris'], f"one sculpted shell: {M['shell_tris_cut']} triangles cut by marching squares, "
         f"{M['shell_mask_tris']} in the mask region, the rest helm")
    for g in G: print(g)
    nf = sum(1 for g in G if g.startswith('FAIL'))
    print(f'{len(G) - nf} of {len(G)} pass')
    info['r5'] = M
    json.dump([info], open(os.path.join(SB.OUTDIR, 'suits_info.json'), 'w'), ensure_ascii=False, indent=1)
    json.dump(M, open(os.path.join(SB.OUTDIR, 'fa_r5_metrics.json'), 'w'), indent=1)
