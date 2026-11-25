"""
Freiraum-Layout für 3D-Modell und Situationsskizzen (nach dem Referenz-Board):
  Bewegungsader   Komturstraße: Zweirichtungs-Radweg in der Mitte, Pflanzstreifen, Tempo 30, breite Gehwege,
                  Straßenbegleitgrün mit Baumreihen, Café-Pavillon
  Erholungsader   Flanierachse Ost-West: geschwungene Wege durch Staudenbeete, Rasenlichtungen, Pergolen, Spielplatz
  Wasserader      offener Bach mit Schilfufer, Schwammknoten als Teiche mit Trittsteinen und Holzdeck
  Quartiersplatz  am Kanal: Pflanzinseln, Café-Tische, Sitzstufen zum Wasser, Retentionsbecken, Kioske
  Gartenfuge      Nachbarschaftsgarten zwischen zwei Zeilen (S4, Baufeld 3): Hochbeete, Spiel, Bänke, Blütenbäume
Schreibt 3d/szene3.json: Varianten S1-S6 (Grundriss je Haus), Landschaft (Flächen, Punkte), Kameras.
Koordinaten lokal: Meter ab E.ORIGIN, z nach oben.
"""
import json, math, random
import numpy as np
from shapely.geometry import Point, LineString, Polygon, box, shape, MultiPolygon
from shapely.ops import unary_union, linemerge, substring
from shapely import affinity
import entwurf as E
from varianten import AKTIV
import nutzungen as N

OX, OY = E.ORIGIN
rnd = random.Random(42)
FL, PK = [], []          # Flächen (Polygon, Art), Punkte (Art, x, y, rot, extra)


def lok(x, y):
    return round(x - OX, 2), round(y - OY, 2)


def flaeche(g, art, z=0.0):
    for p in getattr(g, "geoms", [g]):
        if p.geom_type == "Polygon" and p.area > 0.3:
            FL.append(dict(art=art, z=z, poly=p))
        elif hasattr(p, "geoms"):
            flaeche(p, art, z)


def dreiecke(polys):
    """Polygone mit Löchern triangulieren (earcut) -> {v: [x,y,...], f: [i,j,k,...]}."""
    import mapbox_earcut as earcut
    V, F = [], []
    for p in polys:
        p = p.simplify(0.05)
        if p.is_empty or p.geom_type != "Polygon":
            continue
        ringe = [np.array(p.exterior.coords[:-1])] + [np.array(r.coords[:-1]) for r in p.interiors]
        ringe = [r for r in ringe if len(r) >= 3]
        if not ringe:
            continue
        pts = np.vstack(ringe)
        ends = np.cumsum([len(r) for r in ringe]).astype(np.uint32)
        tri = earcut.triangulate_float64(pts.astype(float), ends)
        b0 = len(V) // 2
        for x, y in pts:
            V += [round(x - OX, 2), round(y - OY, 2)]
        F += [int(b0 + t) for t in tri]
    return dict(v=V, f=F)


def punkt(art, x, y, rot=None, **kw):
    PK.append(dict(art=art, p=lok(x, y), rot=round(rnd.uniform(0, 360) if rot is None else rot, 1), **kw))


def streu(poly, dichte, mindest):
    """Poisson-ähnliche Punkte in einem Polygon: dichte = Punkte je m²."""
    out = []
    if poly.is_empty:
        return out
    x0, y0, x1, y1 = poly.bounds
    soll = int(poly.area * dichte)
    for _ in range(soll * 12):
        if len(out) >= soll:
            break
        q = Point(rnd.uniform(x0, x1), rnd.uniform(y0, y1))
        if q.within(poly) and all(q.distance(o) >= mindest for o in out[-60:]):
            out.append(q)
    return out


