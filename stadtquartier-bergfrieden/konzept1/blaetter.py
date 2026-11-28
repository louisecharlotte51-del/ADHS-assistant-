"""
Konzept I – Regelwerk-Plan, Schnitte 1:500, Piktogramme, Bahnhofs-Schnitt (SVG in out/).
Aufruf: python3 blaetter.py   (nach bebauung.py, geruest.py)
"""
import json, math, os
import plaene as PL
from plaene import Blatt, B, G, FELDER, WEGE, PARKS, GA, GEBIET, FELD_U, ST, INK, DEFS, speichere, retention, hoehe
from bebauung import PLATZ_VOR, PLATZ_EIN, TOR, ACHSE_EW, E, QH
from shapely.geometry import shape, LineString, Point, box
from shapely.ops import unary_union

OUT = PL.OUT
BB = (390960, 5813180, 391560, 5814180)
QF = {"A": "#c0504d", "1": "#8064a2", "2": "#e3a33b", "3": "#6f9c4f", "4": "#d27c3a", "5": "#4f81bd"}


def grundlage(bl, fein=False):
    a = bl.path
    bl.o.append(f'<rect width="{bl.W:.0f}" height="{bl.H:.0f}" fill="#fff"/>')
    a(unary_union([g for g, n in PL.KONTEXT if g.intersects(bl.clip)]), fill="#e4e2dd")
    a(ST.EINSCHNITT.union(ST.A100_TROG), fill="#efede8")
    a(PL.WASSER, fill="#dbe8ee")


# ------------------------------------------------------------------ Regelwerk: Erschließung + Öffentlichkeit
def regelwerk(var="A"):
    bl = Blatt(BB, 2000, 1.6)
    grundlage(bl)
    a = bl.path
    a(shape(G[var]["halb"]), fill="#f6e3c4")
    a(shape(G[var]["privat"]), fill="#e9b77a")
    a(unary_union([g for n, g in PARKS]), fill="#cfe1bc")
    a(ACHSE_EW, fill="#cfe1bc")
    a(unary_union([PLATZ_VOR, PLATZ_EIN, TOR, ST.DECKEL]), fill="#e8e6e1")
    a(unary_union([shape(h["geo"]) for h in B[var]["haeuser"]]), fill="#4a4a48")
    # Wege-Hierarchie
    a(E.KOMTUR_ACHSE.intersection(GEBIET.buffer(40)), fill="none", stroke="#c0504d", stroke_width="7")
    a(ST.SEITE_WEST, fill="none", stroke="#c0504d", stroke_width="3.5")
    a(E.STR["Sachsenhauser Straße"].intersection(GEBIET.buffer(40)), fill="none", stroke="#c0504d", stroke_width="3.5")
    a(E.STR["Germaniastraße"].intersection(TOR.buffer(25)), fill="none", stroke="#c0504d", stroke_width="3.5", stroke_dasharray="2 3")
    for k, l, b in WEGE:
        if k != "wohnweg":
            continue
        if b >= 9:
            a(l, fill="none", stroke="#7b6a55", stroke_width="1.8")
        else:
            a(l, fill="none", stroke="#7b6a55", stroke_width="1", stroke_dasharray="3 2")
    a(GA, fill="none", stroke="#3f88b0", stroke_width="4.5", stroke_opacity=".85")
    for b_ in (ST.BRUECKE_W, ST.BRUECKE_O, ST.HALLE):
        a(b_, fill="#cfe1bc" if b_ is not ST.HALLE else "#fff", stroke=INK, stroke_width=".8")
    # Mobilitätspunkte
    for s, p in [("Radstation 1.200", ST.RADSTATION.centroid), ("Quartiersgarage + Hub Nord", Point(391395, 5813900)),
                 ("Quartiersgarage + Hub Süd", Point(391470, 5813300))]:
        x, y = bl.xy(p.x, p.y)
        bl.o.append(f'<g transform="translate({x:.0f},{y:.0f})"><circle r="8" fill="#c0504d"/>'
                    f'<text y="3.5" font-size="9" font-weight="800" fill="#fff" text-anchor="middle">M</text></g>')
        bl.text(p.x + 14, p.y - 2, s, 7.5, INK, "start", 700)
    legende(bl, [("fill", "#e8e6e1", "öffentlich: Straßen, Plätze, Wege"), ("fill", "#cfe1bc", "öffentlich: Parks, Grünachse, Brücken"),
                 ("fill", "#f6e3c4", "halböffentlich: Gemeinschaftsgarten, Hof (tagsüber offen, Wegerecht)"),
                 ("fill", "#e9b77a", "privat: Vorgarten, Terrasse 3 m, Reihenhausgarten"),
                 ("line", "#c0504d", "Hauptachse Komturstraße · Seitenachsen 6,5 m befahrbar"),
                 ("line2", "#7b6a55", "Wohnweg 3,5 m befahrbar (Feuerwehr, Umzug, Müll)"),
                 ("dash", "#7b6a55", "Fußweg 3 m"), ("blau", "#3f88b0", "Grünachse 8 m: 4 m Weg + 4 m Regenmulde")],
            f'Feuerwehr: {G[var]["feuerwehr_ok"]} von {G[var]["feuerwehr_n"]} Häusern ≤ 50 m an befahrbarer Fläche · Innen autofrei, Parken in 2 Quartiersgaragen')
    kopf(bl, "Regelwerk Erschließung und Öffentlichkeit", f"Variante {var} · M 1:2000")
    return bl


