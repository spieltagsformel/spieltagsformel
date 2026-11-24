"""Modell-Wächter (SF-56): Kalibrierung und Vergleich nach jedem Spieltag, Warnung bei Schieflage.

Liest alle eingefrorenen Datenpakete der Saison und die Ergebnisse, rechnet die Bilanz von Formel,
Vergleichsmodell und Markt und schreibt:
  data/waechter/<saison>.json         (Zahlen)
  entwuerfe/waechter-<saison>.md      (Bericht mit Ampel)
Nichts am Modell wird automatisch geändert – der Wächter meldet nur. Schwellen siehe SCHWELLEN.
"""
import csv
import glob
import json
import os

from . import metriken

ERG = ("heim", "remis", "gast")
SCHWELLEN = {
    "min_spiele_bilanz": 27,        # erst ab 3 vollen Spieltagen bewerten
    "rps_rueckstand": 0.015,        # Formel schlechter als Markt (ganze Saison) → Warnung
    "rps_rueckstand_kurz": 0.03,    # … über die letzten 3 Spieltage → Hinweis
    "kalib_min_n": 15,              # Mindestzahl Wahrscheinlichkeiten je Kalibrierungsstufe
    "kalib_abweichung": 0.15,       # vorhergesagt vs. eingetreten je Stufe → Warnung
    "remis_min_spiele": 45,
    "remis_abweichung": 0.08,       # Remis-Anteil vorhergesagt vs. tatsächlich → Hinweis
}
NAMEN = {"dc-0.2": "Dixon-Coles v0.2"}
STUFEN = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0001)]


def _p(feld):
    return [feld["p_heim"], feld["p_remis"], feld["p_gast"]] if feld else None


