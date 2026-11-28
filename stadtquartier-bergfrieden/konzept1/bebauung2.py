"""
Konzept I, Stand 2: Baufeld-Regelwerk „Der doppelte Hof“ – dichter, je Quartier eine ablesbare Typologie.
Grundregeln für jedes Baufeld (aus „Südring: Konzepte für Hannover“ + Bürklin/Peterek, Basics Stadtbausteine):
  R1 Baulinie = Feldgrenze: die Häuser stehen an Straße, Achse, Platz und Park, auch an beiden Randachsen.
  R2 Bautiefe 12 m (Wohnen), 13 m mit Gewerbe-EG, Werkhallen 15 m. EG 4,2 m (3,25 m licht).
  R3 Hof ≥ 21 m, unterbaufrei; Nordseite höher (+1 G), Südseite niedriger (−1 G) oder offen.
  R4 Hofkette Ost-West: Durchgang auf Höhe der Feldmitte in West- und Ostkante (8 m Lücke, an Hauptachsen Tor im EG).
  R5 An Hauptachse, Platz, Bahnhof: Kante geschlossen (+1 G, Ecken +1 G). Schmale Felder (< 46 m): nur Nordkante + Garten.
Typologie je Quartier (ablesbar im Schwarzplan):
  A  Stadtblock + Hochpunkt, Markthalle füllt den Hof (Ankunftshof)
  Q1 Werkblock: geschlossener Rand + Werkhallen im Hof um einen Werkhof; 1.1 Schule
  Q2 Blockrand mit offenen Ecken: Gemeinschaftshof, Gastgeber an den Ecken
  Q3 Zeilenhof aus Stadthäusern (3 G) hinter Kopfbauten (5 G) an Achse und Achsenplatz
  Q4 Gartenhof offen nach Süden: Glashäuser in der Öffnung, Gartenhalle am Gartenplatz
  Q5 Kamm zum Wasser: Rücken an der Straße, Finger zum Kanal bzw. Uferpark
Aufruf: python3 bebauung2.py -> bebauung2.json
"""
import json, math, os
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box, mapping
from shapely.ops import unary_union
from shapely import affinity
import bebauung as B
from bebauung import FELDER, SPEC, ST, hoehe, teile, durchsetzen, platziere, hauptachse, GRUEN4, HIER
from typologien import reihen, punkte

D = {"A": 13, "1": 13, "2": 12, "3": 12, "4": 12, "5": 12}
G0 = {"A": 8, "1": 6, "2": 6, "3": 5, "4": 5, "5": 6}
GMAX = {"A": 9, "1": 7, "2": 7, "3": 5, "4": 6, "5": 6}
NAME = {"A": "Sockel, Scheibe, Turm", "1": "Werkblock", "2": "Platzrand und Winkel", "3": "Zeilenhof aus Stadthäusern",
        "4": "Gartenhof offen nach Süden", "5": "Kamm zum Wasser"}


def kanten(P):
    c = list(P.exterior.coords)
    out = []
    for i in range(len(c) - 1):
        a, b = c[i], c[i + 1]
        L = math.dist(a, b)
        t = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        n = (t[1], -t[0])                                     # außen (Feld gegen den Uhrzeigersinn)
        r = "N" if n[1] > .7 else "S" if n[1] < -.7 else ("O" if n[0] > 0 else "W")
        out.append(dict(i=i, a=a, b=b, L=L, t=t, n=n, dir=r))
    return out


def baender(P, ks, auswahl, d):
    """Bandstücke je Kante (Tiefe d), Ecken gehören der wichtigeren Kante (Reihenfolge von auswahl)."""
    ring = P.difference(P.buffer(-d, join_style=2))
    vergeben, out = Polygon(), {}
    for i in auswahl:
        k = ks[i]
        (ax, ay), (bx, by), (tx, ty), (nx, ny) = k["a"], k["b"], k["t"], k["n"]
        e = d + 2
        q = Polygon([(ax - tx * e + nx, ay - ty * e + ny), (bx + tx * e + nx, by + ty * e + ny),
                     (bx + tx * e - nx * (d + 1), by + ty * e - ny * (d + 1)), (ax - tx * e - nx * (d + 1), ay - ty * e - ny * (d + 1))])
        s = q.intersection(ring).difference(vergeben)
        if s.area > 60:
            out[i] = s
            vergeben = vergeben.union(s)
    return out


