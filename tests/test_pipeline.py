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


if __name__ == "__main__":
    unittest.main()
