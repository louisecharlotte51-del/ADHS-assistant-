"""
Höhen zu den Schwarzplänen S1-S6 (SVG):
  zeichnungen/hoehenplan_Sx.svg     Höhenplan: Grauwert und Zahl = Geschosse, Schnittführung A-D
  zeichnungen/schnitt_{A,D,B,C}_Sx.svg   Schnitte in wahrem Maßstab (Länge = Höhe):
      A-A Längsschnitt Nord-Süd (S-Bahn -> Kanal, alle Phasen)
      D-D Querschnitt Phase 1, B-B Querschnitt Phase 2, C-C Querschnitt Phase 3
  Schwarz = geschnitten, hellgrau = Ansicht dahinter (bis 40 m), Zahl = Geschosse.
Aufruf: python3 schwarzplan_schnitte.py
"""
import json
from shapely.geometry import shape, LineString, Point
from shapely.ops import unary_union
import entwurf as E
from varianten import EG_H, OG_H
import schwarzplaene as SPL

OUT = "zeichnungen"
GEO = json.load(open("typologien_geo.json"))
INFO = {v["code"]: v for v in json.load(open("typologien.json"))}
KONTEXT_GEB = [(shape(f["geometry"]), f["properties"]["aog"] or 2) for f in SPL.L("geb")]
KANAL = unary_union([shape(f["geometry"]) for f in SPL.L("gew")])
SCHRIFT = SPL.SCHRIFT

LINIEN = [  # Kürzel, Linie, Titel, Marken (Punkt, Text)
    ("A", LineString([(391250, 5813905), (391250, 5813175)]), "Längsschnitt Nord–Süd: S-Bahn → Kanal",
     [((391250, 5813482), "Erholungsader"), ((391250, 5813340), "Albrechtstr.")]),
    ("D", LineString([(390995, 5813760), (391570, 5813760)]), "Querschnitt Phase 1: Baufelder 2 und 1",
     [((391050, 5813760), "Gärten West"), ((391332, 5813760), "Komturstr.")]),
    ("B", LineString([(390995, 5813655), (391570, 5813655)]), "Querschnitt Phase 2: Baufelder 5, 4 und 3",
     [((391040, 5813655), "Gärten West"), ((391332, 5813655), "Komturstr."), ((391548, 5813655), "Sachsenhauser Str.")]),
    ("C", LineString([(390995, 5813540), (391570, 5813540)]), "Querschnitt Phase 3: Baufelder 7, 8, 9 und 6",
     [((391040, 5813540), "Gärten West"), ((391332, 5813540), "Komturstr."), ((391548, 5813540), "Sachsenhauser Str.")]),
]
S = 2.0                      # px je m, horizontal = vertikal (wahrer Maßstab)
TIEFE = 40.0                 # Ansichtstiefe hinter der Linie
HMAX = 46.0                  # m Zeichenhöhe


def h_m(g):
    return EG_H + (g - 1) * OG_H


