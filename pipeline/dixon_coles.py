"""Poisson-Modell nach Dixon & Coles (1997), Version 0.2.

Tore Heim ~ Poisson(exp(mu + heim + angriff[heim] - abwehr[gast]))
Tore Gast ~ Poisson(exp(mu + angriff[gast] - abwehr[heim]))
plus Korrektur tau(rho) für die Ergebnisse 0:0, 1:0, 0:1, 1:1.

Ältere Spiele zählen weniger: Gewicht = exp(-xi * Tage vor dem Stichtag).
Eine schwache Ridge-Strafe hält die Teamwerte nahe einem Vorwert (normal 0). Aufsteiger
bekommen als Vorwert den Mittelwert der drei Absteiger der Vorsaison, weil wir keine Daten
aus der 2. Liga einbeziehen.

Benötigt numpy und scipy (requirements.txt).
"""
from datetime import datetime

import numpy as np
from scipy.optimize import minimize

VERSION = "dc-0.2"
STANDARD = {"xi": 0.002, "fenster_tage": 3 * 365, "ridge": 1.0, "max_tore": 10}


def _datum(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


class DixonColes:
    def __init__(self, params=None):
        self.p = dict(STANDARD)
        if params:
            self.p.update({k: v for k, v in params.items() if k in STANDARD})
        self.teams = []
        self.index = {}
        self.theta = None
        self._start = None

    # ---------- Anpassung ----------
    def anpassen(self, spiele, stichtag, vorwerte=None):
        """spiele: beendete Spiele (beliebige Saisons), stichtag: ISO-Zeit; nur Spiele davor zählen.
        vorwerte: {team_id: (angriff, abwehr)} für die Ridge-Strafe (sonst 0)."""
        t0 = _datum(stichtag)
        daten = []
        for s in spiele:
            if not s["beendet"] or not s["anstoss_utc"]:
                continue
            tage = (t0 - _datum(s["anstoss_utc"])).total_seconds() / 86400.0
            if tage <= 0 or tage > self.p["fenster_tage"]:
                continue
            daten.append((s["heim_id"], s["gast_id"], s["tore_heim"], s["tore_gast"], np.exp(-self.p["xi"] * tage)))
        teams = sorted({d[0] for d in daten} | {d[1] for d in daten} | set((vorwerte or {}).keys()))
        if len(daten) < 50:
            raise ValueError("Zu wenige Spiele für die Anpassung")
        idx = {t: i for i, t in enumerate(teams)}
        n = len(teams)
        h = np.array([idx[d[0]] for d in daten])
        g = np.array([idx[d[1]] for d in daten])
        x = np.array([d[2] for d in daten], dtype=float)
        y = np.array([d[3] for d in daten], dtype=float)
        w = np.array([d[4] for d in daten])
        a0 = np.zeros(n)
        d0 = np.zeros(n)
        for t, (va, vd) in (vorwerte or {}).items():
            a0[idx[t]], d0[idx[t]] = va, vd
        lam_r = self.p["ridge"]

        # Startwerte (warm, falls vorhanden)
        start = np.zeros(2 * n + 3)
        start[-3], start[-2], start[-1] = 0.15, 0.25, -0.05  # mu, heim, rho
        if self.theta is not None:
            for t, i in idx.items():
                if t in self.index:
                    j = self.index[t]
                    start[i], start[n + i] = self.theta[j], self.theta[len(self.teams) + j]
            start[-3:] = self.theta[-3:]

        m00 = (x == 0) & (y == 0)
        m01 = (x == 0) & (y == 1)
        m10 = (x == 1) & (y == 0)
        m11 = (x == 1) & (y == 1)

        def ziel(th):
            a, d = th[:n], th[n:2 * n]
            mu, heim, rho = th[-3], th[-2], th[-1]
            eh = mu + heim + a[h] - d[g]
            eg = mu + a[g] - d[h]
            lh, lg = np.exp(eh), np.exp(eg)
            tau = np.ones_like(x)
            tau[m00] = 1 - lh[m00] * lg[m00] * rho
            tau[m01] = 1 + lh[m01] * rho
            tau[m10] = 1 + lg[m10] * rho
            tau[m11] = 1 - rho
            if np.any(tau <= 0):
                return 1e10, np.zeros_like(th)
            ll = w * (np.log(tau) + x * eh - lh + y * eg - lg)
            wert = -ll.sum() + lam_r * (((a - a0) ** 2).sum() + ((d - d0) ** 2).sum())
            # Gradient
            dh = w * (x - lh)
            dg = w * (y - lg)
            drho = np.zeros_like(x)
            t = tau
            dh[m00] += w[m00] * (-lg[m00] * rho / t[m00]) * lh[m00]
            dg[m00] += w[m00] * (-lh[m00] * rho / t[m00]) * lg[m00]
            drho[m00] = -lh[m00] * lg[m00] / t[m00]
            dh[m01] += w[m01] * (rho / t[m01]) * lh[m01]
            drho[m01] = lh[m01] / t[m01]
            dg[m10] += w[m10] * (rho / t[m10]) * lg[m10]
            drho[m10] = lg[m10] / t[m10]
            drho[m11] = -1 / t[m11]
            ga = np.zeros(n)
            gd = np.zeros(n)
            np.add.at(ga, h, dh)
            np.add.at(gd, g, -dh)
            np.add.at(ga, g, dg)
            np.add.at(gd, h, -dg)
            grad = np.concatenate([-ga + 2 * lam_r * (a - a0), -gd + 2 * lam_r * (d - d0),
                                   [-(dh.sum() + dg.sum()), -dh.sum(), -(w * drho).sum()]])
            return wert, grad

        self._ziel = ziel  # für Tests (Gradientenprüfung)
        grenzen = [(None, None)] * (2 * n + 2) + [(-0.3, 0.3)]
        res = minimize(ziel, start, jac=True, method="L-BFGS-B", bounds=grenzen)
        self.teams, self.index, self.theta = teams, idx, res.x
        return self

    # ---------- Vorhersage ----------
    def werte(self, team_id):
        n = len(self.teams)
        if team_id not in self.index:
            return 0.0, 0.0
        i = self.index[team_id]
        return self.theta[i], self.theta[n + i]

    def erwartete_tore(self, heim_id, gast_id):
        mu, heim = self.theta[-3], self.theta[-2]
        ah, dh = self.werte(heim_id)
        ag, dg = self.werte(gast_id)
        return float(np.exp(mu + heim + ah - dg)), float(np.exp(mu + ag - dh))

    def ergebnis_matrix(self, heim_id, gast_id):
        lh, lg = self.erwartete_tore(heim_id, gast_id)
        rho = self.theta[-1]
        k = np.arange(self.p["max_tore"] + 1)
        from math import factorial
        fak = np.array([factorial(int(i)) for i in k], dtype=float)
        ph = np.exp(-lh) * lh ** k / fak
        pg = np.exp(-lg) * lg ** k / fak
        m = np.outer(ph, pg)
        m[0, 0] *= 1 - lh * lg * rho
        m[0, 1] *= 1 + lh * rho
        m[1, 0] *= 1 + lg * rho
        m[1, 1] *= 1 - rho
        return m / m.sum()

    def vorhersage(self, heim_id, gast_id):
        m = self.ergebnis_matrix(heim_id, gast_id)
        return float(np.tril(m, -1).sum()), float(np.trace(m)), float(np.triu(m, 1).sum())


def absteiger_vorwerte(modell, spiele_vorsaison, spiele_saison):
    """Vorwerte für Aufsteiger: Mittel der Werte der Plätze 16-18 der Vorsaison."""
    from .tabelle import berechne_tabelle
    tab = berechne_tabelle(spiele_vorsaison, vor_spieltag=10 ** 6)
    unten = [t for t, z in tab.items() if z["platz"] >= 16]
    werte = [modell.werte(t) for t in unten if t in modell.index]
    if not werte:
        return {}
    va = float(np.mean([w[0] for w in werte]))
    vd = float(np.mean([w[1] for w in werte]))
    alt = {s["heim_id"] for s in spiele_vorsaison} | {s["gast_id"] for s in spiele_vorsaison}
    neu = ({s["heim_id"] for s in spiele_saison} | {s["gast_id"] for s in spiele_saison}) - alt
    return {t: (va, vd) for t in neu}


def walk_forward(saisons, params=None, von=None, bis=None):
    """Für jeden Spieltag der Saisons von..bis: Anpassung nur mit Spielen vor dem ersten Anstoß
    des Spieltags, dann Vorhersage. Gibt ein Protokoll wie EloModell.lauf zurück."""
    alle = [s for j in sorted(saisons) for s in saisons[j]]
    protokoll = []
    modell = DixonColes(params)
    for jahr in sorted(saisons):
        if (von and jahr < von) or (bis and jahr > bis):
            continue
        sp = saisons[jahr]
        vorwerte = {}
        if jahr - 1 in saisons:
            erster = min(s["anstoss_utc"] for s in sp if s["spieltag"] == 1 and s["anstoss_utc"])
            modell.anpassen(alle, erster)
            vorwerte = absteiger_vorwerte(modell, saisons[jahr - 1], sp)
        for tag in sorted({s["spieltag"] for s in sp}):
            dieser = [s for s in sp if s["spieltag"] == tag and s["beendet"]]
            if not dieser:
                continue
            stichtag = min(s["anstoss_utc"] for s in sp if s["spieltag"] == tag and s["anstoss_utc"])
            modell.anpassen(alle, stichtag, vorwerte)
            for s in dieser:
                p = modell.vorhersage(s["heim_id"], s["gast_id"])
                erg = "heim" if s["tore_heim"] > s["tore_gast"] else "gast" if s["tore_heim"] < s["tore_gast"] else "remis"
                protokoll.append({"saison": jahr, "spieltag": tag, "id": s["id"], "p": p, "ergebnis": erg,
                                  "heim_id": s["heim_id"], "gast_id": s["gast_id"]})
    return protokoll
