"""
Blender 4.x: 3D-Modell der Schwarzplan-Varianten S1-S6 mit Freiraum und Staffage.
  --luft          je Variante Luftbild (Südwest) + Schnittperspektive A-A (Blick nach Westen)
  --situationen   5 Situationen (Kameras aus szene3.json), Bild + Freestyle-Linien getrennt
  --export        glTF je Variante (Phasen als Knoten) + .blend
  --test          eine Situation klein
Aufruf: blender -b --python blender_typologien.py -- --situationen [--variante S4]
"""
import bpy, bmesh, json, math, os, sys, random
from mathutils import Vector, Matrix

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODUS = next((a for a in ARGS if a in ("--luft", "--situationen", "--export", "--test", "--vorschau", "--kandidaten", "--fbx")), "--test")
VAR_SIT = ARGS[ARGS.index("--variante") + 1] if "--variante" in ARGS else "S4"
HIER = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HIER, "3d")
D = json.load(open(os.path.join(OUT, "szene.json")))
S = json.load(open(os.path.join(OUT, "szene3.json")))
EG_H, OG_H = 4.2, 3.1
RENDER = MODUS not in ("--export", "--fbx")      # Export: einfache Materialien (Principled), ohne Schnitt-Knoten
rnd = random.Random(11)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = "METRIC"


def rgb(h):
    h = h.lstrip("#")
    return tuple((int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4)) + (1,)


MATS = {}
SCHNITT_KNOTEN = []          # Math-Knoten "x > Schnitt": Wert 1e6 = kein Schnitt


def schnitt_setzen(x):
    for n in SCHNITT_KNOTEN:
        n.inputs[1].default_value = x


def mat(name, farbe, rough=0.85, glanz=False, schnitt=False):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgb(farbe)
    b.inputs["Roughness"].default_value = 0.08 if glanz else rough
    if glanz:
        b.inputs["Specular IOR Level"].default_value = 0.6
    m.diffuse_color = rgb(farbe)
    if schnitt and RENDER:      # Schnittperspektive: Innenseiten dunkel (Poché)
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        dunkel = nt.nodes.new("ShaderNodeBsdfDiffuse")
        dunkel.inputs["Color"].default_value = rgb("#2a2724")
        mix = nt.nodes.new("ShaderNodeMixShader")
        out = nt.nodes["Material Output"]
        nt.links.new(geo.outputs["Backfacing"], mix.inputs["Fac"])
        nt.links.new(b.outputs["BSDF"], mix.inputs[1])
        nt.links.new(dunkel.outputs["BSDF"], mix.inputs[2])
        nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    if RENDER:                  # Schnitt im Material: alles östlich der Schnittebene durchsichtig
        out = nt.nodes["Material Output"]
        quelle = out.inputs["Surface"].links[0].from_socket
        pos = nt.nodes.new("ShaderNodeNewGeometry")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        gt = nt.nodes.new("ShaderNodeMath")
        gt.operation = "GREATER_THAN"
        gt.inputs[1].default_value = 1e6
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(pos.outputs["Position"], sep.inputs["Vector"])
        nt.links.new(sep.outputs["X"], gt.inputs[0])
        nt.links.new(gt.outputs["Value"], mx.inputs["Fac"])
        nt.links.new(quelle, mx.inputs[1])
        nt.links.new(tr.outputs["BSDF"], mx.inputs[2])
        nt.links.new(mx.outputs["Shader"], out.inputs["Surface"])
        SCHNITT_KNOTEN.append(gt)
    MATS[name] = m
    return m


def koll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or sc.collection).children.link(c)
    return c


def obj_aus_bm(name, bm, mats, coll):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def faces_von(res):
    return {f for v in res["verts"] for f in v.link_faces}


def M(x, y, z, rot=0.0, s=(1, 1, 1), rx=0.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(rot), 4, "Z") @ Matrix.Rotation(rx, 4, "X") @ \
        Matrix.Diagonal((s[0], s[1], s[2], 1))


def kasten(bm, mat_i, m, sx, sy, sz):
    r = bmesh.ops.create_cube(bm, size=1.0, matrix=m @ Matrix.Diagonal((sx, sy, sz, 1)))
    for f in faces_von(r):
        f.material_index = mat_i
    return r


def kegel(bm, mat_i, m, r1, r2, h, seg=8):
    r = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r1, radius2=r2, depth=h, matrix=m)
    for f in faces_von(r):
        f.material_index = mat_i
    return r


def kugel(bm, mat_i, m, r, sub=1):
    res = bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r, matrix=m)
    for f in faces_von(res):
        f.material_index = mat_i
    return res


