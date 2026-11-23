# Apex-hunt jam game: GDD and handoff (working title TBD)

Status: updated 2026-11-23 evening. Lore v2 and the suits (one per school, docs/SUITS.md) approved by the owner 19:57; nine schools in the match (owner 20:03, 稗甲 not summoned). Batches 1-13 built on boxes (map, controls, apex fight, royale minions, buff creatures, 9 bots, leader and bounty, five bagged decrees, W dash); static PASS, runtime 91 of 91 (batch 13). Batch 14 (10-minute game) stopped by the owner, not built. The owner has not yet said the loop works. All numbers are proposals, tunable in one CONFIG block.
Repo for the code: https://github.com/heavenfort77-cpu/Empress-decrees- (all-new code).

## Jam facts (checked 2026-11-23)
- Jamference (itch.io), theme "The Game is Out to Get You", restriction "Follow OpenGame Game Jam rules and be entered in one of its categories". Submit by **4 Dec 2026, 4:00 PM (Brunei time)**. Scored equally on Fun, Polish, AI use, Theme. Guidance: fail fast, make it learnable, leave a way out, let the player win. Rule 3: must be built inside the build window; existing projects are not eligible. Rule 7: disclose team (solo, AI built under direction). Rule 5: flag flashing imagery (hit flashes, bombardment) and combat on the page.
- OpenGame rules (https://opengame.io/rules): entries close 18 Dec 2026 11:59 pm PT, submitted through the OpenGame CLI (not yet checked that it can run from the cloud workspace). Individuals 18+, up to 2 entries. Desktop browser only, mouse and keyboard, static files, `index.html` at root, no login, no ads or payments. Must resize across 1920x1080, 1366x768, 2560x1440, 3440x1440, 1024x640. Perf target 45 fps at 1080p, under 50 MB before first frame. Must be a complete game. Judged on creativity, depth, fun, performance, visual fidelity. AI-made assets allowed if the tool's terms permit; credit what needs crediting.
- **Eligibility risk (open):** OpenGame bans remakes of your own earlier games and pre-existing game-specific gameplay, levels or systems. Since 23 Nov 19:57 the world framing, the suits (names, titles, roles, kits), systems, arena, rules and art are all designed inside the build window from the history of the Hundred Schools; no earlier game's characters, titles or systems remain. Never call it a remake or sequel on any page. Organiser question drafted, not yet sent, no answer. Assessment: grey area, more likely accepted than not, not certain.
- User confirmed 18+ and individual entry.

## Lore (v2, owner 23 Nov 19:57; panel votes in brackets)
- **The world.** The age of the Hundred Schools (百家争鸣). The court catalogue lists ten schools (九流十家) but counts only nine as streams worth reading (九流): 儒、道、阴阳、法、名、墨、纵横、杂、农. Each of the nine forged one war suit (甲): hard-surface armour that fights with its school's doctrine (docs/SUITS.md). The tenth, the tales school (小说家), is not counted, and Kaymuse does not summon it (owner 23 Nov 20:03). The schools have argued for generations over which doctrine should rule.
- **Kaymuse, the unifier (owner: "in a way Kaymuse is the Qin emperor").** She is the first-emperor archetype, never named and never quoting a real ruler [7-0]. She has already made the warring realms one: one script, one axle width, one measure (书同文，车同轨). The schools are the last thing left to unify. She took for herself a word no one else may speak, 朕 ("We"). Her court wears black and her emblem is water [art stage].
- **Her law and its two handles [6-1].** Her decrees are law (法). She rules with the two handles, reward and punishment (赏罚): the bounty is the reward handle; the slow and mark for breaking a decree is the punishment handle. These names live in her lines and this GDD; the HUD keeps plain words.
- **The summons.** "Let the schools dispute with steel. We shall judge." She calls one suit from each of the nine streams into her palace. The prize she announces: the surviving school becomes the empire's one doctrine.
- **The burning [5-2].** The royale is her burning of the books. The palace courts are the schools' halls; her fire falls on them wave by wave and they collapse for good. Eight doctrines are to be broken in front of her.
- **The tiger tally [6-1].** The tiger statue under her throne is the empire's tiger tally (虎符) made beast: a bronze tiger whose two halves must match before an army may move. Her half sleeps under the throne. "The survivor shall be... received": the last suit standing is meant to become the other half.
- **Kaymuse on screen (user, 23 Nov).** She sits on a throne on a high dais in the core hall and watches the whole royale. Under her throne crouches a great tiger statue: the apex, asleep in metal. She never leaves the throne and cannot be attacked (out of reach on the dais).
- **The truth.** There is no prize. The palace is her hunting ground and the survivor is the meal for her **Tiger Demon**, the statue under her throne. She is "the game" that is out to get you: she sets the rules (decrees), shells the palace, and picks who lives.
- **The minions are the demon's own plates.** When the Tiger Demon sheds an outer plate (its Pounce sheds one), the plate grows legs and becomes a feral cub: Stalker or Howler. A broken plate flies to the nearest strong metal and fuses with it, carrying the cub's tricks.
  - In the royale the demon sleeps as a statue, so a broken plate fuses with the suit that broke it. The player learns: kill a cub, get stronger. Royale cubs are plates Kaymuse peels off the statue ("Our kennels stand open."): a plate cracks off, grows legs, runs to its camp.
  - In the apex phase the statue wakes, so a broken plate flies home to the demon. The same rule now works against you. The plate's flight is always shown, so the flip is visible, not a cheat.
- **Why the core hall never falls.** Her throne and her pet are in it. Kaymuse never shells her own seat.
- **The wake.** When one suit is left, Kaymuse rises, lays a hand on the statue's head and it wakes: cracks glow, it steps down from the dais, two plates peel off as the apex minions. About 3 s, the player watches it happen (the fairness tell). She stays on the throne for the hunt and only taunts.
- **Win, and the ending (user, 23 Nov: "even if the player defeats the apex, he becomes the next apex").** Killing the Tiger Demon is a real win: victory banner, time and stats, recorded as a win. Then the ending plays (about 10-15 s, skippable):
  - The demon falls and all its plates come loose. By the plate rule they fly to the nearest strong metal: the player's suit.
  - The plates close over the suit. It drops to four legs and becomes the new tiger, in the suit's school colour and emblem. The two halves of the tally are whole: even the surviving doctrine becomes the throne's beast.
  - Kaymuse sits back down. The new tiger crouches under her throne and turns to metal. Her closing line, then "Hear ye Our decree: nine schools, one answer. Begin." starts over as the credits roll.
  - Both of the user's foreshadow lines pay off here: "The survivor shall be... received." / "The Empress leaveth not her guests alone."
  - Losing to the apex: the player's suit is broken; the old statue goes back under the throne. Short line from her, retry.
- **Panel check.** Critic: "Jam guidance says let the player win; does this take the win away?" Answer: no, the win screen comes first and the stats count; the ending is the theme's last word, not a loss. Player: "Will I want to play again?" Answer (user approved, 23 Nov): the next run's statue and Tiger Demon wear the last winner's school colour and emblem, so you fight what you became. Stored as one value (last winner's school) in browser storage inside try/catch; first run or no storage = the default tiger colour. Material tint and emblem decal only, no new model. CONFIG switch `WINNER_STATUE`.

