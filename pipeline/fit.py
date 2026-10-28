"""Abstimmung der Elo-Parameter (internes Werkzeug, KEIN öffentlicher Backtest).

Ablauf: Die erste Saison dient nur zum Einlaufen der Werte. Die Parameter werden auf den
Saisons bis `--train-bis` gewählt (kleinster RPS) und danach unverändert auf der folgenden
Saison geprüft. Ergebnis: data/modell/elo_params.json
"""
import itertools
import json
import os

from .elo import EloModell, STANDARD
from . import metriken

GITTER = {
    "k": [10, 15, 20, 25, 30, 40],
    "heimvorteil": [40, 55, 65, 75, 90],
    "regress": [0.1, 0.25, 0.4],
    "aufsteiger": [1350, 1400, 1450],
    "nu": [0.6, 0.7, 0.8, 0.9],
}


def bewerte(saisons, params, von, bis):
    protokoll = EloModell(params).lauf(saisons)
    teil = [x for x in protokoll if von <= x["saison"] <= bis]
    return metriken.zusammenfassung(teil), teil


def suche(saisons, train_von, train_bis):
    bester = None
    namen = list(GITTER)
    for werte in itertools.product(*(GITTER[n] for n in namen)):
        params = dict(zip(namen, werte))
        z, _ = bewerte(saisons, params, train_von, train_bis)
        if bester is None or z["rps"] < bester[0]["rps"]:
            bester = (z, params)
    return bester


def lauf(saisons, train_bis, ausgabe="data/modell/elo_params.json"):
    jahre = sorted(saisons)
    erste = jahre[0]
    train_von = erste + 1
    if train_bis >= jahre[-1] or train_bis < train_von:
        raise ValueError("train_bis muss zwischen der zweiten und der vorletzten Saison liegen")
    z_train, params = suche(saisons, train_von, train_bis)
    test_saison = train_bis + 1
    z_test, teil = bewerte(saisons, params, test_saison, test_saison)
    z_std, _ = bewerte(saisons, STANDARD, test_saison, test_saison)
    # Referenz ohne Teamwissen: Häufigkeiten aus dem Trainingszeitraum
    _, train_teil = bewerte(saisons, params, train_von, train_bis)
    h = metriken.haeufigkeiten(train_teil)
    ref = [dict(x, referenz=h) for x in teil]
    z_ref = metriken.zusammenfassung(ref, "referenz")
    bericht = {
        "einlaufen": erste, "training": [train_von, train_bis], "test": test_saison,
        "parameter": params, "training_ergebnis": z_train, "test_ergebnis": z_test,
        "test_mit_standardwerten": z_std, "test_nur_haeufigkeiten": z_ref,
        "haeufigkeiten_training": {"heim": h[0], "remis": h[1], "gast": h[2]},
    }
    os.makedirs(os.path.dirname(ausgabe), exist_ok=True)
    with open(ausgabe, "w", encoding="utf-8") as f:
        json.dump({"version": "elo-0.1", "parameter": params}, f, indent=1)
    with open(ausgabe.replace(".json", "_bericht.json"), "w", encoding="utf-8") as f:
        json.dump(bericht, f, indent=1, ensure_ascii=False)
    return bericht


# ---------- Dixon-Coles v0.2 ----------
GITTER_DC = {"xi": [0.001, 0.002, 0.003, 0.005], "ridge": [1.0, 3.0, 6.0, 10.0, 20.0]}


def lauf_dc(saisons, train_bis, ausgabe="data/modell/dc_params.json", elo_params=None):
    """Wählt xi und ridge auf den Saisons nach der ersten bis train_bis (Spieltag für Spieltag,
    nur Vergangenheit) und prüft auf der folgenden Saison, im Vergleich mit Elo auf denselben Spielen."""
    from . import dixon_coles
    jahre = sorted(saisons)
    train_von, test = jahre[0] + 1, train_bis + 1
    ergebnisse = []
    for xi in GITTER_DC["xi"]:
        for ridge in GITTER_DC["ridge"]:
            prot = dixon_coles.walk_forward(saisons, {"xi": xi, "ridge": ridge}, von=train_von, bis=train_bis)
            ergebnisse.append((metriken.zusammenfassung(prot), {"xi": xi, "ridge": ridge}))
    z_train, params = min(ergebnisse, key=lambda e: e[0]["rps"])
    prot_test = dixon_coles.walk_forward(saisons, params, von=test, bis=test)
    elo_prot = [x for x in EloModell(elo_params).lauf(saisons) if x["saison"] == test]
    ids = {x["id"] for x in prot_test}
    elo_gleich = [x for x in elo_prot if x["id"] in ids]
    mittel = [dict(x, p=tuple((a + b) / 2 for a, b in zip(x["p"], y["p"])))
              for x, y in zip(sorted(prot_test, key=lambda x: x["id"]), sorted(elo_gleich, key=lambda x: x["id"]))]
    bericht = {
        "training": [train_von, train_bis], "test": test, "parameter": params,
        "gitter": [{"parameter": p, "rps": z["rps"]} for z, p in ergebnisse],
        "training_ergebnis": z_train,
        "test_dixon_coles": metriken.zusammenfassung(prot_test),
        "test_elo": metriken.zusammenfassung(elo_gleich),
        "test_mittel_aus_beiden": metriken.zusammenfassung(mittel),
        "remis_als_favorit": {
            "dixon_coles": sum(1 for x in prot_test if max(range(3), key=lambda i: x["p"][i]) == 1) / len(prot_test),
            "elo": sum(1 for x in elo_gleich if max(range(3), key=lambda i: x["p"][i]) == 1) / len(elo_gleich),
        },
    }
    os.makedirs(os.path.dirname(ausgabe), exist_ok=True)
    with open(ausgabe, "w", encoding="utf-8") as f:
        json.dump({"version": dixon_coles.VERSION, "parameter": params}, f, indent=1)
    with open(ausgabe.replace(".json", "_bericht.json"), "w", encoding="utf-8") as f:
        json.dump(bericht, f, indent=1, ensure_ascii=False)
    return bericht
