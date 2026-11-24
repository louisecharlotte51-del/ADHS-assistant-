"""
Bergfrieden v2 – generatives Modell auf ECHTER Geometrie (Geoportal Berlin)
===========================================================================
Befund (Kleingartenentwicklungsplan 2030, gdi.berlin.de):
  Kolonie Bergfrieden (Nr. 07009, 35.219 m², 94 Parzellen) = Kategorie 1
  "dauerhaft gesicherte Kleingärten" (landeseigen + FNP Grün).
  -> Die Kolonie bleibt vollständig. Gebaut wird südlich davon auf den
     Gewerbeflächen zwischen Albrechtstraße und Teltowkanal.

Baufelder (daten/baufelder.geojson, EPSG:25833, aus Straßenachsen geschnitten):
  Nordfeld  Albrechtstr. / Komturstr. / Ordensmeisterstr. / Colditzstr.
            locker bebaut (Hallen, Schuppen) -> Transformation, Mischquartier
  Südfeld   Ordensmeisterstr. bis Teltowkanal
            dicht bebaut (Fabrik, Speicher) -> Bestand + Nachverdichtung,
            Uferpromenade

Ziele (maximiert): Wohnungen, Arbeitsplätze, Hofbesonnung (21.3., 12 Uhr)
Nebenbedingungen: Abstandsfläche 0,4 H (BauO Bln § 6), Hof >= 22 m,
                  wohnungsnahes Grün >= 6 m²/EW (Berliner Richtwert)
Aufruf: python3 generativ_v2_real.py  -> ergebnis_v2.json, plan_v2.svg
"""
import json, math
import numpy as np
from shapely.geometry import shape, box, Polygon, LineString, Point
from shapely.ops import unary_union
from shapely import affinity

import generativ_bergfrieden as G     # NSGA-II-Bausteine aus v1

RNG = np.random.default_rng(7)
DAT = "daten/"
lade = lambda n: json.load(open(DAT + n))["features"]

FELD = {f["properties"]["name"]: shape(f["geometry"]) for f in lade("baufelder.geojson")}
KANAL = shape(lade("kanal.geojson")[0]["geometry"])
GEB = [(shape(f["geometry"]), f["properties"]) for f in lade("gebaeude.geojson")]
KEP = lade("kleingaerten_kep2030.geojson")
BESTAND = json.load(open(DAT + "bestand.json"))

# Ausrichtung an der Ordensmeisterstraße (Colditz- bis Komturstraße)
WINKEL = math.degrees(math.atan2(5813308 - 5813190, 391299 - 390835))   # ~14,3°
URSPRUNG = (390835, 5813190)
rot = lambda g: affinity.rotate(g, -WINKEL, origin=URSPRUNG)
zur = lambda g: affinity.rotate(g, WINKEL, origin=URSPRUNG)

STR_HALB = 9.0            # halbe Straßenbreite ab Achse
TIEFE = 13.0
EG_H, OG_H = 4.5, 3.1
WE_BGF, EW_WE = 92.0, 1.85
SUN_EQ = 90 - 52.46
FUGE_X = 391155           # Gartenweg der Kolonie trifft Albrechtstraße

# Bestandswohnhäuser im Nordfeld bleiben (Puffer 6 m)
WOHN_BESTAND = unary_union([g.buffer(6) for g, p in GEB
                            if p["typ"] == "Wohnhaus" and g.representative_point().within(FELD["Nordfeld"])])

# Genom: bx, fuge_b, promenade_b, g_garten, g_werk, hochpunkt, gfz_sued
LO = np.array([60, 20, 15, 4, 5, 8, 1.3])
HI = np.array([110, 45, 35, 5.4, 7, 14, 2.4])   # Gartenkante max. 5 G (Schatten auf Kolonie)
NAMES = ["Blocklänge", "Breite Gartenfuge", "Breite Uferpromenade",
         "Geschosse Gartenkante", "Geschosse Werkkante", "Hochpunkt Ordensmeisterstraße",
         "GFZ Südfeld (Gewerbe)"]


def hoehe(g):
    return EG_H + (g - 1) * OG_H


