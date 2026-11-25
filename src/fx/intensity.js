// Music intensity and ambience from game state (PREP-AV 25 Nov; docs/AUDIO.md "Proposed intensity mapping" made concrete; docs/HOOKS-17c.md
// lists where each input comes from in index.html). The game writes plain numbers into IN (no object per frame); stepIntensity reads them,
// holds a level for INT_CONFIG.holdS before it falls (no flapping between fight and calm), and calls sound.js only on a change.
export const INT_CONFIG = {
  // Levels (docs/AUDIO.md): exploring, a rival or squad in the room, a fight on, danger (low health, giant awake, burn warning on my wing), peak.
  explore: 0.1, near: 0.3, fight: 0.5, danger: 0.7, peak: 1.0,
  // A fight counts for this long after the player last attacked, cast or was hurt, s.
  fightS: 4,
  // Health share under which the player is in danger.
  lowHp: 0.5,
  // Suits left (the player included) at or under which the end is near: peak.
  lastSuits: 2,
  // A level holds this long before the music may fall to a lower one, s (rises are at once; sound.js smooths with tau 1.2 s).
  holdS: 3,
  // Wind per room type (0-1): open courts and bridges over the black lake are windy, halls are still. Royal Rumble map: rumble.
  wind: { bridge: 1, court: 0.7, garden: 0.6, corridor: 0.4, hall: 0.2, core: 0.1, rumble: 0.5 },
  // Fire: a burning wing near the player; during the 5 s warning of the player's own wing it rises from warnFrom to 1.
  fire: { near: 0.3, warnFrom: 0.4 },
};

// Inputs, written by the game where it already knows them (all numbers or booleans; 0 / false when not in that state).
export const IN = {
  // seconds since the player last attacked, cast or was hurt (large when never)
  sinceFight: 99,
  // the player's health share 0-1
  hpFrac: 1,
  // rivals (other suits) and enemy units (guard, rebels, cubs) seen in the player's room or vision
  rivalsNear: 0, unitsNear: 0,
  // awake bronze giants in the player's room
  giantsAwake: 0,
  // the burn: 1 while the player's own wing is warned (warnProgress 0-1 over the warning), 1 while it falls with the player inside
  burnMine: 0, burnProgress: 0, burnFalling: 0, burnNear: 0,
  // the apex is awake or hunting (G.phase 'wake' or 'hunt')
  apex: 0,
  // suits still in the match (the player included)
  suitsLeft: 10,
  // room type for the wind ('hall', 'court', 'corridor', 'garden', 'bridge', 'core', 'rumble')
  room: 'rumble',
};

const ST = { level: -1, holdT: 0, fire: -1, wind: -1 };

// PERFRAME-BEGIN (stepIntensity, levelOf: numbers only; sound.js is called only when a value changes)
// The target level from IN (the highest condition that holds).
export function levelOf(i) {
  const C = INT_CONFIG;
  if (i.apex || i.burnFalling || (i.suitsLeft > 0 && i.suitsLeft <= C.lastSuits)) return C.peak;
  if (i.hpFrac < C.lowHp || i.giantsAwake > 0 || i.burnMine) return C.danger;
  if (i.sinceFight < C.fightS) return C.fight;
  if (i.rivalsNear > 0 || i.unitsNear > 0) return C.near;
  return C.explore;
}
// Once per game frame (not while paused). dt in s (clamped by the caller's MAX_DT). snd = the sound.js namespace. Returns the level in force.
export function stepIntensity(dt, snd) {
  const want = levelOf(IN);
  if (want >= ST.level) { ST.level = want; ST.holdT = INT_CONFIG.holdS; }
  else { ST.holdT -= dt; if (ST.holdT <= 0) { ST.level = want; ST.holdT = INT_CONFIG.holdS; } }
  if (snd) snd.setIntensity(ST.level);
  const F = INT_CONFIG.fire;
  const fire = IN.burnMine ? F.warnFrom + (1 - F.warnFrom) * IN.burnProgress : (IN.burnNear ? F.near : 0);
  const w = INT_CONFIG.wind[IN.room], wind = w === undefined ? INT_CONFIG.wind.rumble : w;
  if ((fire !== ST.fire || wind !== ST.wind) && snd) { ST.fire = fire; ST.wind = wind; snd.setAmb(fire, wind); }
  return ST.level;
}
// PERFRAME-END

// New run: calm, levels forgotten (the next step sets them again).
export function resetIntensity() {
  ST.level = -1; ST.holdT = 0; ST.fire = -1; ST.wind = -1;
  IN.sinceFight = 99; IN.hpFrac = 1; IN.rivalsNear = 0; IN.unitsNear = 0; IN.giantsAwake = 0; IN.burnMine = 0; IN.burnProgress = 0;
  IN.burnFalling = 0; IN.burnNear = 0; IN.apex = 0; IN.suitsLeft = 10; IN.room = 'rumble';
}
