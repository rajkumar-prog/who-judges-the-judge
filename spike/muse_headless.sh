#!/usr/bin/env bash
# One headless Muse Code fix on the toy seed, then the hidden tests from outside the workspace.
# Usage: META_API_KEY=... ./muse_headless.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="$(mktemp -d)/toy"
ROOT="$(cd "$HERE/.." && pwd)"
cp -r "$ROOT/seeds/toy" "$WORK"
mkdir -p "$HERE/out"
cd "$WORK" && git init -q && git add -A && git -c user.name=seed -c user.email=seed@local commit -qm seed
SEED="$(git rev-parse HEAD)"

# --approval-mode never keeps the sandbox on; avoid --yolo outside a throwaway container.
# Flags come from a third-party guide; confirm with `muse exec --help` first.
time muse exec --json --approval-mode never --disable-web-tools \
  --max-model-steps 30 --reasoning-effort medium \
  --prompt-file "$WORK/task.md" > "$HERE/out/run.jsonl" 2> "$HERE/out/run.stderr" || echo "muse exec exited $?"

# Diff against the seed commit so agent commits and new files are included.
git -C "$WORK" add -A
git -C "$WORK" diff --cached "$SEED" > "$HERE/out/run.diff"
echo "--- visible tests";  (cd "$WORK" && python -m pytest -q tests) || true
echo "--- hidden tests";   (cd "$WORK" && python -m pytest -q "$ROOT/hidden/toy") || true
echo "--- touched test files?"; git -C "$WORK" diff --cached --name-only "$SEED" | grep -E '^tests/' || echo "none"
echo "events: $(wc -l < "$HERE/out/run.jsonl")  diff: $HERE/out/run.diff"
grep -io '"usage"[^}]*}' "$HERE/out/run.jsonl" | tail -1 || echo "no usage event found; check run.jsonl for token counts"
