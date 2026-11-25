"""A3-PDF (quer): Situationsskizzen der Adern und Plätze, Renderings, Luftbilder und Schnittperspektiven S1-S6.
Aufruf: python3 situationen_pdf.py -> situationen_renderings.pdf"""
import json, os, base64, subprocess

SP = os.environ.get("SKIZZEN_TMP", "/tmp/claude-0/-home-user-ADHS-assistant-/01adda2c-47b3-5e17-823c-f789e56bd433/scratchpad")
TYP = {v["code"]: v for v in json.load(open("typologien.json"))}
SIT = [("wasserader", "Wasserader", ["Kühlung vor Ort", "Erholungsbereich offen", "verbindet Kanal und Tempelhofer Feld"],
        "Offener Bach mit Schilfufern, Teiche an den Schwammknoten, Trittsteine und Holzdecks, Kiesweg am Wasser."),
       ("bewegungsader", "Bewegungsader Komturstraße", ["2 Verkehrsachsen", "Auto, Fahrrad, Fußgänger", "Straßenbegleitgrün", "Tempo 30"],
        "Zweirichtungs-Radweg in der Mitte zwischen Pflanzstreifen, Rasengitter zum Liefern, breite Gehwege, Baumreihen, Café-Pavillon."),
       ("erholungsader", "Erholungsader (Flanierachse)", ["Biodiversität steigern", "Raum für Entschleunigung und Ruhe",
                                                         "Verbindung zwischen Parks", "Nischenparks, Spielplätze"],
        "Geschwungene Wege durch Staudenbeete, Rasenlichtungen, Pergolen, Spielplatz."),
       ("quartiersplatz", "Quartiershauptplatz am Kanal", ["Mischung Grünraum, Gastro, Wasser/Retention", "Umlenkung der Verkehrsachsen",
                                                         "Gewerbe und Nutzungsmischung um den Platz"],
        "Pflanzinseln, Café-Tische an der Markthalle, Kioske, Sitzstufen zum Kanal, Retentionsbecken mit Trittsteinen."),
       ("gartenfuge", "Nachbarschaftsgarten in der Gartenfuge", ["Pocketparks", "Gemeinschaftsgärten", "Urban Gardening", "Spielplatz"],
        "Hochbeete, offene Regenrinne, Blütenbäume, Bänke und Sandspiel zwischen zwei Zeilen.")]


def bild(pfad):
    return "data:image/jpeg;base64," + base64.b64encode(open(pfad, "rb").read()).decode()


seiten = []
for k, titel, regeln, text in SIT:
    if not os.path.exists(f"web3/r/skizze_{k}.jpg"):
        continue
    seiten.append(f'''<section class="s"><div class="gross"><img src="{bild(f"web3/r/skizze_{k}.jpg")}"></div>
<div class="leiste"><h2>{titel}</h2><ul class="hand">{"".join(f"<li>{r}</li>" for r in regeln)}</ul><p>{text}</p>
<img class="klein" src="{bild(f"web3/r/rendering_{k}.jpg")}"><p class="u">Rendering derselben Situation · Bebauung: Variante S4</p></div></section>''')
for art, titel in (("luft", "Luftbild aus Südwesten"), ("schnittperspektive", "Schnittperspektive A–A")):
    kacheln = "".join(f'<figure><img src="{bild(f"web3/r/{art}_{c}.jpg")}"><figcaption>{c} {TYP[c]["name"]}</figcaption></figure>'
                      for c in TYP if os.path.exists(f"web3/r/{art}_{c}.jpg"))
    if kacheln:
        seiten.append(f'<section class="s"><h2>{titel} · S1–S6</h2><div class="raster">{kacheln}</div></section>')
html = f'''<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><style>
@page{{size:420mm 297mm;margin:10mm}}
body{{margin:0;font:10.5pt/1.4 Archivo,Arial,sans-serif;color:#141414}}
.s{{height:276mm;display:flex;gap:7mm;overflow:hidden}}.s+.s{{page-break-before:always}}
.gross{{flex:0 0 72%;display:flex;align-items:center}}.gross img{{width:100%;border-radius:2mm}}
.leiste{{flex:1;display:flex;flex-direction:column;gap:3mm;border-left:1.5pt solid #141414;padding-left:6mm}}
h2{{font-size:19pt;margin:0;line-height:1.05}}.hand{{font-family:Caveat,cursive;font-size:17pt;color:#2e8b3a;list-style:none;padding:0;margin:0}}
.hand li::before{{content:"– "}}.klein{{width:100%;border-radius:2mm;margin-top:auto}}.u{{color:#666;font-size:9pt}}
.raster{{display:grid;grid-template-columns:repeat(3,1fr);gap:4mm;width:100%}}figure{{margin:0}}figure img{{width:100%;display:block}}
figcaption{{font-size:9.5pt;margin-top:1mm}}section.s:has(.raster){{flex-direction:column}}
</style></head><body>{"".join(seiten)}</body></html>'''
open(f"{SP}/situationen_druck.html", "w").write(html)
js = """const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage();
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(800);
await p.pdf({path:process.argv[3],width:'420mm',height:'297mm',printBackground:true,margin:{top:'10mm',bottom:'10mm',left:'10mm',right:'10mm'}});await b.close()})()"""
open(f"{SP}/situationen_pdf.js", "w").write(js)
subprocess.run(["node", f"{SP}/situationen_pdf.js", f"{SP}/situationen_druck.html", os.path.abspath("situationen_renderings.pdf")], check=True)
print("PDF", len(seiten), "Seiten,", os.path.getsize("situationen_renderings.pdf") // 1024, "KB")