# ---------------- Kontext ----------------
FARBEN = {
    "boden": "#e9e5dc", "gruen_kontext": "#b4d39a", "bahn": "#948c82", "autobahn": "#a6a49f", "wasser": "#4f97bf",
    "strasse": "#d9d6cf", "kontext": "#f1efea", "kontext_dach": "#dedad2", "bestand": "#c9b9a4", "bestand_dach": "#b7a993",
    "gebiet_garten": "#bcd99c", "zwischenraum": "#a9cf87", "hauptader": "#9fca7c", "erholung": "#e8dfcc",
    "trichter": "#ddd6c9", "bewegung": "#8c8f93", "wasserader": "#4f97bf", "platz": "#c98f72", "station": "#2c6a2c",
    "station_dach": "#3f8a3f",
}
K = koll("Kontext")
for name, daten in D["objekte"].items():
    v, f = daten["v"], daten["f"]
    if not f:
        continue
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v[i:i + 3]) for i in range(0, len(v), 3)], [], [tuple(f[i:i + 3]) for i in range(0, len(f), 3)])
    me.validate()
    if name in ("kontext", "bestand", "kontext_dach", "bestand_dach", "station", "station_dach"):
        # Normalen nach außen bzw. oben drehen (sonst greift die dunkle Innenseite des Schnittmaterials)
        bm_n = bmesh.new()
        bm_n.from_mesh(me)
        if name.endswith("dach"):
            for f_ in bm_n.faces:
                f_.normal_update()
                if f_.normal.z < 0:
                    f_.normal_flip()
        else:
            bmesh.ops.recalc_face_normals(bm_n, faces=bm_n.faces)
        bm_n.to_mesh(me)
        bm_n.free()
    glanz = name in ("wasser", "wasserader")
    me.materials.append(mat("k_" + name, FARBEN.get(name, "#cccccc"), glanz=glanz, schnitt=name == "bestand"))
    ob = bpy.data.objects.new(name, me)
    K.objects.link(ob)
# Boden als Erdkörper (Schnitt: dunkles Band unter der Geländelinie)
bm = bmesh.new()
kasten(bm, 0, M(0, 0, -4.25), 2600, 2600, 8)
obj_aus_bm("erdkoerper", bm, [mat("erde", "#e9e5dc", schnitt=True)], K)

# ---------------- Bäume ----------------
GRUEN = ["#5f8f45", "#6e9e4c", "#4f7f3c", "#7aa556"]
BLUETE = ["#f1c6d3", "#f6e7ee", "#e8a9bf"]


def baeume(name, liste, coll, detail):
    bm = bmesh.new()
    mats = [mat("stamm", "#6b5a48")] + [mat(f"laub{i}", c) for i, c in enumerate(GRUEN)] + \
           [mat(f"bluete{i}", c) for i, c in enumerate(BLUETE)] + [mat("weide", "#9cc06a")]
    for t in liste:
        x, y, h, art = t
        r = max(2.0, h * 0.27) * rnd.uniform(0.85, 1.15)
        kegel(bm, 0, M(x, y, (h - r) / 2), 0.22, 0.15, h - r * 0.8, 6)
        if art == "bluete":
            fi = lambda: 1 + len(GRUEN) + rnd.randrange(len(BLUETE))
        elif art == "weide":
            fi = lambda: 1 + len(GRUEN) + len(BLUETE)
        else:
            fi = lambda: 1 + rnd.randrange(len(GRUEN))
        if detail:
            for k in range(5):
                a = rnd.uniform(0, 6.28)
                d = r * rnd.uniform(0.15, 0.55)
                kugel(bm, fi(), M(x + d * math.cos(a), y + d * math.sin(a), h - r * rnd.uniform(0.55, 1.0),
                                  s=(1, 1, 0.85 if art != "weide" else 1.15)), r * rnd.uniform(0.55, 0.75), 2)
        else:
            kugel(bm, fi(), M(x, y, h - r * 0.8, s=(1, 1, 0.85)), r, 1)
    return obj_aus_bm(name, bm, mats, coll)


baeume("baeume_kontext", [(b[0], b[1], b[2], "laub") for b in S["baeume_kontext"]], K, False)

# ---------------- Freiraum (Flächen) ----------------
F = koll("Freiraum")
TUFFS = koll("Tuffs")
FL_FARBE = dict(radweg="#5fa684", markierung="#ffffff", zebra="#f4f4f2", asphalt="#8c8f93", rasengitter="#a7b991",
                pflaster="#ddd8ce", wiese="#a9c77f", beet="#6c8a4b", kies="#ebe3d1", rasen="#8fc05a", wasser="#4aa0c4",
                ufersteine="#bdb6a8", holzdeck="#b98a59", sand="#efdcac", platzpflaster="#c99376", stufe="#dcd5c8",
                sitzstufen="#dcd5c8")
