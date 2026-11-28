"""
Typologie-Katalog „Fünf Quartiere“ (neuer Plan: Ankunft A, Quartiere 1–5, Stadtwald).
Eine Datenquelle -> Axonometrien (SVG), Straßenquerschnitte (SVG), Wasserkette (SVG),
DXF-Bibliothek für Vectorworks (Grundrisse 1:1 in Metern) und Seite (index.html).
Aufruf: python3 katalog.py
"""
import json, math, os, html
import ezdxf

HIER = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HIER, "out")
os.makedirs(OUT, exist_ok=True)
EG, OG = 4.5, 3.2                      # EG-Höhe publikumsnah, Regelgeschoss

FARBE = dict(wohnen="#f4efe3", publikum="#e8875b", gewerbe="#c9a27a", bildung="#8f7cc9", gemein="#e6b84d",
             kultur="#d9739b", bestand="#b8b3aa", glas="#bfe0ea", dach="#9cc27a", holz="#b98a59")
NAME = dict(wohnen="Wohnen", publikum="Läden, Gastro, Hub", gewerbe="Gewerbe, Werkstatt", bildung="Schule, Kita",
            gemein="Gemeinschaft", kultur="Kultur, Freizeit", bestand="Bestand", glas="Gewächshaus")

# ---------- Bausteine je Quartier ----------
# box: (x, y, breite, tiefe, geschosse, nutzung, z0_geschosse)  Maße in m, Ursprung Feld-Ecke
# fl:  Freiflächen (art, polygon) · baum: (x, y, r) · wasser: polygon
Q = [
 dict(id="A", name="Ankunft an der S-Bahn", farbe="#d7562b", publikum=5, hoehe="6–14 G", verkehr="ÖPNV, Hub, Lieferung",
      versorgung="Ankommen und Umsteigen: Mobilitätshub, Lebensmittel, Gastro, Dienstleistung",
      gruen="Stein und Schatten: Baumdach auf dem Ankunftsplatz, Regendach",
      wasser="Quelle: Das Regendach der Station speist eine Kaskade zum Ankunftsplatz",
      typen=[("Stationsbrücke mit Holzdach", "Brücke ca. 25 × 120 m über Ring und A100, Holzdach als Landmarke, Feldbalkon zum Tempelhofer Feld",
              "Landmarke wie Køge Nord oder Assen; macht aus der Barriere einen Ort"),
             ("Ankunftshaus mit Hochpunkt", "Sockel 2 G (60 × 32 m), darauf Riegel 6 G (13 m tief), Hochpunkt 22 × 22 m, 12–14 G",
              "Ein Hochpunkt markiert die Station im Stadtbild, der Sockel trägt Markthalle und Fahrradparkhaus"),
             ("Mobilitätshub unter der Brücke", "1–2 Ebenen, ca. 1.000 Fahrräder, Carsharing, Lastenräder",
              "Wie Stationsplein Utrecht: Rad und Bahn ohne Umweg")],
      ref="Køge Nord (COBE), Assen Station, Ede-Wageningen, Fahrradparkhaus Utrecht",
      boxes=[(0, 0, 60, 32, 2, "publikum", 0), (0, 0, 36, 13, 6, "wohnen", 2), (38, 0, 22, 22, 12, "publikum", 2)],
      dach=dict(x=8, y=44, w=52, d=30, z=9.0), wfl=[[(14, 46), (54, 46), (54, 50), (14, 50)]],
      baeume=[(x, y, 3.2) for x in range(70, 92, 8) for y in range(40, 75, 8)], platz=[(0, 36, 95, 42)]),
 dict(id="1", name="Quartier 1 · Versorgen und Lernen", farbe="#e8875b", publikum=4, hoehe="5–7 G", verkehr="Quartiersstraße, Tempo 20, Lieferzonen",
      versorgung="Täglicher Bedarf, Arbeit, Bildung: Supermarkt, Läden, Gewerbehof, Grundschule, Kita",
      gruen="Aktiv und robust: Schulhof, der nachmittags offen ist, Sport, Spiel, Baumhain",
      wasser="Wasserplatz: ein abgesenkter Sport- und Spielplatz, der bei Starkregen kurz volläuft",
      typen=[("Hybridriegel mit Gewerbesockel", "Sockel 1–2 G, 20–22 m tief (Supermarkt bis 1.500 m²), darauf Riegel 13 m, 5 G, Gründach-Terrasse auf dem Sockel",
              "Große Erdgeschosse an der Achse, Wohnen darüber, die Kante bleibt offen zum Park"),
             ("Gewerbehof (Stapelgewerbe)", "L-Form, 18–22 m tief, 3–4 G mit 4,5 m Geschosshöhe, Lastenaufzug, Ladehof zur Seitenachse",
              "Handwerk bleibt im Quartier, wie die Malzfabrik oder die Gewerbehallen am Teltowkanal"),
             ("Kinderhaus / Bildungshaus", "2–3 G, 25 × 15 m (Kita) bzw. Schule mit Dachsportfeld, Garten 7 m² je Kind",
              "Schule und Kita gehören zum publikumsstarken Norden, kurze Wege von der S-Bahn")],
      ref="Benthemplein Rotterdam (Wasserplatz), Malzfabrik Berlin, Prinz-Eugen-Park (Läden am Quartiersplatz)",
      boxes=[(0, 0, 72, 22, 2, "publikum", 0), (0, 0, 72, 13, 5, "wohnen", 2), (0, 46, 20, 34, 4, "gewerbe", 0),
             (20, 62, 30, 18, 4, "gewerbe", 0), (64, 56, 26, 15, 2, "bildung", 0)],
      wfl=[[(40, 30), (82, 30), (82, 46), (40, 46)]], baeume=[(28, 36, 3), (30, 50, 3.2), (88, 36, 3), (58, 76, 3)],
      platz=[(36, 26, 52, 24)]),
 dict(id="2", name="Quartier 2 · Treffen am Hauptplatz", farbe="#8a5cc2", publikum=3, hoehe="4–6 G", verkehr="Fahrradstraße, Anlieger frei",
      versorgung="Gemeinschaft und Austausch: Quartiershaus, Café, Markt, Bibliothek der Dinge, Ärztehaus",
      gruen="Hauptgrünplatz: ein Platz mit Rand für Cafés und Markt, in der Mitte Wiese, Hain und Wasser",
      wasser="Retentionsmulde als Amphitheater: meist trocken und Sitzstufen, nach Regen ein flacher See",
      typen=[("Platzhaus (Quartiershaus)", "3 G, ca. 30 × 18 m, rundum offen: Café, Werkstatt, Bibliothek der Dinge, Gästewohnungen, Dachterrasse",
              "Das Herz wie der CYC-Hub im ecovillage Hannover"),
             ("Cluster aus Stadtvillen", "3–4 Punkthäuser 18 × 18 m, 5 G, um einen gemeinsamen Garten, zu zwei Seiten offen",
              "Nachbarschaft ohne geschlossenen Hof, Blicke und Wege zum Platz"),
             ("Wohnen mit Arbeiten am Platzrand", "Zeile 12–13 m tief, 4–5 G, EG 4,5 m hoch mit Ateliers, Praxen, Café",
              "Der Platz bekommt eine belebte Kante, aber kein Einkaufszentrum")],
      ref="ecovillage Hannover (cityförster), Prinz-Eugen-Park München, Tåsinge Plads Kopenhagen",
      boxes=[(4, 4, 30, 18, 3, "gemein", 0), (62, 0, 18, 18, 5, "wohnen", 0), (84, 22, 18, 18, 5, "wohnen", 0),
             (62, 44, 18, 18, 5, "wohnen", 0), (0, 70, 46, 13, 1, "publikum", 0), (0, 70, 46, 13, 4, "wohnen", 1)],
      wfl=[[(14, 36), (24, 30), (38, 32), (44, 42), (36, 52), (20, 52), (12, 46)]],
      baeume=[(6, 32, 3.5), (48, 30, 3.5), (52, 52, 3.3), (8, 58, 3.4), (28, 60, 3.2)], platz=[(0, 26, 56, 40)]),
 dict(id="3", name="Quartier 3 · Wohnen am Stadtwald", farbe="#e5a13a", publikum=1, hoehe="2–4 G", verkehr="Wohnweg, autofrei bis auf Rettung und Umzug",
      versorgung="Ruhe und Natur: Waldkita, Gemeinschaftsgärten, kleine Nachbarschaftsläden",
      gruen="Wald und Wiese: der Stadtwald im Dreieck, Lichtungen, Totholz, Wildstaudenwiesen",
      wasser="Waldtümpel und Feuchtwiese: das Wasser bleibt im Wald und kühlt",
      typen=[("Gestaffelte Zeile", "12–13 m tief, von 4 G auf 2 G zum Wald abgetreppt, Dachterrassen",
              "Der Übergang Wohnen–Wald wird in der Höhe ablesbar"),
             ("Reihen- und Stadthäuser", "6,5 m breit, 11 m tief, 3 G, Gärten nach Süden, Gruppen von 5–6 Häusern, Baugruppen und Holzbau",
              "Familien und kleine Körnung, wie im Prinz-Eugen-Park"),
             ("Punkthäuser am Waldrand", "16 × 16 m, 4 G, Holzbau, frei zwischen den Bäumen",
              "Wohnen im Wald, der Waldrand bleibt durchlässig (Rieselfeld: Rand zum Naturschutzgebiet)")],
      ref="Prinz-Eugen-Park München (Holzbau), Rieselfeld Freiburg (Rand zur Natur), ecovillage Hannover",
      boxes=[(0, 0, 13, 40, 4, "wohnen", 0), (0, 40, 13, 14, 3, "wohnen", 0), (0, 54, 13, 12, 2, "wohnen", 0)]
            + [(24 + i * 6.5, 0, 6.5, 11, 3, "wohnen", 0) for i in range(5)] + [(24 + i * 6.5, 26, 6.5, 11, 3, "wohnen", 0) for i in range(5)]
            + [(66, 4, 16, 16, 4, "wohnen", 0), (72, 40, 16, 16, 4, "wohnen", 0), (40, 66, 14, 9, 1, "bildung", 0)],
      wfl=[[(60, 70), (72, 66), (82, 72), (76, 82), (62, 80)]],
      baeume=[(x, y, 3.3) for x, y in [(60, 30), (90, 22), (58, 52), (92, 60), (30, 52), (44, 54), (20, 76), (32, 86), (52, 88), (88, 84),
                                        (96, 74), (10, 86), (66, 90), (80, 94), (100, 90)]], platz=[]),
 dict(id="4", name="Quartier 4 · Gartenwerk (Vorschlag)", farbe="#c9b632", publikum=3, hoehe="4–6 G", verkehr="Fahrradstraße, Anlieger frei",
      versorgung="Lebensmittel: Gemeinschaftsgärten, Dachgewächshäuser, Verarbeitung, Food-Lab, liefert an die Markthalle am Kanal",
      gruen="Produktiv: Obstwiese, Beete, Gewächshäuser, das Erbe der Kleingärten",
      wasser="Gießteich und Zisternen: Regen von den Dächern wird gesammelt und zum Gießen genutzt",
      typen=[("Riegel mit Dachgewächshaus", "13 m tief, 5 G, auf dem Dach Gewächshaus 1 G (Gemüse, Aquaponik)",
              "Versorgung wird sichtbar; die Abwärme der Wohnungen heizt das Gewächshaus"),
             ("Offener Gartenhof, gespiegelt", "U-Form 4–5 G, öffnet sich nach Norden zum Hof der Bestandsbebauung, so entsteht ein Doppelhof",
              "Greift die Form des Nachbarn auf und verbindet beide Höfe"),
             ("Gartenhalle", "1–2 G, ca. 30 × 20 m an der Achse: Verarbeitung, Food-Lab, Gartengeräte, Hofladen",
              "Publikum ja, aber tagsüber und im kleinen Maßstab")],
      ref="Food Campus Berlin (Tempelhof), ecovillage Hannover (Allmende), Prinz-Eugen-Park (Gemeinschaftsgärten)",
      boxes=[(0, 0, 50, 13, 5, "wohnen", 0), (0, 0, 50, 13, 1, "glas", 5), (62, 30, 13, 40, 5, "wohnen", 0), (75, 30, 22, 13, 4, "wohnen", 0),
             (75, 57, 22, 13, 4, "wohnen", 0), (0, 56, 30, 20, 2, "gewerbe", 0)],
      wfl=[[(40, 44), (52, 40), (58, 48), (50, 56), (40, 54)]],
      baeume=[(x, y, 2.6) for x in (10, 20, 30) for y in (24, 34, 44)], platz=[], beete=[(80 + 0, 45, 14, 2), (80, 49, 14, 2), (80, 53, 14, 2), (36, 22, 18, 2), (36, 26, 18, 2)]),
 dict(id="5", name="Quartier 5 · Am Wasser", farbe="#3d8fc9", publikum=3, hoehe="2–4 G", verkehr="Fuß, Rad, Boot",
      versorgung="Wasser und Freizeit: Bootshaus, Badestelle, Umweltbildung, Markthalle am Platz",
      gruen="Ufer und Wasser: Stege, Flachwasserzone, Schilf, Uferweg (Phase 1 als Zwischennutzung)",
      wasser="Mündung: ein Schilfgarten reinigt das Wasser, bevor es in den Kanal fließt; Phase 3 Baden im Kanal",
      typen=[("Wasserhaus (öffentliches Baufeld)", "2–3 G, ca. 25 × 15 m, halb über dem Wasser: Bootshaus, Badehaus, Café, Umweltbildung, Dach als Aussicht",
              "Öffentlicher Zugang zum Kanal, Gegenstück zur S-Bahn-Brücke"),
             ("Bestand umnutzen", "Das erhaltene Gebäude wird Werkstatt, Kultur oder Markthalle (wie ufaFabrik)",
              "Graue Energie bleibt, Identität bleibt"),
             ("Kran als Landmarke", "Der Kran bleibt: Aussichtsplattform, Kranbar oder Lichtzeichen",
              "Zweite Landmarke am Südende der Achse, Gegenpol zur Station")],
      ref="ufaFabrik Berlin, Badeschiff Berlin, Flussbad Berlin",
      boxes=[(0, 10, 40, 25, 3, "bestand", 0), (54, 44, 25, 15, 2, "kultur", 0)],
      wfl=[[(-6, 60), (106, 60), (106, 92), (-6, 92)]], kanal=True,
      baeume=[(8, 46, 3), (20, 50, 3), (44, 8, 3.2), (90, 20, 3)], platz=[(0, 38, 50, 20)], kran=(90, 50)),
]

