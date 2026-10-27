# What the old benchmark reports teach

Resolves [What the old benchmark reports teach: protocol rules, failures and measurement gaps to carry over](https://github.com/ESchuderer/BenchKeeper-research/issues/11), a ticket of the map [Wayfinder map: benchmark research for BenchKeeper 7.0, MorphCook brief](https://github.com/ESchuderer/BenchKeeper-research/issues/8). Facts and evidence only. Each rule states what the evidence supports (keep, change, drop or no evidence) for a from-scratch Flutter app brief. The owner decides in later tickets.

## Sources and method

- Public, in this repository: `bench/SCENARIOS.md`, `bench/results/2026-10-18-mistreevous.md` (the Sonnet report), `bench/results/2026-10-19-mistreevous-opusplan.md` (the opusplan report), both run folders (per-trial `trial.json`, `review.json`, `review-2.json`, `brownfield-score.json`, `manifest.txt`), `bench/ORIGIN.md`.
- Held back in BenchKeeper at `9a28b89` (the pin in `bench/ORIGIN.md`): `bench/PROTOCOL.md` (cited below as `PROTOCOL:<line>`), `EVALUATIONS.md`, `evaluations/studies.md`, the skill-authoring and skills-inventory results, and 32 review files. Findings from them are paraphrased. Nothing is quoted.
- Numbers marked "computed" come from the recorded trial, review and score files of the two runs, nothing else. Not read: raw transcripts, app archives and briefs (gone, see `bench/ORIGIN.md`), the hidden tests, the reviewer prompt, and the `superseded/` attempts (not published). No claim here depends on an external source.
- Old names in short: the Sonnet run is 12 arms, 3 rounds each (36 trials), with arms AM and AN run the next day. The opusplan run is 2 arms, 3 rounds (6 trials). Arm A is plain Claude Code.

## Summary

- The recorded totals are exactly recomputable from the per-trial and review files (all 42 within 0.015). They are not recomputable from the public files alone: only 20 of 42 trials have both reviews here. The raw runs, which a re-review or a changed trace rule needs, are gone.
- The old design could not separate its arms. Hidden checks and the suite gave the same points to 32 of 36 Sonnet trials (45 of 100 points). Rank order of the 12 arms across rounds correlated between -0.16 and 0.49. Median within-arm range was 4.7 points, 50 of 66 arm pairs had medians within 3 points, and no win rule existed before the run.
- The two components that carry the variance are the process checks (trace heuristics) and the model review. Dropping the process part changes the arm order (rank correlation 0.47 with the full order).
- The follow-up rule fired only for the three BenchKeeper-layer arms (11 follow-ups in 8 of 126 steps), its detector was widened during the run after one arm stalled, and only that arm was rerun. The stopped attempts were not published, which conflicts with the protocol's own rule that every trial is reported.
- The record lacks fields that would have answered later questions: model per step, image digests per trial, attempt and detector version, check details, final messages, reviewer prompt version, network use.

## 1. Protocol rules: what each was, the evidence, what it supports

Rules are numbered for reference in later tickets. "Supports" is what the recorded evidence supports for a from-scratch Flutter brief, not a decision.

### R1. Pinned baseline and pinned hidden tests, one input for all arms
- Was: a baseline commit prepared once per run, copied to every trial, the preparation aborts if the commit differs (`PROTOCOL:169`, `PROTOCOL:182`). The hidden-test hash is recorded per trial (`PROTOCOL:173`).
- Evidence: all 42 `trial.json` files carry the same hidden-test hash and both manifests the same baseline commit (`bench/results/*/manifest.txt`). The hash method later changed so the same files get a different ID, because the old ID depended on the host's sort order (`PROTOCOL:7`).
- Supports: keep. For greenfield there is no baseline repository, so the pinned input is the spec at one commit and the prompt text. The hash method needs to be host-independent.

### R2. Natural brief that names no tool, with the way of working listed in the step text
- Was: each step names the repository's way of working (plan, tests first, run the suite, self-review, README, version history, focused commits) and no tool (`PROTOCOL:183`). Later benches use a prompt without added process requests (`PROTOCOL:199`), and the older winery brief asked every arm for its process (`PROTOCOL:96`, `PROTOCOL:160`).
- Evidence: the step text asked every arm for a plan before code. The plan check passed in 7 of 72 opportunities in the Sonnet run (steps 1 and 2: G 4, V 1, AF 1, AM 1, all others 0) and 2 of 12 in the opusplan run (computed; Sonnet report line 73 gives the ten-arm part). The protocol says results describe prompted behavior (`PROTOCOL:160`).
- Supports: change or decide. Prompted and unprompted behavior are different questions, and the old reports hold no run that compares the two on one brief.

### R3. Multi-step brief in separate sessions on the repository state the last step left
- Was: three steps, each a new session (`PROTOCOL:171`, `PROTOCOL:183`).
- Evidence: a failing suite after step 2 carried into step 3 (AL round 2, Sonnet report line 70). One defect in an equivalence check cost two hidden checks because step 3 repeats the earlier regressions check (B and AF round 1, computed: S2-equivalent and S3-regressions failed together in both).
- Supports: no evidence for greenfield. The step design is brownfield; a spec-only brief has no earlier step.

### R4. k = 3 rounds per arm, order shuffled per round, paired by round, median and range, no significance test
- Was: `PROTOCOL:175`. The protocol names the paired difference per round as the statistic.
- Evidence (computed from the per-trial table, Sonnet report lines 94 to 131):
  - Median within-arm range 4.68 points, largest 9.77 (AN) and 8.41 (B). The report states "up to about 8 points (AN: 79.18 to 88.95)" (line 30), which is 9.77.
  - Arm medians span 6.04 points, 50 of 66 arm pairs are within 3 points.
  - Spearman rank correlation of the 12 arms between rounds: round 1 and 2 -0.16, 1 and 3 0.17, 2 and 3 0.49.
  - Round 1 was won by plain Claude Code (91.48), the top total of round 1; 11 of 11 other arms trail A by 1.4 to 12.3 points in that round. Rounds 2 and 3 have A in the lower half.
  - The one repeated arm: A on the Sonnet run (91.48, 86.61, 86.97) and on the opusplan run (86.61, 85.83, 89.12), medians 0.36 apart, ranges 4.87 and 3.29. The arm image differs between the two runs (manifests, image A).
- Supports: change. Power and number of rounds belong to [How many rounds separate arms: variance in the recorded trials, power at k = 3 to 8, and judge-bias findings](https://github.com/ESchuderer/BenchKeeper-research/issues/14). This ticket gives its inputs only.

### R5. Seed fixes arm order, parallel runners, batch composition
- Was: a seed shuffles the order per round; the manifest logs the order (`PROTOCOL:175`, `PROTOCOL:203`). A seed does not fix model output (`PROTOCOL:203`).
- Evidence: the Sonnet manifest lists five runner processes sharing one order (`bench/results/2026-10-18-mistreevous-sonnet/manifest.txt`, "skipped: runner N runs it" lines, 131 of them) and 20 runner launches. Arms AM and AN ran the next day (manifest lines 510 to 551, order "AN AM", "AM AN") from manifest headers with a different BenchKeeper commit (lines 510 and 524 against `e950c3c` in the first 17 headers). The Sonnet report's claim that AM led AL in all 3 rounds (line 34) compares arms run in different batches. Arm A of the opusplan run used a different image ID than A of the Sonnet run.
- Supports: keep order shuffling and logging; change the batch rule. No recorded run has all compared arms in one interleaved batch on one BenchKeeper commit.

### R6. Win rule
- Was: none in the protocol. The Sonnet report states "No win rule was set before this run" (line 40). A rule is applied in the same report (line 31): median at least 3 points higher and ahead in at least 2 of 3 rounds, taken from an earlier bench whose data was removed.
- Evidence (computed): the rule's median difference is of unpaired medians, but "ahead in 2 of 3 rounds" is paired. H (ECC) meets the rule (+3.15, ahead in 2 of 3, report line 32). The paired median difference against A, the statistic the protocol names, is +1.01 for H. No arm has a paired median of +3 or more against A. In the opusplan run AM against A is +3.73 (medians), ahead in 2 of 3 rounds (opusplan report line 18), which meets the same rule, and the report does not apply it.
- Supports: change. The recorded evidence shows the rule was borrowed after the fact, applied in one report only, and gives different answers under unpaired and paired medians. The rule is an input to [Evidence bar: rounds, pairing, win rule and the wording a claim may use](https://github.com/ESchuderer/BenchKeeper-research/issues/15).

### R7. Follow-up rule (continue the session when the agent stops or waits for approval)
- Was: after a turn the runner sends a fixed continue message, at most twice per step, when the final message waits for confirmation or the work is not done (`PROTOCOL:107`, `PROTOCOL:171`). The detector widened in versions 1.2 and 1.8, and inside 1.21 three times after AL stalls plus two fixes before the AM runs (`PROTOCOL:9`, `PROTOCOL:22`, `PROTOCOL:28`).
- Evidence (computed from `trial.json` steps): 11 follow-ups were sent in 8 of 126 steps: AL 7 in 5 steps, AN 3 in 2 steps, AM 1 in 1 step, none in the 9 other arms. Two AL round 2 steps and one AN step reached the cap of 2. The detector changes followed stalled AL trials; a replay over the 30 recorded final messages showed that only AL's trials would change (Sonnet report lines 79 and 80, `PROTOCOL:9`). Only AL was rerun (rounds 2 and 3, repeatedly as the detector changed). The manifest logs one rerun line (line 490). The protocol later forbids changing prompts, arms or tests after seeing scores (`PROTOCOL:217`).
- Supports: change. The rule is not arm-neutral in the recorded data. Detection and the cap need to be fixed before the first run, the detector version recorded per trial, and attempts counted per arm.

### R8. One time limit for all steps
- Was: 90 minutes per trial (`PROTOCOL:104`, manifest header `timeout=5400s`).
- Evidence (computed): longest trial 47.2 minutes (H, round 3), longest step 25.7 minutes. No trial reached the limit.
- Supports: no evidence on the limit's effect for this brief. A from-scratch app is a larger task than a library feature.

### R9. Delivery audit
- Was: every init event must list exactly the arm's components and none of another arm's; a failed audit invalidates the trial (`PROTOCOL:142`, [SCENARIOS failure classes](../bench/SCENARIOS.md)).
- Evidence (computed): `audit.ok` is true in 42 of 42 trials, `problems` is empty in all. The audit passed for arms whose tools never ran: AB and AC never ran their spec tools (Sonnet report line 72). The opusplan trials record `audit.model` as claude-sonnet-5-5 in all 6 while the manifest header names the `opusplan` setting, and no trial entered plan mode, so the setting never took effect (opusplan report line 17).
- Supports: keep the audit; add a record of use. Delivery and use are separate facts (later protocol versions record listed skills apart from invoked skills, `PROTOCOL:201`; the retained files hold invocations only).

### R10. Infrastructure error rule: rerun once, then exclude
- Was: a trial stopped by a usage limit, API overload or authentication failure is rerun once, then listed as excluded (`PROTOCOL:143`, [SCENARIOS](../bench/SCENARIOS.md) failure classes).
- Evidence (computed): `infra_error` false, `is_error` false, `subtype` success in 42 of 42 trials. The rule never applied in the two runs.
- Supports: no evidence. See section 4 for the stalls that the three failure classes did not cover.

### R11. Every trial is reported
- Was: all trials, including stalls, trials without code and invalid ones (`PROTOCOL:144`).
- Evidence: the stopped AL attempts are kept in the run directory under `superseded/` and are not published (Sonnet report line 80). The retained files do not state how many attempts there were; the protocol text describes at least two stopped attempts for AL round 2 and a further one for round 3 (`PROTOCOL:9`).
- Supports: change. Practice and rule disagreed. Attempt index and reason per trial are missing (section 3).

### R12. Usage gate and subscription share per step
- Was: the runner waits for the 5-hour window to reset above a usage level and for the weekly window near its limit (`PROTOCOL:24`, `PROTOCOL:27`, `PROTOCOL:28`). Per step the share of the 5-hour and weekly windows is recorded. The protocol itself calls it valid only while no other runner or session uses the subscription (`PROTOCOL:174`, `PROTOCOL:176`).
- Evidence (computed): the Sonnet manifest logs 5 waits for a reset and 51 usage readings. Step-level `usage` is absent in 51 of 108 Sonnet steps and in 18 of 18 opusplan steps, and the share fields have a resolution of one percentage point. Five runner processes ran in parallel in the Sonnet run (R5), which the protocol names as invalidating. In the opusplan run, one runner at a time, the readings at trial boundaries (manifest lines 8 to 27) show AM using 15 points of the 5-hour window in round 1 and 5 points in round 2 at 6.26 and 5.72 USD.
- Supports: change. The gate worked as designed. The share is not usable as recorded; minutes and API-equivalent cost remain.

### R13. API-equivalent cost and minutes as the cost measure
- Was: cost as the agent reports it, tokens by type, agent minutes summed over steps (`PROTOCOL:128`, `PROTOCOL:174`; Sonnet report line 63).
- Evidence: cost and minutes are recorded for 42 of 42 trials. Cost spread within one arm is large (H 6.25 to 8.64 USD, A 3.17 to 4.39). The recorded reviews cost 99.96 USD (84 reviews, computed) against 170.24 USD for the 42 trials, about 59 percent on top. Cost split by model is not recorded at step level, so the Opus share in the opusplan report (29 to 35 percent of AM's cost, line 17) cannot be recomputed (the report cites the transcript field).
- Supports: keep the measure; change the record (cost by model, review cost kept in the trial record).

### R14. Composite score, weights 35 hidden, 10 suite, 15 static, 15 process, 25 review
- Was: `PROTOCOL:189`, `brownfield-score.json` `weights`.
- Evidence (computed over the 36 Sonnet trials):
  - Hidden and suite are at their maximum in 32 of 36 trials (6 of 6 in the opusplan run). Hidden checks passed in 28 of 30 trials of the first ten arms (Sonnet report line 67), 34 of 36 with AM and AN, 40 of 42 with the opusplan run.
  - Variance of the total is 10.33. Process contributes 2.91, review 2.23, hidden 0.89, suite 0.58, static 0.21 (variances of the parts, not additive).
  - Median within-arm range: process 3.41, review 1.75, static 0.75, hidden and suite 0.
  - Correlation of the process part with the review part across trials: 0.16.
  - The arm order by median total (H, F, G, AM, AB, AC, AN, B, V, A, AF, AL) differs from the order by mean review part (AB, AC, F, V, A, H, AM, G, AN, B, AL, AF). Spearman 0.47. H is first by total and sixth by review; AB is fifth by total and first by review. Sonnet report line 68 says the same in words.
- Supports: change. The weights carry no recorded validation, 45 points do not discriminate, and the order depends on two heuristic components.

### R15. Hidden checks, validated against a reference and the empty baseline
- Was: the untouched baseline fails every step 1 check, a reference solution passes every check and the suite (`PROTOCOL:191`). The older winery brief also validated each check with one mutant per check (`PROTOCOL:99`).
- Evidence: the brief-level validation passed, and the checks still did not separate arms (R14). Only 2 of 17 hidden checks failed at all (S2-equivalent, S3-regressions, in two trials). No mutant validation is described for this brief.
- Supports: keep reference and empty-solution validation. Whether a check separates arms is a different question from whether it is correct, and the retained data show the checks were too easy for this brief.

### R16. Static checks (20 per trial)
- Was: tests added, tests intact, dependencies unchanged, README documents the feature, version history row, committed, erosion not above baseline by more than 0.01 (`PROTOCOL:185`).
- Evidence (computed over 42 trials): 16 of 20 check ids never failed. The 4 that failed: the version-history check of step 2 failed in 42 of 42 trials, of step 3 in 21 of 42; erosion of step 1 in 3 and of step 2 in 7. The reference trial passes every check (`PROTOCOL:191`) while all 42 agent trials fail the step 2 history check, and the record holds no reason string, so the cause (agent behavior, step text or check) cannot be told apart. The Sonnet report names this check the most missed one (line 75) without noting that it failed everywhere.
- Supports: change. Five checks depend on a baseline or a repository convention (intact, deps unchanged, history, docs, erosion relative to baseline) and have no greenfield meaning as they are.

### R17. Process checks (11 per trial, from the tool-call trace)
- Was: plan before first source edit (steps 1 and 2), tests before first source file, a review skill or agent used, a test, build or lint command after the last source edit (`PROTOCOL:187`). The protocol notes a plan kept in the conversation does not count (`PROTOCOL:192`).
- Evidence (computed, steps of 126 over both runs): plan 9 of 84 opportunities (see R2); tests first 62 of 126; review 30 of 126 (arm A 2 of 18, H 7 of 9); verified 121 of 126, the 5 misses all in AL (3) and AN (2), the arms under a no-host-install rule (Sonnet report line 71). Plain arm A, which has no installed framework, is credited for review through a skill named code-review. A replay of corrected trace rules over 182 published transcripts of all briefs changed `verified` in 9 trials and the plan check in 18 (`PROTOCOL:7`); the published values of the older trials were left unchanged.
- Supports: change. The checks read file and command patterns of one language, miss plans written in the reply, and the rules changed after the runs.

### R18. Model review, blinded, twice per trial
- Was: Claude Opus 5.5, effort high, eight criteria 1 to 5, overall 1 to 10, two reviews per trial, task-only input with arm traces filtered (`PROTOCOL:188`, `PROTOCOL:138`).
- Evidence (computed, 84 reviews):
  - Repeat agreement: the two reviews of a trial gave the same overall in 20 of 42 trials, differed by 1 in 22, never by 2 or more. Mean absolute difference of the review part: 1.04 of 25 points (largest 3.91). Criteria identical in 6.1 of 8 on average.
  - Saturation: `design` is 4 in 81 of 84 reviews; `s1_requirements` is 5 in 77 of 84; mean overall 8.3 of 10.
  - Leak: 7 of 84 review texts mention a code-comment convention of one tool (AM 3, AF 2, B 2), which the protocol lists as a known leak (`PROTOCOL:138`).
  - Reviewer environment: 4 different reviewer image IDs across the 84 reviews (54, 22, 6 and 2 reviews). The reviewer image is the arm A image of the time (`PROTOCOL:138`). Two of the four (56 reviews) match no image ID in either manifest, the other two match the A images of the two runs. Trials of one arm were reviewed on different images (AC, F and H: one trial each on another image). The 12 reviews of AM and AN in the Sonnet run used two images (10 and 2 reviews) that none of the 60 reviews of the ten other arms used.
  - Same model family as the agents (Sonnet agents, Opus reviewer). No human rating of any trial exists.
  - The review prompt and schema are not in the retained files.
- Supports: change. Repeat reviews measured judge noise (about 1 point), which is smaller than the run-to-run range of an arm (median 4.7 total, 1.75 in the review part). Self-preference and bias are untested (the protocol states a judge is a signal with biases, `PROTOCOL:138`). Review design for a greenfield app belongs to [Scoring a greenfield Flutter app: acceptance checks, static checks, process checks, review and human rating](https://github.com/ESchuderer/BenchKeeper-research/issues/19).

### R19. Sandbox, credentials, scan after each trial
- Was: the container mounts only the workspace and a log folder; hidden tests are never mounted; network is on for package installs; the runner scans the trial directory for the credential after each trial and stops on a hit (`PROTOCOL:105`, `PROTOCOL:106`).
- Evidence: no hit is recorded. The brief for step 1 is an open issue of a public repository (`PROTOCOL:183`), and the trial record holds no network log or fetched-URL list, so whether any trial read the upstream project's later work cannot be told from the retained files.
- Supports: keep the isolation and the scan. For contamination see [Contamination: how an agent could reach finished MorphCook implementations, and what controls and detection exist](https://github.com/ESchuderer/BenchKeeper-research/issues/12); the old record has no detection data.

### R20. Protocol versioning
- Was: 24 versions (1.0 to 1.23) with the latest dated 2026-10-21 and the first decisions dated 2026-10-14; the recorded `method.protocol` is "1.21" in all 42 trials (computed). The follow-up detector changed several times inside 1.21 without a version bump (`PROTOCOL:9`). The AN layer label was corrected in six files after the fact (`PROTOCOL:7`); 30 of 42 trials record layer "v1" for arms that have no BenchKeeper layer (computed).
- Supports: change. A version string that does not move with rule changes does not identify the rules a trial ran under.

### R21. Scale of reporting: descriptive only, no tests, Pages site ranks by review overall
- Was: reports give medians and ranges and say "descriptive only" (both reports line 3 or 5; `PROTOCOL:175`). The site page ranks by review overall (`PROTOCOL:233`).
- Evidence: see R4, R6, R14.
- Supports: no evidence beyond R4 and R6. Decision views are covered by [Decision views: what reports and charts must show to keep, drop or retest a setup](https://github.com/ESchuderer/BenchKeeper-research/issues/21).

## 2. Metrics and checks recorded, and what a from-scratch Flutter run can use

Status for Flutter: usable (concept and mechanics carry over), rework (concept carries over, implementation is tied to the old language or brief), unusable (needs an earlier state or an old-brief convention), missing (no old record). Replacements are decided in [Scoring a greenfield Flutter app: acceptance checks, static checks, process checks, review and human rating](https://github.com/ESchuderer/BenchKeeper-research/issues/19), [Analyzer for Dart: fixed analysis config, sandbox image, and what the reviewer and tester see](https://github.com/ESchuderer/BenchKeeper-research/issues/20) and [Flutter and Dart in the analyzer sandbox: tools, image, and how a built app can be exercised and seen](https://github.com/ESchuderer/BenchKeeper-research/issues/10).

### Recorded in the retained files

| Field or check | Where | Status for Flutter |
|---|---|---|
| Hidden acceptance checks per step (17 ids `S1-*` to `S3-*`), passed and total | `trial.json` `steps[].checks` | rework: public-API tests of the old library; the idea (one check per requirement, validated against a reference and an empty solution) carries over |
| Suite green per step | `steps[].suite_ok` | rework: runs the agent's own suite; on greenfield it measures self-consistency only |
| Static checks `Q<k>-tests`, `-committed` | `steps[].checks` | usable in concept; `tests` never failed (0 of 42) |
| Static checks `Q<k>-intact`, `-deps`, `-docs`, `-history`, `-erosion` | `steps[].checks` | unusable as defined: need a baseline (intact, deps, erosion) or an old-repository convention (history, docs of a named API) |
| Process booleans `plan_first`, `tests_first`, `review`, `verified`, `tests_written` | `steps[].workflow` | rework: trace rules are per language and tool name |
| Workflow trace: `tool_calls`, `subagent_tool_calls`, `skills`, `agents`, `tiers`, `plan_or_spec_files`, `last_tool` | `trial.json` `workflow`, `steps[].workflow` | usable: tool-level facts; `skills` holds invocations only |
| Review: 8 scores, `evidence`, `unmet_requirements`, `overall`, `strengths`, `issues`, `verdict`; `model`, `effort`, `image`, review cost | `review.json`, `review-2.json` | rework: criteria `s1_requirements`, `s2_validation`, `s3_fixes` are named for the old steps; the reviewer sees code and patches, no running app |
| Minutes per step, `wall_seconds`, `duration_ms`, `turns`, `sessions`, `result_events` | `trial.json` | usable |
| Cost, API-equivalent, per step and trial; tokens (input, cache creation, cache read, output, thinking) | `trial.json` | usable; model split missing |
| `followups`, `waited`, `ask_user_calls`, `ends_with_question` | `steps[]`, `outcome` | usable; final-message text missing |
| `audit` (`ok`, `problems`, `model`, version, `plugins`) | `trial.json` | usable; `audit.model` is the init model, not the requested setting |
| `outcome` (`finished`, `subtype`, `is_error`, `infra_error`) | `trial.json` | usable; no failure class beyond infra |
| `lines` (source, test, files) | `trial.json` | rework: counts for TypeScript; recorded, not scored |
| `maintenance` (readme, readme_setup, lockfile, test_script, lint_or_typecheck, ci, node_version, changelog, docs) | `trial.json` | rework: `node_version` and `lockfile` are Node facts; recorded, not scored |
| `usage` before and after, `five_hour_share`, `weekly_share` | `steps[].usage` | unusable as recorded (R12) |
| `method` (protocol, hidden hash, `bk` layer) | `trial.json` | rework (R20) |
| Web-scorer fields `score.*` (`features`, `robustness`, `axe`, `lighthouse`, `audit`, `mutation`, `acceptance_run`, `install`, `build`, `agent_tests`, `code`, `changes`, `strict`) | `trial.json` | all null or zero in the 42 trials; left from the winery brief |
| Run-level: order, seed, images, baseline, BenchKeeper commit, usage readings, runner process ids, rerun line | `manifest.txt` | usable if structured; today a log with 557 lines in the Sonnet run, 20 repeated headers and 131 "skipped" lines |
| Score parts and totals, weights | `brownfield-score.json` | rework (R14) |

### Documented in the protocol, data removed

Recorded by older benches and no longer available: six feature tests and twelve robustness tests of a web app, mutation score of the agent's own tests, accessibility violations, Lighthouse scores, dependency audit counts, the agent's own test exit code, screenshots of four pages, per-phase and per-subagent time and cost, code duplication and per-step erosion series, thirteen-criterion app review including visual design, layout, usability and reception, targeted per-skill checks, and the SlopCodeBench group counts that were prepared and never run (`PROTOCOL:96` to `PROTOCOL:138`, `PROTOCOL:194` to `PROTOCOL:229`). Their results are not in the retained files and nothing here can be recomputed for them.

### Missing for a greenfield app (no old record)

- Requirement coverage against a spec (acceptance of a built app, not of a library API).
- Whether the app builds and starts, and any view of its screens; the retained brief ran no app.
- Static analysis result and a complexity measure for Dart.
- Human rating of any trial, and a reviewer from another model family.
- Network use and similarity to known implementations (contamination, [Contamination: how an agent could reach finished MorphCook implementations, and what controls and detection exist](https://github.com/ESchuderer/BenchKeeper-research/issues/12)).
- Cost and time by phase of the build (the old per-phase data is removed).
- Failure counts by class per arm.

## 3. What could not be recomputed or re-reviewed, and the fields that would have prevented it

The ticket context says no table can be recomputed. More exactly:

- Recomputable: every total, part, median and the per-arm tables. All 42 totals reproduce within 0.015 from `trial.json` and both review files with the recorded weights (computed). In this repository alone only 20 of 42 trials hold both review files; the other 22 trials lack 32 files that are still in BenchKeeper ([Cleanup: the held-back files, the old benches and BenchKeeper's copies](https://github.com/ESchuderer/BenchKeeper-research/issues/23) decides their fate). Without them the review part, 25 points, is not recomputable for 22 trials.
- Not recomputable, with the missing field:

| What | Why | Field that would have prevented it |
|---|---|---|
| Process checks under changed trace rules; phase split | the tool-call transcripts are gone; later rules changed 27 values among 182 transcripts of all briefs | the ordered tool-call trace per step (tool, file class, command class) kept in the record, and a rule version per trial |
| Replay of the follow-up detector | final messages are gone, only `waited` and `followups` remain | the final message (or its last lines) of each turn and the detector version used |
| Opus share and cost by model (opusplan report) | model usage lived in the transcripts; `trial.json` has token totals without model | per-model usage per step |
| Re-review of a trial, or a second judge | the repository snapshots, filtered review input, screenshots and the review prompt are gone | per-step diff or snapshot hash, a copy of the filtered review input, the prompt and schema hash in `review.json` |
| Why a check failed | checks store `id` and `ok` only | a detail or reason string per check |
| Rescoring with a corrected check or hidden test | app archives are gone, the hidden tests are not in the record (hash only) | the final repository snapshot per step, the test files or a content-addressed reference to them |
| The excluded and superseded attempts | `superseded/` was not published and the record has no attempt field | attempt index, reason code, detector version and a link to the superseded record per trial |
| Which image and BenchKeeper commit a trial ran on | image digests are in the manifest only, trial files carry none, A's digest differs between runs, the reviewer image has 4 values | image digest, BenchKeeper commit, runner id, start time and order position in each `trial.json` |
| Requested model setting | `audit.model` shows the init model (sonnet) for opusplan trials | the requested model setting and the models seen in the run |
| Subscription share | missing in 51 of 108 Sonnet steps and all 18 opusplan steps; 1 point resolution | drop, or record only for single-runner runs with the reading and the other sessions' use |
| Network use and contamination checks | no egress or fetch record | list of hosts or URLs contacted per trial |

## 4. Infrastructure and delivery failures seen, classes, exclusion and rerun rules

The old failure classes ([SCENARIOS](../bench/SCENARIOS.md), `bench/SCENARIOS.md` section "Failure classes"): installation failure (image does not build or delivery audit fails), execution failure (agent run errors, times out or stops on a usage limit, overload or authentication error; rerun once, then excluded), task-quality failure (run finishes and the scorer reports missing or failing results). A trial is reported in exactly one class.

Seen in the retained data: no installation failure, no execution failure, no timeout (R9, R10, R8). Seen in the protocol history (paraphrased, `PROTOCOL:7` to `PROTOCOL:30`):

| Failure | Class it fell into | What was done |
|---|---|---|
| Agent stops and asks the user, or ends a turn unfinished (AL rounds 2 and 3, repeatedly) | none of the three: not an error, not a scorer failure | follow-up rule, detector widened repeatedly inside one protocol version, AL rerun, stopped attempts kept unpublished (R7, R11) |
| Usage window reached | execution (usage limit) | gate before each Claude Code trial; 5 waits in the Sonnet manifest |
| App check left files in the agent's workspace, so a later maintenance fact did not show what the agent committed | measurement | the check moved to a workspace copy; earlier trials keep the flawed field |
| A hidden test failed a correct app (request aborted by navigation; test patterns too narrow) | scorer defect | test fixed, all saved trials rescored with the agent runs unchanged. Possible only while raw trials exist |
| Robustness tests added after the first rescore showed no separation | scorer design | all trials rescored. The same pattern as R14: checks adjusted after seeing results |
| A checker's rules skipped without an error because of a name clash, and a missing system data file in the scorer image gave a wrong response header | silent scorer defect | found by running the reference solution; a pre-run check of both was added. Found before any trial |
| Hidden-test hash depended on the host's sort order | record identity | hash method made host-independent, so the same files get a new ID |
| Trace rules misread shell writes, heredocs and file names as commands | scoring defect | corrected on replay of 182 transcripts, 27 values would change, published values kept |
| Layer label wrong in six trial files | record | corrected in place |
| Review criteria went from nine to thirteen between runs | measurement version drift | older reviews kept, ratings not comparable (`PROTOCOL:23`) |
| Iterative run stopped at 20 of 22 trials | partial run | not published (`PROTOCOL:15`) |
| A framework's tools never called by the model (SkillsBench-style one-shot tasks) | design | bench removed, arm could not be compared (`PROTOCOL:10`) |

Exclusion and rerun rules, as written:
- Mistreevous era: infrastructure error rerun once, then listed as excluded; failed audit invalidates the trial; every trial reported (`PROTOCOL:142` to `PROTOCOL:144`).
- Later (written, not exercised, no trial run): failed delivery audit, agent infrastructure error and checkpoint scoring error exclude a trial from summaries with counts visible; a failed solution with a completed evaluation stays valid; missing quality output is `n/a`, never zero; failed rescoring keeps the previous result; infrastructure retries keep the failed artifacts under a separately identified run; nothing changes after scores are seen (`PROTOCOL:205`, `PROTOCOL:217`).

Observed gap between rule and practice: the retained mistreevous runs applied none of the exclusion rules, yet reran and hid attempts by a rule not in the written classes (R7, R11).

## Limits of these findings

- Counts of runner processes and of attempts come from manifest lines and protocol prose, not from an attempt record.
- The held-back PROTOCOL lines are paraphrased from one commit (`9a28b89`); later BenchKeeper changes are not read.
- Computed numbers come from the trial, review and score files (the 32 held-back review files read in BenchKeeper). They agree with the report tables.
- Variance, power and judge-bias analysis beyond the inputs above belong to [How many rounds separate arms: variance in the recorded trials, power at k = 3 to 8, and judge-bias findings](https://github.com/ESchuderer/BenchKeeper-research/issues/14).
