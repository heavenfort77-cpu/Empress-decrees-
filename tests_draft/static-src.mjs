// Static check for the modules under src/ (PREP-AV draft for INT; same rules as tests/static-check.mjs, stricter inside PERFRAME blocks).
// Usage: node tests_draft/static-src.mjs [files...]  (default: every .js under src/). Exit 1 on any FAIL; prints failing lines only.
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
const ROOT = new URL('..', import.meta.url).pathname;
const walk = (d) => readdirSync(d).flatMap((f) => { const p = join(d, f); return statSync(p).isDirectory() ? walk(p) : p.endsWith('.js') ? [p] : []; });
const files = process.argv.length > 2 ? process.argv.slice(2) : walk(join(ROOT, 'src'));
// Rule 24 list of tests/static-check.mjs, unchanged.
const BAD = [
  [/\bnew\s+[A-Za-z_$]/, 'object creation'],
  [/getObjectBy(Name|Id|Property)/, 'name lookup'],
  [/\.traverse(Visible)?\(/, 'scene traversal'],
  [/\.(map|filter|reduce|sort|flatMap|forEach)\(/, 'array chain'],
  [/querySelector|getElementById|getElementsBy/, 'DOM lookup'],
  [/\.(textContent|innerHTML|innerText|outerHTML)\s*=/, 'unchecked DOM write'],
  [/create(Oscillator|Gain|BufferSource|BiquadFilter|Buffer|Panner)\(/, 'audio node creation'],
  [/matchMedia\(/, 'per-frame matchMedia'],
  // Stricter for src/ (nothing loosened): literals, closures, string building and copies allocate per call.
  [/(=|\(|,|return|\?|:)\s*\{\s*[\w'"]+\s*:/, 'object literal'],
  [/(=|\(|,|return)\s*\[/, 'array literal'],
  [/=>/, 'closure'],
  [/`/, 'template string'],
  [/\.(slice|concat|split|join|splice)\(/, 'array or string copy'],
  [/JSON\.|Object\.(keys|values|entries|assign)\(/, 'object walk'],
  [/'\s*\+(?!\+)|\+\s*'/, 'string concatenation'],
  [/\b(setTimeout|setInterval)\(/, 'timer'],
];
const fails = [];
let blocks = 0;
for (const f of files) {
  const src = readFileSync(f, 'utf8'), lines = src.split('\n'), rel = f.replace(ROOT, '');
  let inB = false;
  lines.forEach((ln, i) => {
    if (ln.includes('PERFRAME-BEGIN')) { if (inB) fails.push(`${rel}:${i + 1} nested PERFRAME-BEGIN`); inB = true; blocks++; return; }
    if (ln.includes('PERFRAME-END')) { inB = false; return; }
    // Rule 20: no comment placed mid-line before code; and no // comment after code (it can swallow code pasted after it).
    if (/\/\*.*\*\/\s*\S/.test(ln) && !ln.includes('PERFRAME')) fails.push(`${rel}:${i + 1} comment mid-line`);
    if (/;\s*\/\/(?!.*['"`])/.test(ln)) fails.push(`${rel}:${i + 1} comment after code`);
    if (/Math\.random\s*\(/.test(ln.replace(/\/\/.*$/, '')) && !rel.startsWith('src/audio/')) fails.push(`${rel}:${i + 1} unseeded random`);
    if (!inB) return;
    const code = ln.replace(/\/\/.*$/, '').replace(/'[^']*'/g, (m) => (/\+/.test(ln) ? m : "''"));
    for (const [re, what] of BAD) if (re.test(code)) fails.push(`${rel}:${i + 1} perframe ${what}: ${ln.trim().slice(0, 120)}`);
  });
  if (inB) fails.push(`${rel}: unclosed PERFRAME block`);
  // Syntax: every module parses.
}
const { execFileSync } = await import('node:child_process');
for (const f of files) { try { execFileSync(process.execPath, ['--check', f], { stdio: 'pipe' }); } catch (e) { fails.push(`${f.replace(ROOT, '')} syntax: ${String(e.stderr).split('\n').slice(0, 3).join(' | ')}`); } }
const want = files.filter((f) => /src\/(fx\/(cards|fxevent|intensity)|audio\/sound)\.js$/.test(f)).length;
if (blocks < want) fails.push(`perframe: expected a PERFRAME block in each of ${want} per-frame modules, found ${blocks}`);
console.log(fails.length ? 'SRC-STATIC FAIL\n' + fails.join('\n') : `SRC-STATIC PASS (${files.length} files, ${blocks} perframe blocks)`);
process.exit(fails.length ? 1 : 0);