PRISMA = {"stufe", "holzdeck"}
for fl in S["flaechen"]:
    art, z = fl["art"], fl["z"]
    v, f = fl["v"], fl["f"]
    if not f:
        continue
    bm = bmesh.new()
    hoch = art in PRISMA
    z0 = 0.2 + (0 if hoch else max(z, 0)) if art != "wasser" else 0.17
    vs = [bm.verts.new((v[i], v[i + 1], z0)) for i in range(0, len(v), 2)]
    for i in range(0, len(f), 3):
        try:
            bm.faces.new((vs[f[i]], vs[f[i + 1]], vs[f[i + 2]]))
        except ValueError:
            pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.01)
    if hoch:
        r = bmesh.ops.extrude_face_region(bm, geom=list(bm.faces))
        neu = [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=(0, 0, z), verts=neu)
    obj_aus_bm(f"fl_{art}_{z}", bm, [mat("fl_" + art, FL_FARBE.get(art, "#cccccc"), glanz=art == "wasser")], F)

# ---------------- Punkte: Stauden, Möbel, Staffage ----------------
TUFF_F = dict(lila="#8e6bb5", pink="#d77fa1", weiss="#f2efe6", gelb="#e8c547", rot="#c8503f", orange="#e48a3a",
              blau="#6f86c9", gras="#a3b06a", schilf="#a9a56c")
P = [p for p in S["punkte"] if "p" in p]
import time
T0 = time.time()
def zeit(t):
    print(f"ZEIT {t}: {time.time() - T0:.0f} s", flush=True)
import numpy as np
# Vorlagen: Ikosaeder (Blüten) und fünfseitiger Kegel (Gräser, Schilf) -> vektorisiert, sehr schnell
_b = bmesh.new(); bmesh.ops.create_icosphere(_b, subdivisions=0, radius=1.0)
IKO_V = np.array([v.co[:] for v in _b.verts]); IKO_F = np.array([[v.index for v in f.verts] for f in _b.faces]); _b.free()
KEG_V = np.array([[math.cos(2 * math.pi * k / 5), math.sin(2 * math.pi * k / 5), 0] for k in range(5)] + [[0, 0, 1]])
KEG_F = np.array([[k, (k + 1) % 5, 5] for k in range(5)])
gruppen = {k: [] for k in TUFF_F}
for p in P:
    if p["art"] == "tuff":
        gruppen[p["farbe"]].append(p["p"])
for k, pts in gruppen.items():
    if not pts:
        continue
    pts = np.array(pts)
    n = len(pts)
    if k in ("gras", "schilf"):
        h = np.random.uniform(0.6, 0.9, n) if k == "gras" else np.random.uniform(1.1, 1.6, n)
        r = np.random.uniform(0.16, 0.24, n)
        V = KEG_V[None] * np.stack([r, r, h], 1)[:, None] + np.stack([pts[:, 0], pts[:, 1], np.full(n, 0.25)], 1)[:, None]
        Fc = KEG_F[None] + (np.arange(n) * 6)[:, None, None]
    else:
        r = np.random.uniform(0.18, 0.3, n)
        V = IKO_V[None] * np.stack([r, r, r * 0.75], 1)[:, None] + np.stack([pts[:, 0], pts[:, 1], 0.3 + r * 0.9], 1)[:, None]
        Fc = IKO_F[None] + (np.arange(n) * 12)[:, None, None]
    me = bpy.data.meshes.new(f"tuffs_{k}")
    me.from_pydata(V.reshape(-1, 3).tolist(), [], Fc.reshape(-1, 3).tolist())
    me.materials.append(mat("tuff_" + k, TUFF_F[k]))
    ob = bpy.data.objects.new(f"tuffs_{k}", me)
    TUFFS.objects.link(ob)
zeit("Tuffs")

KLEID = ["#c0392b", "#2e86c1", "#f1c40f", "#27ae60", "#8e44ad", "#e67e22", "#f4f6f6", "#34495e"]
HAUT = ["#d9b38c", "#8d5524", "#f1d0b0", "#c68642"]
ST = koll("Staffage")
st_mats = [mat(f"kleid{i}", c) for i, c in enumerate(KLEID)] + [mat("hose", "#3d4a5c"), mat("haut0", HAUT[0]),
                                                                  mat("haut1", HAUT[1]), mat("haut2", HAUT[2]),
                                                                  mat("holz", "#a47449"), mat("metall", "#5a5f63"),
                                                                  mat("schirm_weiss", "#f5f2ea"), mat("schirm_creme", "#efe3c4"),
                                                                  mat("schirm_gruen", "#7fae8a"), mat("glas", "#8fb4c4", glanz=True),
                                                                  mat("weiss", "#f7f6f2"), mat("kiosk1", "#f4d03f"), mat("kiosk2", "#e98aa8"),
                                                                  mat("rot_spiel", "#d9534f"), mat("gelb_spiel", "#f0c419"),
                                                                  mat("auto0", "#c8ccd0"), mat("auto1", "#2b2f33"), mat("auto2", "#9b2d30"),
                                                                  mat("auto3", "#30577d"), mat("auto4", "#e8e6e1"), mat("stein", "#b9b4aa"),
                                                                  mat("laubdach", "#6e9e4c"), mat("beet_gruen", "#5f8a3f")]
