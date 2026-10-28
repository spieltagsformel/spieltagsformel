"""Grafiken erzeugen.

    python -m grafik.run spieltag --paket data/spieltage/2026-27/08.json
    python -m grafik.run staerke --saison 2026
    python -m grafik.run kontostand-beispiel      (nur zum Testen, Beispieldaten)
"""
import argparse
import glob
import json
import os

from . import kontostand, spieltag, staerke

AUSGABE = "grafik/ausgabe"


def neuestes_paket():
    pakete = sorted(glob.glob("data/spieltage/*/*.json"))
    return pakete[-1] if pakete else None


def main(argv=None):
    p = argparse.ArgumentParser(prog="grafik")
    sub = p.add_subparsers(dest="art", required=True)
    a = sub.add_parser("spieltag")
    a.add_argument("--paket", default=None)
    b = sub.add_parser("staerke")
    b.add_argument("--saison", type=int, required=True)
    sub.add_parser("kontostand-beispiel")
    args = p.parse_args(argv)

    if args.art == "spieltag":
        pfad = args.paket or neuestes_paket()
        paket = json.load(open(pfad, encoding="utf-8"))
        for f in ("4x5", "9x16"):
            print(spieltag.zeichne(paket, f, f"{AUSGABE}/spieltag-{paket['spieltag']:02d}-{f}.png"))
    elif args.art == "staerke":
        from pipeline.run import lade_parameter, lade_saisons
        from pipeline.paket import naechster_spieltag
        saisons = lade_saisons(args.saison)
        liste, nu = staerke.werte(saisons, lade_parameter(), args.saison)
        tag = naechster_spieltag(saisons[args.saison])
        saison_txt = f"{args.saison}/{str(args.saison + 1)[-2:]}"
        kopf = f"Spieltag {tag:02d} · {saison_txt} · Stärke der Teams" if tag else f"Saison {saison_txt} · Stärke der Teams"
        stand = max(s["anstoss_utc"] for s in saisons[args.saison] if s["beendet"])
        for f in ("4x5", "9x16"):
            print(staerke.zeichne(liste, nu, kopf, stand, f, f"{AUSGABE}/staerke-{f}.png"))
    else:
        import random
        random.seed(3)
        verlauf, k = [], {"A": 100.0, "B": 100.0, "C": 100.0}
        for t in range(0, 13):
            if t:
                k = {s: max(0, w + random.uniform(-6, 7)) for s, w in k.items()}
            verlauf.append({"spieltag": t, **k})
        print(kontostand.zeichne(verlauf, "Beispieldaten · 100-€-Experiment · Kontostand",
                                 "Beispieldaten, nicht veröffentlichen", "4x5", "/tmp/kontostand-beispiel.png", beispiel=True))


if __name__ == "__main__":
    main()
