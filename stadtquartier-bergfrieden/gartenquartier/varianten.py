"""
Gartenquartier Bergfrieden – 5 Bebauungsvarianten auf denselben Baufeldern
==========================================================================
Das Gerüst (Adern, Wasserader, Trichter, Baufelder) bleibt in allen Varianten
gleich. Variiert wird nur, WIE die 13 Baufelder bebaut werden:

  V1 Gartenhöfe        offener Blockrand, Höfe als halböffentliche Gärten
  V2 Wasserkämme       Zeilen quer zur Wasserader, Fugen öffnen zum Wasser
  V3 Gartenpunkte      Punkthäuser im Garten (Poisson-Verteilung)
  V4 S-Bahn-Gradient   TOD: dicht/hoch an der Station, niedrig zum Kanal
  V5 Gartenparzellen   Stadthäuser auf Voronoi-Parzellen (Kleingarten-Körnung)

Kennzahlen, Schattensimulation (21.3. und 21.12., Breite 52,46°), Abstands-
flächen nach BauO Bln (0,4 H, mind. 3 m), Bewertung (Composite Scorecard,
6 Kategorien), Phasen S-Bahn -> Kanal.
Aufruf: python3 varianten.py -> varianten.json
"""
import json, math, random
import numpy as np
from shapely.geometry import Point, Polygon, LineString, MultiPoint, box, mapping, shape
from shapely.ops import unary_union, voronoi_diagram, nearest_points
from shapely import affinity
import entwurf as E

LAT = 52.46
EG_H, OG_H = 4.2, 3.1
WE_BGF, EW_WE = 88.0, 1.9
GEBIET_HA = E.GEBIET.area / 1e4
WASSERNETZ = unary_union([E.WASSER] + E.AESTE)
AKTIV = unary_union([E.KOMTUR_ROW.buffer(22), E.ERHOLUNG_FL.buffer(14), E.PLATZ.buffer(20),
                     unary_union(E.TRICHTER).buffer(14)])                      # aktive Erdgeschosse


def hoehe(g):
    return EG_H + (g - 1) * OG_H


def hauptachse(poly):
    """Winkel der längsten Kante des minimalen Rechtecks (Grad)."""
    c = list(poly.minimum_rotated_rectangle.exterior.coords)
    kanten = [(math.dist(c[i], c[i + 1]), math.degrees(math.atan2(c[i + 1][1] - c[i][1], c[i + 1][0] - c[i][0])))
              for i in range(4)]
    return max(kanten)[1]


def teile(ring, feld, schritt):
    """Ring in aneinandergebaute Hausabschnitte teilen: gerade Schnitte senkrecht
    zur Feldkante alle `schritt` Meter (Parzellierung, Brandwände ohne Fuge)."""
    from shapely.ops import split
    rand = feld.exterior
    stuecke = [ring] if ring.geom_type == "Polygon" else list(getattr(ring, "geoms", []))
    linien = []
    for d in np.arange(schritt / 2, rand.length, schritt):
        p, q = rand.interpolate(d), rand.interpolate(min(d + 1, rand.length))
        tx, ty = q.x - p.x, q.y - p.y
        n = math.hypot(tx, ty) or 1
        nx, ny = -ty / n, tx / n
        if not Point(p.x + nx * 3, p.y + ny * 3).within(feld):
            nx, ny = -nx, -ny
        linien.append(LineString([(p.x - nx * 2, p.y - ny * 2), (p.x + nx * 18, p.y + ny * 18)]))
    alle = unary_union(linien)
    neu = []
    for st in stuecke:
        if st.geom_type != "Polygon":
            continue
        neu += [g for g in split(st, alle).geoms if g.geom_type == "Polygon"]
    stuecke = neu
    return [g for g in stuecke if g.area > 60]