MI = {m.name: i for i, m in enumerate(st_mats)}
bm = bmesh.new()


def mensch(x, y, rot, haltung, farbe, bm=bm):
    kl = farbe % 8
    haut = MI[f"haut{rnd.randrange(3)}"]
    s = 0.62 if haltung == "kind" else rnd.uniform(0.95, 1.05)
    m0 = M(x, y, 0.2, rot, (s, s, s))
    if haltung in ("geh", "steh", "kind"):
        schritt = 0.12 if haltung != "steh" else 0.0
        for dx in (-0.09, 0.09):
            kasten(bm, MI["hose"], m0 @ M(dx, schritt * (1 if dx > 0 else -1), 0.43), 0.12, 0.14, 0.86)
        kegel(bm, kl, m0 @ M(0, 0, 1.18), 0.2, 0.16, 0.66, 8)
        kugel(bm, haut, m0 @ M(0, 0, 1.64), 0.115, 1)
    elif haltung == "sitz":
        kasten(bm, MI["hose"], m0 @ M(0, 0.2, 0.42), 0.3, 0.42, 0.12)
        kasten(bm, MI["hose"], m0 @ M(0, 0.42, 0.21), 0.3, 0.12, 0.42)
        kegel(bm, kl, m0 @ M(0, 0, 0.78), 0.2, 0.16, 0.62, 8)
        kugel(bm, haut, m0 @ M(0, 0, 1.22), 0.115, 1)
    elif haltung == "lieg":
        kasten(bm, kl, m0 @ M(0, 0, 0.12), 0.38, 0.9, 0.22)
        kasten(bm, MI["hose"], m0 @ M(0, 0.85, 0.08), 0.32, 0.8, 0.15)
        kugel(bm, haut, m0 @ M(0, -0.55, 0.14), 0.115, 1)


