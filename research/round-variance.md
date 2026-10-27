# Round variance, power and judge agreement in the recorded mistreevous trials

Findings for [How many rounds separate arms: variance in the recorded trials, power at k = 3 to 8, and judge-bias findings](https://github.com/ESchuderer/BenchKeeper-research/issues/14), on the map [Wayfinder map: benchmark research for BenchKeeper 7.0, MorphCook brief](https://github.com/ESchuderer/BenchKeeper-research/issues/8). Facts and sources only; no decision is recommended. The decision on rounds, pairing and win rule belongs to [Evidence bar: rounds, pairing, win rule and the wording a claim may use](https://github.com/ESchuderer/BenchKeeper-research/issues/15).

Every number below is printed by `research/round-variance.py` (Python standard library only, fixed seed 20261027, 10000 bootstrap draws, about 15 seconds):

```
python -I research/round-variance.py
```

## Data used

- Sonnet run `bench/results/2026-10-18-mistreevous-sonnet/`: 12 arms, 3 rounds, 36 trials, agent model claude-sonnet-5-5 in every trial (field `audit.model`). 10 arms ran on 2026-10-18, AM and AN on 2026-10-19.
- opusplan run `bench/results/2026-10-19-mistreevous-opusplan/`: arms A and AM, 3 rounds, 6 trials, other seed. Used only for the spread of arm A and AM, not in the bootstrap.
- Score parts (hidden 35, suite 10, static 15, process 15, review 25) add up to the recorded total in all 42 trials (checked in the script).
- Review files: 52 of the 84 expected `review.json` and `review-2.json` files are in this repository (the others stay in BenchKeeper, see `bench/ORIGIN.md`). All 52 are from claude-opus-5-5. Both ratings per trial are also in the per-trial tables of the two reports, so the overall rating (1 to 10) covers all 42 trials. Per-criterion data covers the 20 trials that have both files.
- The review part is the mean of the two reviews: (sum of the 8 criteria minus 8) / 32 x 25 for one review. The script reproduces the recorded review part from the files for 20 of 20 trials.

## 1. Spread per score component

Units are points of the component (hidden 35, suite 10, static 15, process 15, review 25, total 100). "Within-arm SD" is the pooled sample SD over the 3 rounds of each arm. "Residual SD" is what remains after removing arm and round means (22 degrees of freedom). "Round SD" is the estimated SD of a round effect common to all arms. "Pair SD" is the pooled SD of the per-round difference between two arms (average of the variance over all 66 arm pairs, then the root). The two p-values are permutation tests (5000 shuffles): arm labels shuffled inside each round, and round labels shuffled inside each arm.

| Component | Within-arm SD | Largest arm range | Round SD | Residual SD | Pair SD | p, arms differ | p, rounds differ |
|---|---|---|---|---|---|---|---|
| hidden | 0.97 | 4.12 (AF) | 0.29 | 0.93 | 1.31 | 1.000 | 0.327 |
| suite | 0.78 | 3.33 (AL) | 0.00 | 0.80 | 1.13 | 1.000 | 1.000 |
| static | 0.45 | 1.50 (H) | 0.09 | 0.44 | 0.62 | 0.447 | 0.268 |
| process | 1.70 | 5.46 (G) | 0.33 | 1.67 | 2.36 | 0.394 | 0.238 |
| review | 1.22 | 4.30 (B) | 0.37 | 1.17 | 1.65 | 0.022 | 0.136 |
| total | 3.06 | 9.77 (AN) | 1.03 | 2.88 | 4.08 | 0.157 | 0.110 |

- Hidden and suite are constant in 32 of 36 trials. All their spread comes from four trials with a failure (B and AF round 1, AL round 2, AN round 1), so their SD is not a Gaussian noise level and the p-values of 1.000 only say that two or four trials cannot show an arm effect.
- Process (1.70) and review (1.22) carry most of the spread; static is small. The only component whose arm differences are unlikely under shuffling is review (p 0.022, one of six tests, no correction).
- Total: the pooled within-arm SD is 3.06 (median arm SD 2.49). Without the four failed trials it is 2.09. The largest range in one arm is 9.77 (AN, 79.18 to 88.95), then B 8.41 and AL 7.82. The Sonnet report's "about 8 points" matches B and AL; AN is larger.
- Round-to-round: round means of the total are 86.51, 86.93 and 88.98. The round effect (SD 1.03) is small next to the residual (2.88). Pairing by round shrinks the pooled SD of an arm difference by about 6 percent (paired 4.08 against about 4.33 unpaired, ratio 0.94 in the script). Restricted to the 10 arms of 2026-10-18, the pair SD is 3.88, the residual SD 2.75 and the round SD 0.61.
- Arm effect on the total: the permutation p is 0.157. The between-arm SD of the observed 3-round means is 2.11; the part expected from noise alone (residual variance divided by 3) leaves an estimated SD of the true arm means of 1.30.
- Opusplan run: A has SD 1.72 (86.61, 85.83, 89.12) and AM 1.75; in the Sonnet run A has SD 2.71 and AM 2.28. Arm A in both runs (same configuration, 6 trials): mean 87.77, SD 2.13, range 5.65.

Per arm, total score, sorted by mean:

| Arm | Round 1 | Round 2 | Round 3 | Mean | SD | Range |
|---|---|---|---|---|---|---|
| H | 90.12 | 87.62 | 91.64 | 89.79 | 2.03 | 4.02 |
| AM | 87.38 | 88.98 | 91.87 | 89.41 | 2.28 | 4.49 |
| F | 89.73 | 87.97 | 90.48 | 89.39 | 1.29 | 2.51 |
| G | 85.83 | 89.31 | 92.82 | 89.32 | 3.50 | 6.99 |
| A | 91.48 | 86.61 | 86.97 | 88.35 | 2.71 | 4.87 |
| AB | 88.72 | 87.78 | 88.37 | 88.29 | 0.48 | 0.94 |
| AC | 87.94 | 87.39 | 89.15 | 88.16 | 0.90 | 1.76 |
| V | 87.22 | 84.86 | 91.26 | 87.78 | 3.24 | 6.40 |
| AF | 83.82 | 87.74 | 84.63 | 85.40 | 2.07 | 3.92 |
| AN | 79.18 | 87.58 | 88.95 | 85.24 | 5.29 | 9.77 |
| B | 79.56 | 87.97 | 87.58 | 85.04 | 4.75 | 8.41 |
| AL | 87.16 | 79.34 | 84.08 | 83.53 | 3.94 | 7.82 |

## 2. Detectable difference and ranking stability (total score, paired by round)

Design assumed: every arm runs in each of k rounds, the per-round difference between two arms is the unit, and the test is on the mean of those k differences. Round 1 to 3 of the recorded data are the only rounds available, so k = 5, 8 and 10 are extrapolations.

### Minimal detectable difference

The pooled SD of one per-round difference is 4.08 points. A cluster bootstrap over the 12 arms (2000 resamples) gives a 5th to 95th percentile range of 3.04 to 5.01 for it. The minimal detectable difference (MDD) is the true difference a two-sided test at 5 percent detects with 80 percent power.

| k | MDD with a paired t-test (Monte Carlo, pooled SD 4.08) | same, SD at 5th / 95th percentile | MDD if the pooled SD is taken as known (2.80 x SD / sqrt(k)) | P(right sign of the mean difference) for a true difference of 1 / 2 / 3 / 5 points, SD known |
|---|---|---|---|---|
| 3 | 13.30 | 9.92 / 16.35 | 6.59 | 0.66 / 0.80 / 0.90 / 0.98 |
| 5 | 6.90 | 5.15 / 8.49 | 5.11 | 0.71 / 0.86 / 0.95 / 1.00 |
| 8 | 4.75 | 3.54 / 5.83 | 4.04 | 0.76 / 0.92 / 0.98 / 1.00 |
| 10 | 4.03 | 3.01 / 4.96 | 3.61 | 0.78 / 0.94 / 0.99 / 1.00 |

- The t-test column treats the SD of each comparison as estimated from its own k rounds, so at k = 3 (2 degrees of freedom, critical value 4.30) it is about twice the known-SD column. The known-SD column assumes all 66 pairs share one SD, which the failed trials contradict (see limits).
- Rounds needed for 80 percent power with the paired t-test, by true difference, for the pooled SD and (in brackets) the 5th and 95th percentile SD. The script tests k = 3 to 12, 15, 20, 25, 30 and 40 only, so values above 12 are intervals between grid points, and Monte Carlo error can move a boundary by one round: 5 points 8 (6; 10), 4 points 11 (7; 13 to 15), 3 points 16 to 20 (11; 21 to 25), 2 points 31 to 40 (21 to 25; more than 40), 1 point more than 40.
- By component (paired t-test, pooled SD of that component), k = 3 / 5 / 8 / 10: static 2.04 / 1.06 / 0.73 / 0.62; review 5.39 / 2.80 / 1.92 / 1.63; process 7.71 / 4.00 / 2.75 / 2.34; hidden 4.27 / 2.22 / 1.52 / 1.30; suite 3.70 / 1.92 / 1.32 / 1.12. Components are not additive, and hidden and suite rest on four failed trials.

### Bootstrap over the recorded rounds

Method: draw k rounds with replacement from the 3 recorded rounds (whole rounds, so all arms keep their round pairing), average per arm, rank. Two variants: plain, and variance-corrected (deviations from the arm mean multiplied by sqrt(3/2) so that the resampling variance equals the sample variance). Noise band: half width of the central 95 percent of (resampled minus observed) difference of two arm means over all 66 pairs. Bootstrap MDD: 95th percentile of the absolute noise minus the 20th percentile of the signed noise.

| k | Kendall tau to observed ranking (plain / corrected) | P(top-1 arm unchanged) | P(top-3 set unchanged) | SD of a pair difference | 95% noise band | MDD, 80% power |
|---|---|---|---|---|---|---|
| 3 | 0.71 / 0.65 | 0.45 / 0.45 | 0.34 / 0.22 | 1.91 / 2.34 | 3.91 / 4.79 | 5.26 / 6.49 |
| 5 | 0.73 / 0.69 | 0.41 / 0.42 | 0.29 / 0.29 | 1.48 / 1.82 | 3.17 / 3.91 | 4.21 / 5.18 |
| 8 | 0.78 / 0.75 | 0.55 / 0.49 | 0.30 / 0.27 | 1.19 / 1.43 | 2.53 / 3.01 | 3.35 / 4.00 |
| 10 | 0.80 / 0.77 | 0.65 / 0.62 | 0.31 / 0.26 | 1.05 / 1.29 | 2.23 / 2.74 | 2.92 / 3.59 |

Probability that the sign of a pair difference is kept, by the observed gap of the 3-round means (plain bootstrap; number of pairs in the bin: 16, 17, 8, 21, 4):

| Observed gap | k = 3 | k = 5 | k = 8 | k = 10 |
|---|---|---|---|---|
| under 1 | 0.66 | 0.61 | 0.65 | 0.67 |
| 1 to 2 | 0.87 | 0.89 | 0.92 | 0.94 |
| 2 to 3 | 0.91 | 0.96 | 0.98 | 0.99 |
| 3 to 5 | 0.95 | 0.98 | 0.99 | 0.99 |
| 5 and more | 0.99 | 1.00 | 1.00 | 1.00 |

How to read it: the bootstrap measures how far a ranking moves relative to the observed 3-round ranking. Beyond k = 3 it keeps resampling the same 3 rounds, so its stability rises with k by construction and says little about the true ranking. With 3 distinct rounds the results at small k are also lumpy (27 possible resamples at k = 3), which is why P(top-1 unchanged) is not monotone in k.

### Model-based check against the true ranking (not a bootstrap)

True arm means are set to the observed means shrunk by the noise they contain (estimated SD of true arm means 1.30, shrink factor 0.62), or left unshrunk; scores are the true mean plus Gaussian noise with the residual SD 2.88 divided by sqrt(k); 4000 simulated experiments per k.

| k | Kendall tau to true ranking, shrunk / unshrunk | P(true best arm ranked first), shrunk / unshrunk |
|---|---|---|
| 3 | 0.43 / 0.58 | 0.20 / 0.26 |
| 5 | 0.51 / 0.64 | 0.23 / 0.30 |
| 8 | 0.58 / 0.70 | 0.25 / 0.35 |
| 10 | 0.61 / 0.72 | 0.27 / 0.37 |

### The rule in the Sonnet report, at k = 3

The report's reading rule is a median lead of at least 3 points plus a lead in at least 2 of 3 rounds ([2026-10-18-mistreevous.md](../bench/results/2026-10-18-mistreevous.md), section Verdict and Cost, quality and time).

- Under no true difference between arms, the rule fires for a given pair with probability 0.29 when scores are Gaussian with the pooled within-arm SD of 3.06 (0.30 in the bootstrap null built from the recorded rounds), and 0.13 with the SD of 2.09 that remains without the four failed trials. At least one of 66 pairs fires with probability 0.996 (0.935 with SD 2.09); at least one of the 11 pairs that include arm A fires with 0.917 (0.603).
- In the recorded data the rule fires for 16 of 66 pairs: H over A, 6 over AF and 9 over AL. The expected count for 66 pairs is about 19 at 0.29 and about 8 at 0.13. The count does not show that arms are alike: the permutation test on the total gives p 0.157, and AF and AL are the two arms with the lowest means.
- With a true difference of 2, 3, 4 and 6 points, the rule fires for the better arm with probability 0.30, 0.45, 0.60 and 0.84 (bootstrap null shifted by the difference).

## 3. Agreement of the two reviews

Both reviews of a trial come from the same model (claude-opus-5-5, effort high, `model` and `effort` fields of all 52 files). The agreement below is the repeatability of one judge, not agreement between two judges.

Overall rating (1 to 10), all 42 trials (from the report tables):

- Exact agreement 20 of 42, within 1 point 42 of 42, mean absolute difference 0.52, Pearson r 0.44, quadratic weighted kappa 0.42.
- The ratings given are 6 (1 time), 7 (6), 8 (39) and 9 (38). Only 8 and 9 are used in 77 of 84 ratings, so the range is narrow and r and kappa are low partly for that reason.

Per criterion (1 to 5), 20 trials with both files:

| Criterion | Exact agreement | Mean abs difference | Mean, review 1 / review 2 |
|---|---|---|---|
| s1_requirements | 15/20 | 0.25 | 4.95 / 4.80 |
| s1_correctness | 14/20 | 0.30 | 4.70 / 4.60 |
| s2_validation | 15/20 | 0.25 | 4.60 / 4.65 |
| s3_fixes | 13/20 | 0.35 | 4.00 / 3.95 |
| design | 19/20 | 0.05 | 4.05 / 4.00 |
| tests | 17/20 | 0.15 | 4.65 / 4.50 |
| docs | 13/20 | 0.35 | 4.75 / 4.70 |
| process | 13/20 | 0.35 | 4.30 / 4.25 |

- Sum of the 8 criteria: mean absolute difference 1.35 of 40, Pearson r 0.64 (n = 20). Review 1 is higher than review 2 on average: 36.00 against 35.45 of 40, 0.43 points of the 25-point review part.
- Judge noise against arm-by-round spread: the SD of the noise in a 2-review mean is 0.75 points of 25, against a residual SD of 1.17 in the recorded review part. That is about 41 percent of the residual variance of the review part, estimated from 20 trials.

Review against process checks (process checks are the 11 workflow-trace checks scored out of 15; they are computed from the tool trace, not from the review):

| Pair | Pearson / Spearman |
|---|---|
| review part and process-check part, all 42 trials | 0.14 / 0.20 |
| same, Sonnet run, arm means removed (36 trials) | 0.17 / 0.22 |
| same, Sonnet run, between the 12 arm means | 0.17 / -0.12 |
| review criterion `process` (mean of 2) and process-check part, 20 trials | 0.04 / -0.02 |
| review part and static-check part, all 42 trials | -0.29 / -0.29 |
| review part and minutes, all 42 trials | 0.51 / 0.57 |
| review part and minutes, within arm | 0.15 / 0.24 |
| review part and lines of code (source plus test, whole repository), all 42 | 0.53 / 0.44 |
| review part and lines of code, within arm | -0.04 / -0.09 |

- The review and the process checks are nearly uncorrelated, between arms and within arms. The arm order differs: by mean review part AB 23.18, AC 23.05, F, V 22.92, A 22.79 lead and AF 19.79, AL 20.18 trail; by process checks H and AM 8.64 and G 8.18 lead and AL 5.45 trails.
- The positive correlation of the review with minutes and code size is a between-arm effect (the Ponytail arms B, AF and AL are fast, small and lowest in review); within an arm it is weak. The data cannot separate "the judge prefers longer work" from "longer work is better".

## 4. Published findings

Only abstracts and proceedings pages were read, unless stated. "Verified" means the abstract page was fetched and read for this ticket.

Model-judge self-preference

| Source | Finding | Status |
|---|---|---|
| Panickssery, Bowman, Feng, [LLM Evaluators Recognize and Favor Their Own Generations](https://arxiv.org/abs/2404.13076), NeurIPS 2024 ([proceedings](https://papers.nips.cc/paper_files/paper/2024/hash/7f1f0218e45f5414c79c0679633e47bc-Abstract-Conference.html)) | Evaluators rate their own outputs above others of equal human-judged quality; GPT-4 and Llama 2 recognize their own text above chance; fine-tuning shows a linear link between self-recognition and self-preference. Experiments are on summarization (XSUM and CNN/DailyMail, per the [HTML version](https://arxiv.org/html/2404.13076v1)). | verified (abstract, proceedings page, HTML version) |
| Zheng et al., [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685), NeurIPS 2023 Datasets and Benchmarks | Names position, verbosity and self-enhancement bias in LLM judges; GPT-4 reaches over 80 percent agreement with humans, the level of human-human agreement. | verified (abstract) |
| Wataoka, Takahashi, Ri, [Self-Preference Bias in LLM-as-a-Judge](https://arxiv.org/abs/2410.21819), NeurIPS 2024 Safe Generative AI Workshop | GPT-4 shows significant self-preference; the authors tie it to low perplexity: judges rate low-perplexity outputs higher than humans do, whether or not self-generated. | verified (abstract) |
| Chen et al., [Do LLM Evaluators Prefer Themselves for a Reason?](https://arxiv.org/abs/2504.03846) | On verifiable tasks (math, factual knowledge, code generation) across 7 model families, much self-preference of stronger models matches objectively better answers; harmful self-preference (favoring a worse own answer) persists when the model fails as generator and is larger in stronger models; long reasoning before judging reduces it. | verified (abstract); code-specific figures not read |
| Crupi et al., [On the Effectiveness of LLM-as-a-judge for Code Generation and Summarization](https://arxiv.org/abs/2507.16587), IEEE TSE | 8 LLMs judged correctness of 1,405 Java methods and 1,281 Python functions; GPT-4-turbo was best and even the best judge often misjudged correctness. | verified (abstract); whether it analyzes self-preference not seen, unverified |

No source was found or read that measures self-preference for coding-agent repositories reviewed by a model of the same family as the agent. This data set has a Claude Opus 5.5 reviewer for Claude Sonnet 5.5 agents (and Opus subagents in the AM opusplan trials), no non-Claude reviewer and no blinded human rating, so self-preference cannot be measured from it. Whether the 2026-10 reviews were blinded to the arm is not stated in the two reports; `analyzer/review.py` (lines 1 to 10) describes redaction of instruction files and names, but that is the current analyzer, not the script that produced these files.

Run-to-run variance of agent benchmarks

| Source | Finding | Status |
|---|---|---|
| Bjarnason, Silva, Monperrus, [On Randomness in Agentic Evals](https://arxiv.org/abs/2602.07150) (2026) | 60,000 trajectories on SWE-Bench-Verified, three models, two scaffolds: single-run pass@1 varied by 2.2 to 6.0 percentage points depending on the run chosen; SD above 1.5 points even at temperature 0; gains of 2 to 3 points may be noise; recommends several runs per task, power analysis for the number of runs, and reporting pass@k and pass^k. | verified (abstract); body not read (PDF text not extractable here) |
| Miller, [Adding Error Bars to Evals](https://arxiv.org/abs/2411.00640) (2024) | Treats eval questions as a sample from a super-population; gives formulas to analyze results, compare two models and plan evals. | verified (abstract); that it recommends paired differences and clustering is unverified (body not read) |
| Kapoor et al., [AI Agents That Matter](https://arxiv.org/abs/2407.01502) (2024) | Accuracy-only agent evaluation, lack of standardized evaluation and inadequate holdout sets cause reproducibility problems; proposes optimizing cost and accuracy jointly. Does not give run-to-run numbers. | verified (abstract) |

Unverified leads, seen only in search summaries and not read: SWE-agent ([arXiv 2405.15793](https://arxiv.org/abs/2405.15793)) reportedly gives variance over six GPT-4 runs on SWE-bench Lite in an appendix; AgentLens ([arXiv 2607.06624](https://arxiv.org/abs/2607.06624)) reportedly reports an SD of 0.94 over five repeated runs of one configuration.
## What the data cannot say

- One brief (a three-step TypeScript feature task in one library), 3 rounds, 12 arms, one model (Sonnet 5.5, effort high), one runner host and one agent runtime. Variance of a greenfield Flutter app ([Scoring a greenfield Flutter app: acceptance checks, static checks, process checks, review and human rating](https://github.com/ESchuderer/BenchKeeper-research/issues/19)) can differ in size and in which components carry it. Here hidden checks and suite are at their ceiling in 32 of 36 trials, so nearly all spread sits in review, process and static; that will not hold for a score whose acceptance checks discriminate.
- Each arm has 2 degrees of freedom. Pooled values (22 degrees of freedom) assume one noise level for all arms; the failed trials (B, AF, AL, AN) and the arm SDs from 0.48 to 5.29 contradict that. Scores are bounded and have a heavy low tail, so Gaussian power numbers are approximate.
- A "round" here is a position in time, not a matched condition. The arms ran in a different order each round (`manifest.txt`), AM and AN ran a day later, so for those two the round pairing is by index only. The manifests record the subscription usage fractions (5-hour and weekly) before each arm and log "skipped: runner N runs it" lines, which shows more than one runner process on the one host; neither was analyzed, so effects of window position or concurrent runners are not separated from noise. The round effect found (SD about 1 point) is small and not significant (p 0.11), and a larger effect in a new cycle is not excluded.
- Rounds 4 to 10 are not in the data. All results for k = 5, 8 and 10 are extrapolations of the 3-round spread; the bootstrap stability for k above 3 is mechanical (section 2).
- Sources of spread are not separated. Run-to-run randomness of the agent, judge noise (about 41 percent of the review residual, from 20 trials), the two-day split and the follow-up rule reruns (AL rounds 2 and 3) all sit in the same residual.
- Two reviews from the same judge give repeatability, not validity. No human rating exists to check either. Self-preference cannot be measured without a second judge family or humans.
- Cost and minutes were not analyzed; they are not scored.
- Per-criterion review agreement uses the 20 trials that have both files here; the other 22 trials lack at least one file, which stays in BenchKeeper.
- Raw runs are gone (`bench/ORIGIN.md`), so no score can be recomputed from the raw trial and no extra review can be run.
