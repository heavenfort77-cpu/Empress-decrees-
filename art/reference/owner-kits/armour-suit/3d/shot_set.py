"""Headless check for the four-character page: console errors, 4 views each, GLB export each. Prints PASS/FAIL."""
import asyncio, os
from playwright.async_api import async_playwright
from PIL import Image
NAMES=['knight','mage','rogue','beast']
async def main():
    errs=[]; info={}
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
        pg=await b.new_page(viewport={'width':540,'height':760})
        pg.on('console',lambda m: errs.append(m.text) if m.type=='error' else None)
        pg.on('pageerror',lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.abspath('techno_plate_set.html')); await pg.wait_for_timeout(2500)
        for n in NAMES:
            await pg.evaluate(f'window.__show("{n}")'); await pg.wait_for_timeout(700)
            for v,az in (('front',0),('threeq',0.7),('side',1.5708),('back',3.1416)):
                await pg.evaluate(f'window.__view({az})'); await pg.wait_for_timeout(250)
                await pg.screenshot(path=f'shot_{n}_{v}.png')
            tris=await pg.evaluate('window.__tris')
            async with pg.expect_download(timeout=30000) as d:
                await pg.click('#export')
            dl=await d.value; await dl.save_as(f'techno_plate_{n}.glb')
            info[n]=(tris, os.path.getsize(f'techno_plate_{n}.glb')//1024)
        await b.close()
    ok=not errs and all(v[1]>10 for v in info.values()) and len(info)==4
    print('PASS' if ok else 'FAIL', ' '.join(f'{n}: {t} tris, {k} KB' for n,(t,k) in info.items()))
    for e in errs[:8]: print('  ',e[:300])
    for n in NAMES:
        if not os.path.exists(f'shot_{n}_back.png'): continue
        ims=[Image.open(f'shot_{n}_{v}.png').crop((0,70,540,700)) for v in ('front','threeq','side','back')]
        c=Image.new('RGB',(1080,1260))
        for i,im in enumerate(ims): c.paste(im,((i%2)*540,(i//2)*630))
        c.save(f'sheet_{n}.png')
asyncio.run(main())
