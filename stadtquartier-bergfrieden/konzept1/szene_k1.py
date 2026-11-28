"""
Szene für Blender (Konzept I, Variante A): lokale Koordinaten um ORIGIN (391250, 5813550), Meter, z nach oben.
Aufruf: python3 szene_k1.py -> 3d/szene_k1.json ; dann blender -b --python blender_k1.py -- --render|--export
"""
import json, os
import shapely
from shapely.geometry import shape, Polygon, MultiPolygon, Point, box
from shapely.ops import unary_union
import plaene as PL
from plaene import B, G, FELDER, PARKS, GA, GEBIET, FELD_U, ST, retention, hoehe
from bebauung import PLATZ_VOR, PLATZ_EIN, TOR, ACHSE_EW, E, HIER

OX, OY = 391250.0, 5813550.0
OUT = os.path.join(HIER, "3d")
os.makedirs(OUT, exist_ok=True)
CLIP = box(390900, 5813150, 391620, 5814260)


def ring(p):
    return [[round(x - OX, 2), round(y - OY, 2)] for x, y in list(p.exterior.coords)[:-1]]


def flaeche(g, art, z=0.0):
    """Dreiecke über constrained Delaunay: v (flach), f (Indizes)."""
    g = g.intersection(CLIP).buffer(0)
    out = []
    for p in getattr(g, "geoms", [g]):
        if p.geom_type != "Polygon" or p.area < 1:
            continue
        p = p.simplify(0.3)
        tri = shapely.constrained_delaunay_triangles(p)
        v, f, idx = [], [], {}
        for t in tri.geoms:
            ids = []
            for x, y in list(t.exterior.coords)[:3]:
                k = (round(x, 2), round(y, 2))
                if k not in idx:
                    idx[k] = len(v) // 2
                    v += [round(x - OX, 2), round(y - OY, 2)]
                ids.append(idx[k])
            f += ids
        out.append(dict(art=art, z=z, v=v, f=f))
    return out


hs = B["A"]["haeuser"]
geb = unary_union([shape(h["geo"]) for h in hs])
ret = unary_union([retention(g) for n, g in PARKS if n != "Stadtwald"])
mulde = GA.parallel_offset(4.5, "left").buffer(1.6)
parks = unary_union([g for n, g in PARKS if n != "Stadtwald"]).difference(ret)
wald = unary_union([g for n, g in PARKS if n == "Stadtwald"])
plaetze = unary_union([PLATZ_VOR, PLATZ_EIN, TOR, ST.DECKEL.difference(ST.HANG)])
privat = shape(G["A"]["privat"])
halb = shape(G["A"]["halb"])
strassen = unary_union([g.buffer(PL.BREITE(n) / 2, cap_style=2) for n, g in PL.STRASSEN.items()])
grube = ST.EINSCHNITT.union(ST.A100_TROG).intersection(CLIP)
boden = CLIP.difference(grube)
weg_ga = GA.buffer(2, cap_style=2).difference(FELD_U).difference(ST.HALLE)

S = dict(flaechen=[], haeuser=[], kontext=[], baeume=[], station={}, kameras={})
F = S["flaechen"]
F += flaeche(boden.difference(GEBIET).difference(strassen).difference(PL.E.FELD), "umgebung")
F += flaeche(PL.E.FELD.difference(grube), "feld")
F += flaeche(strassen.difference(grube).difference(plaetze), "asphalt", 0.02)
F += flaeche(GEBIET.difference(FELD_U).difference(parks).difference(wald).difference(ACHSE_EW).difference(plaetze).difference(strassen), "pflaster", 0.03)
F += flaeche(plaetze.difference(grube.difference(ST.DECKEL)), "platz", 0.05)
F += flaeche(halb.difference(geb), "garten", 0.04)
F += flaeche(privat.difference(geb), "privatgarten", 0.06)
F += flaeche(parks.union(ACHSE_EW).difference(mulde), "wiese", 0.05)
F += flaeche(wald, "wald", 0.05)
F += flaeche(weg_ga.difference(ret), "weg", 0.08)
F += flaeche(ret.union(mulde).difference(geb), "wasser", -0.3)
F += flaeche(PL.WASSER, "wasser", -1.0)
F += flaeche(ST.HANG, "wiese", 0.05)
for b in (ST.BRUECKE_W, ST.BRUECKE_O):
    F += flaeche(b, "bruecke", 0.6)
