// Headless pacing and balance check for suit_proto.html. Run: node proto_test.js [matches]
// Reports only pass/fail and the failing lines: match length (target >= 600 s for most), winner spread, early finishes, per-faction win rate.
const fs=require("fs");const src=fs.readFileSync(__dirname+"/suit_proto.html","utf8");
const code=src.slice(src.indexOf("//@@LOGIC"),src.indexOf("//@@END"));
const m={exports:{}};new Function("module",code)(m);const {createGame,CONFIG}=m.exports;
const n=+(process.argv[2]||20);const wins={},lens=[],early=[],phaseDeaths=[];
for(let i=0;i<n;i++){const G=createGame({seed:1000+i,suits:+(process.env.SUITS||CONFIG.SUITS)});let steps=0;while(!G.over&&steps<70000){G.step(0.1);steps++}
  lens.push(G.t|0);const w=G.winner?G.winner.f:"none";wins[w]=(wins[w]||0)+1;if(G.t<600)early.push(`seed ${1000+i}: ended at ${G.t|0} s, winner ${w}`);
  G.log.forEach(([t,f,by])=>phaseDeaths.push([t,by]))}
const avg=lens.reduce((a,b)=>a+b,0)/n;const fails=[];
if(avg<600)fails.push(`average match ${avg.toFixed(0)} s < 600`);
if(early.length>n*0.3)fails.push(`${early.length}/${n} matches ended before 600 s`);
const stormKills=phaseDeaths.filter(d=>d[1]=="storm").length,total=phaseDeaths.length;
if(total&&stormKills/total>0.5)fails.push(`storm did ${stormKills}/${total} kills (bots too passive)`);
const spread=Object.entries(wins).sort((a,b)=>b[1]-a[1]);const top=spread[0];
if(top&&top[1]>n*0.5&&top[0]!="none")fails.push(`${top[0]} won ${top[1]}/${n}`);
console.log("matches",n,"avg length",avg.toFixed(0),"s  min",Math.min(...lens),"max",Math.max(...lens));
console.log("winners",JSON.stringify(wins));console.log("kills by storm",stormKills,"of",total);
const byT={};phaseDeaths.forEach(([t])=>{const b=Math.floor(t/100)*100;byT[b]=(byT[b]||0)+1});console.log("deaths per 100 s",JSON.stringify(byT));
console.log(fails.length?"FAILING:\n"+fails.join("\n")+"\n"+early.slice(0,5).join("\n"):"PASS");
