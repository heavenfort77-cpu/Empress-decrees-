"""Audio gates for src/audio/sound.js renders (runner only). Usage: python ci_audio/analyze.py OUTDIR
Reads OUTDIR/stats.json and the WAVs from render.mjs; prints PASS/FAIL per gate, then a mutation round (each gate must FAIL on
its mutant), then writes the phone listening preview (all sounds in one file with a timestamp list)."""
import json, sys, os, wave
import numpy as np
import pyloudnorm as pyln

# Gate thresholds (one block; a comment line above each value).
G = {
    # Peak ceiling for every sound, loop and ramp, dBFS.
    'peak_db': -3.0,
    # Tells and stingers: share of spectral energy in 1-4 kHz (laptop and phone speakers), at least.
    'band_lo': 1000, 'band_hi': 4000, 'band_min': 0.10,
    # Phone renders are tonal: energy-weighted spectral flatness in 300-6000 Hz at most this (noise is near 0.3-0.6).
    'flat_max': 0.2,
    # Loop seam: end-to-start first and second differences at most k x the loop's own 99.9th percentile (plus 16-bit slack).
    'seam_k': 2.0, 'seam_slack': 1e-4,
    # Loop seam, phone loops: first and last second of the loop against the steady state of a continuous render, error at most this, dB.
    'fold_db': -30.0,
    # Ramp loudness windows, LUFS: whole 60 s, first 10 s (calm bed), last 10 s (peak) (13d: mobile -16 +-2, beds -22..-18, peaks -16..-12).
    'ramp_int': (-20.0, -14.0), 'ramp_first': (-26.0, -18.0), 'ramp_last': (-18.0, -12.0),
    # Stinger over the calm bed, LU (13d: not more than 12-15 LU above the bed; at least 3 LU so it reads).
    'sting_over': (3.0, 15.0),
}


def read_wav(p):
    with wave.open(p, 'rb') as w:
        sr, n = w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype='<i2').astype(np.float64) / 32768.0
    return x, sr


