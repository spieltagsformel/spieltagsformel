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

Voraussetzung: Python 3.10 oder neuer und `pip install -r requirements.txt` (numpy, scipy für das Dixon-Coles-Modell).

```
python -m unittest discover -s tests -t .        # Tests
python -m pipeline.run abrufen --von 2019 --bis 2026   # Spiele laden und bereinigen
python -m pipeline.run fit --train-bis 2024 --mit-dc   # Elo- und Dixon-Coles-Parameter abstimmen (intern, schreibt data/modell/)
python -m pipeline.run paket --saison 2026 --spieltag auto   # Datenpaket für den nächsten Spieltag (inkl. Modell)
```

Alternativ in GitHub: Actions → „Daten abrufen“ → „Run workflow“.

Quellen und Lizenzen: siehe `DATENQUELLEN.md`.

## Hinweise

- Kein Wett-Tipp-Dienst. Das 100-€-Experiment ist eine reine Rechnung.
- Datenquellen werden in jedem Beitrag genannt. OpenLigaDB-Daten stehen unter der ODbL.
- Lizenz: noch offen, bis dahin alle Rechte vorbehalten.

## Grafiken

Grafiken im Datenblatt-Stil mit matplotlib (`grafik/`), je als Post (4:5) und Story (9:16):

```
python -m grafik.run spieltag                  # „Die Formel sagt …“ für das neueste Datenpaket
python -m grafik.run staerke --saison 2026     # Stärke der Teams (Elo relativ zum Ligaschnitt)
```

Die Bilder landen in `grafik/ausgabe/`. Der Workflow „Daten abrufen“ erzeugt sie automatisch mit. Jede neue Grafikart muss vor dem Einsatz mindestens 9 von 10 Merkmalen aus `grafik/QUALITAET.md` erfüllen.

## Website

Statische Website mit [Astro](https://astro.build) im Ordner `website/`. Sie liest beim Bauen die Datenpakete aus `data/spieltage/`.

```
cd website
npm install
npm run dev     # lokale Vorschau
npm run build   # fertige Seite in website/dist
```

Die Seite läuft als Cloudflare Worker mit statischen Dateien (`website/wrangler.jsonc`). Der Worker übernimmt nur `/api/*`:

| Pfad | Zweck |
|---|---|
| `POST /api/kontakt` | Kontaktformular → E-Mail an spieltagsformel@gmail.com (Cloudflare Email Routing) |
| `POST /api/aufruf` | anonyme Zählung von Seitenaufrufen (Tag, Seite, Herkunfts-Domain) |
| `POST /api/klick` | anonyme Zählung von Klicks auf externe Links (Tag, Seite, Domain + Pfad) |

Keine Cookies, keine IP-Adressen, keine Kennungen. Tabellen: `website/worker/schema.sql` (D1-Datenbank `spieltagsformel`).

Einstellungen für Workers Builds: Stammverzeichnis `website`, Build-Befehl `npm run build`, Deploy-Befehl `npx wrangler deploy`, Node-Version 22 (siehe `website/.nvmrc`).
