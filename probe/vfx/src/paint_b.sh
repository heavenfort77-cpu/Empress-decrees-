#!/bin/bash
# Repaint B with klad from the generator's ops; export frames 1..17 (272x208 each). Runs under flock heavy.lock.
set -e; cd /home/claude/vfx; K=/home/claude/kladsrc/src/target/linux/release/klad
python3 -I scripts/gen_painted.py out/A_slash_baked.png x out/B_ops.jsonl
rm -rf out/B_slash.klad out/Bf; mkdir -p out/Bf
$K new out/B_slash.klad --width 272 --height 208 --frames 18 --fps 30 >/dev/null
$K apply out/B_slash.klad --file out/B_ops.jsonl | tail -1
for f in $(seq 1 17); do $K export out/B_slash.klad -o out/Bf/f$f.png --frame $f >/dev/null 2>&1; done
