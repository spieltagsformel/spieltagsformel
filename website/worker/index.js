// Worker für spieltagsformel.de
// - liefert die statische Astro-Seite aus (ASSETS)
// - POST /api/kontakt  : Kontaktformular → E-Mail an die Redaktion
// - POST /api/aufruf   : anonyme Zählung eines Seitenaufrufs
// - POST /api/klick    : anonyme Zählung eines Klicks auf einen externen Link
// Es werden keine IP-Adressen, Kennungen oder Cookies gespeichert.

const MAX = { name: 100, email: 200, betreff: 150, nachricht: 5000 };

function heute() {
  return new Date().toISOString().slice(0, 10);
}

function weiter(url, pfad) {
  return Response.redirect(new URL(pfad, url).toString(), 303);
}

function seitePfad(wert) {
  if (typeof wert !== "string" || !wert.startsWith("/")) return null;
  return wert.split("?")[0].split("#")[0].slice(0, 200) || "/";
}

function nurDomain(wert, eigene) {
  try {
    const u = new URL(wert);
    if (u.hostname === eigene) return "";
    return u.hostname.replace(/^www\./, "").slice(0, 100);
  } catch {
    return "";
  }
}

function linkZiel(wert) {
  try {
    const u = new URL(wert);
    if (!["http:", "https:", "mailto:"].includes(u.protocol)) return null;
    if (u.protocol === "mailto:") return "mailto";
    // Nur Domain + Pfad, keine Parameter (dort stecken oft Kennungen)
    return (u.hostname.replace(/^www\./, "") + u.pathname).slice(0, 200);
  } catch {
    return null;
  }
}

// UTM-Werte: nur kurze, einfache Kennungen (Buchstaben, Ziffern, _ . -), sonst leer
function utmWert(wert) {
  return typeof wert === "string" && /^[A-Za-z0-9_.-]{1,40}$/.test(wert) ? wert.toLowerCase() : "";
}

async function zaehle(env, sql, werte) {
  if (!env.DB) return;
  await env.DB.prepare(sql).bind(...werte).run();
}

async function leseJson(request) {
  try {
    const text = await request.text();
    if (text.length > 2000) return null;
    return JSON.parse(text);
  } catch {
    return null;
  }
}

async function kontakt(request, env) {
  const url = new URL(request.url);
  let form;
  try {
    form = await request.formData();
  } catch {
    return weiter(url, "/kontakt?fehler=1");
  }
  const feld = (n) => String(form.get(n) ?? "").trim();
  // Zeilenumbrüche in Einzeilern entfernen (Betreff, Name, E-Mail landen in E-Mail-Kopfzeilen)
  const einzeilig = (n) => feld(n).replace(/[\r\n]+/g, " ");
  // Spam-Schutz: verstecktes Feld muss leer sein, Formular nicht schneller als 3 Sekunden ausgefüllt
  if (feld("website") !== "") return weiter(url, "/kontakt/danke");
  const start = Number(feld("t"));
  if (start && Date.now() - start < 3000) return weiter(url, "/kontakt/danke");

  const name = einzeilig("name").slice(0, MAX.name);
  const email = einzeilig("email").slice(0, MAX.email);
  const betreff = einzeilig("betreff").slice(0, MAX.betreff) || "Nachricht über das Kontaktformular";
  const nachricht = feld("nachricht").slice(0, MAX.nachricht);
  const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  if (!emailOk || nachricht.length < 10) return weiter(url, "/kontakt?fehler=1");

  try {
    await env.KONTAKT.send({
      from: { email: env.ABSENDER, name: "Spieltagsformel Kontaktformular" },
      to: "spieltagsformel@gmail.com",
      replyTo: { email, name: name || email },
      subject: `[Kontakt] ${betreff}`,
      text: `Name: ${name || "-"}\nE-Mail: ${email}\nBetreff: ${betreff}\n\n${nachricht}\n`,
    });
  } catch (fehler) {
    console.error("Kontaktformular: Versand fehlgeschlagen", fehler?.code ?? fehler?.message);
    return weiter(url, "/kontakt?fehler=2");
  }
  return weiter(url, "/kontakt/danke");
}

async function aufruf(request, env) {
  const daten = await leseJson(request);
  const seite = daten && seitePfad(daten.seite);
  if (!seite) return new Response(null, { status: 204 });
  const quelle = nurDomain(daten.quelle ?? "", new URL(request.url).hostname);
  await zaehle(env,
    "INSERT INTO aufrufe (tag, seite, quelle, anzahl) VALUES (?, ?, ?, 1) ON CONFLICT (tag, seite, quelle) DO UPDATE SET anzahl = anzahl + 1",
    [heute(), seite, quelle]);
  // Kampagnen-Kennzeichnung (z. B. aus dem Newsletter): nur Summen pro Tag, Seite und Kennung
  const utm = daten.utm && typeof daten.utm === "object" ? daten.utm : {};
  const [us, um, uc] = [utmWert(utm.s), utmWert(utm.m), utmWert(utm.c)];
  if (us || um || uc) {
    await zaehle(env,
      "INSERT INTO kampagnen (tag, seite, utm_source, utm_medium, utm_campaign, anzahl) VALUES (?, ?, ?, ?, ?, 1) ON CONFLICT (tag, seite, utm_source, utm_medium, utm_campaign) DO UPDATE SET anzahl = anzahl + 1",
      [heute(), seite, us, um, uc]);
  }
  return new Response(null, { status: 204 });
}

async function klick(request, env) {
  const daten = await leseJson(request);
  const seite = daten && seitePfad(daten.seite);
  const ziel = daten && linkZiel(daten.ziel);
  if (!seite || !ziel) return new Response(null, { status: 204 });
  await zaehle(env,
    "INSERT INTO klicks (tag, seite, ziel, anzahl) VALUES (?, ?, ?, 1) ON CONFLICT (tag, seite, ziel) DO UPDATE SET anzahl = anzahl + 1",
    [heute(), seite, ziel]);
  return new Response(null, { status: 204 });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname.startsWith("/api/")) {
      if (request.method !== "POST") return new Response("Methode nicht erlaubt", { status: 405 });
      try {
        if (url.pathname === "/api/kontakt") return await kontakt(request, env);
        if (url.pathname === "/api/aufruf") return await aufruf(request, env);
        if (url.pathname === "/api/klick") return await klick(request, env);
      } catch (fehler) {
        console.error("API-Fehler", url.pathname, fehler?.message);
        return new Response(null, { status: 204 });
      }
      return new Response("Nicht gefunden", { status: 404 });
    }
    return env.ASSETS.fetch(request);
  },
};
