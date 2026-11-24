"""
Gartenquartier Bergfrieden – drei Typologien OHNE Höfe (Phase-1-Fokus + Nutzungen)
=================================================================================
Höfe sind Hauptthema des Parallelkonzepts. Diese drei Varianten bebauen dieselben
13 Baufelder, ohne geschlossene Höfe zu bilden:

  V6 Wassermäander       ein durchlaufender Zickzack-Baukörper je Feld; die Taschen
                         öffnen sich abwechselnd zur Wasserader und zur Straße
  V7 Gartendeck          eingeschossiger Sockel (Läden, Werkstätten, Kita) mit
                         Dachgärten als Ersatzparzellen, darauf Punkthäuser
  V8 Nachbarschaftsinseln  Solitäre gruppieren sich um kleine öffentliche Plätze,
                         außen Stadthäuser im Garten

Feld 6 ist in allen Varianten Bildungscampus (Grundschule + Sporthalle), dazu
ein Mobilitätshub an der S-Bahn. Gebäude tragen eine Nutzung je Geschoss
(siehe nutzungen.py). Abstandsflächen werden wie in V1-V5 durchgesetzt.
"""
import math, random
import numpy as np
from shapely.geometry import Point, Polygon, LineString, MultiLineString, box
from shapely.ops import unary_union, split
from shapely import affinity
import entwurf as E
from varianten import hoehe, hauptachse, durchsetzen, WASSERNETZ

SCHULFELD = 5          # Index von Baufeld 6
STATION_NAH = 420      # m: Zone A/B des TOD-Gradienten


def rahmen(feld):
    ang = hauptachse(feld)
    c = feld.centroid
    return ang, c, (lambda g: affinity.rotate(g, -ang, origin=c)), (lambda g: affinity.rotate(g, ang, origin=c))


def g_station(p, basis, plus=1):
    return basis + (plus if p.distance(E.STATION) < STATION_NAH else 0)


def schneide_entlang(koerper, linie, schritt, breite=40):
    """Baukörper entlang einer Mittellinie in Hausabschnitte teilen (aneinandergebaut)."""
    schnitte = []
    for d in np.arange(schritt, linie.length - schritt / 3, schritt):
        p, q = linie.interpolate(d), linie.interpolate(min(d + 1, linie.length))
        tx, ty = q.x - p.x, q.y - p.y
        n = math.hypot(tx, ty) or 1
        nx, ny = -ty / n * breite / 2, tx / n * breite / 2
        schnitte.append(LineString([(p.x - nx, p.y - ny), (p.x + nx, p.y + ny)]))
    teile = [koerper] if koerper.geom_type == "Polygon" else list(getattr(koerper, "geoms", []))
    if not schnitte:
        return teile
    alle = unary_union(schnitte)
    out = []
    for t in teile:
        out += [g for g in split(t, alle).geoms if g.geom_type == "Polygon" and g.area > 50]
    return out


# ---------------- V6 Wassermäander ----------------
def v6_maeander(feld, i):
    ang, c, rot, zur = rahmen(feld)
    r = rot(feld.buffer(-3, join_style=2))
    x0, y0, x1, y1 = r.bounds
    T = 12.5
    if y1 - y0 < 2 * T + 14:                      # schmal: gestreckte Zeile mit Knick
        ym = (y0 + y1) / 2
        pts = [(x0, ym - 3), ((x0 + x1) / 2, ym + 3), (x1, ym - 3)]
    else:
        n = max(2, round((x1 - x0) / 44))
        xs = np.linspace(x0 + T / 2, x1 - T / 2, n + 1)
        pts = [(x, y0 + T / 2 + 1 if k % 2 == 0 else y1 - T / 2 - 1) for k, x in enumerate(xs)]
    linie = LineString(pts)
    koerper = linie.buffer(T / 2, join_style=2, cap_style=2).intersection(r)
    haeuser = []
    teile = schneide_entlang(koerper, linie, 26)
    for k, t in enumerate(teile):
        g_ = zur(t)
        g = g_station(g_.centroid, 6 if k % 3 else 7)
        if g_.distance(WASSERNETZ) < 12:           # zum Wasser hin abtreppen
            g -= 1
        haeuser.append(dict(geo=g_, g=max(3, g), typ="maeander", gruppe=f"M{i}"))
    return haeuser