# ---------- Isometrie ----------
C, S_ = math.cos(math.radians(30)), math.sin(math.radians(30))
M = 3.2   # px je m


def iso(x, y, z=0.0):
    return ((x - y) * C * M, (x + y) * S_ * M - z * M)


def poly(pts, fill, stroke="#4a4238", sw=0.7, op=1.0):
    d = " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
    return f'<polygon points="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{op}" stroke-linejoin="round"/>'


def hell(hex_, f):
    r, g, b = (int(hex_[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(c * f))) for c in (r, g, b))


def axo(q):
    els = []
    # Boden
    els.append(poly([iso(-6, -6), iso(106, -6), iso(106, 96), iso(-6, 96)], "#e7efd9", "#b9c7a6", 0.8))
    for x, y, w, d in q.get("platz", []):
        els.append(poly([iso(x, y), iso(x + w, y), iso(x + w, y + d), iso(x, y + d)], "#efe3cf", "none"))
    for w in q.get("wfl", []):
        els.append(poly([iso(*p) for p in w], "#7fc0e0" if not q.get("kanal") else "#5aa6d6", "#4a8fb8", 0.8))
    for x, y, w, d in q.get("beete", []):
        els.append(poly([iso(x, y), iso(x + w, y), iso(x + w, y + d), iso(x, y + d)], "#7aa24a", "none"))
    # Körper + Bäume gemeinsam nach Tiefe sortieren
    obj = []
    for b in q["boxes"]:
        x, y, w, d, g, n, z0 = b
        tiefe = x + w + y + d
        if z0:                       # aufgesetzte Körper direkt nach ihrem Sockel zeichnen
            basis = [c for c in q["boxes"] if not c[6] and c[0] <= x + 0.1 and c[1] <= y + 0.1
                     and c[0] + c[2] >= x + w - 0.1 and c[1] + c[3] >= y + d - 0.1]
            if basis:
                tiefe = basis[0][0] + basis[0][2] + basis[0][1] + basis[0][3] + 0.01 * z0
        obj.append((tiefe, "box", b))
    for t in q.get("baeume", []):
        obj.append((t[0] + t[1] + 1, "baum", t))
    if q.get("kran"):
        obj.append((q["kran"][0] + q["kran"][1], "kran", q["kran"]))
    for _, art, o in sorted(obj, key=lambda t: t[0]):
        if art == "box":
            x, y, w, d, g, n, z0 = o
            z0m = 0 if z0 == 0 else EG + (z0 - 1) * OG
            h = (EG + (g - 1) * OG) if z0 == 0 else g * OG
            if n == "glas":
                h = 3.5
            z1 = z0m + h
            f = FARBE[n]
            els.append(poly([iso(x + w, y, z0m), iso(x + w, y + d, z0m), iso(x + w, y + d, z1), iso(x + w, y, z1)], hell(f, 0.82)))
            els.append(poly([iso(x, y + d, z0m), iso(x + w, y + d, z0m), iso(x + w, y + d, z1), iso(x, y + d, z1)], hell(f, 0.92)))
            els.append(poly([iso(x, y, z1), iso(x + w, y, z1), iso(x + w, y + d, z1), iso(x, y + d, z1)],
                            FARBE["dach"] if n not in ("glas", "publikum", "gewerbe", "bestand") else hell(f, 1.04)))
            # Geschosslinien auf den sichtbaren Fassaden
            zz = z0m + (EG if z0 == 0 else OG)
            while zz < z1 - 0.5 and n != "glas":
                a, b_, c = iso(x + w, y, zz), iso(x + w, y + d, zz), iso(x, y + d, zz)
                els.append(f'<polyline points="{a[0]:.1f},{a[1]:.1f} {b_[0]:.1f},{b_[1]:.1f} {c[0]:.1f},{c[1]:.1f}" fill="none" stroke="#4a4238" stroke-width="0.3" opacity=".55"/>')
                zz += OG
        elif art == "baum":
            x, y, r = o
            bx, by = iso(x, y, 0)
            tx, ty = iso(x, y, 7)
            els.append(f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" stroke="#6b5a48" stroke-width="1.2"/>')
            els.append(f'<ellipse cx="{tx:.1f}" cy="{ty - r * M * 0.5:.1f}" rx="{r * M:.1f}" ry="{r * M * 0.85:.1f}" fill="#7fb05d" stroke="#4f7a3a" stroke-width="0.7" opacity=".93"/>')
        elif art == "kran":
            x, y = o
            els.append(poly([iso(x - 3, y - 3, 1), iso(x + 3, y - 3, 1), iso(x + 3, y + 3, 1), iso(x - 3, y + 3, 1)], "#9a9a9a"))
            a, b_ = iso(x, y, 0), iso(x, y, 28)
            c = iso(x - 26, y + 6, 28)
            els.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b_[0]:.1f}" y2="{b_[1]:.1f}" stroke="#c0392b" stroke-width="2.4"/>'
                       f'<line x1="{b_[0]:.1f}" y1="{b_[1]:.1f}" x2="{c[0]:.1f}" y2="{c[1]:.1f}" stroke="#c0392b" stroke-width="2"/>')
    # Regendach (Landmarke) obenauf
    if q.get("dach"):
        dd = q["dach"]
        x, y, w, d, z = dd["x"], dd["y"], dd["w"], dd["d"], dd["z"]
        for cx in (x + 4, x + w - 4):
            for cy in (y + 4, y + d - 4):
                a, b_ = iso(cx, cy, 0), iso(cx, cy, z)
                els.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b_[0]:.1f}" y2="{b_[1]:.1f}" stroke="#7a5a3a" stroke-width="1.6"/>')
        els.append(poly([iso(x, y, z), iso(x + w, y, z), iso(x + w, y + d, z), iso(x, y + d, z)], FARBE["holz"], "#6b4a2a", 1, 0.88))
    xs = [float(v) for e in els for v in __import__("re").findall(r'(-?\d+\.\d),(-?\d+\.\d)', e) for v in [v[0]]]
    ys = [float(v[1]) for e in els for v in __import__("re").findall(r'(-?\d+\.\d),(-?\d+\.\d)', e)]
    x0, x1, y0, y1 = min(xs) - 10, max(xs) + 10, min(ys) - 30, max(ys) + 10
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.0f} {y0:.0f} {x1 - x0:.0f} {y1 - y0:.0f}" role="img" aria-label="Axonometrie {html.escape(q["name"])}">' + "".join(els) + "</svg>"


