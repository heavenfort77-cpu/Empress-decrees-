# 华表 pillar with a watching beast, round 1 (asset list C6; study art/Qin-Bronze-Castings-Study.md "华表 pillar"). In the palace the beast
# on top watches its room: a suit within CONFIG.PIECES.huabiao.range (3 m) wakes it; after the windup (0.5 s tell: the red ring and its
# eyes) every suit within radius 3.5 m is marked for markS 5 s, seen by all (docs/BURNING-PALACE.md "Palace pieces"). Box in index.html:
# base 1.4 x 0.4 x 1.4 m, column r 0.45 to 5.4 m, crossbar at 4.4 m, beast box at 5.7 m facing +z, eyes at 5.85 m; solid 1.4 x 1.4 m.
# Qin first: the 华表 grew from the 表木 / 诽谤木, a timber post with a cross board at a road or gate; Qin palaces sleeved timber with
# bronze 釭 fittings. Our own design: a black-lacquer timber column (the approved pillar texture A3) with three cast bronze 釭 sleeves
# (stamp bands, silver inlay rings), a bronze cloud board through the column, a turned stone plinth, a bronze dew disc on top and a
# crouching bronze beast (flame mane, swept horns, sharp claws) looking down at the room. The eye cue is inlay, not neon: the eyes are
# their own material palEye (dark bronze asleep; bright gold inlay awake, low warm emissive) on the head, a separate node pivoting at the
# neck so the game can turn it toward the passer (clip 'watch': the head dips and turns in the 0.5 s windup).
# Reference only: ComfyUI round E job 3 (run 45441170013): pick 5403 (a beast on a black column), alternates 5405 (bronze ring bands on a
# black column), 5408 (relief panels); measured on 5405: ring bands about 1.7 x the column width; on 5403: beast length about 2 x the
# column width. Nothing traced.
# Output: huabiao_lod0 (+ child huabiao_head), huabiao_lod1 (+ child huabiao_head_lod1), huabiao_lod2 (head merged); clip 'watch'.
# Usage: /home/claude/bpyenv/bin/python huabiao_blender.py OUT.glb
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector, Matrix, Euler
import prop_kit as K
from prop_kit import P, lathe, spheroid, sweep, prism, card, torus, loft, ngon, rect, blade

OUT = sys.argv[-1] if sys.argv[-1].endswith('.glb') else '/tmp/huabiao.glb'

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Triangle budgets LOD0/1/2 (asset list C6: 1.5k / 500; LOD2 far), head included.
BUDGET = (1500, 500, 200)
# Game fit: solid 1.4 x 1.4 m; the box reached about 6 m (beast top).
FOOT = 1.4
HEIGHT = (5.6, 6.6)
# Only the cloud board (above heads) may overhang the solid: below OVER_Z nothing does; above it at most OVER m.
OVER_Z, OVER = 2.2, 0.5
# Column: radius m, bottom and top z; bronze 釭 sleeves (z0, z1); band radius over the column.
COL_R, COL_Z = 0.3, (0.5, 5.0)
SLEEVES = [(0.5, 0.85), (2.55, 2.8), (4.0, 4.25)]
SLEEVE_R = 0.36
# Cloud board through the column: z, half length m, height m, thickness m.
BOARD_Z, BOARD_L, BOARD_H, BOARD_T = 4.55, 0.85, 0.32, 0.1
# Dew disc on top: radius, z.
DISC_R, DISC_Z = 0.55, 5.0
# Beast: seated on the disc facing +f (toward the camera, into the room); neck pivot (head node origin) and the eye size (study: eyes at
# least 12 cm across to read at play size).
NECK = (0.0, 0.2, 5.78)
EYE_W = 0.13
# Watch clip: windup seconds (CONFIG.PIECES.huabiao.windup 0.5) and the head's dip and turn at its end, deg.
WINDUP, DIP, TURN = 0.5, 22, 35
# Plinth: turned stone, octagonal.
PLINTH = [(0.68, 0.0), (0.68, 0.22), (0.56, 0.26), (0.56, 0.42), (0.42, 0.5), (0.0, 0.5)]


