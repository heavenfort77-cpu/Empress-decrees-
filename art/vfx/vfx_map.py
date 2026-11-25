# The effect map (VFXP, 25 Nov): every attack and tell in the game (index.html CONFIG.KITS, MOVES, DEMON_ULT, APEX, GUARD.moves, FANZEI,
# STATUE, LION, PIECES, PIECES2, BURN, ALTAR, BOONS; cross-checked against docs/SUITS.md and the sound list in docs/AUDIO.md) mapped to
# the shared cards. Writes vfx_map.json (read by checks.py and the game writer) and the tables for docs/VFX.md.
# Fields: id, who, move (game name), cfg (CONFIG path), windup (s; tells only), tell / release / hit / trail / state = card names,
# ramp = palette row ('caster' = the caster's school row), size = which CONFIG numbers scale the cards, snd = the AUDIO.md sound names.
import json, sys

S = 'caster'
I = []
def add(id, who, move, cfg, ramp, windup=None, tell=None, release=None, hit=None, trail=None, state=None, size='', snd='', note='', repeat=None):
    I.append({k: v for k, v in dict(id=id, who=who, move=move, cfg=cfg, ramp=ramp, windup=windup, tell=tell, release=release, hit=hit, trail=trail,
                                    state=state, size=size, snd=snd, note=note, repeatS=repeat).items() if v not in (None, '')})

# ---- the nine suits (player and bots share the kits); ramp = the caster's school row ----
add('ru_atk', 'ru 儒甲', 'attack 射+数 (cut close, arrow far; every 6th a 3-arrow volley or heavy cut)', 'KITS.ru.attack', S, release='slash', hit='impact', trail='bolt',
    size='slash x1 (heavy cut x1.25); bolt per arrow (3 for the volley)', snd='ru_atk / ru_hit')
add('ru_q', 'ru 儒甲', 'Q 御·五驭 chariot charge (dash)', 'KITS.ru.skills[0]', S, release='thrust', hit='impact', state='smoke', size='thrust length = range 5, width 1.8; smoke = dust at the start', snd='ru_q')
add('ru_w', 'ru 儒甲', 'W 书·六书·正名 brush-seal shot (line)', 'KITS.ru.skills[1]', S, release='thrust', hit='impact', state='aura', size='thrust length = range 8; aura on a sealed suit for seal 4 s', snd='ru_w')
add('ru_r', 'ru 儒甲', 'R 乐·六乐·编钟 bells (3 rings land at 0.6 / 1.3 / 2.0 s)', 'KITS.ru.skills[2]', S, windup=0.6, tell='ring', release='burst', hit='impact',
    size='ring radius 4.5, held until each ring lands (holds 0.6, 0.7, 0.7 s); burst radius 4.5', snd='ru_r')