def schnitt(code, kz, linie, titel, marken):
    lang = linie.length
    rl, rr, oben, unten = 46, 24, 46, 74
    breite, hoehe = lang * S + rl + rr, HMAX * S + oben + unten
    boden = oben + HMAX * S
    X = lambda d: rl + d * S
    band = linie.buffer(TIEFE, single_sided=True)
    o = [f'<rect width="{breite:.0f}" height="{hoehe:.0f}" fill="#fff"/>']

    def stuecke(g):
        sx = linie.intersection(g)
        for seg in getattr(sx, "geoms", [sx]):
            if seg.is_empty or seg.geom_type != "LineString":
                continue
            yield sorted((linie.project(Point(seg.coords[0])), linie.project(Point(seg.coords[-1]))))

    def spanne(g):
        ds = [linie.project(Point(c)) for p in getattr(g, "geoms", [g]) for c in p.exterior.coords]
        return max(0, min(ds)), min(lang, max(ds))

    def koerper(a, b, g, art):
        hm = h_m(g)
        fuell = {"schnitt": "#111", "ansicht": "#d9d9d9", "kontext": "#a8a8a8"}[art]
        o.append(f'<rect x="{X(a):.1f}" y="{boden - hm * S:.1f}" width="{max((b - a) * S, 1):.1f}" height="{hm * S:.1f}" fill="{fuell}"/>')
        if art != "kontext" and (b - a) * S > 3:
            z = EG_H
            for _ in range(g - 1):
                o.append(f'<line x1="{X(a):.1f}" x2="{X(b):.1f}" y1="{boden - z * S:.1f}" y2="{boden - z * S:.1f}" '
                         f'stroke="{"#fff" if art == "schnitt" else "#f4f4f4"}" stroke-width=".6"/>')
                z += OG_H

    # Höhenraster
    for m in (10, 20, 30, 40):
        o.append(f'<line x1="{rl:.0f}" x2="{breite - rr:.0f}" y1="{boden - m * S:.1f}" y2="{boden - m * S:.1f}" stroke="#ececec" stroke-dasharray="4 4"/>'
                 f'<text x="{rl - 6}" y="{boden - m * S + 3.5:.1f}" font-size="10" fill="#8a8a8a" text-anchor="end">{m} m</text>')
    o.append(f'<text x="{rl - 6}" y="{boden + 3.5:.1f}" font-size="10" fill="#8a8a8a" text-anchor="end">0</text>')
    # Ansicht hinter der Linie (fern -> nah)
    hinten = []
    for h in GEO[code]:
        g = shape(h["geo"])
        if g.intersects(band) and not g.intersects(linie):
            hinten.append((g.distance(linie), g, h["g"]))
    for _, g, gg in sorted(hinten, key=lambda t: -t[0]):
        a, b = spanne(g)
        if b - a > 0.8:
            koerper(a, b, gg, "ansicht")
    # Bäume
    for g, takt in ((E.ERHOLUNG_FL, 13), (E.HAUPT_NS, 13), (E.RAND, 13), (E.GRUEN_OST, 30)):
        for a, b in stuecke(g):
            d = a + 5
            while d < b - 3:
                o.append(f'<line x1="{X(d):.1f}" x2="{X(d):.1f}" y1="{boden:.1f}" y2="{boden - 6 * S:.1f}" stroke="#9a9a9a" stroke-width=".8"/>'
                         f'<circle cx="{X(d):.1f}" cy="{boden - 10 * S:.1f}" r="{4.2 * S:.1f}" fill="none" stroke="#9a9a9a" stroke-width=".8"/>')
                d += takt
    # Kontext und Bestand geschnitten
    for g, og in KONTEXT_GEB:
        if g.intersects(linie) and not g.representative_point().within(E.GEBIET):
            for a, b in stuecke(g):
                o.append(f'<rect x="{X(a):.1f}" y="{boden - (og * 3.2 + 0.8) * S:.1f}" width="{max((b - a) * S, 1):.1f}" '
                         f'height="{(og * 3.2 + 0.8) * S:.1f}" fill="#a8a8a8"/>')
    for bst in E.BESTAND:
        for a, b in stuecke(bst["geo"]):
            koerper(a, b, bst["og"], "kontext")
    # Neubau geschnitten + Geschosszahl
    etiketten = []
    for h in sorted(GEO[code], key=lambda h: h["g"]):
        g = shape(h["geo"])
        if not g.intersects(linie):
            continue
        for a, b in stuecke(g):
            if b - a < 0.8:
                continue
            koerper(a, b, h["g"], "schnitt")
            etiketten.append(((a + b) / 2, h["g"]))
    letzte, vorher = [], None
    for d, gg in sorted(etiketten):
        x, y = X(d), boden - h_m(gg) * S - 5
        if vorher and vorher[1] == gg and x - vorher[0] < 16:
            continue                       # Reihenhäuser: eine Zahl je Hausgruppe
        vorher = (x, gg)
        while any(abs(x - lx) < 13 and abs(y - ly) < 10 for lx, ly in letzte):
            y -= 10
        letzte.append((x, y))
        o.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="10" font-weight="700" fill="#111" text-anchor="middle">{gg}</text>')
    # Boden: Wasser, Kanal, Straße
    for g, f in ((E.WASSER_FL.union(E.SCHWAMM_FL).union(E.RETENTION), "#cfd6da"), (KANAL, "#cfd6da"), (E.KOMTUR_ROW, "#e2e2e2")):
        for a, b in stuecke(g):
            o.append(f'<rect x="{X(a):.1f}" y="{boden:.1f}" width="{(b - a) * S:.1f}" height="5" fill="{f}"/>')
    o.append(f'<line x1="8" x2="{breite - 8:.0f}" y1="{boden:.1f}" y2="{boden:.1f}" stroke="#111" stroke-width="1.6"/>')
    # Baufelder + Phase als Klammern
    for i, f in enumerate(E.BAUFELDER, 1):
        for a, b in stuecke(f):
            if b - a < 15:
                continue
            y = boden + 14
            o.append(f'<path d="M{X(a):.1f},{y - 4} L{X(a):.1f},{y} L{X(b):.1f},{y} L{X(b):.1f},{y - 4}" fill="none" stroke="#111" stroke-width=".8"/>'
                     f'<text x="{X((a + b) / 2):.1f}" y="{y + 12}" font-size="10.5" text-anchor="middle" fill="#111">'
                     f'<tspan font-weight="700">{i}</tspan> · {E.phase(f)}</text>')
    for (px, py), t in marken:
        d = linie.project(Point(px, py))
        o.append(f'<text x="{X(d):.1f}" y="{boden + 50}" font-size="10" text-anchor="middle" fill="#666">{t}</text>')
    # Titel
    o.append(f'<text x="{rl}" y="18" font-size="14" font-weight="800" fill="#111">{INFO[code]["code"]} {INFO[code]["name"]} · Schnitt {kz}–{kz}</text>'
             f'<text x="{rl}" y="34" font-size="11" fill="#555">{titel} · schwarz geschnitten, grau Ansicht bis {TIEFE:.0f} m, Zahl = Geschosse</text>')
    if kz == "A":
        o.append(f'<text x="{X(0):.1f}" y="{boden + 50}" font-size="10" fill="#666">← Nord · S-Bahn</text>'
                 f'<text x="{X(lang):.1f}" y="{boden + 64}" font-size="10" fill="#666" text-anchor="end">Süd · Kanal →</text>')
    else:
        o.append(f'<text x="{X(0):.1f}" y="{boden + 64}" font-size="10" fill="#666">← West</text>'
                 f'<text x="{X(lang):.1f}" y="{boden + 64}" font-size="10" fill="#666" text-anchor="end">Ost →</text>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {breite:.0f} {hoehe:.0f}" font-family="{SCHRIFT}">' + "".join(o) + "</svg>"


GRAU = {1: "#d8d8d8", 2: "#d8d8d8", 3: "#bdbdbd", 4: "#9f9f9f", 5: "#7f7f7f", 6: "#5f5f5f", 7: "#404040"}


def grau(g):
    return GRAU.get(g, "#1a1a1a" if g < 10 else "#000")


def hoehenplan(code):
    v = INFO[code]
    o = SPL.grund()
    for h in sorted(GEO[code], key=lambda h: h["g"]):
        g = shape(h["geo"])
        o.append(f'<path d="{SPL.pfad(g)}" fill="{grau(h["g"])}" stroke="#fff" stroke-width=".4"/>')
    for h in GEO[code]:
        g = shape(h["geo"])
        if g.area > 130 and h["typ"] != "reihe":
            p = g.representative_point()
            x, y = SPL.xy(p.x, p.y)
            o.append(f'<text x="{x:.1f}" y="{y + 3.5:.1f}" font-size="9" font-weight="700" text-anchor="middle" '
                     f'fill="{"#fff" if h["g"] >= 5 else "#111"}">{h["g"]}</text>')
    # Schnittführung
    for kz, ln, *_ in LINIEN:
        a, b = ln.coords[0], ln.coords[-1]
        (x1, y1), (x2, y2) = SPL.xy(*a), SPL.xy(*b)
        o.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#d2332a" stroke-width="1.3" stroke-dasharray="10 4 2 4"/>')
        for (x, y) in ((x1, y1), (x2, y2)):
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="#d2332a"/><text x="{x:.1f}" y="{y + 3.8:.1f}" font-size="10.5" '
                     f'font-weight="800" fill="#fff" text-anchor="middle">{kz}</text>')
    # Legende Geschosse
    lx, ly = SPL.W - 250, SPL.Hh - 40
    o.append(f'<rect x="{lx - 8}" y="{ly - 16}" width="244" height="44" fill="#fff" opacity=".93"/>'
             f'<text x="{lx}" y="{ly - 3}" font-size="10.5" fill="#111">Geschosse</text>')
    for j, (g, t) in enumerate(((2, "1–2"), (3, "3"), (4, "4"), (5, "5"), (6, "6"), (7, "7"), (8, "8–9"), (10, "10+"))):
        o.append(f'<rect x="{lx + j * 27}" y="{ly + 3}" width="24" height="10" fill="{grau(g)}" stroke="#999" stroke-width=".4"/>'
                 f'<text x="{lx + j * 27 + 12}" y="{ly + 24}" font-size="9" text-anchor="middle" fill="#111">{t}</text>')
    SPL.rahmen(o, f'{code} {v["name"]}', "Höhenplan · Zahl = Geschosse · rot = Schnittführung A–D")
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SPL.W:.0f} {SPL.Hh:.0f}" font-family="{SCHRIFT}">' + "".join(o) + "</svg>"


if __name__ == "__main__":
    for code in GEO:
        open(f"{OUT}/hoehenplan_{code}.svg", "w").write(hoehenplan(code))
        for kz, ln, titel, marken in LINIEN:
            open(f"{OUT}/schnitt_{kz}_{code}.svg", "w").write(schnitt(code, kz, ln, titel, marken))
    print("fertig:", len(GEO), "Höhenpläne,", len(GEO) * len(LINIEN), "Schnitte")
