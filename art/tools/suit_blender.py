# Nine school suits (docs/SUITS.md) as 3D game characters: one shared humanoid base plus per-school parts, all as data.
# Study and gates: art/Qin-Lamellar-Suits-Study.md. Research: docs/research/Qin-palace-medieval-tech-fusion.md (small hard plates tied
# with a binding whose colour marks the school; layered lamellar, no mail; the nine differ in outline first, colour second).
# Construction: every part is a loft of rounded superellipse sections (round where round, sharp where sharp; no boxes). Lamellar is
# built as stacked flared rows, each row one strip of the lamellar trim sheet (32 px = 12.5 cm at 256 px/m), with cord bands between.
# Rig: rigid segments (each plate part 100% on one bone) and Blender automatic (bone heat) weights for cloth (robes, sleeves, capes),
# heat restricted to the bones each cloth part may follow. Clips: 'idle' 1 s loop and 'attack' with the kit's tell (windup >= 0.4 s);
# SUITANIM (25 Nov): 'run' loop at the kit's speed tier (IK-planted feet), 'hit' flinch 0.3 s back to idle, 'death' ending lying still.
# LOD1 and LOD2 are decimated copies of LOD0, skinned to the same rig.
# Output per suit: OUTDIR/<id>.glb (Y up, faces +Z in three.js), OUTDIR/<id>_sil.npz (projected triangles for suit_sil.py),
# gate lines PASS/FAIL. No game code is touched.
# Usage: python suit_blender.py -- OUTDIR [ids comma list | all]
import bpy, bmesh, math, sys, os, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUTDIR = ARGV[0] if ARGV else '/tmp/suits'
WANT = ARGV[1].split(',') if len(ARGV) > 1 and ARGV[1] != 'all' else None
os.makedirs(OUTDIR, exist_ok=True)

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Clip frame rate.
FPS = 60
# Idle loop length, s (study).
IDLE_S = 1.0
# Fairness rule: every attack is preceded by a tell of at least this long, s.
TELL_MIN = 0.4
# The tell must move the weapon or prop tip at least this far from rest by the end of the windup, m (readable at play size).
TIP_TRAVEL_MIN = 0.3
# Triangle budgets (min, max) per LOD (owner rules 36: characters 10-15k, low LOD; study: LOD1 2-3k, LOD2 under 1k).
BUDGET = {0: (10000, 15000), 1: (2000, 3000), 2: (300, 999)}
# Ring segments of round parts at LOD0 (torso, robes, helmets) and of limbs and small parts.
SEG_BODY, SEG_LIMB, SEG_SMALL = 32, 16, 10
# Sections inserted between two given loft sections at LOD0 (smooth Catmull-Rom resampling of centre and size), and the
# longest step allowed between sections, m.
SUBDIV, MAX_STEP = 2, 0.045
# Lamellar row height, m (one 32 px strip of the lamellar sheet at 256 px/m), how far a row flares out at its lower edge, m,
# and the superellipse exponent of lamellar rows (2 = ellipse; higher = squarer; kept low so plates read round).
LAM_H, LAM_FLARE, LAM_N = 0.125, 0.014, 2.4
# Cord band height and how far it stands proud, m.
CORD_H, CORD_OUT = 0.035, 0.006
# Faces meeting at more than this angle keep a hard edge (split normals), deg.
SHARP_DEG = 48
# Trim sheets: width px, height px, metres across (all 256 px/m). Layout written by art/tools/suit_tex.py.
SHEETS = {'sLam': (1024, 1024, 4.0), 'sBronze': (512, 512, 2.0), 'sCloth': (512, 512, 2.0)}
ROWS = {
    'sLam': {'plate_black': (0, 152), 'plate_brown': (152, 304), 'plate_cinnabar': (304, 408), 'plate_white': (408, 512),
             'lam_black': (512, 544), 'lam_brown': (544, 576), 'lam_cinnabar': (576, 608), 'lam_white': (608, 640),
             'rim': (640, 672), 'gold': (672, 704), 'silver': (704, 736),
             **{f'cord_{s}': (736 + 32 * i, 768 + 32 * i) for i, s in enumerate(['fa', 'ru', 'dao', 'mo', 'yy', 'za', 'ming', 'zh', 'nong'])}},
    'sBronze': {'plain': (0, 192), 'gold': (192, 224), 'silver': (224, 256), 'blade': (256, 320), 'rivet': (320, 352), 'dark': (352, 416),
                'mask': (416, 512)},
    'sCloth': {'cloth': (0, 512)},
}
# Silhouette cameras (viewer and game: FOV 50, pitch 40; fight framing 10.5 m = 110 px/m, wide 22 m = 52 px/m at 1920 x 1080).
CAMS = {'play_front': (0, 40, 10.5), 'play_34': (35, 40, 10.5), 'play_side': (90, 40, 10.5), 'wide_34': (35, 40, 22.0)}
LOOK_Y = 1.0
# Proportions (FIX-A, owner 25 Nov 02:2x: suits taller, about 7.5 heads, from 6.4): heights up to the chin (V_CHIN of the study scale)
# stretch by BODY_K, the head (chin to crown, and its width) scales by HEAD_K: crown 2.03 m at H 1.0 (study 1.86), head 0.27 m.
BODY_K, HEAD_K, V_CHIN = 1.118, 0.93, 1.57
# Heads-tall gate band (crown / head height).
HEADS_BAND = (7.3, 7.7)
# LOD decimation passes: target triangles.
LOD_TARGET = {1: 2600, 2: 900}
# --- Movement clips (SUITANIM, owner 25 Nov): 'run' loop, 'hit' flinch, 'death'. Keyed every frame from frame 0, in place (the game
# moves the suit). Timing from Muybridge, The Human Figure in Motion: plate 10 (athlete running, 0.042 s intervals): one stride = 10
# phases, each foot on the ground about 3 of them (duty about 0.3), a flight between steps, the landing foot a little ahead of the hip,
# push-off well behind it with the heel rising off the toe. Plate 51 (startle) gives the flinch shape only (shoulders up, arms in,
# head back); its 0.437 s interval is far slower than a hit. Plate 56 (sitting down on the ground, 0.232 s) paces the buckle.
# Run ground speed = the game's speed tier per kit (index.html CONFIG.STATS.speed Low/Mid/High 5.6/6/6.4 m/s).
SPEED = {'Low': 5.6, 'Mid': 6.0, 'High': 6.4}
# Per school run style (the game's kit tier sets the speed): cad = steps per second; duty = share of the cycle each foot is down;
# lean = spine/chest forward lean (forward per unit up); bob = extra hip drop at mid-stance, m; swing = arm swing deg (right, left;
# None keeps the carry pose of that arm); elbow = elbow bend deg (right, left); kick = heel lift in swing, m; width = foot track as a
# share of the rest stance; twist = chest counter-turn deg; out = arm spread; head = head pitch forward; sway = hip side shift, m.
# Optional per school: m0k = swing start speed as a share of the ground speed (1 = the foot leaves at ground speed, below 0 = it swings
# forward at once); kreach = stance stretch (default K_REACH); theta = heel rise deg (default THETA_MAX); ahead = landing share (default AHEAD).
RUN = {
    # 儒 君子: upright and measured, sword arm steady, bow arm swings
    'ru': dict(tier='Mid', cad=3.5, duty=0.28, lean=0.08, bob=0.03, swing=(14, 26), elbow=(60, 75), kick=0.36, width=0.6, twist=5, out=0.22, head=0.02, sway=0.012),
    # 道 真人: light and long, the most flight, loose open arms in the sleeves
    # round 3 (owner 25 Nov: "shorter, gliding stride", robe weights unchanged): short quick steps (1.07 m at 6.4 m/s), no bob, nearly straight
    # stance leg, feet tucked up under the robe in swing and swung forward from toe-off. Cause of the dip (runs 1-2: -122 / -76 mm): the robe's
    # front hem is weighted to the shins, so a shin pitched back behind the body (foot trailing low after toe-off) pulls the hem down and back.
    # Light estimate on the approved dao GLB (/home/claude/suitanim/robesim.py, 10-13 mm optimistic vs runs 1-2): robe 25-34 mm above the floor.
    # robe round (calm binding): the robe no longer follows the shins, so the high heel tuck that kept it off the floor is not needed;
    # kick 0.8 -> 0.4, m0k -0.3 -> 0.3 (feet stay under the robe; estimate: robe 45 mm above the floor, hem swing 0.151 m)
    'dao': dict(tier='High', cad=6.0, duty=0.22, lean=0.1, bob=0.0, swing=(22, 22), elbow=(50, 50), kick=0.4, width=1.0, twist=4, out=0.3, head=0.03, sway=0.006,
                m0k=0.3, kreach=0.99, theta=20.0),
    # 法 廷尉: rigid, upright, mechanical; sword held point-forward, short swing
    'fa': dict(tier='High', cad=3.6, duty=0.27, lean=0.06, bob=0.025, swing=(8, 30), elbow=(40, 85), kick=0.4, width=0.5, twist=3, out=0.18, head=0.0, sway=0.008),
    # 墨 墨守: heavy and stocky, short quick steps, low and forward, crossbow kept at the hip, wide track
    'mo': dict(tier='Low', cad=4.0, duty=0.32, lean=0.22, bob=0.02, swing=(6, 22), elbow=(70, 90), kick=0.26, width=0.85, twist=8, out=0.35, head=0.1, sway=0.02),
    # 阴阳 太极: smooth glide (least bob), both orbs held out in front, balanced
    'yy': dict(tier='Mid', cad=3.5, duty=0.28, lean=0.1, bob=0.015, swing=(14, 14), elbow=(65, 65), kick=0.34, width=0.45, twist=2, out=0.32, head=0.02, sway=0.006),
    # 杂 门客: an even all-round runner, a little loose
    'za': dict(tier='Mid', cad=3.6, duty=0.29, lean=0.13, bob=0.035, swing=(24, 34), elbow=(70, 75), kick=0.4, width=0.55, twist=8, out=0.24, head=0.03, sway=0.012),
    # 名 辩者: quick and proud, chest up, wide-swinging free arm, wheel out at the side
    'ming': dict(tier='Mid', cad=3.7, duty=0.27, lean=0.05, bob=0.04, swing=(16, 44), elbow=(40, 70), kick=0.44, width=0.5, twist=11, out=0.3, head=-0.04, sway=0.012),
    # 纵横 说客: long confident strides, shoulders turning, staff carried upright in the right hand
    'zh': dict(tier='Mid', cad=3.4, duty=0.27, lean=0.1, bob=0.035, swing=(None, 38), elbow=(None, 75), kick=0.4, width=0.55, twist=10, out=0.24, head=0.02, sway=0.012),
    # 农 耕者: sturdy and lumbering, knees bent, hoe on the shoulder, wide track
    'nong': dict(tier='Low', cad=3.9, duty=0.32, lean=0.18, bob=0.025, swing=(None, 26), elbow=(None, 85), kick=0.28, width=0.8, twist=6, out=0.3, head=0.08, sway=0.02),
}
# Landing point as a share of the contact length ahead of the hip joint (plate 10: lands a little ahead, pushes off further behind).
AHEAD = 0.42
# Heel rise at push-off: max foot pitch about the toe, deg, and the share of the contact after which the heel starts to rise.
THETA_MAX, HEEL0 = 30.0, 0.6
# Hip-to-ankle stretch allowed in stance as a share of thigh + shin (a locked knee looks wrong); the base hip drop is solved from it.
K_REACH = 0.97
# Hit flinch: length s; time to full flinch s (plate 51 shape at hit speed); hold s; strength by the kit's armour tier (heavier flinches less).
HIT_S, HIT_UP, HIT_HOLD = 0.3, 0.06, 0.04
HIT_K = {'Low': 1.0, 'Mid': 0.85, 'High': 0.7}
# Long robes (legs 'robe'): the hit's hip drop is capped here, m (round 1: dao's hem went 33 mm under the floor at 0.07 m).
HIT_ROBE_DROP = 0.02
# Death per school: fall = 'back' or 'front'; s = length (1.0 s nominal; key times scale with it).
DEATH = {'ru': dict(fall='back', s=1.0), 'dao': dict(fall='back', s=0.95), 'fa': dict(fall='front', s=0.9), 'mo': dict(fall='front', s=1.1),
         'yy': dict(fall='back', s=1.0), 'za': dict(fall='front', s=1.0), 'ming': dict(fall='back', s=0.95), 'zh': dict(fall='back', s=1.0),
         'nong': dict(fall='front', s=1.1)}
# Death key times at 1.0 s (recoil, buckle, impact, settle) and the gap kept above the floor once lying, m.
DEATH_T, LIE_GAP = (0.12, 0.42, 0.72, 0.85), 0.002
# Calm robe binding (owner 25 Nov "rebind robes calmer": dao, za, zh; meshes unchanged, only the robe's skin weights): after bone heat,
# each robe vertex's shin weight moves to the thigh of the same side, mix = share of the leg weight spread evenly over both thighs (the
# scissor cancels out), K = share of the leg weight kept (the rest goes to the hips). Estimate on the approved GLBs
# (/home/claude/suitanim/robecalm.py): hem swing per run cycle dao 0.413 -> 0.151 m, za 0.454 -> 0.210 m, zh 0.538 -> 0.220 m.
ROBE_CALM = {'dao': (0.2, 0.7), 'za': (0.4, 0.5), 'zh': (0.4, 0.5)}
# Armour tier per school (index.html kits) for HIT_K.
ARMOUR = {'ru': 'High', 'dao': 'Low', 'fa': 'Mid', 'mo': 'High', 'yy': 'Low', 'za': 'Mid', 'ming': 'Low', 'zh': 'Mid', 'nong': 'High'}

