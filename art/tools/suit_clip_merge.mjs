// Fallback route (SUITANIM): copy the clips run, hit and death from a rebuilt suit GLB into the approved GLB, so the approved meshes and
// the attack/idle clips stay byte-identical by construction. Channels are matched to the approved file's nodes by bone name, and the
// rest pose (joint node translation/rotation/scale) must match or the suit is refused. Art tool, not shipped.
// Usage: node art/tools/suit_clip_merge.mjs NEWDIR OLDDIR OUTDIR [ids]
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';
const [NEW, OLD, OUT, IDARG] = process.argv.slice(2);
const IDS = IDARG ? IDARG.split(',') : ['fa', 'ru', 'dao', 'mo', 'yy', 'za', 'ming', 'zh', 'nong'];
// Clips copied from the rebuilt file.
const CLIPS = ['run', 'hit', 'death'];
// Rest pose tolerance per joint value.
const TOL = 1e-5;
function parse(buf) {
  const dv = new DataView(buf.buffer, buf.byteOffset); const jl = dv.getUint32(12, true);
  const json = JSON.parse(new TextDecoder().decode(buf.subarray(20, 20 + jl))); const bo = 20 + jl;
  return { json, bin: buf.slice(bo + 8, bo + 8 + dv.getUint32(bo, true)) };
}
function pack(g) {
  const js = new TextEncoder().encode(JSON.stringify(g.json)); const jp = (4 - (js.length % 4)) % 4, bp = (4 - (g.bin.length % 4)) % 4;
  const total = 28 + js.length + jp + g.bin.length + bp; const out = new Uint8Array(total); const dv = new DataView(out.buffer);
  dv.setUint32(0, 0x46546c67, true); dv.setUint32(4, 2, true); dv.setUint32(8, total, true); dv.setUint32(12, js.length + jp, true); dv.setUint32(16, 0x4e4f534a, true);
  out.set(js, 20); out.fill(0x20, 20 + js.length, 20 + js.length + jp); const o = 20 + js.length + jp;
  dv.setUint32(o, g.bin.length + bp, true); dv.setUint32(o + 4, 0x004e4942, true); out.set(g.bin, o + 8); return out;
}
await mkdir(OUT, { recursive: true });
let bad = 0;
for (const id of IDS) {
  const n = parse(new Uint8Array(await readFile(join(NEW, `${id}.glb`)))), o = parse(new Uint8Array(await readFile(join(OLD, `${id}.glb`))));
  const oIdx = new Map(o.json.nodes.map((nd, i) => [nd.name, i]));
  let rest = 0;
  for (const j of n.json.skins[0].joints) { const a = n.json.nodes[j], b = o.json.nodes[oIdx.get(a.name)];
    for (const k of ['translation', 'rotation', 'scale']) { const x = a[k] || [], y = (b && b[k]) || []; if (x.length !== y.length || x.some((v, i) => Math.abs(v - y[i]) > TOL)) rest++; } }
  if (rest) { console.log(`FAIL ${id} merge: rest pose differs in ${rest} joint values; not merged`); bad++; continue; }
  const parts = [o.bin]; let off = o.bin.length; off += (4 - (off % 4)) % 4; const pad0 = off - o.bin.length; if (pad0) parts.push(new Uint8Array(pad0));
  const accMap = new Map();
  const copyAcc = (ai) => {
    if (accMap.has(ai)) return accMap.get(ai);
    const a = n.json.accessors[ai], bv = n.json.bufferViews[a.bufferView]; const st = (bv.byteOffset || 0), len = bv.byteLength;
    const bytes = n.bin.subarray(st, st + len); parts.push(bytes); const pad = (4 - (len % 4)) % 4; if (pad) parts.push(new Uint8Array(pad));
    o.json.bufferViews.push({ buffer: 0, byteOffset: off, byteLength: len }); off += len + pad;
    const na = { ...a, bufferView: o.json.bufferViews.length - 1 }; o.json.accessors.push(na); const ni = o.json.accessors.length - 1; accMap.set(ai, ni); return ni;
  };
  o.json.animations = o.json.animations.filter((a) => !CLIPS.includes(a.name));
  for (const c of CLIPS) {
    const a = n.json.animations.find((x) => x.name === c); if (!a) { console.log(`FAIL ${id} merge: ${c} missing in the rebuilt GLB`); bad++; continue; }
    o.json.animations.push({ name: c, samplers: a.samplers.map((s) => ({ input: copyAcc(s.input), output: copyAcc(s.output), interpolation: s.interpolation })),
      channels: a.channels.map((ch) => ({ sampler: ch.sampler, target: { node: oIdx.get(n.json.nodes[ch.target.node].name), path: ch.target.path } })) });
  }
  const bin = new Uint8Array(off); let p = 0; for (const x of parts) { bin.set(x, p); p += x.length; }
  o.json.buffers[0].byteLength = bin.length; o.bin = bin;
  await writeFile(join(OUT, `${id}.glb`), pack(o));
  console.log(`PASS ${id} merge: ${CLIPS.join(',')} copied (${accMap.size} accessors), rest pose same, ${(bin.length / 1024) | 0} KB bin`);
}
console.log(`merge ${IDS.length - bad} of ${IDS.length}`);