for p in P:
    a = p["art"]
    x, y = p["p"]
    rot = p.get("rot", 0)
    if a == "mensch":
        mensch(x, y, rot, p["haltung"], p["farbe"])
    elif a == "rad":
        m0 = M(x, y, 0.2, rot)
        for dy in (-0.55, 0.55):
            kegel(bm, MI["metall"], m0 @ M(0, dy, 0.34) @ Matrix.Rotation(math.pi / 2, 4, "Y"), 0.33, 0.33, 0.04, 14)
        kasten(bm, MI["metall"], m0 @ M(0, 0, 0.55), 0.05, 1.0, 0.05)
        kegel(bm, p["farbe"] % 8, m0 @ M(0, 0.05, 1.15), 0.19, 0.15, 0.6, 8)
        kasten(bm, MI["hose"], m0 @ M(0, -0.05, 0.62), 0.24, 0.2, 0.55)
        kugel(bm, MI["haut0"], m0 @ M(0, 0.18, 1.58), 0.11, 1)
    elif a == "auto":
        m0 = M(x, y, 0.2, rot)
        fa = MI[f"auto{p['farbe'] % 5}"]
        kasten(bm, fa, m0 @ M(0, 0, 0.55), 1.8, 4.3, 0.75)
        kasten(bm, MI["glas"], m0 @ M(0, -0.2, 1.2), 1.6, 2.2, 0.6)
    elif a == "bank":
        m0 = M(x, y, 0.2, rot)
        kasten(bm, MI["holz"], m0 @ M(0, 0, 0.42), 1.8, 0.5, 0.08)
        kasten(bm, MI["holz"], m0 @ M(0, 0.23, 0.68), 1.8, 0.06, 0.4)
        for dx in (-0.75, 0.75):
            kasten(bm, MI["metall"], m0 @ M(dx, 0, 0.21), 0.06, 0.45, 0.42)
    elif a == "schirm":
        m0 = M(x, y, 0.2, rot)
        kegel(bm, MI["metall"], m0 @ M(0, 0, 1.2), 0.04, 0.04, 2.4, 6)
        kegel(bm, MI[f"schirm_{p.get('farbe', 'weiss')}"], m0 @ M(0, 0, 2.35), 1.4, 0.05, 0.45, 12)
        kegel(bm, MI["weiss"], m0 @ M(0.6, 0, 0.37), 0.35, 0.35, 0.05, 12)
        kegel(bm, MI["metall"], m0 @ M(0.6, 0, 0.2), 0.04, 0.04, 0.4, 6)
    elif a == "pavillon":
        m0 = M(x, y, 0.2, rot)
        kasten(bm, MI["glas"], m0 @ M(0, 0, 1.6), 7, 4.5, 3.2)
        kasten(bm, MI["weiss"], m0 @ M(0, 0, 3.35), 9, 6.5, 0.3)
    elif a == "kiosk":
        m0 = M(x, y, 0.2, rot)
        kasten(bm, MI[p["farbe"]], m0 @ M(0, 0, 1.4), 5, 2.4, 2.8)
        kasten(bm, MI["weiss"], m0 @ M(0, 1.5, 2.6), 5, 1.2, 0.08)
    elif a == "pergola":
        m0 = M(x, y, 0.2, rot)
        for dx in (-2.8, 0, 2.8):
            for dy in (-1.8, 1.8):
                kasten(bm, MI["weiss"], m0 @ M(dx, dy, 1.4), 0.14, 0.14, 2.8)
        for dy in (-1.8, 1.8):
            kasten(bm, MI["weiss"], m0 @ M(0, dy, 2.85), 6.0, 0.16, 0.16)
        for k in range(6):
            kugel(bm, MI["laubdach"], m0 @ M(rnd.uniform(-2.5, 2.5), rnd.uniform(-1.6, 1.6), 2.95, s=(1.4, 1, 0.35)), 0.9, 1)
        kasten(bm, MI["weiss"], m0 @ M(0, 0, 0.45), 2.4, 0.8, 0.45)
    elif a == "kletter":
        m0 = M(x, y, 0.2, rot)
        for dx in (-1.5, 1.5):
            for dy in (-1, 1):
                kegel(bm, MI["holz"], m0 @ M(dx, dy, 1.25), 0.07, 0.07, 2.5, 6)
        kasten(bm, MI["rot_spiel"], m0 @ M(0, 0, 1.3), 3.2, 2.2, 0.12)
        kasten(bm, MI["gelb_spiel"], m0 @ M(2.9, 0, 0.7, s=(1, 1, 1)) @ Matrix.Rotation(math.radians(-28), 4, "Y"), 3.2, 0.7, 0.1)
    elif a == "hochbeet":
        m0 = M(x, y, 0.2, rot)
        kasten(bm, MI["holz"], m0 @ M(0, 0, 0.35), 3.0, 1.2, 0.7)
        kasten(bm, MI["beet_gruen"], m0 @ M(0, 0, 0.72), 2.8, 1.0, 0.06)
        for k in range(6):
            kugel(bm, MI["laubdach"], m0 @ M(rnd.uniform(-1.2, 1.2), rnd.uniform(-0.35, 0.35), 0.85), rnd.uniform(0.15, 0.28), 0)
    elif a == "trittstein":
        kegel(bm, MI["stein"], M(x, y, 0.26), 0.45, 0.42, 0.16, 10)
obj_aus_bm("staffage", bm, st_mats, ST)
zeit("Staffage")
detail_baeume = [(p["p"][0], p["p"][1], p["h"], p["baumart"]) for p in P if p["art"] == "baum"]
baeume("baeume_detail", detail_baeume, F, True)

# ---------------- Markthalle (Bestand am Platz) ----------------
bm = bmesh.new()
for ring in S["markthalle"]:
    vs = [bm.verts.new((x, y, 0)) for x, y in ring]
    try:
        f = bm.faces.new(vs)
        r = bmesh.ops.extrude_face_region(bm, geom=[f])
        bmesh.ops.translate(bm, vec=(0, 0, 9), verts=[e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)])
    except ValueError:
        pass
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
obj_aus_bm("markthalle", bm, [mat("markthalle", "#b5704f", schnitt=True)], K)

# ---------------- Varianten: Gebäude mit Fenstern ----------------
WAND = ["#f4f0e8", "#e8dccb", "#d9c2a3", "#c4876a", "#ebe9e4", "#b5704f", "#dcd6cc", "#f1e6d2"]
GEWICHT = [3, 2, 2, 1, 3, 1, 2, 2]
SONDER_WAND = dict(halle="#aab3b8", sporthalle="#d6cdbc", schule="#e2cba4", sockel="#d0d3d6")
wand_mats = [mat(f"wand{i}", c, schnitt=True) for i, c in enumerate(WAND)] + \
            [mat(f"wand_{k}", c, schnitt=True) for k, c in SONDER_WAND.items()]
