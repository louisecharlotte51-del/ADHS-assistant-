"""
Konzept I „Grüne Adern" – Pläne als SVG (maßstäblich: width/height in mm).
  out/lageplan_A_2000.svg, out/lageplan_B_2000.svg   Lageplan 1:2000 mit Bestand, Schatten, Freiraum, Wasser
  out/vertiefung_A_1000.svg                          Vertiefung 1:1000 Ankunftsquartier + Q1
  out/erschliessung_2000.svg                         Regelwerk: Wege-Hierarchie, Öffentlichkeit, Feuerwehr
Aufruf: python3 plaene.py   (vorher bebauung.py, geruest.py)
"""
import json, math, os, random
from bebauung import FE, FELDER, E, STATION, ACHSE_EW, TOR, hoehe, HIER
import station as ST
from shapely.geometry import shape, box, Point, LineString, Polygon
from shapely.ops import unary_union
from shapely import affinity

OUT = os.path.join(HIER, "out")
os.makedirs(OUT, exist_ok=True)
B = json.load(open(os.path.join(HIER, "bebauung.json")))
G = json.load(open(os.path.join(HIER, "geruest.json")))
L = lambda n: json.load(open(E.DAT + n + ".json"))["features"]
SCHRIFT = "Archivo, Arial, sans-serif"
INK = "#1d1d1b"

FELD_U = unary_union([P for _, _, P in FELDER])
PARKS = [(f["properties"].get("name"), shape(f["geometry"])) for f in FE if f["properties"]["art"] in ("gruen", "stadtwald")]
WALD = unary_union([g for n, g in PARKS if n == "Stadtwald"])
GEBIET = shape(G["gebiet"])
GA = shape(G["gruenachse"])
WEGE = [(w["klasse"], shape(w["geo"]), w["breite_luecke"]) for w in G["wege"]]

_geb = [(shape(f["geometry"]), f["properties"]["aog"] or 2) for f in L("geb")]
# Bestand: alles außerhalb der neuen Baufelder bleibt; im Plangebiet entfallen nur die Lauben (< 80 m²)
KONTEXT = [(g, n) for g, n in _geb if not g.representative_point().within(FELD_U.buffer(2))
           and not g.representative_point().within(STATION.buffer(-1))
           and not (g.representative_point().within(GEBIET) and g.area < 80)]
_frei = unary_union([shape(f["geometry"]) for f in FE if f["properties"]["art"] in ("gruen", "stadtwald", "achse")] + [TOR])
from bebauung import PLATZ_VOR as _PV, PLATZ_EIN as _PE
_frei = unary_union([_frei, _PV, _PE])
ENTFAELLT = [(g, n) for g, n in KONTEXT if g.intersection(_frei).area > 0.3 * g.area]     # Hallen/Garagen in geplanten Grünflächen
KONTEXT = [(g, n) for g, n in KONTEXT if g.intersection(_frei).area <= 0.3 * g.area]
WASSER = unary_union([shape(f["geometry"]) for f in L("gew")])
PARKS_BESTAND = unary_union([shape(f["geometry"]) for f in L("gruen")])
BAEUME = [shape(f["geometry"]) for f in L("baum_strassenbaeume") + L("baum_anlagenbaeume")]
STRASSEN = {n: g for n, g in E.STR.items()}
_gn = lambda n: [g for nn, g in PARKS if nn == n]
from bebauung import PLATZ_VOR, PLATZ_EIN
ST.NAMEN.update(park1=max(_gn("Grün 1"), key=lambda g: g.area).centroid, haupt=_gn("Grün 2")[0].representative_point(),
                garten=_gn("Grün 4")[0].representative_point(), ufer=min(_gn("Grün 5"), key=lambda g: g.centroid.y).representative_point())
BREITE = lambda n: 32 if ("A 100" in n or "BAB" in n) else (10 if " AS " in n or "Ausf" in n else (20 if n == "Komturstraße" else 13))


