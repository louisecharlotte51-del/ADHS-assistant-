"""
Gartenquartier Bergfrieden – Entwurfsgerüst auf Katastergrundlage
=================================================================
Überträgt den Handentwurf (A3-Skizze „Unbenanntes Projekt 10“) auf echte
Geometrie (Geoportal Berlin, EPSG:25833):

  1 Grüne Hauptachsen   dunkelgrüner Rahmen + Bänder entlang der Komturstraße
  2 Wasserader          Tempelhofer Feld -> Teltowkanal, mit Verästelungen
  3 Freiräume           Hauptadern, Schwammflächen, Grünräume, Zwischenräume
  4 Erschließung        Trichter an den Rändern (öffentlich -> privat)
  5 Baufelder           Restflächen = polygonale Wohnbaufelder

Bewegungsader = Komturstraße (S-Bahn -> Kanal), Erholungsader = Albrechtshöhe-
Promenade (Franckepark -> Osten), Quartiershauptplatz am Kanal.
Alle Maße in Metern. Aufruf: python3 entwurf.py -> entwurf.json
"""
import json, math
from shapely.geometry import shape, Point, LineString, Polygon, box, mapping
from shapely.ops import unary_union, polygonize, nearest_points
from shapely import affinity

DAT = "daten/"
L = lambda n: json.load(open(DAT + n + ".json"))["features"]

# ---------------- Kontext ----------------
STR = {}
for f in L("str"):
    STR.setdefault(f["properties"]["strassenname"], []).append(shape(f["geometry"]))
STR = {k: unary_union(v) for k, v in STR.items()}
KEP = {(f["properties"]["name_der_k"], f["properties"]["teil"]): shape(f["geometry"]) for f in L("kep")}
KANAL = [shape(f["geometry"]) for f in L("gew") if f["properties"]["gewname"] == "Teltowkanal"][0]
FNP = [(f["properties"]["nutzungsart"], shape(f["geometry"])) for f in L("fnp")]
BAHN = unary_union([g for n, g in FNP if n == "Bahnfläche"])
FELD = [shape(f["geometry"]) for f in L("gruen") if "Tempelhofer Freiheit" in (f["properties"]["namenr"] or "")][0]

# S-Bahn-Station (Entwurf): Ringbahn auf Höhe der Komturstraße
_quer = LineString([(391345, 5813850), (391345, 5814300)]).intersection(BAHN)
STATION = Point(391345, (_quer.bounds[1] + _quer.bounds[3]) / 2)

# ---------------- Plangebiet ----------------
kol = [KEP[("Lebensfreude", "-")], KEP[("Bergfrieden", "-")], KEP[("Albrechtshöhe", "a")],
       KEP[("Albrechtshöhe", "b")], KEP[("Südring", "-")]]
west = unary_union(kol[:3]).buffer(14, join_style=2).buffer(-14, join_style=2)
netz = unary_union([STR[n] for n in ("Komturstraße", "Oberlandstraße", "Sachsenhauser Straße", "Teilestraße")]
                   + [box(391280, 5813280, 391560, 5813850).boundary])
ost = [p for p in polygonize(netz) if p.contains(Point(391420, 5813560))][0]
KOMTUR_ACHSE = STR["Komturstraße"]
KOMTUR_ROW = KOMTUR_ACHSE.buffer(9, cap_style=2)                    # Bewegungsader 18 m
GEBIET = unary_union([west, ost, box(391290, 5813330, 391340, 5813830).intersection(
    west.union(ost).convex_hull)]).buffer(2).buffer(-2)
GEBIET = GEBIET.intersection(unary_union([west.convex_hull, ost]).buffer(1))

# ---------------- 1 Grüne Hauptachsen ----------------
def kurve(pts, n=12):
    """Catmull-Rom-Glättung für handgezeichnete Linien."""
    out = []
    p = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for t in [j / n for j in range(n)]:
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in range(2)))
    out.append(pts[-1])
    return LineString(out)

# Bänder links/rechts der Komturstraße (dunkelgrün in der Skizze), aufgeweitet an der Kreuzung
band = KOMTUR_ACHSE.buffer(26, cap_style=2).difference(KOMTUR_ROW)
kreuz = Point(391305, 5813470).buffer(42)
HAUPT_NS = band.union(kreuz.difference(KOMTUR_ROW)).intersection(GEBIET)
ERHOLUNG = kurve([(390735, 5813565), (390880, 5813546), (390910, 5813525), (391010, 5813500),
                  (391120, 5813488), (391220, 5813484), (391305, 5813470), (391400, 5813478),
                  (391495, 5813520), (391600, 5813505), (391720, 5813470)])
