"""
Konzept I „Grüne Adern" – Bebauung der digitalisierten Baufelder (felder.geojson), zwei Varianten.
Regel 1  Kante: Feldkanten an Komturstraße, Plätzen/Parks, Germania-/Teilestraße bekommen eine geschlossene Kante
         (13 m tief), Ecken an zwei Kanten +2 G. An der Erholungsachse und den Seitenachsen: offene Kante.
Regel 2  Körnung: dahinter kleinteilig, je Quartier eine eigene Typologie.
Regel 3  Abstand: 0,4 H je Haus (BauO Bln), durchgesetzt; Reihenhausgruppen aneinandergebaut.
Variante A „Kante und Garten": durchgehende Kanten, ruhige Gärten dahinter.
Variante B „Nachbarschaften": Kopfbauten mit Lücken, dahinter Hausgruppen um Gemeinschaftsgärten (ecovillage-Prinzip).
Aufruf: python3 bebauung.py -> bebauung.json (Häuser je Variante + Kennwerte)
"""
import json, math, os, sys
import numpy as np
HIER = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.join(HIER, "../gartenquartier"))
sys.path.insert(0, ".")
sys.path.insert(0, HIER)
from shapely.geometry import shape, mapping, Polygon, LineString, Point, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely import affinity
import entwurf as E
from varianten import durchsetzen, hoehe, teile, hauptachse
from typologien import punkte, reihen, zeilen, winkel, H, fuge_h

FE = json.load(open(os.path.join(HIER, "felder.geojson")))["features"]
FELDER = [(f["properties"]["name"], f["properties"]["quartier"], orient(shape(f["geometry"]), 1))
          for f in FE if f["properties"]["art"] == "baufeld"]
GRUEN = unary_union([shape(f["geometry"]) for f in FE if f["properties"]["art"] in ("gruen", "stadtwald")])
ACHSE_EW = unary_union([shape(f["geometry"]) for f in FE if f["properties"]["art"] == "achse"])
PLAETZE = unary_union([shape(f["geometry"]) for f in FE if f["properties"]["art"] == "gruen" and shape(f["geometry"]).area > 1500])
STATION = next(shape(f["geometry"]) for f in FE if f["properties"]["art"] == "station")
STRASSEN = unary_union([E.STR[n] for n in ("Germaniastraße", "Teilestraße", "Sachsenhauser Straße", "Albrechtstraße") if n in E.STR]
                       + [LineString([(391086, 5813881), (391079, 5813466)])])      # neue Seitenachse West
KOMTUR = E.KOMTUR_ACHSE

# Kante: Geschosse (Regel), Ecke, Tiefe; Körnung je Quartier
QH = {"A": (7, 9), "1": (6, 8), "2": (5, 6), "3": (4, 4), "4": (5, 6), "5": (4, 5)}
EG_NUTZ = {"A": "publikum", "1": "publikum", "2": "gemein", "3": "wohnen", "4": "gastro", "5": "kultur"}