def luecke(k, p, w, d):
    (tx, ty), (nx, ny) = k["t"], k["n"]
    return Polygon([(p.x - tx * w / 2 + nx * 2, p.y - ty * w / 2 + ny * 2), (p.x + tx * w / 2 + nx * 2, p.y + ty * w / 2 + ny * 2),
                    (p.x + tx * w / 2 - nx * (d + 3), p.y + ty * w / 2 - ny * (d + 3)), (p.x - tx * w / 2 - nx * (d + 3), p.y - ty * w / 2 - ny * (d + 3))])


def hofkette(P, ks, d):
    """R4: Ost-West-Durchgang auf Höhe der Feldmitte -> Lücken in West- und Ostkante."""
    y = P.centroid.y
    linie = LineString([(P.bounds[0] - 5, y), (P.bounds[2] + 5, y)])
    out = []
    for k in ks:
        if k["dir"] in ("W", "O"):
            s = LineString([k["a"], k["b"]]).intersection(linie)
            if not s.is_empty and s.geom_type == "Point":
                out.append((k["i"], s))
    return out


def haus(geo, g, typ, eg, k=None, tor=False):
    return dict(geo=geo, g=int(g), typ=typ, eg=eg, kante=k, tor=tor)


def feld(name, q, P):
    ks = kanten(P)
    sp = B.kantentypen(name, P, "A")                     # geschlossen / offen / innen aus SPEC
    d = D[q]
    hof = not P.buffer(-d - 10.5, join_style=2).is_empty
    achse = {i for i, t in enumerate(sp) if t == "geschlossen"}
    rang = lambda k: (k["i"] in achse, k["dir"] == "N", k["dir"] in ("O", "W"), k["L"])
    alle = [k["i"] for k in sorted(ks, key=rang, reverse=True)]
    hs, extra = [], []
    # --- Auswahl der bebauten Kanten je Typologie ---
    if name == "A.1":
        auswahl = [i for i in alle if ks[i]["dir"] == "N"][:1]                     # Scheibe zur Bahn / A100
    elif q == "3":
        auswahl = [i for i in alle if i in achse or ks[i]["dir"] == "N"]           # Kopfbauten
    elif q == "5":
        rueck = [i for i in alle if i in achse] or [alle[0]]
        auswahl = rueck[:2]
    elif q == "4":
        auswahl = [i for i in alle if ks[i]["dir"] != "S" or i in achse]          # U offen nach Süden
    elif name == "1.1":
        auswahl = [i for i in alle if ks[i]["dir"] in ("N", "W") or i == 1]        # Schule als L + Wohnriegel Ost
    elif not hof:
        # schmales Feld: Winkel aus Nordkante + längster Ost-/Westkante, Süden bleibt Garten
        nord = [i for i in alle if i in achse or ks[i]["dir"] == "N"]
        seite = sorted([i for i in alle if ks[i]["dir"] in ("O", "W") and ks[i]["L"] > 20 and i not in nord], key=lambda i: -ks[i]["L"])[:1]
        auswahl = (nord + seite) or alle[:1]
    else:
        auswahl = alle
    bd = baender(P, ks, auswahl, d)
    # --- Öffnungen ---
    cut = Polygon()
    tore = []
    if hof and q in ("1", "4") and name != "1.1":
        for i, p in hofkette(P, ks, d):
            if i in bd:
                tore.append(luecke(ks[i], p, 6, d))                     # Tordurchgang im EG, Fassade bleibt geschlossen
    # --- Häuser aus den Bändern ---
    eg_axis = {"A": "publikum", "1": "gewerbe", "2": "gemein", "3": "wohnen", "4": "gastro", "5": "kultur"}[q]
    for i, s in bd.items():
        s = s.difference(cut)
        k = ks[i]
        g = G0[q] + (1 if k["dir"] == "N" else -1 if k["dir"] == "S" else 0) + (1 if i in achse else 0)
        if q == "3":
            g = 5
        if name == "1.1" and i != 1:
            g, typ, eg = 4, "schule", "bildung"
        elif q == "4" and name == "4.3" and i == 1:
            g, typ, eg = 2, "gartenhalle", "gastro"
        else:
            typ, eg = "rand", eg_axis if i in achse else "wohnen"
        for st in teile(s, P, 27):
            for p in getattr(st, "geoms", [st]):
                if p.geom_type == "Polygon" and p.area > 90:
                    tor = any(p.intersects(t) for t in tore)
                    hs.append(haus(p, min(g, GMAX[q]) if typ == "rand" else g, typ, eg, i, tor))
    # Ecken an Achsen +1 G
    for h in hs:
        if h["typ"] == "rand" and h["kante"] in achse:
            nachbarn = [x for x in hs if x is not h and x["kante"] != h["kante"] and x["geo"].distance(h["geo"]) < 0.5]
            if nachbarn:
                h["g"] = min(h["g"] + 1, GMAX[q] + (1 if q in ("A", "1", "2") else 0))
    rand = unary_union([h["geo"] for h in hs]) if hs else Polygon()
    innen = P.difference(rand.buffer(0.01))
    # --- Hof je Typologie ---
    if name == "A.1":
        spitze = min(list(P.exterior.coords)[:-1], key=lambda p: ST.loc(*p)[1])
        hp = platziere(P, 21, 21, -26, Point(spitze))
        extra.append(haus(hp, 14, "hochpunkt", "publikum"))
        mh = P.difference(unary_union([h["geo"] for h in hs])).difference(hp)
        for p in getattr(mh, "geoms", [mh]):
            if p.area > 300:
                extra.append(haus(p, 2, "markthalle", "publikum"))
    elif q == "1" and name != "1.1" and hof:
        kern = P.buffer(-d, join_style=2)
        for tiefe in (15, 11, 8):
            werkhof = kern.buffer(-tiefe, join_style=2)
            if werkhof.area > 450:
                break
        hallen = kern.difference(werkhof).difference(cut.buffer(1))
        for p in getattr(hallen, "geoms", [hallen]):
            if p.area > 150:
                extra.append(haus(p, 2, "werkhalle", "gewerbe"))
    elif name == "1.1":
        sh = platziere(innen.buffer(-9, join_style=2), 27, 45, hauptachse(P), Point(ks[1]["a"]))
        if sh is not None:
            extra.append(haus(sh, 2, "sporthalle", "bildung"))
    elif name == "1.3":
        kita = platziere(innen.buffer(-8, join_style=2), 20, 14, hauptachse(P), Point(ks[0]["a"]))
        if kita is not None:
            extra.append(haus(kita, 2, "kita", "bildung"))
    elif q == "3":
        frei = P.buffer(-3, join_style=2).difference(rand.buffer(13, join_style=2))
        # Punkthäuser (6 G) am Waldrand: Südband des Feldes, Blick über den Stadtwald
        sued = unary_union([LineString([k["a"], k["b"]]).buffer(26) for k in ks if k["dir"] == "S"])
        for h in punkte(P, frei.intersection(sued).buffer(-0.5), g=6, s=16, abstand=16, raster=4, max_n=4):
            extra.append(haus(h["geo"], 6, "punkthaus", "wohnen"))
        if extra:
            frei = frei.difference(unary_union([h["geo"] for h in extra]).buffer(12))
        for h in reihen(P, frei, b=6.5, t=10.5, garten=10.0, n=6, luecke=5.0):
            extra.append(haus(h["geo"], 3, "stadthaus", "wohnen"))
            extra[-1]["gruppe"] = h.get("gruppe")
    elif q == "4":
        sued = [k for k in ks if k["dir"] == "S" and k["i"] not in bd and k["L"] > 12]
        for k in sued:                                                          # Glashäuser in der Hoföffnung
            band = baender(P, ks, [k["i"]], 9).get(k["i"])
            if band is None:
                continue
            band = band.difference(rand.buffer(4))
            for st in teile(band, P, 18):
                for p in getattr(st, "geoms", [st]):
                    if p.area > 60:
                        extra.append(haus(p.buffer(-1.5, join_style=2), 1, "glashaus", "gastro"))
        if name == "4.1":
            fl = platziere(innen.buffer(-8, join_style=2), 18, 12, hauptachse(P), GRUEN4.centroid)
            if fl is not None:
                extra.append(haus(fl, 1, "foodlab", "gastro"))
    elif q == "5":
        r = ks[auswahl[0]]
        ang = math.degrees(math.atan2(r["n"][1], r["n"][0])) - 90            # lokales +y = Rückennormale
        c = P.centroid
        rP = affinity.rotate(P, -ang, origin=c)
        rR = affinity.rotate(rand, -ang, origin=c)
        x0, y0, x1, y1 = rP.bounds
        breite, fuge = 12.0, 15.0
        finger = []
        x = x0 + 4
        while x + breite < x1 - 2:
            f = box(x, y0 - 5, x + breite, y1 + 5).intersection(rP.buffer(-3, join_style=2)).difference(rR)
            finger.append(f)
            x += breite + fuge
        for f in finger:
            f = affinity.rotate(f, ang, origin=c)
            for p in getattr(f, "geoms", [f]):
                if p.area > 150 and p.distance(rand) < 0.6:
                    extra.append(haus(p, 5, "finger", "wohnen"))
        if name == "5.2":
            wh = platziere(innen.buffer(-6, join_style=2).difference(unary_union([h["geo"] for h in extra]).buffer(10)) if extra else innen,
                           34, 18, hauptachse(P), Point(c.x, P.bounds[1]))
            if wh is not None:
                extra.append(haus(wh, 2, "wasserhaus", "kultur"))
    out = []
    for h in hs + extra:
        for p in getattr(h["geo"], "geoms", [h["geo"]]):
            if p.geom_type == "Polygon" and p.area > 50:
                out.append(dict(h, geo=p, feld=name, quartier=q))
    return out, dict(hof=hof, auswahl=auswahl, tore=[mapping(t) for t in tore])


