# Apex-hunt jam game: GDD and handoff (working title TBD)

Status: updated 2026-11-23 after batch 6. Batches 1-2 approved. Batches 3-5 (box map, map v2, minimap, fog of war, MOBA controls) and batch 6 (apex fight on boxes) built; static PASS, runtime 50 of 50 PASS; waiting for the user's review. All numbers are proposals, tunable in one CONFIG block.
Repo for the code: https://github.com/heavenfort77-cpu/Empress-decrees- (all-new code, nothing from B.O.I).

## Jam facts (checked 2026-11-23)
- Jamference (itch.io), theme "The Game is Out to Get You", restriction "Follow OpenGame Game Jam rules and be entered in one of its categories". Submit by **4 Dec 2026, 4:00 PM (Brunei time)**. Scored equally on Fun, Polish, AI use, Theme. Guidance: fail fast, make it learnable, leave a way out, let the player win. Rule 3: must be built inside the build window; existing projects are not eligible. Rule 7: disclose team (solo, AI built under direction). Rule 5: flag flashing imagery (hit flashes, bombardment) and combat on the page.
- OpenGame rules (https://opengame.io/rules): entries close 18 Dec 2026 11:59 pm PT, submitted through the OpenGame CLI (not yet checked that it can run from the cloud workspace). Individuals 18+, up to 2 entries. Desktop browser only, mouse and keyboard, static files, `index.html` at root, no login, no ads or payments. Must resize across 1920x1080, 1366x768, 2560x1440, 3440x1440, 1024x640. Perf target 45 fps at 1080p, under 50 MB before first frame. Must be a complete game. Judged on creativity, depth, fun, performance, visual fidelity. AI-made assets allowed if the tool's terms permit; credit what needs crediting.
- **Eligibility risk (open):** OpenGame bans remakes of your own earlier games and pre-existing game-specific gameplay, levels or systems. User's position: nothing of the original remains except the base concept of the characters and world. Code, systems, art, kit system, core loop, arena and rules are new. Never call it a remake or sequel on any page. Organiser question drafted, not yet sent, no answer. Assessment: grey area, more likely accepted than not, not certain.
- User confirmed 18+ and individual entry.

## Lore (batch 1, proposal)
- **The world.** An empire in the age of the Hundred Schools (百家争鸣). Each school forged one war suit (甲): hard-surface armour that fights with the school's doctrine. The schools have argued for generations over which doctrine should rule.
- **Kaymuse.** The Empress ends the argument her way: "Let the schools dispute with steel. We shall judge." She calls one suit from each school into her palace. The prize she announces: the surviving school becomes the empire's one doctrine.
- **Kaymuse on screen (user, 23 Nov).** She sits on a throne on a high dais in the core hall and watches the whole royale. Under her throne crouches a great tiger statue: the apex, asleep in metal. She never leaves the throne and cannot be attacked (out of reach on the dais).
- **The truth.** There is no prize. The palace is her hunting ground and the survivor is the meal for her **Tiger Demon**, the statue under her throne. She is "the game" that is out to get you: she sets the rules (decrees), shells the palace, and picks who lives.
- **The minions are the demon's own plates.** When the Tiger Demon sheds an outer plate (its Pounce sheds one), the plate grows legs and becomes a feral cub: Stalker or Howler. A broken plate flies to the nearest strong metal and fuses with it, carrying the cub's tricks.
  - In the royale the demon sleeps as a statue, so a broken plate fuses with the suit that broke it. The player learns: kill a cub, get stronger. Royale cubs are plates Kaymuse peels off the statue ("Our kennels stand open."): a plate cracks off, grows legs, runs to its camp.
  - In the apex phase the statue wakes, so a broken plate flies home to the demon. The same rule now works against you. The plate's flight is always shown, so the flip is visible, not a cheat.
- **Why the core hall never falls.** Her throne and her pet are in it. Kaymuse never shells her own seat.
- **The wake.** When one suit is left, Kaymuse rises, lays a hand on the statue's head and it wakes: cracks glow, it steps down from the dais, two plates peel off as the apex minions. About 3 s, the player watches it happen (the fairness tell). She stays on the throne for the hunt and only taunts.
- **Win, and the ending (user, 23 Nov: "even if the player defeats the apex, he becomes the next apex").** Killing the Tiger Demon is a real win: victory banner, time and stats, recorded as a win. Then the ending plays (about 10-15 s, skippable):
  - The demon falls and all its plates come loose. By the plate rule they fly to the nearest strong metal: the player's suit.
  - The plates close over the suit. It drops to four legs and becomes the new tiger, in the suit's school colour and emblem.
  - Kaymuse sits back down. The new tiger crouches under her throne and turns to metal. Her closing line, then "Hear ye Our decree: ten schools, one answer. Begin." starts over as the credits roll.
  - Both of the user's foreshadow lines pay off here: "The survivor shall be... received." / "The Empress leaveth not her guests alone."
  - Losing to the apex: the player's suit is broken; the old statue goes back under the throne. Short line from her, retry.
- **Panel check.** Critic: "Jam guidance says let the player win; does this take the win away?" Answer: no, the win screen comes first and the stats count; the ending is the theme's last word, not a loss. Player: "Will I want to play again?" Answer (user approved, 23 Nov): the next run's statue and Tiger Demon wear the last winner's school colour and emblem, so you fight what you became. Stored as one value (last winner's school) in browser storage inside try/catch; first run or no storage = the default tiger colour. Material tint and emblem decal only, no new model. CONFIG switch `WINNER_STATUE`.

