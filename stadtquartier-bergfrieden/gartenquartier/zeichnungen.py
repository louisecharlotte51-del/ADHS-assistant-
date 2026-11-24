"""
Zeichnungen für das Gartenquartier Bergfrieden (SVG):
  schritt_1..5.svg   Entwurfsschritte im Skizzenstil (wie das Handblatt)
  lageplan_Vx.svg    Lageplan je Variante mit Schatten 21.3., 15 Uhr
  schnitt_Vx.svg     Nord-Süd-Schnitt (S-Bahn -> Kanal) und Ost-West-Schnitt
  phasen_Vx.svg      5 Phasen als Kleinbild-Reihe
Aufruf: python3 zeichnungen.py
"""
import json, math, os
from shapely.geometry import shape, box, LineString, Point
from shapely.ops import unary_union
import entwurf as E
import varianten as V

OUT = "zeichnungen"
os.makedirs(OUT, exist_ok=True)
X0, Y0, X1, Y1 = 390880, 5813060, 391680, 5814140
S = 0.9
W, H = (X1 - X0) * S, (Y1 - Y0) * S
L = lambda n: json.load(open(E.DAT + n + ".json"))["features"]
GEO = json.load(open("varianten_geo.json"))
DATEN = json.load(open("varianten.json"))

FARBE = dict(papier="#fbfaf6", geb="#dcd8cf", strasse="#ffffff", feld="#cfe5b8", kanal="#7fb7dd", bahn="#c9c4bb",
             gruen="#2f8f2f", gruen_hell="#a9d98c", wasser="#1fa6e6", schwamm="#8fd8f6", orange="#f39c34",
             rot="#ec6b5e", tinte="#1d1d1b", platz="#f6d977")


def pfad(g, s=S, x0=X0, y1=Y1):
    o = ""
    for p in getattr(g, "geoms", [g]):
        if p.is_empty:
            continue
        if p.geom_type == "Polygon":
            for r in [p.exterior, *p.interiors]:
                o += "M" + " L".join(f"{(x - x0) * s:.1f},{(y1 - y) * s:.1f}" for x, y in r.coords) + "Z "
        elif p.geom_type == "LineString":
            o += "M" + " L".join(f"{(x - x0) * s:.1f},{(y1 - y) * s:.1f}" for x, y in p.coords) + " "
    return o


def xy(p):
    return (p[0] - X0) * S, (Y1 - p[1]) * S


DEFS = f"""<defs>
<filter id="hand" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="7"/>
<feDisplacementMap in="SourceGraphic" scale="5"/></filter>
<pattern id="schraffur" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(35)">
<rect width="7" height="7" fill="#fde3bd"/><line x1="0" y1="0" x2="0" y2="7" stroke="{FARBE['orange']}" stroke-width="1.6"/></pattern>
<pattern id="schraffur_gruen" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(-35)">
<line x1="0" y1="0" x2="0" y2="8" stroke="{FARBE['gruen']}" stroke-width="1.3"/></pattern>
<marker id="pfeil" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="context-stroke"/></marker></defs>"""


def basis(bb_clip=True):
    C = box(X0, Y0, X1, Y1)
    o = [f'<rect width="{W:.0f}" height="{H:.0f}" fill="{FARBE["papier"]}"/>']
    for f in L("fnp"):
        n = f["properties"]["nutzungsart"] or ""
        g = shape(f["geometry"]).intersection(C)
        if n.startswith("Bahnfläche") or n.startswith("Autobahn"):
            o.append(f'<path d="{pfad(g)}" fill="{FARBE["bahn"]}"/>')
        elif n.startswith("Grünfläche"):
            o.append(f'<path d="{pfad(g.difference(E.GEBIET))}" fill="#e2efd6"/>')
    o.append(f'<path d="{pfad(E.FELD.intersection(C))}" fill="#cfe6bd"/>')
    o.append(f'<path d="{pfad(unary_union([shape(f["geometry"]) for f in L("gew")]).intersection(C))}" fill="{FARBE["kanal"]}"/>')
    st = []
    for f in L("str"):
        g = shape(f["geometry"])
        if g.intersects(C):
            st.append(g.buffer(5.5, cap_style=2))
    o.append(f'<path d="{pfad(unary_union(st).intersection(C))}" fill="{FARBE["strasse"]}"/>')
    geb = [shape(f["geometry"]) for f in L("geb")]
    o.append(f'<path d="{pfad(unary_union([g for g in geb if g.intersects(C) and not g.representative_point().within(E.GEBIET)]))}" fill="{FARBE["geb"]}"/>')
    return o