def write_wav(p, x, sr):
    y = np.clip(np.round(x * 32767), -32768, 32767).astype('<i2')
    with wave.open(p, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(y.tobytes())


def dbfs(v):
    return 20 * np.log10(max(v, 1e-12))


def band_frac(x, sr):
    P = np.abs(np.fft.rfft(x)) ** 2
    f = np.fft.rfftfreq(len(x), 1 / sr)
    tot = P[(f >= 20)].sum()
    return float(P[(f >= G['band_lo']) & (f <= G['band_hi'])].sum() / tot) if tot > 0 else 0.0


def flatness(x, sr):
    n, hop = 2048, 1024
    if len(x) < n:
        x = np.pad(x, (0, n - len(x)))
    win = np.hanning(n)
    f = np.fft.rfftfreq(n, 1 / sr)
    sel = (f >= 300) & (f <= min(6000, sr / 2 - 1))
    vals, wts = [], []
    for i in range(0, len(x) - n + 1, hop):
        P = np.abs(np.fft.rfft(x[i:i + n] * win))[sel] ** 2
        e = P.sum()
        if e <= 0:
            continue
        eps = P.max() * 1e-10
        vals.append(np.exp(np.mean(np.log(P + eps))) / np.mean(P + eps)); wts.append(e)
    if not vals:
        return 0.0
    wts = np.array(wts); keep = wts >= wts.max() * 1e-3
    return float(np.average(np.array(vals)[keep], weights=wts[keep]))


def seam(x):
    d1 = np.abs(np.diff(x)); d2 = np.abs(np.diff(x, 2))
    s1 = abs(x[0] - x[-1]); s2 = max(abs(x[0] - 2 * x[-1] + x[-2]), abs(x[1] - 2 * x[0] + x[-1]))
    p1, p2 = np.percentile(d1, 99.9), np.percentile(d2, 99.9)
    ok = s1 <= G['seam_k'] * p1 + G['seam_slack'] and s2 <= G['seam_k'] * p2 + G['seam_slack']
    return ok, s1, p1, s2, p2


def lufs(x, sr):
    return pyln.Meter(sr).integrated_loudness(x)


# ---------- gates: each takes the data dict D and returns (ok, lines) ----------
def g1_render(D):
    bad = [f'{p}/{n}' for p in ('phone', 'desktop') for n, _ in D['list'] if f'{p}/{n}' not in D['snd'] or len(D['snd'][f'{p}/{n}'][0]) == 0]
    bad += [f'loop {p}/{k}' for p in ('phone', 'desktop') for k in D['loops'] if f'{p}/{k}' not in D['loop']]
    bad += [f'ramp {p}' for p in ('phone', 'desktop') if p not in D['ramp']]
    n = 2 * (len(D['list']) + len(D['loops']) + 1)
    return not bad, [f'G1 renders: {n - len(bad)} of {n}'] + [f'  missing {b}' for b in bad[:20]]


def all_items(D):
    for k, v in D['snd'].items():
        yield 'sound ' + k, v
    for k, v in D['loop'].items():
        yield 'loop ' + k, v
    for k, v in D['ramp'].items():
        yield 'ramp ' + k, v


def g2_peak(D):
    lim = 10 ** (G['peak_db'] / 20); bad = []; worst = -99
    for k, (x, sr, st) in all_items(D):
        pk = max(st['peak'], float(np.max(np.abs(x))) if len(x) else 0)
        worst = max(worst, dbfs(pk))
        if pk > lim:
            bad.append(f'  {k} peak {dbfs(pk):.2f} dBFS')
    return not bad, [f'G2 peak <= {G["peak_db"]} dBFS: worst {worst:.2f} dBFS, {len(bad)} over'] + bad[:20]


def g3_nan(D):
    bad = [f'  {k} nan {st["nan"]} clip {st["clip"]}' for k, (x, sr, st) in all_items(D) if st['nan'] or st['clip'] or np.any(~np.isfinite(x)) or np.any(np.abs(x) >= 0.999)]
    return not bad, [f'G3 no NaN, no clipping: {len(bad)} bad'] + bad[:20]


def g4_band(D):
    bad = []; vals = []
    for k, (x, sr, st) in D['snd'].items():
        if st['cat'] in ('tell', 'voice'):
            b = band_frac(x, sr); vals.append(b)
            if b < G['band_min']:
                bad.append(f'  {k} 1-4 kHz share {b:.3f}')
    return not bad and vals, [f'G4 tells+stingers 1-4 kHz share >= {G["band_min"]}: {len(vals) - len(bad)} of {len(vals)} (min {min(vals) if vals else 0:.3f})'] + bad[:20]


def g5_tonal(D):
    bad = []; vals = []
    items = [(k, v) for k, v in D['snd'].items() if k.startswith('phone/')] + [('loop ' + k, v) for k, v in D['loop'].items() if k.startswith('phone/')]
    for k, (x, sr, st) in items:
        fl = flatness(x, sr); vals.append(fl)
        if st.get('noiseSrc', -1) != 0:
            bad.append(f'  {k} noise sources {st.get("noiseSrc")}')
        if fl > G['flat_max']:
            bad.append(f'  {k} flatness {fl:.3f}')
    dn = sum(v[2].get('noiseSrc', 0) for k, v in D['snd'].items() if k.startswith('desktop/'))
    return not bad and vals, [f'G5 phone renders tonal (0 noise sources, flatness <= {G["flat_max"]}): {len(vals) - len(bad)} of {len(vals)} (max flatness {max(vals) if vals else 0:.3f}; desktop effects use {dn} noise sources)'] + bad[:20]


def fold_err(x, ref, sr):
    # Error in the first and last second, relative to the whole loop's RMS (a near-silent window must not inflate it).
    w = sr; out = -200.0; r = np.sqrt(np.mean(ref ** 2))
    for u, v in ((x[:w], ref[:w]), (x[-w:], ref[-w:])):
        out = max(out, dbfs(np.sqrt(np.mean((u - v) ** 2))) - dbfs(r))
    return out


def g6_seam(D):
    bad = []; n = 0; worst = -200.0
    for k, (x, sr, st) in D['loop'].items():
        n += 1; ok, s1, p1, s2, p2 = seam(x)
        if not ok:
            bad.append(f'  {k} seam d1 {s1:.5f} (p99.9 {p1:.5f}) d2 {s2:.5f} (p99.9 {p2:.5f})')
        if k in D['ref']:
            fe = fold_err(x, D['ref'][k][0], sr); worst = max(worst, fe)
            if len(x) != len(D['ref'][k][0]) or fe > G['fold_db']:
                bad.append(f'  {k} differs from the steady state by {fe:.1f} dB')
    nr = sum(1 for k in D['loop'] if k in D['ref'])
    return not bad and n > 0 and nr > 0, [f'G6 loops seamless: {n - len(bad)} of {n} (click check all; steady-state check on {nr} phone loops, worst {worst:.1f} dB)'] + bad


def g7_ramp(D):
    bad = []; out = []
    for p, (x, sr, st) in D['ramp'].items():
        i, a, b = lufs(x, sr), lufs(x[:10 * sr], sr), lufs(x[-10 * sr:], sr)
        out.append(f'  {p}: whole {i:.1f} LUFS, first 10 s {a:.1f}, last 10 s {b:.1f}')
        out.append('    per 10 s: ' + ' '.join(f'{lufs(x[j * 10 * sr:(j + 1) * 10 * sr], sr):.1f}' for j in range(len(x) // (10 * sr))))
        for v, (lo, hi), what in ((i, G['ramp_int'], 'whole'), (a, G['ramp_first'], 'first 10 s'), (b, G['ramp_last'], 'last 10 s')):
            if not (lo <= v <= hi):
                bad.append(f'  {p} {what} {v:.1f} LUFS outside [{lo}, {hi}]')
    return not bad and out, [f'G7 ramp loudness: {"PASS" if not bad else "FAIL"}'] + out + bad


def g8_sting(D):
    bad = []; out = []
    cfg = D['config']; gain = cfg['vol']['voice'] * cfg['master']
    for p in ('phone', 'desktop'):
        if p not in D['ramp']:
            continue
        x, sr, _ = D['ramp'][p]; bed = lufs(x[:10 * sr], sr)
        for n, cat in D['list']:
            if cat != 'voice' or f'{p}/{n}' not in D['snd']:
                continue
            y, sr2, _ = D['snd'][f'{p}/{n}']
            over = lufs(np.pad(y, (0, max(0, sr2 - len(y)))), sr2) + dbfs(gain) - bed
            out.append(f'  {p}/{n}: {over:+.1f} LU over the bed')
            if not (G['sting_over'][0] <= over <= G['sting_over'][1]):
                bad.append(f'  {p}/{n} {over:+.1f} LU outside {G["sting_over"]}')
    return not bad and out, [f'G8 stingers over the calm bed: {"PASS" if not bad else "FAIL"}'] + out + bad


GATES = [g1_render, g2_peak, g3_nan, g4_band, g5_tonal, g6_seam, g7_ramp, g8_sting]


def load(out):
    S = json.load(open(os.path.join(out, 'stats.json')))
    D = {'list': [(s['name'], s['cat']) for s in S['list']], 'loops': S['loops'], 'config': S['config'], 'snd': {}, 'loop': {}, 'ramp': {}}
    for k, st in S['stats']['sounds'].items():
        p, n = k.split('/'); x, sr = read_wav(os.path.join(out, 'wav', p, n + '.wav')); D['snd'][k] = (x, sr, st)
    for k, st in S['stats']['loops'].items():
        p, n = k.split('/'); x, sr = read_wav(os.path.join(out, 'wav', p, 'loop_' + n + '.wav')); D['loop'][k] = (x, sr, st)
    for p, st in S['stats']['ramp'].items():
        x, sr = read_wav(os.path.join(out, 'preview', f'ramp_60s_{p}.wav')); D['ramp'][p] = (x, sr, st)
    D['ref'] = {}
    for k, st in S['stats']['refs'].items():
        p, n = k.split('/'); x, sr = read_wav(os.path.join(out, 'ref', p, 'loop_' + n + '.wav')); D['ref'][k] = (x, sr, st)
    D['mut'] = {k: read_wav(os.path.join(out, 'mut', k + '.wav')) + (st,) for k, st in S['stats']['mut'].items()}
    return D


def clone(D):
    return {k: (dict(v) if isinstance(v, dict) else v) for k, v in D.items()}


def mutants(D):
    """Each yields (gate index, label, mutated data). The gate must FAIL on it."""
    tell = next(k for k, v in D['snd'].items() if v[2]['cat'] == 'tell' and k.startswith('phone/'))
    m = clone(D); k = next(iter(m['snd'])); del m['snd'][k]; yield 0, f'drop {k}', m
    m = clone(D); x, sr, st = m['snd'][tell]; y = x / np.max(np.abs(x)) * 10 ** (-1 / 20); m['snd'][tell] = (y, sr, dict(st, peak=float(np.max(np.abs(y))))); yield 1, f'{tell} raised to -1 dBFS', m
    m = clone(D); x, sr, st = m['snd'][tell]; m['snd'][tell] = (x, sr, dict(st, nan=1)); yield 2, f'{tell} with one NaN', m
    m = clone(D); x, sr, st = m['snd'][tell]; y = x.copy(); y[len(y) // 2] = 1.0; m['snd'][tell] = (y, sr, st); yield 2, f'{tell} with one clipped sample', m
    m = clone(D); x, sr, st = m['snd'][tell]; F = np.fft.rfft(x); F[np.fft.rfftfreq(len(x), 1 / sr) > 800] = 0; m['snd'][tell] = (np.fft.irfft(F, len(x)), sr, st); yield 3, f'{tell} low-passed at 800 Hz', m
    for n in ('vat_splash', 'demon_claw'):
        m = clone(D); m['snd'][f'phone/{n}'] = D['snd'][f'desktop/{n}']; yield 4, f'phone/{n} replaced by its desktop (noise) render', m
    m = clone(D); m['loop']['phone/a_wind'] = D['loop']['desktop/a_wind']; yield 4, 'phone/a_wind replaced by the desktop wind (noise)', m
    for n in ('m_drone', 'm_bells', 'a_wind', 'a_fire'):
        m = clone(D); m['loop'][f'phone/{n}'] = D['mut'][f'raw_{n}']; yield 5, f'phone/{n} rendered without seam handling', m
    for g in (8, -10):
        m = clone(D); m['ramp'] = {p: (x * 10 ** (g / 20), sr, st) for p, (x, sr, st) in D['ramp'].items()}; yield 6, f'ramp {g:+d} dB', m
    m = clone(D); n = next(n for n, c in D['list'] if c == 'voice'); x, sr, st = D['snd'][f'phone/{n}']; m['snd'][f'phone/{n}'] = (x * 10 ** (14 / 20), sr, st); yield 7, f'phone/{n} +14 dB', m


def preview(D, out):
    os.makedirs(os.path.join(out, 'preview'), exist_ok=True)
    sr = D['snd'][f'phone/{D["list"][0][0]}'][1]; gap = np.zeros(int(0.5 * sr)); parts = []; lines = []; t = 0.0
    for n, cat in D['list']:
        x = D['snd'][f'phone/{n}'][0]; lines.append(f'{int(t // 60)}:{t % 60:05.2f}  {n}  ({cat})'); parts += [x, gap]; t += (len(x) + len(gap)) / sr
    write_wav(os.path.join(out, 'preview', 'all_sounds_phone.wav'), np.concatenate(parts), sr)
    open(os.path.join(out, 'preview', 'all_sounds_phone.txt'), 'w').write('\n'.join(lines) + '\n')
    for k in ('m_drone', 'm_bells', 'm_pulse', 'm_drive', 'm_peak', 'a_room', 'a_wind', 'a_fire'):
        x, s2, _ = D['loop'][f'phone/{k}']; write_wav(os.path.join(out, 'preview', f'loop2x_{k}_phone.wav'), np.concatenate([x, x]), s2)
    return t


def main():
    out = sys.argv[1]; D = load(out)
    res = []
    for g in GATES:
        ok, lines = g(D); res.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + '\n'.join(lines))
    print(f'GATES {sum(res)} of {len(res)}')
    for k, (x, sr, st) in sorted(D['loop'].items()):
        if k.startswith('phone/'):
            print(f'INFO loop {k}: rms {dbfs(np.sqrt(np.mean(x ** 2))):.1f} dBFS, peak {dbfs(np.max(np.abs(x))):.1f} dBFS, {lufs(x, sr):.1f} LUFS')
    caught = [0] * len(GATES); tried = [0] * len(GATES)
    for gi, label, m in mutants(D):
        ok, _ = GATES[gi](m); tried[gi] += 1; caught[gi] += (not ok)
        print(f'MUTANT G{gi + 1} {label}: {"caught" if not ok else "NOT CAUGHT"}')
    full = sum(1 for i in range(len(GATES)) if tried[i] and caught[i] == tried[i])
    print(f'MUTATIONS gates fully caught {full} of {len(GATES)}; mutants caught {sum(caught)} of {sum(tried)}')
    mb = {p: sum(len(v[0]) for k, v in D['snd'].items() if k.startswith(p)) * 4 / 1e6 + sum(len(v[0]) for k, v in D['loop'].items() if k.startswith(p)) * 4 / 1e6 for p in ('phone', 'desktop')}
    print(f'DECODED MEMORY (float32): phone {mb["phone"]:.1f} MB, desktop {mb["desktop"]:.1f} MB')
    t = preview(D, out); print(f'PREVIEW all_sounds_phone.wav {t:.1f} s, {len(D["list"])} sounds')
    print('RESULT ' + ('PASS' if all(res) and full == len(GATES) else 'FAIL'))


if __name__ == '__main__':
    main()
