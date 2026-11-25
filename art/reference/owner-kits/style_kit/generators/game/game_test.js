// Pass/fail runner: node game_test.js  (4 sizes, tutorial, match, keys, dupes, blank check, restart x2)
const path=require("path");let pw;for(const t of ["playwright","/opt/npm-tools/node_modules/playwright"]){try{pw=require(t);break}catch(e){}}
const file="file://"+path.resolve(__dirname,"suit_game.html")+"?test";
const SIZES=[["phone-portrait",390,844,2,true],["phone-landscape",844,390,2,true],["laptop",1366,768,1,false],["ultrawide",2560,1080,1,false]];
(async()=>{const br=await pw.chromium.launch();const fails=[];
for(const [n,w,h,dsf,touch] of SIZES){const cx=await br.newContext({viewport:{width:w,height:h},deviceScaleFactor:dsf,isMobile:touch,hasTouch:touch});const pg=await cx.newPage();const bad=[];
 pg.on("pageerror",e=>bad.push("pageerror "+e.message));pg.on("console",m=>{if(m.type()=="error")bad.push("console "+m.text())});
 await pg.goto(file);await pg.waitForTimeout(300);
 const colours=async()=>{const b=await pg.screenshot();return pg.evaluate(async b64=>{const i=new Image();i.src="data:image/png;base64,"+b64;await i.decode();const c=document.createElement("canvas");c.width=c.height=48;const g=c.getContext("2d");g.drawImage(i,0,0,48,48);const d=g.getImageData(0,0,48,48).data,s=new Set();for(let k=0;k<d.length;k+=4)s.add((d[k]>>4)+","+(d[k+1]>>4)+","+(d[k+2]>>4));return s.size},b.toString("base64"))};
 if(await colours()<3)bad.push("blank at menu");
 if((await pg.evaluate(()=>window.__game.keyDupes())).length)bad.push("duplicate key map");
 if(await pg.evaluate(()=>window.__game.mode())!="title")bad.push("not at title");
 await pg.click("#startBtn");await pg.waitForTimeout(100);if(await pg.evaluate(()=>window.__game.mode())!="wipe")bad.push("no storm wipe after Start");await pg.waitForTimeout(1700);if(await pg.evaluate(()=>window.__game.mode())!="arrival")bad.push("no arrival");
 await pg.waitForTimeout(3800);if(await colours()<3)bad.push("blank at arrival");
 if(!(await pg.isDisabled("#arrBtn")))bad.push("arrival Continue not locked on first visit");if(!(await pg.isHidden("#tutSkip"))&&false)bad.push("");
 await pg.evaluate(()=>window.__game.arrUnlock());await pg.waitForTimeout(80);if(await pg.isDisabled("#arrBtn"))bad.push("arrival did not unlock after all scenes");
 await pg.click("#arrBtn");await pg.waitForTimeout(100);if(!(await pg.isHidden("#tutSkip")))bad.push("tutorial skip shown on first run");if(await pg.evaluate(()=>window.__game.mode())!="tut")bad.push("tutorial did not follow arrival");
 for(let k=0;k<7;k++){await pg.click("#tutNext");await pg.waitForTimeout(30)}
 if(await pg.evaluate(()=>window.__game.mode())!="menu")bad.push("tutorial did not lead to menu");
 const names=await pg.evaluate(()=>[...document.querySelectorAll(".btn--pick .btn__text")].map(b=>b.firstChild.textContent));if(names.some(x=>/[\u4e00-\u9fff]{2}/.test(x)))bad.push("two-character Chinese name in menu: "+names.join("|"));
 await pg.click(".btn--pick");await pg.waitForTimeout(100);
 {const sc=await pg.evaluate(()=>({shown:!document.querySelector("#school").classList.contains("is-hidden"),rules:document.querySelectorAll("#schoolRules li").length,skill:document.querySelector("#schoolSkill").textContent,nan:/NaN|undefined/.test(document.querySelector("#school").textContent)}));
  if(!sc.shown)bad.push("school card did not open from the pick list");if(!sc.rules||!sc.skill)bad.push("school card empty");if(sc.nan)bad.push("school card shows NaN/undefined");}
 await pg.click("#schoolGo");await pg.waitForTimeout(100);
 if(await pg.evaluate(()=>window.__game.mode())!="play")bad.push("pick did not start play");
 for(const k of ["ArrowRight","KeyD","KeyJ","KeyK","KeyL","ArrowDown","KeyS"]){await pg.keyboard.down(k);await pg.waitForTimeout(150);await pg.keyboard.up(k)}
 if(touch){for(const a of ["right","attack","dash","skill"]){const b=pg.locator(`[data-act=${a}]`);const bx=await b.boundingBox();if(!bx)bad.push("touch button hidden "+a);else{await pg.touchscreen.tap(bx.x+bx.width/2,bx.y+bx.height/2)}}}
 else if(await pg.locator("#pad").isVisible())bad.push("touch pad shown on desktop");
 await pg.waitForTimeout(500);if(await colours()<3)bad.push("blank in play");
 // controls inside viewport
 const off=await pg.evaluate(()=>[...document.querySelectorAll("#pad .btn,#act .btn,#top .btn")].filter(b=>b.offsetParent).map(b=>b.getBoundingClientRect()).filter(r=>r.left<0||r.top<0||r.right>innerWidth||r.bottom>innerHeight).length);if(off)bad.push(off+" controls off-screen");
 await pg.keyboard.press("KeyP");await pg.waitForTimeout(100);if(await pg.evaluate(()=>window.__game.mode())!="pause")bad.push("P did not pause");
 await pg.keyboard.press("Escape");await pg.waitForTimeout(100);if(await pg.evaluate(()=>window.__game.mode())!="play")bad.push("Esc did not resume");
 if(await pg.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1))bad.push("hscroll");
 for(let r=0;r<2;r++){await pg.evaluate(()=>window.__game.newRun());await pg.waitForTimeout(200)}
 const sp=await pg.evaluate(()=>window.__game.sprites());if(sp.loaded!=sp.expected)bad.push("sprites loaded "+sp.loaded+"/"+sp.expected);const want=(w*dsf>=11*96&&h*dsf>=11*96)?96:64;if(!sp.scene)bad.push("scene sheets not loaded at "+sp.tile);if(!sp.tiles)bad.push("tile sheet not loaded");if(sp.props!=3)bad.push("props not loaded "+sp.props);if(sp.anims!=10)bad.push("anims not loaded "+sp.anims);if(sp.tile!=want)bad.push("tile "+sp.tile+" want "+want);
 await pg.screenshot({path:`/tmp/game_${n}.png`});
 console.log((bad.length?"FAIL ":"PASS ")+n,bad.join("; "));if(bad.length)fails.push(n);await cx.close()}
await br.close();console.log(fails.length?"RESULT FAIL":"RESULT PASS");process.exit(fails.length?1:0)})();
