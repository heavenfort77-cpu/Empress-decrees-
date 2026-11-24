# Apply mutation number N from ci/job.json to index.html (exactly one match required). Usage: python3 ci/apply_mut.py N
import json, sys
job = json.load(open('ci/job.json', encoding='utf-8'))
m = job['muts'][int(sys.argv[1])]
src = open('index.html', encoding='utf-8').read()
n = src.count(m['a'])
if n != 1:
    print('MUTATION-NOT-APPLIED', m['name'], 'matches', n); sys.exit(3)
open('index.html', 'w', encoding='utf-8').write(src.replace(m['a'], m['b']))
print('applied', m['name'])
