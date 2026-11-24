"""Baut web2/index.html (Phase 1 und Nutzungen, V6-V8) + Assets: Renderings als JPG, Zeichnungen, glTF als JSON."""
import json, os, shutil, glob, struct, base64
from PIL import Image
import entwurf as E
import nutzungen as N
from zeichnungen2 import NF, KURZ

W = "web2"
for d in ("r", "z", "3d"):
    os.makedirs(f"{W}/{d}", exist_ok=True)
CODES = ("V6", "V7", "V8")

for f in [f"3d/render_{c}.png" for c in CODES] + [f"3d/p1_{c}.png" for c in CODES]:
    if os.path.exists(f):
        im = Image.open(f).convert("RGB")
        im.thumbnail((1600, 1600), Image.LANCZOS)
        im.save(f"{W}/r/{os.path.basename(f)[:-4]}.jpg", quality=86, optimize=True, progressive=True)
for c in CODES:
    for f in glob.glob(f"3d/phase_{c}_P?.png"):
        im = Image.open(f).convert("RGB")
        im.thumbnail((1280, 1280), Image.LANCZOS)
        im.save(f"{W}/r/{os.path.basename(f)[:-4]}.jpg", quality=84, optimize=True, progressive=True)
for art in ("phase1", "nutzplan", "nutzschnitt1", "nutzschnitt_ns", "nutzphasen"):
    for c in CODES:
        shutil.copy(f"zeichnungen/{art}_{c}.svg", f"{W}/z/")
for f in glob.glob(f"{W}/3d/*"):
    os.remove(f)
for f in ["3d/kontext.glb"] + [f"3d/{c}.glb" for c in CODES]:     # GLB -> eingebettetes glTF (JSON)
    b = open(f, "rb").read()
    n = struct.unpack("<I", b[12:16])[0]
    gltf = json.loads(b[20:20 + n])
    bin_len = struct.unpack("<I", b[20 + n:24 + n])[0]
    binaer = b[28 + n:28 + n + bin_len]
    gltf["buffers"] = [dict(byteLength=len(binaer), uri="data:application/octet-stream;base64," + base64.b64encode(binaer).decode())]
    json.dump(gltf, open(f"{W}/3d/{os.path.basename(f)[:-4]}.json", "w"), separators=(",", ":"))

nutz = json.load(open("nutzung.json"))
daten = dict(nutzung=nutz, farben=NF, kurz=KURZ, phasen=[list(p) for p in E.PHASEN], qm_ap=N.QM_JE_AP)
html = open(f"{W}/vorlage.html").read().replace("/*DATA*/", json.dumps(daten, ensure_ascii=False)) \
    .replace("__LINK_V1__", "https://claude.ai/artifact/7XSSdVs4tovei1V22WfnYk")
open(f"{W}/index.html", "w").write(html)
gr = lambda p: sum(os.path.getsize(x) for x in glob.glob(p))
print("index.html", len(html) // 1024, "KB | r", gr(f"{W}/r/*") // 1024, "KB | z", gr(f"{W}/z/*") // 1024,
      "KB | 3d", gr(f"{W}/3d/*") // 1024, "KB")