def build_pillar(detail):
    lathe('plinth', PLINTH if detail else [PLINTH[0], PLINTH[1], PLINTH[4], PLINTH[5]], 'palStone', 'plain', n=8)
    lathe('column', [(COL_R, COL_Z[0]), (COL_R, COL_Z[1])], 'palLacquer', 'wrap', n=16)  # pillar texture: u once around, 4 m per v
    for i, (z0, z1) in enumerate(SLEEVES):  # bronze sleeves: flange lips top and bottom, cloud band between, silver inlay ring
        prof = [(SLEEVE_R + 0.045, z0), (SLEEVE_R, z0 + 0.06), (SLEEVE_R, z1 - 0.06), (SLEEVE_R + 0.045, z1)] if detail else [(SLEEVE_R, z0), (SLEEVE_R, z1)]
        lathe(f'sleeve_{i}', prof, 'palBronze', [(z0, z0 + 0.06, 'flange'), (z0 + 0.06, z1 - 0.06, 'clouds'), (z1 - 0.06, z1, 'flange')], n=12)
        zc = (z0 + z1) / 2  # silver inlay ring, 6 cm (readable at play size)
        if detail: lathe(f'inlay_{i}', [(SLEEVE_R + 0.008, zc - 0.03), (SLEEVE_R + 0.008, zc + 0.03)], 'palInlay', 'plain', n=12)
    # cloud board: a flat bronze plank through the column (x), ends curled up into cloud scrolls (sharp edges)
    prism('board', rect(BOARD_T, BOARD_H), (-BOARD_L, 0, BOARD_Z), (BOARD_L, 0, BOARD_Z), 'palBronze', 'clouds', up=(0, 1, 0))
    for s in (-1, 1):
        x = s * BOARD_L
        pts = [(x, 0, BOARD_Z), (x + s * 0.16, 0, BOARD_Z + 0.08), (x + s * 0.2, 0, BOARD_Z + 0.26), (x + s * 0.1, 0, BOARD_Z + 0.34), (x + s * 0.02, 0, BOARD_Z + 0.26)]
        rad = [BOARD_H / 2, 0.13, 0.1, 0.07, 0.05]
        if not detail: pts, rad = pts[::2], rad[::2]
        sweep(f'curl_{s}', pts, rad, 'palBronze', 'flange', n=4, flat=(0.35, 1.0), rnd='flat', side=(0, 1, 0))
    # dew disc: a turned bronze dish with a flange rim, on a short neck
    lathe('disc', [(0.24, DISC_Z - 0.18), (DISC_R, DISC_Z), (DISC_R, DISC_Z + 0.08), (DISC_R - 0.05, DISC_Z + 0.1), (0.0, DISC_Z + 0.1)], 'palBronze',
          [(DISC_Z - 0.2, DISC_Z + 0.2, 'flange')], n=12)
    # beast body (seated, facing +f): haunch mass, chest, forelegs straight down to the disc with sharp claws, tail curled up the back
    zb = DISC_Z + 0.1
    loft('torso', [(zb, -0.12, 0.3, 0.32, 0.0), (zb + 0.25, -0.04, 0.32, 0.32, 0.0), (zb + 0.5, 0.08, 0.27, 0.25, 0.0), (NECK[2] - 0.08, 0.16, 0.19, 0.17, 0.0)],
         'palBronze', 'plain', n_exp=2.4, M=12)
    for s in (-1, 1):
        sweep(f'fore_{s}', [(s * 0.17, 0.22, zb + 0.42), (s * 0.18, 0.3, zb + 0.2), (s * 0.17, 0.33, zb + 0.03)], [0.11, 0.085, 0.085], 'palBronze', 'plain', n=6)
        if detail:
            for k in range(3): prism(f'claw_{s}{k}', blade(0.035, 0.03), (s * 0.15 + (k - 1) * 0.04, 0.36, zb + 0.04), (s * 0.15 + (k - 1) * 0.05, 0.47, zb + 0.0), 'palBronze', 'flange', scale_b=0.1, rnd='flat')
        spheroid(f'haunch_{s}', (s * 0.2, -0.12, zb + 0.16), (0.12, 0.22, 0.16), 'palBronze', 'plain', sg=(7, 4))
    if detail: sweep('tail', [(0.0, -0.38, zb + 0.1), (0.0, -0.5, zb + 0.35), (0.0, -0.42, zb + 0.6), (0.0, -0.3, zb + 0.66)], [0.06, 0.05, 0.04, 0.0], 'palBronze', 'flange', n=5 if detail else 4)
    if detail:  # mane tongues down the back of the neck (sharp, rows from the trim sheet)
        for k in range(5):
            a = math.radians(-60 + k * 30); c, sn = math.sin(a), math.cos(a)
            sweep(f'mane_{k}', [(c * 0.14, 0.12 - sn * 0.12, NECK[2] - 0.02), (c * 0.24, 0.05 - sn * 0.2, NECK[2] - 0.2), (c * 0.2, -sn * 0.26, NECK[2] - 0.38)],
                  [0.07, 0.05, 0.0], 'palBronze', 'flange', n=4, flat=(1.0, 0.35), rnd='flat', side=(math.cos(a), math.sin(a), 0))


