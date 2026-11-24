import json
import os
import tempfile
import unittest

from pipeline import qualitaet

FUSS = "*Rein rechnerische Wahrscheinlichkeiten · keine Wettempfehlung · 18+ · Glücksspiel kann süchtig machen · Hilfe: check-dein-spiel.de*"


class Qualitaet(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.w = self.tmp.name
        os.makedirs(os.path.join(self.w, "entwuerfe", "redaktion"))
        os.makedirs(os.path.join(self.w, "website", "src", "pages"))
        os.makedirs(os.path.join(self.w, "data", "spieltage", "2026-27"))
        paket = {"saison": "2026-27", "spieltag": 11, "spiele": [
            {"modell": {"p_heim": 0.5, "p_remis": 0.27, "p_gast": 0.23}, "markt": {"p_heim": 0.55, "p_remis": 0.25, "p_gast": 0.2}}]}
        with open(os.path.join(self.w, "data", "spieltage", "2026-27", "11.json"), "w", encoding="utf-8") as f:
            json.dump(paket, f)

    def tearDown(self):
        self.tmp.cleanup()

    def pruefe(self, rel, text):
        with open(os.path.join(self.w, rel), "w", encoding="utf-8") as f:
            f.write(text)
        return [b for b in qualitaet.pruefe_datei(rel, self.w) if b.fehler]

    def vb(self, text):
        return self.pruefe("entwuerfe/redaktion/vorbericht-2026-27-11.md", text + "\n\n" + FUSS + "\n")

    def test_sauberer_text(self):
        self.assertEqual(self.vb("Die Formel sieht 50 % für den Heimsieg, der Markt 55 %."), [])

    def test_buchmacher(self):
        self.assertTrue(self.vb("Bei Tipico steht das Spiel anders."))

    def test_wett_link(self):
        self.assertTrue(self.vb("Mehr unter https://www.sportwetten-vergleich.example/heute"))

    def test_versprechen(self):
        self.assertTrue(self.vb("Das ist der sichere Tipp des Wochenendes."))
        self.assertTrue(self.vb("Unser Tipp des Tages: Heimsieg."))

    def test_verneinung_erlaubt(self):
        self.assertEqual(self.vb("Hier gibt es keine Wett-Tipps, nur Wahrscheinlichkeiten."), [])
        self.assertEqual(self.pruefe("website/src/pages/newsletter.astro",
                                     "<h2>Was nicht drinsteht</h2>\n<p>Wett-Tipps und Gewinnversprechen.</p>"), [])

    def test_trefferquote_kein_alarm(self):
        self.assertEqual(self.vb("Die Trefferquote der Formel liegt bei 50 %."), [])

    def test_pflichthinweis_fehlt(self):
        self.assertTrue(self.pruefe("entwuerfe/redaktion/vorbericht-2026-27-11.md", "Die Formel sagt 50 %.\n"))

    def test_social_ohne_experiment_braucht_keinen_hinweis(self):
        self.assertEqual(self.pruefe("entwuerfe/redaktion/social-vorbericht-2026-27-11.md", "Die Formel sagt 50 %.\n"), [])

    def test_social_mit_kontostand_braucht_hinweis(self):
        self.assertTrue(self.pruefe("entwuerfe/redaktion/social-nachbericht-2026-27-11.md", "Kontostand: 104 €\n"))

    def test_erfundene_zahl(self):
        fehler = self.vb("Die Formel sieht 61 % für den Heimsieg.")
        self.assertTrue(any("61 %" in b.text for b in fehler))

    def test_platzhalter_auf_website(self):
        self.assertTrue(self.pruefe("website/src/pages/modell.astro", "<p>[AUS DER REDAKTION: Text]</p>"))

    def test_platzhalter_im_entwurf_nur_hinweis(self):
        self.assertEqual(self.vb("[PRÜFEN: Sender]"), [])


if __name__ == "__main__":
    unittest.main()
