"""
Nutzungskonzept Gartenquartier Bergfrieden (V6-V8)
==================================================
1. Bedarf aus Einwohnern (Quartier + Nachbarschaft 600 m, ALKIS) nach den
   Schwellen des Mixed-Use-Programming-Skills.
2. Bausteine (Supermarkt, Kitas, Schule, Gesundheitshaus, Kiezzentrum, ...) mit
   Phase, Anker und erlaubten Geschossen -> werden konkreten Häusern zugeordnet.
3. Jedes Gebäude bekommt eine Nutzung je Geschoss.
4. Kennzahlen: Mix, Arbeitsplätze, Versorgungsradien je Phase, 24-h-Test.
Aufruf: python3 nutzungen.py -> nutzung.json, nutzung_geo.json
"""
import json, math
import numpy as np
from shapely.geometry import shape, Point, mapping
from shapely.ops import unary_union
import entwurf as E
import varianten2 as V2
from varianten import hoehe, AKTIV, WASSERNETZ

KAT = {  # Reihenfolge = feste Farbreihenfolge (Dataviz-Palette, validiert)
    "laden": "Nahversorgung und Läden", "gastro": "Gastronomie", "bildung": "Bildung, Soziales, Kultur",
    "gesundheit": "Gesundheit und Pflege", "arbeiten": "Arbeiten: Büro, Werkstatt", "mobilitaet": "Mobilität",
    "wohnen": "Wohnen"}
QM_JE_AP = dict(laden=40, gastro=25, bildung=30, gesundheit=30, arbeiten=25, mobilitaet=400)
WE_BGF, EW_WE = 88.0, 1.9
NACHBARN_600 = 2834          # Einwohner im 600-m-Umkreis (ALKIS-Wohngebäude, konservativ)
NACHBARN_800 = 6052          # Einwohner im 800-m-Umkreis
PHASEN = ["P1", "P2", "P3", "P4"]

ANKER = dict(station=(391330, 5813850), komtur=(391320, 5813690), kreuzung=(391300, 5813470),
             wasser_nord=(391160, 5813770), garten=(391200, 5813720), west=(391100, 5813640),
             ost=(391455, 5813650), erholung_w=(391140, 5813480), sued=(391180, 5813360))

# Bausteine: (Name, Kategorie, BGF, Phase, Anker, Geschosse, Begründung)
BAUSTEINE = [
    ("Supermarkt + Drogerie", "laden", 1400, "P1", "station", [0], "Anker an der S-Bahn; Einzugsbereich Quartier + Nachbarschaft + Pendler"),
    ("Bäckerei-Café am Bahnhofsplatz", "gastro", 180, "P1", "station", [0], "Morgens die ersten, abends die letzten"),
    ("Coworking und Büros", "arbeiten", 1600, "P1", "station", [1, 2], "Arbeitsplätze an der Station, Tagbelebung"),
    ("Kita „Am Feld“ (80 Plätze)", "bildung", 700, "P1", "wasser_nord", [0, 1], "Bedarf ab dem ersten Bezug; Garten an der Wasserader"),
    ("Kiezzentrum „Gartenhaus“", "bildung", 900, "P1", "garten", [0, 1], "Nachbarschaftshaus, Gartenwerkstatt, Vereinsraum der Kleingärtner"),
    ("Hausarztpraxis + Apotheke", "gesundheit", 450, "P1", "station", [0, 1], "Grundversorgung ab Phase 1"),
    ("Gesundheitshaus (MVZ, Physio)", "gesundheit", 1400, "P2", "komtur", [0, 1, 2], "1 je 5.000–10.000 Menschen; an der Bewegungsader"),
    ("Tagespflege + Pflege-WG", "gesundheit", 900, "P2", "west", [0, 1], "Ruhige Lage an der Wasserader"),
    ("Kita „Grünraum Ost“ (60 Plätze)", "bildung", 520, "P2", "ost", [0, 1], "Bedarf wächst mit Phase 2"),
    ("Läden an der Komturstraße", "laden", 600, "P2", "komtur", [0], "Friseur, Paketshop, Bioladen"),
    ("Café an der Wasserader", "gastro", 250, "P2", "garten", [0], "Am Schwammknoten, Terrasse zum Wasser"),
    ("Jugendclub", "bildung", 400, "P3", "kreuzung", [0], "Nah an Schule und Sport"),
    ("Gastronomie an der Kreuzung", "gastro", 450, "P3", "kreuzung", [0], "Wo Bewegungs- und Erholungsader sich kreuzen"),
    ("Werkstätten an der Erholungsader", "arbeiten", 1200, "P3", "erholung_w", [0, 1], "Handwerk, Ateliers, Reparatur"),
    ("Kita „Am Kanal“ (60 Plätze)", "bildung", 520, "P4", "sued", [0, 1], "Nur wenn der Platzbedarf es verlangt"),
    ("Läden und Gastro an der Albrechtstraße", "laden", 500, "P4", "sued", [0], "Weg zum Quartiershauptplatz"),
    ("Werkstätten an der Albrechtstraße", "arbeiten", 900, "P4", "sued", [0, 1], "Übergang zum Gewerbe am Kanal"),
]
# Feste Orte: Sonderbauten und Bestand
FEST = [
    ("Mobilitätshub Nord", "mobilitaet", "P1", "Fahrradparken (600 Räder), Carsharing, Lastenräder, ca. 110 Stellplätze auf 3 Ebenen", "hub"),
    ("Werkhof Nord (Bestand)", "arbeiten", "P1", "Werkstatt und Fabrik bleiben: Makerspace, Repair-Café, Handwerk", "bestand_nord"),
    ("Bildungscampus: Grundschule + Sporthalle", "bildung", "P3", "3-zügig, Halle abends für Vereine; Baufeld 6", "schule"),
    ("Sport- und Kulturhaus (Bestand)", "bildung", "P3", "Geschäftshaus umgenutzt: Kletterhalle, Bibliothek, Probenräume", "bestand_sued"),
    ("Mobilitätshub Süd (Bestand-Tiefgarage)", "mobilitaet", "P4", "Vorhandene Tiefgarage, 2 Ebenen, ca. 230 Stellplätze", "tg"),
    ("Markthalle am Quartiershauptplatz", "gastro", "P4", "Bestandshalle am Kanal umgebaut: Markt, Gastro, Events", "markthalle"),
]


