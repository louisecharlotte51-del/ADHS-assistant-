"""
Konzept I, Stand 2 – Pläne im Designsystem „Südring Tempelhof“ (Claude Design):
weiße Baukörper mit schwarzer Linie 0,35 mm + Dachlinien 0,18 mm, Bestand 0,13 mm Grau 40,
Altrosa nur für Bewegung, Rosa sehr hell für halböffentliche Höfe, Salbei/Oliv für Grün, Aqua für Wasser,
harte Schatten Anthrazit 20 % nach unten rechts (Stufe 1–3: 3 / 6 / 10 m), Helvetica.
  out2/lageplan_2000.svg, out2/vertiefung_ankunft_1000.svg, out2/vertiefung_kanal_1000.svg, out2/regelwerk_kacheln.svg
Aufruf: python3 plaene2.py   (nach bebauung2.py)
"""
import json, math, os
from shapely.geometry import shape, box, Point, LineString, Polygon
from shapely.ops import unary_union
from shapely import affinity
import plaene as PL
from plaene import Blatt, FELDER, PARKS, GA, GEBIET, FELD_U, ST, retention, hoehe, HIER
from bebauung import PLATZ_VOR, PLATZ_EIN, TOR, ACHSE_EW, E
import ufer as U

OUT = os.path.join(HIER, "out2")
os.makedirs(OUT, exist_ok=True)
N = json.load(open(os.path.join(HIER, "bebauung2.json")))
HS = [dict(h, geo=shape(h["geo"])) for h in N["haeuser"]]
F = dict(papier="#FEFEFD", grau05="#F0F1F2", wassergrau="#D1D5D7", grau40="#A3A8AB", grau60="#75797C", anthrazit="#46494B",
         schwarz="#1E2022", sandhell="#F2ECD6", sand="#E6DACB", sanddunkel="#C9B99C", rosasehrhell="#F8DEDF", rosahell="#F1BABC",
         altrosa="#C4797F", altrosadunkel="#8F4F56", salbeihell="#E3E8CB", salbei="#CDD5A5", oliv="#A1AC67", olivdunkel="#6A7340",
         aquahell="#CFE5E6", aqua="#8FBFC2", petrol="#5E8898")
FONT = '"Helvetica Neue", Helvetica, Arial, sans-serif'
DEFS = (f'<marker id="spitze" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="2.2" markerHeight="2.2" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{F["altrosa"]}"/></marker>')


def mm(bl, x):
    """Strichstärke in mm (Papier) -> SVG-Einheiten."""
    return x * bl.S * bl.mm ** -1


def schatten(g, stufe):
    s = {1: 3.0, 2: 6.0, 3: 10.0}[stufe]
    teile = [affinity.translate(g, s, -s)]
    for p in getattr(g, "geoms", [g]):
        c = list(p.exterior.coords)
        for a, b in zip(c, c[1:]):
            q = Polygon([a, b, (b[0] + s, b[1] - s), (a[0] + s, a[1] - s)])
            if q.is_valid and q.area > 0:
                teile.append(q)
    return unary_union(teile).difference(g)


def stufe(g):
    return 1 if g <= 3 else 2 if g <= 6 else 3


def dachlinien(g, d=2.2):
    """Attika-Linie innen + Verbindungen von den Ecken (wie Komponente Baukörper)."""
    g = g.simplify(0.4)
    inn = g.buffer(-d, join_style=2)
    if inn.is_empty or inn.geom_type != "Polygon":
        return inn, []
    iv = list(inn.exterior.coords)[:-1]
    linien = []
    for v in list(g.exterior.coords)[:-1]:
        w = min(iv, key=lambda q: math.dist(q, v))
        if math.dist(w, v) < d * 2.2:
            linien.append(LineString([v, w]))
    return inn, linien


