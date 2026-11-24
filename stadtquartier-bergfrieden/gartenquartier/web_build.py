"""Baut web/index.html + Assets (Renderings als JPG, Zeichnungen, GLB)."""
import json, os, shutil, glob
from PIL import Image

W = "web"
for d in ("r", "z", "3d"):
    os.makedirs(f"{W}/{d}", exist_ok=True)

for f in glob.glob("3d/render_V?.png") + glob.glob("3d/render_V4_nah.png"):
    im = Image.open(f).convert("RGB")
    name = os.path.basename(f)[:-4]
    g = im.copy(); g.thumbnail((1600, 1600), Image.LANCZOS); g.save(f"{W}/r/{name}.jpg", quality=86, optimize=True, progressive=True)
    k = im.copy(); k.thumbnail((560, 560), Image.LANCZOS); k.save(f"{W}/r/{name}_k.jpg", quality=82, optimize=True)
for f in glob.glob("3d/phase_V?_P?.png"):
    im = Image.open(f).convert("RGB")
    im.thumbnail((960, 960), Image.LANCZOS)
    im.save(f"{W}/r/{os.path.basename(f)[:-4]}.jpg", quality=84, optimize=True, progressive=True)
for f in glob.glob("zeichnungen/schritt_*.svg") + glob.glob("zeichnungen/lageplan_V?.svg") + glob.glob("zeichnungen/schnitt_*_V?.svg"):
    shutil.copy(f, f"{W}/z/")
for f in glob.glob(f"{W}/3d/*"):
    os.remove(f)
import struct, base64
for f in glob.glob("3d/*.glb"):                        # GLB -> eingebettetes glTF (JSON) für den Artefakt-Server
    b = open(f, "rb").read()
    n = struct.unpack("<I", b[12:16])[0]
    gltf = json.loads(b[20:20 + n])
    bin_len = struct.unpack("<I", b[20 + n:24 + n])[0]
    binaer = b[28 + n:28 + n + bin_len]
    gltf["buffers"] = [dict(byteLength=len(binaer), uri="data:application/octet-stream;base64," + base64.b64encode(binaer).decode())]
    json.dump(gltf, open(f"{W}/3d/{os.path.basename(f)[:-4]}.json", "w"), separators=(",", ":"))

var = json.load(open("varianten.json"))
daten = dict(varianten=var["varianten"], felder=var["felder"], regeln=json.load(open("regeln.json")))
html = open(f"{W}/vorlage.html").read().replace("/*DATA*/", json.dumps(daten, ensure_ascii=False))
open(f"{W}/index.html", "w").write(html)
gr = lambda p: sum(os.path.getsize(x) for x in glob.glob(p))
print("index.html", len(html) // 1024, "KB | r", gr(f"{W}/r/*") // 1024, "KB | z", gr(f"{W}/z/*") // 1024,
      "KB | 3d", gr(f"{W}/3d/*") // 1024, "KB")
