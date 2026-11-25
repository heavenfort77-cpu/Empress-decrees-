// Static checks for src/chars.js (draft for INT; same rules as tests/static-check.mjs, applied to the module).
// Usage: node tests_draft/chars-static.mjs [src/chars.js]. Prints PASS or FAIL lines; exit 1 on any FAIL.
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
const file = process.argv[2] || new URL('../src/chars.js', import.meta.url).pathname;
const src = readFileSync(file, 'utf8'), lines = src.split('\n'), fails = [];
// Rule 24 list (tests/static-check.mjs BAD) inside PERFRAME blocks.
const BAD = [
  [/\bnew\s+[A-Za-z_$]/, 'object creation'], [/getObjectBy(Name|Id|Property)/, 'name lookup'], [/\.traverse(Visible)?\(/, 'scene traversal'],
  [/\.(map|filter|reduce|sort|flatMap|forEach)\(/, 'array chain'], [/querySelector|getElementById|getElementsBy/, 'DOM lookup'],
  [/\.(textContent|innerHTML|innerText|outerHTML)\s*=/, 'unchecked DOM write'], [/create(Oscillator|Gain|BufferSource|BiquadFilter|Buffer|Panner)\(/, 'audio node creation'],
  [/matchMedia\(/, 'per-frame matchMedia'],
  // Stricter for this module: closures and for-in in per-frame code allocate.
  [/=>/, 'closure'], [/for\s*\(\s*(const|let|var)\s+\w+\s+in\b/, 'for-in'], [/\.(slice|concat|splice)\(/, 'array copy'], [/\[\s*\.\.\./, 'spread'],
];
let inBlock = false, blocks = 0;
lines.forEach((ln, i) => {
  if (ln.includes('PERFRAME-BEGIN')) { inBlock = true; blocks++; return; }
  if (ln.includes('PERFRAME-END')) { inBlock = false; return; }
  if (!inBlock) return;
  const code = ln.replace(/\/\/.*$/, '');
  for (const [re, what] of BAD) if (re.test(code)) fails.push(`perframe ${what}: line ${i + 1}: ${ln.trim().slice(0, 100)}`);
});
if (blocks < 2) fails.push(`perframe: expected at least 2 PERFRAME blocks, found ${blocks}`);
if (inBlock) fails.push('perframe: unclosed PERFRAME block');
lines.forEach((ln, i) => { if (/Math\.random\s*\(/.test(ln.replace(/\/\/.*$/, ''))) fails.push(`unseeded random: line ${i + 1}`); });
lines.forEach((ln, i) => { if (/\/\*.*\*\/\s*\S/.test(ln) && !ln.includes('PERFRAME')) fails.push(`comment mid-line: line ${i + 1}`); });
// A '//' comment after code on the same line (rule 20 / game-code-clean 18.6.8), outside strings and URLs.
lines.forEach((ln, i) => { const c = ln.replace(/'[^']*'|"[^"]*"|`[^`]*`/g, "''"); if (/\S.*[;{}),]\s*\/\/\s/.test(c) && !/^\s*\/\//.test(c)) fails.push(`comment after code: line ${i + 1}`); });
// Rule 6: every CHR value has a comment line above it.
const a = lines.findIndex((l) => l.startsWith('export const CHR = {'));
if (a < 0) fails.push('config: no export const CHR block');
for (let i = a + 1; a >= 0 && i < lines.length && !lines[i].startsWith('};'); i++) if (/^ {2}[A-Za-z_]+:/.test(lines[i]) && !/^\s*\/\//.test(lines[i - 1])) fails.push(`config value without comment above: line ${i + 1}`);
// frustumCulled = false is never allowed (rule 35).
lines.forEach((ln, i) => { if (/frustumCulled\s*=\s*false/.test(ln.replace(/\/\/.*$/, ''))) fails.push(`frustumCulled = false: line ${i + 1}`); });
try { execFileSync(process.execPath, ['--check', file], { stdio: 'pipe' }); } catch (e) { fails.push('syntax: ' + String(e.stderr || e).split('\n').slice(0, 4).join(' | ')); }
console.log(fails.length ? 'CHARS STATIC FAIL\n' + fails.join('\n') : `CHARS STATIC PASS (${blocks} perframe blocks)`);
process.exit(fails.length ? 1 : 0);
