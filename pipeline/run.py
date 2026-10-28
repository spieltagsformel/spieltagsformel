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
    modell = elo.EloModell(lade_parameter())
    modell.lauf(saisons)  # lernt aus allen beendeten Spielen bis jetzt
    spiele_tag = [s for s in spiele if s["spieltag"] == spieltag]
    vorhersagen = {s["id"]: modell.vorhersage(s["heim_id"], s["gast_id"]) for s in spiele_tag}
    try:
        dc_probs, dc_tore = dixon_coles_vorhersagen(saisons, args.saison, spiele_tag)
    except (ImportError, ValueError) as fehler:
        print(f"Hinweis: Dixon-Coles übersprungen ({fehler})")
        dc_probs, dc_tore = {}, {}
    daten = paket.baue_paket(args.saison, spieltag, spiele, vorsaison, modell=vorhersagen,
                             modell_version=elo.VERSION, weitere_modelle={"dc-0.2": dc_probs} if dc_probs else None,
                             erwartete_tore=dc_tore)
    ordner = f"{SPIELTAGE}/{daten['saison']}"
    os.makedirs(ordner, exist_ok=True)
    pfad = f"{ordner}/{spieltag:02d}.json"
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=1)
    print(f"Datenpaket geschrieben: {pfad}")
    for h in daten["hinweise"]:
        print("  " + h)


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
    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
