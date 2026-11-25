# Builds game/suit_game.html: splices the sandbox-tested LOGIC block (from proto) into shell_template.html
import re
p=open("../proto/suit_proto.html",encoding="utf8").read()
logic=p[p.index("//@@LOGIC")+len("//@@LOGIC"):p.index("//@@END")]
t=open("shell_template.html",encoding="utf8").read()
assert t.count("/*LOGIC_HERE*/")==1
sp=open("sprites_block.js",encoding="utf8").read()+open("anims_block.js",encoding="utf8").read();assert t.count("/*SPRITES_HERE*/")==1
open("suit_game.html","w",encoding="utf8").write(t.replace("/*LOGIC_HERE*/",logic).replace("/*SPRITES_HERE*/",sp))
print("built")