def layout(x):
    bx, fuge_b, prom_b, gg, gw, hp, gfz_s = x
    gg, gw, hp = int(round(gg)), int(round(gw)), int(round(hp))
    nord = FELD["Nordfeld"].buffer(-STR_HALB, join_style=2).difference(WOHN_BESTAND)
    fx = rot(Point(FUGE_X, 5813350)).x
    fuge_r = box(fx - fuge_b / 2, URSPRUNG[1] - 600, fx + fuge_b / 2, URSPRUNG[1] + 600)
    fuge = zur(fuge_r)
    netto = rot(nord.difference(fuge))
    x0, y0, x1, y1 = netto.bounds
    ymid = (y0 + y1) / 2                                   # Wohnweg Ost-West
    blocks = []
    teile = [(x0, fx - fuge_b / 2), (fx + fuge_b / 2, x1)]   # westlich / östlich der Fuge
    for (ta, tb) in teile:
        breite = tb - ta
        n = max(1, round((breite + 2 * STR_HALB) / (bx + 2 * STR_HALB)))
        bw = (breite - (n - 1) * 2 * STR_HALB) / n
        for i in range(n):
            xa = ta + i * (bw + 2 * STR_HALB)
            streifen = box(xa, y0 - 1, xa + bw, y1 + 1).intersection(netto)
            for st in getattr(streifen, "geoms", [streifen]):
                if st.geom_type != "Polygon" or st.area < 1500:
                    continue
                ly0, ly1 = st.bounds[1], st.bounds[3]
                if ly1 - ly0 >= 2 * 50 + 12:                # tief genug: zwei Reihen
                    ym = (ly0 + ly1) / 2
                    teile2 = [(ly0, ym - 6, "W"), (ym + 6, ly1, "G")]
                else:                                       # schmal: eine Reihe, gemischt
                    teile2 = [(ly0, ly1, "M")]
                for (ya, yb, zone) in teile2:
                    r = box(xa, ya, xa + bw, yb).intersection(st)
                    for p in getattr(r, "geoms", [r]):
                        if p.geom_type != "Polygon" or p.area < 1200:
                            continue
                        mrr = p.minimum_rotated_rectangle
                        k2 = sorted(LineString(mrr.exterior.coords[j:j + 2]).length for j in range(2))
                        if k2[0] < 30:
                            continue
                        hof = p.buffer(-TIEFE, join_style=2)
                        typ = "hof"
                        if hof.is_empty or min(LineString(hof.minimum_rotated_rectangle.exterior.coords[j:j + 2]).length
                                               for j in range(2)) < 22:
                            typ = "solitaer"
                        blocks.append(dict(geo=zur(p), zone=zone, typ=typ,
                                           g=gw if zone == "W" else gg, tiefe_ns=yb - ya))
    # Hochpunkt: östlichster Hof-Block der Werkreihe (südlich, kein Schatten auf die Gärten)
    w_bl = [b for b in blocks if b["zone"] == "W" and b["typ"] == "hof"]
    if w_bl:
        max(w_bl, key=lambda b: b["geo"].centroid.x)["hp"] = hp
    # Südfeld: Uferpromenade abziehen, Rest Gewerbe-Bestand + Nachverdichtung
    prom = KANAL.buffer(prom_b).intersection(FELD["Suedfeld" if "Suedfeld" in FELD else "Südfeld"])
    sued_netto = FELD["Südfeld"].buffer(-STR_HALB / 2).difference(prom).difference(fuge)
    return blocks, dict(fuge=fuge.intersection(FELD["Nordfeld"].union(FELD["Südfeld"]).buffer(STR_HALB)),
                        prom=prom, sued=sued_netto, gfz_s=gfz_s, nord_netto=zur(netto))


