"""Tabelle vor einem Spieltag, Form und Tabellenplatz-Regel.

Sortierung: Punkte, Tordifferenz, erzielte Tore, Name (vereinfacht; der direkte Vergleich
als weiteres Kriterium der DFL ist nicht abgebildet).
"""


def _leer(name):
    return {"team": name, "spiele": 0, "siege": 0, "remis": 0, "niederlagen": 0, "tore": 0, "gegentore": 0, "punkte": 0}


def berechne_tabelle(spiele, vor_spieltag):
    """Tabelle auf Basis aller beendeten Spiele mit spieltag < vor_spieltag."""
    zeilen = {}
    for s in spiele:
        zeilen.setdefault(s["heim_id"], _leer(s["heim"]))
        zeilen.setdefault(s["gast_id"], _leer(s["gast"]))
    for s in spiele:
        if not s["beendet"] or s["spieltag"] >= vor_spieltag:
            continue
        h, g = zeilen[s["heim_id"]], zeilen[s["gast_id"]]
        h["spiele"] += 1
        g["spiele"] += 1
        h["tore"] += s["tore_heim"]
        h["gegentore"] += s["tore_gast"]
        g["tore"] += s["tore_gast"]
        g["gegentore"] += s["tore_heim"]
        if s["tore_heim"] > s["tore_gast"]:
            h["siege"] += 1; h["punkte"] += 3; g["niederlagen"] += 1
        elif s["tore_heim"] < s["tore_gast"]:
            g["siege"] += 1; g["punkte"] += 3; h["niederlagen"] += 1
        else:
            h["remis"] += 1; g["remis"] += 1; h["punkte"] += 1; g["punkte"] += 1
    liste = list(zeilen.items())
    liste.sort(key=lambda kv: (-kv[1]["punkte"], -(kv[1]["tore"] - kv[1]["gegentore"]), -kv[1]["tore"], kv[1]["team"]))
    ergebnis = {}
    for platz, (team_id, z) in enumerate(liste, start=1):
        z = dict(z)
        z["platz"] = platz
        z["tordifferenz"] = z["tore"] - z["gegentore"]
        ergebnis[team_id] = z
    return ergebnis


def start_tabelle(spiele_saison, spiele_vorsaison):
    """Tabelle für Spieltag 1: Abschlusstabelle der Vorsaison.

    Teams ohne Vorsaison-Platz (Aufsteiger) bekommen die letzten Plätze in alphabetischer
    Reihenfolge und werden markiert; der Platz ist dann nur ein Platzhalter.
    """
    alt = berechne_tabelle(spiele_vorsaison, vor_spieltag=10**6)
    teams = {}
    for s in spiele_saison:
        teams[s["heim_id"]] = s["heim"]
        teams[s["gast_id"]] = s["gast"]
    bekannt = sorted((t for t in teams if t in alt), key=lambda t: alt[t]["platz"])
    neu = sorted((t for t in teams if t not in alt), key=lambda t: teams[t])
    ergebnis = {}
    for platz, t in enumerate(bekannt + neu, start=1):
        z = _leer(teams[t])
        z["platz"] = platz
        z["tordifferenz"] = 0
        z["aufsteiger_platzhalter"] = t in neu
        ergebnis[t] = z
    return ergebnis


def form(spiele, team_id, vor_spieltag, anzahl=5):
    """Letzte Ergebnisse als Buchstaben (S, U, N), ältestes zuerst."""
    gespielt = [s for s in spiele if s["beendet"] and s["spieltag"] < vor_spieltag
                and team_id in (s["heim_id"], s["gast_id"])]
    gespielt.sort(key=lambda s: (s["spieltag"], s["anstoss_utc"] or ""))
    buchstaben = []
    for s in gespielt[-anzahl:]:
        eigene, fremde = (s["tore_heim"], s["tore_gast"]) if s["heim_id"] == team_id else (s["tore_gast"], s["tore_heim"])
        buchstaben.append("S" if eigene > fremde else "N" if eigene < fremde else "U")
    return "".join(buchstaben)


def tabellenplatz_regel(platz_heim, platz_gast):
    """Vergleichsmaßstab 1 (eingefroren): der besser Platzierte gewinnt,
    bei höchstens einem Platz Abstand gilt Remis."""
    abstand = platz_gast - platz_heim  # positiv: Heimteam steht besser
    if abs(abstand) <= 1:
        return "remis"
    return "heim" if abstand > 1 else "gast"
