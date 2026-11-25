#!/usr/bin/env python3
"""Cards for the W1b bronze props, painted in klad (art is klad paint; this script only places the marks and runs klad).

- smoke_card: incense smoke for the 铜鹤 crane and 香炉 censer (asset list C4: "smoke as few small cards"). A soft warm-grey puff on a
  transparent ground with two curling wisps (the cloud-scroll curl of the trim sheet, so the smoke speaks the palace's ornament);
  alpha falls to zero well inside the edge so no card border shows.
- flame_card: a lamp flame for the C9 bronze lamps (light faked by emissive cards; 2-3 real lights max in the game): a teardrop with a
  pale gold core, orange body, fading to zero at the edge (low saturation at the rim; not neon).
Painted on a 1024 canvas, exported at 256 px (cards are small on screen: a 0.6 m card is 66 px at the fight framing).
Usage: python3 w1b_tex.py KLAD OPSDIR SRCDIR OUTDIR   (writes OPSDIR/<name>.jsonl, SRCDIR/<name>.klad, OUTDIR/<name>.png)
Checked by art/tools/card_check.py.
"""
import json, math, os, shutil, subprocess, sys
KLAD, OPS, SRC, OUTD = sys.argv[1:5]
sys.argv = [sys.argv[0], OPS, '1024']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palace_tex as P

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Export size of every card, px.
CARD_PX = 256
# Smoke ramp (warm grey: the game's smoke colour 0x8c8a86 lightened for the lit side) and its opacity per stroke.
SMOKE = ('#9c968c', '#b8b2a6', '#cfc9bd', '#7e786f')
SMOKE_OP = (0.05, 0.12)
# Flame ramp: core, body, rim.
FLAME = ('#fff1c8', '#f6c25a', '#d98a46')


def smoke():
    t = P.Tex('smoke_card', '#000000', False, False, 931); r = t.r
    t.stage = 0  # base: a broad soft puff, many low strokes (densest in the middle)
    for _ in range(110):
        a = r.uniform(0, math.tau); d = abs(r.gauss(0, 150)); cx, cy = 512 + math.cos(a) * d, 540 + math.sin(a) * d * 0.75
        L = r.uniform(80, 200); b = r.uniform(0, math.tau)
        t.stroke(t.wobble(cx, cy, cx + math.cos(b) * L, cy + math.sin(b) * L, 4, 20), 'soft', r.uniform(120, 220), r.choice(SMOKE[:3]),
                 r.uniform(*SMOKE_OP), wrap=False)
    t.stage = 1  # tone: lighter tops (lit from above), darker under-sides
    for _ in range(30):
        cx, cy = 512 + r.gauss(0, 110), 470 + r.gauss(0, 70)
        t.stroke(t.wobble(cx - 60, cy, cx + 60, cy - 10, 3, 14), 'soft', r.uniform(70, 130), SMOKE[2], r.uniform(0.06, 0.14), wrap=False)
    for _ in range(18):
        cx, cy = 512 + r.gauss(0, 110), 640 + r.gauss(0, 50)
        t.stroke(t.wobble(cx - 50, cy, cx + 50, cy + 6, 3, 12), 'soft', r.uniform(60, 110), SMOKE[3], r.uniform(0.05, 0.1), wrap=False)
    t.stage = 2  # marks: one curling wisp (a cloud-scroll curl), off centre (round 1 draft: two mirrored curls read as a pair of eyes)
    for s in (1,):
        cx, cy = 600, 400; pts = []
        for k in range(22):
            ang = s * (k * 0.32) + (math.pi if s < 0 else 0); rad = 110 - k * 4.2
            pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad * 0.9))
        t.stroke(pts, 'soft', 34, SMOKE[2], 0.22, pressure=[0.3, 1, 0.2], wrap=False)
    t.stage = 3  # detail: faint streaks rising (the smoke drifts up)
    for _ in range(14):
        x = 512 + r.gauss(0, 120); y = 640 + r.uniform(-40, 60)
        t.stroke(t.wobble(x, y, x + r.uniform(-30, 30), y - r.uniform(160, 300), 5, 10), 'soft', r.uniform(18, 34), SMOKE[1], r.uniform(0.07, 0.14),
                 pressure=[0.2, 1, 0.1], wrap=False)
    return t


def flame():
    t = P.Tex('flame_card', '#000000', False, False, 932); r = t.r
    def tear(cx, by, h, w, color, op, n, brush='soft'):
        # a teardrop of horizontal soft strokes: a round base (half circle over the lowest quarter), tapering to a point (round 1 draft:
        # strokes fanned up from a flat base read as a cone)
        for i in range(n):
            tt = (i + 0.5) / n; y = by - tt * h
            hw = w / 2 * (math.sqrt(max(0.0, 1 - ((tt - 0.25) / 0.25) ** 2)) if tt < 0.25 else (1 - (tt - 0.25) / 0.75) ** 1.4)
            if hw < 4: continue
            t.stroke([(cx - hw * 0.6, y), (cx + hw * 0.6, y)], brush, hw * 1.2 + 30, color, op, wrap=False)
        t.stroke([(cx, by - h * 0.2), (cx, by - h)], brush, w * 0.25, color, op, pressure=[1, 0.6, 0.05], wrap=False)  # a soft spine merges the rows
    t.stage = 0
    tear(512, 880, 720, 520, FLAME[2], 0.3, 26)  # rim: soft orange halo
    t.stage = 1
    tear(512, 830, 560, 320, FLAME[1], 0.45, 20)  # body
    t.stage = 2
    tear(512, 800, 380, 190, FLAME[0], 0.85, 16)  # core
    t.stage = 3
    for _ in range(6):  # flicker licks at the top
        x = 512 + r.uniform(-50, 50)
        t.stroke([(x, 420), (x + r.uniform(-30, 30), 300), (x + r.uniform(-20, 20), 230)], 'soft', r.uniform(16, 28), FLAME[1], 0.35,
                 pressure=[1, 0.5, 0.05], wrap=False)
    return t


if __name__ == '__main__':
    for d in (OPS, SRC, OUTD): os.makedirs(d, exist_ok=True)
    for t in (smoke(), flame()):
        n = t.write(); bundle = os.path.join(SRC, t.name + '.klad'); shutil.rmtree(bundle, ignore_errors=True)
        subprocess.run([KLAD, 'new', bundle, '--width', '1024', '--height', '1024'], check=True, capture_output=True)
        subprocess.run([KLAD, 'apply', bundle, '--file', os.path.join(OPS, t.name + '.jsonl')], check=True, capture_output=True)
        out = os.path.join(OUTD, t.name + '.png')
        subprocess.run([KLAD, 'export', bundle, '--scale', str(CARD_PX / 1024), '-o', out], check=True, capture_output=True)
        shutil.rmtree(os.path.join(bundle, '.cache'), ignore_errors=True)
        print(t.name, n, 'ops ->', out)