class Blatt:
    def __init__(self, bb, massstab, px_pro_m=2.0):
        self.X0, self.Y0, self.X1, self.Y1 = bb
        self.S = px_pro_m
        self.W, self.H = (self.X1 - self.X0) * self.S, (self.Y1 - self.Y0) * self.S
        self.mm = 1000 / massstab
        self.clip = box(*bb)
        self.o = []

    def xy(self, x, y):
        return (x - self.X0) * self.S, (self.Y1 - y) * self.S

    def d(self, g):
        o = ""
        for p in getattr(g, "geoms", [g]):
            if p.is_empty:
                continue
            if p.geom_type == "Polygon":
                for r in [p.exterior, *p.interiors]:
                    o += "M" + " L".join("%.1f,%.1f" % self.xy(x, y) for x, y in r.coords) + "Z "
            elif p.geom_type in ("LineString", "LinearRing"):
                o += "M" + " L".join("%.1f,%.1f" % self.xy(x, y) for x, y in p.coords) + " "
            elif hasattr(p, "geoms"):
                o += self.d(p)
        return o

    def path(self, g, **st):
        g = g.intersection(self.clip.buffer(20)) if not g.is_empty else g
        if g.is_empty:
            return
        a = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in st.items())
        self.o.append(f'<path d="{self.d(g)}" {a}/>')

    def text(self, x, y, t, size=9, farbe=INK, anchor="middle", weight=400, halo=True, rot=0, italic=False):
        px, py = self.xy(x, y)
        h = 'paint-order="stroke" stroke="#fff" stroke-width="2.6" stroke-linejoin="round"' if halo else ""
        r = f' transform="rotate({rot:.1f} {px:.1f} {py:.1f})"' if rot else ""
        it = ' font-style="italic"' if italic else ""
        self.o.append(f'<text x="{px:.1f}" y="{py:.1f}" font-size="{size}" fill="{farbe}" text-anchor="{anchor}" '
                      f'font-weight="{weight}" {h}{r}{it}>{t}</text>')

    def svg(self, defs=""):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{(self.X1 - self.X0) * self.mm:.1f}mm" '
                f'height="{(self.Y1 - self.Y0) * self.mm:.1f}mm" viewBox="0 0 {self.W:.0f} {self.H:.0f}" '
                f'font-family="{SCHRIFT}"><defs>{defs}</defs>' + "".join(self.o) + "</svg>")


DEFS = ('<pattern id="schraff" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        '<line x1="0" y1="0" x2="0" y2="4" stroke="#8aa36a" stroke-width=".5"/></pattern>'
        '<pattern id="gleis" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(-26)">'
        '<line x1="0" y1="0" x2="6" y2="0" stroke="#9a968d" stroke-width=".6"/></pattern>'
        '<pattern id="halb" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)">'
        '<line x1="0" y1="0" x2="0" y2="5" stroke="#c9b98f" stroke-width=".6"/></pattern>')


def schatten(g, h, faktor=0.75, az=225):
    """Schattenwurf eines Prismas: Sonne aus Südwest, Darstellung 45° (Länge = faktor x Höhe)."""
    dx, dy = -math.sin(math.radians(az)) * h * faktor, -math.cos(math.radians(az)) * h * faktor
    teile = [g, affinity.translate(g, dx, dy)]
    for p in getattr(g, "geoms", [g]):
        c = list(p.exterior.coords)
        for a, b in zip(c, c[1:]):
            q = Polygon([a, b, (b[0] + dx, b[1] + dy), (a[0] + dx, a[1] + dy)])
            if q.is_valid and q.area > 0:
                teile.append(q)
    return unary_union(teile).difference(g)


def retention(park, anteil=0.16):
    """Retentionsmulde je Park: organische Form, ca. 16 % der Fläche (Wasserkette)."""
    inn = park.buffer(-5, join_style=1)
    if inn.is_empty or inn.area < 120:
        return Polygon()
    if inn.geom_type == "MultiPolygon":
        inn = max(inn.geoms, key=lambda p: p.area)
    f = min(0.85, math.sqrt(anteil * park.area / inn.area))
    return affinity.scale(inn, f, f * 0.8, origin=inn.representative_point()).buffer(2, join_style=1).buffer(-1.5)


def baumraster(fl, schritt=9.0, dichte=0.55, seed=3, aus=None):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = fl.bounds
    out = []
    y = y0
    k = 0
    while y < y1:
        x = x0 + (schritt / 2 if k % 2 else 0)
        while x < x1:
            p = Point(x + rnd.uniform(-2, 2), y + rnd.uniform(-2, 2))
            if p.within(fl) and rnd.random() < dichte and (aus is None or not p.within(aus)):
                out.append((p, rnd.uniform(2.6, 4.2)))
            x += schritt
        y += schritt * 0.87
        k += 1
    return out


def reihe_baeume(linie, abstand=14.0, versatz=0.0):
    out = []
    for d in range(int(abstand / 2), int(linie.length), int(abstand)):
        p = linie.interpolate(d)
        if versatz:
            q = linie.interpolate(min(d + 1, linie.length))
            n = math.hypot(q.x - p.x, q.y - p.y) or 1
            p = Point(p.x - (q.y - p.y) / n * versatz, p.y + (q.x - p.x) / n * versatz)
        out.append((p, 3.4))
    return out


