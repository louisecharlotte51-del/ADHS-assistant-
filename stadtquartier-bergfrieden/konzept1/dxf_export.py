"""
DXF für Vectorworks (Konzept I): lokale Koordinaten wie das 3D-Modell, Nullpunkt = EPSG:25833 (391250 / 5813550), Meter.
Gebäude als geschlossene Polylinien mit Objekthöhe (thickness) -> in Vectorworks als 3D-Körper/Extrusion lesbar.
Aufruf: python3 dxf_export.py -> out/konzept1_lageplan.dxf
"""
import os
import ezdxf
from shapely.geometry import shape
from shapely.ops import unary_union
import plaene as PL
from plaene import B, G, FELDER, PARKS, GA, ST, retention, hoehe
from bebauung import PLATZ_VOR, PLATZ_EIN, TOR, ACHSE_EW, E

OX, OY = 391250.0, 5813550.0
LAYER = {"BAUFELD": (150, 120, 60), "GEB_A": (30, 30, 30), "GEB_B": (90, 90, 160), "BESTAND": (150, 150, 150),
         "PLATZ": (200, 170, 120), "PARK": (110, 160, 80), "RETENTION": (60, 140, 190), "GRUENACHSE": (60, 140, 190),
         "WEG_WOHNWEG": (120, 100, 80), "ACHSE_STRASSE": (190, 80, 70), "STATION": (40, 40, 40), "BRUECKE": (110, 160, 80),
         "PRIVAT_A": (230, 180, 120), "HALBOEFF_A": (245, 225, 195), "TEXT": (0, 0, 0)}


def pts(r):
    return [(round(x - OX, 3), round(y - OY, 3)) for x, y in r.coords]


def poly(msp, g, layer, dicke=0.0):
    for p in getattr(g, "geoms", [g]):
        if p.is_empty:
            continue
        if p.geom_type == "Polygon":
            for r in [p.exterior, *p.interiors]:
                e = msp.add_lwpolyline(pts(r), close=True, dxfattribs={"layer": layer})
                if dicke:
                    e.dxf.thickness = dicke
        elif p.geom_type == "LineString":
            msp.add_lwpolyline(pts(p), dxfattribs={"layer": layer})
        elif hasattr(p, "geoms"):
            poly(msp, p, layer, dicke)


def main():
    doc = ezdxf.new("R2013", setup=True)
    doc.units = ezdxf.units.M
    for n, c in LAYER.items():
        doc.layers.add(n, true_color=ezdxf.colors.rgb2int(c))
    msp = doc.modelspace()
    for name, q, P in FELDER:
        poly(msp, P, "BAUFELD")
        c = P.representative_point()
        msp.add_text(name, height=4, dxfattribs={"layer": "TEXT"}).set_placement((c.x - OX, c.y - OY))
    for var in "AB":
        for h in B[var]["haeuser"]:
            g = shape(h["geo"])
            poly(msp, g, f"GEB_{var}", hoehe(h["g"]))
            c = g.representative_point()
            msp.add_text(f'{h["g"]}G {h["typ"]}', height=1.6, dxfattribs={"layer": "TEXT"}).set_placement((c.x - OX, c.y - OY))
    for g, n in PL.KONTEXT:
        if g.intersects(PL.box(390900, 5813150, 391620, 5814260)):
            poly(msp, g, "BESTAND", hoehe(n))
    poly(msp, unary_union([PLATZ_VOR, PLATZ_EIN, TOR, ST.DECKEL]), "PLATZ")
    poly(msp, unary_union([g for n, g in PARKS] + [ACHSE_EW]), "PARK")
    poly(msp, unary_union([retention(g) for n, g in PARKS if n != "Stadtwald"]), "RETENTION")
    poly(msp, GA, "GRUENACHSE")
    poly(msp, GA.buffer(4, cap_style=2), "GRUENACHSE")
    for k, l, b in PL.WEGE:
        poly(msp, l, "WEG_WOHNWEG" if k == "wohnweg" else "ACHSE_STRASSE")
    poly(msp, ST.SEITE_WEST, "ACHSE_STRASSE")
    for g in (ST.HALLE, ST.DACH, ST.RADSTATION, ST.BAHNSTEIG, ST.DECKEL, ST.FELDBALKON, *ST.KIOSKE):
        poly(msp, g, "STATION")
    for g in (ST.BRUECKE_W, ST.BRUECKE_O):
        poly(msp, g, "BRUECKE")
    poly(msp, shape(G["A"]["privat"]), "PRIVAT_A")
    poly(msp, shape(G["A"]["halb"]), "HALBOEFF_A")
    p = os.path.join(PL.OUT, "konzept1_lageplan.dxf")
    doc.saveas(p)
    return p


if __name__ == "__main__":
    print(main())