def pfeil(bl, linie, breite_mm, farbe=None, deckkraft=1.0):
    farbe = farbe or F["altrosa"]
    pts = " L".join("%.1f,%.1f" % bl.xy(x, y) for x, y in linie.coords)
    bl.o.append(f'<path d="M{pts}" fill="none" stroke="{farbe}" stroke-width="{mm(bl, breite_mm):.2f}" stroke-linejoin="round" '
                f'stroke-linecap="round" stroke-opacity="{deckkraft}" marker-end="url(#spitze)"/>')


def ort(bl, p, r, name):
    """Aufenthaltsort: Rosa-hell-Fläche 55 % + zwei gestrichelte Ringe + Marker."""
    x, y = bl.xy(p.x, p.y)
    R = r * bl.S
    sw = mm(bl, 0.25)
    bl.o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{R:.1f}" fill="{F["rosahell"]}" fill-opacity=".55"/>'
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{R:.1f}" fill="none" stroke="{F["altrosadunkel"]}" stroke-width="{sw:.2f}" stroke-dasharray="{mm(bl, 2):.1f} {mm(bl, 1.5):.1f}"/>'
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{R * 1.25:.1f}" fill="none" stroke="{F["altrosadunkel"]}" stroke-width="{sw:.2f}" stroke-dasharray="{mm(bl, 2):.1f} {mm(bl, 1.5):.1f}"/>'
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{mm(bl, 1.6):.1f}" fill="{F["altrosadunkel"]}"/>')
    bl.text(p.x, p.y - r * 1.25 - 4, name, 9, F["altrosadunkel"], weight=700)


def mittellinie(poly):
    r = poly.minimum_rotated_rectangle
    c = list(r.exterior.coords)
    e = sorted([(math.dist(c[i], c[i + 1]), i) for i in range(4)])
    i, j = e[0][1], e[1][1]
    m = lambda k: ((c[k][0] + c[k + 1][0]) / 2, (c[k][1] + c[k + 1][1]) / 2)
    return LineString([m(i), m(j)]).intersection(poly.buffer(2))


