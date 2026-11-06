// Vereinsfarben und Grundform je Verein für das Spieltags-Design v2 (freigegeben 6.11.2026).
// Keine Vereinslogos: nur eine von vier Grundformen (Kreis, Oval, Rechteck, Schild),
// gefüllt mit den Vereinsfarben als Längsstreifen.
// Farben: Vereinsangaben/Wikipedia, Farbtöne angenähert.
// Grundform: an der Außenkontur des Wappens orientiert, nie dessen Silhouette oder Inhalt.
// Anwaltliche Kurzprüfung in KW 51 (SF-28). Falls abgeraten: EINHEITSFORM = true setzt alle auf „schild“.

export const EINHEITSFORM = false;

export const FORMEN = ["kreis", "oval", "rechteck", "schild"];

export const VEREINE = {
  "FC Bayern München": { form: "kreis", farben: ["#DC052D", "#FFFFFF"] },
  "Borussia Dortmund": { form: "kreis", farben: ["#FDE100", "#000000"] },
  "SC Freiburg": { form: "oval", farben: ["#FFFFFF", "#D50F1E"] },
  "RB Leipzig": { form: "schild", farben: ["#DD0741", "#FFFFFF"] },
  "SV Werder Bremen": { form: "schild", farben: ["#1D9053", "#FFFFFF"] },
  "Bayer 04 Leverkusen": { form: "schild", farben: ["#E32221", "#000000"] },
  "SV 07 Elversberg": { form: "kreis", farben: ["#000000", "#FFFFFF"] },
  "Eintracht Frankfurt": { form: "kreis", farben: ["#E1000F", "#000000", "#FFFFFF"] },
  "1. FSV Mainz 05": { form: "kreis", farben: ["#C3141E", "#FFFFFF"] },
  "FC Augsburg": { form: "schild", farben: ["#BA3733", "#46714D", "#FFFFFF"] },
  "VfB Stuttgart": { form: "schild", farben: ["#FFFFFF", "#E32219"] },
  "TSG Hoffenheim": { form: "schild", farben: ["#1C63B7", "#FFFFFF"] },
  "1. FC Köln": { form: "schild", farben: ["#ED1C24", "#FFFFFF"] },
  "SC Paderborn 07": { form: "kreis", farben: ["#005CA9", "#000000"] },
  "Hamburger SV": { form: "rechteck", farben: ["#0A3F86", "#FFFFFF", "#000000"] },
  "1. FC Union Berlin": { form: "schild", farben: ["#D4011D", "#FFFFFF"] },
  "FC Schalke 04": { form: "kreis", farben: ["#004D9D", "#FFFFFF"] },
  "Borussia Mönchengladbach": { form: "schild", farben: ["#000000", "#FFFFFF", "#00A651"] },
};

const STANDARD = { form: "schild", farben: ["#5A5A5A", "#FFFFFF"] };

/** Form und Farben für einen Vereinsnamen (unbekannte Vereine: neutrales Grau). */
export function verein(name) {
  const v = VEREINE[name] ?? STANDARD;
  return EINHEITSFORM ? { ...v, form: "schild" } : v;
}
