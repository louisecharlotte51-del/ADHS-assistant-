"""
Zeichnungen Nutzungskonzept + Phase 1 (V6-V8), SVG:
  nutzplan_Vx.svg      Lageplan Nutzungen (EG-Farbe, OG gestrichelt, nummerierte Orte)
  phase1_Vx.svg        Phase 1 im Detail: Station, Bahnhofsplatz, Baufelder 1+2, Werkhof, Freiraumprogramm
  nutzschnitt1_Vx.svg  Nutzungsschnitt durch Phase 1 (West -> Ost), Geschosse nach Nutzung
  nutzschnitt_ns_Vx.svg Nutzungsschnitt Nord -> Süd (S-Bahn -> Kanal) mit Phasengrenzen
  nutzphasen_Vx.svg    Nutzungen im Zuge der Phasen: P1..P4 als Kleinbilder
Aufruf: python3 zeichnungen2.py
"""
import json, os
from shapely.geometry import shape, box, LineString, Point, Polygon
from shapely.ops import unary_union
import entwurf as E
from varianten import EG_H, OG_H

OUT = "zeichnungen"
os.makedirs(OUT, exist_ok=True)
L = lambda n: json.load(open(E.DAT + n + ".json"))["features"]
GEO = json.load(open("nutzung_geo.json"))
NUTZ = json.load(open("nutzung.json"))
PHASEN = ["P1", "P2", "P3", "P4"]
JAHRE = {p: f"{a}–{b}" for p, a, b, _ in E.PHASEN}
PTITEL = {p: t for p, _, _, t in E.PHASEN}

# Nutzungsfarben: Dataviz-Validator (light, Fläche #fbfaf6) bestanden; Kontrast < 3:1 bei
# Gastro/Gesundheit/Mobilität -> überall direkte Beschriftung + Tabelle (Relief-Regel).
NF = dict(laden="#e34948", gastro="#eda100", bildung="#6250d6", gesundheit="#e87ba4", arbeiten="#2a78d6",
          mobilitaet="#1baf7a", wohnen="#f3eee1")
KURZ = dict(laden="Läden", gastro="Gastro", bildung="Bildung/Soziales", gesundheit="Gesundheit", arbeiten="Arbeiten",
            mobilitaet="Mobilität", wohnen="Wohnen")
TINTE, PAPIER, WASSER = "#1d1d1b", "#fbfaf6", "#2aaee8"
SCHRIFT = "Archivo, Arial, sans-serif"

KONTEXT_GEB = [shape(f["geometry"]) for f in L("geb")]
KANAL = unary_union([shape(f["geometry"]) for f in L("gew")])
STRASSEN = [(f["properties"]["strassenname"], shape(f["geometry"])) for f in L("str")]


class Blatt:
    def __init__(self, x0, y0, x1, y1, s):
        self.x0, self.y0, self.x1, self.y1, self.s = x0, y0, x1, y1, s
        self.w, self.h = (x1 - x0) * s, (y1 - y0) * s
        self.C = box(x0, y0, x1, y1)

    def xy(self, x, y):
        return (x - self.x0) * self.s, (self.y1 - y) * self.s

    def pfad(self, g):
        o = ""
        for p in getattr(g, "geoms", [g]):
            if p.is_empty:
                continue
            if p.geom_type == "Polygon":
                for r in [p.exterior, *p.interiors]:
                    o += "M" + " L".join("%.1f,%.1f" % self.xy(x, y) for x, y in r.coords) + "Z "
            elif p.geom_type == "LineString":
                o += "M" + " L".join("%.1f,%.1f" % self.xy(x, y) for x, y in p.coords) + " "
            elif p.geom_type in ("MultiPolygon", "MultiLineString", "GeometryCollection"):
                o += self.pfad(p)
        return o

    def text(self, x, y, t, size=12, farbe=TINTE, anchor="start", weight=400, halo=True):
        px, py = self.xy(x, y)
        h = f' paint-order="stroke" stroke="{PAPIER}" stroke-width="{max(2.5, size / 3.5):.1f}" stroke-linejoin="round"' if halo else ""
        return (f'<text x="{px:.1f}" y="{py:.1f}" font-size="{size}" fill="{farbe}" text-anchor="{anchor}" '
                f'font-weight="{weight}"{h}>{t}</text>')


