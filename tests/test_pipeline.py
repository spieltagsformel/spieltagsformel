import json
import os
import tempfile
import unittest

from pipeline import openligadb, paket, speicher, tabelle

# Echtes Beispielspiel im Format der OpenLigaDB (Saison 2025/26, Spieltag 1)
BEISPIEL = {
    "matchID": 77258, "matchDateTime": "2025-08-23T15:30:00", "matchDateTimeUTC": "2025-08-23T13:30:00Z",
    "group": {"groupName": "1. Spieltag", "groupOrderID": 1, "groupID": 47611},
    "team1": {"teamId": 91, "teamName": "Eintracht Frankfurt"},
    "team2": {"teamId": 134, "teamName": "SV Werder Bremen"},
    "matchIsFinished": True,
    "matchResults": [
        {"resultName": "Halbzeit", "pointsTeam1": 2, "pointsTeam2": 0, "resultTypeKind": "HalfTime"},
        {"resultName": "Endergebnis", "pointsTeam1": 4, "pointsTeam2": 1, "resultTypeKind": "After90Minutes"},
    ],
}


def spiel(id_, tag, heim, gast, tore=None, utc="2026-08-22T13:30:00Z"):
    return {"id": id_, "saison": 2026, "spieltag": tag, "anstoss_utc": utc, "anstoss_lokal": utc,
            "heim_id": heim, "heim": f"Team {heim}", "gast_id": gast, "gast": f"Team {gast}",
            "beendet": tore is not None, "tore_heim": tore[0] if tore else None,
            "tore_gast": tore[1] if tore else None, "ht_heim": None, "ht_gast": None}


def saison_18(ergebnisse_tag1, tag2_offen=True):
    """18 Teams, Spieltag 1 mit 9 Spielen (1-2, 3-4, ...), Spieltag 2 mit 9 Spielen (1-3, 2-4, ...)."""
    s = []
    for i in range(9):
        s.append(spiel(100 + i, 1, 2 * i + 1, 2 * i + 2, ergebnisse_tag1[i]))
    paare = [(1, 3), (2, 4), (5, 7), (6, 8), (9, 11), (10, 12), (13, 15), (14, 16), (17, 18)]
    for i, (h, g) in enumerate(paare):
        s.append(spiel(200 + i, 2, h, g, None if tag2_offen else (1, 1), utc="2026-08-29T13:30:00Z"))
    return s


class Umwandeln(unittest.TestCase):
    def test_echtes_spiel(self):
        z = openligadb.umwandeln(BEISPIEL, 2025)
        self.assertEqual((z["id"], z["spieltag"], z["heim"], z["gast"]), (77258, 1, "Eintracht Frankfurt", "SV Werder Bremen"))
        self.assertEqual((z["tore_heim"], z["tore_gast"], z["ht_heim"], z["ht_gast"]), (4, 1, 2, 0))
        self.assertTrue(z["beendet"])

    def test_nicht_beendet(self):
        m = dict(BEISPIEL, matchIsFinished=False, matchResults=[])
        z = openligadb.umwandeln(m, 2025)
        self.assertFalse(z["beendet"])
        self.assertIsNone(z["tore_heim"])

    def test_beendet_ohne_ergebnis_ist_fehler(self):
        m = dict(BEISPIEL, matchResults=[])
        with self.assertRaises(ValueError):
            openligadb.umwandeln(m, 2025)


