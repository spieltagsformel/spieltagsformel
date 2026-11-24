# Modell-Logbuch

Hier steht jede Beobachtung und jede Änderung an der Formel – mit Datum, Grund und Wirkung.
Regel: Nach einem einzelnen Spieltag wird nichts am Modell geändert. Erst mehrere Spieltage zeigen, ob etwas Rauschen oder Signal ist.

## 2026-11-24 · Nach Spieltag 10 – Dixon-Coles v0.2 gegen die Formel (SF-15)

**Frage:** Soll Dixon-Coles v0.2 die Formel (Elo v0.1) ablösen?

**Daten:** 27 Spiele aus Spieltag 8–10, jeweils mit den vor Anpfiff eingefrorenen Wahrscheinlichkeiten beider Modelle und des Markts (`data/waechter/2026-27.json`).

| Modell | RPS | Brier | Treffer | Ø Remis |
|---|---|---|---|---|
| Formel (Elo v0.1) | 0,170 | 0,518 | 18/27 | 26 % |
| Markt | 0,174 | 0,527 | 18/27 | 22 % |
| Dixon-Coles v0.2 | 0,178 | 0,531 | 17/27 | 23 % |

Tatsächlich 6 Remis in 27 Spielen (22 %). RPS je Spieltag (Elo / DC / Markt): 8: 0,224 / 0,225 / 0,234 · 9: 0,111 / 0,119 / 0,110 · 10: 0,174 / 0,190 / 0,178.

**Einordnung:** Elo ist an allen drei Spieltagen vor Dixon-Coles, im Einzelspiel aber nur in 16 von 27 Fällen besser. Der mittlere Abstand (0,008 RPS) ist etwa so groß wie seine Unsicherheit – mit 27 Spielen ist das kein Beleg, nur eine Tendenz.

**Entscheidung:** Die Formel bleibt Elo v0.1. Dixon-Coles läuft als Vergleichsmodell weiter und liefert die erwarteten Tore. Neue Prüfung mit der Hinrunden-Bilanz (SF-27, KW 51). Ablösen würde Dixon-Coles die Formel erst, wenn es über mindestens 90 Spiele beim RPS vorn liegt.

**Neu:** Der Modell-Wächter (SF-56) rechnet diese Bilanz und die Kalibrierung ab jetzt nach jedem Datenabruf (`entwuerfe/waechter-2026-27.md`) und meldet Schieflagen. Stand heute: 🟢, keine Meldung. Auffällig, aber noch ohne Aussagekraft: Ausgängen mit 40–60 % gab die Formel im Schnitt 51 %, eingetreten sind 62 % (16 Werte).

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
