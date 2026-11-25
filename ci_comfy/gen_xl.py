#!/usr/bin/env python3
"""SUITS fa concept references: SDXL base 1.0 + SDXL-Lightning 8-step LoRA on a CPU runner (diffusers, fp32), txt2img per seed plus img2img
from the owner's kit masks. Reference only, never shipped. Usage: python gen_xl.py PROMPTS.json JOB OUTDIR [--probe-only]
Memory plan (16 GB runner): bfloat16 weights (UNet about 5 GB instead of 10 GB fp32); text encoders load first, encode the job's prompt, are
freed; then UNet + VAE + fused LoRA run the images with attention slicing and VAE slicing + tiling. Peak RSS is printed after every image.
Stage 1 (part of the job's PREFLIGHT): download, encode, one 1-step 768 image (prints PROBE PASS with its time)."""
import json, os, sys, time, gc, resource
import torch
from huggingface_hub import snapshot_download, hf_hub_download
from PIL import Image

CFG = json.load(open(sys.argv[1])); J = int(sys.argv[2]); JOB = CFG['jobs'][J]; OUT = sys.argv[3]; PROBE_ONLY = '--probe-only' in sys.argv
CK = os.path.abspath('ckpt'); os.makedirs(OUT, exist_ok=True); torch.set_num_threads(os.cpu_count() or 4)
t0 = time.time()
base = snapshot_download(CFG['base'], local_dir=os.path.join(CK, 'sdxl'), allow_patterns=[
    'model_index.json', 'scheduler/*', 'tokenizer/*', 'tokenizer_2/*', 'text_encoder/config.json', 'text_encoder/model.fp16.safetensors',
    'text_encoder_2/config.json', 'text_encoder_2/model.fp16.safetensors', 'unet/config.json', 'unet/diffusion_pytorch_model.fp16.safetensors',
    'vae/config.json', 'vae/diffusion_pytorch_model.fp16.safetensors'])
lora = hf_hub_download(CFG['lora_repo'], CFG['lora_file'], local_dir=os.path.join(CK, 'lightning'))
print(f'models ready {time.time() - t0:.0f} s', flush=True)

from diffusers import StableDiffusionXLPipeline, StableDiffusionXLImg2ImgPipeline, EulerDiscreteScheduler
prompt = CFG['positive'].replace('{view}', JOB['view'])
DT = torch.bfloat16
rss = lambda: f'peak RSS {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1048576:.2f} GB'
te = StableDiffusionXLPipeline.from_pretrained(base, unet=None, vae=None, variant='fp16', torch_dtype=DT, use_safetensors=True)
with torch.no_grad():
    pe, _, ppe, _ = te.encode_prompt(prompt, device='cpu', num_images_per_prompt=1, do_classifier_free_guidance=False)
del te; gc.collect()
print(f'prompt encoded {time.time() - t0:.0f} s, {rss()}', flush=True)
pipe = StableDiffusionXLPipeline.from_pretrained(base, text_encoder=None, text_encoder_2=None, tokenizer=None, tokenizer_2=None,
                                                 variant='fp16', torch_dtype=DT, use_safetensors=True)
pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config, timestep_spacing='trailing')
pipe.load_lora_weights(lora); pipe.fuse_lora(); pipe.set_progress_bar_config(disable=True)
pipe.enable_attention_slicing(); pipe.vae.enable_slicing(); pipe.vae.enable_tiling()
W, H = JOB.get('width', CFG['width']), JOB.get('height', CFG['height'])
def run(name, steps, seed, init=None, strength=1.0):
    t = time.time(); g = torch.Generator('cpu').manual_seed(seed)
    kw = dict(prompt_embeds=pe, pooled_prompt_embeds=ppe, num_inference_steps=steps, guidance_scale=CFG['guidance'], generator=g)
    if init is None: im = pipe(width=W, height=H, **kw).images[0]
    else: im = i2i(image=Image.open(init).convert('RGB').resize((W, H)), strength=strength, **kw).images[0]
    im.save(os.path.join(OUT, name)); dt = time.time() - t
    line = f'{name} seed {seed} steps {steps}' + (f' img2img {os.path.basename(init)} strength {strength}' if init else '') + f' {dt:.0f} s, {rss()}'
    print(line, flush=True); return line
log = [run('probe_1step.png', 1, 1)]
print(f'PROBE PASS 1-step {W}x{H} image rendered, total {time.time() - t0:.0f} s, {rss()}', flush=True)
if PROBE_ONLY: sys.exit(0)
i2i = StableDiffusionXLImg2ImgPipeline(**pipe.components)
for s in JOB['seeds']: log.append(run(f'fa_{s}.png', CFG['steps'], s))
for e in JOB.get('img2img', []): log.append(run(f'fa_{e["seed"]}_i2i_{os.path.basename(e["init"])[:-4]}.png', CFG['steps'], e['seed'], e['init'], e['strength']))
open(os.path.join(OUT, 'gen.log'), 'w').write(f'prompt: {prompt}\n' + '\n'.join(log) + '\n')
print('GEN DONE', len(log) - 1, 'images')