def build_head(detail):
    """the head in design coords around the neck pivot NECK, looking +f and a little down into the room. Round 1b: a broad skull, short
    snout and a collar of flame tongues around the face (the round 1 draft's long snout and tall horns read as a jackal)."""
    nx, nf, nz = NECK
    loft('skull', [(nz - 0.04, nf + 0.02, 0.19, 0.16, 0.0), (nz + 0.1, nf + 0.08, 0.21, 0.17, 0.0), (nz + 0.22, nf + 0.06, 0.18, 0.14, 0.0), (nz + 0.29, nf + 0.03, 0.11, 0.09, 0.0)],
         'palBronze', 'plain', n_exp=2.4, M=10)
    sweep('snout', [(0.0, nf + 0.16, nz + 0.08), (0.0, nf + 0.27, nz + 0.05), (0.0, nf + 0.31, nz + 0.02)], [0.12, 0.1, 0.08], 'palBronze', 'plain', n=6, flat=(1.0, 0.75))
    for s in (-1, 1):
        if detail: prism(f'brow_{s}', blade(0.06, 0.045), (s * 0.02, nf + 0.24, nz + 0.17), (s * 0.18, nf + 0.17, nz + 0.23), 'palBronze', 'flange', scale_b=0.5, rnd='flat')
        # eyes: inlay almonds (palEye), EYE_W across, under the V brows, facing forward
        spheroid(f'eye_{s}', (s * 0.095, nf + 0.215, nz + 0.14), (EYE_W / 2, 0.025, 0.04), 'palEye', 'plain', sg=(6, 3))
        # short horns swept back flat along the mane (sharp)
        if detail: sweep(f'horn_{s}', [(s * 0.1, nf + 0.06, nz + 0.26), (s * 0.16, nf - 0.1, nz + 0.3), (s * 0.18, nf - 0.26, nz + 0.26)], [0.035, 0.025, 0.0], 'palBronze', 'flange', n=4, rnd='flat')
        if detail: prism(f'fang_{s}', blade(0.03, 0.025), (s * 0.05, nf + 0.29, nz - 0.01), (s * 0.05, nf + 0.3, nz - 0.1), 'palInlay', 'plain', scale_b=0.1, rnd='flat')
    # collar of flame tongues around the face (rhymes with the guardian beast's mane; sharp)
    nt = 9 if detail else 4
    for k in range(nt):
        a = math.radians(-100 + k * 200 / (nt - 1)); c, sn = math.sin(a), math.cos(a)
        b0 = (c * 0.2, nf + 0.02, nz + 0.12 + sn * 0.16); b1 = (c * 0.36, nf - 0.08, nz + 0.12 + sn * 0.3)
        sweep(f'tongue_{k}', [b0, b1], [0.08, 0.0], 'palBronze', 'flange', n=4, flat=(1.0, 0.3), rnd='flat', side=(math.cos(a), 0, -math.sin(a)))
    if detail:
        spheroid('nose', (0.0, nf + 0.33, nz + 0.05), (0.06, 0.035, 0.04), 'palBronze', 'mask', sg=(6, 3))
        prism('jaw', rect(0.16, 0.04), (0.0, nf + 0.14, nz - 0.02), (0.0, nf + 0.29, nz - 0.04), 'palDark', 'plain', rnd='flat')


def head_object(name, detail):
    build_head(detail); ob = K.finish(name, detail)
    piv = P(*NECK); ob.data.transform(Matrix.Translation(-piv)); ob.location = piv
    return ob


