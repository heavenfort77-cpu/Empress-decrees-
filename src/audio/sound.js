// Empress Decrees: sound (design note docs/AUDIO.md). Every sound is generated in code: no files, no licences.
// At the first tap every effect is rendered once with OfflineAudioContext into a buffer; music and ambience are
// pre-rendered seamless loops. During play only one-shot buffer sources are started (no live synthesis).
// API: init(opts), unlock(), play(name, x, z, rate), setListener(x, z), setIntensity(v), setAmb(fire, wind),
// setMode(m), cycleMode(), setReduce(on), setVolume(bus, v), pause(), resume(), status().

export const CONFIG = {
  // Master gain after the limiter, 0-1 (13d: default reduced; the player raises it).
  master: 0.8,
  // Bus gains, 0-1: effects, music, ambience, her stingers.
  vol: { sfx: 1, music: 0.8, amb: 0.8, voice: 0.9 },
  // Compressor in front of the clip (a peak catcher; approximates a limiter; dB, dB, ratio, s, s).
  comp: { threshold: -6, knee: 6, ratio: 8, attack: 0.003, release: 0.15 },
  // Last-stage tanh clip ceiling (linear; 0.7 = -3.1 dBFS, so the mix never peaks above -3 dBFS).
  clip: 0.7,
  // Peak each rendered effect is normalised to, dBFS, per category (all at or under -3).
  peakDb: { tell: -6, sfx: -7, heavy: -5, voice: -4, ui: -10 },
  // Loops: RMS target and peak cap after rendering, dBFS (bus and layer gains set the mix).
  loopRmsDb: -18, loopPeakDb: -3.5,
  // Live voices for effects (desktop, phone) and for her stingers; a new sound steals the oldest non-tell voice.
  pool: { desktop: 16, phone: 8, voice: 2 },
  // Spatial effects: heard within range m of the listener; full level within refM; pan reaches panMax at panM m to a side.
  range: 26, refM: 5, rolloff: 0.6, panM: 14, panMax: 0.7,
  // The same sound starts at most sameN times within sameS seconds (nine guards thrusting at once).
  sameN: 2, sameS: 0.05,
  // Pre-render rate on phones, Hz (halves memory; phone speakers stop well below 12 kHz). Desktop uses ctx.sampleRate.
  phoneRate: 24000,
  // Bus ramp time constant for mode, volume and pause changes, s.
  busTau: 0.05,
  // Music: 五声 tuned by 三分损益 (Pythagorean fifths); gong (宫) in Hz; the music sits in the 羽 (yu) mode.
  music: {
    // 宫 pitch, Hz (F3).
    gongHz: 174.61,
    // Tempo, beats per minute, and bars per loop (4/4): 72 BPM x 4 bars = 13.33 s loops.
    bpm: 72, bars: 4,
    // Intensity smoothing time constant, s (13b: duration / 3 of a 1.2-3.6 s bed move).
    tau: 1.2,
    // Layer windows: [smoothstep start, end] of intensity, and the layer's gain at full, dB.
    layers: {
      m_drone: { win: [-1, 0], db: -6 },
      m_bells: { win: [0.1, 0.35], db: -3 },
      m_pulse: { win: [0.3, 0.55], db: 2 },
      m_drive: { win: [0.55, 0.8], db: -3 },
      m_peak: { win: [0.8, 1.0], db: -3 },
    },
    // Music low-pass by intensity, Hz at 0 and at 1 (13b sweep; open at the top).
    lp: [1600, 9000],
    // Stingers wait for the next beat if it is at most this many beats away (audio clock), else play at once.
    quantBeats: 0.5,
    // Music duck under a stinger: dB, attack and release time constants s.
    duck: { db: -8, inTau: 0.01, outTau: 0.25 },
  },
  // Ambience loops: length s, layer gains dB; fire and wind follow setAmb (0-1); room tone is always on (13b keeps silence alive).
  amb: { loopS: 16, room: -12, wind: -9, fire: -8 },
  // Crossfade length for steady loop content, s (events fold their tails onto the loop start instead).
  xfadeS: 0.25,
  // Reduce intensity (13d): stingers and heavy hits this many dB lower; music intensity capped; no beat-wait before stingers.
  reduce: { voiceDb: -9, heavyDb: -6, maxIntensity: 0.7 },
  // Sound modes cycled by cycleMode (13f: isolate a layer when something sounds wrong).
  modes: ['on', 'music', 'fx', 'off'],
  // Settings key in localStorage.
  saveKey: 'empressDecrees.audio',
  // Seed of the noise generator (renders are identical every run).
  seed: 9,
};

// ---------- pitch: 五声 from 三分损益 ----------
const PENT = [1, 9 / 8, 81 / 64, 3 / 2, 27 / 16];
const PENT_NAME = ['gong', 'shang', 'jue', 'zhi', 'yu'];
// i = scale step from 宫 (0 = gong F3, 4 = yu, 5 = gong one octave up, -1 = yu below).
export function N(i) { const k = ((i % 5) + 5) % 5; return CONFIG.music.gongHz * PENT[k] * Math.pow(2, Math.floor(i / 5)); }
export function noteTable() {
  const out = [];
  for (let i = -6; i <= 18; i++) out.push(`N(${i}) ${PENT_NAME[((i % 5) + 5) % 5]} ${N(i).toFixed(2)} Hz`);
  return out;
}

// ---------- recipe helpers (load time only) ----------
const tn = (f, at, d, g, o) => Object.assign({ t: 'tone', f, at, d, g }, o);
const bl = (f, at, d, g, o) => Object.assign({ t: 'bell', f, at, d, g }, o);
const ch = (f, at, d, g, o) => Object.assign({ t: 'chime', f, at, d, g }, o);
const pk = (f, at, d, g, o) => Object.assign({ t: 'pluck', f, at, d, g }, o);
const dr = (f, f1, at, d, g, o) => Object.assign({ t: 'drum', f, f1, at, d, g }, o);
const ck = (f, at, g, o) => Object.assign({ t: 'click', f, at, d: 0.035, g }, o);
const fm = (f, ratio, index, at, d, g, o) => Object.assign({ t: 'fm', f, ratio, index, at, d, g }, o);
const hm = (f, at, d, g, o) => Object.assign({ t: 'hum', f, at, d, g }, o);
// Noise layers are desktop only (13f: phones get tonal sounds; noise reads as crackle on a phone speaker).
const nz = (f, q, at, d, g, o) => Object.assign({ t: 'noise', f, q, at, d, g }, o);
const pops = (f, f1, at, d, g, n) => ({ t: 'pops', f, f1, at, d, g, n });
const sw = { env: 'swell' };
const swSaw = { env: 'swell', w: 'sawtooth' };
const accel = (f, d, g) => [ck(f, 0, g * 0.6), ck(f, d * 0.45, g * 0.7), ck(f, d * 0.7, g * 0.8), ck(f, d * 0.85, g * 0.9), ck(f, d * 0.95, g)];
const shift = (arr, at) => arr.map((v) => Object.assign({}, v, { at: v.at + at }));

