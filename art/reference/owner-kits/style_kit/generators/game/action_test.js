// Headless: for each suit, force attack/dash/skill timers up and check the matching animation starts. Run: node action_test.js
const path=require("path");let pw;for(const t of ["playwright","/opt/npm-tools/node_modules/playwright"]){try{pw=require(t);break}catch(e){}}
const file="file://"+path.resolve(__dirname,"suit_game.html")+"?test";
const WANT={tianbing:["attack"],wushi:["attack","skill"],tianlong:["skill","dash"],jianxian:["dash"],mingjiang:["attack","skill","dash"],mojiang:["skill"],gushi:["dash"],yuanmo:["attack"]};
(async()=>{const br=await pw.chromium.launch();const fails=[];
for(const [w,h,tag] of [[1366,768,"96"],[390,844,"64"]]){const pg=await (await br.newContext({viewport:{width:w,height:h}})).newPage();pg.on("pageerror",e=>fails.push(tag+" pageerror "+e.message));
 await pg.goto(file);await pg.waitForTimeout(600);
 for(const f of Object.keys(WANT)){await pg.evaluate(f=>window.__game.start(f),f);await pg.waitForTimeout(500);
  for(const act of ["attack","dash","skill"]){
   const want=WANT[f].includes(act)?(f=="wushi"&&act=="skill"?"attack":act):null;
   const got=await pg.evaluate(async act=>{const G=window.__game.state();const p=G.suits.find(s=>s.isPlayer);const fld={attack:"atkT",dash:"dashT",skill:"sklT"}[act];
     for(let i=0;i<40&&window.__game.anim(p.id);i++)await new Promise(r=>setTimeout(r,60));p[fld]=-1;await new Promise(r=>setTimeout(r,120));p[fld]=1;await new Promise(r=>setTimeout(r,120));return window.__game.anim(p.id)||null},act);
   if(got!==want)fails.push(`${tag} ${f}/${act}: want ${want} got ${got}`);}}
 const def=await pg.evaluate(async()=>{const G=window.__game.state();const s=G.suits.find(x=>!x.isPlayer&&x.alive);s.hp=-1;s.alive=false;await new Promise(r=>setTimeout(r,150));return window.__game.anim(s.id)});
 if(def!=="defeat")fails.push(tag+" defeat: got "+def);
 await pg.close()}
console.log(fails.length?"FAIL\n"+fails.join("\n"):"PASS");await br.close()})();
