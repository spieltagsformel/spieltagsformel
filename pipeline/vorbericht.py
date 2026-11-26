"""Vorbericht: Textentwurf (Markdown) für den nächsten Spieltag aus dem Datenpaket.

Alle Zahlen stammen aus dem Datenpaket. Was nicht im Paket steht (TV-Sender, Aufstellung beim Freitagsspiel, sichere Ausfälle,
Kontext), wird als [PRÜFEN: …] bzw. [AUS DER REDAKTION: …] markiert – nichts wird geschätzt.
"""
import hashlib
from datetime import datetime

ERG = ("heim", "remis", "gast")
WORT = {"heim": "Heimsieg", "remis": "Remis", "gast": "Auswärtssieg"}
TAG_LANG = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
MONAT = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September",
         "Oktober", "November", "Dezember"]
KNAPP = 0.03          # Tipp mit weniger als 3 Prozentpunkten Vorsprung gilt als „knapp“
MARKER = "<!-- vorbericht-auto sha="


def _p(feld):
    return (feld["p_heim"], feld["p_remis"], feld["p_gast"]) if feld else None


def tipp(p):
    """(Ergebnis, knapp?) für ein Wahrscheinlichkeits-Tripel."""
    reihen = sorted(range(3), key=lambda i: p[i], reverse=True)
    return ERG[reihen[0]], p[reihen[0]] - p[reihen[1]] < KNAPP


def _pz(x):
    return f"{round(x * 100)} %"


def _drei(p):
    return " · ".join(_pz(x) for x in p)


def _k(x):
    return f"{x:.1f}".replace(".", ",")


def _zeit(spiel):
    lokal = spiel.get("anstoss_lokal")
    return datetime.fromisoformat(lokal) if lokal else None


def tv_hinweis(t):
    """Standardregel nach Anstoßzeit (Rechte 2026/27–2028/29), immer zur Prüfung markiert."""
    if t is None:
        return "[PRÜFEN: Anstoß und Sender noch offen]"
    wt, hm = t.weekday(), t.strftime("%H:%M")
    if wt == 4:
        regel = "Sky/WOW (Freitagsspiel)"
    elif wt == 5 and hm == "15:30":
        regel = "Sky/WOW (Einzelspiel), DAZN (Konferenz)"
    elif wt == 5:
        regel = "Sky/WOW (Topspiel)"
    elif wt == 6:
        regel = "DAZN"
    else:
        regel = "Sky/WOW oder DAZN"
    return f"voraussichtlich {regel} [PRÜFEN: Ansetzung und mögliches Free-TV-Spiel]"


def gruppiert(spiele):
    """[(Tageszeile, [(Uhrzeit, [Spiele])])] in Anstoß-Reihenfolge; Spiele ohne Termin am Ende."""
    mit = sorted((s for s in spiele if _zeit(s)), key=lambda s: (_zeit(s), s["heim"]))
    ohne = [s for s in spiele if not _zeit(s)]
    tage = []
    for s in mit:
        t = _zeit(s)
        tag = f"{TAG_LANG[t.weekday()]}, {t.day}. {MONAT[t.month - 1]}"
        uhr = t.strftime("%H:%M") + " Uhr"
        if not tage or tage[-1][0] != tag:
            tage.append((tag, []))
        slots = tage[-1][1]
        if not slots or slots[-1][0] != uhr:
            slots.append((uhr, []))
        slots[-1][1].append(s)
    if ohne:
        tage.append(("Termin noch offen", [("", ohne)]))
    return tage


def abweichung(s):
    """Größter Abstand Formel–Markt über die drei Ausgänge (0, wenn kein Markt)."""
    f, m = _p(s.get("modell")), _p(s.get("markt"))
    if not f or not m:
        return 0.0
    return max(abs(f[i] - m[i]) for i in range(3))


