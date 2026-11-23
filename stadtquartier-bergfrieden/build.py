"""Füllt vorlage.html mit Plan und Kennzahlen aus dem Modell -> index.html"""
import json
import numpy as np
import generativ_bergfrieden as M

d = json.load(open("ergebnis.json"))
x = np.array(list(d["genom"].values()), float)
blocks, geo = M.layout(x)
k = d["kennzahlen"]


def de(v, nd=0):
    s = f"{v:,.{nd}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# Netto-Kennwerte je Zone und WE je Phase aus der Blockgeometrie
zone = {}
for b in blocks:
    w, h, g = b["w"], b["h"], b["g"]
    ring = (w * h - (w - 2 * M.TIEFE) * (h - 2 * M.TIEFE)) * 0.92
    z = zone.setdefault(b["zone"], dict(f=0, grz=0, bgf=0, we=0))
    z["f"] += w * h
    z["grz"] += ring
    bgf = ring * (3 if b["zone"] == "S" else g) + (22 * 22 * (b["hp"] - g) if "hp" in b else 0)
    z["bgf"] += bgf
    if b["zone"] == "K" or b["zone"] == "N":
        z["we"] += (ring * (g - 1) * 0.85 + (bgf - ring * g)) / M.WE_BGF
    elif b["zone"] == "W":
        z["we"] += ring * (0.85 + g - 1) / M.WE_BGF
for z in zone.values():
    z["GRZ"] = z["grz"] / z["f"]
    z["GFZ"] = z["bgf"] / z["f"]
print({n: (round(z["GRZ"], 2), round(z["GFZ"], 2), round(z["we"])) for n, z in zone.items()})
umf = max(2 * (b["w"] + b["h"]) for b in blocks)
fuge = geo["spine"] * (geo["y1"] - geo["y0"]) / 1e4
r10 = lambda v: de(round(v, -2))

html = open("vorlage.html").read()
p = [q["WE"] for q in d["pareto"]]
rep = {
    "PLAN": open("plan.svg").read(), "DATA": json.dumps(d, ensure_ascii=False),
    "WE": de(k["WE"]), "EW": de(k["EW"]), "AP": de(k["Arbeitsplaetze"]),
    "GFZ": de(k["GFZ_brutto"], 2), "GRZ": de(k["GRZ_brutto"], 2),
    "GRUEN": de(k["Gruen_je_EW"], 1), "SONNE": de(k["Hofbesonnung_pct"]),
    "BGFW": de(k["BGF_Wohnen"]), "BGFG": de(k["BGF_Gewerbe_Gemeinbedarf"]),
    "KITA": de(k["Kita_Plaetze_Bedarf"]), "GS": de(k["Grundschulplaetze_Bedarf"]),
    "STP": de(k["Stellplaetze"]), "BLOECKE": str(k["Bloecke"]),
    "BX": de(blocks[0]["w"]), "BY": de(blocks[0]["h"]),
    "GK": str(d["genom"]["Geschosse Kanalkante"]), "GG": str(d["genom"]["Geschosse Gartenhöfe"]),
    "GN": str(d["genom"]["Geschosse Werkhofkante"]), "HP": str(d["genom"]["Hochpunkt Hafen"]),
    "PMIN": de(min(p)), "PMAX": de(max(p)), "UMF": de(round(umf, -1)), "FUGE": de(fuge, 1),
    "FUGEB": de(geo["spine"]), "EWR": r10(k["EW"]), "APR": r10(k["Arbeitsplaetze"]),
    "P1": r10(zone["K"]["we"]), "P2": r10(zone["N"]["we"]), "P3": r10(zone["W"]["we"]),
}
for n in "KNWS":
    rep[f"GRZ_{n}"] = de(zone[n]["GRZ"], 2)
    rep[f"GFZ_{n}"] = de(zone[n]["GFZ"], 1)
for key, val in rep.items():
    html = html.replace("{{" + key + "}}", val)
left = [t for t in html.split("{{")[1:]]
assert not left, f"Platzhalter offen: {[t[:12] for t in left]}"
open("index.html", "w").write(html)
print("index.html", len(html) // 1024, "KB")
