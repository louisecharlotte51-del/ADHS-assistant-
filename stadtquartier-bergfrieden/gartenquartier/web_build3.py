"""Baut web3/index.html (Schwarzpläne S1-S6) und das Druck-PDF schwarzplaene_S1-S6.pdf (A3 quer)."""
import json, os, shutil, glob, subprocess

W = "web3"
os.makedirs(f"{W}/z", exist_ok=True)
for f in glob.glob("zeichnungen/schwarzplan_S?.svg") + glob.glob("zeichnungen/lesart_S?.svg") + ["zeichnungen/schwarzplaene_uebersicht.svg"]:
    shutil.copy(f, f"{W}/z/")
daten = json.load(open("typologien.json"))
html = open(f"{W}/vorlage.html").read().replace("/*DATA*/", json.dumps(daten, ensure_ascii=False)) \
    .replace("__LINK_V1__", "https://claude.ai/artifact/7XSSdVs4tovei1V22WfnYk") \
    .replace("__LINK_V2__", "https://claude.ai/artifact/GSak6PnuiRjjSXa6nLtkD7")
open(f"{W}/index.html", "w").write(html)

# ---------- Druckfassung A3 quer ----------
komma = lambda z: f"{z:.2f}".replace(".", ",")
inline = lambda p: open(p).read()
seiten = [f'''<section class="s"><h1>Gartenquartier Bergfrieden · Sechs Schwarzpläne</h1>
<p>Typologien mischen: groß an der S-Bahn (P1), wohnlich in der Mitte (P2), Schule und Werkstätten an der Erholungsader (P3), kleinteilig zum Kanal (P4).
Keine Variante nur aus Einzelgebäuden. Abstandsflächen nach BauO Bln eingehalten.</p>
<div class="voll">{inline("zeichnungen/schwarzplaene_uebersicht.svg")}</div></section>''']
for v in daten:
    k = v["kennzahlen"]
    phasen = "".join(f"<li><b>P{j + 1}</b> {t}</li>" for j, t in enumerate(v["phasen"]))
    seiten.append(f'''<section class="s"><div class="zwei"><div>{inline(f"zeichnungen/schwarzplan_{v["code"]}.svg")}</div>
<div>{inline(f"zeichnungen/lesart_{v["code"]}.svg")}</div></div>
<div class="txt"><div><h2>{v["code"]} {v["name"]}</h2><p>{v["text"]}</p><p class="t">{" · ".join(v["typen"])}</p></div>
<ol>{phasen}</ol>
<table><tr><td>GRZ</td><td>{komma(k["grz"])}</td></tr><tr><td>GFZ</td><td>{komma(k["gfz"])}</td></tr><tr><td>Wohnungen</td><td>ca. {k["we"]:,}</td></tr>
<tr><td>ohne Wohnen</td><td>{k["nicht_wohnen"]} %</td></tr><tr><td>max. Geschosse</td><td>{k["g_max"]}</td></tr></table></div></section>'''.replace("ca. 1,", "ca. 1."))
druck = f'''<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><style>
@page{{size:420mm 297mm;margin:10mm}}
body{{margin:0;font:10.5pt/1.4 Archivo,Arial,sans-serif;color:#141414}}
.s{{page-break-after:always;height:277mm;display:flex;flex-direction:column;gap:4mm}}
.s:last-child{{page-break-after:auto}}
h1{{font-size:22pt;margin:0}}h2{{font-size:17pt;margin:0 0 2mm}}p{{margin:0 0 2mm}}
.voll{{flex:1;min-height:0}}.voll svg{{width:100%;height:100%}}
.zwei{{flex:1;min-height:0;display:grid;grid-template-columns:1fr 1fr;gap:6mm}}.zwei svg{{width:100%;height:100%}}
.txt{{display:grid;grid-template-columns:1.3fr 1.6fr .7fr;gap:8mm;border-top:1.5pt solid #141414;padding-top:3mm}}
.t{{color:#555}}ol{{margin:0;padding-left:0;list-style:none}}li{{margin-bottom:1.2mm}}
table{{border-collapse:collapse}}td{{padding:.6mm 3mm .6mm 0}}td+td{{text-align:right;font-weight:700}}
</style></head><body>{"".join(seiten)}</body></html>'''
open("/tmp/claude-0/-home-user-ADHS-assistant-/01adda2c-47b3-5e17-823c-f789e56bd433/scratchpad/schwarzplaene_druck.html", "w").write(druck)
js = """const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage();
await p.goto('file:///tmp/claude-0/-home-user-ADHS-assistant-/01adda2c-47b3-5e17-823c-f789e56bd433/scratchpad/schwarzplaene_druck.html');await p.waitForTimeout(500);
await p.pdf({path:process.argv[2],width:'420mm',height:'297mm',printBackground:true,margin:{top:'10mm',bottom:'10mm',left:'10mm',right:'10mm'}});await b.close()})()"""
open("/tmp/claude-0/-home-user-ADHS-assistant-/01adda2c-47b3-5e17-823c-f789e56bd433/scratchpad/druck_pdf.js", "w").write(js)
subprocess.run(["node", "/tmp/claude-0/-home-user-ADHS-assistant-/01adda2c-47b3-5e17-823c-f789e56bd433/scratchpad/druck_pdf.js", os.path.abspath("schwarzplaene_S1-S6.pdf")], check=True)
print("index.html", len(html) // 1024, "KB | PDF", os.path.getsize("schwarzplaene_S1-S6.pdf") // 1024, "KB")
