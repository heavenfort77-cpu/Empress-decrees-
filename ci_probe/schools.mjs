// Per-school whole matches (batch 16 close-out): the player takes each school in turn (old autopilot, as check 65), 12 seeds each (check 65's seeds),
// watched to the end. Prints per player school: decided range, decrees told per match (bounty included), player plate rate, leader win share, player wins;
// and per school as a bot: wins and R casts per royale. Usage: node ci_probe/schools.mjs [school indexes, e.g. 0,1,2]
import { open } from './harness.mjs';
const only = (process.argv[2] || '').split(',').filter(Boolean).map(Number);
const { page, errors, close } = await open();
const res = await page.evaluate((only) => {
  const G = __game, C = G.config, SC = C.SCHOOLS, seeds = [12345, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], out = [];
  for (let s = 0; s < SC.length; s++) {
    if (only.length && !only.includes(s)) continue;
    const row = { school: SC[s], built: !!C.KITS[SC[s]].built, decided: [], told: [], plate: 0, leadWin: 0, pWin: 0, pUlt: 0, bot: {} };
    for (const seed of seeds) {
      G.setSeed(seed); G.setBots(C.BOTS.count); G.setPkitP(false); G.pickSchool(s); G.autoPlayer(true); G.setWatch(true);
      let prevSt = 0, prevKey = '', told = 0; const lead = {};
      for (let t = 0; t < 300 / C.STEP; t++) {
        G.step(1);
        const d = G.decree(), l = G.leader();
        if (d.st >= 2 && (prevSt < 2 || d.key !== prevKey)) told++;
        prevSt = d.st; prevKey = d.key;
        if (l.phase === 'royale' && l.id >= 0) lead[l.id] = (lead[l.id] || 0) + 1;
        if (G.royale().decidedAt >= 0) break;
      }
      const suits = G.schools().suits, bl = G.bots().list, p = G.player();
      const win = !p.dead ? 0 : (bl.find((q) => !q.dead) || { id: -1 }).id;
      const top = Object.entries(lead).sort((a, b) => b[1] - a[1])[0];
      row.decided.push(+G.royale().decidedAt.toFixed(1)); row.told.push(told);
      if (p.plates > 0) row.plate++; if (top && +top[0] === win) row.leadWin++; if (win === 0) row.pWin++;
      row.pUlt += G.kitState(-1).ultN;
      for (let k = 0; k < bl.length; k++) {
        const sc = suits[k + 1].school, b = row.bot[sc] || (row.bot[sc] = { n: 0, win: 0, ult: 0 });
        b.n++; b.ult += G.kitState(k).ultN; if (win === k + 1) b.win++;
      }
      G.setWatch(false); G.autoPlayer(false);
    }
    out.push(row);
  }
  G.setPkitP(true); G.pickSchool(0); G.setBots(0); G.reset();
  const built = {}; for (const sc of SC) built[sc] = !!C.KITS[sc].built;
  return { names: SC, rows: out, built };
}, only);
const bot = {};
for (const r of res.rows) {
  const mm = (a) => `${Math.min(...a)}-${Math.max(...a)}`, dec = r.decided.filter((x) => x >= 0), und = r.decided.length - dec.length;
  console.log(`P ${r.school}${r.built ? '' : ' (not built)'}: decided ${mm(dec)} s${und ? ` (${und} undecided at 300 s)` : ''}; told ${mm(r.told)}/match; plate ${r.plate}/12; leaderWin ${r.leadWin}/12; playerWin ${r.pWin}/12; player R ${(r.pUlt / 12).toFixed(1)}/royale`);
  for (const [sc, b] of Object.entries(r.bot)) { const a = bot[sc] || (bot[sc] = { n: 0, win: 0, ult: 0 }); a.n += b.n; a.win += b.win; a.ult += b.ult; }
}
for (const sc of res.names) if (bot[sc]) console.log(`BOT ${sc}${res.rows[0] && res.built && !res.built[sc] ? ' (not built)' : ''}: wins ${bot[sc].win}/${bot[sc].n}; R ${(bot[sc].ult / bot[sc].n).toFixed(2)}/royale`);
console.log('ERRORS ' + errors.length + (errors.length ? ' ' + errors.slice(0, 2).join(' | ') : ''));
await close();