# ---------- Straßenquerschnitte ----------
def schnitt(titel, teile, links_g, rechts_g, nutz_eg="publikum"):
    """teile: [(breite_m, art, label)] von links nach rechts; Häuser links/rechts mit Geschossen."""
    s = 9.0
    gesamt = sum(t[0] for t in teile)
    haus = 14
    W = (32.5 + 2 * haus) * s + 40          # alle Schnitte im selben Maßstab, Breite der Hauptachse
    links = (W - (gesamt + 2 * haus) * s) / 2
    boden = 300
    o = [f'<rect width="{W:.0f}" height="380" fill="#fff"/>']
    farben = dict(geh="#ddd6ca", fahr="#9a9ea3", rad="#5fa684", gruen="#8fbf63", baum="#8fbf63", mulde="#7fc0e0", weg="#e9dfc9", wiese="#b5d58f", stauden="#c3a6d8")
    x = links + haus * s
    for gl, (hg, seite) in enumerate(((links_g, 0), (rechts_g, 1))):
        hx = links if seite == 0 else x + gesamt * s
        if hg:
            h = (EG + (hg - 1) * OG) * s
            o.append(f'<rect x="{hx:.1f}" y="{boden - h:.1f}" width="{haus * s:.1f}" height="{h:.1f}" fill="{FARBE["wohnen"]}" stroke="#4a4238"/>')
            o.append(f'<rect x="{hx:.1f}" y="{boden - EG * s:.1f}" width="{haus * s:.1f}" height="{EG * s:.1f}" fill="{FARBE[nutz_eg]}" stroke="#4a4238"/>')
            zz = EG
            while zz < EG + (hg - 1) * OG - 0.1:
                o.append(f'<line x1="{hx:.1f}" x2="{hx + haus * s:.1f}" y1="{boden - zz * s:.1f}" y2="{boden - zz * s:.1f}" stroke="#4a4238" stroke-width=".5"/>')
                zz += OG
            o.append(f'<text x="{hx + haus * s / 2:.1f}" y="{boden - h - 8:.1f}" text-anchor="middle" font-size="13" font-weight="700">{hg} G</text>')
    for i_, (b, art, lab) in enumerate(teile):
        o.append(f'<rect x="{x:.1f}" y="{boden - (6 if art in ("gruen", "baum", "stauden", "wiese") else 0):.1f}" width="{b * s:.1f}" height="{8 if art != "mulde" else 12}" fill="{farben[art]}"/>')
        if art == "baum":
            cx = x + b * s / 2
            o.append(f'<line x1="{cx:.1f}" x2="{cx:.1f}" y1="{boden:.1f}" y2="{boden - 60:.1f}" stroke="#6b5a48" stroke-width="2"/>'
                     f'<circle cx="{cx:.1f}" cy="{boden - 82:.1f}" r="32" fill="#7fb05d" opacity=".9"/>')
        if art == "stauden":
            for k in range(int(b * 2)):
                cx = x + (k + 0.5) * s / 2
                o.append(f'<circle cx="{cx:.1f}" cy="{boden - 10:.1f}" r="3.2" fill="{["#a678c9", "#e58ab0", "#f2efe6", "#e8c547"][k % 4]}"/>')
        o.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{boden + 14}" y2="{boden + 22}" stroke="#333"/>')
        zy = boden + 52 + (i_ % (3 if len(teile) > 6 else 2)) * 13
        o.append(f'<text x="{x + b * s / 2:.1f}" y="{boden + 36}" text-anchor="middle" font-size="11.5" font-weight="700">{str(b).replace(".", ",")}</text>'
                 f'<line x1="{x + b * s / 2:.1f}" x2="{x + b * s / 2:.1f}" y1="{boden + 40}" y2="{zy - 10}" stroke="#bbb" stroke-width=".6"/>'
                 f'<text x="{x + b * s / 2:.1f}" y="{zy}" text-anchor="middle" font-size="10" fill="#555">{lab}</text>')
        x += b * s
    o.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{boden + 14}" y2="{boden + 22}" stroke="#333"/>')
    o.append(f'<line x1="10" x2="{W - 10:.0f}" y1="{boden + 8}" y2="{boden + 8}" stroke="#222" stroke-width="1.6"/>')
    o.append(f'<text x="20" y="26" font-size="14" font-weight="800">{titel}</text>'
             f'<text x="20" y="46" font-size="12" fill="#555">Gesamtbreite {str(round(gesamt, 1)).replace(".", ",")} m zwischen den Häusern</text>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} 390" font-family="Archivo, Arial, sans-serif" role="img" aria-label="{titel}">' + "".join(o) + "</svg>"


SCHNITTE = [
    ("Hauptachse Komturstraße: Einkaufsstraße", [(6, "geh", "Gehweg + Auslage"), (2.5, "baum", "Baum + Rigole"), (3.25, "fahr", "Fahrspur"),
     (2.5, "stauden", "Pflanzstreifen"), (4, "rad", "Radweg 2-Richt."), (2.5, "stauden", "Pflanzstreifen"), (3.25, "fahr", "Fahrspur"),
     (2.5, "baum", "Baum + Liefern"), (6, "geh", "Gehweg + Auslage")], 7, 7),
    ("Seitenachse Nord (Quartier 1, A): Quartiersstraße, Tempo 20", [(3, "geh", "Gehweg"), (2.5, "baum", "Baum + Rigole"), (6, "fahr", "Fahrbahn"),
     (2.5, "mulde", "Mulde / Liefern"), (3, "geh", "Gehweg")], 6, 5),
    ("Seitenachse Mitte (Quartier 2, 4): Fahrradstraße, Anlieger frei", [(2.5, "geh", "Gehweg"), (3, "mulde", "Retentionsmulde"), (5, "rad", "Fahrradstraße"),
     (2.5, "baum", "Baumreihe"), (2.5, "geh", "Gehweg")], 5, 4, "wohnen"),
    ("Seitenachse Süd (Quartier 3, 5): Wohnweg, autofrei", [(1.5, "wiese", "Vorgarten"), (3.5, "weg", "Weg (Rettung)"), (4, "mulde", "Mulde + Stauden"),
     (1.5, "wiese", "Vorgarten")], 3, 3, "wohnen"),
    ("Weg zwischen Baufeldern: 6 m Weg + Vorgärten", [(2.5, "wiese", "Vorgarten"), (3.5, "weg", "Weg (Rettung)"), (2.5, "mulde", "Mulde"),
     (2.5, "wiese", "Vorgarten")], 4, 4, "wohnen"),
    ("Erholungsachse (Ost–West): Flanieren", [(4, "stauden", "Staudenband"), (3.5, "weg", "Flanierweg"), (3, "mulde", "Bioswale"),
     (6, "wiese", "Wiese + Baumgruppen"), (2.5, "weg", "Spielweg"), (4, "stauden", "Staudenband")], 4, 4, "wohnen"),
]

WASSERKETTE = [("A", "Quelle", "Regendach der Station, Kaskade auf den Ankunftsplatz"),
               ("1", "Wasserplatz", "abgesenkter Sport- und Spielplatz, läuft bei Starkregen voll"),
               ("2", "Amphitheater-Mulde", "Sitzstufen am Hauptplatz, nach Regen ein flacher See"),
               ("4", "Gießteich", "sammelt Dachwasser zum Gießen der Gärten"),
               ("·", "Regengärten", "in den Pocket-Parks zwischen den Baufeldern und in den Seitenachsen"),
               ("3", "Waldtümpel", "Feuchtwiese im Stadtwald, das Wasser bleibt und kühlt"),
               ("5", "Mündung", "Schilfgarten reinigt, dann in den Kanal")]


def wasserkette():
    w, o = 150, []
    for i, (q, t, txt) in enumerate(WASSERKETTE):
        x = 20 + i * w
        r = 18 + (i % 3) * 4
        o.append(f'<circle cx="{x + 60:.0f}" cy="70" r="{r}" fill="#7fc0e0" stroke="#3d8fc9" stroke-width="2"/>')
        o.append(f'<text x="{x + 60:.0f}" y="75" text-anchor="middle" font-size="13" font-weight="800" fill="#123">{q}</text>')
        if i < len(WASSERKETTE) - 1:
            o.append(f'<path d="M{x + 60 + r + 6},70 Q{x + 60 + w / 2},50 {x + 60 + w - 26},70" fill="none" stroke="#3d8fc9" stroke-width="2" stroke-dasharray="5 5"/>')
        o.append(f'<text x="{x + 60:.0f}" y="118" text-anchor="middle" font-size="13" font-weight="700">{t}</text>')
    o.append('<text x="20" y="22" font-size="12" fill="#555">S-Bahn (Norden)</text>')
    o.append(f'<text x="{20 + len(WASSERKETTE) * w - 20:.0f}" y="22" font-size="12" fill="#555" text-anchor="end">Teltowkanal (Süden)</text>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {40 + len(WASSERKETTE) * w:.0f} 135" font-family="Archivo, Arial, sans-serif" role="img" aria-label="Wasserkette">' + "".join(o) + "</svg>"


def verlauf():
    """Fade von Nord nach Süd: Publikum, Höhe, Verkehr, Grün."""
    reihen = [("A", 5, 14, 5, 1), ("1", 4, 7, 4, 2), ("2", 3, 6, 3, 3), ("4", 3, 6, 3, 3), ("3", 1, 4, 1, 5), ("5", 3, 4, 1, 4)]
    cols = [("Publikum", "#e8875b", 1), ("Höhe (G max.)", "#8f7cc9", 2), ("Autoverkehr", "#8c8f93", 3), ("Grün", "#7fb05d", 4)]
    o = []
    for j, (lab, f, k) in enumerate(cols):
        o.append(f'<text x="{110 + j * 150}" y="20" font-size="12" font-weight="700">{lab}</text>')
    for i, r in enumerate(reihen):
        q = next(x for x in Q if x["id"] == r[0])
        y = 36 + i * 30
        kurz = dict(A="Ankunft", **{"1": "Versorgen", "2": "Hauptplatz", "4": "Gartenwerk", "3": "Stadtwald", "5": "Am Wasser"})[r[0]]
        o.append(f'<rect x="0" y="{y}" width="12" height="20" rx="3" fill="{q["farbe"]}"/><text x="18" y="{y + 15}" font-size="12.5" font-weight="700">{r[0]} {kurz}</text>')
        for j, (lab, f, k) in enumerate(cols):
            v = r[k]
            mx = 14 if k == 2 else 5
            o.append(f'<rect x="{110 + j * 150}" y="{y + 4}" width="{130 * v / mx:.0f}" height="12" rx="3" fill="{f}"/>'
                     f'<text x="{110 + j * 150 + 130 * v / mx + 5:.0f}" y="{y + 15}" font-size="11" fill="#555">{v if k == 2 else ""}</text>')
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 220" font-family="Archivo, Arial, sans-serif" role="img" aria-label="Verlauf Nord–Süd">' + "".join(o) + "</svg>"


# ---------- DXF für Vectorworks ----------
def dxf():
    doc = ezdxf.new("R2013", setup=True)
    doc.units = ezdxf.units.M
    msp = doc.modelspace()
    for n, f in FARBE.items():
        doc.layers.add(f"TYP_{n}", true_color=ezdxf.colors.rgb2int(tuple(int(f[i:i + 2], 16) for i in (1, 3, 5))))
    for L in ("TEXT", "GRUEN", "WASSER", "FELD"):
        doc.layers.add(L)
    for i, q in enumerate(Q):
        ox, oy = (i % 3) * 140, -(i // 3) * 140
        msp.add_lwpolyline([(ox - 6, oy - 6), (ox + 106, oy - 6), (ox + 106, oy + 96), (ox - 6, oy + 96)], close=True, dxfattribs={"layer": "FELD"})
        msp.add_text(f"{q['id']}  {q['name']}", height=3.5, dxfattribs={"layer": "TEXT"}).set_placement((ox - 6, oy + 100))
        for x, y, w, d, g, nutz, z0 in q["boxes"]:
            # Plan: y nach oben (Vectorworks), Isometrie-y = Plan -y
            pts = [(ox + x, oy + 90 - y), (ox + x + w, oy + 90 - y), (ox + x + w, oy + 90 - y - d), (ox + x, oy + 90 - y - d)]
            msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": f"TYP_{nutz}"})
            msp.add_text(f"{g} G {NAME.get(nutz, nutz)}" + (f" ab {z0 + 1}. G" if z0 else "") + f"  {w:g}x{d:g} m", height=1.2,
                         dxfattribs={"layer": "TEXT"}).set_placement((ox + x + 0.8, oy + 90 - y - 2.2))
        for wsr in q.get("wfl", []):
            msp.add_lwpolyline([(ox + a, oy + 90 - b) for a, b in wsr], close=True, dxfattribs={"layer": "WASSER"})
        for x, y, r in q.get("baeume", []):
            msp.add_circle((ox + x, oy + 90 - y), r, dxfattribs={"layer": "GRUEN"})
    p = os.path.join(OUT, "typologien_fuenf_quartiere.dxf")
    doc.saveas(p)
    return p


if __name__ == "__main__":
    daten = dict(quartiere=[{k: v for k, v in q.items() if k in ("id", "name", "farbe", "hoehe", "verkehr", "versorgung", "gruen", "wasser", "typen", "ref")}
                            | dict(axo=axo(q)) for q in Q],
                 schnitte=[dict(titel=t, svg=schnitt(t, *rest)) for t, *rest in SCHNITTE],
                 wasser=wasserkette(), verlauf=verlauf(), farben=FARBE, namen=NAME)
    json.dump(daten, open(os.path.join(OUT, "daten.json"), "w"), ensure_ascii=False)
    for q in daten["quartiere"]:
        open(os.path.join(OUT, f"axo_{q['id']}.svg"), "w").write(q["axo"])
    for i, s in enumerate(daten["schnitte"]):
        open(os.path.join(OUT, f"schnitt_{i + 1}.svg"), "w").write(s["svg"])
    print("DXF:", dxf())
    print("SVG:", len(daten["quartiere"]), "Axonometrien,", len(daten["schnitte"]), "Schnitte")