// ---------- the sound list (docs/AUDIO.md maps each to the game's attacks and tells) ----------
// cat: tell = gameplay-critical warning (1-4 kHz layer, gate-checked); heavy = big impact; sfx; voice = her stinger; ui.
export const SOUNDS = {
  // 儒甲 bronze bells 编钟 (rites and music).
  ru_atk: { cat: 'sfx', v: [bl(N(5), 0, 0.5, 1), ck(2400, 0, 0.5)] },
  ru_hit: { cat: 'sfx', v: [bl(N(3), 0, 0.4, 1), fm(1800, 1.41, 2, 0, 0.12, 0.4), dr(220, 110, 0, 0.15, 0.6), ck(2000, 0, 0.4)] },
  ru_whiff: { cat: 'sfx', v: [tn(N(13), 0, 0.18, 0.5, { f1: N(10), w: 'triangle' }), nz(1800, 1.2, 0, 0.15, 0.4)] },
  ru_q: { cat: 'sfx', v: [bl(N(5), 0, 0.4, 0.7), bl(N(7), 0.06, 0.4, 0.7), bl(N(10), 0.12, 0.5, 0.8), tn(400, 0, 0.25, 0.4, { f1: 900 }), ck(2600, 0.25, 0.8)] },
  ru_w: { cat: 'sfx', v: [dr(180, 120, 0, 0.2, 0.8), bl(N(4), 0, 1.0, 1), bl(N(9), 0, 0.7, 0.6), ck(3000, 0, 0.6)] },
  ru_r: { cat: 'heavy', v: [bl(N(0), 0, 2.4, 1), bl(N(5), 0.6, 1.4, 0.8), bl(N(7), 1.3, 1.2, 0.8), bl(N(10), 2.0, 1.0, 0.8), ck(2200, 0.6, 0.6), ck(2400, 1.3, 0.6), ck(2600, 2.0, 0.6)] },
  // 道甲 qin plucks and harmonics 泛音 (water, yielding).
  dao_atk: { cat: 'sfx', v: [pk(N(6), 0, 0.4, 1, { n: 6 }), ck(2000, 0, 0.3)] },
  dao_hit: { cat: 'sfx', v: [pk(N(4), 0, 0.3, 1), tn(1500, 0, 0.08, 0.5, { f1: 900 }), dr(260, 140, 0, 0.1, 0.5), ck(1800, 0, 0.3)] },
  dao_whiff: { cat: 'sfx', v: [tn(N(14), 0, 0.2, 0.5, { f1: N(11) }), nz(2500, 1, 0, 0.15, 0.3)] },
  dao_q: { cat: 'sfx', v: [pk(N(14), 0, 1.0, 0.8, { n: 3 }), tn(N(4), 0, 0.8, 0.4, { vib: [5, 15], env: 'flat' }), ck(2200, 0, 0.3)] },
  dao_w: { cat: 'sfx', v: [pk(N(12), 0, 1.0, 0.8, { n: 3 }), tn(N(7), 0, 0.8, 0.4, { vib: [4, 12], env: 'flat' }), ck(2400, 0, 0.3)] },
  dao_counter: { cat: 'sfx', v: [pk(N(14), 0, 0.5, 0.8, { n: 3 }), pk(N(17), 0.07, 0.6, 0.8, { n: 3 }), bl(N(10), 0.07, 0.8, 0.6), ck(3200, 0, 0.7)] },
  dao_r: { cat: 'heavy', v: [pk(N(4), 0, 0.6, 0.8), pk(N(6), 0.08, 0.6, 0.8), pk(N(7), 0.16, 0.6, 0.8), pk(N(9), 0.24, 0.6, 0.8), pk(N(11), 0.32, 0.8, 0.8), tn(N(14), 0.3, 1.2, 0.3, { am: [7, 0.6], env: 'flat' }), ck(2600, 0.32, 0.5)] },
  // 法甲 stone chime 磬 and clapper 拍板 (cold, exact).
  fa_atk: { cat: 'sfx', v: [ch(N(6), 0, 0.3, 1), ck(2800, 0, 0.6)] },
  fa_hit: { cat: 'sfx', v: [ch(N(6), 0, 0.35, 1), fm(2200, 2.7, 3, 0, 0.1, 0.5), dr(200, 90, 0, 0.12, 0.6)] },
  fa_whiff: { cat: 'sfx', v: [tn(1200, 0, 0.15, 0.5, { f1: 600, w: 'triangle' }), nz(3000, 1.5, 0, 0.12, 0.4)] },
  fa_q: { cat: 'sfx', v: [ch(N(11), 0, 0.4, 0.8), tn(500, 0, 0.22, 0.5, { f1: 1400 }), ck(3000, 0.22, 0.8), ch(N(6), 0.22, 0.5, 1)] },
  fa_w: { cat: 'sfx', v: [ch(N(11), 0, 0.6, 0.6), tn(N(6), 0, 0.5, 0.5, { f1: N(1), am: [12, 0.6] }), ck(2600, 0, 0.4)] },
  fa_r: { cat: 'heavy', v: [ch(N(1), 0, 2.0, 1), ch(N(6), 0.3, 1.6, 0.6), dr(110, 60, 0, 0.6, 0.8), ck(2400, 0, 0.6)] },
  // 墨甲 wooden machines: crossbow twang, ratchets, low drum (no dash).
  mo_atk: { cat: 'sfx', v: [pk(N(3), 0, 0.25, 1, { n: 8, pos: 0.1 }), tn(2400, 0.01, 0.12, 0.4, { f1: 1200 })] },
  mo_hit: { cat: 'sfx', v: [dr(170, 80, 0, 0.2, 1), ck(1800, 0, 0.6), tn(900, 0, 0.05, 0.3, { w: 'square' })] },
  mo_whiff: { cat: 'sfx', v: [tn(1600, 0, 0.2, 0.4, { f1: 800 }), nz(2000, 2, 0, 0.15, 0.3)] },
  mo_q: { cat: 'sfx', v: [ck(1400, 0, 0.5), ck(1400, 0.03, 0.5), ck(1450, 0.06, 0.5), ck(1450, 0.09, 0.5), ck(1500, 0.12, 0.5), ck(1500, 0.15, 0.5), ck(1550, 0.18, 0.5), ck(1600, 0.21, 0.6), dr(120, 70, 0.25, 0.4, 1), tn(N(-1), 0.25, 0.6, 0.5, { w: 'triangle' })] },
  mo_w_tell: { cat: 'tell', v: [tn(N(1), 0, 0.6, 0.6, { f1: N(3), env: 'swell', w: 'sawtooth' })].concat(accel(1600, 0.6, 0.8)) },
  mo_w: { cat: 'sfx', v: [tn(300, 0, 0.2, 0.5, { f1: 1200, w: 'triangle' }), dr(150, 70, 0, 0.3, 1), ck(2200, 0, 0.6)] },
  mo_r: { cat: 'heavy', v: [dr(130, 60, 0, 0.5, 1), bl(N(-1), 0, 1.2, 0.5), ck(1200, 0, 0.5), ck(1250, 0.08, 0.5), ck(1300, 0.16, 0.5), ck(1350, 0.24, 0.6)] },
  // 阴阳甲 paired tones: yin low, yang high, crossing.
  yy_atk: { cat: 'sfx', v: [tn(N(4), 0, 0.25, 0.7, { f1: N(9) }), tn(N(9), 0, 0.25, 0.4, { f1: N(4) }), ck(2600, 0, 0.4)] },
  yy_hit: { cat: 'sfx', v: [bl(N(7), 0, 0.4, 0.8), tn(N(2), 0, 0.3, 0.5), ck(2000, 0, 0.5)] },
  yy_whiff: { cat: 'sfx', v: [tn(N(9), 0, 0.2, 0.4, { f1: N(4) })] },
  yy_q: { cat: 'sfx', v: [tn(N(-1), 0, 0.5, 1, { f1: N(-3), w: 'triangle' }), tn(N(4), 0, 0.4, 0.5, { f1: N(2) }), ck(1800, 0, 0.5)] },
  yy_w_tell: { cat: 'tell', v: [tn(N(9), 0, 0.8, 0.6, { f1: N(14), env: 'swell' }), tn(N(4), 0, 0.8, 0.4, { f1: N(9), env: 'swell' })].concat(accel(2400, 0.8, 0.8)) },
  yy_w: { cat: 'sfx', v: [bl(N(9), 0, 0.8, 1), dr(200, 90, 0, 0.25, 0.8), ck(3000, 0, 0.6)] },
  yy_r_tell: { cat: 'tell', v: [tn(1800, 0, 1.0, 0.5, { f1: 3000, env: 'swell' }), tn(N(-1), 0, 1.0, 0.6, { f1: N(9), env: 'swell', w: 'triangle' }), tn(N(9), 0, 1.0, 0.6, { f1: N(-1), env: 'swell', w: 'triangle' })].concat(accel(2200, 1.0, 0.8)) },
  yy_r: { cat: 'heavy', v: [tn(N(4), 0, 1.5, 0.6, { am: [4, 0.8], env: 'flat' }), bl(N(-1), 0, 1.8, 0.8), bl(N(9), 0, 1.2, 0.5), ck(2400, 0, 0.5)] },
  // 杂甲 a blend: bell and chime, odd FM (borrows from every school).
  za_atk: { cat: 'sfx', v: [fm(N(7), 1.5, 1.5, 0, 0.25, 0.8), ck(2200, 0, 0.4)] },
  za_hit: { cat: 'sfx', v: [bl(N(6), 0, 0.3, 0.7), ch(N(8), 0, 0.3, 0.6), dr(210, 100, 0, 0.12, 0.5)] },
  za_whiff: { cat: 'sfx', v: [tn(1400, 0, 0.18, 0.4, { f1: 700, w: 'triangle' })] },
  za_q: { cat: 'sfx', v: [ch(N(5), 0, 0.6, 0.8), bl(N(7), 0, 0.6, 0.6), tn(N(10), 0, 0.3, 0.3, { f1: N(5) }), ck(2800, 0, 0.6)] },
  za_w: { cat: 'sfx', v: [tn(600, 0, 0.12, 0.6, { f1: 2400 }), tn(2400, 0.12, 0.15, 0.4, { f1: 1200 }), ck(3200, 0.12, 0.6)] },
  za_r: { cat: 'heavy', v: [tn(N(5), 0, 0.6, 0.6, sw), fm(N(10), 2.01, 3, 0.6, 0.8, 0.8), bl(N(5), 0.6, 1.0, 0.7), ck(2400, 0.6, 0.5)] },
  // 名甲 the wheel and the paradox: whirr, se plucks, an arrow that keeps rising.
  ming_atk: { cat: 'sfx', v: [tn(N(8), 0, 0.3, 0.6, { am: [28, 0.8], w: 'triangle' }), ck(2400, 0, 0.4)] },
  ming_hit: { cat: 'sfx', v: [ch(N(8), 0, 0.3, 0.7), pk(N(5), 0, 0.3, 0.6), dr(230, 110, 0, 0.1, 0.5)] },
  ming_whiff: { cat: 'sfx', v: [tn(N(10), 0, 0.2, 0.4, { f1: N(7), am: [30, 0.6] })] },
  ming_q: { cat: 'sfx', v: [tn(2000, 0, 0.15, 0.6, { f1: 500 }), pk(N(9), 0.12, 0.4, 0.6), ck(3000, 0, 0.5)] },
  ming_w: { cat: 'sfx', v: [pk(N(4), 0, 0.6, 1, { n: 8 }), tn(N(9), 0, 0.8, 0.4, { vib: [6, 20], env: 'flat' }), ck(2000, 0, 0.5)] },
  ming_r: { cat: 'heavy', v: [tn(N(4), 0, 1.2, 0.6, { f1: N(9) }), tn(N(9), 0, 1.2, 0.4, { f1: N(14) }), tn(N(-1), 0, 1.2, 0.4, { f1: N(4) }), ck(2600, 1.2, 0.8), bl(N(9), 1.2, 1.0, 0.8)] },
  // 纵横甲 linked tones that beat against each other; swaps cross over.
  zh_atk: { cat: 'sfx', v: [ch(N(6), 0, 0.25, 0.7), tn(N(6) * 1.01, 0, 0.25, 0.3), ck(2200, 0, 0.4)] },
  zh_hit: { cat: 'sfx', v: [bl(N(3), 0, 0.3, 0.6), dr(220, 100, 0, 0.12, 0.6), ck(1800, 0, 0.5)] },
  zh_whiff: { cat: 'sfx', v: [tn(1300, 0, 0.18, 0.4, { f1: 700, w: 'triangle' })] },
  zh_q: { cat: 'sfx', v: [tn(N(7), 0, 0.9, 0.6), tn(N(7) * 1.012, 0, 0.9, 0.6), ch(N(12), 0, 0.4, 0.5), ck(2600, 0, 0.5)] },
  zh_w: { cat: 'sfx', v: [tn(500, 0, 0.25, 0.5, { f1: 1500 }), tn(1500, 0, 0.25, 0.5, { f1: 500 }), ck(3000, 0.25, 0.6)] },
  zh_r: { cat: 'heavy', v: [bl(N(4), 0, 0.8, 0.7), bl(N(6), 0.12, 0.8, 0.7), bl(N(7), 0.24, 0.8, 0.7), bl(N(9), 0.36, 0.8, 0.7), bl(N(11), 0.48, 0.9, 0.7), bl(N(9), 0.6, 1.2, 0.7), tn(N(4), 0, 2.0, 0.3, { am: [6, 0.5], env: 'flat' }), ck(2400, 0, 0.5)] },
  // 农甲 earth: clay pot 缶, ocarina 埙, sprouting chirps.
  nong_atk: { cat: 'sfx', v: [dr(260, 160, 0, 0.15, 0.8), tn(N(5), 0, 0.15, 0.4, { w: 'triangle' }), ck(1700, 0, 0.4)] },
  nong_hit: { cat: 'sfx', v: [dr(190, 90, 0, 0.2, 1), tn(N(3), 0, 0.2, 0.4), ck(1500, 0, 0.5)] },
  nong_whiff: { cat: 'sfx', v: [tn(900, 0, 0.2, 0.4, { f1: 500, w: 'triangle' })] },
  nong_q: { cat: 'sfx', v: [tn(N(7), 0, 0.12, 0.5, { f1: N(10) }), tn(N(8), 0.1, 0.12, 0.5, { f1: N(11) }), tn(N(9), 0.2, 0.12, 0.5, { f1: N(12) }), dr(300, 180, 0, 0.12, 0.5), ck(2600, 0.2, 0.4)] },
  nong_w: { cat: 'sfx', v: [dr(120, 70, 0, 0.35, 0.8), tn(400, 0, 0.25, 0.5, { f1: 900, w: 'triangle' }), ck(2000, 0, 0.5)] },
  nong_r: { cat: 'heavy', v: [tn(N(4), 0, 0.5, 0.7, { vib: [5, 12], env: 'flat' }), tn(N(7), 0.35, 0.6, 0.7, { vib: [5, 12], env: 'flat' }), tn(N(9), 0.7, 1.0, 0.7, { vib: [5, 12], env: 'flat' }), dr(150, 80, 0.4, 0.5, 0.8), bl(N(9), 0.4, 1.2, 0.5), ck(2200, 0.4, 0.5)] },

  // Tiger Demon (apex, a bronze machine tiger, 兵家): growls are harmonic stacks; scrapes carry the 1-4 kHz layer.
  demon_wake: { cat: 'tell', v: [dr(80, 50, 0, 1.0, 1), hm(98, 0, 3, 1, { vib: [3, 20], env: 'swell' }), tn(196, 0, 3, 0.4, sw), tn(294, 0, 3, 0.3, sw), fm(2200, 1.5, 1.5, 0, 3, 0.4, sw), ck(2000, 2.9, 0.8)] },
  demon_claw_tell: { cat: 'tell', v: [fm(2200, 1.5, 2, 0, 0.45, 0.7, sw), tn(220, 0, 0.45, 0.5, Object.assign({ f1: 330 }, swSaw))].concat(accel(2600, 0.45, 0.7)) },
  demon_claw: { cat: 'heavy', v: [fm(1800, 2.1, 4, 0, 0.2, 0.8), dr(180, 90, 0, 0.2, 1), nz(2500, 1, 0, 0.15, 0.6)] },
  demon_pounce_tell: { cat: 'tell', v: [tn(110, 0, 0.5, 0.8, Object.assign({ f1: 220 }, swSaw)), tn(1500, 0, 0.5, 0.4, { f1: 3000, env: 'swell' })].concat(accel(2400, 0.5, 0.7)) },
  demon_pounce: { cat: 'heavy', v: [dr(140, 60, 0, 0.4, 1), fm(1600, 1.4, 3, 0, 0.25, 0.6), nz(800, 0.8, 0, 0.3, 0.6)] },
  demon_roar_tell: { cat: 'tell', v: [hm(110, 0, 0.7, 1, { env: 'swell', vib: [7, 40] }), tn(1200, 0, 0.7, 0.4, { f1: 2000, env: 'swell' })].concat(accel(2000, 0.7, 0.6)) },
  demon_roar: { cat: 'heavy', v: [hm(98, 0, 1.4, 1, { am: [30, 0.5], vib: [4, 30] }), tn(196, 0, 1.2, 0.4, { w: 'sawtooth', am: [30, 0.5] }), tn(1800, 0, 1.2, 0.3, { am: [30, 0.6] })] },
  demon_ult_tell: { cat: 'tell', v: [bl(N(-5), 0, 0.8, 0.6), tn(1600, 0, 0.8, 0.6, { f1: 3200, env: 'swell' }), hm(110, 0, 0.8, 0.8, { env: 'swell', vib: [6, 30] }), tn(220, 0, 0.8, 0.4, { f1: 880, env: 'swell' })].concat(accel(2400, 0.8, 0.8)) },
  demon_hit: { cat: 'heavy', v: [fm(700, 1.41, 3, 0, 0.4, 0.8), dr(160, 70, 0, 0.3, 1), ck(2000, 0, 0.6)] },
  // Cubs and hunt minions (treaded four-legged machines): smaller, higher.
  cub_bite_tell: { cat: 'tell', v: [tn(440, 0, 0.4, 0.6, Object.assign({ f1: 660 }, swSaw)), ck(2800, 0.3, 0.8), ck(2800, 0.37, 0.9)] },
  cub_bite: { cat: 'sfx', v: [ck(3000, 0, 1), ck(2200, 0.04, 0.8), dr(260, 140, 0, 0.1, 0.7)] },
  cub_lunge_tell: { cat: 'tell', v: [tn(300, 0, 0.45, 0.6, { f1: 900, env: 'swell', w: 'triangle' }), tn(1800, 0, 0.45, 0.4, { f1: 2600, env: 'swell' })] },
  cub_lunge: { cat: 'sfx', v: [tn(900, 0, 0.15, 0.6, { f1: 400 }), dr(220, 100, 0, 0.15, 0.8), nz(1500, 1, 0, 0.12, 0.4)] },
  cub_rend_tell: { cat: 'tell', v: [fm(2600, 1.3, 2, 0, 0.5, 0.6, sw), tn(330, 0, 0.5, 0.5, Object.assign({ f1: 494 }, swSaw))] },
  cub_rend: { cat: 'sfx', v: [fm(2000, 2.3, 4, 0, 0.25, 0.8), tn(1200, 0.05, 0.3, 0.4, { f1: 300 })] },
  cub_flank_tell: { cat: 'tell', v: [tn(2400, 0, 0.6, 0.5, { f1: 1200, am: [12, 0.7], env: 'swell' }), tn(N(4), 0, 0.6, 0.5, { f1: N(9), env: 'swell', w: 'triangle' })] },
  cub_flank: { cat: 'sfx', v: [ch(N(11), 0, 0.5, 0.8), dr(240, 110, 0, 0.15, 0.7), ck(2200, 0, 0.6)] },
  cub_howl_tell: { cat: 'tell', v: [hm(330, 0, 0.7, 0.8, { env: 'swell', vib: [5, 30] }), tn(1300, 0, 0.7, 0.4, sw)] },
  cub_howl: { cat: 'sfx', v: [hm(440, 0, 1.4, 1, { f1: 620, vib: [6, 40] }), tn(1760, 0, 1.2, 0.3, { f1: 2200, vib: [6, 40] })] },
  // 皇家 guard (Qin army): bronze blades, crossbow 弩, wooden shields, chariots.
  g_thrust_tell: { cat: 'tell', v: [tn(2200, 0, 0.5, 0.4, { f1: 3000, env: 'swell' }), tn(N(6), 0, 0.5, 0.6, { f1: N(9), env: 'swell', w: 'triangle' }), ck(2600, 0.3, 0.7), ck(2600, 0.45, 0.9)] },
  g_thrust: { cat: 'sfx', v: [tn(1600, 0, 0.12, 0.6, { f1: 700 }), ch(N(10), 0, 0.25, 0.6), nz(2200, 1, 0, 0.1, 0.4)] },
  g_volley_tell: { cat: 'tell', v: [tn(N(-1), 0, 0.8, 0.6, Object.assign({ f1: N(2) }, swSaw))].concat(accel(2000, 0.8, 0.8)) },
  g_volley: { cat: 'sfx', v: [pk(N(1), 0, 0.3, 1, { n: 8, pos: 0.08 }), tn(3200, 0.05, 0.5, 0.35, { f1: 1800 }), tn(2800, 0.1, 0.5, 0.3, { f1: 1500 })] },
  g_shove_tell: { cat: 'tell', v: [dr(140, 120, 0, 0.1, 0.6), dr(140, 120, 0.25, 0.1, 0.7), tn(800, 0, 0.5, 0.3, sw), ck(1800, 0.25, 0.7), ck(1800, 0.45, 0.9)] },
  g_shove: { cat: 'sfx', v: [dr(150, 70, 0, 0.3, 1), ck(1500, 0, 0.6), tn(N(1), 0, 0.2, 0.4, { w: 'square' })] },
  g_charge_tell: { cat: 'tell', v: [tn(N(-1), 0, 0.9, 0.8, { w: 'sawtooth', am: [14, 0.8], env: 'swell' }), tn(N(4), 0, 0.9, 0.4, { env: 'swell', w: 'triangle' }), ck(2400, 0.6, 0.7), ck(2400, 0.75, 0.8), ck(2400, 0.85, 0.9)] },
  g_charge: { cat: 'heavy', v: [dr(110, 55, 0, 0.6, 1), tn(N(-1), 0, 0.5, 0.6, { w: 'sawtooth', am: [18, 0.8] }), nz(600, 0.8, 0, 0.4, 0.5), ck(1800, 0, 0.5)] },
  g_cut_tell: { cat: 'tell', v: [tn(2600, 0, 0.5, 0.5, { f1: 3400, env: 'swell' }), ch(N(9), 0, 0.5, 0.4, sw)] },
  g_cut: { cat: 'sfx', v: [tn(2000, 0, 0.12, 0.6, { f1: 800 }), ch(N(11), 0, 0.3, 0.6), nz(2600, 1, 0, 0.1, 0.4)] },
  g_break: { cat: 'heavy', v: [bl(N(0), 0, 1.2, 1), bl(N(4), 0.15, 1.0, 0.7), dr(120, 60, 0, 0.5, 0.8), ck(2000, 0, 0.5)] },
  // 反贼 rebels (黄巾 talismans, crude iron, the 死士 glint).
  r_talisman_tell: { cat: 'tell', v: [ck(2200, 0, 0.6), ck(2600, 0.25, 0.7), ck(3000, 0.45, 0.8), ck(3400, 0.6, 0.9), ck(3800, 0.7, 1), tn(N(9), 0, 0.8, 0.4, { env: 'swell', am: [8, 0.6] })] },
  r_talisman: { cat: 'sfx', v: [bl(N(9), 0, 0.8, 0.7), bl(N(12), 0.08, 0.8, 0.5), ck(3000, 0, 0.4)] },
  r_lunge_tell: { cat: 'tell', v: [tn(3000, 0, 0.6, 0.5, { env: 'swell', am: [16, 0.5] }), ck(3200, 0, 0.8), ck(3200, 0.5, 0.9)] },
  r_lunge: { cat: 'sfx', v: [tn(1800, 0, 0.2, 0.6, { f1: 600 }), ck(2400, 0, 0.6), nz(2000, 1, 0, 0.15, 0.4)] },
  r_cleave_tell: { cat: 'tell', v: [tn(1900, 0, 0.6, 0.45, { f1: 2600, env: 'swell' }), tn(N(1), 0, 0.6, 0.6, { env: 'swell', w: 'square' }), ck(1900, 0.35, 0.7), ck(1900, 0.5, 0.9)] },
  r_cleave: { cat: 'sfx', v: [fm(600, 1.37, 4, 0, 0.3, 0.9), dr(170, 80, 0, 0.2, 0.8)] },
  r_bootleg_tell: { cat: 'tell', v: [tn(2400, 0, 0.9, 0.45, { env: 'swell', vib: [9, 60] }), tn(N(4), 0, 0.9, 0.5, { env: 'swell', vib: [9, 60] }), tn(N(4) * 1.06, 0, 0.9, 0.4, { env: 'swell' })].concat(accel(2200, 0.9, 0.8)) },
  r_stall: { cat: 'sfx', v: [ck(3200, 0, 0.8), ck(2600, 0.06, 0.7), ck(2000, 0.14, 0.6), ck(1400, 0.25, 0.5), tn(800, 0, 0.4, 0.4, { f1: 200, w: 'square' })] },
  // Shared unit blows.
  unit_hit: { cat: 'sfx', v: [dr(240, 120, 0, 0.12, 0.8), ck(2000, 0, 0.6)] },
  unit_break: { cat: 'sfx', v: [dr(140, 70, 0, 0.3, 1), ch(N(8), 0, 0.4, 0.5), ck(1700, 0, 0.5)] },
  // Palace pieces and royale hazards.
  statue_tell: { cat: 'tell', v: [tn(N(-3), 0, 0.6, 0.8, { w: 'sawtooth', am: [22, 0.7], env: 'swell' }), ck(2300, 0.2, 0.6), ck(2300, 0.4, 0.8), ck(2300, 0.55, 1)] },
  statue_strike: { cat: 'heavy', v: [dr(90, 45, 0, 0.6, 1), ch(N(1), 0, 0.6, 0.6), nz(300, 0.7, 0, 0.4, 0.5), ck(1600, 0, 0.5)] },
  lion_tell: { cat: 'tell', v: [tn(2500, 0, 0.6, 0.45, { f1: 3200, env: 'swell' }), fm(N(6), 1.41, 1.5, 0, 0.6, 0.7, sw), ck(2500, 0.3, 0.7), ck(2500, 0.5, 0.9)] },
  lion_strike: { cat: 'heavy', v: [dr(120, 55, 0, 0.45, 1), bl(N(1), 0, 0.6, 0.6), ck(1800, 0, 0.5)] },
  merc_warn: { cat: 'tell', v: [tn(2400, 0, 0.6, 0.5, { am: [14, 0.9], env: 'swell' }), tn(3100, 0, 0.6, 0.4, { am: [11, 0.9], env: 'swell' }), tn(N(9), 0, 0.6, 0.3, sw)] },
  merc_on: { cat: 'sfx', v: [tn(N(-1), 0, 1.2, 0.6, { w: 'triangle', am: [9, 0.5], env: 'flat' }), tn(1800, 0, 1.2, 0.25, { am: [9, 0.8], env: 'flat' })] },
  giant_wake: { cat: 'tell', v: [bl(N(-5), 0, 2.0, 0.6), tn(1500, 0, 2.0, 0.5, { f1: 2500, env: 'swell', am: [6, 0.5] }), ck(2000, 0.8, 0.6), ck(2000, 1.2, 0.7), hm(N(-5), 0, 2.0, 0.6, { f1: N(-3), env: 'swell' }), tn(N(-1), 0, 2.0, 0.4, { f1: N(4), env: 'swell' }), ck(2000, 1.6, 0.7), ck(2000, 1.9, 0.9)] },
  giant_slam_tell: { cat: 'tell', v: [tn(N(-3), 0, 1.0, 0.8, Object.assign({ f1: N(2) }, swSaw)), dr(120, 90, 0, 0.15, 0.6), dr(120, 90, 0.5, 0.15, 0.7)].concat(accel(2200, 1.0, 0.9)) },
  giant_slam: { cat: 'heavy', v: [dr(80, 40, 0, 0.9, 1), bl(N(-5), 0, 1.4, 0.8), ch(N(1), 0, 0.6, 0.4), nz(200, 0.7, 0, 0.6, 0.6), ck(1600, 0, 0.5)] },
  giant_sweep_tell: { cat: 'tell', v: [tn(N(1), 0, 1.2, 0.7, { w: 'sawtooth', am: [3, 0.6], env: 'swell' }), tn(1400, 0, 1.2, 0.4, { f1: 2600, env: 'swell' })].concat(accel(2400, 1.2, 0.8)) },
  giant_sweep: { cat: 'heavy', v: [tn(1800, 0, 0.35, 0.7, { f1: 500 }), dr(100, 50, 0, 0.6, 1), fm(500, 1.37, 2, 0, 0.5, 0.5), nz(900, 0.7, 0, 0.35, 0.5)] },
  giant_fall: { cat: 'heavy', v: [bl(N(-5), 0, 2.0, 1), bl(N(-3), 0.25, 1.6, 0.8), bl(N(-1), 0.5, 1.4, 0.7), dr(70, 40, 0.6, 1.0, 1), ck(1600, 0.6, 0.5)] },
  vat_crack: { cat: 'tell', v: [ck(2800, 0, 0.6), ck(2800, 0.2, 0.7), ck(3000, 0.33, 0.8), ck(3200, 0.42, 1), bl(N(9), 0, 0.5, 0.4, sw)] },
  vat_splash: { cat: 'sfx', v: [nz(1200, 0.6, 0, 0.6, 1), tn(1200, 0, 0.08, 0.5, { f1: 400 }), tn(1500, 0.05, 0.08, 0.5, { f1: 500 }), tn(1100, 0.11, 0.08, 0.4, { f1: 380 }), tn(1700, 0.16, 0.08, 0.4, { f1: 600 }), tn(1300, 0.22, 0.1, 0.4, { f1: 450 }), dr(160, 80, 0, 0.3, 0.8)] },
  burn_fall: { cat: 'heavy', v: [dr(70, 35, 0, 1.6, 1), tn(N(-5), 0, 1.4, 0.5, { w: 'sawtooth', am: [11, 0.7] }), bl(N(-5), 0, 2.0, 0.6), nz(300, 0.7, 0, 1.5, 0.8), ck(1600, 0, 0.5), ck(1500, 0.3, 0.5), ck(1400, 0.6, 0.5)] },
  door_lock: { cat: 'sfx', v: [dr(200, 120, 0, 0.15, 0.8), ch(N(6), 0, 0.25, 0.6), ck(2200, 0, 0.6)] },
  door_open: { cat: 'sfx', v: [ch(N(8), 0, 0.3, 0.5), tn(600, 0, 0.2, 0.4, { f1: 900, w: 'triangle' }), ck(1800, 0, 0.4)] },
  ding_heal: { cat: 'sfx', v: [bl(N(0), 0, 1.2, 0.8), bl(N(4), 0, 1.2, 0.6), bl(N(7), 0.1, 1.0, 0.5)] },
  // The player's state.
  p_hurt: { cat: 'sfx', v: [dr(200, 90, 0, 0.15, 1), ck(1500, 0, 0.7), tn(N(1), 0, 0.15, 0.4, { f1: N(-1), w: 'square' })] },
  p_bleed: { cat: 'sfx', v: [tn(1400, 0, 0.1, 0.6, { f1: 700 }), ck(2000, 0, 0.5)] },
  p_slow: { cat: 'sfx', v: [tn(N(7), 0, 0.4, 0.6, { f1: N(2), w: 'triangle' }), ck(1700, 0, 0.5)] },
  p_stun: { cat: 'sfx', v: [ch(N(11), 0, 0.6, 0.7), tn(2200, 0, 0.6, 0.4, { am: [10, 0.8] })] },
  p_marked: { cat: 'tell', v: [ch(N(9), 0, 0.5, 0.8), ch(N(14), 0.15, 0.6, 0.8), ck(2600, 0, 0.6)] },
  p_break: { cat: 'heavy', v: [bl(N(5), 0, 0.8, 0.8), bl(N(3), 0.2, 0.8, 0.8), bl(N(0), 0.4, 1.4, 1), dr(100, 50, 0.4, 0.6, 0.8)] },
  ult_ready: { cat: 'ui', v: [bl(N(5), 0, 0.6, 0.6), bl(N(7), 0.1, 0.6, 0.6), bl(N(10), 0.2, 0.9, 0.8), ck(2800, 0.2, 0.5)] },
  plate_take: { cat: 'sfx', v: [ch(N(10), 0, 0.4, 0.6), bl(N(5), 0.05, 0.6, 0.6), ck(2400, 0, 0.5)] },
  boon: { cat: 'sfx', v: [tn(N(9), 0, 0.2, 0.5, { f1: N(12) }), bl(N(12), 0.1, 0.5, 0.6), ck(3000, 0, 0.4)] },
  // Menus.
  ui_move: { cat: 'ui', v: [ck(2000, 0, 1), tn(N(9), 0, 0.05, 0.4)] },
  ui_ok: { cat: 'ui', v: [bl(N(7), 0, 0.3, 0.7), ck(2500, 0, 0.6)] },
  ui_back: { cat: 'ui', v: [tn(N(7), 0, 0.12, 0.5, { f1: N(4) }), ck(1600, 0, 0.5)] },
  // Kaymuse's stingers (synth only, no speech; calm contempt, never a shout). Each under 3 s (tone brief).
  st_decree: { cat: 'voice', v: [bl(N(0), 0, 2.2, 0.5), bl(N(3), 0.35, 1.9, 0.4), ch(N(15), 0, 1.4, 0.35), ch(N(18), 0.35, 1.4, 0.3), hm(N(-1), 0.05, 2.1, 1.2, { env: 'flat', vib: [4.5, 12] }), hm(N(2), 0.35, 1.8, 0.8, { env: 'flat', vib: [4.5, 12] }), tn(N(17), 0.05, 2.0, 0.12, { env: 'flat', vib: [4.5, 12] }), ck(2200, 0, 0.5), ck(2200, 0.35, 0.5)] },
  st_burn: { cat: 'voice', v: [bl(N(9), 0, 1.2, 0.4), bl(N(7), 0.3, 1.2, 0.4), bl(N(4), 0.6, 1.8, 0.5), ch(N(19), 0, 0.8, 0.3), ch(N(17), 0.3, 0.8, 0.3), ch(N(14), 0.6, 1.0, 0.3), tn(N(-5), 0, 2.2, 0.4, { w: 'sawtooth', am: [7, 0.6], env: 'swell' }), hm(N(-1), 0.1, 2.2, 1.2, { env: 'flat', vib: [4, 14] }), tn(1800, 0, 2.2, 0.25, { am: [7, 0.8], env: 'flat' }), ck(2600, 0, 0.5), ck(2600, 0.3, 0.5), ck(2600, 0.6, 0.5)] },
  st_bounty: { cat: 'voice', v: [ch(N(14), 0, 0.3, 0.4), ch(N(16), 0.07, 0.3, 0.4), ch(N(13), 0.13, 0.3, 0.4), ch(N(17), 0.2, 0.3, 0.4), ch(N(15), 0.28, 0.4, 0.4), dr(180, 80, 0.4, 0.5, 0.6), bl(N(4), 0.4, 1.4, 0.4), hm(N(-1), 0.3, 1.5, 1.2, { env: 'flat', vib: [4.5, 12] }), hm(N(4), 0.3, 1.5, 0.6, { env: 'flat', vib: [4.5, 12] })] },
  st_wake: { cat: 'voice', v: [bl(N(-5), 0, 2.6, 0.5), ch(N(16), 0, 1.6, 0.3), hm(N(-1), 0.1, 2.5, 1.2, { f1: N(1), env: 'flat', vib: [4, 10] }), hm(N(4), 0.6, 2.0, 0.6, { f1: N(6), env: 'flat', vib: [4, 10] }), bl(N(1), 1.4, 1.2, 0.4), ch(N(16), 1.4, 1.2, 0.3), ck(2000, 0, 0.5)] },
};

