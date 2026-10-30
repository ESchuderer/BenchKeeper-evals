#!/usr/bin/env bash
# Runs the review prompt over each fixture with one agent and compares kind and first line with expected.json.
# Usage: bash run.sh claude|codex [model]
set -u
here=$(cd "$(dirname "$0")" && pwd)
agent=$1 model=${2:-}
out=$here/out/$agent; mkdir -p "$out"
pass=0 total=0
for f in "$here"/fixtures/*.md; do
  name=$(basename "$f")
  q="$(cat "$here/prompt.txt")"$'\n'"$(nl -ba -w1 -s': ' "$f")"
  dir=$(mktemp -d)
  start=$(date +%s)
  if [ "$agent" = claude ]; then
    (cd "$dir" && timeout 120 claude -p "$q" --restricted --tools "" --strict-mcp-config --no-session-persistence --output-format json --max-turns 2 --max-budget-usd 0.25 ${model:+--model "$model"} </dev/null) > "$out/$name.json"
    answer=$(jq -r .result "$out/$name.json"); cost=$(jq -r '.total_cost_usd' "$out/$name.json"); tokens=$(jq -r '.usage | (.input_tokens + .cache_read_input_tokens + .cache_creation_input_tokens) as $i | "\($i) in, \(.output_tokens) out"' "$out/$name.json")
  else
    (cd "$dir" && timeout 120 codex exec --sandbox read-only --skip-git-repo-check --ephemeral --json -o "$dir/answer.txt" ${model:+-m "$model"} "$q" </dev/null) > "$out/$name.jsonl"
    answer=$(cat "$dir/answer.txt"); cost=n/a; tokens=$(jq -rs '[.[] | select(.type=="turn.completed") | .usage] | "\(map(.input_tokens) | add) in, \(map(.output_tokens) | add) out"' "$out/$name.jsonl")
  fi
  secs=$(( $(date +%s) - start )); rm -rf "$dir"
  got=$(printf '%s' "$answer" | sed -n '/{/,$p' | jq -c '[.findings[] | "\(.kind):\(.lines[0])"] | sort' 2>/dev/null || echo '"unparsed"')
  want=$(jq -c --arg n "$name" '[.[$n][] | "\(.kind):\(.lines[0])"] | sort' "$here/expected.json")
  total=$((total + 1)); [ "$got" = "$want" ] && pass=$((pass + 1)) && ok=PASS || ok=FAIL
  echo "$ok $name ${secs}s cost=$cost tokens=($tokens) want=$want got=$got"
done
echo "$pass/$total fixtures match"
