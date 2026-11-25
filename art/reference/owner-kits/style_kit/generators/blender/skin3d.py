"""One continuous all-quad skin per character, skinned to a skeleton (python3 -I skin3d.py -- set3d.json <outdir> [names]).
1. The body parts (every slab except props) are joined and voxel-remeshed into one watertight quad shell (VOX, 0.016 m = mid density).
2. Colour moves onto the skin as data: each face takes the colour of the nearest source part, or of a detail plate or stud within
   DETAIL_REACH, as a face-corner colour attribute; "metal" and "glow" face attributes drive the material. (Bake to a texture on export
   if an engine needs one.)
3. A 17-bone skeleton is placed from the part regions (pelvis, spine, chest, neck, head, upper/lower arm and hand, thigh/shin/foot).
4. Weights: each vertex gets candidate bones from the region of its nearest source part, inverse-distance^4 to those bone segments,
   then SMOOTH passes over the mesh so joints bend softly; top 4 kept and normalised.
5. Props (sword, staff, dagger, shield) stay separate quad-remeshed rigid objects parented to the hand or forearm bone.
6. Renders rest and a test pose (arm raised, knee lifted, spine and head turned) and exports a skinned GLB."""
import bpy, bmesh, json, math, sys, bisect
import numpy as np
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree

CONFIG = {"S": 0.02, "VOX": 0.016, "DETAIL_REACH": 0.011, "SMOOTH": 6, "POW": 4, "SAMPLES": 32, "RES": (640, 640),
          "PROPS": {"sword", "staff", "dagger", "shield", "halberd", "pagoda"}, "SPEC": 0.12, "METALLIC": 0.35,
          "POSE": {"upperarm_R": ("Z", 75), "forearm_R": ("X", 40), "upperarm_L": ("Z", -30), "thigh_L": ("X", 40), "shin_L": ("X", -60),
                   "chest": ("Y", 12), "head": ("Y", -20)}}   # measured: outward is +Z on the right arm, -Z on the left; a forward lift is +X
argv = sys.argv[sys.argv.index("--") + 1:]
DATA = json.load(open(argv[0])); OUT = argv[1]; NAMES = argv[2].split(",") if len(argv) > 2 else ["knight", "mage", "rogue", "golem"]
S = CONFIG["S"]


def lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


def P3(x, y, d=0.0): return Vector(((x - 47.5) * S, d * S, (91.5 - y) * S))


def slab_bm(bm, poly, y0, y1):
    pts = [tuple(p) for i, p in enumerate(poly) if tuple(p) != tuple(poly[i - 1])]
    if len(pts) < 3: return False
    fr = [bm.verts.new(P3(x, y, y0)) for x, y in pts]; bk = [bm.verts.new(P3(x, y, y1)) for x, y in pts]
    try:
        bm.faces.new(fr); bm.faces.new(bk[::-1])
        for i in range(len(pts)): j = (i + 1) % len(pts); bm.faces.new((fr[i], fr[j], bk[j], bk[i]))
    except ValueError: return False
    return True


def obj_from_bm(name, bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); me = bpy.data.meshes.new(name); bm.to_mesh(me)
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); return ob


