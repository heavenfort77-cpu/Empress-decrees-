#!/usr/bin/env python3
"""GLB check for the guard and rebel units (re-import without Blender): meshes and triangles, skins and joints, materials, animations with
their channel counts and durations, extras. Prints PASS/FAIL for: skinned lod0, lod1 and lod2 present, clips idle/move/attack each with
channels and length > 0. Usage: python3 glb_info.py FILE.glb [...]"""
import json, struct, sys
fails = 0; checks = 0
for f in sys.argv[1:]:
    b = open(f, 'rb').read(); n = struct.unpack_from('<I', b, 12)[0]; g = json.loads(b[20:20 + n]); acc = g['accessors']
    name = f.split('/')[-1][:-4]
    meshes = {}
    for node in g['nodes']:
        if 'mesh' in node:
            m = g['meshes'][node['mesh']]; t = sum(acc[p['indices']]['count'] // 3 for p in m['primitives'])
            meshes[node['name']] = (t, 'skin' in node, [g['materials'][p['material']]['name'] for p in m['primitives'] if 'material' in p])
    anims = {}
    for a in g.get('animations', []):
        dur = max(acc[s['input']]['max'][0] for s in a['samplers']) if a['samplers'] else 0
        anims[a['name']] = (len(a['channels']), dur)
    res = [(f'{name}_lod0 skinned', meshes.get(f'{name}_lod0', (0, False))[1]), ('lod1 and lod2 present', f'{name}_lod1' in meshes and f'{name}_lod2' in meshes)]
    for c in ('idle', 'move', 'attack'):
        ch, dur = anims.get(c, (0, 0)); res.append((f'clip {c}: {ch} channels, {dur:.2f} s', ch > 0 and dur > 0))
    for k, ok in res:
        checks += 1; fails += not ok; print(('PASS ' if ok else 'FAIL ') + f'{name} glb {k}')
    print(f'INFO {name} meshes ' + ', '.join(f'{k} {v[0]} tris {"+".join(v[2])}' for k, v in meshes.items()))
    ex = [n.get('extras') for n in g['nodes'] if n.get('extras')]
    if ex: print(f'INFO {name} extras {str(ex)[:160]}')
print(f'{checks - fails} of {checks} pass')