def kontext(B, gebaeude=True):
    o = [f'<rect width="{B.w:.0f}" height="{B.h:.0f}" fill="{PAPIER}"/>']
    for f in L("fnp"):
        n = f["properties"]["nutzungsart"] or ""
        g = shape(f["geometry"]).intersection(B.C)
        if g.is_empty:
            continue
        if n.startswith("Bahnfläche") or n.startswith("Autobahn"):
            o.append(f'<path d="{B.pfad(g)}" fill="#d6d1c8"/>')
        elif n.startswith("Grünfläche"):
            o.append(f'<path d="{B.pfad(g.difference(E.GEBIET))}" fill="#e2efd6"/>')
    o.append(f'<path d="{B.pfad(E.FELD.intersection(B.C))}" fill="#d3e8c2"/>')
    o.append(f'<path d="{B.pfad(KANAL.intersection(B.C))}" fill="#9cc8e6"/>')
    st = unary_union([g.buffer(5.5, cap_style=2) for _, g in STRASSEN if g.intersects(B.C)]).intersection(B.C)
    o.append(f'<path d="{B.pfad(st)}" fill="#ffffff" stroke="#e4e0d6" stroke-width=".6"/>')
    if gebaeude:
        kg = unary_union([g for g in KONTEXT_GEB if g.intersects(B.C) and not g.representative_point().within(E.GEBIET)])
        o.append(f'<path d="{B.pfad(kg.intersection(B.C))}" fill="#dcd8cf"/>')
    return o


def geruest(B, staerke=1.0):
    o = [f'<path d="{B.pfad(E.GEBIET)}" fill="#e3efd3"/>',
         f'<path d="{B.pfad(E.RAND.union(E.HAUPT_NS).union(E.GRUEN_OST))}" fill="#b5d99a" opacity="{staerke}"/>',
         f'<path d="{B.pfad(E.ERHOLUNG_FL)}" fill="#f8dcb0" opacity="{staerke}"/>',
         f'<path d="{B.pfad(E.KOMTUR_ROW.intersection(B.C))}" fill="#f6c3b9" opacity="{staerke}"/>',
         f'<path d="{B.pfad(unary_union(E.TRICHTER))}" fill="#f9cf98" opacity="{staerke}"/>',
         f'<path d="{B.pfad(E.WASSER_FL.intersection(E.GEBIET.buffer(30)).union(E.SCHWAMM_FL).union(E.RETENTION))}" '
         f'fill="{WASSER}" opacity="{0.85 * staerke}"/>',
         f'<path d="{B.pfad(E.PLATZ)}" fill="#f6e3a6" opacity="{staerke}"/>']
    return o


def haeuser_svg(B, hs, bis=None, neu=None, zahlen=False, blass_zukunft=False):
    """Gebäude: Füllung = EG-Nutzung; gestrichelter Innenrand = andere Nutzung im OG."""
    o = []
    reihen = sorted(hs, key=lambda h: (h["typ"] == "turm"))          # Sockel vor Türmen
    for h in reihen:
        g = shape(h["geo"])
        if not g.intersects(B.C):
            continue
        spaet = bis is not None and PHASEN.index(h["phase"]) > PHASEN.index(bis)
        if spaet:
            if blass_zukunft:
                o.append(f'<path d="{B.pfad(g)}" fill="none" stroke="#9b8f7d" stroke-width=".7" stroke-dasharray="3 2"/>')
            continue
        eg = h["nutz"][0]
        st = 1.6 if (neu and h["phase"] == neu) else 0.7
        o.append(f'<path d="{B.pfad(g)}" fill="{NF[eg]}" stroke="#4a3f33" stroke-width="{st}"/>')
        og = [n for n in h["nutz"][1:] if n != "wohnen" and n != eg]
        if og and g.area > 120:
            inn = g.buffer(-2.4, join_style=2)
            if not inn.is_empty:
                o.append(f'<path d="{B.pfad(inn)}" fill="none" stroke="{NF[og[0]]}" stroke-width="2.6" stroke-dasharray="4 2.5"/>')
        if zahlen and g.area > 140 and h["typ"] != "sockel":
            c = g.representative_point()
            o.append(B.text(c.x, c.y - 1.5, str(h["g"]), 10, "#3b2a1a", "middle", halo=False))
    return o