def remesh(ob):
    rm = ob.modifiers.new("q", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = CONFIG["VOX"]; rm.adaptivity = 0.0
    dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    ob.modifiers.clear(); old = ob.data; ob.data = me; bpy.data.meshes.remove(old)
    for f in me.polygons: f.use_smooth = True
    return ob


def skin_material():
    m = bpy.data.materials.new("skin"); nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    col = nt.nodes.new("ShaderNodeVertexColor"); col.layer_name = "col"
    met = nt.nodes.new("ShaderNodeAttribute"); met.attribute_name = "metal"
    glw = nt.nodes.new("ShaderNodeAttribute"); glw.attribute_name = "glow"
    mm = nt.nodes.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.inputs[1].default_value = CONFIG["METALLIC"]
    rg = nt.nodes.new("ShaderNodeMapRange"); rg.inputs["To Min"].default_value = 0.85; rg.inputs["To Max"].default_value = 0.55
    em = nt.nodes.new("ShaderNodeMath"); em.operation = "MULTIPLY"; em.inputs[1].default_value = 6.0
    L = nt.links
    L.new(col.outputs["Color"], b.inputs["Base Color"]); L.new(met.outputs["Fac"], mm.inputs[0]); L.new(mm.outputs[0], b.inputs["Metallic"])
    L.new(met.outputs["Fac"], rg.inputs["Value"]); L.new(rg.outputs["Result"], b.inputs["Roughness"])
    L.new(col.outputs["Color"], b.inputs["Emission Color"]); L.new(glw.outputs["Fac"], em.inputs[0]); L.new(em.outputs[0], b.inputs["Emission Strength"])
    b.inputs["Specular IOR Level"].default_value = CONFIG["SPEC"]
    return m


def flat_material(h, metal):
    m = bpy.data.materials.new("prop"); b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lin(h) + [1]; b.inputs["Metallic"].default_value = CONFIG["METALLIC"] if metal else 0
    b.inputs["Roughness"].default_value = 0.55 if metal else 0.85; b.inputs["Specular IOR Level"].default_value = CONFIG["SPEC"]
    return m


def regions_bbox(d):
    bb = {}
    for p in d["parts"]:
        xs = [v[0] for v in p["poly"]]; ys = [v[1] for v in p["poly"]]; r = p["region"]
        if r == "hand":   # both hands share one region name: split by side
            r = "hand_L" if sum(xs) / len(xs) < 47.5 else "hand_R"
        b = bb.setdefault(r, [999, 999, -999, -999])
        bb[r] = [min(b[0], min(xs)), min(b[1], min(ys)), max(b[2], max(xs)), max(b[3], max(ys))]
    return bb


def skeleton(name, bb):
    """bone list (name, head, tail, parent) in pixel space from the region boxes"""
    t = bb["torso"]; h = bb["head"]; mid = (t[1] + t[3]) / 2
    B = [("pelvis", (47.5, t[3] + 2), (47.5, mid), None), ("chest", (47.5, mid), (47.5, t[1]), "pelvis"),
         ("neck", (47.5, t[1]), (47.5, h[3] - 2), "chest"), ("head", (47.5, h[3] - 2), (47.5, h[1]), "neck")]
    for side, leg in (("L", "legL"), ("R", "legR")):
        l = bb[leg]; cx = (l[0] + l[2]) / 2; knee = (l[1] + l[3]) / 2
        B += [(f"thigh_{side}", (cx, l[1]), (cx, knee), "pelvis"), (f"shin_{side}", (cx, knee), (cx, l[3] - 4), f"thigh_{side}"),
              (f"foot_{side}", (cx, l[3] - 4), (cx, l[3] - 1), f"shin_{side}")]
    pts = {}
    for p in DATA[name]["parts"]: pts.setdefault(p["region"], []).extend(tuple(v) for v in p["poly"])
    for side, arm in (("L", "armL"), ("R", "armR")):
        if arm not in bb: continue
        a = bb[arm]; inner = a[2] if side == "L" else a[0]
        sh = (inner + (-3 if side == "L" else 3), min(max(t[1] + 6, a[1] + 2), a[3] - 2))   # shoulder: the arm's inner edge at chest height
        hd = bb.get(f"hand_{side}")
        if hd: wrist = ((hd[0] + hd[2]) / 2, hd[1] if hd[1] > sh[1] else hd[3])
        else:   # hand inside the arm region (the game suits): the arm point farthest from the shoulder, so raised arms work too
            far = max(pts[arm], key=lambda q: (q[0] - sh[0]) ** 2 + (q[1] - sh[1]) ** 2); wrist = (far[0] + (sh[0] - far[0]) * 0.15, far[1] + (sh[1] - far[1]) * 0.15)
        el = ((sh[0] + wrist[0]) / 2, (sh[1] + wrist[1]) / 2)
        dv = (wrist[0] - el[0], wrist[1] - el[1]); n = max(1e-6, (dv[0] ** 2 + dv[1] ** 2) ** 0.5)
        B += [(f"upperarm_{side}", sh, el, "chest"), (f"forearm_{side}", el, wrist, f"upperarm_{side}"),
              (f"hand_{side}", wrist, (wrist[0] + dv[0] / n * 6, wrist[1] + dv[1] / n * 6), f"forearm_{side}")]
    return B


GROUP = {"armL": "armL", "hand_L": "armL", "pauL": "armL", "armR": "armR", "hand_R": "armR", "pauR": "armR", "legL": "legL", "legR": "legR"}
CAND = {"legL": ["thigh_L", "shin_L", "foot_L", "pelvis"], "legR": ["thigh_R", "shin_R", "foot_R", "pelvis"], "skirt": ["pelvis", "thigh_L", "thigh_R"],
        "torso": ["pelvis", "chest", "neck"], "head": ["head", "neck"], "pauL": ["upperarm_L"], "pauR": ["upperarm_R"],
        "armL": ["upperarm_L", "forearm_L"], "armR": ["upperarm_R", "forearm_R"],   # arm shells are separate from the core: no chest weight, so nothing tears "hand_L": ["hand_L", "forearm_L"],
        "hand_R": ["hand_R", "forearm_R"], "mantle": ["chest", "upperarm_L", "upperarm_R"]}


def seg_dist(P, A, Bq):
    ab = Bq - A; t = np.clip(((P - A) @ ab) / max(ab @ ab, 1e-9), 0, 1); return np.linalg.norm(P - (A + np.outer(t, ab)), axis=1)


def build(name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    d = DATA[name]; bb = regions_bbox(d)
    # sources: body slabs into one bmesh (face -> part index), props into their own objects
    body = bmesh.new(); starts, regs, cols, metals = [], [], [], []; props = []; groups = {}; gstarts, gregs = {}, {}
    for i, p in enumerate(d["parts"]):
        c, dep = p["centre"], p["depth"]
        if p["region"] in CONFIG["PROPS"]: props.append(p); continue
        n0 = len(body.faces)
        if slab_bm(body, p["poly"], -(dep / 2 - c), dep / 2 + c):
            r = p["region"]
            if r == "hand": xs = [v[0] for v in p["poly"]]; r = "hand_L" if sum(xs) / len(xs) < 47.5 else "hand_R"
            starts.append(n0); regs.append(r); cols.append(p["col"][1]); metals.append(p["metal"])
            g = GROUP.get(r, "core"); gb = groups.setdefault(g, bmesh.new()); gstarts.setdefault(g, []).append(len(gb.faces)); gregs.setdefault(g, []).append(r)
            slab_bm(gb, p["poly"], -(dep / 2 - c), dep / 2 + c)
    body.faces.ensure_lookup_table()
    # one quad shell per group (core, each arm with its shoulder plate, each leg), combined into one mesh: limbs overlap the core like armour
    comb = bmesh.new(); gbvh = {}; vgroup = []
    for g, gb in groups.items():
        gb.faces.ensure_lookup_table(); gbvh[g] = BVHTree.FromBMesh(gb)
        sh = remesh(obj_from_bm(f"{name}_{g}", gb)); vgroup += [g] * len(sh.data.vertices); comb.from_mesh(sh.data); bpy.data.objects.remove(sh)
    src = obj_from_bm(f"{name}_src", comb)
    bvh_body = BVHTree.FromBMesh(body)
    # details and studs as colour sources
    det = bmesh.new(); dstart, dcol, dglow = [], [], []
    for x, y, col, fy, glow in d["details"]:
        dstart.append(len(det.faces)); dcol.append(col); dglow.append(glow)
        v = [det.verts.new(P3(x + ox, y + oy, -(fy + 0.4))) for ox, oy in ((-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5))]; det.faces.new(v)
    for x, y, col, fy in d["studs"]:
        dstart.append(len(det.faces)); dcol.append(col); dglow.append(False)
        v = [det.verts.new(P3(x + ox, y + oy, -(fy + 0.6))) for ox, oy in ((-.6, -.6), (.6, -.6), (.6, .6), (-.6, .6))]; det.faces.new(v)
    bvh_det = BVHTree.FromBMesh(det)
    # the skin
    skin = src; skin.name = f"{name}_skin"; me = skin.data
    for f in me.polygons: f.use_smooth = True
    ca = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER"); fm = me.attributes.new("metal", "FLOAT", "FACE"); fg = me.attributes.new("glow", "FLOAT", "FACE")
    for f in me.polygons:
        c = f.center; hit = bvh_det.find_nearest(c); colh, metal, glow = None, 0.0, 0.0
        if hit[0] is not None and hit[3] < CONFIG["DETAIL_REACH"]:
            k = bisect.bisect_right(dstart, hit[2]) - 1; colh = dcol[k]; glow = 1.0 if dglow[k] else 0.0; metal = 0.0 if glow else 1.0
        else:
            k = bisect.bisect_right(starts, bvh_body.find_nearest(c)[2]) - 1; colh = cols[k]; metal = 1.0 if metals[k] else 0.0
        rgb = lin(colh) + [1.0]
        for li in f.loop_indices: ca.data[li].color = rgb
        fm.data[f.index].value = metal; fg.data[f.index].value = glow
    me.materials.append(skin_material())
    # skeleton
    bones = skeleton(name, bb)
    ad = bpy.data.armatures.new(f"{name}_rig"); arm = bpy.data.objects.new(f"{name}_rig", ad); bpy.context.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode="EDIT")
    for bn, h, t, par in bones:
        eb = ad.edit_bones.new(bn); eb.head = P3(*h); eb.tail = P3(*t); eb.align_roll(Vector((0, -1, 0)))
        if par: eb.parent = ad.edit_bones[par]; eb.use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")
    # weights
    V = np.array([v.co[:] for v in me.vertices]); names = [b[0] for b in bones]; NB = len(names)
    A = np.array([P3(*b[1])[:] for b in bones]); Bt = np.array([P3(*b[2])[:] for b in bones])
    D = np.stack([seg_dist(V, A[j], Bt[j]) for j in range(NB)], axis=1)
    def region_in_group(i, v):   # a shell's weights come only from its own group's parts (the golem's fist touches its thigh)
        g = vgroup[i]; return gregs[g][bisect.bisect_right(gstarts[g], gbvh[g].find_nearest(Vector(v))[2]) - 1]
    reg_of = np.array([region_in_group(i, v) for i, v in enumerate(V)])
    W = np.zeros((len(V), NB))
    for r in set(reg_of.tolist()):
        cand = [names.index(c) for c in CAND.get(r, ["chest"]) if c in names]; m = reg_of == r
        W[np.ix_(m, cand)] = 1.0 / (D[np.ix_(m, cand)] + 1e-3) ** CONFIG["POW"]
    W /= W.sum(1, keepdims=True)
    E = np.array([e.vertices[:] for e in me.edges]); deg = np.bincount(E.ravel(), minlength=len(V)).astype(float)
    for _ in range(CONFIG["SMOOTH"]):
        acc = np.zeros_like(W); np.add.at(acc, E[:, 0], W[E[:, 1]]); np.add.at(acc, E[:, 1], W[E[:, 0]])
        W = 0.5 * W + 0.5 * acc / np.maximum(deg, 1)[:, None]
    top = np.argsort(-W, 1)[:, :4]; Wk = np.take_along_axis(W, top, 1); Wk /= Wk.sum(1, keepdims=True)
    groups = {n: skin.vertex_groups.new(name=n) for n in names}
    for vi in range(len(V)):
        for j, w in zip(top[vi], Wk[vi]):
            if w > 0.004: groups[names[j]].add([vi], float(w), "REPLACE")
    skin.parent = arm; mod = skin.modifiers.new("rig", "ARMATURE"); mod.object = arm
    # props: rigid quad objects on the nearest hand or forearm
    for p in props:
        bm = bmesh.new(); c, dep = p["centre"], p["depth"]; slab_bm(bm, p["poly"], -(dep / 2 - c), dep / 2 + c)
        ob = remesh(obj_from_bm(f"{name}_{p['region']}", bm)); ob.data.materials.append(flat_material(p["col"][1], p["metal"]))
        cx = sum(v[0] for v in p["poly"]) / len(p["poly"]); side = "L" if cx < 47.5 else "R"
        bn = (f"forearm_{side}" if p["region"] == "shield" else f"hand_{side}")
        if bn not in names: bn = "chest"
        bpy.context.view_layer.update(); bone = ad.bones[bn]
        ob.parent = arm; ob.parent_type = "BONE"; ob.parent_bone = bn
        ob.matrix_parent_inverse = (arm.matrix_world @ bone.matrix_local @ Matrix.Translation((0, bone.length, 0))).inverted()
    return arm, skin


def stage(res):
    sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = CONFIG["SAMPLES"]; sc.cycles.use_denoising = True
    sc.view_settings.view_transform = "Standard"; sc.render.resolution_x, sc.render.resolution_y = res
    w = bpy.data.worlds.new("w"); w.node_tree.nodes["Background"].inputs[0].default_value = (0.018, 0.02, 0.026, 1); sc.world = w
    for nm, loc, pw, sz in (("key", (-2.2, -3.2, 3.6), 650, 2.0), ("fill", (2.6, -2.4, 1.0), 180, 3.0), ("rim", (0.8, 3.0, 3.0), 700, 1.5)):
        ld = bpy.data.lights.new(nm, "AREA"); ld.energy = pw; ld.size = sz; lo = bpy.data.objects.new(nm, ld); lo.location = loc
        sc.collection.objects.link(lo); lo.rotation_euler = (Vector((0, 0, 0.9)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.mesh.primitive_plane_add(size=40); fl = bpy.context.object; fl.data.materials.append(flat_material("#1a232b", False))
    cd = bpy.data.cameras.new("cam"); cd.lens = 55; co = bpy.data.objects.new("cam", cd); sc.collection.objects.link(co)
    t = Vector((0, 0, 0.92)); y, p = math.radians(-28), math.radians(12)
    co.location = t + Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p))) * 4.6
    co.rotation_euler = (t - co.location).to_track_quat("-Z", "Y").to_euler(); sc.camera = co
    return sc


