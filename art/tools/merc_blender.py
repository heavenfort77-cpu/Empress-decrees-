# 水银 mercury channel, round 1 (asset list C7; study art/Qin-Bronze-Castings-Study.md "水银 mercury channel"). Silver channels across
# bridges and halls (the Qin tomb's rivers of mercury); standing in one hurts while it burns; crossed between pulses; it shimmers before
# each pulse (CONFIG.PIECES.mercury: period 4 s, warn 0.6 s (the tell), on 1.2 s; the game swaps materials merc / mercWarn / mercHot).
# Box today: a flat 0.06 m slab per channel (sx by sz, 2 m wide). Flat and instanced: a 1 m bronze lip segment repeated along both
# edges, an end piece, a corner post and a 1 x 1 m mercury surface scaled to the channel. The mercury is the only bright cool
# reflective surface (matcap A14, W2's mercury_matcap.png); the lip is cast bronze with a silver inlay line, so the channel's edge
# reads as a made thing and the mercury inside it as the hazard. Reference only: ComfyUI round F job 3 (run 45446297299).
# Output: merc_lip (1 m along x, the channel's inside at +f), merc_end (1 m across), merc_post, merc_surface (1 x 1 m, centred), and
# merc_demo (a 2 x 6 m channel made of linked duplicates of those meshes, for review; the game places the pieces itself).
# Usage: /home/claude/bpyenv/bin/python merc_blender.py OUT.glb
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import prop_kit as K
from prop_kit import P, prism, rect, lathe

OUT = sys.argv[-1] if sys.argv[-1].endswith('.glb') else '/tmp/merc.glb'

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Lip: top flange width, height above the floor, inner wall depth below the mercury, m; inlay width m (6 cm reads at the fight framing).
LIP_W, LIP_H, INLAY_W = 0.14, 0.07, 0.06
# Mercury surface height m (under the lip top, above the floor: the box slab was 0.06 m); grid cells per side; shading normals tilted
# toward the play camera and rippled, deg (see surface()).
SURF_Z = 0.04
GRID, TILT, RIPPLE = 2, 38, 9
# Triangle budget per piece (flat, instanced) and for the 2 x 6 m demo channel drawn.
PIECE_BUDGET, DEMO_BUDGET = 60, 600
# Demo channel size m.
DEMO = (2.0, 6.0)


def lip(name, length):
    """a lip segment along x from -length/2 to +length/2; outside face at f = -LIP_W, inside (channel) at f = 0."""
    prism('flange', [(-LIP_W, 0.0), (0.0, 0.0), (0.0, LIP_H), (-LIP_W + 0.02, LIP_H), (-LIP_W, LIP_H - 0.02)], (-length / 2, 0, 0), (length / 2, 0, 0), 'palBronze', 'flange', up=(0, 0, 1))
    prism('inlay', rect(INLAY_W, 0.004), (-length / 2, -LIP_W / 2, LIP_H + 0.002), (length / 2, -LIP_W / 2, LIP_H + 0.002), 'palInlay', 'plain', rnd='flat', up=(0, 0, 1))
    return K.finish(name)


def surface():
    """the mercury: a GRID x GRID quad grid 1 x 1 m, flat, facing up, with custom normals tilted TILT deg toward the play camera (+f) and
    a small ripple (RIPPLE deg). Cause (measured on W2's A14 matcap): its top band is dark (value 62-107 at 0.7-0.95 of the height), and
    a flat upward surface seen from the 40 deg play pitch samples exactly that band, so the round 1 draft's mercury read dark grey with
    streaks; tilting the shading normals toward the camera samples the bright centre (173) and the ripple gives it a liquid shimmer."""
    import bmesh
    from mathutils import Vector
    bm = bmesh.new(); vs = [[bm.verts.new(P(-0.5 + i / GRID, 0.5 - j / GRID, SURF_Z)) for i in range(GRID + 1)] for j in range(GRID + 1)]
    for j in range(GRID):
        for i in range(GRID): bm.faces.new([vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]])
    for f in bm.faces:
        f.normal_update()
        if f.normal.z < 0: f.normal_flip()
    K.put('surf', bm, 'palMerc', 'plain', True); ob = K.finish('merc_surface')
    me = ob.data; ns = []
    for lp in me.loops:
        co = me.vertices[lp.vertex_index].co
        # one wave per metre, equal on opposite tile edges, so 1 m tiles join without a seam (draft: free sines showed a checker)
        r = math.radians(RIPPLE) * math.cos(math.tau * (co.x + 0.5)); q = math.radians(RIPPLE) * math.cos(math.tau * (co.y + 0.5) + 1.0)
        n = Vector((math.sin(r), -math.sin(math.radians(TILT)) + math.sin(q), math.cos(math.radians(TILT)))).normalized()  # design +f = Blender -Y
        ns.append(n)
    me.normals_split_custom_set(ns)
    return ob