## Tone brief: Kaymuse (proposal)
- Speaker: only Kaymuse. No narrator.
- Attitude (user, 23 Nov: "always haughty, like every empress and emperor"): imperial and haughty at all times. Speaks of herself as "We / Us / Our" (朕). Uses decree forms ("By Our decree", "It is Our will"). Everyone else is a subject beneath her. Never says please or thanks, never explains herself, never raises her voice; contempt is calm. Imperial register in general, never quoting or naming a real ruler.
- Rule: she never lies outright. Every line is true in a second sense the player only sees after the twist.
- Dread is aimed at her rules and her palace, never at a real school's teaching or a real person.
- Never: modern slang, jokes that break the mood, gore, a shouting villain.
- Length: banner at most 10 words; voice line under 3 s.
- Archaic English (user, 23 Nov): thou/thee/thy for one listener, ye/your for all the schools, -eth and -est verb forms, hath, shalt, art, wert. Kept readable: no invented words, one archaic touch or two per line. Only her voice is archaic; HUD, menus and rule text stay plain modern English.
- Learnability: every decree banner shows a small plain-English rule line and icon under her words (e.g. "No dashing: west courtyard").
- Example lines (proposals): Start: "Hear ye Our decree: ten schools, one answer. Begin." / Collapse: "The west courtyard hath displeased Us." / Kennels: "Our kennels stand open. Take what falleth, if thou canst." / "The survivor shall be... received." (user line, archaic form) / "The Empress leaveth not her guests alone." (user line, archaic form) / Apex start: "Thou soughtest Our answer. Kneel before it."
- Closing line, ending (LOCKED by user 23 Nov): B. "Heaven chose thee. We chose what thou wouldst become." (天选了你，朕选了你的归宿。) Rejected: A, C.
- Wrong for her: "Get wrecked!" (slang) / "Prepare to die, fools!" (shouting villain) / "Please, do your best." (humble) / "Thou hast been most kind." (humble, even if archaic).

## Core
- **Lore:** see Lore above. Kaymuse sits on her throne in the core hall with the apex as a statue under her (her look still TBD).
- **The apex hunt is the game.** A shrunk battle royale is the lead-in. When the player is the last suit alive, the Tiger Demon and 2 minions appear and the hunt begins. Killing the Tiger Demon wins.
- 3D, semi-realistic. Controls (user, 23 Nov): desktop follows LoL/Dota: right-click to move or attack, Q and W skills and R ultimate cast at the cursor (hold to aim, release to cast), A attack-move, S stop. Phone follows MLBB: left thumb stick, ATK button auto-targets the nearest visible enemy, skill buttons: tap = auto-aim, drag = manual aim, drag onto Cancel = no cast.
- Vision (user, 23 Nov): fog of war. Terrain beyond the vision radius (11 m) is dimmed; units beyond it are hidden and cannot be targeted; the minimap shows only what is seen. No full-map view for players.
- Minimap (user, 23 Nov): MOBA corner map, bottom-right on desktop (LoL), top-left on phone (MLBB). Shows floors by layer, warned and fallen sections, camps, lions, altars, active hazard tells, seen units, your path and vision circle. Right-click on it to walk there (desktop).
- Camera (user, 23 Nov): follow camera, pitch 40, distance 14.
- Kit per suit follows Mobile Legends: Bang Bang: 1 attack, 2 skills (mostly dashes of different range and effect, some suits no dash), 1 ultimate. Ultimate unlocks from charge, then cooldown. The Tiger Demon has it from the start.
- Minions: independent, smaller four-legged feral versions of the Tiger Demon, 2 skills each. In the apex phase, killing a minion adds its 2 skills to the apex (up to 6 skills plus ultimate). Royale cubs work the other way (see Royale minions). Intended punishment for beating minions.
- Not a remake: new code, new systems, new art written inside the window. Reuse only general-purpose tools (Three.js).

