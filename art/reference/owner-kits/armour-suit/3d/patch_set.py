s=open('main.js').read()
def cut(a,b):
    i=s.index(a); j=s.index(b,i); return i,j
A="// ---- body under the plates (keeps every joint closed) ----"
H="// ---- helmet ----"
P="// ---- power pack: ribbed reactor drum, exhaust stacks, cables ----"
AR="// ---- arms ----"
L="// ---- legs ----"
G="// ---- greatsword, planted point down ----"
D="// ---- display base ----"
pre=s[:s.index(A)]
torso=s[s.index(A):s.index(H)].replace("M.cloth, 0, 0.72","clothMat, 0, 0.72")
helmet=s[s.index(H):s.index(P)]
pack=s[s.index(P):s.index(AR)]
arms=s[s.index(AR):s.index(L)]
legs=s[s.index(L):s.index(G)]
ls="for (const s of [-1, 1]) {\n  const lx = s * 0.165;\n"
assert ls in legs
legbody=legs[legs.index(ls)+len(ls):legs.rindex("}")]
sword=s[s.index(G):s.index(D)]
tail=s[s.index(D):]
a="const knight = new THREE.Group(); knight.name = 'TechnoPlateKnight';\nscene.add(knight);"
assert a in pre
pre=pre.replace(a,"let knight = new THREE.Group();   // the group currently being built; every helper adds to it\nM.violet = M.cloth.clone(); M.violet.color.set(0x3b2f63); M.violet.name = 'cloth_violet';\nM.red = M.cloth.clone(); M.red.color.set(0x6b1f24); M.red.name = 'cloth_red';")
generic=open('generic.js').read()
builders=open('builders.js').read()
i=tail.index("document.getElementById('export').onclick")
tail=tail[:i]+open('tail.js').read()
out=(pre+"function torsoParts(clothMat = M.cloth) {\n"+torso+"}\nfunction packParts() {\n"+pack+"}\nfunction legParts(s, lx) {\n"+legbody+"}\n"+generic
     +"function buildKnight() {\ntorsoParts();\n"+helmet+"packParts();\n"+arms+"for (const s of [-1, 1]) legParts(s, s * 0.165);\n\n"+sword+"}\n"+builders+tail)
open('main.js','w').write(out)
print('ok',len(out))
