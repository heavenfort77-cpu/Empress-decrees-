# Standards gate: run before anything reaches the owner (owner 25 Nov 12:11)

"I gave you standards to adhere to. Don't say yes and break them. If uncertain of a standard, ask for it."
Every deliverable (build, art sample, report) is checked line by line against this list by the lead, and the answers are written in the log before sending. Any line answered "unsure" means: ASK THE OWNER FOR THE STANDARD before building, never guess.

## Builds
- [ ] Delivered as an HTML file the owner can open (an artifact link is not "playable").
- [ ] Carries the game's current art, motion, audio and VFX (rejected art included in a prototype); box shapes are not playable.
- [ ] Whole player journey works: load -> title -> match -> end -> new run; tested on the exact file sent (standalone probe).
- [ ] Full suite on the exact code: baseline passes kept (only check 42 may fail); new checks mutation-tested.
- [ ] Perf: heaviest scene < 500 draw calls, < 0.5M triangles, tier medium, real-GPU run; nothing blamed on the machine without a control.
- [ ] Plays on phone, laptop, desktop (desktop is master; phone dialled down).

## Art
- [ ] Started from the owner's references: kits (techno-plate, suit_style_kit_v2), research docs, ComfyUI concept (SDXL route, commercial licence), cocolito measurement.
- [ ] The job targets the real problem (premortem: "can this change fix what the owner hates?").
- [ ] Side-by-side with the reference at the same scale, by measurement, close-up AND play size.
- [ ] Lead verdict per option: would the lead ship it at a AAA desktop bar? If no option passes, nothing is sent.
- [ ] Suits (owner 25 Nov 12:1x): Qin court look (black lacquer), each suit distinct for its school (outline first, then the school colour on bindings/trim/accents); the techno-plate kit sets construction quality only, not its steel colour.
- [ ] AAA bar (owner 25 Nov 12:5x): the owner's kits, and a side-by-side against Warframe at the same scale (close-up AND play size).
- [ ] Royal guards 皇家 keep bronze and blue (owner 25 Nov 12:5x); black lacquer is for the nine suits only.
- [ ] Guardian beast, mercury channel, tiger tally: redo only after the playable build is sent (owner 25 Nov 12:5x).
- [ ] Distinct characters, not recolours; Qin materials; reads at play size (value contrast >= 3:1 where measured).
- [ ] One round, then the lead looks, before any further round.
- [ ] Never replace an approved asset without telling the owner; sources kept.

## Reports
- [ ] Every claim carries a run id or log line, read by the lead from the run itself; guesses labelled.
- [ ] Every failure and every skipped item reported; no overselling; no deadline talk.