def zeichne(bl, detail=False):
    a = bl.path
    s = lambda x: f"{mm(bl, x):.2f}"
    bl.o.append(f'<rect width="{bl.W:.0f}" height="{bl.H:.0f}" fill="{F["papier"]}"/>')
    # --- Umgebung ---
    a(E.FELD, fill=F["salbeihell"])
    a(PL.PARKS_BESTAND, fill=F["salbeihell"])
    a(ST.EINSCHNITT.union(ST.A100_TROG), fill=F["grau05"], stroke=F["grau40"], stroke_width=s(0.13))
    for l in ST.GLEISE:
        a(l, fill="none", stroke=F["grau40"], stroke_width=s(0.13))
    a(PL.WASSER, fill=F["aqua"])
    a(unary_union([g.buffer(PL.BREITE(n) / 2, cap_style=2) for n, g in PL.STRASSEN.items()]).difference(GEBIET), fill=F["wassergrau"])
    # --- Plangebiet: öffentliche Flächen, Plätze, Grün, Wasser ---
    a(E.KOMTUR_ACHSE.buffer(11, cap_style=2).intersection(GEBIET.buffer(30)), fill=F["wassergrau"])
    plaetze = unary_union([PLATZ_VOR, PLATZ_EIN, TOR, ST.DECKEL.difference(ST.HANG), U.UFERWEG, U.KANALHOF.difference(FELD_U)])
    a(plaetze, fill=F["sandhell"], stroke=F["sanddunkel"], stroke_width=s(0.13))
    for k, l, b in PL.WEGE:
        if k == "wohnweg" and b >= 7:
            a(l.buffer(1.75), fill=F["sand"])
    a(ST.SEITE_WEST.buffer(3.25, cap_style=2), fill=F["wassergrau"])
    a(FELD_U.difference(unary_union([h["geo"] for h in HS])), fill=F["rosasehrhell"])
    gruen = unary_union([g for n, g in PARKS if n != "Stadtwald"] + [ACHSE_EW, ST.HANG])
    a(gruen, fill=F["salbei"], stroke=F["olivdunkel"], stroke_width=s(0.13))
    a(unary_union([g for n, g in PARKS if n == "Stadtwald"]), fill=F["oliv"], stroke=F["olivdunkel"], stroke_width=s(0.13))
    ret = unary_union([retention(g) for n, g in PARKS if n != "Stadtwald"] + [GA.parallel_offset(4.5, "left").buffer(1.6)])
    a(ret, fill=F["aquahell"], stroke=F["petrol"], stroke_width=s(0.13))
    a(GA.buffer(2, cap_style=2).difference(FELD_U).difference(ST.HALLE), fill=F["sand"])
    # --- Ufer ---
    a(U.BUCHT, fill=F["aqua"])
    a(U.DECKS, fill=F["sand"], stroke=F["sanddunkel"], stroke_width=s(0.13))
    a(U.BADESCHIFF, fill="#ffffff", stroke=F["schwarz"], stroke_width=s(0.25))
    a(U.BADESCHIFF.buffer(-1.2, join_style=2), fill=F["aquahell"], stroke=F["petrol"], stroke_width=s(0.13))
    a(U.STEG, fill=F["sand"], stroke=F["schwarz"], stroke_width=s(0.18))
    a(unary_union(U.INSELN), fill=F["salbei"], stroke=F["olivdunkel"], stroke_width=s(0.13))
    a(U.STUFEN, fill=F["sanddunkel"])
    # --- Station und Brücken ---
    for b_ in (ST.BRUECKE_W, ST.BRUECKE_O):
        a(b_, fill=F["salbei"], stroke=F["schwarz"], stroke_width=s(0.25))
    a(ST.FELDBALKON, fill=F["sandhell"], stroke=F["grau40"], stroke_width=s(0.13))
    a(ST.BAHNSTEIG, fill="none", stroke=F["grau60"], stroke_width=s(0.18), stroke_dasharray="4 3")
    a(ST.KASKADE.buffer(1.4), fill=F["aqua"])
    # --- Bäume (Schatten Oliv 35 %, Kronen Salbei) ---
    bm = [(p, 3.2) for p in PL.BAEUME if p.within(bl.clip) and not p.within(FELD_U)]
    for n, g in PARKS:
        bm += PL.baumraster(g.buffer(-3), 8 if n == "Stadtwald" else 11, 0.8 if n == "Stadtwald" else 0.45,
                            seed=len(n) + int(g.area) % 97, aus=ret.buffer(2))
    bm += PL.reihe_baeume(E.KOMTUR_ACHSE.intersection(GEBIET.buffer(20)), 13, 7.5) + PL.reihe_baeume(E.KOMTUR_ACHSE.intersection(GEBIET.buffer(20)), 13, -7.5)
    bm += PL.reihe_baeume(GA, 16, -9) + PL.reihe_baeume(U.UFER, 14, 8)
    geb = unary_union([h["geo"] for h in HS])
    bm = [(p, r) for p, r in bm if not p.within(geb.buffer(1.5)) and not p.within(U.BUCHT.buffer(3))]
    for p, r in bm:
        x, y = bl.xy(p.x + 2, p.y - 2)
        bl.o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * bl.S:.1f}" fill="{F["olivdunkel"]}" fill-opacity=".35"/>')
    for p, r in bm:
        x, y = bl.xy(p.x, p.y)
        bl.o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * bl.S:.1f}" fill="{F["salbei"]}" stroke="{F["olivdunkel"]}" stroke-width="{s(0.13)}"/>')
    # --- Schatten (hart, Anthrazit 20 %) ---
    sch = unary_union([schatten(g, stufe(n)) for g, n in PL.KONTEXT if g.intersects(bl.clip)] +
                      [schatten(h["geo"], stufe(h["g"])) for h in HS] + [schatten(ST.DACH, 3)])
    a(sch, fill=F["anthrazit"], fill_opacity=".2")
    # --- Bestand: 0,13 mm Grau 40 ---
    a(unary_union([g for g, n in PL.KONTEXT]), fill=F["grau05"], stroke=F["grau40"], stroke_width=s(0.13))
    # --- Neubau: weiß, 0,35 mm schwarz, Dachlinien 0,18 mm ---
    for h in HS:
        g = h["geo"]
        a(g, fill="#ffffff", stroke=F["schwarz"], stroke_width=s(0.35))
        if h["typ"] in ("glashaus", "gartenhalle"):
            a(g.buffer(-1.2, join_style=2), fill="none", stroke=F["schwarz"], stroke_width=s(0.13), stroke_dasharray="2 2")
            continue
        inn, linien = dachlinien(g, 2.0 if h["g"] <= 3 else 2.6)
        if not inn.is_empty:
            a(inn, fill="none", stroke=F["schwarz"], stroke_width=s(0.18))
        for l in linien:
            a(l, fill="none", stroke=F["schwarz"], stroke_width=s(0.18))
        if h.get("tor"):
            a(g.exterior, fill="none", stroke=F["schwarz"], stroke_width=s(0.18), stroke_dasharray="3 2")
    # Dach der Station: Gitterschale
    a(ST.DACH, fill="#ffffff", stroke=F["schwarz"], stroke_width=s(0.35))
    gitter = []
    for k in range(-220, 221, 9):
        gitter += [LineString([ST.w(k - 70, -60), ST.w(k + 70, 60)]), LineString([ST.w(k + 70, -60), ST.w(k - 70, 60)])]
    a(unary_union(gitter).intersection(ST.DACH.buffer(-0.8)), fill="none", stroke=F["schwarz"], stroke_width=s(0.13))
    for k in ST.KIOSKE + [ST.RADSTATION]:
        a(k, fill="#ffffff", stroke=F["schwarz"], stroke_width=s(0.25))
    a(U.KRAN, fill="none", stroke=F["schwarz"], stroke_width=s(0.25), stroke_dasharray="4 2")
    # --- Bewegung: Altrosa-Pfeile ---
    pfeil(bl, LineString(list(GA.coords)[::-1]), 2.5)                                   # Bahnhof -> Kanal
    pfeil(bl, LineString(list(U.UFER.parallel_offset(2.5, "left").coords)), 1.2)       # Uferweg (Teltowkanalweg)
    ew = mittellinie(ACHSE_EW)
    if ew.geom_type == "LineString":
        pfeil(bl, ew, 1.2)
    for b_ in (ST.BRUECKE_W, ST.BRUECKE_O):
        pfeil(bl, mittellinie(b_), 1.2)
    for name, inf in N["info"].items():                                               # Hofkette Ost-West
        if len(inf["tore"]) >= 2:
            c = sorted([shape(t).centroid for t in inf["tore"]], key=lambda p: p.x)
            l = LineString([(c[0].x - 12, c[0].y), (c[-1].x + 12, c[-1].y)])
            pfeil(bl, l, 1.2)
    # --- Orte (max. 4) ---
    ort(bl, PLATZ_VOR.centroid, 18, "Bahnhofsplatz")
    ort(bl, ST.NAMEN.get("haupt", Point(391290, 5813520)), 20, "Hauptplatz")
    ort(bl, ST.NAMEN.get("garten", Point(391440, 5813620)), 14, "Gartenplatz")
    ort(bl, U.KANALHOF.centroid, 10, "Badebucht + Kanalhof")
    return bl


