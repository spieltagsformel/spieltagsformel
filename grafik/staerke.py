"""Grafik „Stärke der Teams“: Elo-Werte relativ zum Ligaschnitt (Punkt-Diagramm)."""
import math

from .namen import kurz
from .stil import RAND, Leinwand, stand_text


def chancen_neutral(differenz, nu):
    """Sieg/Remis/Niederlage des stärkeren Teams auf neutralem Platz bei gegebener Elo-Differenz."""
    a = math.sqrt(10 ** (differenz / 400.0))
    summe = a + 1 / a + nu
    return a / summe, nu / summe, (1 / a) / summe


def werte(saisons, params, saison):
    """Elo-Werte aller Teams der Saison nach den bisher beendeten Spielen."""
    from pipeline.elo import EloModell
    m = EloModell(params)
    m.lauf(saisons)
    teams = {}
    for s in saisons[saison]:
        teams[s["heim_id"]] = s["heim"]
        teams[s["gast_id"]] = s["gast"]
    liste = [(name, m.rating_von(t)) for t, name in teams.items()]
    schnitt = sum(r for _, r in liste) / len(liste)
    return sorted(((n, r - schnitt) for n, r in liste), key=lambda x: -x[1]), m.p["nu"]


def zahl(x):
    v = round(x)
    return f"+{v}" if v > 0 else ("±0" if v == 0 else f"−{abs(v)}")


def zeichne(liste, nu, kopf, stand_iso, format_="4x5", pfad="grafik/ausgabe/staerke.png"):
    lw = Leinwand(format_)
    y = lw.kopf(kopf)
    (erster, w1), (zweiter, w2) = liste[0], liste[1]
    titel = f"{kurz(erster)} liegt {round(w1)} Punkte über dem Ligaschnitt"
    y = lw.titel(titel, y + 28)
    y += 62
    s_, r_, n_ = chancen_neutral(100, nu)
    zeile1 = f"{round(w1 - w2)} Punkte vor {kurz(zweiter)}." if w1 - w2 >= 40 else f"Knapp vor {kurz(zweiter)}."
    y = lw.absatz(f"{zeile1} Zur Einordnung: 100 Punkte Vorsprung bedeuten auf neutralem Platz etwa "
                  f"{round(s_ * 100)} % Sieg, {round(r_ * 100)} % Remis, {round(n_ * 100)} % Niederlage.", y)

    y_ende = lw.fuss(f"Quelle: OpenLigaDB (ODbL), eigene Berechnung, Modell elo-0.1 · Stand {stand_text(stand_iso)}")
    y0 = y + 76
    zeile = (y_ende - 16 - y0) / len(liste)
    x_name_ende = RAND + 250
    x_wert = lw.b - RAND
    x_links, x_rechts = x_name_ende + 30, x_wert - 90
    groesster = max(abs(w) for _, w in liste)
    skala = (x_rechts - x_links) / 2 / max(groesster, 1)
    x_mitte = (x_links + x_rechts) / 2
    lw.linie(x_mitte, y0 - 6, x_mitte, y0 + zeile * len(liste), "leise", 1.5)
    lw.text(x_mitte, y0 - 14, "Ligaschnitt", "fett", "notiz", "leise", ha="center")
    for i, (name, w) in enumerate(liste):
        ym = y0 + zeile * (i + 0.5)
        lw.text(RAND, ym, kurz(name), "fett" if i < 3 else "text", "notiz", "tinte", va="center_baseline")
        x = x_mitte + w * skala
        farbe = "akzent" if w >= 0 else "leise"
        lw.linie(x_mitte, ym, x, ym, farbe, 3)
        lw.ax.scatter([x], [ym], s=(14 * 0.72) ** 2, color=lw.ax.lines[-1].get_color(), zorder=4, linewidths=0)
        lw.text(x_wert, ym, zahl(w), "mono_fett" if i < 3 else "mono", "notiz", "tinte", ha="right", va="center_baseline")
    return lw.speichern(pfad)
