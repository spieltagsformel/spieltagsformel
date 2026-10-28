"""Elo-Modell v0.1 mit Heimvorteil und Remis-Parameter.

Dreiwege-Wahrscheinlichkeiten nach Davidson: Mit r = 10^(d/400) und d = Elo-Differenz
inkl. Heimvorteil gilt P(Heim) : P(Gast) = r, und der Parameter nu steuert die Remis-Rate.
Nach jedem Spiel wird mit dem Faktor k aktualisiert (Torfaktor wie im World Football Elo).
Zu Saisonbeginn werden alle Werte teilweise zur Mitte (1500) zurückgezogen; Teams ohne
Vorsaison-Wert (Aufsteiger) starten mit dem Parameter `aufsteiger`.
"""
import math

STANDARD = {"k": 20.0, "heimvorteil": 65.0, "regress": 0.25, "aufsteiger": 1400.0, "start": 1500.0, "nu": 0.74}
VERSION = "elo-0.1"


def wahrscheinlichkeiten(r_heim, r_gast, p):
    d = r_heim + p["heimvorteil"] - r_gast
    a = math.sqrt(10 ** (d / 400.0))
    b = 1.0 / a
    s = a + b + p["nu"]
    return a / s, p["nu"] / s, b / s


def tor_faktor(differenz):
    d = abs(differenz)
    if d <= 1:
        return 1.0
    if d == 2:
        return 1.5
    return (11 + d) / 8.0


def _zeit(s):
    return (s["anstoss_utc"] or "", s["spieltag"], s["id"])


class EloModell:
    def __init__(self, params=None):
        self.p = dict(STANDARD)
        if params:
            self.p.update({k: v for k, v in params.items() if k in STANDARD})
        self.rating = {}
        self._erste_saison = True

    def rating_von(self, team_id):
        if team_id in self.rating:
            return self.rating[team_id]
        return self.p["start"] if self._erste_saison else self.p["aufsteiger"]

    def neue_saison(self):
        """Teilweise Rückkehr zur Mitte; ab jetzt gelten unbekannte Teams als Aufsteiger."""
        if self.rating:
            mitte = self.p["start"]
            for t in self.rating:
                self.rating[t] = mitte + (1 - self.p["regress"]) * (self.rating[t] - mitte)
        self._erste_saison = False

    def vorhersage(self, heim_id, gast_id):
        return wahrscheinlichkeiten(self.rating_von(heim_id), self.rating_von(gast_id), self.p)

    def verarbeite(self, s):
        """Aktualisiert die Werte nach einem beendeten Spiel."""
        rh, rg = self.rating_von(s["heim_id"]), self.rating_von(s["gast_id"])
        ph, pd, _ = wahrscheinlichkeiten(rh, rg, self.p)
        erwartet = ph + 0.5 * pd
        if s["tore_heim"] > s["tore_gast"]:
            ist = 1.0
        elif s["tore_heim"] < s["tore_gast"]:
            ist = 0.0
        else:
            ist = 0.5
        delta = self.p["k"] * tor_faktor(s["tore_heim"] - s["tore_gast"]) * (ist - erwartet)
        self.rating[s["heim_id"]] = rh + delta
        self.rating[s["gast_id"]] = rg - delta

    def lauf(self, saisons):
        """saisons: {Startjahr: [Spiele]}. Gibt für jedes beendete Spiel die Vorhersage VOR dem
        Spiel zurück (nur Daten bis dahin, kein Blick in die Zukunft)."""
        protokoll = []
        for i, saison in enumerate(sorted(saisons)):
            if i > 0:
                self.neue_saison()
            for s in sorted(saisons[saison], key=_zeit):
                if not s["beendet"]:
                    continue
                ph, pd, pa = self.vorhersage(s["heim_id"], s["gast_id"])
                ergebnis = "heim" if s["tore_heim"] > s["tore_gast"] else "gast" if s["tore_heim"] < s["tore_gast"] else "remis"
                protokoll.append({"saison": saison, "spieltag": s["spieltag"], "id": s["id"],
                                  "p": (ph, pd, pa), "ergebnis": ergebnis,
                                  "heim_id": s["heim_id"], "gast_id": s["gast_id"]})
                self.verarbeite(s)
        return protokoll