// ---------- loops: music layers (13.33 s) and ambience (16 s) ----------
function musicEvents(name) {
  const M = CONFIG.music, beat = 60 / M.bpm, bar = beat * 4, ev = [];
  if (name === 'm_bells') {
    // Slow 编钟 line in the yu mode, one strike or two per bar; it ends unresolved on shang.
    const line = [[0, 4, 1], [2.5, 7, 0.6], [4, 6, 0.9], [7, 9, 0.5], [8, 4, 0.9], [10, 2, 0.6], [12, 1, 0.9], [14.5, 4, 0.5]];
    for (const [b, i, g] of line) ev.push(bl(N(i + 5), b * beat, 3.0, g));
  } else if (name === 'm_pulse') {
    // 建鼓 on beats 1 and 3, a stick click for small speakers.
    for (let k = 0; k < M.bars; k++) {
      ev.push(dr(150, 70, k * bar, 0.5, 1), ck(2400, k * bar, 0.25));
      ev.push(dr(150, 70, k * bar + 2 * beat, 0.4, 0.7), ck(2400, k * bar + 2 * beat, 0.18));
    }
  } else if (name === 'm_drive') {
    // Small drum on the off-beats and a qin ostinato in eighths.
    const ost = [4, 6, 7, 9, 7, 6, 4, 2];
    for (let k = 0; k < M.bars * 8; k++) {
      const t = k * beat / 2;
      ev.push(pk(N(ost[k % 8] + 5), t, 0.5, k % 4 === 0 ? 0.8 : 0.5, { n: 6 }));
      if (k % 2 === 1) ev.push(dr(240, 130, t, 0.15, 0.5), ck(3000, t, 0.12));
    }
  } else if (name === 'm_peak') {
    // Stone chimes a semitone apart (deliberately outside the five tones) and a drum roll into each bar.
    for (let k = 0; k < M.bars; k++) {
      ev.push(ch(N(9), k * bar, 1.2, 0.6), ch(N(9) * 16 / 15, k * bar + beat * 0.5, 1.2, 0.5));
      for (let r = 0; r < 6; r++) ev.push(dr(200, 110, k * bar + 3 * beat + r * beat / 6, 0.12, 0.3 + r * 0.1));
    }
  }
  return ev;
}