# Kanten je Baufeld (Kantenindex nach orient(feld, 1)), festgelegt am Plan, nicht geschätzt:
# k = Hauptplatz/Komturstraße/Bahnhof: immer geschlossen · s = Seitenachse/Straße: in A geschlossen, in B Kopfbauten
# o = offene Kante (Häuser mit Fugen, Durchgänge zu den Gärten) · alle übrigen Kanten: unbebaut (Garten, Weg)
SPEC = {
    "A.1": dict(k="alle"), "A.2": dict(k="nord_west"),
    "1.1": dict(s=[3, 5]), "1.2": dict(k=[0, 1, 8, 6], o=[2]), "1.3": dict(s=[3], o=[1]),
    "1.4": dict(k=[6, 1], o=[2, 4]), "1.5": dict(k=[0], o=[1, 3]),
    "2.1": dict(s=[4], o=[2, 5]), "2.2": dict(k=[5], o=[2]), "2.3": dict(), "2.4": dict(k=[4], o=[0, 3]),
    "3.1": dict(o=[4, 2, 9]), "3.2": dict(k=[5], o=[1, 4]),
    "4.1": dict(s=[1], o=[3, 4]), "4.2": dict(k=[1], o=[4]), "4.3": dict(s=[7], k=[2], o=[1, 4]),
    "5.1": dict(s=[6, 5], o=[1]), "5.2": dict(s=[2]),
}
# Ankunftsquartier: Westteile von A.1 / A.2 werden Plätze (Bahnhofsplatz, Eingangsplatz), Germaniastraße dazwischen = Platzteppich
import station as ST
_WEST = ST.R(-500, -500, -5, 500)
PLATZ_VOR = orient(next(P for n, _, P in FELDER if n == "A.1").intersection(_WEST), 1)
PLATZ_EIN = orient(next(P for n, _, P in FELDER if n == "A.2").intersection(_WEST), 1)
FELDER = [(n, q, orient(P.difference(_WEST), 1) if n in ("A.1", "A.2") else P) for n, q, P in FELDER]
_F = {n: P for n, _, P in FELDER}
# Platzteppich: Durchgang über die Germaniastraße zwischen Vorplatz (A.1) und Eingangsplatz (A.2)
TOR = unary_union([PLATZ_VOR, PLATZ_EIN]).convex_hull.difference(_F["A.1"]).difference(_F["A.2"]).intersection(_WEST.buffer(-0.5))
GRUEN4 = next(shape(f["geometry"]) for f in FE if f["properties"].get("name") == "Grün 4")


def kantentypen(name, P, var):
    sp = SPEC.get(name, {})
    n = len(P.exterior.coords) - 1
    t = ["innen"] * n
    for i in sp.get("o", []):
        t[i] = "offen"
    for i in sp.get("s", []):
        t[i] = "geschlossen" if (var == "A" or name == "1.1") else "offen"
    k = sp.get("k", [])
    c = list(P.exterior.coords)
    if k == "alle":
        k = range(n)
    elif k == "nord_west":                                  # zur Germaniastraße und zum Eingangsplatz
        k = [i for i in range(n) if ST.loc(*c[i])[1] > -216 and ST.loc(*c[i + 1])[1] > -216
             or abs(ST.loc(*c[i])[0] + 5) < 1.5 and abs(ST.loc(*c[i + 1])[0] + 5) < 1.5]
    for i in k:
        t[i] = "geschlossen"
    return t


def baender(P, typen, tiefe=13.0):
    c = list(P.exterior.coords)
    out = []
    for i in range(len(c) - 1):
        if typen[i] == "innen":
            continue
        a, b = c[i], c[i + 1]
        L = math.dist(a, b)
        if L < 8:
            continue
        tx, ty = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        nx, ny = -ty, tx                                   # links = innen bei gegen den Uhrzeigersinn
        q = Polygon([(a[0] - tx * 3, a[1] - ty * 3), (b[0] + tx * 3, b[1] + ty * 3),
                     (b[0] + tx * 3 + nx * tiefe, b[1] + ty * 3 + ny * tiefe), (a[0] - tx * 3 + nx * tiefe, a[1] - ty * 3 + ny * tiefe)])
        out.append((typen[i], q.intersection(P)))
    return out


def luecken(feld, schritt, breite):
    """Lücken senkrecht zur Feldkante alle `schritt` m (Durchgänge in offenen Kanten)."""
    r = feld.exterior
    ls = []
    for d in np.arange(schritt, r.length - schritt / 2, schritt):
        p, q = r.interpolate(d), r.interpolate(d + 1)
        n = math.hypot(q.x - p.x, q.y - p.y) or 1
        nx, ny = -(q.y - p.y) / n, (q.x - p.x) / n
        ls.append(LineString([(p.x - nx * 3, p.y - ny * 3), (p.x + nx * 20, p.y + ny * 20)]).buffer(breite / 2, cap_style=2))
    return unary_union(ls) if ls else Polygon()


