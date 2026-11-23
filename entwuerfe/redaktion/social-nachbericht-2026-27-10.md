# Social-Paket · Nachbericht 10. Spieltag 2026/27

Grundlage: `entwuerfe/redaktion/nachbericht-2026-27-10.md`, `data/nachberichte/2026-27/10.json`, `data/spieltage/2026-27/10.json`, `data/clean/spiele_2026.csv`. Absender „wir“ / „die Formel“. Veröffentlichung nur durch den Gründer. Zeichenzahlen der X-Posts sind geprüft (inkl. Link).

---

## 1 · Bilanz des Spieltags

Kanal: X | Format: Text + Grafik | Veröffentlichung: Montag, 23.11., 12:30 Uhr
Hook: 10. Spieltag abgerechnet: 7 von 9.
Text:
> 10. Spieltag abgerechnet: Die Formel lag bei 7 von 9 Spielen richtig, der Markt bei 6, die Tabellen-Regel bei 5.
>
> Beim RPS (kleiner ist besser): Formel 0,174, Markt 0,178 – praktisch Unentschieden.
>
> Alle Spiele: spieltagsformel.de

Grafik-Briefing: Vorhanden ist nur die Vorher-Grafik `grafik/ausgabe/spieltag-10-4x5.png` (Wahrscheinlichkeiten vor dem Spieltag). Für den Nachbericht in Canva „Spieltagsformel“ eine 4:5-Abrechnungsgrafik bauen: 9 Zeilen „Spiel · Ergebnis · Formel ✓/✗ · Markt ✓/✗“, oben groß „7 von 9“, darunter klein „Markt 6 · Tabellen-Regel 5“. Farben: Treffer Elektroblau #2F5BFF, daneben Koralle #FF5A5F (✓/✗ zusätzlich als Symbol, nicht nur über Farbe). Quellenzeile: „OpenLigaDB (ODbL), eigene Berechnung · Wahrscheinlichkeiten, keine Wettempfehlung“.
CTA: Alle Spiele: spieltagsformel.de
Kennzeichnung nötig: nein

---

## 2 · Die Formel lag daneben

Kanal: X | Format: Text + Grafik | Veröffentlichung: Montag, 23.11., 18:30 Uhr
Hook: Die Formel lag daneben: 82 % für Bayern. Ergebnis: 1:1.
Text:
> Die Formel lag daneben: 82 % für Bayern gegen Köln. Ergebnis: 1:1.
>
> Fürs Remis hatten wir 14 % berechnet, der Markt nur 7 %. Ein 14-%-Ereignis passiert etwa jedes siebte Mal. Diesmal eben am Freitag.
>
> Die ganze Abrechnung: spieltagsformel.de

Grafik-Briefing: Ausschnitt der Bayern-Köln-Zeile aus `grafik/ausgabe/spieltag-10-4x5.png` (82 % · 14 % · 4 %) mit Stempel „1:1“ in Koralle dunkel #C8323A. Hinweis: In der vorhandenen Grafik fehlt bei Bayern – Köln die Zahl im schmalen Auswärts-Balken (nur „%“ sichtbar) – in Canva „4 %“ ergänzen oder neu setzen. Kopfzeile „DIE FORMEL LAG DANEBEN“.
CTA: Die ganze Abrechnung: spieltagsformel.de
Kennzeichnung nötig: nein

---

## 3 · Eine überraschende Zahl

Kanal: X | Format: Text | Veröffentlichung: Dienstag, 24.11., 12:30 Uhr
Hook: 15 von 23 Toren fielen nach der Pause.
Text:
> 15 von 23 Toren am 10. Spieltag fielen nach der Pause.
>
> Bremen – HSV: zur Halbzeit 0:0, am Ende 4:0.
> Union – Leipzig: zur Halbzeit 1:1, am Ende 1:5.
>
> Mehr Zahlen zum Spieltag: spieltagsformel.de

Grafik-Briefing: optional, Canva „Spieltagsformel“: zwei Balken „1. Halbzeit 8 Tore / 2. Halbzeit 15 Tore“ in Tinte #111111 und Elektroblau #2F5BFF, Zahlen in JetBrains Mono. Quelle: OpenLigaDB (ODbL).
CTA: Mehr Zahlen zum Spieltag: spieltagsformel.de
Kennzeichnung nötig: nein

---

## 4 · Instagram – Bilanz

Kanal: Instagram | Format: Feed-Grafik 4:5 (Karussell, 2 Folien) | Veröffentlichung: Montag, 23.11., 18:00 Uhr
Hook: 7 von 9 richtig – und ausgerechnet die 82 % für Bayern halten nicht.
Text:
> 7 von 9 richtig – und ausgerechnet die 82 % für Bayern halten nicht.
>
> Die Abrechnung des 10. Spieltags:
> Formel 7 von 9 · Markt 6 von 9 · Tabellen-Regel 5 von 9
>
> Den einen Treffer Vorsprung holt die Formel bei Augsburg – Mainz (3:1): 39 % für Augsburg, der Markt sah Mainz vorn. Bei 39 % ist das eher Münzwurf als Geniestreich.
>
> Daneben: Bayern – Köln 1:1 (Remis laut Formel 14 %) und Schalke – Stuttgart 0:0.
>
> Nach 27 Spielen steht es Formel 18, Markt 18. Spannend bleibt’s.
>
> Die ganze Abrechnung: spieltagsformel.de (Link in der Bio)
>
> #Bundesliga #BundesligaInZahlen #Fußballstatistik #Datenanalyse #Spieltagsformel

Grafik-Briefing: Folie 1 = Abrechnungsgrafik aus Post 1 (Canva-Vorlage 4:5). Folie 2 = Bilanzkarte „Seit Start: 27 Spiele · Formel 18 · Markt 18 · Tabellen-Regel 16“ in den Markenfarben.
CTA: Die ganze Abrechnung: spieltagsformel.de (Link in der Bio)
Kennzeichnung nötig: nein

---

## Kandidaten „Zahl der Woche“ (Newsletter, Mittwoch)

1. **15 von 23** – so viele Tore des 10. Spieltags fielen nach der Pause. Quelle: `data/clean/spiele_2026.csv` (Spalten `tore_*` und `ht_*`, Spieltag 10).
2. **0 von 27** – in keinem der bisher 27 abgerechneten Spiele hat die Formel ein Remis als wahrscheinlichsten Ausgang gesehen; tatsächlich endeten 6 unentschieden. Quelle: `data/nachberichte/2026-27/10.json` (Block `bilanz_seit_start`: Zahl der Remis-Vorhersagen und `ergebnisse.remis`).
3. **2,56** – Tore pro Spiel am 10. Spieltag (23 in 9 Spielen), deutlich unter dem Saisonschnitt von 3,39 nach 10 Spieltagen (90 Spiele). Quelle: `data/clean/spiele_2026.csv`, eigene Berechnung.

Empfehlung: Kandidat 2 – er passt zur Rubrik „Modell-Logbuch“ und erklärt, warum Remis die Schwachstelle von Elo-Modellen sind.
