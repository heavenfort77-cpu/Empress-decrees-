# Handoff: knight front and back in the other user's sprite style (batch 1, sample for approval)
Reference: /mnt/user-data/uploads/30f03db6-image.gif = 64 px native shown at 6x, 8 frames, 13 colours, sprite 32x61,
isolated 12.0%, ink 24%, outline dark on 58% of edge, steel dark-to-light 16/33/30/18/4%. Technique reference only.
Method now: draw_views.py (CONFIG at top) draws plates as planned shapes with the reference's 13 colours and band rule,
klad holds the grid, adds the outline, checks and exports. Old 3D-capture attempt is in old/ (blobby, dropped).
Run: python3 draw_views.py ; python3 -I stats.py ref_native.png out/knight_front_1x.png out/knight_back_1x.png ; python3 make_strip.py
Results: front 36x62, 13 colours, isolated 5.5%, ink 36%, outline 100%, steel 20/30/29/17/4%, klad check 54 notes.
         back  36x62, 12 colours, isolated 3.0%, ink 34%, outline 100%, steel 25/29/29/15/2%, klad check 46 notes.
Gaps vs reference: too much ink (36 vs 24%), outline fully closed (100 vs 58%), 4 px wider, shapes are boxy rectangles
(reads as a toy robot, not the reference's curved plates), helmet lacks the beast snout, stills only (reference is an 8-frame walk).
Next if approved: open the outline on lit edges, round the plates (polygons instead of rects), thin interior ink, narrow to 32 px,
then walk frames. Checked only in the code tool. klad licence: ship PNGs only, credit klad.
Files: out/knight_{front,back}_{1x,6x}.png, out/knight_{front,back}.klad, out/compare_strip_views.png

## Batch 2 (replaces batch 1 sample; batch 1 kept in old/v1/)
draw_views.py now holds the sprites as typed half-grids (FRONT, BACK overrides), mirrored + relit + one step darker on the far side;
klad lays the grid, outlines, opens the outline (NO_OUTLINE rule), checks, exports. Sword: front at viewer's right, back tip over left shoulder.
Front 32x60, 13 colours, isolated 9.5%, ink 24%, outline 73%, steel 13/26/36/19/7%, klad check 74 notes.
Back  32x60, 12 colours, isolated 7.8%, ink 21%, outline 68%, steel 16/30/33/16/4%, klad check 66 notes.
Reference 32x61, 13, 12.0%, 24%, 58%, 16/33/30/18/4%.
Still open: helmet is a round dome, not the reference's long beast snout/swept horns; 1 px shorter; outline 10-15 points more closed;
stills only (no walk frames); klad check notes not gone through. Checked only in the code tool.

## Batch 3 (helmet, hands, backpack; batch 2 kept in old/v2/)
Helmet: striped swept horns, brass brow, slanted eyes, muzzle with teeth. Hands: both fists on a centre grip, forearms angled in, guard above fists,
blade leans to viewer's right in even 3-row steps (BLADE in CONFIG). Backpack: box with brass-ringed glowing reactor, two brass-capped stacks
(also peeking behind the shoulders in front). Back view has no blade (hidden by the body).
Front 32x60, 12 colours, isolated 11.0%, ink 24%, outline 73%, steel 13/28/34/18/7%, klad check 91 notes.
Back  32x60, 12 colours, isolated 8.3%, ink 21%, outline 65%, steel 21/31/29/16/2%, klad check 61 notes.
Open: blade crosses the knight's left cheek in front; leather red unused (12 colours); outline more closed than reference (58%); stills only.
