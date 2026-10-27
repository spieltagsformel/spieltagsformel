# Spieltagsformel

Bundesliga in Zahlen. Ein Prognosemodell sagt jeden Spieltag voraus, die Prognosen werden vor Anpfiff mit Zeitstempel eingefroren und danach offen abgerechnet. Dazu ein rechnerisches 100-€-Experiment (kein echtes Geld) und ein wöchentlicher Newsletter.

Website: spieltagsformel.de (im Aufbau)

## Status

Phase 0 – Fundament. Datenpipeline, Modell und Website entstehen gerade.

## Ordner

| Ordner | Inhalt |
|---|---|
| `data/raw/` | Rohdaten der Quellen (nicht im Repo, siehe `.gitignore`) |
| `data/clean/` | bereinigte Daten |
| `data/manuell/` | von Hand gepflegte Angaben (z. B. Ausfälle) |
| `data/spieltage/` | Spieltags-Datenpakete (JSON) und eingefrorene Prognosen |
| `pipeline/` | Python-Skripte für Abruf, Bereinigung, Modell |
| `.github/workflows/` | automatische Abläufe (GitHub Actions) |

## Hinweise

- Kein Wett-Tipp-Dienst. Das 100-€-Experiment ist eine reine Rechnung.
- Datenquellen werden in jedem Beitrag genannt. OpenLigaDB-Daten stehen unter der ODbL.
- Lizenz: noch offen, bis dahin alle Rechte vorbehalten.
