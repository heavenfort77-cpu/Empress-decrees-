// Batch 17c gates on the real-GPU probe output (INT, 25 Nov): reads perf.txt (ROW and RENDERER lines), prints one GATE line per gate and exits 1
// on any FAIL. Gates (owner rules 31-32, 41; the lead's long-frame limit): every scene measured frames with no page error; the GPU is real; in each
// palace_heavy run (default tier medium): calls < 500, triangles < 0.5M, p95 <= 20 ms (the tier step-down limit), worst frame <= 100 ms,
// geometries and textures flat over the timed window, heap growth <= 10 MB. Usage: node ci_probe/gates17c.mjs perf.txt
import { readFileSync } from 'node:fs';
const txt = readFileSync(process.argv[2] || 'perf.txt', 'utf8');
const rows = txt.split('\n').filter((l) => l.startsWith('ROW ')).map((l) => JSON.parse(l.slice(4)));
const gpu = (txt.split('\n').find((l) => l.startsWith('RENDERER ')) || '');
const G = []; const gate = (name, ok, v) => { G.push(ok); console.log(`GATE ${name} ${v} ${ok ? 'PASS' : 'FAIL'}`); };
gate('rows measured', rows.length > 0, rows.length);
gate('gpu real', gpu.length > 9 && !/NOT a real GPU|swiftshader|llvmpipe|software/i.test(gpu), JSON.stringify(gpu.slice(9, 90)));
for (const r of rows) gate(`${r.scene} frames and no page error`, r.frames > 0 && r.errs === 0, `frames ${r.frames} errs ${r.errs} ${r.err0 || ''}`);
const heavy = rows.filter((r) => r.scene === 'palace_heavy');
gate('heavy runs measured', heavy.length >= 2, heavy.length);
heavy.forEach((r, i) => {
  gate(`heavy#${i + 1} calls < 500`, r.calls > 0 && r.calls < 500, r.calls);
  gate(`heavy#${i + 1} tris < 500k`, r.tris > 0 && r.tris < 500000, r.tris);
  gate(`heavy#${i + 1} p95 <= 20 ms`, r.p95 > 0 && r.p95 <= 20, r.p95);
  gate(`heavy#${i + 1} worst <= 100 ms`, r.worst > 0 && r.worst <= 100, r.worst);
  gate(`heavy#${i + 1} geometries and textures flat`, r.geo0 === r.geoms && r.tex0 === r.texs, `${r.geo0}-${r.geoms} / ${r.tex0}-${r.texs}`);
  gate(`heavy#${i + 1} heap growth <= 10 MB`, r.heap0 >= 0 && r.heap1 - r.heap0 <= 10, `${r.heap0}-${r.heap1}`);
});
const ref = rows.filter((r) => r.scene === 'reference'), fa = (a) => a.reduce((s, r) => s + r.fps, 0) / Math.max(1, a.length);
console.log(`RATIO heavy/reference fps ${(fa(heavy) / Math.max(1e-9, fa(ref))).toFixed(3)} (heavy ${fa(heavy).toFixed(1)}, reference ${fa(ref).toFixed(1)}; reported, not gated)`);
console.log(`GATES ${G.filter(Boolean).length} of ${G.length} pass`);
process.exit(G.every(Boolean) ? 0 : 1);
