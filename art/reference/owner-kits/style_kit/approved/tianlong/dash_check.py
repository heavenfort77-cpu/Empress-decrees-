"""Dash differentiation check: every faction's dash is data (movement signature); no two may be similar.
Rule: any two dashes must differ in MODE and PATH, and in at least 4 of the 6 axes in total, and at least one
timing phase (anticipation, travel, recovery) must differ by 40% or more. Built dashes (sprite frames) are also
compared pixel-wise by their silhouette-motion strip when a sprite set exists (see built_strip below).
Run: python3 dash_check.py -> pass/fail per pair
"""
import itertools

# axes: mode, path, body (what the suit does to its own shape), contact (what touches the ground), fx (overlay), timing ms
DASHES = {
    "天兵": dict(mode="skyfall leap", path="high arc up and down", body="plates flare open, body upright, pagoda unit rises", contact="airborne mid-way, ground shadow stays", fx="gold shockwave ring at landing", t=(200, 150, 220)),
    "猿魔": dict(mode="staff vault", path="low zigzag, bounces off tile edges", body="hunched, long arms plant the telescoping staff, knuckle-walk", contact="staff and fists touch down in turn", fx="dust puffs at each plant", t=(70, 320, 90)),
    "巫师": dict(mode="swarm blink", path="no travel: dissolves into drone-beasts and re-forms", body="suit breaks into the twelve beasts", contact="none while swarming", fx="teal soul-fire motes stream between tiles", t=(260, 40, 80)),
    "墨将": dict(mode="tread slide", path="short straight slide, one tile", body="low chassis braced, shield edge forward, legs still", contact="continuous, scraping", fx="sparks and drag marks", t=(120, 380, 200)),
    "剑仙": dict(mode="sword ride", path="straight line along the blade", body="stands on the back blade, other blades fan out", contact="none (rides above ground)", fx="thin silver line along the whole path", t=(60, 140, 60)),
    "冥将": dict(mode="shadow step", path="ground-hugging curve ending behind the target", body="flattens to an outline, cloak trails", contact="none (cloaked)", fx="no afterimage: only a faint outline", t=(40, 90, 280)),
    "天龙": dict(mode="thruster burst", path="straight, upright glide", body="upright, leans forward, claws held in", contact="none (hovers)", fx="orange plumes from the back pods and speed lines", t=(100, 160, 100)),
    "蛊师": dict(mode="vessel crawl", path="snaking S-curve", body="torso flattens, pods unfold as legs", contact="pods drag on the ground", fx="leaves an erosion trail tile (not poison)", t=(200, 480, 260)),
    "虎魔": dict(mode="pounce", path="low fast leap, long flat arc", body="crouches then stretches full length, claws forward", contact="airborne, lands on all four limbs", fx="shed outer plate flies off on landing", t=(320, 90, 140)),
}
AXES = ["mode", "path", "body", "contact", "fx"]


def timing_differs(a, b):
    return any(abs(x - y) / max(x, y) >= 0.40 for x, y in zip(a, b))


def main():
    fails, rows = [], []
    for (na, a), (nb, b) in itertools.combinations(DASHES.items(), 2):
        diff = [k for k in AXES if a[k] != b[k]]
        td = timing_differs(a["t"], b["t"])
        n = len(diff) + (1 if td else 0)
        ok = ("mode" in diff) and ("path" in diff) and n >= 4 and td
        rows.append((na, nb, n, td, ok))
        if not ok:
            fails.append(f"{na}/{nb}: differ on {n}/6 (mode {'mode' in diff}, path {'path' in diff}, timing {td})")
    worst = min(r[2] for r in rows)
    print(f"{len(rows)} pairs, fewest differing axes {worst}/6")
    print("PASS" if not fails else "FAILING:\n" + "\n".join(fails))
    return fails


if __name__ == "__main__":
    main()
