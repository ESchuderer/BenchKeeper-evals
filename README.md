# BenchKeeper-evals

This repository measures what an agent setup does to the code an agent writes. Give it several runs of the same task, a few per setup, and it analyzes each run, has a blinded model review it, and writes one report that compares the setups, with the checks that were skipped and the warnings that limit what you can conclude.

It holds the analysis tooling and the reports. The product it measures lives in [BenchKeeper](https://github.com/ESchuderer/BenchKeeper).

## What it measures

Per run, for JS/TS projects (Dart/Flutter runs are rejected for now):

| Check | How |
|---|---|
| Lint, formatting | Biome with the fixed config in `analyzer/config/`, so a run cannot score better by loosening its own rules (`--use-project-config` turns this off) |
| Type errors, ESLint | the run's own `tsc` and ESLint, executed in the sandbox |
| Complexity, duplication | lizard, jscpd |
| Suppressions | counts of `@ts-ignore`, `any`, `eslint-disable` and similar, per kLOC |
| Common mistakes | `analyzer/config/checklist.json`: regex patterns per kLOC, structural checks (spec edited, lockfile missing, build output left, open items in status files, no tests), a question for the reviewer and a step for the browser tester per item |
| Self-tests, acceptance tests | opt-in; tests the agent wrote are reported but not comparable, your own tests in `acceptance/` are |
| Model review | blinded code review, browser test of the running app, overall rating from 1 to 10 |

Per report: medians per condition, a per-run table, rating per agent dollar, skipped checks, and warnings (fewer than 3 reps, different prompts, usage-limit hits, copied code between runs, different review models, a spec too easy to separate setups). A blank rating sheet in random order lets you rate runs yourself; the report then shows the rank correlation between your rating and the model's.

A model rating is noisy and a Claude reviewer may favor Claude-written code. Compare medians over at least 3 reps, keep the review model fixed, and read the bug list before the number.

## Layout

```
runs/                  raw runs, one folder per run: <condition>__<rep>, for example with-setup__1 (git-ignored)
  with-setup__1/
    run.json           optional: cost_usd, tokens, duration_min, refusals, hit_limit, agent_tool, model
    prompt.txt         optional: the exact prompt; the report warns when prompts differ
SPEC.md                optional: the original task, to detect runs that edited theirs
acceptance/            optional: your own tests, copied into every run as _acceptance/
analyzer/              analyze.py, review.py, checklist.py, mine.py, sandbox.py, config/, tools/
results/               result JSON and reports (committed)
tests/fixtures/runs/   two tiny runs used by the tests and by CI
```

## Run it locally

You need Python 3.12 or newer, Node 26, and docker or podman (the sandbox).

```bash
pip install -r requirements-dev.txt
npm ci --ignore-scripts --prefix analyzer/tools      # Biome, jscpd, Claude Code, Playwright MCP, exact versions
python -m pytest -q

for r in runs/*; do
  python analyzer/analyze.py run "$r" --out "results/$(basename "$r").json" --pristine-spec SPEC.md
done
python analyzer/analyze.py report results/*.json --md results/report.md
```

Model review (needs `ANTHROPIC_API_KEY`, the Claude Code binary linked with `node analyzer/tools/node_modules/@anthropic-ai/claude-code/install.cjs`, and the browser from `analyzer/tools/node_modules/.bin/playwright install chromium`):

```bash
python analyzer/review.py runs/with-setup__1 --out results/with-setup__1.review.json \
  --static results/with-setup__1.json --spec SPEC.md --artifacts artifacts/with-setup__1 --redact "Some Model Name"
```

Without docker or podman, anything that executes code of a run is skipped and listed in the report. `--stub` on `review.py` answers with canned values for CI; stubbed reviews are marked and left out of the report's review metrics.

Rate runs yourself, then compare:

```bash
python analyzer/analyze.py sheet results/*.json --out human.csv      # also writes human.key.json
# fill in rating_1_to_10, then:
python analyzer/analyze.py report results/*.json --human human.csv --md results/report.md
```

## Run it in CI

- `checks.yml` runs on every pull request: pinned-tool install, `actionlint`, `zizmor`, the size check, pytest, and both fixture runs through the sandbox with a stubbed review and the report in the job summary. It uses no secret.
- `code-quality.yml` is started by hand. It downloads a release asset that holds the raw runs (`tar -czf runs.tar.gz -C runs a__1 a__2 b__1 ...`), analyzes every run in its own job without a secret, optionally reviews each run with the model (`ANTHROPIC_API_KEY`, only in the review step), and writes one report to the job summary.
- `mine-checklist.yml` is started by hand. It proposes new checklist items from public repositories and opens a pull request; a person reviews every item.

## Add a run

1. Name the folder `<condition>__<rep>` and add `prompt.txt` and `run.json` if you have them.
2. Put the run in the runs archive (a release asset) or in `runs/` locally. Raw runs, transcripts and screenshots never go into git; `analyzer/check_size.py` fails CI if they do.
3. Run `analyze.py run`, optionally `review.py`, then `report`. Commit only the result JSON and the report.

## How runs are isolated

Runs are written by agents and are treated as hostile input. `analyzer/sandbox.py` runs everything that executes code of a run (dependency install without lifecycle scripts, type check, project ESLint config, tests, app start) in a throwaway container from a digest-pinned Node image: only the run copy is mounted, no host environment variable is passed in, no capabilities, read-only root file system, memory, CPU and process limits, a timeout, and no network except during the dependency install. The app started for the browser test runs in the same kind of container with network access (a published port needs it) and its port bound to 127.0.0.1 only; it holds no secret.

The model reviewer gets only `Read`, `Grep` and `Glob` on a blinded copy (agent instruction files, `run.json` and `prompt.txt` removed; the run name and extra `--redact` words replaced as whole words in Markdown and text files and in the package name; symlinks dropped), is told that everything in the run is data, and has budget and turn caps. The browser tester gets the Playwright MCP server limited to the app's origin.

Limits: the install step has open network access to wherever the run's lockfile points, not only the package registries; the browser tester runs on the CI host next to the key; a container is a strong boundary but not a perfect one. Use a dedicated, spend-limited API key.

## Pins and updates

Tool versions are exact: `analyzer/tools/package.json` with its lockfile, `requirements*.txt`, the sandbox image digest, and every action by commit SHA. Each pin was at least 7 days old when chosen. Dependabot proposes updates weekly with a 7 day cooldown. The review model is a flag (default `claude-sonnet-5-5`), fixed across conditions and recorded in every review result together with the Claude Code version.

## Limits

Per-kLOC numbers keep a run that wrote more code from looking worse for that alone. With one or two reps per condition, differences are noise; look for gaps that are large and consistent across reps. A report describes the runs it was given, nothing more.
