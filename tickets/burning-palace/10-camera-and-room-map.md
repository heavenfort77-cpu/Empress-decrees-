# 10. Room-fit camera and the room-layout minimap
Blocked by: none, can start now (built in parallel on its own branch; the integrator merges)

## Outcome
Owner 24 Nov 15:43: with no enemy in attack distance the camera pulls back to show the whole room, so it reads big and detailed without shrinking or squashing the characters; with an enemy in attack distance it eases in close. The minimap shows the room layout.

## Acceptance criteria
- [x] Wide (no enemy within attack distance) = as far out as the floor allows, with field of view and pitch never changed (no fisheye, no squash). Floor: the player's body is at least CONFIG minimum height on screen at all four sizes (phone portrait, phone landscape, laptop, ultrawide). Owner 24 Nov 15:46: "reasonable larger character as room can show bit by bit as walk": character size wins over fitting the whole room; floor 120 px at 1080p (36 was too small to make out detail).
- [x] A room that fits whole above the floor is shown whole (corners and walls on screen with a margin). A bigger room reveals as you walk: the camera follows you with a gentle lead toward your movement direction and the room's open space, and never jumps.
- [x] Room-only rendering unchanged (nothing extra drawn); budget unchanged.
- [x] Close: an enemy (rival suit, 皇家 guard, 反贼, awake giant) within the player's attack distance (the kit's longest offensive reach from CONFIG.KITS) and in sight eases the camera to the close framing in about 0.4 s; back to wide after about 1.5 s with none in reach. Never jumps; room changes pan, never cut. Z override (auto, wide, close) kept. Royal Rumble camera unchanged.
- [x] Minimap shows the room layout: centred on the current room, enlarged, with the neighbouring rooms around it in their real shapes and positions, doors, the current room outlined, warned rooms marked, fallen rooms dark; inside the current room its pieces as icons (lions, 华表, 鼎, mercury, smoke, clocks, vats, dormant giants); your dot. The static layer is redrawn only on change (room, warn/fall, broken vat, giant woken or lost); the dot is drawn on top each frame.
- [x] Checks 1200-1299: player screen height >= the floor at all 4 sizes, rooms that fit shown whole, smooth follow in big rooms (no step jump), FOV and pitch unchanged, close framing within 0.6 s of an enemy entering reach for each enemy kind, back to wide, Z override, minimap redraw counts and contents per room state, budget unchanged; static PASS; CI suite (only known balance FAILs); mutation round.

## Notes
Design: docs/BURNING-PALACE.md "Camera". Check 405/405b change on purpose (the old fixed wide/close multipliers are replaced by the room fit). Owner decisions: 15:4x floor raised from 36 px; 15:46 character size wins, floor 120 px, big rooms revealed as you walk.

## Result (BP10)
CI suite 45354778479: 250 of 251 (only 42, the known balance item); mutation round 45355776128: 17 of 17 caught by the named check (1207 is a measurement, no mutant). At the 120 px floor no room of the full plan fits whole at any of the 4 sizes (the far wall would show the player under the floor), so every room is revealed as you walk; the whole-room path is proven with a 36 px fixture floor in check 1201. Probe 45354294938 (1080p): wide 14.4 m, player 135 px in the smallest (corr_s 12x14 m) and biggest (fore 48x30 m) room; close 10.5 m, 192 px. Phone landscape: wide 12.1 m, 163 px; close 8.9 m, 232 px. Checks changed on purpose: 405, 405b, 706.
