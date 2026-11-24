"""
Exportiert Kontext + Entwurf + 5 Varianten als triangulierte Meshes (3d/szene.json)
für blender_szene.py. Lokale Koordinaten: x/y in Metern ab ORIGIN, z nach oben.
"""
import json, math, random
import numpy as np
import mapbox_earcut as earcut
from shapely.geometry import shape, box, Point, Polygon, MultiPolygon, LineString
from shapely.ops import unary_union
import entwurf as E
import varianten as V

OX, OY = E.ORIGIN
BB = box(390650, 5812980, 391900, 5814330)
rnd = random.Random(5)


def polys(g):
    if g.is_empty:
        return []
    if g.geom_type == "Polygon":
        return [g]
    return [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon" and p.area > 0.5]


class Mesh:
    def __init__(self):
        self.v, self.f = [], []

    def flach(self, g, z):
        for p in polys(g.simplify(0.3)):
            ringe = [np.array(p.exterior.coords[:-1])] + [np.array(r.coords[:-1]) for r in p.interiors]
            ringe = [r for r in ringe if len(r) >= 3]
            if not ringe:
                continue
            pts = np.vstack(ringe)
            ends = np.cumsum([len(r) for r in ringe]).astype(np.uint32)
            tri = earcut.triangulate_float64(pts.astype(float), ends)
            b = len(self.v)
            self.v += [(x - OX, y - OY, z) for x, y in pts]
            self.f += [(b + tri[i], b + tri[i + 1], b + tri[i + 2]) for i in range(0, len(tri), 3)]

    def prisma(self, g, z0, z1, dach=None):
        for p in polys(g.simplify(0.2)):
            ringe = [list(p.exterior.coords[:-1])] + [list(r.coords[:-1]) for r in p.interiors]
            for r in ringe:
                n = len(r)
                for i in range(n):
                    a, c = r[i], r[(i + 1) % n]
                    b = len(self.v)
                    self.v += [(a[0] - OX, a[1] - OY, z0), (c[0] - OX, c[1] - OY, z0),
                               (c[0] - OX, c[1] - OY, z1), (a[0] - OX, a[1] - OY, z1)]
                    self.f += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
            (dach or self).flach(p, z1)

    def daten(self):
        return dict(v=[round(c, 2) for t in self.v for c in t], f=[int(i) for t in self.f for i in t])


L = lambda n: json.load(open(E.DAT + n + ".json"))["features"]
objs = {}
def M(name):
    objs.setdefault(name, Mesh())
    return objs[name]

# ---------------- Boden & Nutzung ----------------
M("boden").flach(BB.buffer(400), -0.05)
for f in L("fnp"):
    n = f["properties"]["nutzungsart"] or ""
    g = shape(f["geometry"]).intersection(BB)
    if n.startswith("Grünfläche"):
        M("gruen_kontext").flach(g.difference(E.GEBIET), 0.02)
    elif n.startswith("Bahnfläche"):
        M("bahn").flach(g, 0.03)
    elif n.startswith("Autobahn"):
        M("autobahn").flach(g, 0.04)
M("wasser").flach(unary_union([shape(f["geometry"]) for f in L("gew")]).intersection(BB), 0.06)
strassen = []
for f in L("str"):
    g = shape(f["geometry"])
    if not g.intersects(BB):
        continue
    kl = f["properties"]["strassenklasse"] or "G"
    strassen.append(g.buffer(9 if kl in ("I", "II") else 7 if kl == "III" else 5.5, cap_style=2))
M("strasse").flach(unary_union(strassen).intersection(BB).difference(E.GEBIET.buffer(-1)), 0.07)

# ---------------- Kontextgebäude ----------------
for f in L("geb"):
    g = shape(f["geometry"])
    if not g.intersects(BB) or g.representative_point().within(E.GEBIET):
        continue
    og = f["properties"]["aog"] or 2
    M("kontext").prisma(g, 0, og * 3.2 + 0.8, dach=M("kontext_dach"))
for b in E.BESTAND:
    M("bestand").prisma(b["geo"], 0, b["og"] * 3.4 + 1, dach=M("bestand_dach"))

# ---------------- Entwurfsebenen ----------------
M("gebiet_garten").flach(E.GEBIET.difference(E.KOMTUR_ROW), 0.10)
M("zwischenraum").flach(E.RAND, 0.12)
M("hauptader").flach(E.HAUPT_NS.union(E.GRUEN_OST), 0.13)
M("erholung").flach(E.ERHOLUNG_FL, 0.15)
M("trichter").flach(unary_union(E.TRICHTER), 0.16)
M("bewegung").flach(E.KOMTUR_ROW.intersection(BB), 0.11)
_kontext_geb = unary_union([shape(f["geometry"]).buffer(4) for f in L("geb")
                            if shape(f["geometry"]).intersects(BB) and not shape(f["geometry"]).representative_point().within(E.GEBIET)])
_korridor = unary_union([E.GEBIET.buffer(2), box(391225, 5813140, 391330, 5813345),
                         box(391120, 5813850, 391260, 5814060)])
WASSER_3D = E.WASSER_FL.union(E.SCHWAMM_FL).intersection(_korridor).difference(_kontext_geb.difference(E.GEBIET))
M("wasserader").flach(WASSER_3D.intersection(BB), 0.18)
M("wasserader").flach(E.RETENTION, 0.18)
M("platz").flach(E.PLATZ, 0.17)
# S-Bahn-Station (Entwurf): Bahnsteigdach quer zur Komturstraße entlang des Rings
st = E.STATION
bahn_lokal = E.BAHN.intersection(st.buffer(150))
ang = math.degrees(math.atan2(*reversed([c[1] - c[0] for c in zip(*list(bahn_lokal.minimum_rotated_rectangle.exterior.coords)[:2])])))
from shapely import affinity
dach = affinity.rotate(box(st.x - 85, st.y - 9, st.x + 85, st.y + 9), ang, origin=st)
M("station").prisma(dach, 6.5, 7.6, dach=M("station_dach"))
M("station").prisma(Point(st.x, st.y - 30).buffer(4, join_style=2), 0, 12)          # S-Pylon

# ---------------- Bäume ----------------
baeume = []
for n in ("baum_strassenbaeume", "baum_anlagenbaeume"):
    for f in L(n):
        p = shape(f["geometry"])
        if p.within(BB) and not p.within(E.GEBIET):
            h = f["properties"].get("baumhoehe") or 14
            try:
                h = float(h)
            except Exception:
                h = 14
            baeume.append((round(p.x - OX, 1), round(p.y - OY, 1), round(min(max(h, 6), 26), 1), 0))
def baumreihe(linie, abst, versatz, ausschluss):
    for d in np.arange(4, linie.length, abst):
        p = linie.interpolate(d)
        q = linie.interpolate(min(d + 1, linie.length))
        nx, ny = -(q.y - p.y), q.x - p.x
        n = math.hypot(nx, ny) or 1
        for s in versatz:
            t = Point(p.x + nx / n * s, p.y + ny / n * s)
            if t.within(E.GEBIET.buffer(30)) and not t.within(ausschluss):
                baeume.append((round(t.x - OX, 1), round(t.y - OY, 1), round(rnd.uniform(9, 16), 1), 1))
blocker = unary_union([E.WASSER_FL, E.KOMTUR_ROW] + E.BAUFELDER)
baumreihe(E.ERHOLUNG, 10, (-12, 12), blocker)
baumreihe(E.KOMTUR_ACHSE, 11, (-16, 16), unary_union([E.WASSER_FL] + E.BAUFELDER))
baumreihe(E.WASSER, 13, (-10, 10), unary_union([E.KOMTUR_ROW] + E.BAUFELDER))
for g in polys(E.GRUEN_OST):
    x0, y0, x1, y1 = g.bounds
    for _ in range(int(g.area / 260)):
        p = Point(rnd.uniform(x0, x1), rnd.uniform(y0, y1))
        if p.within(g):
            baeume.append((round(p.x - OX, 1), round(p.y - OY, 1), round(rnd.uniform(10, 18), 1), 1))

# ---------------- Varianten ----------------
geo = json.load(open("varianten_geo.json"))
var = {}
for code in geo:
    vm = {}
    hs = geo[code]["haeuser"]
    frei = unary_union(E.BAUFELDER).difference(unary_union([shape(h["geo"]).buffer(4) for h in hs]))
    for h in hs:
        g = shape(h["geo"])
        ph = h["phase"]
        H = V.hoehe(h["g"])
        key = lambda k: vm.setdefault(f"{code}_{ph}_{k}", Mesh())
        if h["eg"] == "aktiv":
            key("eg").prisma(g, 0, V.EG_H, dach=Mesh())
            key("wohnen").prisma(g, V.EG_H, H, dach=key("dach"))
        else:
            key("wohnen").prisma(g, 0, H, dach=key("dach"))
    # Bäume in den Gärten der Baufelder (variantenabhängig)
    vb = []
    for p_ in polys(frei.buffer(-3)):
        x0, y0, x1, y1 = p_.bounds
        pts = []
        for _ in range(int(p_.area / 30)):
            q = Point(rnd.uniform(x0, x1), rnd.uniform(y0, y1))
            if q.within(p_) and all(q.distance(o) > 15 for o in pts):
                pts.append(q)
        vb += [(round(q.x - OX, 1), round(q.y - OY, 1), round(rnd.uniform(7, 13), 1), E.phase(p_)) for q in pts]
    var[code] = dict(meshes={k: m.daten() for k, m in vm.items()}, baeume=vb)

json.dump(dict(origin=[OX, OY], objekte={k: m.daten() for k, m in objs.items()}, baeume=baeume, varianten=var,
               station=[round(st.x - OX, 1), round(st.y - OY, 1)]),
          open("3d/szene.json", "w"), separators=(",", ":"))
print("Objekte", {k: len(m.f) for k, m in objs.items()})
print("Bäume Kontext+Adern", len(baeume), "| Varianten", {k: (len(v["meshes"]), len(v["baeume"])) for k, v in var.items()})
