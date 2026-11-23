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
console.log(fails.length ? 'STATIC FAIL\n' + fails.join('\n') : `STATIC PASS (${blocks} perframe blocks, ${keys.size} text keys)`);
process.exit(fails.length ? 1 : 0);
