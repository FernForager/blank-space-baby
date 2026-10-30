// The text editor's Send (Morg, Oct 26, 2026: research/text-system.md). A Cloudflare Pages Function, served at /api/text.
//   POST {edits: [{id, from, to}]}  records one batch of Morg's text changes, made in the game with ?text on a preview link
// Batches go to the triviela-beta database (the DB binding in wrangler.toml), into its texts table, oldest first. Trivelle reads
// them from there (tools/textedits.py), writes them into build/text/en.json, rebuilds and checks. Only preview links send them.
const ID = /^[a-z][a-z0-9]*(?:\.[a-zA-Z0-9]+)*$/;

const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json', 'cache-control': 'no-store' } });

export async function onRequestPost({ request, env }) {
  const url = new URL(request.url);
  if (!url.hostname.endsWith('.blank-space-baby.pages.dev')) return json({ error: 'text edits are for the beta only' }, 403);
  if (!env.DB) return json({ error: 'the database is not connected (no DB binding)' }, 503);
  const origin = request.headers.get('origin');
  if (origin && origin !== url.origin) return json({ error: 'edits come from the game itself' }, 403);
  let d;
  try { d = await request.json(); } catch (e) { return json({ error: 'not JSON' }, 400); }
  const edits = d && Array.isArray(d.edits) ? d.edits : null;
  if (!edits || !edits.length || edits.length > 200) return json({ error: 'no edits' }, 400);
  for (const e of edits) {
    if (!e || typeof e.id !== 'string' || !ID.test(e.id) || typeof e.to !== 'string' || typeof e.from !== 'string' || e.to.length > 500 || e.from.length > 500) return json({ error: 'not an edit' }, 400);
  }
  const body = JSON.stringify(edits.map(e => ({ id: e.id, from: e.from, to: e.to.trim() })));
  await env.DB.prepare('INSERT INTO texts (body, host, at) VALUES (?, ?, ?)').bind(body, url.hostname, new Date().toISOString()).run();
  return json({ ok: true, n: edits.length });
}
