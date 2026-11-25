// Sharded full suite (owner 25 Nov 09:15: "do it faster, use github"). CI tool only, never on main or batches-3-5.
// Usage: node ci/shard.mjs I N   (I = 0..N-1; N = 1 gives the unsharded-equivalent run with per-statement timings)
// tests/run.mjs runs its checks as top-level statements inside one try block. This tool parses it (acorn), keeps a prelude (page load, base
// counts) and the one-line config reads whose names are used far apart (ALWAYS) in every shard, and splits the rest at statement boundaries no
// variable crosses (checked from the code: names used by later statements, page-side functions excluded). Shard I runs only its own statements
// (each guarded as `if (RUN(k))`, declarations turned into var so a skipped one is simply undefined) and prints per-statement times
// (STMT line ms) so ci/shard_times.json can rebalance the cuts. The suite's own output (RUNTIME, FAIL, -v, -sims) is unchanged.
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
const acorn = await import('acorn');
const [I, N] = [Number(process.argv[2] || 0), Number(process.argv[3] || 1)];
const SRC = 'tests/run.mjs', src = readFileSync(SRC, 'utf8');
const ast = acorn.parse(src, { ecmaVersion: 'latest', sourceType: 'module', locations: true });
const tryS = ast.body.filter((s) => s.type === 'TryStatement').sort((a, b) => b.block.body.length - a.block.body.length)[0];
const st = tryS.block.body;
const declOf = (s) => { const n = []; const id = (p) => { if (!p) return; if (p.type === 'Identifier') n.push(p.name); else if (p.type === 'ObjectPattern') p.properties.forEach((q) => id(q.value || q.argument)); else if (p.type === 'ArrayPattern') p.elements.forEach(id); else if (p.type === 'AssignmentPattern') id(p.left); else if (p.type === 'RestElement') id(p.argument); };
  if (s.type === 'VariableDeclaration') s.declarations.forEach((d) => id(d.id)); if (s.type === 'FunctionDeclaration' || s.type === 'ClassDeclaration') n.push(s.id.name); return n; };
const refsOf = (s) => { const r = new Set();
  const rec = (n, skip) => { if (!n || typeof n.type !== 'string') return; if (n.type === 'Identifier') { if (!skip) r.add(n.name); return; }
    if (n.type === 'CallExpression' && n.callee.type === 'Identifier' && n.callee.name === 'g') { n.arguments.slice(1).forEach((c) => rec(c, false)); return; }
    if (n.type === 'CallExpression' && n.callee.type === 'MemberExpression' && !n.callee.computed && /^(evaluate|waitForFunction|addInitScript)$/.test(n.callee.property.name)) { rec(n.callee.object, false); n.arguments.slice(1).forEach((c) => rec(c, false)); return; }
    for (const k in n) { if (k === 'loc' || k === 'start' || k === 'end') continue; const v = n[k];
      const sk = (n.type === 'MemberExpression' && k === 'property' && !n.computed) || (n.type === 'Property' && k === 'key' && !n.computed) || (n.type === 'MethodDefinition' && k === 'key');
      if (Array.isArray(v)) v.forEach((c) => rec(c, false)); else if (v && typeof v.type === 'string') rec(v, sk); } };
  rec(s, false); return r; };
