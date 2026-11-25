// Static checks: per-frame code rules and text keys. Usage: node tests/static-check.mjs [index.html]
import { readFileSync } from 'node:fs';

const file = process.argv[2] || new URL('../index.html', import.meta.url).pathname;
const src = readFileSync(file, 'utf8');
const lines = src.split('\n');
const fails = [];

// Rule 24: no object creation, name lookups, traversals, array chains, DOM lookups, audio nodes
// or unchecked DOM writes inside PERFRAME blocks.
const BAD = [
  [/\bnew\s+[A-Za-z_$]/, 'object creation'],
  [/getObjectBy(Name|Id|Property)/, 'name lookup'],
  [/\.traverse(Visible)?\(/, 'scene traversal'],
  [/\.(map|filter|reduce|sort|flatMap|forEach)\(/, 'array chain'],
  [/querySelector|getElementById|getElementsBy/, 'DOM lookup'],
  [/\.(textContent|innerHTML|innerText|outerHTML)\s*=/, 'unchecked DOM write'],
  [/create(Oscillator|Gain|BufferSource|BiquadFilter|Buffer|Panner)\(/, 'audio node creation'],
  [/matchMedia\(/, 'per-frame matchMedia'],
];
let inBlock = false, blocks = 0;
lines.forEach((ln, i) => {
  if (ln.includes('PERFRAME-BEGIN')) { inBlock = true; blocks++; return; }
  if (ln.includes('PERFRAME-END')) { inBlock = false; return; }
  if (!inBlock) return;
  const code = ln.replace(/\/\/.*$/, '');
  for (const [re, what] of BAD) if (re.test(code)) fails.push(`perframe ${what}: line ${i + 1}: ${ln.trim()}`);
});
if (blocks < 2) fails.push(`perframe: expected at least 2 PERFRAME blocks, found ${blocks}`);
if (inBlock) fails.push('perframe: unclosed PERFRAME block');

// Replays (batch 9): every random choice comes from the seeded generators, never Math.random.
lines.forEach((ln, i) => { if (/Math\.random\s*\(/.test(ln.replace(/\/\/.*$/, ''))) fails.push(`unseeded random: line ${i + 1}`); });

// Text keys: every literal T('key') must exist in TEXT; dynamic keys checked by the runtime test.
const textBlock = src.slice(src.indexOf('const TEXT = {'), src.indexOf('};', src.indexOf('const TEXT = {')));
const keys = new Set([...textBlock.matchAll(/(\w+):\s*'/g)].map((m) => m[1]));
for (const m of src.matchAll(/\bT\('(\w+)'\s*[,)]/g)) if (!keys.has(m[1])) fails.push(`text: missing key '${m[1]}'`);

// Rule 20: no comment placed mid-line before code.
lines.forEach((ln, i) => { if (/\/\*.*\*\/\s*\S/.test(ln) && !ln.includes('PERFRAME')) fails.push(`comment mid-line: line ${i + 1}`); });

// Rule 6: every CONFIG value has a comment line above it.
const cfgStart = lines.findIndex((l) => l.startsWith('const CONFIG = {'));
for (let i = cfgStart + 1; i < lines.length && !lines[i].startsWith('};'); i++) {
  const l = lines[i];
  if (/^ {2}[A-Z_]+:/.test(l) && !/^\s*\/\//.test(lines[i - 1])) fails.push(`config value without comment above: line ${i + 1}`);
}

// Syntax: the module script must parse (catches duplicate declarations before any browser run).
{
  const m = src.match(/<script type="module">([\s\S]*?)<\/script>/);
  if (!m) fails.push('syntax: no module script found');
  else {
    const { writeFileSync } = await import('node:fs'); const { execFileSync } = await import('node:child_process');
    const tmp = '/tmp/static-check-module.mjs'; writeFileSync(tmp, m[1].replace(/^import .*$/m, 'const THREE = {};'));
    try { execFileSync(process.execPath, ['--check', tmp], { stdio: 'pipe' }); }
    catch (e) { fails.push('syntax: ' + String(e.stderr || e).split('\n').slice(0, 5).join(' | ')); }
  }
}
// Batch 17b (owner 25 Nov 09:15): every module under src/ (prep workers' code) gets the same per-frame rules inside its PERFRAME blocks, the
// unseeded-random and mid-line-comment rules, and a syntax check. Usage with a folder argument: node tests/static-check.mjs index.html SRCDIR.
const { readdirSync, statSync } = await import('node:fs');
const srcDir = process.argv[3] || new URL('../src', import.meta.url).pathname;
const mods = [];
const walkDir = (d) => { let names = []; try { names = readdirSync(d); } catch (e) { return; } for (const n of names) { const p = d + '/' + n; if (statSync(p).isDirectory()) walkDir(p); else if (/\.(m?js)$/.test(n)) mods.push(p); } };
walkDir(srcDir);
let modBlocks = 0;
for (const f of mods) {
  const ml = readFileSync(f, 'utf8').split('\n'); let open = false;
  ml.forEach((ln, i) => {
    const code = ln.replace(/\/\/.*$/, '');
    if (ln.includes('PERFRAME-BEGIN')) { if (open) fails.push(`${f}: nested PERFRAME-BEGIN line ${i + 1}`); open = true; modBlocks++; return; }
    if (ln.includes('PERFRAME-END')) { open = false; return; }
    if (/Math\.random\s*\(/.test(code)) fails.push(`${f}: unseeded random: line ${i + 1}`);
    if (/\/\*.*\*\/\s*\S/.test(ln) && !ln.includes('PERFRAME')) fails.push(`${f}: comment mid-line: line ${i + 1}`);
    if (open) for (const [re, what] of BAD) if (re.test(code)) fails.push(`${f}: perframe ${what}: line ${i + 1}: ${ln.trim()}`);
  });
  if (open) fails.push(`${f}: unclosed PERFRAME block`);
  const { writeFileSync } = await import('node:fs'); const { execFileSync } = await import('node:child_process');
  const tmp = '/tmp/static-check-src.mjs'; writeFileSync(tmp, ml.join('\n'));
  try { execFileSync(process.execPath, ['--check', tmp], { stdio: 'pipe' }); } catch (e) { fails.push(`${f}: syntax: ` + String(e.stderr || e).split('\n').slice(0, 4).join(' | ')); }
}
console.log(fails.length ? 'STATIC FAIL\n' + fails.join('\n') : `STATIC PASS (${blocks} perframe blocks, ${keys.size} text keys; src: ${mods.length} modules, ${modBlocks} perframe blocks)`);
process.exit(fails.length ? 1 : 0);
