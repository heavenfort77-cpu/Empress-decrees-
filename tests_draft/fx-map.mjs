// Event table check (PREP-AV draft for INT): node tests_draft/fx-map.mjs [index.html]. Exit 1 on any FAIL; prints FAIL lines and one summary.
// Without index.html (prep branch), the checks that need the game's CONFIG and TEXT print SKIP lines (not counted as passes).
import { readFileSync, existsSync } from 'node:fs';
import { parseFx, FX_ITEMS, UNIT_ITEM, GUARD_ITEM, STINGER_OF } from '../src/fx/fxmap.js';
import { SOUNDS } from '../src/audio/sound.js';
import { OPT_TEXT, OPT_SLIDERS } from '../src/audio/options.js';
const ROOT = new URL('..', import.meta.url).pathname;
const meta = JSON.parse(readFileSync(ROOT + 'assets/vfx/vfx.json', 'utf8'));
const vmap = JSON.parse(readFileSync(ROOT + 'art/vfx/vfx_map.json', 'utf8')).items;
const fails = [], skips = []; let checks = 0;
const ck = (name, bad) => { checks++; for (const b of bad) fails.push(`${name}: ${b}`); };
const cardIdx = {}, rowIdx = {};
Object.keys(meta.effects).forEach((n, i) => { cardIdx[n] = i; });
meta.ramps.rows.forEach((r, i) => { rowIdx[r] = i; });
const P = parseFx(cardIdx, rowIdx);
if (!P.list.length || !vmap.length || !Object.keys(SOUNDS).length) fails.push('counts: nothing to check (passed on nothing)');
// 1. the table parses: every card, row and phase exists.
ck('parse', P.errs);
// 2. every sound named exists in SOUNDS (a wrong name would be silent in play).
ck('sounds', P.list.filter((e) => e.snd && !(e.snd in SOUNDS)).map((e) => `${e.name} -> ${e.snd}`));
ck('stinger sounds', Object.entries(STINGER_OF).filter(([, s]) => !(s in SOUNDS)).map(([k, s]) => `${k} -> ${s}`));
// 3. every item of the effect map (docs/VFX.md, 86) has an item here; 华表 is decoration only (owner 25 Nov 02:25).
const DROPPED = ['huabiao'];
ck('vfx map items', vmap.filter((it) => !(it.id in FX_ITEMS) && !DROPPED.includes(it.id)).map((it) => it.id));
// 4. the map's cards per item appear in the item (tell, release, hit, trail, state cards; '-' none).
const cardsOf = (id) => new Set(P.list.filter((e) => e.item === id).flatMap((e) => e.cards.map((c) => c.card)));
ck('vfx map cards', vmap.filter((it) => it.id in FX_ITEMS).flatMap((it) => ['tell', 'release', 'hit', 'trail', 'state'].map((k) => it[k]).filter((c) => c && c !== '-' && c !== 'none' && !cardsOf(it.id).has(c)).map((c) => `${it.id} lacks ${c}`)));
// 5. every tell card shows for at least 0.4 s (fairness rule) and is held (a loop card with a hold).
ck('tell hold', P.list.filter((e) => e.phase === 'tell' && e.cards.length).filter((e) => !(e.cards[0].h >= 0.4) && e.item !== 'burn_warn').map((e) => `${e.name} h=${e.cards[0].h}`));
ck('tell loops', P.list.filter((e) => e.phase === 'tell' && e.cards.length && e.cards[0].card !== 'smoke').filter((e) => !meta.effects[e.cards[0].card].loop).map((e) => `${e.name} ${e.cards[0].card} has no loop`));
// 6. every gameplay-critical tell has a sound or a card (both for unit and hazard tells).
ck('tell cue', P.list.filter((e) => e.phase === 'tell' && !e.snd && !e.cards.length).map((e) => e.name));
// 7. options strings: every key the menu uses has English text.
const optSrc = readFileSync(ROOT + 'src/audio/options.js', 'utf8');
const used = new Set([...optSrc.matchAll(/\bT\('(\w+)'\)/g)].map((m) => m[1]).concat(OPT_SLIDERS.map((s) => s[0]), ['opt_mute', 'opt_unmute']));
ck('options text', [...used].filter((k) => !(k in OPT_TEXT)).map((k) => `missing ${k}`));
// 8-10 need the game (index.html).
const html = process.argv[2] || ROOT + 'index.html';
if (existsSync(html) && /const TEXT = \{/.test(readFileSync(html, 'utf8'))) {
  const src = readFileSync(html, 'utf8');
  const block = (name) => { const i = src.indexOf('  ' + name + ': {'); if (i < 0) return ''; let d = 0, j = src.indexOf('{', i); for (let k = j; k < src.length; k++) { if (src[k] === '{') d++; else if (src[k] === '}' && --d === 0) return src.slice(j, k + 1); } return ''; };
  const keys = (b) => [...b.matchAll(/^\s{4,6}(\w+): \{/gm)].map((m) => m[1]);
  const moves = keys(block('MOVES')), gmoves = keys(block('moves')), boot = keys(block('bootleg')).map((k) => 'bl_' + k);
  ck('unit moves', moves.concat(['ult']).filter((k) => !(k in UNIT_ITEM)).map((k) => `MOVES.${k} has no item`));
  ck('guard moves', gmoves.concat(boot).filter((k) => !(k in GUARD_ITEM)).map((k) => `GUARD move ${k} has no item`));
  const tb = src.slice(src.indexOf('const TEXT = {'), src.indexOf('};', src.indexOf('const TEXT = {')));
  const tkeys = new Set([...tb.matchAll(/(\w+):\s*'/g)].map((m) => m[1]));
  ck('stinger keys', Object.keys(STINGER_OF).filter((k) => !tkeys.has(k)).map((k) => `TEXT lacks ${k}`));
  ck('options keys in TEXT', Object.keys(OPT_TEXT).filter((k) => !tkeys.has(k)).map((k) => `TEXT lacks ${k}`));
} else skips.push('unit moves', 'guard moves', 'stinger keys', 'options keys in TEXT');
for (const s of skips) console.log('SKIP ' + s + ' (needs index.html with TEXT)');
for (const f of fails) console.log('FAIL ' + f);
console.log(`FX-MAP ${fails.length ? 'FAIL' : 'PASS'} ${checks - new Set(fails.map((f) => f.split(':')[0])).size} of ${checks} checks (${P.list.length} events, ${Object.keys(FX_ITEMS).length} items)${skips.length ? `, ${skips.length} skipped` : ''}`);
process.exit(fails.length ? 1 : 0);