export const LOOPS = {
  // Drone: 瑟 low strings on yu and its fifth with slow beating (steady; frequencies snapped to whole cycles per loop).
  m_drone: { kind: 'music', steady: () => [tn(N(-1), 0, 0, 1, { env: 'flat', w: 'triangle' }), tn(N(-1) + 0.3, 0, 0, 0.6, { env: 'flat', w: 'triangle' }), tn(N(2), 0, 0, 0.5, { env: 'flat' }), tn(N(4), 0, 0, 0.35, { env: 'flat', am: [0.075, 0.5] }), tn(N(9), 0, 0, 0.12, { env: 'flat', am: [0.15, 0.7] })] },
  m_bells: { kind: 'music', events: () => musicEvents('m_bells') },
  m_pulse: { kind: 'music', events: () => musicEvents('m_pulse') },
  m_drive: { kind: 'music', events: () => musicEvents('m_drive') },
  m_peak: { kind: 'music', steady: () => [tn(1600, 0, 0, 0.12, { env: 'flat', am: [6, 0.8] })], events: () => musicEvents('m_peak') },
  // Room tone: a low hall hum (always on, very low; 13b keeps quiet from sounding like a bug).
  a_room: { kind: 'amb', steady: () => [tn(N(-6) * 2, 0, 0, 1, { env: 'flat' }), tn(N(-6) * 3, 0, 0, 0.4, { env: 'flat', am: [0.125, 0.4] }), tn(N(-6) * 4 + 0.25, 0, 0, 0.25, { env: 'flat' }), nz(500, 0.5, 0, 0, 0.5, { env: 'flat' })] },
  // Wind over the black lake: whistling tones on phones; band noise added on desktop.
  a_wind: { kind: 'amb', steady: () => [tn(760, 0, 0, 0.4, { env: 'flat', am: [0.0625, 0.9], vib: [0.125, 60] }), tn(1020, 0, 0, 0.3, { env: 'flat', am: [0.1875, 0.9], vib: [0.25, 50] }), tn(560, 0, 0, 0.3, { env: 'flat', am: [0.125, 0.8] }), nz(700, 0.7, 0, 0, 1, { env: 'flat', am: [0.0625, 0.7] })] },
  // Fire: a flickering low rumble and tonal pops (phones); a noise bed and crackle on desktop.
  a_fire: { kind: 'amb', steady: () => [tn(98, 0, 0, 0.6, { env: 'flat', w: 'triangle', am: [3, 0.5] }), tn(147, 0, 0, 0.4, { env: 'flat', w: 'triangle', am: [5, 0.5] }), tn(196, 0, 0, 0.3, { env: 'flat', am: [7, 0.6] }), nz(400, 0.5, 0, 0, 1, { env: 'flat', am: [4, 0.5] })], events: () => [pops(1200, 3200, 0, 16, 0.4, 70), nz(2500, 0.8, 1, 0.05, 0.3), nz(3000, 0.8, 5.3, 0.05, 0.3), nz(2200, 0.8, 9.1, 0.05, 0.3), nz(2800, 0.8, 12.7, 0.05, 0.3)] },
};

