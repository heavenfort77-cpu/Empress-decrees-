#!/usr/bin/env python3
"""Cause probe (SUITS fa, 25 Nov): time ONE SDXL UNet forward at the job's size in one dtype, in its own process, so the oneDNN ISA cap
(env ONEDNN_MAX_CPU_ISA, set by the caller before torch starts) can imitate a runner CPU without native bf16 (avx512_bf16 / AMX).
Hypothesis under test: the stalled jobs (runs 45538983377, 45542072933; 286 s for 1 step in run 45545052794) ran bf16 on such a CPU.
Uses the files gen_xl.py already downloaded (ckpt/sdxl). Usage: python unet_step.py PROMPTS.json DTYPE(bfloat16|float32)"""
import json, os, sys, time
import torch
from diffusers import UNet2DConditionModel
CFG = json.load(open(sys.argv[1])); DT = getattr(torch, sys.argv[2]); torch.set_num_threads(os.cpu_count() or 4)
W, H = CFG['width'], CFG['height']
u = UNet2DConditionModel.from_pretrained(os.path.abspath('ckpt/sdxl'), subfolder='unet', variant='fp16', torch_dtype=DT, use_safetensors=True).eval()
x = torch.randn(1, 4, H // 8, W // 8, dtype=DT); pe = torch.randn(1, 77, 2048, dtype=DT)
add = {'text_embeds': torch.randn(1, 1280, dtype=DT), 'time_ids': torch.tensor([[H, W, 0, 0, H, W]], dtype=DT)}
with torch.no_grad():
    t = time.time(); u(x, torch.tensor([999]), encoder_hidden_states=pe, added_cond_kwargs=add); dt = time.time() - t
print(f"UNET STEP isa cap {os.environ.get('ONEDNN_MAX_CPU_ISA', 'none')} dtype {sys.argv[2]} {W}x{H}: {dt:.0f} s, threads {torch.get_num_threads()}", flush=True)
