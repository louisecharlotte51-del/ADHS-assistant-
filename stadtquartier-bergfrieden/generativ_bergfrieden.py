"""
Bergfrieden – generatives Rahmenplan-Modell (Konzeptstufe)
==========================================================
Parametrisches Blockraster + NSGA-II (Mehrziel-Evolution) für das neue
Stadtquartier auf/um die Kolonie Bergfrieden (Berlin-Tempelhof, 12099)
zwischen Komturstraße (Nord) und Teltowkanal (Süd).

WICHTIG: Die Gebietsgeometrie ist eine SCHEMATISCHE Annahme (560 m x 430 m,
ca. 24 ha Untersuchungsraum). Vor jeder Weiterarbeit mit Flurstücken aus dem
Geoportal Berlin / FIS-Broker ersetzen.

Ziele (alle maximiert):
  f1  Wohneinheiten (WE)                     -> Wohnraumbedarf Berlin
  f2  öffentliches Grün je Einwohner (m²/EW) -> Berliner Richtwert 6 m² wohnungsnah
  f3  Hofbesonnung Tag-Nacht-Gleiche 12 Uhr  -> Anteil sonniger Hoffläche
Nebenbedingungen (Straf-Terme):
  - Abstandsfläche BauO Bln § 6: 0,4 H, mind. 3 m (Straße & Hof)
  - Hofbreite >= 22 m (Belichtung), Blockumfang <= 450 m (Durchwegung)
Aufruf:  python3 generativ_bergfrieden.py   -> ergebnis.json, plan.svg
"""
import json, math
import numpy as np

RNG = np.random.default_rng(42)

# ---------------- Gebiet (Annahme, Meter, Ursprung SW-Ecke) ----------------
SITE_W, SITE_H = 560.0, 430.0          # Bruttobauland ~24,1 ha
PROMENADE = 30.0                        # Uferpromenade Teltowkanal (Süd)
NORD_STR = 22.0                         # Komturstraße-Kante (Nord, Allee)
ACHSE_B = 20.0                          # Ost-West-Quartiersachse (Fahrradstraße)
STR = 18.0                              # Quartiersstraße (Wohnstraße)
LAT = 52.46                             # Berlin-Tempelhof
SUN_EQ = 90 - LAT                       # 37,5° Sonnenhöhe 21.3./23.9. 12 Uhr
EG_H, OG_H = 4.5, 3.1                   # Geschosshöhen (EG gewerbetauglich)
TIEFE = 13.0                            # Gebäudetiefe Blockrand
WE_BGF = 92.0                           # m² BGF je WE (inkl. Erschließung)
EW_WE = 1.85                            # Haushaltsgröße Berlin
STELLPL_WE = 0.3                        # Quartiersgaragen-Schlüssel

# Genom: [bx, by, spine_w, g_kanal, g_garten, g_nord, hochpunkt]
LO = np.array([ 70,  60, 40, 5, 3, 5, 10], float)
HI = np.array([115, 105, 90, 8, 6, 7, 16], float)
NAMES = ["Blocklänge bx", "Blocktiefe by", "Breite Gartenfuge",
         "Geschosse Kanalkante", "Geschosse Gartenhöfe",
         "Geschosse Werkhofkante", "Hochpunkt Hafen"]


def hoehe(g):
    return EG_H + (g - 1) * OG_H


def teile(lange, soll):
    """Teilt eine Strecke in n Blöcke + (n-1) Straßen, n so dass Block ~ soll."""
    n = max(1, round((lange + STR) / (soll + STR)))
    return n, (lange - (n - 1) * STR) / n