## Tone brief: Kaymuse (proposal)
- Speaker: only Kaymuse. No narrator.
- Attitude (user, 23 Nov: "always haughty, like every empress and emperor"): imperial and haughty at all times. Speaks of herself as "We / Us / Our" (朕). Uses decree forms ("By Our decree", "It is Our will"). Everyone else is a subject beneath her. Never says please or thanks, never explains herself, never raises her voice; contempt is calm. Imperial register in general, never quoting or naming a real ruler. She is the unifying first-emperor archetype (lore v2): she speaks of one script, one measure, one law, and of reward and punishment, never of a historical name or event by name.
- Rule: she never lies outright. Every line is true in a second sense the player only sees after the twist.
- Dread is aimed at her rules and her palace, never at a real school's teaching or a real person.
- Never: modern slang, jokes that break the mood, gore, a shouting villain.
- Length: banner at most 10 words; voice line under 3 s.
- Archaic English (user, 23 Nov): thou/thee/thy for one listener, ye/your for all the schools, -eth and -est verb forms, hath, shalt, art, wert. Kept readable: no invented words, one archaic touch or two per line. Only her voice is archaic; HUD, menus and rule text stay plain modern English.
- Learnability: every decree banner shows a small plain-English rule line and icon under her words (e.g. "No dashing: west courtyard").
- Example lines (proposals): Start: "Hear ye Our decree: nine schools, one answer. Begin." / Collapse: "The west courtyard hath displeased Us." / Kennels: "Our kennels stand open. Take what falleth, if thou canst." / "The survivor shall be... received." (user line, archaic form) / "The Empress leaveth not her guests alone." (user line, archaic form) / Apex start: "Thou soughtest Our answer. Kneel before it."
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
- All new: code, systems, suits, art and rules written inside the window. Reuse only general-purpose tools (Three.js).

