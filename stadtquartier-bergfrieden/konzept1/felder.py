"""Rohfelder (digitalisieren.py) -> felder.geojson mit Quartier, Art und Fläche. Nummern wie im Kontrollbild."""
import json
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

roh = [shape(f["geometry"]) for f in json.load(open("felder_roh.geojson"))["features"]]
Q = {"A": [1, 2], "1": [3, 4, 5, 6, 7], "2": [10, 11, 13, 14], "3": [(15, 18), 16], "4": [8, 9, 12], "5": [17, 20]}
GRUEN = {"A": [22], "1": [25, 23, 24], "2": [28, 26], "3": [30, 31], "4": [27], "5": [32, 33]}
out = []
def add(geo, **p):
    out.append(dict(type="Feature", geometry=mapping(geo), properties=dict(p, flaeche=round(geo.area))))
add(roh[0], art="station", quartier="A", name="S-Bahn-Station")
for q, ids in Q.items():
    for k, i in enumerate(ids):
        g = unary_union([roh[j] for j in i]).convex_hull if isinstance(i, tuple) else roh[i]
        add(g, art="baufeld", quartier=q, name=f"{q}.{k + 1}")
for q, ids in GRUEN.items():
    for i in ids:
        add(roh[i], art="gruen", quartier=q, name=f"Grün {q}")
add(roh[29], art="achse", quartier="-", name="Erholungsachse")
add(unary_union([roh[19], roh[21]]).convex_hull, art="stadtwald", quartier="3", name="Stadtwald")
json.dump(dict(type="FeatureCollection", features=out), open("felder.geojson", "w"))
bf = [f for f in out if f["properties"]["art"] == "baufeld"]
print(len(bf), "Baufelder,", round(sum(f["properties"]["flaeche"] for f in bf) / 1e4, 2), "ha")
for q in Q:
    print(q, [(f["properties"]["name"], f["properties"]["flaeche"]) for f in bf if f["properties"]["quartier"] == q])
