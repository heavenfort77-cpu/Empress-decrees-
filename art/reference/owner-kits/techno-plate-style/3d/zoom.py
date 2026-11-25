import asyncio, os, sys
from playwright.async_api import async_playwright
from PIL import Image
async def main():
    errs=[]
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
        pg=await b.new_page(viewport={'width':540,'height':760},device_scale_factor=2)
        pg.on('console',lambda m: errs.append(m.text) if m.type=='error' else None); pg.on('pageerror',lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.abspath('techno_plate_set.html')); await pg.wait_for_timeout(2500)
        for n,views in (('rogue',(0,0.7,1.5708)),('beast',(0,0.75,1.5708))):
            await pg.evaluate(f'window.__show("{n}")'); await pg.wait_for_timeout(800)
            for i,az in enumerate(views):
                await pg.evaluate(f'window.__view({az})'); await pg.wait_for_timeout(300)
                await pg.screenshot(path=f'/tmp/z_{n}_{i}.png')
        await b.close()
    print('errors:',errs[:5])
asyncio.run(main())
r=[Image.open(f'/tmp/z_rogue_{i}.png').crop((370,110,710,450)) for i in range(3)]
c=Image.new('RGB',(1020,340))
for i,im in enumerate(r): c.paste(im,(i*340,0))
c.save('rogue_head_zoom.png')
b=[Image.open(f'/tmp/z_beast_{i}.png').crop((0,300,1080,1000)).resize((540,350),Image.LANCZOS) for i in range(3)]
c=Image.new('RGB',(1620,350))
for i,im in enumerate(b): c.paste(im,(i*540,0))
c.save('beast_zoom.png')
