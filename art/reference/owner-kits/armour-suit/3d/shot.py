"""Headless check: console errors, 4 screenshots, GLB export. Prints PASS/FAIL."""
import asyncio, os, sys
from playwright.async_api import async_playwright
async def main():
    errs=[]
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
        pg=await b.new_page(viewport={'width':540,'height':760})
        pg.on('console',lambda m: errs.append(m.text) if m.type=='error' else None)
        pg.on('pageerror',lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.abspath('techno_plate_knight.html'))
        await pg.wait_for_timeout(2500)
        for n,az in (('front',0),('threeq',0.7),('side',1.5708),('back',3.1416)):
            await pg.evaluate(f'window.__view({az})'); await pg.wait_for_timeout(300)
            await pg.screenshot(path=f'shot_{n}.png')
        tris=await pg.evaluate('window.__tris')
        async with pg.expect_download(timeout=20000) as d:
            await pg.click('#export')
        dl=await d.value; await dl.save_as('techno_plate_knight.glb')
        await b.close()
    size=os.path.getsize('techno_plate_knight.glb')
    ok=not errs and size>10000
    print('PASS' if ok else 'FAIL', f'tris={int(tris)} glb={size//1024}KB')
    for e in errs[:8]: print('  ',e[:200])
asyncio.run(main())