// ---------- offline synthesis ----------
function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
const BRONZE = { p: [1, 1.19, 2.0, 2.92, 4.2, 5.4], a: [1, 0.5, 0.45, 0.3, 0.2, 0.12] };
const STONE = { p: [1, 2.32, 4.25, 6.63, 9.4], a: [1, 0.6, 0.4, 0.25, 0.15] };

// Gain envelope on param g (a GainNode's gain) for a voice: exp (strike), flat (held), swell (rises to its end: a tell).
function envelope(g, v, at, d) {
  const peak = v.g, a = v.a || 0.004;
  g.setValueAtTime(0, at);
  if (v.env === 'flat') { const r = Math.min(0.05, d / 4); g.linearRampToValueAtTime(peak, at + Math.max(a, r)); g.setValueAtTime(peak, at + d - r); g.linearRampToValueAtTime(0, at + d); }
  else if (v.env === 'swell') { g.linearRampToValueAtTime(peak * 0.15, at + Math.min(0.03, d * 0.1)); g.linearRampToValueAtTime(peak, at + d * 0.94); g.linearRampToValueAtTime(0, at + d); }
  else { g.linearRampToValueAtTime(peak, at + a); g.exponentialRampToValueAtTime(peak * 0.001, at + d); g.linearRampToValueAtTime(0, at + d + 0.01); }
}
function addMods(c, v, src, gainNode, at, end) {
  if (v.vib && src.detune) { const l = c.createOscillator(), lg = c.createGain(); l.frequency.value = v.vib[0]; lg.gain.value = v.vib[1]; l.connect(lg); lg.connect(src.detune); l.start(at); l.stop(end); }
  if (v.am) { const l = c.createOscillator(), lg = c.createGain(); l.frequency.value = v.am[0]; lg.gain.value = v.am[1] / 2; gainNode.gain.value = 1 - v.am[1] / 2; l.connect(lg); lg.connect(gainNode.gain); l.start(at); l.stop(end); }
}
function osc(c, out, type, f0, f1, at, d, v) {
  const o = c.createOscillator(), e = c.createGain(), m = c.createGain();
  o.type = type || 'sine';
  o.frequency.setValueAtTime(f0, at);
  if (f1 && f1 !== f0) o.frequency.exponentialRampToValueAtTime(f1, at + d * (v.glide || 1));
  envelope(e.gain, v, at, d);
  o.connect(e); e.connect(m); m.connect(out);
  addMods(c, v, o, m, at, at + d + 0.02);
  o.start(at); o.stop(at + d + 0.02);
  return o;
}
function partials(c, out, v, set, decayK) {
  for (let k = 0; k < set.p.length; k++) {
    const f = v.f * set.p[k];
    if (f > c.sampleRate * 0.45) continue;
    osc(c, out, 'sine', f, 0, v.at, Math.max(0.04, v.d / (1 + decayK * k)), { g: v.g * set.a[k], a: 0.002 });
  }
}
function noiseBuf(c, seconds, seed) {
  const n = Math.max(1, Math.ceil(seconds * c.sampleRate)), b = c.createBuffer(1, n, c.sampleRate), d = b.getChannelData(0), r = rng(seed);
  for (let i = 0; i < n; i++) d[i] = r() * 2 - 1;
  return b;
}
function buildVoice(c, out, v, phone, r, dur) {
  const d = v.d > 0 ? v.d : dur;
  switch (v.t) {
    case 'tone': osc(c, out, v.w, v.f, v.f1, v.at, d, v); break;
    case 'bell': partials(c, out, v, BRONZE, 0.8); osc(c, out, 'sine', v.f * 1.003, 0, v.at, v.d * 0.9, { g: v.g * 0.35, a: 0.002 }); break;
    case 'chime': partials(c, out, v, STONE, 1.5); break;
    case 'pluck': {
      const n = v.n || 6, pos = v.pos || 0.2;
      for (let k = 1; k <= n; k++) {
        const f = v.f * k; if (f > c.sampleRate * 0.45) break;
        osc(c, out, 'sine', f * 1.01, f, v.at, Math.max(0.05, v.d / (1 + 0.5 * (k - 1))), { g: v.g * Math.abs(Math.sin(k * Math.PI * pos)) / k * 2, a: 0.002, glide: 0.08 });
      }
      break;
    }
    case 'drum':
      // Membrane: pitch-dropped sine, its 1.59x mode, and a 2x/3x stack so phone speakers carry it (13d fake bass).
      osc(c, out, 'sine', v.f, v.f1, v.at, v.d, { g: v.g, a: 0.002, glide: 0.4 });
      osc(c, out, 'sine', v.f * 1.59, v.f1 * 1.59, v.at, v.d * 0.6, { g: v.g * 0.4, a: 0.002, glide: 0.4 });
      osc(c, out, 'triangle', v.f * 2, v.f1 * 2, v.at, v.d * 0.5, { g: v.g * 0.35, a: 0.002, glide: 0.4 });
      osc(c, out, 'sine', v.f * 3, v.f1 * 3, v.at, v.d * 0.35, { g: v.g * 0.2, a: 0.002, glide: 0.4 });
      break;
    case 'click': osc(c, out, 'sine', v.f, 0, v.at, v.d, { g: v.g, a: 0.001 }); osc(c, out, 'sine', v.f * 1.5, 0, v.at, v.d * 0.6, { g: v.g * 0.4, a: 0.001 }); break;
    case 'fm': {
      const car = osc(c, out, 'sine', v.f, v.f1, v.at, d, v), mod = c.createOscillator(), mg = c.createGain();
      mod.frequency.value = v.f * v.ratio;
      mg.gain.setValueAtTime(v.f * v.index, v.at); mg.gain.exponentialRampToValueAtTime(v.f * v.index * 0.1, v.at + d);
      mod.connect(mg); mg.connect(car.frequency); mod.start(v.at); mod.stop(v.at + d + 0.02);
      break;
    }
    case 'hum': {
      // A voice-like hum: a sawtooth through two vowel formants (tonal: only harmonics).
      const bus = c.createGain();
      for (const [ff, q, gg] of [[480, 5, 1], [880, 6, 0.6], [2600, 8, 0.25]]) { const bp = c.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = ff; bp.Q.value = q; bus.connect(bp); const og = c.createGain(); og.gain.value = gg * 3; bp.connect(og); og.connect(out); }
      osc(c, bus, 'sawtooth', v.f, v.f1, v.at, d, v);
      break;
    }
    case 'pops': {
      // Fire crackle made of short tonal pops at seeded times (phone-safe).
      const pr = rng(Math.round(v.f * 7 + v.d * 1000 + v.n));
      for (let k = 0; k < v.n; k++) { const t = v.at + pr() * (v.d - 0.06), f = v.f + pr() * (v.f1 - v.f); osc(c, out, 'sine', f, f * 0.8, t, 0.02 + pr() * 0.03, { g: v.g * (0.3 + pr() * 0.7), a: 0.001 }); }
      break;
    }
    case 'noise': {
      if (phone) break;
      const s = c.createBufferSource(); s.buffer = noiseBuf(c, d + 0.05, (r() * 1e9) | 0);
      const f = c.createBiquadFilter(); f.type = 'bandpass'; f.frequency.value = v.f; f.Q.value = v.q;
      const e = c.createGain(), m = c.createGain(); envelope(e.gain, v, v.at, d);
      s.connect(f); f.connect(e); e.connect(m); m.connect(out); addMods(c, v, s, m, v.at, v.at + d + 0.02);
      s.start(v.at); s.stop(v.at + d + 0.02);
      break;
    }
    default: throw new Error('sound: unknown voice type ' + v.t);
  }
}
function OAC() { return globalThis.OfflineAudioContext || globalThis.webkitOfflineAudioContext; }
function voicesEnd(vs) { let e = 0; for (const v of vs) e = Math.max(e, v.at + v.d); return e; }
async function renderVoices(vs, seconds, sr, phone, seed, steadyLen) {
  const C = OAC(), c = new C(1, Math.max(1, Math.ceil(seconds * sr)), sr), r = rng(seed);
  for (const v of vs) buildVoice(c, c.destination, v, phone, r, steadyLen || 0);
  const b = await c.startRendering();
  return b.getChannelData(0);
}
function peakOf(x) { let p = 0; for (let i = 0; i < x.length; i++) { const a = Math.abs(x[i]); if (a > p) p = a; } return p; }
function rmsOf(x) { let s = 0; for (let i = 0; i < x.length; i++) s += x[i] * x[i]; return Math.sqrt(s / Math.max(1, x.length)); }
function scale(x, k) { for (let i = 0; i < x.length; i++) x[i] *= k; return x; }
const db = (v) => Math.pow(10, v / 20);

