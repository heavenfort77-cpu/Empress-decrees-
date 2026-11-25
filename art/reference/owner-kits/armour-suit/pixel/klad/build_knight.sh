#!/bin/sh
# Method 2: build the knight in klad from the planned grid, outline it, clear doubled corners in the outline, check, export.
K=${KLAD:-/home/claude/klad/src/target/linux/release/klad}
python3 knight_grid.py > knight.grid || exit 1
rm -rf knight.klad && $K new knight.klad --pixel 96x96 >/dev/null
$K palette knight.klad --add '#14161c' --name ink >/dev/null
for r in "steel #8f99a6 5" "gun #3e4550 3" "brass #b8923e 4" "cloth #2f4a33 3" "leather #8a2f24 2" "glow #5fe6f0 2"; do set -- $r; $K palette knight.klad --ramp $1 --base "$2" --steps $3 >/dev/null; done
$K pixel knight.klad l1 --grid knight.grid >/dev/null
$K pixel knight.klad l1 --color ink --outline >/dev/null
python3 fix_corners.py "$K"
$K export knight.klad --scale 1 -o m2_knight_1x.png >/dev/null && $K export knight.klad --scale 3 -o m2_knight_3x.png >/dev/null
$K check knight.klad | head -1