def bestand_orte():
    nord = [b for b in E.BESTAND if b["geo"].representative_point().within(E.OST_NORD)]
    sued = [b for b in E.BESTAND if b["geo"].representative_point().within(E.OST_SUED)]
    gesch = max((b for b in sued if (b["typ"] or "").startswith("Geschäft")), key=lambda b: b["geo"].area)
    tg = [b for b in sued if b["typ"] == "Tiefgarage"]
    geb = json.load(open(E.DAT + "geb.json"))["features"]
    halle = min((shape(f["geometry"]) for f in geb if shape(f["geometry"]).area > 400), key=lambda g: g.distance(E.PLATZ))
    return dict(bestand_nord=unary_union([b["geo"] for b in nord]), bestand_sued=gesch["geo"],
                tg=tg[0]["geo"] if tg else gesch["geo"], markthalle=halle)


def zuordnen(code, haeuser, plaetze):
    # Grundbelegung je Geschoss
    for h in haeuser:
        t = h["typ"]
        if t in ("schule", "sporthalle"):
            h["nutz"] = ["bildung"] * h["g"]
        elif t == "mobilitaet":
            h["nutz"] = ["mobilitaet"] * h["g"]
        elif t == "sockel":
            h["nutz"] = ["wohnen"]            # Gartenwohnungen, Ateliers, Fahrradräume
        else:
            h["nutz"] = ["wohnen"] * h["g"]
    belegbar = [h for h in haeuser if h["typ"] not in ("schule", "sporthalle", "mobilitaet")]
    ew_end = sum(h["geo"].area * h["g"] for h in haeuser if h["typ"] not in ("schule", "sporthalle", "mobilitaet", "sockel")) \
        / WE_BGF * EW_WE
    kita_bedarf = ew_end * 0.045
    orte = []
    vergeben = 0
    for name, kat, bgf, ph, anker, gesch, grund in BAUSTEINE:
        if name.startswith("Kita „Am Kanal“") and kita_bedarf <= 140:
            continue                                     # dritte Kita nur bei Bedarf
        if name.startswith("Kita „Grünraum Ost“") and kita_bedarf <= 80:
            continue
        a = Point(ANKER[anker])
        if name.startswith("Supermarkt"):
            # Regel: Supermarkt nur in EINEM Haus mit >= 1.000 m² Grundfläche, sonst im EG des Mobilitätshubs
            gross = [h for h in belegbar if h["phase"] == ph and h["geo"].area >= 1000 and h["nutz"][0] == "wohnen"]
            socks = [h for h in belegbar if h["typ"] == "sockel" and h["phase"] == ph and h["nutz"][0] == "wohnen"]
            deck = None
            if not gross and socks:                         # V7: zusammenhängende Sockeleinheiten eines Decks
                decks = unary_union([h["geo"].buffer(0.4) for h in socks])
                for d in sorted(getattr(decks, "geoms", [decks]), key=lambda d: d.distance(a)):
                    teile = sorted([h for h in socks if h["geo"].representative_point().within(d)],
                                   key=lambda h: h["geo"].distance(a))
                    if sum(t["geo"].area for t in teile) >= 1000:
                        deck, summe = [], 0.0
                        for t in teile:
                            if summe >= bgf:
                                break
                            deck.append(t)
                            summe += t["geo"].area
                        break
            if gross:
                h = min(gross, key=lambda h: h["geo"].distance(a))
                h["nutz"][0], h["fest_0"] = kat, name
                wo, bgf_ist, grund_ist = h, h["geo"].area, grund + "; ein Haus, eine Ebene"
            elif deck:
                for t in deck:
                    t["nutz"][0], t["fest_0"] = kat, name
                wo = dict(geo=unary_union([t["geo"] for t in deck]), feld=deck[0]["feld"])
                bgf_ist, grund_ist = sum(t["geo"].area for t in deck), grund + "; unter dem Gartendeck, eine Ebene"
            else:
                wo = next(h for h in haeuser if h["typ"] == "mobilitaet")
                wo["nutz"][0], wo["fest_0"] = kat, name
                bgf_ist, grund_ist = wo["geo"].area, grund + "; im EG des Mobilitätshubs (kein Baufeldhaus groß genug)"
            p = wo["geo"].representative_point()
            orte.append(dict(name=name, kat=kat, phase=ph, bgf=round(bgf_ist), soll=bgf, grund=grund_ist, x=round(p.x, 1),
                             y=round(p.y, 1), felder=[wo["feld"]] if wo.get("feld") else [], geschosse=[1]))
            continue
        kand = sorted([h for h in belegbar if PHASEN.index(h["phase"]) <= PHASEN.index(ph) and h["phase"] == ph] or
                      [h for h in belegbar if h["phase"] == ph], key=lambda h: h["geo"].distance(a))
        rest, wirte = bgf, []
        pool = kand[:10]                                     # nur Häuser nahe am Anker
        while rest > 0 and pool:
            # Regel: Geschossfläche passend zum Bedarf (<= 130 %), sonst das nächste Haus
            passend = [h for h in pool if h["geo"].area <= max(rest * 1.3, 160)]
            h = passend[0] if passend else pool[0]
            pool.remove(h)
            fp = h["geo"].area
            for gi in gesch:
                if h["typ"] == "turm" and gi == 0:
                    continue                                 # EG der Türme liegt im Sockel
                if gi < h["g"] and h["nutz"][gi] in ("wohnen", "arbeiten") and rest > 0 and not h.get("fest_" + str(gi)):
                    h["nutz"][gi] = kat
                    h["fest_" + str(gi)] = name
                    rest -= fp
                    if h not in wirte:
                        wirte.append(h)
        if wirte:
            p = unary_union([w["geo"] for w in wirte]).representative_point()
            orte.append(dict(name=name, kat=kat, phase=ph, bgf=round(bgf - min(rest, 0) if rest < 0 else bgf - rest),
                             soll=bgf, grund=grund, x=round(p.x, 1), y=round(p.y, 1),
                             felder=sorted({w["feld"] for w in wirte}), geschosse=[g + 1 for g in gesch]))
            vergeben += 1
    # Feste Orte
    bo = bestand_orte()
    for name, kat, ph, grund, wo in FEST:
        if wo == "hub":
            hub = next(h for h in haeuser if h["typ"] == "mobilitaet")
            geo = hub["geo"]
        elif wo == "schule":
            geo = unary_union([h["geo"] for h in haeuser if h["typ"] in ("schule", "sporthalle")])
        else:
            geo = bo[wo]
        p = geo.representative_point()
        bgf = round(sum(h["geo"].area * h["g"] for h in haeuser if h["typ"] in ("schule", "sporthalle"))) if wo == "schule" else \
            round(geo.area * ((4 if hub["nutz"][0] == "mobilitaet" else 3) if wo == "hub" else 2 if wo in ("tg", "bestand_nord") else 3 if wo == "bestand_sued" else 1))
        orte.append(dict(name=name, kat=kat, phase=ph, bgf=bgf, soll=bgf, grund=grund, x=round(p.x, 1), y=round(p.y, 1),
                         felder=[6] if wo == "schule" else [], geschosse=[], bestand=wo.startswith("bestand") or wo in ("tg", "markthalle")))
    # Aktive Erdgeschosse: an Adern, Trichtern, Station -> Läden/Gastro (kleinteilig)
    for k, h in enumerate(haeuser):
        if h["typ"] in ("schule", "sporthalle", "mobilitaet", "turm") or h.get("fest_0"):
            continue
        if h["geo"].intersects(AKTIV) and h["nutz"][0] in ("wohnen", "arbeiten"):
            nah_wasser = h["geo"].distance(E.SCHWAMM_FL) < 8
            h["nutz"][0] = "gastro" if (nah_wasser and k % 3 == 0) else "laden" if k % 3 == 0 else "arbeiten"
    # V8: Platzhaus je Insel (Café oder Kita-Gruppe)
    for j, pl in enumerate(plaetze):
        nah = [h for h in haeuser if h["typ"] == "insel" and h["geo"].distance(pl["geo"]) < 6 and not h.get("fest_0")]
        if nah:
            h = min(nah, key=lambda h: h["geo"].distance(pl["geo"].centroid))
            h["nutz"][0] = "gastro" if j % 2 == 0 else "bildung"
    # Türme im Gartendeck: Geschosse 1-2 liegen im Sockel
    for h in haeuser:
        if h["typ"] == "turm":
            sockel = min((s for s in haeuser if s["typ"] == "sockel"), key=lambda s: s["geo"].distance(h["geo"]))
            h["nutz"][0] = sockel["nutz"][0]
    return orte, kita_bedarf


