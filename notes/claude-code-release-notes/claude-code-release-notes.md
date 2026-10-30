# Claude Code release notes and models since BenchKeeper's pinned schemas

Research for issue #381 (parent #372). Read on 2026-10-27. Scope is Claude Code and the Claude model line-up; the Codex schema pin (`app/src/settings/codex-config.schema.json`, tag rust-v0.164.0) was not reviewed.

## Question

What changed in Claude Code (release notes, changelog) and in the Claude model line-up after the schemas and pins that BenchKeeper ships were taken? Which settings keys, hook events, deprecations, renames, removals and model ids, each with an official URL, a date or version, and the BenchKeeper file that must change or would gain.

## Short answer

Almost nothing is new after the pins, because the pins are two to five days old.

- Settings pins are dated 2026-10-25 (`app/src/settings/sources.json`). Only Claude Code 2.1.311 (2026-10-26) is newer. It changes no settings key, hook event or model id. One real file effect: model names drop the `[1m]` suffix where it has no effect, which the advisor-rank check at `app/src/settings.mjs:203` does not handle.
- The plugin, skills CLI and model-alias pins came in with commit a5fdd71 on 2026-10-22. Claude Code 2.1.309 (same day), 2.1.310 and 2.1.311 followed. No new model id appeared after any pin: the newest, Haiku 5.5, shipped on 2026-10-07.
- Re-fetching the pinned sources today shows no drift: the Claude Code settings key table (250 rows, one reworded description), the SchemaStore schema (zero structural differences), the advisor rank table, and all 18 Claude Code quotes in `couplings.json` still hold.
- The useful findings are gaps that predate the pins: Haiku 5.5 is missing from the per-model effort step, the `manual` permission mode alias is rejected by the catalog, the `StopFailure` hook records 3 of 12 documented error types, `[1m]` model ids skip the advisor check, and the docs table marks six settings keys as deprecated or removed that BenchKeeper does not flag.
- The only deprecation that touches a default BenchKeeper writes: `claude-sonnet-4-5-20250929` retires 2026-11-30, and on Microsoft Foundry the `sonnet` alias still resolves to it.

## What BenchKeeper pinned, and when

| Pin | Value | Taken | Where |
|---|---|---|---|
| SchemaStore Claude Code schema | 142 top-level keys | 2026-10-25 | `app/src/settings/sources.json`, `claude-code-settings.schema.json` |
| Settings index table (docs) | 247 keys | 2026-10-25 | `claude-settings-keys.json` |
| Docs quotes for coupling rules | 18 Claude Code quotes | 2026-10-25, scrub and read-deny passages 2026-10-26 | `app/test/fixtures/settings-docs.json`, `couplings.json` |
| Advisor rank table | haiku-4-5 up to fable-5-1 | 2026-10-25 (commit e1d9c19) | `couplings.json:4` |
| Plugin refs | ponytail v5.3.2, mattpocock-skills v1.3.1 | 2026-10-22 (commit a5fdd71) | `app/src/steps/global.mjs:38-39` |
| Skills CLI | 1.7.2 | 2026-10-22 | `global.mjs:17`, `PIN_DATES` at `global.mjs:31-36` |
| Model names | aliases `opus` (advisor), `sonnet` (subagents); ids `claude-opus-5-5`, `claude-sonnet-5-5` | 2026-10-22 | `global.mjs:81,85,87` |
| Evals | no model name; `--model` is passed through from the caller | n/a | `app/src/eval.mjs:38`, `plugins/benchkeeper/evals/*.json` |

Newest repository entry when read: setup-v6.23 (2026-10-27) in `CHANGELOG.md`.

## Deprecations and removals (first)

