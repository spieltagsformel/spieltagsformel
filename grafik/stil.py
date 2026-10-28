"""Gemeinsamer Stil aller Grafiken (Styleguide v1, Farbwelt „Datenblatt“).

Gezeichnet wird in Pixel-Koordinaten (0,0 = oben links), damit Ränder und Raster exakt sind.
Qualitätsmerkmale: siehe grafik/QUALITAET.md.
"""
import os
from datetime import datetime, timezone

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle

ORDNER = os.path.dirname(os.path.abspath(__file__))
SCHRIFTEN = os.path.join(ORDNER, "schriften")

FARBE = {
    "papier": "#FFFFFF", "tinte": "#111111", "leise": "#5A5A5A", "linie": "#E3E3E3",
    "heim": "#2F5BFF", "remis": "#111111", "gast": "#FF5A5F", "markt": "#5A5A5A",
    "akzent": "#2F5BFF", "koralle_text": "#C8323A",
}
RAND = 64

FORMATE = {"4x5": (1080, 1350), "9x16": (1080, 1920)}
# Bereiche, die Instagram in Stories mit Bedienelementen überdeckt
SICHER = {"4x5": (0, 0), "9x16": (220, 240)}


def _schrift(datei):
    pfad = os.path.join(SCHRIFTEN, datei)
    font_manager.fontManager.addfont(pfad)
    return font_manager.FontProperties(fname=pfad)


SCHRIFT = {
    "titel": _schrift("Inter-ExtraBold.ttf"),
    "fett": _schrift("Inter-SemiBold.ttf"),
    "text": _schrift("Inter-Regular.ttf"),
    "mono": _schrift("JetBrainsMono-Regular.ttf"),
    "mono_fett": _schrift("JetBrainsMono-Bold.ttf"),
}

# Drei Größenstufen (px): Titel, Inhalt, Notiz
GROESSE = {"titel": 54, "inhalt": 28, "notiz": 20}


def komma(x, stellen=1):
    return f"{x:.{stellen}f}".replace(".", ",")


def prozent(p):
    return f"{round(p * 100)} %"


class Leinwand:
    """Eine Grafik in Pixeln. Text-Größen in px, y wächst nach unten."""

    def __init__(self, format_="4x5"):
        self.format = format_
        self.b, self.h = FORMATE[format_]
        self.oben, self.unten = SICHER[format_]
        self.fig = plt.figure(figsize=(self.b / 100, self.h / 100), dpi=100)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, self.b)
        self.ax.set_ylim(self.h, 0)
        self.ax.axis("off")
        self.fig.patch.set_facecolor(FARBE["papier"])

    # px -> pt (bei dpi 100 ist 1 px = 0,72 pt)
    @staticmethod
    def _pt(px):
        return px * 0.72

    def text(self, x, y, s, art="text", groesse="inhalt", farbe="tinte", ha="left", va="baseline", **kw):
        px = GROESSE[groesse] if isinstance(groesse, str) else groesse
        return self.ax.text(x, y, s, fontproperties=SCHRIFT[art], fontsize=self._pt(px),
                            color=FARBE.get(farbe, farbe), ha=ha, va=va, **kw)

    def textbreite(self, s, art="text", groesse="inhalt"):
        t = self.text(0, -1000, s, art, groesse)
        r = self.fig.canvas.get_renderer()
        bb = t.get_window_extent(renderer=r)
        t.remove()
        return bb.width

    def umbrechen(self, s, breite, art="titel", groesse="titel"):
        """Bricht Text in Zeilen, die in `breite` px passen."""
        woerter, zeilen, zeile = s.split(), [], ""
        for w in woerter:
            probe = (zeile + " " + w).strip()
            if self.textbreite(probe, art, groesse) <= breite:
                zeile = probe
            else:
                if zeile:
                    zeilen.append(zeile)
                zeile = w
        if zeile:
            zeilen.append(zeile)
        return zeilen

    def absatz(self, s, y, art="text", groesse="inhalt", farbe="leise", max_zeilen=3):
        """Umbrochener Fließtext ab Grundlinie y; gibt die Grundlinie der letzten Zeile zurück."""
        px = GROESSE[groesse] if isinstance(groesse, str) else groesse
        zeilen = self.umbrechen(s, self.b - 2 * RAND, art, groesse)[:max_zeilen]
        for i, z in enumerate(zeilen):
            self.text(RAND, y + i * px * 1.3, z, art, groesse, farbe)
        return y + (len(zeilen) - 1) * px * 1.3

    def flaeche(self, x, y, b, h, farbe):
        self.ax.add_patch(Rectangle((x, y), b, h, facecolor=FARBE.get(farbe, farbe), edgecolor="none", linewidth=0))

    def linie(self, x1, y1, x2, y2, farbe="linie", px=1.5, art="-"):
        self.ax.plot([x1, x2], [y1, y2], color=FARBE.get(farbe, farbe), linewidth=self._pt(px), linestyle=art,
                     solid_capstyle="butt")

    def kopf(self, laufzeile):
        """Signatur: Mono-Laufzeile + Haarlinie (Merkmal 9)."""
        y = self.oben + RAND + 20
        self.text(RAND, y, laufzeile.upper(), "mono", "notiz", "leise")
        self.linie(RAND, y + 20, self.b - RAND, y + 20, "tinte", 1.5)
        return y + 20

    def titel(self, s, y, max_zeilen=2):
        zeilen = self.umbrechen(s, self.b - 2 * RAND)[:max_zeilen]
        for i, z in enumerate(zeilen):
            self.text(RAND, y + GROESSE["titel"] * (0.95 + i * 1.08), z, "titel", "titel")
        return y + GROESSE["titel"] * (0.95 + (len(zeilen) - 1) * 1.08)

    def fuss(self, quelle):
        """Quellenzeile links unten, Logo-Stempel rechts unten (Merkmal 8 und 9)."""
        y_logo = self.h - self.unten - RAND - 64
        self.linie(RAND, y_logo - 24, self.b - RAND, y_logo - 24, "linie", 1.5)
        zeilen = self.umbrechen(quelle, self.b - 2 * RAND - 96, "text", "notiz")[:2]
        for i, z in enumerate(zeilen):
            self.text(RAND, y_logo + 26 + i * 26, z, "text", "notiz", "leise")
        bild = plt.imread(os.path.join(ORDNER, "logo-stempel.png"))
        x = self.b - RAND - 64
        self.ax.imshow(bild, extent=(x, x + 64, y_logo + 64, y_logo), zorder=5, interpolation="antialiased")
        self.ax.set_xlim(0, self.b)
        self.ax.set_ylim(self.h, 0)
        return y_logo - 24

    def speichern(self, pfad):
        os.makedirs(os.path.dirname(pfad) or ".", exist_ok=True)
        self.fig.savefig(pfad, dpi=100, facecolor=self.fig.get_facecolor())
        plt.close(self.fig)
        return pfad


def stand_text(iso):
    try:
        t = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, AttributeError):
        return ""
    # Anzeige in deutscher Zeit (MEZ/MESZ grob über die Systemzeitzone nicht verlässlich): nur Datum
    return t.strftime("%d.%m.%Y")