def legende(bl, eintraege, fuss=""):
    x0, y0 = 14, bl.H - 26 - 17 * len(eintraege) - (20 if fuss else 0)
    o = [f'<g transform="translate({x0},{y0})"><rect x="-8" y="-16" width="{bl.W * 0.62:.0f}" height="{17 * len(eintraege) + 26 + (20 if fuss else 0)}" fill="#fff" opacity=".93"/>']
    for i, (art, f, t) in enumerate(eintraege):
        y = i * 17
        if art == "fill":
            o.append(f'<rect y="{y - 9}" width="22" height="11" fill="{f}" stroke="#999" stroke-width=".4"/>')
        elif art == "blau":
            o.append(f'<line x1="0" x2="22" y1="{y - 4}" y2="{y - 4}" stroke="{f}" stroke-width="4.5"/>')
        elif art == "dash":
            o.append(f'<line x1="0" x2="22" y1="{y - 4}" y2="{y - 4}" stroke="{f}" stroke-width="1" stroke-dasharray="3 2"/>')
        else:
            o.append(f'<line x1="0" x2="22" y1="{y - 4}" y2="{y - 4}" stroke="{f}" stroke-width="{5 if art == "line" else 1.8}"/>')
        o.append(f'<text x="30" y="{y}" font-size="9.5" fill="{INK}">{t}</text>')
    if fuss:
        o.append(f'<text x="0" y="{len(eintraege) * 17 + 6}" font-size="9" fill="#555">{fuss}</text>')
    bl.o.append("".join(o) + "</g>")


def kopf(bl, titel, unter):
    bl.o.append(f'<rect x="8" y="8" width="{max(len(titel) * 10.5, len(unter) * 6.5) + 24:.0f}" height="48" fill="#fff" opacity=".93"/>'
                f'<text x="20" y="30" font-size="17" font-weight="800" fill="{INK}">{titel}</text>'
                f'<text x="20" y="47" font-size="11" fill="#555">{unter}</text>')
    bl.o.append(f'<g transform="translate({bl.W - 28:.0f},40)"><path d="M0,-18 L8,7 L0,2 L-8,7z" fill="{INK}"/>'
                f'<text y="22" text-anchor="middle" font-size="11" fill="{INK}">N</text></g>')