BASIS = basis()


def kopf(titel=None, extra=""):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" font-family="Caveat, \'Comic Neue\', cursive">',
            DEFS] + BASIS


def fuss(o):
    st = xy(E.STATION.coords[0])
    o.append(f'<g transform="translate({st[0]:.0f},{st[1]:.0f})"><rect x="-17" y="-17" width="34" height="34" rx="4" fill="{FARBE["gruen"]}"/>'
             f'<circle r="11" fill="none" stroke="#fff" stroke-width="2.4"/><text y="7" text-anchor="middle" font-size="19" fill="#fff" font-family="Arial" font-weight="700">S</text></g>')
    o.append(f'<g transform="translate({W - 34:.0f},40)"><path d="M0,-22 L9,8 L0,2 L-9,8z" fill="{FARBE["tinte"]}"/>'
             f'<text y="26" text-anchor="middle" font-size="18" fill="{FARBE["tinte"]}">N</text></g>')
    o.append(f'<g transform="translate(24,{H - 26:.0f})"><rect width="{100 * S:.0f}" height="5" fill="{FARBE["tinte"]}"/>'
             f'<text x="{100 * S + 8:.0f}" y="6" font-size="17" fill="{FARBE["tinte"]}">100 m</text></g>')
    o.append("</svg>")
    return "\n".join(o)


def label(o, p, text, farbe, size=24, anchor="start"):
    x, y = xy(p)
    o.append(f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" fill="{farbe}" text-anchor="{anchor}" '
             f'paint-order="stroke" stroke="{FARBE["papier"]}" stroke-width="5">{text}</text>')


