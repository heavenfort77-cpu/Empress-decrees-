# Empress Decrees (working title) - rules for every session
- At session start attach both repos: heavenfort77-cpu/Empress-decrees- (push) and heavenfort77-cpu/dawnpunk (read, reference for frame rate and bug pitfalls).
- Read HANDOFF.md first, then only the docs/GDD.md section being changed. Do not read the whole codebase; open only the section being changed.
- Jam: Jamference, theme "The Game is Out to Get You". OpenGame rules: desktop browser, mouse and keyboard, static files, index.html at root, no login. Do not talk about the deadline unless the user asks.
- All-new code, systems and art. Never copy B.O.I code, systems or art. Never call this a remake or sequel in any text.
- Credit efficiency: cheap box-and-shape prototype first; art only after the user approves the loop. Small numbered batches; update HANDOFF.md at the end of each batch. One sample, wait for approval.
- Keep all tunables in one CONFIG block with a comment line above each value. Automated pass/fail tests (tests/); report only pass/fail and failing lines; mutation-test new checks.
- 3D budget: under 500 draw calls and 0.5M triangles, tier medium, pixel ratio max 1.25. Per-frame code sits between PERFRAME-BEGIN/END markers and must pass tests/static-check.mjs.
- Build only what the user has said go for; design questions get answers, not builds.
