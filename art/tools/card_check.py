#!/usr/bin/env python3
"""Checks for the W1b effect cards (art/tools/w1b_tex.py; study art/Qin-Bronze-Castings-Study.md, "Cards"). PASS/FAIL per rule.
Rules:
- size: 256 x 256 RGBA (cards are small on screen; transparency budget);
- soft edge: no alpha above 0.03 in the outer 6% border (no visible card border);
- coverage: share of pixels with alpha > 0.1 between 15% and 60% (a puff or a flame, not a square);
- smoke: mean opaque-weighted luminance 120-200, saturation <= 0.12 (warm grey, never coloured), peak alpha 0.35-0.9 (stacked cards still
  let the room show through), soft: mean alpha step between neighbours < 0.03;
- flame: core (top 5% alpha) luminance >= 200, body hue 20-50 deg, rim (alpha 0.1-0.3) saturation <= 0.75 (not neon), peak alpha >= 0.8.
Usage: python3 card_check.py TEXDIR
"""
import sys
import numpy as np
from PIL import Image
D = sys.argv[1]
fails = 0; n = 0
def rule(ok, line):
    global fails, n
    n += 1; fails += not ok; print(('PASS ' if ok else 'FAIL ') + line)
def hue_sat(c):
    mx, mn = c.max(-1), c.min(-1); d = np.maximum(mx - mn, 1e-6)
    h = np.where(mx == c[..., 0], 60 * (((c[..., 1] - c[..., 2]) / d) % 6), np.where(mx == c[..., 1], 60 * ((c[..., 2] - c[..., 0]) / d + 2), 60 * ((c[..., 0] - c[..., 1]) / d + 4)))
    return h, np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
for name in ('smoke_card', 'flame_card'):
    im = Image.open(f'{D}/{name}.png'); rule(im.size == (256, 256) and im.mode == 'RGBA', f'{name} size {im.size} {im.mode}')
    a = np.asarray(im.convert('RGBA')).astype(float) / 255; al = a[..., 3]; rgb = a[..., :3]
    b = int(256 * 0.06); edge = np.concatenate([al[:b].ravel(), al[-b:].ravel(), al[:, :b].ravel(), al[:, -b:].ravel()])
    rule(edge.max() <= 0.03, f'{name} soft edge: border alpha max {edge.max():.3f} (max 0.03)')
    cov = (al > 0.1).mean(); rule(0.15 <= cov <= 0.6, f'{name} coverage {cov:.0%} (15-60%)')
    lum = (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]) * 255
    h, s = hue_sat(rgb)
    if name == 'smoke_card':
        w = al / max(al.sum(), 1e-6); L = (lum * w).sum(); S = (s * w).sum()
        rule(120 <= L <= 200, f'smoke mean luminance {L:.0f} (120-200)')
        rule(S <= 0.12, f'smoke saturation {S:.2f} (max 0.12, warm grey)')
        rule(0.35 <= al.max() <= 0.9, f'smoke peak alpha {al.max():.2f} (0.35-0.9)')
        st = max(np.abs(np.diff(al, axis=0)).mean(), np.abs(np.diff(al, axis=1)).mean()); rule(st < 0.03, f'smoke softness: mean alpha step {st:.4f} (< 0.03)')
    else:
        core = al >= np.quantile(al[al > 0.01], 0.95); rule(lum[core].mean() >= 200, f'flame core luminance {lum[core].mean():.0f} (min 200)')
        body = (al > 0.3); hb = h[body].mean(); rule(20 <= hb <= 50, f'flame body hue {hb:.0f} deg (20-50)')
        rim = (al > 0.1) & (al < 0.3); sr = s[rim].mean() if rim.any() else 1; rule(sr <= 0.75, f'flame rim saturation {sr:.2f} (max 0.75, not neon)')
        rule(al.max() >= 0.8, f'flame peak alpha {al.max():.2f} (min 0.8)')
print(f'{n - fails} of {n} pass')