def kopf(bl, titel, kapitel, massstab, nr):
    W, H = bl.W, bl.H
    bl.o.append(f'<rect x="0" y="0" width="{max(len(titel) * 19, len(kapitel) * 10) + 60:.0f}" height="104" fill="{F["papier"]}" fill-opacity=".94"/>')
    bl.o.append(f'<g font-family=\'{FONT}\'><text x="28" y="54" font-size="34" font-weight="500" fill="{F["altrosadunkel"]}">{titel}</text>'
                f'<text x="28" y="84" font-size="18" fill="{F["altrosadunkel"]}">{kapitel}</text></g>')
    m = 100 * bl.S
    bl.o.append(f'<rect x="{W - m - 110:.0f}" y="{H - 96:.0f}" width="{m + 110:.0f}" height="96" fill="{F["papier"]}" fill-opacity=".94"/>')
    bl.o.append(f'<g transform="translate({W - m - 150:.0f},{H - 30:.0f})" font-family=\'{FONT}\'>'
                f'<rect width="{m:.0f}" height="4" fill="{F["anthrazit"]}"/><rect width="{m / 2:.0f}" height="4" fill="#fff" stroke="{F["anthrazit"]}" stroke-width=".6"/>'
                f'<text x="0" y="-6" font-size="9" font-weight="500" letter-spacing=".04em" fill="{F["anthrazit"]}">0</text>'
                f'<text x="{m:.0f}" y="-6" font-size="9" font-weight="500" fill="{F["anthrazit"]}" text-anchor="end">100 m</text>'
                f'<text x="{m + 14:.0f}" y="5" font-size="9" font-weight="500" letter-spacing=".04em" fill="{F["anthrazit"]}">M 1:{massstab}   {nr}</text></g>'
                f'<g transform="translate({W - 40:.0f},{H - 70:.0f})"><path d="M0,-20 L8,8 L0,3 L-8,8z" fill="{F["anthrazit"]}"/>'
                f'<text y="22" font-size="10" text-anchor="middle" fill="{F["anthrazit"]}" font-family=\'{FONT}\'>N</text></g>')