def klecks(c, r, n=14, rauh=0.25):
    pts = []
    phase = rnd.uniform(0, 6.28)
    for k in range(n):
        a = 2 * math.pi * k / n
        rr = r * (1 + rauh * math.sin(3 * a + phase) + rnd.uniform(-rauh, rauh) * 0.5)
        pts.append((c[0] + rr * math.cos(a), c[1] + rr * math.sin(a)))
    return Polygon(pts).buffer(r * 0.15).buffer(-r * 0.12)


def mäander(linie, amp, wellen, breite, versatz=0.0):
    pts = []
    L = linie.length
    for d in np.linspace(0, L, max(20, int(L / 3))):
        p = linie.interpolate(d)
        q = linie.interpolate(min(L, d + 1))
        tx, ty = q.x - p.x, q.y - p.y
        n = math.hypot(tx, ty) or 1
        nx, ny = -ty / n, tx / n
        o = versatz + amp * math.sin(2 * math.pi * wellen * d / L)
        pts.append((p.x + nx * o, p.y + ny * o))
    return LineString(pts).buffer(breite / 2, cap_style=1)


def bett(poly, mischung="stauden"):
    """Staudenbeet: Fläche + Blütenpunkte (werden in Blender als Tuffs gebaut)."""
    flaeche(poly, "beet", 0.12)
    for q in streu(poly, 1.6 if mischung == "stauden" else 1.0, 0.55):
        punkt("tuff", q.x, q.y, farbe=rnd.choice(["lila", "pink", "weiss", "lila", "gras", "gras", "gras", "gras", "pink",
                                                  "gelb", "rot", "weiss", "lila", "orange"]
                                                    if mischung == "stauden" else ["gras", "gras", "schilf", "lila", "weiss"]))


def baum(x, y, art="laub", h=None):
    punkt("baum", x, y, h=round(h or rnd.uniform(9, 15), 1), baumart=art)


def menschen(poly, n, arten=("geh", "geh", "geh", "steh", "kind")):
    for q in streu(poly, n / max(poly.area, 1), 1.2)[:n]:
        punkt("mensch", q.x, q.y, haltung=rnd.choice(arten), farbe=rnd.randrange(8))


KAMERAS = {}


def kamera(name, pos, ziel, linse=28, titel=""):
    KAMERAS[name] = dict(pos=[*lok(*pos[:2]), pos[2]], ziel=[*lok(*ziel[:2]), ziel[2]], linse=linse, titel=titel)


# ======================= 1 Bewegungsader (Komturstraße) =======================
achse = linemerge(E.KOMTUR_ACHSE)
achse = max(getattr(achse, "geoms", [achse]), key=lambda g: g.length)
abschnitt = achse.intersection(box(391200, 5813300, 391450, 5813850))
abschnitt = max(getattr(abschnitt, "geoms", [abschnitt]), key=lambda g: g.length)
B = lambda d: abschnitt.buffer(d, cap_style=2)
rad = B(1.75)
pflanz = B(4.25).difference(rad)
fahr = B(7.5).difference(B(4.25))
rasen_gitter = B(9).difference(B(7.5))
geh = B(14).difference(B(9))
gruen_band = E.HAUPT_NS.intersection(box(391200, 5813300, 391450, 5813850)).difference(B(14))
# Querungen alle ~70 m: Pflanzstreifen unterbrochen, Zebrastreifen
querungen = []
for d in np.arange(40, abschnitt.length, 70):
    p = abschnitt.interpolate(d)
    q = abschnitt.interpolate(min(abschnitt.length, d + 1))
    ang = math.degrees(math.atan2(q.y - p.y, q.x - p.x))
    quer = affinity.rotate(box(p.x - 2.5, p.y - 9, p.x + 2.5, p.y + 9), ang, origin=p)
    querungen.append(quer)
    for k in range(-8, 9, 2):
        s = affinity.rotate(box(p.x - 2.2, p.y + k - 0.4, p.x + 2.2, p.y + k + 0.4), ang, origin=p)
        flaeche(s.intersection(B(7.5)).difference(rad), "zebra", 0.06)