# The nine suits as data (docs/SUITS.md; outline cues and colours from the study, art/Qin-Lamellar-Suits-Study.md).
# H height scale, W shoulder width scale, G girth scale, L limb thickness scale. lac = plate lacquer (sheet rows), cord = binding row,
# cloth = cloth tint (sRGB hex), trim = inlay row on the bronze sheet. Parts name a component and its parameters.
SUITS = {
    'fa': dict(eyes=(0.55, 0.465, 0.017, 0.009, True), title='法甲 廷尉', H=1.0, W=0.92, G=0.9, L=0.9, lac='black', cord='fa', cloth='#2b2422', trim='silver',
               helm=('horn', {}), shoulders=('cap', {}), torso=('lam', {'rows': 3}), lower=('tassets', {'rows': 4, 'split': True, 'apron': True}),
               legs='greaves', arms='bracers', weapon=('jian', {'len': 0.95}), back=None,
               attack=dict(windup=0.45, strike=0.12, back=0.45, kind='thrust')),
    'ru': dict(eyes=(0.5, 0.5, 0.018, 0.008, False), title='儒甲 君子', H=1.02, W=1.1, G=1.05, L=1.05, lac='brown', cord='ru', cloth='#ddd5c3', trim='gold',
               helm=('board', {}), shoulders=('layered', {'rows': 3}), torso=('lam', {'rows': 3}), lower=('skirt', {'rows': 5}),
               legs='greaves', arms='bracers', weapon=('jian', {'len': 0.8}), back=('bowhand', {}),
               attack=dict(windup=0.5, strike=0.14, back=0.45, kind='overhead')),
    'dao': dict(eyes=(0.47, 0.52, 0.02, 0.006, False), title='道甲 真人', H=0.98, W=0.9, G=0.88, L=0.88, lac='white', cord='dao', cloth='#d9d3c4', trim='silver',
                helm=('topknot', {}), shoulders=('none', {}), torso=('lam', {'rows': 2}), lower=('robe', {'hem': 0.06, 'flare': 0.34}),
                legs='robe', arms='sleeves', weapon=None, back=None,
                attack=dict(windup=0.42, strike=0.1, back=0.45, kind='palm')),
    'mo': dict(eyes=(0.5, 0.5, 0.014, 0.011, True), title='墨甲 墨守', H=0.9, W=1.3, G=1.3, L=1.3, lac='brown', cord='mo', cloth='#6b5634', trim='gold',
               helm=('dome', {}), shoulders=('dome', {'size': 1.0}), torso=('lam', {'rows': 3}), lower=('skirt', {'rows': 2}),
               legs='greaves', arms='bracers', weapon=('crossbow', {}), back=None,
               attack=dict(windup=0.5, strike=0.1, back=0.4, kind='aim')),
    'yy': dict(eyes=(0.52, 0.48, 0.022, 0.012, False), title='阴阳甲 太极', H=1.0, W=1.0, G=0.95, L=0.92, lac='black', cord='yy', cloth='#26232a', trim='silver',
               helm=('crescent', {}), shoulders=('yinyang', {}), torso=('lam', {'rows': 2}), lower=('robe', {'hem': 0.08, 'flare': 0.08}),
               legs='robe', arms='sleeves', weapon=('orbs', {}), back=None,
               attack=dict(windup=0.6, strike=0.12, back=0.45, kind='raise')),
    'za': dict(eyes=(0.48, 0.5, 0.018, 0.007, True), title='杂甲 门客', H=1.0, W=1.0, G=1.0, L=1.0, lac='brown', cord='za', cloth='#2e5a9c', trim='gold',
               helm=('flapcap', {}), shoulders=('mixed', {}), torso=('lam', {'rows': 2}), lower=('robe', {'hem': 0.42, 'flare': 0.2}),
               legs='greaves', arms='bracers', weapon=('orb', {}), back=('slips', {}),
               attack=dict(windup=0.45, strike=0.12, back=0.45, kind='cast')),
    'ming': dict(eyes=(0.54, 0.5, 0.024, 0.005, False), title='名甲 辩者', H=1.0, W=0.95, G=0.88, L=0.88, lac='brown', cord='ming', cloth='#4a4440', trim='silver',
                 helm=('plume', {}), shoulders=('disc', {}), torso=('lam', {'rows': 3}), lower=('tassets', {'rows': 2, 'split': False}),
                 legs='greaves', arms='bracers', weapon=('wheel', {}), back=None,
                 attack=dict(windup=0.5, strike=0.1, back=0.45, kind='throw')),
    'zh': dict(eyes=(0.46, 0.53, 0.018, 0.007, False), title='纵横甲 说客', H=1.0, W=1.0, G=0.98, L=0.95, lac='black', cord='zh', cloth='#5b3f8c', trim='gold',
               helm=('twinplume', {}), shoulders=('cape', {}), torso=('lam', {'rows': 3}), lower=('robe', {'hem': 0.4, 'flare': 0.18}),
               legs='greaves', arms='bracers', weapon=('staff', {}), back=None,
               attack=dict(windup=0.45, strike=0.12, back=0.45, kind='point')),
    'nong': dict(eyes=(0.5, 0.5, 0.012, 0.012, False), title='农甲 耕者', H=0.96, W=1.15, G=1.15, L=1.15, lac='brown', cord='nong', cloth='#6e6a4a', trim='gold',
                 helm=('cone', {}), shoulders=('dome', {'size': 0.75}), torso=('lam', {'rows': 3}), lower=('skirt', {'rows': 2}),
                 legs='greaves', arms='bracers', weapon=('hoe', {}), back=('basket', {}),
                 attack=dict(windup=0.5, strike=0.14, back=0.45, kind='chop')),
}

# helpers -------------------------------------------------------------------------------------------------------------
def D(x, f, z):
    """design coords (x = the suit's own right, f forward, z up; right-handed) -> Blender (forward = -Y so the glTF faces +Z; the suit's
    right is then Blender -X, the .R side). Round 2 fix: round 1 mapped x to +X, which put the weapon in the left hand."""
    return Vector((-x, -f, z))

PARTS = []   # dicts: ob, bone, mat, kind ('rigid' | 'cloth'), allow (bones cloth heat may use)
DENS = []    # (part name, v density factor) when a part had to be squeezed into its sheet row
Q = {'seg': 1.0}

def segs(n): return max(4, int(round(n * Q['seg'] / 2)) * 2)

def ring_pts(c, ax, bx, a, b, n, N):
    out = []
    for k in range(N):
        t = 2 * math.pi * k / N
        co, si = math.cos(t), math.sin(t)
        cx = math.copysign(abs(co) ** (2 / n), co); cy = math.copysign(abs(si) ** (2 / n), si)
        out.append(c + ax * (a * cx) + bx * (b * cy))
    return out

def frames(cs, ref=None):
    n = len(cs); T = []
    for i in range(n):
        d = cs[min(i + 1, n - 1)] - cs[max(i - 1, 0)]
        T.append(d.normalized() if d.length > 1e-9 else Vector((0, 0, 1)))
    r = ref if ref is not None else (Vector((0, -1, 0)) if abs(T[0].z) > 0.7 else Vector((0, 0, 1)))
    a = T[0].cross(r)
    if a.length < 1e-6: a = T[0].cross(Vector((1, 0, 0)))
    a.normalize(); A = [a]
    for i in range(1, n):
        a = A[-1] - T[i] * A[-1].dot(T[i]); a = a.normalized() if a.length > 1e-6 else A[-1]; A.append(a)
    B = [A[i].cross(T[i]).normalized() for i in range(n)]
    return A, B

def uvmap(mat, row, um, vm, vspan, name=None):
    W, H, M = SHEETS[mat]; dens = W / M; y0, y1 = ROWS[mat][row]
    room = (y1 - y0 - 2) / dens; k = min(1.0, room / max(vspan, 1e-6))
    return (um / M, 1.0 - (y0 + 1 + vm * k * dens) / H)

def room_m(mat, row):
    W, H, M = SHEETS[mat]; y0, y1 = ROWS[mat][row]; return (y1 - y0 - 2) / (W / M)

def resample(secs):
    """Catmull-Rom through the section centres and sizes: rounder profiles along each part (round where round)."""
    if len(secs) < 2 or Q['seg'] < 1: return secs
    out = []
    for i in range(len(secs) - 1):
        p0, p1, p2, p3 = secs[max(i - 1, 0)], secs[i], secs[i + 1], secs[min(i + 2, len(secs) - 1)]
        L = (Vector(p2[0]) - Vector(p1[0])).length
        k = max(SUBDIV, int(math.ceil(L / MAX_STEP)))
        for j in range(k):
            t = j / k
            def cr(a, b, c, d): return 0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3)
            cen = tuple(cr(p0[0][q], p1[0][q], p2[0][q], p3[0][q]) for q in range(3))
            a = max(0.0, cr(p0[1], p1[1], p2[1], p3[1])) if j else p1[1]; bb = max(0.0, cr(p0[2], p1[2], p2[2], p3[2])) if j else p1[2]
            if j: a = min(a, max(p1[1], p2[1]) * 1.15); bb = min(bb, max(p1[2], p2[2]) * 1.15)
            out.append((cen, a, bb, p1[3] + (p2[3] - p1[3]) * t))
    out.append(secs[-1])
    return out

