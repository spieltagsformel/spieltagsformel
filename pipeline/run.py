"""Kommandozeile der Pipeline.

Beispiele (im Repo-Ordner ausführen):
    python -m pipeline.run abrufen --von 2019 --bis 2026
    python -m pipeline.run paket --saison 2026 --spieltag auto
"""
import argparse
import json
import os
import sys
import time

import glob
import re

from . import elo, fit, openligadb, paket, speicher

RAW = "data/raw"
CLEAN = "data/clean"
SPIELTAGE = "data/spieltage"


def cmd_abrufen(args):
    namen = {}
    for saison in range(args.von, args.bis + 1):
        print(f"Saison {saison}/{saison + 1} wird abgerufen ...")
        roh = openligadb.abrufen_saison(saison)
        os.makedirs(RAW, exist_ok=True)
        with open(f"{RAW}/{openligadb.LIGA}_{saison}.json", "w", encoding="utf-8") as f:
            json.dump(roh, f, ensure_ascii=False)
        zeilen = [openligadb.umwandeln(s, saison) for s in roh]
        for w in openligadb.pruefen_saison(zeilen):
            print(f"  WARNUNG {saison}: {w}")
        speicher.schreibe_csv(f"{CLEAN}/spiele_{saison}.csv", zeilen)
        for z in zeilen:
            namen.setdefault(z["heim_id"], set()).add(z["heim"])
            namen.setdefault(z["gast_id"], set()).add(z["gast"])
        beendet = sum(1 for z in zeilen if z["beendet"])
        print(f"  {len(zeilen)} Spiele, {beendet} beendet")
        time.sleep(1)
    teams = {str(i): sorted(n) for i, n in sorted(namen.items())}
    with open(f"{CLEAN}/teams_{args.von}-{args.bis}.json", "w", encoding="utf-8") as f:
        json.dump(teams, f, ensure_ascii=False, indent=1)
    abweichend = {i: n for i, n in teams.items() if len(n) > 1}
    if abweichend:
        print("Hinweis: Teams mit mehreren Schreibweisen (bitte prüfen):")
        for i, n in abweichend.items():
            print(f"  {i}: {n}")


def lade_saisons(bis):
    """Alle bereinigten Saisons bis einschließlich `bis` als {Startjahr: Spiele}."""
    saisons = {}
    for pfad in glob.glob(f"{CLEAN}/spiele_*.csv"):
        jahr = int(re.search(r"spiele_(\d{4})\.csv$", pfad).group(1))
        if jahr <= bis:
            saisons[jahr] = speicher.lese_csv(pfad)
    return saisons


def lade_parameter(pfad="data/modell/elo_params.json"):
    if os.path.exists(pfad):
        with open(pfad, encoding="utf-8") as f:
            return json.load(f)["parameter"]
    return None


def cmd_fit(args):
    saisons = lade_saisons(args.train_bis + 1)
    b = fit.lauf(saisons, args.train_bis)
    print(json.dumps(b, indent=1, ensure_ascii=False))
    if args.mit_dc:
        b2 = fit.lauf_dc(saisons, args.train_bis, elo_params=lade_parameter())
        print(json.dumps(b2, indent=1, ensure_ascii=False))


def dixon_coles_vorhersagen(saisons, saison, spiele_tag):
    """Dixon-Coles v0.2 für einen Spieltag: Wahrscheinlichkeiten und erwartete Tore."""
    from . import dixon_coles
    params = lade_parameter("data/modell/dc_params.json")
    alle = [s for j in sorted(saisons) for s in saisons[j]]
    zeiten = [s["anstoss_utc"] for s in spiele_tag if s["anstoss_utc"]]
    if not zeiten:
        return {}, {}
    m = dixon_coles.DixonColes(params)
    vorwerte = {}
    if saison - 1 in saisons:
        erster = min(s["anstoss_utc"] for s in saisons[saison] if s["spieltag"] == 1 and s["anstoss_utc"])
        m.anpassen(alle, erster)
        vorwerte = dixon_coles.absteiger_vorwerte(m, saisons[saison - 1], saisons[saison])
    m.anpassen(alle, min(zeiten), vorwerte)
    probs = {s["id"]: m.vorhersage(s["heim_id"], s["gast_id"]) for s in spiele_tag}
    tore = {s["id"]: m.erwartete_tore(s["heim_id"], s["gast_id"]) for s in spiele_tag}
    return probs, tore


