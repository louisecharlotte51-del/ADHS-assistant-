"""
Blender 4.x: baut das 3D-Modell „Gartenquartier Bergfrieden" mit Umgebung,
rendert alle Varianten und Bauphasen, speichert .blend und exportiert .glb.
Aufruf:  blender -b --python blender_szene.py -- [--nur-test] [--samples 24] [--skala 200]
"""
import bpy, bmesh, json, math, sys, os, random
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
TEST = "--nur-test" in ARGS
SAMPLES = int(ARGS[ARGS.index("--samples") + 1]) if "--samples" in ARGS else 24
SKALA = int(ARGS[ARGS.index("--skala") + 1]) if "--skala" in ARGS else 200
HIER = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HIER, "3d")
D = json.load(open(os.path.join(OUT, "szene.json")))

# ---------------- Szene leeren ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = "METRIC"

FARBEN = {
    "boden": "#e7e2d6", "gruen_kontext": "#a7cd8c", "bahn": "#8d857b", "autobahn": "#a19f9a", "wasser": "#3d82b5",
    "strasse": "#dcd8cf", "kontext": "#f3f1eb", "kontext_dach": "#e2ded4", "bestand": "#b7b1a6", "bestand_dach": "#a7a196",
    "gebiet_garten": "#cfe3b2", "zwischenraum": "#b9dc99", "hauptader": "#3d9a3d", "erholung": "#f3bb6b",
    "trichter": "#f19a35", "bewegung": "#ec7d6d", "wasserader": "#2aaee8", "platz": "#f3e2a4", "station": "#245a24",
    "station_dach": "#2f7d2f", "wohnen": "#fbf9f3", "eg": "#e0873a", "dach": "#93c26d", "krone": "#4f8f3f",
    "krone_neu": "#6bb04e", "stamm": "#6b5a48",
}


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple((int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4)) + (1,)


MATS = {}
def mat(name):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = hex2rgb(FARBEN.get(name, "#cccccc"))
    b.inputs["Roughness"].default_value = 0.85
    if name in ("wasser", "wasserader"):
        b.inputs["Roughness"].default_value = 0.25
        b.inputs["Specular IOR Level"].default_value = 0.5
    m.diffuse_color = hex2rgb(FARBEN.get(name, "#cccccc"))
    MATS[name] = m
    return m


def koll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or sc.collection).children.link(c)
    return c


def mesh_obj(name, daten, material, coll):
    v, f = daten["v"], daten["f"]
    if not f:
        return None
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v[i:i + 3]) for i in range(0, len(v), 3)], [], [tuple(f[i:i + 3]) for i in range(0, len(f), 3)])
    me.validate()
    me.materials.append(mat(material))
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def baeume_obj(name, liste, coll, neu=False):
    """Alle Bäume einer Gruppe als ein Mesh (Krone = Ikosaeder, Stamm = Prisma)."""
    if not liste:
        return None
    bm = bmesh.new()
    rnd = random.Random(len(liste))
    for (x, y, h, *_rest) in liste:
        r = max(2.2, h * 0.28) * rnd.uniform(0.85, 1.15)
        k = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
        bmesh.ops.scale(bm, vec=(1, 1, 0.85), verts=k["verts"])
        bmesh.ops.translate(bm, vec=(x, y, h - r * 0.8), verts=k["verts"])
        for fc in {f for v_ in k["verts"] for f in v_.link_faces}:
            fc.material_index = 0
        s = bmesh.ops.create_cone(bm, cap_ends=True, segments=5, radius1=0.25, radius2=0.18, depth=h - r)
        bmesh.ops.translate(bm, vec=(x, y, (h - r) / 2), verts=s["verts"])
        for fc in {f for v_ in s["verts"] for f in v_.link_faces}:
            fc.material_index = 1
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat("krone_neu" if neu else "krone"))
    me.materials.append(mat("stamm"))
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


# ---------------- Kontext & Entwurf ----------------
K = koll("Kontext")
ENT = koll("Entwurf_Geruest")
kontext_namen = {"boden", "gruen_kontext", "bahn", "autobahn", "wasser", "strasse", "kontext", "kontext_dach"}
for name, daten in D["objekte"].items():
    mesh_obj(name, daten, name, K if name in kontext_namen else ENT)
alt = [b for b in D["baeume"] if b[3] == 0]
neu = [b for b in D["baeume"] if b[3] == 1]
baeume_obj("baeume_bestand", alt, K)
baeume_obj("baeume_adern", neu, ENT, neu=True)

