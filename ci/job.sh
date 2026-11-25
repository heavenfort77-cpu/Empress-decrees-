#!/usr/bin/env bash
# PREP-AV job script (lead rule 25 Nov: a runner branch carries ci/job.sh with a PREFLIGHT step). Called by .github/workflows/prepav-run.yml.
# Usage: bash ci/job.sh linux|mac. Linux: checks and the mutation round (software GPU: correctness only). Mac: real-GPU timing.
# PREFLIGHT_ONLY=1 stops after the preflight. Exit 1 on a failed preflight, a failed check, a missed mutant or a failed gate.
set -u
MODE=${1:-}
case "$MODE" in linux) OUT=o ;; mac) OUT=mac_out ;; *) echo "usage: bash ci/job.sh linux|mac"; exit 2 ;; esac
# 1. PREFLIGHT (tools, imports, inputs, outputs, clean tree): fails in the first minute.
bash ci_prepav/preflight.sh "$OUT" 2>&1 | tee preflight.txt
[ "${PIPESTATUS[0]}" -eq 0 ] || exit 1
if [ "${PREFLIGHT_ONLY:-0}" = 1 ]; then echo "PREFLIGHT-ONLY: checks skipped"; exit 0; fi
# 2. The run.
if [ "$MODE" = linux ]; then
  { echo "== static-src"; node tests_draft/static-src.mjs; echo "exit $?";
    echo "== fx-map"; node tests_draft/fx-map.mjs /nonexistent; echo "exit $?";
    echo "== fx-runtime"; node tests_draft/fx-runtime.mjs; echo "exit $?";
    echo "== mutate"; node tests_draft/mutate.mjs; echo "exit $?"; } 2>&1 | tee "$OUT/checks.txt"
  git diff --stat | tee "$OUT/diff_after.txt"
  # A failed section fails the job (each script exits 1 on a FAIL or a missed mutant); the FAIL lines on ci-out stay the proof.
  ! grep -q '^exit [1-9]' "$OUT/checks.txt"
else
  OUT="$OUT" node ci_prepav/perfprepav.mjs 2>&1 | tee "$OUT/perf.txt"
  [ "${PIPESTATUS[0]}" -eq 0 ]
fi