def _spielblock(s, kurz):
    h, g = kurz(s["heim"]), kurz(s["gast"])
    f, m = _p(s.get("modell")), _p(s.get("markt"))
    z = [f"#### {h} – {g}", ""]
    z.append(f"- **Tabelle:** {h} Platz {s['platz_heim']} (Form {s['form_heim'] or '–'}) gegen "
             f"{g} Platz {s['platz_gast']} (Form {s['form_gast'] or '–'})")
    if s.get("erwartete_tore"):
        z.append(f"- **Erwartete Tore:** {_k(s['erwartete_tore']['heim'])} : {_k(s['erwartete_tore']['gast'])}")
    if f:
        t, knapp = tipp(f)
        z.append(f"- **Formel:** {_drei(f)} → {WORT[t]}" + (" (knapp)" if knapp else ""))
    if m:
        t, knapp = tipp(m)
        z.append(f"- **Markt:** {_drei(m)} → {WORT[t]}" + (" (knapp)" if knapp else ""))
    z.append(f"- **Tabellen-Regel:** {WORT[s['vergleich']['tabellenplatz']]}")
    z.append(f"- **Wo läuft das Spiel?** {tv_hinweis(_zeit(s))}")
    # Aufstellungen sind vorher meist nicht bekannt: nur beim Freitagsspiel die voraussichtliche Elf,
    # sonst nur Spieler, die sicher fehlen (Verletzung mit bestätigter Ausfallzeit, Sperre). Entscheidung 26.11.2026.
    t = _zeit(s)
    if t is not None and t.weekday() == 4:
        z.append(f"- **Voraussichtliche Aufstellung {h}:** [PRÜFEN: eigene Zusammenstellung aus mindestens zwei Quellen, verlinkt]")
        z.append(f"- **Voraussichtliche Aufstellung {g}:** [PRÜFEN: eigene Zusammenstellung aus mindestens zwei Quellen, verlinkt]")
    z.append(f"- **Fehlen sicher:** {h}: [PRÜFEN: nur bestätigte Ausfälle mit Quelle] · {g}: [PRÜFEN: nur bestätigte Ausfälle mit Quelle]")
    z += ["", "[AUS DER REDAKTION: ein Satz Kontext – Serie, Bedeutung]", ""]
    return z


