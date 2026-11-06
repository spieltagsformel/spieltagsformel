"""API-Football (api-sports.io) – Ausfälle (verletzt/gesperrt) für den Vorbericht.

Schlüssel nur aus der Umgebungsvariable API_FOOTBALL_KEY (GitHub-Secret), nie im Code.
Gratis-Tarif: 100 Abrufe pro Tag.
"""
import json
import urllib.parse
import urllib.request

BASIS = "https://v3.football.api-sports.io"
BUNDESLIGA = 78


def abrufen(schluessel, endpunkt, **params):
    url = f"{BASIS}/{endpunkt}" + (("?" + urllib.parse.urlencode(params)) if params else "")
    req = urllib.request.Request(url, headers={"x-apisports-key": schluessel, "User-Agent": "spieltagsformel-pipeline"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def pruefen(schluessel, saison):
    """Kleiner Test (3 Abrufe): Konto, Abdeckung der Saison, Ausfälle. Gibt nur Zusammenfassungen zurück."""
    ergebnis = {}
    status = abrufen(schluessel, "status")
    konto = (status.get("response") or {})
    ergebnis["status"] = {"fehler": status.get("errors"), "tarif": (konto.get("subscription") or {}).get("plan"),
                          "abrufe_heute": (konto.get("requests") or {})}
    liga = abrufen(schluessel, "leagues", id=BUNDESLIGA, season=saison)
    abdeckung = None
    for eintrag in liga.get("response") or []:
        for s in eintrag.get("seasons") or []:
            if s.get("year") == saison:
                abdeckung = {"start": s.get("start"), "ende": s.get("end"), "coverage": s.get("coverage")}
    ergebnis["liga"] = {"fehler": liga.get("errors"), "saison": abdeckung}
    aus = abrufen(schluessel, "injuries", league=BUNDESLIGA, season=saison)
    zeilen = aus.get("response") or []
    ergebnis["ausfaelle"] = {
        "fehler": aus.get("errors"),
        "anzahl": len(zeilen),
        "teams": len({(z.get("team") or {}).get("name") for z in zeilen}),
        "felder": sorted({k for z in zeilen[:5] for k in z}),
        "beispiel_gruende": sorted({(z.get("player") or {}).get("reason") for z in zeilen if z.get("player")})[:10],
        "spiele_bis": max(((z.get("fixture") or {}).get("date") or "" for z in zeilen), default=None),
    }
    return ergebnis