## Royale structure
One palace arena with two levels; her fire collapses the halls section by section (no shrinking ring); Kaymuse's decrees; cubs from the tiger's plates; buff creatures; nine suits, one per school. Kills do not feed the apex.

### Royale minions (batch 2, proposal; user: "minions appear for suits to defeat, else no one will have a lead")
Purpose: give a suit a way to pull ahead, so the royale is not nine equal suits trading hits.
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
- **As built on boxes (batch 7, 23 Nov; numbers in CONFIG):** waves at 30, 90, 150, 210 s with a 5 s warning; cubs at 80% health and 60% damage, aggro 6 m, leash 12 m, heal at rest; plate flies to the last hitter, two 45 s slots; Stalker plate = bleed on your hits, Howler plate = +10% speed; the ultimate-charge reward is a 30% ultimate cooldown cut until charge exists. Leader and bounty built in batch 11 (below).
- **As built (batch 11, 23 Nov; CONFIG.LEADER, DECREE, BOUNTY):** leader = most plates held now, then kills; a tie keeps the leader; none before 1 plate or 1 kill. HUD line "Leader: <school>" for everyone; gold crown on the leader only when in vision; leader on the minimap in vision, and anywhere during its bounty (owner). Bounty after 25 s of one leader (once per suit), 5 s warning, 40 s; breaking the leader in force resets the breaker's ultimate (stand-in for "big ultimate charge"); ends when the leader is out or loses the lead. Up to 3 bots may target a player leader during its bounty, otherwise 1 (owner; hitting back never capped).
- **Batch 13 (autopilot proxy for a player who reads the kennel banner, 12 seeds):** player took at least 1 plate in 9 of 12 (75%, target 70% met; the old sight-only autopilot 3 of 12); leader win share 2 of 12 with the proxy (below the band). No game change: one cub per camp at every wave (fallback) not needed.
- **Sims:** plate share per school; leader win share (band 25-45%); player plate rate on medium bots; cub deaths caused by collapse. Batch 11 (6 seeds, autopilot player): longest leader won 1 of 6 (below band); player >= 1 plate in 1 of 6 (target 70%, missed).

### Cubs and minions: body and speed (owner, 23 Nov)
- Every cub and minion that moves on the map is a four-legged machine on treads. They are faster than most suits; their other numbers sit at the suits' median (read as health and damage; confirm). On boxes: 6.6 m/s against the suit's 6. Look comes at the art stage.
- Cubs alive at the wake go back to the statue in view of the player: built as plates flying home during the 3 s wake.

### Buff creatures and marble bags (owner, 23 Nov; batch 8 on boxes)
- Two neutral creatures that never attack and give a boon to the last hitter, in the manner of a MOBA jungle crab and river wanderer. Own names, look and code (working names: crab, wanderer).
- Marble-bag rule (draw without putting back, refill when empty, seeded) decides four things: when (25/35/45/55 s), where (6 spots; fallen or warned sections skipped), which boon, and how big (0.5x, 1x, 1x, 1.5x).
- Crab boons: ultimate cooldown cut (stand-in for exp or charge), damage up, heal. Wanderer boons: regen, wider vision, speed. Every stack is capped at 1.4x.
- Bots take plates and boons too (owner, 23 Nov). Open: whether the crab should fight back; final names.