dach_mats = [mat("dach_gruen", "#9cbf7a", schnitt=True), mat("dach_hell", "#cfcac0", schnitt=True)]
fenster_mats = [mat("fenster", "#55687a", rough=0.2), mat("schaufenster", "#a9c6d4", rough=0.15)]


def hoehe(g):
    return EG_H + (g - 1) * OG_H


VK = {}
for code, hs in S["varianten"].items():
    c = koll(code)
    VK[code] = c
    teile = {}
    for idx, h in enumerate(hs):
        ring = h["ring"]
        if len(ring) < 3:
            continue
        fl = sum(ring[i][0] * ring[(i + 1) % len(ring)][1] - ring[(i + 1) % len(ring)][0] * ring[i][1] for i in range(len(ring)))
        if fl < 0:
            ring = ring[::-1]
        ph = h["phase"]
        for teil in ("wand", "dach", "fenster"):
            teile.setdefault((ph, teil), bmesh.new())
        H = hoehe(h["g"])
        r_ = random.Random(idx * 7 + len(code))
        wi = len(WAND) + list(SONDER_WAND).index(h["typ"]) if h["typ"] in SONDER_WAND else \
            r_.choices(range(len(WAND)), weights=GEWICHT)[0]
        # Wände
        bw = teile[(ph, "wand")]
        unten = [bw.verts.new((x, y, 0)) for x, y in ring]
        oben = [bw.verts.new((x, y, H)) for x, y in ring]
        n = len(ring)
        for i in range(n):
            j = (i + 1) % n
            f = bw.faces.new((unten[i], unten[j], oben[j], oben[i]))
            f.material_index = wi
        # Dach
        bd = teile[(ph, "dach")]
        try:
            f = bd.faces.new([bd.verts.new((x, y, H)) for x, y in ring])
            f.material_index = 1 if h["typ"] in ("halle", "sporthalle") else 0
        except ValueError:
            pass
        # Fenster: je Kante Achsen à 3,3 m, je Geschoss ein Fenster; aktive EG = Schaufenster
        bf = teile[(ph, "fenster")]
        band = h["typ"] in ("halle", "sporthalle", "schule", "sockel")
        for i in range(n):
            (x0, y0), (x1, y1) = ring[i], ring[(i + 1) % n]
            L = math.hypot(x1 - x0, y1 - y0)
            if L < 3.0:
                continue
            tx, ty = (x1 - x0) / L, (y1 - y0) / L
            nx, ny = ty, -tx
            achsen = max(1, int(L / 3.3))
            teil = L / achsen
            for k in range(h["g"]):
                z0 = 0 if k == 0 else EG_H + (k - 1) * OG_H
                schau = (k == 0 and (h["aktiv"] or band))
                if band:
                    za, zb, w = z0 + 0.9, z0 + (3.4 if k == 0 else 2.6), teil - 0.5
                elif schau:
                    za, zb, w = z0 + 0.25, z0 + 3.5, teil - 0.45
                else:
                    za, zb, w = z0 + 0.95, z0 + 2.55, min(1.5, teil - 0.8) if h["typ"] != "reihe" else 1.2
                for a in range(achsen):
                    mx = x0 + tx * teil * (a + 0.5) + nx * 0.06
                    my = y0 + ty * teil * (a + 0.5) + ny * 0.06
                    q = [bf.verts.new((mx - tx * w / 2, my - ty * w / 2, za)), bf.verts.new((mx + tx * w / 2, my + ty * w / 2, za)),
                         bf.verts.new((mx + tx * w / 2, my + ty * w / 2, zb)), bf.verts.new((mx - tx * w / 2, my - ty * w / 2, zb))]
                    f = bf.faces.new(q)
                    f.material_index = 1 if schau else 0
    for (ph, teil), b in sorted(teile.items()):
        ms = wand_mats if teil == "wand" else dach_mats if teil == "dach" else fenster_mats
        obj_aus_bm(f"{code}_{ph}_{teil}", b, ms, c)


zeit("Gebäude")


def zeige(code):
    for c2, coll in VK.items():
        coll.hide_render = c2 != code
        coll.hide_viewport = c2 != code


