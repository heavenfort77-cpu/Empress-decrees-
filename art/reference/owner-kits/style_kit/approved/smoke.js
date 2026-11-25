// browser smoke test: load the page, pick a suit, play 6 s with keys, report errors only
const {chromium}=require("playwright");(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:390,height:844}});const errs=[];p.on("pageerror",e=>errs.push(e.message));p.on("console",m=>{if(m.type()==="error")errs.push(m.text())});
await p.goto("file://"+__dirname+"/suit_proto.html");await p.click("#picks button:nth-child(1)");for(let i=0;i<30;i++){await p.keyboard.down("ArrowRight");await p.waitForTimeout(100);await p.keyboard.up("ArrowRight");await p.keyboard.press("j")}
await p.keyboard.press("k");await p.keyboard.press("l");await p.waitForTimeout(1500);const hud=await p.textContent("#hud");await p.screenshot({path:"smoke.png"});await b.close();
console.log(errs.length?"FAILING:\n"+errs.join("\n"):"PASS "+hud.split("\n")[0])})();