### Kaymuse's decrees (proposal)
- About one decree a minute (3 to 4 per royale). She is a live opponent: she speaks on screen, and decrees hit the player and the bots alike.
- Each decree is announced with a 5 s warning (voice line, text banner and HUD icon), then lasts 30 to 45 s. One at a time. A decree never causes damage by itself; breaking one costs a small penalty (a brief slow or a mark).
- Draft decrees (her words / plain rule line): "Our altars are dry." / Altars do not heal. "Let none dash within the west courtyard." / No dashing: west courtyard. "A bounty lieth upon the leader." / Bounty on the leader. "Upon the bridges, your arts are stilled." / Skills silenced on bridges. "None shall set foot upon Our roof." / Roof forbidden (standing there draws shells). "Let your ultimates swell twice as swift." / Ultimates charge 2x.
- As built (batch 11): one decree slot reused by every decree: queued while another banner shows or a collapse warning starts within 20 s, 5 s warning (voice, banner, rule countdown), then in force. The bounty is the first.
- As built (batch 12; owner 23 Nov, panel votes 15:11): seeded marble bags draw which decree, the first request (35-45 s), the gap after one ends (10-25 s), its length (30-45 s) and the no-dash zone; a draw whose place has fallen is skipped. The bounty keeps its leader trigger and shares the slot (it takes the place of a bagged request not yet told). Bagged decrees run only in a match (with bots).
  - "Our altars are dry." / Altars do not heal: no healing in force (charge kept), discs show the empty look.
  - "Let none dash within the <zone>." / No dashing in <zone>: zone drawn from a bag; floor tinted gold, gold outline on the minimap; a dash cast while standing there breaks it. The placeholder W is a 4 m Dash with its burst on landing (walking rule: rails, walls and the void stop it).
  - "Upon the bridges, your arts are stilled." / No skills on bridges: true silence (no new cast; "Silenced" note, status and greyed buttons; a cast already released still lands). Nothing to break.
  - "None shall set foot upon Our heights." / Stay off the upper level (replaces the roof-only line, which was dead after the roof fell at 60 s): roof, terraces and sloped bridge ends at or above 3 m; standing there breaks it, again every 2 s.
  - "Let your ultimates swell twice as swift." / Ultimates recharge 2x: ultimate cooldowns tick 2x (stand-in until charge exists).
  - Breaking: "Thou art marked." / 30% slow for 2 s and marked 5 s: a red marker over the head; the marked suit is seen by every suit from anywhere (body and minimap); while the player is marked up to 2 bots may target it (the bounty's 3 wins).
  - As built (batch 13a; panel 23 Nov 16:11): the queue only keeps banners apart (no decree warning while a collapse or kennel banner shows or one starts within 5 s); a decree in force runs on through a collapse; gap bag 5-15 s; the bounty counts as a decree (it waits for the gap and a gap follows it); no heights break while standing on a warned section or within 3 s of leaving one.
  - Measured (12 seeded matches, batch 13a): 3-4 decrees told per royale (bounty included), mean warning to warning 50.7 s; no banner over a decree warning; no heights break near a warned section.
- Foreshadowing: her lines hint at the twist ("The survivor shall be... received", "The Empress leaveth not her guests alone"). Decrees pause in the apex phase; she only taunts.

### Palace arena (proposal)
- One 3D palace. Zones: courtyards (west, east, centre), bridges, a roof tier, and a core hall.
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

### Hiding (working decision, can change; batch 18)
- **General cover: silk curtains.** Hanging silks hide any suit standing behind them. Attacking or being hit breaks it.
- **道甲 · 真人: non-action (无为).** Standing still and not attacking for 2 s hides the Daoist anywhere (docs/SUITS.md).
- A faint shimmer shows within about 3 m; an attack or hit breaks the hide. The Howler's Howl reveals hidden suits; a hidden suit on the upper level still breaks "None shall set foot upon Our heights". A hidden suit is still hit by collapses.
- Walls and curtains block sight (vision is a plain radius until this batch).

## Nine schools (九流), suit = school + 甲 (owner 23 Nov 19:57 and 20:03; full kits in docs/SUITS.md)
Each suit's title, role and kit come from its school's own doctrine.
| School | Suit | Title | Role | Doctrine in play |
|---|---|---|---|---|
| 儒家 | 儒甲 | 君子 | Fighter | propriety, rectifying names (strips a leader's plates), benevolence |
| 道家 | 道甲 | 真人 | Evasive duelist | non-action hides it, water dash through suits, yield (parry) |
| 法家 | 法甲 | 廷尉 | Assassin | law binds all: bonus on marked decree-breakers; two handles |
| 墨家 | 墨甲 | 墨守 | Tank (zone), no dash | against aggression: holds ground, walls, crossbow engine |
| 阴阳家 | 阴阳甲 | 五行 | Mage (artillery) | five-phase wheel changes each skill |
| 杂家 | 杂甲 | 门客 | Mage (control) | stores and casts back the last skill that hit it |
| 名家 | 名甲 | 辩者 | Marksman | the sword: flying swords that hang, then strike (paradoxes) |
| 纵横家 | 纵横甲 | 说客 | Control | links two enemies so they share damage; swaps places |
| 农家 | 农甲 | 耕者 | Support (sustain) | plants heal and feed it; harvest ultimate |
Match size: 9 suits, one per school (owner 20:03). The player plus 8 bots (built now: 9 bots; changes in the next code batch). Royale length: owner wants each game about 10 min (batch 14, not built yet); built now: about 3-4 min.

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
| Skill 1 (dash) | Pounce | low flat leap, 7.5 m (CONFIG.MOVES), damage, sheds an outer plate. Windup 0.5 s is the telegraph |
| Skill 2 | Metal roar | radius 4, slows 40% for 2 s, interrupts channels |
| Ultimate | Shed the limit | 8 s frenzy: +40% speed, +30% attack, cannot be stunned or slowed. Open: single use below 50% HP |

## Minions (working names)
| Minion | Attack | Skill 1 | Skill 2 | Apex gains |
|---|---|---|---|---|
| Stalker | bite | Lunge: straight 4.5 m dash, damage | Rend: bleed 4 s, stacks | a second dash, bleed on hits |
| Howler | bite | Flank: dash ending behind the player, 0.6 s stun if it lands | Howl: radius 5, reveals the player through cover 5 s, slows 20% | a stunning flank, reveal through cover |

## Bombardment (proposal)
Telegraphed shells land in waves; a wave ends with a section collapse. Every shell shows a warning circle first; a hit must always be avoidable at human reaction time. CONFIG: warning time, radius, damage, shells per wave, wave interval, sections per wave, collapse warning time.

## Kit sample: 法甲「廷尉」 (assassin; first sample, panel 4-2-1, owner 19:57)
Kit in docs/SUITS.md: passive Law Binds All (bonus on marked suits), Q Pursuit (dash, longer at a marked or low target), W Two Handles (slow a target or speed yourself), R Sentence (delayed strike shown on the ground, grows with the target's missing health). Numbers go in CONFIG at build (batch 16).
Ultimate charges from kills and shared hits; exact amounts TBD (batch 15). Kits for the other nine come after this one is approved. Dashes all differ; 墨甲 has no dash.

### Bots (batch 9, owner go 23 Nov; numbers in CONFIG.BOT)
- 9 bots, one per other spawn, with the player's placeholder kit until school kits exist; all 'average' (0.3 s reaction) for now. They act only through the player's actions and see only their own 11 m.
- Target: the nearest suit they can see; once a bot sees the player it switches to the player and keeps it while seen (owner). Only one bot at a time may target the player for any reason but hitting back (owner, 23 Nov; 3 during a bounty on the player). Bots take plates and boons.
- Pacing (assumption): until 2:00 a bot only answers a suit that hit it; then fights start, radius growing to full vision by 3:40. Measured royale length 3:01-3:31 over 6 seeds.
- End: the player broken (or fallen) = loss banner with the place and New run; the last suit standing wakes the demon (no H key except with ?debug or without bots).

## Sims (headless, pass/fail)
Duel matrix 9x9 plus apex and minions; bombardment and collapse fairness (never dodge, 0.3 s reaction, perfect dodge; target 0 unavoidable hits); decree fairness; 道甲 hide-and-strike win share within band; full match win share per school and length; apex phase by kill order and bot skill; ultimate timing; idle-versus-active. Frame rate on a real GPU is not testable in the cloud workspace.

## Plan to 4 Dec 4 PM (submit with buffer on 3 Dec)
1. 23-26 Nov, boxes. Order set by the user on 23 Nov: lore (batch 1), royale minions (batch 2), box palace map (batch 3, with zones, minion camps and collapse sections), then the apex fight, decrees, hiding, ultimate charge, sims. User approves the loop before 3D.
2. 27 Nov - 1 Dec, 3D: one suit for approval, then the rest. Tiger Demon and minions are hardest. Kaymuse needs one on-screen design. First cuts: 3D detail.
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