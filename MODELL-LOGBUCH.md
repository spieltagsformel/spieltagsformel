# Modell-Logbuch

Hier steht jede Beobachtung und jede Änderung an der Formel – mit Datum, Grund und Wirkung.
Regel: Nach einem einzelnen Spieltag wird nichts am Modell geändert. Erst mehrere Spieltage zeigen, ob etwas Rauschen oder Signal ist.

## 2026-11-04 · Spieltag 8 (2026/27) – erster echter Nachbericht

**Version:** Formel = Elo v0.1, Vergleichsmodell Dixon-Coles v0.2, Markt = margenbereinigte Durchschnittsquoten (The Odds API).

**Geprüft:** Alle Zahlen im Entwurf `entwuerfe/nachbericht-2026-27-08.md` stimmen mit Datenpaket und Ergebnissen (OpenLigaDB) überein: Treffer Formel 3/9, Markt 4/9, Tabellen-Regel 4/9; RPS Formel 0,224, Markt 0,234 (nachgerechnet); größte Fehlprognose Leverkusen – Stuttgart (22 % für den Auswärtssieg).

**Eingefroren:** Letzte Änderung am Datenpaket 08 am 1.11. um 13:32 UTC, vor dem ersten Sonntagsspiel (14:30 UTC). Alle Prognosen lagen also vor Anpfiff fest.

**Beobachtungen (kein Handlungsbedarf, nur notieren):**
- 3 Remis in 9 Spielen (33 %). Die Formel gab im Schnitt 27 % Remis, der Markt 23 %. Der früher vermutete „zu hohe Remis-Parameter“ hat diesmal eher geholfen – ein Spieltag ist aber Rauschen.
- Die Formel tippt praktisch nie Remis, weil Remis selten die höchste Einzelwahrscheinlichkeit ist. Die Trefferquote bestraft das; der RPS nicht. Deshalb im Nachbericht den RPS als Hauptmaß erklären.
- Bayern – Dortmund (2:2): Formel 58 % Heimsieg, Markt 72 %. Die vorsichtigere Formel lag beim RPS vorn.
- Union – Köln (1:1): größter Unterschied zum Markt (Formel Heimsieg 45 %, Markt Auswärtssieg 38 %).
- Bremen – Hoffenheim: Formel-Tipp hing an 1 Prozentpunkt (35 % zu 36 %). Solche Münzwürfe sollten im Text als „knapp“ erkennbar sein.

**Verbesserungen an der Nachbericht-Vorlage (für SF-50/SF-53):**
1. Bei kleinem RPS-Abstand (< 0,02) „knapp“ schreiben statt „Näher dran war …“.
2. In der Tabelle Tipps mit < 3 Prozentpunkten Vorsprung als „knapp“ markieren.
3. Satz zur Stichprobe ergänzen („ein Spieltag ist Rauschen, die Bilanz zählt“).
4. Feld `eingefroren` fehlt bei Spielen, nach deren Anpfiff das Paket nicht neu gebaut wurde (hier die beiden Sonntagsspiele). Der Nachweis über den Commit-Zeitpunkt reicht, kosmetisch aber nach Spieltagsende für alle Spiele setzen.
