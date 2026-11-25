"""pxkit: tiny shaded-shape painter for 64 px sprites (original shapes, drawn in code).
A canvas holds, per pixel, a material, a tone on that material's ramp and a part id.
"""
import numpy as np
from PIL import Image

W = H = 64
AX = 31.5  # mirror axis


def unit(v):
    v = np.array(v, float)
    return v / np.linalg.norm(v)


class Cv:
    def __init__(s, cfg):
        s.cfg = cfg
        s.L = unit(cfg['light'])
        s.m = np.full((H, W), -1, int)
        s.t = np.zeros((H, W), int)
        s.p = np.zeros((H, W), int)
        s.n = 0
        s.thin = np.zeros((H, W), bool)   # pixels that get no outline of their own
        s.yy, s.xx = np.mgrid[0:H, 0:W].astype(float)
        s.mats = list(cfg['ramps'].keys())

    # ---------- masks
    def ell(s, cx, cy, rx, ry):
        return ((s.xx - cx) / rx) ** 2 + ((s.yy - cy) / ry) ** 2 <= 1.0

    def rect(s, x0, y0, x1, y1):
        return (s.xx >= x0) & (s.xx <= x1) & (s.yy >= y0) & (s.yy <= y1)

    def poly(s, pts):
        x, y = s.xx, s.yy
        inside = np.zeros((H, W), bool)
        n = len(pts)
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            if y0 == y1:
                continue
            c = ((y0 <= y) & (y < y1)) | ((y1 <= y) & (y < y0))
            xi = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            inside ^= c & (x < xi)
        return inside

    def cap(s, p0, p1, r0, r1=None):
        """tapered capsule; returns mask, and signed lateral offset (-1..1) for shading"""
        r1 = r0 if r1 is None else r1
        p0 = np.array(p0, float); p1 = np.array(p1, float)
        d = p1 - p0
        ln = np.hypot(*d)
        u = d / ln
        px = s.xx - p0[0]; py = s.yy - p0[1]
        t = np.clip((px * u[0] + py * u[1]) / ln, 0, 1)
        qx = px - t * d[0]; qy = py - t * d[1]
        r = r0 + (r1 - r0) * t
        dist = np.hypot(qx, qy)
        lat = (qx * (-u[1]) + qy * u[0]) / np.maximum(r, 1e-6)
        return dist <= r, lat, u

    # ---------- intensities (dot of a surface normal with the light)
    def i_sphere(s, cx, cy, rx, ry):
        nx = (s.xx - cx) / rx; ny = (s.yy - cy) / ry
        nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
        return nx * s.L[0] + ny * s.L[1] + nz * s.L[2]

    def i_cylv(s, cx, w, tilt=0.0):
        """upright cylinder, half-width w (number or array); tilt = ny of the surface"""
        nx = np.clip((s.xx - cx) / w, -1, 1)
        nz = np.sqrt(np.clip(1 - nx * nx - tilt * tilt, 0, 1))
        return nx * s.L[0] + tilt * s.L[1] + nz * s.L[2]

    def i_cylh(s, cy, h, tilt=0.0):
        ny = np.clip((s.yy - cy) / h, -1, 1)
        nz = np.sqrt(np.clip(1 - ny * ny - tilt * tilt, 0, 1))
        return tilt * s.L[0] + ny * s.L[1] + nz * s.L[2]

    def i_cap(s, lat, u):
        lat = np.clip(lat, -1, 1)
        nx = lat * (-u[1]); ny = lat * u[0]
        nz = np.sqrt(np.clip(1 - lat * lat, 0, 1))
        return nx * s.L[0] + ny * s.L[1] + nz * s.L[2]

    def i_flat(s, n):
        n = unit(n)
        return np.full((H, W), float(n @ s.L))

    # ---------- painting
    def tone(s, mat, inten, lo=1, hi=None, bias=0.0):
        ramp = s.cfg['ramps'][mat]
        hi = len(ramp) - 1 if hi is None else hi
        a, b = s.cfg['shade_range']
        f = np.clip((inten + bias - a) / (b - a), 0, 0.9999)
        f = f ** s.cfg['shade_gamma']
        return lo + np.floor(f * (hi - lo + 1)).astype(int)

    def put(s, mask, mat, inten=None, tone=None, lo=1, hi=None, bias=0.0, part='new'):
        mi = s.mats.index(mat)
        if part == 'new':
            s.n += 1
            part = s.n
        if inten is not None:
            tn = s.tone(mat, inten, lo, hi, bias)
        else:
            tn = np.full((H, W), tone if tone is not None else 2, int)
        s.m[mask] = mi
        s.t[mask] = tn[mask]
        if part is not None:
            s.p[mask] = part
        return part

    def px(s, cells, mat, tone, part=None):
        mi = s.mats.index(mat)
        for (x, y) in cells:
            x = int(round(x)); y = int(round(y))
            if 0 <= x < W and 0 <= y < H:
                s.m[y, x] = mi; s.t[y, x] = tone
                if part == 'new':
                    s.n += 1; part = s.n
                if part is not None:
                    s.p[y, x] = part

    def line(s, p0, p1, mat, tone, part=None):
        x0, y0 = p0; x1, y1 = p1
        n = int(max(abs(x1 - x0), abs(y1 - y0)))
        cells = [(x0 + (x1 - x0) * i / max(n, 1), y0 + (y1 - y0) * i / max(n, 1)) for i in range(n + 1)]
        s.px(cells, mat, tone, part)

    def shift(s, mask, d, only=None):
        """move tones along the ramp inside mask (d = +1 lighter, -1 darker), never to tone 0"""
        sel = mask & (s.m >= 0)
        if only is not None:
            sel &= (s.m == s.mats.index(only))
        for mi, name in enumerate(s.mats):
            top = len(s.cfg['ramps'][name]) - 1
            q = sel & (s.m == mi)
            s.t[q] = np.clip(s.t[q] + d, 1, top)

    LEG = {**{str(i): ('steel', i) for i in range(1, 7)},
           'a': ('gun', 1), 'b': ('gun', 2), 'c': ('gun', 3), 'd': ('gun', 4),
           'g': ('glow', 1), 'h': ('glow', 2), 'i': ('glow', 3), 'j': ('glow', 4),
           'o': ('brass', 1), 'p': ('brass', 2), 'q': ('brass', 3), 'r': ('brass', 4),
           'u': ('cloth', 1), 'v': ('cloth', 2), 'w': ('cloth', 3), 'x': ('cloth', 4),
           'R': ('grip', 1), 'S': ('grip', 2), 'T': ('grip', 3)}

    def grid(s, rows, x0, y0, part='new', mirror=False):
        """hand-placed pixels: one character per pixel ('.' leaves what is there)"""
        w = len(rows[0])
        if part == 'new':
            s.n += 1; part = s.n
        for j, row in enumerate(rows):
            assert len(row) == w, (j, row, len(row))
            if mirror:
                row = row[::-1]
            for i, ch in enumerate(row):
                if ch == '.':
                    continue
                mat, tn = s.LEG[ch]
                s.m[y0 + j, x0 + i] = s.mats.index(mat); s.t[y0 + j, x0 + i] = tn; s.p[y0 + j, x0 + i] = part
        return part

    # ---------- finishing
    def part_shadow(s):
        """a part drawn later casts a 1 px shadow on the part under it, down and right of it"""
        k = s.cfg['part_shadow']
        if not k:
            return
        t2 = s.t.copy()
        for y in range(H):
            for x in range(W):
                if s.m[y, x] < 0:
                    continue
                a = s.p[y, x]
                for (dx, dy) in ((-1, 0), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < W and 0 <= yy < H and s.m[yy, xx] >= 0:
                        b = s.p[yy, xx]
                        if b > a and s.cfg['glow'] != s.mats[s.m[y, x]]:
                            t2[y, x] = max(1, s.t[y, x] - k)
        s.t = t2

    def despeckle(s):
        """mid tones standing alone (no 8-neighbour of the same colour) join the commonest tone of their material nearby.
        Kept: highlights, darkest accents, and the materials listed in cfg['keep_single'] (lights, trim)."""
        if not s.cfg.get('despeckle'):
            return
        keep = s.cfg.get('keep_single', [])
        for _ in range(2):
            t2 = s.t.copy()
            for y in range(H):
                for x in range(W):
                    mi = s.m[y, x]
                    if mi < 0 or s.mats[mi] in keep:
                        continue
                    top = len(s.cfg['ramps'][s.mats[mi]]) - 1
                    if s.t[y, x] >= top or s.t[y, x] <= 1:
                        continue
                    cnt = {}
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            yy, xx = y + dy, x + dx
                            if (dy or dx) and 0 <= yy < H and 0 <= xx < W and s.m[yy, xx] == mi:
                                cnt[s.t[yy, xx]] = cnt.get(s.t[yy, xx], 0) + 1
                    if cnt and s.t[y, x] not in cnt:
                        t2[y, x] = max(cnt, key=lambda q: (cnt[q], -abs(q - s.t[y, x])))
            s.t = t2

    def outline(s):
        """1 px outside outline in tone 0 of the touching material (darkest material wins)"""
        m2 = s.m.copy(); t2 = s.t.copy()
        order = s.cfg['outline_order']
        for y in range(H):
            for x in range(W):
                if s.m[y, x] >= 0:
                    continue
                best = None
                for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < W and 0 <= yy < H and s.m[yy, xx] >= 0 and not s.thin[yy, xx]:
                        name = s.mats[s.m[yy, xx]]
                        r = order.index(name) if name in order else 99
                        if best is None or r < best[0]:
                            best = (r, s.m[yy, xx])
                if best is not None:
                    m2[y, x] = best[1]; t2[y, x] = 0
        s.m, s.t = m2, t2

    def flip(s):
        s.m = s.m[:, ::-1].copy(); s.t = s.t[:, ::-1].copy(); s.p = s.p[:, ::-1].copy(); s.thin = s.thin[:, ::-1].copy()

    def image(s):
        im = np.zeros((H, W, 4), np.uint8)
        for mi, name in enumerate(s.mats):
            ramp = s.cfg['ramps'][name]
            for ti, hx in enumerate(ramp):
                q = (s.m == mi) & (s.t == ti)
                if q.any():
                    im[q] = (int(hx[1:3], 16), int(hx[3:5], 16), int(hx[5:7], 16), 255)
        return Image.fromarray(im, 'RGBA')


def up(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def sheet(ims, bg=(86, 92, 104, 255), gap=0):
    w = sum(i.width for i in ims) + gap * (len(ims) - 1)
    out = Image.new('RGBA', (w, ims[0].height), bg)
    x = 0
    for i in ims:
        out.alpha_composite(i, (x, 0)); x += i.width + gap
    return out
