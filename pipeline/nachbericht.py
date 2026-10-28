"""Nachbericht: Abrechnung der eingefrorenen Prognosen eines Spieltags.

Vergleicht Formel (Hauptmodell), Markt und Tabellen-Regel mit den Ergebnissen,
findet die größte Fehlprognose und schreibt einen Textentwurf (Markdown).
Alle Zahlen stammen aus dem Datenpaket und den Ergebnissen; nichts wird geschätzt.
"""
from . import metriken

ERG = ("heim", "remis", "gast")
WORT = {"heim": "Heimsieg", "remis": "Remis", "gast": "Auswärtssieg"}


def _probs(feld):
    return (feld["p_heim"], feld["p_remis"], feld["p_gast"]) if feld else None


def _tipp(p):
    return ERG[max(range(3), key=lambda i: p[i])]


def ergebnis(s):
    h, g = s["tore_heim"], s["tore_gast"]
    return "heim" if h > g else "gast" if h < g else "remis"


def auswerten(paket, spiele_saison):
    """paket: eingefrorenes Datenpaket; spiele_saison: bereinigte Spiele mit Ergebnissen."""
    nach_id = {s["id"]: s for s in spiele_saison}
    zeilen = []
    for s in paket["spiele"]:
        e = nach_id.get(s["id"])
        if not e or not e["beendet"]:
            continue
        erg = ergebnis(e)
        z = {"id": s["id"], "heim": s["heim"], "gast": s["gast"], "tore": f"{e['tore_heim']}:{e['tore_gast']}",
             "ergebnis": erg, "regel": s["vergleich"]["tabellenplatz"], "regel_treffer": s["vergleich"]["tabellenplatz"] == erg}
        for name, feld in (("formel", s.get("modell")), ("markt", s.get("markt"))):
            p = _probs(feld)
            if p:
                z[name] = {"p": p, "tipp": _tipp(p), "treffer": _tipp(p) == erg,
                           "p_ergebnis": p[ERG.index(erg)], "rps": metriken.rps(p, erg)}
        community = s["vergleich"].get("community")
        if community:
            z["community"] = {"tipp": community, "treffer": community == erg}
        zeilen.append(z)
    return zeilen


def zusammenfassung(zeilen):
    n = len(zeilen)
    def summe(name):
        mit = [z for z in zeilen if name in z]
        if not mit:
            return None
        return {"n": len(mit), "treffer": sum(z[name]["treffer"] for z in mit),
                "rps": sum(z[name]["rps"] for z in mit) / len(mit) if "rps" in mit[0][name] else None,
                "remis_getippt": sum(1 for z in mit if z[name]["tipp"] == "remis")}
    regel = {"n": n, "treffer": sum(z["regel_treffer"] for z in zeilen),
             "remis_getippt": sum(1 for z in zeilen if z["regel"] == "remis")}
    mit_formel = [z for z in zeilen if "formel" in z]
    daneben = min(mit_formel, key=lambda z: z["formel"]["p_ergebnis"]) if mit_formel else None
    volltreffer = max((z for z in mit_formel if z["formel"]["treffer"]), key=lambda z: z["formel"]["p_ergebnis"], default=None)
    ergebnisse = {k: sum(1 for z in zeilen if z["ergebnis"] == k) for k in ERG}
    return {"spiele": n, "formel": summe("formel"), "markt": summe("markt"), "regel": regel,
            "community": summe("community"), "daneben": daneben, "volltreffer": volltreffer, "ergebnisse": ergebnisse}


def _pz(p):
    return f"{round(p * 100)} %"


def _k(x, stellen=3):
    return f"{x:.{stellen}f}".replace(".", ",")


