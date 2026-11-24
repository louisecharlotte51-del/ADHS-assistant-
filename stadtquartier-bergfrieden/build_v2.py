"""Baut index.html (v2, echte Geometrie) aus Modell, Daten und Vorlagen."""
import json, math
from shapely.geometry import shape
from shapely.ops import unary_union
import generativ_v2_real as V

d = json.load(open("ergebnis_v2.json"))
k = d["kennzahlen"]
x = list(d["genom"].values())
blocks, geo = V.layout(x)


def de(v, nd=0):
    return f"{v:,.{nd}f}".replace(",", "X").replace(".", ",").replace("X", ".")


r100 = lambda v: de(round(v, -2))

# Nettokennwerte je Zone
z = {}
for b in blocks:
    p, g = b["geo"], b["g"]
    if b["typ"] == "solitaer":
        fp = p.area * 0.42
    else:
        fp = (p.area - p.buffer(-V.TIEFE, join_style=2).area) * 0.92
    bgf = fp * g + (24 * 24 * (b["hp"] - g) if "hp" in b else 0)
    e = z.setdefault(b["zone"], dict(f=0, fp=0, bgf=0))
    e["f"] += p.area; e["fp"] += fp; e["bgf"] += bgf

# Schatten der Gartenkante auf die Kolonie
K1 = unary_union([shape(f["geometry"]) for f in V.KEP if f["properties"]["entwicklung"].startswith("1")])
gg = d["genom"]["Geschosse Gartenkante"]
schatten = V.hoehe(gg) / math.tan(math.radians(V.SUN_EQ))
abst = min(b["geo"].distance(K1) for b in blocks if b["zone"] in "GM")

kat = {"1": "1 · dauerhaft gesichert", "3": "3 · langfristige Perspektive", "4": "4 · bauliche Entwicklung"}
rows = []
for f in sorted(V.KEP, key=lambda f: -f["properties"]["fl_in_m2"]):
    p = f["properties"]
    name = p["name_der_k"] + (f" ({p['teil']})" if p["teil"] not in ("-", None) else "")
    bold = "<b>{}</b>" if p["name_der_k"] == "Bergfrieden" else "{}"
    rows.append(f'<tr><td>{bold.format(name)}</td><td class="n">{de(p["fl_in_m2"])} m²</td>'
                f'<td class="n">{p["parzellen"]}</td><td>{kat.get(p["entwicklung"][0], p["entwicklung"])}</td>'
                f'<td>{p["bem_entw"]}</td></tr>')

head = open("vorlage.html").read().split("</head>")[0]
head = head.replace("--marker:light-dark(#ffffff,#f3f1ea)}",
                    "--marker:light-dark(#ffffff,#f3f1ea);--wohnbest:light-dark(#e6dcc6,#2c2a24);"
                    "--gewbest:light-dark(#e2dcd2,#2a2824);--gbbest:light-dark(#dcd3e6,#2a2630);"
                    "--k3:light-dark(#d9e6b0,#4a5a32);--best:light-dark(#b9b2a4,#55514a);"
                    "--gew:light-dark(#8f6fa8,#7a5c93)}")
head = head.replace("--strasse:light-dark(#d8d0c0,#3a3a33)", "--strasse:light-dark(#ffffff,#3a3a33)")
assert "--gew:" in head
html = head + "</head>\n" + open("vorlage_v2_body.html").read()

flaeche = (V.FELD["Nordfeld"].area + V.FELD["Südfeld"].area)
p = [q["WE"] for q in d["pareto"]]
rep = dict(
    PLAN=open("plan_v2.svg").read(), DATA=json.dumps(d, ensure_ascii=False),
    GEBIET=de(k["Gebiet_ha"], 1), NORDHA=de(k["Nordfeld_ha"], 1), SUEDHA=de(k["Suedfeld_ha"], 1),
    WE=de(k["WE"]), WER=r100(k["WE"]), EW=de(k["EW"]), AP=de(k["Arbeitsplaetze"]),
    APR=r100(k["Arbeitsplaetze"]), APB=r100(k["Arbeitsplaetze_Bestand_ca"]),
    GRUEN=de(k["Gruen_je_EW"], 1), GRUENM2=de(k["Gruen_neu_m2"]), NPARETO=str(len(p)),
    K1HA=de(K1.area / 1e4, 1), FUGEB=de(d["genom"]["Breite Gartenfuge"]), PROMB=de(d["genom"]["Breite Uferpromenade"]),
    HP=str(d["genom"]["Hochpunkt Ordensmeisterstraße"]), GG=str(gg), GW=str(d["genom"]["Geschosse Werkkante"]),
    BX=de(d["genom"]["Blocklänge"]), BLOECKE=str(k["Bloecke"]), GFZS=de(d["genom"]["GFZ Südfeld (Gewerbe)"], 1),
    BESTBGF=r100(k["Bestand_BGF"]), SUEDBGF=r100(json.load(open("daten/bestand.json"))["suedfeld"]["bgf"]),
    HG=de(V.hoehe(gg), 1), SCHATTEN=de(schatten), INTRUSION=de(max(0, schatten - abst)),
    SONNE=str(k["Hofbesonnung_pct"]), PMIN=de(min(p)), PMAX=de(max(p)),
    BGFW=de(k["BGF_Wohnen"]), BGFG=de(k["BGF_Gewerbe"]), BGFS=de(k["BGF_Gewerbe_Sued"]),
    GFZ=de(k["GFZ_brutto"], 2), GFZB=de(k["Bestand_BGF"] / flaeche, 2),
    KITA=de(k["Kita_Plaetze_Bedarf"]), GS=de(k["Grundschulplaetze_Bedarf"]), STP=de(k["Stellplaetze"]),
    KEPROWS="\n".join(rows),
)
for n in "GWM":
    rep[f"GRZ_{n}"] = de(z[n]["fp"] / z[n]["f"], 2) if n in z else "–"
    rep[f"GFZ_{n}"] = de(z[n]["bgf"] / z[n]["f"], 1) if n in z else "–"
for a, b in rep.items():
    html = html.replace("{{" + a + "}}", b)
offen = [t[:14] for t in html.split("{{")[1:]]
assert not offen, offen
open("index.html", "w").write(html)
print("index.html", len(html) // 1024, "KB | Schatten", round(schatten, 1), "Abstand", round(abst, 1),
      {n: (round(e["fp"] / e["f"], 2), round(e["bgf"] / e["f"], 2)) for n, e in z.items()})