def oeffnen(ring, feld, n=2, breite=10):
    """Blockrand zur Wasserader/zu Trichtern öffnen (Lücken = Durchgänge)."""
    p, _ = nearest_points(feld.exterior, WASSERNETZ)
    luecken = [p.buffer(breite / 2 + 2)]
    pts = [feld.exterior.interpolate(t, normalized=True) for t in (0.0, 0.5)]
    luecken += [q.buffer(breite / 2) for q in pts[: n - 1]]
    return ring.difference(unary_union(luecken))


# ---------------- Typologien ----------------
def v1_gartenhoefe(feld, i):
    innen = feld.buffer(-13, join_style=2)
    if innen.is_empty or innen.area < 250:
        ring = feld.buffer(-2)
    else:
        ring = feld.buffer(-2, join_style=2).difference(innen)
    # Hoföffnung als Tordurchgang im EG (kein Schnitt im Baukörper)
    klein = innen.is_empty or min(math.dist(*list(innen.minimum_rotated_rectangle.exterior.coords)[j:j + 2])
                                  for j in range(2)) < 22
    haeuser = []
    for k, h in enumerate(teile(ring, feld, 24)):
        if klein and h.centroid.y < feld.centroid.y:      # kleine Felder: L/U-Hof, nach Süden offen
            continue
        g = 5 + (1 if h.centroid.distance(E.KOMTUR_ACHSE) < 60 else 0) - (1 if k % 4 == 3 else 0)
        # Regel: Südflügel max. 3 Geschosse -> Sonne im Gartenhof
        if not innen.is_empty and h.centroid.y < innen.centroid.y - 6:
            g = 3
        haeuser.append(dict(geo=h, g=max(3, g)))
    return haeuser


def v2_wasserkaemme(feld, i):
    p, q = nearest_points(feld.centroid, WASSERNETZ)
    # Zeilen stehen quer zur Wasserader: Längsachse zeigt zum Wasser
    winkel = math.degrees(math.atan2(q.y - p.y, q.x - p.x))
    g = 5 if feld.centroid.distance(E.STATION) < 450 else 4
    tiefe, abstand = 12.5, max(18.0, 1.0 * hoehe(g) + 6)
    r = affinity.rotate(feld.buffer(-4), -winkel, origin=feld.centroid)
    x0, y0, x1, y1 = r.bounds
    haeuser = []
    y = y0 + 4
    while y + tiefe < y1:
        streifen = box(x0, y, x1, y + tiefe).intersection(r)
        for s in getattr(streifen, "geoms", [streifen]):
            if s.geom_type != "Polygon" or s.area < 160:
                continue
            # lange Zeilen alle ~45 m teilen (Durchgänge)
            sx0, _, sx1, _ = s.bounds
            for xa in np.arange(sx0, sx1, 47):
                t = s.intersection(box(xa, y - 1, xa + 36, y + tiefe + 1))
                for u in getattr(t, "geoms", [t]):
                    if u.geom_type == "Polygon" and u.area > 140:
                        gg = g + (1 if u.centroid.distance(E.KOMTUR_ACHSE.centroid) < 0 else 0)
                        haeuser.append(dict(geo=affinity.rotate(u, winkel, origin=feld.centroid), g=gg))
        y += tiefe + abstand
    return haeuser


def v3_gartenpunkte(feld, i, seed=3):
    rnd = random.Random(seed + i)
    innen = feld.buffer(-11)
    if innen.is_empty:
        return []
    ang = hauptachse(feld)
    x0, y0, x1, y1 = innen.bounds
    pts = []
    for _ in range(4000):
        p = Point(rnd.uniform(x0, x1), rnd.uniform(y0, y1))
        if p.within(innen) and all(p.distance(o) > 41 for o in pts):
            pts.append(p)
    haeuser = []
    for p in pts:
        d = p.distance(E.STATION)
        g = int(np.clip(round(9 - d / 130), 5, 8))
        s = 19 if g <= 6 else 21
        h = affinity.rotate(box(p.x - s / 2, p.y - s / 2, p.x + s / 2, p.y + s / 2), ang, origin=p)
        haeuser.append(dict(geo=h.intersection(feld.buffer(-3)), g=g))
    return haeuser