## Royale changes from B.O.I
Chosen: Kaymuse's decrees; one palace arena with levels, bombardment collapses sections. Not chosen: kills feeding the apex, bot school behaviours, no-truce rule. Dropped from B.O.I: the 64x64 grid, shrinking ring and poison fog, growth pickups, followers, bush and tile-vision rules.

### Royale minions (batch 2, proposal; user: "minions appear for suits to defeat, else no one will have a lead")
Purpose: give a suit a way to pull ahead, so the royale is not ten equal suits trading hits.
- **Spawn.** Kaymuse announces "Our kennels stand open." with the 5 s warning (voice, banner, HUD and map marker). First cub (Stalker) at about 0:40, then a pair (Stalker and Howler) about every 60 s, 3 to 4 waves per royale. Camps sit in zones that collapse later, so taking a camp late is a risk.
- **Behaviour.** Neutral: attacks the nearest suit inside aggro radius 4, returns to camp past radius 8 and heals. Royale cubs use the same kit as the apex minions at lower HP and damage. A solo suit kills one in about 6-8 s, so a second suit can steal it. Last hit claims the plate.
- **Reward: the plate.** Instant +30% ultimate charge, plus a plate buff for 45 s. Stalker plate: hits add a short bleed. Howler plate: shimmer reveal range from 3 m to 6 m and +10% speed. Up to 2 plates at once. All multipliers capped at 1.4x.
- **The leader.** Leader = most plates held, then most kills. Shown on the HUD with a crown marker. The decree "A bounty lieth upon the leader." is the brake: killing the leader gives a big ultimate charge. Keeps a lead from snowballing.
- **Bots** contest camps by role weight (assassin and fighter high, support low), in CONFIG.
- **Apex trigger.** Any royale cubs still alive run back and fuse into the statue as it wakes. Only the 2 apex minions fight in the hunt.
- **Panel check.**
  - Critic: "Won't the flip in the apex phase feel like a cheat?" Answer: the plate flight is shown on every kill in the royale; in the apex phase the first broken plate visibly flies to the demon and Kaymuse says one line about it.
  - Player: "Bots will steal every camp." Answer: sim target, the player claims at least 1 plate in 70% of runs on medium bots.
  - Tech lead: plates, cubs and their effects come from fixed pools; no spawning per kill.
- **CONFIG:** first spawn time, wave interval, cubs per wave, aggro and leash radius, cub HP and damage scale, ult charge per plate, buff length, max plates, bounty charge, bot contest weights. On/off switch: `ROYALE_MINIONS`.
- **Sims:** plate share per school; leader win share (band 25-45%); player plate rate on medium bots; cub deaths caused by collapse.

### Kaymuse's decrees (proposal)
- About one decree a minute (3 to 4 per royale). She is a live opponent: she speaks on screen, and decrees hit the player and the bots alike.
- Each decree is announced with a 5 s warning (voice line, text banner and HUD icon), then lasts 30 to 45 s. One at a time. A decree never causes damage by itself; breaking one costs a small penalty (a brief slow or a mark).
- Draft decrees (her words / plain rule line): "Our altars are dry." / Altars do not heal. "Let none dash within the west courtyard." / No dashing: west courtyard. "A bounty lieth upon the leader." / Bounty on the leader. "Upon the bridges, your arts are stilled." / Skills silenced on bridges. "None shall set foot upon Our roof." / Roof forbidden (standing there draws shells). "Let your ultimates swell twice as swift." / Ultimates charge 2x.
- Foreshadowing: her lines hint at the twist ("The survivor shall be... received", "The Empress leaveth not her guests alone"). Decrees pause in the apex phase; she only taunts.

### Palace arena (proposal)
- One 3D palace, no tile grid. Zones: courtyards (west, east, centre), bridges, a roof tier, and a core hall.
- **Bombardment collapses sections for good.** Every shell wave shows a warning, then a whole section (a bridge span, a courtyard, a roof tier) falls and stays gone. No ring, no fog.
- Collapse order is announced by Kaymuse one wave ahead and telegraphed on the section itself.
- The core hall is never destroyed. It holds Kaymuse's throne dais with the tiger statue under it, and its floor is the apex arena. Bombardment and collapse stop in the apex phase.
- Bridge dashes must not drop the player off the edge by accident (edge clamp).
- Perf: instancing, merged static props, 2 to 3 lights, under 500 draw calls, under 0.5M triangles.

