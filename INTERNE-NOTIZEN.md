# Interne Arbeitsnotizen

Arbeitsnotizen, die nicht ins öffentliche Modell-Logbuch gehören (Vorlagen, Technik, Aufgaben-Bezüge).

**Schreibregeln für `MODELL-LOGBUCH.md`** (erscheint öffentlich auf spieltagsformel.de/modell/logbuch): für Leserinnen und Leser verständlich, Absender „wir“, keine Aufgaben-Kürzel (SF-…), keine Dateipfade, Uhrzeiten in deutscher Zeit, Fachbegriffe beim ersten Auftreten kurz erklären. Technische Details hierher.

## 2026-11-04 · Aus der Prüfung des ersten Nachberichts (Spieltag 8)

Geprüft: Zahlen in `entwuerfe/nachbericht-2026-27-08.md` stimmen mit Datenpaket und OpenLigaDB überein (Treffer Formel 3/9, Markt 4/9, Tabellen-Regel 4/9; RPS 0,224 / 0,234). Datenpaket 08 zuletzt geändert 1.11., 13:32 UTC, erstes Sonntagsspiel 14:30 UTC.

Verbesserungen an der Nachbericht-Vorlage (SF-50/SF-53), inzwischen umgesetzt:
1. Bei kleinem RPS-Abstand (< 0,02) „knapp“ / „praktisch Unentschieden“ statt „Näher dran war …“.
2. Tipps mit < 3 Prozentpunkten Vorsprung als „knapp“ markieren.
3. Satz zur Stichprobe („ein Spieltag ist Rauschen, die Bilanz zählt“).
4. Offen/kosmetisch: Feld `eingefroren` fehlt bei Spielen, nach deren Anpfiff das Paket nicht neu gebaut wurde. Nachweis über Commit-Zeitpunkt reicht.

## 2026-11-24 · Dixon-Coles gegen Elo (SF-15), Modell-Wächter (SF-56)

Quelle der Zahlen: `data/waechter/2026-27.json`, Bericht `entwuerfe/waechter-2026-27.md`. Mittlere RPS-Differenz Elo − DC −0,008, Standardfehler 0,007 (gepaarte Differenzen über 27 Spiele). Nächste Prüfung: Hinrunden-Bilanz (SF-27, KW 51).