# ---------------- 5 Entwurfsschritte (Skizzenstil) ----------------
def schritt(n):
    o = kopf()
    hand = 'filter="url(#hand)"'
    # 1 Grüne Hauptachsen
    o.append(f'<path d="{pfad(E.RAND.union(E.HAUPT_NS))}" fill="{FARBE["gruen"]}" opacity=".92" {hand}/>')
    nord_sued = LineString([(391345, 5814130), (391330, 5813860), (391300, 5813470), (391285, 5813160), (391280, 5813070)])
    ost_west = LineString([(390885, 5813540), (391010, 5813500), (391300, 5813470), (391495, 5813520), (391675, 5813490)])
    o.append(f'<path d="{pfad(nord_sued)}" stroke="{FARBE["gruen"]}" stroke-width="4" fill="none" {hand}/>')
    o.append(f'<path d="{pfad(ost_west)}" stroke="{FARBE["gruen"]}" stroke-width="4" fill="none" {hand}/>')
    o.append(f'<path d="{pfad(E.ERHOLUNG_FL)}" fill="{FARBE["gruen"]}" opacity=".85" {hand}/>')
    o.append(f'<path d="{pfad(E.GRUEN_OST)}" fill="url(#schraffur_gruen)" {hand}/>')
    if n == 1:
        label(o, (390905, 5813600), "Franckepark", FARBE["gruen"], 22)
        label(o, (391520, 5813545), "Grünzug Ost", FARBE["gruen"], 22)
        label(o, (391020, 5814090), "Tempelhofer Feld", FARBE["gruen"], 26)
    # 2 Wasserader
    if n >= 2:
        o.append(f'<path d="{pfad(E.WASSER)}" stroke="{FARBE["wasser"]}" stroke-width="11" fill="none" stroke-linecap="round" {hand}/>')
        for a in E.AESTE:
            o.append(f'<path d="{pfad(a.intersection(E.GEBIET.buffer(3)))}" stroke="{FARBE["wasser"]}" stroke-width="4.5" fill="none" stroke-linecap="round" {hand}/>')
        o.append(f'<path d="{pfad(E.RETENTION)}" fill="{FARBE["wasser"]}" opacity=".8" {hand}/>')
        if n == 2:
            label(o, (390905, 5814000), "Wasserader", FARBE["wasser"], 34)
            label(o, (390905, 5813965), "Tempelhofer Feld → Teltowkanal", FARBE["wasser"], 21)
    # 3 Freiräume zuordnen
    if n >= 3:
        o.append(f'<path d="{pfad(E.SCHWAMM_FL)}" fill="{FARBE["schwamm"]}" stroke="{FARBE["wasser"]}" stroke-width="1.5" {hand}/>')
        o.append(f'<path d="{pfad(E.RAND)}" fill="{FARBE["gruen_hell"]}" opacity=".85" {hand}/>')
        if n == 3:
            label(o, (390905, 5813965), "Hauptadern · Schwammflächen · Grünräume", FARBE["gruen"], 21)
            label(o, (390905, 5813930), "Zwischenräume an Grenzen", FARBE["gruen"], 21)
    # 4 Erschließung
    if n >= 4:
        o.append(f'<path d="{pfad(E.KOMTUR_ACHSE)}" stroke="{FARBE["rot"]}" stroke-width="9" fill="none" stroke-linecap="round" {hand}/>')
        o.append(f'<path d="{pfad(unary_union(E.TRICHTER))}" fill="{FARBE["orange"]}" {hand}/>')
        o.append(f'<path d="{pfad(E.PLATZ)}" fill="{FARBE["platz"]}" stroke="{FARBE["orange"]}" stroke-width="2" {hand}/>')
        for a, b in E.TRICHTER_DEF:
            pa, pb = xy(a), xy(b)
            dx, dy = pb[0] - pa[0], pb[1] - pa[1]
            o.append(f'<path d="M{pa[0] - dx * 1.3:.0f},{pa[1] - dy * 1.3:.0f} L{pa[0] + dx * 0.2:.0f},{pa[1] + dy * 0.2:.0f}" '
                     f'stroke="{FARBE["orange"]}" stroke-width="3" marker-end="url(#pfeil)"/>')
        if n == 4:
            label(o, (390905, 5813965), "Trichter: öffentlich → privat", FARBE["orange"], 24)
            label(o, (391360, 5813900), "Bewegungsader", FARBE["rot"], 24)
    # 5 Baufelder
    if n >= 5:
        for i, g in enumerate(E.BAUFELDER):
            o.append(f'<path d="{pfad(g)}" fill="url(#schraffur)" stroke="{FARBE["orange"]}" stroke-width="3" {hand}/>')
            c = g.representative_point()
            x, y = xy(c.coords[0])
            o.append(f'<text x="{x:.0f}" y="{y + 8:.0f}" font-size="26" font-weight="700" text-anchor="middle" fill="{FARBE["tinte"]}">{i + 1}</text>')
        label(o, (390905, 5813965), "13 Wohnbaufelder", "#c46d00", 26)
    for b in E.BESTAND:
        o.append(f'<path d="{pfad(b["geo"])}" fill="#9c968c"/>')
    return fuss(o)


TITEL = ["Grüne Hauptachsen", "Wasserader", "Freiräume zuordnen", "Erschließungsflächen", "Wohnbaufelder"]
for n in range(1, 6):
    open(f"{OUT}/schritt_{n}.svg", "w").write(schritt(n))


# ---------------- Lagepläne ----------------
GESCH = ["#fff7e6", "#fde6bf", "#f9cf8e", "#f3b062", "#e8893c", "#d1652a", "#a8461f", "#7d3018"]
def gfarbe(g):
    return GESCH[min(len(GESCH) - 1, max(0, g - 2))]


