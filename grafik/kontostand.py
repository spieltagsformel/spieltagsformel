"""Grafik „Kontostand“ des 100-€-Experiments (rechnerisch, kein echtes Geld)."""
from .stil import FARBE, RAND, Leinwand, komma

STRATEGIEN = [
    ("A", "Favoritenfan", "akzent", "-", False),
    ("B", "Der Vorsichtige", "tinte", "--", False),
    ("C", "Value-Jäger", "gast", "-", True),
]
HINWEIS = "Rechnerisches Experiment ohne echtes Geld · 18+ · Glücksspiel kann süchtig machen · Hilfe: check-dein-spiel.de"


def euro(x):
    return f"{komma(x, 2)} €"


def zeichne(verlauf, kopf, quelle, format_="4x5", pfad="grafik/ausgabe/kontostand.png", beispiel=False):
    """verlauf: Liste von {"spieltag": n, "A": €, "B": €, "C": €}, beginnend mit Spieltag 0 = 100 €."""
    lw = Leinwand(format_)
    y = lw.kopf(kopf)
    letzter = verlauf[-1]
    reihenfolge = sorted("ABC", key=lambda k: -letzter[k])
    bester = next(s for s in STRATEGIEN if s[0] == reihenfolge[0])
    n = letzter["spieltag"]
    titel = f"{bester[1]} führt: {euro(letzter[bester[0]])} nach {n} Spieltagen"
    if beispiel:
        titel = "BEISPIELDATEN – " + titel
    y = lw.titel(titel, y + 28)
    y += 62
    y = lw.absatz("Kontostand der drei Strategien, Start mit 100 €.", y)
    y_ende = lw.fuss(f"{quelle} · {HINWEIS}")

    # Diagrammfläche
    x0, x1 = RAND + 70, lw.b - RAND - 230
    y_oben, y_unten = y + 70, y_ende - 70
    werte = [v[k] for v in verlauf for k in "ABC"] + [100]
    lo, hi = min(werte), max(werte)
    schritt = 10 if hi - lo <= 60 else 20
    lo = (int(lo // schritt)) * schritt
    hi = (int(hi // schritt) + 1) * schritt
    def py(v):
        return y_unten - (v - lo) / (hi - lo) * (y_unten - y_oben)
    def px(t):
        return x0 + t / max(n, 1) * (x1 - x0)
    v = lo
    while v <= hi + 1e-9:
        lw.linie(x0, py(v), x1, py(v), "linie", 1.5)
        lw.text(x0 - 14, py(v), f"{int(v)} €" if v == hi else f"{int(v)}", "mono", "notiz", "leise", ha="right", va="center_baseline")
        v += schritt
    lw.linie(x0, py(100), x1, py(100), "leise", 1.5, ":")
    for t in sorted({0, n} | {x for x in range(0, n + 1, 4)}):
        lw.text(px(t), y_unten + 34, f"Sp. {t}", "mono", "notiz", "leise", ha="center")

    ziel_y = []
    for k, name, farbe, art, punkte in STRATEGIEN:
        xs = [px(v["spieltag"]) for v in verlauf]
        ys = [py(v[k]) for v in verlauf]
        lw.ax.plot(xs, ys, color=FARBE[farbe], linewidth=4 * 0.72, linestyle=art, solid_capstyle="round", zorder=3)
        if punkte:
            lw.ax.scatter(xs, ys, s=(9 * 0.72) ** 2, color=FARBE[farbe], zorder=4, linewidths=0)
        ziel_y.append([ys[-1], k, name, farbe])
    # Namensschilder am Linienende, ohne Überlappung (Merkmal 6)
    ziel_y.sort()
    for i in range(1, len(ziel_y)):
        if ziel_y[i][0] - ziel_y[i - 1][0] < 58:
            ziel_y[i][0] = ziel_y[i - 1][0] + 58
    for yy, k, name, farbe in ziel_y:
        f = "koralle_text" if farbe == "gast" else farbe
        lw.text(x1 + 18, yy - 4, f"{k} · {name}", "fett", "notiz", f)
        lw.text(x1 + 18, yy + 22, euro(letzter[k]), "mono_fett", "notiz", "tinte")
    return lw.speichern(pfad)
