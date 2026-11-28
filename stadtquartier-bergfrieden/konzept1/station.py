"""
S-Bahn-Station Komturstraße + Brücken + Plätze (Konzept I, angenommene Maße).
Lokales System: u entlang der Gleise (Richtung OSO, -26°), v quer (Richtung Tempelhofer Feld). Ursprung = Stationsmitte.
Befund (ALKIS/FNP): Ringbahn v -24..+24, A100 im Trog v -70..-38, Baufeld A.1 ab v -97.
Idee: A100-Deckel trägt den Bahnhofsplatz -> Brücken spannen nur über den Ring (ca. 48 m, nicht zu lang).
  Stationsbrücke     32 x 76 m, Halle unter Holz-Diagrid-Dach 52 x 86 m, First 18 m: Landmarke, Laterne bei Nacht
  Bahnsteig          Mittelbahnsteig 152 x 10 m (S-Bahn-Vollzug), Treppen, Rolltreppen, 2 Aufzüge
  Landschaftsbrücke  West 32 m breit (Grünachse -> Feld), Ost 26 m (Rad/Fuß -> Feld); Kioske nur an den Brückenköpfen
  Feldbalkon         Terrasse 14 m tief entlang der Feldkante, Blick über die Gleise
  Regendach          Dachwasser fällt als Kaskade auf den Bahnhofsplatz: Quelle der Wasserkette zum Kanal
  Radstation         1.200 Plätze im Hang zwischen Deckel und Ring, Eingang vom Bahnhofsplatz
"""
import math, os, sys
_GQ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../gartenquartier")
if _GQ not in sys.path:
    sys.path.insert(0, _GQ)
if not os.path.exists("daten"):
    os.chdir(_GQ)
import entwurf as E
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from shapely import affinity

C = (391345.0, 5814061.0)
T = math.radians(-26)
U = (math.cos(T), math.sin(T))
V = (-math.sin(T), math.cos(T))


def w(u, v):
    return (C[0] + U[0] * u + V[0] * v, C[1] + U[1] * u + V[1] * v)


def loc(x, y):
    dx, dy = x - C[0], y - C[1]
    return dx * U[0] + dy * U[1], dx * V[0] + dy * V[1]


def R(u0, v0, u1, v1):
    return Polygon([w(u0, v0), w(u1, v0), w(u1, v1), w(u0, v1)])


EINSCHNITT = R(-420, -24, 420, 24)
A100_TROG = R(-420, -70, 420, -38)
DECKEL = R(-125, -72, 65, -36)                          # A100-Deckel = Bahnhofsplatz (190 x 36 m)
HANG = R(-125, -36, 65, -24)
BAHNSTEIG = R(-76, -5, 76, 5)
GLEISE = [LineString([w(-420, v), w(420, v)]) for v in (-15, -9, 9, 15)]
HALLE = R(-16, -40, 16, 36)                             # Stationsbrücke
DACH = affinity.scale(Point(C).buffer(1, 64), 26, 43, origin=C)
DACH = affinity.rotate(DACH, math.degrees(T), origin=C)
DACH = affinity.translate(DACH, *(V[0] * -2, V[1] * -2))
BRUECKE_W = R(-122, -36, -90, 30)
BRUECKE_O = R(58, -36, 84, 30)
FELDBALKON = R(-150, 24, 110, 38)
RADSTATION = R(-60, -36, -22, -26)
KIOSKE = [R(u, v, u + 9, v + 6) for u, v in [(-121, -46), (-104, -46), (59, -46), (74, -46), (-115, 31), (66, 31)]]
KASKADE = LineString([w(-6, -44), w(-10, -60), w(-22, -84), w(-40, -104)])
SEITE_WEST = LineString([(391086, 5813881), (391079, 5813466)])
NAMEN = {}


def zeichne(bl):
    a = bl.path
    a(A100_TROG, fill="#d9d5cc")
    for l in GLEISE:
        a(l, fill="none", stroke="#8d897f", stroke_width=".9")
    a(BAHNSTEIG, fill="#e9e5dc", stroke="#6e6a62", stroke_width=".5", stroke_dasharray="3 2")
    a(DECKEL, fill="#f1ede4", stroke="#b8b2a5", stroke_width=".5")
    a(HANG, fill="#dfe8cd")
    a(RADSTATION, fill="#ffffff", stroke="#1d1d1b", stroke_width=".6")
    a(FELDBALKON, fill="#efe9dc", stroke="#b8b2a5", stroke_width=".5")
    for b in (BRUECKE_W, BRUECKE_O):
        a(b, fill="#d6e3bf", stroke="#6f7f5a", stroke_width=".8")
        a(b.buffer(-4, join_style=2), fill="none", stroke="#9cb07c", stroke_width=".5", stroke_dasharray="2 2")
    a(HALLE, fill="#ffffff", stroke="#1d1d1b", stroke_width=".9")
    for k in KIOSKE:
        a(k, fill="#ffffff", stroke="#1d1d1b", stroke_width=".6")
    a(KASKADE.buffer(1.4), fill="#c7dde7", stroke="#8fb5c8", stroke_width=".4")


def zeichne_daecher(bl):
    a = bl.path
    a(DACH, fill="#000", fill_opacity=".12")
    a(DACH, fill="none", stroke="#1d1d1b", stroke_width="1.1")
    # Diagrid des Holzdachs
    linien = []
    for s in range(-120, 121, 12):
        linien += [LineString([w(s - 60, -60), w(s + 60, 60)]), LineString([w(s + 60, -60), w(s - 60, 60)])]
    a(unary_union(linien).intersection(DACH), fill="none", stroke="#1d1d1b", stroke_width=".35")
    t = bl.text
    p = w(0, 50)
    t(*p, "S Komturstraße", 9, "#1d1d1b", weight=800)
    for s, (u, v), r in [("Landschaftsbrücke West", (-106, 0), -26 + 90), ("Landschaftsbrücke Ost", (71, 0), 64),
                         ("Bahnhofsplatz auf dem A100-Deckel", (-60, -55), -26), ("Feldbalkon", (-40, 31), -26),
                         ("Radstation 1.200", (-41, -31), -26), ("Ringbahn", (200, 0), -26), ("A100 im Trog", (200, -54), -26)]:
        bl.text(*w(u, v), s, 6.5, "#4a4740", rot=-r if r != -26 else 26, italic=True)


if __name__ == "__main__":
    print("Spannweite Ring", 48, "m · Deckel", round(DECKEL.area), "m² · Dach", round(DACH.area), "m²")
