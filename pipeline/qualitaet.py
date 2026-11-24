"""Qualitätsprüfung für Pull Requests (SF-52).

Prüft Entwürfe (entwuerfe/) und Website-Quelltext (website/src/) auf die Leitplanken der Spieltagsformel.
Fehler lassen den Check scheitern, Hinweise erscheinen nur in der Zusammenfassung.

Aufruf:
    python -m pipeline.qualitaet DATEI ...        # bestimmte Dateien
    python -m pipeline.qualitaet --alle            # alles unter entwuerfe/ und website/src/
Die Regeln stehen in QUALITAETSPRUEFUNG.md.
"""
import glob
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass

ENDUNGEN = (".md", ".mdx", ".astro", ".js", ".ts", ".html")

# Buchmacher und Glücksspiel-Anbieter: dürfen nirgends genannt oder verlinkt werden.
BUCHMACHER = [
    "bet365", "tipico", "bwin", "betway", "interwetten", "bet-at-home", "betathome", "unibet",
    "william hill", "williamhill", "betano", "neobet", "neo.bet", "merkur bets", "merkurbets",
    "admiralbet", "winamax", "betfair", "1xbet", "oddset", "happybet", "mobilebet", "betsson",
    "zebet", "bet3000", "sportwetten.de", "novibet", "bildbet", "wetten.com", "pinnacle",
    "betvictor", "888sport", "pokerstars", "sunmaker", "lottoland",
]
_BUCHMACHER_RE = re.compile(r"(?<![a-z0-9])(" + "|".join(re.escape(b) for b in BUCHMACHER) + r")(?![a-z0-9])", re.I)

# Links auf Wett- oder Casino-Seiten (zusätzlich zu den Namen oben)
_LINK_RE = re.compile(r"https?://[^\s)\"'>\]]+", re.I)
_WETT_HOST_RE = re.compile(r"(wett|casino|sportsbook|bookmaker|buchmacher)", re.I)

# Reißerische Versprechen und Wett-Sprache. Steht im selben Satz eine Verneinung
# („keine Wett-Tipps“, „nicht sicher“), ist das in Ordnung.
VERSPRECHEN = [
    r"sichere[nrs]?\s+(tipps?|quoten?|sieg|wetten?|bank)",
    r"tipps?\s+des\s+tages",
    r"todsicher",
    r"gewinn\s+garantiert", r"garantierte[nrs]?\s+gewinn",
    r"risikolos",
    r"wett-?bonus", r"bonus-?code",
    r"jetzt\s+(wetten|tippen|einsetzen)",
    r"wett-?tipps?", r"quoten-?tipps?",
    r"value-?bets?",
    r"sichere\s+bank",
]
_VERSPRECHEN_RE = re.compile(r"(" + "|".join(VERSPRECHEN) + r")", re.I)
_VERNEINUNG_RE = re.compile(r"\b(kein\w*|nicht|ohne|nie|niemals|statt)\b", re.I)

_PLATZHALTER_RE = re.compile(r"\[(PRÜFEN|AUS DER REDAKTION)\b[^\]]*\]?")
_EXPERIMENT_RE = re.compile(r"(100[\s-]*(€|euro)[\s-]*experiment|kontostand)", re.I)
_PROZENT_RE = re.compile(r"(?<![\d,.])(\d{1,3}(?:,\d)?)\s?%")
_DEZIMAL_RE = re.compile(r"(?<![\d,.])(0,\d{2,3})(?![\d])")
_DATEI_RE = re.compile(r"(vorbericht|nachbericht)-(\d{4}-\d{2})-(\d{2})\.md$")


@dataclass
class Befund:
    datei: str
    zeile: int
    text: str
    fehler: bool = True


def _saetze(zeile):
    return re.split(r"(?<=[.!?])\s+", zeile)


def _zahlen_aus(obj, menge):
    """Sammelt alle Zahlen eines JSON-Objekts in den Schreibweisen, in denen sie im Text auftauchen."""
    if isinstance(obj, dict):
        for v in obj.values():
            _zahlen_aus(v, menge)
    elif isinstance(obj, list):
        for v in obj:
            _zahlen_aus(v, menge)
    elif isinstance(obj, bool) or obj is None:
        return
    elif isinstance(obj, (int, float)):
        x = float(obj)
        menge.add(f"{round(x)}")
        if 0 <= x <= 1:
            menge.add(f"{round(x * 100)}")
            menge.add(f"{x * 100:.1f}".replace(".", ","))
            for st in (2, 3):
                menge.add(f"{x:.{st}f}".replace(".", ","))
        if x <= 100:
            menge.add(f"{x:.1f}".replace(".", ","))