// Renders one effect to a mono Float32Array, normalised to its category's peak.
export async function renderSound(name, sr, profile) {
  const s = SOUNDS[name]; if (!s) throw new Error('sound: no sound ' + name);
  const end = voicesEnd(s.v) + 0.06, x = await renderVoices(s.v, end, sr, profile === 'phone', CONFIG.seed + hashName(name));
  const p = peakOf(x);
  return p > 0 ? scale(x, db(CONFIG.peakDb[s.cat]) / p) : x;
}
function hashName(n) { let h = 7; for (let i = 0; i < n.length; i++) h = (h * 31 + n.charCodeAt(i)) >>> 0; return h % 100000; }
export function loopSeconds(name) { const M = CONFIG.music; return LOOPS[name].kind === 'music' ? M.bars * 4 * 60 / M.bpm : CONFIG.amb.loopS; }
// Snap steady frequencies to whole cycles per loop so the loop point is seamless.
function snapVoices(vs, L) {
  return vs.map((v) => {
    const o = Object.assign({}, v), q = (f) => Math.max(1, Math.round(f * L)) / L;
    o.f = q(v.f); if (v.f1) o.f1 = q(v.f1);
    if (v.am) o.am = [q(v.am[0]), v.am[1]]; if (v.vib) o.vib = [q(v.vib[0]), v.vib[1]];
    return o;
  });
}
// Renders one loop. Steady voices (snapped to whole cycles) are read from an offset Y past their attack and crossfaded across the
// seam (an identity for tonal content, a true crossfade for noise); event tails are folded onto the loop start.
// opts.raw = no snap, no offset, no crossfade, no fold (test mutant). opts.ref = the second loop of a continuous two-loop render,
// scaled like the loop (the steady state the loop must equal; test reference).
export async function renderLoop(name, sr, profile, opts) {
  const def = LOOPS[name], Ls = loopSeconds(name), L = Math.round(Ls * sr), X = Math.round(CONFIG.xfadeS * sr), Y = Math.round(0.1 * sr);
  const phone = profile === 'phone', raw = !!(opts && opts.raw), seed = CONFIG.seed + hashName(name);
  const out = await loopBody(def, Ls, L, X, Y, sr, phone, raw, seed);
  const p = peakOf(out), r = rmsOf(out), k = p > 0 ? Math.min(db(CONFIG.loopRmsDb) / r, db(CONFIG.loopPeakDb) / p) : 1;
  if (opts && opts.ref) return scale(await loopRef(def, Ls, L, sr, phone, seed), k);
  return scale(out, k);
}
async function loopBody(def, Ls, L, X, Y, sr, phone, raw, seed) {
  const out = new Float32Array(L);
  if (def.steady) {
    const vs = raw ? def.steady() : snapVoices(def.steady(), Ls), total = raw ? Ls : (Y + L + X) / sr;
    const s = await renderVoices(vs, total, sr, phone, seed, total + 0.1);
    if (raw) out.set(s.subarray(0, L));
    else for (let i = 0; i < L; i++) out[i] = i < X ? s[Y + i] * (i / X) + s[Y + L + i] * (1 - i / X) : s[Y + i];
  }
  if (def.events) {
    const ev = def.events(), tail = raw ? Ls : Math.max(Ls, voicesEnd(ev) + 0.05);
    const e = await renderVoices(ev, tail, sr, phone, seed + 1, 0);
    for (let i = 0; i < L; i++) out[i] += e[i];
    if (!raw) for (let i = L; i < e.length; i++) out[i % L] += e[i];
  }
  return out;
}
async function loopRef(def, Ls, L, sr, phone, seed) {
  const out = new Float32Array(L);
  if (def.steady) {
    const vs = snapVoices(def.steady(), Ls), s = await renderVoices(vs, (2 * L) / sr, sr, phone, seed, (2 * L) / sr + 0.1);
    for (let i = 0; i < L; i++) out[i] = s[L + i];
  }
  if (def.events) {
    const ev = def.events(), both = ev.concat(shift(ev, Ls)), e = await renderVoices(both, (2 * L) / sr, sr, phone, seed + 1, 0);
    for (let i = 0; i < L; i++) out[i] += e[L + i];
  }
  return out;
}

