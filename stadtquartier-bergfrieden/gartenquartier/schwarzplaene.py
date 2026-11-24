"""
Schwarzpläne S1-S6 (SVG):
  zeichnungen/schwarzplan_Sx.svg   reiner Schwarzplan: Neubau schwarz, Umgebung grau
  zeichnungen/lesart_Sx.svg        Lesart: Typologie + Phase je Baufeld, Sonderbauten grau beschriftet
  zeichnungen/schwarzplaene_uebersicht.svg   alle sechs nebeneinander
Aufruf: python3 schwarzplaene.py
"""
import json, os
from shapely.geometry import shape, box
from shapely.ops import unary_union
import entwurf as E

OUT = "zeichnungen"
GEO = json.load(open("typologien_geo.json"))
INFO = {v["code"]: v for v in json.load(open("typologien.json"))}
L = lambda n: json.load(open(E.DAT + n + ".json"))["features"]
X0, Y0, X1, Y1, S = 390965, 5813195, 391600, 5813900, 1.2
W, Hh = (X1 - X0) * S, (Y1 - Y0) * S
C = box(X0, Y0, X1, Y1)
SCHRIFT = "Archivo, Arial, sans-serif"
TYPNAME = dict(kamm_ruecken="Kamm", kamm_finger="Kamm", zeile="Zeile", winkel="Winkel", punkt="Punkthaus", reihe="Reihenhäuser",
               kante="Kante", sockel="Sockel + Hochpunkt", riegel="Riegel", hochpunkt="Sockel + Hochpunkt", halle="Halle",
               schule="Schule", sporthalle="Sporthalle", uferzeile="Uferzeile", kopfbau="Kopfbau")
SONDER = {"schule", "sporthalle", "halle", "sockel"}


def xy(x, y):
    return (x - X0) * S, (Y1 - y) * S


def pfad(g):
    o = ""
    for p in getattr(g, "geoms", [g]):
        if p.is_empty:
            continue
        if p.geom_type == "Polygon":
            for r in [p.exterior, *p.interiors]:
                o += "M" + " L".join("%.1f,%.1f" % xy(x, y) for x, y in r.coords) + "Z "
        elif p.geom_type == "LineString":
            o += "M" + " L".join("%.1f,%.1f" % xy(x, y) for x, y in p.coords) + " "
        elif hasattr(p, "geoms"):
            o += pfad(p)
    return o


def text(x, y, t, size=11, farbe="#1d1d1b", anchor="middle", weight=400):
    px, py = xy(x, y)
    return (f'<text x="{px:.1f}" y="{py:.1f}" font-size="{size}" fill="{farbe}" text-anchor="{anchor}" font-weight="{weight}" '
            f'paint-order="stroke" stroke="#fff" stroke-width="3.2" stroke-linejoin="round">{t}</text>')


KONTEXT = unary_union([shape(f["geometry"]) for f in L("geb") if shape(f["geometry"]).intersects(C)
                       and not shape(f["geometry"]).representative_point().within(E.GEBIET)]).intersection(C)
KANAL = unary_union([shape(f["geometry"]) for f in L("gew")]).intersection(C)
BESTAND = unary_union([b["geo"] for b in E.BESTAND])


def grund(lesart=False):
    o = [f'<rect width="{W:.0f}" height="{Hh:.0f}" fill="#fff"/>',
         f'<path d="{pfad(KANAL)}" fill="#ececec"/>',
         f'<path d="{pfad(KONTEXT)}" fill="#b9b9b9"/>',
         f'<path d="{pfad(BESTAND)}" fill="#b9b9b9"/>',
         f'<path d="{pfad(E.GEBIET)}" fill="none" stroke="#9a9a9a" stroke-width=".8"/>']
    wasser = E.WASSER_FL.intersection(E.GEBIET.buffer(25))
    o.append(f'<path d="{pfad(wasser)}" fill="none" stroke="#c9c9c9" stroke-width=".7"/>')
    for f in E.BAUFELDER:
        o.append(f'<path d="{pfad(f)}" fill="none" stroke="{"#7a7a7a" if lesart else "#cfcfcf"}" stroke-width="{.9 if lesart else .7}" '
                 f'stroke-dasharray="{"none" if lesart else "3 3"}"/>')
    return o


def haeuser(code, lesart=False):
    o = []
    hs = GEO[code]
    for h in hs:
        g = shape(h["geo"])
        f = "#111"
        if lesart and h["typ"] in SONDER:
            f = "#7d7d7d"
        o.append(f'<path d="{pfad(g)}" fill="{f}"/>')
    # Reihenhäuser: Hauskörnung als feine weiße Fugen
    for h in hs:
        if h["typ"] == "reihe":
            o.append(f'<path d="{pfad(shape(h["geo"]).exterior)}" fill="none" stroke="#fff" stroke-width=".55"/>')
    return o


