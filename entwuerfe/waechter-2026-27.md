# Modell-Wächter 2026/27

**Stand:** 27 beendete Spiele aus Spieltag 8, 9, 10 · **Ampel:** 🟢 Alles im Rahmen

Der Wächter ändert nichts am Modell. Er meldet nur – entschieden wird im Modell-Logbuch, frühestens nach mehreren Spieltagen.

## Bilanz

| Modell | Spiele | RPS | Brier | Treffer | Ø Remis |
|---|---|---|---|---|---|
| Formel | 27 | 0,170 | 0,518 | 18 | 26 % |
| Markt | 27 | 0,174 | 0,527 | 18 | 22 % |
| Dixon-Coles v0.2 | 27 | 0,178 | 0,531 | 17 | 23 % |

Tatsächliche Remis: 6 von 27. RPS und Brier: kleiner ist besser.

## Kalibrierung der Formel

Wie oft trat ein Ausgang ein, dem die Formel eine bestimmte Wahrscheinlichkeit gab? Gut kalibriert heißt: beide Spalten ähnlich.

| Stufe | Anzahl | vorhergesagt | eingetreten |
|---|---|---|---|
| 0–20 % | 14 | 15 % | 7 % |
| 20–40 % | 45 | 28 % | 24 % |
| 40–60 % | 16 | 51 % | 62 % |
| 60–80 % | 5 | 66 % | 100 % |
| 80–100 % | 1 | 82 % | 0 % |

*Schwellen und Regeln: `pipeline/waechter.py` (SCHWELLEN). Wenige Spiele = großer Zufall; unter 15 Werten je Stufe wird nicht gewarnt.*
