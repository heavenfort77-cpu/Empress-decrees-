"""Builds the four set characters in 3D from their part data and renders them with Cycles (python3 -I blender/set3d_render.py <json> <outdir>).
Every 2D part becomes a bevelled slab (x from the sprite, z up from the feet row, depth by region), so the 3D figure is the approved design
with real volume. Materials take the part's ramp mid colour (metal for steel and bronze plates); details are thin plates on the surface,
glow details emit; studs are small metal domes. Key light upper left (the style's light), rim from behind, dark stone floor."""
import bpy, bmesh, json, math, sys
from mathutils import Vector

CONFIG = {
    "S": 0.02, "BEVEL": 0.35, "LEVELS": {"low": 0.032, "mid": 0.016, "high": 0.008},   # voxel size (m) of the quad remesh; 0.02 m = one sprite pixel
    "SPEC": 0.12, "ROUGH_METAL": 0.55, "ROUGH_MATTE": 0.85, "METALLIC": 0.35, "STUD_ROUGH": 0.5, "SAMPLES": 32, "RES": (768, 768), "LINEUP_RES": (1600, 720),
    "KEY": ((-2.2, -3.2, 3.6), 650, 2.0), "FILL": ((2.6, -2.4, 1.0), 180, 3.0), "RIM": ((0.8, 3.0, 3.0), 700, 1.5),
    "FLOOR": "#1a232b", "WORLD": (0.018, 0.02, 0.026), "ORDER": ["knight", "mage", "rogue", "golem"], "GAP": 1.55,
}
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
DATA = json.load(open(argv[0])); OUT = argv[1]
S = CONFIG["S"]


def lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]


MATS = {}
MATS_LAST = [None]
def mat(col, metal=False, glow=False, rough=None):
    key = (col, metal, glow, rough)
    if key in MATS: return MATS[key]
    m = bpy.data.materials.new(f"m{len(MATS)}"); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lin(col)
    b.inputs["Metallic"].default_value = CONFIG["METALLIC"] if metal else 0.0
    b.inputs["Roughness"].default_value = rough if rough is not None else (CONFIG["ROUGH_METAL"] if metal else CONFIG["ROUGH_MATTE"])
    b.inputs["Specular IOR Level"].default_value = CONFIG["SPEC"]   # low specular: no hot highlights
    if glow:
        b.inputs["Emission Color"].default_value = lin(col); b.inputs["Emission Strength"].default_value = 6.0
    MATS[key] = m; return m


def to3(x, y, ox): return ((x - 47.5) * S + ox, (91.5 - y) * S)


def slab(name, poly, y0, y1, ox, m):
    pts = [p for i, p in enumerate(poly) if p != poly[i - 1]]
    if len(pts) < 3: return None
    bm = bmesh.new()
    fr = [bm.verts.new((to3(x, y, ox)[0], y0 * S, to3(x, y, ox)[1])) for x, y in pts]
    bk = [bm.verts.new((to3(x, y, ox)[0], y1 * S, to3(x, y, ox)[1])) for x, y in pts]
    try:
        bm.faces.new(fr); bm.faces.new(bk[::-1])
        for i in range(len(pts)):
            j = (i + 1) % len(pts); bm.faces.new((fr[i], fr[j], bk[j], bk[i]))
    except ValueError:
        bm.free(); return None
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.data.materials.append(m); MATS_LAST[:] = [m]
    return quadify(ob)


VOX = {"size": 0.016}
STATS = {"faces": 0, "quads": 0}
def quadify(ob):
    """voxel remesh to an all-quad shell at VOX size, applied, smooth shaded"""
    rm = ob.modifiers.new("quads", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = VOX["size"]; rm.adaptivity = 0.0; rm.use_smooth_shade = True
    dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    ob.modifiers.clear(); old = ob.data; ob.data = me; bpy.data.meshes.remove(old)
    if not me.materials: me.materials.append(MATS_LAST[0])
    for f in me.polygons: f.use_smooth = True
    STATS["faces"] += len(me.polygons); STATS["quads"] += sum(1 for f in me.polygons if f.loop_total == 4)
    return ob


def plates(name, items, ox, m, thick=0.5):
    """detail pixels merged into horizontal runs, one mesh per colour"""
    bm = bmesh.new()
    rows = {}
    for x, y, fy in items: rows.setdefault((y, round(fy, 1)), []).append(x)
    for (y, fy), xs in rows.items():
        xs.sort(); runs = [[xs[0], xs[0]]]
        for x in xs[1:]:
            if x == runs[-1][1] + 1: runs[-1][1] = x
            else: runs.append([x, x])
        for a, b in runs:
            x0, z1 = to3(a - 0.5, y - 0.5, ox); x1, z0 = to3(b + 0.5, y + 0.5, ox); yf = -(fy + thick) * S; yb = -(fy - 0.2) * S
            v = [bm.verts.new(c) for c in ((x0, yf, z0), (x1, yf, z0), (x1, yf, z1), (x0, yf, z1), (x0, yb, z0), (x1, yb, z0), (x1, yb, z1), (x0, yb, z1))]
            for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)): bm.faces.new([v[i] for i in f])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.data.materials.append(m)
    STATS["faces"] += len(me.polygons); STATS["quads"] += sum(1 for f in me.polygons if f.loop_total == 4)


def quad_sphere():
    """unit quad sphere: a cube subdivided once with grid fill (24 quads), pushed onto the sphere"""
    t = bmesh.new(); bmesh.ops.create_cube(t, size=1.0)
    bmesh.ops.subdivide_edges(t, edges=t.edges[:], cuts=1, use_grid_fill=True)
    for v in t.verts: v.co = v.co.normalized()
    t.verts.index_update(); out = ([v.co.copy() for v in t.verts], [[v.index for v in f.verts] for f in t.faces]); t.free(); return out