def v4_gradient(feld, i):
    d = feld.centroid.distance(E.STATION)
    g = int(np.clip(round(10 - d / 100), 3, 8))            # TOD-Zonen A-D
    if g <= 3:                                               # Kanalende: Stadthäuser
        return v5_parzellen(feld, i, g_basis=3)
    tiefe = 13 if g < 6 else 14
    innen = feld.buffer(-tiefe, join_style=2)
    ring = feld.buffer(-2, join_style=2) if innen.is_empty else feld.buffer(-2, join_style=2).difference(innen)
    klein = innen.is_empty or min(math.dist(*list(innen.minimum_rotated_rectangle.exterior.coords)[j:j + 2])
                                  for j in range(2)) < 24
    haeuser = []
    for h in teile(ring, feld, 28):
        sued = (not innen.is_empty) and h.centroid.y < innen.centroid.y - 6
        if klein and h.centroid.y < feld.centroid.y:
            continue
        haeuser.append(dict(geo=h, g=max(3, g - 2) if sued else g))
    if i in (0, 2):                                          # Hochpunkte an der Station / am Autobahnohr
        ecke = min(feld.exterior.coords, key=lambda c: Point(c).distance(E.STATION))
        hp = Point(ecke).buffer(13, join_style=2).envelope.intersection(feld.buffer(-2))
        haeuser = [h for h in haeuser if h["geo"].distance(hp) > 6]
        haeuser.append(dict(geo=hp, g=14 if i == 0 else 11))
    return haeuser


def v5_parzellen(feld, i, g_basis=None, seed=11):
    rnd = random.Random(seed + i)
    x0, y0, x1, y1 = feld.bounds
    pts = []
    for _ in range(3000):
        p = Point(rnd.uniform(x0, x1), rnd.uniform(y0, y1))
        if p.within(feld) and all(p.distance(o) > 24 for o in pts):
            pts.append(p)
    if len(pts) < 3:
        return []
    # Lloyd-Relaxation: gleichmäßigere Parzellen
    for _ in range(3):
        vor = voronoi_diagram(MultiPoint(pts), envelope=feld.buffer(40))
        pts = [z.intersection(feld).centroid for z in vor.geoms if not z.intersection(feld).is_empty]
    vor = voronoi_diagram(MultiPoint(pts), envelope=feld.buffer(40))
    haeuser = []
    for k, z in enumerate(sorted(vor.geoms, key=lambda z: (z.centroid.y, z.centroid.x))):
        parz = z.intersection(feld)
        if parz.is_empty or parz.area < 120:
            continue
        if k % 5 == 2:                                     # jede 5. Parzelle bleibt Gemeinschaftsgarten
            continue
        c = parz.centroid
        ang = hauptachse(parz)
        haus = affinity.rotate(box(c.x - 8, c.y - 7, c.x + 8, c.y + 7), ang, origin=c).intersection(
            parz.buffer(-5.5))
        if haus.area > 70:
            g = g_basis or 4
            haeuser.append(dict(geo=haus, g=g))
    return haeuser


VARIANTEN = [
    ("V1", "Gartenhöfe", v1_gartenhoefe,
     "Offener Blockrand folgt den Feldkanten. Jeder Hof ist ein halböffentlicher Garten, der sich zur Wasserader öffnet."),
    ("V2", "Wasserkämme", v2_wasserkaemme,
     "Zeilen stehen quer zur Wasserader. Die Fugen dazwischen führen Wasser, Wind und Wege direkt zu den Adern."),
    ("V3", "Gartenpunkte", v3_gartenpunkte,
     "Punkthäuser stehen frei im Garten. Der Boden bleibt fast ganz grün, die Kleingarten-Atmosphäre bleibt erlebbar."),
    ("V4", "S-Bahn-Gradient", v4_gradient,
     "Am Bahnhof dicht und hoch, zum Kanal hin niedrig und kleinteilig. Zwei Hochpunkte markieren Station und Autobahnohr."),
    ("V5", "Gartenparzellen", v5_parzellen,
     "Stadthäuser auf einer Parzellenstruktur wie im Kleingarten: viele Bauherren, Baugruppen, jede fünfte Parzelle bleibt Gemeinschaftsgarten."),
]


