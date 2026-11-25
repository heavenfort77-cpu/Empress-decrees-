"""Game-action animations packed from the approved specs: python3 pack_anims.py <suit> <stage|-> <size> act (worker) or pack_anims.py act (all).
prepare(suit, stage, size) does that suit's setup and returns [(game_action, specs, frame_fn)]. Specs keep the approved tables; ms is the last item.
Mapping (game action -> approved animation):  tianbing attack=ATTACK | wushi attack=ATTACK (stun-cast) | tianlong skill=CHANNEL dash=DASH |
jianxian dash=RIDE | mingjiang attack=STRIKE skill=CLOAK dash=DASH | mojiang skill=BUILD | gushi dash=CRAWL | yuanmo none yet."""
import importlib
import tianbing96_views as V

WIND = {}
CONFIG = {"MAP": {"tianbing": ["attack"], "wushi": ["attack"], "tianlong": ["skill", "dash"], "jianxian": ["dash"],
                  "mingjiang": ["attack", "skill", "dash"], "mojiang": ["skill"], "gushi": ["dash"], "yuanmo": ["attack"]}}


def attack_specs():
    return [(s[0], i, s[5]) for i, s in enumerate(V.CONFIG["ATTACK_FRONT"])]


def attack_fn(name, spec, size):
    """the approved halberd/stun-cast frames, same calls as the views script: ops_for + smear, windup remembered per view"""
    view = V.VIEWS[name]
    fname, dy, arm, shf, hal, dur, sm = V.CONFIG[view["attack"]][spec[1]]
    if fname == "idle":
        return dict(T=None)
    T, fist, arm_ops, hide, extra = V.ops_for(view, dy, arm, shf, hal)
    if fname == "windup":
        WIND[name] = (arm_ops, fist, hal)
    ov = None
    if sm:
        cur = (arm_ops, fist, hal); wind = WIND.get(name)
        ov = lambda _v, view=view, sm=sm, wind=wind, cur=cur: V.smear(view, sm, wind, cur)
    return dict(T=T, hide=hide, extra=extra, extra_front=view.get("spear_front", True), overlay=ov,
                overlay_front=bool(sm == "burst" and view.get("spear_front", True)))


def prepare(suit, stage, size):
    if suit == "tianbing":
        if size == "64":
            import tianbing64_views as T64; T64.setup()
        return [("attack", attack_specs(), attack_fn)]
    if suit == "wushi":
        import wushi_views as WV; WV.setup(size)
        return [("attack", attack_specs(), attack_fn)]
    if suit == "mingjiang":
        import mingjiang_views as MV, mingjiang_anims as A
        MV.setup(size); A.SIZE[0] = size
        return [("attack", A.CONFIG["STRIKE"], A.frame_fn), ("skill", A.CONFIG["CLOAK"], A.frame_fn), ("dash", A.CONFIG["DASH"], A.frame_fn)]
    if suit == "mojiang":
        import mojiang_views as MV, mojiang_anims as A
        MV.setup(size); A.SIZE[0] = size
        return [("skill", A.CONFIG["BUILD"], A.frame_fn)]
    if suit == "gushi":
        import gushi_views as GV, gushi_crawl as A
        GV.setup(size); A.SZ["s"] = size; A.SZ["k"] = 1.0 if size == "96" else 59 / 90
        return [("dash", A.CONFIG["CRAWL"], A.frame_fn)]
    if suit == "tianlong":
        import tianlong_views as TV
        TV.setup(size)
        return [("skill", TV.CONFIG["CHANNEL"], TV.frame_fn), ("dash", TV.CONFIG["DASH"], TV.frame_fn)]
    if suit == "jianxian":
        import jianxian_views as JV, jianxian_ride_anim as A
        A.SIZE[0] = size; JV.setup(size)
        return [("dash", A.CONFIG["RIDE"], A.frame_fn)]
    if suit == "yuanmo":
        import yuanmo_views as YV, yuanmo_attack as A
        A.SZ["s"] = size; A.SZ["k"] = 1.0 if size == "96" else 59 / 90; YV.setup(stage, size)
        return [("attack", A.CONFIG["ATTACK"], A.frame_fn)]
    return []