def BESTAND_NUTZ():
    import nutzungen as N
    bo = N.bestand_orte()
    return [(bo["bestand_nord"], "arbeiten", "P1"), (bo["bestand_sued"], "bildung", "P3"), (bo["markthalle"], "gastro", "P4")]


BN = BESTAND_NUTZ()


def orte_liste(code):
    v = next(v for v in NUTZ["varianten"] if v["code"] == code)
    orte = sorted(v["orte"], key=lambda o: (PHASEN.index(o["phase"]), -o["y"]))
    for i, o in enumerate(orte):
        o["nr"] = i + 1
    return v, orte


def marke(B, o, r=8.5):
    x, y = B.xy(o["x"], o["y"])
    return (f'<g transform="translate({x:.1f},{y:.1f})"><circle r="{r}" fill="{NF[o["kat"]]}" stroke="#fff" stroke-width="1.8"/>'
            f'<text y="{r * 0.42:.1f}" font-size="{r * 1.15:.1f}" font-weight="700" fill="#fff" text-anchor="middle">{o["nr"]}</text></g>')


def marken(B, orte, r=8.5):
    """Nummern-Marken ohne Überlappung: kollidierende Marken kreisen um ihren Ort, mit Haarlinie zurück."""
    import math
    gesetzt, out = [], []
    for ort in orte:
        x0, y0 = B.xy(ort["x"], ort["y"])
        x, y = x0, y0
        k = 0
        while any(math.hypot(x - a, y - b) < 2 * r + 2 for a, b in gesetzt) and k < 24:
            k += 1
            w = k * 2.1
            x, y = x0 + math.cos(w) * (2 * r + 3) * (1 + k // 8), y0 + math.sin(w) * (2 * r + 3) * (1 + k // 8)
        gesetzt.append((x, y))
        if k:
            out.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x:.1f}" y2="{y:.1f}" stroke="{TINTE}" stroke-width=".8"/>'
                       f'<circle cx="{x0:.1f}" cy="{y0:.1f}" r="2" fill="{TINTE}"/>')
        out.append(f'<g transform="translate({x:.1f},{y:.1f})"><circle r="{r}" fill="{NF[ort["kat"]]}" stroke="#fff" stroke-width="1.8"/>'
                   f'<text y="{r * 0.42:.1f}" font-size="{r * 1.15:.1f}" font-weight="700" fill="#fff" text-anchor="middle">{ort["nr"]}</text></g>')
    return out


def bestand_svg(B, bis=None):
    o = []
    for b in E.BESTAND:
        o.append(f'<path d="{B.pfad(b["geo"])}" fill="#d9d3c8" stroke="#4a3f33" stroke-width=".5"/>')
    for g, n, ph in BN:
        aktiv = bis is None or PHASEN.index(ph) <= PHASEN.index(bis)
        if g.intersects(B.C):
            o.append(f'<path d="{B.pfad(g)}" fill="{NF[n] if aktiv else "#d9d3c8"}" stroke="#4a3f33" stroke-width="{1.1 if aktiv else .5}"/>')
    return o


def station(B, r=15):
    x, y = B.xy(E.STATION.x, E.STATION.y)
    return (f'<g transform="translate({x:.0f},{y:.0f})"><rect x="{-r}" y="{-r}" width="{2 * r}" height="{2 * r}" rx="4" fill="#245a24"/>'
            f'<circle r="{r * 0.65:.1f}" fill="none" stroke="#fff" stroke-width="2"/><text y="{r * 0.4:.1f}" text-anchor="middle" '
            f'font-size="{r * 1.1:.0f}" fill="#fff" font-weight="700">S</text></g>')


def nordpfeil_massstab(B, m=100):
    return (f'<g transform="translate({B.w - 28:.0f},34)"><path d="M0,-18 L8,7 L0,2 L-8,7z" fill="{TINTE}"/>'
            f'<text y="22" text-anchor="middle" font-size="13" fill="{TINTE}">N</text></g>'
            f'<g transform="translate(18,{B.h - 18:.0f})"><rect width="{m * B.s:.0f}" height="4" fill="{TINTE}"/>'
            f'<text x="{m * B.s + 7:.0f}" y="5" font-size="12" fill="{TINTE}">{m} m</text></g>')


