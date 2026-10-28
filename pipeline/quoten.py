"""Aktuelle Quoten vor Anpfiff über The Odds API (https://the-odds-api.com).

Wichtig (Nutzungsbedingungen): Rohdaten der Quoten dürfen nicht weitergegeben werden.
Ins öffentliche Datenpaket kommen deshalb nur daraus abgeleitete, margenbereinigte
Wahrscheinlichkeiten und die Zahl der Buchmacher. Buchmachernamen werden nicht gespeichert.
Der API-Schlüssel kommt aus der Umgebungsvariable ODDS_API_KEY (GitHub-Secret), nie aus dem Code.
"""
import json
import os
import re
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime

SPORT = "soccer_germany_bundesliga"
BASIS = "https://api.the-odds-api.com/v4/sports"

# Wörter, die bei Vereinsnamen nichts unterscheiden
FUELL = {"fc", "sv", "vfb", "vfl", "tsg", "sc", "fsv", "bsc", "1", "04", "05", "07", "1899", "1846", "1910",
         "borussia", "bayer", "eintracht", "rb", "der", "von", "e", "v", "ev"}
ERSATZ = {"munich": "munchen", "cologne": "koln", "gladbach": "monchengladbach", "hamburg": "hamburger"}


def abrufen(api_key, region="eu"):
    """Holt die Vorab-Quoten (1 Credit pro Abruf). Gibt (Ereignisse, verbleibende Credits) zurück."""
    if not api_key:
        raise ValueError("ODDS_API_KEY fehlt")
    parameter = urllib.parse.urlencode({"apiKey": api_key, "regions": region, "markets": "h2h",
                                        "oddsFormat": "decimal", "dateFormat": "iso"})
    req = urllib.request.Request(f"{BASIS}/{SPORT}/odds/?{parameter}",
                                 headers={"User-Agent": "spieltagsformel-pipeline/0.1"})
    with urllib.request.urlopen(req, timeout=30) as antwort:
        rest = antwort.headers.get("x-requests-remaining")
        return json.loads(antwort.read().decode("utf-8")), rest


def _tokens(name):
    s = unicodedata.normalize("NFKD", name.lower())
    s = "".join(c for c in s if not unicodedata.combining(c)).replace("ß", "ss")
    woerter = re.findall(r"[a-z0-9]+", s)
    return {ERSATZ.get(w, w) for w in woerter if w not in FUELL}


def _aehnlich(a, b):
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    gemeinsam = sum(1 for x in ta if any(x == y or (len(x) > 4 and (x in y or y in x)) for y in tb))
    return gemeinsam / max(len(ta), len(tb))


def _zeit(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def zuordnen(ereignisse, spiele, max_stunden=3):
    """Ordnet Ereignisse der API den Spielen des Datenpakets zu (Anstoß + Teamnamen)."""
    zuordnung = {}
    for s in spiele:
        if not s.get("anstoss_utc"):
            continue
        t = _zeit(s["anstoss_utc"])
        bester, punkte = None, 0.0
        for e in ereignisse:
            if abs((_zeit(e["commence_time"]) - t).total_seconds()) > max_stunden * 3600:
                continue
            p = _aehnlich(s["heim"], e["home_team"]) + _aehnlich(s["gast"], e["away_team"])
            if p > punkte:
                bester, punkte = e, p
        if bester is not None and punkte >= 0.9:
            zuordnung[s["id"]] = bester
    return zuordnung


def markt(ereignis):
    """Margenbereinigte Marktwahrscheinlichkeiten (Mittel über alle Buchmacher) und Durchschnittsquoten."""
    probs, quoten = [], []
    for b in ereignis.get("bookmakers", []):
        for m in b.get("markets", []):
            if m.get("key") != "h2h":
                continue
            werte = {}
            for o in m.get("outcomes", []):
                if o["name"] == ereignis["home_team"]:
                    werte["heim"] = float(o["price"])
                elif o["name"] == ereignis["away_team"]:
                    werte["gast"] = float(o["price"])
                else:
                    werte["remis"] = float(o["price"])
            if len(werte) == 3 and all(v > 1.0 for v in werte.values()):
                roh = {k: 1 / v for k, v in werte.items()}
                summe = sum(roh.values())
                probs.append({k: v / summe for k, v in roh.items()})
                quoten.append(werte)
    if not probs:
        return None
    n = len(probs)
    mittel = {k: sum(p[k] for p in probs) / n for k in ("heim", "remis", "gast")}
    q = {k: sum(x[k] for x in quoten) / n for k in ("heim", "remis", "gast")}
    return {"p_heim": mittel["heim"], "p_remis": mittel["remis"], "p_gast": mittel["gast"],
            "buchmacher": n, "quote_mittel": q}


def ergaenze_paket(paket, ereignisse, abruf_zeit):
    """Schreibt die Marktwahrscheinlichkeiten ins Datenpaket (ohne Rohquoten). Gibt Anzahl zugeordneter Spiele zurück."""
    zuordnung = zuordnen(ereignisse, paket["spiele"])
    treffer = 0
    for s in paket["spiele"]:
        # Nach Anpfiff oder bei eingefrorenen Spielen keine Quoten mehr ändern
        if s.get("eingefroren") or (s.get("anstoss_utc") and s["anstoss_utc"].replace("Z", "+00:00") <= abruf_zeit):
            if s.get("markt"):
                treffer += 1
            continue
        e = zuordnung.get(s["id"])
        mk = markt(e) if e else None
        if mk:
            s["markt"] = {"p_heim": round(mk["p_heim"], 4), "p_remis": round(mk["p_remis"], 4),
                          "p_gast": round(mk["p_gast"], 4), "buchmacher": mk["buchmacher"], "abruf": abruf_zeit}
            treffer += 1
    quelle = {"name": "The Odds API (margenbereinigte Durchschnittsquoten)", "url": "https://the-odds-api.com"}
    if treffer and quelle not in paket["quellen"]:
        paket["quellen"].append(quelle)
    fehlend = [s["id"] for s in paket["spiele"] if not s.get("markt")]
    if fehlend:
        paket["hinweise"] = [h for h in paket["hinweise"] if "Quoten" not in h]
        paket["hinweise"].append(f"[PRÜFEN: Für {len(fehlend)} Spiel(e) keine Quoten gefunden]")
    return treffer
