#!/bin/sh
# Method 2, version 2: klad pixelises the 3D render into the sprite's own palette, the grid is cleaned, then outline, corner fix, check, export.
K=${KLAD:-/home/claude/klad/src/target/linux/release/klad}
ramps() { b=$1; $K palette $b --add '#14161c' --name ink >/dev/null; for r in "steel #8f99a6 5" "gun #3e4550 3" "brass #b8923e 4" "cloth #2f4a33 3" "leather #8a2f24 2" "glow #5fe6f0 2"; do set -- $r; $K palette $b --ramp $1 --base "$2" --steps $3 >/dev/null; done; }
rm -rf knight3d.klad knight.klad
python3 prep_refs.py
$K new knight3d.klad --pixel 96x96 >/dev/null; ramps knight3d.klad
$K pixelize knight3d.klad --image flat_knight_alpha.png --to l1 --size 92 --at 23,2 >/dev/null
$K pixels knight3d.klad l1 --plain | python3 finish_from_render.py > knight_v2.grid || exit 1
$K new knight.klad --pixel 96x96 >/dev/null; ramps knight.klad
$K pixel knight.klad l1 --grid knight_v2.grid >/dev/null
$K pixel knight.klad l1 --color ink --outline >/dev/null
python3 fix_corners.py "$K" knight.klad
$K export knight.klad --scale 1 -o m2_knight_1x.png >/dev/null && $K export knight.klad --scale 3 -o m2_knight_3x.png >/dev/null
$K check knight.klad | head -1