F += flaeche(ST.FELDBALKON, "platz", 0.3)
F += flaeche(ST.KASKADE.buffer(1.4), "wasser", 0.1)

for h in hs:
    g = shape(h["geo"])
    for p in getattr(g, "geoms", [g]):
        S["haeuser"].append(dict(ring=ring(p), g=h["g"], h=round(hoehe(h["g"]), 2), typ=h["typ"], q=h["quartier"], eg=h["eg"]))
for g, n in PL.KONTEXT:
    if g.intersects(CLIP):
        for p in getattr(g, "geoms", [g]):
            if p.geom_type == "Polygon":
                S["kontext"].append(dict(ring=ring(p.simplify(0.4)), h=round(hoehe(n), 1)))
# Bäume: Bestand + Parks + Komturstraße + Grünachse + Wohnwege
bm = [(p, 3.2) for p in PL.BAEUME if p.within(CLIP) and not p.within(FELD_U)]
for n, g in PARKS:
    bm += PL.baumraster(g.buffer(-3), 8 if n == "Stadtwald" else 11, 0.8 if n == "Stadtwald" else 0.45, seed=len(n) + int(g.area) % 97,
                        aus=ret.buffer(2))
bm += PL.reihe_baeume(E.KOMTUR_ACHSE.intersection(GEBIET.buffer(20)), 13, 7.5) + PL.reihe_baeume(E.KOMTUR_ACHSE.intersection(GEBIET.buffer(20)), 13, -7.5)
bm += PL.reihe_baeume(GA, 16, -9)
for k, l, b in PL.WEGE:
    if k == "wohnweg" and b >= 12:
        bm += PL.reihe_baeume(l, 18, 4)
bm += [(p, 3) for p, r in PL.baumraster(PLATZ_VOR.buffer(-6), 14, 0.5, seed=5)]
S["baeume"] = [[round(p.x - OX, 1), round(p.y - OY, 1), round(6 + r * 2.4, 1)] for p, r in bm if not p.within(geb.buffer(2))]

# Station: Halle (Brücke), Dach-Ellipse, Kioske, Radstation, Grube (Einschnitt + Trog)
S["station"] = dict(halle=ring(ST.HALLE), dach=ring(ST.DACH.simplify(0.5)), kioske=[ring(k) for k in ST.KIOSKE], radstation=ring(ST.RADSTATION),
                    grube=[ring(p) for p in getattr(grube, "geoms", [grube])], deckel=ring(ST.DECKEL),
                    bahnsteig=ring(ST.BAHNSTEIG), gleise=[[[round(x - OX, 1), round(y - OY, 1)] for x, y in l.coords] for l in ST.GLEISE],
                    winkel=-26)


def kam(name, pos, ziel, linse, z=1.7, zz=None):
    S["kameras"][name] = dict(pos=[round(pos[0] - OX, 1), round(pos[1] - OY, 1), z],
                              ziel=[round(ziel[0] - OX, 1), round(ziel[1] - OY, 1), zz if zz is not None else z], linse=linse)


_n = PL.ST.NAMEN
kam("ankunft", ST.w(-75, 85), ST.w(25, -165), 28, z=38, zz=0)                          # Feldbalkon: über das Dach auf den Bahnhofsplatz
kam("bahnhofsplatz", ST.w(-55, -150), ST.w(40, -40), 22, z=1.7, zz=8)                 # Germaniastraße -> Station + Hochpunkt
kam("schulpark", (_n["park1"].x - 25, _n["park1"].y - 20), (_n["park1"].x + 60, _n["park1"].y + 30), 22, zz=4)
kam("hauptplatz", (_n["haupt"].x - 19, _n["haupt"].y - 33), (_n["haupt"].x + 60, _n["haupt"].y + 50), 22, zz=4)
kam("gartenplatz", (_n["garten"].x - 10, _n["garten"].y + 25), (_n["garten"].x + 30, _n["garten"].y - 60), 22, zz=3)
kam("luft", (390850, 5813050), (391280, 5813680), 35, z=520, zz=0)
json.dump(S, open(os.path.join(OUT, "szene_k1.json"), "w"))
print("Flächen", len(F), "Häuser", len(S["haeuser"]), "Kontext", len(S["kontext"]), "Bäume", len(S["baeume"]))