def pose(arm, on):
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = Quaternion()
        if on and pb.name in CONFIG["POSE"]:
            ax, deg = CONFIG["POSE"][pb.name]; pb.rotation_quaternion = Quaternion(Vector({"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}[ax]), math.radians(deg))
    bpy.context.view_layer.update()


if __name__ == "__main__":
    for name in NAMES:
        arm, skin = build(name)
        me = skin.data; q = sum(1 for f in me.polygons if f.loop_total == 4)
        nowt = sum(1 for v in me.vertices if not v.groups)
        print(f"SKIN {name}: faces {len(me.polygons)}, quads {q} ({q / len(me.polygons) * 100:.1f}%), verts {len(me.vertices)}, unweighted {nowt}, bones {len(arm.data.bones)}", flush=True)
        sc = stage(CONFIG["RES"])
        for on in (False, True):
            pose(arm, on); sc.render.filepath = f"{OUT}/skin_{name}_{'pose' if on else 'rest'}.png"; bpy.ops.render.render(write_still=True)
        pose(arm, False)
        bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/skin_{name}.blend")
        try:
            bpy.ops.object.select_all(action="DESELECT")
            for ob in bpy.context.scene.objects:
                if ob.name.startswith(name): ob.select_set(True)
            bpy.ops.export_scene.gltf(filepath=f"{OUT}/skin_{name}.glb", export_format="GLB", use_selection=True)
            print("GLB", name, flush=True)
        except Exception as e: print("GLB failed", name, e, flush=True)
