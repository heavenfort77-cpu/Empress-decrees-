"""Capture the knight in the walking pose from the side, front and back: plain material colours, and the full render.
Run from the 3d folder: python3 ../pixel/match/capture_views.py"""
import asyncio, json, os
from playwright.async_api import async_playwright
VIEWS = [('side', -1.5708), ('front', 0.0), ('back', 3.1416)]; POSE = ('walk', 1); PXM = 27
async def main():
    errs = []; info = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        pg = await b.new_page(viewport={'width': 900, 'height': 1200})
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://' + os.path.abspath('techno_plate_set.html')); await pg.wait_for_timeout(2500)
        await pg.evaluate('window.__show("knight")'); await pg.wait_for_timeout(600)
        await pg.evaluate(f'window.__pxm = {PXM}'); await pg.evaluate(f'window.__pose("{POSE[0]}", {POSE[1]})')
        for name, az in VIEWS:
            await pg.evaluate(f'window.__lights({az})'); await pg.evaluate('window.__sprite("flat")'); await pg.evaluate(f'window.__orthoView({az})'); await pg.wait_for_timeout(300)
            await pg.screenshot(path=f'../pixel/match/cap/{name}_flat.png'); info[name] = await pg.evaluate('window.__proj()')
            await pg.evaluate('window.__sprite(false)'); await pg.evaluate(f'window.__orthoView({az})'); await pg.wait_for_timeout(300)
            await pg.screenshot(path=f'../pixel/match/cap/{name}_ref.png')
        await b.close()
    json.dump(info, open('../pixel/match/cap/proj.json', 'w')); print('errors:', errs[:3], info['side'])
asyncio.run(main())
