# Audio design note (AUDIO worker, 25 Nov; owner 02:3x: attack SFX and tells, Kaymuse's stingers, palace ambience, music; generated in code for now)
Status: design note plus a prototype module, src/audio/sound.js. NOT in the game yet: the index.html writer wires it in (API below).
Nothing here was heard by Claude. The numbers were measured from offline renders on a GitHub runner (see "Gates"). The owner's ears decide.

## Rules this follows
- Generated in code: no files, no licences, nothing to credit (13a, 13e). itch.io AI disclosure: code-made sound written by Claude is a grey zone. The cautious reading is to disclose it (13e). That is the owner's call.
- No live synthesis in play (13f). At the first tap every effect is rendered once into a buffer with OfflineAudioContext. Music and ambience are pre-rendered loops. During play the only thing made is one AudioBufferSourceNode per sound (perf rule: one-shot sources are fine). Gains, panners, buses, the compressor and the clip are built once.
- Phones get tonal sounds only (13f): every noise layer is marked desktop only and skipped on phones. Phones render at 24 kHz.
- Every gameplay-critical tell has a 1-4 kHz layer (clicks, bell partials or a scrape) so laptop speakers carry it (13a). The gate measures it.
- Nothing runs while paused or while the tab is hidden: the AudioContext is suspended, so the loops, ramps and queued sounds all stop with the audio clock.
- The sound mode toggle ships from day one: ON / MUSIC ONLY / FX ONLY / OFF (13f).
- Speakers first: low sounds are harmonic stacks between 150 and 1000 Hz; nothing relies on sub-bass (13d).

## Palette (Qin; original sounds, never copied from any game)
- Tuning: 五声 (gong 宫, shang 商, jue 角, zhi 徵, yu 羽) built by 三分损益, the ratios of fifths in the 管子 and the 吕氏春秋: 1, 9/8, 81/64, 3/2, 27/16. 宫 = 174.61 Hz (CONFIG.music.gongHz). The music sits in the 羽 mode, the minor-like mode (13b: minor is the strongest cue for dread). `N(i)` gives step i from 宫. The computed table is printed once in every runner log.
- Instruments, all synthesised:
  - 编钟 bronze bells: inharmonic partials 1, 1.19, 2, 2.92, 4.2, 5.4. The 1.19 partial is the side strike tone, a minor third up.
  - 磬 stone chimes: partials 1, 2.32, 4.25, 6.63, 9.4, with a fast decay.
  - 建鼓 drums: a pitch-dropped membrane, its 1.59x mode, and a 2x/3x stack for small speakers.
  - 琴/瑟 plucks: additive harmonics with a pluck-position shape and faster decay up high.
  - 埙 ocarina and 缶 clay pot.
  - Her "voice": a sawtooth through vowel formants, a hum that is never speech.
- The nine schools each have a sonic family. Each school also has its own hit sound, so a player can tell rivals apart by ear:

| School | Family | Character |
|---|---|---|
| 儒 ru | 编钟 bells, 宫 | Dignified. The R rings sound exactly when the game's three bell rings fire (0.6, 1.3, 2.0 s) |
| 道 dao | 琴 harmonics 泛音, glides | Soft and yielding. A bright double pluck marks a successful counter |
| 法 fa | 磬 stone chime, 拍板 clapper | Cold and exact |
| 墨 mo | Wooden machines: crossbow twang, ratchets, low drum | Mechanical. No dash, so there is no dash sound |
| 阴阳 yinyang | Paired tones: yin low and yang high, crossing glides | Balanced |
| 杂 za | Bell plus chime, odd FM | Borrowed from everyone |
| 名 ming | Wheel whirr (AM), 瑟 plucks, an "arrow" that keeps rising (the paradox) | Uncanny |
| 纵横 zongheng | Two tones beating against each other; crossing swaps | Persuasive |
| 农 nong | 缶 clay pot, 埙 ocarina, sprouting chirps | Earthy |