def put(name, bm, mat, bone, kind='rigid', allow=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    PARTS.append(dict(ob=ob, bone=bone, mat=mat, kind=kind, allow=allow))
    return ob

def loft(name, secs, mat, row, bone, N=None, caps=(True, True), ref=None, kind='rigid', allow=None, sharp=False, phase=0.0, flat=False, vz=False):
    """secs: list of (center (x, f, z) design, a, b, n). a = half size along the side axis, b along the second axis."""
    N = N or segs(SEG_LIMB)
    secs = resample(secs)
    cs = [D(*s[0]) for s in secs]
    # flat: horizontal rings with fixed axes (lamellar rows fold back up at the lip; a moving frame would flip and twist the band)
    A, B = ([Vector((1, 0, 0))] * len(cs), [Vector((0, -1, 0))] * len(cs)) if flat else frames(cs, ref)
    rings = []
    for i, (c, a, b, n) in enumerate(secs):
        pts = ring_pts(cs[i], A[i], B[i], a, b, n, N)
        if abs(phase) > 0: pts = pts[int(phase):] + pts[:int(phase)]
        rings.append(pts)
    # arc lengths: around (mean ring perimeter) and along (mean surface distance between rings)
    per = [sum((r[(k + 1) % N] - r[k]).length for k in range(N)) for r in rings]
    P = sum(per) / len(per)
    sv = [0.0]
    for i in range(1, len(rings)):
        sv.append(sv[-1] + sum((rings[i][k] - rings[i - 1][k]).length for k in range(N)) / N)
    if vz:   # lamellar rows: v follows height only, so one row of plates fills the sheet strip (the lip folds back onto it)
        sv = [abs(c.z - cs[0].z) for c in cs]
    vspan = max(sv)
    # long thin parts (blades, shafts, horns, plumes) run along the sheet's wrapping u axis instead, so they keep 256 px/m
    room = room_m(mat, row); swap = vspan > room and P <= room
    k = 1.0 if swap else min(1.0, room / max(vspan, 1e-6))
    if k < 0.999: DENS.append((name, k))
    def UV(uu, vv): return uvmap(mat, row, vv, uu, P, None) if swap else uvmap(mat, row, uu, vv, vspan, None)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    V = [[bm.verts.new(p) for p in r] for r in rings]
    for i in range(len(rings) - 1):
        for k in range(N):
            k2 = (k + 1) % N
            f = bm.faces.new([V[i][k], V[i][k2], V[i + 1][k2], V[i + 1][k]])
            for lp, (kk, ii) in zip(f.loops, ((k, i), (k + 1, i), (k + 1, i + 1), (k, i + 1))):
                lp[uvl].uv = UV(P * kk / N, sv[ii])
    for ci, on in ((0, caps[0]), (len(rings) - 1, caps[1])):
        if not on or secs[ci][1] < 1e-4: continue
        c = bm.verts.new(cs[ci]); r = V[ci]
        for k in range(N):
            vs = [r[k], r[(k + 1) % N], c] if ci else [r[(k + 1) % N], r[k], c]
            f = bm.faces.new(vs)
            for lp in f.loops:
                d = lp.vert.co - cs[ci]
                lp[uvl].uv = uvmap(mat, row, d.dot(A[ci]) + 1.0, d.dot(B[ci]) + min(0.5, room / 2), 1.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces: f.smooth = not sharp
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(SHARP_DEG): e.smooth = False
    return put(name, bm, mat, bone, kind, allow)

def tube(name, a, b, r0, r1, mat, row, bone, N=None, n=2.0, **kw):
    return loft(name, [(a, r0, r0, n), (b, r1, r1, n)], mat, row, bone, N=N, **kw)

def path(pts, w, mat, row, bone, name, n=2.0, N=None, **kw):
    """loft along a polyline of (x, f, z) with per-point (a, b) half sizes in w."""
    return loft(name, [(p, ab[0], ab[1], n) for p, ab in zip(pts, w)], mat, row, bone, N=N, **kw)

def bez(p0, p1, p2, k):
    return [tuple(((1 - t) ** 2) * p0[j] + 2 * (1 - t) * t * p1[j] + t * t * p2[j] for j in range(3)) for t in [i / (k - 1) for i in range(k)]]

# the shared humanoid base ----------------------------------------------------------------------------------------------
class Body:
    """measured proportions (study): crown 1.86 m at H 1.0 (6.4 heads), head 0.29 m, shoulders 0.46 m wide at W 1.0, legs 0.92 m.
    FIX-A: study heights v map to v * BODY_K below the chin and the head part by HEAD_K (crown 2.03 m, 7.5 heads at H 1.0)."""
    def __init__(s, S, body_k=None, head_k=None):
        s.S = S; H, W, G, L = S['H'], S['W'], S['G'], S['L']
        s.H, s.W, s.G, s.L = H, W, G, L
        bk = BODY_K if body_k is None else body_k; hk = HEAD_K if head_k is None else head_k; s.hk = hk
        z = lambda v: (v * bk if v <= V_CHIN else V_CHIN * bk + (v - V_CHIN) * hk) * H
        s.z = z
        s.sx = 0.2 * W                       # shoulder joint x
        s.hx = 0.095 * G                     # hip joint x
        s.zank, s.zknee, s.zhip, s.zwaist, s.zchest, s.zsh, s.zneck, s.zchin, s.zcrown = (z(v) for v in (0.09, 0.5, 0.92, 1.03, 1.3, 1.45, 1.52, 1.57, 1.86))
        s.zelb, s.zwri, s.zhand = z(1.17), z(0.91), z(0.8)

    def torso_ab(s, zz):
        """body profile (half width, half depth) at height zz (pelvis to neck), girth and shoulder scaled."""
        H, W, G = s.H, s.W, s.G
        tab = [(0.86, 0.165 * G, 0.12 * G), (0.95, 0.17 * G, 0.125 * G), (1.03, 0.15 * G, 0.115 * G), (1.2, 0.17 * max(G, W), 0.13 * G),
               (1.32, 0.195 * W, 0.14 * G), (1.44, 0.19 * W, 0.12 * G), (1.52, 0.075, 0.075)]
        zs = [s.z(t[0]) for t in tab]
        if zz <= zs[0]: return tab[0][1:]
        for i in range(len(tab) - 1):
            if zz <= zs[i + 1]:
                t = (zz - zs[i]) / (zs[i + 1] - zs[i]); t = t * t * (3 - 2 * t)
                return (tab[i][1] + (tab[i + 1][1] - tab[i][1]) * t, tab[i][2] + (tab[i + 1][2] - tab[i][2]) * t)
        return tab[-1][1:]

    def bones(s):
        sx, hx = s.sx, s.hx
        B = [('root', (0, 0, 0), (0, 0, 0.25), None), ('hips', (0, 0, s.zhip), (0, 0, s.zwaist), 'root'),
             ('spine', (0, 0, s.zwaist), (0, 0, s.z(1.24)), 'hips'), ('chest', (0, 0, s.z(1.24)), (0, 0, s.zneck), 'spine'),
             ('neck', (0, 0, s.zneck), (0, 0, s.zchin + 0.02), 'chest'), ('head', (0, 0, s.zchin + 0.02), (0, 0, s.zcrown), 'neck')]
        for side, m in (('R', 1), ('L', -1)):
            B += [(f'upper_arm.{side}', (m * sx, 0, s.zsh - 0.01), (m * (sx + 0.05), 0.0, s.zelb), 'chest'),
                  (f'forearm.{side}', (m * (sx + 0.05), 0.0, s.zelb), (m * (sx + 0.08), 0.05, s.zwri), f'upper_arm.{side}'),
                  (f'hand.{side}', (m * (sx + 0.08), 0.05, s.zwri), (m * (sx + 0.09), 0.07, s.zhand), f'forearm.{side}'),
                  (f'thigh.{side}', (m * hx, 0, s.zhip), (m * (hx + 0.01), 0.01, s.zknee), 'hips'),
                  (f'shin.{side}', (m * (hx + 0.01), 0.01, s.zknee), (m * (hx + 0.015), -0.01, s.zank), f'thigh.{side}'),
                  (f'foot.{side}', (m * (hx + 0.015), -0.01, s.zank), (m * (hx + 0.02), 0.15, 0.02), f'shin.{side}')]
        return B

    def hand(s, m):
        return (m * (s.sx + 0.085), 0.06, (s.zwri + s.zhand) / 2)

def base_parts(b, S):
    """the shared body: torso core, neck, pelvis, arms, legs, boots, hands (the suit's own pieces go over these)."""
    lac = S['lac']; L = b.L
    zs = [b.z(v) for v in (0.9, 0.97, 1.03, 1.2, 1.32, 1.42, 1.48)]
    loft('torso', [((0, 0, zz), *b.torso_ab(zz), 2.6) for zz in zs], 'sLam', f'plate_{lac}' if lac in ('black', 'brown') else 'plate_brown', 'spine', N=segs(SEG_BODY))
    tube('neck', (0, 0, b.zneck - 0.03), (0, 0, b.zchin + 0.03), 0.06, 0.055, 'sCloth', 'cloth', 'neck')
    for side, m in (('R', 1), ('L', -1)):
        sh = (m * b.sx, 0, b.zsh - 0.01); el = (m * (b.sx + 0.05), 0, b.zelb); wr = (m * (b.sx + 0.08), 0.05, b.zwri)
        if S['arms'] != 'sleeves':
            loft(f'uarm_{side}', [(sh, 0.06 * L, 0.06 * L, 2), (el, 0.05 * L, 0.05 * L, 2)], 'sCloth', 'cloth', f'upper_arm.{side}', caps=(True, False))
            loft(f'farm_{side}', [(el, 0.052 * L, 0.052 * L, 2.4), ((m * (b.sx + 0.065), 0.025, (b.zelb + b.zwri) / 2), 0.056 * L, 0.05 * L, 2.6),
                                  (wr, 0.046 * L, 0.042 * L, 2.4)], 'sLam', f'plate_{lac}', f'forearm.{side}')
        else:
            loft(f'farm_{side}', [(el, 0.045, 0.045, 2), (wr, 0.04, 0.04, 2)], 'sCloth', 'cloth', f'forearm.{side}')
        hc = b.hand(m)
        loft(f'hand_{side}', [(wr, 0.04 * L, 0.03 * L, 2.2), ((hc[0], hc[1] + 0.005, hc[2]), 0.05 * L, 0.04 * L, 2.6),
                              ((m * (b.sx + 0.09), 0.075, b.zhand), 0.035 * L, 0.03 * L, 2.4)], 'sBronze', 'dark', f'hand.{side}', N=segs(SEG_SMALL))
        hp = (m * b.hx, 0, b.zhip); kn = (m * (b.hx + 0.01), 0.01, b.zknee); an = (m * (b.hx + 0.015), -0.01, b.zank)
        if S['legs'] != 'robe':
            loft(f'thigh_{side}', [(hp, 0.09 * L, 0.09 * L, 2), (kn, 0.065 * L, 0.065 * L, 2)], 'sCloth', 'cloth', f'thigh.{side}', caps=(False, True))
            loft(f'shin_{side}', [(kn, 0.07 * L, 0.07 * L, 2.4), ((m * (b.hx + 0.012), 0.015, (b.zknee * 0.6 + b.zank * 0.4)), 0.068 * L, 0.066 * L, 2.6),
                                  (an, 0.05 * L, 0.05 * L, 2.4)], 'sLam', f'plate_{lac}', f'shin.{side}')
        loft(f'boot_{side}', [((an[0], -0.03, 0.12), 0.055 * L, 0.06 * L, 2.4), ((an[0], 0.02, 0.05), 0.06 * L, 0.08 * L, 2.6),
                              ((an[0], 0.12, 0.03), 0.045 * L, 0.045 * L, 2.4), ((an[0], 0.17, 0.02), 0.02, 0.02, 2)], 'sLam', 'plate_brown', f'foot.{side}',
             N=segs(SEG_LIMB), ref=Vector((0, 0, 1)))

def lam_rows(b, name, z_top, rows, row, bone, ab_fn, kind='rigid', allow=None, cord=None, N=None, flare=LAM_FLARE):
    """stacked lamellar rows from z_top down; ab_fn(z) -> (cx, cf, a, b); a cord band ties every second row (school binding)."""
    N = N or segs(SEG_BODY)
    for k in range(rows):
        zt = z_top - k * LAM_H; zb = zt - LAM_H
        ct, ft, at, bt = ab_fn(zt); cb, fb, ab, bb = ab_fn(zb)
        loft(f'{name}{k}', [((ct, ft, zt + 0.01), at, bt, LAM_N), ((cb, fb, zb), ab + flare, bb + flare, LAM_N),
                            ((cb, fb, zb + 0.014), ab + 0.002, bb + 0.002, LAM_N)], 'sLam', row, bone, N=N, caps=(False, False), kind=kind, allow=allow, flat=True, vz=True)
        if cord and k % 2 == 0:
            zc = zt - LAM_H * 0.35; cc, fc, ac, bc = ab_fn(zc)
            fl = flare * 0.35 + CORD_OUT
            loft(f'{name}c{k}', [((cc, fc, zc + CORD_H / 2), ac + fl, bc + fl, LAM_N), ((cc, fc, zc - CORD_H / 2), ac + fl, bc + fl, LAM_N)],
                 'sLam', cord, bone, N=N, caps=(False, False), kind=kind, allow=allow, flat=True, vz=True)

# per-school components --------------------------------------------------------------------------------------------------
def c_torso(b, S, rows):
    lac, cord = S['lac'], f"cord_{S['cord']}"
    ab = lambda zz: (0, 0, *(v + 0.012 for v in b.torso_ab(zz)))
    lam_rows(b, 'tlam', b.z(1.0) + rows * LAM_H, rows, f'lam_{lac}', 'spine', ab, cord=cord)
    # breast plate: one rounded plate over the chest, a cord collar and a broad belt (the school's binding)
    zc = b.z(1.36); a0, b0 = b.torso_ab(zc)
    loft('breast', [((0, 0.02, b.z(1.48)), a0 * 0.8, b0 * 0.85 + 0.015, 2.2), ((0, 0.03, zc), a0 + 0.02, b0 + 0.03, 2.4),
                    ((0, 0.03, b.z(1.24)), a0 * 0.95, b0 + 0.025, 2.4)], 'sLam', f'plate_{lac}', 'chest', N=segs(SEG_BODY))
    loft('collar', [((0, 0, b.zneck - 0.02), 0.1, 0.095, 2), ((0, 0, b.zneck + 0.03), 0.085, 0.08, 2)], 'sLam', cord, 'chest', N=segs(SEG_LIMB))
    a1, b1 = b.torso_ab(b.zwaist)
    loft('belt', [((0, 0, b.zwaist + 0.04), a1 + 0.03, b1 + 0.03, 2.4), ((0, 0, b.zwaist - 0.03), a1 + 0.035, b1 + 0.035, 2.4)], 'sLam', cord, 'hips', N=segs(SEG_BODY))
    loft('buckle', [((0, b1 + 0.03, b.zwaist + 0.035), 0.045, 0.015, 2), ((0, b1 + 0.04, b.zwaist - 0.035), 0.045, 0.015, 2)], 'sBronze', S['trim'], 'hips', N=segs(SEG_SMALL))

def skirt_ab(b, flare):
    def f(zz):
        t = max(0.0, (b.zwaist - zz)) / max(b.zwaist, 1e-6)
        a, bb = b.torso_ab(min(zz, b.zhip)) if zz > b.z(0.86) else b.torso_ab(b.z(0.86))
        return (0, 0, a + 0.03 + flare * t * 2.2, bb + 0.03 + flare * t * 1.6)
    return f

def c_lower(b, S, kind, p):
    lac, cord = S['lac'], f"cord_{S['cord']}"
    if kind in ('skirt', 'tassets'):
        rows = p['rows']; fl = 0.16 if kind == 'skirt' else 0.1
        legs_allow = ['hips', 'thigh.R', 'thigh.L']
        # skirts over the thighs follow the hips and thighs (cloth weights); short tassets are rigid on the hips
        k = 'cloth' if rows >= 3 else 'rigid'
        if kind == 'tassets' and p.get('split'):
            for side, m in (('R', 1), ('L', -1)):
                def ab(zz, m=m):
                    a, bb = b.torso_ab(b.z(0.86)); t = (b.zwaist - zz) / b.zwaist
                    return (m * (0.085 * b.G + 0.03 * t), 0.0, 0.095 * b.G + 0.07 * t, bb + 0.035 + 0.1 * t)
                lam_rows(b, f'tas{side}', b.zwaist + 0.02, rows, f'lam_{lac}', f'thigh.{side}' if k == 'rigid' else 'hips', ab, kind=k,
                         allow=['hips', f'thigh.{side}', f'shin.{side}'], cord=cord, N=segs(SEG_LIMB + 2))
        else:
            lam_rows(b, 'skirt', b.zwaist + 0.02, rows, f'lam_{lac}', 'hips', skirt_ab(b, fl * 0.5), kind=k, allow=legs_allow, cord=cord)
        if p.get('apron'):   # 法: a long front plate hanging between the split tassets to below the knee (concept fa_5102)
            a0, b0 = b.torso_ab(b.zwaist)
            loft('apron', [((0, b0 + 0.05, b.zwaist - 0.02), 0.09, 0.014, 3), ((0, b0 + 0.08, b.zhip - 0.1), 0.085, 0.014, 3),
                           ((0, b0 + 0.1, b.zknee - 0.06), 0.075, 0.014, 3), ((0, b0 + 0.1, b.zknee - 0.12), 0.03, 0.012, 2.4)],
                 'sLam', f'plate_{lac}', 'hips', N=segs(SEG_LIMB), ref=Vector((0, -1, 0)))
            loft('apronband', [((0, b0 + 0.068, b.zhip - 0.02), 0.092, 0.012, 3), ((0, b0 + 0.074, b.zhip - 0.06), 0.09, 0.012, 3)], 'sBronze', S['trim'], 'hips',
                 N=segs(SEG_LIMB), ref=Vector((0, -1, 0)))
    elif kind == 'robe':
        hem = b.z(p['hem']); flare = p['flare']
        zs = [b.zwaist + 0.02, b.zhip, b.z(0.7), b.z(0.45), max(hem, 0.04)]
        secs = []
        for zz in zs:
            t = max(0.0, (b.zwaist - zz) / max(b.zwaist - hem, 1e-6)); a, bb = b.torso_ab(max(zz, b.z(0.86)))
            secs.append(((0, 0.01 * t, zz), a + 0.03 + flare * t ** 1.3, bb + 0.035 + flare * 0.8 * t ** 1.3, 2.2))
        loft('robe', secs, 'sCloth', 'cloth', 'hips', N=segs(SEG_BODY + 12), caps=(False, False), kind='cloth',
             allow=['hips', 'thigh.R', 'thigh.L', 'shin.R', 'shin.L'])
        loft('robe_in', [(s[0], s[1] - 0.012, s[2] - 0.012, s[3]) for s in secs[-2:]][::-1], 'sCloth', 'cloth', 'hips', N=segs(SEG_BODY + 12),
             caps=(False, False), kind='cloth', allow=['hips', 'thigh.R', 'thigh.L', 'shin.R', 'shin.L'])
        lam_rows(b, 'waistlam', b.zwaist + 0.02, 1, f'lam_{lac}', 'hips', skirt_ab(b, 0.05), cord=cord)

def c_sleeves(b, S):
    for side, m in (('R', 1), ('L', -1)):
        sh = (m * b.sx, 0, b.zsh); el = (m * (b.sx + 0.06), 0, b.zelb); wr = (m * (b.sx + 0.1), 0.06, b.zwri + 0.02)
        loft(f'sleeve_{side}', [(sh, 0.085, 0.085, 2), (el, 0.1, 0.095, 2), ((m * (b.sx + 0.09), 0.05, b.zwri + 0.08), 0.15, 0.12, 2.2),
                                (wr, 0.17, 0.13, 2.2)], 'sCloth', 'cloth', f'upper_arm.{side}', N=segs(SEG_LIMB + 2), caps=(True, False), kind='cloth',
             allow=[f'upper_arm.{side}', f'forearm.{side}'])

def c_shoulders(b, S, kind, p):
    lac, cord = S['lac'], f"cord_{S['cord']}"
    def pauldron(side, m, rows, wide, drop, row=None, bone=None):
        row = row or f'lam_{lac}'
        def ab(zz):
            t = (b.zsh + 0.06 - zz) / (rows * LAM_H)
            return (m * (b.sx + 0.02 + 0.03 * t), 0.0, 0.08 * wide + 0.05 * t * wide, 0.085 * wide + 0.02 * t)
        lam_rows(b, f'paul{side}', b.zsh + 0.06, rows, row, bone or f'upper_arm.{side}', ab, cord=cord, N=segs(SEG_LIMB + 2), flare=LAM_FLARE * 1.4)
    def dome(side, m, size, row, name='dome'):
        c = (m * (b.sx + 0.03), 0, b.zsh + 0.02)
        loft(f'{name}{side}', [((c[0] + m * 0.01, 0, c[2] + 0.12 * size), 0.02, 0.02, 2), ((c[0] + m * 0.02, 0, c[2] + 0.07 * size), 0.13 * size, 0.13 * size, 2.2),
                               ((c[0] + m * 0.05, 0, c[2] - 0.04 * size), 0.18 * size, 0.16 * size, 2.4), ((c[0] + m * 0.06, 0, c[2] - 0.1 * size), 0.19 * size, 0.165 * size, 2.4),
                               ((c[0] + m * 0.06, 0, c[2] - 0.085 * size), 0.16 * size, 0.14 * size, 2.4)], 'sLam', row, f'upper_arm.{side}',
             N=segs(SEG_BODY), caps=(False, False), flat=True)
        loft(f'{name}rim{side}', [((c[0] + m * 0.06, 0, c[2] - 0.08 * size), 0.195 * size, 0.17 * size, 2.4),
                                  ((c[0] + m * 0.06, 0, c[2] - 0.11 * size), 0.195 * size, 0.17 * size, 2.4)], 'sBronze', S['trim'], f'upper_arm.{side}',
             N=segs(SEG_BODY), caps=(False, False))
    if kind == 'cap':
        for side, m in (('R', 1), ('L', -1)): pauldron(side, m, 2, 0.85, 0)
    elif kind == 'layered':
        for side, m in (('R', 1), ('L', -1)): pauldron(side, m, p['rows'], 1.35, 0)
    elif kind == 'dome':
        for side, m in (('R', 1), ('L', -1)): dome(side, m, 1.0 * p['size'] * 1.25, f'plate_{lac}')
    elif kind == 'yinyang':
        dome('R', 1, 1.05, 'plate_white', 'yy'); dome('L', -1, 1.05, 'plate_black', 'yy')
    elif kind == 'mixed':   # 兼儒墨: a Mohist dome on one shoulder, Confucian layered rows on the other
        dome('L', -1, 1.0, 'plate_brown'); pauldron('R', 1, 3, 1.2, 0, row='lam_black')
    elif kind == 'disc':    # 名: one big round guard on the off shoulder, the throwing arm left free
        c = (-(b.sx + 0.1), 0.0, b.zsh - 0.04)
        loft('discL', [((c[0] - 0.02, 0, c[2]), 0.26, 0.26, 2), ((c[0] - 0.06, 0, c[2]), 0.24, 0.24, 2)], 'sLam', f'plate_{lac}', 'upper_arm.L',
             N=segs(SEG_BODY + 4), ref=Vector((0, -1, 0)))
        loft('discLb', [((c[0] - 0.065, 0, c[2]), 0.1, 0.1, 2), ((c[0] - 0.09, 0, c[2]), 0.05, 0.05, 2)], 'sBronze', S['trim'], 'upper_arm.L', N=segs(SEG_LIMB))
        pauldron('R', 1, 1, 0.75, 0)
    elif kind == 'cape':    # 纵横: a cape over the left shoulder down the back (cloth); a small plate on the right
        pts = [(-b.sx * 0.9, 0.02, b.zsh + 0.06), (-b.sx * 0.6, -0.14, b.zsh - 0.05), (-b.sx * 0.2, -0.2, b.z(1.1)), (0.0, -0.24, b.z(0.75)), (0.05, -0.28, b.z(0.45))]
        w = [(0.14, 0.02), (0.22, 0.02), (0.26, 0.02), (0.3, 0.02), (0.33, 0.02)]
        path(pts, w, 'sCloth', 'cloth', 'chest', 'cape', n=2.2, N=segs(SEG_LIMB + 4), ref=Vector((0, 1, 0)), kind='cloth',
             allow=['chest', 'spine', 'hips', 'upper_arm.L'])
        pauldron('L', -1, 1, 1.0, 0)
        pauldron('R', 1, 1, 0.8, 0)

def c_helm(b, S, kind, p):
    lac, trim = S['lac'], S['trim']
    z0, zc = b.zchin, b.zcrown
    hz = lambda t: z0 + (zc - z0) * t
    # shared helmet shell and bronze face mask with dark eye slits (the suit is hard-surface armour; no skin)
    shell = [((0, -0.01, hz(-0.05)), 0.12, 0.13, 2.2), ((0, -0.01, hz(0.25)), 0.13, 0.145, 2.2), ((0, 0.0, hz(0.6)), 0.13, 0.14, 2.2),
             ((0, 0.0, hz(0.85)), 0.11, 0.12, 2.2), ((0, 0.0, hz(1.0)), 0.06, 0.065, 2), ((0, 0.0, hz(1.04)), 0.005, 0.005, 2)]
    if kind != 'cone':
        loft('helm', shell, 'sLam', f'plate_{lac}', 'head', N=segs(SEG_BODY), caps=(True, False))
    loft('mask', [((0, 0.11, hz(0.02)), 0.05, 0.035, 2.2), ((0, 0.125, hz(0.3)), 0.095, 0.045, 2.4), ((0, 0.125, hz(0.62)), 0.1, 0.045, 2.4),
                  ((0, 0.11, hz(0.75)), 0.09, 0.035, 2.2)], 'sBronze', 'mask', 'head', N=segs(SEG_LIMB))
    # eyes per school (owner rule: distinct characters, not recolours): (outer height, inner height, half length, half height) as head fractions/metres,
    # plus an optional bronze brow bar. 法 stern, 儒 level, 道 closed crescents, 墨 heavy brow, 阴阳 wide, 杂 hooded, 名 long and narrow,
    # 纵横 smiling crescents, 农 round.
    ex = S.get('eyes', (0.55, 0.465, 0.017, 0.009, False))
    for m in (1, -1):
        zo, zi, hl, hh, brow = ex
        loft(f'eye{m}', [((m * 0.088, 0.158, hz(zo)), 0.002, 0.004, 2), ((m * 0.055, 0.17, hz((zo + zi) / 2)), hl, hh, 2),
                         ((m * 0.024, 0.172, hz(zi)), 0.002, 0.004, 2)], 'sLam', 'plate_black', 'head', N=6, ref=Vector((0, -1, 0)))
        if brow:
            loft(f'brow{m}', [((m * 0.095, 0.16, hz(zo + 0.08)), 0.006, 0.008, 2), ((m * 0.05, 0.175, hz((zo + zi) / 2 + 0.1)), 0.012, 0.016, 2),
                              ((m * 0.01, 0.178, hz(zi + 0.1)), 0.006, 0.008, 2)], 'sBronze', trim, 'head', N=6, ref=Vector((0, -1, 0)))
    brim = lambda r0, r1, z, t=0.02, row=None, nm='brim': loft(nm, [((0, 0, z + t), r0, r0 * 1.05, 2), ((0, 0, z), r1, r1 * 1.05, 2), ((0, 0, z - t * 0.5), r1 * 0.98, r1 * 1.03, 2)],
                                                     'sLam', row or f'plate_{lac}', 'head', N=segs(SEG_BODY + 4), caps=(False, True))
    if kind == 'horn':      # 獬豸 law beast: one tall horn rising from the brow and hooking forward (round 2: 0.38 m above the crown)
        pts = bez((0, 0.07, hz(0.8)), (0, -0.1, hz(2.0)), (0, 0.24, hz(2.35)), 9)
        w = [(0.055, 0.07), (0.052, 0.064), (0.047, 0.056), (0.041, 0.048), (0.034, 0.04), (0.027, 0.031), (0.019, 0.022), (0.01, 0.012), (0.001, 0.001)]
        path(pts, w, 'sLam', f'plate_{lac}', 'head', 'horn', N=segs(SEG_LIMB))
        tube('hornring', (0, 0.06, hz(0.86)), (0, 0.05, hz(0.98)), 0.065, 0.06, 'sBronze', trim, 'head')
        loft('ridge', [((0, 0.13, hz(0.75)), 0.01, 0.012, 2), ((0, 0.0, hz(1.02)), 0.012, 0.02, 2), ((0, -0.13, hz(0.75)), 0.01, 0.015, 2)], 'sBronze', trim, 'head', N=6)
        for m in (1, -1):   # cheek prongs sweeping out and down from the helmet sides (concept fa_5102)
            path(bez((m * 0.12, 0.02, hz(0.6)), (m * 0.24, 0.05, hz(0.62)), (m * 0.27, 0.0, hz(0.25)), 6), [(0.022, 0.018), (0.02, 0.016), (0.017, 0.014), (0.013, 0.011),
                 (0.008, 0.007), (0.001, 0.001)], 'sBronze', trim, 'head', f'prong{m}', N=6)
        loft('nose', [((0, 0.17, hz(0.62)), 0.008, 0.01, 2), ((0, 0.18, hz(0.4)), 0.014, 0.016, 2), ((0, 0.172, hz(0.28)), 0.004, 0.006, 2)], 'sBronze', 'mask', 'head', N=6)
    elif kind == 'board':   # 儒: a tall slanted board cap (scholar's cap made in plate), rising to the back
        loft('capbase', [((0, 0, hz(0.92)), 0.085, 0.1, 2.2), ((0, -0.01, hz(1.05)), 0.075, 0.09, 2.2)], 'sLam', f'plate_{lac}', 'head', N=segs(SEG_LIMB))
        pts = bez((0, 0.07, hz(1.04)), (0, 0.0, hz(1.55)), (0, -0.2, hz(1.9)), 6)   # round 2: taller and wider board (outline cue)
        path(pts, [(0.1, 0.016)] * 6, 'sLam', 'plate_black', 'head', 'board', n=3.0, N=segs(SEG_LIMB), ref=Vector((1, 0, 0)))
        tube('pin', (-0.16, 0.0, hz(0.98)), (0.16, 0.0, hz(0.98)), 0.012, 0.012, 'sBronze', trim, 'head', N=6)
    elif kind == 'topknot': # 道: small crown over a topknot, a hairpin and two long ribbons
        tube('knot', (0, -0.02, hz(0.95)), (0, -0.02, hz(1.18)), 0.06, 0.05, 'sLam', 'plate_white', 'head')
        loft('crown', [((0, -0.02, hz(1.02)), 0.075, 0.07, 2.4), ((0, -0.02, hz(1.2)), 0.085, 0.06, 2.4), ((0, -0.02, hz(1.24)), 0.05, 0.04, 2)],
             'sBronze', trim, 'head', N=segs(SEG_LIMB))
        tube('hairpin', (-0.15, -0.02, hz(1.12)), (0.15, -0.02, hz(1.12)), 0.01, 0.01, 'sBronze', 'gold', 'head', N=6)
        for m in (1, -1):
            pts = [(m * 0.05, -0.08, hz(1.05)), (m * 0.1, -0.2, hz(0.75)), (m * 0.14, -0.26, hz(0.3)), (m * 0.17, -0.3, hz(-0.4)), (m * 0.2, -0.34, hz(-1.1))]
            path(pts, [(0.03, 0.006), (0.035, 0.006), (0.04, 0.006), (0.04, 0.006), (0.03, 0.006)], 'sCloth', 'cloth', 'head', f'ribbon{m}',
                 n=2.2, N=6, ref=Vector((0, 1, 0)), kind='cloth', allow=['head', 'neck', 'chest'])
    elif kind == 'dome':    # 墨: low wide dome with a broad brim (the wall-holder's helmet)
        brim(0.15, 0.26, hz(0.62), 0.025)
        loft('domecap', [((0, 0, hz(0.62)), 0.17, 0.18, 2.2), ((0, 0, hz(0.95)), 0.15, 0.16, 2.2), ((0, 0, hz(1.12)), 0.07, 0.075, 2), ((0, 0, hz(1.15)), 0.01, 0.01, 2)],
             'sLam', f'plate_{lac}', 'head', N=segs(SEG_BODY), caps=(True, False))
        tube('knob', (0, 0, hz(1.1)), (0, 0, hz(1.2)), 0.03, 0.02, 'sBronze', trim, 'head', N=8)
    elif kind == 'crescent':  # 阴阳: crescent horns (moon) rising out to the sides, a sun disc between them
        for m in (1, -1):
            pts = bez((m * 0.1, 0, hz(0.8)), (m * 0.42, 0, hz(1.0)), (m * 0.32, 0.0, hz(1.85)), 8)   # round 2: wider and taller moon horns
            w = [(0.05, 0.04), (0.05, 0.04), (0.046, 0.036), (0.04, 0.032), (0.032, 0.026), (0.024, 0.02), (0.014, 0.012), (0.003, 0.003)]
            path(pts, w, 'sLam', 'plate_white' if m > 0 else 'plate_black', 'head', f'moon{m}', N=segs(SEG_LIMB))
        loft('sun', [((0, 0.0, hz(1.45)), 0.14, 0.14, 2), ((0, -0.03, hz(1.45)), 0.14, 0.14, 2)], 'sBronze', 'gold', 'head', N=segs(SEG_BODY), ref=Vector((0, 0, 1)))
        tube('sunpost', (0, -0.015, hz(1.0)), (0, -0.015, hz(1.32)), 0.02, 0.018, 'sBronze', 'gold', 'head', N=6)
    elif kind == 'flapcap':  # 杂: soft retainer's cap with two side flaps hanging over the ears
        loft('capcrown', [((0, -0.01, hz(0.8)), 0.14, 0.15, 2.4), ((0, -0.02, hz(1.12)), 0.12, 0.12, 2.6), ((0, -0.03, hz(1.2)), 0.06, 0.05, 2)],
             'sLam', 'plate_black', 'head', N=segs(SEG_BODY), caps=(False, True))
        for m in (1, -1):
            pts = [(m * 0.14, -0.03, hz(1.0)), (m * 0.22, -0.04, hz(0.75)), (m * 0.26, -0.05, hz(0.35)), (m * 0.27, -0.05, hz(0.05))]
            path(pts, [(0.012, 0.06), (0.012, 0.075), (0.012, 0.085), (0.012, 0.08)], 'sLam', 'plate_black', 'head', f'flap{m}', n=2.4, N=8)
    elif kind == 'plume':   # 名: one long plume swept back and down from a crest socket
        tube('socket', (0, 0.0, hz(0.98)), (0, -0.02, hz(1.1)), 0.035, 0.03, 'sBronze', trim, 'head', N=8)
        pts = bez((0, -0.02, hz(1.08)), (0, -0.22, hz(1.65)), (0, -0.62, hz(0.75)), 8)
        w = [(0.03, 0.03), (0.06, 0.04), (0.075, 0.045), (0.08, 0.045), (0.075, 0.04), (0.06, 0.035), (0.04, 0.025), (0.008, 0.008)]
        path(pts, w, 'sLam', 'plate_white', 'head', 'plume', n=2.0, N=segs(SEG_LIMB))
    elif kind == 'twinplume':  # 纵横: two long pheasant-tail plumes rising up and back from the temples
        for m in (1, -1):
            pts = bez((m * 0.08, -0.02, hz(0.95)), (m * 0.16, -0.05, hz(1.9)), (m * 0.3, -0.32, hz(2.6)), 8)
            w = [(0.025, 0.02), (0.03, 0.02), (0.032, 0.018), (0.03, 0.016), (0.026, 0.014), (0.02, 0.012), (0.012, 0.008), (0.002, 0.002)]
            path(pts, w, 'sLam', f"cord_{S['cord']}", 'head', f'tail{m}', N=8)
        loft('band', [((0, 0, hz(0.78)), 0.135, 0.15, 2.2), ((0, 0, hz(0.7)), 0.137, 0.152, 2.2)], 'sBronze', trim, 'head', N=segs(SEG_BODY), caps=(False, False))
    elif kind == 'cone':    # 农: wide conical hat-helmet with a broad brim
        loft('helm', shell[:3], 'sLam', f'plate_{lac}', 'head', N=segs(SEG_BODY), caps=(True, False))
        loft('cone', [((0, 0, hz(1.7)), 0.01, 0.01, 2), ((0, 0, hz(1.5)), 0.07, 0.07, 2), ((0, 0, hz(0.95)), 0.28, 0.28, 2),
                      ((0, 0, hz(0.88)), 0.3, 0.3, 2), ((0, 0, hz(0.91)), 0.24, 0.24, 2)], 'sLam', 'plate_brown', 'head', N=segs(SEG_BODY + 8), caps=(False, False), flat=True)
        loft('conerim', [((0, 0, hz(0.94)), 0.285, 0.285, 2), ((0, 0, hz(0.88)), 0.305, 0.305, 2)], 'sLam', f"cord_{S['cord']}", 'head', N=segs(SEG_BODY + 8), caps=(False, False))

def weapon_bone(b, S):
    """weapon bone (child of hand.R): head at the grip, tail toward the tip at rest; parts on it are rigid."""
    return None

def c_weapon(b, S, kind, p):
    """returns (grip point, rest direction, length) for the weapon bone, or None."""
    trim = S['trim']; g = b.hand(1)
    if kind == 'jian':      # long straight bronze sword held low and forward
        L = p['len']; d = Vector((0.45, 0.6, -0.66)).normalized()   # round 2: held low, forward and out to the side (round 1 hung down and read as a cane)
        gp = Vector(g); dd = Vector((d.x, d.y, d.z))
        P_ = lambda t: tuple(gp + dd * t)
        loft('grip', [(P_(-0.1), 0.018, 0.018, 2), (P_(0.03), 0.02, 0.02, 2)], 'sLam', f"cord_{S['cord']}", 'weapon', N=6)
        loft('pommel', [(P_(-0.13), 0.03, 0.03, 2), (P_(-0.1), 0.03, 0.03, 2)], 'sBronze', trim, 'weapon', N=8)
        loft('guard', [(P_(0.03), 0.06, 0.025, 2.6), (P_(0.06), 0.05, 0.02, 2.4)], 'sBronze', trim, 'weapon', N=8, ref=Vector((1, 0, 0)))
        loft('blade', [(P_(0.06), 0.028, 0.008, 1.4), (P_(0.06 + L * 0.7), 0.024, 0.007, 1.4), (P_(0.06 + L * 0.93), 0.016, 0.006, 1.4), (P_(0.06 + L), 0.001, 0.001, 1.4)],
             'sBronze', 'blade', 'weapon', N=4, ref=Vector((1, 0, 0)), sharp=True)
        return g, d, L + 0.06
    if kind == 'crossbow':  # 连弩: repeating crossbow at the hip, box magazine on top, bow arms across the front
        d = Vector((0, 1, 0)); gp = Vector(g) + Vector((-0.06, 0.0, 0.08))
        P_ = lambda t, up=0.0, side=0.0: tuple(gp + d * t + Vector((side, 0, up)))
        loft('stock', [(P_(-0.25), 0.035, 0.05, 2.4), (P_(0.1), 0.04, 0.05, 2.6), (P_(0.55), 0.035, 0.04, 2.4)], 'sLam', 'plate_brown', 'weapon', N=8)
        loft('mag', [(P_(0.0, 0.08), 0.045, 0.03, 3), (P_(0.45, 0.1), 0.045, 0.03, 3)], 'sLam', 'plate_black', 'weapon', N=8, ref=Vector((0, 0, 1)))
        loft('lever', [(P_(-0.15, 0.06), 0.012, 0.012, 2), (P_(0.1, 0.22), 0.012, 0.012, 2)], 'sBronze', trim, 'weapon', N=6)
        bow = [P_(0.5, 0.0, x) for x in (-0.42, -0.25, 0.0, 0.25, 0.42)]
        bow = [(q[0], q[1] - abs(q[0] - gp.x) * 0.35, q[2]) for q in bow]
        path(bow, [(0.015, 0.025), (0.02, 0.03), (0.025, 0.035), (0.02, 0.03), (0.015, 0.025)], 'sLam', 'plate_black', 'weapon', 'bowarm', N=6)
        loft('trigger', [(P_(-0.05, -0.05), 0.012, 0.02, 2), (P_(-0.02, -0.11), 0.01, 0.015, 2)], 'sBronze', trim, 'weapon', N=6)
        return tuple(gp), d, 0.55
    if kind == 'hoe':       # 耒耜: a long shaft carried up over the right shoulder, the two-pronged bronze head high behind (round 2)
        d = Vector((0.12, -0.22, 1.0)).normalized(); gp = Vector(g)
        P_ = lambda t: tuple(gp + d * t)
        tube('shaft', P_(-0.25), P_(1.45), 0.024, 0.022, 'sLam', 'plate_brown', 'weapon', N=6)
        top = gp + d * 1.45
        loft('hoehead', [(tuple(top + Vector((0, 0.02, 0.02))), 0.1, 0.035, 2.4), (tuple(top + Vector((0, 0.12, -0.01))), 0.11, 0.035, 2.4)], 'sBronze', 'plain', 'weapon',
             N=8, ref=Vector((0, 0, 1)))
        for m in (1, -1):
            a = top + Vector((m * 0.07, 0.12, -0.01))
            loft(f'prong{m}', [(tuple(a), 0.024, 0.02, 2), (tuple(a + Vector((0, 0.1, -0.22))), 0.018, 0.014, 2), (tuple(a + Vector((0, 0.12, -0.34))), 0.002, 0.002, 2)],
                 'sBronze', 'blade', 'weapon', N=6, sharp=True)
        return g, d, 1.45
    if kind == 'staff':     # 节: the envoy's tall staff with three tiers of tufts
        d = Vector((0.0, 0.08, 1.0)).normalized(); gp = Vector(g)
        P_ = lambda t: tuple(gp + d * t)
        tube('pole', P_(-0.75), P_(1.35), 0.02, 0.018, 'sLam', 'plate_black', 'weapon', N=6)
        tube('finial', P_(1.35), P_(1.47), 0.03, 0.002, 'sBronze', trim, 'weapon', N=8)
        for i, t in enumerate((1.28, 1.1, 0.92)):
            loft(f'tuft{i}', [(P_(t + 0.02), 0.03, 0.03, 2), (P_(t - 0.05), 0.11, 0.11, 2), (P_(t - 0.12), 0.09, 0.09, 2), (P_(t - 0.14), 0.02, 0.02, 2)],
                 'sCloth', 'cloth', 'weapon', N=segs(SEG_LIMB))
        return g, d, 1.47
    if kind == 'wheel':     # 名: thrown bronze wheel (轮不蹍地), held out at the side, its face to the front (round 2: round 1 was edge-on)
        c = Vector(g) + Vector((0.16, 0.06, 0.05)); R = 0.32
        rp = lambda t, rr: c + Vector((math.cos(t) * rr, 0, math.sin(t) * rr))
        pts = [tuple(rp(t, R)) for t in [i * 2 * math.pi / 18 for i in range(19)]]
        path(pts, [(0.03, 0.025)] * 19, 'sBronze', 'plain', 'weapon', 'rim', N=6, ref=Vector((0, 1, 0)))
        for i in range(6):
            tube(f'spoke{i}', tuple(c), tuple(rp(i * math.pi / 3, R)), 0.012, 0.01, 'sBronze', trim, 'weapon', N=4)
        loft('hub', [(tuple(c + Vector((0, -0.04, 0))), 0.055, 0.055, 2), (tuple(c + Vector((0, 0.04, 0))), 0.055, 0.055, 2)], 'sBronze', 'plain', 'weapon', N=8)
        for k in range(8):
            t = k * math.pi / 4
            tube(f'tooth{k}', tuple(rp(t, R + 0.02)), tuple(rp(t + 0.12, R + 0.09)), 0.02, 0.002, 'sBronze', 'blade', 'weapon', N=4)
        return tuple(c), Vector((0, 0, -1)), R
    if kind in ('orb', 'orbs'):  # 杂 orb in the right hand; 阴阳 a dark orb and a light orb, one per hand
        out = None
        for side, m in ((('R', 1),) if kind == 'orb' else (('R', 1), ('L', -1))):
            c = Vector(b.hand(m)) + Vector((m * 0.02, 0.14, 0.02))
            row = 'plate_white' if (kind == 'orbs' and m < 0) else ('plate_black' if kind == 'orbs' else None)
            R_ = 0.15 if kind == 'orbs' else 0.11
            c = c + Vector((m * 0.06, 0.04, 0)) if kind == 'orbs' else c
            secs = [(tuple(c + Vector((0, 0, r * R_))), R_ * math.sqrt(max(0, 1 - r * r)) + 0.002, R_ * math.sqrt(max(0, 1 - r * r)) + 0.002, 2)
                    for r in [1 - 2 * i / 10 for i in range(11)]]
            bone = 'weapon' if m > 0 else 'hand.L'
            if row: loft(f'orb{side}', secs, 'sLam', row, bone, N=segs(SEG_LIMB))
            else: loft(f'orb{side}', secs, 'sBronze', 'plain', bone, N=segs(SEG_LIMB))
            loft(f'orbring{side}', [(tuple(c + Vector((0, 0, 0.015))), R_ + 0.025, R_ + 0.025, 2), (tuple(c - Vector((0, 0, 0.015))), R_ + 0.025, R_ + 0.025, 2)],
                 'sBronze', trim, bone, N=segs(SEG_LIMB), caps=(False, False))
            if m > 0: out = (tuple(Vector(b.hand(1))), (c - Vector(b.hand(1))).normalized(), (c - Vector(b.hand(1))).length + 0.11)
        return out
    return None

def c_back(b, S, kind, p):
    if kind == 'bowhand':   # 儒 五射: a tall recurved bow in the left hand (round 2: round 1 slung it on the back, hidden in the outline)
        g = Vector(b.hand(-1)); up = lambda t: g + Vector((-0.04 - 0.05 * abs(t) ** 2, 0.1 * (1 - t * t) + 0.04, t * 0.72))
        ts = [-1, -0.75, -0.45, -0.15, 0.15, 0.45, 0.75, 1]
        pts = [tuple(up(t)) for t in ts]
        w = [(0.012, 0.018), (0.016, 0.024), (0.02, 0.028), (0.024, 0.032), (0.024, 0.032), (0.02, 0.028), (0.016, 0.024), (0.012, 0.018)]
        path(pts, w, 'sLam', 'plate_black', 'hand.L', 'bow', N=6)
        for t in (-1, 1):
            q = up(t); tube(f'nock{t}', tuple(q), tuple(q + Vector((-0.03, 0.06, 0.06 * t))), 0.016, 0.004, 'sBronze', S['trim'], 'hand.L', N=4)
        tube('string', pts[0], pts[-1], 0.004, 0.004, 'sLam', f"cord_{S['cord']}", 'hand.L', N=4)
        tube('grip', tuple(g + Vector((-0.04, 0.14, -0.06))), tuple(g + Vector((-0.04, 0.14, 0.06))), 0.028, 0.028, 'sLam', f"cord_{S['cord']}", 'hand.L', N=6)
        loft('quiver', [((0.12, -0.2, b.z(1.55)), 0.06, 0.05, 2.2), ((0.1, -0.2, b.z(1.0)), 0.055, 0.045, 2.2)], 'sLam', 'plate_cinnabar', 'chest', N=8)
        for i in range(3):
            tube(f'arrow{i}', (0.1 + i * 0.03, -0.2, b.z(1.5)), (0.12 + i * 0.035, -0.22, b.z(1.78)), 0.006, 0.006, 'sBronze', 'plain', 'chest', N=4)
    elif kind == 'slips':   # 杂: a fan of bamboo slips on the back (the book no one could change by a word)
        for i in range(9):
            t = (i - 4) / 4 * 0.95
            base = (0.0, -0.2, b.z(1.2)); tip = (math.sin(t * 1.15) * 0.7, -0.26 - 0.05 * abs(t), b.z(1.2) + math.cos(t * 1.15) * 0.72)   # round 2: wider fan
            loft(f'slip{i}', [(base, 0.025, 0.006, 3), (tip, 0.03, 0.006, 3)], 'sLam', 'plate_brown' if i % 2 else 'plate_cinnabar', 'chest', N=4,
                 ref=Vector((0, 1, 0)))
        for r in (0.36, 0.58):
            pts = [(math.sin((i - 4) / 4 * 0.95 * 1.15) * r, -0.27, b.z(1.2) + math.cos((i - 4) / 4 * 0.95 * 1.15) * r) for i in range(9)]
            path(pts, [(0.008, 0.008)] * 9, 'sLam', f"cord_{S['cord']}", 'chest', f'slipcord{r}', N=4)
    elif kind == 'basket':  # 农: seed basket on the back
        loft('basket', [((0, -0.26, b.z(1.48)), 0.17, 0.12, 2.6), ((0, -0.27, b.z(1.3)), 0.16, 0.11, 2.6), ((0, -0.25, b.z(1.05)), 0.12, 0.08, 2.4),
                        ((0, -0.22, b.z(1.0)), 0.06, 0.04, 2)], 'sLam', 'plate_brown', 'chest', N=segs(SEG_LIMB + 2), caps=(True, True))
        loft('basketrim', [((0, -0.26, b.z(1.5)), 0.175, 0.125, 2.6), ((0, -0.26, b.z(1.45)), 0.175, 0.125, 2.6)], 'sLam', 'plate_brown', 'chest', N=segs(SEG_LIMB + 2),
             caps=(False, False))
        for i in range(3):
            tube(f'sprout{i}', (-0.08 + i * 0.08, -0.26, b.z(1.48)), (-0.1 + i * 0.1, -0.28, b.z(1.62 + 0.04 * (i % 2))), 0.012, 0.004, 'sLam', 'cord_nong', 'chest', N=4)

# the attack clips: windup -> strike -> back to rest; poses as bone directions (design coords) ----------------------------------
def poses(kind, b):
    """returns (windup pose, strike pose); a pose maps bone -> design direction, plus 'hips' (dx, df, dz) offset."""
    if kind == 'thrust':
        return ({'chest': (0, -0.15, 1), 'upper_arm.R': (0.35, -0.75, -0.35), 'forearm.R': (0.1, 0.4, -0.3), 'weapon': (-0.15, 1, 0.05), 'hips': (0, -0.05, -0.04),
                 'upper_arm.L': (-0.2, 0.35, -0.8)},
                {'chest': (0, 0.35, 1), 'upper_arm.R': (0.1, 1, -0.05), 'forearm.R': (0.0, 1, 0.0), 'weapon': (0, 1, -0.05), 'hips': (0, 0.18, -0.08),
                 'upper_arm.L': (-0.25, -0.25, -1)})   # round 3: the off arm swings down and back (round 2 stuck out sideways)
    if kind == 'overhead':
        return ({'chest': (0, -0.2, 1), 'upper_arm.R': (0.2, -0.1, 1), 'forearm.R': (0.05, -0.4, 1), 'weapon': (0, -0.7, 0.5), 'hips': (0, -0.04, -0.03),
                 'upper_arm.L': (-0.1, 0.1, 1), 'forearm.L': (0.2, -0.4, 1)},
                {'chest': (0, 0.4, 1), 'upper_arm.R': (0.1, 1, -0.2), 'forearm.R': (0.0, 1, -0.4), 'weapon': (0, 0.6, -1), 'hips': (0, 0.12, -0.08),
                 'upper_arm.L': (0, 1, -0.3), 'forearm.L': (0.2, 1, -0.4)})
    if kind == 'palm':
        return ({'chest': (0, -0.1, 1), 'upper_arm.R': (0.4, -0.6, -0.5), 'forearm.R': (0.2, 0.5, 0.6), 'hand.R': (0, 0.3, 1), 'upper_arm.L': (-0.5, 0.6, -0.2),
                 'forearm.L': (-0.1, 1, 0.3), 'hips': (0, -0.04, -0.06)},
                {'chest': (0, 0.3, 1), 'upper_arm.R': (0.05, 1, 0.05), 'forearm.R': (0, 1, 0.1), 'hand.R': (0, 0.2, 1), 'upper_arm.L': (-0.4, -0.3, -0.7),
                 'hips': (0, 0.15, -0.06)})
    if kind == 'aim':
        return ({'chest': (0, -0.05, 1), 'upper_arm.R': (0.25, 0.75, -0.2), 'forearm.R': (0.0, 1, 0.05), 'weapon': (0, 1, 0.15), 'upper_arm.L': (-0.2, 0.8, -0.2),
                 'forearm.L': (0.3, 1, 0.1), 'hips': (0, -0.03, -0.06)},
                {'chest': (0, -0.15, 1), 'upper_arm.R': (0.25, 0.6, 0.0), 'forearm.R': (0.0, 1, 0.35), 'weapon': (0, 1, 0.45), 'upper_arm.L': (-0.2, 0.7, 0.0),
                 'forearm.L': (0.3, 1, 0.4), 'hips': (0, -0.08, -0.04)})
    if kind == 'raise':
        return ({'chest': (0, -0.15, 1), 'upper_arm.R': (0.35, 0.0, 1), 'forearm.R': (0.1, 0.1, 1), 'upper_arm.L': (-0.35, 0.0, 1), 'forearm.L': (-0.1, 0.1, 1),
                 'weapon': (0, 0.2, 1), 'hips': (0, -0.02, -0.02)},
                {'chest': (0, 0.3, 1), 'upper_arm.R': (0.2, 1, -0.1), 'forearm.R': (0.05, 1, -0.2), 'upper_arm.L': (-0.2, 1, -0.1), 'forearm.L': (-0.05, 1, -0.2),
                 'weapon': (0, 1, -0.3), 'hips': (0, 0.1, -0.05)})
    if kind == 'cast':
        return ({'chest': (0, -0.1, 1), 'upper_arm.R': (0.6, -0.5, 0.2), 'forearm.R': (0.2, -0.3, 1), 'weapon': (0, -0.2, 1), 'upper_arm.L': (-0.3, 0.6, -0.4),
                 'hips': (0, -0.04, -0.03)},
                {'chest': (0, 0.25, 1), 'upper_arm.R': (0.15, 1, 0.1), 'forearm.R': (0.0, 1, 0.1), 'weapon': (0, 1, 0.1), 'upper_arm.L': (-0.3, -0.3, -0.7),
                 'hips': (0, 0.1, -0.05)})
    if kind == 'throw':
        return ({'chest': (0.1, -0.2, 1), 'upper_arm.R': (0.6, -0.7, 0.1), 'forearm.R': (0.2, -0.6, 0.6), 'weapon': (0.2, -0.6, 0.6), 'upper_arm.L': (-0.2, 0.9, 0.1),
                 'hips': (0, -0.05, -0.04)},
                {'chest': (-0.1, 0.35, 1), 'upper_arm.R': (0.0, 1, 0.1), 'forearm.R': (-0.1, 1, 0.0), 'weapon': (0, 1, 0.0), 'upper_arm.L': (-0.4, -0.4, -0.5),
                 'hips': (0, 0.15, -0.06)})
    if kind == 'point':
        return ({'chest': (0, -0.15, 1), 'upper_arm.R': (0.5, -0.2, 0.6), 'forearm.R': (0.2, -0.1, 1), 'weapon': (0, -0.35, 1), 'hips': (0, -0.03, -0.03),
                 'upper_arm.L': (-0.3, 0.2, -0.8)},
                {'chest': (0, 0.3, 1), 'upper_arm.R': (0.1, 1, 0.2), 'forearm.R': (0.0, 1, 0.1), 'weapon': (0, 1, 0.25), 'hips': (0, 0.12, -0.05)})
    if kind == 'chop':
        return ({'chest': (0, -0.25, 1), 'upper_arm.R': (0.2, -0.2, 1), 'forearm.R': (0.0, -0.4, 1), 'weapon': (0, -0.9, 0.4), 'upper_arm.L': (-0.1, -0.1, 1),
                 'forearm.L': (0.2, -0.3, 1), 'hips': (0, -0.04, -0.04)},
                {'chest': (0, 0.45, 1), 'upper_arm.R': (0.1, 1, -0.3), 'forearm.R': (0.0, 1, -0.5), 'weapon': (0, 0.7, -1), 'upper_arm.L': (-0.05, 1, -0.3),
                 'forearm.L': (0.15, 1, -0.5), 'hips': (0, 0.12, -0.1)})
    raise ValueError(kind)

ORDER = ['root', 'hips', 'spine', 'chest', 'neck', 'head', 'upper_arm.R', 'forearm.R', 'hand.R', 'weapon', 'upper_arm.L', 'forearm.L', 'hand.L',
         'thigh.R', 'shin.R', 'foot.R', 'thigh.L', 'shin.L', 'foot.L']

def apply_pose(arm, pose):
    """set bones to point along design directions (armature space), parents first; 'hips' offsets the hips bone."""
    for n in ORDER:
        if n not in arm.pose.bones: continue
        pb = arm.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion(); pb.location = (0, 0, 0)
    bpy.context.view_layer.update()
    if 'hips' in pose and isinstance(pose['hips'][0], (int, float)) and len(pose['hips']) == 3 and pose.get('_hips_offset', True):
        pass
    for n in ORDER:
        if n == 'hips' and 'hips_dir' in pose and 'hips' in arm.pose.bones:   # SUITANIM: pelvis direction (death falls); offset below
            pb = arm.pose.bones['hips']
            if 'hips' in pose: pb.location = (pb.bone.matrix_local.to_3x3().inverted() @ D(*pose['hips'])); bpy.context.view_layer.update()
            want = D(*tuple(pose['hips_dir'])[:3]).normalized(); M0 = pb.matrix.to_3x3(); cur = (M0 @ Vector((0, 1, 0))).normalized()
            pb.rotation_quaternion = (M0.inverted() @ cur.rotation_difference(want).to_matrix() @ M0).to_quaternion()
            bpy.context.view_layer.update(); continue
        if n not in pose or n not in arm.pose.bones: continue
        pb = arm.pose.bones[n]
        if n == 'hips':
            off = D(*pose['hips'])
            pb.location = (pb.bone.matrix_local.to_3x3().inverted() @ off)
            bpy.context.view_layer.update(); continue
        want = D(*tuple(pose[n])[:3]).normalized()
        M0 = pb.matrix.to_3x3()        # current (rotation identity) armature-space basis
        cur = (M0 @ Vector((0, 1, 0))).normalized()
        R = cur.rotation_difference(want).to_matrix()
        if len(pose[n]) > 3 and pose[n][3]: R = Quaternion(want, math.radians(pose[n][3])).to_matrix() @ R   # SUITANIM: twist about the bone (run chest)
        L = M0.inverted() @ R @ M0
        pb.rotation_quaternion = L.to_quaternion()
        bpy.context.view_layer.update()

def key_all(arm, f):
    for pb in arm.pose.bones:
        pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)

def make_clip(arm, name, keys):
    """keys: list of (frame, pose dict)."""
    arm.animation_data_create(); act = bpy.data.actions.new(name); arm.animation_data.action = act
    for f, pose in keys:
        apply_pose(arm, pose); key_all(arm, f)
    tr = arm.animation_data.nla_tracks.new(); tr.name = name; tr.strips.new(name, 1, act)
    arm.animation_data.action = None
    apply_pose(arm, {})

def tip_world(arm, bone):
    pb = arm.pose.bones[bone]; return arm.matrix_world @ pb.tail

# movement clips (SUITANIM) ---------------------------------------------------------------------------------------------------
def smooth(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)

def herm(p0, p1, m0, m1, s):
    return (2 * s ** 3 - 3 * s * s + 1) * p0 + (s ** 3 - 2 * s * s + s) * m0 + (-2 * s ** 3 + 3 * s * s) * p1 + (s ** 3 - s * s) * m1

def rotfz(v, th):
    """turn a design vector in the forward-up plane: positive th pitches a toe down (the heel rises)."""
    c, s = math.cos(math.radians(th)), math.sin(math.radians(th))
    return Vector((v.x, v.y * c + v.z * s, -v.y * s + v.z * c))

def slerp_dir(a, b, u):
    a, b = Vector(a).normalized(), Vector(b).normalized(); d = max(-1.0, min(1.0, a.dot(b))); w = math.acos(d)
    if w < 1e-4: return (a * (1 - u) + b * u).normalized()
    return ((a * math.sin((1 - u) * w) + b * math.sin(u * w)) / math.sin(w)).normalized()

def leg_ik(hip, ank, Lt, Ls, pole):
    """two-bone leg in design coords: (thigh dir, shin dir, clamped?) with the knee bent toward pole."""
    d = ank - hip; dist = d.length; reach = Lt + Ls
    dc = min(max(dist, abs(Lt - Ls) + 1e-4), reach * 0.9995); u = d.normalized()
    w = pole - u * pole.dot(u); w.normalize()
    ca = max(-1.0, min(1.0, (Lt * Lt + dc * dc - Ls * Ls) / (2 * Lt * dc))); sa = math.sqrt(1 - ca * ca)
    knee = hip + (u * ca + w * sa) * Lt
    return (knee - hip).normalized(), (hip + u * dc - knee).normalized(), dist > reach * 0.9995

def posed_dirs(arm):
    """every deform bone's current direction in design coords ('hips' stored as 'hips_dir')."""
    out = {}
    for pb in arm.pose.bones:
        if pb.name == 'root': continue
        d = (pb.tail - pb.head).normalized(); out['hips_dir' if pb.name == 'hips' else pb.name] = Vector((-d.x, -d.y, d.z))
    return out

def snap(arm):
    return {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in arm.pose.bones}

def lowest(lods):
    """lowest evaluated vertex z over all LODs (current pose, no animation playing)."""
    dg = bpy.context.evaluated_depsgraph_get(); m = 1e9
    for ob in lods:
        ev = ob.evaluated_get(dg); me = ev.to_mesh(); co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co)
        m = min(m, float(co[2::3].min()) + ob.matrix_world.translation.z); ev.to_mesh_clear()
    return m

