# Arm inputs: install method, pin and licence for agency-agents, Matt Pocock's skills and plain Claude Code

Answers [Arm inputs: install method, pin and licence for agency-agents, Matt Pocock's skills and plain Claude Code](https://github.com/ESchuderer/BenchKeeper-research/issues/13) for the map [Wayfinder map: benchmark research for BenchKeeper 7.0, MorphCook brief](https://github.com/ESchuderer/BenchKeeper-research/issues/8). Context: [Benchmark: agency-agents arm on mistreevous (Sonnet 5.5, opusplan, Opus 5.5)](https://github.com/ESchuderer/BenchKeeper-research/issues/5). Facts and sources only; no decision is recommended. Date of research: 2026-10-27. Anything not checked against a source is marked "unverified".

## Method

- Cloned read-only into empty scratch folders: `msitarzewski/agency-agents`, `mattpocock/skills`, `ESchuderer/BenchKeeper`. No installer, script or hook of these repositories was run on the host. File counts were computed with a separate script that repeats the installer's selection rule (first line of a file is `---`), not by running the installer.
- Claude Code documentation read at `https://code.claude.com/docs/en/` (pages named per claim).
- Local facts (the plugin cache of the owner's machine, Claude Code 2.1.308) are marked "local observation".

## 1. Claude Code (all arms)

### 1.1 Version and licence

| Item | Value | Source |
|---|---|---|
| npm dist-tags on 2026-10-27 | `stable` = 2.1.308 (published 2026-10-22T04:19:48Z), `latest` = `next` = 2.1.311 (2026-10-26T19:47:57Z) | `https://registry.npmjs.org/@anthropic-ai/claude-code` |
| Installed on the owner's machine | 2.1.308 (`claude --version`), equal to `stable` | local observation |
| Licence | Proprietary: "© Anthropic PBC. All rights reserved. Use is subject to Anthropic's Commercial Terms of Service" | `https://github.com/anthropics/claude-code/blob/main/LICENSE.md` |

### 1.2 Pinning the version

All from `https://code.claude.com/docs/en/setup`:

- Native installer with a version: `curl -fsSL https://claude.ai/install.sh | bash -s 2.1.308`. `claude --version` then prints the exact version. The installer also takes `stable` or `latest`.
- npm: the page shows `npm install -g @anthropic-ai/claude-code` and `@latest` for upgrades. A versioned form `@anthropic-ai/claude-code@2.1.308` is ordinary npm syntax but is not shown on that page (unverified there).
- Releases from 2.1.89 on have a GPG-signed `manifest.json` with SHA256 per platform (`https://downloads.claude.ai/claude-code-releases/<version>/manifest.json`); key fingerprint `31DD DE24 DDFA B679 F42D 7BD2 BAA9 29FF 1A7E CACE`.
- Keeping the pin: `DISABLE_AUTOUPDATER=1` (in the `env` key of settings or the process environment) stops the background check only; `claude update` and `claude install` still work. `DISABLE_UPDATES` blocks all update paths. Managed settings `requiredMinimumVersion` and `requiredMaximumVersion` make Claude Code refuse to start outside a range. `minimumVersion` is a floor for updates only.
- Native installs update themselves in the background by default (same page).

### 1.3 Running headless

Sources: `https://code.claude.com/docs/en/headless`, `https://code.claude.com/docs/en/cli-reference`, `https://code.claude.com/docs/en/model-config`, `https://code.claude.com/docs/en/permission-modes` (linked from the headless page, not read in full).

| Need | Documented form |
|---|---|
| Non-interactive run | `claude -p "<prompt>"`; exit 0 on success, non-zero on failure; `--output-format text\|json\|stream-json` (`stream-json` needs `--verbose`) |
| Fixed model | `--model <alias or full name>`, for example `--model claude-opus-5-5`. Aliases: `sonnet`, `opus`, `haiku`, `fable`, `opusplan` ("uses `opus` during plan mode, then switches to `sonnet` for execution"). On the Anthropic API `opus` resolves to Opus 5.5 and `sonnet` to Sonnet 5.5. Pinning an alias: `ANTHROPIC_DEFAULT_OPUS_MODEL` and siblings. The full name of Sonnet 5.5 is not printed on the pages read; the `claude-opus-5-5` pattern is (so `claude-sonnet-5-5` is inferred, unverified). |
| Fixed effort | `--effort low\|medium\|high\|xhigh\|max` (also `ultracode`); overrides settings for the session and does not persist. Env: `CLAUDE_CODE_EFFORT_LEVEL`. Precedence: explicit choice (env var, `--effort`, `/effort`), then saved settings, then the model default. Defaults are `medium` for Opus 5.5, Sonnet 5.5 and Haiku 5.5. "A top-level `effortLevel` in your user settings file doesn't count for Opus 5.5" (it does count in project, local, managed settings or `--settings`). `max` "isn't accepted as a level" in the `effortLevel` setting or in `modelSettings`; it is a valid value of the flag. Whether the env var takes `max` is not stated (the page says "a level name or `auto`"; unverified). |
| Fixed permission mode | `--permission-mode default\|acceptEdits\|plan\|auto\|dontAsk\|bypassPermissions\|manual`; `--dangerously-skip-permissions` equals `bypassPermissions`. From 2.1.302 a `-p` run with no mode set starts in Manual mode, where a call needing approval is denied. `--permission-prompts none` (2.1.259 or later) denies instead of waiting for a host. `--allowedTools`, `--disallowedTools`, `--tools` shape the tool set. |
| Limits | `--max-turns` and `--max-budget-usd` (print mode only; spend of subagents counts; the cost is a client-side estimate). `--output-format json` returns `total_cost_usd` and a per-model breakdown. |
| Pin the settings seen | `--settings <file-or-json>` overrides the same keys in settings files; `--setting-sources user,project,local` selects which files load. |
| Session records | `--no-session-persistence` disables saving. Without it, transcripts go to `$HOME/.claude/projects/` (as BenchKeeper's `docs/setup.md` states; Claude Code page on transcripts not read). |
| Load content for one session | `--plugin-dir <path or .zip>`, `--plugin-url`, `--agents <json or file>` (file form from 2.1.281), `--mcp-config`, `--strict-mcp-config`, `--disable-slash-commands` |
| Wait for plugins | In `-p` runs marketplaces and plugins install in the background, so a plugin can be missing on the first turn; `CLAUDE_CODE_SYNC_PLUGIN_INSTALL=1` makes the run wait (`https://code.claude.com/docs/en/plugins/org`). |
| See what loaded | `--output-format stream-json --verbose`: the `system/init` event lists `plugins` (name and path), `plugin_errors`, `mcp_servers` and the model. Whether it also lists subagents and skills: unverified (the SDK type page was too long to read in full). |

Points that bear on arm delivery:

1. `--bare` skips hooks, skills, custom commands, subagents, installed plugins, MCP servers, auto memory and CLAUDE.md. In bare mode "Claude Code never reads OAuth credentials or the system keychain"; it needs `ANTHROPIC_API_KEY` or an `apiKeyHelper`, and `CLAUDE_CODE_OAUTH_TOKEN` is not read (headless page, authentication page). Content must then come through `--plugin-dir`, `--agents`, `--settings`. Bare mode also drops the skill list from the system reminders.
2. Without `--bare`, a `-p` run loads everything under `$HOME/.claude` and the working directory like an interactive session, runs project hooks and connects project MCP servers "even in a folder you've never trusted" (no trust dialog in `-p`).
3. `extraKnownMarketplaces` in a repository's `.claude/settings.json` apply in `-p` runs only in a folder already trusted interactively or with `hasTrustDialogAccepted` set in `$HOME/.claude.json` (`plugins/org` page).
4. The official marketplace `claude-plugins-official` registers itself only in an interactive terminal session; "a `-p` run or a terminal attached to a cloud session never registers it" (`plugins/org` page).
5. Subagent model order: per-invocation parameter, then the subagent file's `model` field (`inherit` selects the main model), then `CLAUDE_CODE_SUBAGENT_MODEL`, then the main conversation's model. Subagents inherit the main conversation's permission mode, and in `bypassPermissions`, `acceptEdits` or auto mode the main mode wins over the file (`https://code.claude.com/docs/en/sub-agents`).

### 1.4 Authentication and billing

From `https://code.claude.com/docs/en/authentication`:

- Subscription login is the lowest-ranked credential. Order: cloud-provider variables, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_API_KEY` ("in non-interactive mode (`-p`), the key is always used when present"), `apiKeyHelper`, `CLAUDE_CODE_OAUTH_TOKEN`, profiles, subscription login.
- `claude setup-token` prints a one-year OAuth token for CI that "authenticates with your Claude subscription and requires a Pro, Max, Team, or Enterprise plan" and can make model requests only. It is set as `CLAUDE_CODE_OAUTH_TOKEN`.
- A separate `CLAUDE_CONFIG_DIR` holds its own settings, session history and login; credentials go to `.credentials.json` under that directory on Linux. A fresh directory therefore needs a login or `CLAUDE_CODE_OAUTH_TOKEN`.
- `ANTHROPIC_API_KEY` in the environment switches a run to API billing ("uses the API key once you approve it", always in `-p`).

## 2. Plain Claude Code arm

- Install: nothing beyond section 1. Licence and pin: section 1.1 and 1.2. Network at install: the installer downloads the binary (native installer from `claude.ai`, signed manifest from `downloads.claude.ai`).
- Writes: nothing arm-specific. Paid key: none beyond the subscription.
- What defines "plain" in the documented mechanisms: an empty `$HOME/.claude` (or a fresh `CLAUDE_CONFIG_DIR`) without `agents/`, `rules/`, `skills/`, `CLAUDE.md`, plugins, and settings; or `--bare` (which needs an API key, see 1.3). Which of these the owner picks belongs to later tickets.

## 3. agency-agents

### 3.1 Identity, pin, licence

| Item | Value | Source |
|---|---|---|
| Repository | https://github.com/msitarzewski/agency-agents | |
| Pin named in [Benchmark: agency-agents arm on mistreevous (Sonnet 5.5, opusplan, Opus 5.5)](https://github.com/ESchuderer/BenchKeeper-research/issues/5) | `4e3ac3ca6604c75113f52c695dbddcc7af928b46` (merge of PR 1175; committer date 2026-10-19T11:47:34-05:00; it is the last commit on `main` before 2026-10-23, so "main on 2026-10-22" matches) | `git log` of the clone |
| Newest `main` seen | `b37b5bb33b78f2c1d6567d98e25ca818e3259219` (2026-10-24T19:37:22-05:00), also the pin in BenchKeeper's catalog (`plugins/benchkeeper/library/library.json`, `install.ref`) | clone; BenchKeeper `65d5c14` |
| Tags and releases | none in the clone; BenchKeeper's evaluation says "no release" | `evaluations/workflow-frameworks/agency-agents.md` |
| Licence | MIT, "Copyright (c) 2025 AgentLand Contributors" (`LICENSE`, line 3); GitHub reports MIT | `https://github.com/msitarzewski/agency-agents/blob/main/LICENSE` |
| Difference between the two commits | `scripts/install.sh`, `scripts/lib.sh` and `LICENSE` are byte-identical; agent files: 282 at the pin, 283 at `b37b5bb` (one electrical-engineer agent added) | `diff` of two extracted trees |

### 3.2 Non-interactive install for Claude Code

- Documented command: `./scripts/install.sh --tool claude-code` (`README.md`, `integrations/claude-code/README.md`). `--tool` sets non-interactive mode by itself (`scripts/install.sh`, argument loop); `--no-interactive` is also accepted. A bare call asks questions only when stdin and stdout are a terminal.
- Selection flags: `--division <a,b>`, `--agent <id,...>`, `--agents-file <path>`; mode flags `--link` (symlink instead of copy), `--path <dir>` (single destination), `--dry-run`, `--list`.
- Destination: `$CLAUDE_CONFIG_DIR/agents` if the variable is set (a value ending in `/agents` is used as is), else `$HOME/.claude/agents` (`resolve_dest`, `install_claude_code`).
- Network use: none in `install.sh` and `lib.sh` (searched for `curl`, `wget`, `git clone`, `npm`, `pip`: no hits). The only network step is cloning the repository itself. For `claude-code` the installer does not run `convert.sh` (`ensure_converted` returns early). It needs `bash`, `find`, `awk`, `sed`, `grep` and the committed `integrations/` folder.
- Failure behaviour: an existing file of the same name is overwritten by `cp`; a destination that is a foreign symlink is skipped with a warning and the run still exits 0 (`install_file`, `SKIPPED_LOG`).
- Alternative the README names: `cp engineering/*.md $HOME/.claude/agents/` for one division. The README also advertises a desktop app (agencyagents.app) that installs without scripts; it is not a scriptable path and was not read beyond the README.

### 3.3 Files written (Claude Code)

- Only `*.md` files, copied flat (no subfolders) into the agents folder under their source name, for every `*.md` in the 18 division folders of `divisions.json` and in `strategy/` whose first line is `---` (`install_claude_code`, `is_agent_file`). Result: 282 files at the pin, 283 at `b37b5bb`. Division folders: academic, design, engineering, finance, game-development, gis, healthcare, marketing, paid-media, product, project-management, research, sales, security, spatial-computing, specialized, support, testing.
- File names: mostly `<division>-<slug>.md`; the installer's own comment says 73 of 279 (at its writing) are named `<slug>.md` already (`path_collision_group` comment). No two files share a base name, at the pin and at `b37b5bb` (checked on both trees).
- Frontmatter at `b37b5bb`: every file has `name`, `description`, `color`, `emoji`; 282 have `vibe`; 17 have a `tools:` line (for example `WebFetch, WebSearch, Read, Write, Edit`, no `Bash`); none has `model:`; 4 have `services:` listing outside services, one marked `tier: paid` (Xquik in `marketing/marketing-x-twitter-intelligence-analyst.md`); 7 have `author`. The pin was not scanned for these keys.
- Not written: no `settings.json`, hooks, skills, rules, CLAUDE.md, plugin, MCP configuration, no change to existing files other than same-name overwrite.
- Effect in Claude Code: each subagent's `description` is held in context for delegation; Claude Code warns at startup when the combined descriptions of non-built-in subagents exceed 15,000 tokens (`sub-agents` page). The 282 descriptions at the pin sum to about 62,000 characters, roughly 15,500 tokens at 4 characters per token (a rough estimate, unverified as a token count). The README says the full bodies are about a million tokens (`README.md`, Aider section), our count of all 282 files is 4.04 million characters. Subagents without `model:` follow the order in 1.3 point 5. Files in `$HOME/.claude/agents/` are watched; after the first agent file is created in a new `agents` directory, a restart is needed to load it (`sub-agents` page).
- Whether Claude Code reads agents from under a `CLAUDE_CONFIG_DIR` other than `$HOME/.claude`: the installer assumes it (code comment in `resolve_dest` on `CLAUDE_CONFIG_DIR`); the Claude Code subagent page does not say (unverified).

### 3.4 Paid key or account

None for install or for the Claude Code files (the `--bare` caveat in 1.3 and 1.4 applies to every arm). Four agents name outside services they would call when used; one is paid (3.3). Not needed unless those agents run.

## 4. Matt Pocock's skills

### 4.1 Identity, pin, licence

| Item | Value | Source |
|---|---|---|
| Repository | https://github.com/mattpocock/skills (plugin `mattpocock-skills`) | |
| Licence | MIT, "Copyright (c) 2026 Matt Pocock"; `plugin.json` and `package.json` say MIT | `LICENSE` |
| Version | 1.3.1 | `.claude-plugin/plugin.json` |
| Tag `v1.3.1` | `24fe0ef7737efae15c87225755e9f6f5965e4888` (2026-10-04T13:48:05+01:00, merge of PR 1160) | clone |
| What Claude Code's official marketplace installs | `49dd158d1076134a641b33efb035946536778336` (2026-10-09T11:56:49+01:00, 46 commits after the tag, `plugin.json` still says 1.3.1) | `anthropics/claude-plugins-official`, `.claude-plugin/marketplace.json` entry `mattpocock-skills`, `source.sha` (local clone of that repository at commit `41f619d61b99`, 2026-10-26) |
| Between the two commits | 18 files under `skills/` differ | `git diff --stat` |
| Local plugin cache 1.3.1 | content of `skills/` and `.claude-plugin/` equals `49dd158` (diff of an extracted archive); `installed_plugins.json` records `gitCommitSha` `49dd158...` | local observation |
| Newest `main` seen | `59db609eb1e18aaf59b63284d0e52255aff0c63c` (2026-10-27) | clone |

So the same version string 1.3.1 covers two different contents. BenchKeeper pins the tag commit `24fe0ef` for Codex and names the official marketplace (no commit) for Claude Code (`app/src/steps/global.mjs`, `MATT_POCOCK_COMMIT`, `PLUGINS`).

### 4.2 Non-interactive install

- Documented: `claude plugin install mattpocock-skills@claude-plugins-official` (repository `README.md`, Claude Code section: "Updates itself by default").
- Headless caveat: the official marketplace is not auto-registered in `-p` runs (1.3 point 4), so it must exist first: `claude plugin marketplace add anthropics/claude-plugins-official`, or in one command `claude plugin install mattpocock-skills --marketplace anthropics/claude-plugins-official` (needs 2.1.292 or later) (`plugins/cli-reference` page). Another route: an `enabledPlugins` entry `"mattpocock-skills@claude-plugins-official": true` declares the official marketplace by itself (`plugins/org` page). `claude plugin install` asks nothing for a plain git-sourced plugin; the `-y` flag only concerns `command` sources, and without a TTY and without `-y` an install that needs a prompt is refused with exit 1. Exit codes: 0 success, 1 failure. `--json` prints a result object (2.1.268 or later).
- The marketplace checkout is not pinned by default: `marketplace add owner/repo#ref` pins a branch or tag of the marketplace. The plugin inside it is pinned by `source.sha`, which Anthropic can change. A plugin only updates when its computed version changes (`plugins/host-marketplace`); `plugin.json` says 1.3.1 at both commits, so an existing cache copy would not refresh between them (inference from the documented rule, unverified in practice).
- Pin by the project's own marketplace: the repository ships `.claude-plugin/marketplace.json` (marketplace name `mattpocock`, plugin source `./`). `claude plugin marketplace add mattpocock/skills#v1.3.1` then `claude plugin install mattpocock-skills@mattpocock` yields the tag commit `24fe0ef` (inferred from the documented `#ref` form; not run). Whether `#ref` accepts a commit SHA is not stated on the pages read (unverified).
- Seeded containers: build with `CLAUDE_CODE_PLUGIN_CACHE_DIR=/opt/seed claude plugin marketplace add ...` and `... plugin install ...`, run with `CLAUDE_CODE_PLUGIN_SEED_DIR=/opt/seed`, and enable the plugin through `enabledPlugins`; seeds are read-only and force `autoUpdate` off (`plugins/org` page).
- Network use at install: git clones from github.com (marketplace repository, then the plugin repository at the sha). Locally the 1.3.1 cache folder also holds `node_modules` and `.in_use` although the repository does not track them; the repository has a `package-lock.json` with dev dependencies (`@changesets/*`). The marketplace reference states Claude Code installs Node.js dependencies of a plugin that has a supported lockfile, with scripts disabled, so an npm registry request at install is likely (the exact rule is on `plugins/loading`, not read; unverified).
- Background updates: auto-update is off by default for a third-party marketplace (`plugins/host-marketplace` page). The default for the official marketplace is on the `plugins/loading` page, which was not read (unverified). `DISABLE_AUTOUPDATER=1` or `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` stops plugin auto-update; `FORCE_AUTOUPDATE_PLUGINS=1` keeps it while `DISABLE_AUTOUPDATER` is set (`plugins/org` page).

### 4.3 Files written and not written

Written by the install (paths from the `plugins/org` seed layout and local observation):

- `$HOME/.claude/plugins/known_marketplaces.json` and `marketplaces/<name>/` (the marketplace clone), `$HOME/.claude/plugins/cache/claude-plugins-official/mattpocock-skills/1.3.1/` (the plugin files), `$HOME/.claude/plugins/installed_plugins.json` (entry with `scope`, `version`, `gitCommitSha`), plus the marketplace declaration and `enabledPlugins` entry in the user settings file (`marketplace add` prints "declared in user settings"; the exact `enabledPlugins` key is described on the `plugin-marketplaces` and `plugins/org` pages).
- Plugin content: 27 skills listed in `plugin.json` (20 under `engineering`, 7 under `productivity`). 16 are user-invoked only (`disable-model-invocation: true`): `ask-matt`, `grill-with-docs`, `triage`, `improve-codebase-architecture`, `setup-matt-pocock-skills`, `to-spec`, `to-tickets`, `wayfinder`, `implement`, `implement-spec`, `retro`, `grill-me`, `handoff`, `teach`, `to-questionnaire`, `wait-what`. 11 can be invoked by the model: `diagnosing-bugs`, `tdd`, `prototype`, `research`, `domain-modeling`, `codebase-design`, `code-review`, `pr`, `wizard`, `grilling`, `writing-for-agents`. In `-p`, a user-invoked skill works when `/skill-name` is in the prompt (headless page). Skills are namespaced `mattpocock-skills:<name>`.
- Not in the plugin: hooks, subagent definitions, commands, MCP servers, rules, settings. The folders `skills/*/agents/openai.yaml` are interface metadata for Codex, not Claude Code subagents (file content checked). `skills/in-progress`, `skills/misc` and `skills/deprecated` exist in the repository but are not listed in `plugin.json`.
- Per repository, only when the user-invoked `setup-matt-pocock-skills` runs: it explores the repository, asks questions, and writes `docs/agents/issue-tracker.md` and related files plus an `## Agent skills` section in `AGENTS.md` or `CLAUDE.md` (its `SKILL.md`). Skills such as `to-tickets` and `triage` then read those files and use the `gh` CLI for a GitHub tracker.

### 4.4 Paid key or account

None. The skills are MIT text; install uses public repositories.

## 5. BenchKeeper (current 6.x setup only, 7.0 not covered)

### 5.1 Identity, pin, licence

| Item | Value | Source |
|---|---|---|
| Repository | https://github.com/ESchuderer/BenchKeeper | |
| Licence | MIT, "Copyright (c) 2026 ESchuderer" | `LICENSE` |
| Current setup | setup-v6.23, plugin and app version 6.23.0 (CHANGELOG entry dated 2026-10-27) | `CHANGELOG.md`, `plugins/benchkeeper/.claude-plugin/plugin.json` |
| Tag `setup-v6.23` | `ab4b14ff56a92166fb079a80444e3f015cbd9f6d`; the branch `stable` points at the same commit | `git rev-list`, `git ls-remote` |
| `main` seen | `65d5c14f6f6059d61b6ed623f9e97e4a09583130` (2026-10-27T09:46:11+01:00), ahead of the tag | clone |
| npm package | `benchkeeper`, `dist-tags.latest` = 6.23.0 | `https://registry.npmjs.org/benchkeeper` |

### 5.2 Non-interactive install

From `README.md` and `docs/setup.md` (at `65d5c14`):

- Needs Node.js 22 and at least one agent already installed. Linux and macOS are tested.
- `npx benchkeeper@6.23.0 plan` lists changes and writes nothing; `npx benchkeeper@6.23.0 apply --yes` "applies the default selection without questions"; `--all` also applies removals; `--agents claude` selects the agent; `--pack matt-pocock` adds Matt Pocock's skills; `--level lite|standard|full` picks the level (default: full on a machine without BenchKeeper). Whether `--yes` and `--level` combine is not shown together in the docs (unverified).
- Levels (generated table in `docs/setup.md`):
  - lite: the BenchKeeper plugin only (`workflow`, `tier`, `setting-up-projects`, `maintaining-repos`, `orchestrating-projects` skills); writes nothing outside the plugin install apart from the app's run record.
  - standard: lite plus a local project block (`CLAUDE.local.md`, `AGENTS.override.md`, git exclude list) written by `project apply` in each project.
  - full: standard plus global rules, Ponytail, Claude Code and Codex settings, packs and the app.
- Lite by hand (documented): `claude plugin marketplace add ESchuderer/BenchKeeper#stable --sparse .claude-plugin plugins && claude plugin install benchkeeper@benchkeeper`. The app adds the marketplace at the branch `stable`, which each release moves; a marketplace added at another ref stays there. Using the tag `#setup-v6.23` instead of `#stable` follows from the documented `#ref` form (not in BenchKeeper's docs, unverified).
- Without npm: `git clone --depth 1 --branch setup-v6.23 https://github.com/ESchuderer/BenchKeeper.git && npm ci --prefix BenchKeeper/app --omit=dev`, then `node BenchKeeper/app/bin/benchkeeper.mjs <command>`.
- Network use: npm registry for `npx` and `npm ci`; GitHub for the marketplace clone and for Ponytail (pinned tag `v5.3.2`, commit `16352ac229eb08a9598dcae48fe9f2b342567d86`); the app's own update check against the npm registry in a terminal (off with `BENCHKEEPER_NO_UPDATE_CHECK=1`, and off when `CI` is set); a full `apply` also runs `npm i -g` for the Dev Containers CLI and installs `find-skills` through the skills CLI. The app sends no telemetry (`docs/setup.md`).

### 5.3 Files written

Plugin (all levels; Claude Code's plugin cache as in 4.3): five skills; a hooks entry `hooks/claude-tier.json` that registers the module `hooks/tier/register.tsx`, an optional tier band controlled by `userConfig.tierBand` (default `false`; whether it loads in `-p` is unverified). `rules/global.md` (864 bytes) and `rules/project.md` (617 bytes) sit in the plugin folder but "a plugin cannot ship always-on instructions" (`docs/setup.md`, Levels); they are inputs of the app. The plugin's `plugin.json` sets `hooks`, `skills`, `types`, `userConfig`; no agent files and no commands.

Full `apply` (list in `docs/setup.md`, "What a full `apply` writes"):

- `$HOME/.claude/rules/00-global.md` (global rules).
- Plugins BenchKeeper (marketplace `benchkeeper`, branch `stable`), Ponytail (`ponytail@ponytail`, tag `v5.3.2`; it runs a `SessionStart` hook; level `full` in `$HOME/.config/ponytail/config.json`) and, with the pack, `mattpocock-skills@claude-plugins-official` (`app/src/steps/global.mjs`, `PLUGINS.claude`).
- Claude Code settings, merged: error reporting, feedback survey and `/feedback` off; transcripts kept 14 days; the stable update channel; subagents without a model on Sonnet; the advisor on Opus; Remote Control on at startup; the clear-context offer on plan accept; attribution lines (commits end with `Assisted-by: generative AI`, pull requests with "Created with the assistance of generative AI.").
- Default model `opusplan` as its own change; effort `high` and the auto-compact window 400000 tokens ("Neither is benchmarked").
- Optional and off unless chosen: the tier band (`pluginConfigs` in `$HOME/.claude/settings.json`), Orca worker-spec files under the app config folder.
- Removals of other global rules, skills, plugins, marketplaces, MCP servers and hooks: off unless chosen.
- Ledger and backups under `$HOME/.config/benchkeeper/ledger/` and `backup/<run>/`; `benchkeeper undo <run>` reverses a run.
- Whether `apply` honours `CLAUDE_CONFIG_DIR`: the documented paths are under `$HOME`; the app moves `.claude` for its `run` and accounts commands, but the global plan was not checked (unverified). A throwaway `HOME` is what the docs imply.

Per project (`project apply`, standard and full): `CLAUDE.local.md`, `AGENTS.override.md`, entries in `.git/info/exclude`, `.benchkeeper/state.json`, pack skills at pinned commits (with `skills-lock.json` for shared setups), `.claude/settings.local.json` when `--sandbox`; `--share` commits the block into `AGENTS.md` and `CLAUDE.md` instead.

Related path inside BenchKeeper: `project apply --framework agency-agents --agent-file <path>` fetches single agent files with `curl` from `raw.githubusercontent.com` at `b37b5bb33b78f2c1d6567d98e25ca818e3259219` into the project's `.claude/agents/`; the catalog offers six files, not the roster (`plugins/benchkeeper/library/library.json`, `app/README.md`). [Benchmark: agency-agents arm on mistreevous (Sonnet 5.5, opusplan, Opus 5.5)](https://github.com/ESchuderer/BenchKeeper-research/issues/5) asks for all subagents through the arm's own installer, which is section 3.

### 5.4 Paid key or account

None beyond the subscription. `docs/setup.md` offers an optional `accounts login --token` that wraps `claude setup-token` (subscription needed). Benchmark note from the map: jev-kit needs a paid API key for its judging model (statement in [Benchmark: agency-agents arm on mistreevous (Sonnet 5.5, opusplan, Opus 5.5)](https://github.com/ESchuderer/BenchKeeper-research/issues/5) and [Wayfinder map: benchmark research for BenchKeeper 7.0, MorphCook brief](https://github.com/ESchuderer/BenchKeeper-research/issues/8); not re-checked here).

## 6. Summary table

| Arm | Install without a person | Pin | Licence | Network at install | Writes | Paid key beyond subscription |
|---|---|---|---|---|---|---|
| Plain Claude Code | none | CLI 2.1.308 (`stable`) | proprietary, Commercial Terms | binary download | nothing | no, unless the run uses `--bare` or sets `ANTHROPIC_API_KEY` (API billing, see 1.3 and 1.4) |
| agency-agents | `scripts/install.sh --tool claude-code` | `4e3ac3ca6604` (282 agents) or `b37b5bb33b78` (283) | MIT | clone only; script has none | `*.md` files in `$CLAUDE_CONFIG_DIR/agents` or `$HOME/.claude/agents` | no, same `--bare` caveat |
| Matt Pocock's skills | `claude plugin marketplace add anthropics/claude-plugins-official`, then `claude plugin install mattpocock-skills@claude-plugins-official` | 1.3.1; official marketplace serves `49dd158`, tag is `24fe0ef` | MIT | GitHub clones, likely npm for plugin dependencies | plugin cache, marketplace and plugin records, settings entries; 27 skills, no hooks or agents | no, same `--bare` caveat |
| BenchKeeper 6.x | `npx benchkeeper@6.23.0 apply --level lite` (plugin) or `apply --yes` (full) | setup-v6.23, `ab4b14ff56a9`, npm 6.23.0 | MIT | npm, GitHub, npm global install at full | plugin; at full also `$HOME/.claude/rules/00-global.md`, settings, Ponytail | no, same `--bare` caveat |

## 7. Not verified

- Full model id of Sonnet 5.5 (inferred from the Opus 5.5 pattern).
- Versioned npm install form of Claude Code on the official page; `#<commit sha>` as marketplace ref; that `marketplace add ...#v1.3.1` yields `24fe0ef`.
- Whether the `system/init` event lists subagents and skills; whether the BenchKeeper tier-band module loads in `-p`.
- Whether `CLAUDE_CONFIG_DIR` relocates `agents/` for Claude Code (the installer assumes it) and whether BenchKeeper `apply` honours it.
- Plugin auto-update defaults and the npm dependency install of plugins (`plugins/loading` page not read); whether an existing cache copy at 1.3.1 would stay stale between `24fe0ef` and `49dd158`.
- The token estimate for agency-agents descriptions (character count divided by four).
- Combination of `--yes` with `--level` in BenchKeeper `apply`.
- No installer was run, so none of the file lists above was confirmed by a real install; they come from the scripts, manifests and docs.