## Sound list mapped to the game (CONFIG names as in index.html; sound names as in SOUNDS)
Slots: windup = the tell, which plays at windup start and swells to the release. Release = when the move fires. Hit = when it lands. Whiff = a miss.
"none" means the move has no windup (delay 0, instant). Shared means the sound is reused, sometimes at another playback rate (the `rate` argument of play).

### Suits (CONFIG.KITS; player and bots use the same kits)
| Move | Windup | Release | Hit | Whiff |
|---|---|---|---|---|
| ru attack (close/far, volley every 6th) | none | ru_atk | ru_hit | ru_whiff |
| ru Q dash-in | none | ru_q | ru_hit (rate 0.8) | ru_whiff |
| ru W seal line | none | ru_w | ru_hit (rate 0.8) | ru_whiff |
| ru R bells (rings 0.6/1.3/2.0) | none | ru_r (rings timed in the sound) | ru_hit | none |
| dao attack | none | dao_atk | dao_hit | dao_whiff |
| dao Q rou / W zheng stances | none | dao_q / dao_w | dao_counter on a successful counter | none |
| dao R fan | none | dao_r | none | none |
| fa attack | none | fa_atk | fa_hit | fa_whiff |
| fa Q pursuit dash | none | fa_q | fa_hit (rate 0.8) | fa_whiff |
| fa W unseen | none | fa_w (rivals hear it only within range) | none | none |
| fa R aura | none | fa_r | none | none |
| mo attack (bolt, 6 m) | none | mo_atk | mo_hit | mo_whiff |
| mo Q wall | none | mo_q | none | none |
| mo W lever (delay 0.6) | mo_w_tell (0.6 s) | mo_w | mo_hit (rate 0.8) | mo_whiff |
| mo R jiu | none | mo_r | none | none |
| yinyang attack (orb) | none | yy_atk | yy_hit | yy_whiff |
| yinyang Q yin orb | none | yy_q | yy_hit (rate 0.8) | yy_whiff |
| yinyang W yang (delay 0.8) | yy_w_tell (0.8 s) | yy_w | yy_hit | yy_whiff |
| yinyang R taiji (tellS 1) | yy_r_tell (1.0 s) | yy_r | yy_hit (each pulse, rate 1.2) | none |
| za attack (orb) | none | za_atk | za_hit | za_whiff |
| za Q seal / W blink / R copy | none | za_q / za_w / za_r | za_hit (rate 0.8) | za_whiff |
| ming attack (wheel) | none | ming_atk | ming_hit | ming_whiff |
| ming Q blink / W hang line / R pierce | none | ming_q / ming_w / ming_r | ming_hit (rate 0.8) | ming_whiff |
| zongheng attack | none | zh_atk | zh_hit | zh_whiff |
| zongheng Q link / W swap / R persuade | none | zh_q / zh_w / zh_r | zh_hit | zh_whiff |
| nong attack | none | nong_atk | nong_hit | nong_whiff |
| nong Q sow / W furrow / R harvest | none | nong_q / nong_w / nong_r | nong_hit | nong_whiff |
| Ultimate meter full (ULT.full) | | ult_ready (UI, player only) | | |

### Tiger Demon and hunt minions (CONFIG.MOVES, DEMON_ULT, APEX)
| Move | Windup (tell) | Release | Hit |
|---|---|---|---|
| Apex wakes (APEX.wakeS 3) | demon_wake (3 s) | | |
| claw (0.45) | demon_claw_tell | demon_claw | demon_hit |
| pounce (0.5) | demon_pounce_tell | demon_pounce | demon_hit |
| roar (0.7, slow) | demon_roar_tell | demon_roar | p_slow on the player |
| Shed the limit (DEMON_ULT 0.8) | demon_ult_tell | demon_roar (rate 1.2) | |
| bite (0.4) | cub_bite_tell | cub_bite | unit_hit |
| lunge (0.45) | cub_lunge_tell | cub_lunge | unit_hit |
| rend (0.5, bleed) | cub_rend_tell | cub_rend | p_bleed per stack |
| flank (0.6, stun) | cub_flank_tell | cub_flank | p_stun |
| howl (0.7, slow) | cub_howl_tell | cub_howl | p_slow |
| Cubs at camps (CUB) | same as minions at rate 1.15 (smaller) | | |

