"""
Blender 4.x: Konzept I „Grüne Adern", Variante A – Arbeitsmodell (weiß, Freestyle-Linien) als Basis für KI-Renderings.
  --render [--nur a,b] [--klein]   Perspektiven aus szene_k1.json (Bild mit Linien) -> 3d/k1_<name>.png
  --export                         .blend + FBX/OBJ je Baustein -> export_3d/
Aufruf: blender -b --python blender_k1.py -- --render
"""
import bpy, bmesh, json, math, os, sys, random
from mathutils import Vector, Matrix

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODUS = "--export" if "--export" in ARGS else "--render"
HIER = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HIER, "3d")
K2 = "--k2" in ARGS
S = json.load(open(os.path.join(OUT, "szene_k2.json" if K2 else "szene_k1.json")))
PRE = "k2_" if K2 else "k1_"
EG_H, OG_H = 4.2, 3.1
rnd = random.Random(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = "METRIC"


def rgb(h):
    h = h.lstrip("#")
    return tuple((int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4)) + (1,)


MATS = {}


def mat(name, farbe, rough=0.9, alpha=1.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgb(farbe)
    b.inputs["Roughness"].default_value = rough
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
    m.diffuse_color = rgb(farbe)
    MATS[name] = m
    return m


def koll(name):
    c = bpy.data.collections.new(name)
    sc.collection.children.link(c)
    return c


def obj(name, bm, mats, c):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    c.objects.link(ob)
    return ob


def prisma(bm, ring, z0, z1, mi=0, deckel=True):
    if len(ring) < 3:
        return
    a = sum(ring[i][0] * ring[(i + 1) % len(ring)][1] - ring[(i + 1) % len(ring)][0] * ring[i][1] for i in range(len(ring)))
    if a < 0:
        ring = ring[::-1]
    u = [bm.verts.new((x, y, z0)) for x, y in ring]
    o = [bm.verts.new((x, y, z1)) for x, y in ring]
    n = len(ring)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((u[i], u[j], o[j], o[i])).material_index = mi
    if deckel:
        try:
            bm.faces.new(o).material_index = mi
        except ValueError:
            pass


# ---------------- Flächen ----------------
FARBE = dict(umgebung="#ece9e2", feld="#d9e3c4", asphalt="#b9b6b0", pflaster="#e3ded4", platz="#e8dfcf", garten="#dfe6cc",
             privatgarten="#d3ddb8", wiese="#c5d9a4", wald="#a9c68a", weg="#efe7d6", wasser="#8fc0d6", bruecke="#b8d09a")
FL = koll("Freiraum")
for i, fl in enumerate(S["flaechen"]):
    bm = bmesh.new()
    v, f = fl["v"], fl["f"]
    vs = [bm.verts.new((v[k], v[k + 1], fl["z"])) for k in range(0, len(v), 2)]
    for k in range(0, len(f), 3):
        try:
            bm.faces.new((vs[f[k]], vs[f[k + 1]], vs[f[k + 2]]))
        except ValueError:
            pass
    if fl["art"] == "bruecke":            # Brückendeck mit Stärke
        r = bmesh.ops.extrude_face_region(bm, geom=list(bm.faces))
        bmesh.ops.translate(bm, vec=(0, 0, -1.8), verts=[e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)])
    obj(f"fl_{fl['art']}_{i}", bm, [mat("fl_" + fl["art"], FARBE[fl["art"]], 0.15 if fl["art"] == "wasser" else 0.95)], FL)

# ---------------- Station: Grube, Gleise, Bahnsteig, Halle, Dach, Kioske ----------------
STN = koll("Station")
st = S["station"]
bm = bmesh.new()
for r in st["grube"]:
    prisma(bm, r, -7.5, -7.5, 0, True)
    a = sum(r[i][0] * r[(i + 1) % len(r)][1] - r[(i + 1) % len(r)][0] * r[i][1] for i in range(len(r)))
    rr = r if a > 0 else r[::-1]
    for i in range(len(rr)):                      # Wände nach innen
        j = (i + 1) % len(rr)
        q = [bm.verts.new((rr[i][0], rr[i][1], -7.5)), bm.verts.new((rr[j][0], rr[j][1], -7.5)),
             bm.verts.new((rr[j][0], rr[j][1], 0)), bm.verts.new((rr[i][0], rr[i][1], 0))]
        bm.faces.new(q[::-1]).material_index = 1
obj("einschnitt", bm, [mat("schotter", "#a9a39a"), mat("stuetzwand", "#cbc6bd")], STN)
bm = bmesh.new()
for g in st["gleise"]:
    (x0, y0), (x1, y1) = g
    L = math.hypot(x1 - x0, y1 - y0)
    ang = math.atan2(y1 - y0, x1 - x0)
    for d in (-0.75, 0.75):
        m = Matrix.Translation(((x0 + x1) / 2 - math.sin(ang) * d, (y0 + y1) / 2 + math.cos(ang) * d, -7.35)) @ \
            Matrix.Rotation(ang, 4, "Z") @ Matrix.Diagonal((L, 0.12, 0.2, 1))
        bmesh.ops.create_cube(bm, size=1, matrix=m)
obj("gleise", bm, [mat("stahl", "#6c6a66", 0.4)], STN)
bm = bmesh.new()
prisma(bm, st["bahnsteig"], -7.5, -6.5, 0)
prisma(bm, st["deckel"], -1.4, 0.0, 1, False)
prisma(bm, st["halle"], -1.6, 0.4, 1)                     # Brückendeck
for k in st["kioske"]:
    prisma(bm, k, 0.3, 3.6, 0)
prisma(bm, st["radstation"], -7.5, 0.3, 0)
obj("station_massiv", bm, [mat("weiss_station", "#f4f2ee"), mat("beton", "#d5d1c9")], STN)
# Halle: Glasvolumen 6 m auf der Brücke
bm = bmesh.new()
prisma(bm, st["halle"], 0.4, 6.4, 0)
obj("halle_glas", bm, [mat("glas", "#b9d3df", 0.08, 0.35)], STN)
if st.get("dach_grid"):
    bm = bmesh.new()
    gr = st["dach_grid"]
    vs = [[bm.verts.new(tuple(p)) for p in row] for row in gr]
    for i in range(len(vs) - 1):
        for j in range(len(vs[0]) - 1):
            bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    me_d = obj("dach_diagrid", bm, [mat("holz", "#c89b64", 0.6)], STN)
    wf = me_d.modifiers.new("Diagrid", "WIREFRAME")
    wf.thickness = 0.5
    huelle = me_d.copy()
    huelle.data = me_d.data.copy()
    huelle.modifiers.clear()
    huelle.name = "dach_huelle"
    huelle.data.materials[0] = mat("dachglas", "#dfe9ee", 0.1, 0.25)
    STN.objects.link(huelle)
    d = [gr[i][0][:2] for i in range(len(gr))] + [gr[i][-1][:2] for i in range(len(gr) - 1, -1, -1)]
    cx = sum(p[0] for p in d) / len(d)
    cy = sum(p[1] for p in d) / len(d)
else:
    # Dach: Ellipsen-Kuppel als Raster, Diagrid über Wireframe-Modifier, Hülle halbtransparent
    d = st["dach"]
    cx = sum(p[0] for p in d) / len(d)
    cy = sum(p[1] for p in d) / len(d)
    bm = bmesh.new()
    ringe = 9
    verts = []
    for k in range(ringe + 1):
        t = k / ringe
        reihe = []
        for p in d:
            x = cx + (p[0] - cx) * (1 - t * 0.97)
            y = cy + (p[1] - cy) * (1 - t * 0.97)
            z = 6.0 + 12.0 * math.sin(t * math.pi / 2)
            reihe.append(bm.verts.new((x, y, z)))
        verts.append(reihe)
    n = len(d)
    for k in range(ringe):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((verts[k][i], verts[k][j], verts[k + 1][j], verts[k + 1][i]))
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    me_d = obj("dach_diagrid", bm, [mat("holz", "#c89b64", 0.6)], STN)
    wf = me_d.modifiers.new("Diagrid", "WIREFRAME")
    wf.thickness = 0.45
    huelle = me_d.copy()
    huelle.data = me_d.data.copy()
    huelle.modifiers.clear()
    huelle.name = "dach_huelle"
    huelle.data.materials[0] = mat("dachglas", "#dfe9ee", 0.1, 0.25)
    STN.objects.link(huelle)

# Stützen der Halle (Baumstützen)
bm = bmesh.new()
for p in d[:: max(1, len(d) // (14 if K2 else 10))]:
    x, y = cx + (p[0] - cx) * 0.9, cy + (p[1] - cy) * 0.9
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.35, radius2=0.25, depth=6.4,
                          matrix=Matrix.Translation((x, y, 3.2)))
obj("stuetzen", bm, [mat("holz", "#c89b64")], STN)

if K2 and S.get("ufer"):
    uf = S["ufer"]
    bm = bmesh.new()
    r = uf["bucht"]
    a2 = sum(r[i][0] * r[(i + 1) % len(r)][1] - r[(i + 1) % len(r)][0] * r[i][1] for i in range(len(r)))
    rr = r if a2 > 0 else r[::-1]
    for i in range(len(rr)):
        j = (i + 1) % len(rr)
        q = [bm.verts.new((rr[i][0], rr[i][1], -2.6)), bm.verts.new((rr[j][0], rr[j][1], -2.6)),
             bm.verts.new((rr[j][0], rr[j][1], 0)), bm.verts.new((rr[i][0], rr[i][1], 0))]
        bm.faces.new(q[::-1])
    obj("bucht_wand", bm, [mat("spundwand", "#8d8a84", 0.5)], STN)
    bm = bmesh.new()
    prisma(bm, r, -1.0, -1.0, 0)
    obj("bucht_wasser", bm, [mat("fl_wasser", "#8fc0d6", 0.15)], STN)
    bm = bmesh.new()
    prisma(bm, uf["badeschiff"], -1.6, 0.4, 0)
    obj("badeschiff", bm, [mat("weiss_station", "#f4f2ee")], STN)
    k = uf["kran"]
    bm = bmesh.new()
    for p in k:                                            # vier Stützen, Träger oben: Portalkran 16 m
        bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation((p[0], p[1], 8)) @ Matrix.Diagonal((0.9, 0.9, 16, 1)))
    prisma(bm, k, 15.0, 16.8, 0)
    obj("portalkran", bm, [mat("kranrot", "#b9473b", 0.5)], STN)

# ---------------- Gebäude ----------------
GB = koll("Bebauung")
WAND = {"A": "#efe6dc", "1": "#e9e9e6", "2": "#f1ebe1", "3": "#efe4d2", "4": "#eee8da", "5": "#efe3d6"}
SONDER = {"markthalle": "#e6d5bd", "werkhalle": "#dedcd6", "sporthalle": "#e7e3da", "gartenhalle": "#d9e6d0", "foodlab": "#d9e6d0",
          "wasserhaus": "#d8e3e6", "kita": "#f0e3c8", "pavillon": "#f0e3c8", "hochpunkt": "#f6f3ee", "glashaus": "#dfeee4",
          "schule": "#f2ead8", "finger": "#efe3d6", "stadthaus": "#efe4d2"}
wm = [mat("wand_" + q, c) for q, c in WAND.items()] + [mat("wand_" + t, c) for t, c in SONDER.items()]
idx = {k: i for i, k in enumerate(list(WAND) + list(SONDER))}
bw, bd, bf = bmesh.new(), bmesh.new(), bmesh.new()
for h in S["haeuser"]:
    mi = idx[h["typ"]] if h["typ"] in SONDER else idx[h["q"]]
    prisma(bw, h["ring"], 0, h["h"], mi, deckel=False)
    try:
        f = bd.faces.new([bd.verts.new((x, y, h["h"])) for x, y in h["ring"]])
        f.material_index = 1 if h["typ"] in ("gartenhalle", "foodlab") else 0
    except ValueError:
        pass
    # Fenster: Achsen 3,3 m, je Geschoss; EG publikum/gastro = Schaufenster
    r = h["ring"]
    a = sum(r[i][0] * r[(i + 1) % len(r)][1] - r[(i + 1) % len(r)][0] * r[i][1] for i in range(len(r)))
    r = r if a > 0 else r[::-1]
    for i in range(len(r)):
        (x0, y0), (x1, y1) = r[i], r[(i + 1) % len(r)]
        L = math.hypot(x1 - x0, y1 - y0)
        if L < 3:
            continue
        tx, ty = (x1 - x0) / L, (y1 - y0) / L
        nx, ny = ty, -tx
        ach = max(1, int(L / 3.3))
        t = L / ach
        for k in range(h["g"]):
            z0 = 0 if k == 0 else EG_H + (k - 1) * OG_H
            schau = k == 0 and h["eg"] != "wohnen"
            za, zb, w = (z0 + 0.3, z0 + 3.6, t - 0.5) if schau else (z0 + 0.9, z0 + 2.5, min(1.5, t - 0.8))
            for s in range(ach):
                mx, my = x0 + tx * t * (s + 0.5) + nx * 0.05, y0 + ty * t * (s + 0.5) + ny * 0.05
                q = [bf.verts.new((mx - tx * w / 2, my - ty * w / 2, za)), bf.verts.new((mx + tx * w / 2, my + ty * w / 2, za)),
                     bf.verts.new((mx + tx * w / 2, my + ty * w / 2, zb)), bf.verts.new((mx - tx * w / 2, my - ty * w / 2, zb))]
                bf.faces.new(q).material_index = 1 if schau else 0
obj("waende", bw, wm, GB)
obj("daecher", bd, [mat("dach", "#d8d3c9"), mat("glasdach", "#cfe3e8", 0.1)], GB)
obj("fenster", bf, [mat("fenster", "#6d7d8a", 0.25), mat("schaufenster", "#9fbccb", 0.15)], GB)
KT = koll("Kontext")
bm = bmesh.new()
for h in S["kontext"]:
    prisma(bm, h["ring"], 0, h["h"], 0)
obj("kontext", bm, [mat("kontext", "#d6d3cd")], KT)

# ---------------- Bäume ----------------
BA = koll("Baeume")
bm = bmesh.new()
for x, y, hh in S["baeume"]:
    r = max(2.2, hh * 0.28) * rnd.uniform(0.85, 1.15)
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.22, radius2=0.15, depth=hh - r,
                          matrix=Matrix.Translation((x, y, (hh - r) / 2)))
    res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r, matrix=Matrix.Translation((x, y, hh - r * 0.75)) @ Matrix.Diagonal((1, 1, 0.85, 1)))
    for v in res["verts"]:
        for f in v.link_faces:
            f.material_index = 1 + (int(x * 7 + y * 3) % 3)