def build():
    K.reset()
    l = lip('merc_lip', 1.0); e = lip('merc_end', 1.0)
    prism('post', rect(LIP_W + 0.02, LIP_W + 0.02), (0, 0, 0), (0, 0, LIP_H + 0.03), 'palBronze', 'mask'); p = K.finish('merc_post')
    s = surface()
    return l, e, p, s


lip_ob, end_ob, post_ob, surf_ob = build()
W, Lg = DEMO
demo = bpy.data.objects.new('merc_demo', None); bpy.context.collection.objects.link(demo)
def inst(src, name, loc, rz=0.0, scale=(1, 1, 1)):
    ob = bpy.data.objects.new(name, src.data); bpy.context.collection.objects.link(ob)
    ob.location = loc; ob.rotation_euler = (0, 0, rz); ob.scale = scale; ob.parent = demo; return ob
drawn = []
for k in range(int(Lg)):  # the channel runs along design f (toward the camera): lips on its two long sides face inward
    fy = -(-Lg / 2 + 0.5 + k)
    drawn.append(inst(lip_ob, f'demo_lipL_{k}', (-W / 2, fy, 0), rz=math.radians(90)))
    drawn.append(inst(lip_ob, f'demo_lipR_{k}', (W / 2, fy, 0), rz=math.radians(-90)))
for s, fy in ((0, Lg / 2), (1, -Lg / 2)):
    for j in range(int(W)):
        drawn.append(inst(end_ob, f'demo_end_{s}{j}', (-W / 2 + 0.5 + j, fy, 0), rz=math.radians(0 if s == 0 else 180)))
for sx in (-1, 1):
    for sy in (-1, 1): drawn.append(inst(post_ob, f'demo_post_{sx}{sy}', (sx * (W / 2 + LIP_W / 2), sy * (Lg / 2 + LIP_W / 2), 0)))
# mercury in 1 x 1 m tiles (instanced), never one stretched quad: a non-uniform scale bends the tilted shading normals flat again
# (the draft scaled one quad 2 x 6 and its tilt fell from 38 to about 7 deg: dark grey marble look)
for i in range(int(W)):
    for j in range(int(Lg)): drawn.append(inst(surf_ob, f'demo_surface_{i}{j}', (-W / 2 + 0.5 + i, -(-Lg / 2 + 0.5 + j), 0)))
for o in (lip_ob, end_ob, post_ob, surf_ob): o.location.x += 4  # the bare pieces beside the demo

G = K.Gates()
for o in (lip_ob, end_ob, post_ob, surf_ob): G(K.tris(o) <= PIECE_BUDGET, f'{o.name} tris {K.tris(o)} (piece budget {PIECE_BUDGET}, instanced)')
dt = sum(K.tris(o) for o in drawn)
G(dt <= DEMO_BUDGET, f'2 x 6 m demo channel drawn tris {dt} from {len(drawn)} instances of 4 meshes (budget {DEMO_BUDGET})')
G(len({o.data.name for o in drawn}) == 4 and all(tuple(o.scale) == (1.0, 1.0, 1.0) for o in drawn), f'demo uses only the 4 shared meshes, none scaled (tilted normals survive) ({sorted({o.data.name for o in drawn})})')
up = all(p.normal.z > 0.99 for p in surf_ob.data.polygons)
cn = [v.vector for v in surf_ob.data.corner_normals] if hasattr(surf_ob.data, 'corner_normals') else []
tilt = sum(math.degrees(math.atan2(-v.y, v.z)) for v in cn) / max(1, len(cn))
G(len(cn) and 25 <= tilt <= 50, f'mercury shading normals tilted {tilt:.0f} deg toward the camera on average (25-50: samples the matcap centre from the 40 deg pitch)')
G(SURF_Z < LIP_H and up and 'palMerc' in K.mats(surf_ob), f'mercury surface at {SURF_Z} m under the lip top {LIP_H} m, faces up: {up}, material palMerc (matcap)')
G(INLAY_W >= 0.06 and 'palInlay' in K.mats(lip_ob), f'silver inlay line {INLAY_W * 100:.0f} cm on the bronze lip (min 6)')
G.done()
K.export(OUT)
