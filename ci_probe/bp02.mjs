// BP02 probe (not committed): load, base render, the guard checks only.
import { open } from './harness.mjs';
import { guardChecks } from '../tests/guard-checks.mjs';
const { page, errors, close } = await open();
const g = (fn, arg) => page.evaluate(fn, arg);
const res = [];
const check = (name, ok, detail) => res.push({ name, ok: !!ok, detail });
try {
  await g(() => { __game.setSeed(12345); __game.reset(); });
  const base = await g(() => __game.render(true));
  console.log('base', JSON.stringify(base));
  await guardChecks(g, check, base);
} catch (e) { console.log('ERR', e && e.stack || e); }
for (const r of res) console.log(r.ok ? 'ok  ' : 'FAIL', r.name, '::', String(r.detail).slice(0, 1500));
console.log('errors', errors.slice(0, 5).join(' | '));
await close();
