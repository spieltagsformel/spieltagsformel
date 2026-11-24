# Qualitätsprüfung (SF-52)

Bei jedem Pull Request, der `entwuerfe/` oder `website/src/` ändert, läuft automatisch der Check **„Qualitätsprüfung“**. Er prüft nur die geänderten Dateien.

- **Grüner Haken:** keine Verstöße – Inhalt prüfen und mergen wie gewohnt.
- **Rotes Kreuz:** mindestens ein Fehler. Im Pull Request unter „Checks“ → „Qualitätsprüfung“ steht eine Tabelle mit Datei, Zeile und Problem; die Stellen sind zusätzlich direkt im Tab „Files changed“ markiert. Erst beheben, dann mergen.

Lokal prüfen: `python -m pipeline.qualitaet --alle` (oder einzelne Dateien angeben).

## Fehler (Check schlägt fehl)

| Regel | Gilt für | Warum |
|---|---|---|
| Kein Buchmacher- oder Glücksspielname (z. B. Tipico, bet365, bwin, Oddset …) | alle geprüften Dateien | Leitplanke: keine Wettwerbung, auch nicht versehentlich |
| Kein Link auf Wett-/Casino-Seiten | alle | dito |
| Keine Wett-Sprache und Versprechen: „sicherer Tipp“, „Tipp des Tages“, „todsicher“, „Gewinn garantiert“, „risikolos“, „Wettbonus“, „Bonus-Code“, „jetzt wetten“, „Wett-Tipps“, „Value-Bets“ … | alle | Tonalität: nie reißerisch, nie „sicher“. **Erlaubt**, wenn im selben Satz oder in den zwei Zeilen davor verneint wird („keine Wett-Tipps“, Überschrift „Was nicht drinsteht“) |
| Pflichthinweis „18+“ **und** Hilfe (check-dein-spiel.de oder „Glücksspiel kann süchtig machen“) | Vor-/Nachberichte immer; Social-Pakete, wenn sie das 100-€-Experiment oder den Kontostand erwähnen; Website-Seite zum 100-€-Experiment | Jugendschutz, Glücksspiel-Bezug der Simulation |
| Jede Prozentzahl („53 %“) und jeder Kennwert („0,174“) steht in den Daten | Vor-/Nachberichte und Social-Pakete in `entwuerfe/redaktion/` | Keine erfundenen Zahlen. Quelle: Datenpaket `data/spieltage/…`, Nachbericht-Daten `data/nachberichte/…` (auch frühere Stände, weil sich Quoten bis zum Anpfiff ändern) und der automatische Roh-Entwurf |
| Kein offener Platzhalter `[PRÜFEN …]` / `[AUS DER REDAKTION …]` | `website/src/` (also alles, was live geht) | Platzhalter gehören nie auf die Website |

## Hinweise (Check bleibt grün)

- Offene `[PRÜFEN]`/`[AUS DER REDAKTION]`-Stellen in Redaktions-Entwürfen werden gezählt – die füllst du vor dem Veröffentlichen.

## Grenzen

Die Prüfung ersetzt nicht das Gegenlesen: Sie erkennt keine falsche Einordnung, keine kopierten Texte und keine sachlich falschen Aussagen ohne Zahl. Abgeleitete Zahlen, die nirgends gespeichert sind (z. B. eine selbst gerechnete Summe), meldet sie als Fehler – dann entweder die Zahl in die Pipeline aufnehmen (wie den Brier-Score seit 24.11.2026) oder umformulieren.

Neue Buchmachernamen oder Formulierungen: Listen `BUCHMACHER` und `VERSPRECHEN` in `pipeline/qualitaet.py` ergänzen, Test in `tests/test_qualitaet.py` dazuschreiben.