class Tabelle(unittest.TestCase):
    def test_punkte_und_sortierung(self):
        spiele = [spiel(1, 1, 1, 2, (2, 0)), spiel(2, 1, 3, 4, (1, 1))]
        t = tabelle.berechne_tabelle(spiele, vor_spieltag=2)
        self.assertEqual(t[1]["platz"], 1)
        self.assertEqual(t[1]["punkte"], 3)
        self.assertEqual(t[2]["punkte"], 0)
        self.assertEqual(t[3]["punkte"], 1)
        self.assertEqual(t[1]["tordifferenz"], 2)

    def test_spieltag_wird_nicht_mitgezaehlt(self):
        spiele = [spiel(1, 1, 1, 2, (2, 0)), spiel(2, 2, 1, 2, (5, 0))]
        t = tabelle.berechne_tabelle(spiele, vor_spieltag=2)
        self.assertEqual(t[1]["punkte"], 3)

    def test_form(self):
        spiele = [spiel(1, 1, 1, 2, (2, 0)), spiel(2, 2, 3, 1, (1, 1)), spiel(3, 3, 1, 4, (0, 3))]
        self.assertEqual(tabelle.form(spiele, 1, vor_spieltag=4), "SUN")
        self.assertEqual(tabelle.form(spiele, 1, vor_spieltag=3), "SU")

    def test_tabellenplatz_regel(self):
        self.assertEqual(tabelle.tabellenplatz_regel(3, 8), "heim")
        self.assertEqual(tabelle.tabellenplatz_regel(8, 3), "gast")
        self.assertEqual(tabelle.tabellenplatz_regel(4, 5), "remis")
        self.assertEqual(tabelle.tabellenplatz_regel(5, 4), "remis")
        self.assertEqual(tabelle.tabellenplatz_regel(6, 6), "remis")
        self.assertEqual(tabelle.tabellenplatz_regel(4, 6), "heim")
        self.assertEqual(tabelle.tabellenplatz_regel(6, 4), "gast")

    def test_starttabelle_mit_aufsteigern(self):
        vor = [spiel(1, 1, 1, 2, (3, 0)), spiel(2, 1, 3, 4, (0, 1))]
        aktuell = [spiel(10, 1, 1, 2), spiel(11, 1, 4, 9)]
        t = tabelle.start_tabelle(aktuell, vor)
        self.assertEqual(t[1]["platz"], 1)
        self.assertEqual(t[4]["platz"], 2)
        self.assertEqual(t[9]["platz"], 4)
        self.assertTrue(t[9]["aufsteiger_platzhalter"])
        self.assertFalse(t[1]["aufsteiger_platzhalter"])


class Paket(unittest.TestCase):
    def test_spieltag_2(self):
        s = saison_18([(2, 0)] * 9)
        p = paket.baue_paket(2026, 2, s, erstellt="2026-08-27T10:00:00+00:00")
        self.assertEqual(p["saison"], "2026-27")
        self.assertEqual(len(p["spiele"]), 9)
        self.assertEqual(p["hinweise"], [])
        self.assertEqual(len(p["tabelle_vor_spieltag"]), 18)
        erstes = next(x for x in p["spiele"] if x["heim"] == "Team 1")
        self.assertEqual(erstes["form_heim"], "S")
        self.assertEqual(erstes["form_gast"], "S")  # Team 3 gewann ebenfalls
        self.assertEqual(erstes["platz_heim"], 1)
        self.assertIsNone(erstes["ergebnis"])
        self.assertIsNone(erstes["modell"])

    def test_naechster_spieltag(self):
        self.assertEqual(paket.naechster_spieltag(saison_18([(2, 0)] * 9)), 2)
        self.assertIsNone(paket.naechster_spieltag([spiel(1, 1, 1, 2, (1, 0))]))

    def test_spieltag_1_braucht_vorsaison(self):
        s = saison_18([None] * 9)
        with self.assertRaises(ValueError):
            paket.baue_paket(2026, 1, s)

    def test_unbekannter_spieltag(self):
        with self.assertRaises(ValueError):
            paket.baue_paket(2026, 99, saison_18([(1, 0)] * 9))

    def test_nachholspiel_wird_gemeldet(self):
        erg = [(1, 0)] * 8 + [None]
        p = paket.baue_paket(2026, 2, saison_18(erg))
        self.assertTrue(any("nicht beendet" in h for h in p["hinweise"]))


class Speicher(unittest.TestCase):
    def test_csv_hin_und_zurueck(self):
        zeilen = saison_18([(2, 0)] * 9)
        with tempfile.TemporaryDirectory() as d:
            pfad = os.path.join(d, "x", "s.csv")
            speicher.schreibe_csv(pfad, zeilen)
            zurueck = speicher.lese_csv(pfad)
        self.assertEqual(len(zurueck), len(zeilen))
        self.assertEqual(sorted(z["id"] for z in zurueck), sorted(z["id"] for z in zeilen))
        offen = next(z for z in zurueck if z["spieltag"] == 2)
        self.assertFalse(offen["beendet"])
        self.assertIsNone(offen["tore_heim"])