# ---------------- Licht, Himmel, Kamera ----------------
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.use_denoising = False
sc.cycles.max_bounces = 4
sc.cycles.diffuse_bounces = 2
sc.cycles.glossy_bounces = 2
sc.cycles.transmission_bounces = 0
sc.cycles.transparent_max_bounces = 24
welt = bpy.data.worlds.new("Himmel")
sc.world = welt
welt.use_nodes = True
nt = welt.node_tree
grad = nt.nodes.new("ShaderNodeTexGradient")
grad.gradient_type = "EASING"
koord = nt.nodes.new("ShaderNodeTexCoord")
mapn = nt.nodes.new("ShaderNodeMapping")
mapn.inputs["Rotation"].default_value = (0, math.radians(-90), 0)
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (0.95, 0.96, 0.97, 1)
ramp.color_ramp.elements[1].color = (0.58, 0.74, 0.92, 1)
nt.links.new(koord.outputs["Generated"], mapn.inputs["Vector"])
nt.links.new(mapn.outputs["Vector"], grad.inputs["Vector"])
nt.links.new(grad.outputs["Fac"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], nt.nodes["Background"].inputs["Color"])
nt.nodes["Background"].inputs["Strength"].default_value = 0.85
sonne = bpy.data.objects.new("Sonne", bpy.data.lights.new("Sonne", "SUN"))
sonne.data.energy = 3.6
sonne.data.angle = math.radians(2.5)
sonne.rotation_euler = (math.radians(50), 0, math.radians(-40))
sc.collection.objects.link(sonne)
cam = bpy.data.objects.new("Kamera", bpy.data.cameras.new("Kamera"))
cam.data.clip_end = 6000
sc.collection.objects.link(cam)
sc.camera = cam
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "None"


def zielen(pos, ziel, linse):
    cam.location = Vector(pos)
    cam.rotation_euler = (Vector(ziel) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = linse


def freestyle(an, als_pass=False):
    sc.render.use_freestyle = an
    if not an:
        return
    sc.render.line_thickness_mode = "ABSOLUTE"
    sc.render.line_thickness = 0.95
    vl = bpy.context.view_layer
    fs = vl.freestyle_settings
    fs.as_render_pass = als_pass
    fs.crease_angle = math.radians(140)
    ls = fs.linesets[0] if fs.linesets else fs.linesets.new("Skizze")
    ls.select_by_visibility = True
    ls.select_by_edge_types = True
    ls.select_silhouette = ls.select_border = ls.select_crease = ls.select_external_contour = True
    ls.select_by_collection = True
    ls.collection = TUFFS
    ls.collection_negation = "EXCLUSIVE"
    st = ls.linestyle or bpy.data.linestyles.new("Skizze")
    ls.linestyle = st
    st.color = (0.16, 0.13, 0.11)
    st.alpha = 0.9
    st.chaining = "SKETCHY"
    st.rounds = 2
    if not st.geometry_modifiers:
        pn = st.geometry_modifiers.new(name="Wackeln", type="PERLIN_NOISE_1D")
        pn.frequency, pn.amplitude, pn.octaves = 10.0, 1.3, 2
        st.geometry_modifiers.new(name="Strecken", type="BACKBONE_STRETCHER").backbone_length = 2.0
        tm = st.thickness_modifiers.new(name="Ansatz", type="ALONG_STROKE")
        tm.mapping = "CURVE"
        tm.value_min, tm.value_max = 0.6, 1.4


def render(datei, x, y, samples):
    sc.render.resolution_x, sc.render.resolution_y = x, y
    sc.render.resolution_percentage = 100
    sc.cycles.samples = samples
    sc.render.filepath = os.path.join(OUT, datei)
    bpy.ops.render.render(write_still=True)
    print("RENDER", datei, flush=True)


def situation(name, k, x, y, samples):
    """Ein Rendering ohne Linien + Freestyle-Linien als eigene Datei (Pass) -> Skizze per Nachbearbeitung."""
    zielen(k["pos"], k["ziel"], k["linse"])
    sc.render.film_transparent = True
    sc.render.image_settings.color_mode = "RGBA"
    freestyle(True, als_pass=True)
    sc.use_nodes = True
    tree = sc.node_tree
    for n in list(tree.nodes):
        tree.nodes.remove(n)
    rl = tree.nodes.new("CompositorNodeRLayers")
    comp = tree.nodes.new("CompositorNodeComposite")
    tree.links.new(rl.outputs["Image"], comp.inputs["Image"])
    fo = tree.nodes.new("CompositorNodeOutputFile")
    fo.base_path = OUT
    fo.format.file_format = "PNG"
    fo.format.color_mode = "RGBA"
    fo.file_slots[0].path = f"sit_{name}_linien_"
    tree.links.new(rl.outputs["Freestyle"], fo.inputs[0])
    render(f"sit_{name}_bild.png", x, y, samples)


if MODUS in ("--luft",):
    freestyle(False)
    for code in VK:
        zeige(code)
        zielen((-470, -900, 600), (20, 40, 0), 42)
        cam.data.clip_start = 5
        cam.data.shift_y = 0
        if not os.path.exists(os.path.join(OUT, f"luft_{code}.png")):
            render(f"luft_{code}.png", 1800, 1125, 20)
        if os.path.exists(os.path.join(OUT, f"schnittperspektive_{code}.png")):
            continue
        # Schnittperspektive A-A: senkrechte Schnittebene x = 0, Kamera östlich, Blick nach Westen
        schnitt_setzen(S["schnitt"]["x"])
        zielen((S["schnitt"]["x"] + 150, -150, 85), (S["schnitt"]["x"] - 40, 110, 0), 30)
        render(f"schnittperspektive_{code}.png", 2000, 1250, 20)
        schnitt_setzen(1e6)
elif MODUS == "--kandidaten":
    zeige(VAR_SIT)
    freestyle(False)
    sc.render.film_transparent = True
    for k in json.load(open(os.path.join(OUT, "kandidaten.json"))):
        zielen(k["pos"], k["ziel"], k["linse"])
        render(f"kand_{k['name']}.png", 420, 280, 3)
elif MODUS == "--vorschau":
    zeige(VAR_SIT)
    freestyle(False)
    sc.render.film_transparent = True
    for name, k in S["kameras"].items():
        zielen(k["pos"], k["ziel"], k["linse"])
        render(f"vorschau_{name}.png", 540, 360, 4)
    zeige("S2")
    zielen((-470, -900, 600), (20, 40, 0), 42)
    render("vorschau_luft.png", 640, 400, 4)
    schnitt_setzen(S["schnitt"]["x"])
    zielen((S["schnitt"]["x"] + 150, -150, 85), (S["schnitt"]["x"] - 40, 110, 0), 30)
    render("vorschau_schnitt.png", 800, 500, 6)
    schnitt_setzen(1e6)
elif MODUS in ("--situationen", "--test"):
    zeige(VAR_SIT)
    sc.view_settings.view_transform = "AgX"
    namen = ARGS[ARGS.index("--nur") + 1].split(",") if "--nur" in ARGS else list(S["kameras"])
    for name in namen:
        k = S["kameras"][name]
        if MODUS == "--test":
            situation(name, k, 600, 400, 6)
        else:
            situation(name, k, 1650, 1100, 28)
elif MODUS == "--export":
    def export(datei, colls):
        bpy.ops.object.select_all(action="DESELECT")
        for c in colls:
            for ob in c.all_objects:
                ob.select_set(True)
        bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, datei), export_format="GLB", use_selection=True,
                                  export_apply=True, export_yup=True, export_cameras=False, export_lights=False)
        print("GLB", datei, flush=True)
    for code in VK:
        VK[code].hide_viewport = False
        export(f"{code}.glb", [VK[code]])
    export("freiraum.glb", [F])
    zeige("S4")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "bergfrieden_typologien_S1-S6.blend"), compress=True)
