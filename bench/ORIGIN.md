# Origin of the files in `bench/`

The files in the table below were copied unchanged from [ESchuderer/BenchKeeper](https://github.com/ESchuderer/BenchKeeper) at commit `9a28b89` (main, 2026-10-27), same relative path. Earlier history is in that repository. The files under "Moved last" came from a later commit.

| Here | Origin (BenchKeeper `main@9a28b89`) |
|---|---|
| `bench/SCENARIOS.md` | `bench/SCENARIOS.md` |
| `bench/results/2026-10-18-mistreevous.md` | `bench/results/2026-10-18-mistreevous.md` |
| `bench/results/2026-10-19-mistreevous-opusplan.md` | `bench/results/2026-10-19-mistreevous-opusplan.md` |
| `bench/results/2026-10-18-mistreevous-sonnet/` | `bench/results/2026-10-18-mistreevous-sonnet/`: run score, manifest, trial files and reviews per round and arm |
| `bench/results/2026-10-19-mistreevous-opusplan/` | `bench/results/2026-10-19-mistreevous-opusplan/`: run score, manifest, trial files and reviews |

## Evaluations

`EVALUATIONS.md` and `evaluations/` (one file per component, plus `studies.md`) were copied from BenchKeeper at commit `fd5dafd` (integration/7.0, 2026-10-28), same relative path. `evaluations/practices/lite-install.md` came later with the files below. Links to files that were still in BenchKeeper at the time now point to their copies here.

## Moved last

These 38 files were copied unchanged from BenchKeeper at commit `822bf7a` (main, 2026-10-31), same relative path. With them every recorded file of the trials is here.

- `bench/PROTOCOL.md`
- `bench/results/2026-10-16-skill-authoring.md`, `bench/results/2026-10-16-skills-inventory.md`, `bench/results/skills-files-2026-10-16.json`, `bench/results/skill-lint-2026-10-16.json`
- Sonnet run (`bench/results/2026-10-18-mistreevous-sonnet/`), `review.json` of round-1 A, AC, AL, AM, B, F; round-2 A, AM, F, G, V; round-3 AB, V. `review-2.json` of round-1 AC, AL, AM, B, H, V; round-2 A, B, F, V; round-3 AC, AM, V.
- opusplan run (`bench/results/2026-10-19-mistreevous-opusplan/`), `review.json` of round-1 A, AM; round-2 A; round-3 A. `review-2.json` of round-1 AM; round-2 A.
- `evaluations/practices/lite-install.md`

## Raw trial data is gone

The raw assets of the trials (app archives, transcripts, screenshots) and the run machinery were removed from BenchKeeper ([#256](https://github.com/ESchuderer/BenchKeeper/issues/256), [#266](https://github.com/ESchuderer/BenchKeeper/issues/266)) and are not available anywhere. The results here are the recorded summaries and per-trial score and review files only. A table in a report cannot be recomputed from the raw runs, and a trial cannot be re-reviewed. Nothing here was rebuilt or estimated.