def lift_hips(arm, dz):
    pb = arm.pose.bones['hips']; pb.location = pb.location + pb.bone.matrix_local.to_3x3().inverted() @ Vector((0, 0, dz))
    bpy.context.view_layer.update()

def keyed_clip(arm, name, snaps):
    """key one snapshot per frame from frame 0 (quaternion signs kept continuous) and push the action to its own NLA track."""
    act = bpy.data.actions.new(name); arm.animation_data.action = act; prev = {}
    for f, sn in enumerate(snaps):
        for pb in arm.pose.bones:
            q, loc = sn[pb.name]; q = q.copy()
            if pb.name in prev and prev[pb.name].dot(q) < 0: q.negate()
            prev[pb.name] = q; pb.rotation_quaternion = q; pb.location = loc
        key_all(arm, f)
    tr = arm.animation_data.nla_tracks.new(); tr.name = name; tr.strips.new(name, 0, act)
    tr.mute = True   # round 2: an unmuted new track overrode the pose while the next clip was authored (round 1 hit started from a run pose)
    arm.animation_data.action = None

class Legs:
    """leg data in design coords from the rig and the rest mesh: hip joints, bone lengths, ankle, toe pivot (front of the sole)."""
    def __init__(s, b, lod0):
        bones = {n: (Vector(h), Vector(t)) for n, h, t, p in b.bones()}
        s.L = {}
        co = {v.index: Vector((-v.co.x, -v.co.y, v.co.z)) for v in lod0.data.vertices}
        for side, m in (('R', 1), ('L', -1)):
            hip, knee = bones[f'thigh.{side}']; ank = bones[f'shin.{side}'][1]; toe = bones[f'foot.{side}'][1]
            gi = lod0.vertex_groups[f'foot.{side}'].index
            fv = [co[v.index] for v in lod0.data.vertices if any(g.group == gi and g.weight >= 0.99 for g in v.groups)]
            zmin = min(p.z for p in fv)
            # round 2: rolling contact. For each heel-rise angle, the lowest point of the turned foot (relative to the ankle) and the front-most
            # point at that height; the ankle is placed so that point is on the floor at a fixed spot (round 1 turned about one fixed toe
            # vertex and the boot nose in front of it went 6-21 mm under the floor)
            # round 3: the round-2 'lowest point held' let the contact jump from mid-sole (+0.05 m) to the boot nose (+0.15 m) at about 12 deg,
            # so the foot slid back 13-15 cm per cycle (run 45518008969). Now the sole's lower hull (forward, up; relative to the ankle) rolls
            # without slipping: turn about one hull vertex until the next one meets the floor, then switch (world contact advances by the chord).
            rel = sorted(set((round(p.y - ank.y, 6), round(p.z - ank.z, 6)) for p in fv)); lo = []
            for q in rel:
                while len(lo) >= 2 and (lo[-1][0] - lo[-2][0]) * (q[1] - lo[-2][1]) - (lo[-1][1] - lo[-2][1]) * (q[0] - lo[-2][0]) <= 0: lo.pop()
                lo.append(q)
            i0 = min(range(len(lo)), key=lambda i: (round(lo[i][1], 4), -lo[i][0])); roll = [(0.0, lo[i0], 0.0)]
            for q in lo[i0 + 1:]:
                dq = (q[0] - roll[-1][1][0], q[1] - roll[-1][1][1]); a = math.degrees(math.atan2(dq[1], dq[0]))
                if a >= roll[-1][0]: roll.append((a, q, roll[-1][2] + math.hypot(*dq)))
            s.L[side] = dict(m=m, hip=hip, Lt=(knee - hip).length, Ls=(ank - knee).length, ank=ank, roll=roll,
                             fd=(toe - ank).normalized(), pole=Vector((m * 0.1, 1, 0)).normalized(), sole=zmin)

