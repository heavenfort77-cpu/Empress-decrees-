// Mutation round for the PREP-AV checks (draft for INT). Runs on a GitHub runner only (project rule: mutation rounds never on the session
// machine). Each mutant changes one spot of a module in the runner's checkout, runs the check that must catch it, and restores the file.
// A mutant is CAUGHT when the named check prints FAIL. Usage: node tests_draft/mutate.mjs [names...]
import { readFileSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
const ROOT = new URL('..', import.meta.url).pathname;
const M = [
  { name: 'pause ignored by fxEvent', file: 'src/fx/fxevent.js', a: 'if (F.paused || !F.ev) return -1;', b: 'if (!F.ev) return -1;', test: ['fx-runtime.mjs', 'T4'], want: 'T4' },
  { name: 'card clock runs while paused', file: 'src/fx/fxevent.js', a: 'if (paused || F.paused) return;', b: 'if (false) return;', test: ['fx-runtime.mjs', 'T4'], want: 'T4' },
  { name: 'pause does not suspend audio', file: 'src/audio/sound.js', a: 'const p = (S.paused || S.hidden) ? S.ctx.suspend()', b: 'const p = (S.hidden) ? S.ctx.suspend()', test: ['fx-runtime.mjs', 'T4'], want: 'T4' },
  { name: 'hidden tab ignored', file: 'src/audio/sound.js', a: "document.addEventListener('visibilitychange', () => { S.hidden = document.hidden; runState(); });", b: '', test: ['fx-runtime.mjs', 'T5'], want: 'T5' },
  { name: 'unlock never resumes', file: 'src/audio/sound.js', a: "if (S.ctx.state !== 'running' && !S.paused && !S.hidden) { const p = S.ctx.resume(); if (p && p.catch) p.catch(() => {}); }", b: '', test: ['fx-runtime.mjs', 'T1'], want: 'T1' },
  { name: 'dt not clamped', file: 'src/fx/fxevent.js', a: '  dtMax: 0.05,', b: '  dtMax: 50,', test: ['fx-runtime.mjs', 'T6'], want: 'T6' },
  { name: 'warm-up skipped', file: 'src/fx/fxevent.js', a: '  renderer.compile(F.scene, camera);\n  renderer.render(F.scene, camera);', b: '', test: ['fx-runtime.mjs', 'T7'], want: 'T7' },
  { name: 'intensity never falls', file: 'src/fx/intensity.js', a: 'if (ST.holdT <= 0) { ST.level = want;', b: 'if (ST.holdT <= -1e9) { ST.level = want;', test: ['fx-runtime.mjs', 'T8'], want: 'T8' },
  { name: 'danger level lost', file: 'src/fx/intensity.js', a: 'if (i.hpFrac < C.lowHp || i.giantsAwake > 0 || i.burnMine) return C.danger;', b: 'if (i.giantsAwake > 0 || i.burnMine) return C.danger;', test: ['fx-runtime.mjs', 'T8'], want: 'T8' },
  { name: 'slider change not saved', file: 'src/audio/options.js', a: "r.addEventListener('change', () => apply(true));", b: "r.addEventListener('change', () => apply(false));", test: ['fx-runtime.mjs', 'T9'], want: 'T9' },
  { name: 'mute lets sounds through', file: 'src/audio/sound.js', a: "if (!S.ctx || S.paused || S.hidden || S.mute || S.mode === 'off') return false;", b: "if (!S.ctx || S.paused || S.hidden || S.mode === 'off') return false;", test: ['fx-runtime.mjs', 'T9'], want: 'T9' },
  { name: 'mute not saved', file: 'src/audio/sound.js', a: 'vol: S.vol, mute: S.mute })', b: 'vol: S.vol })', test: ['fx-runtime.mjs', 'T10'], want: 'T10' },
  { name: 'storage not guarded', file: 'src/audio/sound.js', a: 'function saveSettings() { try { localStorage.setItem(CONFIG.saveKey, JSON.stringify({ mode: S.mode, reduce: S.reduce, vol: S.vol, mute: S.mute })); } catch (e) { } }', b: 'function saveSettings() { localStorage.setItem(CONFIG.saveKey, JSON.stringify({ mode: S.mode, reduce: S.reduce, vol: S.vol, mute: S.mute })); }', test: ['fx-runtime.mjs', 'T13'], want: 'T13' },
  { name: 'slider 30 px', file: 'src/audio/options.js', a: '.opts__range{width:100%;min-height:44px;', b: '.opts__range{width:100%;height:30px;max-height:30px;', test: ['fx-runtime.mjs', 'T14'], want: 'T14' },
  { name: 'low tier keeps smoke states', file: 'src/fx/fxevent.js', a: "if (F.tier === 'low' && ((c.card === 'smoke' && phase === 'state')", b: "if (F.tier === 'x' && ((c.card === 'smoke' && phase === 'state')", test: ['fx-runtime.mjs', 'T15'], want: 'T15' },
  { name: 'sound name typo', file: 'src/fx/fxmap.js', a: '~demon_claw_tell |', b: '~demon_claw_tel |', test: ['fx-map.mjs'], want: 'sounds' },
  { name: 'tell under 0.4 s', file: 'src/fx/fxmap.js', a: 'tell ring r1.7 h0.4 ~cub_bite_tell', b: 'tell ring r1.7 h0.3 ~cub_bite_tell', test: ['fx-map.mjs'], want: 'tell hold' },
  { name: 'map item dropped', file: 'src/fx/fxmap.js', a: "  r_stall: '*rebel_umber | rel impact s0.8 ~r_stall | state smoke s0.6',\n", b: '', test: ['fx-map.mjs'], want: 'vfx map items' },
  { name: 'object per event', file: 'src/fx/fxevent.js', a: '  F.events++;\n', b: '  F.events++; const tmp = { n: name };\n', test: ['static-src.mjs'], want: 'perframe object literal' },
  { name: 'closure per frame', file: 'src/fx/intensity.js', a: '  const want = levelOf(IN);', b: '  const want = [IN].map((v) => levelOf(v))[0];', test: ['static-src.mjs'], want: 'perframe' },
];
const only = process.argv.slice(2);
let caught = 0, ran = 0;
for (const m of M) {
  if (only.length && !only.includes(m.name)) continue;
  const p = ROOT + m.file, orig = readFileSync(p, 'utf8');
  ran++;
  if (orig.split(m.a).length !== 2) { console.log(`MUT ERROR ${m.name}: anchor not found once in ${m.file}`); continue; }
  writeFileSync(p, orig.replace(m.a, m.b));
  let out = '';
  try { out = execFileSync(process.execPath, [ROOT + 'tests_draft/' + m.test[0], ...m.test.slice(1)], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 600000 }); }
  catch (e) { out = String(e.stdout || '') + String(e.stderr || ''); }
  finally { writeFileSync(p, orig); }
  const hit = out.split('\n').some((l) => (l.startsWith('FAIL') || /:\d+ perframe/.test(l)) && l.includes(m.want));
  if (hit) caught++;
  console.log(`MUT ${hit ? 'CAUGHT' : 'MISSED'} ${m.name} (by ${m.want})`);
  if (!hit) console.log(out.split('\n').filter((l) => /FAIL|PASS|ERR/.test(l)).slice(0, 8).join('\n'));
}
console.log(`MUTATIONS ${caught} of ${ran} caught`);
process.exit(caught === ran ? 0 : 1);
