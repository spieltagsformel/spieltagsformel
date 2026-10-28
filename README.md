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
| `data/modell/` | abgestimmte Modellparameter |
| `.github/workflows/` | automatische Abläufe (GitHub Actions) |

## Pipeline benutzen

Voraussetzung: Python 3.10 oder neuer, keine weiteren Pakete nötig.

```
python -m unittest discover -s tests -t .        # Tests
python -m pipeline.run abrufen --von 2019 --bis 2026   # Spiele laden und bereinigen
python -m pipeline.run fit --train-bis 2024    # Elo-Parameter abstimmen (intern, schreibt data/modell/)
python -m pipeline.run paket --saison 2026 --spieltag auto   # Datenpaket für den nächsten Spieltag (inkl. Modell)
```

Alternativ in GitHub: Actions → „Daten abrufen“ → „Run workflow“.

Quellen und Lizenzen: siehe `DATENQUELLEN.md`.

## Hinweise

- Kein Wett-Tipp-Dienst. Das 100-€-Experiment ist eine reine Rechnung.
- Datenquellen werden in jedem Beitrag genannt. OpenLigaDB-Daten stehen unter der ODbL.
- Lizenz: noch offen, bis dahin alle Rechte vorbehalten.

## Website

Statische Website mit [Astro](https://astro.build) im Ordner `website/`. Sie liest beim Bauen die Datenpakete aus `data/spieltage/`.

```
cd website
npm install
npm run dev     # lokale Vorschau
npm run build   # fertige Seite in website/dist
```

Einstellungen für Cloudflare: Stammverzeichnis `website`, Build-Befehl `npm run build`, Ausgabeordner `dist`, Node-Version 22 (siehe `website/.nvmrc`).