class Qualitaet(unittest.TestCase):
    def test_warnung_bei_falscher_spielzahl(self):
        w = openligadb.pruefen_saison(saison_18([(1, 0)] * 9))
        self.assertTrue(any("statt 306" in x for x in w))


# ---- Elo-Modell und Metriken ----
import math
from pipeline import elo, metriken


class EloTests(unittest.TestCase):
    def test_wahrscheinlichkeiten_summe_eins(self):
        for d in (-300, -50, 0, 80, 400):
            p = elo.wahrscheinlichkeiten(1500 + d, 1500, elo.STANDARD)
            self.assertAlmostEqual(sum(p), 1.0)
            self.assertTrue(all(0 < x < 1 for x in p))

    def test_heimvorteil_und_staerke(self):
        gleich = elo.wahrscheinlichkeiten(1500, 1500, elo.STANDARD)
        self.assertGreater(gleich[0], gleich[2])
        staerker = elo.wahrscheinlichkeiten(1600, 1500, elo.STANDARD)
        self.assertGreater(staerker[0], gleich[0])
        self.assertLess(staerker[2], gleich[2])

    def test_verhaeltnis_heim_gast_ist_r(self):
        p = dict(elo.STANDARD, heimvorteil=0.0)
        ph, pd, pa = elo.wahrscheinlichkeiten(1600, 1500, p)
        self.assertAlmostEqual(ph / pa, 10 ** (100 / 400))

    def test_remis_rate_bei_gleichstand(self):
        p = dict(elo.STANDARD, heimvorteil=0.0, nu=0.74)
        self.assertAlmostEqual(elo.wahrscheinlichkeiten(1500, 1500, p)[1], 0.74 / 2.74)

    def test_torfaktor(self):
        self.assertEqual(elo.tor_faktor(0), 1.0)
        self.assertEqual(elo.tor_faktor(-1), 1.0)
        self.assertEqual(elo.tor_faktor(2), 1.5)
        self.assertAlmostEqual(elo.tor_faktor(4), 15 / 8)

    def test_sieger_gewinnt_punkte_summe_null(self):
        m = elo.EloModell()
        m.verarbeite(spiel(1, 1, 1, 2, (3, 0)))
        self.assertGreater(m.rating[1], 1500)
        self.assertLess(m.rating[2], 1500)
        self.assertAlmostEqual(m.rating[1] + m.rating[2], 3000)

    def test_remis_gleich_starker_teams_aendert_nur_wegen_heimvorteil(self):
        m = elo.EloModell()
        m.verarbeite(spiel(1, 1, 1, 2, (1, 1)))
        self.assertLess(m.rating[1], 1500)  # Heimteam hätte laut Modell gewinnen sollen

    def test_neue_saison_regress_und_aufsteiger(self):
        m = elo.EloModell({"regress": 0.5, "aufsteiger": 1400.0})
        m.rating = {1: 1700.0}
        m._erste_saison = True
        m.neue_saison()
        self.assertAlmostEqual(m.rating[1], 1600.0)
        self.assertEqual(m.rating_von(99), 1400.0)

    def test_lauf_nutzt_nur_vergangenheit(self):
        s1 = [spiel(1, 1, 1, 2, (2, 0), utc="2026-08-01T10:00:00Z"), spiel(2, 2, 1, 2, (2, 0), utc="2026-08-08T10:00:00Z")]
        prot = elo.EloModell().lauf({2026: s1})
        self.assertAlmostEqual(prot[0]["p"][0], elo.wahrscheinlichkeiten(1500, 1500, elo.STANDARD)[0])
        self.assertGreater(prot[1]["p"][0], prot[0]["p"][0])  # nach dem ersten Sieg ist Team 1 stärker eingeschätzt

    def test_unbeendete_spiele_werden_ignoriert(self):
        prot = elo.EloModell().lauf({2026: [spiel(1, 1, 1, 2)]})
        self.assertEqual(prot, [])


