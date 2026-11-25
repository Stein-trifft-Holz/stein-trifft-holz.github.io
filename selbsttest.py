#!/usr/bin/env python3
"""Selbsttest für bauen.py – läuft mit Testdaten in einem Wegwerf-Ordner.

Prüft K8 (Pausen nach Datum), K9 (vergangene Termine weg), K2 (Bilder verkleinert,
ohne Metadaten) und K5 (keine fremden Server eingebunden).
Aufruf: python3 selbsttest.py [--behalten ORDNER]   (ORDNER = gebaute Testseite zum Ansehen)
"""
import argparse
import datetime as dt
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bauen  # noqa: E402

HEUTE = dt.date(2027, 4, 10)
T = lambda tage: (HEUTE + dt.timedelta(days=tage)).isoformat()


def testdaten(ordner):
    inhalt, bilder = ordner / "inhalt", ordner / "bilder"
    inhalt.mkdir()
    bilder.mkdir()
    farben = [(120, 110, 100), (150, 100, 60), (90, 90, 95), (170, 140, 100), (110, 80, 50), (130, 125, 118)]
    for i, f in enumerate(farben):
        b = Image.new("RGB", (4000, 3000) if i % 2 else (3000, 4000), f)
        exif = Image.Exif()
        exif[0x010F] = "Testkamera"  # Hersteller – muss nach dem Bauen weg sein
        b.save(bilder / f"foto-{i}.jpg", quality=90, exif=exif)
    (inhalt / "texte.json").write_text(json.dumps({
        "titelbild": "/bilder/foto-1.jpg",
        "begruessung": "[Testtext] Begrüßung.",
        "ueber": "[Testtext] Erster Absatz.\n\nZweiter Absatz.",
        "ueber_bild": "/bilder/foto-2.jpg",
        "telefon": "02750 222580", "mail": "stein-trifft-holz@t-online.de",
        "strasse": "An der Hude 10", "ort": "57319 Bad Berleburg-Wunderthausen",
        "besuch": "Besuche und Aufträge nach telefonischer Absprache.",
    }), encoding="utf-8")
    (inhalt / "galerie.json").write_text(json.dumps(
        [{"bild": f"/bilder/foto-{i}.jpg", "titel": f"[Test] Stück {i}"} for i in range(6)]), encoding="utf-8")
    (inhalt / "termine.json").write_text(json.dumps([
        {"titel": "TEST-VERGANGEN", "von": T(-3), "ort": "Hesborn"},
        {"titel": "TEST-MEHRTAEGIG-ENDET-HEUTE", "von": T(-1), "bis": T(0), "ort": "Bad Berleburg", "partner": "Wiebelhaus"},
        {"titel": "TEST-KOMMEND", "von": T(20), "ort": "Köln", "partner": "Wiebelhaus", "link": "https://example.org"},
    ]), encoding="utf-8")
    (inhalt / "pausen.json").write_text(json.dumps([
        {"von": T(-40), "bis": T(-1), "text": "TEST-PAUSE-VORBEI"},
        {"von": T(10), "bis": T(60), "text": "TEST-PAUSE-BALD"},
        {"von": T(45), "bis": T(90), "text": "TEST-PAUSE-ZU-FRUEH"},
    ]), encoding="utf-8")
    return inhalt, bilder


def pruefen(ziel):
    seite = (ziel / "index.html").read_text(encoding="utf-8")
    fehler = []
    erwartet = {
        "vergangener Termin fehlt": "TEST-VERGANGEN" not in seite,
        "Termin, der heute endet, steht da": "TEST-MEHRTAEGIG-ENDET-HEUTE" in seite,
        "kommender Termin steht da": "TEST-KOMMEND" in seite,
        "Partner wird genannt": "mit Wiebelhaus" in seite,
        "Pause in 10 Tagen sichtbar": re.search(r'<p class="pause"[^>]*>TEST-PAUSE-BALD', seite) is not None,
        "Pause in 45 Tagen verborgen": re.search(r'<p class="pause"[^>]*hidden>TEST-PAUSE-ZU-FRUEH', seite) is not None,
        "vergangene Pause verborgen": re.search(r'<p class="pause"[^>]*hidden>TEST-PAUSE-VORBEI', seite) is not None,
        "keine Platzhalter übrig": "{{" not in seite,
        "keine fremden Skripte/Schriften/Stile": not re.search(r'<(script|link)[^>]+(src|href)="https?://', seite)
        and "googleapis" not in seite and "gstatic" not in seite,
        "Galerie mit 6 Bildern": seite.count("<figure>") == 6,
    }
    for name, ok in erwartet.items():
        (print if ok else fehler.append)(f"  ok  {name}" if ok else name)
    for webp in sorted((ziel / "bilder").glob("*.webp")):
        with Image.open(webp) as b:
            if max(b.size) > 3200 or b.width > 1600:
                fehler.append(f"{webp.name} zu groß: {b.size}")
            if b.getexif():
                fehler.append(f"{webp.name} hat noch Metadaten")
        if webp.stat().st_size > 300_000:
            fehler.append(f"{webp.name} über 300 KB")
    print("  ok  Bilder klein und ohne Metadaten" if not any("webp" in f for f in fehler) else "")
    for name in ("impressum.html", "datenschutz.html"):
        if "{{" in (ziel / name).read_text(encoding="utf-8"):
            fehler.append(f"Platzhalter in {name}")
    return fehler


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--behalten", type=Path)
    o = a.parse_args()
    tmp = Path(tempfile.mkdtemp())
    try:
        inhalt, bilder = testdaten(tmp)
        ziel = o.behalten or tmp / "_site"
        bauen.bauen(inhalt, bilder, ziel, HEUTE)
        fehler = pruefen(ziel)
    finally:
        shutil.rmtree(tmp)
    if fehler:
        print("FEHLER:\n- " + "\n- ".join(fehler))
        sys.exit(1)
    print("Selbsttest bestanden.")