| Change | Date or version | Official URL | BenchKeeper file | Effort |
|---|---|---|---|---|
| `claude-sonnet-4-5-20250929` deprecated, retires 2026-11-30, replacement `claude-sonnet-5-5`. Dates apply to Anthropic-operated platforms including Microsoft Foundry, where the `sonnet` alias still resolves to Sonnet 4.5 (Anthropic API: Sonnet 5.5; Claude Platform on AWS: 4.6; Bedrock and Google Cloud Agent Platform: 4.5, own schedules) | Announced 2026-09-30 | https://platform.claude.com/docs/en/about-claude/model-deprecations ; https://code.claude.com/docs/en/model-config | `global.mjs:85` writes `CLAUDE_CODE_SUBAGENT_MODEL=sonnet`; no file names the retired id. Would gain a Foundry note in the settings sentence for that key | S |
| `claude-haiku-4-5-20251001`: still Active, "not sooner than 2026-10-15" has passed, no retirement date announced | status read 2026-10-27 | https://platform.claude.com/docs/en/about-claude/model-deprecations | `couplings.json:4` ranks `haiku-4-5` (ranking only, no call). Watch, no change | none |
| `claude-opus-4-5-20251101`: not sooner than 2026-11-24. Opus 4.1, Opus 4, Sonnet 4: retired in 2026 | same page | same page | not referenced | none |
| `temperature`, `top_p`, `top_k` removed in API version 2026-10-21 (400 error) | 2026-10-21 | https://platform.claude.com/docs/en/about-claude/model-deprecations ; https://platform.claude.com/docs/en/release-notes/overview | BenchKeeper makes no Messages API call; none | none |
| Settings keys marked deprecated or removed in the docs table: `permissionExplainerEnabled` (removed 2.1.257), `taskOutputMaxChars` (removed 2.1.277 with the `TaskOutput` tool), `teammateDefaultModel` (removed 2.1.234), `keybindingFlavor` (deprecated, no effect), `disableArtifact` (use `enableArtifact`), `includeCoAuthoredBy` (use `attribution`) | 2.1.234 to 2.1.277 | https://code.claude.com/docs/en/settings-reference | Only `includeCoAuthoredBy` is handled (`couplings.json:36-38`, `catalog.json:50`). Advanced list in `app/src/settings.mjs` shows the other five without a note; a generic note from the first word of each description in `claude-settings-keys.json` would cover them | S |
| `claude project purge` renamed `claude purge`, old name still works | 2.1.288 | https://code.claude.com/docs/en/changelog | not referenced | none |
| `--sandbox` and `--no-sandbox` removed from `claude remote-control` (exit with an error) | 2.1.300 | https://code.claude.com/docs/en/changelog | not referenced | none |
| `bold` deprecated in favor of `weight` in a mod's `Text` | 2.1.299 | https://code.claude.com/docs/en/changelog | BenchKeeper ships no mod | none |

## After the pins

Cut-off per pin: settings and advisor ranks 2026-10-25, plugin refs and model aliases 2026-10-22. Versions and dates are from https://code.claude.com/docs/en/changelog (2.1.309: 2026-10-22, 2.1.310: 2026-10-23, 2.1.311: 2026-10-26; the order of releases within 2026-10-22 was not checked).

| Change | Version or date | Official URL | BenchKeeper file | Effort |
|---|---|---|---|---|
| Model names and ids drop the `[1m]` suffix and its label where the suffix has no effect; the suffix is still accepted (for example `claude-opus-4-6[1m]` is documented) | 2.1.311, 2026-10-26 | https://code.claude.com/docs/en/changelog ; https://code.claude.com/docs/en/model-config | Must change: `rankOf` at `app/src/settings.mjs:203` matches `claude-<family>-<n>[-<n>][-<date>]` and returns null for a suffixed id, so the advisor-below-main rule is skipped silently. Strip `[1m]` before matching and add a test in `app/test/settings.test.mjs` | S |
| Settings reference wording for `idleCompaction` changed ("while your terminal session is idle" became "that you've stepped away from"); key, topic and scope unchanged | between 2026-10-25 and 2026-10-27, exact date unverified | https://code.claude.com/docs/en/settings-reference | `claude-settings-keys.json` (next re-pin) | S |
| `skills` CLI 1.7.3 and 1.7.4 published 2026-10-19; 1.7.4 is now past the 7-day hold, so it can be pinned | 2026-10-19 (eligible 2026-10-26) | https://www.npmjs.com/package/skills (registry document https://registry.npmjs.org/skills) | `global.mjs:17` (`SKILLS_CLI`), `global.mjs:32` (`PIN_DATES`); content of the releases not read | S |
| Newer commits than the pinned skill-source commits (`vercel-labs/skills` 13e4063, `stablyai/orca` 5df4fef); the head of `main` is not the target, the newest commit at least 7 days old is | read 2026-10-27 | https://github.com/vercel-labs/skills ; https://github.com/stablyai/orca | `global.mjs:25-28` and `PIN_DATES`. Which commit qualifies was not determined | S |
| Plugin tags: ponytail v5.3.2 and mattpocock-skills v1.3.1 are still the newest tags and releases | read 2026-10-27 | https://github.com/DietrichGebert/ponytail/releases ; https://github.com/mattpocock/skills/releases | `global.mjs:38-39`: no change | none |
| New model ids after the pins | none | https://platform.claude.com/docs/en/about-claude/models/overview | `advisorRanks` at `couplings.json:4` already lists every id on the page (haiku-4-5 to fable-5-1) | none |
| 2.1.309 to 2.1.311 behavior changes without BenchKeeper impact: `sed -i` gets the standard Bash prompt; `ultrathink` runs at xhigh effort on the 5.5 models and Fable 5.1; `DISABLE_COMPACT` in settings can only turn compaction off; stream-json output escapes control characters as `\uXXXX` (parsed values unchanged, `eval.mjs:38` parses JSON); Bedrock, Mantle, Vertex and Foundry load model settings from a signed file on a Claude download host (`CLAUDE_CODE_MODEL_CATALOG=off` stops it); Monitor tool on third-party providers | 2.1.309 to 2.1.311 | https://code.claude.com/docs/en/changelog | none. The model-catalog fetch could matter to users behind a network allowlist; no BenchKeeper doc covers allowlists | none |