# ------------------------------------------------------------------ Schnitte 1:500
def schnitt(name, a_, b_, var="A", titel="", zusatz=None):
    L = LineString([a_, b_])
    k = 2.0                                     # px pro m (1:500 bei 1 m = 2 mm -> width in mm)
    laenge = L.length
    W, H = laenge * k + 80, 60 * k + 90
    z0 = H - 60
    X = lambda s: 40 + s * k
    Z = lambda z: z0 - z * k
    o = [f'<rect width="{W:.0f}" height="{H:.0f}" fill="#fff"/>']

    def stuecke(g):
        q = L.intersection(g)
        out = []
        for p in getattr(q, "geoms", [q]):
            if p.is_empty or p.geom_type != "LineString":
                continue
            s0, s1 = sorted((L.project(Point(p.coords[0])), L.project(Point(p.coords[-1]))))
            out.append((s0, s1))
        return out
    # Boden: Flächenarten
    for g, f in [(GEBIET, "#efece5"), (unary_union([g for n, g in PARKS] + [ACHSE_EW]), "#cfe1bc"),
                 (FELD_U, "#f6e3c4"), (E.KOMTUR_ACHSE.buffer(11, cap_style=2), "#cfcbc3")]:
        for s0, s1 in stuecke(g):
            o.append(f'<rect x="{X(s0):.1f}" y="{z0:.1f}" width="{(s1 - s0) * k:.1f}" height="5" fill="{f}"/>')
    # Mulden / Retention: 0,6-1,0 m tief
    ret = unary_union([retention(g) for n, g in PARKS if n != "Stadtwald"] + [GA.parallel_offset(4.5, "left").buffer(1.6)])
    for s0, s1 in stuecke(ret):
        m = (s0 + s1) / 2
        o.append(f'<path d="M{X(s0):.1f},{z0:.1f} Q{X(m):.1f},{Z(-1.6):.1f} {X(s1):.1f},{z0:.1f}Z" fill="#9cc3d6"/>')
    o.append(f'<line x1="20" x2="{W - 20:.0f}" y1="{z0:.1f}" y2="{z0:.1f}" stroke="{INK}" stroke-width="1.4"/>')
    # Bäume (Profil)
    for p, r in PL.reihe_baeume(E.KOMTUR_ACHSE, 13, 7.5) + PL.reihe_baeume(E.KOMTUR_ACHSE, 13, -7.5) + \
            [(q, 3.2) for q in PL.BAEUME] + [x for n, g in PARKS for x in PL.baumraster(g.buffer(-3), 11, 0.45, seed=len(n) + int(g.area) % 97)]:
        if p.distance(L) < 4:
            s = L.project(p)
            o.append(f'<line x1="{X(s):.1f}" x2="{X(s):.1f}" y1="{z0:.1f}" y2="{Z(4):.1f}" stroke="#6f8a52" stroke-width="1.2"/>'
                     f'<ellipse cx="{X(s):.1f}" cy="{Z(9):.1f}" rx="{4.5 * k:.1f}" ry="{5.5 * k:.1f}" fill="#b5cb98" fill-opacity=".8" stroke="#6f8a52" stroke-width=".6"/>')
    # Gebäude: geschnitten (schwarz) und Ansicht dahinter (grau, bis 40 m)
    hs = [(shape(h["geo"]), hoehe(h["g"]), h["typ"]) for h in B[var]["haeuser"]] + [(g, hoehe(n), "bestand") for g, n in PL.KONTEXT]
    for g, h, typ in sorted(hs, key=lambda t: -t[0].distance(L)):
        if g.intersects(L):
            for s0, s1 in stuecke(g):
                o.append(f'<rect x="{X(s0):.1f}" y="{Z(h):.1f}" width="{(s1 - s0) * k:.1f}" height="{h * k:.1f}" fill="{"#1d1d1b" if typ != "bestand" else "#6d6b67"}"/>')
        elif g.distance(L) < 40:
            s = [L.project(Point(c)) for p_ in getattr(g, "geoms", [g]) for c in p_.exterior.coords]
            o.append(f'<rect x="{X(min(s)):.1f}" y="{Z(h):.1f}" width="{(max(s) - min(s)) * k:.1f}" height="{h * k:.1f}" '
                     f'fill="#fff" stroke="#9a9893" stroke-width=".6"/>')
    # Menschen
    for s in range(15, int(laenge), 37):
        o.append(f'<g transform="translate({X(s):.1f},{z0:.1f})"><circle cy="-15" r="1.6" fill="{INK}"/><rect x="-1.4" y="-13" width="2.8" height="7" rx="1.2" fill="{INK}"/>'
                 f'<rect x="-1.2" y="-6.5" width="2.4" height="6.5" fill="{INK}"/></g>')
    # Beschriftung der Räume unter der Geländelinie
    namen = [(n, P) for n, q, P in FELDER] + [(n, g) for n, g in PARKS] + [("Erholungsachse", ACHSE_EW),
             ("Komturstraße", E.KOMTUR_ACHSE.buffer(11, cap_style=2)), ("Grünachse", GA.buffer(4)), ("Bahnhofsplatz", PLATZ_VOR.union(ST.DECKEL)),
             ("Eingangsplatz", PLATZ_EIN), ("Germaniastraße", TOR), ("Ringbahn", ST.EINSCHNITT), ("A100", ST.A100_TROG), ("Feldbalkon", ST.FELDBALKON)]
    for n, g in namen:
        for s0, s1 in stuecke(g):
            if s1 - s0 > 5:
                o.append(f'<text x="{X((s0 + s1) / 2):.1f}" y="{z0 + 30:.1f}" font-size="8.5" text-anchor="middle" fill="#555">{n}</text>')
    if zusatz:
        o += zusatz(X, Z, L)
    o.append(f'<text x="24" y="26" font-size="15" font-weight="800" fill="{INK}">{titel}</text>'
             f'<text x="24" y="44" font-size="10.5" fill="#555">M 1:500 · Höhen: EG 4,2 m, OG 3,1 m · Ansicht dahinter grau</text>')
    for hz in (10, 20, 30, 40):
        o.append(f'<text x="8" y="{Z(hz) + 3:.1f}" font-size="8" fill="#999">+{hz}</text>'
                 f'<line x1="22" x2="30" y1="{Z(hz):.1f}" y2="{Z(hz):.1f}" stroke="#bbb"/>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W / k * 2:.0f}mm" height="{H / k * 2:.0f}mm" viewBox="0 0 {W:.0f} {H:.0f}" '
           f'font-family="{PL.SCHRIFT}">' + "".join(o) + "</svg>")
    p = os.path.join(OUT, name)
    open(p, "w").write(svg)
    return p, L


