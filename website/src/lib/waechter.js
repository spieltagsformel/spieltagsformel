// Liest beim Bauen den Stand des Modell-Wächters aus ../data/waechter (neueste Saison).
import fs from "node:fs";
import path from "node:path";

const ORDNER = path.resolve(process.cwd(), "..", "data", "waechter");

export function waechterStand() {
  if (!fs.existsSync(ORDNER)) return null;
  const dateien = fs.readdirSync(ORDNER).filter((d) => d.endsWith(".json")).sort();
  if (!dateien.length) return null;
  return JSON.parse(fs.readFileSync(path.join(ORDNER, dateien[dateien.length - 1]), "utf-8"));
}