def komtur_flaeche():
    """Komturstraße im Plangebiet: Raum zwischen den Baufeldern (Hauptachse)."""
    return E.KOMTUR_ACHSE.buffer(11, cap_style=2)


# ------------------------------------------------------------------ Lageplan
def lageplan(var, bb=(390890, 5813150, 391600, 5814260), massstab=2000, pxm=2.0, detail=False):
    bl = Blatt(bb, massstab, pxm)
    a = bl.path
    bl.o.append(f'<rect width="{bl.W:.0f}" height="{bl.H:.0f}" fill="#fbfaf7"/>')
    # Umgebung
    a(E.FELD, fill="#e6ecd6")
    a(PARKS_BESTAND, fill="#e3ead2")
    a(E.BAHN.intersection(bl.clip), fill="#ebe8e2")
    a(ST.EINSCHNITT, fill="url(#gleis)", stroke="#b3afa6", stroke_width=".5")
    a(WASSER, fill="#cfe0e8", stroke="#9fbccb", stroke_width=".6")
    for n, g in STRASSEN.items():
        a(g.buffer(BREITE(n) / 2, cap_style=2), fill="#ece9e3")
    # Plangebiet: öffentliche Flächen (Wege, Plätze) hell, Baufelder halböffentlich, private Gärten
    a(GEBIET.difference(WALD), fill="#f4f1ea")
    a(komtur_flaeche().intersection(GEBIET.buffer(30)), fill="#dcd8d0")
    a(unary_union([PLATZ_VOR, PLATZ_EIN, TOR, ST.DECKEL.difference(ST.HANG)]), fill="#efe8da", stroke="#c9b98f", stroke_width=".4")
    a(TOR, fill="url(#halb)")                                                                # Platzteppich Germaniastraße
    a(FELD_U, fill="#eef0e2")
    a(shape(G[var]["privat"]), fill="#e2e7d0", stroke="#c9d1b3", stroke_width=".3")
    for n, g in PARKS:
        a(g, fill="#d1e0bb" if n != "Stadtwald" else "#bfd3a2")
    a(ACHSE_EW, fill="#dbe6c4")
    # Wege
    for k, l, b in WEGE:
        if k == "wohnweg" and b >= 7:
            a(l.buffer(1.75, cap_style=1), fill="#faf8f3", stroke="#cfc9bd", stroke_width=".35")
    a(ST.SEITE_WEST.buffer(3.25, cap_style=2), fill="#e6e2da", stroke="#cfc9bd", stroke_width=".35")
    # Wasserkette: Retention in jedem Park + Mulde entlang der Grünachse
    ret = unary_union([retention(g) for n, g in PARKS if n != "Stadtwald"])
    a(ret, fill="#c7dde7", stroke="#8fb5c8", stroke_width=".5")
    a(GA.buffer(4, cap_style=2).difference(FELD_U).difference(ST.HALLE), fill="#faf8f3", stroke="#c9b98f", stroke_width=".4")
    a(GA.parallel_offset(4.5, "left").buffer(1.6), fill="#c7dde7")
    # Station, Brücken, Plätze
    ST.zeichne(bl)
    # Bäume
    bm = [(p, 3.2) for p in BAEUME if p.within(bl.clip) and not p.within(FELD_U)]
    for n, g in PARKS:
        bm += baumraster(g.buffer(-3), 8 if n == "Stadtwald" else 11, 0.8 if n == "Stadtwald" else 0.45,
                         seed=len(n) + int(g.area) % 97, aus=ret.buffer(2))
    bm += reihe_baeume(E.KOMTUR_ACHSE.intersection(GEBIET.buffer(20)), 13, 7.5)
    bm += reihe_baeume(E.KOMTUR_ACHSE.intersection(GEBIET.buffer(20)), 13, -7.5)
    bm += reihe_baeume(ACHSE_EW.centroid.buffer(1).exterior, 99)
    bm += reihe_baeume(GA, 16, -9)
    for k, l, b in WEGE:
        if k == "wohnweg" and b >= 12:
            bm += reihe_baeume(l, 18, 4)
    # Schatten (Kontext + Neubau), dann Dächer
    hs = B[var]["haeuser"]
    sch = unary_union([schatten(g, hoehe(n)) for g, n in KONTEXT if g.intersects(bl.clip)] +
                      [schatten(shape(h["geo"]), hoehe(h["g"])) for h in hs])
    for p, r in bm:
        bl.o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#a9c18a" fill-opacity=".85" stroke="#7d9a62" stroke-width=".35"/>'
                    % (*bl.xy(p.x, p.y), r * bl.S))
    a(sch, fill="#000", fill_opacity=".2")
    a(unary_union([g for g, n in KONTEXT]), fill="#d8d5cf", stroke="#a9a6a0", stroke_width=".35")
    for h in hs:
        g = shape(h["geo"])
        sonder = h["typ"] in ("markthalle", "werkhalle", "sporthalle", "schule", "kita", "gartenhalle", "foodlab", "wasserhaus", "pavillon")
        a(g, fill="#f6f2e8" if sonder else "#ffffff", stroke=INK, stroke_width=".75")
        if h["typ"] == "reihenhaus":
            a(g.exterior, fill="none", stroke=INK, stroke_width=".35")
    if detail or massstab <= 2000:
        for h in hs:
            g = shape(h["geo"])
            if g.area > 140:
                p = g.representative_point()
                bl.text(p.x, p.y - 1.6, ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV"][min(h["g"], 14)],
                        5.2 if massstab >= 2000 else 7, "#555", halo=False)
    ST.zeichne_daecher(bl)
    beschriftung(bl, var, massstab)
    return bl


