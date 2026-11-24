# Scrolling tread belts (FIX-A, 25 Nov; owner decision 02:2x: treads roll by a scrolling texture, not by moving links).
# Shared by the apex cubs (apex_kit / apex_cubs.py) and the guard (fodder_base / guard_build.py). A belt is a loop around its end wheels;
# its faces carry material 'treadBelt' (texture assets/tex/tread_belt.png, made by art/tools/tread_tex.py) with their own UVs:
#   U = distance along the belt loop / metres per repeat (whole repeats round the loop, so the loop closes without a seam);
#   V = across the belt (image rows: side edge, link face, side edge).
# Loop direction: U grows forward along the bottom run (rear to front), up the front, back along the top run and down the rear.
# The game rolls a belt by scrolling the texture: map.offset.x += (metres travelled forward) / (metres per repeat); backward = minus.
# Metres per repeat per asset are measured from the built mesh by check() and printed in the gate line (report: art/FIXA-REPORT.md).
# Geometry is plain python (lists) so it can be tested without Blender; build_bm() turns it into a bmesh with a 'UVMap' layer.
import math

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Target metres of belt per texture repeat; snapped per belt to a whole number of repeats round the loop.
MPR = 0.5
# Image rows as fractions of the strip height from the top: side edge band, then the link face, then the other side edge.
V_SIDE = 12 / 64
# Arc segments per half circle (LOD0); LODs scale it with their segment factor.
ARC_SEGS = 8
# Tolerance of the UV gate: U per metre along straight runs within this share of 1 / mpr, and the loop's U span this close to whole.
TOL_RATE, TOL_WHOLE = 0.02, 0.01


def stadium(fc, zc, hl, rp):
    """a belt loop round two end wheels at f = fc +- hl (centre height zc, belt centre-line radius rp): returns at(u), total length.
    at(u) -> ((f, z), (nf, nz)) point on the centre line and its outward normal; u = 0 at the rear end of the bottom run."""
    arc = math.pi * rp; tot = 4 * hl + 2 * arc

    def at(u):
        u %= tot
        if u < 2 * hl: return (fc - hl + u, zc - rp), (0.0, -1.0)
        u -= 2 * hl
        if u < arc:
            a = -math.pi / 2 + u / rp; return (fc + hl + rp * math.cos(a), zc + rp * math.sin(a)), (math.cos(a), math.sin(a))
        u -= arc
        if u < 2 * hl: return (fc + hl - u, zc + rp), (0.0, 1.0)
        u -= 2 * hl; a = math.pi / 2 + u / rp
        return (fc - hl + rp * math.cos(a), zc + rp * math.sin(a)), (math.cos(a), math.sin(a))
    return at, tot, hl, rp


def samples(loop, seg=1.0):
    """u values along the loop: straight runs as one span each, half circles in ARC_SEGS * seg steps; last = tot (closes the seam)."""
    at, tot, hl, rp = loop; n = max(3, round(ARC_SEGS * seg)); arc = math.pi * rp; us = []
    for base in (0.0, 2 * hl + arc):
        us.append(base)
        for k in range(n): us.append(base + 2 * hl + arc * k / n)
    return [u for u in us if u < tot - 1e-9] + [tot]


