# Modell-Logbuch

Hier steht jede Beobachtung und jede Änderung an der Formel – mit Datum, Grund und Wirkung.
Regel: Nach einem einzelnen Spieltag wird nichts am Modell geändert. Erst mehrere Spieltage zeigen, ob etwas Zufall ist oder ein Muster.

## 24. November 2026 · Bleibt die Formel, oder übernimmt das Vergleichsmodell?

Neben der Formel (ein sogenanntes Elo-Modell) rechnet von Anfang an ein zweites Modell mit: **Dixon-Coles**. Es schätzt, wie viele Tore beide Teams schießen, und leitet daraus die Wahrscheinlichkeiten ab. Nach drei Spieltagen mit echten Prognosen haben wir beide verglichen – und den Markt, also die Einschätzung der Buchmacher ohne deren Marge, gleich mit.

**Gemessen** haben wir mit dem **RPS** (Ranked Probability Score). Er bewertet nicht nur, ob der Favorit gewonnen hat, sondern auch, wie überzeugt ein Modell war. Kleiner ist besser. Der **Brier-Score** misst etwas Ähnliches auf einer anderen Skala.

| Modell | RPS | Brier | richtig getippt | Remis im Schnitt erwartet |
|---|---|---|---|---|
| Formel | 0,170 | 0,518 | 18 von 27 | 26 % |
| Markt | 0,174 | 0,527 | 18 von 27 | 22 % |
| Dixon-Coles | 0,178 | 0,531 | 17 von 27 | 23 % |

Tatsächlich endeten 6 der 27 Spiele unentschieden (22 %). Die Formel lag an allen drei Spieltagen vor Dixon-Coles:

| Spieltag | Formel | Dixon-Coles | Markt |
|---|---|---|---|
| 8 | 0,224 | 0,225 | 0,234 |
| 9 | 0,111 | 0,119 | 0,110 |
| 10 | 0,174 | 0,190 | 0,178 |

**Was das heißt:** Ein klarer Sieg ist das nicht. Spiel für Spiel war die Formel nur in 16 von 27 Fällen besser, und der Abstand ist so klein, dass er auch Zufall sein kann. 27 Spiele sind schlicht zu wenig für ein Urteil.

**Unsere Entscheidung:** Die Formel bleibt unser Hauptmodell. Dixon-Coles läuft weiter mit und liefert die erwarteten Tore, die du in jedem Vorbericht siehst. Mit der Bilanz der Hinrunde schauen wir erneut hin. Ablösen würde Dixon-Coles die Formel erst, wenn es über mindestens 90 Spiele klar vorn liegt.

**Neu ab heute:** Ein automatischer Wächter rechnet diese Bilanz nach jedem Spieltag neu und schlägt Alarm, wenn die Formel dauerhaft hinter dem Markt zurückfällt oder ihre Wahrscheinlichkeiten nicht zur Wirklichkeit passen. Die aktuelle Bilanz steht oben auf dieser Seite. Stand heute: alles im grünen Bereich.

Eine Kleinigkeit behalten wir im Blick: Wenn die Formel einem Ausgang ungefähr 50 % gab, trat er bisher in 62 % der Fälle ein – sie war dort also eher zu vorsichtig. Bei 16 solchen Fällen ist das aber noch kein Muster.

## 4. November 2026 · Spieltag 8 – der erste echte Nachbericht

Zum ersten Mal haben wir die Formel an einem echten Spieltag abgerechnet: mit Prognosen, die vor dem Anpfiff eingefroren waren. Die letzte Änderung an den Prognosen war am 1. November um 14:32 Uhr, eine knappe Stunde vor dem ersten Sonntagsspiel. Alle Zahlen im Nachbericht haben wir nachgerechnet.

**Ergebnis:** Die Formel lag bei 3 von 9 Spielen richtig, der Markt bei 4, die einfache Tabellen-Regel („der besser Platzierte gewinnt“) ebenfalls bei 4. Beim RPS war die Formel trotzdem knapp besser als der Markt (0,224 gegen 0,234) – sie war bei ihren Fehlern vorsichtiger. Die größte Fehlprognose: Leverkusen – Stuttgart, die Formel gab dem Auswärtssieg nur 22 %.

**Was uns aufgefallen ist:**
- **Viele Remis:** 3 von 9 Spielen (33 %) endeten unentschieden. Die Formel hatte im Schnitt 27 % Remis erwartet, der Markt 23 %. Diesmal half der Formel, dass sie Unentschieden etwas mehr zutraut – ein einzelner Spieltag ist aber Zufall.
- **Die Formel tippt fast nie auf Remis.** Das liegt nicht an einer Abneigung, sondern an der Rechnung: Ein Unentschieden ist selten der einzelne wahrscheinlichste Ausgang. Wer nur „richtig getippt“ zählt, bestraft das. Deshalb ist der RPS unser Hauptmaß.
- **Bayern – Dortmund (2:2):** Die Formel gab den Bayern 58 %, der Markt 72 %. Die vorsichtigere Formel lag hier vorn.
- **Union – Köln (1:1):** Hier waren sich Formel und Markt am wenigsten einig – die Formel sah eher Union vorn (45 %), der Markt eher Köln (38 %).
- **Bremen – Hoffenheim:** Der Tipp der Formel hing an einem einzigen Prozentpunkt (35 % zu 36 %). Solche Münzwürfe kennzeichnen wir seitdem in den Berichten als „knapp“.