QNAME = {"A": "Ankunft", "1": "Q1 Werk- und Schulquartier", "2": "Q2 Mischquartier am Hauptplatz", "3": "Q3 Wohnen am Stadtwald",
         "4": "Q4 Garten, Gastro, Food", "5": "Q5 Kanalquartier"}


def beschriftung(bl, var, massstab):
    t = bl.text
    k = 1.0 if massstab >= 2000 else 1.5
    for q, (x, y) in {"A": (391212, 5813990), "1": (391020, 5813790), "2": (391030, 5813560), "3": (391040, 5813345),
                      "4": (391520, 5813700), "5": (391530, 5813300)}.items():
        t(x, y, QNAME[q], 11 * k, INK, "middle", 800)
    for name, q, P in FELDER:
        p = P.representative_point()
        t(p.x, p.y + 9, name, 6.5 * k, "#8a7a55", weight=700)
    labels = [("Komturstraße", E.KOMTUR_ACHSE.interpolate(0.55, normalized=True), 87, 8),
              ("Germaniastraße", Point(391150, 5813930), -32, 7), ("Sachsenhauser Str.", Point(391515, 5813480), 86, 7),
              ("Teltowkanal", Point(391260, 5813185), -8, 8), ("Tempelhofer Feld", Point(391120, 5814215), 0, 10),
              ("Erholungsachse", Point(391230, 5813455), -9, 7), ("Grünachse Kanal–Bahnhof", GA.interpolate(0.3, normalized=True), 75, 6.5),
              ("Seitenachse West", Point(391068, 5813700), 89, 6.5)]
    for s, p, r, sz in labels:
        t(p.x, p.y, s, sz * k, "#6b675f", rot=r, italic=True)
    for s, p in [("Schulpark", ST.NAMEN["park1"]), ("Hauptplatz", ST.NAMEN["haupt"]), ("Gartenplatz", ST.NAMEN["garten"]),
                 ("Stadtwald", WALD.representative_point()), ("Uferpark", ST.NAMEN["ufer"])]:
        t(p.x, p.y, s, 7.5 * k, "#4f6b37", weight=700)
    # Nordpfeil, Maßstab, Titel
    W, H = bl.W, bl.H
    bl.o.append(f'<g transform="translate({W - 40:.0f},50)"><path d="M0,-22 L9,9 L0,3 L-9,9z" fill="{INK}"/>'
                f'<text y="26" text-anchor="middle" font-size="12" fill="{INK}">N</text></g>')
    m = 100 * bl.S
    bl.o.append(f'<g transform="translate(24,{H - 26:.0f})"><rect width="{m:.0f}" height="4" fill="{INK}"/>'
                f'<rect width="{m / 2:.0f}" height="4" fill="#fff" stroke="{INK}" stroke-width=".6"/>'
                f'<text x="{m + 8:.0f}" y="6" font-size="11" fill="{INK}">100 m · M 1:{massstab}</text></g>')


def speichere(bl, name):
    p = os.path.join(OUT, name)
    open(p, "w").write(bl.svg(DEFS))
    return p


if __name__ == "__main__":
    for var in "AB":
        print(speichere(lageplan(var), f"lageplan_{var}_2000.svg"))
    print(speichere(lageplan("A", bb=(391090, 5813690, 391500, 5814190), massstab=1000, pxm=3.0, detail=True), "vertiefung_A_1000.svg"))