# ---------------- Sonne & Schatten ----------------
def sonne(dekl, stunde):
    phi, d, h = math.radians(LAT), math.radians(dekl), math.radians(15 * (stunde - 12))
    alt = math.asin(math.sin(phi) * math.sin(d) + math.cos(phi) * math.cos(d) * math.cos(h))
    az = math.atan2(math.sin(h), math.cos(h) * math.sin(phi) - math.tan(d) * math.cos(phi))   # von Süd, + West
    return alt, az


def schatten(haeuser, alt, az):
    if alt <= 0.02:
        return None
    teile_ = []
    for h in haeuser:
        L = hoehe(h["g"]) / math.tan(alt)
        dx, dy = math.sin(az) * L, math.cos(az) * L
        p = h["geo"]
        for poly in getattr(p, "geoms", [p]):
            if poly.geom_type != "Polygon":
                continue
            c = list(poly.exterior.coords)
            teile_.append(poly)
            teile_.append(affinity.translate(poly, dx, dy))
            for a, b in zip(c[:-1], c[1:]):
                q = Polygon([a, b, (b[0] + dx, b[1] + dy), (a[0] + dx, a[1] + dy)])
                if q.is_valid and q.area > 0.01:
                    teile_.append(q)
    return unary_union(teile_)


# ---------------- Auswertung ----------------
def abstand_verstoesse(haeuser):
    """Abstandsflächen BauO Bln: Gebäude-Abstand >= 0,4 H_a + 0,4 H_b, je mind. 3 m."""
    n = 0
    geos = [h["geo"] for h in haeuser]
    for a in range(len(haeuser)):
        for b in range(a + 1, len(haeuser)):
            d = geos[a].distance(geos[b])
            if d < 1.0:             # aneinandergebaut (Brandwand / Fuge) ist zulässig
                continue
            soll = max(3, 0.4 * hoehe(haeuser[a]["g"])) + max(3, 0.4 * hoehe(haeuser[b]["g"]))
            if d < soll - 0.5:
                n += 1
    return n


def durchsetzen(haeuser):
    """Regel-Durchsetzung Abstandsflächen: höheres Haus um je 1 G senken (min. 2 G),
    reicht das nicht, entfällt das kleinere Haus. Gibt Anzahl der Eingriffe zurück."""
    from shapely.strtree import STRtree
    eingriffe = 0
    for _ in range(12):
        geos = [h["geo"] for h in haeuser]
        baum = STRtree(geos)
        konflikt = False
        weg = set()
        for a, ga in enumerate(geos):
            if a in weg:
                continue
            for b in baum.query(ga.buffer(25)):
                b = int(b)
                if b <= a or b in weg:
                    continue
                d = ga.distance(geos[b])
                if d < 1.0:
                    continue
                soll = max(3, 0.4 * hoehe(haeuser[a]["g"])) + max(3, 0.4 * hoehe(haeuser[b]["g"]))
                if d < soll - 0.5:
                    konflikt = True; eingriffe += 1
                    hoch = a if haeuser[a]["g"] >= haeuser[b]["g"] else b
                    if haeuser[hoch]["g"] > 2:
                        haeuser[hoch]["g"] -= 1
                    else:
                        weg.add(a if geos[a].area < geos[b].area else b)
        haeuser = [h for i, h in enumerate(haeuser) if i not in weg]
        if not konflikt:
            break
    return haeuser, eingriffe