Q = unary_union(querungen)
flaeche(rad, "radweg", 0.05)
for k in np.arange(0, abschnitt.length, 6):
    s = substring(abschnitt, k, min(abschnitt.length, k + 3))
    flaeche(s.buffer(0.08, cap_style=2), "markierung", 0.07)
bett(pflanz.difference(Q.buffer(0.5)))
flaeche(fahr, "asphalt", 0.03)
flaeche(rasen_gitter, "rasengitter", 0.04)
flaeche(geh.union(Q.intersection(B(9))), "pflaster", 0.06)
# Straßenbegleitgrün: Wiese + Staudeninseln + Baumreihen + Café-Pavillon
flaeche(gruen_band, "wiese", 0.05)
for poly in getattr(gruen_band, "geoms", [gruen_band]):
    for q in streu(poly.buffer(-3), 0.004, 14):
        bett(klecks((q.x, q.y), rnd.uniform(3, 5)).intersection(poly.buffer(-1)))
for seite in (-1, 1):
    zeile = abschnitt.offset_curve(seite * 12.0)
    for d in np.arange(6, zeile.length, 11):
        p = zeile.interpolate(d)
        if p.within(E.HAUPT_NS.buffer(1)) and not p.within(Q.buffer(4)):
            baum(p.x, p.y, "laub", rnd.uniform(11, 15))
# Bänke und Fahrradbügel am Gehweg
for seite in (-1, 1):
    zeile = abschnitt.offset_curve(seite * 9.6)
    for d in np.arange(14, zeile.length, 23):
        p = zeile.interpolate(d)
        q = zeile.interpolate(min(zeile.length, d + 1))
        punkt("bank", p.x, p.y, math.degrees(math.atan2(q.y - p.y, q.x - p.x)))
# Café-Pavillon mit Tischen im Grünband West auf Höhe Trichter
cafe = Point(391296, 5813612)
punkt("pavillon", cafe.x, cafe.y, 4)
for k in range(9):
    a = rnd.uniform(0, 6.28)
    rr = rnd.uniform(6, 11)
    x, y = cafe.x + rr * math.cos(a), cafe.y + rr * math.sin(a)
    punkt("schirm", x, y, farbe=rnd.choice(["weiss", "weiss", "creme"]))
    for j in range(2):
        punkt("mensch", x + rnd.uniform(-1, 1), y + rnd.uniform(-1, 1), haltung="sitz", farbe=rnd.randrange(8))
menschen(geh.intersection(box(391250, 5813540, 391400, 5813760)), 55)
for d in np.arange(20, 200, 17):
    p = abschnitt.interpolate(abschnitt.project(Point(391320, 5813560)) + d)
    q = abschnitt.interpolate(abschnitt.project(p) + 1)
    w = math.degrees(math.atan2(q.y - p.y, q.x - p.x))
    punkt("rad", p.x + rnd.uniform(-0.8, 0.8), p.y, w + rnd.choice([0, 180]), farbe=rnd.randrange(8))
for d, seite in ((60, 1), (140, -1), (230, 1)):
    p = abschnitt.interpolate(abschnitt.project(Point(391320, 5813560)) + d)
    zeile = abschnitt.offset_curve(seite * 5.9)
    q = zeile.interpolate(zeile.project(p))
    q2 = abschnitt.interpolate(abschnitt.project(p) + 1)
    w = math.degrees(math.atan2(q2.y - p.y, q2.x - p.x)) + (0 if seite > 0 else 180)
    punkt("auto", q.x, q.y, w, farbe=rnd.randrange(5))
p0 = abschnitt.interpolate(abschnitt.project(Point(391320, 5813540)))
p1 = abschnitt.interpolate(abschnitt.project(Point(391320, 5813540)) + 120)
kamera("bewegungsader", (p0.x + 2.0, p0.y, 3.6), (p1.x, p1.y, 5.5), 24, "Bewegungsader Komturstraße")

