# 01. Mode menu, palace rooms and the context camera
Blocked by: none, can start now

## Outcome
A title/mode menu (The Burning Palace / Royal Rumble) leads into a small box palace of about 5 rooms joined by doors; the player walks room to room; only the current room (and what shows through an open door) is in the scene; the camera zooms out with no enemy in reach and in when one is.

## Acceptance criteria
- [x] Mode menu before the school select; keyboard and 44 px touch; Royal Rumble = today's game unchanged.
- [x] Room graph data (rooms, doors, links) in CONFIG/MAP data; rooms built once at load, attached on entry, detached on leaving; renderer counts show only the current room (+ the one behind an open door).
- [x] Doors show a preview (room type, decree, reward, "something stirs"); walking through a door moves you to the next room.
- [x] Walls block sight (fog and bot vision) inside the palace.
- [x] Context camera: wide with no enemy within reach, tighter when one is, eased over about 0.4 s, manual zoom key overrides; phones start closer.
- [x] Checks: rooms attach/detach (scene counts), door travel, preview text, camera zoom states, mode menu.
- [x] Royal Rumble (parked mode) keeps every existing check green; nothing in it changes.
- [x] Every new hit has a tell >= 0.4 s; new numbers in CONFIG with a comment line; TEXT keys; HUD/DOM only on change; PERFRAME without allocations; pooled and warmed at load.
- [x] Budget in the heaviest room on tier medium: under 500 calls and 0.5M tris, programs and geometry flat; static PASS (ratchet); CI suite with no FAIL except known balance items; mutation round on the new checks (CI); one commit, pushed.

## Notes
Design: docs/BURNING-PALACE.md (owner 24 Nov 13:18-13:44). Heavy runs on GitHub only (CLAUDE.md). No balance tuning (owner: results first).

## Done (BP01, 24 Nov)
CI suite run 45337663804: 190 of 191 (FAIL 42 only, known balance). Mutation run 45338169408: 12 of 12 caught by the named check.
Budget (headless counts, tier medium): heaviest = hall with the court door open, 13 calls / 554 tris; one room per room.
A palace run ends at the core hall for now (prototype end screen); rivals, locks and the apex come with BP03. No rivals or guard yet.
