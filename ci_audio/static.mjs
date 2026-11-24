// Static check for src/audio/sound.js: the per-frame rules of tests/static-check.mjs applied to its PERFRAME block, plus
// unseeded random, mid-line comments and a comment line above every top-level CONFIG value. Usage: node ci_audio/static.mjs [file]
import { readFileSync } from 'node:fs';
const file = process.argv[2] || new URL('../src/audio/sound.js', import.meta.url).pathname;
const lines = readFileSync(file, 'utf8').split('\n');
const fails = [];
const BAD = [
  [/\bnew\s+[A-Za-z_$]/, 'object creation'], [/getObjectBy(Name|Id|Property)/, 'name lookup'], [/\.traverse(Visible)?\(/, 'scene traversal'],
  [/\.(map|filter|reduce|sort|flatMap|forEach)\(/, 'array chain'], [/querySelector|getElementById|getElementsBy/, 'DOM lookup'],
  [/\.(textContent|innerHTML|innerText|outerHTML)\s*=/, 'unchecked DOM write'],
  [/create(Oscillator|Gain|BufferSource|BiquadFilter|Buffer|Panner|StereoPanner|WaveShaper|DynamicsCompressor)\(/, 'audio node creation'],
  [/matchMedia\(/, 'per-frame matchMedia'], [/\bfunction\s*\(|=>/, 'closure'], [/`|JSON\.|\.concat\(|Object\.assign/, 'string or object building'],
];
let inBlock = false, blocks = 0, blockLines = 0;
lines.forEach((ln, i) => {
  if (ln.includes('PERFRAME-BEGIN')) { inBlock = true; blocks++; return; }
  if (ln.includes('PERFRAME-END')) { inBlock = false; return; }
  if (!inBlock) return;
  blockLines++;
  const code = ln.replace(/\/\/.*$/, '');
  for (const [re, what] of BAD) if (re.test(code)) fails.push(`perframe ${what}: line ${i + 1}: ${ln.trim()}`);
});
if (blocks < 1) fails.push('perframe: no PERFRAME block');
if (inBlock) fails.push('perframe: unclosed PERFRAME block');
lines.forEach((ln, i) => { if (/Math\.random\s*\(/.test(ln.replace(/\/\/.*$/, ''))) fails.push(`unseeded random: line ${i + 1}`); });
lines.forEach((ln, i) => { if (/\/\*.*\*\/\s*\S/.test(ln) && !ln.includes('PERFRAME')) fails.push(`comment mid-line: line ${i + 1}`); });
const c0 = lines.findIndex((l) => l.startsWith('export const CONFIG = {'));
if (c0 < 0) fails.push('config: no CONFIG block');
for (let i = c0 + 1; c0 >= 0 && i < lines.length && !lines[i].startsWith('};'); i++) {
  if (/^ {2}[A-Za-z_]+:/.test(lines[i]) && !/^\s*\/\//.test(lines[i - 1])) fails.push(`config value without comment above: line ${i + 1}`);
  if (/^ {4}[A-Za-z_]+:/.test(lines[i]) && !/^\s*\/\//.test(lines[i - 1]) && !/^ {4}m_/.test(lines[i])) fails.push(`config value without comment above: line ${i + 1}`);
}
console.log(fails.length ? 'AUDIO STATIC FAIL\n' + fails.join('\n') : `AUDIO STATIC PASS (${blocks} perframe block, ${blockLines} lines)`);
process.exit(fails.length ? 1 : 0);