class MetrikTests(unittest.TestCase):
    def test_rps(self):
        self.assertAlmostEqual(metriken.rps((1, 0, 0), "heim"), 0.0)
        self.assertAlmostEqual(metriken.rps((1 / 3, 1 / 3, 1 / 3), "heim"), 5 / 18)
        self.assertAlmostEqual(metriken.rps((0, 0, 1), "heim"), 1.0)

    def test_brier_und_logloss_und_treffer(self):
        self.assertAlmostEqual(metriken.brier((1, 0, 0), "heim"), 0.0)
        self.assertAlmostEqual(metriken.brier((1 / 3,) * 3, "remis"), 2 / 3)
        self.assertAlmostEqual(metriken.logloss((0.5, 0.3, 0.2), "remis"), -math.log(0.3))
        self.assertTrue(metriken.treffer((0.5, 0.3, 0.2), "heim"))
        self.assertFalse(metriken.treffer((0.5, 0.3, 0.2), "gast"))

    def test_paket_mit_modell(self):
        s = saison_18([(2, 0)] * 9)
        probs = {x["id"]: (0.5, 0.3, 0.2) for x in s if x["spieltag"] == 2}
        p = paket.baue_paket(2026, 2, s, modell=probs, modell_version="elo-0.1")
        self.assertEqual(p["spiele"][0]["modell"], {"version": "elo-0.1", "p_heim": 0.5, "p_remis": 0.3, "p_gast": 0.2})



# ---- Dixon-Coles v0.2 ----
try:
    import numpy as np
    from scipy.optimize import check_grad
    from pipeline import dixon_coles
    HAT_NUMPY = True
except ImportError:  # pragma: no cover
    HAT_NUMPY = False


def runde_saison(jahr=2025, stark=1):
    teams = list(range(1, 19))
    tage = []
    t = teams[:]
    for r in range(17):
        tage.append([(t[i], t[17 - i]) for i in range(9)])
        t = [t[0]] + [t[-1]] + t[1:-1]
    tage += [[(g, h) for h, g in tag] for tag in tage]
    spiele = []
    for n, paare in enumerate(tage, start=1):
        for k, (h, g) in enumerate(paare):
            if stark in (h, g):
                tore = (3, 0) if h == stark else (0, 3)
            else:
                tore = ((h + n) % 3, (g + k) % 2)
            monat, tag = 8 + (n - 1) // 4, 1 + ((n - 1) % 4) * 7
            jahr_n = jahr + (1 if monat > 12 else 0)
            monat = monat - 12 if monat > 12 else monat
            spiele.append(spiel(jahr * 1000 + n * 10 + k, n, h, g, tore, utc=f"{jahr_n}-{monat:02d}-{tag:02d}T13:30:00Z"))
    return spiele


@unittest.skipUnless(HAT_NUMPY, "numpy/scipy nicht installiert")
class DixonColesTests(unittest.TestCase):
    def setUp(self):
        self.spiele = runde_saison()
        self.m = dixon_coles.DixonColes().anpassen(self.spiele, "2026-06-01T00:00:00Z")

    def test_wahrscheinlichkeiten(self):
        p = self.m.vorhersage(1, 2)
        self.assertAlmostEqual(sum(p), 1.0, places=6)
        self.assertGreater(p[0], 0.6)  # Team 1 gewinnt in den Daten immer
        q = self.m.vorhersage(2, 1)
        self.assertGreater(q[2], q[0])

    def test_matrix_und_tore(self):
        mat = self.m.ergebnis_matrix(3, 4)
        self.assertAlmostEqual(float(mat.sum()), 1.0, places=9)
        lh, lg = self.m.erwartete_tore(1, 2)
        self.assertGreater(lh, lg)

    def test_gradient(self):
        th = self.m.theta + np.random.default_rng(0).normal(0, 0.05, len(self.m.theta))
        th[-1] = -0.05
        f = lambda t: self.m._ziel(t)[0]
        g = lambda t: self.m._ziel(t)[1]
        self.assertLess(check_grad(f, g, th), 1e-3)

    def test_nur_vergangenheit(self):
        with self.assertRaises(ValueError):
            dixon_coles.DixonColes().anpassen(self.spiele, "2025-08-01T00:00:00Z")

    def test_unbekanntes_team_ist_durchschnitt(self):
        self.assertEqual(self.m.werte(999), (0.0, 0.0))



# ---- Quoten (The Odds API, Antwort nachgebildet) ----
from pipeline import quoten


