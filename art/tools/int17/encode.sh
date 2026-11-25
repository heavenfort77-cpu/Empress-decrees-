#!/bin/bash
# Batch 17a encoder (runs on a GitHub runner; needs toktx from KTX-Software and npx @gltf-transform/cli). Usage: encode.sh REPO STAGE [mutants]
# Textures: assets/tex/<name>.png -> STAGE/{desk,phone}/{etc1s,uastc}/<name>.ktx2 (phone = 512 px max, Lanczos). Opaque sheets lose their unused alpha.
# Models: assets/models/**.glb -> STAGE/models/<same path> with meshopt + quantisation (position 14, normal 10, texcoord 14, weights 16 bits).
set -uo pipefail
R=$1; S=$2; MUT=${3:-}
SKIP=' bronze_trim star_ceiling '
mkdir -p "$S/src/desk" "$S/src/phone"
python3 "$R/art/tools/int17/prep.py" "$R/assets/tex" "$S/src" "$SKIP"
enc() { # set mode name
  local set=$1 mode=$2 n=$3 in="$S/src/$1/$3.png" out="$S/$1/$2/$3.ktx2"
  mkdir -p "$S/$1/$2"
  case $mode in
    etc1s) toktx --t2 --encode etc1s --clevel 4 --qlevel 255 --genmipmap --assign_oetf srgb "$out" "$in" ;;
    uastc) toktx --t2 --encode uastc --uastc_quality 2 --zcmp 18 --genmipmap --assign_oetf srgb "$out" "$in" ;;
    uastc4) toktx --t2 --encode uastc --uastc_quality 4 --zcmp 18 --genmipmap --assign_oetf srgb "$out" "$in" ;;
  esac || echo "ENCFAIL $set $mode $n"
}
export -f enc; export S
for set in desk phone; do for f in "$S/src/$set"/*.png; do n=$(basename "$f" .png); echo "$set etc1s $n"; echo "$set uastc $n"; echo "$set uastc4 $n"; done; done | xargs -P 4 -L 1 bash -c 'enc $0 $1 $2'
# Mutants (must each fail a gate): quality 1 (reported), red/blue swapped input, blurred input (detail lost), no mips, alpha dropped, posterised input.
if [ -n "$MUT" ]; then
  M="$S/mut"; mkdir -p "$M"
  toktx --t2 --encode etc1s --clevel 0 --qlevel 1 --genmipmap --assign_oetf srgb "$M/q1__hall_floor.ktx2" "$S/src/desk/hall_floor.png"
  toktx --t2 --encode etc1s --clevel 4 --qlevel 255 --genmipmap --assign_oetf srgb "$M/swap__hall_wall.ktx2" "$S/src/mut/swap__hall_wall.png"
  toktx --t2 --encode etc1s --clevel 4 --qlevel 255 --assign_oetf srgb "$M/nomip__pillar.ktx2" "$S/src/desk/pillar.png"
  toktx --t2 --encode etc1s --clevel 4 --qlevel 255 --genmipmap --assign_oetf srgb "$M/noalpha__smoke_card.ktx2" "$S/src/mut/noalpha__smoke_card.png"
  toktx --t2 --encode uastc --uastc_quality 2 --zcmp 18 --genmipmap --assign_oetf srgb "$M/poster__hall_floor.ktx2" "$S/src/mut/poster__hall_floor.png"
  toktx --t2 --encode etc1s --clevel 4 --qlevel 255 --genmipmap --assign_oetf srgb "$M/blur__hall_wall.ktx2" "$S/src/mut/blur__hall_wall.png"
fi
# Models (GT = the gltf-transform command)
GT=${GT:-gltf-transform}; QF="--level medium --quantize-position 14 --quantize-normal 10 --quantize-texcoord 14 --quantize-weight 16"
if [ -n "$MUT" ]; then
  mkdir -p "$S/mutm"
  $GT simplify "$R/assets/models/ding.glb" "$S/mutsrc/decim.glb" --ratio 0.5 --error 0.01 >>"$S/gt.log" 2>&1 && $GT meshopt "$S/mutsrc/decim.glb" "$S/mutm/decim__ding.glb" $QF >>"$S/gt.log" 2>&1
  for f in "$S/mutsrc"/*__*.glb; do $GT meshopt "$f" "$S/mutm/$(basename "$f")" $QF >>"$S/gt.log" 2>&1; done
  ls "$S/mutm"
fi
cd "$R/assets/models"
find . -name '*.glb' | sort | while read -r g; do
  mkdir -p "$S/models/$(dirname "$g")"
  $GT meshopt "$g" "$S/models/$g" $QF >>"$S/gt.log" 2>&1 \
    && echo "MESHOPT ok $g $(stat -c %s "$g") -> $(stat -c %s "$S/models/$g")" || echo "MESHOPT FAIL $g"
done
