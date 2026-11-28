"""Umrechnung Plan-Pixel <-> EPSG:25833 aus georef.json."""
import json, os
import numpy as np
G = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "georef.json")))
_c, _s = np.cos(np.radians(G["rot"])), np.sin(np.radians(G["rot"]))


def px2welt(u, v):
    x, y = G["X0"] + u * G["s"] - G["cx"], G["Y0"] - v * G["s"] - G["cy"]
    return (x * _c + y * _s + G["cx"], -x * _s + y * _c + G["cy"])     # Drehung des Katasters zurück


def welt2px(x, y):
    x, y = x - G["cx"], y - G["cy"]
    xr, yr = x * _c - y * _s + G["cx"], x * _s + y * _c + G["cy"]
    return ((xr - G["X0"]) / G["s"], (G["Y0"] - yr) / G["s"])


assert all(abs(a - b) < 1e-6 for a, b in zip(welt2px(*px2welt(100, 200)), (100, 200)))
