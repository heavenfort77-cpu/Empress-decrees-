#!/bin/bash
# SUITS fa concept job (branch ci-comfy-suitfa): SDXL base 1.0 + SDXL-Lightning 8-step LoRA (diffusers, CPU) renders one prompts.json entry:
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
assert (j['seeds'] or j.get('img2img')) and j['view']; [c[k] for k in ('base','lora_repo','lora_file','positive','width','height','steps','guidance')]
for e in j.get('img2img',[]): assert os.path.getsize(e['init'])>0 and 0<e['strength']<1, e" "$J" || die "prompts.json job $J"
python -m py_compile ci_comfy/gen_xl.py ci_comfy/unet_step.py || die "gen_xl.py / unet_step.py compile"
mkdir -p "$O" || die "mkdir $O"
echo "PREFLIGHT A PASS"
sleep $((40 * J))   # stagger the matrix jobs (two of four stalled with simultaneous starts)
export HF_HUB_DOWNLOAD_TIMEOUT=60 HF_HUB_ETAG_TIMEOUT=30 PYTHONUNBUFFERED=1
echo "== preflight B (install, models, 1-step probe) $(date +%H:%M:%S)"
timeout 600 python -m pip install --quiet torch --index-url https://download.pytorch.org/whl/cpu || die "pip torch"
timeout 600 python -m pip install --quiet diffusers transformers accelerate safetensors huggingface_hub peft pillow || die "pip diffusers"
python -c "import torch, diffusers, transformers, peft; print('torch', torch.__version__, 'diffusers', diffusers.__version__, 'threads', torch.get_num_threads())" | tee "$O/versions.txt" || die "imports"
free -g | head -2
echo "cpu: $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | xargs), nproc $(nproc), bf16 flags: $(grep -m1 -o -w -E 'avx512_bf16|amx_bf16' /proc/cpuinfo | sort -u | xargs echo -n) (none = no native bf16), avx512f: $(grep -m1 -c -w avx512f /proc/cpuinfo)" | tee -a "$O/versions.txt"
if [ -f ci/PREFLIGHT_ONLY ]; then
  timeout 1500 python ci_comfy/gen_xl.py ci_comfy/prompts.json "$J" "$O" --probe-only 2>&1 | grep -v Warning || die "probe"
  grep -q . "$O/probe_1step.png" 2>/dev/null || die "probe image"
  # cause probe: one UNet forward per process; the oneDNN ISA cap imitates a CPU without native bf16 (AVX512_CORE = AVX-512 without bf16,
  # AVX2 = no AVX-512 at all, e.g. EPYC 7763). Info lines, not a gate.
  for c in "none bfloat16" "AVX512_CORE bfloat16" "AVX2 bfloat16" "AVX2 float32"; do set -- $c
    if [ "$1" = none ]; then timeout 600 python ci_comfy/unet_step.py ci_comfy/prompts.json $2 2>&1 | grep "UNET STEP" || echo "UNET STEP isa cap $1 dtype $2: timeout/fail"
    else ONEDNN_MAX_CPU_ISA=$1 timeout 600 python ci_comfy/unet_step.py ci_comfy/prompts.json $2 2>&1 | grep "UNET STEP" || echo "UNET STEP isa cap $1 dtype $2: timeout/fail (600 s)"; fi
  done
  echo "PREFLIGHT PASS"; echo "RESULT preflight only"; exit 0
fi
echo "== generate $(date +%H:%M:%S)"
timeout 3000 python ci_comfy/gen_xl.py ci_comfy/prompts.json "$J" "$O" 2>&1 | grep --line-buffered -v Warning; rc=${PIPESTATUS[0]}
n=$(ls "$O"/fa_*.png 2>/dev/null | wc -l); echo "RESULT job $J images $n (exit $rc)"
[ $rc -eq 0 ] && [ "$n" -gt 0 ]