# ======================= 2 Erholungsader (Flanierachse) =======================
band = E.ERHOLUNG_FL.intersection(box(390995, 5813420, 391560, 5813560)).difference(E.KOMTUR_ROW.buffer(1))
wege = unary_union([mäander(E.ERHOLUNG, 5.5, 7, 3.2, -3), mäander(E.ERHOLUNG, 4.5, 9, 2.4, 6)]).intersection(band)
lichtungen = unary_union([klecks((x, y), rnd.uniform(7, 10)) for x, y in
                          [(391190, 5813490), (391060, 5813508), (391410, 5813480), (391500, 5813515)]]).intersection(band)
flaeche(wege, "kies", 0.08)
flaeche(lichtungen.difference(wege), "rasen", 0.07)
bett(band.difference(wege.buffer(0.6)).difference(lichtungen.buffer(0.8)))
for x, y in [(391205, 5813472), (391458, 5813497)]:
    punkt("pergola", x, y, rnd.uniform(-20, 20))
    for j in range(3):
        punkt("mensch", x + rnd.uniform(-2, 2), y + rnd.uniform(-1, 1), haltung="sitz", farbe=rnd.randrange(8))
spiel = Point(391105, 5813486)
flaeche(klecks((spiel.x, spiel.y), 7).intersection(band), "sand", 0.09)
punkt("kletter", spiel.x, spiel.y, 15)
for k in range(5):
    punkt("mensch", spiel.x + rnd.uniform(-5, 5), spiel.y + rnd.uniform(-4, 4), haltung="kind", farbe=rnd.randrange(8))
for q in streu(lichtungen, 0.03, 3):
    punkt("mensch", q.x, q.y, haltung="lieg" if rnd.random() < 0.5 else "sitz", farbe=rnd.randrange(8))
menschen(wege, 45, ("geh", "geh", "steh", "kind", "geh"))
for poly in getattr(band, "geoms", [band]):
    rand = poly.exterior
    for d in np.arange(5, rand.length, 16):
        p = rand.interpolate(d)
        if not p.within(wege.buffer(2)) and rnd.random() < 0.7:
            baum(p.x, p.y, rnd.choice(["laub", "laub", "bluete"]), rnd.uniform(8, 13))
for d in np.arange(10, 520, 26):
    p = E.ERHOLUNG.interpolate(d + 100)
    if p.within(band) and not p.within(wege):
        punkt("bank", p.x, p.y + 2, rnd.uniform(-10, 10))
kamera("erholungsader", (391305, 5813474, 10), (391155, 5813488, 0), 26, "Erholungsader: Flanieren zwischen Stauden")

# ======================= 3 Wasserader =======================
wasser_l = E.WASSER.intersection(box(390990, 5813180, 391600, 5813900))
bach = wasser_l.buffer(3.2)
ufer = wasser_l.buffer(7).difference(bach)
teiche = unary_union([klecks((p.x, p.y), 8.5, rauh=0.18) for p in
                      [E.WASSER.interpolate(d) for d in np.arange(140, E.WASSER.length - 40, 120)]])
aeste_wasser = unary_union([a.buffer(1.4) for a in E.AESTE]).intersection(E.GEBIET.buffer(5))
wasser_flaeche = unary_union([bach, teiche, aeste_wasser])
flaeche(wasser_flaeche, "wasser", -0.25)
flaeche(wasser_flaeche.buffer(1.2).difference(wasser_flaeche), "ufersteine", 0.02)
bett(ufer.difference(teiche.buffer(1.2)).difference(wasser_flaeche.buffer(1.2)), "ufer")
weg_w = wasser_l.offset_curve(-10.0).buffer(1.4).intersection(E.GEBIET).difference(wasser_flaeche.buffer(2))
flaeche(weg_w, "kies", 0.08)
for p in [E.WASSER.interpolate(d) for d in np.arange(140, E.WASSER.length - 40, 120)]:
    # Trittsteine quer durch jeden Teich, Holzdeck am Rand
    for k in range(-7, 8, 2):
        punkt("trittstein", p.x + k * 0.9, p.y + math.sin(k) * 0.8, rnd.uniform(0, 90))
    d = box(p.x + 6, p.y - 2.5, p.x + 12, p.y + 2.5)
    flaeche(d, "holzdeck", 0.35)
    for j in range(3):
        punkt("mensch", p.x + 7 + rnd.uniform(0, 4), p.y + rnd.uniform(-2, 2), haltung="sitz", farbe=rnd.randrange(8))
    for j in range(3):
        punkt("mensch", p.x + rnd.uniform(-5, 5), p.y + rnd.uniform(-1.5, 1.5), haltung="kind", farbe=rnd.randrange(8))
