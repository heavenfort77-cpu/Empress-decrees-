# Collect per-job results (results/*.json) into one summary.json and a short summary.txt.
import json, glob
rows = [json.load(open(f)) for f in sorted(glob.glob('results/**/*.json', recursive=True))]
rows.sort(key=lambda r: r.get('i', -1))
json.dump(rows, open('summary.json', 'w'), ensure_ascii=False, indent=1)
with open('summary.txt', 'w') as o:
    if rows and 'oks' in rows[0]:
        # Sharded suite: one result per check name over all shards (prelude checks run in every shard: a check fails if it failed anywhere).
        ok = set(n for r in rows for n in r['oks']); bad = set(n for r in rows for n in r['fails'])
        names = ok | bad; o.write(f"SHARDED RUNTIME {len(names - bad)} of {len(names)} pass; shards {len(rows)}; wall s {[r['s'] for r in rows]}; failing {sorted(bad)}\n")
        if not names: o.write('FAIL sharded suite measured 0 checks\n')
        o.write('cuts ' + ' | '.join(r['shard'][0] if r['shard'] else '?' for r in rows) + '\n')
        tm = {}
        for r in rows:
            for l, ms in r['stmt']: tm[l] = max(tm.get(l, 0), int(ms))
        json.dump(tm, open('shard_times.json', 'w')); o.write(f"stmt times {len(tm)}\n")
        for r in rows:
            for l in r['faillines']: o.write(l[:600] + '\n')
            for l in r['sims']: o.write(l[:300] + '\n')
        print(open('summary.txt').read()); raise SystemExit(0)
    if not rows: o.write('FAIL no job results (0 measured)\n')
    for r in rows:
        if 'tot' in r and not r['tot'] and r.get('fails') is not None and 'name' not in r and 'tail' not in r: o.write(f"FAIL job {r.get('i')} printed no RUNTIME line (0 measured)\n")
    named = sum(1 for r in rows if r.get('caught_named'))
    o.write(f"jobs {len(rows)}; caught by named check {named} of {sum(1 for r in rows if r.get('want'))}\n")
    for r in rows: o.write(json.dumps(r, ensure_ascii=False) + '\n')
print(open('summary.txt').read())