### 皇家 guard and 反贼 rebels (CONFIG.GUARD.moves, FANZEI)
| Move | Windup (tell) | Release | Hit |
|---|---|---|---|
| thrust 卒 (0.5) | g_thrust_tell | g_thrust | unit_hit |
| volley 弩 (0.8, mark) | g_volley_tell | g_volley | unit_hit |
| shove 盾 (0.5) | g_shove_tell | g_shove | unit_hit |
| charge 车 (0.9) | g_charge_tell | g_charge | demon_hit (rate 1.3) |
| cut 伍长 (0.5) | g_cut_tell | g_cut | unit_hit |
| 伍长 breaks (squad buff ends) | | g_break | |
| talisman 符水 (0.8, heal mark) | r_talisman_tell | r_talisman | |
| lunge 死士 (0.6, the yellow glint) | r_lunge_tell | r_lunge | unit_hit |
| cleave 渠帅 (0.6) | r_cleave_tell | r_cleave | unit_hit |
| 力士 bootleg moves (0.8-1.0) | r_bootleg_tell | the school's Q or W at rate 0.85 (a cracked copy) | the school's hit at rate 0.85 |
| 力士 stall (spark flash) | | r_stall | |
| A guard or rebel unit breaks | | unit_break | |
| The player takes a rebel charge | | plate_take (rate 0.9) | |

### Palace pieces and royale hazards (CONFIG.STATUE, LION, PIECES, PIECES2, BURN, PAL_LOCK)
| Piece | Windup (tell) | Release / effect |
|---|---|---|
| Tiger statue (0.6) | statue_tell | statue_strike |
| 石狮 lions (0.6; becoming bronze guardian beasts) | lion_tell | lion_strike |
| 水银 mercury (warn 0.6, on 1.2) | merc_warn | merc_on |
| 十二金人 giant wakes (wakeS 2) | giant_wake | |
| Giant slam (1.0) | giant_slam_tell | giant_slam |
| Giant sweep (1.2) | giant_sweep_tell | giant_sweep |
| Giant breaks (fallS 0.8) | | giant_fall |
| 门海 vat (crackS 0.5) | vat_crack | vat_splash |
| A wing burns (warnS 5) | st_burn (her stinger) and fire ambience rising | burn_fall when the wing falls |
| Doors lock / open | | door_lock / door_open |
| 鼎 cauldron or altar heal | | ding_heal |
| 华表 marking | dropped (owner 25 Nov 02:25: decoration only, no marking) | |

### The player, menus
- Player state: p_hurt, p_bleed, p_slow, p_stun, p_marked (a tell: you are seen by all), p_break, boon (crab or wanderer reward), plate_take.
- Menus: ui_move, ui_ok, ui_back.

### Kaymuse's stingers (synth, no speech; calm contempt, never a shout; each under 3 s per the tone brief)
| Stinger | Sound | Her lines (TEXT keys) it plays under |
|---|---|---|
| Decree | st_decree: two bell strikes a fifth apart over a hummed fifth | voice_dec_dry, voice_dec_nodash, voice_dec_silence, voice_dec_heights, voice_dec_ult2x, voice_kennel, voice_guard_break, voice_marked, voice_silenced, piece_voice_hb |
| Burning warning | st_burn: falling yu-zhi-yu bells, a fire tremolo and a low swell | burn_voice, voice_wave0-4, voice_fell |
| Bounty | st_bounty: a cascade of coin chimes, a drum and a bell | voice_bounty, voice_bounty_paid, fz_voice_charge, voice_plate, voice_plate_take |
| Wake | st_wake: a deep bell and a hum rising to an unresolved shang | voice_wake, voice_frenzy, pal_voice_core, voice_won, voice_lost, pal_voice_lost, voice_died, voice_royale_lost |
| Silent for now | | voice_crab, voice_wander, voice_boon (small events; boon plays instead) |