elif MODUS == "--fbx":
    # FBX und OBJ für Rhino, SketchUp, 3ds Max, Archicad, Cinema 4D: ein Baustein je Datei, gleiche Koordinaten
    ziel = os.path.join(HIER, "export_3d")
    for f in ("FBX", "OBJ"):
        os.makedirs(os.path.join(ziel, f), exist_ok=True)
    for c in list(VK.values()) + [K, F, ST, TUFFS]:
        c.hide_viewport = False
        c.hide_render = False
    gruppen = [("umgebung_und_geruest", [o for o in K.all_objects if o.name != "erdkoerper"]),
               ("freiraum", list(F.all_objects)), ("staffage", list(ST.all_objects)), ("stauden", list(TUFFS.all_objects))] + \
              [(f"bebauung_{code}", list(VK[code].all_objects)) for code in VK]
    for name, obs in gruppen:
        bpy.ops.object.select_all(action="DESELECT")
        for ob in obs:
            ob.select_set(True)
        bpy.context.view_layer.objects.active = obs[0]
        bpy.ops.export_scene.fbx(filepath=os.path.join(ziel, "FBX", f"bergfrieden_{name}.fbx"), use_selection=True,
                                 object_types={"MESH"}, apply_scale_options="FBX_SCALE_UNITS", mesh_smooth_type="FACE",
                                 use_mesh_modifiers=True, add_leaf_bones=False, bake_anim=False)
        bpy.ops.wm.obj_export(filepath=os.path.join(ziel, "OBJ", f"bergfrieden_{name}.obj"), export_selected_objects=True,
                              forward_axis="Y", up_axis="Z", export_uv=False, export_normals=True, export_materials=True,
                              export_object_groups=False, export_material_groups=False)
        print("EXPORT", name, len(obs), "Objekte", flush=True)
print("FERTIG", flush=True)