def bewerten(x):
    blocks, geo = layout(x)
    wohn = gew = 0.0
    sonne, strafe = [], 0.0
    for b in blocks:
        p = b["geo"]
        g = b["g"]
        if b["typ"] == "solitaer":                        # Stadthäuser/Zeilen auf Restflächen
            fp = p.area * 0.42
            gew += fp
            wohn += fp * (g - 1)
            continue
        hof = p.buffer(-TIEFE, join_style=2)
        ring = (p.area - hof.area) * 0.92
        H, H_sued = hoehe(g), hoehe(g - 1)
        if b["zone"] == "W":                               # Werkkante: MU, EG + 1. OG Gewerbe
            gew += ring * 2
            wohn += ring * (g - 2)
        elif b["zone"] == "M":                             # schmale Mischreihe: EG Gewerbe
            gew += ring
            wohn += ring * (g - 1)
        else:                                              # Gartenkante: Wohnen, Ecken gewerblich
            gew += ring * 0.15
            wohn += ring * (g - 0.15)
        if "hp" in b:
            wohn += 24 * 24 * (b["hp"] - g)
        if hof.is_empty:
            strafe += 50
            sonne.append(0)
            continue
        mrr = hof.minimum_rotated_rectangle
        kanten = sorted(LineString(mrr.exterior.coords[i:i + 2]).length for i in range(2))
        hof_ns = b["tiefe_ns"] - 2 * TIEFE
        schatten = H_sued / math.tan(math.radians(SUN_EQ))
        sonne.append(max(0, (hof_ns - schatten) / hof_ns) if hof_ns > 0 else 0)
        af = max(3, 0.4 * H)
        strafe += max(0, 2 * af - kanten[0]) + max(0, 22 - kanten[0]) * 2
        strafe += max(0, 2 * af - 2 * STR_HALB) * 0.5
    # Südfeld: Bestand bleibt mindestens erhalten, Nachverdichtung bis GFZ
    sued_bgf = max(geo["sued"].area * geo["gfz_s"], BESTAND["suedfeld"]["bgf"] * 0.85)
    gew += sued_bgf
    we = wohn / WE_BGF
    ew = we * EW_WE
    gruen = geo["fuge"].area + geo["prom"].area
    gruen_ew = gruen / max(ew, 1)
    strafe += max(0, 6 - gruen_ew) * 40                    # Berliner Richtwert
    ap = gew * 0.8 / 40
    f = np.array([we, ap, float(np.mean(sonne)) * 100 if sonne else 0])
    flaeche = FELD["Nordfeld"].area + FELD["Südfeld"].area
    kenn = dict(WE=round(we), EW=round(ew), Arbeitsplaetze=round(ap),
                BGF_Wohnen=round(wohn), BGF_Gewerbe=round(gew), BGF_Gewerbe_Sued=round(sued_bgf),
                Bestand_BGF=BESTAND["nordfeld"]["bgf"] + BESTAND["suedfeld"]["bgf"],
                Arbeitsplaetze_Bestand_ca=round((BESTAND["nordfeld"]["bgf"] + BESTAND["suedfeld"]["bgf"]) * 0.8 / 60),
                GFZ_brutto=round((wohn + gew) / flaeche, 2), Gebiet_ha=round(flaeche / 1e4, 1),
                Nordfeld_ha=round(FELD["Nordfeld"].area / 1e4, 1), Suedfeld_ha=round(FELD["Südfeld"].area / 1e4, 1),
                Gruen_neu_m2=round(gruen), Gruen_je_EW=round(gruen_ew, 1),
                Hofbesonnung_pct=round(f[2]), Bloecke=len(blocks),
                Stellplaetze=round(we * 0.3), Kita_Plaetze_Bedarf=round(ew * 0.045),
                Grundschulplaetze_Bedarf=round(ew * 0.05), Strafe=round(strafe, 1))
    return f - strafe * np.array([15, 10, 1]), kenn


def nsga2(pop_n=60, gens=40):
    G.LO, G.HI, G.RNG = LO, HI, RNG                      # Operatoren aus v1 wiederverwenden
    P = LO + RNG.random((pop_n, len(LO))) * (HI - LO)
    cache = {}
    def ev(x):
        k = tuple(np.round(x, 3))
        if k not in cache:
            cache[k] = bewerten(x)[0]
        return cache[k]
    for _ in range(gens):
        F = np.array([ev(x) for x in P])
        _, rank = G.fronten(F)
        kids = []
        for _ in range(pop_n):
            a, b = RNG.integers(pop_n, size=2); p1 = P[a] if rank[a] <= rank[b] else P[b]
            a, b = RNG.integers(pop_n, size=2); p2 = P[a] if rank[a] <= rank[b] else P[b]
            kids.append(G.sbx_mut(p1, p2, pm=1 / len(LO)))
        R = np.vstack([P, kids]); FR = np.array([ev(x) for x in R])
        fr, _ = G.fronten(FR); neu = []
        for f in fr:
            f = np.array(f)
            if len(neu) + len(f) <= pop_n:
                neu += list(f)
            else:
                cd = G.crowding(FR, f); neu += list(f[np.argsort(-cd)][:pop_n - len(neu)]); break
        P = R[neu]
    F = np.array([ev(x) for x in P]); fr, _ = G.fronten(F)
    ok = [i for i in fr[0] if bewerten(P[i])[1]["Strafe"] == 0] or fr[0]
    return P[ok], F[ok]


# ---------------- SVG mit echtem Kontext ----------------
X0, Y0, X1, Y1 = 390690, 5813000, 391420, 5813700
SK = 1.0


def pfad(g):
    out = ""
    for p in getattr(g, "geoms", [g]):
        if p.geom_type != "Polygon" or p.is_empty:
            continue
        for r in [p.exterior, *p.interiors]:
            out += "M" + " L".join(f"{(x - X0) * SK:.1f},{(Y1 - y) * SK:.1f}" for x, y in r.coords) + "Z "
    return out


