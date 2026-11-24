# Burning Palace: parallel build contract (owner 24 Nov 14:29: "parallel build with one to manage the file")
One INTEGRATOR owns batches-3-5 (index.html, tests/run.mjs) and merges. Builders work on their own branch and worktree, never push batches-3-5.

| Ticket | Branch / worktree | CI lane | Checks | CONFIG block | TEXT prefix |
|---|---|---|---|---|---|
| 02 guard | bp02-guard /home/claude/wt-bp02 | ci-run-bp02 | 300-399 | GUARD | guard_ |
| 03 locks + rivals | bp03-locks /home/claude/wt-bp03 | ci-run-bp03 | 500-599 | PAL_LOCK, PAL_SIM | pal3_ |
| 04 burning | bp04-burn /home/claude/wt-bp04 | ci-run-bp04 | 600-699 | BURN | burn_ |
| 05 full palace | bp05-layout /home/claude/wt-bp05 | ci-run-bp05 | 700-799 | PAL_ROOMS data, PAL_ESC | pal5_ |
| 08 pieces I | bp08-pieces /home/claude/wt-bp08 | ci-run-bp08 | 800-899 | PIECES | piece_ |
| 07 反贼 (after 02 merged) | bp07-fanzei | ci-run-bp07 | 900-999 | FANZEI | fz_ |
| 09 pieces II (after 04 merged) | bp09-burnpieces | ci-run-bp09 | 1000-1099 | PIECES2 | piece2_ |

## Shared names (as built by 01 unless marked)
- Rooms: PAL_ROOMS (data), PAL.rooms / PAL.byId / PAL.cur (runtime), palRoomAt(x, z), palDoor(d, open), enterPalace, leavePalace, endPalace, stepPalace(dt).
- Room fields added by the parallel tickets (each has one owner; others only read):
  - room.locked (03): true while a fight is on; doors stay shut both ways.
  - room.wing (05; 04 reads; until 05 lands, 04 gives the 01 rooms a wing in its own test data).
  - room.fallen, room.warned (04).
  - room.pieces = [{ type, x, z, ... }] (05 places; 08/09 read; until 05 lands, 08 adds pieces to the 01 rooms in its own block).
- Guard spawn (02): spawnSquad(faction, types, x, z, opts) -> squad; faction 'huangjia' now, 'fanzei' later; sides hostile to each other.
- Burning (04): onWingWarn(wing) and onWingFall(wing) are the only entry points; 09 hooks in there. Read-only hook burnState().
- Core seal (03): the core door opens only when the player is the last suit (owner 14:16).
- Announcements (03): palAnnounce(key, args) queues her lines through the existing banner slot; 04/08/09 call it.

## Rules for every builder
- In shared functions (reset/new run, the step loop, hooks, MAP, CONFIG top, TEXT) add ONE call line or ONE block; put your code in your own section next to related code. Don't reorder or reformat what you don't change.
- Royal Rumble behaviour unchanged (each feature switched off outside the palace).
- When done: CI suite green on your branch (only known balance FAILs) + mutation round, then log `BPxx READY <commit> <branch> suite <run> N of N mut <run> N of N` to /home/claude/batch16.log. The integrator merges.