## Before the pins, not yet reflected in BenchKeeper

These are older than every pin. They are listed because the pins were taken from sources that already described them.

| Change | Version or date | Official URL | BenchKeeper file | Effort |
|---|---|---|---|---|
| Opus 5.5 and models released after it ignore a top-level `effortLevel` in the user file and take a per-model level under `modelSettings`. Haiku 5.5 (2.1.293, 2026-10-07; default effort medium) is later than Opus 5.5 (2.1.280, 2026-09-22) and is not in `EFFORT_MODELS`. The step title names only Opus 5.5. The doc names Opus 5.5 explicitly and says "models released after it"; applying that to Haiku 5.5 is an inference | 2.1.293 | https://code.claude.com/docs/en/model-config ; https://platform.claude.com/docs/en/about-claude/models/overview | `global.mjs:87` (`EFFORT_MODELS`) and `global.mjs:310` (step title and edit). Add `claude-haiku-5-5` and update the title | S |
| `manual` is an accepted alias of `default` for `permissions.defaultMode` and `--permission-mode`; the schema enum has it, the catalog list does not, so `benchkeeper settings set permissions.defaultMode manual` fails validation | 2.1.200, 2026-07-03 | https://code.claude.com/docs/en/settings-reference#permissions-defaultmode ; https://code.claude.com/docs/en/permission-modes | `app/src/settings/catalog.json:12` (`values`) | S |
| `StopFailure` hook input documents 12 error types: `rate_limit`, `overloaded`, `authentication_failed`, `oauth_org_not_allowed`, `account_on_hold`, `billing_error`, `invalid_request`, `model_not_found`, `server_error`, `max_output_tokens`, `cloud_credential_error`, `unknown`. BenchKeeper records 3. Date of each addition unverified (the event itself: 2.1.78) | event 2.1.78; types undated | https://code.claude.com/docs/en/hooks | `app/src/usage-hook.mjs:9` (`FAILURES`, also the hook matcher at `usage.mjs:104`) and the finding texts at `usage.mjs:70-72`. `account_on_hold` and `oauth_org_not_allowed` fit the Accounts notices | S |
| `PreModelSwitch` and `PostModelSwitch` hook events (release of 2026-08-28) and the `onFailure` field (`"continue"` or `"block"`) on command and HTTP hooks (2.1.295, 2026-10-08) are in the hooks docs but not in the SchemaStore schema, whose `hooks` object has `additionalProperties: false`. BenchKeeper does not validate whole documents against it: the schema types keys and the unknown-key check is top level only (`settings.mjs:299-307`), and the Extensions view lists hook events generically (`app/src/extensions.mjs:40`). No false flag results | 2026-08-28 release, 2.1.295 | https://code.claude.com/docs/en/hooks | none. SchemaStore is a community schema, so cite the docs page for these | none |
| Sandbox and compaction keys the docs table has and the schema lacks: `sandbox.allowNestedUserNamespaces` (2.1.305), `allowedProviders` (2.1.285), `idleCompaction` (2.1.299) and `autoCompactWindow` (version of first appearance unverified). The table pin has them; the schema pin does not, as `sources.json` already notes | 2.1.285 to 2.1.305 | https://code.claude.com/docs/en/settings-reference | none (the Advanced list merges both sources, `settings.mjs:327`) | none |
| `claude plugin eval` (2.1.269, `--disallow-tools` added 2.1.299) and `/skill-doctor` (2.1.261) overlap `benchkeeper eval` (`app/src/eval.mjs`) and the unused-skills insight. The repository already cites them in `evaluations/` and `web/src/data/facts.json`; whether `eval.mjs` should reuse the native runner is a design question, not drift | 2.1.261, 2.1.269 | https://code.claude.com/docs/en/plugin-evals | `app/src/eval.mjs` (would gain, no change forced) | M |
| Sessions started with `claude -p` and no permission mode start in Manual since 2.1.302 (auto before, where feature flags were not fetched). `eval.mjs:38` passes `--permission-mode plan` and `advise.mjs:54` passes `--restricted`, so neither depends on the default | 2.1.302 | https://code.claude.com/docs/en/permission-modes | none | none |
| Sonnet 5.5 prompt-cache reads cost $0.10 per million tokens (was $0.20). BenchKeeper reads `totalCostUSD` from Claude Code's own transcript entry (`app/src/sessions.mjs:50`) and keeps no price table, so only the comparability of old and new session costs changes | 2026-10-07 (Claude Code 2.1.296) | https://platform.claude.com/docs/en/release-notes/overview | none | none |