// ---------- mixer (shared by live play and the offline ramp render) ----------
function clipCurve(ceil) {
  const n = 2049, cv = new Float32Array(n);
  for (let i = 0; i < n; i++) { const x = (i / (n - 1)) * 2 - 1; cv[i] = ceil * Math.tanh((x * 2) / ceil); }
  return cv;
}
function makeGraph(c) {
  const G = {};
  G.master = c.createGain(); G.master.gain.value = CONFIG.master;
  G.comp = c.createDynamicsCompressor();
  const K = CONFIG.comp; G.comp.threshold.value = K.threshold; G.comp.knee.value = K.knee; G.comp.ratio.value = K.ratio; G.comp.attack.value = K.attack; G.comp.release.value = K.release;
  G.pre = c.createGain(); G.pre.gain.value = 0.5;
  G.clip = c.createWaveShaper(); G.clip.curve = clipCurve(CONFIG.clip);
  G.comp.connect(G.pre); G.pre.connect(G.clip); G.clip.connect(G.master); G.master.connect(c.destination);
  G.bus = {};
  for (const k of ['sfx', 'music', 'amb', 'voice']) { G.bus[k] = c.createGain(); G.bus[k].gain.value = CONFIG.vol[k]; G.bus[k].connect(G.comp); }
  G.duck = c.createGain(); G.lp = c.createBiquadFilter(); G.lp.type = 'lowpass'; G.lp.frequency.value = CONFIG.music.lp[0]; G.lp.Q.value = 0.5;
  G.lp.connect(G.duck); G.duck.connect(G.bus.music);
  G.layer = {};
  for (const k in CONFIG.music.layers) { G.layer[k] = c.createGain(); G.layer[k].gain.value = 0; G.layer[k].connect(G.lp); }
  for (const k of ['room', 'wind', 'fire']) { G.layer['a_' + k] = c.createGain(); G.layer['a_' + k].gain.value = 0; G.layer['a_' + k].connect(G.bus.amb); }
  G.loopSrc = [];
  return G;
}
const smooth = (x, a, b) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
function applyIntensity(G, v, t, tau) {
  const L = CONFIG.music.layers;
  for (const k in L) G.layer[k].gain.setTargetAtTime(smooth(v, L[k].win[0], L[k].win[1]) * db(L[k].db), t, tau);
  const lp = CONFIG.music.lp; G.lp.frequency.setTargetAtTime(lp[0] * Math.pow(lp[1] / lp[0], v), t, tau);
}
function applyAmb(G, fire, wind, t, tau) {
  const A = CONFIG.amb;
  G.layer.a_room.gain.setTargetAtTime(db(A.room), t, tau);
  G.layer.a_wind.gain.setTargetAtTime(db(A.wind) * wind, t, tau);
  G.layer.a_fire.gain.setTargetAtTime(db(A.fire) * fire, t, tau);
}
function toBuffer(c, x, sr) { const b = c.createBuffer(1, x.length, sr); b.getChannelData(0).set(x); return b; }
function startLoops(c, G, loops, sr, t0) {
  for (const k in loops) {
    const s = c.createBufferSource(); s.buffer = toBuffer(c, loops[k], sr); s.loop = true;
    s.connect(G.layer[k]); s.start(t0); G.loopSrc.push(s);
  }
}

// Offline ramp (preview and loudness gate): music and ambience through the real mixer, intensity 0 to 1 over the run.
export async function renderRamp(sr, seconds, profile, loops) {
  const C = OAC(), c = new C(1, Math.round(seconds * sr), sr), G = makeGraph(c);
  startLoops(c, G, loops, sr, 0);
  for (let s = 0; s <= seconds; s++) { const v = Math.min(1, s / (seconds - 6)); applyIntensity(G, v, s, CONFIG.music.tau); applyAmb(G, 0.15 + 0.85 * v, 0.7, s, 1); }
  const b = await c.startRendering();
  return b.getChannelData(0);
}

// ---------- live play ----------
// Empty catch blocks below are on purpose: audio must never stop the game; a failure leaves that sound silent.
const S = { ctx: null, G: null, profile: 'desktop', sr: 0, buf: Object.create(null), rec: Object.create(null), loops: null, voices: [], vvoices: [],
  mode: 'on', reduce: false, vol: { sfx: 1, music: 1, amb: 1, voice: 1, master: 1 }, paused: false, hidden: false, intensity: 0, fire: 0, wind: 0.7,
  lx: 0, lz: 0, t0: -1, rendering: false, ready: 0, total: 0, unlocked: false, silent: null, inited: false };

function loadSettings() {
  try { const j = JSON.parse(localStorage.getItem(CONFIG.saveKey) || 'null'); if (j) { if (CONFIG.modes.indexOf(j.mode) >= 0) S.mode = j.mode; S.reduce = !!j.reduce; if (j.vol) for (const k in S.vol) if (typeof j.vol[k] === 'number') S.vol[k] = j.vol[k]; } } catch (e) { }
}
function saveSettings() { try { localStorage.setItem(CONFIG.saveKey, JSON.stringify({ mode: S.mode, reduce: S.reduce, vol: S.vol })); } catch (e) { } }

export function init(opts) {
  if (S.inited) return;
  S.inited = true;
  const o = opts || {};
  try { S.profile = o.profile || ((globalThis.matchMedia && matchMedia('(pointer: coarse)').matches) ? 'phone' : 'desktop'); } catch (e) { S.profile = 'desktop'; }
  loadSettings();
  const el = o.unlockEl || globalThis;
  if (el && el.addEventListener) for (const ev of ['pointerdown', 'touchend', 'keydown']) el.addEventListener(ev, unlock, { passive: true });
  if (globalThis.document) document.addEventListener('visibilitychange', () => { S.hidden = document.hidden; runState(); });
}