K.reset()
K.Q['seg'] = 0.5; build_pillar(False); lod1 = K.finish('huabiao_lod1'); h1 = head_object('huabiao_head_lod1', False)
build_pillar(False); build_head(False); lod2 = K.decimate(K.finish('huabiao_lod2'), 0.36)
K.Q['seg'] = 1.0; build_pillar(True); lod0 = K.finish('huabiao_lod0', True); h0 = head_object('huabiao_head', True)
for h, body in ((h0, lod0), (h1, lod1)): h.parent = body
h0['pivot'] = list(NECK); h0['turn'] = f'rotate about the vertical axis toward the marked suit; clip watch dips {DIP} deg and turns {TURN} deg in {WINDUP} s'
h0['eyeMaterial'] = 'palEye: asleep = dark bronze (CONFIG.PIECES.col.eyeOff), awake = gold inlay with low warm emissive (not neon)'

# watch clip (object animation on the LOD0 head): rest -> dip and turn by the end of the windup -> hold
h0.rotation_mode = 'XYZ'
for f, (dip, turn) in ((1, (0, 0)), (1 + round(WINDUP * 60), (DIP, TURN)), (1 + round(1.0 * 60), (DIP, TURN))):
    h0.rotation_euler = Euler((math.radians(dip), 0, math.radians(turn)))  # +X dips the nose (it looks along -Y), Z turns
    h0.keyframe_insert('rotation_euler', frame=f)
act = h0.animation_data.action; act.name = 'watch'
bpy.context.scene.render.fps = 60

def tri_sum(*obs): return sum(K.tris(o) for o in obs)
G = K.Gates()
for obs, lim, nm in (((lod0, h0), BUDGET[0], 'lod0 + head'), ((lod1, h1), BUDGET[1], 'lod1 + head'), ((lod2,), BUDGET[2], 'lod2')):
    G(tri_sum(*obs) <= lim, f'huabiao {nm} tris {tri_sum(*obs)} (budget {lim})')
bpy.context.view_layer.update()
(x0, x1), (y0, y1), (z0, z1) = K.bounds(lod0)
hz = max((h0.matrix_world @ v.co).z for v in h0.data.vertices)
low = [v.co for v in lod0.data.vertices if v.co.z < OVER_Z]; lw = max(abs(c.x) for c in low) * 2; ld = max(abs(c.y) for c in low) * 2
ov = max(max(abs(v.co.x), abs(v.co.y)) for v in lod0.data.vertices) - FOOT / 2
G(lw <= FOOT + 1e-6 and ld <= FOOT + 1e-6 and ov <= OVER, f'footprint below {OVER_Z} m {lw:.2f} x {ld:.2f} m (solid {FOOT} x {FOOT}); cloud board overhang above it {ov:.2f} m (max {OVER})')
G(HEIGHT[0] <= max(z1, hz) <= HEIGHT[1], f'height {max(z1, hz):.2f} m (range {HEIGHT}; box about 6 m)')
eyes = [v.co for p in h0.data.polygons if h0.data.materials[p.material_index].name == 'palEye' for v in [h0.data.vertices[i] for i in p.vertices]]
ew = (max(c.x for c in eyes) - min(c.x for c in eyes))
G('palEye' in K.mats(h0) and 'palEye' in K.mats(h1) and EYE_W >= 0.12, f'eye inlay material palEye on the LOD0 and LOD1 heads; each eye {EYE_W * 100:.0f} cm across (min 12), pair spans {ew * 100:.0f} cm')
G(h0.parent == lod0 and h1.parent == lod1 and act.frame_range[1] - act.frame_range[0] >= WINDUP * 60 - 1, f'head nodes parented to their LOD; clip watch {act.frame_range[1] - act.frame_range[0]:.0f} frames at 60 fps (windup {WINDUP} s, dip {DIP}, turn {TURN} deg)')
# the dip must show from the play camera: the eyes move down by at least 3 cm (they face the room at 40 deg pitch)
e0 = sum(eyes, Vector()) / len(eyes); R = Euler((math.radians(DIP), 0, math.radians(TURN))).to_matrix()
e1 = R @ e0
G(e0.z - e1.z >= 0.03 or abs(e1.x - e0.x) >= 0.05, f'watch moves the eyes {abs(e1.x - e0.x) * 100:.0f} cm sideways and {(e0.z - e1.z) * 100:.0f} cm down (min 5 sideways or 3 down)')
G({'palLacquer', 'palBronze', 'palInlay', 'palStone'} <= K.mats(lod0), 'materials: lacquer column (approved A3 texture), bronze sleeves and board, silver inlay rings, stone plinth')
G(K.smooth_share(lod0) >= 0.5, f'smooth-shaded share {K.smooth_share(lod0):.0%} (min 50%)')
G.done()
K.export(OUT, ((lod1, 3), (lod2, 6)))