add('dao_atk', 'dao 道甲', 'attack 水 open-hand strike', 'KITS.dao.attack', S, release='slash', hit='impact', size='slash x0.8, mirrored', snd='dao_atk / dao_hit')
add('dao_q', 'dao 道甲', 'Q 柔 stance (counter to basic attacks)', 'KITS.dao.skills[0]', S, state='shield', hit='burst', size='shield held stance 0.8 s; burst x0.5 on a successful counter', snd='dao_q / dao_counter')
add('dao_w', 'dao 道甲', 'W 不争 stance (counter to skills), flow dash on success', 'KITS.dao.skills[1]', S, state='shield', release='thrust', size='shield held 0.8 s; thrust length = the flow (max 8)', snd='dao_w / dao_counter')
add('dao_r', 'dao 道甲', 'R 反 buff (8 s, grows with counters)', 'KITS.dao.skills[2]', S, state='aura', size='aura held dur 8 s', snd='dao_r')
add('dao_p', 'dao 道甲', 'passive 无为 unseen after 2 s still', 'KITS.dao.wuwei', S, state='smoke', size='smoke x0.6 when he turns unseen (the shimmer stays the game\'s)', snd='')
add('fa_atk', 'fa 法甲', 'attack bronze sword (the approved sample B)', 'KITS.fa.attack', S, release='slash', hit='impact', size='slash x1', snd='fa_atk / fa_hit')
add('fa_q', 'fa 法甲', 'Q 刑无等级 pursuit dash + landing burst', 'KITS.fa.skills[0]', S, release='thrust', hit='burst', size='thrust length = dash (5 / 7.5); burst radius 1.6', snd='fa_q / fa_hit')
add('fa_w', 'fa 法甲', 'W 术·潜御 unseen, first hit exposes', 'KITS.fa.skills[1]', S, state='smoke', hit='ring', size='smoke x0.8 at the cast; ring radius 0.8 under the exposed target for exposeS 3 s', snd='fa_w')
add('fa_r', 'fa 法甲', 'R 势 ring that follows him (6 s)', 'KITS.fa.skills[2]', S, state='ring', size='ring radius 6 held dur 6 s, follows him; aura on him', snd='fa_r')
add('mo_atk', 'mo 墨甲', 'attack 连弩 repeating crossbow bolts', 'KITS.mo.attack', S, trail='bolt', hit='impact', size='bolt x0.8', snd='mo_atk / mo_hit')
add('mo_q', 'mo 墨甲', 'Q 距云梯 the wall (4 s)', 'KITS.mo.skills[0]', S, release='crack', state='smoke', size='crack radius 2 at the wall base when raised; smoke at raise and fall', snd='mo_q')
add('mo_w', 'mo 墨甲', 'W 墨经·衡 the lever (plate shown 0.6 s, then fling)', 'KITS.mo.skills[1]', S, windup=0.6, tell='mark', release='burst', hit='impact', size='mark radius 2.2; burst radius 2.2', snd='mo_w_tell / mo_w')
add('mo_r', 'mo 墨甲', 'R 九距之 nine defences (8 s or 9 blows)', 'KITS.mo.skills[2]', S, state='shield', hit='impact', size='shield held dur 8 s; impact at each blocked blow', snd='mo_r')
add('yy_atk', 'yinyang 阴阳甲', 'attack 两仪 orb (dark / light alternate)', 'KITS.yinyang.attack', S, trail='bolt', hit='impact', size='bolt x1', snd='yy_atk / yy_hit')
add('yy_q', 'yinyang 阴阳甲', 'Q 阴·月 slow orb (slow + drain)', 'KITS.yinyang.skills[0]', S, trail='bolt', hit='burst', size='bolt x1.4; burst radius 0.9', snd='yy_q')
add('yy_w', 'yinyang 阴阳甲', 'W 阳·日 sunburst (shown 0.8 s)', 'KITS.yinyang.skills[1]', S, windup=0.8, tell='mark', release='burst', hit='impact', size='mark radius 2.5; burst radius 2.5', snd='yy_w_tell / yy_w')
add('yy_r', 'yinyang 阴阳甲', 'R 太极 disk (shown 1 s, then 2 x 1.5 s halves)', 'KITS.yinyang.skills[2]', S, windup=1.0, tell='mark', state='ring', hit='impact', size='mark radius 5 for tellS; ring radius 5 held 3 s; impact per burn pulse (0.25 s)', snd='yy_r_tell / yy_r')
add('za_atk', 'za 杂甲', 'attack 议 orb', 'KITS.za.attack', S, trail='bolt', hit='impact', size='bolt x1', snd='za_atk / za_hit')
add('za_q', 'za 杂甲', 'Q 兼儒墨 seal shot (line)', 'KITS.za.skills[0]', S, release='thrust', hit='impact', state='aura', size='thrust length = range 8; aura on a sealed suit for seal 2 s', snd='za_q')
add('za_w', 'za 杂甲', 'W 合名法 blink', 'KITS.za.skills[1]', S, state='smoke', size='smoke x0.8 at both ends', snd='za_w')
add('za_r', 'za 杂甲', 'R 一字千金 casts the stored skill', 'KITS.za.skills[2]', 'caster', note='plays the stored skill\'s own cards in that skill\'s own ramp row (a unit move keeps its unit\'s row)', snd='za_r')
add('ming_atk', 'ming 名甲', 'attack 轮不蹍地 wheel out and back', 'KITS.ming.attack', S, trail='bolt', hit='impact', size='bolt x1 (both ways)', snd='ming_atk / ming_hit')
add('ming_q', 'ming 名甲', 'Q 飞鸟之景 shadow blink', 'KITS.ming.skills[0]', S, state='smoke', size='smoke x0.8 at the start (the shadow stays the game\'s)', snd='ming_q')
add('ming_w', 'ming 名甲', 'W 镞矢之疾 hanging arrowheads (line shown 1 s)', 'KITS.ming.skills[1]', S, windup=1.0, tell='strip', release='thrust', hit='impact', size='strip 8 x 1.2; thrust length 8', snd='ming_w')
add('ming_r', 'ming 名甲', 'R 指不至 pointing never arrives (30 m line, 1 s)', 'KITS.ming.skills[2]', S, windup=1.0, tell='strip', release='thrust', hit='impact', size='strip 30 x 1.4; thrust length 30', snd='ming_r')
add('zh_atk', 'zongheng 纵横甲', 'attack 符节 token shot', 'KITS.zongheng.attack', S, trail='bolt', hit='impact', size='bolt x0.8', snd='zh_atk / zh_hit')
add('zh_q', 'zongheng 纵横甲', 'Q 合纵 the link (cord 5 s)', 'KITS.zongheng.skills[0]', S, hit='impact', state='aura', size='impact on both at the tie; aura on both for dur 5 s; burst x0.5 on both when it snaps (the cord line stays the game\'s)', snd='zh_q')
add('zh_w', 'zongheng 纵横甲', 'W 连横 the swap', 'KITS.zongheng.skills[1]', S, state='smoke', size='smoke x0.8 at both places', snd='zh_w')
add('zh_r', 'zongheng 纵横甲', 'R 不攻自破 circle (shown 5 s)', 'KITS.zongheng.skills[2]', S, state='ring', size='ring radius 6 held dur 5 s', snd='zh_r')
add('nong_atk', 'nong 农甲', 'attack 耒 plough-hoe', 'KITS.nong.attack', S, release='slash', hit='impact', size='slash x0.9', snd='nong_atk / nong_hit')
add('nong_q', 'nong 农甲', 'Q 播百谷 sow', 'KITS.nong.skills[0]', S, state='smoke', size='smoke x0.4 per seed (sprouts stay models)', snd='nong_q')
add('nong_w', 'nong 农甲', 'W 并耕 plough charge (furrow 4 s)', 'KITS.nong.skills[1]', S, release='thrust', state='strip', size='thrust length = range 5; strip = the furrow, range x width 1.6, held furrowS 4 s', snd='nong_w')
add('nong_r', 'nong 农甲', 'R 百草生机 harvest (ring 0.4 s, pulses)', 'KITS.nong.skills[2]', S, state='ring', release='burst', hit='heal', size='ring radius 8 held ringS 0.4; burst radius 3 per pulse; heal on him per sprout', snd='nong_r')
add('nong_p', 'nong 农甲', 'passive 并耕而食 eats a sprout', 'KITS.nong.tiller', S, hit='heal', size='heal x0.8 one loop', snd='')