def text(paket, kurz=lambda n: n):
    saison = paket["saison"].replace("-", "/")
    nr = paket["spieltag"]
    spiele = paket["spiele"]
    mit_formel = [s for s in spiele if s.get("modell")]
    mit_markt = [s for s in spiele if s.get("markt")]

    sicher = max(mit_formel, key=lambda s: max(_p(s["modell"])), default=None)
    offen = min(mit_formel, key=lambda s: max(_p(s["modell"])), default=None)
    if sicher:
        t, _ = tipp(_p(sicher["modell"]))
        sieger = sicher["heim"] if t == "heim" else sicher["gast"] if t == "gast" else None
        titel = (f"{kurz(sieger)} vorn, {kurz(offen['heim'])} – {kurz(offen['gast'])} offen"
                 if sieger and offen is not sicher else f"Der {nr}. Spieltag in Zahlen")
    else:
        titel = f"Der {nr}. Spieltag in Zahlen"

    teile = [f"# Die Formel sagt: {titel}", "",
             f"*Vorbericht zum {nr}. Spieltag {saison} · Titel ist ein Vorschlag – [AUS DER REDAKTION: anpassen oder übernehmen]*", "",
             "[AUS DER REDAKTION: zwei, drei Sätze Einstieg – worauf schaut die Liga an diesem Wochenende?]", ""]

    # Kurzüberblick
    if mit_formel:
        tipps = [tipp(_p(s["modell"]))[0] for s in mit_formel]
        anz = {k: tipps.count(k) for k in ERG}
        teile += ["## Auf einen Blick", ""]
        teile.append(f"- Die Formel sieht {anz['heim']}× den Gastgeber, {anz['gast']}× die Gäste vorn"
                     + (f" und tippt {anz['remis']}× Remis." if anz["remis"] else ". Remis ist bei keinem Spiel der wahrscheinlichste Ausgang – typisch, weil ein Unentschieden selten über 30 % liegt."))
        p = _p(sicher["modell"])
        teile.append(f"- Am klarsten: **{kurz(sicher['heim'])} – {kurz(sicher['gast'])}** mit {_pz(max(p))} für den {WORT[tipp(p)[0]]}.")
        p = _p(offen["modell"])
        teile.append(f"- Am offensten: **{kurz(offen['heim'])} – {kurz(offen['gast'])}** ({_drei(p)}).")
        knappe = [s for s in mit_formel if tipp(_p(s["modell"]))[1]]
        if knappe:
            teile.append("- Münzwurf-Tipps (unter 3 Prozentpunkten Vorsprung): "
                         + ", ".join(f"{kurz(s['heim'])} – {kurz(s['gast'])}" for s in knappe) + ".")
        teile.append("")

    # Formel gegen Markt
    if mit_markt and mit_formel:
        strittig = sorted((s for s in mit_markt if s.get("modell")), key=abweichung, reverse=True)[:3]
        strittig = [s for s in strittig if abweichung(s) >= 0.05]
        teile += ["## Formel gegen Markt", ""]
        if strittig:
            teile.append("Hier sieht die Formel das Spiel anders als die Buchmacher im Durchschnitt (ohne Marge):")
            teile.append("")
            for s in strittig:
                f, m = _p(s["modell"]), _p(s["markt"])
                teile.append(f"- **{kurz(s['heim'])} – {kurz(s['gast'])}:** Formel {_drei(f)}, Markt {_drei(m)}")
            teile += ["", "[AUS DER REDAKTION: Wem traust du hier mehr – und warum?]", ""]
        else:
            teile += ["Formel und Markt liegen diesmal überall nah beieinander (höchstens 5 Prozentpunkte Abstand).", ""]

    # Spiele nach Tagen
    teile += ["## Alle Spiele", "",
              "Wahrscheinlichkeiten in der Reihenfolge Heimsieg · Remis · Auswärtssieg.", ""]
    for tag, slots in gruppiert(spiele):
        teile += [f"### {tag}", ""]
        for uhr, liste in slots:
            if uhr:
                teile += [f"**{uhr}**", ""]
            for s in liste:
                teile += _spielblock(s, kurz)

    teile += ["## So rechnen wir", "",
              "Die Formel ist ein Elo-Modell mit Heimvorteil; die erwarteten Tore stammen aus unserem Vergleichsmodell (Dixon-Coles). "
              "Die Prognosen werden vor dem ersten Anpfiff eingefroren und nach dem Spieltag ehrlich abgerechnet – "
              "gegen den Markt und gegen die einfache Tabellen-Regel (der besser Platzierte gewinnt). Ein einzelner Spieltag sagt wenig, die Bilanz zählt.", "",
              "---", "",
              "*Rein rechnerische Wahrscheinlichkeiten · keine Wettempfehlung · 18+ · Glücksspiel kann süchtig machen · Hilfe: check-dein-spiel.de*", "",
              "Quellen: OpenLigaDB (ODbL), " + ("The Odds API (margenbereinigte Durchschnittsquoten), " if mit_markt else "")
              + f"eigene Berechnung. Datenpaket {paket['saison']}/{nr:02d} im Repository."]
    return "\n".join(teile) + "\n"


def _sha(inhalt):
    return hashlib.sha256(inhalt.encode("utf-8")).hexdigest()[:16]


def mit_marker(inhalt):
    """Stellt eine Kennung voran, an der spätere Läufe erkennen, ob der Entwurf von Hand bearbeitet wurde."""
    return f"{MARKER}{_sha(inhalt)} -->\n{inhalt}"


def unbearbeitet(vorhanden):
    """True, wenn der Entwurf noch genau so ist, wie die Pipeline ihn geschrieben hat."""
    erste, _, rest = vorhanden.partition("\n")
    if not erste.startswith(MARKER):
        return False
    return erste[len(MARKER):].split(" ")[0] == _sha(rest)
