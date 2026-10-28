-- Anonyme Statistik: nur Tag, Seite, Herkunfts-Domain bzw. Linkziel und eine Zahl. Keine IP, keine Kennungen.
CREATE TABLE IF NOT EXISTS aufrufe (tag TEXT NOT NULL, seite TEXT NOT NULL, quelle TEXT NOT NULL DEFAULT '', anzahl INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (tag, seite, quelle));
CREATE TABLE IF NOT EXISTS klicks (tag TEXT NOT NULL, seite TEXT NOT NULL, ziel TEXT NOT NULL, anzahl INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (tag, seite, ziel));
