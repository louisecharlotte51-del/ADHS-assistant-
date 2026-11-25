"""
Nachbearbeitung der Situationen (Blender-Ausgabe 3d/sit_<name>_bild.png + sit_<name>_linien_0001.png):
  3d/skizze_<name>.png    Skizze: Papier, aquarellartige Farbe, Freestyle-Linien, auslaufende Ränder
  3d/rendering_<name>.png Rendering: Himmel, entrauscht, ohne Linien
Aufruf: python3 skizzen_nachbearbeitung.py
"""
import glob, os
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageChops

OUT = "3d"
rng = np.random.default_rng(3)
PAPIER = np.array([248, 245, 237], float)


def rauschen(w, h, skala, staerke):
    klein = rng.normal(0, 1, (max(2, h // skala), max(2, w // skala)))
    img = Image.fromarray(((klein - klein.min()) / (np.ptp(klein) + 1e-9) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return (np.asarray(img, float) / 255 - 0.5) * 2 * staerke


def papier(w, h):
    p = np.ones((h, w, 3)) * PAPIER
    p += (rauschen(w, h, 2, 5) + rauschen(w, h, 40, 6))[..., None]
    return p


def randmaske(w, h):
    """Weicher, unregelmäßiger Rand: die Zeichnung läuft zum Papier hin aus."""
    yy, xx = np.mgrid[0:h, 0:w]
    dx = np.minimum(xx, w - 1 - xx) / (w * 0.07)
    dy = np.minimum(yy, h - 1 - yy) / (h * 0.09)
    m = np.clip(np.minimum(dx, dy) + rauschen(w, h, 60, 0.35), 0, 1)
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), float) / 255


def himmel(w, h):
    t = np.linspace(0, 1, h)[:, None, None]
    oben, unten = np.array([168, 199, 228], float), np.array([236, 241, 245], float)
    return np.ones((h, w, 3)) * (oben * (1 - t ** 0.7) + unten * t ** 0.7)


for bild in sorted(glob.glob(f"{OUT}/sit_*_bild.png")):
    name = os.path.basename(bild)[4:-9]
    linien = glob.glob(f"{OUT}/sit_{name}_linien_*.png")
    b = Image.open(bild).convert("RGBA")
    w, h = b.size
    rgb = b.convert("RGB").filter(ImageFilter.MedianFilter(3))
    alpha = np.asarray(b.split()[3], float) / 255

    # ---------- Rendering ----------
    r = np.asarray(rgb.filter(ImageFilter.GaussianBlur(0.5)), float)
    r = r * alpha[..., None] + himmel(w, h) * (1 - alpha[..., None])
    Image.fromarray(np.clip(r, 0, 255).astype(np.uint8)).save(f"{OUT}/rendering_{name}.png")

    # ---------- Skizze ----------
    farbe = rgb.filter(ImageFilter.MedianFilter(5))
    weich = farbe.filter(ImageFilter.GaussianBlur(2.2))
    farbe = Image.blend(farbe, weich, 0.5)                         # Farbe verläuft leicht
    farbe = ImageEnhance.Color(farbe).enhance(1.12)
    f = np.asarray(farbe, float)
    f = f * 0.80 + 255 * 0.20                                      # lasierend, heller
    f += rauschen(w, h, 18, 10)[..., None]                         # Pigment ungleichmäßig
    pap = papier(w, h)
    m = randmaske(w, h) * alpha
    # Himmel: lockere Aquarell-Lasur im oberen Bilddrittel
    lasur = np.clip(1 - np.linspace(0, 1, h)[:, None] * 2.4, 0, 1) * np.clip(0.55 + rauschen(w, h, 90, 0.5), 0, 1)
    lasur = lasur * (1 - alpha) * randmaske(w, h)
    blau = np.array([186, 210, 232], float)
    s = pap * (1 - lasur[..., None] * 0.6) + blau * lasur[..., None] * 0.6
    s = s * (1 - m[..., None]) + (f * pap / 255) * m[..., None]   # Farbe multipliziert mit Papier
    s = Image.fromarray(np.clip(s, 0, 255).astype(np.uint8)).convert("RGBA")
    if linien:
        l = Image.open(linien[0]).convert("RGBA")
        la = np.asarray(l, float)
        la[..., 3] *= np.clip(randmaske(w, h) * 1.3, 0, 1) * 0.92
        s.alpha_composite(Image.fromarray(la.astype(np.uint8)))
    s.convert("RGB").save(f"{OUT}/skizze_{name}.png")
    print("Skizze + Rendering:", name)
