# 皇家 guard and 反贼 rebels: art study (cocolito, worker W5, 25 Nov overnight)

Sources, in order: docs/BURNING-PALACE.md (guard and rebel sections), docs/SUITS.md, index.html CONFIG.GUARD / CONFIG.FANZEI (read only),
docs/research/Qin-palace-medieval-tech-fusion.md, art/Qin-Bronze-Castings-Study.md, art/Qin-Palace-Painted-Study.md. ComfyUI concepts are
reference only (never shipped, never traced). Nothing here goes into the game tonight.

## What the game needs from these models (from CONFIG, read 25 Nov 00:2x)
| Type | Key | Radius m | Move | Windup (tell) s | Role read |
|---|---|---|---|---|---|
| 卒 foot soldier | zu | 0.45 | thrust, line 2.6 x 0.8 m | 0.5 | the line; long weapon forward |
| 弩手 crossbowman | nu | 0.45 | volley, mark r 1.6 at 2.5-10 m | 0.8 | stands behind; wide horizontal bow |
| 盾 shieldbearer | dun | 0.6 | shove, circle r 1.8 | 0.5 | front block (arc 60 deg): the shield is the front |
| 车 chariot | che | 0.9 | charge, line 10 x 1.8 m | 0.9 | courtyards; big, low, long |
| 伍长 squad leader | wz | 0.5 | cut, line 2.4 x 1.0 m | 0.5 | buff r 8 m; must read as the leader at a glance |
| 黄巾力士 mob | ls | 0.45 | bootleg move per school, 0.8-1.0 | 0.8 (1.0 mo/yinyang, 0.9 zongheng) | the school copy: weapon shape + patch colour |
| 符水道人 healer | fs | 0.45 | talisman, heal mark r 2.5 | 0.8 | from behind; kill first |
| 死士 assassin | ss | 0.45 | lunge, line 7 m | 0.6 | hides; yellow glint tell |
| 渠帅 leader | qs | 0.55 | cleave, circle r 2.2 | 0.6 | leads; drops the bootleg charge |
Pools: zu 10, nu 6, dun 4, che 2, wz 2, ls 12, fs 2, ss 4, qs 2; squadMax 12 (the room cap). Drawn as instances, about one draw call per type.