NICHT_WOHNEN = {"markthalle", "werkhalle", "sporthalle", "schule", "kita", "gartenhalle", "foodlab", "glashaus", "wasserhaus", "hochpunkt_eg"}


def kennwerte(hs):
    bf = sum(P.area for _, _, P in FELDER)
    gr = unary_union([h["geo"] for h in hs]).area
    bgf = sum(h["geo"].area * h["g"] for h in hs)
    nw = sum(h["geo"].area * (h["g"] if h["typ"] in NICHT_WOHNEN else (1 if h["eg"] != "wohnen" else 0)) for h in hs)
    we = (bgf - nw) / 88
    gebiet = 22.7e4
    jq = {}
    for q in G0:
        hq = [h for h in hs if h["quartier"] == q]
        fq = sum(P.area for _, qq, P in FELDER if qq == q)
        jq[q] = dict(name=NAME[q], grz=round(unary_union([h["geo"] for h in hq]).area / fq, 2) if hq else 0,
                     gfz=round(sum(h["geo"].area * h["g"] for h in hq) / fq, 2), g_max=max((h["g"] for h in hq), default=0),
                     we=round(sum(h["geo"].area * h["g"] for h in hq if h["typ"] not in NICHT_WOHNEN) / 88 * 0.93))
    return dict(baufelder_ha=round(bf / 1e4, 2), grz=round(gr / bf, 2), gfz=round(bgf / bf, 2), gfz_brutto=round(bgf / gebiet, 2),
                bgf=round(bgf), we=round(we), ew=round(we * 1.9), nicht_wohnen=round(100 * nw / bgf), quartiere=jq)