def run_clip(arm, b, sid, legs):
    R_ = RUN[sid]; v = SPEED[R_['tier']]
    N = int(round(2 * FPS / R_['cad'])); T = N / FPS; tc = R_['duty'] * T; tsw = T - tc; Lc = v * tc
    THM, AHD, KRE, M0K = R_.get('theta', THETA_MAX), R_.get('ahead', AHEAD), R_.get('kreach', K_REACH), R_.get('m0k', 1.0)
    def stance(L, tau):
        th = THM * smooth((tau / tc - HEEL0) / (1 - HEEL0))
        a, (pf, pz), off = [r for r in L['roll'] if r[0] <= th + 1e-9][-1]; f0, z0 = L['roll'][0][1]
        q = rotfz(Vector((0, pf, pz)), th)                   # active hull pivot, turned with the foot
        cf = Lc * AHD - v * tau + f0 + off                 # its floor spot (moves back at ground speed: fixed on the floor)
        return Vector((L['ank'].x * R_['width'], cf - q.y, L['ank'].z + z0 - q.z)), rotfz(L['fd'], th)
    def foot(L, tau):
        if tau <= tc: return stance(L, tau) + (True,)
        s = (tau - tc) / tsw; A0, F0 = stance(L, tc); A1, F1 = stance(L, 0)
        # heel lift: eases up off the toe (squared sine) and comes down onto the floor with some speed (plain sine), so the frame before
        # touchdown is clear of the floor instead of skimming it
        g = math.sin(math.pi * s ** 0.8); A = Vector((A0.x, herm(A0.y, A1.y, -v * tsw * M0K, -v * tsw, s), herm(A0.z, A1.z, 0, 0, s) + R_['kick'] * (g * g * (1 - s) + g * s)))
        return A, rotfz(L['fd'], THM * (1 - smooth(s))), False
    bump = lambda t: 0.5 * (1 + math.cos(2 * math.pi * (t - tc / 2) / (T / 2)))
    # base hip drop solved so the stance leg never stretches past K_REACH of thigh + shin
    drop = 0.02
    for side, ph in (('R', 0.0), ('L', T / 2)):
        L = legs.L[side]; C = (L['Lt'] + L['Ls']) * KRE
        for i in range(41):
            tau = tc * i / 40; A, _ = stance(L, tau); t = (tau + ph) % T
            dx, df = A.x - L['hip'].x, A.y - L['hip'].y; room = C * C - dx * dx - df * df
            zmax = A.z + math.sqrt(max(room, 0.0)); drop = max(drop, L['hip'].z - R_['bob'] * bump(t) - zmax)
    snaps, clamped, minhip = [], 0, 9
    for k in range(N + 1):
        t = (k % N) / FPS; ph = 2 * math.pi * t / T
        dz = -drop - R_['bob'] * bump(t); dx = R_['sway'] * math.cos(2 * math.pi * (t - tc / 2) / T)
        pose = {'hips': (dx, 0, dz), 'spine': (0, R_['lean'], 1), 'chest': (0, R_['lean'] * 1.2, 1, R_['twist'] * math.cos(ph)),
                'neck': (0, R_['lean'] * 0.4, 1), 'head': (0, R_['head'], 1)}
        for i, (side, m, sg) in enumerate((('R', 1, -1), ('L', -1, 1))):
            sw, el = R_['swing'][i], R_['elbow'][i]
            if sw is None: continue
            a = math.radians(sg * sw * math.cos(ph)); e = a + math.radians(el)
            pose[f'upper_arm.{side}'] = (m * R_['out'], math.sin(a), -math.cos(a)); pose[f'forearm.{side}'] = (m * R_['out'] * 0.3, math.sin(e), -math.cos(e))
        for side, off in (('R', 0.0), ('L', T / 2)):
            L = legs.L[side]; tau = (t - off) % T; A, fdir, st = foot(L, tau)
            hip = L['hip'] + Vector((dx, 0, dz)); th, sh, cl = leg_ik(hip, A, L['Lt'], L['Ls'], L['pole'])
            if cl and st: clamped += 1
            pose[f'thigh.{side}'], pose[f'shin.{side}'], pose[f'foot.{side}'] = th, sh, fdir
        minhip = min(minhip, legs.L['R']['hip'].z + dz)
        apply_pose(arm, pose); snaps.append(snap(arm))
    keyed_clip(arm, 'run', snaps)
    return dict(run_v=v, run_s=round(T, 6), run_frames=N, run_tc=round(tc, 4), run_drop=round(drop, 3), run_hip_min=round(minhip, 3),
                run_cad=round(2 / T, 3), run_step=round(v * T / 2, 3)), clamped

