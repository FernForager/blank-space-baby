// The playtest's anonymous results (Morg, Oct 19, 2026). A Cloudflare Pages Function, served at /api/result.
//   POST {day, ids, res, path}   records one finished board: the puzzle (day 0 is #1), its 9 card ids in board order (15 before Oct 27, 2026),
//                                each one's result (1 right, 2 wrong) and the order they were tapped
// Nothing about who played: no name, no device id, no IP stored. Rows go to the triviela-beta database (the DB binding in
// wrangler.toml), into its results table, and tools/results.py sums them up. The beta's rows say host 'beta', so Morg's own
// testing can be told apart from the players'.
const CARD = /^[a-z0-9-]{1,30}:\d{1,5}$/;
const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json', 'cache-control': 'no-store' } });

export async function onRequestPost({ request, env }) {
  const url = new URL(request.url), host = url.hostname;
  const where = /(^|\.)triviela\.net$/.test(host) ? 'real' : host.endsWith('.blank-space-baby.pages.dev') ? 'beta' : null;
  if (!where) return json({ error: 'results come from the game itself' }, 403);
  const origin = request.headers.get('origin');
  if (origin && origin !== url.origin) return json({ error: 'results come from the game itself' }, 403);
  if (!env.DB) return json({ error: 'the database is not connected (no DB binding)' }, 503);
  let d;
  try { d = await request.json(); } catch (e) { return json({ error: 'not JSON' }, 400); }
  const n = d && Array.isArray(d.ids) ? d.ids.length : 0;   // nine cards a day since Oct 27, 2026, and a 15-card day finished earlier can still arrive
  const ok = (n === 9 || n === 15) && typeof d === 'object' && Number.isInteger(d.day) && d.day >= 0 && d.day < 100000 &&
    d.ids.every(x => typeof x === 'string' && CARD.test(x)) && new Set(d.ids).size === n &&   // n different cards (the audit, Oct 30, 2026)
    Array.isArray(d.res) && d.res.length === n && d.res.every(x => x === 1 || x === 2) &&
    Array.isArray(d.path) && d.path.length === n && new Set(d.path).size === n && d.path.every(x => Number.isInteger(x) && x >= 0 && x < n);
  if (!ok) return json({ error: 'not a finished board' }, 400);
  const score = d.res.filter(x => x === 1).length;
  await env.DB.prepare('INSERT INTO results (day, score, ids, res, path, host, at) VALUES (?, ?, ?, ?, ?, ?, ?)')
    .bind(d.day, score, d.ids.join(' '), d.res.join(''), d.path.join(' '), where, new Date().toISOString()).run();
  return json({ ok: true });
}
