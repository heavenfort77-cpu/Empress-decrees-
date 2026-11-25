// Headless: sound starts after a gesture, every SFX plays without error, mute toggles, credits open and close. Run: node audio_test.js
const path=require("path");let pw;for(const t of ["playwright","/opt/npm-tools/node_modules/playwright"]){try{pw=require(t);break}catch(e){}}
const file="file://"+path.resolve(__dirname,"suit_game.html")+"?test";
(async()=>{const br=await pw.chromium.launch({args:["--autoplay-policy=no-user-gesture-required"]});const fails=[];
const pg=await (await br.newContext({viewport:{width:1366,height:768}})).newPage();pg.on("pageerror",e=>fails.push("pageerror "+e.message));
await pg.goto(file);await pg.waitForTimeout(600);
if(await pg.evaluate(()=>window.__game.audio())!==null)fails.push("audio started before any gesture");
await pg.click("#credBtn");if(await pg.isHidden("#credits"))fails.push("credits did not open");
if(!(await pg.textContent("#credText")).includes("original"))fails.push("credits text empty");
await pg.click("#credBack");if(await pg.isHidden("#title"))fails.push("credits back did not return to title");
if((await pg.evaluate(()=>window.__game.audio()))!=="running")fails.push("audio not running after tap: "+await pg.evaluate(()=>window.__game.audio()));
await pg.evaluate(()=>window.__game.start("mingjiang"));await pg.waitForTimeout(400);
const r=await pg.evaluate(async()=>{const G=window.__game.state();const id=G.suits[0].id;const bad=[];for(const n of ["attack","hit","dash","skill","death","storm","win","lose"]){try{window.__game.sfx(n,id);await new Promise(r=>setTimeout(r,80))}catch(e){bad.push(n+": "+e.message)}}return bad});
fails.push(...r);
await pg.keyboard.press("m");await pg.waitForTimeout(150);if(!(await pg.evaluate(()=>window.__game.muted())))fails.push("M did not mute");
await pg.keyboard.press("m");await pg.waitForTimeout(150);if(await pg.evaluate(()=>window.__game.muted()))fails.push("M did not unmute");
await pg.keyboard.press("p");await pg.waitForTimeout(150);await pg.click("#pCred");if(await pg.isHidden("#credits"))fails.push("pause credits did not open");
await pg.click("#credBack");if(await pg.isHidden("#pause"))fails.push("credits back did not return to pause");
await pg.click("#soundBtn");if((await pg.textContent("#soundBtn"))!=="Sound: off")fails.push("sound button label");
console.log(fails.length?"FAIL\n"+fails.join("\n"):"PASS");await br.close()})();