if __name__ == "__main__":
    hs, info = [], {}
    for name, q, P in FELDER:
        h, inf = feld(name, q, P)
        hs += h
        info[name] = inf
    ausnahme = lambda a, b: (a["feld"] == b["feld"] and ({a["typ"], b["typ"]} & {"werkhalle", "markthalle", "glashaus"})
                            and min(a["g"], b["g"]) <= 2) or \
                            (a.get("gruppe") and a.get("gruppe") == b.get("gruppe")) or \
                            (a["feld"] == b["feld"] and {a["typ"], b["typ"]} == {"rand", "finger"})          # Kamm = ein Haus
    hs, eingriffe = durchsetzen(hs, ausnahme=ausnahme, angebaut=1.6)
    k = kennwerte(hs)
    print({x: k[x] for x in ("grz", "gfz", "gfz_brutto", "we", "ew", "nicht_wohnen")}, "Eingriffe", eingriffe)
    for q, v in k["quartiere"].items():
        print("  ", q, v)
    json.dump(dict(haeuser=[dict(geo=mapping(h["geo"]), g=h["g"], typ=h["typ"], eg=h["eg"], feld=h["feld"], quartier=h["quartier"],
                                 tor=h.get("tor", False)) for h in hs], kennwerte=k, info=info),
              open(os.path.join(HIER, "bebauung2.json"), "w"))
