"""Capture every animation frame of the knight from the 3D page: a flat matt capture (materials) and the full render (light).
Run from the 3d folder: python3 ../pixel/anim/capture.py"""
import asyncio, json, os
from playwright.async_api import async_playwright
ANIMS = [('idle', 4, 0.0), ('walk_left', 6, 1.5708), ('walk_right', 6, -1.5708), ('battle', 1, 0.0)]   # name, frames, camera angle
async def main():
    errs = []; info = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        pg = await b.new_page(viewport={'width': 900, 'height': 1200})
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://' + os.path.abspath('techno_plate_set.html')); await pg.wait_for_timeout(2500)
        await pg.evaluate('window.__show("knight")'); await pg.wait_for_timeout(600)
        await pg.evaluate('window.__pxm = 38')
        for name, n, az in ANIMS:
            for i in range(n):
                await pg.evaluate(f'window.__pose("{name.split("_")[0]}", {i})')
                await pg.evaluate(f'window.__lights({az})'); await pg.evaluate('window.__sprite("flat")'); await pg.evaluate(f'window.__orthoView({az})'); await pg.wait_for_timeout(250)
                await pg.screenshot(path=f'../pixel/anim/cap/{name}_{i}_flat.png'); info[f'{name}_{i}'] = await pg.evaluate('window.__proj()')
                await pg.evaluate('window.__sprite(false)'); await pg.evaluate(f'window.__orthoView({az})'); await pg.wait_for_timeout(250)
                await pg.screenshot(path=f'../pixel/anim/cap/{name}_{i}_ref.png')
        await b.close()
    json.dump(info, open('../pixel/anim/cap/proj.json', 'w')); print('errors:', errs[:5]); print(len(info), 'frames', info['idle_0'])
asyncio.run(main())