obj("baeume", bm, [mat("stamm", "#7a6a58"), mat("laub0", "#9dbb7c"), mat("laub1", "#a9c48a"), mat("laub2", "#8fb06f")], BA)

# ---------------- Licht, Kamera, Linien ----------------
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.use_denoising = False
sc.cycles.max_bounces = 4
sc.cycles.diffuse_bounces = 2
sc.cycles.transparent_max_bounces = 12
w = bpy.data.worlds.new("Himmel")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.93, 0.95, 0.97, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
sonne = bpy.data.objects.new("Sonne", bpy.data.lights.new("Sonne", "SUN"))
sonne.data.energy = 4.6
sonne.data.angle = math.radians(3)
sonne.rotation_euler = (math.radians(52), 0, math.radians(-35))
sc.collection.objects.link(sonne)
cam = bpy.data.objects.new("Kamera", bpy.data.cameras.new("Kamera"))
cam.data.clip_end = 5000
sc.collection.objects.link(cam)
sc.camera = cam
sc.view_settings.view_transform = "AgX"


def zielen(k):
    cam.location = Vector(k["pos"])
    cam.rotation_euler = (Vector(k["ziel"]) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = k["linse"]


def linien():
    sc.render.use_freestyle = True
    sc.render.line_thickness_mode = "ABSOLUTE"
    sc.render.line_thickness = 0.9
    fs = bpy.context.view_layer.freestyle_settings
    fs.crease_angle = math.radians(140)
    ls = fs.linesets[0] if fs.linesets else fs.linesets.new("Skizze")
    ls.select_by_collection = True
    ls.collection = BA
    ls.collection_negation = "EXCLUSIVE"
    stl = ls.linestyle or bpy.data.linestyles.new("Skizze")
    ls.linestyle = stl
    stl.color = (0.17, 0.15, 0.13)
    stl.chaining = "SKETCHY"
    stl.rounds = 2
    if not stl.geometry_modifiers:
        pn = stl.geometry_modifiers.new(name="Wackeln", type="PERLIN_NOISE_1D")
        pn.frequency, pn.amplitude, pn.octaves = 10.0, 1.0, 2


if MODUS == "--render":
    linien()
    nur = ARGS[ARGS.index("--nur") + 1].split(",") if "--nur" in ARGS else list(S["kameras"])
    klein = "--klein" in ARGS
    for name in nur:
        k = S["kameras"][name]
        zielen(k)
        sc.render.line_thickness = 0.45 if name == "luft" else 0.9
        sc.render.resolution_x, sc.render.resolution_y = (480, 300) if klein else (1440, 900)
        sc.cycles.samples = 4 if klein else 16
        sc.render.filepath = os.path.join(OUT, f"{PRE}{name}{'_klein' if klein else ''}.png")
        bpy.ops.render.render(write_still=True)
        print("RENDER", name, flush=True)
else:
    ziel = os.path.join(HIER, "export_3d")
    for f in ("FBX", "OBJ"):
        os.makedirs(os.path.join(ziel, f), exist_ok=True)
    for name, c in [("bebauung", GB), ("kontext", KT), ("freiraum", FL), ("station", STN), ("baeume", BA)]:
        bpy.ops.object.select_all(action="DESELECT")
        obs = list(c.all_objects)
        for ob in obs:
            ob.select_set(True)
        bpy.context.view_layer.objects.active = obs[0]
        bpy.ops.export_scene.fbx(filepath=os.path.join(ziel, "FBX", f"{PRE}{name}.fbx"), use_selection=True, object_types={"MESH"},
                                 apply_scale_options="FBX_SCALE_UNITS", mesh_smooth_type="FACE", use_mesh_modifiers=True,
                                 add_leaf_bones=False, bake_anim=False)
        bpy.ops.wm.obj_export(filepath=os.path.join(ziel, "OBJ", f"{PRE}{name}.obj"), export_selected_objects=True, forward_axis="Y",
                              up_axis="Z", export_uv=False, export_normals=True, export_materials=True, apply_modifiers=True)
        print("EXPORT", name, len(obs), flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "konzept1_stand2.blend" if K2 else "konzept1_variante_A.blend"), compress=True)
print("FERTIG", flush=True)
