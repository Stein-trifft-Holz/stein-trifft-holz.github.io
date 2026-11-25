#!/usr/bin/env python3
"""Setzt den Kartenausschnitt für „Anfahrt“ aus OpenStreetMap-Kacheln zusammen.

Einmalig: Kacheln (Zoom 16) liegen in karte/kacheln/16-<x>-<y>.png. Ergebnis: vorlage/karte.webp
mit goldener Markierung an der Werkstatt und Quellenangabe (Pflicht laut OSM-Lizenz).
Kein Kartendienst wird beim Besuch der Seite geladen – das Bild liegt auf der eigenen Seite.
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HIER = Path(__file__).resolve().parent
LAT, LON, Z = 51.0964918, 8.5127523, 16   # An der Hude 10, laut Nominatim (2026-11-25)
XS, YS = range(34315, 34320), range(21910, 21914)
BREITE, HOEHE = 1000, 620
GOLD, SCHIEFER = (201, 165, 78), (31, 34, 38)


def main():
    n = 2 ** Z
    px = ((LON + 180) / 360 * n - XS[0]) * 256
    lat = math.radians(LAT)
    py = ((1 - math.log(math.tan(lat) + 1 / math.cos(lat)) / math.pi) / 2 * n - YS[0]) * 256
    ganz = Image.new("RGB", (256 * len(XS), 256 * len(YS)))
    for i, x in enumerate(XS):
        for j, y in enumerate(YS):
            ganz.paste(Image.open(HIER / "karte" / "kacheln" / f"{Z}-{x}-{y}.png").convert("RGB"), (i * 256, j * 256))
    links, oben = round(px - BREITE / 2), round(py - HOEHE / 2)
    bild = ganz.crop((links, oben, links + BREITE, oben + HOEHE))
    d = ImageDraw.Draw(bild)
    cx, cy = px - links, py - oben
    # Stecknadel: Kreis mit Spitze, Gold auf Schiefer-Rand
    d.polygon([(cx - 14, cy - 30), (cx + 14, cy - 30), (cx, cy)], fill=SCHIEFER)
    d.ellipse((cx - 20, cy - 58, cx + 20, cy - 18), fill=SCHIEFER)
    d.ellipse((cx - 15, cy - 53, cx + 15, cy - 23), fill=GOLD)
    d.polygon([(cx - 10, cy - 30), (cx + 10, cy - 30), (cx, cy - 6)], fill=GOLD)
    try:
        schrift = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    except OSError:
        schrift = ImageFont.load_default()
    text = "© OpenStreetMap-Mitwirkende"
    b = d.textbbox((0, 0), text, font=schrift)
    d.rectangle((BREITE - b[2] - 16, HOEHE - b[3] - 12, BREITE, HOEHE), fill=(255, 255, 255))
    d.text((BREITE - b[2] - 8, HOEHE - b[3] - 7), text, fill=(40, 40, 40), font=schrift)
    ziel = HIER / "vorlage" / "karte.webp"
    bild.save(ziel, "WEBP", quality=82, method=6)
    print(f"{ziel} ({ziel.stat().st_size // 1024} KB, {BREITE}×{HOEHE})")


if __name__ == "__main__":
    main()