def kennzahlen(code, haeuser, orte, kita_bedarf):
    bgf = {k: 0.0 for k in KAT}
    for h in haeuser:
        fp = h["geo"].area
        for gi, n in enumerate(h["nutz"]):
            if h["typ"] == "turm" and gi < 1:
                continue                                     # im Sockel bereits gezählt
            bgf[n] += fp
    gesamt = sum(bgf.values())
    we = bgf["wohnen"] / WE_BGF
    ew = we * EW_WE
    ap = sum(bgf[k] / QM_JE_AP[k] for k in QM_JE_AP)
    # Phasen: BGF je Kategorie kumuliert
    phasen = {}
    for i, ph in enumerate(PHASEN):
        sel = [h for h in haeuser if PHASEN.index(h["phase"]) <= i]
        d = {k: 0.0 for k in KAT}
        for h in sel:
            for gi, n in enumerate(h["nutz"]):
                if not (h["typ"] == "turm" and gi < 1):
                    d[n] += h["geo"].area
        phasen[ph] = {k: round(v) for k, v in d.items()}
        phasen[ph]["we"] = round(d["wohnen"] / WE_BGF)
    # Versorgung: Anteil Wohnfläche im Radius, je Phase (Orte, die in der Phase existieren)
    radien = dict(nahversorgung=("Supermarkt", 500), kita=("Kita", 400), schule=("Grundschule", 700),
                  arzt=("praxis|Gesundheitshaus", 600), kiez=("Kiezzentrum|Jugendclub|Sport- und Kultur", 600))
    import re
    versorgung = {}
    for i, ph in enumerate(PHASEN):
        wohn = [(h["geo"].centroid, h["geo"].area * sum(1 for n in h["nutz"] if n == "wohnen"))
                for h in haeuser if PHASEN.index(h["phase"]) <= i]
        summe = sum(w for _, w in wohn) or 1
        versorgung[ph] = {}
        for key, (muster, r) in radien.items():
            pts = [Point(o["x"], o["y"]) for o in orte if re.search(muster, o["name"]) and PHASEN.index(o["phase"]) <= i]
            gedeckt = sum(w for c, w in wohn if any(c.distance(p) <= r for p in pts))
            versorgung[ph][key] = round(100 * gedeckt / summe)
    kita_plaetze = sum(int(re.search(r"\((\d+) Plätze\)", o["name"]).group(1)) for o in orte if "Plätze" in o["name"])
    dachgaerten = 0.0
    if code == "V7":
        sockel = unary_union([h["geo"] for h in haeuser if h["typ"] == "sockel"])
        tuerme = unary_union([h["geo"] for h in haeuser if h["typ"] == "turm"])
        dachgaerten = sockel.difference(tuerme.buffer(3)).area * 0.7
    einzug = ew + NACHBARN_800
    # mittlere Wege von Wohnungen zu den Bausteinen (Luftlinie) in der Endphase
    def weg(muster):
        pts = [Point(o["x"], o["y"]) for o in orte if re.search(muster, o["name"])]
        wohn = [(h["geo"].centroid, h["geo"].area) for h in haeuser if "wohnen" in h["nutz"]]
        if not pts or not wohn:
            return None
        return round(sum(min(c.distance(p) for p in pts) * w for c, w in wohn) / sum(w for _, w in wohn))
    wege = dict(supermarkt=weg("Supermarkt"), kita=weg("Kita"), schule=weg("Grundschule"),
                arzt=weg("praxis|Gesundheitshaus"), sbahn=round(sum(h["geo"].centroid.distance(E.STATION) * h["geo"].area
                                                                    for h in haeuser if "wohnen" in h["nutz"])
                                                               / max(1, sum(h["geo"].area for h in haeuser if "wohnen" in h["nutz"]))))
    return dict(bgf={k: round(v) for k, v in bgf.items()}, bgf_gesamt=round(gesamt),
                anteil_nicht_wohnen=round(100 * (1 - bgf["wohnen"] / gesamt)), we=round(we), ew=round(ew),
                arbeitsplaetze=round(ap), gfz_brutto=round(gesamt / E.GEBIET.area, 2),
                kita_bedarf=round(kita_bedarf), kita_plaetze=kita_plaetze, grundschul_bedarf=round(ew * 0.05),
                einzugsbereich_supermarkt=round(einzug), supermarkt_tragfaehig=einzug >= 5000,
                dachgaerten_m2=round(dachgaerten), ersatzparzellen_dach=round(dachgaerten / 150),
                phasen=phasen, versorgung=versorgung, wege=wege, gebaeude=len(haeuser),
                geschosse_max=max(h["g"] for h in haeuser))