for d in np.arange(8, wasser_l.length, 14):
    for seite in (-1, 1):
        p = wasser_l.offset_curve(seite * rnd.uniform(5.5, 7.5)).interpolate(d)
        if rnd.random() < 0.55 and p.within(E.GEBIET.buffer(10)):
            baum(p.x, p.y, rnd.choice(["weide", "laub", "laub"]), rnd.uniform(8, 13))
menschen(weg_w.intersection(box(391100, 5813560, 391260, 5813800)), 18)
w0, w1 = E.WASSER.interpolate(E.WASSER.project(Point(391205, 5813590))), E.WASSER.interpolate(E.WASSER.project(Point(391172, 5813690)))
_c, _t = E.WASSER.interpolate(380 + 45), E.WASSER.interpolate(380 - 6.75)
kamera("wasserader", (_c.x, _c.y, 12), (_t.x, _t.y, 0), 24, "Wasserader: Bach, Teiche, Trittsteine")

# ======================= 4 Quartiershauptplatz am Kanal =======================
halle = N.bestand_orte()["markthalle"]
ufer_kanal = E.KANAL.buffer(14).difference(E.KANAL).intersection(Point(391280, 5813165).buffer(55))
platz = unary_union([Point(391262, 5813228).buffer(42), ufer_kanal, E.PLATZ]).convex_hull.difference(E.KANAL)
platz = platz.intersection(box(391195, 5813120, 391345, 5813300)).difference(halle.buffer(0.5))
inseln = unary_union([klecks(c, r, rauh=0.3) for c, r in
                      [((391232, 5813258), 6.5), ((391286, 5813262), 5.5), ((391228, 5813215), 5), ((391292, 5813226), 6),
                       ((391306, 5813278), 4.5)]]).intersection(platz)
stufen_basis = E.KANAL.buffer(9).difference(E.KANAL).intersection(platz)
flaeche(platz.difference(inseln), "platzpflaster", 0.06)
bett(inseln)
for c in [(391232, 5813258), (391292, 5813226)]:
    baum(c[0], c[1], "laub", 12)
for k in range(3):
    st = E.KANAL.buffer(9 - k * 3).difference(E.KANAL.buffer(6 - k * 3)).intersection(platz)
    flaeche(st, "stufe", round(1.35 - k * 0.45, 2))
    PK.append(dict(art="stufe_info", k=k))
flaeche(E.KANAL.buffer(9).difference(E.KANAL.buffer(3)).intersection(platz), "sitzstufen", 0.0)
# Retentionsbecken mit Deck und Trittsteinen
ret = E.RETENTION.intersection(box(391295, 5813150, 391450, 5813240))
flaeche(ret.buffer(-3), "wasser", -0.3)
bett(ret.difference(ret.buffer(-3)), "ufer")
for k in range(10):
    punkt("trittstein", 391310 + k * 2.2, 5813200 + math.sin(k / 1.5) * 1.5, rnd.uniform(0, 90))
