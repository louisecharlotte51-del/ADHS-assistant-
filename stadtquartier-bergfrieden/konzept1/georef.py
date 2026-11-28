"""Plan-Bild (Team-Plan, PNG/JPG) auf ALKIS-Gebäude georeferenzieren: Maßstab + Verschiebung per Template-Matching.
Ergebnis: georef.json mit Pixel -> EPSG:25833 (x = X0 + u*s, y = Y0 - v*s)."""
import json, sys, os
import numpy as np, cv2
HIER = os.path.dirname(os.path.abspath(__file__))
BILD = os.path.abspath(sys.argv[1])
os.chdir(os.path.join(HIER, "../gartenquartier"))          # entwurf.py liest daten/ relativ
from PIL import Image
from shapely.geometry import shape
sys.path.insert(0, ".")
import entwurf as E

im = np.asarray(Image.open(BILD).convert("RGB")).astype(int)
r, g, b = im[..., 0], im[..., 1], im[..., 2]
grau = (np.abs(r - g) < 8) & (np.abs(g - b) < 8) & (r > 185) & (r < 236)
U0, V0, U1, V1 = 850, 200, 1450, 900                  # Ausschnitt um das Gebiet
tpl = grau[V0:V1, U0:U1].astype(np.float32)
geb = [shape(f["geometry"]) for f in json.load(open("daten/geb.json"))["features"]]
bx0, by0, bx1, by1 = 390166, 5812548, 392491, 5814847
def raster(s, rot):
    W, H = int((bx1 - bx0) / s), int((by1 - by0) / s)
    ras = np.zeros((H, W), np.uint8)
    cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    c, si = np.cos(np.radians(rot)), np.sin(np.radians(rot))
    for p in geb:
        for q in getattr(p, "geoms", [p]):
            xy = np.array(q.exterior.coords) - (cx, cy)
            xy = xy @ np.array([[c, si], [-si, c]]) + (cx, cy)          # Kataster um rot drehen
            pts = np.stack([(xy[:, 0] - bx0) / s, (by1 - xy[:, 1]) / s], 1).astype(np.int32)
            cv2.fillPoly(ras, [pts], 1)
    return ras
best = None
for s in np.arange(1.66, 1.82, 0.005):                 # Meter je Pixel, fein
    for rot in (-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5):
        ras = raster(s, rot)
        res = cv2.matchTemplate(ras.astype(np.float32), tpl, cv2.TM_CCOEFF_NORMED)
        _, mx, _, loc = cv2.minMaxLoc(res)
        if best is None or mx > best[0]:
            best = (mx, s, loc, rot)
mx, s, (lx, ly), rot = best
assert rot == 0.0 or abs(rot) <= 1.5
# Pixel (U0,V0) des Bildes liegt bei Raster (lx,ly) -> Weltkoordinaten (Drehung: Kataster wurde um rot gedreht)
X0 = bx0 + (lx - U0) * s
Y0 = by1 - (ly - V0) * s
json.dump(dict(s=s, X0=X0, Y0=Y0, score=mx, rot=rot, cx=(bx0 + bx1) / 2, cy=(by0 + by1) / 2), open(os.path.join(HIER, "georef.json"), "w"))
print(f"Maßstab {s:.3f} m/px, Drehung {rot}°, Score {mx:.3f}, X0 {X0:.0f}, Y0 {Y0:.0f}")
# Kontrolle: Station und Kanal
st = E.STATION
print("Station im Bild:", round((st.x - X0) / s), round((Y0 - st.y) / s))
