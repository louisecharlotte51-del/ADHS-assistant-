"""
Exportiert die Varianten V6-V8 mit Nutzung je Geschoss als Meshes (3d/szene2.json).
Kontext, Gerüst und Bäume werden aus 3d/szene.json übernommen.
Mesh-Namen: {Variante}_{Phase}_{Nutzung} (Nutzung: laden, gastro, bildung, gesundheit, arbeiten,
mobilitaet, wohnen, dach) -> Blender-Materialien und Phasenschalter im Web-Viewer.
"""
import json, random
import numpy as np
import mapbox_earcut as earcut
from shapely.geometry import shape, Point
from shapely.ops import unary_union
import entwurf as E
from varianten import EG_H, OG_H
import nutzungen as N

OX, OY = E.ORIGIN
rnd = random.Random(11)


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

    def wand(self, g, z0, z1):
        for p in polys(g.simplify(0.2)):
            for r in [list(p.exterior.coords[:-1])] + [list(r.coords[:-1]) for r in p.interiors]:
                n = len(r)
                for i in range(n):
                    a, c = r[i], r[(i + 1) % n]
                    b = len(self.v)
                    self.v += [(a[0] - OX, a[1] - OY, z0), (c[0] - OX, c[1] - OY, z0),
                               (c[0] - OX, c[1] - OY, z1), (a[0] - OX, a[1] - OY, z1)]
                    self.f += [(b, b + 1, b + 2), (b, b + 2, b + 3)]

    def daten(self):
        return dict(v=[round(c, 2) for t in self.v for c in t], f=[int(i) for t in self.f for i in t])


def bloecke(nutz):
    """Geschosse gleicher Nutzung zusammenfassen: [(nutzung, z0, z1), ...]."""
    out, z = [], 0.0
    for gi, n in enumerate(nutz):
        dz = EG_H if gi == 0 else OG_H
        if out and out[-1][0] == n:
            out[-1][2] = z + dz
        else:
            out.append([n, z, z + dz])
        z += dz
    return out


basis = json.load(open("3d/szene.json"))
geo = json.load(open("nutzung_geo.json"))
bo = N.bestand_orte()
BESTAND_NUTZ = [(bo["bestand_nord"], "arbeiten", "P1", 2), (bo["bestand_sued"], "bildung", "P3", 3), (bo["markthalle"], "gastro", "P4", 1)]
var = {}
for code in geo:
    vm = {}
    M = lambda ph, k: vm.setdefault(f"{code}_{ph}_{k}", Mesh())
    hs = geo[code]["haeuser"]
    for h in hs:
        g = shape(h["geo"])
        ph = h["phase"]
        bl = bloecke(h["nutz"])
        for n, z0, z1 in bl:
            M(ph, n).wand(g, z0, z1)
        M(ph, "dach").flach(g, bl[-1][2])
    # Bestand mit neuer Nutzung: leicht größere Hülle über dem grauen Bestand
    for g, n, ph, og in BESTAND_NUTZ:
        H = og * 3.4 + 1.15
        M(ph, n).wand(g.buffer(0.25, join_style=2), 0, H)
        M(ph, n).flach(g.buffer(0.25, join_style=2), H)
    # V8: Nachbarschaftsplätze als helle Platzflächen
    for p in geo[code]["plaetze"]:
        M(p["phase"], "platz").flach(shape(p["geo"]), 0.2)
    # Bäume in den Gärten der Baufelder
    frei = unary_union(E.BAUFELDER).difference(unary_union([shape(h["geo"]).buffer(4) for h in hs]))
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

json.dump(dict(origin=basis["origin"], objekte=basis["objekte"], baeume=basis["baeume"], varianten=var,
               station=basis["station"]), open("3d/szene2.json", "w"), separators=(",", ":"))
print({k: sorted(v["meshes"]) for k, v in var.items()})