def svg(B, inhalt):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {B.w:.0f} {B.h:.0f}" font-family="{SCHRIFT}">'
            + "".join(inhalt) + "</svg>")


# ---------------- 1 Nutzungsplan gesamt ----------------
def nutzplan(code):
    B = Blatt(390980, 5813140, 391600, 5813890, 1.25)
    v, orte = orte_liste(code)
    o = kontext(B) + geruest(B)
    for p in GEO[code]["plaetze"]:
        o.append(f'<path d="{B.pfad(shape(p["geo"]))}" fill="#f6e3a6" stroke="#d8b65c" stroke-width=".8"/>')
    o += bestand_svg(B)
    o += haeuser_svg(B, GEO[code]["haeuser"])
    o += marken(B, orte)
    o.append(station(B))
    o.append(nordpfeil_massstab(B))
    return svg(B, o)


# ---------------- 2 Phase 1 im Detail ----------------
P1B = Blatt(391035, 5813655, 391535, 5814085, 1.8)
BAHNHOFSPLATZ = Polygon([(391290, 5813858), (391352, 5813870), (391362, 5813838), (391340, 5813812),
                         (391300, 5813826)])
ZUGANG = LineString([(391338, 5813862), (391340, 5813930), (391344, 5814000), (391345, 5814045)])
QUELLE = Point(E.WASSER.coords[0]).buffer(1)