function silentLoop() {
  // iOS silent switch fallback (13a): a looping silent <audio> started inside the unlock gesture.
  try {
    if (S.silent || !globalThis.Audio) return;
    const n = 4800, b = new Uint8Array(44 + n * 2), dv = new DataView(b.buffer), w = (o, s) => { for (let i = 0; i < s.length; i++) b[o + i] = s.charCodeAt(i); };
    w(0, 'RIFF'); dv.setUint32(4, 36 + n * 2, true); w(8, 'WAVEfmt '); dv.setUint32(16, 16, true); dv.setUint16(20, 1, true); dv.setUint16(22, 1, true);
    dv.setUint32(24, 48000, true); dv.setUint32(28, 96000, true); dv.setUint16(32, 2, true); dv.setUint16(34, 16, true); w(36, 'data'); dv.setUint32(40, n * 2, true);
    let s = ''; for (let i = 0; i < b.length; i++) s += String.fromCharCode(b[i]);
    const a = new Audio('data:audio/wav;base64,' + btoa(s)); a.loop = true; a.setAttribute('playsinline', ''); S.silent = a;
    const p = a.play(); if (p && p.catch) p.catch(() => {});
  } catch (e) { }
}

// Call inside the tap-to-begin gesture (init also hooks the first pointer or key event). Safe to call again (interrupted contexts retry here).
export function unlock() {
  try {
    if (!S.ctx) {
      const AC = globalThis.AudioContext || globalThis.webkitAudioContext; if (!AC) return;
      S.ctx = new AC(); S.G = makeGraph(S.ctx);
      S.sr = S.profile === 'phone' ? Math.min(S.ctx.sampleRate, CONFIG.phoneRate) : S.ctx.sampleRate;
      buildPools(); applyBuses();
    }
    if (navigator.audioSession) { try { navigator.audioSession.type = 'playback'; } catch (e) { } } else silentLoop();
    if (S.ctx.state !== 'running' && !S.paused && !S.hidden) { const p = S.ctx.resume(); if (p && p.catch) p.catch(() => {}); }
    S.unlocked = true;
    if (!S.rendering) { S.rendering = true; renderQueue(); }
  } catch (e) { }
}

function buildPools() {
  const c = S.ctx, n = CONFIG.pool[S.profile];
  for (let i = 0; i < n; i++) { const g = c.createGain(), p = c.createStereoPanner ? c.createStereoPanner() : null; if (p) { g.connect(p); p.connect(S.G.bus.sfx); } else g.connect(S.G.bus.sfx); S.voices.push({ g, p, src: null, end: 0, tell: false }); }
  for (let i = 0; i < CONFIG.pool.voice; i++) { const g = c.createGain(); g.connect(S.G.bus.voice); S.vvoices.push({ g, p: null, src: null, end: 0, tell: true }); }
}

async function renderQueue() {
  // Tells first (they carry gameplay), then her stingers, then the rest; music and ambience last, started together.
  const names = Object.keys(SOUNDS), rank = { tell: 0, voice: 1, heavy: 2, sfx: 3, ui: 4 };
  names.sort((a, b) => rank[SOUNDS[a].cat] - rank[SOUNDS[b].cat]);
  S.total = names.length + Object.keys(LOOPS).length;
  for (const n of names) {
    try { const x = await renderSound(n, S.sr, S.profile); S.buf[n] = toBuffer(S.ctx, x, S.sr); S.rec[n] = { cat: SOUNDS[n].cat, last: -1, n: 0 }; S.ready++; } catch (e) { }
    await new Promise((r) => setTimeout(r, 0));
  }
  const loops = {};
  for (const k in LOOPS) { try { loops[k] = await renderLoop(k, S.sr, S.profile); S.ready++; } catch (e) { } await new Promise((r) => setTimeout(r, 0)); }
  S.loops = loops;
  const t0 = S.ctx.currentTime + 0.1; S.t0 = t0;
  startLoops(S.ctx, S.G, loops, S.sr, t0);
  applyIntensity(S.G, S.intensity, S.ctx.currentTime, 0.5); applyAmb(S.G, S.fire, S.wind, S.ctx.currentTime, 0.5);
}

function busTarget(k) {
  const m = S.mode, on = m === 'on' || (m === 'music' && (k === 'music' || k === 'amb')) || (m === 'fx' && (k === 'sfx' || k === 'voice'));
  let v = on ? CONFIG.vol[k] * S.vol[k] : 0;
  if (k === 'voice' && S.reduce) v *= db(CONFIG.reduce.voiceDb);
  return v;
}
function applyBuses() {
  if (!S.G) return;
  const t = S.ctx.currentTime, tau = CONFIG.busTau;
  for (const k in S.G.bus) S.G.bus[k].gain.setTargetAtTime(busTarget(k), t, tau);
  S.G.master.gain.setTargetAtTime(CONFIG.master * S.vol.master, t, tau);
}
function runState() {
  if (!S.ctx) return;
  try { const p = (S.paused || S.hidden) ? S.ctx.suspend() : S.ctx.resume(); if (p && p.catch) p.catch(() => {}); } catch (e) { }
}
function newSource() { return S.ctx.createBufferSource(); }

// PERFRAME-BEGIN (per-event code: no allocation except the one-shot source made in newSource above, allowed by the perf rules for one-shot sounds)
export function setListener(x, z) { S.lx = x; S.lz = z; }
// Plays a rendered sound. x, z = world position (omit for a sound at the listener); rate = playback rate (bootleg copies use 0.85).
export function play(name, x, z, rate) {
  if (!S.ctx || S.paused || S.hidden || S.mode === 'off') return false;
  const b = S.buf[name], rec = S.rec[name]; if (!b) return false;
  const now = S.ctx.currentTime, cat = rec.cat, isVoice = cat === 'voice';
  let gain = 1, pan = 0;
  if (x !== undefined && !isVoice) {
    const dx = x - S.lx, dz = z - S.lz, d = Math.sqrt(dx * dx + dz * dz);
    if (d > CONFIG.range) return false;
    gain = CONFIG.refM / (CONFIG.refM + CONFIG.rolloff * Math.max(0, d - CONFIG.refM));
    pan = Math.max(-1, Math.min(1, dx / CONFIG.panM)) * CONFIG.panMax;
  }
  if (now - rec.last < CONFIG.sameS) { if (rec.n >= CONFIG.sameN) return false; rec.n++; } else { rec.last = now; rec.n = 1; }
  if (cat === 'heavy' && S.reduce) gain *= db(CONFIG.reduce.heavyDb);
  const pool = isVoice ? S.vvoices : S.voices;
  let v = null, old = null;
  for (let i = 0; i < pool.length; i++) { const p = pool[i]; if (p.end <= now) { v = p; break; } if (!p.tell && (!old || p.end < old.end)) old = p; }
  if (!v) { v = old || pool[0]; if (v.src) { try { v.src.stop(now); } catch (e) { } } }
  let when = now;
  if (isVoice && S.t0 >= 0 && !S.reduce) {
    const beat = 60 / CONFIG.music.bpm, k = Math.ceil((now - S.t0) / beat), nb = S.t0 + k * beat;
    if (nb - now <= CONFIG.music.quantBeats * beat) when = nb;
  }
  const src = newSource(), r = rate || 1;
  src.buffer = b; src.playbackRate.value = r; src.connect(v.g);
  v.g.gain.setValueAtTime(gain, when); if (v.p) v.p.pan.setValueAtTime(pan, when);
  src.start(when); v.src = src; v.end = when + b.duration / r; v.tell = cat === 'tell' || isVoice;
  if (isVoice) { const D = CONFIG.music.duck; S.G.duck.gain.setTargetAtTime(db(S.reduce ? D.db / 2 : D.db), Math.max(now, when - 0.03), D.inTau); S.G.duck.gain.setTargetAtTime(1, when + b.duration * 0.8, D.outTau); }
  return true;
}
// Master intensity 0-1 (calm to the heaviest fight); smoothed on the audio clock.
export function setIntensity(v) {
  const x = Math.max(0, Math.min(S.reduce ? CONFIG.reduce.maxIntensity : 1, v));
  if (x === S.intensity) return; S.intensity = x;
  if (S.G && S.t0 >= 0) applyIntensity(S.G, x, S.ctx.currentTime, CONFIG.music.tau);
}
// Ambience levels 0-1: fire (a burning wing near the player), wind (open courts and bridges over the lake).
export function setAmb(fire, wind) {
  if (fire === S.fire && wind === S.wind) return; S.fire = fire; S.wind = wind;
  if (S.G && S.t0 >= 0) applyAmb(S.G, fire, wind, S.ctx.currentTime, 1);
}
// PERFRAME-END

// Sound mode: 'on' | 'music' (music and ambience) | 'fx' (effects and stingers) | 'off'. Saved.
export function setMode(m) { if (CONFIG.modes.indexOf(m) < 0) return; S.mode = m; applyBuses(); saveSettings(); }
export function cycleMode() { const i = CONFIG.modes.indexOf(S.mode); setMode(CONFIG.modes[(i + 1) % CONFIG.modes.length]); return S.mode; }
// Reduce intensity (13d): stingers and heavy hits quieter, music capped, no beat-wait before stingers. Saved.
export function setReduce(on) { S.reduce = !!on; applyBuses(); const v = S.intensity; S.intensity = -1; setIntensity(v); saveSettings(); }
// Volume 0-1 per bus: 'master', 'sfx', 'music', 'amb', 'voice'. Saved.
export function setVolume(bus, v) { if (!(bus in S.vol)) return; S.vol[bus] = Math.max(0, Math.min(1, v)); applyBuses(); saveSettings(); }
// Game pause and menus: the audio clock stops, so loops, ramps and queued sounds all freeze.
export function pause() { S.paused = true; runState(); }
export function resume() { S.paused = false; runState(); }
// Read-only state for tests and the settings menu.
export function status() { return { ctx: S.ctx ? S.ctx.state : 'none', profile: S.profile, mode: S.mode, reduce: S.reduce, ready: S.ready, total: S.total, music: S.t0 >= 0, intensity: S.intensity }; }