def cmd_paket(args):
    spiele = speicher.lese_csv(f"{CLEAN}/spiele_{args.saison}.csv")
    vor = f"{CLEAN}/spiele_{args.saison - 1}.csv"
    vorsaison = speicher.lese_csv(vor) if os.path.exists(vor) else None
    spieltag = paket.naechster_spieltag(spiele) if args.spieltag == "auto" else int(args.spieltag)
    if spieltag is None:
        print("Alle Spiele der Saison sind beendet.")
        return
    saisons = lade_saisons(args.saison)
    spiele_tag = [s for s in spiele if s["spieltag"] == spieltag]
    # Stichtag = erster Anstoß des Spieltags: das Modell kennt nur Spiele davor
    stichtag = min((s["anstoss_utc"] for s in spiele_tag if s["anstoss_utc"]), default=None)
    bekannt = paket.bis_stichtag(saisons, stichtag) if stichtag else saisons
    modell = elo.EloModell(lade_parameter())
    modell.lauf(bekannt)
    vorhersagen = {s["id"]: modell.vorhersage(s["heim_id"], s["gast_id"]) for s in spiele_tag}
    try:
        dc_probs, dc_tore = dixon_coles_vorhersagen(bekannt, args.saison, spiele_tag)
    except (ImportError, ValueError) as fehler:
        print(f"Hinweis: Dixon-Coles übersprungen ({fehler})")
        dc_probs, dc_tore = {}, {}
    daten = paket.baue_paket(args.saison, spieltag, spiele, vorsaison, modell=vorhersagen,
                             modell_version=elo.VERSION, weitere_modelle={"dc-0.2": dc_probs} if dc_probs else None,
                             erwartete_tore=dc_tore)
    ordner = f"{SPIELTAGE}/{daten['saison']}"
    os.makedirs(ordner, exist_ok=True)
    pfad = f"{ordner}/{spieltag:02d}.json"
    if os.path.exists(pfad):
        from datetime import datetime, timezone
        with open(pfad, encoding="utf-8") as f:
            alt = json.load(f)
        daten = paket.einfrieren(daten, alt, datetime.now(timezone.utc).isoformat(timespec="seconds"))
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=1)
    print(f"Datenpaket geschrieben: {pfad}")
    for h in daten["hinweise"]:
        print("  " + h)


def cmd_quoten(args):
    from datetime import datetime, timezone
    from . import quoten
    pfad_tag = args.spieltag
    spiele = speicher.lese_csv(f"{CLEAN}/spiele_{args.saison}.csv")
    spieltag = paket.naechster_spieltag(spiele) if pfad_tag == "auto" else int(pfad_tag)
    saison_txt = f"{args.saison}-{str(args.saison + 1)[-2:]}"
    pfad = f"{SPIELTAGE}/{saison_txt}/{spieltag:02d}.json"
    if not os.path.exists(pfad):
        print(f"Kein Datenpaket {pfad} – zuerst 'paket' ausführen.")
        return
    schluessel = os.environ.get("ODDS_API_KEY", "")
    if not schluessel:
        print("Hinweis: ODDS_API_KEY nicht gesetzt, Quoten übersprungen.")
        return
    ereignisse, rest = quoten.abrufen(schluessel)
    jetzt = datetime.now(timezone.utc).isoformat(timespec="seconds")
    os.makedirs(RAW, exist_ok=True)
    with open(f"{RAW}/quoten_{jetzt[:13].replace(':', '')}.json", "w", encoding="utf-8") as f:
        json.dump(ereignisse, f)  # Rohdaten nur lokal (data/raw ist von Git ausgeschlossen)
    with open(pfad, encoding="utf-8") as f:
        daten = json.load(f)
    treffer = quoten.ergaenze_paket(daten, ereignisse, jetzt)
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=1)
    print(f"Quoten für {treffer} von {len(daten['spiele'])} Spielen eingetragen. Verbleibende Credits: {rest}")