def beschriftung(bl, k=1.0):
    t = lambda x, y, s_, sz=9, w=400, rot=0: bl.text(x, y, s_, sz * k, F["anthrazit"], "middle", w, rot=rot)
    pos = {"A": (391190, 5813985), "1": (391140, 5813790), "2": (391125, 5813548), "3": (391110, 5813262),
           "4": (391520, 5813715), "5": (391560, 5813330)}                    # freie Stellen neben den Quartieren
    for q, (x, y) in pos.items():
        nm = {"A": "A Ankunft", "1": "Q1 Werk + Schule", "2": "Q2 Hauptplatz", "3": "Q3 Wald", "4": "Q4 Garten · Food", "5": "Q5 Kanal"}[q]
        t(x, y, nm, 11, 700)
        t(x, y - 13 / k, N["kennwerte"]["quartiere"][q]["name"], 8.5)
    for s_, p, r in [("Komturstraße", E.KOMTUR_ACHSE.interpolate(0.5, normalized=True), 87), ("Teltowkanal", Point(391230, 5813150), -15),
                     ("Tempelhofer Feld", Point(391150, 5814215), 0), ("Sachsenhauser Str.", Point(391515, 5813480), 86)]:
        bl.text(p.x, p.y, s_, 8.5 * k, F["grau60"], rot=r, italic=True)
    p = ST.w(0, 0)
    bl.text(p[0], p[1] - 34, "S Komturstraße", 10 * k, F["anthrazit"], weight=700)


def lageplan():
    bl = Blatt((390890, 5813080, 391640, 5814260), 2000, 2.0)
    zeichne(bl)
    beschriftung(bl)
    kopf(bl, "Südring – Quartiere am Tempelhofer Feld", "Konzept I „Grüne Adern“ · Lageplan", 2000, "Plan 01")
    return bl


def vertiefung(bb, titel, nr):
    bl = Blatt(bb, 1000, 3.0)
    zeichne(bl, detail=True)
    beschriftung(bl, 1.4)
    kopf(bl, "Südring – Quartiere am Tempelhofer Feld", titel, 1000, nr)
    return bl


