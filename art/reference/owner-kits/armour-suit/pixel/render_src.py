"""Capture a character from the 3D page on a magenta backdrop, for pixel conversion.
Run from the 3d folder: python3 ../pixel/render_src.py knight 0"""
import asyncio, os, sys
from playwright.async_api import async_playwright
name=sys.argv[1]; az=float(sys.argv[2]) if len(sys.argv)>2 else 0.0
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
        pg=await b.new_page(viewport={'width':900,'height':1200})
        await pg.goto('file://'+os.path.abspath('techno_plate_set.html')); await pg.wait_for_timeout(2500)
        await pg.evaluate(f'window.__show("{name}")'); await pg.wait_for_timeout(900)
        await pg.evaluate('window.__sprite(true)'); await pg.evaluate(f'window.__view({az})'); await pg.wait_for_timeout(500)
        await pg.screenshot(path=f'../pixel/src_{name}.png')
        await pg.evaluate('window.__sprite(false)'); await pg.evaluate(f'window.__view({az})'); await pg.wait_for_timeout(300)
        await pg.screenshot(path=f'../pixel/ref_{name}.png')
        await b.close()
asyncio.run(main())