def planted(pose, legs, hips_off):
    """add IK legs to a pose that keep both feet on their rest spot and rest angle while the hips move by hips_off."""
    for side in ('R', 'L'):
        L = legs.L[side]; hip = L['hip'] + Vector(hips_off)
        th, sh, _ = leg_ik(hip, L['ank'], L['Lt'], L['Ls'], L['pole'])
        pose[f'thigh.{side}'], pose[f'shin.{side}'], pose[f'foot.{side}'] = th, sh, L['fd']
    return pose

def full_key(arm, pose):
    """a pose made complete: every bone's direction after applying it (for slerping between keys), plus the hips offset."""
    apply_pose(arm, pose); d = posed_dirs(arm); d['hips'] = tuple(pose.get('hips', (0, 0, 0))); return d

def blend(ka, kb, u):
    out = {n: slerp_dir(ka[n], kb[n], u) for n in ka if n != 'hips'}
    out['hips'] = tuple(ka['hips'][i] * (1 - u) + kb['hips'][i] * u for i in range(3)); return out

HIT_POSE = {'hips': (0, -0.05, -0.07), 'spine': (0, -0.12, 1), 'chest': (0, -0.32, 1), 'neck': (0, -0.25, 1), 'head': (0.15, -0.5, 1),
            'upper_arm.R': (0.35, 0.25, -1), 'forearm.R': (0.15, 1, 0.55), 'upper_arm.L': (-0.35, 0.25, -1), 'forearm.L': (-0.15, 1, 0.55)}