def finger(P, kante_hs, laenge=20.0, breite=11.0, jede=2):
    """Finger senkrecht hinter der Kante (Kamm): jedes `jede`-te Kantenhaus bekommt einen Flügel in den Garten."""
    from shapely.ops import nearest_points
    out = []
    for k, h in enumerate(kante_hs):
        if k % jede:
            continue
        c = h["geo"].centroid
        r = nearest_points(P.exterior, c)[0]
        dx, dy = c.x - r.x, c.y - r.y
        n = math.hypot(dx, dy) or 1
        dx, dy = dx / n, dy / n
        a, b = (c.x - dy * breite / 2, c.y + dx * breite / 2), (c.x + dy * breite / 2, c.y - dx * breite / 2)
        f = Polygon([a, b, (b[0] + dx * (laenge + 6.5), b[1] + dy * (laenge + 6.5)), (a[0] + dx * (laenge + 6.5), a[1] + dy * (laenge + 6.5))])
        out.append(f.intersection(P.buffer(-3, join_style=2)))
    return out


def platziere(frei, w, d, ang, bevorzugt=None):
    """Erstes Rechteck w x d (Winkel ang), das ganz in frei liegt; nahe am bevorzugten Punkt."""
    if frei.is_empty:
        return None
    x0, y0, x1, y1 = frei.bounds
    kand = []
    for x in range(int(x0), int(x1), 4):
        for y in range(int(y0), int(y1), 4):
            r = affinity.rotate(box(x - w / 2, y - d / 2, x + w / 2, y + d / 2), ang, origin=(x, y))
            if r.within(frei):
                kand.append(r)
    if not kand:
        return None
    if bevorzugt is not None:
        return min(kand, key=lambda r: r.centroid.distance(bevorzugt))
    return kand[len(kand) // 2]


def feld_bebauen(name, q, P, var):
    hk, he = QH[q]
    c = list(P.exterior.coords)
    typen = kantentypen(name, P, var)
    hs = []
    # --- Kante: geschlossen = aneinandergebaut (Brandwände), offen = Häuser mit Fugen ---
    bs = baender(P, typen)
    geschl = unary_union([b for a, b in bs if a == "geschlossen"]) if bs else Polygon()
    offen_ = unary_union([b for a, b in bs if a == "offen"]).difference(geschl.buffer(0.1)) if bs else Polygon()
    geschl, offen_ = geschl.difference(TOR), offen_.difference(TOR)
    fuge = fuge_h(hk)
    for art, koerper in (("geschlossen", geschl), ("offen", offen_)):
        if koerper.is_empty:
            continue
        if art == "offen":
            koerper = koerper.difference(luecken(P, 26 + fuge, fuge))
        for s in teile(koerper, P, 26 if art == "offen" else 30):
            ecke = any(typen[i] == "geschlossen" and typen[i - 1] == "geschlossen" and Point(c[i]).distance(s) < 4
                       for i in range(len(c) - 1))
            hs.append(dict(geo=s, g=he if (ecke and art == "geschlossen") else hk, typ="kante",
                           eg=EG_NUTZ[q] if art == "geschlossen" else "wohnen"))
    if name == "1.1":                                                  # Grundschule: L an Westachse + Nordstraße
        for h in hs:
            h.update(eg="bildung", typ="schule", g=4)
    kante = unary_union([h["geo"] for h in hs]) if hs else Polygon()
    abstand = max(8.0, 0.4 * hoehe(hk) + 0.4 * hoehe(4) + 1)
    frei = P.buffer(-3, join_style=2).difference(kante.buffer(abstand, join_style=2)).difference(TOR.buffer(4))
    ang = hauptachse(P)
    innen = []
    frei_fuer = lambda g: P.buffer(-2, join_style=2).difference(
        kante.buffer(max(3, 0.4 * hoehe(g)) + max(3, 0.4 * hoehe(hk)) + 0.5, join_style=2)).difference(TOR.buffer(4))
    def add(geo, g, typ, eg):
        if geo is not None:
            innen.append(dict(geo=geo, g=g, typ=typ, eg=eg))
        return geo
    # --- Körnung je Quartier ---
    if name == "A.1":
        spitze = min(c[:-1], key=lambda p: ST.loc(*p)[1])                                    # Südspitze am Ende der Komturachse
        hp = platziere(P, 21, 21, -26, Point(spitze))      # Hochpunkt am Ende der Komturachse
        ok = lambda h: h["geo"].distance(hp) < 0.5 or h["geo"].distance(hp) >= max(3, 0.4 * hoehe(14)) + max(3, 0.4 * hoehe(h["g"]))
        hs = [dict(h, geo=h["geo"].difference(hp)) for h in hs if ok(h)]
        add(hp, 14, "hochpunkt", "publikum")
        # Markthalle als Passage Bahnhof <-> Germaniastraße: füllt den Hof (2 G), Dachgarten für die Bewohner darüber
        k2 = unary_union([h["geo"] for h in hs])
        for p in getattr(P.buffer(-0.5, join_style=2).difference(k2).difference(hp), "geoms", []) or [P.buffer(-0.5, join_style=2).difference(k2).difference(hp)]:
            if p.area > 300:
                add(p, 2, "markthalle", "publikum")
    elif name == "1.1":
        add(platziere(frei_fuer(2), 27, 45, ang, Point(c[1])), 2, "sporthalle", "bildung")
    elif name == "1.3":
        add(platziere(frei_fuer(2), 22, 14, ang, Point(c[0])), 2, "kita", "bildung")
    elif q == "1":
        # Gewerbehof: Werkhallen (1-2 G) als Sockel direkt hinter der Kante, Hof in der Mitte, Anlieferung über den Hof
        kk = unary_union([h["geo"] for h in hs if h["eg"] != "wohnen"])
        ring = kk.buffer(15, join_style=2).intersection(P.buffer(-1, join_style=2)).difference(kante).difference(
            P.buffer(-(13 + 15), join_style=2).difference(kk.buffer(15, join_style=2)))
        for p in getattr(ring, "geoms", [ring]):
            if p.area > 250:
                add(p, 2, "werkhalle", "gewerbe")
    elif name == "2.3":
        add(platziere(P.buffer(-2), 15, 9, ang), 2, "pavillon", "gastro")
    elif q == "2":
        if var == "A":                                                  # Kamm: Finger hinter der Platzkante
            kk = [h for h in hs if h["eg"] != "wohnen"] or hs
            for f in finger(P, kk, jede=2 if fuge_h(4) < 26 else 3):
                add(f.difference(kante), 4, "kammfinger", "wohnen")
        else:                                                           # Hausgruppen um einen Gemeinschaftsgarten
            innen += [dict(h, typ="hausgruppe", eg="wohnen") for h in
                      punkte(P, frei.difference(frei.centroid.buffer(13)), g=3, s=12, abstand=8)]
    elif q == "3":
        sued = Polygon([(P.bounds[0] - 5, P.bounds[1] - 5), (P.bounds[2] + 5, P.bounds[1] - 5),
                        (P.bounds[2] + 5, P.bounds[1] + 24), (P.bounds[0] - 5, P.bounds[1] + 24)])
        rf = frei.difference(sued) if var == "A" else frei.difference(sued).difference(
            LineString([P.centroid, (P.centroid.x + 200, P.centroid.y + 60)]).buffer(9))     # B: Anger quer durchs Feld
        innen += [dict(h, typ="reihenhaus", eg="wohnen") for h in reihen(P, rf)]
        rest = frei.intersection(sued.buffer(4))
        innen += [dict(h, typ="punkthaus", eg="wohnen") for h in punkte(P, rest, g=4, s=15, abstand=12, max_n=4)]
    elif q == "4":
        gh = None
        if name in ("4.3", "4.1"):
            w, d = (32, 18) if name == "4.3" else (18, 12)
            gh = add(platziere(frei_fuer(2), w, d, ang, GRUEN4.centroid), 2 if name == "4.3" else 1,
                     "gartenhalle" if name == "4.3" else "foodlab", "gastro")
        rest = frei.difference(gh.buffer(10)) if gh is not None else frei
        a_, b_, g_ = (30, 24, 4) if var == "A" else (22, 18, 3)
        innen += [dict(h, typ="gartenhof", eg="wohnen") for h in winkel(P, rest, g=g_, a=a_, b=b_, t=11)]
    elif name == "5.2":
        add(platziere(frei_fuer(3), 40, 22, ang, Point(P.centroid.x, P.bounds[1])), 3, "wasserhaus", "kultur")
    elif q == "5":
        if var == "A":
            innen += [dict(h, typ="punkthaus", eg="wohnen") for h in punkte(P, frei, g=4, s=17, abstand=12)]
        else:
            innen += [dict(h, typ="uferzeile", eg="wohnen") for h in zeilen(P, frei, g=4, tiefe=12, seg=30)]
    # Rückseiten auffüllen: kleinere Körnung je Quartier (g, Kantenlänge, Abstand)
    fill = {"1": (4, 16, 10), "2": (4, 16, 10) if var == "A" else (3, 12, 8), "3": (3, 12, 8),
            "4": (4, 15, 10) if var == "A" else (3, 12, 8), "5": (4, 16, 11)}.get(q)
    if fill and name not in ("1.1", "5.2", "2.3"):
        belegt = unary_union([h["geo"].buffer(max(3, 0.4 * hoehe(h["g"])) + max(3, 0.4 * hoehe(fill[0])))
                              for h in innen]) if innen else Polygon()
        innen += [dict(h, typ="stadthaus", eg="wohnen") for h in
                  punkte(P, frei.difference(belegt), g=fill[0], s=fill[1], abstand=fill[2], raster=4)]
    out = []
    for h in hs + innen:
        for p in getattr(h["geo"], "geoms", [h["geo"]]):
            if p.geom_type == "Polygon" and p.area > (150 if h["typ"] in ("kante", "kammfinger") else 60):
                out.append(dict(h, geo=p, feld=name, quartier=q))
    return out


NICHT_WOHNEN = {"werkhalle", "markthalle", "kita", "pavillon", "foodlab", "halle", "sporthalle", "schule", "gartenhalle", "wasserhaus", "gewerbehof"}


def kennwerte(hs):
    bf = sum(P.area for _, _, P in FELDER)
    gr = sum(h["geo"].area for h in hs)
    bgf = sum(h["geo"].area * h["g"] for h in hs)
    nw = sum(h["geo"].area * (h["g"] if h["typ"] in NICHT_WOHNEN else (1 if h["eg"] != "wohnen" else 0)) for h in hs)
    we = (bgf - nw) / 88
    gebiet = unary_union([P for _, _, P in FELDER] + [GRUEN, ACHSE_EW]).buffer(14).area
    je_q = {}
    for q in QH:
        hq = [h for h in hs if h["quartier"] == q]
        fq = sum(P.area for _, qq, P in FELDER if qq == q)
        je_q[q] = dict(grz=round(sum(h["geo"].area for h in hq) / fq, 2), gfz=round(sum(h["geo"].area * h["g"] for h in hq) / fq, 2),
                       g_max=max((h["g"] for h in hq), default=0), haeuser=len(hq))
    return dict(baufelder_ha=round(bf / 1e4, 2), gebiet_ha=round(gebiet / 1e4, 1), grz=round(gr / bf, 2), gfz=round(bgf / bf, 2),
                gfz_brutto=round(bgf / gebiet, 2), bgf=round(bgf), nicht_wohnen=round(100 * nw / bgf), we=round(we),
                ew=round(we * 1.9), ew_ha=round(we * 1.9 / (gebiet / 1e4)), quartiere=je_q)


if __name__ == "__main__":
    out = {}
    for var in ("A", "B"):
        hs = []
        for name, q, P in FELDER:
            hs += feld_bebauen(name, q, P, var)
        hs = [h for h in hs if h["geo"].area > 50]
        hs, eingriffe = durchsetzen(hs, ausnahme=lambda a, b: a.get("gruppe") is not None and a.get("gruppe") == b.get("gruppe"))
        k = kennwerte(hs)
        out[var] = dict(haeuser=[dict(geo=mapping(h["geo"]), g=h["g"], typ=h["typ"], eg=h["eg"], feld=h["feld"], quartier=h["quartier"])
                                 for h in hs], kennwerte=k, eingriffe=eingriffe)
        print(var, {x: k[x] for x in ("grz", "gfz", "gfz_brutto", "we", "ew", "nicht_wohnen", "gebiet_ha")}, "Eingriffe", eingriffe)
        print("  ", {q: (v["grz"], v["gfz"], v["g_max"]) for q, v in k["quartiere"].items()})
    json.dump(out, open(os.path.join(HIER, "bebauung.json"), "w"))