def gerust(o, deck=1.0):
    o.append(f'<path d="{pfad(E.GEBIET)}" fill="{FARBE["feld"]}" opacity="{deck}"/>')
    o.append(f'<path d="{pfad(E.RAND.union(E.HAUPT_NS).union(E.GRUEN_OST))}" fill="#7fbf63" opacity="{deck}"/>')
    o.append(f'<path d="{pfad(E.ERHOLUNG_FL)}" fill="#f6c98a" opacity="{deck}"/>')
    o.append(f'<path d="{pfad(E.KOMTUR_ROW.intersection(box(X0, Y0, X1, Y1)))}" fill="#f2a296"/>')
    o.append(f'<path d="{pfad(unary_union(E.TRICHTER))}" fill="#f7b66a" opacity="{deck}"/>')
    o.append(f'<path d="{pfad(E.WASSER_FL.intersection(E.GEBIET.buffer(30)).union(E.SCHWAMM_FL).union(E.RETENTION))}" fill="{FARBE["wasser"]}" opacity="{0.9 * deck}"/>')
    o.append(f'<path d="{pfad(E.PLATZ)}" fill="{FARBE["platz"]}" opacity="{deck}"/>')
    for b in E.BESTAND:
        o.append(f'<path d="{pfad(b["geo"])}" fill="#9c968c"/>')


def lageplan(code, bis=None):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" font-family="Archivo, Arial, sans-serif">', DEFS] + BASIS
    gerust(o)
    hs = GEO[code]["haeuser"]
    reihen = ["P1", "P2", "P3", "P4"]
    if bis is None:
        o.append(f'<path d="{pfad(shape(GEO[code]["schatten15"]))}" fill="#3b3a36" opacity=".16"/>')
    for h in hs:
        if bis is not None and (bis == "P0" or reihen.index(h["phase"]) > reihen.index(bis)):
            continue
        g = shape(h["geo"])
        o.append(f'<path d="{pfad(g)}" fill="{gfarbe(h["g"])}" stroke="#5b4a3a" stroke-width=".8"/>')
        if bis is None and g.area > 260:
            c = g.representative_point()
            x, y = xy(c.coords[0])
            o.append(f'<text x="{x:.0f}" y="{y + 4:.0f}" font-size="11" text-anchor="middle" fill="#3b2a1a">{h["g"]}</text>')
    return fuss(o)


for v in DATEN["varianten"]:
    open(f"{OUT}/lageplan_{v['code']}.svg", "w").write(lageplan(v["code"]))


# ---------------- Phasen (5 Kleinbilder) ----------------
def phasenreihe(code):
    teile = []
    for i, ph in enumerate(["P0", "P1", "P2", "P3", "P4"]):
        svg = lageplan(code, bis=ph)
        inner = svg.split(">", 1)[1].rsplit("</svg>", 1)[0]
        teile.append(f'<g transform="translate({i * (W + 30):.0f},0)">{inner}</g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {5 * W + 120:.0f} {H:.0f}" font-family="Archivo, Arial, sans-serif">'
            + "".join(teile) + "</svg>")


for v in DATEN["varianten"]:
    open(f"{OUT}/phasen_{v['code']}.svg", "w").write(phasenreihe(v["code"]))


