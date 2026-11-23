# Handoff (2026-11-23). Full GDD: Project "hunter or hunt", doc claude/Remake-GDD-Apex.md
Status: design only, nothing built. Waiting for the user to approve the 儒甲 kit and say "go" for batch 21 (apex fight on boxes).

## Game
3D, computer only. Empress Kaymuse (on screen) sends 10 suits (one per school, player + 9 bots) into a palace arena. Short royale (3-4 min) with her decrees and bombardment that collapses sections for good. Twist: when you are the last suit, the Tiger Demon and 2 four-legged minions hunt you. Kill the Tiger Demon to win. Killing a minion gives its 2 skills to the Tiger Demon. No bombardment or decrees in the apex phase; the core hall never collapses.

## Controls and kits
WASD move, mouse aim, left click attack, Q and E skills, R ultimate. Every suit: 1 attack, 2 skills (mostly dashes, different range/effect, some none), 1 ultimate (charges from kills and shared hits, then cooldown).

## Suits: school + 甲
儒甲 天兵, 道甲 猿魔, 法甲 冥将, 墨甲 墨将, 阴阳甲 天龙, 杂甲 蛊师, 稗甲 巫师, 名甲 剑仙 (sword attack), 纵横甲 (new), 农甲 (new). 稗甲 attacks with calligraphy and painting. Cut order if time runs short: the two new suits, then 3D detail.

## 儒甲 kit (proposal)
Attack: halberd thrust 10 dmg ~0.8 s. Q Skyfall leap: 4 tiles, cd 8 s, ring r1.5, 1.2x attack, 0.5 s stun. E Overdrive: +50% attack and speed 8 s, cd 40 s. R Pagoda fall: range 6, 1 s telegraph, r3, 3x attack, 1.5 s stun, cd 60 s.

## Tiger Demon (apex)
Claw swipe; Pounce (5-tile leap, 320 ms windup); Metal roar (r4, slow 40% 2 s); ultimate Shed the limit (8 s, +40% speed, +30% attack; open: single use below 50% HP). Minions: Stalker (bite, Lunge 3-tile dash, Rend bleed 4 s), Howler (bite, Flank 4-tile curved dash with 0.6 s stun, Howl r5 reveal 5 s, slow 20%).

## Hiding
Silk curtains hide any suit. 猿魔 climbs pillars and beams, hangs above sight lines, ambushes with its staff vault. Shimmer within ~3 m; attack or hit breaks the hide.

## Decrees
~1 per minute, 5 s warning, lasts 30-45 s, one at a time, never damage by themselves, hint at the twist.

## Sims (headless, pass/fail)
Duel matrix; bombardment/collapse fairness (0 unavoidable hits); decree fairness; win share per school; apex phase by kill order; ultimate timing; 猿魔 ambush band.

## Plan
23-26 Nov box prototype (apex fight first, user approves loop), 27 Nov-1 Dec 3D, 2-4 Dec polish and submit (buffer 3 Dec). OpenGame CLI entry before 18 Dec.

## Open
Kaymuse's look and the title; apex ultimate rule; ultimate charge amounts; minion names; organiser answer on eligibility; OpenGame CLI test.