def _alle_staende(pfad, wurzel="."):
    """Aktueller Stand der Datei plus alle früheren Stände aus der Git-Historie.
    Grund: Die Marktwerte werden bis zum Anpfiff aufgefrischt; ein Vorbericht vom Donnerstag
    nennt zu Recht den Donnerstags-Stand."""
    staende = []
    if os.path.exists(pfad):
        with open(pfad, encoding="utf-8") as f:
            staende.append(json.load(f))
    rel = os.path.relpath(pfad, wurzel)
    try:
        hashes = subprocess.run(["git", "-C", wurzel, "log", "--format=%H", "--", rel],
                                capture_output=True, text=True, timeout=30).stdout.split()
        for h in hashes[:40]:
            r = subprocess.run(["git", "-C", wurzel, "show", f"{h}:{rel}"], capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                try:
                    staende.append(json.loads(r.stdout))
                except json.JSONDecodeError:
                    pass
    except (OSError, subprocess.SubprocessError):
        pass
    return staende


def erlaubte_zahlen(pfad, wurzel="."):
    """Zahlen, die ein Vor-/Nachbericht nennen darf: aus Datenpaket, Nachbericht-Daten und Roh-Entwurf.
    None, wenn die Datei kein Spieltagsbeitrag ist (dann keine Zahlenprüfung)."""
    m = _DATEI_RE.search(os.path.basename(pfad))
    if not m:
        return None
    _, saison, nr = m.groups()
    menge = set()
    quellen = [
        os.path.join(wurzel, "data", "spieltage", saison, f"{nr}.json"),
        os.path.join(wurzel, "data", "nachberichte", saison, f"{nr}.json"),
    ]
    gefunden = False
    for q in quellen:
        for stand in _alle_staende(q, wurzel):
            gefunden = True
            _zahlen_aus(stand, menge)
    # Roh-Entwürfe der Pipeline (aus denselben Daten gerechnet, z. B. Trefferquoten)
    for art in ("vorbericht", "nachbericht"):
        roh = os.path.join(wurzel, "entwuerfe", f"{art}-{saison}-{nr}.md")
        if os.path.exists(roh):
            gefunden = True
            with open(roh, encoding="utf-8") as f:
                inhalt = f.read()
            menge.update(_PROZENT_RE.findall(inhalt))
            menge.update(_DEZIMAL_RE.findall(inhalt))
    return menge if gefunden else None


def pruefe_datei(pfad, wurzel="."):
    befunde = []
    try:
        with open(os.path.join(wurzel, pfad), encoding="utf-8") as f:
            zeilen = f.read().splitlines()
    except (FileNotFoundError, UnicodeDecodeError):
        return befunde
    inhalt = "\n".join(zeilen)
    ist_website = pfad.replace("\\", "/").startswith("website/src/")
    ist_redaktion = "/redaktion/" in pfad.replace("\\", "/")
    ist_social = os.path.basename(pfad).startswith("social-")

    for i, z in enumerate(zeilen, 1):
        for m in _BUCHMACHER_RE.finditer(z):
            befunde.append(Befund(pfad, i, f"Buchmacher-/Glücksspielname „{m.group(1)}“ – nie nennen oder verlinken"))
        for url in _LINK_RE.findall(z):
            host = re.sub(r"^https?://", "", url, flags=re.I).split("/")[0]
            if _WETT_HOST_RE.search(host):
                befunde.append(Befund(pfad, i, f"Link auf Wett-/Casino-Seite: {url}"))
        davor = " ".join(zeilen[max(0, i - 3):i - 1])
        for satz in _saetze(z):
            m = _VERSPRECHEN_RE.search(satz)
            if m and not _VERNEINUNG_RE.search(satz) and not _VERNEINUNG_RE.search(davor):
                befunde.append(Befund(pfad, i, f"Wett-Sprache/Versprechen „{m.group(1)}“ – sachlich formulieren"))
        if ist_website:
            for m in _PLATZHALTER_RE.finditer(z):
                befunde.append(Befund(pfad, i, f"Offener Platzhalter auf der Website: {m.group(0)[:60]}"))

    # Pflichthinweis 18+ / Hilfsangebot
    braucht_hinweis = False
    if ist_website:
        braucht_hinweis = "100-euro" in os.path.basename(pfad)
    elif ist_social:
        braucht_hinweis = bool(_EXPERIMENT_RE.search(inhalt))
    elif ist_redaktion or _DATEI_RE.search(os.path.basename(pfad)):
        braucht_hinweis = True
    if braucht_hinweis:
        fehlt = []
        if "18+" not in inhalt:
            fehlt.append("„18+“")
        if "check-dein-spiel" not in inhalt.lower() and "süchtig" not in inhalt.lower():
            fehlt.append("Hilfe-Hinweis (check-dein-spiel.de)")
        if fehlt:
            befunde.append(Befund(pfad, 1, "Pflichthinweis unvollständig, es fehlt: " + ", ".join(fehlt)))

    # Zahlen nur aus den Daten (Vor-/Nachberichte und ihre Social-Pakete)
    erlaubt = erlaubte_zahlen(pfad.replace("social-", ""), wurzel) if (ist_redaktion or ist_social) else None
    if erlaubt is not None:
        for i, z in enumerate(zeilen, 1):
            for wert in _PROZENT_RE.findall(z):
                if wert not in erlaubt:
                    befunde.append(Befund(pfad, i, f"„{wert} %“ steht in keinem Datenpaket – Zahl prüfen"))
            for wert in _DEZIMAL_RE.findall(z):
                if wert not in erlaubt:
                    befunde.append(Befund(pfad, i, f"„{wert}“ steht in keinem Datenpaket – Zahl prüfen"))

    # Offene Platzhalter in Redaktions-Entwürfen: nur Hinweis (werden vor der Veröffentlichung gefüllt)
    if ist_redaktion:
        offen = len(_PLATZHALTER_RE.findall(inhalt))
        if offen:
            befunde.append(Befund(pfad, 0, f"{offen} offene Stelle(n) [PRÜFEN]/[AUS DER REDAKTION] – vor dem Veröffentlichen füllen", fehler=False))
    return befunde


def relevant(pfad):
    p = pfad.replace("\\", "/")
    return p.endswith(ENDUNGEN) and (p.startswith("entwuerfe/") or p.startswith("website/src/"))


def alle_dateien(wurzel="."):
    treffer = []
    for muster in ("entwuerfe/**/*", "website/src/**/*"):
        for p in glob.glob(os.path.join(wurzel, muster), recursive=True):
            rel = os.path.relpath(p, wurzel).replace("\\", "/")
            if os.path.isfile(p) and relevant(rel):
                treffer.append(rel)
    return sorted(treffer)


def bericht(befunde, dateien):
    fehler = [b for b in befunde if b.fehler]
    hinweise = [b for b in befunde if not b.fehler]
    z = ["## Qualitätsprüfung", ""]
    z.append(f"Geprüft: {len(dateien)} Datei(en). " + ("✅ Keine Fehler." if not fehler else f"❌ {len(fehler)} Fehler – bitte vor dem Merge beheben."))
    z.append("")
    if fehler:
        z += ["| Datei | Zeile | Problem |", "|---|---|---|"]
        z += [f"| `{b.datei}` | {b.zeile} | {b.text} |" for b in fehler]
        z.append("")
    if hinweise:
        z += ["**Hinweise (kein Fehler):**", ""] + [f"- `{b.datei}`: {b.text}" for b in hinweise] + [""]
    z.append("Regeln: siehe `QUALITAETSPRUEFUNG.md`.")
    return "\n".join(z) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    dateien = alle_dateien() if "--alle" in argv else [a for a in argv if relevant(a) and os.path.exists(a)]
    befunde = [b for d in dateien for b in pruefe_datei(d)]
    text = bericht(befunde, dateien)
    print(text)
    for b in befunde:
        art = "error" if b.fehler else "notice"
        print(f"::{art} file={b.datei},line={max(b.zeile, 1)}::{b.text}")
    ziel = os.environ.get("GITHUB_STEP_SUMMARY")
    if ziel:
        with open(ziel, "a", encoding="utf-8") as f:
            f.write(text)
    return 1 if any(b.fehler for b in befunde) else 0


if __name__ == "__main__":
    sys.exit(main())
