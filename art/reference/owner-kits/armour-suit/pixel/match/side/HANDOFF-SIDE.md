# Handoff: knight side view, 64x64, to the other user's standard (sample for approval)
Read in full: `klad skill pixel` (order of work, clusters, lines, outlines, ramps, shading, AA, animation, what goes wrong, before-you-show list).
Flow: side/prep_render.py cuts the side 3D render (uploads/79bfa46a-image.png) from background and base, faces it right, `klad pixelize` at 58 px tall
with the 13-colour palette -> side/render_px.klad (proportions only; klad's guide: a converted picture is a start, redraw it).
side/side_still.py: SIDE = 58 hand-typed rows (30 wide) placed over those proportions; klad lays the grid, outlines, outline opened by NO_OUTLINE rule, check, export.
Pose is the render's: standing, both fists on the grip, blade point down (the other user's sprite is mid-walk with the blade up).
Measured: mine 28x58, 12 colours, isolated 11.8%, ink 25%, outline 57%, steel 13/26/30/26/5%.
          reference 32x61, 13 colours, isolated 12.0%, ink 24%, outline 58%, steel 16/33/30/18/4%.
klad check: 58 stray, 13 corner, 3 banding. Stray = single-pixel details placed on purpose (glow dots, brass highlights, teeth, notched hem, horn stripes);
corners and banding not fixed yet (list printed by the script).
Not in it: far leg, pauldron engraving, hoses. No animation for the side yet. Checked only in the code tool.
Next if approved: fix the 13 corners, redo front/back to this standard, then side idle + walk frame by frame.
Outputs: side/out/knight_side_{1x,6x}.png, knight_side.klad, compare_side.png (reference | klad conversion of render | mine).

## v2 (after looking at v1 beside the reference; v1 kept as side/side_still_v1.py and out/knight_side_v1_6x.png)
v1 matched the numbers but not the picture: stiff column, ear-like crest, two big ring discs, muddled fists, no far leg, cloth unseen.
v2 follows the reference's pose and big shapes: stride, dark far leg behind, blade upright in front (no outline), two long striped horns,
one glow strip on the pauldron, small elbow/knee discs, green cloth at the back hip, long spiked boot.
v2: 34x59, 13 colours, isolated 11.3%, ink 24%, outline 50%, steel 20/29/25/22/4%. klad check 62 stray, 15 corner, 3 banding (not fixed).
Still weaker than the reference: head is shorter and blunter (snout 3 px shorter, eye glow smaller, mouth too dark), pauldron too tall, hands less clear.

## v4 (current sample; v3 kept as side/side_still_v3.py and out/knight_side_v3_6x.png)
Done in klad's order of work: size 64, the 13-colour palette, silhouette, flat colour, one light from the upper left, outline then opened, clean-up, check.
Changes: neck row so the head lifts clear; lighter jaw and shorter mouth line; far leg in mid tones with brass ankle band and a boot reaching the ground behind;
darkest steel left without outline below row LOW; klad's doubled outline corners erased in a clean-up loop.
v4: 34x60, 13 colours, isolated 10.8%, ink 25%, outline 62%, steel 14/30/31/21/4%. Reference 32x61, 13, 12.0%, 24%, 58%, 16/33/30/18/4%.
klad check: 55 stray (placed details), 13 corner (inside plates, not outline), 5 banding. Not fixed.
Facing check (by reading the shapes, code tool only): snout, teeth, toes, fists and blade point right; horns, stacks, reactor and cloth sit behind.
Status: proposal, waiting for approval. Next if approved: front and back to this standard, then side idle and walk frame by frame.

## v5 (current; v4 kept as side/side_still_v4.py). User said v4 was far off.
Found by printing both sprites as grids side by side: v4 had doubled outlines (typed ink + klad outline), boxed stacks, a vertical near leg and a 3-row dark sole slab.
v5: one outline only (bare() rule), stacks thin and unboxed, legs on the reference's diagonal construction (near leg forward, far leg dark behind), no slab.
Numbers are printed by the script run + stats.py. Status: proposal, waiting for approval.

## v6 (current; v5 kept as side/side_still_v5.py). User feedback on v5: the leg, size of hand.
Hands: fists 5 wide (were 4), lower fist 4 tall, brass cuffs on both, red grip between, pommel under. Legs: bigger knee with disc, near boot 7 rows with segmented toe,
far boot as a dark boxed shape behind. v6: 33x59, 13 colours, isolated 10.9%, ink 20%, outline 59%, steel 18/29/27/22/4%. klad check 58 stray, 21 corner, 3 banding (not fixed).
Status: proposal, waiting for approval.
