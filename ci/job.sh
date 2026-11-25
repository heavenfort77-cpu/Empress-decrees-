#!/bin/bash
# PREP-CHR runner job script, called step by step by .github/workflows/prepchr.yml (lead RULE 25 Nov: every runner job starts with PREFLIGHT).
# Steps: preflight | perf A|B | static | checks <shard 0-2>. A commit message with [preflight] runs the preflight step only (workflow if:).
set -e
set -o pipefail
step=$1
part=$2
case "$step" in
  preflight)
    # PREFLIGHT: tools, imports, inputs, output folder and a clean tree, failing in the first minute.
    sh ci_probe/chr_preflight.sh chr_out ;;
  perf)
    # Real-GPU probe (vsync off); each part measures the game's reference scene in the same job.
    if [ "$part" = "A" ]; then S=reference,chr_wide,chr_close,chr_noout,chr_wide,reference; else S=reference,chr_low,chr_dorm,chr_cycles,webglmin,reference; fi
    SCENES=$S OUT=chr_out node ci_probe/chrperf.mjs 2>&1 | tee perf.txt ;;
  static)
    node tests_draft/chars-static.mjs 2>&1 | tee static.txt ;;
  checks)
    # In-page checks and mutant shard <part> of 3 (SwiftShader: correctness and counts only).
    MUT_SHARD=$part/3 node tests_draft/chars-checks.mjs --mutants 2>&1 | tee checks.txt ;;
  *)
    echo "FAIL ci/job.sh: unknown step '$step'"; exit 1 ;;
esac
