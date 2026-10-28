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

/** Zahl mit einer Nachkommastelle und deutschem Komma. */
export function komma(x) {
  return x.toFixed(1).replace(".", ",");
}

/** Kurzname für Satzbausteine („Mainz leicht vorn“). */
const KURZ = {
  "SV 07 Elversberg": "Elversberg", "1. FSV Mainz 05": "Mainz", "Bayer 04 Leverkusen": "Leverkusen",
  "VfB Stuttgart": "Stuttgart", "FC Augsburg": "Augsburg", "SC Freiburg": "Freiburg",
  "Borussia Mönchengladbach": "Gladbach", "SC Paderborn 07": "Paderborn", "SV Werder Bremen": "Bremen",
  "TSG Hoffenheim": "Hoffenheim", "FC Schalke 04": "Schalke", "RB Leipzig": "Leipzig",
  "FC Bayern München": "Bayern", "Borussia Dortmund": "Dortmund", "1. FC Union Berlin": "Union",
  "1. FC Köln": "Köln", "Eintracht Frankfurt": "Frankfurt", "Hamburger SV": "HSV",
  "VfL Wolfsburg": "Wolfsburg", "1. FC Heidenheim 1846": "Heidenheim", "FC St. Pauli": "St. Pauli",
  "VfL Bochum": "Bochum", "Holstein Kiel": "Kiel", "SV Darmstadt 98": "Darmstadt",
};
export function kurz(name) {
  return KURZ[name] ?? name;
}

/**
 * Lage des Punkts auf der Skala (Entwurf B): links = Heimteam stärker, rechts = Gastteam stärker.
 * Grundlage ist der Abstand der Sieg-Wahrscheinlichkeiten; ±0,6 füllt die ganze Breite.
 */
export function skala(spiel) {
  const m = spiel.modell;
  const diff = m.p_heim - m.p_gast;
  const pos = Math.max(4, Math.min(96, 50 - (diff / 0.6) * 50));
  const staerke = Math.abs(diff);
  let label = "ausgeglichen";
  if (staerke >= 0.08) {
    const wer = diff > 0 ? kurz(spiel.heim) : kurz(spiel.gast);
    label = `${wer} ${staerke < 0.3 ? "leicht vorn" : "klar vorn"}`;
  }
  return { pos, label, zoneLinks: Math.min(pos, 50), zoneBreite: Math.abs(pos - 50) };
}
