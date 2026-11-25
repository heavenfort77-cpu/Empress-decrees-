# Techno-plate armour suit style: handoff

Status (2026-11-12): batch 1 done, waiting for approval. Nothing is in the Style Library.

## What exists
- `gen.py`: one generator, four characters as data (KNIGHT, MAGE, ROGUE, CONSTRUCT). All colours and shading values are in the CONFIG block at the top.
- `check.py`: prints PASS/FAIL per character (height, feet gap, frame edge, colour count, isolated pixels, one piece).
- `out/`: `<name>_1x.png`, `<name>_3x.png`, `lineup_1x.png`, `lineup_4x.png`.

## How to run
`python3 gen.py && python3 check.py` (needs Pillow and numpy).

## Style choices (proposal, not measured from a reference)
- 64 px frame, front view, light from upper left, 1 px outside outline in the darkest tone of the touching material.
- Materials: worn steel, dark gunmetal, brass trim, black ribbed undersuit at joints, one cloth colour per character, one cyan glow.
- Shapes: fluted breastplates, lamed plates, oversized pauldrons and gauntlets, visor glow.

## Batch 2 (2026-11-12), waiting for approval
- New: `KNIGHT96` in `gen.py`, a 96 px knight redrawn (not resized), sword planted in front with both hands on the grip. Files: `out/knight96_1x.png`, `out/knight96_3x.png`.
- Rogue (64 px): peaked hood, larger scarf tail, wider stance, longer angled daggers.
- `out/batch2_compare_1x.png` and `_4x.png`: 96 px knight beside the 64 px rogue.
- `gen_backup_batch1.py`: the script as it was before this batch.
- `check.py` now also checks `knight96` (height limit 72 to 93 for a 96 px frame).

## Known weak points
- Rogue: the daggers are the same steel as the bracers, so they read as long arms.
- Knight 96: belt, forearms and fauld are close in tone and merge a little.
- 64 px knight still has the small side sword (kept unchanged).
- Back view has no reference; it would be an original design.

## Next (only after approval)
1. Mage, rogue and construct at 96 px.
2. Side and back views.
3. Smooth (vector) version of the same four.
