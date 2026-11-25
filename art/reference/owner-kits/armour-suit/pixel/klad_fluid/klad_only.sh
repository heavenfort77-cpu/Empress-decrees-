#!/bin/sh
# Sprite 2b animated with klad commands only: the sprite is split into pixel layers by body part, and each
# layer is moved by klad's own eased keys. Parts start their moves one or two frames apart (body, then
# shoulders, then head), which is what makes it flow instead of everything stepping at once.
# Every drawing and animation step below is a klad command. Run: sh klad_only.sh
K=${KLAD:-/home/claude/klad/src/target/linux/release/klad}
# ---------------- CONFIG: tune by hand ----------------
FPS=12          # frames a second
LOOP0=12        # the loop that is exported is frames 12 to 23 of a 24-frame timeline (one full cycle after the start)
LIFT=3          # how many pixels a foot lifts in the walk
SWORD_WALK=-4   # how far the sword is held off the ground in the walk (negative = up)
SWORD_BATTLE=-10
SPREAD=2        # legs apart by this many pixels each in the battle stance
# -------------------------------------------------------
PARTS="leg_l leg_r hips body sword shoulders head"

erase() { $K pixel $B $1 --erase --rect $2 --filled >/dev/null; }
base() {  # $1 = bundle: seven part layers cut from sprite 2b, each with its own outline layer underneath all of them
  B=$1; rm -rf $B; $K new $B --pixel 96x96 --frames 24 --fps $FPS >/dev/null
  $K palette $B --add '#14161c' --name ink >/dev/null
  for r in "steel #8f99a6 5" "gun #3e4550 3" "brass #b8923e 4" "cloth #2f4a33 3" "leather #8a2f24 2" "glow #5fe6f0 2"; do set -- $r; $K palette $B --ramp $1 --base "$2" --steps $3 >/dev/null; done
  $K set $B l1 name=ink_leg_l >/dev/null
  for p in leg_r hips body sword shoulders head; do $K add $B layer pixel name=ink_$p >/dev/null; done
  for p in $PARTS; do $K add $B layer pixel name=$p >/dev/null; done
  for p in leg_l leg_r body sword shoulders head; do $K pixel $B $p --grid base_2b.grid >/dev/null; done
  erase leg_l 0,0,96,52;  erase leg_l 44,52,52,44                                   # viewer's left leg
  erase leg_r 0,0,96,52;  erase leg_r 0,52,52,44                                    # viewer's right leg
  $K pixel $B hips --color steel-3 --rect 36,50,24,1 --filled >/dev/null            # a plain band behind the sword guard, seen when the sword is lifted
  $K pixel $B hips --color steel-2 --rect 36,51,24,1 --filled >/dev/null
  erase body 0,0,96,14;   erase body 0,50,96,46;  erase body 21,20,17,1;  erase body 58,20,17,1
  erase sword 0,0,96,50;  erase sword 0,52,44,44; erase sword 52,52,44,44           # guard and blade
  erase shoulders 0,0,96,20; erase shoulders 0,37,96,59; erase shoulders 41,20,14,17; erase shoulders 0,20,21,17; erase shoulders 75,20,21,17
  erase head 0,20,96,76;  erase head 0,0,37,20;   erase head 59,0,37,20
  for p in $PARTS; do $K pixel $B ink_$p --color ink --outline --ref $p >/dev/null; done
}
key() {  # $1 layer, $2 frame, $3.. values: the part and its outline get the same key
  l=$1; f=$2; shift 2
  $K key $B $l --frame $f "$@" --ease in-out >/dev/null; $K key $B ink_$l --frame $f "$@" --ease in-out >/dev/null
}
wave() {  # $1 layer, $2 delay, $3 prop, $4 value A, $5 value B, $6 half period: A at 0, B at half, A at period ... across the timeline
  f=$2; v=$4
  while [ $f -le 30 ]; do key $1 $f $3=$v; f=$((f + $6)); if [ "$v" = "$4" ]; then v=$5; else v=$4; fi; done
}
out() {  # $1 = name: the loop as numbered PNGs at real size and a GIF at 3x
  i=0; while [ $i -lt 12 ]; do $K export $B --frame $((LOOP0 + i)) --scale 1 -o out/$1_$i.png >/dev/null; i=$((i + 1)); done
  $K export $B --gif $LOOP0-$((LOOP0 + 11)) --scale 3 -o out/$1_3x.gif >/dev/null
}

# ---- idle: the body sinks and rises 1 px; shoulders follow a frame later, the head two frames later
base out/idle.klad
wave body 0 y 0 1 6; wave shoulders 1 y 0 1 6; wave head 2 y 0 1 6
out idle

# ---- walk: $1 name, $2 direction (-1 = toward the viewer's left), $3 leading leg, $4 other leg
walk() {
  base out/$1.klad; d=$2
  for p in body shoulders head sword; do key $p 0 x=$d; done
  wave body 0 y 1 0 3; wave shoulders 1 y 1 0 3; wave head 2 y 1 0 3                # low at each footfall, high as a foot passes
  f=1; v=$((SWORD_WALK + 1)); while [ $f -le 30 ]; do key sword $f y=$v; f=$((f + 3)); if [ $v = $SWORD_WALK ]; then v=$((SWORD_WALK + 1)); else v=$SWORD_WALK; fi; done
  for s in 0 12 24; do                                                              # each foot lifts, swings a pixel the way it walks, and comes down
    key $3 $s y=0 x=0;            key $3 $((s + 3)) y=-$LIFT x=$d; key $3 $((s + 6)) y=0 x=0
    key $4 $((s + 6)) y=0 x=0;    key $4 $((s + 9)) y=-$LIFT x=$d; key $4 $((s + 12)) y=0 x=0
  done
  out $1
}
walk walk_left -1 leg_l leg_r
walk walk_right 1 leg_r leg_l

# ---- battle: legs apart, body low and breathing, sword raised and swaying
base out/battle.klad
key leg_l 0 x=-$SPREAD; key leg_r 0 x=$SPREAD
wave body 0 y 2 3 6; wave shoulders 1 y 2 3 6; wave head 2 y 2 3 6
wave sword 0 y $SWORD_BATTLE $((SWORD_BATTLE - 1)) 6
f=0; for v in 0 1 0 -1 0 1 0 -1 0 1 0; do key sword $f x=$v; f=$((f + 3)); done
out battle
for a in idle walk_left walk_right battle; do printf '%s: ' $a; $K check out/$a.klad --frame $LOOP0 | head -1; done