def ereignis(heim, gast, zeit, preise):
    return {"id": "x", "sport_key": "soccer_germany_bundesliga", "commence_time": zeit, "home_team": heim, "away_team": gast,
            "bookmakers": [{"key": f"b{i}", "title": f"B{i}", "markets": [{"key": "h2h", "outcomes": [
                {"name": heim, "price": p[0]}, {"name": gast, "price": p[2]}, {"name": "Draw", "price": p[1]}]}]}
                for i, p in enumerate(preise)]}


class QuotenTests(unittest.TestCase):
    def setUp(self):
        self.spiele = [
            {"id": 1, "heim": "FC Bayern München", "gast": "Borussia Dortmund", "anstoss_utc": "2026-10-31T17:30:00Z"},
            {"id": 2, "heim": "Borussia Mönchengladbach", "gast": "SC Paderborn 07", "anstoss_utc": "2026-10-31T14:30:00Z"},
            {"id": 3, "heim": "1. FC Köln", "gast": "1. FC Union Berlin", "anstoss_utc": "2026-11-01T14:30:00Z"},
        ]
        self.ereignisse = [
            ereignis("Bayern Munich", "Borussia Dortmund", "2026-10-31T17:30:00Z", [(1.6, 4.2, 5.0), (1.65, 4.0, 4.8)]),
            ereignis("Borussia Monchengladbach", "SC Paderborn", "2026-10-31T14:30:00Z", [(2.2, 3.4, 3.2)]),
            ereignis("FC Koln", "Union Berlin", "2026-11-08T14:30:00Z", [(2.5, 3.3, 2.8)]),  # falscher Termin
        ]

    def test_zuordnung_ueber_namen_und_zeit(self):
        z = quoten.zuordnen(self.ereignisse, self.spiele)
        self.assertEqual(z[1]["home_team"], "Bayern Munich")
        self.assertEqual(z[2]["home_team"], "Borussia Monchengladbach")
        self.assertNotIn(3, z)

    def test_keine_verwechslung_bei_gleicher_zeit(self):
        spiele = [{"id": 9, "heim": "Borussia Dortmund", "gast": "FC Bayern München", "anstoss_utc": "2026-10-31T17:30:00Z"}]
        self.assertEqual(quoten.zuordnen(self.ereignisse, spiele), {})

    def test_margenbereinigung(self):
        m = quoten.markt(self.ereignisse[1])
        roh = [1 / 2.2, 1 / 3.4, 1 / 3.2]
        self.assertAlmostEqual(m["p_heim"], roh[0] / sum(roh))
        self.assertAlmostEqual(m["p_heim"] + m["p_remis"] + m["p_gast"], 1.0)
        self.assertEqual(m["buchmacher"], 1)

    def test_paket_enthaelt_keine_rohquoten(self):
        paket = {"spiele": [dict(s) for s in self.spiele], "quellen": [], "hinweise": []}
        n = quoten.ergaenze_paket(paket, self.ereignisse, "2026-10-30T10:00:00+00:00")
        self.assertEqual(n, 2)
        self.assertNotIn("quote_mittel", paket["spiele"][0]["markt"])
        self.assertEqual(paket["spiele"][0]["markt"]["buchmacher"], 2)
        self.assertTrue(any("keine Quoten" in h for h in paket["hinweise"]))
        self.assertNotIn("B0", json.dumps(paket))

    def test_ohne_schluessel_fehler(self):
        with self.assertRaises(ValueError):
            quoten.abrufen("")



# ---- Einfrieren und Nachbericht ----
from pipeline import nachbericht


def paketspiel(id_, heim, gast, ph, pr, pg, regel, markt=None, utc="2026-10-31T14:30:00Z"):
    s = {"id": id_, "heim": heim, "gast": gast, "anstoss_utc": utc,
         "modell": {"version": "elo-0.1", "p_heim": ph, "p_remis": pr, "p_gast": pg},
         "vergleich": {"tabellenplatz": regel, "community": None}}
    if markt:
        s["markt"] = {"p_heim": markt[0], "p_remis": markt[1], "p_gast": markt[2], "buchmacher": 20}
    return s