### Box map as built (batch 3, metres, north = -z)
- Core hall x -14..14, z -50..-26, walls, south gate path; throne dais at the north wall, Kaymuse seated, tiger statue at the dais foot (solid). Never falls.
- Centre courtyard C1 (z -20..-6) and C2 (z -6..8); west W1/W2 and east E1/E2 courtyards (x 26..46, z -20..20); two bridges each side (WB1/WB2, EB1/EB2) over the void; roof tier (y 4, z 16..28) reached by a ramp from C2 and side ramps down to W2 and E2.
- Collapse waves (CONFIG.WAVES): roof; south bridges; south courts; north courts with their bridges; C2. Final arena: core hall + C1. First wave at 60 s, then every 40 s, 5 s warning glow, 1.2 s fall.
- Camps (markers only, minions later): W1, E1, roof, C2. 10 spawn discs. Pillars (solid) and silk curtains (walk-through) placed for hiding later.
- Counts on medium (software GPU): follow view 25 calls / 1.4k tris; overview 48 calls / 2.9k tris.

### Map v2 (batch 4, user approved all on 23 Nov)
- 1.5x larger (MAP_SCALE). Upper layer at 4 m: west and east terraces (W1, E1) with ramps up from W2/E2, sloped north bridges up from the centre, and the roof tier. Walking off an upper edge drops you to the layer below (8 damage). Void edges have rails; 4 broken-rail gaps can only throw you off by knockback.
- Tiger statue strikes anyone within 6 m of the throne (0.6 s red ring and glowing eyes first; 30 damage, knockback). 4 stone lions (gate pair and centre bridgeheads) strike within 3.5 m (0.6 s ring; 20 damage).
- 3 incense altars (W1, E1, C2): 8 HP/s while standing, a hit pauses healing 2 s, 40 HP per charge, then dry 30 s. Planned decree: "The altars are dry".

### Hiding (replaces B.O.I bushes; working decision, can change)
- **General cover: silk curtains.** Hanging silks hide any suit standing behind them. Attacking or being hit breaks it.
- **猿魔 (道甲): climb and hang.** The ape climbs pillars and beams and hangs above sight lines, hidden from the ground. Its staff vault drops it onto a target as an ambush. Weakest early, so hiding is how it survives until its stages come.
- A faint shimmer shows within about 3 m; an attack or hit breaks the hide; the decree "the roof is forbidden" counters it. A hidden suit is still hit by shells and collapses.
- 猿魔 has 3 stages, time-based. In a 3 to 4 minute royale they come about once a minute (exact times in CONFIG).

## Ten schools (百家争鸣), suit = school + 甲 (CONFIRMED)
Old names stay as titles so the flavour is kept.
| School | Suit | Title | Role label (ML) |
|---|---|---|---|
| 儒家 | 儒甲 | 天兵 | Fighter |
| 道家 | 道甲 | 猿魔 | Tank |
| 法家 | 法甲 | 冥将 | Assassin |
| 墨家 | 墨甲 | 墨将 | Tank (zone) |
| 阴阳家 | 阴阳甲 | 天龙 | Mage (artillery) |
| 杂家 | 杂甲 | 蛊师 | Mage (control) |
| 小说家 | 稗甲 | 巫师 | Support |
| 名家 | 名甲 | 剑仙 | Marksman |
| 纵横家 | 纵横甲 | new | Control (links two enemies so they share damage) |
| 农家 | 农甲 | new | Support (plants heal or feed it, harvest ultimate) |
Attack methods: 名甲 attacks with the sword (剑); 稗甲 attacks with calligraphy and painting (书画, brush strokes as projectiles or marks). Names stay 名甲 and 稗甲.
Match size: 10 suits, one per school. The player plus 9 bots, royale about 3 to 4 minutes.

## Apex phase (proposal)
- Trigger: the player is the last suit alive. Bombardment and decrees stop. The statue wakes under the throne (about 3 s, see The wake), the 2 minions peel off it, and the hunt starts from the dais. The player is moved to the core hall entrance under a short card if they are elsewhere (open: walk there instead?).
- Panel check. Player: "Can I hit Kaymuse?" No; she is out of reach on the dais, attacks stop at her veil. Tech lead: in the royale throne and statue are one merged static mesh; at the wake the statue is hidden and the live demon (same pose, compiled at load) takes its place, so no first-use freeze.
- Minions flank and harass with their own AI. The apex pushes straight in, one skill at a time with a short gap, each telegraphed.
- Stolen skills keep the minion's look so the player sees what they gave the boss.
- Sim target: no kill order is dominant.
- As built on boxes (batch 6, 23 Nov; numbers in CONFIG): arena is the core hall with the gate sealed; H or the Hunt button starts it until the royale exists. Every enemy move shows its shape for its whole windup (all >= 0.4 s; Pounce 0.5 s, not 320 ms) and hits only a player still inside it. Demon ultimate: one use at half health. A killed minion's plate flies to the demon in 0.9 s and brings both of its skills; stolen moves keep the minion's tell colour. Win and loss freeze the game; retry restarts the hunt. Bot sweep: minions-first is currently the better order for a 0.3 s-reaction bot, so the sim target is not met yet (placeholder player kit).