Stingers wait for the next music beat on the audio clock if it is at most half a beat away. The music ducks 8 dB under them.

## Ambience (CONFIG.amb; loops of 16 s)
- Room tone (a_room): a low hall hum at 147/221/295 Hz. Always on and very low, so silence never sounds like a bug (13b).
- Wind over the black lake (a_wind): whistling tones that rise and fall. Desktop adds band noise. Level comes from setAmb(fire, wind): high on bridges and open courts, low in halls.
- Fire (a_fire): a flickering low rumble and tonal pops. Desktop adds a noise bed and crackle. Level is setAmb fire: a burning wing near the player. It should rise during the 5 s burn warning.

## Music (CONFIG.music; loops of 13.33 s = 4 bars at 72 BPM, all layers started together on the audio clock)
One master intensity value (0-1), set by setIntensity and smoothed with setTargetAtTime (tau 1.2 s). It drives:

| Layer | In over intensity | Content |
|---|---|---|
| m_drone | always | 瑟 drone on yu and its fifth, slow beating |
| m_bells | 0.10-0.35 | Slow 编钟 line in the yu mode, ending unresolved |
| m_pulse | 0.30-0.55 | 建鼓 on beats 1 and 3, with a stick click |
| m_drive | 0.55-0.80 | Off-beat drum and a 琴 ostinato in eighths |
| m_peak | 0.80-1.00 | Stone chimes a semitone apart (outside the five tones on purpose), a drum roll into each bar, a high tremolo |

A low-pass on the music bus also follows intensity, from 1.6 to 9 kHz (13b).
Proposed intensity mapping for the game writer (a proposal, not tuned):
- 0.1 exploring.
- 0.3 a rival or squad in the room.
- 0.5 a fight on.
- 0.7 the player below half health, a giant awake, or a burn warning in the player's wing.
- 1.0 the apex, the last two suits, or a wing falling with the player inside.

## Mix and bus chain
Effects (pooled voices: gain and stereo pan), stingers (two voices), music layers (into the low-pass and the duck), and ambience layers. These feed the buses sfx, voice, music and amb, then:
compressor (threshold -10 dB, ratio 8) → 0.5 pre-gain → tanh clip with a 0.7 ceiling (-3.1 dBFS, so the mix cannot pass -3 dBFS) → master 0.8 → output.
- Spatial: play(name, x, z) is heard within 26 m of setListener. It is at full level within 5 m, then rolls off, with pan up to 0.7 at 14 m to a side.
- Throttle: the same sound starts at most twice in 50 ms (a squad of nine thrusting together).
- Voice stealing: the oldest non-tell voice is stolen; tells and stingers are kept.

## Loudness targets (13d) and what the gates measure
- Effects are peak-normalised per category: tells -6, effects -7, heavy -5, stingers -4, UI -10 dBFS.
- Loops are RMS -18 dBFS, with peaks capped at -6.
- Music plus ambience ramp: whole -20 to -14 LUFS, calm first 10 s -26 to -18, peak last 10 s -18 to -12.
- Stingers: 3-15 LU over the calm bed.
- Everything stays at or under -3 dBFS peak, with no NaN and no clipping.

## Phone budget
- Phones render at 24 kHz into mono float buffers. Desktop renders at the context rate (48 kHz on the runner).
- The decoded size per profile is printed in the runner log (see Gates).
- Voices: 16 pooled effect voices on desktop, 8 on phones, plus 2 for stingers. Graph nodes are built once at unlock: one master chain, 4 buses, 8 loop gains, the pools.
- Render order at the first tap: tells first, then stingers, heavy hits, other effects and UI. The music and ambience loops come last and start together. A sound asked for before its render is done stays silent (play returns false).
- Not measured: render time and memory on a real phone. The runner's CPU render time is printed in the log; a phone will be slower.

