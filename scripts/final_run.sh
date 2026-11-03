#!/bin/bash
# The final run, exactly as docs/final-run.md says. Run from the repo root on the final-run branch:
#   caffeinate -i bash scripts/final_run.sh 2>&1 | tee final-run.log
# Takes several hours. Each command has its own --budget, so a broken loop can't run away.
set -u
cd "$(dirname "$0")/.."

python scripts/verify_seeds.py | grep -v '^ok' && { echo "a seed is broken, stopping"; exit 1; }
python scripts/freeze.py
git add docs/frozen-manifest.json
git commit -qm "Freeze the answer key for the final run"
git push -q origin final-run
touch results/final/START
echo "frozen at $(git rev-parse --short HEAD), starting $(date)"

run_prompt() {
  local flag="$1" tag="$2"
  python -m wjj $flag --budget 8 duel all --rounds 3
  for s in ttlcache proxyauth xmlattr; do
    for t in spec_narrowing input_guard; do
      for i in 1 2 3; do
        python -m wjj $flag --budget 2 duel $s --cheat-type $t --rounds 3
      done
    done
  done
  python -m wjj $flag --budget 3 probe
  python -m wjj $flag --budget 8 eval --attempts 2 --workers 2 --out results/final/eval-$tag
}

run_prompt "" original > results/final/log-original.txt 2>&1 &
sleep 5
run_prompt "--strict-judge" strict > results/final/log-strict.txt 2>&1 &
wait
python -m wjj --budget 5 cases --repeat 3

find results -maxdepth 1 -type f -newer results/final/START -exec mv {} results/final/ \;
for f in results/final/duel-ttlcache-*.jsonl results/final/duel-proxyauth-*.jsonl results/final/duel-xmlattr-*.jsonl results/final/cases-*.jsonl; do
  python -m wjj --budget 1 confirm "$f"
done

python scripts/freeze.py --check
echo "done $(date)"