# Café-Tische um die Markthalle und an den Inseln
for q in streu(platz.difference(inseln.buffer(1.5)).intersection(halle.buffer(14)), 0.02, 4):
    punkt("schirm", q.x, q.y, farbe=rnd.choice(["weiss", "weiss", "creme", "gruen"]))
    for j in range(2):
        punkt("mensch", q.x + rnd.uniform(-1, 1), q.y + rnd.uniform(-1, 1), haltung="sitz", farbe=rnd.randrange(8))
for x, y, f in [(391300, 5813245, "kiosk1"), (391310, 5813260, "kiosk2")]:
    punkt("kiosk", x, y, rnd.uniform(-15, 15), farbe=f)
menschen(platz.difference(inseln), 90, ("geh", "geh", "steh", "kind", "geh", "steh"))
for q in streu(stufen_basis, 0.05, 1.6):
    punkt("mensch", q.x, q.y, haltung="sitz", farbe=rnd.randrange(8))
kamera("quartiersplatz", (391262, 5813128, 14), (391262, 5813235, 0), 24, "Quartiershauptplatz am Kanal")

# ======================= 5 Gartenfuge (Nachbarschaftsgarten, S4 Baufeld 3) =======================
S4 = [h for h in json.load(open("typologien_geo.json"))["S4"] if h["feld"] == 3 and h["typ"] == "zeile"]
z = sorted(S4, key=lambda h: shape(h["geo"]).centroid.x)[:2]
za, zb = shape(z[0]["geo"]), shape(z[1]["geo"])
fuge = unary_union([za, zb]).convex_hull.difference(za.buffer(2)).difference(zb.buffer(2))
fx0, fy0, fx1, fy1 = fuge.bounds
mitte = LineString([((fx0 + fx1) / 2, fy0 - 6), ((fx0 + fx1) / 2, fy1 + 6)])
weg_g = mäander(mitte, 2.0, 1.5, 2.2).intersection(fuge.buffer(5))
flaeche(fuge.buffer(4).difference(weg_g), "rasen", 0.07)
flaeche(weg_g, "kies", 0.08)
for k, y in enumerate(np.arange(fy0 + 6, fy1 - 4, 6.5)):
    for seite in (-1, 1):
        x = (fx0 + fx1) / 2 + seite * 5.2
        punkt("hochbeet", x, y, 90 + rnd.uniform(-4, 4))
        if rnd.random() < 0.5:
            punkt("mensch", x + seite * 1.4, y, haltung="steh", farbe=rnd.randrange(8))
sp = Point((fx0 + fx1) / 2 - 3, fy1 + 1)
flaeche(klecks((sp.x, sp.y), 4.5), "sand", 0.09)
punkt("kletter", sp.x, sp.y, 0)
for k in range(4):
    punkt("mensch", sp.x + rnd.uniform(-3, 3), sp.y + rnd.uniform(-3, 3), haltung="kind", farbe=rnd.randrange(8))
for y in (fy0 + 3, (fy0 + fy1) / 2, fy1 - 2):
    baum(fx0 + 2.5, y, "bluete", 7)
    baum(fx1 - 2.5, y + 4, "bluete", 7.5)
for y in np.arange(fy0 + 9, fy1, 13):
    punkt("bank", (fx0 + fx1) / 2 + 1.6, y, 90)
bett(fuge.difference(weg_g.buffer(5.6)).intersection(box(fx0, fy0, fx1, fy0 + 8)))
kamera("gartenfuge", ((fx0 + fx1) / 2 + 3, fy0 - 16, 9), ((fx0 + fx1) / 2, fy1, 0), 24, "Gartenfuge: Nachbarschaftsgarten zwischen den Zeilen")