ERHOLUNG_FL = ERHOLUNG.buffer(16).intersection(GEBIET).union(
    Point(391190, 5813486).buffer(30).intersection(GEBIET))          # Blob wie in der Skizze
RAND = GEBIET.difference(GEBIET.buffer(-11))                          # Zwischenräume an Grenzen

# Ostfeld: Norden (am Autobahnohr) und Südosten bleiben Grün + Bestand (grau in der Skizze)
OST_NORD = ost.intersection(box(391300, 5813680, 391600, 5813900))
_teile = ost.difference(ERHOLUNG.buffer(16))
OST_SUED = unary_union([p for p in getattr(_teile, "geoms", [_teile]) if p.centroid.y < 5813470])
BESTAND = []
for f in L("geb"):
    g = shape(f["geometry"])
    rp = g.representative_point()
    if g.area > 350 and (rp.within(OST_NORD) or rp.within(OST_SUED)):
        BESTAND.append(dict(geo=g, og=f["properties"]["aog"] or 2, typ=f["properties"]["bezgfk"]))

# ---------------- 2 Wasserader ----------------
WASSER = kurve([(391205, 5814040), (391170, 5813930), (391140, 5813860), (391152, 5813790),
                (391185, 5813720), (391172, 5813660), (391205, 5813595), (391250, 5813540),
                (391288, 5813488), (391282, 5813420), (391286, 5813340), (391279, 5813270),
                (391276, 5813215), (391300, 5813185)])
AESTE = [kurve(a) for a in [
    [(391150, 5813800), (391115, 5813812), (391078, 5813800), (391040, 5813790)],   # NW oben
    [(391180, 5813705), (391140, 5813690), (391098, 5813705), (391040, 5813690)],   # NW Mitte
    [(391190, 5813745), (391240, 5813768), (391300, 5813800)],                      # trennt Nordfeld
    [(391190, 5813690), (391240, 5813700), (391300, 5813710)],                      # zur Achse
    [(391180, 5813630), (391135, 5813610), (391090, 5813580), (391030, 5813585)],   # W Mitte
    [(391222, 5813575), (391262, 5813592), (391305, 5813600)],                      # zur Achse
    [(391228, 5813566), (391178, 5813535), (391125, 5813508)],                      # SW diagonal
    [(391270, 5813500), (391200, 5813455), (391130, 5813440), (391040, 5813420)],   # SW lang
    [(391150, 5813440), (391140, 5813400), (391150, 5813350)],                      # SW in Feld
    [(391225, 5813455), (391230, 5813405), (391240, 5813340)],                      # SW in Feld
    [(391335, 5813595), (391400, 5813600), (391460, 5813612), (391520, 5813630), (391560, 5813640)],   # O: trennt NO/O
    [(391380, 5813660), (391375, 5813600), (391385, 5813540), (391395, 5813490)],   # O: Achsenstreifen
    [(391335, 5813470), (391385, 5813460), (391430, 5813470)],                      # SO
]]
WASSER_FL = WASSER.buffer(7).union(unary_union([a.buffer(3.5) for a in AESTE]))
SCHWAMM = []                                                           # Retentionsknoten
for a in AESTE + [WASSER]:
    for d in range(18, int(a.length), 34):
        p = a.interpolate(d)
        if p.within(GEBIET):
            SCHWAMM.append(p.buffer(7 if a is not WASSER else 10))
SCHWAMM_FL = unary_union(SCHWAMM)
RETENTION = Polygon([(391300, 5813205), (391420, 5813232), (391445, 5813205), (391440, 5813175),
                     (391305, 5813150)]).difference(KANAL)
PLATZ = Point(391262, 5813228).buffer(34).difference(KOMTUR_ROW).difference(KANAL)   # Quartiershauptplatz

# ---------------- 4 Erschließung: Trichter ----------------
def trichter(rand_pt, richtung_pt, tiefe=26, mund=26):
    a = Point(rand_pt); b = Point(richtung_pt)
    ang = math.atan2(b.y - a.y, b.x - a.x)
    nx, ny = -math.sin(ang), math.cos(ang)
    spitze = (a.x + math.cos(ang) * tiefe, a.y + math.sin(ang) * tiefe)
    return Polygon([(a.x + nx * mund / 2, a.y + ny * mund / 2), spitze, (a.x - nx * mund / 2, a.y - ny * mund / 2)])

