# MorphCook brief: source, commit, prompt, spec and what a finished app is

Findings for the ticket [MorphCook brief: which source and commit to pin, what the prompt and spec require, and what a finished app is](https://github.com/ESchuderer/BenchKeeper-research/issues/9), part of the map [Wayfinder map: benchmark research for BenchKeeper 7.0, MorphCook brief](https://github.com/ESchuderer/BenchKeeper-research/issues/8). Read on 2026-10-27. No decision is made here: the owner decides in a later grilling ticket.

## How this was read

- Primary sources only: the two public repositories read through `gh api` and two shallow clones into an empty scratch directory, plus official documentation URLs where an external claim is made.
- No file from either repository was run, built or executed. Counts come from `find`, `grep` and `awk` over the text. Test-case counts are line-pattern approximations (a `test(` or `testWidgets(` at line start), not results of a test run.
- Every claim about a repository is tied to a path and, where it fits, a line. SPEC.md line numbers (written `L54`) refer to blob `ff0a931ffe1f3244db0b725d3ae0383f2a5a081f` (24,810 bytes), which is the same file in both repositories (see 1.1).
- Short names: **morphcook** is [TheMorpheus407/morphcook](https://github.com/TheMorpheus407/morphcook), **cli-benchmark** is [TheMorpheus407/morphcook-cli-benchmark](https://github.com/TheMorpheus407/morphcook-cli-benchmark).

## Summary

- SPEC.md is byte-identical in both repositories (blob `ff0a931f`, SHA-256 `5fb46fa8f1c84b5629684bd5e2dc068a04a154da1ccdc91d38cb502796cde987`). Which repository to pin matters for the prompt and for what else gets pulled in, not for the spec text.
- The two repositories carry two different prompts. cli-benchmark has `PROMPT.md` (630 bytes, autonomous, internet allowed, no budget). morphcook has a 174-byte `prompt.txt` in 6 of its 32 folders and no prompt at its root. The prompt used for the other 26 folders is not recorded.
- morphcook holds 32 implementation folders and cli-benchmark 3, so 35 finished implementations of this spec are public. The README of morphcook lists 7 folders; the list is stale.
- Four folders carry a spec text that differs from the pristine one: `claude-fable-5` (27,005 bytes), `kimi-k3`, `kimi-k2-7` and `glm-5-2` (25,724 bytes). The pristine text was added at the morphcook root in commit `708d5e4893` on 2026-07-26 and is unchanged at the current head.
- Both repositories are MIT licensed under one identical LICENSE file ("Copyright (c) 2026 Cedric Mössner (The Morpheus)"). The SPEC itself says the licence is "TBD (do not add yet)" (L482, L542).
- SPEC.md yields 212 atomic requirements by my count: 141 checkable by code without a UI (68 of them from files, static scans or the pipeline script alone), 52 that need the running app driven, 13 that need a person, 6 that need model calls (the corpus pipeline stages).
- The spec pins no Flutter, Dart or package version. The 32 reference `pubspec.yaml` files hold lower bounds only (Dart `^3.10.1` is the most common). Every `.metadata` file carries a Nix placeholder instead of a real SDK revision, so the SDK actually used is not recoverable from the repositories.
- 31 of 32 folders ship Flutter tests. Every test is written against its own folder's classes, so they can seed test vectors but are not drop-in hidden checks. There are no `integration_test` directories.

## 1. What to pin

### 1.1 The two repositories

| | morphcook | cli-benchmark |
|---|---|---|
| Head commit | `d314a20dbcb5d0d96bbe7334967adc6b6ecc6813`, 2026-10-15 | `bb5bacfc6c584296bb88de1d3a078c8b59b18ee5`, 2026-09-01 (the only commit) |
| Created | 2026-06-10 | 2026-09-01 |
| Branches, tags | 1 branch, 0 tags | not checked |
| SPEC.md | [root SPEC.md](https://github.com/TheMorpheus407/morphcook/blob/d314a20dbcb5d0d96bbe7334967adc6b6ecc6813/SPEC.md), added by `708d5e4893ac787f49526b38f8cf3ddf1f6c6b54` ("Add pristine SPEC.md at repo root as the benchmark baseline"), never changed since | [SPEC.md](https://github.com/TheMorpheus407/morphcook-cli-benchmark/blob/bb5bacfc6c584296bb88de1d3a078c8b59b18ee5/SPEC.md), same blob |
| Prompt | none at root; `prompt.txt` in 6 folders | [PROMPT.md](https://github.com/TheMorpheus407/morphcook-cli-benchmark/blob/bb5bacfc6c584296bb88de1d3a078c8b59b18ee5/PROMPT.md), blob `d68b6bde9ee9493114932db9021528d1d18b1cee` |
| Content | 32 top-level folders, one per model run | 3 folders under `implementations/` (Claude Code, Codex CLI, Antigravity CLI) |
| Stated purpose | model comparison; each folder holds the spec it was built against ([README](https://github.com/TheMorpheus407/morphcook/blob/d314a20dbcb5d0d96bbe7334967adc6b6ecc6813/README.md)) | coding-agent CLI comparison with model and assignment held constant; scores, rankings, logs, transcripts, costs, token usage, run tooling code and infrastructure configuration are excluded ([README](https://github.com/TheMorpheus407/morphcook-cli-benchmark/blob/bb5bacfc6c584296bb88de1d3a078c8b59b18ee5/README.md)) |
| History caveat | README says the first commit touching a folder is the one-shot output and later commits are human-directed. By commit messages only `claude-fable-5` has later commits (v1.7.0 at head); path-filtered commit lists for `claude-fable-5-1`, `claude-sonnet-5-5`, `GPT-6-Astra`, `claude-opus-4-7`, `qwen-3.8-27b` show only the landing commit | README says no manual product fixes were applied and non-source artifacts were removed |

The README of cli-benchmark says "fourteen coding-agent CLIs" but publishes three; it says the missing entries are not a ranking.

### 1.2 Three spec texts exist

| Text | SHA-256 (first 12) | Bytes | Where |
|---|---|---|---|
| Pristine | `5fb46fa8f1c8` | 24,810 | morphcook root, cli-benchmark root, 27 of 31 morphcook folder copies (also `claude-fable-5` at its first commit `24d1bcb2cc`), 3 cli-benchmark folders (hashes checked) |
| Lattice wording | `3137a918de56` | 25,724 | `kimi-k3`, `kimi-k2-7`, `glm-5-2` |
| Fable 5 head | `f79ea99ca728` | 27,005 | `claude-fable-5` (changed by `393dc3881e` and `caa984fdb1`) |

`sakana-fugu-ultra` has no SPEC.md copy. The pristine text is the only one that matches the cli-benchmark assignment.

What differs from the pristine text (from `diff`):

- Lattice wording (`3137a918de56`): rewrites the "load-bearing idea" so each dish has a complete lattice of diet columns x two effort levels x two calorie levels, with titles that do not name the diet; refers to `docs/corpus-brief-4.md`; says combinations outside the profile are never locked; changes the dish-detail example chips. Four diff hunks, no change to the backup format or the matching algorithm.
- Fable 5 head (`f79ea99ca728`): the above plus personal recipes, local recipe photos, backup schema version 2 with `personal_recipes` and `recipe_images`, a stricter import (size limits, duplicate checks), PBKDF2 raised from 10,000 to 210,000 iterations, only the encrypted JSON shared when a password is set, and "Bundled photography" replacing "Real photography". This text describes a later product than the pristine spec.

### 1.3 Two prompts exist

| | `PROMPT.md` in cli-benchmark | `prompt.txt` in morphcook |
|---|---|---|
| Size | 630 bytes, 10 lines | 174 bytes, one sentence |
| Text, in short | Build the complete app from SPEC.md (L1); work autonomously until the whole system is implemented, "tests and static analysis pass, and you have run the application yourself" (L3-4); do not stop at scaffolding, prototype or MVP; internet and dependency installs allowed (L5-6); do not modify SPEC.md (L7); when blocked, decide, document and continue (L7-8); no time, turn, model-call or tool-call budget (L10) | "Implement the flutter app defined in SPEC.md 100% complete. Do create the nostalgic calm look and feel for the app yourself. You may NOT touch any files outside this folder!" |
| Folders | applies to the 3 cli-benchmark folders | `qwen-3.8-27b`, `qwen-3.8-27b-128k`, `qwen-3.8-27b-256k`, `claude-fable-5-1`, `GPT-6-Astra`, `claude-opus-5` (all six byte-identical, SHA-256 `aaf7c6f5d674`) |
| Silent on | Flutter version, target device, working folder, how to run the app, which analyzer, the pipeline agent CLIs, design and web references | tests, static analysis, running the app, internet, budget |

Whether `PROMPT.md` was also given to the morphcook folders, or which prompt the other 26 folders got, is not stated in either repository (unverified). The three cli-benchmark folders and the six prompt.txt folders are the only runs with a recorded prompt.

### 1.4 Licence of each file

| File or set | Licence | Source |
|---|---|---|
| Everything in morphcook not listed below (SPEC.md, README.md, `prompt.txt`, all implementation folders) | MIT, "Copyright (c) 2026 Cedric Mössner (The Morpheus)" | [LICENSE](https://github.com/TheMorpheus407/morphcook/blob/d314a20dbcb5d0d96bbe7334967adc6b6ecc6813/LICENSE); GitHub API reports SPDX `MIT` for both repositories |
| Everything in cli-benchmark (SPEC.md, PROMPT.md, README.md, 3 implementations) | MIT, same text | [LICENSE](https://github.com/TheMorpheus407/morphcook-cli-benchmark/blob/bb5bacfc6c584296bb88de1d3a078c8b59b18ee5/LICENSE); `cmp` shows the two LICENSE files are byte-identical |
| Bundled fonts in 7 folders (`claude-fable-5`, `claude-fable-5-1`, `claude-opus-5`, `claude-opus-5-5`, `claude-sonnet-5-5`, `GPT-5.6-Sol-Ultra`, `Mistral-Large-4`) | SIL Open Font License, text files `OFL*.txt` next to the fonts | files in those folders' `assets/fonts` or `assets/google_fonts` |
| Third-party notices in `claude-fable-5/app/assets/licenses` | Bouncy Castle, Liberation Fonts, PDFBox Android, Unicode license texts | [SOURCES.md and licence files](https://github.com/TheMorpheus407/morphcook/tree/d314a20dbcb5d0d96bbe7334967adc6b6ecc6813/claude-fable-5/app/assets/licenses) |

- No per-file licence headers exist in the Dart, Python or shell sources (the only copyright lines are Flutter template `AppInfo.xcconfig` files).
- The spec text contradicts the repositories: SPEC.md says "License: TBD (do not add yet)" (L482, L542) and "Repo name: morphcook (GitHub, private)" (L466).
- MIT requires the copyright and permission notice to stay with copies of the files (text of the LICENSE file above). Whether the licence covers model-generated code is a legal question not answered here (unverified).

### 1.5 Options for the pin, and what each costs

The options differ in provenance, prompt and what a clone drags in. None is recommended here.

| Option | What it fixes | What it leaves open or costs |
|---|---|---|
| A. cli-benchmark at `bb5bacfc6c` | Spec and prompt in one commit that the repository's README names as "the assignment". The repository has one commit, so the pin cannot drift under a branch. | The same commit holds 3 finished implementations (plain clone exposes them to the agent workspace unless the two files are copied out). `PROMPT.md` assumes an unbounded budget, internet and the ability to run the app. History, scoring and run tooling are not published, so how the original runs applied it is not verifiable. |
| B. morphcook at `708d5e4893` (spec) or `d314a20dbc` (head) | Spec identical to A. The commit message calls the root spec "the benchmark baseline". 32 folders give a wide reference set. | No root prompt: we would choose or write one, or reuse the 174-byte `prompt.txt`. The head moves (7 folders landed between 2026-09-07 and 2026-10-15). 32 implementations (35 with A) are public. |
| C. Copy the two files (SPEC.md plus a prompt) into our repository with the blob hash `ff0a931f` and the SHA-256 above | A pin that needs no network and survives a rewritten upstream history. | Must carry the MIT notice. Any prompt choice is ours, so comparability with upstream runs is by spec text only. |
| D. A non-pristine spec (`3137a918de56` or `f79ea99ca728`) | Describes the lattice contract or the later product. | Not what cli-benchmark published; `f79ea99ca728` adds features outside the pristine scope and refers to files (`docs/corpus-brief-4.md`) that exist only inside one folder. |

Any change to the spec is to be written down (map decision). The places where a from-scratch run would need a change or a ruling are listed in 3.4.

### 1.6 Inputs the spec names that neither repository supplies

- `design/` (a "Claude Design bundle", L503) and `web/` (a runnable HTML prototype) are called the reference for onboarding, aesthetic and branding (L61, L111-113, L467-470, L503-504). Neither repository has them at its root. The `design/` folders inside implementations differ (for example `claude-code/design/design-spec.md` versus `codex-cli/design/design-system.md` and `tokens.json`), which suggests each agent wrote its own (inference).
- `docs/asset-partitioning-strategy.md` (L151) and `docs/b2b/` (L555): 13 folders contain a copy of the first, with 13 different hashes, so each was authored per run (inference; provenance unverified). Whether the run setup supplied any of these files to the agents is not stated (unverified).
- Consequence: a run from SPEC.md alone has a spec that points at four resources it does not contain.

## 2. What cannot be checked offline, needs a model call, or needs the network

The spec, the prompt and the build each touch the network at different times. Rows refer to the appendix IDs.

### 2.1 App at run time (the spec forbids network)

- No network calls at run time, no HTTP client beyond store and legal URLs (L137-138); no backend, telemetry or LLM calls from the app (L55, L128). Checkable offline by static scan of dependencies and the Android manifest (rows 3, 6, 78, 79). One implementation's own notes say its release manifest has no Internet permission ([GPT-6.1-Sol/docs/verification.md](https://github.com/TheMorpheus407/morphcook/blob/d314a20dbcb5d0d96bbe7334967adc6b6ecc6813/GPT-6.1-Sol/docs/verification.md), self-reported, not verified here).
- Ambiguity: search "partition-based chunk loading with on-demand partition fetching" (L223, row 121) reads as network fetching but the corpus is bundled (L56). A checker needs a ruling.
- Share sheet and file picker (L85-86) need an OS or emulator, but no network.

### 2.2 Agent run and build (not in the spec, implied by the prompt)

- `flutter pub get` resolves packages from pub.dev over the network by default. `--offline` uses only the local package cache ([dart pub get](https://dart.dev/tools/pub/cmd/pub-get)). A sandbox without network needs a warm cache for every package the agent may choose.
- `google_fonts` fetches fonts over HTTP at run time by default and prefers matching font files declared in the app's assets; bundling needs the font files downloaded from fonts.google.com first ([pub.dev google_fonts](https://pub.dev/packages/google_fonts)). The spec requires bundling (L142), so the agent needs the network, or supplied font files, once.
- Android builds fetch Gradle: all 34 `gradle-wrapper.properties` files in the two repositories point to `https://services.gradle.org/distributions/gradle-8.14-all.zip`.
- "You have run the application yourself" (PROMPT.md L4) needs a device or emulator. iOS: Flutter runs iOS apps through Xcode ([Flutter iOS setup](https://docs.flutter.dev/platform-integration/ios/setup)); that Xcode needs macOS is stated by one reference implementation ([GPT-6-Astra/README.md](https://github.com/TheMorpheus407/morphcook/blob/d314a20dbcb5d0d96bbe7334967adc6b6ecc6813/GPT-6-Astra/README.md): "iOS requires macOS and Xcode") and not read in a first-party Flutter or Apple page here (unverified). On a Linux runner only Android and `flutter test` are reachable.
- PROMPT.md L5-6 allows internet use. Both repositories are public, so the finished apps are reachable from inside a run; how to control or detect that belongs to the ticket [Contamination: how an agent could reach finished MorphCook implementations, and what controls and detection exist](https://github.com/ESchuderer/BenchKeeper-research/issues/12) and is not decided here.

### 2.3 Corpus generation pipeline (model calls)

- The pipeline has five model stages, each an agent call: generator, flag-verifier (with up to N retries), nutrition-calculator, copy-editor, final reviewer (L369-399, rows 178 to 183).
- The spec's own run example names three agent back ends: `claude`, `codex` and `opencode/minimax` (L410-413). A reference pipeline maps them to `claude -p`, `codex exec` and `opencode run` ([claude-sonnet-5-5/pipeline/pipeline.sh L272-286](https://github.com/TheMorpheus407/morphcook/blob/d314a20dbcb5d0d96bbe7334967adc6b6ecc6813/claude-sonnet-5-5/pipeline/pipeline.sh#L272-L286)). Running a stage needs those CLIs installed, authenticated and online.
- Offline parts: the `--dry-run` flag (L415) is implemented without agent calls in the references ([claude-opus-5/pipeline/pipeline.sh L90-92](https://github.com/TheMorpheus407/morphcook/blob/d314a20dbcb5d0d96bbe7334967adc6b6ecc6813/claude-opus-5/pipeline/pipeline.sh#L90-L92), [claude-sonnet-5-5 help text L60](https://github.com/TheMorpheus407/morphcook/blob/d314a20dbcb5d0d96bbe7334967adc6b6ecc6813/claude-sonnet-5-5/pipeline/pipeline.sh#L60)), and the quality gates (schema, ontology, cross-check, duplicate detection, sample output; L423-429, rows 192 to 196) are plain scripts.
- Cannot be met by an autonomous agent at all: "human-reviewed" recipes (L17-18) and the human spot-check (L428-429), because PROMPT.md tells the agent to work autonomously (L3) and to decide and continue when blocked (L7-8). They are person-checked claims, not agent actions.
- Corpus size: the spec gives no minimum number of dishes or recipes (only an 80/20 split between core and extended files, L155-156). One reference reports 64 recipes and 16 dishes ([GPT-6.1-Sol/docs/verification.md](https://github.com/TheMorpheus407/morphcook/blob/d314a20dbcb5d0d96bbe7334967adc6b6ecc6813/GPT-6.1-Sol/docs/verification.md), self-reported). Corpus content (DE and EN texts, correct flags, voice) can only be judged by a person or a model.

## 3. Size of the task

### 3.1 Count and method

I split SPEC.md into atomic, separately testable statements: one per bullet clause, profile field, flag, pipeline flag, table row, named method or error string. This is my segmentation, so another reader may count 180 to 250; the appendix lists every row with its line so it can be re-cut. Excluded as non-product text: the RepoLens note (L3-4), the ticket sizing rules for another tool (L509-517), the "Decisions Locked" table (L521-542, which repeats earlier lines) and "Decisions Deferred" (L546-555, all negative).

Classes:

- **U**: checkable by code without driving a UI (pure logic, data files, static scan, script flags). Split into **F** (file, static or script check at a path or flag the spec names) and **A** (pure logic that needs a per-implementation adapter, because the spec fixes no function or constructor).
- **W**: needs the running app driven (widget, emulator or UI tester), offline. The spec fixes no widget keys or labels.
- **H**: needs a person or a judge for look, tone or UX.
- **N**: needs network or a model call.

| Section (SPEC lines) | Rows | U | W | H | N |
|---|---|---|---|---|---|
| Scope, in (L50-113) | 72 | 25 | 40 | 7 | 0 |
| Scope, out (L115-128) | 6 | 3 | 2 | 1 | 0 |
| Architecture, client (L134-146) | 6 | 4 | 1 | 1 | 0 |
| Data assets (L148-171) | 9 | 8 | 1 | 0 | 0 |
| Local state (L173-187) | 11 | 11 | 0 | 0 | 0 |
| Matching algorithm (L189-201) | 9 | 9 | 0 | 0 | 0 |
| Time and staleness ranking (L203-218) | 6 | 6 | 0 | 0 | 0 |
| Search (L220-226) | 5 | 4 | 1 | 0 | 0 |
| Pagination (L228-260) | 14 | 11 | 3 | 0 | 0 |
| Backup format (L262-292) | 17 | 17 | 0 | 0 | 0 |
| Ontology (L296-357) | 18 | 16 | 2 | 0 | 0 |
| Recipe pipeline (L361-429) | 23 | 17 | 0 | 0 | 6 |
| Variant switching UX (L433-459) | 3 | 0 | 2 | 1 | 0 |
| Branding (L463-472) | 3 | 1 | 0 | 2 | 0 |
| Repository layout (L476-505) | 10 | 9 | 0 | 1 | 0 |
| **Total** | **212** | **141** | **52** | **13** | **6** |

### 3.2 What checks need

- **F: 68 rows** are checkable with no adapter: asset file names and presence, ontology contents, forbidden dependencies and permissions, the repository layout, pipeline script flags and gates. They check presence and shape only; the spec does not define the recipe record (fields appear only inside the matching pseudo-code, L192-198).
- **A: 73 rows** (matching 9, ranking 6, backup section 17, backup rows in scope 5, shopping and insights 7, quick-tap 2, calorie filter and avoidance 2, pagination logic 10, profile fields 9, search logic 4, ontology propagation 2) need glue per implementation. Of these, 8 name a Dart identifier the glue can look for: `PaginationController` with `loadMore()`, `refresh()`, `reset()`, `shouldLoadMore(index)` (L254-258), `OneHandedCookModeController.quickNextTapEnabled` (L100) and `DecryptionException` (L288). Constructors, import paths and signatures are not specified for any of them. The spec also names the settings `visualAlertEnabled` and `reduceMotion` (L97-98, L187).
- **W: 52 rows** need a UI driver. A hidden widget test cannot find widgets in an unknown tree without selectors, so these checks need a model-driven or human tester. This is the subject of the tickets [Scoring a greenfield Flutter app: acceptance checks, static checks, process checks, review and human rating](https://github.com/ESchuderer/BenchKeeper-research/issues/19) and [Analyzer for Dart: fixed analysis config, sandbox image, and what the reviewer and tester see](https://github.com/ESchuderer/BenchKeeper-research/issues/20).
- **H: 13 rows** understate the human share: most W rows also carry a look-and-feel judgement (polaroid rotation, paper grain, masthead).
- **N: 6 rows** are the model stages of the pipeline (2.3).

### 3.3 What "finished" means in the prompt, and what code can see

PROMPT.md names three conditions (L3-4): the entire specified system is implemented; tests and static analysis pass; the agent ran the application itself.

| Condition | Checkable by code | Needs a person or a transcript |
|---|---|---|
| Whole system implemented | partly: the 141 U rows and, with a driver, the 52 W rows | the 13 H rows and the content quality of the corpus |
| Tests pass | `flutter test` exit status, but the tests are the agent's own, so a pass says little about the spec | whether the tests cover the spec |
| Static analysis passes | `flutter analyze` exit status; the analysis options sit in the agent's tree and can be edited (one `analysis_options.yaml` per Flutter project, 35 in all; `flutter_lints` is a dev dependency in all 32 morphcook `pubspec.yaml` files) | whether the agent weakened the rules |
| Ran the application | no | evidence in the run transcript only |

The cli-benchmark repository publishes no transcripts, so the original runs cannot be checked against these conditions (README: scores, logs and transcripts excluded).

### 3.4 Undefined or contradictory points in SPEC.md

A from-scratch run, or a hidden check, needs a ruling on each (and any ruling is a written spec change):

| Point | Lines | Fact |
|---|---|---|
| Calorie tolerance | L197 | `tolerance` is used but never given a value |
| Base ranking score | L200-201, L218 | bonuses (+200, +90, +90, +50) apply "after the base ranking calculation", which has no numeric definition; whether the tie-break order is lexicographic or weighted is not said |
| Time windows | L207-209 | "5am to 11am", "5pm to 9pm", "weekend": inclusivity and day set not stated |
| Recipe asset name | L155-156, L364, L402, L486 | partition files `core-recipes.json` and `extended-recipes.json` versus a single `assets/recipes.json`; the layout tree lists `recipes.json` and `faqs.json` but not the partition files or `ingredient-guide.json` |
| Effort values | L69 versus L322 | "effort=pro" in the switcher text versus `easy`, `medium`, `hard` in the ontology |
| Network | L137-138 versus L223 | "No network calls at runtime" versus "on-demand partition fetching" |
| Platform APIs | L93 versus L85-86 | "no platform-specific APIs" versus the OS share sheet |
| Backup encryption | L90-92, L283 | with a password the GZip file stays unencrypted (so the same data is exposed); PBKDF2 at 10,000 iterations, where OWASP recommends 600,000 for PBKDF2-HMAC-SHA256 ([OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)). The Fable 5 spec text raised it to 210,000 and stopped sharing the GZip file |
| Licence and repository | L466, L482, L542 | "private", "no LICENSE yet" versus public MIT repositories |
| Missing referenced inputs | L61, L111-113, L151, L503, L555 | see 1.6 |
| Tooling note | L3-4 | "Feed to RepoLens as `--spec SPEC.md --mode feature`" addresses another tool, not the agent |
| Quick-tap and visual alert | L96-101 | the spec names `OneHandedCookModeController` and `visualAlertEnabled` as if they were existing code; a from-scratch app has no such class until it creates it |

### 3.5 Scale reference

From the reference folders (Dart under `lib/`; `claude-fable-5` is its edited head state, not one-shot output): lines of Dart range from 2,781 (`qwen-3.8-27b`) to 18,383 (`claude-sonnet-5-5`), median 8,393 over the 31 folders that contain an app. `qwen-3.8-27b-256k` holds only `SPEC.md`, `prompt.txt` and `opencode.jsonc`, no app. Whether any reference implements all 212 rows was not assessed (nothing was run).

## 4. Flutter, Dart and package versions

### 4.1 The spec pins nothing

SPEC.md names Flutter and Dart (L136), `google_fonts` (L141), `flutter_animate` "or similar" (L143), `ValueNotifier`, `Provider` or `Riverpod` (L145), `shared_preferences` (L175), "Hive (or sqflite)" (L176), `ListView.builder` (L250), `ChangeNotifier` (L254), AES-256-GCM and PBKDF2 (L282-283). No version number appears for any of them. The example dates in the backup block (`2026-04-18`, `2026-W16`; L267, L270) suggest the spec was drafted around April 2026 (inference); Flutter 3.41.7 with Dart 3.11.5 was the stable release on 2026-04-16 per the [official release list](https://storage.googleapis.com/flutter_infra_release/releases/releases_linux.json).

### 4.2 What the reference implementations declare

Dart constraint in `pubspec.yaml` (32 files, 31 folders; `Gemini-4-Argon` has two):

| Constraint | Files |
|---|---|
| `^3.10.1` | 12 |
| `^3.11.5` | 8 |
| `^3.10.0` | 3 |
| `^3.11.0` | 2 |
| `>=3.8.0 <4.0.0` | 2 |
| `>=3.3.0 <4.0.0` | 2 |
| `^3.5.0`, `>=3.10.0 <4.0.0`, `>=3.0.0 <4.0.0` | 1 each |

`pubspec.lock` `sdks:` block (31 files): Flutter lower bound `>=3.38.0` 15, `>=3.38.4` 10, `>=3.41.0` 4, `>=3.38.1` 1, `>=3.35.6` 1. These are the lowest SDK that satisfies the resolved packages, not the SDK used to build ([pubspec SDK constraints](https://dart.dev/tools/pub/pubspec#sdk-constraints)). The effective minimum is set by the Dart constraint: per the official release list Dart 3.10.x ships with Flutter 3.38.x, Dart 3.11.x with Flutter 3.41.x.

- Every `.metadata` file (32, in both repositories) holds `revision: "nixpkgs000000000000000000000000000000000"` and `channel: "stable"`, so the exact SDK that created each project is not recoverable. This suggests Flutter came from Nixpkgs (inference).
- Four READMEs state a version: `claude-sonnet-5-5` "Flutter 3.41 (Dart 3.11)", `GPT-6-Astra` "Flutter 3.41 / Dart 3.11 or newer", `GPT-6.1-Sol` "Flutter 3.41.9 / Dart 3.11.5 or a compatible newer stable SDK" (and its `docs/verification.md` says the same version on Linux, 2026-09-30, self-reported), `GPT-5.6-Sol-Ultra` "Flutter 3.38 or newer".
- All 34 Gradle wrappers use Gradle 8.14 (see 2.2), which points to one template generation (inference).
- The current stable release at the time of reading is Flutter 3.47.8 with Dart 3.13.7 (2026-10-23, [official release list](https://storage.googleapis.com/flutter_infra_release/releases/releases_linux.json)). All reference constraints allow it; whether any reference compiles on it was not tested.

### 4.3 Packages the references chose

Direct dependencies across the 32 `pubspec.yaml` files (count of files; all with caret ranges):

| Package | Files | Package | Files |
|---|---|---|---|
| `path_provider` | 31 | `intl` | 17 |
| `share_plus`, `shared_preferences` | 30 each | `flutter_animate` | 17 |
| `file_picker` | 26 | `hive` | 16 |
| `provider` | 23 | `google_fonts` | 16 |
| `cupertino_icons` | 21 | `collection` | 11 |
| `pointycastle` | 19 | `archive` | 11 |
| `hive_flutter` | 18 | `cryptography` | 10 |
| `flutter_localizations` | 14 | `crypto` | 10 |

Also present: `hive_ce`, `hive_ce_flutter`, `encrypt`, `uuid`, `wakelock_plus`, `audioplayers`, `url_launcher`, and singletons. No `riverpod`, `sqflite` or `bloc` dependency appears in any file. Dev dependency `flutter_lints` is in all 32. `google_fonts`, which the spec names, is in only 16 of 32 files. Versions differ per folder (for example `google_fonts` `^6.2.1` in cli-benchmark `claude-code`, `^8.2.1` in `claude-sonnet-5-5`), so package versions are an agent choice at run time, resolved by whatever pub.dev offered on the day.

## 5. Implementations that ship tests or acceptance material

Full inventory in Appendix B. Facts:

- 31 of 32 folders have a Dart test directory (`qwen-3.8-27b-256k` has no app). Test files per folder range from 1 to 47; approximate cases from 1 (`qwen-3.8-27b`) to 915 (`claude-sonnet-5-5`); next are `claude-fable-5` 295 (head state), `claude-opus-5` 236, `Mistral-Large-4` 181, `GLM-5.3-in-Kimi-Code` 139.
- By test file name: matching 26 folders, widget or smoke or flow 28, backup or crypto 24, pagination 21, shopping or units 20, corpus or ontology integrity 19, ranking 14, cook mode 13, meal plan 10. These are the areas where the spec has the most precise statements (rows 105 to 155).
- Pipeline tests: 14 files in 11 folders (Python or shell), including `claude-sonnet-5-5/pipeline/tests/fixtures/dish-spec.json`, the only pipeline fixture found.
- Visual material: golden images only in `claude-fable-5-1/app/test/goldens` (20 files, driven by `golden_test.dart`); screenshot tests in `claude-sonnet-5-5/app/test/visual`; screenshots from the emulator in `deepseek-v4-pro/tool/goldens` (6 files) and `claude-fable-5/docs/store-assets/screenshots`. No `integration_test` directory exists in any folder.
- Other acceptance-like files: `GPT-6.1-Sol/docs/verification.md` (self-reported results), `claude-fable-5/app/android/PDF_IMPORT_TESTS.md`, `claude-fable-5/docs/production-issue-reviews.md`.
- Limits for use as hidden checks:
  - Every test targets that folder's own classes and file layout, so they seed test vectors (inputs and expected outputs for matching, shopping aggregation, backup bytes, pagination thresholds), not portable checks.
  - They were written by the implementing model, so expected values (for example the calorie tolerance) are that model's reading of an under-specified spec.
  - `claude-fable-5`'s tests at head cover features outside the pristine spec (PDF and website import, sharing, personal recipes).
  - All files are public and MIT licensed; reuse needs the notice (1.4). Because the repositories are public and PROMPT.md allows internet, tests copied from them are not secret from an agent that looks (see the contamination ticket named in 2.2).
  - Test counts are line-pattern approximations. `gemini-3-5-flash`, `Gemini-4-Argon`, `GPT-5.6-Terra-Max`, `GPT-5.6-Luna-Max`, `kimi-k2-7`, `sakana-fugu-ultra`, `tencent-hy3`, `qwen-3.8-27b` and `qwen-3.8-27b-128k` have 13 cases or fewer.
- The cli-benchmark README says internal validation reports and run tooling are excluded, so no acceptance suite from the original benchmark is published.

## 6. Not verified

- Which prompt, and which files (design, web, docs), the 26 folders without `prompt.txt` and the 3 cli-benchmark folders actually received.
- Whether any reference implementation builds or passes its own tests; nothing was run.
- That Xcode runs only on macOS (Apple source not read); only a reference README states it.
- Release count of the repositories (tags checked for morphcook only).
- Whether the MIT licence validly covers model-generated code.
- The requirement count is my segmentation; classes are my judgement.

## Appendix A: SPEC.md requirement rows

IDs are used in the text above. Line numbers are for SPEC.md blob `ff0a931f`. Class legend in 3.1 (U rows tagged F or A in 3.2 are not split per row; F rows are IDs 1-3, 5-9, 49, 74, 76, 78-79, 81-82, 84-92, 94-95, 131, 157-169, 172, 174-177, 184-196, 200, 203-210, 212).

| ID | Section | Class | Requirement | SPEC lines |
|---|---|---|---|---|
| 1 | Scope in | U | iOS and Android only, no web target | L54 |
| 2 | Scope in | U | One Flutter codebase | L54 |
| 3 | Scope in | U | No backend | L55 |
| 4 | Scope in | W | No account system | L55 |
| 5 | Scope in | U | No cloud sync | L55 |
| 6 | Scope in | U | No telemetry | L55 |
| 7 | Scope in | U | Recipe corpus bundled under assets/ | L56 |
| 8 | Scope in | U | German and English content present | L58 |
| 9 | Scope in | U | All user-visible text stored as Map<lang, String> (N-language-ready) | L58-60 |
| 10 | Scope in | W | Onboarding in order: language, name, diet and allergies, calorie target and time budget, confirm | L61-62 |
| 11 | Scope in | H | Home feed has a newspaper-style masthead | L63 |
| 12 | Scope in | W | Home feed shows a featured dish | L63 |
| 13 | Scope in | W | Home feed shows grid sections | L63 |
| 14 | Scope in | W | Dish detail has one switcher row per dimension (diet, effort, calorie level) | L64-65 |
| 15 | Scope in | W | Each row collapsed by default, showing only the selected variant | L66 |
| 16 | Scope in | W | Tap on a row reveals the alternatives | L67 |
| 17 | Scope in | W | Switcher defaults come from the profile | L67 |
| 18 | Scope in | W | Unreachable combinations are disabled with a note, not hidden | L68-69 |
| 19 | Scope in | W | Cookbook saves a specific variant (recipe ID), not a dish | L70-71 |
| 20 | Scope in | W | Search by free text | L72 |
| 21 | Scope in | W | Search tag filters | L72 |
| 22 | Scope in | W | Search results respect profile filters | L72 |
| 23 | Scope in | W | Settings: full profile editor | L73 |
| 24 | Scope in | W | Settings: language toggle | L73 |
| 25 | Scope in | W | Settings: adaptation preferences | L73 |
| 26 | Scope in | W | FAQ / Help Center is searchable | L74 |
| 27 | Scope in | W | FAQ has category filters | L74 |
| 28 | Scope in | W | FAQ is linked contextually from UI copy | L74 |
| 29 | Scope in | H | FAQ content covers dietary matching, recipe visibility, features, troubleshooting | L74 |
| 30 | Scope in | U | Shopping list adds same-unit quantities (garlic 2 cloves + 3 cloves = 5 cloves) | L75-76 |
| 31 | Scope in | U | Shopping list converts ml and tbsp for compatible ingredient types | L76-77 |
| 32 | Scope in | U | Shopping list deduplicates | L77 |
| 33 | Scope in | U | Shopping list groups by aisle | L77 |
| 34 | Scope in | W | Shopping Insights reachable from Settings | L78 |
| 35 | Scope in | U | Shopping Insights: variety score (unique ingredient count) | L79 |
| 36 | Scope in | U | Shopping Insights: top added ingredients with frequency counts | L79-80 |
| 37 | Scope in | U | Shopping Insights: seasonal breakdown grouped by month | L80 |
| 38 | Scope in | W | Meal plan weekly grid, Monday to Sunday by breakfast, lunch, dinner | L82 |
| 39 | Scope in | W | Tap a slot to assign a recipe from cookbook or search | L82-83 |
| 40 | Scope in | W | Drag and drop between slots | L83 |
| 41 | Scope in | W | One-tap export of the plan to the shopping list | L83-84 |
| 42 | Scope in | W | No auto-planning and no nutrition rollups | L84 |
| 43 | Scope in | U | Backup writes morphcook-backup.json (human-readable) | L85 |
| 44 | Scope in | W | Backup writes morphcook-backup.json.gz and hands both files to the OS share sheet | L85-86 |
| 45 | Scope in | U | Import auto-detects compression and reads both formats | L87-88 |
| 46 | Scope in | U | Optional password gives AES-256-GCM encryption | L89-91 |
| 47 | Scope in | U | With a password the JSON is encrypted and the GZip file stays unencrypted | L90-92 |
| 48 | Scope in | U | Encrypted backups start with magic bytes 0x45 0x4E 0x43 | L92 |
| 49 | Scope in | U | No OAuth, cloud integration or platform-specific APIs in backup | L93 |
| 50 | Scope in | H | Cook mode is dark and full-bleed | L94 |
| 51 | Scope in | W | Cook mode is step-by-step | L94 |
| 52 | Scope in | W | Cook mode has a per-step timer | L95 |
| 53 | Scope in | W | Cook mode has a servings scaler | L95 |
| 54 | Scope in | W | Cook mode has previous and next | L95 |
| 55 | Scope in | W | Cook mode pause and resume with progress persistence | L95 |
| 56 | Scope in | W | Cook mode completion screen | L95 |
| 57 | Scope in | W | Visual flash alert (coral or teal) when a timer completes | L96 |
| 58 | Scope in | W | Visual alert is controlled by the visualAlertEnabled setting | L97 |
| 59 | Scope in | W | Visual alert respects reduceMotion | L98 |
| 60 | Scope in | W | Single tap on step content advances with haptic feedback | L98-99 |
| 61 | Scope in | U | Quick-tap is opt-in through OneHandedCookModeController.quickNextTapEnabled | L99-100 |
| 62 | Scope in | U | Quick-tap has a 300 ms debounce | L100-101 |
| 63 | Scope in | W | Quick-tap respects reduceMotion | L101 |
| 64 | Scope in | U | Calorie target is a hard profile filter | L102 |
| 65 | Scope in | W | Per-dish switch overrides the calorie target | L102-103 |
| 66 | Scope in | W | Class avoidance checkboxes (dairy, nuts, shellfish) | L105 |
| 67 | Scope in | W | Specific avoidance typeahead backed by the ingredient dictionary | L106 |
| 68 | Scope in | U | Class and specific avoidance combine, any match excludes | L107-108 |
| 69 | Scope in | H | Typography: Playfair Display italic, JetBrains Mono, Caveat | L109 |
| 70 | Scope in | H | Paper grain | L109-110 |
| 71 | Scope in | H | Striped SVG placeholders with captions | L110 |
| 72 | Scope in | H | Polaroid-style cards with slight rotation | L111 |
| 73 | Scope out | W | One profile per install (no multi-profile) | L119 |
| 74 | Scope out | U | No over-the-air content updates | L120 |
| 75 | Scope out | H | No real photos, striped placeholders only | L121 |
| 76 | Scope out | U | No social video integration | L122 |
| 77 | Scope out | W | No paywall, nothing gated | L126-127 |
| 78 | Scope out | U | No LLM calls from the app | L128 |
| 79 | Architecture | U | No runtime network calls beyond store and legal URLs | L137-138 |
| 80 | Architecture | H | Pixel-identical rendering on both platforms | L139-140 |
| 81 | Architecture | U | google_fonts used for the three typefaces | L141 |
| 82 | Architecture | U | Fonts bundled, not fetched at runtime | L142 |
| 83 | Architecture | W | Variant switch animates with highlight flash on changed ingredients | L143-144 |
| 84 | Architecture | U | State via ValueNotifier, Provider or Riverpod, no Redux or BLoC | L145-146 |
| 85 | Data assets | U | assets/partition-manifest.json with partitions, cross-references, loading strategy, version | L153 |
| 86 | Data assets | U | assets/core-recipes.json (top 80 percent of recipes) | L155 |
| 87 | Data assets | U | assets/extended-recipes.json (remaining 20 percent) | L156 |
| 88 | Data assets | U | cuisine-italian, cuisine-asian, cuisine-middle-eastern partitions | L157-158 |
| 89 | Data assets | U | assets/dishes.json fields incl. partition_id, secondary_partitions, cuisine_tags, frequency_tier | L159-162 |
| 90 | Data assets | U | assets/ontology.json (contains-flags, avoid-flags, compound flags, attributes) | L163-164 |
| 91 | Data assets | U | assets/ingredients.json hierarchical tree | L165-167 |
| 92 | Data assets | U | assets/ingredient-guide.json bilingual with description, usage, storage, where to find | L168-171 |
| 93 | Data assets | W | "Learn more" button in recipe ingredient lists opens the guide | L171 |
| 94 | Local state | U | shared_preferences for profile and small flags | L175 |
| 95 | Local state | U | Hive or sqflite for saved, history, meal plan | L176-177 |
| 96 | Local state | U | Profile fields name, lang | L179 |
| 97 | Local state | U | Profile field avoid_flags | L180 |
| 98 | Local state | U | Profile field avoid_ingredients | L181 |
| 99 | Local state | U | Profile field required_attributes | L182 |
| 100 | Local state | U | Profile field max_time_minutes | L183 |
| 101 | Local state | U | Profile field calorie_target | L184 |
| 102 | Local state | U | Profile field preferred_effort easy/medium/hard | L185 |
| 103 | Local state | U | Profile field show_variant_tags | L186 |
| 104 | Local state | U | Profile field reduceMotion (null uses system setting) | L187 |
| 105 | Matching | U | contains and avoid_flags do not intersect | L192 |
| 106 | Matching | U | avoid_ingredients and recipe ingredient_ids do not intersect | L193 |
| 107 | Matching | U | required_attributes are a subset of recipe attributes | L194 |
| 108 | Matching | U | time_minutes at most max_time_minutes | L195 |
| 109 | Matching | U | Calories within tolerance of target (tolerance undefined in the spec) | L196 |
| 110 | Matching | U | Tie-break 1: match_count(required_attributes) | L200-201 |
| 111 | Matching | U | Tie-break 2: effort_match | L200-201 |
| 112 | Matching | U | Tie-break 3: time_closeness | L200-201 |
| 113 | Matching | U | Tie-break 4: calorie_closeness | L200-201 |
| 114 | Ranking | U | Morning 05:00 to 11:00: breakfast +200 | L207 |
| 115 | Ranking | U | Evening 17:00 to 21:00: dinner +90 | L208 |
| 116 | Ranking | U | Weekend: medium and hard effort +90 | L209 |
| 117 | Ranking | U | Not cooked in 30 or more days: +50 | L215 |
| 118 | Ranking | U | Recently or never cooked: no bonus | L216 |
| 119 | Ranking | U | Bonuses apply after the base ranking (base score undefined) | L218 |
| 120 | Search | U | Bundled search index generated at build time | L222 |
| 121 | Search | W | Partition-based chunk loading with on-demand partition fetching | L223 |
| 122 | Search | U | Tokenizes title, tags, ingredient names per language | L224 |
| 123 | Search | U | Profile filters applied after matching | L225 |
| 124 | Search | U | Cursor-based pagination, 20 per page, infinite scroll with prefetch | L226 |
| 125 | Pagination | U | Search: cursor, 20 per page, prefetch 10, max 50 | L234 |
| 126 | Pagination | U | Cookbook: offset, 30 per page, prefetch 10, max 50 | L235 |
| 127 | Pagination | U | History: time-based, 7 weeks, prefetch 1 week, max 50 | L236 |
| 128 | Pagination | U | Meal plan: weekly, 1 week, prefetch 0, max 4 weeks | L237 |
| 129 | Pagination | W | Never more than 50 items rendered, off-screen items disposed | L248 |
| 130 | Pagination | U | Prefetch when within the threshold of the end | L249 |
| 131 | Pagination | U | Paginated lists use ListView.builder with unknown itemCount | L250 |
| 132 | Pagination | U | PaginationController is a ChangeNotifier | L254 |
| 133 | Pagination | U | PaginationController.loadMore() | L255 |
| 134 | Pagination | U | PaginationController.refresh() | L256 |
| 135 | Pagination | U | PaginationController.reset() | L257 |
| 136 | Pagination | U | PaginationController.shouldLoadMore(index) | L258 |
| 137 | Pagination | W | Loading, error, empty states per view | L260 |
| 138 | Pagination | W | Skeleton loaders during fetches | L260 |
| 139 | Backup | U | schema_version 1 | L266 |
| 140 | Backup | U | exported_at | L267 |
| 141 | Backup | U | profile | L268 |
| 142 | Backup | U | saved (recipe IDs) | L269 |
| 143 | Backup | U | meal_plan keyed by ISO week and slot | L270 |
| 144 | Backup | U | history | L271 |
| 145 | Backup | U | content_requests: zero-result queries logged locally and exportable | L272, L276 |
| 146 | Backup | U | PBKDF2 with 10,000 iterations and SHA-256 | L283 |
| 147 | Backup | U | Unique salt and IV per encryption | L283-284 |
| 148 | Backup | U | Import checks ENC magic bytes first, then GZip 0x1f 0x8b | L286-287 |
| 149 | Backup | U | Encrypted file raises DecryptionException with a reason; caller prompts for password | L287-289 |
| 150 | Backup | U | Error text: wrong password | L290 |
| 151 | Backup | U | Error text: corrupted data | L290-291 |
| 152 | Backup | U | Error text: invalid format | L291 |
| 153 | Backup | U | Import validates schema_version | L292 |
| 154 | Backup | U | Import merges or replaces by user choice | L292 |
| 155 | Backup | U | Import never touches the bundled corpus | L292 |
| 156 | Ontology | U | Extending the ontology needs no schema change or migration | L300-302 |
| 157 | Ontology | U | Contains-flags taxonomy (about 25 named plus "...") | L307-311 |
| 158 | Ontology | U | Compound avoid-flag vegan | L313 |
| 159 | Ontology | U | Compound avoid-flag vegetarian | L314 |
| 160 | Ontology | U | Compound avoid-flag pescatarian | L315 |
| 161 | Ontology | U | Compound avoid-flag halal | L316 |
| 162 | Ontology | U | Compound avoid-flag kosher | L317 |
| 163 | Ontology | U | Compound avoid-flag low-fodmap | L318 |
| 164 | Ontology | U | Compound avoid-flag sugar-free | L319 |
| 165 | Ontology | U | Compound avoid-flag lactose-free | L320 |
| 166 | Ontology | U | Attribute effort easy/medium/hard | L322 |
| 167 | Ontology | U | Attribute time_bucket | L323 |
| 168 | Ontology | U | Attribute calorie_bucket | L324 |
| 169 | Ontology | U | Attribute technique (14 tags) | L325 |
| 170 | Ontology | U | Specific avoidance of a parent excludes all descendants | L329-330 |
| 171 | Ontology | W | Typeahead searches leaves and parents, any level selectable | L349 |
| 172 | Ontology | U | UI copy never claims halal-certified or kosher-certified | L354-356 |
| 173 | Ontology | W | Settings screen documents this near the halal and kosher toggles | L356-357 |
| 174 | Pipeline | U | Pipeline runs on the maintainer machine, not on user devices | L363 |
| 175 | Pipeline | U | Pipeline output is JSON committed to assets/recipes.json | L363-364 |
| 176 | Pipeline | U | Five agents, each a separate prompt with a configurable model | L369-370 |
| 177 | Pipeline | U | --agent <model> flag, no hardcoded cheap or premium tier | L370-371 |
| 178 | Pipeline | N | Stage 1 Generator proposes recipe JSON for one variant | L378 |
| 179 | Pipeline | N | Stage 2 Flag-verifier rejects contradictions (vegan plus honey) | L383-384 |
| 180 | Pipeline | N | Verifier feedback loops back to generator, up to N retries | L385 |
| 181 | Pipeline | N | Stage 3 Nutrition-calculator per-serving macros | L388-389 |
| 182 | Pipeline | N | Stage 4 Copy-editor, tumblr voice, DE and EN consistency | L393-394 |
| 183 | Pipeline | N | Stage 5 Final reviewer signs off or bounces with feedback | L398-399 |
| 184 | Pipeline | U | pipeline.sh flag --dish | L409 |
| 185 | Pipeline | U | pipeline.sh flag --variants | L410 |
| 186 | Pipeline | U | pipeline.sh flag --agent | L411 |
| 187 | Pipeline | U | pipeline.sh flag --agent-verifier | L412 |
| 188 | Pipeline | U | pipeline.sh flag --agent-nutrition | L413 |
| 189 | Pipeline | U | pipeline.sh flag --max-retries | L414 |
| 190 | Pipeline | U | pipeline.sh flag --dry-run | L415 |
| 191 | Pipeline | U | Per-stage agents default to the primary --agent | L418-419 |
| 192 | Pipeline | U | Quality gate: JSON schema validation | L423 |
| 193 | Pipeline | U | Quality gate: ontology validation | L424 |
| 194 | Pipeline | U | Quality gate: contains-flags cover flags derivable from ingredients | L425 |
| 195 | Pipeline | U | Quality gate: duplicate detection against sibling variants | L426-427 |
| 196 | Pipeline | U | Quality gate: script outputs a sample of N recipes for human spot-check | L428-429 |
| 197 | Variant UX | W | Switching one dimension narrows combos; disabled note ("no vegan x keto version yet") | L456-457 |
| 198 | Variant UX | W | Switching is in place, ingredients morph-animate (highlight flash and fade) | L457-459 |
| 199 | Variant UX | H | Method text re-renders smoothly | L459 |
| 200 | Branding | U | Product name MorphCook | L465 |
| 201 | Branding | H | Prototype look kept verbatim (prototype not supplied with the spec) | L467-470 |
| 202 | Branding | H | Wordmark swap only, no logo or colour variants | L471-472 |
| 203 | Layout | U | SPEC.md and README.md at repository root | L480-481 |
| 204 | Layout | U | No LICENSE file added (spec says "do not add yet") | L482 |
| 205 | Layout | U | app/ with lib/, assets/ (recipes.json, dishes.json, ontology.json, ingredients.json, faqs.json), pubspec.yaml, test/ | L483-492 |
| 206 | Layout | U | Flutter tests include the matching algorithm | L492 |
| 207 | Layout | U | pipeline/ with pipeline.sh | L493-494 |
| 208 | Layout | U | pipeline/agents/ with generator, flag-verifier, nutrition, copy-editor, reviewer prompts | L495-500 |
| 209 | Layout | U | pipeline/schemas/ for recipe, dish, ontology | L501 |
| 210 | Layout | U | pipeline/tests/ | L502 |
| 211 | Layout | H | design/ and web/ are visual references, not codebase | L503-504 |
| 212 | Layout | U | faqs.json holds bilingual FAQ entries | L490 |

## Appendix B: Folder inventory

Spec text: P pristine, L lattice wording, F Fable 5 head. Layout: `app/` means the Flutter project is under `app/`, root means at the folder root. Test files are `*_test.dart` under `test/`; cases are the approximate line-pattern count; pipeline tests are Python or shell files under `pipeline/` with test in the name. Source: files at commit `d314a20dbc`.

| Folder | Spec | Layout | Dart constraint | Test files | Cases (approx) | Pipeline tests | Prompt file |
|---|---|---|---|---|---|---|---|
| claude-fable-5 | F | app/ | `^3.10.0` | 29 | 295 | run_tests.sh | none |
| claude-fable-5-1 | P | app/ | `^3.11.0` | 13 | 90 | test_validate_corpus.py (7) | prompt.txt |
| claude-opus-4-7 | P | app/ | `>=3.3.0 <4.0.0` | 6 | 29 | none | none |
| claude-opus-4-8 | P | app/ | `^3.10.1` | 8 | 63 | none | none |
| claude-opus-5 | P | app/ | `^3.10.1` | 11 | 236 | test_pipeline.py (49) | prompt.txt |
| claude-opus-5-5 | P | app/ | `^3.11.5` | 8 | 109 | test_pipeline.py (8) | none |
| claude-sonnet-5-5 | P | app/ | `^3.11.5` | 47 | 915 | 3 shell scripts, 1 fixture | none |
| deepseek-v4-flash | P | app/ | `^3.10.1` | 9 | 73 | none | none |
| deepseek-v4-pro | P | root | `^3.11.5` | 11 | 113 | none | none |
| gemini-3-5-flash | P | app/ | `^3.10.1` | 3 | 12 | none | none |
| Gemini-3.7-Flash | P | root | `^3.11.5` | 4 | 21 | none | none |
| Gemini-4-Argon | P | root and app/ | `^3.11.5` | 3 | 13 | test_pipeline.sh | none |
| glm-5-2 | L | root | `^3.10.1` | 3 | 21 | none | none |
| GLM-5.3 | P | app/ | `>=3.3.0 <4.0.0` | 10 | 82 | none | none |
| GLM-5.3-in-Kimi-Code | P | app/ | `^3.11.0` | 13 | 139 | test_pipeline.py | none |
| GPT-5.6-Luna-Max | P | app/ | `>=3.8.0 <4.0.0` | 2 | 6 | none | none |
| GPT-5.6-Sol-Max | P | app/ | `^3.10.1` | 8 | 32 | none | none |
| GPT-5.6-Sol-Ultra | P | app/ | `^3.10.1` | 19 | 98 | none | none |
| GPT-5.6-Terra-Max | P | app/ | `^3.10.1` | 2 | 5 | none | none |
| GPT-6.1-Sol | P | app/ | `>=3.8.0 <4.0.0` | 7 | 65 | test_pipeline.py (11) | none |
| GPT-6-Astra | P | app/ | `>=3.10.0 <4.0.0` | 12 | 75 | test_corpus.py, test_runner.py (16) | prompt.txt |
| Grok-4.6 | P | app/ | `^3.11.5` | 13 | 54 | none | none |
| kimi-k2-7 | L | app/ | `^3.10.1` | 2 | 6 | none | none |
| kimi-k3 | L | app/ | `^3.10.1` | 8 | 59 | none | none |
| minimax-m3 | P | app/ | `^3.10.1` | 7 | 52 | none | none |
| Mistral-Large-4 | P | app/ | `^3.5.0` | 10 | 181 | test_validate_corpus.py (17) | none |
| qwen-3.8-27b | P | app/ | `^3.11.5` | 1 | 1 | none | prompt.txt |
| qwen-3.8-27b-128k | P | app/ | `^3.10.0` | 2 | 8 | none | prompt.txt |
| qwen-3.8-27b-256k | P | none (no app) | none | 0 | 0 | none | prompt.txt |
| qwen-3.8-max | P | app/ | `^3.10.0` | 9 | 90 | Python test file (4) | none |
| sakana-fugu-ultra | no SPEC copy | root | `^3.10.1` | 1 | 6 | none | none |
| tencent-hy3 | P | root | `>=3.0.0 <4.0.0` | 2 | 6 | none | none |