def rahmen(o, titel, unter):
    st = xy(E.STATION.x, min(E.STATION.y, Y1 - 12))
    o.append(f'<g transform="translate({W - 30:.0f},34)"><path d="M0,-18 L8,7 L0,2 L-8,7z" fill="#1d1d1b"/>'
             f'<text y="22" text-anchor="middle" font-size="12" fill="#1d1d1b">N</text></g>')
    o.append(f'<g transform="translate(18,{Hh - 18:.0f})"><rect width="{100 * S:.0f}" height="3.5" fill="#1d1d1b"/>'
             f'<rect width="{50 * S:.0f}" height="3.5" fill="#fff" stroke="#1d1d1b" stroke-width=".6"/>'
             f'<text x="{100 * S + 7:.0f}" y="5" font-size="11" fill="#1d1d1b">100 m</text></g>')
    o.append(f'<rect x="8" y="8" width="{max(len(unter) * 5.9, len(titel) * 10) + 22:.0f}" height="46" fill="#fff" opacity=".93"/>')
    o.append(f'<text x="18" y="28" font-size="17" font-weight="800" fill="#1d1d1b">{titel}</text>'
             f'<text x="18" y="46" font-size="11.5" fill="#555">{unter}</text>')
    x, y = xy(E.STATION.x, 5813890)
    o.append(f'<g transform="translate({x:.0f},{y + 10:.0f})"><rect x="-9" y="-9" width="18" height="18" rx="3" fill="#1d1d1b"/>'
             f'<text y="4.5" text-anchor="middle" font-size="12" font-weight="700" fill="#fff">S</text></g>')
    x, y = xy(391262, 5813228)
    o.append(f'<text x="{x:.0f}" y="{y:.0f}" font-size="10.5" fill="#777" text-anchor="middle">Kanal</text>')


def lesart_labels(code):
    o = []
    hs = GEO[code]
    for i, f in enumerate(E.BAUFELDER, 1):
        typen = []
        for h in hs:
            if h["feld"] == i:
                n = TYPNAME[h["typ"]]
                if n in ("Riegel",) and any(x["feld"] == i and x["typ"] == "halle" for x in hs):
                    n = "Halle + Riegel"
                if n == "Riegel" and any(x["feld"] == i and x["typ"] == "sockel" for x in hs):
                    continue
                if n == "Halle" and any(x["feld"] == i and x["typ"] == "riegel" for x in hs):
                    n = "Halle + Riegel"
                if n not in typen:
                    typen.append(n)
        p = f.representative_point()
        o.append(text(p.x, p.y + 6, f"{i} · {E.phase(f)}", 11.5, "#1d1d1b", weight=800))
        for j, t in enumerate(typen[:3]):
            o.append(text(p.x, p.y - 7 - 12.5 * j, t, 10.5, "#333"))
    return o


def blatt(code, lesart=False):
    v = INFO[code]
    k = v["kennzahlen"]
    o = grund(lesart) + haeuser(code, lesart)
    if lesart:
        o += lesart_labels(code)
    komma = lambda z: f"{z:.2f}".replace(".", ",")
    unter = ("Lesart: Baufeld · Phase · Typologien · grau = Schule, Sport, Hallen, Sockel" if lesart else
             f'Schwarzplan · GRZ {komma(k["grz"])} · GFZ {komma(k["gfz"])} (Baufelder) · ca. {k["we"]:,} Wohnungen'.replace(f'{k["we"]:,}', f'{k["we"]:,}'.replace(",", ".")))
    rahmen(o, f'{code} {v["name"]}', unter)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {Hh:.0f}" font-family="{SCHRIFT}">' + "".join(o) + "</svg>"


def uebersicht():
    teile = []
    for n, code in enumerate(GEO):
        inner = blatt(code).split(">", 1)[1].rsplit("</svg>", 1)[0]
        teile.append(f'<g transform="translate({(n % 3) * (W + 24):.0f},{(n // 3) * (Hh + 24):.0f})">{inner}</g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {3 * W + 48:.0f} {2 * Hh + 24:.0f}" font-family="{SCHRIFT}">'
            f'<rect width="100%" height="100%" fill="#fff"/>' + "".join(teile) + "</svg>")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for code in GEO:
        open(f"{OUT}/schwarzplan_{code}.svg", "w").write(blatt(code))
        open(f"{OUT}/lesart_{code}.svg", "w").write(blatt(code, True))
    open(f"{OUT}/schwarzplaene_uebersicht.svg", "w").write(uebersicht())
    print(sorted(f for f in os.listdir(OUT) if f.startswith(("schwarz", "lesart"))))
