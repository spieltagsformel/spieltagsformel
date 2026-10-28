"""Grafik „Die Formel sagt …“: alle Spiele eines Spieltags mit Heim/Remis/Gast-Balken (Social Media)."""
from .namen import anstoss, kurz
from .stil import FARBE, GROESSE, RAND, Leinwand, prozent, stand_text


def aussage(paket):
    """Titel als Aussage mit Zahl (Merkmal 4)."""
    spiele = [s for s in paket["spiele"] if s.get("modell")]
    def staerkster(s):
        m = s["modell"]
        return max(m["p_heim"], m["p_gast"])
    top = max(spiele, key=staerkster)
    m = top["modell"]
    if m["p_heim"] >= m["p_gast"]:
        fav, geg, p = kurz(top["heim"]), kurz(top["gast"]), m["p_heim"]
    else:
        fav, geg, p = kurz(top["gast"]), kurz(top["heim"]), m["p_gast"]
    offen = sum(1 for s in spiele if staerkster(s) < 0.40)
    titel = f"{fav} ist der klarste Favorit: {prozent(p)} gegen {geg}"
    if offen == 0:
        unter = f"In allen {len(spiele)} Spielen hat die Formel einen Favoriten mit mindestens 40 %."
    elif offen == 1:
        unter = f"Nur ein Spiel ist offen: Dort kommt kein Team auf 40 %."
    else:
        unter = f"{offen} von {len(spiele)} Spielen sind offen: Dort kommt kein Team auf 40 %."
    return titel, unter


def zeichne(paket, format_="4x5", pfad=None):
    lw = Leinwand(format_)
    saison = paket["saison"].replace("-", "/")
    y = lw.kopf(f"Spieltag {paket['spieltag']:02d} · {saison} · Die Formel sagt")
    titel, unter = aussage(paket)
    y = lw.titel(titel, y + 28)
    y += 62
    y = lw.absatz(unter, y)

    y_ende = lw.fuss(
        f"Quelle: OpenLigaDB (ODbL), eigene Berechnung, Modell {paket['spiele'][0]['modell']['version']} · "
        f"Stand {stand_text(paket['erstellt'])} · Wahrscheinlichkeiten, keine Wettempfehlung"
    )

    breite = lw.b - 2 * RAND
    y_start = y + 44
    # Direkte Beschriftung der Balken-Reihenfolge (Merkmal 6)
    lw.text(RAND, y_start + 16, "Heimsieg", "fett", "notiz", "heim")
    lw.text(RAND + breite / 2, y_start + 16, "Remis", "fett", "notiz", "tinte", ha="center")
    lw.text(RAND + breite, y_start + 16, "Auswärtssieg", "fett", "notiz", "koralle_text", ha="right")
    y_start += 30

    spiele = paket["spiele"]
    zeile = (y_ende - 24 - y_start) / len(spiele)
    balken_h = min(34, zeile * 0.34)
    for i, s in enumerate(spiele):
        oben = y_start + i * zeile
        lw.text(RAND, oben + zeile * 0.40, f"{kurz(s['heim'])} – {kurz(s['gast'])}", "fett", "inhalt")
        lw.text(lw.b - RAND, oben + zeile * 0.40, anstoss(s.get("anstoss_lokal")), "mono", "notiz", "leise", ha="right")
        m = s.get("modell")
        yb = oben + zeile * 0.52
        if not m:
            lw.text(RAND, yb + balken_h * 0.7, "noch keine Prognose", "text", "notiz", "leise")
            continue
        teile = [(m["p_heim"], "heim", "#FFFFFF"), (m["p_remis"], "remis", "#FFFFFF"), (m["p_gast"], "gast", FARBE["tinte"])]
        x = RAND
        for j, (p, farbe, schrift) in enumerate(teile):
            w = breite * p
            lw.flaeche(x, yb, w - (3 if j < 2 else 0), balken_h, farbe)
            ha, tx = ("left", x + 12) if j < 2 else ("right", x + w - 12)
            lw.text(tx, yb + balken_h / 2, prozent(p), "mono_fett", "notiz", schrift, ha=ha, va="center_baseline")
            x += w
    return lw.speichern(pfad or f"grafik/ausgabe/spieltag-{paket['spieltag']:02d}-{format_}.png")
