// Liest beim Bauen der Website die Spieltags-Datenpakete aus ../data/spieltage.
import fs from "node:fs";
import path from "node:path";

const ORDNER = path.resolve(process.cwd(), "..", "data", "spieltage");

/** Alle Pakete, sortiert nach Saison und Spieltag (neuestes zuletzt). */
export function allePakete() {
  if (!fs.existsSync(ORDNER)) return [];
  const pakete = [];
  for (const saison of fs.readdirSync(ORDNER).sort()) {
    const sOrdner = path.join(ORDNER, saison);
    if (!fs.statSync(sOrdner).isDirectory()) continue;
    for (const datei of fs.readdirSync(sOrdner).filter((d) => d.endsWith(".json")).sort()) {
      pakete.push(JSON.parse(fs.readFileSync(path.join(sOrdner, datei), "utf-8")));
    }
  }
  return pakete;
}

export function neuestesPaket() {
  const p = allePakete();
  return p.length ? p[p.length - 1] : null;
}

const FORMAT = new Intl.DateTimeFormat("de-DE", {
  timeZone: "Europe/Berlin",
  weekday: "short",
  day: "2-digit",
  month: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
});

export function anstoss(isoUtc) {
  if (!isoUtc) return "Anstoß noch offen";
  return FORMAT.format(new Date(isoUtc)) + " Uhr";
}

export function prozent(p) {
  return Math.round(p * 100);
}

export const REGEL_TEXT = { heim: "Heimsieg", remis: "Remis", gast: "Auswärtssieg" };
