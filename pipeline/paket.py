"""Baut das Spieltags-Datenpaket (JSON), die Schnittstelle zu Modell und Redaktion."""
from datetime import datetime, timezone

from .tabelle import berechne_tabelle, start_tabelle, form, tabellenplatz_regel

QUELLEN = [{
    "name": "OpenLigaDB",
    "url": "https://www.openligadb.de",
    "lizenz": "ODbL 1.0",
}]


def naechster_spieltag(spiele):
    """Kleinster Spieltag mit mindestens einem noch nicht beendeten Spiel."""
    offen = [s["spieltag"] for s in spiele if not s["beendet"]]
    return min(offen) if offen else None


def baue_paket(saison, spieltag, spiele, spiele_vorsaison=None, erstellt=None, modell=None, modell_version=None,
               weitere_modelle=None, erwartete_tore=None):
    """saison = Startjahr (2026 für 2026/27). modell = {Spiel-ID: (p_heim, p_remis, p_gast)} oder None
    (Hauptmodell). weitere_modelle = {Version: {Spiel-ID: (p_heim, p_remis, p_gast)}} zum Vergleich.
    erwartete_tore = {Spiel-ID: (heim, gast)}."""
    dieser = [s for s in spiele if s["spieltag"] == spieltag]
    if not dieser:
        raise ValueError(f"Kein Spieltag {spieltag} in den Daten der Saison {saison}")
    hinweise = []
    if spieltag == 1:
        if not spiele_vorsaison:
            raise ValueError("Für Spieltag 1 werden die Daten der Vorsaison benötigt")
        tab = start_tabelle(spiele, spiele_vorsaison)
        if any(z.get("aufsteiger_platzhalter") for z in tab.values()):
            hinweise.append("[PRÜFEN: Aufsteiger haben nur einen Platzhalter-Platz in der Starttabelle]")
    else:
        tab = berechne_tabelle(spiele, vor_spieltag=spieltag)
        unfertig = [s["id"] for s in spiele if s["spieltag"] < spieltag and not s["beendet"]]
        if unfertig:
            hinweise.append(f"[PRÜFEN: {len(unfertig)} Spiel(e) früherer Spieltage nicht beendet (Nachholspiele?)]")
    spielliste = []
    for s in sorted(dieser, key=lambda s: (s["anstoss_utc"] or "", s["id"])):
        ph, pg = tab[s["heim_id"]]["platz"], tab[s["gast_id"]]["platz"]
        spielliste.append({
            "id": s["id"],
            "anstoss_utc": s["anstoss_utc"],
            "anstoss_lokal": s["anstoss_lokal"],
            "heim": s["heim"],
            "gast": s["gast"],
            "tv": None,
            "platz_heim": ph,
            "platz_gast": pg,
            "form_heim": form(spiele, s["heim_id"], spieltag),
            "form_gast": form(spiele, s["gast_id"], spieltag),
            "vergleich": {"tabellenplatz": tabellenplatz_regel(ph, pg), "community": None},
            "modell": ({"version": modell_version, "p_heim": round(modell[s["id"]][0], 4),
                        "p_remis": round(modell[s["id"]][1], 4), "p_gast": round(modell[s["id"]][2], 4)}
                       if modell and s["id"] in modell else None),
            "weitere_modelle": {v: {"p_heim": round(w[s["id"]][0], 4), "p_remis": round(w[s["id"]][1], 4),
                                    "p_gast": round(w[s["id"]][2], 4)}
                                for v, w in (weitere_modelle or {}).items() if s["id"] in w},
            "erwartete_tore": ({"heim": round(erwartete_tore[s["id"]][0], 2), "gast": round(erwartete_tore[s["id"]][1], 2)}
                               if erwartete_tore and s["id"] in erwartete_tore else None),
            "markt": None,
            "ergebnis": {"heim": s["tore_heim"], "gast": s["tore_gast"]} if s["beendet"] else None,
        })
    if len(spielliste) != 9:
        hinweise.append(f"[PRÜFEN: {len(spielliste)} Spiele statt 9 an diesem Spieltag]")
    return {
        "saison": f"{saison}-{str(saison + 1)[-2:]}",
        "spieltag": spieltag,
        "erstellt": erstellt or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "quellen": QUELLEN,
        "hinweise": hinweise,
        "tabelle_vor_spieltag": [
            {"platz": z["platz"], "team": z["team"], "spiele": z["spiele"], "punkte": z["punkte"],
             "tore": z["tore"], "gegentore": z["gegentore"]}
            for z in sorted(tab.values(), key=lambda z: z["platz"])
        ],
        "spiele": spielliste,
    }


EINGEFRORENE_FELDER = ("modell", "weitere_modelle", "erwartete_tore", "markt", "vergleich",
                       "platz_heim", "platz_gast", "form_heim", "form_gast")


def einfrieren(neu, alt, jetzt_iso):
    """Übernimmt für Spiele, die schon angepfiffen sind (oder bereits eingefroren waren), alle
    Prognosewerte aus dem alten Paket. So ändert ein späterer Neubau nie eine Prognose nachträglich."""
    if not alt:
        return neu
    alte = {s["id"]: s for s in alt.get("spiele", [])}
    for s in neu["spiele"]:
        a = alte.get(s["id"])
        if not a:
            continue
        begonnen = bool(a.get("anstoss_utc")) and a["anstoss_utc"].replace("Z", "+00:00") <= jetzt_iso
        if a.get("eingefroren") or begonnen:
            for f in EINGEFRORENE_FELDER:
                if f in a:
                    s[f] = a[f]
            s["eingefroren"] = a.get("eingefroren") or alt.get("erstellt")
    return neu


def bis_stichtag(saisons, stichtag_iso):
    """Kopie der Saisons, in der nur Spiele vor dem Stichtag als beendet gelten (kein Blick nach vorn)."""
    kopie = {}
    for jahr, spiele in saisons.items():
        kopie[jahr] = [s if (s["anstoss_utc"] and s["anstoss_utc"] < stichtag_iso)
                       else dict(s, beendet=False, tore_heim=None, tore_gast=None) for s in spiele]
    return kopie
