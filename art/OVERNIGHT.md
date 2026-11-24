# Overnight asset run, 25 Nov 2026 from 00:15 (owner asleep)

Owner 25 Nov 00:08: "use /cocolito along with current procedures to continue with all asset and suit, ensure follow GDD. If you know it will fail, do it again. Do all; any that have problems deciding, leave to show after all are done."

## Readings the lead took while the owner sleeps (stated here so the morning report can be checked against them)
1. "All asset" = every item in art/ASSET-LIST.md sections A-C (surfaces, architecture pieces, props, giants). "Suit" = the nine school suits of docs/SUITS.md (儒 道 阴阳 法 名 墨 纵横 杂 农). Owner 00:15: the apex Tiger Demon, the 皇家 guard and the 反贼 rebels are in tonight's run as well (the cubs go with the apex: they are its shed plates).
2. Assets are built, textured, rigged and shown on review sheets; they are NOT put into the game tonight (no approvals yet; never hand over a half-finished build). Game integration is a morning decision.
3. suit_style_kit_v2 (Suit Mythology) is art reference (owner 00:15: "it is reference, not telling you to copy; use it if it better matches the design in the GDD"). Its approved suit sheets are looked at for design ideas (silhouettes, plate seams, bronze/green/steel ramps, light from the upper left); no generator code or sprite is copied (repo rule: never copy B.O.I code, systems or art). Where its ideas fit the GDD and the Qin research better than the techno-plate kit, they win.
4. The techno-plate kit (3D armoured set) is used as a technique reference for suits (plate construction, engraving, per-character look table, sculpted-shell heads, its known weak points); our builders are new Blender scripts, not its main.js.
5. ComfyUI concepts (CPU, GitHub runners, branch ci-comfy) are references only; when the owner is asleep the worker picks by the study criteria and keeps the next two candidates for the owner.
6. "If you know it will fail, do it again": each asset gets an honest verdict against its criteria after every round; a failing asset gets up to 3 rounds; still failing after 3 = parked in "Needs owner" with the reason.

## Rules every worker follows
- GDD first (docs/GDD.md, docs/BURNING-PALACE.md, docs/SUITS.md), studies second (art/Qin-Bronze-Castings-Study.md, art/Qin-Palace-Painted-Study.md, docs/research/Qin-palace-medieval-tech-fusion.md, docs/research/Sketchfab-Qin-palace-references.md), references last.
- Owner rules: round where round, sharp where sharp, never square and blocky; not a fluffy cat (round 3); research and concepts are reference only; own designs; Qin materials (no glazed roofs, Ming/Qing, neon, sci-fi panel lines, green patina on live pieces); klad for textures; budgets: props 7k / 2.5k / 800, characters 10-15k with a low LOD, heaviest room under 500 calls and 0.5M triangles.
- Small machine (2 cores, 7 GB): one heavy job at a time (Blender, klad, software renders); ComfyUI only on runners.
- Every asset: script in art/tools/, GLB in assets/models/ (props) or assets/models/suits/, textures in assets/tex/, sources (.klad) in art/src/, review sheet in art/<asset>/roundN/, gates printed PASS/FAIL, honest verdict table in the study.
- Commits: name Claude, noreply@anthropic.com, attribution lines; art files only on batches-3-5 (no game code changes); CI files only on ci-comfy; secret scan before push.
- Log one line per step to /home/claude/overnight.log (prefix W1a/W1b/W1c/W2/W3, LEAD).

## Queue (owner 00:15: "github can't help?" -> heavy jobs run on GitHub runners (workflow art-run, branches ci-art-<w>; route proof run 45435204434), so workers run in parallel; local heavy jobs only under flock /home/claude/heavy.lock; guide /home/claude/RUNNERS.md)
| Worker | Scope | Status |
|---|---|---|
| W1a | C1 guardian beast round 4 (face from ComfyUI round C), C2 鼎 x9 (lit/dry), C3 门海 vat (intact/cracked/shards) | running (00:15) |
| W2 | Surfaces A6-A12, A14-A20 (klad), architecture B1-B11 (Blender), one room scene sheet | running (00:25, branch ci-art-w2) |
| W3 | Nine school suits: study (cocolito), concepts, Blender builder, rig, klad lacquer/lamellar sheet | running (00:25, branch ci-art-w3) |
| W1b | C4 crane and censer, C5 water clock, C6 华表, C9 lamps, C10 bell stand, C11 tiger tally, C7 mercury channel | queued (after W1a: same bronze study) |
| W1c | C8 twelve bronze giants (shared cast body, 12 heads/beams/motifs, patina dormant / brass awake, rig) | queued (after W1a) |
| W4 | Apex Tiger Demon (兵家 bronze tiger, patina dormant / brass awake, three inlaid organ weak points, plates that shed) and its cubs Stalker and Howler (four-legged tread machines) | running (00:26, branch ci-art-w4) |
| W5 | 皇家 guard (卒, 弩手, 盾, 车 chariot, 伍长; bronze on treads, black and water-blue) and 反贼 rebels (黄巾力士, 符水道人, 死士, 渠帅; bootleg suits, yellow headbands, school-colour patches); fodder budget about 4k / 1.5k / 500, instanced | running (00:26, branch ci-art-w5) |

## Needs owner (filled during the night)