QSPHERE = quad_sphere()


def studs(name, items, ox, m):
    bm = bmesh.new()
    for x, y, fy in items:
        cx, cz = to3(x, y, ox)
        cen = Vector((cx, -(fy + 0.1) * S, cz)); vmap = [bm.verts.new(cen + p * 0.7 * S) for p in QSPHERE[0]]
        for f in QSPHERE[1]: bm.faces.new([vmap[i] for i in f])           # quad sphere: every face is a quad
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for f in me.polygons: f.use_smooth = True
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.data.materials.append(m)
    STATS["faces"] += len(me.polygons); STATS["quads"] += sum(1 for f in me.polygons if f.loop_total == 4)


def wire_on(dark="#0d1418"):
    """show the topology: a thin wireframe over every remeshed part (material slot 2)"""
    wm = mat(dark, rough=0.9)
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH" or ob.name.startswith("Plane") or "_stud_" in ob.name or "_det_" in ob.name: continue
        ob.data.materials.append(wm); w = ob.modifiers.new("wire", "WIREFRAME"); w.thickness = 0.0016
        w.use_replace = False; w.material_offset = 1; w.use_even_offset = True


def build(name, ox):
    d = DATA[name]
    for i, p in enumerate(d["parts"]):
        c, dep = p["centre"], p["depth"]
        slab(f"{name}_{i}_{p['region']}", [tuple(v) for v in p["poly"]], -(dep / 2 - c), dep / 2 + c, ox,
             mat(p["col"][1], metal=p["metal"], rough=0.9 if p["ramp"] == "f" else None))
    by = {}
    for x, y, col, fy, glow in d["details"]: by.setdefault((col, glow), []).append((x, y, fy))
    for (col, glow), items in by.items(): plates(f"{name}_det_{col}", items, ox, mat(col, metal=not glow, glow=glow))
    bs = {}
    for x, y, col, fy in d["studs"]: bs.setdefault(col, []).append((x, y, fy))
    for col, items in bs.items(): studs(f"{name}_stud_{col}", items, ox, mat(col, metal=True, rough=0.25))


def scene_setup():
    bpy.ops.wm.read_factory_settings(use_empty=True); MATS.clear()
    sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = CONFIG["SAMPLES"]
    sc.cycles.use_denoising = True; sc.view_settings.view_transform = "Standard"; sc.render.film_transparent = False
    w = bpy.data.worlds.new("w"); w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (*CONFIG["WORLD"], 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.0; sc.world = w
    for nm, (loc, power, size) in (("key", CONFIG["KEY"]), ("fill", CONFIG["FILL"]), ("rim", CONFIG["RIM"])):
        ld = bpy.data.lights.new(nm, "AREA"); ld.energy = power; ld.size = size
        lo = bpy.data.objects.new(nm, ld); lo.location = loc; sc.collection.objects.link(lo)
        lo.rotation_euler = (Vector((0, 0, 0.9)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0)); fl = bpy.context.object
    fl.data.materials.append(mat(CONFIG["FLOOR"], rough=0.85))
    return sc


def camera(sc, target, dist, yaw, pitch, lens=55, res=(768, 768)):
    cd = bpy.data.cameras.new("cam"); cd.lens = lens; co = bpy.data.objects.new("cam", cd); sc.collection.objects.link(co)
    t = Vector(target); y, p = math.radians(yaw), math.radians(pitch)
    co.location = t + Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p))) * dist
    co.rotation_euler = (t - co.location).to_track_quat("-Z", "Y").to_euler(); sc.camera = co
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    return co


def render(sc, path):
    sc.render.filepath = path; bpy.ops.render.render(write_still=True); print("wrote", path, flush=True)


def levels(name):
    """the same character at each quad density, shaded and with its wireframe, plus a face count report"""
    rows = []
    for lv, size in CONFIG["LEVELS"].items():
        VOX["size"] = size
        for wire in (False, True):
            STATS.update(faces=0, quads=0); sc = scene_setup(); build(name, 0.0)
            if wire: wire_on()
            camera(sc, (0, 0, 0.92), 4.6, -28, 12, res=(640, 640)); render(sc, f"{OUT}/set3dq_{name}_{lv}{'_wire' if wire else ''}.png")
            if not wire: rows.append((lv, size, STATS["faces"], STATS["quads"]))
    for lv, size, f, q in rows: print(f"LEVEL {name} {lv} voxel {size} m: faces {f}, quads {q} ({q / max(1, f) * 100:.1f}%)", flush=True)


if __name__ == "__main__":
    mode = argv[2] if len(argv) > 2 else "all"
    if mode == "levels":
        levels(argv[3] if len(argv) > 3 else "knight"); sys.exit(0)
    if mode in ("all", "single"):
        for name in CONFIG["ORDER"]:
            sc = scene_setup(); build(name, 0.0)
            camera(sc, (0, 0, 0.92), 4.6, -28, 12); render(sc, f"{OUT}/set3d_{name}_34.png")
            if mode == "single": bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/set3d_{name}.blend")
    if mode in ("all", "lineup"):
        sc = scene_setup(); n = len(CONFIG["ORDER"])
        for i, name in enumerate(CONFIG["ORDER"]): build(name, (i - (n - 1) / 2) * CONFIG["GAP"])
        camera(sc, (0, 0, 0.85), 10.2, -16, 9, lens=50, res=CONFIG["LINEUP_RES"]); render(sc, f"{OUT}/set3dq_lineup_mid.png"); print(f"LINEUP faces {STATS['faces']} quads {STATS['quads']}", flush=True)
        bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/set3dq_lineup_mid.blend")
