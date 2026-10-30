-- The triviela-beta database (Cloudflare D1, id 28b9326e-e80a-433a-ab24-64c0c11712fe), as it stands on Oct 30, 2026,
-- so it can be rebuilt (the audit's small item). The three Pages Functions in functions/api/ write here:
--   marks    mark.js    Morg's flag, unflag, lock and unlock taps from the beta, read by tools/vet.py marks (synced marks the rows it took)
--   results  result.js  one finished board per row, anonymous (no name, device or IP), read by tools/results.py.
--                       token is the board's own random mark, unique, so a retry after a lost reply is dropped (INSERT OR IGNORE)
--   texts    text.js    a batch of Morg's text edits from the in-game editor, read by tools/textedits.py (applied marks the batches it took)
CREATE TABLE marks (id INTEGER PRIMARY KEY AUTOINCREMENT, card TEXT NOT NULL, hash TEXT NOT NULL, mark TEXT NOT NULL CHECK (mark IN ('flag','unflag','lock','unlock')), note TEXT NOT NULL DEFAULT '', snap TEXT NOT NULL DEFAULT '', day INTEGER, at TEXT NOT NULL, synced INTEGER NOT NULL DEFAULT 0);
CREATE INDEX marks_card ON marks(card, id);
CREATE TABLE results (id INTEGER PRIMARY KEY AUTOINCREMENT, day INTEGER NOT NULL, score INTEGER NOT NULL, ids TEXT NOT NULL, res TEXT NOT NULL, path TEXT NOT NULL, host TEXT NOT NULL, at TEXT NOT NULL, token TEXT);
CREATE UNIQUE INDEX results_token ON results(token);
CREATE TABLE texts (id INTEGER PRIMARY KEY AUTOINCREMENT, body TEXT NOT NULL, host TEXT, at TEXT NOT NULL, applied INTEGER NOT NULL DEFAULT 0);