def bahnhof_zusatz(X, Z, L):
    """Einschnitt Ring (-7 m), A100-Trog (-7 m), Deckel, Stationsbrücke, Holzdach als Laterne."""
    o = []
    for g, tief, f in [(ST.EINSCHNITT, 7.5, "#d8d4cc"), (ST.A100_TROG, 7.0, "#d8d4cc")]:
        q = L.intersection(g)
        if q.is_empty:
            continue
        s0, s1 = sorted((L.project(Point(q.coords[0])), L.project(Point(q.coords[-1]))))
        o.append(f'<rect x="{X(s0):.1f}" y="{Z(0):.1f}" width="{(s1 - s0) * 2:.1f}" height="{tief * 2:.1f}" fill="{f}" stroke="{INK}" stroke-width=".8"/>')
    for g, z, d, f in [(ST.DECKEL, 0, 1.2, INK), (ST.HALLE, 0, 1.4, INK)]:
        q = L.intersection(g)
        if not q.is_empty:
            s0, s1 = sorted((L.project(Point(q.coords[0])), L.project(Point(q.coords[-1]))))
            o.append(f'<rect x="{X(s0):.1f}" y="{Z(z):.1f}" width="{(s1 - s0) * 2:.1f}" height="{d * 2:.1f}" fill="{f}"/>')
    q = L.intersection(ST.DACH)
    if not q.is_empty:
        s0, s1 = sorted((L.project(Point(q.coords[0])), L.project(Point(q.coords[-1]))))
        m = (s0 + s1) / 2
        o.append(f'<path d="M{X(s0):.1f},{Z(6):.1f} Q{X(m):.1f},{Z(26):.1f} {X(s1):.1f},{Z(6):.1f}" fill="none" stroke="{INK}" stroke-width="2.2"/>')
        for t in range(1, 9):
            xs = X(s0) + (X(s1) - X(s0)) * t / 9
            o.append(f'<line x1="{xs:.1f}" x2="{xs:.1f}" y1="{Z(0):.1f}" y2="{Z(6 + 12 * math.sin(math.pi * t / 9)):.1f}" stroke="#777" stroke-width=".5"/>')
        o.append(f'<text x="{X(m):.1f}" y="{Z(20):.1f}" font-size="9" text-anchor="middle" fill="{INK}" font-weight="700">Holz-Diagrid, First 18 m</text>')
        o.append(f'<rect x="{X(m) - 76:.1f}" y="{Z(-7.5) - 4:.1f}" width="152" height="4" fill="#9a968d"/>'
                 f'<text x="{X(m):.1f}" y="{Z(-7.5) + 10:.1f}" font-size="8" text-anchor="middle" fill="#555">Bahnsteig −7,5 m</text>')
    return o


