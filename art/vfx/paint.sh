#!/bin/bash
# Paint every family with klad from gen_cards.py's ops and export its frames (PNG per frame). Light; run under flock on the small machine.
# Usage: KLAD=<klad binary> OUT=<work dir> paint.sh [family ...]
#   writes $OUT/ops/<family>.jsonl + families.json, $OUT/klad/<family>.klad (the klad sources) and $OUT/frames/<family>/f<n>.png
# Then: python3 -I pack.py $OUT/frames $OUT/ops/families.json <assets/vfx>; checks.py <assets/vfx> <hall_floor.png> <vfx_map.json>
set -e; S=$(cd "$(dirname "$0")" && pwd); K=${KLAD:-/home/claude/kladsrc/src/target/linux/release/klad}; O=${OUT:-/home/claude/vfxp/out}
python3 -I $S/gen_cards.py $O/ops "$@"
FAMS=${@:-$(python3 -c "import json;print(' '.join(json.load(open('$O/ops/families.json'))))")}
for k in $FAMS; do
  read W H N FPS < <(python3 -c "import json;f=json.load(open('$O/ops/families.json'))['$k'];print(f['cell'][0]*f['paintK'],f['cell'][1]*f['paintK'],f['frames'],f['fps'])")
  rm -rf $O/klad/$k.klad $O/frames/$k; mkdir -p $O/klad $O/frames/$k
  $K new $O/klad/$k.klad --width $W --height $H --frames $((N+1)) --fps $FPS >/dev/null
  $K apply $O/klad/$k.klad --file $O/ops/$k.jsonl | tail -1
  for f in $(seq 1 $N); do $K export $O/klad/$k.klad -o $O/frames/$k/f$f.png --frame $f >/dev/null 2>&1; done
  echo "$k painted $N frames ${W}x${H}"
done
