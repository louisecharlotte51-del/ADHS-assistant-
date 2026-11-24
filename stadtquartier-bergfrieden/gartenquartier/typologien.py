"""
Schwarzplan-Varianten S1-S6: Typologie-Mischungen auf den 13 Baufeldern
=======================================================================
Unabhängig von V1-V8. Jede Variante mischt mindestens drei Typologien, keine
besteht nur aus Einzelgebäuden. Die Typologie folgt Nutzung und Phase:
  P1 an der S-Bahn   große Erdgeschosse (Supermarkt, Kita, Büros), dichter
  P2 Gartenmitte     Wohnen, Gesundheitshaus
  P3 Erholungsader   Schule + Sporthalle, Werkstätten, Treffpunkte
  P4 zum Kanal       Werkstätten, Hallen, kleinteiliges Wohnen
Öffentliche Seite eines Feldes: P1 Norden (Station), P4 Süden (Albrechtstraße),
sonst die nächste Ader (Komturstraße oder Erholungsader).
Abstandsflächen BauO Bln (0,4 H, mind. 3 m) werden durchgesetzt.
Aufruf: python3 typologien.py -> typologien.json, typologien_geo.json
"""
import json, math
from shapely.geometry import Point, box, mapping, Polygon, LineString
from shapely.ops import unary_union, nearest_points
from shapely import affinity
import entwurf as E
from varianten import hauptachse, durchsetzen, hoehe, WASSERNETZ, WE_BGF, EW_WE


# ---------------- Hilfen ----------------
def ziel(feld):
    c = feld.centroid
    ph = E.phase(feld)
    if ph == "P1":
        return Point(c.x, 5813980)                    # S-Bahn im Norden
    if ph == "P4":
        return Point(c.x, 5813250)                    # Albrechtstraße / Kanal im Süden
    return nearest_points(c, unary_union([E.KOMTUR_ACHSE, E.ERHOLUNG]))[1]


def rahmen(feld, zielpunkt, lang=False):
    """Lokales Koordinatensystem: Achsen parallel zum Feld, lokales +y zeigt zum Ziel.
    lang=True: bei gestreckten Feldern liegt die lokale x-Achse immer auf der Längsseite."""
    c = feld.centroid
    a_ziel = math.degrees(math.atan2(zielpunkt.y - c.y, zielpunkt.x - c.x))
    basis = hauptachse(feld)
    q = list(feld.minimum_rotated_rectangle.exterior.coords)
    seiten = sorted([math.dist(q[0], q[1]), math.dist(q[1], q[2])])
    ks = (0, 2) if lang and seiten[1] / seiten[0] > 1.5 else range(4)
    k = min(ks, key=lambda k: abs(((basis + 90 * k) - (a_ziel - 90) + 180) % 360 - 180))
    ang = basis + 90 * k
    return (lambda g: affinity.rotate(g, -ang, origin=c)), (lambda g: affinity.rotate(g, ang, origin=c))


def nord(feld):
    return rahmen(feld, Point(feld.centroid.x, feld.centroid.y + 1000))


def stuecke(g, min_flaeche=140, min_breite=7):
    out = []
    for p in getattr(g, "geoms", [g]):
        if p.geom_type == "Polygon" and p.area >= min_flaeche and not p.buffer(-min_breite / 2).is_empty:
            out.append(p.simplify(0.3))
    return out


def oben_band(r, tiefe):
    """Streifen entlang der oberen Kante (lokal +y), folgt der Feldform."""
    return r.difference(affinity.translate(r, 0, -tiefe)).buffer(-3.5, join_style=2).buffer(3.5, join_style=2)


def H(geo, g, typ):
    return dict(geo=geo, g=g, typ=typ)


