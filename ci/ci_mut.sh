#!/bin/bash
# Run a mutation round (or a full suite with -sims) on GitHub runners and wait for the summary.
# Usage: ci_mut.sh <label> <job.json> [repo-dir]
#   job.json: {"mode":"mut","label":...,"muts":[{"name","want","a","b"}...]}  or  {"mode":"suite","label":...}
#   The CURRENT working tree of repo-dir (default /home/claude/empress-decrees-) is what gets tested, committed or not.
# Result: prints summary.txt; files in out/<label>/<run id>/ on branch ci-out. Never pushes to main or batches-3-5.
set -euo pipefail
LABEL=$1; JOB=$2; REPO=${3:-/home/claude/empress-decrees-}; WT=/home/claude/ci-wt; GH=heavenfort77-cpu/Empress-decrees-
exec 9>/home/claude/citools/.lock; flock 9
cd "$WT"; git fetch -q origin ci-run
git reset -q --hard origin/ci-run
KEEP=$(mktemp -d); cp -r .github ci "$KEEP"/
find "$WT" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +; (cd "$REPO" && tar --exclude=.git --exclude=node_modules --exclude=backup --exclude="*_before_*" -cf - .) | (cd "$WT" && tar -xf -)
cp -r "$KEEP"/.github "$KEEP"/ci "$WT"/; python3 - "$JOB" "$LABEL" <<'PY'
import json,sys; j=json.load(open(sys.argv[1],encoding='utf-8')); j['label']=sys.argv[2]; json.dump(j,open('ci/job.json','w',encoding='utf-8'),ensure_ascii=False)
PY
git add -A; git -c user.name=Claude -c user.email=noreply@anthropic.com commit -qm "ci job $LABEL"
SHA=$(git rev-parse HEAD); git -c push.negotiate=true push -q -f origin HEAD:ci-run 2>&1 | grep -iE "error|reject" || true
for k in $(seq 1 30); do ID=$(gh api "repos/$GH/actions/runs?branch=ci-run&head_sha=$SHA&per_page=1" --jq '.workflow_runs[0].id // empty'); [ -n "$ID" ] && break; sleep 5; done
echo "run $ID sha ${SHA:0:7}"
for k in $(seq 1 120); do S=$(gh api "repos/$GH/actions/runs/$ID" --jq .status); [ "$S" = completed ] && break; sleep 20; done
gh api "repos/$GH/actions/runs/$ID" --jq '"\(.conclusion) wall \((((.updated_at|fromdate)-(.run_started_at|fromdate))/60)|floor) min"'
git fetch -q --depth=1 origin ci-out; git show "origin/ci-out:out/$LABEL/$ID/summary.txt"