def hit_clip(arm, sid, legs):
    k = HIT_K[ARMOUR[sid]]; N = int(round(HIT_S * FPS))
    rest = full_key(arm, {}); hp = dict(HIT_POSE)
    if SUITS[sid]['legs'] == 'robe': hp['hips'] = (0, -0.03, -HIT_ROBE_DROP / k)
    peak = full_key(arm, planted(hp, legs, D0(hp['hips'])))
    snaps = []
    for f in range(N + 1):
        t = f / FPS
        e = (1 - (1 - t / HIT_UP) ** 2) if t < HIT_UP else 1.0 if t < HIT_UP + HIT_HOLD else 1 - smooth((t - HIT_UP - HIT_HOLD) / (HIT_S - HIT_UP - HIT_HOLD))
        pose = blend(rest, peak, e * k)
        apply_pose(arm, planted(pose, legs, D0(pose['hips']))); snaps.append(snap(arm))
    keyed_clip(arm, 'hit', snaps)
    return dict(hit_s=N / FPS, hit_k=k)

def D0(off):
    """a design-coords hips offset as a Vector (x, f, z); leg data is in design coords too."""
    return Vector(off)

def death_poses(fall):
    """key poses (design directions, absolute): recoil, buckle, impact, settle; 'hips' = hip joint offset, 'hips_dir' = pelvis direction."""
    s = 1 if fall == 'back' else -1
    recoil = {'hips': (0, -0.05, -0.08), 'spine': (0, -0.15, 1), 'chest': (0, -0.38, 1), 'neck': (0, -0.3, 1), 'head': (0.1, -0.55, 1),
              'upper_arm.R': (0.6, 0.15, -0.6), 'forearm.R': (0.5, 0.5, 0.25), 'upper_arm.L': (-0.6, 0.15, -0.6), 'forearm.L': (-0.5, 0.5, 0.25)}
    if fall == 'back':
        buckle = {'hips': (0, -0.16, -0.4), 'hips_dir': (0, -0.25, 1), 'spine': (0, -0.45, 1), 'chest': (0, -0.65, 1), 'neck': (0, -0.45, 1), 'head': (0.1, -0.15, 1),
                  'upper_arm.R': (0.75, -0.2, -0.35), 'forearm.R': (0.6, 0.3, 0.3), 'upper_arm.L': (-0.75, -0.2, -0.35), 'forearm.L': (-0.6, 0.3, 0.3)}
        impact = {'hips': (0, -0.9, -0.85), 'hips_dir': (0, -1, 0.03), 'spine': (0, -1, 0.0), 'chest': (0, -1, 0.0), 'neck': (0, -1, 0.12), 'head': (0.05, -1, 0.3),
                  'thigh.R': (0.06, 1, 0.22), 'shin.R': (0.03, 1, -0.22), 'foot.R': (0.15, 0.3, 1), 'thigh.L': (-0.06, 1, 0.22), 'shin.L': (-0.03, 1, -0.22), 'foot.L': (-0.15, 0.3, 1),
                  'upper_arm.R': (0.9, -0.35, 0.2), 'forearm.R': (0.7, 0.3, 0.25), 'upper_arm.L': (-0.9, -0.35, 0.2), 'forearm.L': (-0.7, 0.3, 0.25)}
        settle = dict(impact, **{'head': (0.35, -1, 0.0), 'neck': (0, -1, 0.04), 'thigh.R': (0.06, 1, 0.1), 'shin.R': (0.03, 1, -0.1), 'thigh.L': (-0.06, 1, 0.1),
                                 'shin.L': (-0.03, 1, -0.1), 'upper_arm.R': (0.92, -0.3, 0.0), 'forearm.R': (0.6, 0.45, -0.03), 'upper_arm.L': (-0.92, -0.3, 0.0),
                                 'forearm.L': (-0.6, 0.45, -0.03)})
    else:
        # round 2: the knees reach the floor (shins back along it), then the body falls forward over the knees (round 1 kept the feet planted and
        # interpolated to lying: the shins swept through the floor and the floor solve lifted the body up to 0.3 m, a dive in mid-air)
        buckle = {'hips': (0, 0.05, -0.5), 'hips_dir': (0, 0.2, 1), 'spine': (0, 0.4, 1), 'chest': (0, 0.6, 1), 'neck': (0, 0.7, 1), 'head': (0, 1, 0.5),
                  'thigh.R': (0.05, 0.25, -1), 'shin.R': (0.03, -1, 0.04), 'foot.R': (0.02, -1, -0.45), 'thigh.L': (-0.05, 0.25, -1), 'shin.L': (-0.03, -1, 0.04),
                  'foot.L': (-0.02, -1, -0.45),
                  'upper_arm.R': (0.2, 0.45, -1), 'forearm.R': (0.1, 0.7, -1), 'upper_arm.L': (-0.2, 0.45, -1), 'forearm.L': (-0.1, 0.7, -1)}
        impact = {'hips': (0, 0.85, -0.8), 'hips_dir': (0, 1, -0.03), 'spine': (0, 1, 0.0), 'chest': (0, 1, 0.0), 'neck': (0, 1, 0.1), 'head': (0.2, 1, 0.3),
                  'thigh.R': (0.06, -1, -0.02), 'shin.R': (0.03, -1, 0.06), 'foot.R': (0.05, -1, -0.35), 'thigh.L': (-0.06, -1, -0.02), 'shin.L': (-0.03, -1, 0.06), 'foot.L': (-0.05, -1, -0.35),
                  'upper_arm.R': (0.65, 0.75, 0.1), 'forearm.R': (0.3, 0.95, 0.1), 'upper_arm.L': (-0.65, 0.75, 0.1), 'forearm.L': (-0.3, 0.95, 0.1)}
        settle = dict(impact, **{'head': (0.6, 1, -0.05), 'neck': (0, 1, 0.02), 'upper_arm.R': (0.7, 0.7, -0.02), 'forearm.R': (0.35, 0.94, -0.03),
                                 'upper_arm.L': (-0.7, 0.7, -0.02), 'forearm.L': (-0.35, 0.94, -0.03)})
    return recoil, buckle, impact, settle

def death_clip(arm, sid, legs, lods, floor):
    Dd = DEATH[sid]; dur = Dd['s']; N = int(round(dur * FPS)); tr, tb, ti, ts = (x * dur for x in DEATH_T)
    recoil, buckle, impact, settle = death_poses(Dd['fall']); front = Dd['fall'] == 'front'
    K0 = full_key(arm, {})
    K1 = full_key(arm, planted(dict(recoil), legs, D0(recoil['hips'])))
    # lying keys: hips height solved so the lowest vertex (all LODs) rests LIE_GAP above the floor reference
    def lying(p):
        apply_pose(arm, p); lift_hips(arm, floor + LIE_GAP - lowest(lods))
        k = posed_dirs(arm); pb = arm.pose.bones['hips']; off = pb.bone.matrix_local.to_3x3() @ pb.location
        k['hips'] = (-off.x, -off.y, off.z); return k
    knees = None
    if front:
        K2 = lying(dict(buckle))                                                    # kneeling: knees on the floor
        knees = {sd: Vector((-arm.pose.bones[f'shin.{sd}'].head.x, -arm.pose.bones[f'shin.{sd}'].head.y, arm.pose.bones[f'shin.{sd}'].head.z)) for sd in ('R', 'L')}
        for p in (impact, settle): p['hips'] = pivot_hips(p, knees, legs)
    else:
        K2 = full_key(arm, planted(dict(buckle), legs, D0(buckle['hips'])))
    K4 = lying(dict(settle)); K3 = lying(dict(impact))
    # round 3: the lying contact height differs from the knee-pivot height (mo's thick body and domes: the floor solve lifted 0.343 m in one
    # step, run 45518008969); the pivot phase eases that difference in so the fall meets the lying pose without a jump
    corr = (Vector(K3['hips']) - Vector(pivot_hips(K3, knees, legs))) if front else Vector((0, 0, 0))
    snaps, lifted, lift_f = [], 0.0, -1
    for f in range(N + 1):
        t = f / FPS
        if t <= tr: pose = blend(K0, K1, 1 - (1 - t / tr) ** 2)
        elif t <= tb: pose = blend(K1, K2, smooth((t - tr) / (tb - tr)))
        elif t <= ti:
            u = (t - tb) / (ti - tb); pose = blend(K2, K3, u * u)                     # falling: accelerates
            if front: pose['hips'] = tuple(Vector(pivot_hips(pose, knees, legs)) + corr * (u * u))   # over the knees, which stay on the floor
        elif t <= ts: pose = blend(K3, K4, smooth((t - ti) / (ts - ti)))
        else: pose = dict(K4)
        if t <= (tr if front else tb): pose = planted(pose, legs, D0(pose['hips']))  # feet stay put until the legs give
        apply_pose(arm, pose)
        lo = lowest(lods)
        if t > ti: lift_hips(arm, floor + LIE_GAP - lo)                              # lying: exactly on the floor
        elif lo < floor:                                                             # never through it
            lift_hips(arm, floor - lo + 0.0005)
            if floor - lo > lifted: lifted, lift_f = floor - lo, f
        snaps.append(snap(arm))
    keyed_clip(arm, 'death', snaps)
    return dict(death_s=N / FPS, death_fall=Dd['fall'], death_lift_max=round(lifted, 3), death_lift_frame=lift_f)

def pivot_hips(p, knees, legs):
    """hip joint offset that keeps both knees where they are for the pose's thigh directions (front fall over the knees)."""
    o = Vector((0, 0, 0))
    for sd in ('R', 'L'):
        L = legs.L[sd]; o += (knees[sd] - Vector(tuple(p[f'thigh.{sd}'])).normalized() * L['Lt']) - L['hip']
    o /= 2; return (o.x, o.y, o.z)

def movement_clips(arm, b, sid, lods):
    """author run, hit and death on the shared rig (all NLA tracks muted while posing, restored after)."""
    ad = arm.animation_data; mutes = {tr.name: tr.mute for tr in ad.nla_tracks}
    for tr in ad.nla_tracks: tr.mute = True
    ad.action = None; apply_pose(arm, {})
    floor = min(min(v.co.z for v in ob.data.vertices) for ob in lods)
    legs = Legs(b, lods[0])
    info, clamped = run_clip(arm, b, sid, legs)
    info.update(hit_clip(arm, sid, legs)); info.update(death_clip(arm, sid, legs, lods, floor))
    apply_pose(arm, {})
    for tr in ad.nla_tracks: tr.mute = mutes.get(tr.name, False)
    info['floor_y'] = round(floor, 4); info['sole_R'] = round(legs.L['R']['sole'], 4)
    return info, clamped

# build -------------------------------------------------------------------------------------------------------------------
def build_parts(S):
    PARTS.clear(); DENS.clear()
    b = Body(S)
    base_parts(b, S)
    c_torso(b, S, S['torso'][1]['rows'])
    c_lower(b, S, *S['lower'])
    if S['arms'] == 'sleeves': c_sleeves(b, S)
    c_shoulders(b, S, *S['shoulders'])
    n0 = len(PARTS); c_helm(b, S, *S['helm'])
    for P_ in PARTS[n0:]:  # FIX-A: the head is HEAD_K smaller across too (its heights already follow zchin..zcrown)
        if P_['bone'] == 'head':
            for v in P_['ob'].data.vertices: v.co.x *= b.hk; v.co.y *= b.hk
    wb = c_weapon(b, S, *S['weapon']) if S['weapon'] else None
    if S['back']: c_back(b, S, *S['back'])
    return b, wb

def material(name, S):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    if name.startswith('sCloth'):
        h = S['cloth'].lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]   # sRGB -> linear (vertex/factor colours are linear)
        bsdf.inputs['Base Color'].default_value = (*c, 1); bsdf.inputs['Roughness'].default_value = 0.85
    elif name == 'sBronze':
        bsdf.inputs['Metallic'].default_value = 0.5; bsdf.inputs['Roughness'].default_value = 0.45
    else:
        bsdf.inputs['Roughness'].default_value = 0.5
    return m

def make_armature(b, sid, wb):
    bpy.ops.object.armature_add(location=(0, 0, 0)); arm = bpy.context.active_object; arm.name = f'{sid}_rig'; arm.data.name = f'{sid}_rig'
    bpy.ops.object.mode_set(mode='EDIT'); eb = arm.data.edit_bones; eb.remove(eb[0])
    for n, h, t, p in b.bones():
        e = eb.new(n); e.head = D(*h); e.tail = D(*t)
        if p: e.parent = eb[p]
        e.roll = 0
    if wb:
        g, d, L = wb; e = eb.new('weapon'); e.head = D(*g); e.tail = D(*(Vector(g) + Vector(d) * max(L, 0.2))); e.parent = eb['hand.R']
    bpy.ops.object.mode_set(mode='OBJECT')
    arm.data.bones['root'].use_deform = False
    return arm

def heat_weights(ob, arm, allow):
    """Blender automatic (bone heat) weights for one cloth part, using only the bones in allow."""
    saved = {bn.name: bn.use_deform for bn in arm.data.bones}
    for bn in arm.data.bones: bn.use_deform = bn.name in allow
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    for n, v in saved.items(): arm.data.bones[n].use_deform = v
    ok = all(v.groups and sum(g.weight for g in v.groups) > 1e-4 for v in ob.data.vertices)
    if not ok:  # bone heat found no solution for some vertices: nearest allowed bone segment gets them (reported)
        for v in ob.data.vertices:
            if v.groups and sum(g.weight for g in v.groups) > 1e-4: continue
            p = ob.matrix_world @ v.co; best = None
            for n in allow:
                bn = arm.data.bones[n]; a, c = arm.matrix_world @ bn.head_local, arm.matrix_world @ bn.tail_local
                t = max(0, min(1, (p - a).dot(c - a) / max((c - a).length_squared, 1e-9))); dd = (a + (c - a) * t - p).length
                if best is None or dd < best[0]: best = (dd, n)
            g = ob.vertex_groups.get(best[1]) or ob.vertex_groups.new(name=best[1]); g.add([v.index], 1.0, 'REPLACE')
    for m in list(ob.modifiers): ob.modifiers.remove(m)
    ob.parent = None
    return ok