def layout(x):
    bx, by, spine, gk, gg, gn, hp = x
    gk, gg, gn, hp = int(round(gk)), int(round(gg)), int(round(gn)), int(round(hp))
    sx0 = SITE_W * 0.47 - spine / 2
    sx1 = sx0 + spine
    y0, y1 = PROMENADE, SITE_H - NORD_STR
    ya = y0 + (y1 - y0) * 0.48 - ACHSE_B / 2           # Achse leicht südlich
    felder = [(0, sx0, y0, ya), (0, sx0, ya + ACHSE_B, y1),
              (sx1, SITE_W, y0, ya), (sx1, SITE_W, ya + ACHSE_B, y1)]
    blocks = []
    for (fx0, fx1, fy0, fy1) in felder:
        nx, bw = teile(fx1 - fx0, bx)
        ny, bh = teile(fy1 - fy0, by)
        for i in range(nx):
            for j in range(ny):
                X = fx0 + i * (bw + STR)
                Y = fy0 + j * (bh + STR)
                if Y <= y0 + 1:
                    zone, g = "K", gk                 # Kanalkante (MU)
                elif Y + bh >= y1 - 1:
                    zone, g = "N", gn                 # Werkhofkante (MU)
                else:
                    zone, g = "W", gg                 # Gartenhöfe (WA)
                blocks.append(dict(x=X, y=Y, w=bw, h=bh, zone=zone, g=g))
    # Gemeinbedarf: Block an Achse + Fuge, westlich -> Schule/Kita-Campus
    cand = [b for b in blocks if b["zone"] == "W" and abs(b["x"] + b["w"] - sx0) < 1]
    if cand:
        min(cand, key=lambda b: abs(b["y"] - ya))["zone"] = "S"
    # Hochpunkt: Kanalblock direkt östlich der Fuge (Hafenplatz)
    hk = [b for b in blocks if b["zone"] == "K" and abs(b["x"] - sx1) < 1]
    if hk:
        hk[0]["hp"] = hp
    return blocks, dict(sx0=sx0, sx1=sx1, ya=ya, y0=y0, y1=y1, spine=spine)


def bewerten(x):
    blocks, geo = layout(x)
    bgf_wohn = bgf_gew = 0.0
    grz_fl = 0.0
    sonne, strafe = [], 0.0
    for b in blocks:
        w, h, g = b["w"], b["h"], b["g"]
        hof_w, hof_h = w - 2 * TIEFE, h - 2 * TIEFE
        ring = w * h - max(hof_w, 0) * max(hof_h, 0)
        ring *= 0.92                                   # 2 Durchgänge je Block
        grz_fl += ring
        H = hoehe(g)
        H_sued = hoehe(g - 1)                          # Regel: Südflügel -1 G
        if b["zone"] == "S":
            bgf_gew += ring * 3                        # Schule 3 G
            continue
        n_og = g - 1
        if b["zone"] in "KN":
            bgf_gew += ring                            # EG gewerblich
            bgf_wohn += ring * n_og * 0.85
            bgf_gew += ring * n_og * 0.15              # Büro/Werkstatt-OG
        else:
            bgf_gew += ring * 0.15
            bgf_wohn += ring * (0.85 + n_og)
        if "hp" in b:                                   # Hochpunkt 22x22 m
            bgf_wohn += 22 * 22 * (b["hp"] - g)
        # Hofbesonnung Tag-Nacht-Gleiche 12 Uhr (Schatten des Südflügels)
        schatten = H_sued / math.tan(math.radians(SUN_EQ))
        sonne.append(max(0.0, (hof_h - schatten) / hof_h) if hof_h > 0 else 0)
        # Abstandsflächen 0,4H (mind. 3 m) – Hof und Straße
        af = max(3.0, 0.4 * H)
        strafe += max(0, 2 * af - hof_w) + max(0, 2 * af - hof_h)
        strafe += max(0, 2 * af - STR) * 0.5
        strafe += max(0, 22 - min(hof_w, hof_h)) * 2   # Hofmindestmaß
        strafe += max(0, 2 * (w + h) - 450) * 0.5      # Blockumfang
    we = bgf_wohn / WE_BGF
    ew = we * EW_WE
    flaeche = SITE_W * SITE_H
    gruen = geo["spine"] * (geo["y1"] - geo["y0"]) + SITE_W * PROMENADE * 0.7
    gruen_ew = gruen / max(ew, 1)
    f = np.array([we, gruen_ew, float(np.mean(sonne)) * 100])
    kenn = dict(WE=round(we), EW=round(ew), BGF_Wohnen=round(bgf_wohn),
                BGF_Gewerbe_Gemeinbedarf=round(bgf_gew),
                GFZ_brutto=round((bgf_wohn + bgf_gew) / flaeche, 2),
                GRZ_brutto=round(grz_fl / flaeche, 2),
                Gruen_oeffentlich_m2=round(gruen), Gruen_je_EW=round(gruen_ew, 1),
                Hofbesonnung_pct=round(f[2]), Bloecke=len(blocks),
                Arbeitsplaetze=round(bgf_gew * 0.8 / 35),
                Stellplaetze=round(we * STELLPL_WE),
                Kita_Plaetze_Bedarf=round(ew * 0.045),
                Grundschulplaetze_Bedarf=round(ew * 0.05),
                Strafe=round(strafe, 1))
    return f - strafe * np.array([20, 0.2, 1.0]), kenn


# ---------------- NSGA-II ----------------
def dominiert(a, b):
    return np.all(a >= b) and np.any(a > b)