def speichere(bl, name):
    svg = bl.svg(DEFS).replace('font-family="Archivo, Arial, sans-serif"', f"font-family='{FONT}'")
    p = os.path.join(OUT, name)
    open(p, "w").write(svg)
    return p


KACHELN = [("A.1", "SOCKEL, SCHEIBE, TURM", "Scheibe schirmt Bahn und A100 ab. Turm markiert das Ende der Komturachse. Markthalle ist die Passage zum Bahnhof."),
           ("1.2", "WERKBLOCK", "Geschlossener Rand an Komturstraße und Schulpark. Werkhallen im Hof, Anlieferung durch das Tor."),
           ("2.1", "PLATZRAND UND WINKEL", "Kanten fassen Achse und Hauptplatz. Der Winkel öffnet den Garten nach Süden."),
           ("3.1", "ZEILENHOF", "Kopfbauten an der Erholungsachse. Dahinter Stadthäuser in Ost-West-Zeilen, Gärten nach Süden."),
           ("4.3", "GARTENHOF", "U offen nach Süden. Glashäuser in der Öffnung, Gartenhalle am Gartenplatz."),
           ("5.2", "KAMM ZUM WASSER", "Rücken an der Straße, Finger zum Kanal. Die Höfe öffnen sich zur Badebucht.")]
ROEM = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV"]