def cmd_nachbericht(args):
    from . import nachbericht
    try:
        from grafik.namen import kurz
    except ImportError:
        kurz = lambda n: n
    spiele = speicher.lese_csv(f"{CLEAN}/spiele_{args.saison}.csv")
    saison_txt = f"{args.saison}-{str(args.saison + 1)[-2:]}"
    ordner = f"{SPIELTAGE}/{saison_txt}"
    vorhanden = sorted(int(d[:2]) for d in os.listdir(ordner) if d.endswith(".json")) if os.path.isdir(ordner) else []

    def fertig(tag):
        sp = [s for s in spiele if s["spieltag"] == tag]
        return bool(sp) and all(s["beendet"] for s in sp)

    if args.spieltag == "letzter":
        kandidaten = [t for t in vorhanden if fertig(t)]
        if not kandidaten:
            print("Noch kein abgeschlossener Spieltag mit eingefrorenem Datenpaket.")
            return
        tag = kandidaten[-1]
    else:
        tag = int(args.spieltag)
        if tag not in vorhanden or not fertig(tag):
            print(f"Spieltag {tag}: Datenpaket fehlt oder Spiele noch nicht beendet.")
            return

    def lade(t):
        with open(f"{ordner}/{t:02d}.json", encoding="utf-8") as f:
            return json.load(f)

    daten = lade(tag)
    zeilen = nachbericht.auswerten(daten, spiele)
    zusammen = nachbericht.zusammenfassung(zeilen)
    bis_jetzt = [nachbericht.auswerten(lade(t), spiele) for t in vorhanden if t <= tag and fertig(t)]
    gesamt = nachbericht.bilanz(bis_jetzt)

    os.makedirs(f"data/nachberichte/{saison_txt}", exist_ok=True)
    with open(f"data/nachberichte/{saison_txt}/{tag:02d}.json", "w", encoding="utf-8") as f:
        json.dump({"saison": daten["saison"], "spieltag": tag, "spiele": zeilen, "zusammenfassung": zusammen,
                   "bilanz_seit_start": gesamt}, f, ensure_ascii=False, indent=1)
    os.makedirs("entwuerfe", exist_ok=True)
    pfad = f"entwuerfe/nachbericht-{saison_txt}-{tag:02d}.md"
    if os.path.exists(pfad) and not args.neu:
        print(f"Entwurf existiert schon ({pfad}), nicht überschrieben. Mit --neu neu erzeugen.")
    else:
        with open(pfad, "w", encoding="utf-8") as f:
            f.write(nachbericht.text(daten, zeilen, zusammen, gesamt, kurz))
        print(f"Entwurf geschrieben: {pfad}")
    fz = zusammen["formel"]
    print(f"Spieltag {tag}: Formel {fz['treffer']}/{fz['n']}, Tabellen-Regel {zusammen['regel']['treffer']}/{zusammen['regel']['n']}"
          + (f", Markt {zusammen['markt']['treffer']}/{zusammen['markt']['n']}" if zusammen["markt"] else ""))


def main(argv=None):
    p = argparse.ArgumentParser(prog="pipeline")
    sub = p.add_subparsers(dest="befehl", required=True)
    a = sub.add_parser("abrufen", help="Saisons von OpenLigaDB laden und bereinigen")
    a.add_argument("--von", type=int, required=True, help="erstes Startjahr, z. B. 2019")
    a.add_argument("--bis", type=int, required=True, help="letztes Startjahr, z. B. 2026")
    a.set_defaults(func=cmd_abrufen)
    b = sub.add_parser("paket", help="Spieltags-Datenpaket (JSON) bauen")
    b.add_argument("--saison", type=int, required=True)
    b.add_argument("--spieltag", default="auto", help="Zahl oder 'auto' (nächster offener Spieltag)")
    b.set_defaults(func=cmd_paket)
    c = sub.add_parser("fit", help="Elo-Parameter abstimmen (intern)")
    c.add_argument("--train-bis", type=int, required=True, help="letzte Trainingssaison, z. B. 2024")
    c.add_argument("--mit-dc", action="store_true", help="zusätzlich Dixon-Coles abstimmen")
    c.set_defaults(func=cmd_fit)
    q = sub.add_parser("quoten", help="Marktwahrscheinlichkeiten ins Datenpaket eintragen (braucht ODDS_API_KEY)")
    q.add_argument("--saison", type=int, required=True)
    q.add_argument("--spieltag", default="auto")
    q.set_defaults(func=cmd_quoten)
    n = sub.add_parser("nachbericht", help="Abrechnung eines beendeten Spieltags + Textentwurf")
    n.add_argument("--saison", type=int, required=True)
    n.add_argument("--spieltag", default="letzter", help="Zahl oder 'letzter'")
    n.add_argument("--neu", action="store_true", help="vorhandenen Entwurf überschreiben")
    n.set_defaults(func=cmd_nachbericht)
    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