# ---- the apex Tiger Demon (兵家) and its minions/cubs: water-blue ----
add('apex_wake', 'Tiger Demon', 'wakes (3 s)', 'APEX.wakeS', 'apex', windup=3.0, tell='aura', release='crack', size='aura x1.6 held 3 s; crack radius 3', snd='demon_wake')
add('claw', 'Tiger Demon', 'claw', 'MOVES.claw', 'apex', windup=0.45, tell='ring', release='slash', hit='impact', size='ring radius 2.6; slash x1.3', snd='demon_claw_tell / demon_claw')
add('pounce', 'Tiger Demon', 'pounce (dash line)', 'MOVES.pounce', 'apex', windup=0.5, tell='strip', release='thrust', hit='impact', size='strip 7.5 x 2.2; thrust length 7.5; crack radius 1.5 on landing', snd='demon_pounce_tell / demon_pounce')
add('roar', 'Tiger Demon', 'roar (slow)', 'MOVES.roar', 'apex', windup=0.7, tell='ring', release='burst', size='ring radius 6; burst radius 6', snd='demon_roar_tell / demon_roar')
add('demon_ult', 'Tiger Demon', 'Shed the limit (frenzy 8 s)', 'DEMON_ULT', 'apex', windup=0.8, tell='aura', release='burst', state='aura', size='aura x1.6 held windup then dur 8; burst radius 3', snd='demon_ult_tell')
add('bite', 'Stalker / Howler / cubs', 'bite', 'MOVES.bite', 'apex', windup=0.4, tell='ring', release='slash', hit='impact', size='ring radius 1.7; slash x0.6', snd='cub_bite_tell / cub_bite')
add('lunge', 'Stalker / Howler / cubs', 'lunge (dash line)', 'MOVES.lunge', 'apex', windup=0.45, tell='strip', release='thrust', hit='impact', size='strip 4.5 x 1.4; thrust length 4.5', snd='cub_lunge_tell / cub_lunge')
add('rend', 'Stalker / Howler / cubs', 'rend (bleed)', 'MOVES.rend', 'apex', windup=0.5, tell='ring', release='slash', hit='impact', size='ring radius 1.9; slash x0.6; impact x0.5 per bleed tick', snd='cub_rend_tell / cub_rend')
add('flank', 'Stalker / Howler / cubs', 'flank (spot behind, stun)', 'MOVES.flank', 'apex', windup=0.6, tell='mark', release='burst', hit='impact', size='mark radius 2.2; burst radius 2.2', snd='cub_flank_tell / cub_flank')
add('howl', 'Stalker / Howler / cubs', 'howl (slow)', 'MOVES.howl', 'apex', windup=0.7, tell='ring', release='burst', size='ring radius 7.5; burst radius 7.5', snd='cub_howl_tell / cub_howl')
add('plate', 'cub plate reward', 'plate flies to the suit', 'PLATE.flyS', 'apex', trail='bolt', hit='heal', size='bolt x1 for flyS 0.7; heal x0.8', snd='plate_take')