# ---------------- Typologien ----------------
def kamm(feld, frei, g_r=6, g_f=5, tiefe=13.0, f_b=12.5, takt=34.0, f_len=40.0, je=2, fuge=10.0):
    """Rücken zur öffentlichen Seite (aktives EG), Finger in die Gärten. Nie geschlossen."""
    rot, zur = rahmen(feld, ziel(feld), lang=True)
    r = rot(frei)
    x0, y0, x1, y1 = r.bounds
    ruecken = oben_band(r, tiefe)
    if ruecken.is_empty:
        return []
    lang = oben_band(r, tiefe + min(f_len, (y1 - y0) - tiefe - 8))
    out = []
    n = max(1, int((x1 - x0 - f_b) // takt) + 1)
    rest = (x1 - x0) - ((n - 1) * takt + f_b)
    xs = [x0 + rest / 2 + k * takt for k in range(n)]
    finger = [box(x, y0, x + f_b, y1).intersection(lang) for x in xs]
    # Fugen zwischen Gruppen von je `je` Fingern
    fugen = unary_union([box(xs[k] + f_b + (takt - f_b) / 2 - fuge / 2, y0 - 5, xs[k] + f_b + (takt - f_b) / 2 + fuge / 2, y1 + 5)
                         for k in range(je - 1, n - 1, je)]) if n > je else Polygon()
    for st in stuecke(ruecken.difference(fugen), 120):
        out.append(H(zur(st), g_r, "kamm_ruecken"))
    for f in finger:
        for st in stuecke(f.difference(ruecken).difference(fugen), 120):
            out.append(H(zur(st), g_f, "kamm_finger"))
    return out


def zeilen(feld, frei, g=5, tiefe=12.5, seg=46.0, fuge=8.0, nord_sued=True, abstand=None):
    """Zeilen, Längsachse Nord-Süd (Ost-West-Licht) oder parallel zur öffentlichen Seite."""
    if nord_sued:
        rot, zur = rahmen(feld, Point(feld.centroid.x + 1000, feld.centroid.y))   # lokal x = Nord
    else:
        rot, zur = rahmen(feld, ziel(feld))
    r = rot(frei)
    x0, y0, x1, y1 = r.bounds
    abstand = abstand or max(16.0, 0.85 * hoehe(g) + 4)
    out, y = [], y0 + 1
    while y + tiefe <= y1 + 0.5:
        x = x0
        while x < x1:
            for st in stuecke(box(x, y, x + seg, y + tiefe).intersection(r), 160, 8):
                out.append(H(zur(st), g, "zeile"))
            x += seg + fuge
        y += tiefe + abstand
    return out


def winkel(feld, frei, g=5, a=34.0, b=27.0, t=12.5, dx=45.0, dy=40.0, typ="winkel"):
    """Winkel, geschlossen nach Nord und Ost, offen nach Südwest (Sonne). Reihen versetzt."""
    rot, zur = nord(feld)
    r = rot(frei)
    x0, y0, x1, y1 = r.bounds
    out, k, y = [], 0, y0
    while y < y1:
        x = x0 - (dx / 2 if k % 2 else 0)
        while x < x1:
            L = box(x, y + b - t, x + a, y + b).union(box(x + a - t, y, x + a, y + b))
            teil = L.intersection(r)
            if teil.area > 0.8 * L.area:
                out.append(H(zur(teil), g, typ))
            else:
                for st in stuecke(teil, 220, 9):
                    out.append(H(zur(st), g, typ))
            x += dx
        y += dy
        k += 1
    return out


def punkte(feld, frei, g=6, s=19.0, abstand=14.0, raster=7.0, max_n=99):
    rot, zur = nord(feld)
    r = rot(frei)
    x0, y0, x1, y1 = r.bounds
    out, gesetzt = [], []
    y = y0
    while y < y1 and len(out) < max_n:
        x = x0
        while x < x1 and len(out) < max_n:
            q = box(x, y, x + s, y + s)
            if q.within(r) and all(q.distance(p) >= abstand for p in gesetzt):
                gesetzt.append(q)
                out.append(H(zur(q), g, "punkt"))
            x += raster
        y += raster
    return out


def reihen(feld, frei, b=6.5, t=11.0, garten=12.0, n=5, luecke=5.0):
    """Reihenhäuser / Stadthäuser, 3 G, Gärten nach Süden, Gruppen zu n Häusern.
    Probiert Nord- und Feldausrichtung und verschiedene Versätze, nimmt die dichteste Packung."""
    beste = []
    for rot, zur in (nord(feld), rahmen(feld, ziel(feld), lang=True)):
        r = rot(frei).buffer(0.3)
        x0, y0, x1, y1 = r.bounds
        for dy in range(0, int(t + garten), 4):
            for dx in (0.0, 3.0, 6.0, 9.0):
                out, y = [], y1 - t - dy
                while y >= y0 - 0.5:
                    x = x0 + dx
                    while x + b * 2 <= x1:
                        for j in range(n):
                            hs = box(x + j * b, y, x + (j + 1) * b, y + t)
                            if hs.within(r):
                                out.append(H(zur(hs), 3, "reihe"))
                        x += n * b + luecke
                    y -= t + garten
                if len(out) > len(beste):
                    beste = out
    return beste


def kante(feld, frei, g=6, tiefe=13.0, seite=True, typ="kante", seg=52.0, fuge=8.0):
    """Riegel an der öffentlichen Seite, bei großen Feldern als Winkel um eine Ecke. Nie ringsum."""
    rot, zur = rahmen(feld, ziel(feld), lang=True)
    r = rot(frei)
    x0, y0, x1, y1 = r.bounds
    band = oben_band(r, tiefe).intersection(box(x0, y1 - tiefe - 18, x1, y1))
    if seite and (y1 - y0) > 70:
        # zweite Seite: zur Komturstraße hin, falls nah, sonst Westseite; nur obere Hälfte
        rechts = r.difference(affinity.translate(r, -tiefe, 0)).intersection(box(x0, (y0 + y1) / 2, x1, y1))
        band = band.union(rechts.buffer(-1.5, join_style=2).buffer(1.5, join_style=2))
    fugen = unary_union([box(x, y0 - 5, x + fuge, y1 + 5) for x in [x0 + seg + k * (seg + fuge) for k in range(8)] if x < x1 - 20])
    return [H(zur(st), g, typ) for st in stuecke(band.difference(fugen), 160, 8)]


def hybrid(feld, frei, g_sockel=2, g_turm=13, g_riegel=7):
    """Sockel (Supermarkt, Kita, Büros) + Riegel + Hochpunkt an der Ecke zur Station."""
    rot, zur = rahmen(feld, ziel(feld))
    r = rot(frei)
    x0, y0, x1, y1 = r.bounds
    sock = oben_band(r, 44).intersection(box(x1 - 78, y0, x1, y1))
    sock = max(stuecke(sock, 400, 20), key=lambda p: p.area, default=None)
    if sock is None:
        return []
    sx0, sy0, sx1, sy1 = sock.bounds
    riegel = oben_band(sock, 13)
    turm = box(sx1 - 24, sy1 - 24, sx1, sy1).intersection(sock)
    return [H(zur(sock), g_sockel, "sockel"), H(zur(riegel.difference(turm)), g_riegel, "riegel"), H(zur(turm), g_turm, "hochpunkt")]


def halle(feld, frei, w=30.0, l=44.0, g_halle=2, g_riegel=5, mit_riegel=True, ecke="oben"):
    """Werkhalle mit Wohnriegel daneben: Werkstätten, Markt, Sport. Steht an der öffentlichen Seite."""
    rot, zur = rahmen(feld, ziel(feld))
    r = rot(frei)
    x0, y0, x1, y1 = r.bounds
    for x in [x0 + 2 + k * 6 for k in range(int((x1 - x0) / 6))]:
        hb = box(x, y1 - w - 30, x + l, y1)
        hb = oben_band(r, w + 4).intersection(box(x, y0, x + l, y1))
        if hb.area > 0.85 * w * l:
            p = hb.buffer(-0.01)
            out = [H(zur(p), g_halle, "halle")]
            if mit_riegel:
                rg = box(x + l + 0.5, y0, x + l + 13.5, y1).intersection(oben_band(r, w + 10))
                out += [H(zur(st), g_riegel, "riegel") for st in stuecke(rg, 200, 9)]
            return out
    return []


def fingerschule(feld, frei, typ_g=3):
    """Grundschule als Kamm: Rücken zur Erholungsader, drei Klassenfinger, Sporthalle extra."""
    rot, zur = rahmen(feld, ziel(feld), lang=True)
    r = rot(frei)
    x0, y0, x1, y1 = r.bounds
    ruecken = oben_band(r, 16).intersection(box(x0, y0, x0 + 92, y1))
    out = [H(zur(st), typ_g, "schule") for st in stuecke(ruecken, 300, 10)]
    lang = oben_band(r, 16 + 28)
    for k in range(3):
        f = box(x0 + 4 + k * 32, y0, x0 + 18 + k * 32, y1).intersection(lang).difference(ruecken)
        out += [H(zur(st), typ_g, "schule") for st in stuecke(f, 150, 9)]
    rest = r.difference(box(x0, y0, x0 + 100, y1)).difference(ruecken.buffer(12))
    sh = box(x1 - 50, y0 + 2, x1 - 4, y0 + 30)
    if sh.within(r):
        out.append(H(zur(sh), 2, "sporthalle"))
    else:
        for st in stuecke(rest, 900, 22)[:1]:
            sx0, sy0, sx1, sy1 = st.bounds
            out.append(H(zur(box(sx0, sy0, min(sx1, sx0 + 46), min(sy1, sy0 + 28)).intersection(st)), 2, "sporthalle"))
    return out


def uferzeilen(feld, frei, g=6, t=12.5, d0=12.0, zweite=True, seg=44.0, fuge=8.0):
    """Zeilen, die der Wasserader folgen (parallel zum Wasser), mit Fugen."""
    baender = [WASSERNETZ.buffer(d0 + t).difference(WASSERNETZ.buffer(d0))]
    if zweite:
        d1 = d0 + t + max(18.0, 0.8 * hoehe(g))
        baender.append(WASSERNETZ.buffer(d1 + t).difference(WASSERNETZ.buffer(d1)))
    rot, zur = rahmen(feld, ziel(feld))
    c = feld.centroid
    out = []
    for bd in baender:
        lokal = rot(bd.intersection(frei))
        x0, y0, x1, y1 = rot(frei).bounds
        luecken = unary_union([box(x, y0 - 5, x + fuge, y1 + 5) for x in [x0 + seg + k * (seg + fuge) for k in range(10)]])
        luecken2 = unary_union([box(x0 - 5, y, x1 + 5, y + fuge) for y in [y0 + seg + k * (seg + fuge) for k in range(10)]])
        for st in stuecke(lokal.difference(luecken).difference(luecken2), 180, 9):
            out.append(H(zur(st), g, "uferzeile"))
    return out


def kopfbauten(feld, frei, g=8, s=21.0):
    """Kopfbauten an den Trichterspitzen: Adressen, Läden, Café im EG."""
    out = []
    for a, b in E.TRICHTER_DEF:
        spitze = Point(b)
        if feld.distance(spitze) > 30:
            continue
        p = nearest_points(frei, spitze)[0]
        q = affinity.rotate(box(p.x - s / 2, p.y - s / 2, p.x + s / 2, p.y + s / 2), hauptachse(feld), origin=p)
        q = affinity.translate(q, (feld.centroid.x - p.x) * 0.12, (feld.centroid.y - p.y) * 0.12)
        q = q.intersection(frei)
        if q.area > 0.75 * s * s:
            out.append(H(q, g, "kopfbau"))
    return out


# ---------------- Varianten ----------------
def frei_von(feld, liste, abstand=12.0):
    innen = feld.buffer(-3, join_style=2)
    if not liste:
        return innen
    return innen.difference(unary_union([h["geo"] for h in liste]).buffer(abstand, join_style=2))


def mach(feld, *schritte):
    out = []
    for fn, kw in schritte:
        out += fn(feld, frei_von(feld, out, kw.pop("_abstand", 12.0)), **kw)
    return out


G = {"P1": 7, "P2": 6, "P3": 5, "P4": 5}


def s1_kammstadt(i, f):
    g = G[E.phase(f)]
    if i == 6:
        return mach(f, (fingerschule, {}), (zeilen, dict(g=4, _abstand=14)))
    if i == 13:
        return mach(f, (halle, dict(g_riegel=4)), (kamm, dict(g_r=4, g_f=4, _abstand=14)))
    return mach(f, (kamm, dict(g_r=g, g_f=g - 1)))


def s2_kante_reihe(i, f):
    g = G[E.phase(f)]
    if i == 6:
        return mach(f, (kante, dict(g=3, typ="schule", tiefe=15)), (halle, dict(mit_riegel=False, w=28, l=46, _abstand=14)),
                    (reihen, dict(_abstand=10)))
    if i in (11, 13):
        return mach(f, (kante, dict(g=g, tiefe=13)), (halle, dict(g_riegel=4, _abstand=12)), (reihen, dict(_abstand=10)))
    return mach(f, (kante, dict(g=g, tiefe=16 if i <= 2 else 13, seite=(i in (1, 4, 6)))), (reihen, dict(_abstand=12)))


def s3_winkel_punkt(i, f):
    g = G[E.phase(f)]
    if i == 6:
        return mach(f, (winkel, dict(g=3, a=62, b=46, t=14, dx=76, dy=64, typ="schule")),
                    (halle, dict(w=28, l=46, mit_riegel=False, _abstand=12)), (punkte, dict(g=4, max_n=2, _abstand=14)))
    if i == 11:
        return mach(f, (halle, dict(g_riegel=4)), (winkel, dict(g=g - 1, _abstand=14)), (punkte, dict(g=5, _abstand=14)))
    return mach(f, (winkel, dict(g=g)), (punkte, dict(g=g + 1, _abstand=13, max_n=5)))


def s4_gross_klein(i, f):
    ph = E.phase(f)
    if ph == "P1":
        return mach(f, (hybrid, dict(g_turm=13 if i == 1 else 10)), (zeilen, dict(g=6, _abstand=16)))
    if ph == "P2":
        return mach(f, (zeilen, dict(g=6)))
    if i == 6:
        return mach(f, (fingerschule, {}), (winkel, dict(g=4, _abstand=14)))
    if ph == "P3":
        return mach(f, (winkel, dict(g=4)), (reihen, dict(_abstand=10)))
    return mach(f, (halle, dict(g_riegel=4, mit_riegel=False)), (reihen, dict(_abstand=10)))


def s5_zeile_halle(i, f):
    ph = E.phase(f)
    g = {"P1": 6, "P2": 5, "P3": 5, "P4": 4}[ph]
    if i == 1:
        return mach(f, (halle, dict(w=36, l=44, g_halle=2, g_riegel=6)), (zeilen, dict(g=g, _abstand=16)))
    if i == 6:
        return mach(f, (halle, dict(w=28, l=46, mit_riegel=False)), (zeilen, dict(g=3, _abstand=14)))
    if ph in ("P3", "P4") or i == 3:
        return mach(f, (halle, dict(w=24, l=30, g_riegel=g)), (zeilen, dict(g=g, _abstand=15)))
    return mach(f, (zeilen, dict(g=g)), (halle, dict(w=20, l=26, mit_riegel=False, _abstand=12)))


def s6_uferlinien(i, f):
    ph = E.phase(f)
    g = G[ph]
    if i == 7:
        return mach(f, (fingerschule, {}), (uferzeilen, dict(g=4, zweite=False, _abstand=14)))
    kb = (kopfbauten, dict(g=10 if ph == "P1" else g + 2))
    return mach(f, kb, (uferzeilen, dict(g=g - 1, _abstand=13)), (reihen, dict(_abstand=11)))


VARIANTEN = [
    ("S1", "Kammstadt", s1_kammstadt, ["Kamm", "Fingerschule", "Halle + Riegel", "Zeile"],
     "Jedes Feld bekommt einen Kamm: Der Rücken steht an der öffentlichen Seite und trägt das aktive Erdgeschoss, die Finger reichen in die Gärten.",
     ["Rücken zur S-Bahn: Supermarkt, Bäckerei, Praxis im EG, Büros im 1. OG", "Rücken zur Komturstraße: Gesundheitshaus, Läden. Finger: Wohnen",
      "Schule selbst als Kamm an der Erholungsader, Rücken der Wohnkämme mit Werkstätten", "Halle an der Albrechtstraße für Handwerk, Kämme zum Kanal"]),
    ("S2", "Kante und Reihe", s2_kante_reihe, ["Kante (Riegel)", "Reihenhaus", "Halle", "Schule als Kante"],
     "Ein Riegel fasst die öffentliche Seite, dahinter liegen Reihen- und Stadthäuser mit Gärten. Die Kante schützt, die Reihen geben Körnung.",
     ["16 m tiefe Kante an der Station: Platz für Supermarkt und Kita im EG", "Kante an Komturstraße mit Läden, Reihenhäuser für Familien",
      "Schule als Kante an der Erholungsader, Sporthalle als Halle", "Hallen + Kanten mit Werkstätten, Reihenhäuser von Baugruppen"]),
    ("S3", "Winkel und Punkt", s3_winkel_punkt, ["Winkel", "Punkthaus (nur im Mix)", "Halle", "Schule als Winkel"],
     "Versetzte Winkel öffnen sich nach Südwest zur Sonne. Punkthäuser füllen die Lücken und markieren Ecken. Kein Winkel schließt sich mit dem nächsten.",
     ["Winkel mit Ecke zur Station: Ladenecke, Kita im ruhigen Schenkel", "Winkel um Gartenräume, Punkte an der Komturstraße",
      "Große Winkel als Schule, die Schenkel fassen den Schulhof nach Süden offen", "Halle für Werkstätten, kleinere Winkel zum Kanal"]),
    ("S4", "Groß zu Klein", s4_gross_klein, ["Sockel + Hochpunkt", "Zeile", "Winkel", "Reihenhaus", "Halle"],
     "Die Körnung nimmt von der S-Bahn zum Kanal ab: Großform mit Hochpunkt an der Station, Zeilen in der Mitte, Winkel und Reihen im Süden.",
     ["Sockel mit Supermarkt, Kita, Büros; Hochpunkt (13 G) markiert den Bahnhofsplatz", "Nord-Süd-Zeilen, 6 G: viel Wohnen, Ost-West-Licht",
      "Fingerschule + Winkel und Reihen, 3-4 G", "Hallen für Werkstätten an der Albrechtstraße, Reihenhäuser zum Kanal"]),
    ("S5", "Zeilen und Hallen", s5_zeile_halle, ["Zeile", "Halle", "Halle + Riegel"],
     "Produktive Stadt: Nord-Süd-Zeilen zum Wohnen, dazwischen Hallen an der öffentlichen Seite für Markt, Werkstatt, Sport und Kita.",
     ["Große Halle an der Station: Supermarkt, darüber Riegel mit Büros und Wohnungen", "Zeilen, kleine Hallen als Kita und Gemeinschaftsräume",
      "Sporthalle und Schulzeilen (3 G), Werkhallen an der Erholungsader", "Werkhallen mit Wohnriegeln: Handwerk am Kanal"]),
    ("S6", "Uferlinien", s6_uferlinien, ["Uferzeile", "Kopfbau", "Reihenhaus", "Fingerschule"],
     "Zeilen folgen der Wasserader in zwei Reihen. Kopfbauten stehen an den Trichterspitzen und bilden Adressen. Innen liegen Reihenhäuser.",
     ["Kopfbau mit 10 G am Eingang Nord: Café, Praxis; Uferzeilen mit Kita zum Wasser", "Uferzeilen zum Wasser, Kopfbauten an der Komturstraße mit Läden",
      "Schule an der Erholungsader, Uferzeile mit Werkstätten", "Kopfbauten zur Albrechtstraße, Reihenhäuser zum Kanal"]),
]


def generiere():
    alle = {}
    for code, name, fn, typen, text, phasen in VARIANTEN:
        hs = []
        for i, f in enumerate(E.BAUFELDER, 1):
            for h in fn(i, f):
                g = h["geo"]
                if g.is_empty or g.area < 60:
                    continue
                h.update(feld=i, phase=E.phase(f))
                hs.append(h)
        hs, eingriffe = durchsetzen(hs)
        alle[code] = dict(haeuser=hs, eingriffe=eingriffe)
    return alle


NICHT_WOHNEN = {"halle": 1.0, "sockel": 1.0, "schule": 1.0, "sporthalle": 1.0}
AKTIV_EG = {"kamm_ruecken", "kante", "riegel", "kopfbau", "hochpunkt"}


def kennzahlen(hs):
    bf = sum(f.area for f in E.BAUFELDER)
    gr = sum(h["geo"].area for h in hs)
    bgf = sum(h["geo"].area * h["g"] for h in hs)
    from varianten import AKTIV
    nw = sum(h["geo"].area * (h["g"] if h["typ"] in NICHT_WOHNEN else
                              1 if (h["typ"] in AKTIV_EG or (h["typ"] != "reihe" and h["geo"].intersects(AKTIV))) else 0) for h in hs)
    we = (bgf - nw) / WE_BGF
    typen = {}
    for h in hs:
        typen[h["typ"]] = typen.get(h["typ"], 0) + round(h["geo"].area)
    return dict(grz=round(gr / bf, 2), gfz=round(bgf / bf, 2), gfz_brutto=round(bgf / E.GEBIET.area, 2), bgf=round(bgf),
                nicht_wohnen=round(100 * nw / bgf), we=round(we), ew=round(we * EW_WE), gebaeude=len(hs),
                g_max=max(h["g"] for h in hs), typen_grundflaeche=typen)


if __name__ == "__main__":
    alle = generiere()
    out, geo = [], {}
    for code, name, fn, typen, text, phasen in VARIANTEN:
        hs = alle[code]["haeuser"]
        k = kennzahlen(hs)
        out.append(dict(code=code, name=name, typen=typen, text=text, phasen=phasen, kennzahlen=k, eingriffe=alle[code]["eingriffe"]))
        geo[code] = [dict(geo=mapping(h["geo"]), g=h["g"], typ=h["typ"], feld=h["feld"], phase=h["phase"]) for h in hs]
        print(f'{code} {name:18s} GRZ {k["grz"]:.2f} GFZ {k["gfz"]:.2f} (brutto {k["gfz_brutto"]:.2f}) WE {k["we"]:5d} '
              f'nicht-Wohnen {k["nicht_wohnen"]:2d}%  Häuser {k["gebaeude"]:3d}  maxG {k["g_max"]}  Eingriffe {alle[code]["eingriffe"]}')
        print("    ", k["typen_grundflaeche"])
    json.dump(out, open("typologien.json", "w"), ensure_ascii=False, indent=1)
    json.dump(geo, open("typologien_geo.json", "w"))
