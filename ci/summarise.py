# Collect per-job results (results/*.json) into one summary.json and a short summary.txt.
import json, glob
rows = [json.load(open(f)) for f in sorted(glob.glob('results/**/*.json', recursive=True))]
rows.sort(key=lambda r: r.get('i', -1))
json.dump(rows, open('summary.json', 'w'), ensure_ascii=False, indent=1)
with open('summary.txt', 'w') as o:
    named = sum(1 for r in rows if r.get('caught_named'))
    o.write(f"jobs {len(rows)}; caught by named check {named} of {sum(1 for r in rows if r.get('want'))}\n")
    for r in rows: o.write(json.dumps(r, ensure_ascii=False) + '\n')
print(open('summary.txt').read())