## Settings and safety (13d, 13f)
- Sound mode: on / music (music and ambience) / fx (effects and stingers) / off. cycleMode() is for the M key and the pause menu.
- Reduce intensity: stingers 9 dB lower, heavy hits 6 dB lower, music intensity capped at 0.7, a lighter duck, and no beat-wait before a stinger.
- Volumes per bus (master, sfx, music, amb, voice), 0-1.
- Mode, reduce and volumes are saved in localStorage under empressDecrees.audio, inside try/catch.
- Unlock: init() hooks the first pointerdown, touchend or keydown. The game's tap-to-begin screen should also call unlock() inside its handler. It creates or resumes the context and sets navigator.audioSession.type = 'playback' where it exists (the iOS silent switch). Otherwise it loops a silent `<audio>` (data URI, no fetch). An interrupted context retries on the next tap.
- Untested here: an iPhone (silent switch, the interrupted state) and the 13f media-element path that phones needed on Briar Prince. Run the first build on a real phone and ask which sound mode is clean.

## Integration API (for the index.html writer)
```js
import * as SND from './src/audio/sound.js';
SND.init({ unlockEl: canvasOrWindow, profile: isPhone ? 'phone' : 'desktop' });  // once at load; profile optional (pointer: coarse)
SND.unlock();                          // inside the tap-to-begin handler (safe to call again)
SND.setListener(px, pz);               // per frame, the player's (or camera focus) x, z
SND.play('g_volley_tell', ux, uz);     // at windup start; returns false if out of range, not ready, paused or off
SND.play('ru_hit', x, z, 0.8);         // optional playback rate (heavier hit, bootleg copies 0.85)
SND.play('st_burn');                   // her stinger (no position: always heard, ducks the music)
SND.setIntensity(v);                   // 0-1, call on change (cheap when unchanged)
SND.setAmb(fire, wind);                // 0-1 each
SND.pause(); SND.resume();             // pause menu and end screens
SND.setMode('fx'); SND.cycleMode();    // sound mode toggle (M key, pause menu)
SND.setReduce(true); SND.setVolume('music', 0.5);
SND.status();                          // { ctx, profile, mode, reduce, ready, total, music, intensity } for tests
```
- play, setListener, setIntensity and setAmb sit between PERFRAME markers. They allocate nothing except the one-shot source. ci_audio/static.mjs checks this with the rules of tests/static-check.mjs.
- The game needs TEXT keys for the mode labels (proposal): snd_mode_on 'Sound: on', snd_mode_music 'Sound: music only', snd_mode_fx 'Sound: effects only', snd_mode_off 'Sound: off', snd_reduce 'Reduce intensity'.
- Bots' sounds play through the same calls. Range culling keeps off-screen fights quiet.

## Gates (runner: branch ci-audio, workflow audio-run; results on ci-out out/audio/ci-audio/<run>/)
Render in headless Chromium (OfflineAudioContext), then numpy and pyloudnorm in ci_audio/analyze.py:
1. Every sound, loop and both ramps render (phone and desktop).
2. Peak <= -3 dBFS everywhere.
3. No NaN and no clipped samples (float data, checked in the page).
4. Tells and stingers carry at least 10% of their energy in 1-4 kHz.
5. Phone renders are tonal: spectral flatness in 300-6000 Hz is at most 0.2.
6. Loops are seamless: the end-to-start first and second differences are within 2x the loop's own 99.9th percentile.
7. The ramp loudness falls inside the windows above.
8. Stingers sit 3-15 LU over the calm bed.

Each gate has a mutant that must fail it. The mutants are:
- a dropped sound;
- a tell at -1 dBFS;
- a NaN, and a clipped sample;
- a tell low-passed at 800 Hz;
- desktop noise renders used as phone renders;
- loops rendered without seam handling;
- the ramp at +8 dB and -10 dB;
- a stinger at +14 dB.

Results and run numbers: see the run log (job.log) on ci-out. The final numbers are in HANDOFF/overnight.log.