def phase1(code):
    B = P1B
    v, orte = orte_liste(code)
    hs = GEO[code]["haeuser"]
    bebaut = unary_union([shape(h["geo"]) for h in hs if h["phase"] == "P1"])
    o = kontext(B) + geruest(B)
    # Freiraumprogramm Phase 1
    platz = BAHNHOFSPLATZ.difference(bebaut.buffer(1))
    o.append(f'<path d="{B.pfad(platz)}" fill="#f6e3a6" stroke="#d8b65c" stroke-width="1"/>')
    o.append(f'<path d="{B.pfad(ZUGANG)}" fill="none" stroke="#245a24" stroke-width="5" stroke-dasharray="9 6" stroke-linecap="round"/>')
    kita = next(x for x in orte if x["name"].startswith("Kita"))
    kg = Point(kita["x"], kita["y"]).buffer(34).difference(bebaut.buffer(2)).difference(E.WASSER_FL.buffer(2)) \
        .intersection(E.GEBIET).intersection(Point(kita["x"], kita["y"]).buffer(34))
    kg = max(getattr(kg, "geoms", [kg]), key=lambda g: g.area) if not kg.is_empty else kg
    o.append(f'<path d="{B.pfad(kg)}" fill="#cfe9a9" stroke="#6b9a3c" stroke-width="1.2" stroke-dasharray="3 2"/>')
    garten = E.RAND.intersection(box(391000, 5813700, 391200, 5813870)).difference(bebaut.buffer(2))
    o.append(f'<path d="{B.pfad(garten)}" fill="url(#beete)"/>')
    werkhof = [b["geo"] for b in E.BESTAND if b["geo"].representative_point().within(E.OST_NORD)]
    wh = unary_union(werkhof)
    o.append(f'<path d="{B.pfad(wh.convex_hull.buffer(6).difference(wh).intersection(E.OST_NORD))}" fill="#efe1c6"/>')
    o += bestand_svg(B, "P1")
    for i in (0, 1):
        o.append(f'<path d="{B.pfad(E.BAUFELDER[i])}" fill="none" stroke="#c46d00" stroke-width="1.2" stroke-dasharray="7 4"/>')
    o.append(B.text(391178, 5813850, "Baufeld 1", 11, "#a85a00", weight=700))
    o.append(B.text(391060, 5813812, "Baufeld 2", 11, "#a85a00", weight=700))
    # Gebäude: Phase 1 farbig, spätere Phasen als Umriss
    o += haeuser_svg(B, hs, bis="P1", zahlen=True, blass_zukunft=True)
    for p in GEO[code]["plaetze"]:
        if p["phase"] == "P1":
            o.append(f'<path d="{B.pfad(shape(p["geo"]))}" fill="#f6e3a6" stroke="#d8b65c" stroke-width=".8"/>')
    # Lieferzone: Straßenseite des Supermarkts (Komturstraße bzw. nächstgelegene Straße)
    sm = next(x for x in orte if x["name"].startswith("Supermarkt"))
    smg = min((shape(h["geo"]) for h in hs if h["nutz"][0] == "laden" and h["phase"] == "P1"),
              key=lambda g: g.distance(Point(sm["x"], sm["y"])))
    from shapely.ops import nearest_points
    rand_ = E.GEBIET.boundary.union(E.KOMTUR_ACHSE)
    lp = nearest_points(smg, rand_)[1]
    o.append(f'<path d="{B.pfad(lp.buffer(7, cap_style=3))}" fill="none" stroke="{TINTE}" stroke-width="1.2" stroke-dasharray="2 2"/>')
    # Phasengrenze
    o.append(f'<path d="{B.pfad(LineString([(391035, 5813700), (391330, 5813700)]))}" stroke="{TINTE}" stroke-width="1" '
             f'stroke-dasharray="10 4 2 4"/>')
    o.append(B.text(391040, 5813692, "Grenze Phase 1 | Phase 2", 11, "#5b5247"))
    # Beschriftung Freiraum
    T = lambda x, y, t, s=12, f="#3a5a22", w=600: o.append(B.text(x, y, t, s, f, weight=w))
    T(391350, 5813985, "Neuer Zugang S-Bahn Komturstraße", 13, "#245a24")
    T(391350, 5813970, "Steg über A100 und Germaniastraße, ca. 200 m", 11, "#245a24", 400)
    T(391368, 5813858, "Bahnhofsplatz", 13, "#8a6b12")
    T(391368, 5813845, "Ankommen, Fahrräder, Wochenmarkt", 11, "#8a6b12", 400)
    T(lp.x + 10, lp.y - 18, "Lieferzone", 11, TINTE, 400)
    T(391160, 5813875, "Quellgarten", 13, "#1777a8")
    T(391160, 5813862, "Wasser vom Tempelhofer Feld", 11, "#1777a8", 400)
    c = kg.representative_point() if not kg.is_empty else Point(kita["x"], kita["y"])
    T(c.x - 8, c.y - 4, "Kita-Garten", 11, "#3a5a22")
    T(391040, 5813845, "Gemeinschafts-", 11, "#3a5a22")
    T(391040, 5813834, "gärten am Rand", 11, "#3a5a22")
    T(391420, 5813745, "Werkhof Nord (Bestand)", 12, "#1f4f8f")
    T(391420, 5813733, "Makerspace, Repair-Café ab 2028", 11, "#1f4f8f", 400)
    T(391338, 5813672, "Bewegungsader Komturstraße: Tempo 20, Rad, Bus", 11, "#9a3b2e", 600)
    # Orte (Phase 1): Marken + Legendentafel mit Namen und Kennzahlen
    p1 = [x for x in orte if x["phase"] == "P1"]
    o += marken(B, p1, 9.5)
    o.append(station(B, 16))
    import nutzungen as N
    ph = v["kennzahlen"]["phasen"]["P1"]
    ap = round(sum(ph[k] / N.QM_JE_AP[k] for k in N.QM_JE_AP))
    zeilen = 4 + len(p1)
    o.append(f'<g transform="translate(14,14)"><rect width="376" height="{66 + 17 * len(p1) + 64}" rx="8" fill="{PAPIER}" '
             f'stroke="#d8d2c4" opacity=".96"/>'
             f'<text x="14" y="24" font-size="15" font-weight="700" fill="{TINTE}">Phase 1 · {JAHRE["P1"]} · Ankunft an der S-Bahn</text>'
             f'<text x="14" y="44" font-size="12" fill="#5b5247">{ph["we"]} Wohnungen · ca. {round(ph["we"] * 1.9, -1):.0f} Menschen · '
             f'ca. {ap} Arbeitsplätze</text>')
    for j, ort in enumerate(p1):
        yy = 68 + 17 * j
        o.append(f'<circle cx="22" cy="{yy - 4}" r="7" fill="{NF[ort["kat"]]}"/><text x="22" y="{yy - 0.5}" font-size="8.5" '
                 f'font-weight="700" fill="#fff" text-anchor="middle">{ort["nr"]}</text>'
                 f'<text x="36" y="{yy}" font-size="12" fill="{TINTE}">{ort["name"]}</text>')
    yy = 68 + 17 * len(p1) + 6
    for j, k in enumerate(N.KAT):
        xx = [14, 92, 170, 286][j % 4]
        y2 = yy + (j // 4) * 17
        o.append(f'<rect x="{xx}" y="{y2 - 9}" width="11" height="11" fill="{NF[k]}" stroke="#4a3f33" stroke-width=".5"/>'
                 f'<text x="{xx + 15}" y="{y2}" font-size="11" fill="{TINTE}">{KURZ[k]}</text>')
    o.append(f'<text x="14" y="{yy + 38}" font-size="10.5" fill="#5b5247">Füllung = Erdgeschoss · gestrichelt = Nutzung im OG · '
             f'Zahl = Geschosse</text></g>')
    o.append(nordpfeil_massstab(B, 50))
    defs = ('<defs><pattern id="beete" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(20)">'
            '<rect width="9" height="9" fill="#d9ecbf"/><rect width="9" height="3" fill="#a9cf86"/></pattern></defs>')
    return svg(B, [defs] + o)


# ---------------- 3 Nutzungsschnitte ----------------
def hell(farbe, t=0.5):
    f = [int(farbe[i:i + 2], 16) for i in (1, 3, 5)]
    p = [int(PAPIER[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(a + (b - a) * t):02x}" for a, b in zip(f, p))





def schnitt(code, linie, titel, marken, phasen_y=None, s=2.4, tiefe=45):
    """Schnitt + Ansicht: geschnittene Gebäude kräftig, Gebäude dahinter (bis 'tiefe' m, links der
    Linienrichtung) als helle Ansicht. Jedes Geschoss in der Farbe seiner Nutzung."""
    hs = GEO[code]["haeuser"]
    lang = linie.length
    rand = 36
    breite, hoehe = lang * s + 2 * rand, 40 * s + 92
    boden = 40 * s + 40
    X = lambda d: rand + d * s
    band = linie.buffer(tiefe, single_sided=True)
    o = [f'<rect width="{breite:.0f}" height="{hoehe:.0f}" fill="{PAPIER}"/>']

    def spanne(g):
        ds = [linie.project(Point(c)) for p in getattr(g, "geoms", [g]) for c in p.exterior.coords]
        return max(0, min(ds)), min(lang, max(ds))

    def schnittstuecke(g):
        sx = linie.intersection(g)
        for seg in getattr(sx, "geoms", [sx]):
            if seg.is_empty or seg.geom_type != "LineString":
                continue
            yield sorted((linie.project(Point(seg.coords[0])), linie.project(Point(seg.coords[-1]))))

    def turm(a, b, nutz, schnitt_, z0=0.0):
        z = z0
        for gi, n in enumerate(nutz):
            dz = EG_H if gi == 0 else OG_H
            f = NF[n] if schnitt_ else hell(NF[n], 0.55)
            st = "#3b3128" if schnitt_ else "#b9b0a2"
            o.append(f'<rect x="{X(a):.1f}" y="{boden - (z + dz) * s:.1f}" width="{max((b - a) * s, 1):.1f}" height="{dz * s:.1f}" '
                     f'fill="{f}" stroke="{st}" stroke-width="{.6 if schnitt_ else .4}"/>')
            z += dz
        return z

    # Ansicht (hinter der Linie), fern -> nah
    hinten = [(shape(h["geo"]), h) for h in hs if shape(h["geo"]).intersects(band) and not shape(h["geo"]).intersects(linie)]
    hinten.sort(key=lambda t: -t[0].distance(linie))
    for g, h in hinten:
        a, b = spanne(g)
        if b - a > 0.5:
            turm(a, b, h["nutz"], False)
    for g, n, _ in BN:
        if g.intersects(band) and not g.intersects(linie):
            a, b = spanne(g)
            turm(a, b, [n, n], False)
    for g in KONTEXT_GEB:
        if g.intersects(linie) and not g.representative_point().within(E.GEBIET):
            for a, b in schnittstuecke(g):
                o.append(f'<rect x="{X(a):.1f}" y="{boden - 12 * s:.1f}" width="{max((b - a) * s, 1):.1f}" height="{12 * s:.1f}" fill="#e2ded5"/>')
    # Bodenbänder
    for g, farbe in ((E.RAND.union(E.HAUPT_NS).union(E.GRUEN_OST), "#9ccd7e"), (E.ERHOLUNG_FL, "#f4c98f"),
                     (E.KOMTUR_ROW, "#f2a296"), (E.WASSER_FL.union(E.SCHWAMM_FL), WASSER), (KANAL, "#9cc8e6")):
        for a, b in schnittstuecke(g):
            o.append(f'<rect x="{X(a):.1f}" y="{boden:.1f}" width="{(b - a) * s:.1f}" height="6" fill="{farbe}"/>')
    # Bäume auf Grünstreifen
    for g in (E.ERHOLUNG_FL, E.HAUPT_NS, E.RAND):
        for a, b in schnittstuecke(g):
            d = a + 4
            while d < b - 2:
                o.append(f'<line x1="{X(d):.1f}" x2="{X(d):.1f}" y1="{boden:.1f}" y2="{boden - 7 * s:.1f}" stroke="#6b5a48" stroke-width="1"/>'
                         f'<circle cx="{X(d):.1f}" cy="{boden - 11 * s:.1f}" r="{4.5 * s:.1f}" fill="#7fb767" opacity=".8"/>')
                d += 12
    # Schnitt
    for g, n, _ in BN:
        for a, b in schnittstuecke(g):
            turm(a, b, [n, n], True)
    for h in sorted(hs, key=lambda h: h["typ"] != "sockel"):
        g = shape(h["geo"])
        if not g.intersects(linie):
            continue
        for a, b in schnittstuecke(g):
            z = turm(a, b, h["nutz"], True)
            if h["typ"] == "sockel":
                o.append(f'<rect x="{X(a):.1f}" y="{boden - z * s - 3:.1f}" width="{(b - a) * s:.1f}" height="3" fill="#5f9f45"/>')
    o.append(f'<line x1="10" x2="{breite - 10:.0f}" y1="{boden:.1f}" y2="{boden:.1f}" stroke="{TINTE}" stroke-width="1.6"/>')
    if phasen_y:
        for d, ph in phasen_y:
            o.append(f'<line x1="{X(d):.1f}" x2="{X(d):.1f}" y1="30" y2="{boden + 8:.1f}" stroke="{TINTE}" stroke-width=".8" stroke-dasharray="6 3 1 3"/>')
            o.append(f'<text x="{X(d) + 4:.1f}" y="42" font-size="12" fill="{TINTE}" font-weight="700">{ph}</text>')
    letzte = -999
    for d, t in sorted(marken):
        zeile = 1 if X(d) - letzte < 80 else 0
        letzte = X(d) if not zeile else letzte
        yy = hoehe - 22 + zeile * 14
        o.append(f'<text x="{X(d):.1f}" y="{yy:.0f}" font-size="12" text-anchor="middle" fill="{TINTE}">{t}</text>'
                 f'<line x1="{X(d):.1f}" x2="{X(d):.1f}" y1="{boden + 8:.1f}" y2="{yy - 12:.0f}" stroke="{TINTE}" stroke-width=".6"/>')
    o.append(f'<text x="14" y="20" font-size="14" font-weight="700" fill="{TINTE}">{titel}</text>')
    o.append(f'<text x="{breite - 14:.0f}" y="20" font-size="11" text-anchor="end" fill="#5b5247">kräftig = geschnitten · hell = Ansicht dahinter (bis {tiefe} m)</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {breite:.0f} {hoehe:.0f}" font-family="{SCHRIFT}">'
            + "".join(o) + "</svg>")


def schnitt_y_phase1():
    """Ost-West-Linie in Phase 1, die in allen drei Varianten die meisten Nicht-Wohn-Geschosse schneidet."""
    best = None
    for y in range(5813712, 5813836, 3):
        ln = LineString([(391060, y), (391420, y)])
        n = sum(sum(1 for k in h["nutz"] if k != "wohnen") for c in GEO for h in GEO[c]["haeuser"]
                if h["phase"] == "P1" and shape(h["geo"]).intersects(ln))
        if best is None or n > best[0]:
            best = (n, y)
    return best[1]


# ---------------- 4 Nutzungen im Zuge der Phasen ----------------
def nutzphasen(code):
    B = Blatt(390995, 5813290, 391575, 5813880, 0.62)
    v, orte = orte_liste(code)
    teile = []
    for i, ph in enumerate(PHASEN):
        o = kontext(B, gebaeude=False) + geruest(B, 0.9)
        o += bestand_svg(B, ph)
        o += haeuser_svg(B, GEO[code]["haeuser"], bis=ph, neu=ph, blass_zukunft=True)
        o += marken(B, [x for x in orte if x["phase"] == ph], 6.5)
        o.append(station(B, 9))
        o.append(f'<rect x="0" y="0" width="{B.w:.0f}" height="26" fill="{PAPIER}" opacity=".92"/>'
                 f'<text x="8" y="18" font-size="14" font-weight="700" fill="{TINTE}">{ph} · {JAHRE[ph]}</text>'
                 f'<text x="{B.w - 8:.0f}" y="18" font-size="11" text-anchor="end" fill="#5b5247">{PTITEL[ph]}</text>')
        teile.append(f'<g transform="translate({i * (B.w + 14):.0f},0)"><svg width="{B.w:.0f}" height="{B.h:.0f}" '
                     f'viewBox="0 0 {B.w:.0f} {B.h:.0f}">{"".join(o)}</svg></g>')
    W = 4 * B.w + 3 * 14
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {B.h:.0f}" font-family="{SCHRIFT}">'
            + "".join(teile) + "</svg>")


if __name__ == "__main__":
    y1 = schnitt_y_phase1()
    OW1 = LineString([(391060, y1), (391420, y1)])
    NS = LineString([(391262, 5813870), (391262, 5813200)])
    for v in NUTZ["varianten"]:
        c = v["code"]
        open(f"{OUT}/nutzplan_{c}.svg", "w").write(nutzplan(c))
        open(f"{OUT}/phase1_{c}.svg", "w").write(phase1(c))
        mk = [(OW1.project(Point(391140, y1)), "Baufeld 2"), (OW1.project(Point(E.WASSER.intersection(OW1.buffer(.5)).centroid.x, y1))
                                                             if E.WASSER.intersects(OW1) else 120, "Wasserader"),
              (OW1.project(Point(391240, y1)), "Baufeld 1"), (OW1.project(Point(391330, y1)), "Komturstr."),
              (OW1.project(Point(391372, y1)), "Hub")]
        open(f"{OUT}/nutzschnitt1_{c}.svg", "w").write(
            schnitt(c, OW1, f"Nutzungsschnitt Phase 1 · West → Ost · {v['name']}", mk))
        ph = [(NS.project(Point(391262, 5813700)), "P2"), (NS.project(Point(391262, 5813620)), "P3"),
              (NS.project(Point(391262, 5813470)), "P4"), (NS.project(Point(391262, 5813860)), "P1")]
        mk = [(NS.project(Point(391262, 5813850)), "Bahnhofsplatz"), (NS.project(Point(391262, 5813480)), "Erholungsader"),
              (NS.project(Point(391262, 5813345)), "Albrechtstr."), (NS.project(Point(391262, 5813228)), "Quartiersplatz")]
        open(f"{OUT}/nutzschnitt_ns_{c}.svg", "w").write(
            schnitt(c, NS, f"Nutzungsschnitt Nord → Süd · {v['name']}", mk, phasen_y=ph, s=1.45))
        open(f"{OUT}/nutzphasen_{c}.svg", "w").write(nutzphasen(c))
    print("Schnitt Phase 1 bei y =", y1)
    print(sorted(f for f in os.listdir(OUT) if f.startswith(("nutz", "phase1"))))