def kacheln():
    """Regelwerk je Quartier im Stil Konzeptdiagramm: gleich große Kacheln, gestrichelter Baufeldrahmen, Titel + 1 Satz."""
    T, G, H0 = 300, 32, 150
    W = 3 * T + 4 * G
    H = H0 + 2 * (T + 120) + 330
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W * 0.5:.0f}mm" height="{H * 0.5:.0f}mm" viewBox="0 0 {W} {H}" font-family=\'{FONT}\'>',
         f'<defs>{DEFS}</defs><rect width="{W}" height="{H}" fill="{F["papier"]}"/>',
         f'<text x="{G}" y="58" font-size="34" font-weight="500" fill="{F["altrosadunkel"]}">Regelwerk der Baufelder</text>',
         f'<text x="{G}" y="92" font-size="18" fill="{F["altrosadunkel"]}">Sechs Grundregeln für jedes Feld, eine Typologie je Quartier</text>']
    felder = {n: P for n, q, P in FELDER}
    for k, (name, titel, satz) in enumerate(KACHELN):
        x0, y0 = G + (k % 3) * (T + G), H0 + (k // 3) * (T + 120)
        P = felder[name]
        bx0, by0, bx1, by1 = P.buffer(12).bounds
        sk = (T - 20) / max(bx1 - bx0, by1 - by0)
        ox, oy = x0 + (T - (bx1 - bx0) * sk) / 2, y0 + (T - (by1 - by0) * sk) / 2
        xy = lambda x, y: (ox + (x - bx0) * sk, oy + (by1 - y) * sk)
        d = lambda g: " ".join("M" + " L".join("%.1f,%.1f" % xy(*c) for c in r.coords) + "Z" for p in getattr(g, "geoms", [g])
                               if p.geom_type == "Polygon" for r in [p.exterior, *p.interiors])
        hs = [h for h in HS if h["feld"] == name]
        geb = unary_union([h["geo"] for h in hs])
        o.append(f'<rect x="{x0}" y="{y0}" width="{T}" height="{T}" fill="#ffffff" stroke="{F["grau40"]}" stroke-width=".6"/>')
        o.append(f'<path d="{d(P.difference(geb))}" fill="{F["rosasehrhell"]}"/>')
        o.append(f'<path d="{d(P)}" fill="none" stroke="{F["schwarz"]}" stroke-width=".8" stroke-dasharray="5 4"/>')
        for h in hs:
            o.append(f'<path d="{d(h["geo"])}" fill="#ffffff" stroke="{F["schwarz"]}" stroke-width="1.4"/>')
            c = h["geo"].representative_point()
            if h["geo"].area > 120:
                px, py = xy(c.x, c.y)
                o.append(f'<text x="{px:.1f}" y="{py + 3:.1f}" font-size="9" text-anchor="middle" fill="{F["anthrazit"]}">{ROEM[min(h["g"], 14)]}</text>')
        inf = N["info"][name]
        if len(inf["tore"]) >= 2:
            c = sorted([shape(t).centroid for t in inf["tore"]], key=lambda p: p.x)
            (ax, ay), (bx, by) = xy(c[0].x - 10, c[0].y), xy(c[-1].x + 10, c[-1].y)
            o.append(f'<path d="M{ax:.1f},{ay:.1f} L{bx:.1f},{by:.1f}" stroke="{F["altrosa"]}" stroke-width="5" stroke-linecap="round" fill="none" marker-end="url(#spitze)"/>')
        o.append(f'<path d="M{x0 + T - 18},{y0 + 30} l6,-18 l6,18 l-6,-5z" fill="{F["anthrazit"]}"/>')
        o.append(f'<text x="{x0}" y="{y0 + T + 26}" font-size="14" font-weight="700" letter-spacing=".06em" fill="{F["anthrazit"]}">{["A", "Q1", "Q2", "Q3", "Q4", "Q5"][k]}  {titel}</text>')
        zeilen, z = [], ""
        for wort in satz.split():
            if len(z) + len(wort) > 46:
                zeilen.append(z)
                z = ""
            z += ("" if not z else " ") + wort
        zeilen.append(z)
        for j, zl in enumerate(zeilen):
            o.append(f'<text x="{x0}" y="{y0 + T + 48 + j * 18}" font-size="13" fill="{F["anthrazit"]}">{zl}</text>')
    y = H0 + 2 * (T + 120) + 20
    regeln = ["R1  Baulinie = Feldgrenze: Häuser stehen an Straße, Achse, Platz und Park, auch an beiden Randachsen.",
              "R2  Bautiefe 12 m Wohnen, 13 m mit Gewerbe-EG (4,2 m, 3,25 m licht), Werkhallen bis 15 m.",
              "R3  Hof mind. 21 m, unterbaufrei. Nordseite +1 G, Südseite −1 G oder offen: Sonne in den Hof.",
              "R4  Hofkette Ost-West: Tor im EG auf Höhe der Feldmitte. Die Höfe bilden eine Passage durchs Quartier.",
              "R5  Höhe folgt Raumbreite: an Achse und Platz hoch (+1 G, Ecken +1 G), an schmalen Fugen niedrig (0,4 H bis Wegmitte).",
              "R6  Hof halböffentlich (tagsüber offen), Schwelle statt Zaun, Gastgeber am Hofeingang. Parken nur in den Quartiersgaragen."]
    o.append(f'<text x="{G}" y="{y + 10}" font-size="14" font-weight="700" letter-spacing=".06em" fill="{F["anthrazit"]}">GRUNDREGELN FÜR JEDES BAUFELD</text>')
    for j, r in enumerate(regeln):
        o.append(f'<text x="{G}" y="{y + 40 + j * 26}" font-size="14" fill="{F["anthrazit"]}">{r}</text>')
    o.append("</svg>")
    p = os.path.join(OUT, "regelwerk_kacheln.svg")
    open(p, "w").write("".join(o))
    return p


if __name__ == "__main__":
    print(kacheln())
    print(speichere(lageplan(), "lageplan_2000.svg"))
    print(speichere(vertiefung((391120, 5813760, 391520, 5814160), "Vertiefung Ankunft · Bahnhof, Plätze, Q1", "Plan 02"), "vertiefung_ankunft_1000.svg"))
    print(speichere(vertiefung((391230, 5813140, 391640, 5813500), "Vertiefung Kanal · Q4, Q5, Badebucht", "Plan 03"), "vertiefung_kanal_1000.svg"))
