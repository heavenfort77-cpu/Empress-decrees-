// SUITANIM: quaternion sign continuity for the movement clips, in place. The glTF exporter writes each sampled bone rotation with its own
// sign (round 1, run 45515328643: 6-9 sign flips per clip although the Blender keys were continuous). q and -q are the same rotation, so
// the pose is unchanged; consistent signs keep every engine's interpolation on the short path. attack/idle are not touched (they must stay
// byte-identical to the approved files). Art tool, not shipped.
// Usage: node art/tools/suit_clip_signfix.mjs DIR [ids]
import { readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
const [DIR, IDARG] = process.argv.slice(2);
const IDS = IDARG ? IDARG.split(',') : ['fa', 'ru', 'dao', 'mo', 'yy', 'za', 'ming', 'zh', 'nong'];
// Clips whose rotation keys are made sign-continuous.
const CLIPS = ['run', 'hit', 'death'];
for (const id of IDS) {
  const p = join(DIR, `${id}.glb`); const buf = new Uint8Array(await readFile(p)); const dv = new DataView(buf.buffer);
  const jl = dv.getUint32(12, true); const json = JSON.parse(new TextDecoder().decode(buf.subarray(20, 20 + jl))); const bin0 = 20 + jl + 8;
  let fixed = 0, shared = 0, dup = 0; const seen = new Set();
  for (const a of json.animations.filter((x) => CLIPS.includes(x.name))) for (const c of a.channels) {
    if (c.target.path !== 'rotation') continue; const oi = a.samplers[c.sampler].output;
    if (seen.has(oi)) { dup++; continue; } seen.add(oi);   // one accessor used by two channels: fixed once
    const acc = json.accessors[oi], bv = json.bufferViews[acc.bufferView]; if (acc.componentType !== 5126 || (bv.byteStride && bv.byteStride !== 16)) { shared++; continue; }
    const off = bin0 + (bv.byteOffset || 0) + (acc.byteOffset || 0);
    for (let k = 1; k < acc.count; k++) {
      let d = 0; for (let j = 0; j < 4; j++) d += dv.getFloat32(off + (k * 4 + j) * 4, true) * dv.getFloat32(off + ((k - 1) * 4 + j) * 4, true);
      if (d < 0) { for (let j = 0; j < 4; j++) dv.setFloat32(off + (k * 4 + j) * 4, -dv.getFloat32(off + (k * 4 + j) * 4, true), true); fixed++; }
    }
  }
  await writeFile(p, buf);
  console.log(`${shared ? 'FAIL' : 'PASS'} ${id} signfix: ${fixed} keys negated in ${CLIPS.join(',')}${dup ? ` (${dup} channels reuse an accessor)` : ''}${shared ? `, ${shared} accessors not float or strided (not touched)` : ''}`);
}
