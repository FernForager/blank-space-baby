// The beta's flag and lock keys (Morg, Oct 16, 2026). A Cloudflare Pages Function, served at /api/mark.
//   POST {card, hash, mark, note, day, snap}  records one of Morg's marks: flag, unflag, lock or unlock
//   GET  ?card=<deck id>:<index>              says whether that card is flagged or locked right now
// Marks go to the triviela-beta database (the DB binding in wrangler.toml), into its marks table, oldest first.
// Trivelle reads them from there (tools/vet.py marks). Only preview links take marks: the real site never does.
const MARKS = new Set(['flag', 'unflag', 'lock', 'unlock']);
const CARD = /^[a-z0-9-]{1,30}:\d{1,5}$/, HASH = /^[0-9a-f]{10}$/;

const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json', 'cache-control': 'no-store' } });
function refuse(request, env) {
  const url = new URL(request.url);
  if (!url.hostname.endsWith('.blank-space-baby.pages.dev')) return json({ error: 'marks are for the beta only' }, 403);
  if (!env.DB) return json({ error: 'the database is not connected (no DB binding)' }, 503);
  return null;
}

export async function onRequestPost({ request, env }) {
  const no = refuse(request, env); if (no) return no;
  const origin = request.headers.get('origin');
  if (origin && origin !== new URL(request.url).origin) return json({ error: 'marks come from the game itself' }, 403);
  let d;
  try { d = await request.json(); } catch (e) { return json({ error: 'not JSON' }, 400); }
  if (!d || typeof d !== 'object') return json({ error: 'not a mark' }, 400);
  if (!CARD.test(String(d.card || '')) || !HASH.test(String(d.hash || '')) || !MARKS.has(d.mark)) return json({ error: 'not a mark' }, 400);
  const note = typeof d.note === 'string' ? d.note.trim().slice(0, 500) : '';
  const snap = JSON.stringify(d.snap && typeof d.snap === 'object' ? d.snap : {}).slice(0, 2000);
  const day = Number.isInteger(d.day) && d.day >= 0 && d.day < 100000 ? d.day : null;
  await env.DB.prepare('INSERT INTO marks (card, hash, mark, note, snap, day, at) VALUES (?, ?, ?, ?, ?, ?, ?)')
    .bind(d.card, d.hash, d.mark, note, snap, day, new Date().toISOString()).run();
  return json({ ok: true });
}

export async function onRequestGet({ request, env }) {
  const no = refuse(request, env); if (no) return no;
  const card = new URL(request.url).searchParams.get('card') || '';
  if (!CARD.test(card)) return json({ error: 'not a card' }, 400);
  const { results } = await env.DB.prepare('SELECT mark FROM marks WHERE card = ? ORDER BY id').bind(card).all();
  let flag = false, lock = false;   // the latest of each pair wins
  for (const r of results) { if (r.mark === 'flag' || r.mark === 'unflag') flag = r.mark === 'flag'; else lock = r.mark === 'lock'; }
  return json({ flag, lock });
}
