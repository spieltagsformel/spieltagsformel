"""Lesen und Schreiben der bereinigten Spieldaten (CSV)."""
import csv
import os

SPALTEN = ["id", "saison", "spieltag", "anstoss_utc", "anstoss_lokal", "heim_id", "heim", "gast_id", "gast",
           "beendet", "tore_heim", "tore_gast", "ht_heim", "ht_gast"]
GANZZAHL = {"id", "saison", "spieltag", "heim_id", "gast_id", "tore_heim", "tore_gast", "ht_heim", "ht_gast"}


def schreibe_csv(pfad, zeilen):
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    with open(pfad, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SPALTEN)
        w.writeheader()
        for z in sorted(zeilen, key=lambda z: (z["spieltag"], z["anstoss_utc"] or "", z["id"])):
            w.writerow({k: ("" if z[k] is None else z[k]) for k in SPALTEN})


def lese_csv(pfad):
    zeilen = []
    with open(pfad, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            z = {}
            for k in SPALTEN:
                v = r[k]
                if k == "beendet":
                    z[k] = v == "True"
                elif v == "":
                    z[k] = None
                elif k in GANZZAHL:
                    z[k] = int(v)
                else:
                    z[k] = v
            zeilen.append(z)
    return zeilen
