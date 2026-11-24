# Vergleichsmaßstäbe – eingefrorene Regeln

**Version 1.0 · eingefroren am 24.11.2026** (maßgeblich ist der Zeitstempel des Commits, mit dem diese Datei in `main` kam).

Die Formel muss sich an drei Maßstäben messen lassen: der **Tabellenplatz-Regel**, dem **Community-Tipp** und dem **Markt**. Damit der Vergleich ehrlich bleibt, stehen die Regeln vorher fest und werden während einer Saison **nicht** verändert – auch nicht, wenn die Formel dadurch besser aussähe.

## 1. Tabellenplatz-Regel

- **Tipp:** Der besser platzierte Verein gewinnt. Liegen beide nur **einen Platz** (oder weniger) auseinander, lautet der Tipp **Remis**.
- **Grundlage:** die Tabelle **vor** dem Spieltag, berechnet aus den eigenen Ergebnisdaten (OpenLigaDB). Reihenfolge: Punkte, dann Tordifferenz, dann erzielte Tore, dann alphabetisch.
- **Spieltag 1:** Abschlusstabelle der Vorsaison. Aufsteiger stehen in alphabetischer Reihenfolge auf den letzten Plätzen.
- **Code:** `pipeline/tabelle.py` → `tabellenplatz_regel()`; Ergebnis im Datenpaket unter `vergleich.tabellenplatz`.

## 2. Community-Tipp

- **Abstimmung:** je Spiel eine Umfrage „Wer gewinnt?“ mit drei Antworten **Heim / Remis / Gast** – alle Spiele des Spieltags, ohne Geld- oder Wettbezug.
- **Kanäle:** Instagram-Story und X-Umfrage (sobald die Profile stehen). Die Stimmen aller Kanäle werden **addiert**.
- **Zeitfenster:** öffnet mit dem Vorbericht am Donnerstag, schließt **vor dem ersten Anpfiff** des Spieltags. Stimmen nach dem ersten Anpfiff zählen nicht (Story-Umfragen laufen 24 Stunden, X-Umfragen werden auf 24 Stunden gestellt).
- **Tipp:** die Antwort mit den meisten Stimmen.
  - Gleichstand zwischen Heim und Gast → **Remis**.
  - Gleichstand, an dem Remis beteiligt ist → **Remis**.
- **Mindestbeteiligung:** Ein Spiel mit **weniger als 10 Stimmen** (alle Kanäle zusammen) wird für die Community nicht gewertet und erscheint als „keine Wertung“.
- **Erfassung:** Screenshot jeder Umfrage mit Zeitstempel vor dem ersten Anpfiff; die Summen je Spiel kommen nach `data/manuell/community/<saison>/<spieltag>.csv` (Spalten: `id, heim_stimmen, remis_stimmen, gast_stimmen, kanaele`). **Nur Summen, keine Namen oder Konten.**
- **Start:** Test ab KW 50 (SF-46), gewertet ab dem ersten Spieltag nach der Winterpause.

## 3. Markt

- Durchschnitt der Buchmacher-Quoten kurz vor Anpfiff (The Odds API), **ohne Marge** in Wahrscheinlichkeiten umgerechnet. Tipp = wahrscheinlichster Ausgang.
- Buchmacher werden nie einzeln genannt.

## 4. Messgrößen

| Maßstab | Trefferquote | RPS / Brier |
|---|---|---|
| Formel | ja | ja |
| Markt | ja | ja |
| Tabellenplatz-Regel | ja | – (gibt nur einen Tipp, keine Wahrscheinlichkeiten) |
| Community | ja | – |

Gewertet wird immer gegen das Endergebnis nach 90 Minuten (plus Nachspielzeit). Fällt ein Spiel aus oder wird verlegt, wird es mit den **vor dem ursprünglichen Termin eingefrorenen** Tipps abgerechnet, sobald es gespielt ist.

## 5. Vergleichskonten im 100-€-Experiment (rein rechnerisch, kein echtes Geld)

- Zwei Referenzkonten laufen neben den Strategien A–C der Formel mit: **„Tabellen-Regel“** und **„Community“**.
- **Start:** je 100 € mit dem ersten Spieltag nach der Winterpause.
- **Einsatz:** fest **10 €** je gewertetem Spiel auf den Tipp des jeweiligen Maßstabs – auch auf Remis.
- **Quote:** dieselbe durchschnittliche Marktquote kurz vor Anpfiff wie bei den Strategien der Formel (margenbereinigt wird nur für die Wahrscheinlichkeiten, abgerechnet wird mit der Durchschnittsquote).
- **Keine Wertung → kein Einsatz.** Fällt der Kontostand unter 10 €, ist das Konto **pleite**: keine weiteren Einsätze, der Spieltag wird als „Pleite-Spieltag“ festgehalten.
- Kennzahlen wie bei der Formel: Kontostand, ROI, größter Rückgang (Max Drawdown), ggf. Pleite-Spieltag.

*Rechnerisches Experiment ohne echtes Geld · keine Wettempfehlung · 18+ · Glücksspiel kann süchtig machen · Hilfe: check-dein-spiel.de*

## 6. Änderungen

Diese Regeln gelten bis Saisonende 2026/27 unverändert. Änderungen sind nur zur **nächsten Saison** möglich, werden **vorher** angekündigt, bekommen eine neue Versionsnummer und einen Eintrag im `MODELL-LOGBUCH.md`. Bereits abgerechnete Spieltage werden nie neu berechnet.