## Tiger Demon (apex)
Assumption to confirm: a hard-surface beast like the war suits.
| Slot | Name | Effect |
|---|---|---|
| Attack | Claw swipe | short cone, range 1.5 |
| Skill 1 (dash) | Pounce | low flat leap, 5 tiles, damage, sheds an outer plate. Windup 320 ms is the telegraph |
| Skill 2 | Metal roar | radius 4, slows 40% for 2 s, interrupts channels |
| Ultimate | Shed the limit | 8 s frenzy: +40% speed, +30% attack, cannot be stunned or slowed. Open: single use below 50% HP |

## Minions (working names)
| Minion | Attack | Skill 1 | Skill 2 | Apex gains |
|---|---|---|---|---|
| Stalker | bite | Lunge: straight 3-tile dash, damage | Rend: bleed 4 s, stacks | a second dash, bleed on hits |
| Howler | bite | Flank: curved 4-tile dash ending behind the player, 0.6 s stun if it lands | Howl: radius 5, reveals the player through cover 5 s, slows 20% | a stunning flank, reveal through cover |

## Bombardment (proposal)
Telegraphed shells land in waves; a wave ends with a section collapse. Every shell shows a warning circle first; a hit must always be avoidable at human reaction time. CONFIG: warning time, radius, damage, shells per wave, wave interval, sections per wave, collapse warning time.

## Kit sample: 儒甲「天兵」 (balanced fighter, range 1)
| Slot | Name | Effect | Numbers |
|---|---|---|---|
| Attack | Halberd thrust | single target | 10 damage, about 0.8 s |
| Q (dash) | Skyfall leap | arcs to the cursor, untargetable in air, ring on landing | 4 tiles, cd 8 s, ring radius 1.5, 1.2x attack, 0.5 s stun |
| E | Overdrive | +50% attack and speed | 8 s, cd 40 s |
| R | Pagoda fall | pagoda drops on the cursor point (range 6), 1 s telegraph | radius 3, 3x attack, 1.5 s stun, cd 60 s |
Ultimate charges from kills and shared hits; exact amounts TBD. Kits for the other nine come after this one is approved. Dashes all differ; 墨甲 has no dash.

## Sims (headless, pass/fail)
Duel matrix 10x10 plus apex and minions; bombardment and collapse fairness (never dodge, 0.3 s reaction, perfect dodge; target 0 unavoidable hits); decree fairness; 猿魔 ambush win share within band; full match win share per school and length; apex phase by kill order and bot skill; ultimate timing; idle-versus-active. Frame rate on a real GPU is not testable in the cloud workspace.

## Plan to 4 Dec 4 PM (submit with buffer on 3 Dec)
1. 23-26 Nov, boxes. Order set by the user on 23 Nov: lore (batch 1), royale minions (batch 2), box palace map (batch 3, with zones, minion camps and collapse sections), then the apex fight, decrees, hiding, ultimate charge, sims. User approves the loop before 3D.
2. 27 Nov - 1 Dec, 3D: one suit for approval, then the rest. Tiger Demon and minions are hardest. Kaymuse needs one on-screen design. First cuts: the two new schools, then 3D detail.
3. 2-4 Dec: polish, itch page (disclose AI use, team, flashing imagery), release zip, submit. OpenGame CLI entry before 18 Dec.

## Open questions
1. Kaymuse's look (placement decided: throne, apex statue under her). Game title.
2. Apex ultimate: always on cooldown, or single use below 50% HP.
3. Ultimate charge amounts; minion names; Tiger Demon hard-surface.
4. Organiser answer on eligibility; OpenGame CLI test.
5. (closed 23 Nov: lore and minion rules taken as approved; closing line B locked)
6. Royale minions: plate reward as written, or a different reward (for example the suit borrows the cub's skill for 45 s)?

## Working rules (user)
Credit efficiency. Prove the loop with a cheap box prototype before art. Small numbered batches with a handoff file. One sample, wait for approval. Automated pass/fail tests. All tunables in one CONFIG block. Read only the needed section. Do not build until the user says go.