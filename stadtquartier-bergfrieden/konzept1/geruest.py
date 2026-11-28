"""
Gerüst Konzept I: Erschließung, Grünachse, Wasserkette, Öffentlichkeit, Feuerwehr-Nachweis.
Wegenetz = Mittellinien der Zwischenräume zwischen Baufeldern und Grünflächen (Voronoi der Feldränder).
Profile (Regelwerk):
  Komturstraße      Hauptachse, 2 Fahrspuren + Radwege + Baumstreifen/Mulde, Tempo 30
  Germaniastraße    zwischen A.1 und A.2: Platzteppich, Mischfläche Tempo 10
  Seitenachsen      Wohnstraße 6,5 m befahrbar + 2,5 m Mulde (West neu, Ost = Sachsenhauser Str.)
  Wohnweg           3,5 m befahrbar (Feuerwehr, Umzug, Müll), sonst Fuß/Rad + Mulde 3-6 m, Vorgärten
  Grünachse         Kanal -> Bahnhof, 8 m: 4 m Weg + 4 m Regenmulde, quert Komturstraße auf Plateau
Aufruf: python3 geruest.py -> geruest.json
"""
import json, os, sys
import numpy as np
HIER = os.path.dirname(os.path.abspath(__file__))
from bebauung import FE, FELDER, E, STATION, ACHSE_EW, GRUEN, TOR
import shapely
from shapely.geometry import shape, mapping, LineString, MultiPoint, Point, Polygon
from shapely.ops import unary_union, linemerge

POLYS = [shape(f["geometry"]) for f in FE]
NAME = {f["properties"].get("name"): shape(f["geometry"]) for f in FE}
ALLES = unary_union(POLYS)
GEBIET = ALLES.buffer(18, join_style=2).buffer(-10, join_style=2)
LUECKE = GEBIET.difference(ALLES)

WEST = LineString([(391086, 5813881), (391079, 5813466)])
KOMTUR = E.KOMTUR_ACHSE
GERMANIA = E.STR["Germaniastraße"]


def mittellinien():
    pts, lab = [], []
    for i, p in enumerate(POLYS):
        for g in getattr(p, "geoms", [p]):
            r = g.exterior
            for d in np.arange(0, r.length, 2.5):
                q = r.interpolate(d)
                pts.append((q.x, q.y)); lab.append(i)
    zellen = shapely.voronoi_polygons(MultiPoint(pts), extend_to=GEBIET.envelope.buffer(50), ordered=True)
    zellen = list(zellen.geoms)
    regionen = [unary_union([z for z, l in zip(zellen, lab) if l == i]) for i in range(len(POLYS))]
    grenzen = unary_union([r.boundary for r in regionen]).intersection(LUECKE.buffer(-1))
    linien = [l for l in getattr(linemerge(grenzen), "geoms", [linemerge(grenzen)]) if l.length > 6]
    return linien


def klasse(l):
    m = l.interpolate(0.5, normalized=True)
    breite = 2 * min(p.distance(m) for p in POLYS)
    if l.distance(KOMTUR) < 6 and m.distance(KOMTUR) < 10:
        return "komtur", breite
    if m.distance(GERMANIA) < 12:
        return "germania", breite
    if m.distance(WEST) < 14:
        return "seitenachse", breite
    if breite > 45:
        return "platz", breite
    return "wohnweg", breite


def gruenachse():
    """Grüne Ader Kanal -> Bahnhof durch die Kette der Parks (Retentionskette)."""
    g = lambda n, k=0: [p for f, p in [(f, shape(f["geometry"])) for f in FE] if f["properties"].get("name") == n][k]
    kanal = Point(NAME["5.2"].centroid.x - 60, NAME["5.2"].bounds[1] - 10)
    gr5 = sorted([shape(f["geometry"]) for f in FE if f["properties"].get("name") == "Grün 5"], key=lambda p: p.centroid.y)
    gr1 = sorted([shape(f["geometry"]) for f in FE if f["properties"].get("name") == "Grün 1"], key=lambda p: -p.area)
    kette = [kanal, gr5[0].centroid, gr5[1].centroid, NAME["Grün 2"].centroid,
             Point(gr1[0].centroid.x - 2, gr1[0].bounds[1] + 20), gr1[0].centroid,
             Point((NAME["1.1"].centroid.x + NAME["1.2"].centroid.x) / 2 + 8, NAME["1.2"].bounds[3] - 25),
             TOR.centroid, STATION.centroid]
    return LineString([(p.x, p.y) for p in kette])


def oeffentlichkeit(haeuser):
    """privat: 3 m Vorgarten/Terrasse an jeder Gartenfassade + Reihenhausgärten · halböffentlich: Rest des Baufelds
    (Gemeinschaftsgarten, Hof, tagsüber offen über Wegerecht) · öffentlich: alles außerhalb der Baufelder."""
    geb = unary_union([shape(h["geo"]) for h in haeuser])
    privat, halb = [], []
    for name, q, P in FELDER:
        hs = [shape(h["geo"]) for h in haeuser if h["feld"] == name]
        if not hs:
            halb.append(P); continue
        g = unary_union(hs)
        rh = unary_union([shape(h["geo"]) for h in haeuser if h["feld"] == name and h["typ"] == "reihenhaus"])
        pv = g.buffer(3, join_style=2).union(rh.buffer(11, join_style=2) if not rh.is_empty else Polygon())
        pv = pv.intersection(P).difference(geb)
        privat.append(pv)
        halb.append(P.difference(geb).difference(pv))
    return unary_union(privat), unary_union(halb)


def feuerwehr(haeuser, befahrbar):
    """Jeder Hauseingang höchstens 50 m von einer befahrbaren Fläche (BauO Bln § 5, Zugänge)."""
    zu_weit = [h for h in haeuser if shape(h["geo"]).distance(befahrbar) > 50]
    return len(haeuser) - len(zu_weit), zu_weit


if __name__ == "__main__":
    linien = mittellinien()
    wege = []
    for l in linien:
        k, b = klasse(l)
        wege.append(dict(geo=mapping(l.simplify(1.5)), klasse=k, breite_luecke=round(b, 1)))
    ga = gruenachse()
    straßen = unary_union([E.STR[n] for n in E.STR]).intersection(GEBIET.buffer(150))
    befahrbar = unary_union([straßen.buffer(4), WEST.buffer(4)] +
                            [shape(w["geo"]).buffer(2) for w in wege if w["klasse"] in ("wohnweg", "seitenachse", "germania")])
    B = json.load(open(os.path.join(HIER, "bebauung.json")))
    out = dict(wege=wege, gruenachse=mapping(ga), west=mapping(WEST), gebiet=mapping(GEBIET))
    for var in "AB":
        pv, hb = oeffentlichkeit(B[var]["haeuser"])
        ok, weit = feuerwehr(B[var]["haeuser"], befahrbar)
        out[var] = dict(privat=mapping(pv), halb=mapping(hb), feuerwehr_ok=ok, feuerwehr_n=len(B[var]["haeuser"]))
        print(var, "Feuerwehr ok", ok, "/", len(B[var]["haeuser"]), "privat ha", round(pv.area / 1e4, 2), "halb ha", round(hb.area / 1e4, 2))
    from collections import Counter
    print(Counter(w["klasse"] for w in wege), "Grünachse m", round(ga.length))
    print("Wohnweg-Lücken (m):", sorted(round(w["breite_luecke"]) for w in wege if w["klasse"] == "wohnweg"))
    json.dump(out, open(os.path.join(HIER, "geruest.json"), "w"))
