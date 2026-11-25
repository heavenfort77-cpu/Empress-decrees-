// Batch 17a model mutants (each must fail a gate): a dropped clip (guard/zu) and a shifted bone (suits/ru, 5 cm), written uncompressed for the
// encoder to compress like the real files. The decimated mutant is made with the CLI (simplify). Usage: node mut_models.mjs REPO OUTDIR
import { NodeIO } from '@gltf-transform/core';
const [R, O] = process.argv.slice(2), io = new NodeIO();
const a = await io.read(`${R}/assets/models/guard/zu.glb`); a.getRoot().listAnimations()[0].dispose(); await io.write(`${O}/dropclip__guard~zu.glb`, a);
const b = await io.read(`${R}/assets/models/suits/ru.glb`); const j = b.getRoot().listSkins()[0].listJoints()[5]; const t = j.getTranslation(); j.setTranslation([t[0] + 0.05, t[1], t[2]]);
await io.write(`${O}/shiftbone__suits~ru.glb`, b);
console.log('MUTM written: dropclip zu, shiftbone ru joint ' + j.getName());