def ergebnisse(pfad_csv):
    erg = {}
    if not os.path.exists(pfad_csv):
        return erg
    with open(pfad_csv, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if str(r.get("beendet")).lower() in ("true", "1") and r.get("tore_heim", "") != "":
                h, g = int(r["tore_heim"]), int(r["tore_gast"])
                erg[int(r["id"])] = "heim" if h > g else "gast" if h < g else "remis"
    return erg


def protokoll(pakete, erg):
    """Eine Zeile je beendetem Spiel mit den eingefrorenen Wahrscheinlichkeiten."""
    zeilen = []
    for paket in pakete:
        for s in paket["spiele"]:
            e = erg.get(s["id"])
            if not e:
                continue
            z = {"spieltag": paket["spieltag"], "ergebnis": e,
                 "formel": _p(s.get("modell")), "markt": _p(s.get("markt"))}
            for name, feld in (s.get("weitere_modelle") or {}).items():
                z.setdefault("weitere", {})[name] = _p(feld)
            zeilen.append(z)
    return zeilen


def bilanz(zeilen, schluessel):
    mit = [(z[schluessel] if schluessel in ("formel", "markt") else (z.get("weitere") or {}).get(schluessel), z["ergebnis"])
           for z in zeilen]
    mit = [(p, e) for p, e in mit if p]
    if not mit:
        return None
    n = len(mit)
    return {"n": n,
            "rps": sum(metriken.rps(p, e) for p, e in mit) / n,
            "brier": sum(metriken.brier(p, e) for p, e in mit) / n,
            "treffer": sum(metriken.treffer(p, e) for p, e in mit),
            "remis_vorhergesagt": sum(p[1] for p, _ in mit) / n}


def kalibrierung(zeilen, schluessel="formel"):
    stufen = []
    for lo, hi in STUFEN:
        werte = [(p[i], 1 if z["ergebnis"] == ERG[i] else 0)
                 for z in zeilen if (p := z.get(schluessel)) for i in range(3) if lo <= p[i] < hi]
        n = len(werte)
        stufen.append({"von": lo, "bis": min(hi, 1.0), "n": n,
                       "vorhergesagt": sum(w for w, _ in werte) / n if n else None,
                       "eingetreten": sum(t for _, t in werte) / n if n else None})
    return stufen


def pruefen(zeilen):
    S = SCHWELLEN
    meldungen = []
    gesamt = {"formel": bilanz(zeilen, "formel"), "markt": bilanz(zeilen, "markt")}
    tage = sorted({z["spieltag"] for z in zeilen})
    kurz = [z for z in zeilen if z["spieltag"] in tage[-3:]]
    kurzb = {"formel": bilanz(kurz, "formel"), "markt": bilanz(kurz, "markt")}
    f, m = gesamt["formel"], gesamt["markt"]
    if f and m and m["n"] >= S["min_spiele_bilanz"] and f["rps"] - m["rps"] > S["rps_rueckstand"]:
        meldungen.append(("warnung", f"Formel liegt über die Saison deutlich hinter dem Markt (RPS {f['rps']:.3f} gegen {m['rps']:.3f})."))
    fk, mk = kurzb["formel"], kurzb["markt"]
    if fk and mk and fk["rps"] - mk["rps"] > S["rps_rueckstand_kurz"]:
        meldungen.append(("hinweis", f"Letzte {len(tage[-3:])} Spieltage: Formel hinter dem Markt (RPS {fk['rps']:.3f} gegen {mk['rps']:.3f}) – beobachten, nichts ändern."))
    for st in kalibrierung(zeilen):
        if st["n"] >= S["kalib_min_n"] and abs(st["vorhergesagt"] - st["eingetreten"]) > S["kalib_abweichung"]:
            meldungen.append(("warnung", f"Kalibrierung {round(st['von']*100)}–{round(st['bis']*100)} %: vorhergesagt {st['vorhergesagt']:.0%}, eingetreten {st['eingetreten']:.0%} (n = {st['n']})."))
    if f and f["n"] >= S["remis_min_spiele"]:
        tats = sum(1 for z in zeilen if z["ergebnis"] == "remis") / len(zeilen)
        if abs(f["remis_vorhergesagt"] - tats) > S["remis_abweichung"]:
            meldungen.append(("hinweis", f"Remis: Formel erwartet im Schnitt {f['remis_vorhergesagt']:.0%}, tatsächlich {tats:.0%}."))
    ohne = sum(1 for z in zeilen if not z["formel"])
    if ohne:
        meldungen.append(("warnung", f"{ohne} beendete(s) Spiel(e) ohne eingefrorene Formel-Prognose – Datenpaket prüfen."))
    ohne_m = sum(1 for z in zeilen if not z["markt"])
    if ohne_m:
        meldungen.append(("hinweis", f"{ohne_m} beendete(s) Spiel(e) ohne Marktwerte."))
    return gesamt, kurzb, meldungen


def _k(x, st=3):
    return f"{x:.{st}f}".replace(".", ",")


def bericht(saison, zeilen, gesamt, kurzb, meldungen, weitere):
    ampel = "🔴 Warnung" if any(a == "warnung" for a, _ in meldungen) else "🟡 Hinweis" if meldungen else "🟢 Alles im Rahmen"
    tage = sorted({z["spieltag"] for z in zeilen})
    t = [f"# Modell-Wächter {saison.replace('-', '/')}", "",
         f"**Stand:** {len(zeilen)} beendete Spiele aus Spieltag {', '.join(map(str, tage)) or '–'} · **Ampel:** {ampel}", "",
         "Der Wächter ändert nichts am Modell. Er meldet nur – entschieden wird im Modell-Logbuch, frühestens nach mehreren Spieltagen.", ""]
    if meldungen:
        t += ["## Meldungen", ""] + [f"- **{a.capitalize()}:** {txt}" for a, txt in meldungen] + [""]
    t += ["## Bilanz", "", "| Modell | Spiele | RPS | Brier | Treffer | Ø Remis |", "|---|---|---|---|---|---|"]
    for name, b in [("Formel", gesamt["formel"]), ("Markt", gesamt["markt"])] + [(NAMEN.get(n, n), bilanz(zeilen, n)) for n in weitere]:
        if b:
            t.append(f"| {name} | {b['n']} | {_k(b['rps'])} | {_k(b['brier'])} | {b['treffer']} | {round(b['remis_vorhergesagt']*100)} % |")
    tats = sum(1 for z in zeilen if z["ergebnis"] == "remis")
    t += ["", f"Tatsächliche Remis: {tats} von {len(zeilen)}. RPS und Brier: kleiner ist besser.", ""]
    t += ["## Kalibrierung der Formel", "", "Wie oft trat ein Ausgang ein, dem die Formel eine bestimmte Wahrscheinlichkeit gab? Gut kalibriert heißt: beide Spalten ähnlich.", "",
          "| Stufe | Anzahl | vorhergesagt | eingetreten |", "|---|---|---|---|"]
    for st in kalibrierung(zeilen):
        if st["n"]:
            t.append(f"| {round(st['von']*100)}–{round(st['bis']*100)} % | {st['n']} | {round(st['vorhergesagt']*100)} % | {round(st['eingetreten']*100)} % |")
    t += ["", f"*Schwellen und Regeln: `pipeline/waechter.py` (SCHWELLEN). Wenige Spiele = großer Zufall; unter {SCHWELLEN['kalib_min_n']} Werten je Stufe wird nicht gewarnt.*"]
    return "\n".join(t) + "\n"


def lauf(saison_text, startjahr, wurzel="."):
    pakete = []
    for pf in sorted(glob.glob(os.path.join(wurzel, "data", "spieltage", saison_text, "*.json"))):
        with open(pf, encoding="utf-8") as f:
            pakete.append(json.load(f))
    erg = ergebnisse(os.path.join(wurzel, "data", "clean", f"spiele_{startjahr}.csv"))
    zeilen = protokoll(pakete, erg)
    gesamt, kurzb, meldungen = pruefen(zeilen)
    weitere = sorted({n for z in zeilen for n in (z.get("weitere") or {})})
    daten = {"saison": saison_text, "spiele": len(zeilen), "gesamt": gesamt, "letzte_3": kurzb,
             "weitere": {n: bilanz(zeilen, n) for n in weitere}, "kalibrierung": kalibrierung(zeilen),
             "meldungen": [{"art": a, "text": t} for a, t in meldungen], "schwellen": SCHWELLEN}
    os.makedirs(os.path.join(wurzel, "data", "waechter"), exist_ok=True)
    with open(os.path.join(wurzel, "data", "waechter", f"{saison_text}.json"), "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=1)
    os.makedirs(os.path.join(wurzel, "entwuerfe"), exist_ok=True)
    with open(os.path.join(wurzel, "entwuerfe", f"waechter-{saison_text}.md"), "w", encoding="utf-8") as f:
        f.write(bericht(saison_text, zeilen, gesamt, kurzb, meldungen, weitere))
    return daten