def calm_weights(ob, K, mix):
    """robe round: stiffer robe binding on one robe part (see ROBE_CALM); only weights change, never positions."""
    g = {vg.index: vg.name for vg in ob.vertex_groups}
    for n in ('hips', 'thigh.R', 'thigh.L'):
        if n not in ob.vertex_groups: ob.vertex_groups.new(name=n)
    for v in ob.data.vertices:
        w = {}
        for e in v.groups: w[g[e.group]] = w.get(g[e.group], 0.0) + e.weight
        tot = sum(w.values()) or 1.0
        tR = (w.get('thigh.R', 0) + w.get('shin.R', 0)) / tot; tL = (w.get('thigh.L', 0) + w.get('shin.L', 0)) / tot; legs = tR + tL
        tR, tL = ((1 - mix) * tR + mix * legs / 2) * K, ((1 - mix) * tL + mix * legs / 2) * K
        for e in list(v.groups): ob.vertex_groups[g[e.group]].remove([v.index])
        for n, x in (('hips', 1 - tR - tL), ('thigh.R', tR), ('thigh.L', tL)):
            if x > 1e-6: ob.vertex_groups[n].add([v.index], x, 'REPLACE')

def finish_lod0(sid, S, arm):
    heat_fail = []
    for P_ in PARTS:
        ob = P_['ob']; ob.data.materials.append(material(P_['mat'] if P_['mat'] != 'sCloth' else f'sCloth_{sid}', S))
        if P_['kind'] == 'cloth':
            if not heat_weights(ob, arm, P_['allow']): heat_fail.append(ob.name)
            if sid in ROBE_CALM and ob.name in ('robe', 'robe_in'): calm_weights(ob, *ROBE_CALM[sid])
        else:
            vg = ob.vertex_groups.new(name=P_['bone']); vg.add(list(range(len(ob.data.vertices))), 1.0, 'REPLACE')
    bpy.ops.object.select_all(action='DESELECT')
    for P_ in PARTS: P_['ob'].select_set(True)
    bpy.context.view_layer.objects.active = PARTS[0]['ob']; bpy.ops.object.join()
    ob = bpy.context.active_object; ob.name = f'{sid}_lod0'; ob.data.name = f'{sid}_lod0'
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    bpy.ops.object.vertex_group_limit_total(limit=4); bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.parent = arm; md = ob.modifiers.new('arm', 'ARMATURE'); md.object = arm
    return ob, heat_fail

def tris(ob): return sum(len(p.vertices) - 2 for p in ob.data.polygons)

def make_lod(src, arm, lvl):
    me = src.data.copy(); ob = bpy.data.objects.new(src.name.replace('lod0', f'lod{lvl}'), me); bpy.context.collection.objects.link(ob)
    me.name = ob.name
    for vg in src.vertex_groups: ob.vertex_groups.new(name=vg.name)
    target = LOD_TARGET[lvl]; ratio = target / tris(src)
    for _ in range(6):
        dm = ob.modifiers.new('dec', 'DECIMATE'); dm.ratio = ratio; dm.use_collapse_triangulate = True
        bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier='dec')
        n = tris(ob)
        lo, hi = BUDGET[lvl]
        if n <= hi: break
        ratio = (hi * 0.97) / n
    bpy.context.view_layer.objects.active = ob; bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    bpy.ops.object.vertex_group_limit_total(limit=4); bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.parent = arm; md = ob.modifiers.new('arm', 'ARMATURE'); md.object = arm
    return ob

# preview colours per sheet row (sRGB; match the klad sheets' base tones, for the local preview raster only)
PREVIEW = {'plate_black': (38, 34, 34), 'plate_brown': (69, 41, 27), 'plate_cinnabar': (160, 58, 40), 'plate_white': (214, 206, 190),
           'lam_black': (44, 40, 40), 'lam_brown': (74, 45, 30), 'lam_cinnabar': (168, 62, 44), 'lam_white': (206, 198, 182),
           'rim': (120, 96, 60), 'gold': (201, 165, 74), 'silver': (191, 195, 198), 'plain': (150, 118, 66), 'blade': (190, 160, 100),
           'rivet': (130, 100, 60), 'dark': (70, 54, 36), 'mask': (160, 126, 72),
           'cord_fa': (176, 64, 44), 'cord_ru': (201, 165, 74), 'cord_dao': (228, 222, 208), 'cord_mo': (184, 134, 46), 'cord_yy': (30, 27, 26),
           'cord_za': (46, 90, 156), 'cord_ming': (191, 195, 198), 'cord_zh': (91, 63, 140), 'cord_nong': (47, 138, 92)}

def row_of(mat, v):
    W, H, M = SHEETS[mat]; y = (1 - v) * H
    for n, (y0, y1) in ROWS[mat].items():
        if y0 <= y < y1: return n
    return None

def project(ob, yaw, pitch, dist, W=1920, H=1080, cloth=(128, 128, 128)):
    """triangles of the evaluated mesh in screen pixels for the viewer camera (three.js: y up; glTF maps Blender (x, y, z) to (x, z, -y)),
    with view depth and a preview colour (row colour x Lambert from the upper left) per triangle."""
    dg = bpy.context.evaluated_depsgraph_get(); ev = ob.evaluated_get(dg); me = ev.to_mesh()
    me.calc_loop_triangles()
    co = np.array([tuple(ob.matrix_world @ v.co) for v in me.vertices], dtype=np.float64)
    tri = np.array([tuple(t.vertices) for t in me.loop_triangles], dtype=np.int64)
    uvl = me.uv_layers.active.data
    cols = []
    for t in me.loop_triangles:
        mname = me.materials[t.material_index].name
        v = sum(uvl[li].uv[1] for li in t.loops) / 3
        if mname.startswith('sCloth'): cols.append(cloth); continue
        cols.append(PREVIEW.get(row_of(mname, v % 1.0 if v < 0 or v > 1 else v), (255, 0, 255)))
    ev.to_mesh_clear()
    P = np.stack([co[:, 0], co[:, 2], -co[:, 1]], 1)
    y, p = math.radians(yaw), math.radians(pitch); look = np.array([0, LOOK_Y, 0.0])
    eye = look + np.array([math.sin(y) * math.cos(p), math.sin(p), math.cos(y) * math.cos(p)]) * dist
    fwd = look - eye; fwd /= np.linalg.norm(fwd); rt = np.cross(fwd, [0, 1, 0]); rt /= np.linalg.norm(rt); up = np.cross(rt, fwd)
    rel = P - eye; xc, yc, zc = rel @ rt, rel @ up, rel @ fwd
    f = 1 / math.tan(math.radians(25))
    sx = (xc / zc * f * (H / W)) * W / 2 + W / 2; sy = H / 2 - (yc / zc * f) * H / 2
    T = P[tri]; n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    light = np.array([-30, 60, 25.0]); light /= np.linalg.norm(light)
    lam = 0.45 + 0.55 * np.clip(n @ light, 0, 1)
    vis = (T.mean(1) - eye) @ n.T if False else None
    shade = (np.array(cols, dtype=np.float32) * lam[:, None]).clip(0, 255)
    facing = ((T.mean(1) - eye) * n).sum(1) < 0
    return dict(tri=np.stack([sx, sy], 1)[tri].astype(np.float32), depth=zc[tri].mean(1).astype(np.float32), col=shade.astype(np.uint8), front=facing)

def CLOTH(S):
    h = S['cloth'].lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def build_suit(sid):
    S = SUITS[sid]
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps = FPS
    for m in list(bpy.data.materials): bpy.data.materials.remove(m)
    b, wb = build_parts(S)
    arm = make_armature(b, sid, wb)
    lod0, heat_fail = finish_lod0(sid, S, arm)
    lods = {0: lod0, 1: make_lod(lod0, arm, 1), 2: make_lod(lod0, arm, 2)}
    # clips
    rest = {}
    A = S['attack']; fw = 1 + round(A['windup'] * FPS); fs = fw + round(A['strike'] * FPS); fb = fs + round(A['back'] * FPS)
    wind, strike = poses(A['kind'], b)
    tipbone = 'weapon' if 'weapon' in arm.pose.bones else 'hand.R'
    apply_pose(arm, {}); t0 = tip_world(arm, tipbone).copy()
    apply_pose(arm, wind); t1 = tip_world(arm, tipbone).copy()
    apply_pose(arm, strike); t2 = tip_world(arm, tipbone).copy()
    apply_pose(arm, {})
    make_clip(arm, 'attack', [(1, {}), (fw, wind), (fs, strike), (fs + 6, strike), (fb, {})])
    breathe = {'chest': (0, 0.02, 1), 'hips': (0, 0, -0.012), 'upper_arm.R': (0.2, 0.03, -1), 'upper_arm.L': (-0.2, 0.03, -1), 'head': (0, 0.04, 1)}
    fi = 1 + round(IDLE_S * FPS)
    make_clip(arm, 'idle', [(1, {}), (1 + (fi - 1) // 2, breathe), (fi, {})])
    for tr in arm.animation_data.nla_tracks: tr.mute = True
    bpy.context.view_layer.update()
    # silhouettes (rest pose) for suit_sil.py
    sil = {}
    for cam, (yaw, pitch, dist) in CAMS.items():
        for lv in ((0, 1, 2) if cam == 'wide_34' else (0,)):
            for k, v in project(lods[lv], yaw, pitch, dist, cloth=CLOTH(S)).items(): sil[f'{cam}_lod{lv}__{k}'] = v
    for tr in arm.animation_data.nla_tracks: tr.mute = tr.name != 'attack'
    bpy.context.scene.frame_set(fw); bpy.context.view_layer.update()
    for k, v in project(lod0, 35, 40, 10.5, cloth=CLOTH(S)).items(): sil[f'windup_34_lod0__{k}'] = v
    bpy.context.scene.frame_set(1)
    for tr in arm.animation_data.nla_tracks: tr.mute = False
    np.savez_compressed(os.path.join(OUTDIR, f'{sid}_sil.npz'), **sil)
    # SUITANIM: run, hit and death on the same rig (after the silhouettes, which stay rest/windup only)
    mv, clamped = movement_clips(arm, b, sid, [lods[0], lods[1], lods[2]])
    # gates
    G = []
    def gate(ok, line): G.append(('PASS ' if ok else 'FAIL ') + f'{sid} ' + line)
    for lv, ob in lods.items():
        lo, hi = BUDGET[lv]; n = tris(ob); gate(lo <= n <= hi, f'lod{lv} tris {n} (budget {lo}-{hi})')
    unw = sum(1 for v in lod0.data.vertices if not v.groups); gate(unw == 0, f'lod0 unweighted vertices {unw}')
    bad = sum(1 for v in lod0.data.vertices if abs(sum(g.weight for g in v.groups) - 1) > 0.02); gate(bad == 0, f'lod0 weight sums off 1: {bad}')
    many = max(len(v.groups) for v in lod0.data.vertices); gate(many <= 4, f'max influences {many} (glTF 4)')
    gate(not heat_fail, f'cloth heat weights solved ({len(heat_fail)} parts fell back to nearest bone: {",".join(heat_fail)[:80]})')
    nmat = len(lod0.data.materials); gate(nmat <= 3, f'materials (draw calls) {nmat} (max 3)')
    gate(A['windup'] >= TELL_MIN, f"attack tell {A['windup']:.2f} s (min {TELL_MIN})")
    trav = (t1 - t0).length; gate(trav >= TIP_TRAVEL_MIN, f'tell travel {trav:.2f} m ({tipbone} tip, rest to windup; min {TIP_TRAVEL_MIN})')
    gate(abs((fi - 1) / FPS - IDLE_S) < 1e-6, f'idle {(fi - 1) / FPS:.2f} s')
    bb = [lod0.matrix_world @ Vector(c) for c in lod0.bound_box]; h = max(c.z for c in bb)
    gate(1.7 <= h <= 2.9, f'height with crest {h:.2f} m (1.7-2.9)')
    # FIX-A proportion gate (owner: about 7.5 heads): crown / (crown - chin); the round-3 proportions must fail it (mutation)
    heads = b.zcrown / (b.zcrown - b.zchin); b3 = Body(S, 1.0, 1.0); h3 = b3.zcrown / (b3.zcrown - b3.zchin)
    gate(HEADS_BAND[0] <= heads <= HEADS_BAND[1] and not (HEADS_BAND[0] <= h3 <= HEADS_BAND[1]),
         f'{heads:.2f} heads tall (crown {b.zcrown:.2f} m, head {b.zcrown - b.zchin:.2f} m; band {HEADS_BAND}); mutation round-3 body {h3:.2f} heads caught')
    gate(clamped == 0, f"run stance legs within reach every frame ({clamped} stance frames clamped); hip drop {mv['run_drop']} m, lowest hip {mv['run_hip_min']} m, "
                       f"cycle {mv['run_s']} s ({mv['run_frames']} frames, {mv['run_cad']} steps/s, step {mv['run_step']} m) at {mv['run_v']} m/s")
    gate(mv['death_lift_max'] < 0.25, f"death floor solve: largest lift {mv['death_lift_max']} m at frame {mv['death_lift_frame']} (fall {mv['death_fall']}, {mv['death_s']:.2f} s); floor ref {mv['floor_y']} m (rest sole)")
    dmin = min([k for _, k in DENS], default=1.0); low = sorted(DENS, key=lambda d: d[1])[:4]
    gate(dmin >= 0.8, f'texel density min {dmin:.2f} of 256 px/m (min 0.8; {len(DENS)} parts squeezed; lowest {[(n, round(k, 2)) for n, k in low]})')
    # export: three LODs on one rig
    p = os.path.join(OUTDIR, f'{sid}.glb')
    bpy.ops.export_scene.gltf(filepath=p, export_format='GLB', export_animations=True, export_animation_mode='NLA_TRACKS',
                              export_materials='EXPORT', export_image_format='NONE')
    size = os.path.getsize(p)
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=p)
    sk = [o for o in bpy.data.objects if o.type == 'MESH' and o.find_armature()]
    acts = sorted(a.name for a in bpy.data.actions)
    gate(len(sk) == 3 and all(any(c in a for a in acts) for c in ('idle', 'attack', 'run', 'hit', 'death')), f'GLB re-import: {len(sk)} skinned meshes, actions {acts}, {size // 1024} KB')
    info = dict(id=sid, title=S['title'], tris={lv: tris(o) for lv, o in lods.items()} if False else None, glb_kb=size // 1024,
                tell=A['windup'], travel=round(trav, 3), strike_travel=round((t2 - t0).length, 3), height=round(h, 3), **mv)
    return G, info

if __name__ == '__main__':
    allg = []; infos = []
    for sid in (WANT or list(SUITS)):
        G, info = build_suit(sid)
        for g in G: print(g)
        allg += G; infos.append(info)
    nf = sum(1 for g in allg if g.startswith('FAIL'))
    print(f'{len(allg) - nf} of {len(allg)} pass')
    json.dump(infos, open(os.path.join(OUTDIR, 'suits_info.json'), 'w'), ensure_ascii=False, indent=1)
