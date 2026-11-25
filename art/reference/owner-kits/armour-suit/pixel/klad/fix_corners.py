#!/usr/bin/env python3
"""Remove doubled corners from the ink outline, as klad's pixel skill asks, until klad check finds none there."""
import json, subprocess, sys
K = sys.argv[1]; B = sys.argv[2] if len(sys.argv) > 2 else 'knight.klad'
for _ in range(6):
    f = json.loads(subprocess.run([K, 'check', B, '--json'], capture_output=True, text=True).stdout)['findings']
    c = [x['at'] for x in f if x['kind'] == 'corner' and x['color'] == 'ink']
    if not c: break
    subprocess.run([K, 'pixel', B, 'l1', '--erase', '--cells', ' '.join(f'{x},{y}' for x, y in c)], capture_output=True)
f = json.loads(subprocess.run([K, 'check', B, '--json'], capture_output=True, text=True).stdout)['findings']
kinds = {}
for x in f: kinds[x['kind']] = kinds.get(x['kind'], 0) + 1
print('klad check after fixes:', kinds or 'nothing to look at')