class EinfrierenTests(unittest.TestCase):
    def test_begonnene_spiele_bleiben(self):
        alt = {"erstellt": "2026-10-30T10:00:00+00:00", "spiele": [
            paketspiel(1, "A", "B", 0.5, 0.3, 0.2, "heim", utc="2026-10-30T19:30:00Z"),
            paketspiel(2, "C", "D", 0.4, 0.3, 0.3, "heim", utc="2026-11-01T14:30:00Z")]}
        neu = {"spiele": [paketspiel(1, "A", "B", 0.9, 0.05, 0.05, "gast", utc="2026-10-30T19:30:00Z"),
                          paketspiel(2, "C", "D", 0.6, 0.2, 0.2, "gast", utc="2026-11-01T14:30:00Z")]}
        out = paket.einfrieren(neu, alt, "2026-10-31T12:00:00+00:00")
        self.assertEqual(out["spiele"][0]["modell"]["p_heim"], 0.5)   # schon angepfiffen: alter Wert
        self.assertEqual(out["spiele"][0]["vergleich"]["tabellenplatz"], "heim")
        self.assertEqual(out["spiele"][0]["eingefroren"], "2026-10-30T10:00:00+00:00")
        self.assertEqual(out["spiele"][1]["modell"]["p_heim"], 0.6)   # noch nicht angepfiffen: neu

    def test_bis_stichtag(self):
        s = {2026: [spiel(1, 1, 1, 2, (2, 0), utc="2026-08-01T10:00:00Z"), spiel(2, 2, 1, 2, (3, 0), utc="2026-08-09T10:00:00Z")]}
        k = paket.bis_stichtag(s, "2026-08-05T00:00:00Z")
        self.assertTrue(k[2026][0]["beendet"])
        self.assertFalse(k[2026][1]["beendet"])
        self.assertTrue(s[2026][1]["beendet"])  # Original unverändert


class NachberichtTests(unittest.TestCase):
    def setUp(self):
        self.paket = {"saison": "2026-27", "spieltag": 8, "spiele": [
            paketspiel(1, "FC Bayern München", "Borussia Dortmund", 0.58, 0.25, 0.17, "remis", (0.70, 0.17, 0.13)),
            paketspiel(2, "FC Schalke 04", "RB Leipzig", 0.20, 0.26, 0.54, "gast", (0.25, 0.24, 0.51)),
            paketspiel(3, "1. FC Union Berlin", "1. FC Köln", 0.45, 0.28, 0.27, "gast", (0.37, 0.26, 0.37))]}
        self.spiele = [spiel(1, 8, 40, 7, (1, 1)), spiel(2, 8, 9, 1635, (0, 2)), spiel(3, 8, 80, 65, (2, 0))]

    def test_auswertung(self):
        z = nachbericht.auswerten(self.paket, self.spiele)
        self.assertEqual([x["ergebnis"] for x in z], ["remis", "gast", "heim"])
        self.assertFalse(z[0]["formel"]["treffer"])
        self.assertTrue(z[0]["regel_treffer"])
        self.assertTrue(z[1]["formel"]["treffer"] and z[1]["markt"]["treffer"])
        self.assertAlmostEqual(z[0]["formel"]["p_ergebnis"], 0.25)

    def test_zusammenfassung_und_text(self):
        z = nachbericht.auswerten(self.paket, self.spiele)
        s = nachbericht.zusammenfassung(z)
        self.assertEqual(s["formel"]["treffer"], 2)
        self.assertEqual(s["markt"]["treffer"], 2)
        self.assertEqual(s["regel"]["treffer"], 2)
        self.assertEqual(s["daneben"]["id"], 1)  # Remis mit nur 25 %
        t = nachbericht.text(self.paket, z, s)
        self.assertIn("2 von 3", t)
        self.assertIn("| Markt |", t)
        self.assertIn("[AUS DER REDAKTION", t)
        self.assertIn("keine Wettempfehlung".lower(), t.lower())
        self.assertNotIn("Tipp", t)

    def test_unbeendete_spiele_werden_ausgelassen(self):
        spiele = [spiel(1, 8, 40, 7, (1, 1)), spiel(2, 8, 9, 1635), spiel(3, 8, 80, 65, (2, 0))]
        self.assertEqual(len(nachbericht.auswerten(self.paket, spiele)), 2)


if __name__ == "__main__":
    unittest.main()
