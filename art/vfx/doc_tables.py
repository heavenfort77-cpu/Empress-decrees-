# Markdown tables for docs/VFX.md from vfx.json and vfx_map.json (VFXP, 25 Nov). Usage: python3 -I doc_tables.py <assets dir> <vfx_map.json>
import sys, json
A, MP = sys.argv[1], sys.argv[2]
M = json.load(open(f'{A}/vfx.json')); I = json.load(open(MP))['items']
print('| Card | Atlas (draw) | Faces | Frames @ fps (s) | Tell loop | Size m (w x h) | Pivot m from left, bottom | Anchor m | pixelfx reference (shape, timing) |')
print('|---|---|---|---|---|---|---|---|---|')
for k, e in M['effects'].items():
    unit = ', '.join(f'{u} {e[u]}' for u in ('unitRadiusM', 'unitLenM', 'unitWidthM') if u in e)
    print(f"| {k} | {e['atlas']} ({e['blend']}) | {'camera' if e['orient'] == 'bill' else 'ground'} | {e['frames']} @ {e['fps']} ({e['durationS']}) | {e['loop'] or '-'} | {e['sizeM'][0]} x {e['sizeM'][1]}{' (' + unit + ')' if unit else ''} | {e['pivotM'][0]}, {e['pivotM'][1]} | {e['anchorHeightM']} | {e['ref'].replace('pixelfx ', '').replace(' (shape and timing only)', '')} |")
print()
print('| Row | Name | Pigment | Used by |'); print('|---|---|---|---|')
use = {'apex': 'Tiger Demon, Stalker, Howler, cubs, plates', 'rebel_olive': '反贼 variant 0', 'rebel_umber': '反贼 variant 1', 'rebel_madder': '反贼 variant 2',
       'guard': '皇家 guard', 'bronze': 'statue, guardian beasts, 十二金人', 'jade': '鼎 / altar heal, boons', 'water': '门海 vats', 'ash': 'burning wings, dust'}
for i, n in enumerate(M['ramps']['rows']): print(f"| {i} | {n} | {M['ramps']['hex'][n]} | {use.get(n, 'the ' + n + ' suit (player or bot)')} |")
print()
groups = [('Suits (CONFIG.KITS; ramp = the caster\'s school row)', lambda i: i['cfg'].startswith('KITS')),
          ('Tiger Demon and its minions (CONFIG.APEX, MOVES, DEMON_ULT, PLATE; ramp apex)', lambda i: i['cfg'].split('.')[0] in ('APEX', 'MOVES', 'DEMON_ULT', 'PLATE')),
          ('皇家 guard and 反贼 rebels (CONFIG.GUARD, FANZEI)', lambda i: i['cfg'].split('.')[0] in ('GUARD', 'FANZEI')),
          ('Palace pieces, hazards, heals (CONFIG.STATUE, LION, PIECES, PIECES2, BURN, ALTAR, BOONS)', lambda i: True)]
done = set()
for title, f in groups:
    print(f'### {title}\n'); print('| id | Who | Move | CONFIG | Windup s | Tell | Release | Hit | Trail | State | Ramp | Sizes | Sounds (AUDIO.md) |')
    print('|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    for it in I:
        if it['id'] in done or not f(it): continue
        done.add(it['id'])
        g = lambda k: it.get(k, '-')
        sz = it.get('size', '') + (('; ' if it.get('size') else '') + it['note'] if it.get('note') else '') + (f"; repeat every {it['repeatS']} s" if it.get('repeatS') else '')
        print(f"| {it['id']} | {it['who']} | {it['move']} | {it['cfg']} | {g('windup')} | {g('tell')} | {g('release')} | {g('hit')} | {g('trail')} | {g('state')} | {it['ramp']} | {sz} | {it.get('snd', '') or '-'} |")
    print()
print(f"Items: {len(I)}; tells (windup): {sum(1 for i in I if 'windup' in i)}; no card: {sum(1 for i in I if not any(k in i for k in ('tell', 'release', 'hit', 'trail', 'state')))}")
