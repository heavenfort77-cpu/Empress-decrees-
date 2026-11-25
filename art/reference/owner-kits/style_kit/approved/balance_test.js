// Sandbox balance test for suit_proto.html. Run: node balance_test.js [matches]
// 1) full 20-suit matches: wins per appearance with a 95% interval, pacing, kills/deaths
// 2) duel matrix: each pair fights 1v1 from the same growth clock (0, 250, 500 s) on the full map, 30 duels per cell, win share of the row suit
// Reports pass/fail and the failing lines. PASS needs: every faction within 3-35% of the expected win share, no duel pair worse than 20/80 at ALL three clocks, average length >= 560 s.
const fs=require("fs");const src=fs.readFileSync(__dirname+"/suit_proto.html","utf8");
const code=src.slice(src.indexOf("//@@LOGIC"),src.indexOf("//@@END"));const m={exports:{}};new Function("module",code)(m);const {createGame,CONFIG}=m.exports;
const facs=Object.keys(CONFIG.F);const NM=+(process.argv[2]||120);
const app={},win={},lens=[];facs.forEach(f=>{app[f]=0;win[f]=0});
for(let i=0;i<NM;i++){const G=createGame({seed:5000+i});let s=0;while(!G.over&&s<90000){G.step(0.1);s++}lens.push(G.t);
  G.suits.filter(x=>!x.owner).forEach(x=>app[x.f]++);if(G.winner)win[G.winner.f]++}
const avg=lens.reduce((a,b)=>a+b,0)/NM;const fails=[];
console.log("FULL MATCHES",NM,"avg",avg.toFixed(0),"s min",Math.min(...lens).toFixed(0),"max",Math.max(...lens).toFixed(0));
console.log("faction     appeared  wins  win/appearance  (fair share = 1/20 = 5.0%)  95% interval");
facs.forEach(f=>{const p=win[f]/app[f],n=app[f],se=Math.sqrt(p*(1-p)/n);const lo=Math.max(0,p-1.96*se),hi=p+1.96*se;
  console.log(f.padEnd(11),String(n).padStart(6),String(win[f]).padStart(6),(100*p).toFixed(1).padStart(10)+"%",`   ${(100*lo).toFixed(1)}-${(100*hi).toFixed(1)}%`);
  if(hi<0.03)fails.push(`${f}: win/appearance ${(100*p).toFixed(1)}% (interval ${(100*lo).toFixed(1)}-${(100*hi).toFixed(1)}%) is below the 3% floor`);
  if(lo>0.075)fails.push(`${f}: win/appearance ${(100*p).toFixed(1)}% (interval ${(100*lo).toFixed(1)}-${(100*hi).toFixed(1)}%) is above the 7.5% ceiling`)});
if(avg<560)fails.push(`average match ${avg.toFixed(0)} s < 560`);
// duels
const NDU=30;const clocks=[0,250,500];const M={};
function duel(a,b,clock,seed){const G=createGame({seed,factions:[a,b],suits:2});G.suits.forEach(s=>{s.clock=clock;});
  // park them 8 tiles apart in an empty centre, full zone, no storm
  G.suits[0].x=28;G.suits[0].y=32;G.suits[1].x=36;G.suits[1].y=32;for(let k=0;k<64*64;k++)G.tiles[k]=0;
  G.suits.forEach(s=>{s.aiGoal=null});let t=0;while(!G.over&&t<240){G.step(0.1);t+=0.1}return G.winner?G.winner.f==a?1:(G.winner.f==b?0:0.5):0.5}
console.log("\nDUEL MATRIX: row suit's win share vs column suit, at growth clock 0 / 250 / 500 s (30 duels each, 1v1, open ground, bots)");
clocks.forEach(c=>{console.log("\nclock",c,"s    "+facs.map(f=>f.slice(0,5).padStart(6)).join(""));
  facs.forEach(a=>{const row=facs.map(b=>{if(a==b)return "    - ";let w=0;for(let k=0;k<NDU;k++)w+=duel(a,b,c,9000+k+(c/10));const sh=w/NDU;M[`${a}|${b}|${c}`]=sh;return (Math.round(sh*100)+"%").padStart(6)});console.log(a.slice(0,9).padEnd(10)+row.join(""))})});
facs.forEach(a=>facs.forEach(b=>{if(a>=b)return;const s=clocks.map(c=>M[`${a}|${b}|${c}`]);if(s.every(x=>x<0.2))fails.push(`${a} loses to ${b} at every clock (${s.map(x=>Math.round(x*100)+"%").join("/")})`);if(s.every(x=>x>0.8))fails.push(`${a} beats ${b} at every clock (${s.map(x=>Math.round(x*100)+"%").join("/")})`)}));
console.log(fails.length?"\nFAILING:\n"+fails.join("\n"):"\nPASS");