# ======================= Vordergrund je Kamera =======================
begehbar = unary_union([geh, Q.intersection(B(9)), wege, lichtungen, weg_w, platz.difference(inseln), weg_g, fuge.buffer(4).difference(weg_g)])
for name, k in KAMERAS.items():
    cx, cy = k["pos"][0] + OX, k["pos"][1] + OY
    tx, ty = k["ziel"][0] + OX, k["ziel"][1] + OY
    w = math.atan2(ty - cy, tx - cx)
    kegel_ = Polygon([(cx, cy), (cx + 60 * math.cos(w - 0.42), cy + 60 * math.sin(w - 0.42)),
                      (cx + 60 * math.cos(w + 0.42), cy + 60 * math.sin(w + 0.42))]).difference(Point(cx, cy).buffer(9))
    zone = kegel_.intersection(begehbar)
    menschen(zone, 22, ("geh", "geh", "steh", "kind", "geh", "steh"))
    # Bäume, die das Bild zustellen würden, entfernen
    PK[:] = [p for p in PK if not (p["art"] == "baum" and math.hypot(p["p"][0] - k["pos"][0], p["p"][1] - k["pos"][1]) < 20)]

# ======================= Varianten: Grundrisse =======================
geo = json.load(open("typologien_geo.json"))
var = {}
for code, hs in geo.items():
    out = []
    for h in hs:
        g = shape(h["geo"]).simplify(0.2)
        for p in getattr(g, "geoms", [g]):
            if p.geom_type != "Polygon" or p.area < 20:
                continue
            ring = [lok(x, y) for x, y in p.exterior.coords[:-1]]
            out.append(dict(ring=ring, g=h["g"], typ=h["typ"], phase=h["phase"], feld=h["feld"],
                            aktiv=bool(p.intersects(AKTIV)) and h["typ"] not in ("reihe",)))
    var[code] = out
# Schnittperspektive A-A: senkrechte Ebene x = 391250, Blick nach Westen
schnitt = dict(x=lok(391250, 0)[0])
detail = unary_union([gruen_band, B(14), band.buffer(3), wasser_l.buffer(12), fuge.buffer(4), platz])
kb = []
for b_ in json.load(open("3d/szene.json"))["baeume"]:
    if not Point(b_[0] + OX, b_[1] + OY).within(detail):
        kb.append(b_)
# Flächen gleicher Höhe dürfen sich nicht überlagern (Cycles rechnet koplanare Flächen schwarz):
# Rangfolge oben -> unten, jede Art verliert die Fläche aller höherrangigen Arten
RANG = ["wasser", "trittflaeche", "ufersteine", "holzdeck", "stufe", "zebra", "markierung", "radweg", "beet", "sand", "kies",
        "rasen", "platzpflaster", "pflaster", "asphalt", "rasengitter", "wiese", "sitzstufen"]
gruppen = {}
for f in FL:
    gruppen.setdefault((f["art"], f["z"]), []).append(f["poly"])
belegt = Polygon()
flaechen = []
for (a, z) in sorted(gruppen, key=lambda k: (RANG.index(k[0]) if k[0] in RANG else 99, -k[1])):
    u = unary_union(gruppen[(a, z)]).buffer(0)
    if a not in ("stufe", "holzdeck", "markierung", "zebra"):
        u = u.difference(belegt)
    if a == "sitzstufen":
        continue
    belegt = belegt.union(u)
    zz = z if a in ("stufe", "holzdeck") else round(0.02 + 0.006 * (len(RANG) - (RANG.index(a) if a in RANG else 0)), 3)
    if a == "wasser":
        zz = -0.25
    teile = [p for p in getattr(u, "geoms", [u]) if p.geom_type == "Polygon"]
    flaechen.append(dict(art=a, z=zz, **dreiecke(teile)))
FL = [dict(art=f["art"]) for f in FL]
json.dump(dict(varianten=var, flaechen=flaechen, punkte=PK, kameras=KAMERAS, schnitt=schnitt, baeume_kontext=kb,
               markthalle=[[lok(x, y) for x, y in p.exterior.coords[:-1]] for p in getattr(halle, "geoms", [halle])]),
          open("3d/szene3.json", "w"), separators=(",", ":"))
from collections import Counter
print("Flächen", Counter(f["art"] for f in FL))
print("Punkte", Counter(p["art"] for p in PK))
print("Kameras", list(KAMERAS))