def auswerten(code, haeuser, felder):
    bgf = woh = gew = 0.0
    for h in haeuser:
        fp = h["geo"].area
        b = fp * h["g"]
        eg_gew = h["geo"].intersects(AKTIV)
        h["eg"] = "aktiv" if eg_gew else "wohnen"
        g_gew = fp * (1 if eg_gew else 0) + (fp if (code == "V4" and h["g"] >= 6 and eg_gew) else 0)
        bgf += b; gew += g_gew; woh += b - g_gew
    we = woh / WE_BGF
    ew = we * EW_WE
    fp_sum = sum(h["geo"].area for h in haeuser)
    feld_sum = sum(f.area for f in felder)
    oeff_gruen = sum(g.area for g in [E.HAUPT_NS, E.ERHOLUNG_FL, E.WASSER_FL, E.SCHWAMM_FL, E.RAND,
                                       E.GRUEN_OST if hasattr(E, "GRUEN_OST") else Point(0, 0)])
    hof_frei = feld_sum - fp_sum
    # Sonne auf Freiflächen in den Baufeldern (21.3., 10-16 Uhr) und Adern
    frei = unary_union(felder).difference(unary_union([h["geo"] for h in haeuser]))
    adern = unary_union([E.ERHOLUNG_FL, E.WASSER_FL, E.HAUPT_NS])
    sonne_frei, sonne_adern = [], []
    for st in (10, 12, 14, 16):
        s = schatten(haeuser, *sonne(0, st))
        sonne_frei.append(1 - frei.intersection(s).area / frei.area)
        sonne_adern.append(1 - adern.intersection(s).area / adern.area)
    s_w = schatten(haeuser, *sonne(-23.44, 12))
    winter = 1 - frei.intersection(s_w).area / frei.area
    # Schattenbild 21.3. 15 Uhr für die Zeichnung
    s15 = schatten(haeuser, *sonne(0, 15))
    hoehen = [h["g"] for h in haeuser]
    laengen = [max(math.dist(*list(h["geo"].minimum_rotated_rectangle.exterior.coords)[k:k + 2]) for k in range(2))
               for h in haeuser if h["geo"].area > 0]
    # Durchlässigkeit: Anteil der Feldkanten ohne Bebauung (3 m Saum)
    rand = unary_union([f.exterior for f in felder])
    bebauter_rand = rand.intersection(unary_union([h["geo"].buffer(3) for h in haeuser])).length
    durchl = 1 - bebauter_rand / rand.length
    phasen = {}
    for h in haeuser:
        ph = h["phase"]
        phasen.setdefault(ph, dict(bgf=0, we=0))
        phasen[ph]["bgf"] += h["geo"].area * h["g"]
    for ph in phasen:
        phasen[ph]["we"] = round(phasen[ph]["bgf"] * (woh / bgf) / WE_BGF)
        phasen[ph]["bgf"] = round(phasen[ph]["bgf"])
    k = dict(gebaeude=len(haeuser), bgf=round(bgf), bgf_wohnen=round(woh), bgf_gewerbe=round(gew),
             we=round(we), ew=round(ew), gfz_brutto=round(bgf / E.GEBIET.area, 2),
             gfz_netto=round(bgf / feld_sum, 2), grz_netto=round(fp_sum / feld_sum, 2),
             geschosse_mittel=round(sum(h["g"] * h["geo"].area for h in haeuser) / fp_sum, 1),
             geschosse_max=max(hoehen), hoehe_max=round(hoehe(max(hoehen)), 1),
             hauslaenge_mittel=round(float(np.mean(laengen)), 1),
             gruen_oeff_je_ew=round(oeff_gruen / ew, 1), freiraum_je_ew=round((oeff_gruen + hof_frei) / ew, 1),
             sonne_hof_maerz=round(100 * float(np.mean(sonne_frei))), sonne_adern_maerz=round(100 * float(np.mean(sonne_adern))),
             sonne_hof_dez=round(100 * winter), durchlaessigkeit=round(100 * durchl),
             dichte_we_ha=round(we / GEBIET_HA), abstand_verstoesse=abstand_verstoesse(haeuser),
             kita_plaetze=round(ew * 0.045), grundschulplaetze=round(ew * 0.05), stellplaetze=round(we * 0.3),
             arbeitsplaetze=round(gew * 0.8 / 35), phasen=phasen)
    return k, s15


