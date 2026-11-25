#!/usr/bin/env python3
"""Baut die Website „Stein trifft Holz“ aus inhalt/*.json und bilder/ nach _site/.

Aufruf:  python3 bauen.py [--inhalt DIR] [--bilder DIR] [--ziel DIR] [--heute JJJJ-MM-TT]

- Termine, deren letzter Tag vorbei ist, fliegen raus.
- Eine Pause wird ab 30 Tage vor Beginn bis zum letzten Tag angezeigt.
- Fotos werden verkleinert (WebP, 1600 und 800 px), Metadaten (z. B. GPS) entfallen.
Die Seite wird zusätzlich täglich neu gebaut; ein kleines Skript im Browser prüft die
Daten noch einmal, damit nie etwas Veraltetes stehen bleibt.
"""
import argparse
import datetime as dt
import html
import json
import shutil
from pathlib import Path

from PIL import Image, ImageOps

HIER = Path(__file__).resolve().parent
VORLAUF_PAUSE = 30  # Tage
BREITEN = (1600, 800)
WOCHENTAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def esc(t):
    return html.escape(str(t or ""), quote=True)


def datum(s):
    return dt.date.fromisoformat(str(s)[:10]) if s else None


def tag(d):
    return f"{d.day:02d}.{d.month:02d}.{d.year}"


def zeitraum(von, bis):
    if not bis or bis == von:
        return f"{WOCHENTAGE[von.weekday()]}, {tag(von)}"
    if von.year == bis.year and von.month == bis.month:
        return f"{von.day:02d}.–{tag(bis)}"
    return f"{tag(von)} – {tag(bis)}"


class Bilder:
    def __init__(self, quelle, ziel):
        self.quelle, self.ziel, self.fertig = quelle, ziel / "bilder", {}
        self.ziel.mkdir(parents=True, exist_ok=True)

    def __call__(self, pfad):
        """Gibt {'src','srcset','w','h'} zurück oder None, wenn das Bild fehlt."""
        if not pfad:
            return None
        if pfad in self.fertig:
            return self.fertig[pfad]
        datei = self.quelle / Path(str(pfad)).name
        if not datei.is_file():
            print(f"WARNUNG: Bild fehlt: {pfad}")
            return None
        with Image.open(datei) as roh:
            bild = ImageOps.exif_transpose(roh).convert("RGB")
        teile = []
        for b in BREITEN:
            kopie = bild.copy()
            kopie.thumbnail((b, b * 2))
            name = f"{datei.stem}-{b}.webp"
            kopie.save(self.ziel / name, "WEBP", quality=80, method=6)
            teile.append((name, kopie.width))
        klein = bild.copy()
        klein.thumbnail((BREITEN[0], BREITEN[0] * 2))
        info = {
            "src": f"bilder/{teile[0][0]}",
            "srcset": ", ".join(f"bilder/{n} {w}w" for n, w in teile),
            "w": klein.width,
            "h": klein.height,
        }
        self.fertig[pfad] = info
        return info


def img(info, alt, sizes, klasse="", laden="lazy"):
    if not info:
        return ""
    k = f' class="{klasse}"' if klasse else ""
    return (f'<img{k} src="{info["src"]}" srcset="{info["srcset"]}" sizes="{sizes}" '
            f'width="{info["w"]}" height="{info["h"]}" alt="{esc(alt)}" loading="{laden}" decoding="async">')


def pausen_html(pausen, heute):
    teile = []
    for p in sorted(pausen, key=lambda p: str(p.get("von"))):
        von, bis = datum(p.get("von")), datum(p.get("bis"))
        if not von or not bis:
            continue
        ab = von - dt.timedelta(days=VORLAUF_PAUSE)
        sichtbar = ab <= heute <= bis
        text = (p.get("text") or "").strip() or (
            f"Werkstattpause vom {tag(von)} bis {tag(bis)} – in dieser Zeit nimmt die Werkstatt keine Aufträge an.")
        teile.append(
            f'<p class="pause" data-ab="{ab.isoformat()}" data-bis="{bis.isoformat()}"'
            f'{"" if sichtbar else " hidden"}>{esc(text)}</p>')
    return "\n".join(teile)