def fronten(F):
    n = len(F)
    S = [[] for _ in range(n)]
    cnt = np.zeros(n, int)
    rank = np.zeros(n, int)
    fr = [[]]
    for p in range(n):
        for q in range(n):
            if dominiert(F[p], F[q]):
                S[p].append(q)
            elif dominiert(F[q], F[p]):
                cnt[p] += 1
        if cnt[p] == 0:
            fr[0].append(p)
    i = 0
    while fr[i]:
        nxt = []
        for p in fr[i]:
            for q in S[p]:
                cnt[q] -= 1
                if cnt[q] == 0:
                    rank[q] = i + 1
                    nxt.append(q)
        i += 1
        fr.append(nxt)
    return fr[:-1], rank


def crowding(F, idx):
    d = np.zeros(len(idx))
    for m in range(F.shape[1]):
        o = np.argsort(F[idx, m])
        d[o[0]] = d[o[-1]] = np.inf
        span = F[idx[o[-1]], m] - F[idx[o[0]], m] or 1
        for k in range(1, len(idx) - 1):
            d[o[k]] += (F[idx[o[k + 1]], m] - F[idx[o[k - 1]], m]) / span
    return d


def sbx_mut(p1, p2, eta=15, pm=1 / 7):
    c = p1.copy()
    for i in range(len(p1)):
        if RNG.random() < 0.9:
            u = RNG.random()
            beta = (2 * u) ** (1 / (eta + 1)) if u < .5 else (1 / (2 * (1 - u))) ** (1 / (eta + 1))
            c[i] = 0.5 * ((1 + beta) * p1[i] + (1 - beta) * p2[i])
        if RNG.random() < pm:
            c[i] += RNG.normal(0, 0.1 * (HI[i] - LO[i]))
    return np.clip(c, LO, HI)


def nsga2(pop_n=80, gens=60):
    P = LO + RNG.random((pop_n, len(LO))) * (HI - LO)
    for _ in range(gens):
        F = np.array([bewerten(x)[0] for x in P])
        _, rank = fronten(F)
        kids = []
        for _ in range(pop_n):
            a, b = RNG.integers(pop_n, size=2)
            p1 = P[a] if rank[a] <= rank[b] else P[b]
            a, b = RNG.integers(pop_n, size=2)
            p2 = P[a] if rank[a] <= rank[b] else P[b]
            kids.append(sbx_mut(p1, p2))
        R = np.vstack([P, kids])
        FR = np.array([bewerten(x)[0] for x in R])
        fr, _ = fronten(FR)
        neu = []
        for f in fr:
            f = np.array(f)
            if len(neu) + len(f) <= pop_n:
                neu += list(f)
            else:
                cd = crowding(FR, f)
                neu += list(f[np.argsort(-cd)][:pop_n - len(neu)])
                break
        P = R[neu]
    F = np.array([bewerten(x)[0] for x in P])
    fr, _ = fronten(F)
    return P[fr[0]], F[fr[0]]


def knie(F):
    """Kompromisslösung: geringster normierter Abstand zum Idealpunkt."""
    lo, hi = F.min(0), F.max(0)
    N = (F - lo) / np.where(hi - lo == 0, 1, hi - lo)
    return int(np.argmin(np.linalg.norm(1 - N, axis=1)))