# ---------------- V7 Gartendeck ----------------
def v7_gartendeck(feld, i, seed=7):
    """Punkthäuser (24 x 24 m) auf eingeschossigen Deck-Sockeln; Deckdach = Gärten."""
    rnd = random.Random(seed + i)
    ang, c, rot, zur = rahmen(feld)
    innen = feld.buffer(-15)
    if innen.is_empty:
        innen = feld.buffer(-9)
    if innen.is_empty:
        return []
    x0, y0, x1, y1 = innen.bounds
    pts = []
    for _ in range(4000):
        p = Point(rnd.uniform(x0, x1), rnd.uniform(y0, y1))
        if p.within(innen) and all(p.distance(o) > 46 for o in pts):   # Sweep: 46 m / 24 m
            pts.append(p)
    haeuser, pads = [], []
    for p in pts:
        g = int(np.clip(round(11.5 - p.distance(E.STATION) / 100), 6, 11))
        turm = affinity.rotate(box(p.x - 12, p.y - 12, p.x + 12, p.y + 12), ang, origin=p)
        haeuser.append(dict(geo=turm, g=g, typ="turm"))
        pads.append(affinity.rotate(box(p.x - 21, p.y - 20, p.x + 21, p.y + 20), ang, origin=p))
    sockel = unary_union(pads).intersection(feld.buffer(-4, join_style=2))
    # Sockel in Einheiten von ca. 21 x 20 m teilen: Läden, Kita-Gruppen, Werkstätten, Gartenwohnungen
    for s_ in getattr(sockel, "geoms", [sockel]):
        if s_.geom_type != "Polygon" or s_.area <= 150:
            continue
        r = rot(s_)
        x0, y0, x1, y1 = r.bounds
        nx, ny = max(1, round((x1 - x0) / 21)), max(1, round((y1 - y0) / 20))
        dx, dy = (x1 - x0) / nx, (y1 - y0) / ny
        for i_ in range(nx):
            for j_ in range(ny):
                t = r.intersection(box(x0 + i_ * dx, y0 + j_ * dy, x0 + (i_ + 1) * dx, y0 + (j_ + 1) * dy))
                for t_ in getattr(t, "geoms", [t]):
                    if t_.geom_type == "Polygon" and t_.area > 60:
                        haeuser.append(dict(geo=zur(t_), g=1, typ="sockel"))
    return haeuser


# ---------------- V8 Nachbarschaftsinseln ----------------
MASSE = [(26, 14), (22, 15), (30, 13), (18, 18), (24, 14)]


def v8_inseln(feld, i, seed=13):
    rnd = random.Random(seed + i)
    ang, c, rot, zur = rahmen(feld)
    innen = feld.buffer(-26)
    r = rot(feld)
    x0, y0, x1, y1 = r.bounds
    n = max(1, round(feld.area / 5200))
    zentren = [zur(Point(x0 + (x1 - x0) * (k + 0.5) / n, (y0 + y1) / 2)) for k in range(n)]
    zentren = [z if (innen.is_empty or z.within(innen)) else (nearest(innen, z) if not innen.is_empty else z) for z in zentren]
    haeuser, plaetze = [], []
    def passt(h, g, gruppe=None):
        H = hoehe(g)
        for o in haeuser:
            if gruppe and o.get("gruppe") == gruppe:
                d = abs(hauptachse(h) - hauptachse(o["geo"])) % 180
                if min(d, 180 - d) > 75:              # § 6 Abs. 3 BauO Bln
                    continue
            if h.distance(o["geo"]) < max(6, 0.4 * H) + max(3, 0.4 * hoehe(o["g"])):
                return False
        return True
    for zi, z in enumerate(zentren):
        R = 17
        if any(z.distance(p.centroid) < 2 * R + 30 for p in plaetze):
            continue
        plaetze.append(z.buffer(R))
        start = ang + rnd.uniform(0, 90)
        gruppe = f"I{i}_{zi}"
        for k in range(4):                           # Stern: Giebel zum Platz, 90° versetzt
            a_ = math.radians(start + k * 90)
            L_ = rnd.choice([24, 27, 30])
            g = g_station(z, rnd.choice([5, 6, 6]))
            mp = Point(z.x + math.cos(a_) * (R + L_ / 2 + 1), z.y + math.sin(a_) * (R + L_ / 2 + 1))
            h = affinity.rotate(box(mp.x - L_ / 2, mp.y - 6.5, mp.x + L_ / 2, mp.y + 6.5),
                                math.degrees(a_), origin=mp).intersection(feld.buffer(-3))
            if h.area < 150:
                continue
            if not passt(h, g, gruppe):
                g = 4
                if not passt(h, g, gruppe):
                    continue
            haeuser.append(dict(geo=h, g=g, typ="insel", gruppe=gruppe))
    # Stadthäuser im Garten außerhalb der Inseln
    frei = feld.buffer(-4).difference(unary_union([h["geo"].buffer(8) for h in haeuser] + [p.buffer(5) for p in plaetze]))
    fx0, fy0, fx1, fy1 = feld.bounds
    for _ in range(5000):
        p = Point(rnd.uniform(fx0, fx1), rnd.uniform(fy0, fy1))
        if not p.within(frei.buffer(-6.5)):
            continue
        h = affinity.rotate(box(p.x - 8, p.y - 6.5, p.x + 8, p.y + 6.5), ang, origin=p)
        g = g_station(p, 4)
        if passt(h, g):
            haeuser.append(dict(geo=h, g=g, typ="stadthaus"))
    return haeuser, plaetze


