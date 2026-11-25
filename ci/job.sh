#!/bin/bash
# FACES concept job (branch ci-comfy-faces): SDXL base 1.0 + SDXL-Lightning 8-step LoRA (diffusers, CPU) renders one prompts.json entry:
# txt2img per seed plus img2img from the owner's kit masks. Reference only. Usage: bash ci/job.sh JOB_INDEX OUTDIR
# PREFLIGHT (lead 25 Nov): stage A tools, prompts, scripts, init images, output folder; stage B installs, downloads the models and renders
# one 1-step image (PROBE PASS). ci/PREFLIGHT_ONLY stops after stage B.
set -u
J=$1; O=$2
die() { echo "PREFLIGHT FAIL $1"; exit 1; }
echo "== preflight A $(date +%H:%M:%S)"
for t in python curl git; do command -v $t >/dev/null || die "tool $t"; done
python -c "
import json,sys,os; c=json.load(open('ci_comfy/prompts.json')); j=c['jobs'][int(sys.argv[1])]
assert j['seeds'] and j['view']; [c[k] for k in ('base','lora_repo','lora_file','positive','width','height','steps','guidance')]
for e in j.get('img2img',[]): assert os.path.getsize(e['init'])>0 and 0<e['strength']<1, e" "$J" || die "prompts.json job $J"
python -m py_compile ci_comfy/gen_xl.py || die "gen_xl.py compiles"
mkdir -p "$O" || die "mkdir $O"
echo "PREFLIGHT A PASS"
echo "== preflight B (install, models, 1-step probe) $(date +%H:%M:%S)"
python -m pip install --quiet torch --index-url https://download.pytorch.org/whl/cpu || die "pip torch"
python -m pip install --quiet diffusers transformers accelerate safetensors huggingface_hub peft pillow || die "pip diffusers"
python -c "import torch, diffusers, transformers, peft; print('torch', torch.__version__, 'diffusers', diffusers.__version__, 'threads', torch.get_num_threads())" | tee "$O/versions.txt" || die "imports"
free -g | head -2
if [ -f ci/PREFLIGHT_ONLY ]; then
  python ci_comfy/gen_xl.py ci_comfy/prompts.json "$J" "$O" --probe-only 2>&1 | grep -v Warning || die "probe"
  grep -q . "$O/probe_1step.png" 2>/dev/null || die "probe image"
  echo "PREFLIGHT PASS"; echo "RESULT preflight only"; exit 0
fi
echo "== generate $(date +%H:%M:%S)"
python ci_comfy/gen_xl.py ci_comfy/prompts.json "$J" "$O" 2>&1 | grep -v Warning; rc=${PIPESTATUS[0]}
n=$(ls "$O"/face_*.png 2>/dev/null | wc -l); echo "RESULT job $J images $n (exit $rc)"
[ $rc -eq 0 ] && [ "$n" -gt 0 ]