def svg(x):
    blocks, geo = layout(x)
    W, H = (X1 - X0) * SK, (Y1 - Y0) * SK
    C = box(X0, Y0, X1, Y1)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" role="img" '
         f'aria-label="Rahmenplan Bergfrieden v2 auf Katastergrundlage">',
         f'<rect width="{W}" height="{H}" fill="var(--land,#efe9dc)"/>']
    farbe = {"Wohnbaufläche": "var(--wohnbest,#e6dcc6)", "Grünfläche": "var(--gruen2,#9cc58a)",
             "Gemeinbedarfsfläche": "var(--gbbest,#dcd3e6)", "Gewerbliche Baufläche": "var(--gewbest,#e2dcd2)"}
    for f in lade("fnp.geojson"):
        n = f["properties"]["nutzung"] or ""
        c = next((v for k, v in farbe.items() if n.startswith(k)), None)
        if c:
            o.append(f'<path d="{pfad(shape(f["geometry"]).intersection(C))}" fill="{c}"/>')
    # Kolonien: Kategorie 1 gesichert
    for f in KEP:
        g = shape(f["geometry"]).intersection(C)
        k1 = f["properties"]["entwicklung"].startswith("1")
        o.append(f'<path d="{pfad(g)}" fill="{"var(--parzelle,#b9d98f)" if k1 else "var(--k3,#d9e6b0)"}" '
                 f'stroke="var(--gruen,#6fae5c)" stroke-width="3"/>')
    o.append('<defs><pattern id="pz" width="12" height="14" patternUnits="userSpaceOnUse">'
             '<rect width="12" height="14" fill="none" stroke="var(--gruen,#6fae5c)" stroke-width=".8"/></pattern></defs>')
    for f in KEP:
        if f["properties"]["entwicklung"].startswith("1"):
            o.append(f'<path d="{pfad(shape(f["geometry"]).intersection(C))}" fill="url(#pz)"/>')
    o.append(f'<path d="{pfad(KANAL.intersection(C))}" fill="var(--wasser,#3f7fb0)"/>')
    # Bestandsgebäude Südfeld + Umgebung (grau, dünn)
    for g, p in GEB:
        if g.intersects(C) and not g.representative_point().within(FELD["Nordfeld"]) or \
                (p["typ"] == "Wohnhaus" and g.representative_point().within(FELD["Nordfeld"])):
            rp = g.representative_point()
            if rp.within(geo["fuge"]) or rp.within(geo["prom"]):
                continue                                   # Abriss für Fuge / Promenade
            inside_s = rp.within(geo["sued"])
            o.append(f'<path d="{pfad(g)}" fill="{"var(--gew,#8f6fa8)" if inside_s else "var(--best,#b9b2a4)"}"/>')
    o.append(f'<path d="{pfad(geo["prom"])}" fill="var(--gruen,#6fae5c)"/>')
    o.append(f'<path d="{pfad(geo["fuge"])}" fill="var(--gruen,#6fae5c)"/>')
    # Straßen
    for f in lade("strassen.geojson"):
        g = shape(f["geometry"]).intersection(C)
        for l in getattr(g, "geoms", [g]):
            if l.geom_type == "LineString":
                d = "M" + " L".join(f"{(a - X0) * SK:.1f},{(Y1 - b) * SK:.1f}" for a, b in l.coords)
                o.append(f'<path d="{d}" stroke="var(--strasse,#fff)" stroke-width="10" fill="none" stroke-linecap="round"/>')
    farbe_b = {"G": "var(--wa,#e3b448)", "W": "var(--mu,#c4553b)", "M": "var(--mu,#c4553b)"}
    for b in blocks:
        p = b["geo"]; hof = p.buffer(-TIEFE, join_style=2)
        if b["typ"] == "solitaer":                         # drei Stadthäuser je Restfläche
            rp = rot(p); bx0, by0, bx1, by1 = rp.bounds; w3 = (bx1 - bx0) / 3
            for j in range(3):
                h = zur(box(bx0 + j * w3 + 3, by0 + 4, bx0 + (j + 1) * w3 - 3, by1 - 4).intersection(rp.buffer(-3)))
                o.append(f'<path d="{pfad(h)}" fill="{farbe_b[b["zone"]]}"/>')
            c = p.centroid
            o.append(f'<text x="{(c.x - X0) * SK:.0f}" y="{(Y1 - c.y) * SK + 7:.0f}" text-anchor="middle" class="g">{b["g"]}</text>')
            continue
        o.append(f'<path d="{pfad(p)}" fill="{farbe_b[b["zone"]]}"/>')
        if not hof.is_empty:
            o.append(f'<path d="{pfad(hof)}" fill="var(--hof,#cfe3b8)"/>')
        c = p.centroid
        o.append(f'<text x="{(c.x - X0) * SK:.0f}" y="{(Y1 - c.y) * SK + 7:.0f}" text-anchor="middle" class="g">{b["g"]}</text>')
        if "hp" in b:
            mr = min(p.exterior.coords, key=lambda q: q[1] - 0.6 * q[0]); mr = (mr[0] + 30, mr[1] + 30)
            o.append(f'<rect x="{(mr[0] - X0) * SK - 30:.0f}" y="{(Y1 - mr[1]) * SK + 4:.0f}" width="24" height="24" fill="var(--ink,#1d1d1b)"/>'
                     f'<text x="{(mr[0] - X0) * SK - 18:.0f}" y="{(Y1 - mr[1]) * SK + 21:.0f}" text-anchor="middle" class="hp">{b["hp"]}</text>')
    # Fußgängerbrücke in Verlängerung der Fuge
    fc = geo["fuge"].centroid
    br = zur(box(rot(fc).x - 4, URSPRUNG[1] - 260, rot(fc).x + 4, URSPRUNG[1] - 20)).intersection(KANAL.buffer(10))
    o.append(f'<path d="{pfad(br)}" fill="var(--weg,#fff)" stroke="var(--ink,#1d1d1b)" stroke-width="1"/>')
    # Marker
    def M(n, px, py):
        o.append(f'<circle cx="{(px - X0) * SK:.0f}" cy="{(Y1 - py) * SK:.0f}" r="13" fill="var(--marker,#fff)" '
                 f'stroke="var(--ink,#1d1d1b)" stroke-width="2"/><text x="{(px - X0) * SK:.0f}" '
                 f'y="{(Y1 - py) * SK + 5:.0f}" text-anchor="middle" class="m">{n}</text>')
    bf = [shape(f["geometry"]) for f in KEP if f["properties"]["name_der_k"] == "Bergfrieden"][0]
    M(1, bf.centroid.x, bf.centroid.y)
    M(2, fc.x + 2, fc.y + 18)
    pc = geo["prom"].representative_point(); M(3, pc.x - 90, pc.y)
    bc = br.centroid if not br.is_empty else fc; M(4, bc.x + 22, bc.y)
    hp = [b for b in blocks if "hp" in b]
    if hp: M(5, hp[0]["geo"].centroid.x + 30, hp[0]["geo"].centroid.y - 22)
    w = [b for b in blocks if b["zone"] == "W"]
    if w: M(6, w[0]["geo"].centroid.x, w[0]["geo"].centroid.y + 26)
    sc = geo["sued"].representative_point(); M(7, sc.x + 60, sc.y)
    M(8, 391345, 5813560)                                   # Grünzug Ost
    o.append(f'<g><path d="M{W - 30} 50 l10 26 l-10 -7 l-10 7z" fill="var(--ink,#1d1d1b)"/>'
             f'<text x="{W - 30}" y="40" text-anchor="middle">N</text></g>')
    o.append(f'<g><rect x="24" y="{H - 30}" width="100" height="6" fill="var(--ink,#1d1d1b)"/>'
             f'<text x="132" y="{H - 22}">100 m</text></g>')
    o.append("</svg>")
    o = [e for e in o if 'd=""' not in e and 'd="M"' not in e]   # leere Geometrien
    return "\n".join(o)


if __name__ == "__main__":
    P, F = nsga2()
    k = G.knie(F)
    best = P[k]
    _, kenn = bewerten(best)
    pareto = [dict(WE=round(float(f[0])), AP=round(float(f[1])), Sonne=round(float(f[2]))) for f in F]
    out = dict(genom={n: (round(float(v), 1) if i in (0, 1, 2, 6) else int(round(float(v))))
                      for i, (n, v) in enumerate(zip(NAMES, best))},
               kennzahlen=kenn, pareto=pareto, knie=k,
               kolonie=dict(nr="07009", flaeche_m2=35219, parzellen=94,
                            kategorie="1 dauerhaft gesicherte Kleingärten", grund="Landeseigen + FNP Grün"))
    json.dump(out, open("ergebnis_v2.json", "w"), ensure_ascii=False, indent=1)
    open("plan_v2.svg", "w").write(svg(best))
    print(json.dumps(out["genom"], ensure_ascii=False))
    print(json.dumps(kenn, ensure_ascii=False))
    print("Pareto-Lösungen ohne Regelverstoß:", len(pareto))