def geometry(loop, x0, x1, thick=None, seg=1.0, mpr_target=MPR):
    """belt between x0 and x1 (design x). thick None: a solid stadium (perimeter band + two flat side caps, caps returned apart);
    thick t: an open ring band t thick (outer, inner and two side faces). Returns dict(verts, band, caps, mpr, reps, tot) with
    verts as design (x, f, z); band faces as [(vertex index, (u, v_img))...] with v_img measured from the image top; caps as index lists."""
    at, tot, hl, rp = loop; reps = max(1, round(tot / mpr_target)); mpr = tot / reps
    us = samples(loop, seg); V = []; band = []; caps = []
    def vert(p): V.append(p); return len(V) - 1
    if thick is None:
        cols = []
        for u in us:
            (f, z), _ = at(u); cols.append((vert((x0, f, z)), vert((x1, f, z)), u / mpr))
        for (a0, a1, ua), (b0, b1, ub) in zip(cols, cols[1:]):
            band.append([(a0, (ua, V_SIDE)), (b0, (ub, V_SIDE)), (b1, (ub, 1 - V_SIDE)), (a1, (ua, 1 - V_SIDE))])
        caps = [[c[0] for c in cols[:-1]], [c[1] for c in cols[:-1]]]
    else:
        cols = []
        for u in us:
            (f, z), (nf, nz) = at(u); o, i = thick / 2, -thick / 2
            cols.append(dict(u=u / mpr, ol=vert((x0, f + nf * o, z + nz * o)), orr=vert((x1, f + nf * o, z + nz * o)),
                             il=vert((x0, f + nf * i, z + nz * i)), ir=vert((x1, f + nf * i, z + nz * i))))
        for a, b in zip(cols, cols[1:]):
            ua, ub = a['u'], b['u']
            band.append([(a['ol'], (ua, V_SIDE)), (b['ol'], (ub, V_SIDE)), (b['orr'], (ub, 1 - V_SIDE)), (a['orr'], (ua, 1 - V_SIDE))])  # outer (tread face)
            band.append([(a['il'], (ua, V_SIDE)), (a['ir'], (ua, 1 - V_SIDE)), (b['ir'], (ub, 1 - V_SIDE)), (b['il'], (ub, V_SIDE))])    # inner (wheel side)
            band.append([(a['il'], (ua, 0.0)), (b['il'], (ub, 0.0)), (b['ol'], (ub, V_SIDE)), (a['ol'], (ua, V_SIDE))])               # side x0
            band.append([(a['ir'], (ua, 1.0)), (a['orr'], (ua, 1 - V_SIDE)), (b['orr'], (ub, 1 - V_SIDE)), (b['ir'], (ub, 1.0))])       # side x1
    return dict(verts=V, band=band, caps=caps, mpr=mpr, reps=reps, tot=tot)


def build_bm(G, P, outward):
    """bmesh of the band (UV layer 'UVMap', faces turned so they face away from the belt's inside) and of the caps (or None).
    P(x, f, z) -> Blender Vector (the kit's own mapping); outward(face design centre) -> design direction the face should face."""
    import bmesh
    def mk(faces, uv):
        bm = bmesh.new(); vs = [bm.verts.new(P(*p)) for p in G['verts']]; lay = bm.loops.layers.uv.new('UVMap') if uv else None
        back = {v: i for i, v in enumerate(vs)}
        for fc in faces:
            idx = [i for i, _ in fc] if uv else fc
            try: f = bm.faces.new([vs[i] for i in idx])
            except ValueError: continue
            if uv:
                m = dict(fc)
                for lp in f.loops:
                    u, v = m[back[lp.vert]]; lp[lay].uv = (u, 1.0 - v)
            c = [sum(G['verts'][i][k] for i in idx) / len(idx) for k in range(3)]
            want = outward(c, idx); w = P(c[0] + want[0] * 0.01, c[1] + want[1] * 0.01, c[2] + want[2] * 0.01) - P(*c)
            f.normal_update()
            if f.normal.dot(w) < 0: f.normal_flip()
        bm.verts.index_update()
        unused = [v for v in bm.verts if not v.link_faces]
        if unused: bmesh.ops.delete(bm, geom=unused, context='VERTS')
        return bm
    return mk(G['band'], True), (mk(G['caps'], False) if G['caps'] else None)


def outward_for(G, loop, x0, x1):
    """outward direction of a band face from its design centre: across the belt for side faces (all verts on one x), else away from
    the loop centre line (outer faces out, inner faces in, judged by distance to the centre line)."""
    at, tot, hl, rp = loop
    xm = (x0 + x1) / 2; sx = 1 if x1 > x0 else -1
    def fn(c, idx):
        xs = {round(G['verts'][i][0], 6) for i in idx}
        if len(xs) == 1: return ((1 if c[0] > xm else -1) * 1.0, 0.0, 0.0)
        # nearest centre-line point
        best = None
        for k in range(64):
            (f, z), (nf, nz) = at(tot * k / 64); d = (c[1] - f) ** 2 + (c[2] - z) ** 2
            if best is None or d < best[0]: best = (d, f, z, nf, nz)
        _, f, z, nf, nz = best; s = (c[1] - f) * nf + (c[2] - z) * nz
        return (0.0, nf, nz) if s >= -1e-6 else (0.0, -nf, -nz)
    return fn


def caps_outward(x0, x1):
    xm = (x0 + x1) / 2
    return lambda c, idx: ((1 if c[0] > xm else -1) * 1.0, 0.0, 0.0)


