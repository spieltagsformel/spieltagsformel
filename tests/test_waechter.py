import unittest

from pipeline import waechter


def zeile(tag, erg, formel, markt=(0.4, 0.3, 0.3)):
    return {"spieltag": tag, "ergebnis": erg, "formel": list(formel), "markt": list(markt)}


class Waechter(unittest.TestCase):
    def test_ruhig_bei_wenigen_spielen(self):
        z = [zeile(1, "gast", (0.9, 0.05, 0.05)) for _ in range(9)]
        _, _, meldungen = waechter.pruefen(z)
        self.assertFalse([m for m in meldungen if m[0] == "warnung" and "Saison" in m[1]])

    def test_warnung_bei_rueckstand_zum_markt(self):
        z = [zeile(t, "gast", (0.6, 0.2, 0.2), (0.2, 0.2, 0.6)) for t in range(1, 5) for _ in range(9)]
        _, _, meldungen = waechter.pruefen(z)
        self.assertTrue(any(a == "warnung" and "Markt" in txt for a, txt in meldungen))

    def test_warnung_bei_kalibrierung(self):
        # Formel gibt 70 % Heimsieg, es gewinnt nie das Heimteam
        z = [zeile(1 + i // 9, "gast", (0.7, 0.15, 0.15), (0.3, 0.3, 0.4)) for i in range(20)]
        _, _, meldungen = waechter.pruefen(z)
        self.assertTrue(any("Kalibrierung 60–80" in txt for _, txt in meldungen))

    def test_fehlende_prognose(self):
        z = [{"spieltag": 1, "ergebnis": "heim", "formel": None, "markt": [0.5, 0.3, 0.2]}]
        _, _, meldungen = waechter.pruefen(z)
        self.assertTrue(any("ohne eingefrorene Formel-Prognose" in txt for _, txt in meldungen))

    def test_alles_im_rahmen(self):
        z = [zeile(t, e, (0.45, 0.28, 0.27), (0.45, 0.28, 0.27)) for t in range(1, 4)
             for e in ("heim", "heim", "heim", "heim", "remis", "remis", "gast", "gast", "gast")]
        _, _, meldungen = waechter.pruefen(z)
        self.assertEqual(meldungen, [])


if __name__ == "__main__":
    unittest.main()
