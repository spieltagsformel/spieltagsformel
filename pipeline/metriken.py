"""Bewertung von Wahrscheinlichkeitsprognosen (Reihenfolge: heim, remis, gast)."""
import math

INDEX = {"heim": 0, "remis": 1, "gast": 2}


def _eins(ergebnis):
    v = [0.0, 0.0, 0.0]
    v[INDEX[ergebnis]] = 1.0
    return v


def rps(p, ergebnis):
    """Ranked Probability Score, 0 = perfekt (kleiner ist besser)."""
    o = _eins(ergebnis)
    cp = co = 0.0
    summe = 0.0
    for k in range(2):
        cp += p[k]
        co += o[k]
        summe += (cp - co) ** 2
    return summe / 2.0


def brier(p, ergebnis):
    o = _eins(ergebnis)
    return sum((p[i] - o[i]) ** 2 for i in range(3))


def logloss(p, ergebnis):
    return -math.log(max(p[INDEX[ergebnis]], 1e-12))


def treffer(p, ergebnis):
    return max(range(3), key=lambda i: p[i]) == INDEX[ergebnis]


def zusammenfassung(protokoll, schluessel="p"):
    n = len(protokoll)
    if n == 0:
        return {"n": 0}
    return {
        "n": n,
        "rps": sum(rps(x[schluessel], x["ergebnis"]) for x in protokoll) / n,
        "brier": sum(brier(x[schluessel], x["ergebnis"]) for x in protokoll) / n,
        "logloss": sum(logloss(x[schluessel], x["ergebnis"]) for x in protokoll) / n,
        "trefferquote": sum(treffer(x[schluessel], x["ergebnis"]) for x in protokoll) / n,
    }


def haeufigkeiten(protokoll):
    """Anteile Heimsieg / Remis / Auswärtssieg (Referenz ohne jedes Wissen über die Teams)."""
    n = len(protokoll)
    return tuple(sum(1 for x in protokoll if x["ergebnis"] == k) / n for k in ("heim", "remis", "gast"))