TAGESZEIT = [("6–9 Uhr", ["wohnen", "laden", "gastro", "mobilitaet"]), ("9–12 Uhr", ["arbeiten", "bildung", "gesundheit"]),
             ("12–14 Uhr", ["gastro", "arbeiten", "laden"]), ("14–17 Uhr", ["bildung", "laden", "gesundheit"]),
             ("17–20 Uhr", ["wohnen", "laden", "gastro", "bildung"]), ("20–23 Uhr", ["wohnen", "gastro", "bildung"]),
             ("Wochenende", ["gastro", "laden", "bildung", "wohnen"])]

if __name__ == "__main__":
    alle, plaetze = V2.generiere()
    out = dict(kategorien=KAT, varianten=[], nachbarn_600=NACHBARN_600, tageszeit=TAGESZEIT)
    geo = {}
    for code, name, _fn, text in V2.VARIANTEN2:
        hs = alle[code]["haeuser"]
        orte, kb = zuordnen(code, hs, plaetze[code])
        k = kennzahlen(code, hs, orte, kb)
        out["varianten"].append(dict(code=code, name=name, text=text, kennzahlen=k, orte=orte,
                                     eingriffe=alle[code]["eingriffe"]))
        geo[code] = dict(haeuser=[dict(geo=mapping(h["geo"]), g=h["g"], typ=h["typ"], phase=h["phase"], feld=h["feld"],
                                       nutz=h["nutz"]) for h in hs],
                         plaetze=[dict(geo=mapping(p["geo"]), phase=p["phase"]) for p in plaetze[code]])
        b = k["bgf"]
        print(f'{code} {name:20s} WE {k["we"]:5d} EW {k["ew"]:5d} AP {k["arbeitsplaetze"]:5d} nicht-Wohnen {k["anteil_nicht_wohnen"]}%'
              f' GFZbr {k["gfz_brutto"]}  Kita {k["kita_plaetze"]}/{k["kita_bedarf"]}  Einzug {k["einzugsbereich_supermarkt"]}'
              f'  Dach {k["dachgaerten_m2"]} m²  Orte {len(orte)}')
        print("   BGF", {kk: v for kk, v in b.items()})
        print("   Versorgung", k["versorgung"])
    json.dump(out, open("nutzung.json", "w"), ensure_ascii=False, indent=1)
    json.dump(geo, open("nutzung_geo.json", "w"))