## Screen sizes (camera FOV 50, pitch 40; bronze study numbers)
- Fight framing 10.5 m: 110 px/m; wide 22 m: 52 px/m. A 1.7 m unit is 187 px tall at the fight framing, 88 px wide view.
- Smallest detail that reads (6 px): 5.5 cm fight, 11.5 cm wide. So headband tails, plume, banner, weapon heads are at least 12 cm.
- Suits are 2.05 m (the player box). Fodder stays shorter (1.55-1.8 m) so a real suit always out-sizes a fodder unit; leaders are the tallest
  of their squad by their banner (at least 1.15 x the squad's tallest member, top of banner).

## Faction reads (colour is never the only cue)
| Cue | 皇家 guard | 反贼 rebels |
|---|---|---|
| Lower body | tread sled (no legs): a low bronze hull on two lamellar-plate tread belts | legs in wrapped trousers, bare or straw-shod feet |
| Material | cast bronze (bronze_trim sheet) + Qin-black lacquer lamellar, water-blue cord bindings | hemp cloth, patched bootleg plates tied with rope, a yellow headband with two tails |
| Head | a smooth cast bronze face mask under a black cap (officer: the double-tail cap) | bare head, topknot, yellow headband tails; hood on the 死士 |
| Posture | upright, symmetrical, machine-still idle | hunched, asymmetrical, weight shifting |
| Movement | glide, tread belts roll, torso does not bob | walk, arms swing, body bobs |
Value plan (palace study): Qin black lacquer lum 25-40 (matte, roughness 0.8); bronze 70-110; rebel hemp 90-130; headband yellow 140-170.
Units must read at 3:1 against the red floor (lum 55-75): guard read by the bronze hull and mask and the water-blue cords (lum 70-100),
not by the black, which is darker than the floor; rebels by the light hemp and yellow.

## Per-type silhouette plan (flat-black lineup must separate every pair)
- 卒: the base guard: upper torso on the tread sled, a long 戟 (halberd with a side blade) held upright-diagonal, tallest point the weapon.
- 弩手: same base, crossbow held level across the chest (widest horizontal at chest height), a tall bolt case on the back, no long pole.
- 盾: wider sled and torso (r 0.6), a tall rectangular shield with a notched top in front covering the torso; reads as a wall.
- 车: no soldier base: a long, low hull on four treads, a round parasol canopy on a pole (the Qin bronze chariot's canopy) over a driver
  mask, and a bronze ram beam forward; longest and lowest unit.
- 伍长: the base guard at 1.1 x with the double-tail officer cap and a tall signal banner pole on the back with a water-blue banner; a sword.
- 黄巾力士: hunched bulky man, headband tails, mismatched shoulder plates, one school weapon (nine weapon shapes, one per school).
- 符水道人: long robe to the ground (bell shape), a staff with a hanging gourd and yellow talisman strips, no plates.
- 死士: low crouch, hooded, two short blades held back; the blade edges carry the yellow glint (emissive card) as the 0.6 s tell.
- 渠帅: biggest rebel, yellow sash and cape, a tall yellow pennant on the back pole, ring-pommel dao (环首刀).

## Bootleg suits: one mesh, nine variants
- One 力士 body; the patch parts (shoulder plate, chest patch, armband) use material palPatch (a neutral light cloth region of the sheet),
  tinted per school by instance colour (one draw call), colours from the game's COL.schools (what the suits wear in the game today).
- Shape cue per school = the copied weapon (the bootleg move is one move of that school): 儒 sword with a bow on the back, 道 a water gourd and open
  hand fan, 法 a bronze sword with a long guard, 墨 a crossbow, 阴阳 a round taiji disc on a staff, 杂 a seal block on a cord, 名 a bronze wheel,
  纵横 an envoy tally staff with tufts, 农 a plough-hoe. Nine small meshes on the hand bone; one per instance.

## Budgets and build
- Triangles per type (instanced): LOD0 <= 4000, LOD1 <= 1500, LOD2 <= 500. LOD0 skinned; LOD1 and LOD2 static.
- Rig: rigid segments (one bone per vertex) for bronze and plates; automatic weights (bone heat) for rebel cloth (robe, trousers, sleeves).
- Clips (60 fps): idle (loop 2 s), move (loop 1 s), attack (windup = CONFIG windup of its move, then strike and recover). The windup moves the
  weapon tip at least 0.3 m (33 px at the fight framing) and is held readable: the tell is the windup pose.
- Texture: own klad sheet assets/tex/fodder_trim.png (1024 = 4 m, 256 px/m), rows listed in art/tools/fodder_tex.py; bronze parts use the
  approved bronze_trim.png. tex_check rules: density, brush scale 4-15 cm, lum sd 8-30, saturation <= 0.6, and lacquer/cloth value bands.
- Instancing note for the morning merge: rigid binding keeps the bone count small (<= 16) so the game can draw a type as one InstancedMesh
  with a baked bone-matrix texture (per-instance clip time); not built tonight.

## Gates per unit (printed PASS/FAIL by the builder and the viewer)
1-3 LOD0/1/2 triangles in budget; 4 every LOD0 vertex weighted (sum 1); 5 clips idle, move, attack present after GLB re-import;
6 attack windup equals the CONFIG windup and is >= 0.4 s; 7 weapon tip moves >= 0.3 m by the windup; 8 body half-width within 0.7-1.4 x the
CONFIG radius; 9 height in band (guard 1.5-1.85 m, leaders taller than their squad); 10 lineup: flat-black silhouettes at the wide view,
every pair of types differs (IoU < 0.75 after aligning feet); 11 leader banner top >= 1.15 x the tallest squad member.

## Lessons found while building (keep for the merge)
- Weapons stand upright or lean outward at rest: the game camera looks down 40 deg at units that face the player, so a forward-leaning pike
  foreshortened into the body (round 1: the 卒's pike vanished from its flat-black silhouette).
- Same base, different squad roles: the silhouette gate failed on 卒 vs 弩手 (IoU 0.89) until each kept one unique outline feature
  (卒 the tall pike, 弩手 the 1.2 m prod and a lower torso, 盾 the notched shield, 车 the canopy, 伍长 the banner).
- Draw calls: guard types use two materials (bronze sheet + fodder sheet) = 2 calls per type; rebels 1 (力士 2: body + patch, +1 for the
  school weapon mesh; 死士 +1 for the glint). Viewer lineups: guard 5 types 12 calls / 15k tris, rebels 4 types 9 calls / 6k tris
  (run 45442633307 shots.json; one copy per type, not instanced).

## Concepts (ComfyUI run 45435813341, SD 1.5 + LCM, reference only; art/guard/concepts, art/rebels/concepts)
- Guard (16): no image gave treads (SD ignored it). Picked 5103 (one smooth cast figure whose coat flares like a bell, a mask-like head),
  alternates 5115 (ground-length lamellar coat, wide sleeves) and 5112 (black lamellar with blue and bronze trim). Used: the bell coat,
  the flared sleeves, two-tier shoulder plates, the black/blue/bronze split.
- Rebels (16): the prompt's "red patch" pulled most images red. Picked 5204 (ragged hemp mantle over a tunic, wrapped shins), alternates
  5203 (knee tunic, belt, sandals) and 5212 (leader: yellow over-robe on a dark tunic). Used: knee tunic, rag mantle, wrapped shins, the
  leader's yellow over dark. Avoided: 5208 (striped jacket, reads modern), 5211 (turban).

## Verdicts (honest; shots: art/guard/roundN, art/rebels/roundN; textured viewer shots in round2/viewer from the runner)
| Round | Unit(s) | Result | Cause / change |
|---|---|---|---|
| 1 (built before concepts) | 卒 and the guard set | FAIL look: a toy soldier on a bread-loaf sled; treads read as logs; arms thin; pike invisible in the silhouette | built from the plan only; forward pike foreshortened |
| 1 | 黄巾力士 and the rebel set | FAIL look: stick limbs, headband tails read as horns from the front | |
| 2 | guard | PASS with notes: one cast figure in a bell lamellar coat on a bronze tread sled (concept 5103/5115), Qin black plates with water-blue lacing, stamp-band treads, a mask plate on the hull front. Close up the masks are plain and the build is simple; at play size the five roles separate | |
| 2 | rebels | PASS with notes: knee tunic, rag mantle, wrapped shins, broader headband (8 cm), school weapon + patch | |
| 3 | 弩手 only | silhouette vs 卒 IoU 0.75 (at the limit) -> 0.70 by a lower torso and a 1.2 m prod | |
| 3 (lead review) | guard | FAIL look: treads read as log rafts, chariot canopy as a blue parasol, bodies squat at the fight framing | rollers; parasol 1.56 m wide, blue; 4.9 heads |
| 4 (W5b) | guard | better, not yet: track units with links and spoked wheels, but from the front the fender and mudguards made a bronze block; chariot box beige | |
| 5 (W5b) | guard | PASS with notes: link loops show at both ends, black lacquer war chariot with ribbed small canopy, 6.2-6.5 heads | run 45451027192; W5-REPORT round 4-5 |