# ---- 皇家 guard (iron) ----
add('g_thrust', '卒 guard', 'thrust (line)', 'GUARD.moves.thrust', 'guard', windup=0.5, tell='strip', release='thrust', hit='impact', size='strip 2.6 x 0.8; thrust length 2.6', snd='g_thrust_tell / g_thrust')
add('g_volley', '弩 guard', 'volley (mark on the target)', 'GUARD.moves.volley', 'guard', windup=0.8, tell='mark', release='burst', hit='impact', trail='bolt', size='mark radius 1.6; 3 bolts falling in; burst radius 1.6', snd='g_volley_tell / g_volley')
add('g_shove', '盾 guard', 'shove (circle, push)', 'GUARD.moves.shove', 'guard', windup=0.5, tell='ring', release='burst', hit='impact', size='ring radius 1.8; burst radius 1.8', snd='g_shove_tell / g_shove')
add('g_charge', '车 guard', 'charge (dash line)', 'GUARD.moves.charge', 'guard', windup=0.9, tell='strip', release='thrust', hit='impact', state='smoke', size='strip 10 x 1.8; thrust length 10; smoke = dust', snd='g_charge_tell / g_charge')
add('g_cut', '伍长 guard', 'cut (line)', 'GUARD.moves.cut', 'guard', windup=0.5, tell='strip', release='slash', hit='impact', size='strip 2.4 x 1.0; slash x0.9', snd='g_cut_tell / g_cut')
add('g_buff', '伍长 guard', 'squad buff while the 伍长 lives', 'GUARD.buff', 'guard', state='aura', size='aura x1 on the 伍长 only', snd='')
add('g_break', '伍长 guard', 'the 伍长 breaks (buff ends)', 'GUARD.leaderBoon', 'guard', release='burst', state='smoke', size='burst x0.6; smoke x1', snd='g_break')
add('g_block', '盾 guard', 'block (blow from the front)', 'GUARD.block', 'guard', hit='impact', state='shield', size='impact x0.8; shield frames 0-3 once', snd='')
add('unit_break', 'guard / rebel unit', 'a unit breaks', 'GUARD.types', 'guard', state='smoke', size='smoke x0.8 (rebels: their own row)', snd='unit_break')

# ---- 反贼 rebels (olive / umber / madder by variant; never a school colour) ----
add('r_talisman', '符水道人 rebel', 'talisman (heal mark on allies)', 'GUARD.moves.talisman', 'rebel_olive', windup=0.8, tell='mark', release='heal', size='mark radius 2.5; heal x1 on each mended ally', snd='r_talisman_tell / r_talisman')
add('r_lunge', '死士 rebel', 'lunge (line, the yellow glint)', 'GUARD.moves.lunge', 'rebel_umber', windup=0.6, tell='strip', release='thrust', hit='impact', size='strip 7 x 1.0; impact x0.6 as the glint at the tell start; thrust length 7', snd='r_lunge_tell / r_lunge')
add('r_cleave', '渠帅 rebel', 'cleave (circle)', 'GUARD.moves.cleave', 'rebel_madder', windup=0.6, tell='ring', release='slash', hit='impact', size='ring radius 2.2; slash x1', snd='r_cleave_tell / r_cleave')
for sc, shape, w in (('ru', 'line', 0.8), ('dao', 'circle', 0.8), ('fa', 'line', 0.8), ('mo', 'mark', 1.0), ('yinyang', 'mark', 1.0), ('za', 'line', 0.8), ('ming', 'line', 0.8), ('zongheng', 'circle', 0.9), ('nong', 'line', 0.8)):
    tell = {'line': 'strip', 'circle': 'ring', 'mark': 'mark'}[shape]; rel = {'line': 'thrust', 'circle': 'burst', 'mark': 'burst'}[shape]
    add(f'bl_{sc}', '力士 rebel', f'bootleg {sc} move ({shape})', f'FANZEI.bootleg.{sc}', 'rebel_olive', windup=w, tell=tell, release=rel, hit='impact',
        size='tell and release sized from the move (range x width or radius); rebel row of the unit\'s variant, never the school\'s', snd='r_bootleg_tell')