const D = st.map(declOf), R = st.map(refsOf);
const lastUse = D.map((names, i) => { let m = i; for (let j = i + 1; j < st.length; j++) if (names.some((x) => R[j].has(x))) m = j; return m; });
const text = (s) => src.slice(s.start, s.end);
// Prelude: through the statement that declares S (page load, base render, bot count, map scale): run in every shard.
const P = Math.max(0, D.findIndex((n) => n.includes('S')));
// ALWAYS: one-line declarations read from the config or text tables (no reset, no stepping), used across a cut.
const pure = (s) => /^\s*const \w+(, \w+ = [^,]+)? = (await g\(\(\) => (__game\.(config|text|K)\b|\[.*__game\.text)|C0\.|Array\(C0\.)/.test(text(s)) || /^const \w+ = C0\./.test(text(s));
const ALWAYS = new Set(); for (let i = P + 1; i < st.length; i++) if (D[i].length && st[i].loc.start.line === st[i].loc.end.line && lastUse[i] > i + 1 && pure(st[i])) ALWAYS.add(i);
// Page helpers (window.__x = {...} set up by one statement and used by later ones) are page state: their statements run in every shard too.
for (let i = P + 1; i < st.length; i++) if (/window\.__\w+\s*=(?!=)/.test(text(st[i])) && st[i].loc.end.line - st[i].loc.start.line < 40 && !D[i].length) ALWAYS.add(i);
const cuts = []; for (let c = P + 2; c < st.length; c++) { let ok = true; for (let i = P + 1; i < c; i++) if (!ALWAYS.has(i) && lastUse[i] >= c) { ok = false; break; } if (ok) cuts.push(c); }
// Weights: measured statement times (ci/shard_times.json, line -> ms) if present, else lines of code.
const TW = existsSync('ci/shard_times.json') ? JSON.parse(readFileSync('ci/shard_times.json', 'utf8')) : null;
const w = st.map((s, i) => (i <= P || ALWAYS.has(i) ? 0 : TW ? (TW[s.loc.start.line] ?? 50) : s.loc.end.line - s.loc.start.line + 1));
const total = w.reduce((a, b) => a + b, 0);
const seg = new Array(st.length).fill(0); let k = 0, acc = 0;
const chosen = [];
for (let i = P + 1; i < st.length; i++) {
  if (k < N - 1 && cuts.includes(i) && acc >= total * (k + 1) / N) { k++; chosen.push(i); }
  acc += w[i]; seg[i] = k;
}
// Module-level names must not collide with hoisted vars.
const top = new Set(ast.body.flatMap(declOf));
const clash = [...new Set(st.flatMap((s, i) => (i > P && !ALWAYS.has(i) ? D[i] : [])))].filter((n) => top.has(n));
if (clash.length) { console.log('SHARD-ERROR name clash ' + clash.join(',')); process.exit(3); }
let out = '', pos = 0;
const emit = (upto) => { out += src.slice(pos, upto); pos = upto; };
for (let i = 0; i < st.length; i++) {
  const s = st[i]; emit(s.start);
  out += `__T(${s.loc.start.line});`;
  if (i <= P || ALWAYS.has(i)) continue;
  if (s.type === 'VariableDeclaration') { out += `if (RUN(${seg[i]})) var `; pos = s.start + s.kind.length + 1; }
  else if (s.type === 'FunctionDeclaration' || s.type === 'ClassDeclaration') continue;
  else out += `if (RUN(${seg[i]})) `;
}
emit(src.length);
const head = `const RUN = (k) => k === ${I}; const __TT = []; let __tl = 0, __tt = performance.now(); const __T = (l) => { const n = performance.now(); if (__tl) __TT.push([__tl, Math.round(n - __tt)]); __tl = l; __tt = n; };\nprocess.on('exit', () => { __T(0); for (const [l, ms] of __TT) if (ms > 0) console.log('STMT', l, ms); });\n`;
const firstImport = out.indexOf('\nlet chromium');
out = out.slice(0, firstImport + 1) + head + out.slice(firstImport + 1);
writeFileSync('tests/run_shard.mjs', out);
console.log(`SHARD ${I} of ${N}: statements ${st.length}, prelude ${P + 1}, always ${ALWAYS.size}, valid cuts ${cuts.length}, cuts at lines ${chosen.map((c) => st[c].loc.start.line).join(',') || '-'}; weight ${TW ? 'ms' : 'lines'}`);
try { execFileSync(process.execPath, ['tests/run_shard.mjs', ...process.argv.slice(4)], { stdio: 'inherit' }); } catch (e) { /* the suite exits 1 when a check fails */ }
