# Royal Rumble map: art dressing note (design only, nothing modelled this round)

Owner 25 Nov 13:1x: the Royal Rumble map is un-parked for art. This note says which EXISTING palace kit pieces dress its box layout.
INT integrates it later; the collision boxes, floors and sections in index.html stay as they are (art sits on top, as palace_art.js does).
Layout read from origin/int-17c index.html (MAP DATA, MAP_SCALE 1.5). Counts marked (est.) are estimates from that data, not measured in a build.

## Layout to dress (after MAP_SCALE 1.5)
- Lower layer y 0: core hall 42 x 36 m (walls 7 m, dais, throne, statue), gate neck, courts C1 and C2, west and east courts W2 and E2, four bridges.
- Upper layer y 4 m: terraces W1 and E1 (solid blocks 30 x 30 m), the roof tier 42 x 18 m, six ramps.
- Rails on every edge over the void: about 813 m (est., same edge rule as the game), with 4 broken gaps; 3 altars, 4 lions, the tiger statue.
- 12 collapse sections besides CORE (C1, C2, W1, W2, E1, E2, WB1, WB2, EB1, EB2, ROOF): each falls as one piece.

## Kit pieces per box (all in assets/models/arch unless noted)
| Box today | Dressing | Piece (tris) | Count (est.) |
|---|---|---|---|
| Floors, lower courts | stone_paving.png on the slab top, river_stone.png on slab sides (texture only) | - | 0 |
| Floors, core hall | hall_floor.png (the calmer repaint when COLOUR lands) | - | 0 |
| Floors, bridges | bridge_bay_8 under each 6 m wide bridge (trestle legs into the void), timber deck texture | bridge_bay_8 (194) | 18 |
| Terraces W1, E1 (4 m blocks) | rammed-earth faces with layer lines, stone footing course | wall_earth_seg (12) + terrace_edge (12) | 60 + 60 |
| Roof tier | timber deck on posts and beams over the void; tile eave along its south edge | walk_post (72), walk_beam (12), eave_seg (222), tile_end (28, instanced) | 16, 11, 11, 44 |
| Rails | hollow-brick parapet on courts and terraces; low wall on the roof tier | parapet_seg (18), wall_low (16) | 180, 23 |
| 4 broken gaps | no rail; debris piece at the gap, charred timber stubs (timber_burnt.png) | debris (484) | 4 |
| Core hall walls 7 m | plaster wall with painted band + mural bays behind the throne, pilasters each 4 m | wall_seg (22), wall_mural_seg, pillar (282) | 34, 6, 12 |
| Dais, throne, empress | throne_dais.glb + Kaymuse (this round) | throne_dais (434), kaymuse | 1, 1 |
| Tiger statue | apex tiger.glb in its dormant clip (patina sheet), as the palace core | tiger (existing) | 1 |
| 3 altars (1 m boxes) | 鼎 (lit when charged, dry when empty: its two states already exist) | ding.glb (1,972 / 556 / 184) | 3 |
| 4 lions | guardian beast | beast.glb (6,988 LOD0, LODs exist) | 4 |
| Roof supports (4 cylinders, 18 m) | pillar stacked x4 on a stone base, bronze sleeve at each joint | pillar (282) | 16 |
| Spawn marks, camps | school standards at spawns; signal flags on poles at the gate neck and bridge heads | standard.glb, flag_pole (16) + flag_0-8 (8) | 9, 8 |
| Gate between core and C1 | 阙 pair framing the 12 m neck | que_pair (1,852 LOD0) | 1 |

## Collapsing sections
- Every dressing piece belongs to its floor's section and is parented to the section group, so it falls with it (no new meshes).
- Warning state (COLLAPSE_WARN_S 5 s): swap the section's timber and earth materials to the burnt sheets (timber_burnt, earth_burnt, wall_burnt), the palace's own burn rule; no new geometry.
- Instancing is per section and per piece (one InstancedMesh each), so a falling section moves one group matrix.

## New pieces needed
- None for a first dressed pass. Two gaps to decide after it is seen in the game (not built, not promised):
  1. A ramp side piece: the six ramps have no kit piece for their sloped flanks; a sheared wall_earth_seg (texture-mapped box, 12 tris) would do.
  2. A bridge rail in timber (the hollow-brick parapet is a court piece; on a trestle bridge it is wrong): one 4 m timber rail segment, about 40 tris.

## Cost estimate (est., to be measured by INT in the heaviest scene)
- Triangles: parapets 3.6k + terraces 1.5k + bridges 3.5k + roof tier 5.4k + core walls 4.3k + pillars 4.5k + debris 1.9k + props (3 ding, 4 beasts, tiger, throne, 阙, standards) about 45k at LOD0 = about 70k, far under 0.5M.
- Draw calls: about 14 distinct pieces x up to 12 sections if instanced per section = worst case about 110, typical about 60 (most pieces sit in 3-4 sections), plus props about 25. Budget 500; the Rumble box map today is the baseline to compare in the same run.
- Textures: none new (all sheets already load for the palace); the palace set would have to load for Rumble too (today Rumble disposes it): one loading-plan change for INT to weigh.

## Risks to check when it is integrated
- The palace set load for Rumble adds GPU memory and card time; measure, do not assume.
- 180 parapet instances along void edges: keep them out of the collision set (the invisible rail boxes stay the colliders).
- The roof tier's eave must not hide players under it from the 40 degree camera: eave only on the south edge, facing away from the camera.