def nearest(poly, p):
    from shapely.ops import nearest_points
    return nearest_points(poly, p)[0]


# ---------------- Sonderbausteine (für alle drei Varianten gleich) ----------------
def schulcampus(feld):
    """Feld 6: 3-zügige Grundschule (2 Flügel, 3 G) + Zweifeld-Sporthalle."""
    ang, c, rot, zur = rahmen(feld)
    r = rot(feld.buffer(-6, join_style=2))
    x0, y0, x1, y1 = r.bounds
    nord = box(x0, y1 - 16, x0 + (x1 - x0) * 0.72, y1).intersection(r)
    west = box(x0, y0 + 8, x0 + 16, y1 - 16).intersection(r)
    halle = box(x1 - 46, y0 + 6, x1, y0 + 6 + 28).intersection(r)
    out = []
    for g_, typ, g in ((nord, "schule", 3), (west, "schule", 3), (halle, "sporthalle", 2)):
        g_ = zur(g_)
        if not g_.is_empty and g_.area > 200:
            out.append(dict(geo=g_, g=g, typ=typ))
    return out


def mobilitaetshub():
    """Fahrradparkhaus + Quartiersgarage an der S-Bahn, im Grünraum Nordost."""
    p = Point(391390, 5813790)                     # 34 x 52 m: EG trägt bei Bedarf den Supermarkt (>= 1.000 m²)
    ang = math.degrees(math.atan2(5813821 - 5813778, 391364 - 391345))
    geo = affinity.rotate(box(p.x - 17, p.y - 26, p.x + 17, p.y + 26), ang - 90, origin=p).intersection(E.GEBIET) \
        .difference(E.KOMTUR_ROW.buffer(2))
    return dict(geo=geo, g=4, typ="mobilitaet", phase="P1", feld=0)


VARIANTEN2 = [
    ("V6", "Wassermäander", v6_maeander,
     "Ein durchlaufender Baukörper schwingt im Zickzack durch jedes Feld. Die offenen Taschen wechseln die Seite: eine zur Wasserader, eine zur Straße. So entstehen Gärten, aber keine Höfe."),
    ("V7", "Gartendeck", v7_gartendeck,
     "Ein eingeschossiger Sockel trägt Läden, Werkstätten und Kitas. Sein Dach ist ein Gartendeck mit Ersatzparzellen für die Kleingärtner. Darauf stehen schlanke Punkthäuser."),
    ("V8", "Nachbarschaftsinseln", v8_inseln,
     "Fünf Häuser gruppieren sich jeweils um einen kleinen öffentlichen Platz mit Café oder Kita. Dazwischen stehen Stadthäuser im Garten. Die Plätze sind offen, nicht umbaut."),
]


def winkel_ausnahme(a, b):
    """§ 6 Abs. 3 BauO Bln: Abstandsflächen dürfen sich überdecken, wenn die Wände
    mehr als 75° zueinander stehen. Gilt hier für Arme desselben Mäanders."""
    if a.get("gruppe") is None or a.get("gruppe") != b.get("gruppe"):
        return False
    d = abs(hauptachse(a["geo"]) - hauptachse(b["geo"])) % 180
    return min(d, 180 - d) > 75


def generiere():
    alle, plaetze_alle = {}, {}
    for code, name, fn, text in VARIANTEN2:
        haeuser, plaetze = [], []
        for i, f in enumerate(E.BAUFELDER):
            if i == SCHULFELD:
                neu = schulcampus(f)
            else:
                res = fn(f, i)
                if isinstance(res, tuple):
                    neu, pl = res
                    plaetze += [dict(geo=p, phase=E.phase(f), feld=i + 1) for p in pl]
                else:
                    neu = res
            for h in neu:
                if h["geo"].is_empty or h["geo"].area < 40:
                    continue
                h["phase"] = E.phase(f)
                h["feld"] = i + 1
                haeuser.append(h)
        haeuser.append(mobilitaetshub())
        # Abstandsflächen; Sockel und aufgesetzte Türme gelten als ein Gebäude
        frei = [h for h in haeuser if h["typ"] not in ("sockel",)]
        fest = [h for h in haeuser if h["typ"] == "sockel"]
        frei, eingriffe = durchsetzen(frei, ausnahme=winkel_ausnahme)
        alle[code] = dict(haeuser=fest + frei, eingriffe=eingriffe)
        plaetze_alle[code] = plaetze
    return alle, plaetze_alle


if __name__ == "__main__":
    alle, pl = generiere()
    for code, d in alle.items():
        hs = d["haeuser"]
        bgf = sum(h["geo"].area * h["g"] for h in hs)
        print(code, "Häuser", len(hs), "BGF", round(bgf), "GFZbr", round(bgf / E.GEBIET.area, 2),
              "Eingriffe", d["eingriffe"], "Plätze", len(pl[code]),
              "Typen", {t: sum(1 for h in hs if h["typ"] == t) for t in sorted({h["typ"] for h in hs})})
