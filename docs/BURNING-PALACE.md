# The Burning Palace (design note, panel 24 Nov 13:30; waiting for the owner's go)

Owner 24 Nov 13:18-13:28: the map is too small; zoom out in rooms, zoom in at attack range; don't render unseen areas.
Direction chosen: a royale played room by room ("option 1, expand"), with more cannon fodder so rooms are never empty walking.
The current open-map royale stays as a second mode, "Royal Rumble" (owner 13:28: "keep the royal rumble").

## Owner decisions (24 Nov 13:26-13:28)
- Doors show: the room type, the decree in force there, the reward, and "something stirs" (not who), unless the rival was seen or announced.
- No fleeing: doors lock while a fight is on in the room.
- Off-screen rival fights: only Kaymuse's announcements and the traces left behind; the room map shows fallen rooms only.
- Keep Royal Rumble as a second mode (menu choice).
- More cannon fodder (owner 13:26): the 皇家 guard, Kaymuse's own imperial household guard (owner 13:30: 皇家, not 兵家) (below).

## The palace (阿房宫 model)
- A rammed-earth platform over a black lake (the Qin water virtue). Fallen rooms drop into the lake.
- About 25-30 rooms, each 20-60 m: the nine schools' halls on the rim -> courtyards, corridors, gardens -> bridges over the lake -> the core hall (throne, apex). Central axis plus east and west routes.
- Room types change fights: courtyards open (ranged kits, chariots), corridors are chokepoints (墨 wall, 名 lines), gardens have curtains (hiding: 道, 法), bridges (silence decree, knockback into the lake), halls with pillars and an altar.
- About 3-4x today's area, but only the current room and what shows through an open door are in the scene (build once, detach on leaving).

## A run
1. Pick a school (select + random, as built). Each suit starts in its own school's hall.
2. Choose one of 2-3 doors from what they show (above).
3. Entering a room with enemies (fodder or rivals) locks its doors until every enemy there is broken. A locked room is sealed both ways: no one else enters.
4. Out of sight, rivals move room to room, farm fodder and meet each other; their fights are resolved by a simulation seeded per run (deterministic: checks and replays still work), using the measured win shares of the kits, health, plates and meter. She announces each result; the loser drops its plates in that room.
5. Behind a door you may find: an empty room with a reward; fodder; one rival in whatever state it is in; two rivals mid-fight (three-way, locked); the leader with a bounty; the hunter that tracks you between rooms.
6. The burning: about every 40 s she names a wing, 5 s warning, its rooms fall. FAIRNESS RULE: a locked room is never warned; a wave that needs it waits until its fight is over (no unavoidable death behind locked doors).
7. Two suits left: she seals all other doors so the two meet in one hall. The winner opens the core hall: the 兵家 apex.
- Target length 4-5 min (owner 23 Nov 21:28); about 6-10 rooms, 3-5 rivals met in person; no more than about 5 s without something to fight, dodge or choose.

## Cannon fodder: the 皇家 guard (owner 24 Nov 13:30)
Kaymuse's own imperial household guard, not 兵家: the 兵家 is the tiger under her throne; the 皇家 guard is her palace's men-at-arms. Bronze soldiers on treads in her court's black and water-blue (look decided at the art stage, distinct from the cubs, which are the tiger's plates). Every attack shows its tell >= 0.4 s; low damage per hit; numbers in CONFIG.
- 卒 foot soldiers: line thrust; packs of 3-6; die in 2-3 hits.
- 弩手 crossbowmen: volley on a ground marker, from behind the 卒.
- 盾 shieldbearers: block from the front, shove; go around or break with skills.
- 车 chariots (courtyards only): line charge shown on the ground.
- 伍长 squad leader: keeps the 方阵 formation and buffs it; kill it first to break the formation.
- Rewards: ultimate charge (like creep XP; also eases the measured low R use), small heal and short boons; plates stay with the cubs.
- Escalation: rim rooms 1 small squad; near the core 2-3 squads with crossbows and a chariot; her decree can call reinforcements.
- Performance: pooled, drawn as instances (about one draw call per unit type), cap about 12 per room, spawned when the door opens; simple brain (follow formation, one attack).
- Rivals farm them too (off-screen in the simulation, on-screen with the bot brain).

## Camera
- Wide when no enemy is within reach, tighter when one is; eased over about 0.4 s; never jumps. Corridors closer, courtyards wider.
- A manual zoom key overrides it (MOBA players expect a fixed zoom). Phones start closer.
- Walls block sight (pulled forward from batch 18 hiding).

## Reused as built
All nine kits and the bot brain, decrees and their bags, collapses (per room), plates, cubs and boons, leader/bounty/hunter cap, the 兵家 apex, school select, the ultimate meter.

## New work (for tickets after the go)
Room graph and doors with previews; room build/detach; door locks; off-screen simulation (seeded) and announcements; spawning rivals in their current state; the 皇家 guard (5 unit types, formation, pool, instancing); context camera; walls block sight; room minimap; mode menu (Burning Palace / Royal Rumble); checks for each (fairness: no warned locked room; tells; budget per room; determinism per seed).

## Premortem (panel)
- The simulation must feel fair: every off-screen death is announced and leaves a trace.
- Locked doors + burning: the fairness rule above must be a checked invariant.
- Two modes double the test surface: Royal Rumble keeps its current checks; Burning Palace gets its own.
- Map size and room count change pacing again: balance after it is playable (owner rule: results first).
- Phone: room-only rendering helps; fodder instancing must hold the budget in the heaviest room.