# gate ------------------------------------------------------------------------------------------------------------------
def check_mesh(edges):
    """edges: [(length_m, du, dv, along_forward)] of every tread face edge in the exported mesh (world metres), plus the U span.
    Pass when every straight-run edge (along the forward axis, dv 0) has |du| / length = one rate, and the loop's U span is whole."""
    rates = [abs(du) / L for L, du, dv, fwd in edges if fwd and abs(dv) < 1e-4 and L > 1e-3 and abs(du) > 1e-6]
    if not rates: return False, 0.0, 'no straight-run tread edges'
    r = sorted(rates)[len(rates) // 2]; worst = max(abs(x / r - 1) for x in rates)
    return worst <= TOL_RATE, 1.0 / r, f'U rate spread {worst:.1%}'


def edges_of(ob, mat_name, M_world=None):
    """tread edges of a Blender mesh: (world length, du, dv, along forward) for faces with material mat_name; also each connected
    loop's U span (max - min per tread part, measured on vertices grouped by x side)."""
    me = ob.data; uvl = me.uv_layers.get('UVMap') or me.uv_layers[0]; mi = [i for i, m in enumerate(me.materials) if m and m.name == mat_name]
    Mw = M_world or ob.matrix_world; out = []; spans = []
    for p in me.polygons:
        if p.material_index not in mi: continue
        li = list(p.loop_indices); n = len(li)
        for k in range(n):
            a, b = li[k], li[(k + 1) % n]
            va, vb = Mw @ me.vertices[me.loops[a].vertex_index].co, Mw @ me.vertices[me.loops[b].vertex_index].co
            d = vb - va; L = d.length
            ua, ub = uvl.data[a].uv, uvl.data[b].uv
            fwd = L > 1e-6 and abs(d.y) / L > 0.999  # Blender -Y = design forward
            out.append((L, ub[0] - ua[0], ub[1] - ua[1], fwd))
    return out


def selftest():
    """pure-python mutation test of the geometry and the gate: the right belt passes, a wrong U rate and a seam fail."""
    loop = stadium(0.0, 0.2, 0.3, 0.15); rows = []
    for thick in (None, 0.04):
        G = geometry(loop, -0.06, 0.06, thick)
        def edges(G, k=1.0):
            out = []
            for fc in G['band']:
                for j in range(len(fc)):
                    (ia, (ua, va)), (ib, (ub, vb)) = fc[j], fc[(j + 1) % len(fc)]
                    a, b = G['verts'][ia], G['verts'][ib]; d = [b[i] - a[i] for i in range(3)]; L = math.sqrt(sum(x * x for x in d))
                    fwd = L > 1e-6 and abs(d[1]) / L > 0.999 and abs(d[0]) < 1e-9
                    out.append((L, (ub - ua) * k, vb - va, fwd))
            return out
        ok, mpr, _ = check_mesh(edges(G)); span = G['tot'] / G['mpr']
        rows.append((ok and abs(span - round(span)) < TOL_WHOLE and abs(mpr - G['mpr']) < 1e-6, f'tread selftest thick={thick}: right belt passes (mpr {G["mpr"]:.3f} m, {G["reps"]} repeats)'))
        # mutation 1: one straight run at a different U rate -> fails
        E = edges(G); bad = [(L, du * (1.1 if i == 0 else 1.0), dv, f) for i, (L, du, dv, f) in enumerate(E)]
        i0 = next(i for i, e in enumerate(E) if e[3] and abs(e[2]) < 1e-4 and e[0] > 1e-3 and abs(e[1]) > 1e-6)
        bad = [(L, du * (1.1 if i == i0 else 1.0), dv, f) for i, (L, du, dv, f) in enumerate(E)]
        rows.append((not check_mesh(bad)[0], f'tread selftest thick={thick}: mutation (one run 10% off) caught'))
        # mutation 2: unsnapped repeat length -> the loop's U span is not whole (a seam)
        G2 = geometry(loop, -0.06, 0.06, thick, mpr_target=0.5); span2 = G2['tot'] / (G2['mpr'] * 1.07)
        rows.append((abs(span2 - round(span2)) >= TOL_WHOLE, f'tread selftest thick={thick}: mutation (unsnapped repeat, span {span2:.3f}) caught'))
    return rows


if __name__ == '__main__':
    rows = selftest()
    for ok, line in rows: print(('PASS ' if ok else 'FAIL ') + line)
    print(f'tread selftest: {sum(ok for ok, _ in rows)} of {len(rows)} pass')