# ---------------- Varianten (je Phase eigene Collection) ----------------
VK = {}
for code, vd in D["varianten"].items():
    c = koll(code)
    VK[code] = {}
    for ph in ("P1", "P2", "P3", "P4"):
        pc = koll(f"{code}_{ph}", c)
        VK[code][ph] = pc
        for teil, m in (("wohnen", "wohnen"), ("eg", "eg"), ("dach", "dach")):
            k = f"{code}_{ph}_{teil}"
            if k in vd["meshes"]:
                mesh_obj(k, vd["meshes"][k], m, pc)
        baeume_obj(f"{code}_{ph}_baeume", [b for b in vd["baeume"] if b[3] == ph], pc, neu=True)

# ---------------- Licht, Himmel, Kamera ----------------
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = False
sc.cycles.max_bounces = 4
sc.cycles.diffuse_bounces = 2
sc.cycles.glossy_bounces = 2
sc.cycles.transmission_bounces = 0
sc.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
sc.view_settings.look = "None"
sc.view_settings.exposure = -0.3
sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
sc.render.resolution_percentage = SKALA
sc.render.image_settings.file_format = "PNG"

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
ramp.color_ramp.elements[0].color = (0.93, 0.95, 0.97, 1)
ramp.color_ramp.elements[1].color = (0.55, 0.70, 0.90, 1)
nt.links.new(koord.outputs["Generated"], mapn.inputs["Vector"])
nt.links.new(mapn.outputs["Vector"], grad.inputs["Vector"])
nt.links.new(grad.outputs["Fac"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], nt.nodes["Background"].inputs["Color"])
nt.nodes["Background"].inputs["Strength"].default_value = 0.75
sonne = bpy.data.objects.new("Sonne", bpy.data.lights.new("Sonne", "SUN"))
sonne.data.energy = 3.4
sonne.data.angle = math.radians(1.2)
sonne.rotation_euler = (math.radians(52), 0, math.radians(-50))
sc.collection.objects.link(sonne)

cam = bpy.data.objects.new("Kamera", bpy.data.cameras.new("Kamera"))
cam.data.lens = 50
cam.data.clip_end = 8000
sc.collection.objects.link(cam)
sc.camera = cam


def zielen(pos, ziel):
    cam.location = Vector(pos)
    richtung = Vector(ziel) - cam.location
    cam.rotation_euler = richtung.to_track_quat("-Z", "Y").to_euler()


ANSICHTEN = {
    "uebersicht": ((-470, -960, 640), (30, 10, 0)),        # aus Südwesten: Kanal vorn, S-Bahn hinten
    "nah": ((-260, -380, 230), (40, 120, 0)),
}


def zeige(code, bis_phase):
    reihen = ["P1", "P2", "P3", "P4"]
    for c2, phs in VK.items():
        for ph, coll in phs.items():
            sichtbar = c2 == code and bis_phase is not None and reihen.index(ph) <= reihen.index(bis_phase)
            coll.hide_render = not sichtbar
            coll.hide_viewport = not sichtbar


def render(datei, ansicht="uebersicht", prozent=None, samples=None):
    zielen(*ANSICHTEN[ansicht])
    sc.render.resolution_percentage = prozent or SKALA
    sc.cycles.samples = samples or SAMPLES
    sc.render.filepath = os.path.join(OUT, datei)
    bpy.ops.render.render(write_still=True)
    print("RENDER", datei, flush=True)


NUR_EXPORT = "--nur-export" in ARGS
if TEST:
    sc.render.resolution_percentage = 50
    sc.cycles.samples = 8
    zeige("V1", "P4")
    render("test_V1.png")
else:
  if not NUR_EXPORT:
    for code in VK:
        zeige(code, "P4")
        render(f"render_{code}.png", prozent=150, samples=24)
    for code in VK:                                       # Phasen: Gerüst zuerst, dann Nord -> Süd
        for i, ph in enumerate([None, "P1", "P2", "P3"]):
            zeige(code, ph)
            render(f"phase_{code}_P{i}.png", prozent=60, samples=14)
    zeige("V4", "P4")
    render("render_V4_nah.png", "nah", prozent=125, samples=24)
  if True:
    # .blend speichern (alle Varianten sichtbar umschaltbar über Collections)
    zeige("V1", "P4")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "gartenquartier_bergfrieden.blend"), compress=True)

    # GLB-Export: Kontext+Gerüst gemeinsam, jede Variante einzeln (Phasen als Knoten)
    def export(datei, colls):
        bpy.ops.object.select_all(action="DESELECT")
        for c in colls:
            for ob in c.all_objects:
                ob.select_set(True)
        bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, datei), export_format="GLB", use_selection=True,
                                  export_apply=True, export_yup=True, export_cameras=False, export_lights=False,
                                  export_draco_mesh_compression_enable=False)
        print("GLB", datei, flush=True)
    for code in VK:
        for ph in VK[code].values():
            ph.hide_viewport = False
            ph.hide_render = False
    export("kontext.glb", [K, ENT])
    for code in VK:
        export(f"{code}.glb", [bpy.data.collections[code]])
print("FERTIG", flush=True)