## Model line-up read on 2026-10-27

Source: https://platform.claude.com/docs/en/about-claude/models/overview

| Model | API id | Added to Claude Code | Retirement |
|---|---|---|---|
| Fable 5.1 | `claude-fable-5-1` | 2.1.257 | not sooner than 2027-09-01 |
| Opus 5.5 | `claude-opus-5-5` | 2.1.280 | not sooner than 2027-09-22 |
| Sonnet 5.5 | `claude-sonnet-5-5` | 2.1.284 | not sooner than 2027-09-28 |
| Haiku 5.5 | `claude-haiku-5-5` | 2.1.293 | not sooner than 2027-10-07 |

All four have a 1M token context window and 128K max output. The advisor page (https://code.claude.com/docs/en/advisor) ranks the same ids as `couplings.json:4`, and states Haiku 5.5 as main model or advisor needs 2.1.293. The deprecations page also lists `claude-mythos-5` and `claude-mythos-5-1` (Active); neither Claude Code's model-config page nor the advisor page mentions them, so `advisorRanks` correctly omits them.

## Checked and unchanged

- The 18 Claude Code quotes in `couplings.json` were searched in the live Markdown pages (advisor, remote-control, env-vars, settings-reference, permissions) with quote and apostrophe normalization: 18 found, 0 missing. `npm test` checks the frozen fixture only, so this is the check that catches a rewritten page.
- SchemaStore schema (https://json.schemastore.org/claude-code-settings.json): 142 properties, permission rule pattern equal, zero structural differences after ignoring descriptions. The 14 properties that differ as text differ by the repository's own rewrites (em dash, home path).
- Settings table: 247 keys pinned, 247 key rows today (3 further rows the parser reads are from a sandbox path table). No key added or removed.
- Advisor rank table: equal to `advisorRanks`.
- Plugin CLI flags BenchKeeper uses are documented in https://code.claude.com/docs/en/plugins/cli-reference: `plugin install`, `uninstall`, `list --json`, `marketplace list --json`, `marketplace add --sparse`, `--scope`. No rename of `enabledPlugins` or of marketplace commands in 2.1.284 to 2.1.311. "Mods" (2.1.287) are plugins that register event handlers.
- Flags used by `eval.mjs:38` and `advise.mjs:54`: `-p`, `--output-format`, `--verbose`, `--permission-mode`, `--strict-mcp-config`, `--no-session-persistence`, `--model`, `--restricted`, `--tools` are in https://code.claude.com/docs/en/cli-reference.
- Status line input fields read by `usage-hook.mjs` (`rate_limits.five_hour` and `seven_day`, `used_percentage`, `resets_at`) are unchanged in https://code.claude.com/docs/en/statusline; 2.1.284 only added gateway spend fields.

## Unverified

- Changelog dates between 2.1.283 and 2.1.311 come from the docs changelog page. The GitHub `CHANGELOG.md` has no dates; the two agree on bullets where compared.
- The release order inside 2026-10-22 (2.1.308 and 2.1.309) against the a5fdd71 commit time.
- Contents of `skills` 1.7.3 and 1.7.4, and which commit of `vercel-labs/skills` and `stablyai/orca` is the newest one at least 7 days old.
- When each extra `StopFailure` error type was added.
- Whether the Haiku 5.5 effort behavior matches the Opus 5.5 statement (inferred from "models released after it").
- Whether the transcript format change in 2.1.300 (each API request's system prompt, tools and parameters now recorded) affects the sessions parser or its size limits. Transcript format is not documented, and no transcript was opened.
- Whether `claude plugin install` without a terminal is refused for any of the three pinned plugins (it is refused only when a marketplace declares an install command, per https://code.claude.com/docs/en/plugins/cli-reference); not tested, as nothing was run.
- The Codex side: `codex-config.schema.json` and its pin were not reviewed.

## Method

Primary sources only: the Claude Code docs (Markdown and HTML), its changelog (https://code.claude.com/docs/en/changelog, also https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md), the Claude Platform model, deprecation and release-notes pages, the npm registry document for `skills`, and GitHub tags and commits via the API. The changelog was read for 2.1.284 to 2.1.311 (2026-09-28 to 2026-10-26) and searched for deprecation, removal, rename, settings, hook, plugin and model terms; older entries were searched only for the items above. Pinned files were diffed against fresh copies by script. Nothing was installed or run against a real home folder.
