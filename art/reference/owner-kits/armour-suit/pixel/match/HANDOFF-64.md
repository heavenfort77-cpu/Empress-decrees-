# Handoff: knight 64x64 from the four 3D renders (front + back stills, idle, walk)
Task (user's brief): 64x64 pixel sprite from the renders, then walk and idle where every pixel is redrawn per frame (no moved layers, no rig); research first.
Script: knight64.py (CONFIG at top: WALK, IDLE, FPS, JUMP). Stills are typed half-grids (FRONT_L/FRONT_R/BACK_L); each frame = the still's text with named rows
changed, handed to klad as its own cel; klad outlines, opens the outline, checks, exports GIF/sheet. Palette = the other user's 13 colours.
Research applied (klad `skill pixel` Animation + Saint11): few strong poses; walk = contact/down/passing per step (bob 0,+1,-1), weight shifts 1 px to the support leg;
legs redrawn per pose (fwd bigger boot, back smaller+darker+raised, lift knee up); keep volume; sub-pixel = highlight shift and glow dip; cloth and blade tip trail one frame.
Outputs in out64/: knight_{front,back}_{1x,6x}.png, knight_{view}_{idle,walk}_{1x,6x}.gif, _sheet.png, .klad, frames/, contact_sheet_4x.png.
Gates (in script): <=13 colours, 0 semi-transparent, not touching frame edge, soles on one row, area within 8%, every frame differs, jump limit.
Not done: side view animation, attack; klad check notes not gone through; motion judged from a contact sheet only (I cannot watch a GIF). Checked only in the code tool.
Earlier front/back attempts: old/v1..v3, draw_views.py (superseded).

## Batch 2: audit against the renders (previous script kept as old/v3/knight64_before_audit.py)
Restored: antenna + light, armpit rondels, elbow discs (front), cuff glow rings, red grip, guard-end glow, tasset chevrons, knee side discs, shin glow lines (front),
calf brass pistons (back), hoses (back), stacks behind the neck (front), glowing line down the blade. Colour fixes: horns and stacks darkest steel (were mid grey),
ankle cuff bright steel (was brass). Walk: shoulder over the supporting leg drops one row each step.
Front 32x60, 12 colours, isolated 12.6%, ink 22%, outline 66%, steel 14/27/32/23/4%. Back 32x60, 12 colours, isolated 7.5%, ink 19%, outline 52%, steel 22/27/29/18/3%.
Gates PASS. klad notes rose (front idle 567, front walk 523, back idle 432, back walk 376): small glow/brass details count as stray pixels; before the audit the front still had 55 stray, 13 corner, 7 banding.
Still missing vs render: pauldron engraving, finger detail, wide crossguard (drawn 12 px), blade width, toe spikes, head vents. Palette is the other user's 13 colours, not sampled from the render.
Not done: side view, upper body beyond shoulder drop, motion watched as a GIF.
