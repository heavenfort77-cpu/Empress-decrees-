#!/usr/bin/env python3
"""Queue txt2img prompts on a local ComfyUI server (CPU) and save the images. Usage: python gen.py PROMPTS.json JOB_INDEX OUTDIR
Builds the standard API graph: checkpoint -> two text encodes -> empty latent -> KSampler -> VAE decode -> SaveImage."""
import json, sys, time, urllib.request, urllib.parse, os

CFG = json.load(open(sys.argv[1])); JOB = CFG['jobs'][int(sys.argv[2])]; OUT = sys.argv[3]
URL = 'http://127.0.0.1:8188'
os.makedirs(OUT, exist_ok=True)

def get(path):
    with urllib.request.urlopen(URL + path, timeout=60) as r: return r.read()

for _ in range(300):  # wait for the server (up to 10 min)
    try: get('/system_stats'); break
    except Exception: time.sleep(2)

log = []
for seed in JOB['seeds']:
    pos = CFG['positive'].replace('{view}', JOB['view'])
    g = {
        '1': {'class_type': 'CheckpointLoaderSimple', 'inputs': {'ckpt_name': CFG['checkpoint']}},
        '2': {'class_type': 'CLIPTextEncode', 'inputs': {'text': pos, 'clip': ['1', 1]}},
        '3': {'class_type': 'CLIPTextEncode', 'inputs': {'text': CFG['negative'], 'clip': ['1', 1]}},
        '4': {'class_type': 'EmptyLatentImage', 'inputs': {'width': CFG['width'], 'height': CFG['height'], 'batch_size': 1}},
        '5': {'class_type': 'KSampler', 'inputs': {'model': ['8', 0] if CFG.get('lora') else ['1', 0], 'positive': ['2', 0], 'negative': ['3', 0], 'latent_image': ['4', 0], 'seed': seed,
              'steps': CFG['steps'], 'cfg': CFG['cfg'], 'sampler_name': CFG['sampler'], 'scheduler': CFG['scheduler'], 'denoise': 1.0}},
        '6': {'class_type': 'VAEDecode', 'inputs': {'samples': ['5', 0], 'vae': ['1', 2]}},
        '7': {'class_type': 'SaveImage', 'inputs': {'images': ['6', 0], 'filename_prefix': f'beast_{seed}'}},
    }
    if CFG.get('lora'):
        g['8'] = {'class_type': 'LoraLoaderModelOnly', 'inputs': {'model': ['1', 0], 'lora_name': CFG['lora'], 'strength_model': 1.0}}
    t0 = time.time()
    req = urllib.request.Request(URL + '/prompt', data=json.dumps({'prompt': g}).encode(), headers={'Content-Type': 'application/json'})
    pid = json.loads(urllib.request.urlopen(req, timeout=60).read())['prompt_id']
    while True:
        h = json.loads(get('/history/' + pid))
        if pid in h and h[pid].get('outputs'): break
        if pid in h and h[pid].get('status', {}).get('status_str') == 'error':
            print('ERROR', seed, json.dumps(h[pid]['status'])[:400]); sys.exit(1)
        time.sleep(3)
    for img in h[pid]['outputs']['7']['images']:
        q = urllib.parse.urlencode({'filename': img['filename'], 'subfolder': img['subfolder'], 'type': img['type']})
        open(os.path.join(OUT, f"beast_{seed}.png"), 'wb').write(get('/view?' + q))
    line = f'seed {seed} view "{JOB["view"]}" {time.time() - t0:.0f} s'
    print(line); log.append(line)
open(os.path.join(OUT, 'gen.log'), 'w').write('\n'.join(log) + '\n')