def termine_html(termine, heute):
    zeilen = []
    for t in sorted(termine, key=lambda t: str(t.get("von"))):
        von, bis = datum(t.get("von")), datum(t.get("bis"))
        if not von:
            continue
        ende = bis or von
        if ende < heute:
            continue
        titel = esc(t.get("titel"))
        if t.get("link"):
            titel = f'<a href="{esc(t["link"])}" rel="noopener">{titel}</a>'
        partner = f' · mit {esc(t["partner"])}' if t.get("partner") else ""
        text = f'<p>{esc(t["text"])}</p>' if t.get("text") else ""
        zeilen.append(
            f'<li class="termin" data-bis="{ende.isoformat()}">'
            f'<time datetime="{von.isoformat()}">{zeitraum(von, bis)}</time>'
            f'<h3>{titel}</h3><p class="ort">{esc(t.get("ort"))}{partner}</p>{text}</li>')
    leer = '<p class="leer"{}>Gerade stehen keine Termine an – fragen Sie gern telefonisch nach.</p>'
    return (f'<ul class="termine">{"".join(zeilen)}</ul>' + leer.format(" hidden" if zeilen else ""))


def galerie_html(galerie, bilder):
    stuecke = []
    for g in galerie:
        info = bilder(g.get("bild"))
        if info:
            unter = f'<figcaption>{esc(g["titel"])}</figcaption>' if g.get("titel") else ""
            stuecke.append(f'<figure>{img(info, g.get("titel") or "Arbeit aus der Werkstatt", "(min-width: 700px) 33vw, 50vw")}{unter}</figure>')
    return "\n".join(stuecke)


def absatz(text):
    return "".join(f"<p>{esc(a.strip())}</p>" for a in str(text or "").split("\n\n") if a.strip())


def bauen(inhalt, bildquelle, ziel, heute):
    lade = lambda n: json.loads((inhalt / f"{n}.json").read_text(encoding="utf-8"))
    texte, galerie, termine, pausen = lade("texte"), lade("galerie"), lade("termine"), lade("pausen")
    if ziel.exists():
        shutil.rmtree(ziel)
    ziel.mkdir(parents=True)
    bilder = Bilder(bildquelle, ziel)

    titelbild = bilder(texte.get("titelbild"))
    ueber_bild = bilder(texte.get("ueber_bild"))
    gal = galerie_html(galerie, bilder)
    tel = texte.get("telefon", "")
    felder = {
        "PAUSEN": pausen_html(pausen, heute),
        "TITELBILD": img(titelbild, "Arbeit aus der Werkstatt Stein trifft Holz", "100vw", "titelbild", "eager"),
        "BEGRUESSUNG": absatz(texte.get("begruessung")),
        "GALERIE": gal,
        "GALERIE_HIDDEN": "" if gal else " hidden",
        "TERMINE": termine_html(termine, heute),
        "UEBER": absatz(texte.get("ueber")),
        "UEBER_BILD": img(ueber_bild, "Die Werkstatt", "(min-width: 700px) 40vw, 100vw"),
        "TELEFON": esc(tel),
        "TELEFON_LINK": "tel:+49" + "".join(c for c in tel if c.isdigit()).lstrip("0"),
        "MAIL": esc(texte.get("mail")),
        "STRASSE": esc(texte.get("strasse")),
        "ORT": esc(texte.get("ort")),
        "BESUCH": esc(texte.get("besuch")),
        "JAHR": str(heute.year),
        "STAND": heute.isoformat(),
    }
    for name in ("index.html", "impressum.html", "datenschutz.html"):
        seite = (HIER / "vorlage" / name).read_text(encoding="utf-8")
        for k, v in felder.items():
            seite = seite.replace("{{" + k + "}}", v)
        (ziel / name).write_text(seite, encoding="utf-8")
    for extra in (HIER / "vorlage").iterdir():
        if extra.suffix in (".css", ".js", ".woff2", ".svg", ".png", ".ico"):
            shutil.copy(extra, ziel / extra.name)
    (ziel / ".nojekyll").write_text("")
    print(f"Gebaut nach {ziel} (Stand {heute}): {len(galerie)} Fotos, "
          f"{felder['TERMINE'].count('<li')} kommende Termine.")


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--inhalt", type=Path, default=HIER / "inhalt")
    a.add_argument("--bilder", type=Path, default=HIER / "bilder")
    a.add_argument("--ziel", type=Path, default=HIER / "_site")
    a.add_argument("--heute", type=dt.date.fromisoformat, default=dt.date.today())
    o = a.parse_args()
    bauen(o.inhalt, o.bilder, o.ziel, o.heute)