def text(paket, zeilen, z, bilanz=None, kurz=lambda n: n):
    """Markdown-Entwurf. Platzhalter [AUS DER REDAKTION: …] füllt der Gründer."""
    saison = paket["saison"].replace("-", "/")
    t = paket["spieltag"]
    f, m, r = z["formel"], z["markt"], z["regel"]
    d = z["daneben"]
    if d and d["ergebnis"] == "remis":
        ueberraschung = f"Das Remis in {kurz(d['heim'])} erwischt die Formel kalt"
    elif d:
        sieger = d["heim"] if d["ergebnis"] == "heim" else d["gast"]
        ueberraschung = f"{kurz(sieger)} erwischt die Formel kalt"
    else:
        ueberraschung = "Die Abrechnung"
    teile = [f"# {f['treffer']} von {f['n']}: {ueberraschung}", "",
             f"*Nachbericht zum {t}. Spieltag {saison} · Titel ist ein Vorschlag – [AUS DER REDAKTION: anpassen oder übernehmen]*", ""]

    # Einstieg mit den harten Zahlen
    satz = f"Die Formel lag bei **{f['treffer']} von {f['n']}** Spielen richtig"
    if m:
        satz += f", der Markt bei **{m['treffer']} von {m['n']}**"
    satz += f", die Tabellen-Regel bei **{r['treffer']} von {r['n']}**."
    teile += [satz, "", "[AUS DER REDAKTION: ein, zwei Sätze Einordnung]", ""]

    mit_markt = any("markt" in zl for zl in zeilen)
    kopf = "| Spiel | Ergebnis | Formel |" + (" Markt |" if mit_markt else "") + " Tabellen-Regel |"
    trenner = "|---|---|---|" + ("---|" if mit_markt else "") + "---|"
    teile += ["## Die Abrechnung", "", kopf, trenner]
    for zl in zeilen:
        def zelle(name):
            if name not in zl:
                return "–"
            x = zl[name]
            return f"{WORT[x['tipp']]} ({_pz(max(x['p']))}) {'✓' if x['treffer'] else '✗'}"
        teile.append(f"| {kurz(zl['heim'])} – {kurz(zl['gast'])} | {zl['tore']} | {zelle('formel')} |"
                     + (f" {zelle('markt')} |" if mit_markt else "")
                     + f" {WORT[zl['regel']]} {'✓' if zl['regel_treffer'] else '✗'} |")
    teile += ["", "✓ = Ergebnis getroffen (Heimsieg, Remis oder Auswärtssieg). In Klammern: die Wahrscheinlichkeit des getippten Ergebnisses.", ""]

    # Genauigkeit über die Wahrscheinlichkeiten
    if m and f.get("rps") is not None and m.get("rps") is not None:
        besser = "die Formel" if f["rps"] < m["rps"] else "der Markt"
        teile += ["## Wer lag näher dran?", "",
                  f"Die Trefferquote erzählt nur die halbe Geschichte. Der Ranked Probability Score (RPS) bewertet auch, wie sicher sich jemand war – kleiner ist besser. "
                  f"Diesmal: Formel **{_k(f['rps'])}**, Markt **{_k(m['rps'])}**. Näher dran war damit {besser}.", ""]

    # Größte Fehlprognose
    if d:
        teile += ["## Die Formel lag daneben", "",
                  f"Am meisten überrascht hat die Formel **{kurz(d['heim'])} – {kurz(d['gast'])} ({d['tore']})**. "
                  f"Für dieses Ergebnis ({WORT[d['ergebnis']]}) hatte sie nur **{_pz(d['formel']['p_ergebnis'])}** berechnet"
                  + (f", der Markt {_pz(d['markt']['p_ergebnis'])}." if "markt" in d else "."),
                  "", "[AUS DER REDAKTION: Was ist passiert? Ein Satz Selbstironie, dann die Erklärung aus den Zahlen.]", ""]
    v = z["volltreffer"]
    if v:
        teile += [f"Am sichersten richtig lag sie bei **{kurz(v['heim'])} – {kurz(v['gast'])} ({v['tore']})** mit {_pz(v['formel']['p_ergebnis'])} für den {WORT[v['ergebnis']]}.", ""]

    # Auffälligkeiten aus den Zahlen
    e = z["ergebnisse"]
    teile += ["## Was die Zahlen zeigen", "",
              f"- Ergebnisse: {e['heim']}× Heimsieg, {e['remis']}× Remis, {e['gast']}× Auswärtssieg.",
              f"- Remis getippt: Formel {f['remis_getippt']}-mal, Tabellen-Regel {r['remis_getippt']}-mal"
              + (f", Markt {m['remis_getippt']}-mal." if m else ".")]
    if bilanz and bilanz["spieltage"] > 1:
        b = bilanz
        teile.append(f"- Bilanz seit Start ({b['spieltage']} Spieltage, {b['formel']['n']} Spiele): Formel {b['formel']['treffer']} Treffer"
                     + (f", Markt {b['markt']['treffer']}" if b.get("markt") else "")
                     + f", Tabellen-Regel {b['regel']['treffer']}.")
    teile += ["- [AUS DER REDAKTION: eine Auffälligkeit, die dir aufgefallen ist]", ""]

    teile += ["## Kontostand: 100-€-Experiment", "",
              "Das rechnerische Experiment startet mit dem ersten Spieltag nach der Winterpause. Bis dahin üben wir die Abrechnung ohne Kontostand.",
              "", "*Rechnerisches Experiment ohne echtes Geld · 18+ · Glücksspiel kann süchtig machen · Hilfe: check-dein-spiel.de*", "",
              "---", "", "Quellen: OpenLigaDB (ODbL), " + ("The Odds API (margenbereinigte Durchschnittsquoten), " if mit_markt else "") + "eigene Berechnung. "
              + f"Die Prognosen wurden vor Anpfiff eingefroren (Datenpaket {paket['saison']}/{t:02d} im Repository). Keine Wettempfehlung."]
    return "\n".join(teile) + "\n"


def bilanz(berichte):
    """Summe über mehrere Spieltage: berichte = Liste von (zeilen) je Spieltag."""
    alle = [z for zeilen in berichte for z in zeilen]
    s = zusammenfassung(alle) if alle else None
    if not s:
        return None
    s["spieltage"] = len(berichte)
    return s
