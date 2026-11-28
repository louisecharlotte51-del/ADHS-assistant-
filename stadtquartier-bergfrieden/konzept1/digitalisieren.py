"""Baufelder (beige) und Grünflächen (oliv) aus dem Team-Plan lesen -> felder.geojson (EPSG:25833).
Konvexe Hülle je Feld: überdeckende Beschriftungen und Zahlen schneiden sonst Kerben ins Feld."""
import json, sys
import numpy as np, cv2
from PIL import Image
from shapely.geometry import Polygon, mapping, Point
from gr import px2welt

im = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(int)
r, g, b = im[..., 0], im[..., 1], im[..., 2]
beige = (r > 232) & (g > 218) & (g < 244) & (b > 190) & (b < 228) & (r - b > 14)
oliv = (g > 140) & (g < 200) & (r > 120) & (r < 185) & (b < 130) & (g - b > 35)
U0, V0, U1, V1 = 960, 230, 1320, 810                    # Gebiet inkl. Station und Kanal
feats = []
for art, maske, min_px in (("baufeld", beige, 120), ("gruen", oliv, 25)):
    m = np.zeros_like(maske, np.uint8)
    m[V0:V1, U0:U1] = maske[V0:V1, U0:U1]
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] < min_px:
            continue
        pts = np.column_stack(np.where(lab == i))[:, ::-1].astype(np.int32)
        hull = cv2.convexHull(pts) if art == "baufeld" else \
            max(cv2.findContours((lab == i).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0], key=cv2.contourArea)
        hull = cv2.approxPolyDP(hull, 1.5, True)[:, 0, :]
        if len(hull) < 3:
            continue
        p = Polygon([px2welt(u + 0.5, v + 0.5) for u, v in hull]).buffer(0)
        feats.append(dict(type="Feature", geometry=mapping(p), properties=dict(art=art, flaeche=round(p.area))))
json.dump(dict(type="FeatureCollection", features=feats), open("felder_roh.geojson", "w"))
from collections import Counter
print(Counter(f["properties"]["art"] for f in feats), sorted(f["properties"]["flaeche"] for f in feats if f["properties"]["art"] == "baufeld"))
