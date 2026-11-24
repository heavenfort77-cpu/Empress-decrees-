# 10. Room-fit camera and the room-layout minimap
Blocked by: none, can start now (built in parallel on its own branch; the integrator merges)

## Outcome
Owner 24 Nov 15:43: with no enemy in attack distance the camera pulls back to show the whole room, so it reads big and detailed without shrinking or squashing the characters; with an enemy in attack distance it eases in close. The minimap shows the room layout.

## Acceptance criteria
- [ ] Wide (no enemy within attack distance) = as far out as the floor allows, with field of view and pitch never changed (no fisheye, no squash). Floor: the player's body is at least CONFIG minimum height on screen at all four sizes (phone portrait, phone landscape, laptop, ultrawide). Owner 24 Nov 15:46: "reasonable larger character as room can show bit by bit as walk": character size wins over fitting the whole room; floor 120 px at 1080p (36 was too small to make out detail).
- [ ] A room that fits whole above the floor is shown whole (corners and walls on screen with a margin). A bigger room reveals as you walk: the camera follows you with a gentle lead toward your movement direction and the room's open space, and never jumps.
- [ ] Room-only rendering unchanged (nothing extra drawn); budget unchanged.
- [ ] Close: an enemy (rival suit, 皇家 guard, 反贼, awake giant) within the player's attack distance (the kit's longest offensive reach from CONFIG.KITS) and in sight eases the camera to the close framing in about 0.4 s; back to wide after about 1.5 s with none in reach. Never jumps; room changes pan, never cut. Z override (auto, wide, close) kept. Royal Rumble camera unchanged.
- [ ] Minimap shows the room layout: centred on the current room, enlarged, with the neighbouring rooms around it in their real shapes and positions, doors, the current room outlined, warned rooms marked, fallen rooms dark; inside the current room its pieces as icons (lions, 华表, 鼎, mercury, smoke, clocks, vats, dormant giants); your dot. The static layer is redrawn only on change (room, warn/fall, broken vat, giant woken or lost); the dot is drawn on top each frame.
- [ ] Checks 1200-1299: player screen height >= the floor at all 4 sizes, rooms that fit shown whole, smooth follow in big rooms (no step jump), FOV and pitch unchanged, close framing within 0.6 s of an enemy entering reach for each enemy kind, back to wide, Z override, minimap redraw counts and contents per room state, budget unchanged; static PASS; CI suite (only known balance FAILs); mutation round.

## Notes
Design: docs/BURNING-PALACE.md "Camera". Check 405/405b change on purpose (the old fixed wide/close multipliers are replaced by the room fit). Owner decisions: 15:4x floor raised from 36 px; 15:46 character size wins, floor 120 px, big rooms revealed as you walk.
