# Techno-plate knight: everything, and how to rebuild it
Not included on purpose: node_modules (run `npm install three@0.158 esbuild` in 3d/), and the klad program itself
(its licence does not allow passing on a build; get it from github.com/klad-app/klad, branch feature/pixelart, `cargo build --release -p klad-cli`).
The .klad folders here are drawings made with klad and are yours. Credit klad if its output ships in a game; ship PNGs only.
- 3d/                      Three.js model of the four characters. main.js -> `npx esbuild main.js --bundle --minify --format=iife --outfile=bundle.js`,
                           then inline bundle.js into techno_plate_set.html. HANDOFF-3D.md has the details.
- Techno-Plate-Style-Study.md   the style study (status: proposal, not in the Style Library).
- pixel/                   earlier pixel passes (code-drawn, klad v1, klad 2b), animations in anim/, klad_anim/, klad_fluid/. Each has a HANDOFF file.
- pixel/match/             work against the other user's sprite: knight64.py (front/back stills, idle, walk -> out64/),
                           side/side_still.py (side view, current v6 -> side/out/), side/prep_render.py (render through klad pixelize).
                           HANDOFF-64.md, HANDOFF-MATCH.md, side/HANDOFF-SIDE.md. Scripts expect the klad binary path in the KLAD variable.
- The four 3D renders and the other user's GIF are in refs/ (the GIF is another person's art: technique reference only).
All of it was checked only in the code tool.
