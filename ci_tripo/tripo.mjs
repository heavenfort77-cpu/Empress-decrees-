// Tripo text-to-model jobs on a GitHub runner (the session machine cannot reach the Tripo API). Reads ci_tripo/jobs.json, writes
// tripo_out/<name>.glb, tripo_out/<name>.png (Tripo preview render), tripo_out/<name>.json (task record, no key) and tripo_out/summary.txt.
// Key: repo secret TRIPO_API_KEY (the owner adds it in GitHub settings; it is never written to a file or a log).
// API (developers.tripo3d.com): POST {base}/generation/text-to-model, GET {base}/tasks/{id}; model URLs expire minutes after success,
// so each model is downloaded as soon as its task succeeds.
import { readFile, writeFile, mkdir } from 'node:fs/promises';

const KEY = process.env.TRIPO_API_KEY || '';
const BASE = process.env.TRIPO_BASE || 'https://openapi.tripo3d.ai/v3';
const lines = [];
const log = (s) => { lines.push(s); console.log(s); };
await mkdir('tripo_out', { recursive: true });
if (!KEY) { log('FAIL no TRIPO_API_KEY secret on the repo'); await writeFile('tripo_out/summary.txt', lines.join('\n') + '\n'); process.exit(1); }
const H = { Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' };
const jobs = JSON.parse(await readFile(new URL('jobs.json', import.meta.url), 'utf8'));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function run(job) {
  const body = Object.assign({ model: 'v3.1-20260211', texture: false, pbr: false }, job.req);
  const r = await fetch(BASE + '/generation/text-to-model', { method: 'POST', headers: H, body: JSON.stringify(body) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok || j.code !== 0) { log(`FAIL ${job.name} create http ${r.status} ${JSON.stringify(j).slice(0, 200)}`); return; }
  const id = j.data.task_id; log(`TASK ${job.name} ${id}`);
  const t0 = Date.now();
  for (;;) {
    await sleep(5000);
    const q = await fetch(BASE + '/tasks/' + id, { headers: H }).then((x) => x.json()).catch(() => ({}));
    const d = q.data || {}, st = d.status;
    if (st === 'success') {
      const o = d.output || {};
      for (const [k, ext] of [['model_url', 'glb'], ['pbr_model_url', 'glb'], ['base_model_url', 'glb'], ['rendered_image_url', 'png']]) {
        if (!o[k]) continue;
        const b = Buffer.from(await (await fetch(o[k])).arrayBuffer());
        const f = `tripo_out/${job.name}${k === 'model_url' || ext === 'png' ? '' : '_' + k.replace('_model_url', '')}.${ext === 'png' ? (o[k].includes('.webp') ? 'webp' : 'png') : 'glb'}`;
        await writeFile(f, b); log(`FILE ${f} ${b.length} bytes`);
      }
      await writeFile(`tripo_out/${job.name}.json`, JSON.stringify({ job, task_id: id, status: st, credits: d.credits_consumed, created_at: d.created_at, completed_at: d.completed_at }, null, 1));
      log(`OK ${job.name} ${Math.round((Date.now() - t0) / 1000)} s credits ${d.credits_consumed}`);
      return;
    }
    if (['failed', 'cancelled', 'banned', 'expired'].includes(st)) { log(`FAIL ${job.name} ${st} ${d.error_code || ''} ${d.error_message || ''}`); return; }
    if (Date.now() - t0 > 20 * 60 * 1000) { log(`FAIL ${job.name} no result in 20 min (last status ${st})`); return; }
  }
}
for (const job of jobs) await run(job);
await writeFile('tripo_out/summary.txt', lines.join('\n') + '\n');
