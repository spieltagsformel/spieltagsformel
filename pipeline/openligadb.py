"""Abruf und Umwandlung der OpenLigaDB-Daten (Quelle: https://www.openligadb.de, Lizenz ODbL).

Nur Standardbibliothek, keine Zusatzpakete nötig.
"""
import json
import time
import urllib.error
import urllib.request

BASE = "https://api.openligadb.de"
USER_AGENT = "spieltagsformel-pipeline/0.1 (+https://github.com/spieltagsformel/spieltagsformel)"
LIGA = "bl1"  # 1. Bundesliga; "bl2" = 2. Bundesliga


def get_json(url, versuche=3, pause=2.0):
    """Ruft eine URL ab und gibt das JSON zurück. Wiederholt bei Fehlern."""
    letzter_fehler = None
    for n in range(1, versuche + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as antwort:
                return json.loads(antwort.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as fehler:
            letzter_fehler = fehler
            if n < versuche:
                time.sleep(pause * n)
    raise RuntimeError(f"Abruf fehlgeschlagen: {url} ({letzter_fehler})")


def abrufen_saison(saison, liga=LIGA):
    """Alle Spiele einer Saison. saison = Startjahr, z. B. 2026 für 2026/27."""
    return get_json(f"{BASE}/getmatchdata/{liga}/{saison}")


def _ergebnis(spiel, art):
    for r in spiel.get("matchResults") or []:
        if r.get("resultTypeKind") == art:
            return r.get("pointsTeam1"), r.get("pointsTeam2")
    return None


def umwandeln(spiel, saison):
    """Ein OpenLigaDB-Spiel in eine flache Zeile. Wirft ValueError bei unplausiblen Daten."""
    beendet = bool(spiel.get("matchIsFinished"))
    endstand = _ergebnis(spiel, "After90Minutes")
    halbzeit = _ergebnis(spiel, "HalfTime")
    if beendet and endstand is None:
        raise ValueError(f"Spiel {spiel.get('matchID')} ist beendet, hat aber kein Endergebnis")
    tore_heim, tore_gast = endstand if (beendet and endstand) else (None, None)
    if beendet and (tore_heim is None or tore_gast is None or tore_heim < 0 or tore_gast < 0):
        raise ValueError(f"Spiel {spiel.get('matchID')} hat ein unplausibles Ergebnis: {endstand}")
    return {
        "id": spiel["matchID"],
        "saison": saison,
        "spieltag": spiel["group"]["groupOrderID"],
        "anstoss_utc": spiel.get("matchDateTimeUTC"),
        "anstoss_lokal": spiel.get("matchDateTime"),
        "heim_id": spiel["team1"]["teamId"],
        "heim": spiel["team1"]["teamName"],
        "gast_id": spiel["team2"]["teamId"],
        "gast": spiel["team2"]["teamName"],
        "beendet": beendet,
        "tore_heim": tore_heim,
        "tore_gast": tore_gast,
        "ht_heim": halbzeit[0] if halbzeit else None,
        "ht_gast": halbzeit[1] if halbzeit else None,
    }


def pruefen_saison(zeilen):
    """Gibt eine Liste von Warnungen zur Datenqualität zurück (leer = alles in Ordnung)."""
    warnungen = []
    ids = [z["id"] for z in zeilen]
    if len(ids) != len(set(ids)):
        warnungen.append("doppelte Spiel-IDs")
    if len(zeilen) != 306:
        warnungen.append(f"{len(zeilen)} Spiele statt 306")
    teams = {z["heim_id"] for z in zeilen} | {z["gast_id"] for z in zeilen}
    if len(teams) != 18:
        warnungen.append(f"{len(teams)} Teams statt 18")
    return warnungen