add('r_stall', '力士 rebel', 'bootleg 甲 stalls (spark flash)', 'FANZEI.stallN', 'rebel_umber', hit='impact', state='smoke', size='impact x0.8; smoke x0.6', snd='r_stall')
add('r_charge', 'player (渠帅 charge)', 'the taken bootleg charge (school move x chargeK)', 'FANZEI.chargeK', 'caster', note='plays the school move\'s own cards in the player\'s school row', snd='plate_take')

# ---- palace pieces and royale hazards ----
add('statue', 'tiger statue (royale)', 'strike', 'STATUE', 'bronze', windup=0.6, tell='ring', release='crack', hit='burst', size='ring radius 6.5; crack radius 6.5; burst x1', snd='statue_tell / statue_strike')
add('lion', '石狮 / bronze guardian beasts', 'strike', 'LION', 'bronze', windup=0.6, tell='ring', release='crack', hit='burst', size='ring radius 4; crack radius 4', snd='lion_tell / lion_strike')
add('giant_wake', '十二金人 giant', 'wakes (2 s)', 'PIECES2.giant.wakeS', 'bronze', windup=2.0, tell='aura', state='smoke', size='aura x2.4 held 2 s; smoke x1.5 when it steps off', snd='giant_wake')
add('giant_slam', '十二金人 giant', 'slam (ring round itself)', 'PIECES2.giant.slam', 'bronze', windup=1.0, tell='ring', release='crack', hit='burst', state='smoke', size='ring radius 4; crack radius 4; burst x1.5; smoke x1.5', snd='giant_slam_tell / giant_slam')
add('giant_sweep', '十二金人 giant', 'sweep (line ahead)', 'PIECES2.giant.sweep', 'bronze', windup=1.2, tell='strip', release='slash', hit='impact', size='strip 7 x 3; slash x2.5', snd='giant_sweep_tell / giant_sweep')
add('giant_fall', '十二金人 giant', 'breaks and falls (0.8 s)', 'PIECES2.giant.fallS', 'bronze', release='crack', state='smoke', size='crack radius 3; smoke x2', snd='giant_fall')
add('vat', '门海 vat', 'cracks then splashes', 'PIECES2.vat', 'water', windup=0.5, tell='ring', release='burst', state='smoke', size='ring radius 3.5; burst radius 3.5 (the flood stays the game\'s)', snd='vat_crack / vat_splash')
add('burn_warn', 'burning wing', 'warning (5 s) before the wing falls', 'BURN.warnS', 'ash', windup=5.0, tell='smoke', size='smoke x2 at each door of the wing, one every 0.6 s (pooled one-shots)', snd='st_burn', repeat=0.6)
add('burn_fall', 'burning wing', 'the wing falls (1.2 s)', 'BURN.fallS', 'ash', release='crack', state='smoke', size='crack radius 3 at each door; smoke x2', snd='burn_fall')
add('mercury', '水银 channels', 'warn 0.6 s, on 1.2 s', 'PIECES.mercury', 'ash', note='no card: owner 25 Nov 02:2x, the warning is a brighter texture + shimmer (game material)', snd='merc_warn / merc_on')
add('huabiao', '华表', 'marking', 'PIECES.huabiao', 'bronze', note='no card: owner 25 Nov 02:25, decoration only', snd='')
add('ding', '鼎 / altar', 'heal while standing in it', 'ALTAR', 'jade', state='heal', size='heal x1.2 held while healing', snd='ding_heal')
add('boon', 'crab / wanderer boon', 'boon taken', 'BOONS', 'jade', hit='burst', state='heal', size='burst x0.6; heal for heal/regen; aura (bronze row) for power/speed/vision for s', snd='boon')
add('suit_break', 'any suit', 'a suit breaks', 'MAX_HP', 'caster', release='burst', state='smoke', size='burst x1; smoke x1.2', snd='')

if __name__ == '__main__':
    json.dump({'items': I}, open(sys.argv[1], 'w'), indent=1, ensure_ascii=False)
    print(len(I), 'items', sum(1 for i in I if 'windup' in i), 'tells')
