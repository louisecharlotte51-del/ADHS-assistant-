"""
Ufer am Teltowkanal (Q5): Lückenschluss Teltowkanalweg, Badebucht, Steg, Kanalhof.
Befund (WSA/Wikipedia, siehe Seite): Klasse IV, Wasserspiegel ≥ 37 m frei halten, Spundwandufer, Baden im Kanal
verboten -> Badeschiff mit eigenem Wasser (Spree-Badeschiff 32,5 × 8,2 m) in einer Bucht HINTER der Uferlinie.
  UFERWEG   5 m Promenade auf der Spundwandkante, Sitzstufen landseitig (Teltowkanalweg heute umgeleitet)
  BUCHT     70 × 16 m, ausgehoben südlich von 5.2; Fahrrinne unberührt
  BADESCHIFF 32,5 × 8,2 m, geschlossener Wasserkreislauf, Holzdecks rundum (Prinzip Islands Brygge)
  STEG      4 m Holzsteg über die Buchtmündung, Uferweg läuft durch
  INSELN    schwimmende Pflanzeninseln in der Bucht (Rotterdam Floating Park)
  KRAN      Portalkran als Landmarke im Kanalhof (Bühne darunter)
"""
import math
import numpy as np
from shapely.geometry import LineString, Polygon, Point, box
from shapely.ops import unary_union
import plaene as PL
from bebauung import FELDER

_W = PL.WASSER.intersection(box(391150, 5813050, 391700, 5813300))


def _nordufer(x0=391290, x1=391640, n=36):
    pts = []
    for x in np.linspace(x0, x1, n):
        q = LineString([(x, 5813050), (x, 5813300)]).intersection(_W)
        if not q.is_empty:
            pts.append((x, q.bounds[3]))
    return LineString(pts)


UFER = _nordufer()
_n = lambda d: UFER.parallel_offset(d, "left", join_style=2)          # landseitig (links bei West->Ost)
UFERWEG = Polygon(list(UFER.coords) + list(_n(5).coords)[::-1]) if _n(5).geom_type == "LineString" else UFER.buffer(5)
STUFEN = unary_union([LineString(_n(5 + k * 0.9).coords).buffer(0.08) for k in range(1, 5)]).intersection(box(391480, 5813100, 391620, 5813300))
_a, _b = UFER.interpolate(UFER.project(Point(391395, 5813200))), UFER.interpolate(UFER.project(Point(391465, 5813215)))
_t = ((_b.x - _a.x) / _a.distance(_b), (_b.y - _a.y) / _a.distance(_b))
_nn = (-_t[1], _t[0])
BUCHT = Polygon([(_a.x, _a.y), (_b.x, _b.y), (_b.x + _nn[0] * 20, _b.y + _nn[1] * 20), (_a.x + _nn[0] * 20, _a.y + _nn[1] * 20)])
_m = Point((_a.x + _b.x) / 2 + _nn[0] * 10.5, (_a.y + _b.y) / 2 + _nn[1] * 10.5)
_ang = math.degrees(math.atan2(_t[1], _t[0]))
from shapely import affinity
BADESCHIFF = affinity.rotate(box(_m.x - 16.25, _m.y - 4.1, _m.x + 16.25, _m.y + 4.1), _ang, origin=_m)
DECKS = BUCHT.buffer(-0.5).difference(BUCHT.buffer(-3.5)).union(BADESCHIFF.buffer(2.5).difference(BADESCHIFF))
STEG = LineString([(_a.x, _a.y), (_b.x, _b.y)]).buffer(2, cap_style=2)
INSELN = [Point(_a.x + _t[0] * 8 + _nn[0] * 6, _a.y + _t[1] * 8 + _nn[1] * 6).buffer(3, 6),
          Point(_b.x - _t[0] * 9 + _nn[0] * 7, _b.y - _t[1] * 9 + _nn[1] * 7).buffer(3.5, 6)]
_P52 = [p for n, q, p in FELDER if n == "5.2"][0]
KRAN = affinity.rotate(box(_m.x - 10, _m.y + 13, _m.x + 10, _m.y + 21), _ang, origin=_m)    # Portalkran über dem Kanalhof
KANALHOF = Point(_m.x + _nn[0] * 18, _m.y + _nn[1] * 18).buffer(12)

if __name__ == "__main__":
    print("Ufer m", round(UFER.length), "Bucht m²", round(BUCHT.area), "Badeschiff", round(BADESCHIFF.area), "m²",
          "Abstand Bucht–5.2", round(BUCHT.distance(_P52), 1))
