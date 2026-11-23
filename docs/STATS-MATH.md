# Stats math for batch 16 (from the owner's two videos, 23 Nov 22:04). Proposal; goes into the batch 16 panel note.

Source (transcribed, faster-whisper base.en):
- Video A "How to tune the Armor formula": taken = damage x K / (K + armor); reduction = armor / (armor + K). K is the designer's choice
  (LoL 100: 100 armor = half; Warcraft 3 about 17; WoW 400 + 85 x attacker level). Tuning: pick the target reduction, pick nice armor numbers, solve K
  (28 armor at 25% gives K 84). Use the attacker's level, never the defender's. Same curve turns any growing stat into a percentage (Genshin mastery).
- Video B "The Simple Math Hiding in Your Favorite Games": flat subtraction breaks on fast hits, damage over time and thorns; linear % needs a hard cap.
  With the K formula the hits you survive grow linearly with armor: effective HP = HP x (1 + armor / K).

Proposal for Empress Decrees (no levels, no gear, 4-5 min runs):
1. Toughness = armor; HP stays 100 for every suit (one bar, one meaning). K = 100. SUITS.md HP column: Low 20, Mid 40, High 70 armor
   (reduction 17% / 29% / 41%; effective HP 120 / 140 / 170; a 25 Q breaks Low in 3.4 hits, Mid 4.0, High 4.9: computed).
2. Mid is the yardstick: every damage number in CONFIG means "what a Mid suit takes"; taken = raw x (K + 40) / (K + armor).
   The placeholder suit and all bots are Mid, so every current number, check and the hunt stay exactly as they are until kits land.
3. Every suit and creature damage goes through it (attacks, skills, bleed, cub and demon moves): fast hits, slow hits and damage over time alike.
   Open for the panel: hazards (statue, lions), drops and the void stay fixed (environment, fairness tells).
4. Growth inside a run stays additive with the 1.4x cap (owner rule). 道甲 R multiplies his ARMOR by up to 1.4 (well defined with this curve,
   unlike a linear %). 法甲 R (hits grow with missing health) and 墨甲 R (nine hits turned back) are unaffected.
5. Speed Low / Mid / High is separate (not in the videos); set in the batch 16 sample.
