"""Exports the four set characters' part data to JSON for the Blender build (python3 blender/prep3d.py -> blender/set3d.json).
Each 2D part (region, ramp, polygon) becomes a slab: depth by region plus 1.2 px per earlier part in the same region, so later layers
(tabard over breastplate, field over shield) stand proud like plate relief. A front-depth map per pixel places details and studs on the surface."""
import json, sys, os
sys.path.insert(0, os.getcwd())
import numpy as np
from PIL import Image, ImageDraw
import set96, knight96 as KN, tianbing96_v5 as F

DEPTH = {"torso": 24, "head": 20, "skirt": 18, "legL": 14, "legR": 14, "armL": 13, "armR": 13, "hand": 14, "pauL": 17, "pauR": 17,
         "shield": 4, "sword": 4, "staff": 4, "dagger": 4, "mantle": 22, "halberd": 4, "pagoda": 12}
CENTRE = {"shield": -9.0, "hand": -1.0}
METAL = {"tianbing": {"s", "b"}, "knight": {"g", "b", "f"}, "mage": {"s", "b"}, "rogue": {"s", "b"}, "golem": {"g", "s", "b"}}


def chars():
    yield "tianbing", dict(PAL=F.CONFIG["PAL"], RAMP=F.CONFIG["RAMP"], PARTS=F.PARTS, DETAILS=F.DETAILS, STUDS=F.STUDS)
    yield "knight", dict(PAL=KN.CONFIG["PAL"], RAMP=KN.CONFIG["RAMP"], PARTS=KN.PARTS, DETAILS=KN.DETAILS, STUDS=KN.STUDS)
    for n in ("mage", "rogue", "golem"): yield n, set96.SET[n]


def mask(poly):
    m = Image.new("L", (96, 96), 0); ImageDraw.Draw(m).polygon(poly, fill=1); return np.asarray(m) > 0


out = {}
for name, ch in chars():
    P, R = ch["PAL"], ch["RAMP"]; count = {}; parts = []; front = np.full((96, 96), -99.0)
    for region, ramp, poly, flat in ch["PARTS"]:
        k = count.get(region, 0); count[region] = k + 1
        d = DEPTH.get(region, 12) + 1.2 * k - (2 if ramp == "f" else 0); c = CENTRE.get(region, 0.0)
        sh, mid, lit = (P[x] for x in R[ramp])
        parts.append(dict(region=region, ramp=ramp, poly=poly, depth=d, centre=c, col=[sh, mid, lit], metal=ramp in METAL[name], flat=bool(flat)))
        m = mask(poly); front[m] = np.maximum(front[m], d / 2 - c)
    det = []
    for key, x0, y0, x1, y1 in ch["DETAILS"]:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if front[y, x] > -90: det.append([x, y, P[key], float(front[y, x]), key == "glow"])
    studs = [[x, y, P[key], float(front[y, x])] for key, x, y in ch["STUDS"] if front[y, x] > -90]
    out[name] = dict(parts=parts, details=det, studs=studs)
    print(name, len(parts), "parts,", len(det), "detail px,", len(studs), "studs")
json.dump(out, open("blender/set3d.json", "w"))
