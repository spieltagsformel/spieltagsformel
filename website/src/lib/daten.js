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

const TAG = new Intl.DateTimeFormat("de-DE", { timeZone: "Europe/Berlin", weekday: "long", day: "numeric", month: "long" });
const UHR = new Intl.DateTimeFormat("de-DE", { timeZone: "Europe/Berlin", hour: "2-digit", minute: "2-digit" });

/**
 * Spiele chronologisch nach Tagen und Anstoßzeiten (Europe/Berlin):
 * [{ tag: "Freitag, 20. November", zeiten: [{ uhr: "20:30 Uhr", spiele: [...] }] }]
 * Spiele ohne Anstoßzeit stehen am Ende unter „Termin noch offen“.
 */
export function nachTagen(spiele) {
  const mit = spiele.filter((s) => s.anstoss_utc).sort((a, b) => a.anstoss_utc.localeCompare(b.anstoss_utc) || a.heim.localeCompare(b.heim));
  const ohne = spiele.filter((s) => !s.anstoss_utc);
  const tage = [];
  for (const s of mit) {
    const d = new Date(s.anstoss_utc);
    const tag = TAG.format(d);
    const uhr = UHR.format(d) + " Uhr";
    let t = tage[tage.length - 1];
    if (!t || t.tag !== tag) tage.push((t = { tag, zeiten: [] }));
    let z = t.zeiten[t.zeiten.length - 1];
    if (!z || z.uhr !== uhr) t.zeiten.push((z = { uhr, spiele: [] }));
    z.spiele.push(s);
  }
  if (ohne.length) tage.push({ tag: "Termin noch offen", zeiten: [{ uhr: "", spiele: ohne }] });
  return tage;
}

/** „20 % · 25 % · 55 %“ (Heimsieg · Remis · Auswärtssieg). */
export function drei(p) {
  return [p.p_heim, p.p_remis, p.p_gast].map((x) => `${prozent(x)} %`).join(" · ");
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

// ---------------------------------------------------------------------------
// Startseite v3 „Bühne“ (Entwurf A, freigegeben 24.11.2026)

const AUSGANG = ["heim", "remis", "gast"];

/** [Heim, Remis, Gast] in ganzen Prozent, oder null. */
export function werte(f) {
  return f ? [prozent(f.p_heim), prozent(f.p_remis), prozent(f.p_gast)] : null;
}

/** Ausgang mit dem größten Abstand zwischen Markt und Formel (d = Markt − Formel, Prozentpunkte). */
export function abstand(s) {
  const F = werte(s.modell);
  const M = werte(s.markt);
  if (!F || !M) return null;
  let i = 0;
  for (let k = 1; k < 3; k++) if (Math.abs(M[k] - F[k]) > Math.abs(M[i] - F[i])) i = k;
  return { i, ausgang: AUSGANG[i], d: M[i] - F[i], F, M };
}

/** Das Spiel für den Hero: größter Abstand Formel–Markt; ohne Marktwerte das erste Spiel mit Prognose. */
export function heldSpiel(spiele) {
  const mit = spiele.filter((s) => abstand(s));
  if (mit.length) return mit.reduce((a, b) => (Math.abs(abstand(b).d) > Math.abs(abstand(a).d) ? b : a));
  return spiele.find((s) => s.modell) ?? null;
}

export const WIDERSPRUCH_AB = 8; // Prozentpunkte

/** Zeitraum des Spieltags: „vom 27. bis 29. November“ bzw. „am 5. Dezember“. */
export function zeitraum(spiele) {
  const zeiten = spiele.map((s) => s.anstoss_utc).filter(Boolean).sort();
  if (!zeiten.length) return "";
  const T = (iso, opt) => new Intl.DateTimeFormat("de-DE", { timeZone: "Europe/Berlin", ...opt }).format(new Date(iso));
  const [a, b] = [zeiten[0], zeiten[zeiten.length - 1]];
  const ta = T(a, { day: "numeric", month: "long" });
  const tb = T(b, { day: "numeric", month: "long" });
  if (ta === tb) return `am ${ta}`;
  const ma = T(a, { month: "long" });
  return ma === T(b, { month: "long" }) ? `vom ${T(a, { day: "numeric" })}. bis ${tb}` : `vom ${ta} bis ${tb}`;
}

/** „Sa, 15:30“ */
export function kurzAnstoss(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const wt = new Intl.DateTimeFormat("de-DE", { timeZone: "Europe/Berlin", weekday: "short" }).format(d).replace(".", "");
  return `${wt}, ${UHR.format(d)}`;
}

/** Ein Satz zur Einordnung eines Spiels (Formel gegen Markt). */
export function einordnung(s) {
  const F = werte(s.modell);
  if (!F) return "";
  const H = kurz(s.heim);
  const G = kurz(s.gast);
  const fav = F.indexOf(Math.max(...F));
  const vorn = fav === 1 ? "Die Formel hält ein Remis für am wahrscheinlichsten" : `Die Formel sieht ${fav === 0 ? H : G} vorn`;
  const a = abstand(s);
  if (!a) return `${vorn}.`;
  const dH = a.M[0] - F[0];
  const dG = a.M[2] - F[2];
  if (Math.abs(dH) < 3 && Math.abs(dG) < 3) return `${vorn}, und der Markt sieht es fast genauso.`;
  const [k, wer, m, f, d] = Math.abs(dH) >= Math.abs(dG) ? [0, H, a.M[0], F[0], dH] : [2, G, a.M[2], F[2], dG];
  if (k === fav) {
    return d > 0
      ? `${vorn}. Der Markt sieht ${wer} noch deutlicher vorn: ${m} statt ${f} Prozent.`
      : `${vorn}. Der Markt ist bei ${wer} vorsichtiger: ${m} statt ${f} Prozent.`;
  }
  return d > 0
    ? `${vorn}. Der Markt traut ${wer} mehr zu: ${m} statt ${f} Prozent.`
    : `${vorn}. Der Markt traut ${wer} weniger zu: ${m} statt ${f} Prozent.`;
}

/** Markierungen für besondere Spiele: { [id]: "Topspiel" | … }, jedes Spiel höchstens eine. */
export function markierungen(spiele) {
  const mit = spiele.filter((s) => s.modell);
  const out = {};
  const setze = (s, text) => { if (s && !out[s.id]) out[s.id] = text; };
  const maxF = (s) => Math.max(...werte(s.modell));
  const plaetze = spiele.filter((s) => s.platz_heim && s.platz_gast);
  if (plaetze.length) setze(plaetze.reduce((a, b) => (b.platz_heim + b.platz_gast < a.platz_heim + a.platz_gast ? b : a)), "Topspiel");
  const held = heldSpiel(spiele);
  if (held && abstand(held) && Math.abs(abstand(held).d) >= WIDERSPRUCH_AB) setze(held, "Größter Widerspruch");
  if (mit.length) {
    setze(mit.reduce((a, b) => (maxF(b) > maxF(a) ? b : a)), "Klarster Favorit");
    setze(mit.reduce((a, b) => (maxF(b) < maxF(a) ? b : a)), "Offenstes Spiel");
  }
  return out;
}

/** Zahl mit drei Nachkommastellen und Komma (RPS, Brier). */
export function komma3(x) {
  return x.toFixed(3).replace(".", ",");
}