TRICHTER_DEF = [((391041, 5813741), (391100, 5813742)),      # Zastrowstraße
                ((391022, 5813509), (391090, 5813520)),      # Felixstraße
                ((391095, 5813860), (391110, 5813800)),      # Götzstraße Nord
                ((391240, 5813865), (391230, 5813800)),      # Nord / Feld
                ((391090, 5813362), (391100, 5813420)),      # Albrechtstraße West
                ((391200, 5813343), (391205, 5813400)),      # Albrechtstraße Mitte
                ((391318, 5813690), (391260, 5813690)),      # Komturstraße West
                ((391330, 5813680), (391390, 5813680)),      # Komturstraße Ost
                ((391500, 5813560), (391440, 5813565)),      # Sachsenhauser Straße
                ((391460, 5813790), (391450, 5813730))]      # Oberlandstraße
TRICHTER = [trichter(a, b).intersection(GEBIET.buffer(4)) for a, b in TRICHTER_DEF]

# ---------------- 5 Baufelder ----------------
GRUEN_OST = unary_union([OST_NORD, OST_SUED]).difference(unary_union([b["geo"].buffer(4) for b in BESTAND]))
frei = unary_union([KOMTUR_ROW.buffer(2), HAUPT_NS, ERHOLUNG_FL, RAND, WASSER_FL.buffer(5), OST_NORD, OST_SUED,
                    SCHWAMM_FL.buffer(3), unary_union(TRICHTER).buffer(3)]
                   + [b["geo"].buffer(6) for b in BESTAND])
rest = GEBIET.difference(frei)
BAUFELDER = []
for p in getattr(rest, "geoms", [rest]):
    q = p.buffer(-5, join_style=2).buffer(5, join_style=2).simplify(4)
    for r in getattr(q, "geoms", [q]):
        if r.geom_type == "Polygon" and r.area > 1400:
            # Facettieren wie in der Skizze: Ecken brechen
            r2 = r.buffer(-4, join_style=2).buffer(4, join_style=3).simplify(3)
            BAUFELDER.append(r2)
BAUFELDER.sort(key=lambda g: -g.centroid.y)

# Phasen: von der S-Bahn (Nord) zum Kanal (Süd)
PHASEN = [("P1", 2029, 2032, "Ankunft an der S-Bahn"), ("P2", 2032, 2035, "Gartenmitte"),
          ("P3", 2035, 2038, "Erholungsader"), ("P4", 2038, 2042, "Ankunft am Kanal")]
PHASEN = [("P0", 2027, 2029, "Vorlauf: S-Bahn, Adern, Gärten verlagern"),
          ("P1", 2029, 2032, "Ankunft an der S-Bahn"), ("P2", 2032, 2035, "Gartenmitte"),
          ("P3", 2035, 2038, "Erholungsader"), ("P4", 2038, 2042, "Ankunft am Kanal")]
def phase(g):
    y = g.centroid.y
    return "P1" if y > 5813700 else "P2" if y > 5813620 else "P3" if y > 5813470 else "P4"

ORIGIN = (391250.0, 5813550.0)    # lokaler Nullpunkt für 3D

if __name__ == "__main__":
    F = lambda g, **p: dict(type="Feature", geometry=mapping(g), properties=p)
    feats = [F(GEBIET, ebene="gebiet"), F(HAUPT_NS, ebene="hauptader"), F(ERHOLUNG_FL, ebene="erholung"),
             F(ERHOLUNG, ebene="erholung_linie"), F(RAND, ebene="zwischenraum"), F(WASSER, ebene="wasser_linie"),
             F(WASSER_FL, ebene="wasser"), F(SCHWAMM_FL, ebene="schwamm"), F(RETENTION, ebene="retention"),
             F(PLATZ, ebene="platz"), F(GRUEN_OST, ebene="gruenraum"), F(KOMTUR_ROW, ebene="bewegung"), F(STATION, ebene="station")]
    feats += [F(a, ebene="ast", nr=i) for i, a in enumerate(AESTE)]
    feats += [F(t, ebene="trichter", nr=i) for i, t in enumerate(TRICHTER)]
    feats += [F(b["geo"], ebene="bestand", og=b["og"], typ=b["typ"]) for b in BESTAND]
    feats += [F(g, ebene="baufeld", nr=i + 1, phase=phase(g), flaeche=round(g.area)) for i, g in enumerate(BAUFELDER)]
    json.dump(dict(type="FeatureCollection", features=feats, origin=ORIGIN), open("entwurf.json", "w"))
    print("Gebiet", round(GEBIET.area / 1e4, 2), "ha | Baufelder", len(BAUFELDER),
          round(sum(g.area for g in BAUFELDER) / 1e4, 2), "ha | Station", [round(v) for v in STATION.coords[0]],
          "| Bestand", len(BESTAND), "| Schwammknoten", len(SCHWAMM))
    for i, g in enumerate(BAUFELDER):
        print(" BF", i + 1, phase(g), round(g.area), [round(v) for v in g.centroid.coords[0]])