# ---------------- Schnitte ----------------
def schnitt(code, linie, titel, marken):
    """Geländeschnitt entlang einer Linie: Gebäude im Schnitt (dunkel), Bäume, Wasser."""
    hs = [(shape(h["geo"]), h["g"]) for h in GEO[code]["haeuser"]] + [(b["geo"], b["og"]) for b in E.BESTAND]
    kontext = [(shape(f["geometry"]), f["properties"]["aog"] or 2) for f in L("geb")
               if shape(f["geometry"]).intersects(linie) and not shape(f["geometry"]).representative_point().within(E.GEBIET)]
    lang = linie.length
    sx, sz = 1.05, 2.4
    breite, hoehe_ = lang * sx + 80, 200
    basis_y = 158
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {breite:.0f} {hoehe_}" font-family="Archivo, Arial, sans-serif">',
         f'<rect width="{breite:.0f}" height="{hoehe_}" fill="{FARBE["papier"]}"/>']
    X = lambda d: 40 + d * sx
    # Bodenbänder: Wasser, Adern
    for g, farbe in ((E.WASSER_FL.union(E.SCHWAMM_FL), FARBE["wasser"]), (E.ERHOLUNG_FL, "#f6c98a"),
                     (E.KOMTUR_ROW, "#f2a296"), (unary_union([shape(f["geometry"]) for f in L("gew")]), FARBE["kanal"])):
        s = linie.intersection(g)
        for seg in getattr(s, "geoms", [s]):
            if seg.is_empty or seg.geom_type != "LineString":
                continue
            a, b = linie.project(Point(seg.coords[0])), linie.project(Point(seg.coords[-1]))
            o.append(f'<rect x="{X(min(a, b)):.1f}" y="{basis_y:.0f}" width="{abs(b - a) * sx:.1f}" height="7" fill="{farbe}"/>')
    o.append(f'<line x1="20" x2="{breite - 20:.0f}" y1="{basis_y}" y2="{basis_y}" stroke="{FARBE["tinte"]}" stroke-width="1.6"/>')
    for (g, og), dunkel in [(k, False) for k in kontext] + [(k, True) for k in hs]:
        s = linie.intersection(g)
        for seg in getattr(s, "geoms", [s]):
            if seg.is_empty or seg.geom_type != "LineString":
                continue
            a, b = linie.project(Point(seg.coords[0])), linie.project(Point(seg.coords[-1]))
            hh = (V.hoehe(og) if dunkel else og * 3.2 + 0.8) * sz
            o.append(f'<rect x="{X(min(a, b)):.1f}" y="{basis_y - hh:.1f}" width="{max(abs(b - a) * sx, 1):.1f}" height="{hh:.1f}" '
                     f'fill="{"#3b3a36" if dunkel else "#d8d3c8"}"/>')
    # Bäume entlang der Adern
    for g in (E.ERHOLUNG_FL, E.HAUPT_NS, E.RAND):
        s = linie.intersection(g)
        for seg in getattr(s, "geoms", [s]):
            if seg.is_empty or seg.geom_type != "LineString":
                continue
            a, b = sorted((linie.project(Point(seg.coords[0])), linie.project(Point(seg.coords[-1]))))
            d = a + 5
            while d < b - 3:
                o.append(f'<circle cx="{X(d):.1f}" cy="{basis_y - 14 * sz:.1f}" r="{5 * sz:.1f}" fill="#6fae5c" opacity=".85"/>'
                         f'<line x1="{X(d):.1f}" x2="{X(d):.1f}" y1="{basis_y:.0f}" y2="{basis_y - 9 * sz:.1f}" stroke="#6b5a48"/>')
                d += 11
    for d, text in marken:
        o.append(f'<text x="{X(d):.0f}" y="{hoehe_ - 12}" font-size="12" text-anchor="middle" fill="{FARBE["tinte"]}">{text}</text>'
                 f'<line x1="{X(d):.0f}" x2="{X(d):.0f}" y1="{basis_y + 9}" y2="{hoehe_ - 26}" stroke="{FARBE["tinte"]}" stroke-width=".6"/>')
    o.append(f'<text x="20" y="20" font-size="14" font-weight="700" fill="{FARBE["tinte"]}">{titel}</text>')
    o.append("</svg>")
    return "\n".join(o)


NS = LineString([(391245, 5814080), (391245, 5813120)])     # S-Bahn -> Kanal (durch die Baufelder)
OW = LineString([(390930, 5813655), (391600, 5813655)])     # Gartenmitte
for v in DATEN["varianten"]:
    c = v["code"]
    ns = schnitt(c, NS, f"Schnitt Nord–Süd · {v['name']}",
                 [(NS.project(Point(391245, 5814061)), "S-Bahn"), (NS.project(Point(391245, 5813485)), "Erholungsader"),
                  (NS.project(Point(391245, 5813345)), "Albrechtstr."), (NS.project(Point(391245, 5813170)), "Kanal")])
    ow = schnitt(c, OW, f"Schnitt West–Ost · {v['name']}",
                 [(OW.project(Point(391020, 5813655)), "Gärten West"), (OW.project(Point(391180, 5813655)), "Wasserader"),
                  (OW.project(Point(391325, 5813655)), "Komturstr."), (OW.project(Point(391520, 5813655)), "Sachsenhauser Str.")])
    open(f"{OUT}/schnitt_ns_{c}.svg", "w").write(ns)
    open(f"{OUT}/schnitt_ow_{c}.svg", "w").write(ow)
print("Zeichnungen:", sorted(os.listdir(OUT)))