# ------------------------------------------------------------------ Piktogramme
def pikto(titel, farbe_von, legende_):
    bl = Blatt(BB, 6000, 0.42)
    bl.o.append(f'<rect width="{bl.W:.0f}" height="{bl.H:.0f}" fill="#fff"/>')
    bl.path(unary_union([g for n, g in PARKS]), fill="#e3eddb")
    bl.path(FELD_U, fill="#f3f1ec")
    for h in B["A"]["haeuser"]:
        bl.path(shape(h["geo"]), fill=farbe_von(h))
    bl.o.append(f'<text x="6" y="16" font-size="13" font-weight="800" fill="{INK}">{titel}</text>')
    for i, (f, t) in enumerate(legende_):
        bl.o.append(f'<rect x="6" y="{bl.H - 14 - 13 * (len(legende_) - i)}" width="10" height="9" fill="{f}"/>'
                    f'<text x="20" y="{bl.H - 6 - 13 * (len(legende_) - i)}" font-size="9" fill="{INK}">{t}</text>')
    return bl


def piktogramme():
    gfz = {}
    for name, q, P in FELDER:
        hs = [h for h in B["A"]["haeuser"] if h["feld"] == name]
        gfz[name] = sum(shape(h["geo"]).area * h["g"] for h in hs) / P.area
    rampe = lambda t, a, b: "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
    cl = lambda v, s: min(1, v / s)
    geschoss = lambda g: "#d9d4c7" if g <= 2 else "#b9a98a" if g <= 3 else "#97835f" if g <= 4 else "#76603d" if g <= 6 else "#4e3d22" if g <= 9 else "#1d1d1b"
    mat = {"A": "#b86b4b", "1": "#8c8c8c", "2": "#d9b48f", "3": "#c4a06a", "4": "#a3b86b", "5": "#c98d5c"}
    bilder = [
        ("Dichte (GFZ je Baufeld)", lambda h: rampe(cl(gfz[h["feld"]], 4.0), (240, 220, 180), (150, 40, 30)),
         [("#f0dcb4", "GFZ &lt; 1"), ("#d28a62", "GFZ 2"), ("#962820", "GFZ ≥ 4")]),
        ("Geschossigkeit", lambda h: geschoss(h["g"]),
         [("#d9d4c7", "I–II"), ("#b9a98a", "III"), ("#97835f", "IV"), ("#76603d", "V–VI"), ("#4e3d22", "VII–IX"), ("#1d1d1b", "XIV")]),
        ("Höhe", lambda h: rampe(cl(hoehe(h["g"]), 45), (230, 235, 240), (30, 60, 110)),
         [("#e6ebf0", "bis 10 m"), ("#8ea0b7", "ca. 20 m"), ("#1e3c6e", "45 m Hochpunkt")]),
        ("Material", lambda h: mat[h["quartier"]],
         [(mat["A"], "A Klinker + Holzdach"), (mat["1"], "Q1 Beton, Metall, Glas"), (mat["2"], "Q2 Putz + Holz"), (mat["3"], "Q3 Holz"),
          (mat["4"], "Q4 Holz + Glashaus"), (mat["5"], "Q5 Ziegel + Holz")]),
        ("Quartiere", lambda h: QF[h["quartier"]], [(QF[q], n) for q, n in PL.QNAME.items()]),
    ]
    pfade = []
    for i, (t, f, lg) in enumerate(bilder):
        pfade.append(speichere(pikto(t, f, lg), f"pikto_{i + 1}.svg"))
    return pfade


if __name__ == "__main__":
    for v in "AB":
        print(speichere(regelwerk(v), f"regelwerk_{v}_2000.svg"))
    # Schnitte: A-A quer über die Komturstraße (Q1/Q4), B-B Bahnhof -> Eingangsplatz, C-C Q3 Wohnweg + Retention
    print(schnitt("schnitt_AA_500.svg", (391040, 5813650), (391520, 5813650), titel="Schnitt A–A · Q1 Gewerbehof – Grünachse – Komturstraße – Q4 Gartenhof")[0])
    print(schnitt("schnitt_BB_500.svg", ST.w(-20, 60), ST.w(-20, -260), titel="Schnitt B–B · Feldbalkon – Station – Bahnhofsplatz – Germaniastraße – Eingangsplatz",
                  zusatz=bahnhof_zusatz)[0])
    print(schnitt("schnitt_CC_500.svg", (391150, 5813250), (391150, 5813520), titel="Schnitt C–C · Stadtwald – Q3 Reihenhäuser – Erholungsachse – Q2")[0])
    print(piktogramme())