def bewerten(code, k):
    """Composite Scorecard (Design-Evaluation-Skill), 6 Kategorien je 1-5.
    Aus Kennzahlen abgeleitet; qualitative Werte sind typologie-spezifisch gesetzt und benannt."""
    lin = lambda v, a, b: float(np.clip(1 + 4 * (v - a) / (b - a), 1, 5))
    A = np.mean([lin(k["durchlaessigkeit"], 20, 80), lin(60 - k["hauslaenge_mittel"], 0, 45), 5])        # Bahn nah
    vielfalt = {"V1": 3.5, "V2": 3, "V3": 3, "V4": 4.5, "V5": 4.5}[code]
    B = np.mean([lin(k["dichte_we_ha"], 25, 110), vielfalt, lin(k["bgf_gewerbe"] / max(k["bgf"], 1) * 100, 3, 20)])
    C = np.mean([lin(k["freiraum_je_ew"], 15, 60), lin(k["gruen_oeff_je_ew"], 6, 30)])
    D = np.mean([lin(k["sonne_hof_maerz"], 45, 85), lin(k["sonne_hof_dez"], 10, 50),
                 5 if k["abstand_verstoesse"] == 0 else max(1, 5 - k["abstand_verstoesse"] / 3)])
    massstab = {"V1": 4.5, "V2": 3.5, "V3": 3, "V4": 3.5, "V5": 5}[code]
    E_ = np.mean([massstab, lin(8 - k["geschosse_mittel"], 1, 5)])
    F = np.mean([5, lin(100 - 100 * k["grz_netto"], 40, 80)])                                             # Schwammstadt
    cats = dict(A=round(float(A), 1), B=round(float(B), 1), C=round(float(C), 1), D=round(float(D), 1),
                E=round(float(E_), 1), F=round(float(F), 1))
    return cats, round(sum(cats.values()) * 5)          # 6 Kat. x 5 Kriterien x Mittel = /150


if __name__ == "__main__":
    felder = E.BAUFELDER
    out = dict(varianten=[], felder=[dict(nr=i + 1, phase=E.phase(f), flaeche=round(f.area)) for i, f in enumerate(felder)],
               phasen=[dict(code=c, von=a, bis=b, titel=t) for c, a, b, t in E.PHASEN],
               gebiet_ha=round(GEBIET_HA, 2), baufelder_ha=round(sum(f.area for f in felder) / 1e4, 2))
    geo = {}
    for code, name, fn, text in VARIANTEN:
        haeuser = []
        for i, f in enumerate(felder):
            for h in fn(f, i):
                if h["geo"].is_empty or h["geo"].area < 40:
                    continue
                h["phase"] = E.phase(f); h["feld"] = i + 1
                haeuser.append(h)
        haeuser, angepasst = durchsetzen(haeuser)
        k, s15 = auswerten(code, haeuser, felder)
        k["regel_anpassungen"] = angepasst
        cats, total = bewerten(code, k)
        out["varianten"].append(dict(code=code, name=name, text=text, kennzahlen=k, bewertung=cats, punkte=total))
        geo[code] = dict(haeuser=[dict(geo=mapping(h["geo"]), g=h["g"], phase=h["phase"], feld=h["feld"], eg=h["eg"])
                                  for h in haeuser], schatten15=mapping(s15))
        print(f'{code} {name:16s} Häuser {k["gebaeude"]:3d}  WE {k["we"]:5d}  EW {k["ew"]:5d}  GFZbr {k["gfz_brutto"]:.2f}'
              f'  GFZn {k["gfz_netto"]:.2f}  G~{k["geschosse_mittel"]}  Sonne März {k["sonne_hof_maerz"]}%  Dez {k["sonne_hof_dez"]}%'
              f'  Grün/EW {k["gruen_oeff_je_ew"]}  Abst.-Verst. {k["abstand_verstoesse"]}  Punkte {total}/150 {cats}')
    json.dump(out, open("varianten.json", "w"), ensure_ascii=False, indent=1)
    json.dump(geo, open("varianten_geo.json", "w"))