# ---------------- SVG-Plan ----------------
def svg(x):
    blocks, geo = layout(x)
    s, pad = 1.0, 60
    W, H = SITE_W + 2 * pad, SITE_H + 2 * pad + 70
    Y = lambda y: pad + SITE_H - y                       # Nord oben
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
         f'role="img" aria-label="Rahmenplan Bergfrieden">']
    o.append(f'<rect width="{W}" height="{H}" fill="var(--land,#efe9dc)"/>')
    # Teltowkanal
    o.append(f'<rect x="0" y="{Y(-8):.0f}" width="{W}" height="46" fill="var(--wasser,#3f7fb0)"/>')
    # Promenade + Fuge + Nordallee
    o.append(f'<rect x="{pad}" y="{Y(PROMENADE):.0f}" width="{SITE_W}" height="{PROMENADE}" fill="var(--gruen2,#9cc58a)"/>')
    o.append(f'<rect x="{pad+geo["sx0"]:.0f}" y="{Y(geo["y1"]):.0f}" width="{geo["spine"]:.0f}" '
             f'height="{geo["y1"]-geo["y0"]:.0f}" fill="var(--gruen,#6fae5c)"/>')
    # Gartenparzellen in der Fuge (erhaltene Kolonie-Gärten)
    gx0 = pad + geo["sx0"] + 6
    for r in range(int((geo["y1"] - geo["ya"] - 30) // 16)):
        for c in range(int((geo["spine"] - 12) // 14)):
            o.append(f'<rect x="{gx0+c*14:.0f}" y="{Y(geo["y1"]-8-r*16):.0f}" width="11" height="13" '
                     f'fill="var(--parzelle,#b9d98f)" stroke="var(--gruen,#6fae5c)"/>')
    o.append(f'<rect x="{pad}" y="{Y(SITE_H):.0f}" width="{SITE_W}" height="{NORD_STR}" fill="var(--strasse,#d8d0c0)"/>')
    o.append(f'<rect x="{pad}" y="{Y(geo["ya"]+ACHSE_B):.0f}" width="{SITE_W}" height="{ACHSE_B}" fill="var(--strasse,#d8d0c0)"/>')
    farbe = {"K": "var(--mu,#c4553b)", "N": "var(--mu,#c4553b)",
             "W": "var(--wa,#e3b448)", "S": "var(--gb,#5a6fa8)"}
    for b in blocks:
        X, YY = pad + b["x"], Y(b["y"] + b["h"])
        o.append(f'<rect x="{X:.1f}" y="{YY:.1f}" width="{b["w"]:.1f}" height="{b["h"]:.1f}" '
                 f'fill="{farbe[b["zone"]]}"/>')
        if b["zone"] != "S":
            o.append(f'<rect x="{X+TIEFE:.1f}" y="{YY+TIEFE:.1f}" width="{b["w"]-2*TIEFE:.1f}" '
                     f'height="{b["h"]-2*TIEFE:.1f}" fill="var(--hof,#cfe3b8)"/>')
            o.append(f'<rect x="{X+b["w"]/2-4:.1f}" y="{YY:.1f}" width="8" height="{TIEFE}" fill="var(--hof,#cfe3b8)"/>')
        else:
            o.append(f'<rect x="{X+14:.1f}" y="{YY+14:.1f}" width="{b["w"]-28:.1f}" height="{b["h"]-28:.1f}" fill="var(--hof,#cfe3b8)"/>')
        lab = f'{b["g"]}' if b["zone"] != "S" else ""
        o.append(f'<text x="{X+b["w"]/2:.0f}" y="{YY+b["h"]/2+7:.0f}" text-anchor="middle" '
                 f'class="g">{lab}</text>')
        if "hp" in b:
            o.append(f'<rect x="{X+4:.0f}" y="{YY+b["h"]-26:.0f}" width="22" height="22" fill="var(--ink,#1d1d1b)"/>')
            o.append(f'<text x="{X+15:.0f}" y="{YY+b["h"]-9:.0f}" text-anchor="middle" class="hp">{b["hp"]}</text>')
    sx0, sx1, ya, y0, y1 = geo["sx0"], geo["sx1"], geo["ya"], geo["y0"], geo["y1"]
    mx = pad + (sx0 + sx1) / 2
    # Uferstufen am Hafenplatz (Fuge trifft Kanal)
    for k in range(3):
        o.append(f'<rect x="{pad+sx0+6:.0f}" y="{Y(PROMENADE-8-k*7):.0f}" width="{sx1-sx0-12:.0f}" '
                 f'height="5" fill="var(--stufe,#e9e4d6)"/>')
    # Regenwasser-Mulde (Schwammstadt) in der südlichen Fuge
    yy = np.linspace(y0 + 4, ya - 6, 9)
    pts = " ".join(f"{mx + (14 if i % 2 else -14):.0f},{Y(v):.0f}" for i, v in enumerate(yy))
    o.append(f'<polyline points="{pts}" fill="none" stroke="var(--wasser,#3f7fb0)" '
             f'stroke-width="9" stroke-linejoin="round" opacity=".85"/>')
    # Bäume: Achse, Komturstraße, Promenade, Fuge
    o.append('<defs><circle id="t" r="5" fill="var(--baum,#3f7d3a)"/></defs>')
    for xx in np.arange(pad + 8, pad + SITE_W, 16):
        for yv in (ya + ACHSE_B / 2 + 5, ya + ACHSE_B / 2 - 5, SITE_H - NORD_STR / 2, PROMENADE - 4):
            if pad + sx0 < xx < pad + sx1 and yv == PROMENADE - 4:
                continue
            o.append(f'<use href="#t" x="{xx:.0f}" y="{Y(yv):.0f}"/>')
    rng = np.random.default_rng(7)
    for _ in range(26):
        o.append(f'<use href="#t" x="{pad+sx0+8+rng.random()*(sx1-sx0-16):.0f}" '
                 f'y="{Y(y0+8+rng.random()*(ya-y0-16)):.0f}"/>')
    # Quartiersplatz: Kreuzung Fuge x Achse
    o.append(f'<rect x="{pad+sx0:.0f}" y="{Y(ya+ACHSE_B+6):.0f}" width="{sx1-sx0:.0f}" '
             f'height="{ACHSE_B+12}" fill="var(--platz,#f4efe3)" stroke="var(--ink,#1d1d1b)" stroke-width="1.5"/>')
    # Brücke über den Teltowkanal (Fuß/Rad)
    bx_ = pad + sx1 + 10
    o.append(f'<rect x="{bx_:.0f}" y="{Y(0):.0f}" width="9" height="56" fill="var(--weg,#fff)" '
             f'stroke="var(--ink,#1d1d1b)" stroke-width="1"/>')
    # Mobilitätshubs (Quartiersgaragen) an der Komturstraße, Außenecken
    nb = [b for b in blocks if b["zone"] == "N"]
    hubs = [min(nb, key=lambda b: b["x"]), max(nb, key=lambda b: b["x"])] if nb else []
    for b in hubs:
        cx = pad + b["x"] + (TIEFE if b["x"] < 1 else b["w"] - TIEFE) / 1
        o.append(f'<rect x="{cx-11:.0f}" y="{Y(b["y"]+b["h"])+2:.0f}" width="22" height="22" '
                 f'rx="4" fill="var(--ink,#1d1d1b)"/><text x="{cx:.0f}" y="{Y(b["y"]+b["h"])+19:.0f}" '
                 f'text-anchor="middle" class="hp">P</text>')
    # Nummern-Marker (Legende im Dokument)
    sch = [b for b in blocks if b["zone"] == "S"]
    hp = [b for b in blocks if "hp" in b]
    mk = [(1, mx, Y(y1 - 40)), (2, mx, Y(ya + ACHSE_B / 2)), (3, mx, Y(y0 + 40)),
          (4, bx_ + 4, Y(-24)), (8, pad + 40, Y(PROMENADE / 2))]
    if sch:
        mk.append((5, pad + sch[0]["x"] + sch[0]["w"] / 2, Y(sch[0]["y"] + sch[0]["h"] / 2) - 5))
    if hp:
        mk.append((6, pad + hp[0]["x"] + 50, Y(PROMENADE / 2)))
    if nb:
        mk.append((7, pad + nb[-1]["x"] + nb[-1]["w"] - 18, Y(nb[-1]["y"] + 18)))
    for n, cx, cy in mk:
        o.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="13" fill="var(--marker,#fff)" '
                 f'stroke="var(--ink,#1d1d1b)" stroke-width="2"/><text x="{cx:.0f}" y="{cy+5:.0f}" '
                 f'text-anchor="middle" class="m">{n}</text>')
    o.append(f'<g class="nord"><path d="M{W-34} 46 l10 26 l-10 -7 l-10 7z" fill="var(--ink,#1d1d1b)"/>'
             f'<text x="{W-34}" y="36" text-anchor="middle">N</text></g>')
    o.append(f'<g><rect x="{pad}" y="{H-34}" width="100" height="6" fill="var(--ink,#1d1d1b)"/>'
             f'<text x="{pad+110}" y="{H-26}">100 m</text></g>')
    o.append('</svg>')
    return "\n".join(o)


if __name__ == "__main__":
    P, F = nsga2()
    k = knie(F)
    best = P[k]
    _, kenn = bewerten(best)
    pareto = [dict(WE=round(float(f[0])), Gruen=round(float(f[1]), 1),
                   Sonne=round(float(f[2]))) for f in F]
    out = dict(genom={n: (round(float(v), 1) if i < 3 else int(round(float(v))))
                      for i, (n, v) in enumerate(zip(NAMES, best))},
               kennzahlen=kenn, pareto=pareto, knie=k,
               annahmen=dict(Gebiet_m=[SITE_W, SITE_H], Breitengrad=LAT,
                             Sonnenhoehe_TNG=SUN_EQ, WE_BGF=WE_BGF, EW_WE=EW_WE))
    json.dump(out, open("ergebnis.json", "w"), ensure_ascii=False, indent=1)
    open("plan.svg", "w").write(svg(best))
    print(json.dumps(out["genom"], ensure_ascii=False))
    print(json.dumps(kenn, ensure_ascii=False))
    print("Pareto-Lösungen:", len(pareto))
