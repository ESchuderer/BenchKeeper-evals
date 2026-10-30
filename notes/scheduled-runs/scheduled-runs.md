# Scheduled agent runs: what Orca, Claude Code and Codex offer and allow

Research for issue #374, input to #344 (Automations). Sources were read on 2026-10-27. Orca was checked against the installed `orca` 1.4.237 (`orca automations create --help`, `orca automations list --help`, read-only). Claude Code docs were read from code.claude.com (installed Claude Code is 2.1.308). Codex docs now live on learn.chatgpt.com; the older developers.openai.com/codex URLs redirect there. Anything not found in an official source is marked "unverified".

## Question

What do the runners documented today offer for unattended, scheduled agent runs, and what do the providers allow on a subscription? Does #344 need its own template format and Orca adapter, or do the runners' own features suffice?

## Short answer

#344 needs a template layer, but not a scheduler.

- No runner offers what #344 asks for: a versioned file with parameters, a lint check, a diff and an undo, applied to the runner. Orca stores automations only in its own store and has no template or parameter option in `create --help`. Claude Code Desktop keeps a task prompt in `scheduled-tasks/<name>/SKILL.md` under the Claude config folder, but schedule, folder, model and enabled state are not in that file. Claude cloud scheduled tasks live in the claude.ai account and are managed from the web or `/schedule`. Codex scheduled tasks are created and managed in the ChatGPT desktop app or on the web, not from the CLI.
- Orca is the only runner whose documented feature set covers all of #344's fields (cron or RRULE with time zone, precheck, session reuse, missed-run grace, new worktree per run, per-run model and effort). The claims in #344 hold for 1.4.237 (details below). The meaning of the missed-run grace window is not documented.
- The runners' own schedulers do not fit the two basic automations equally. The issue pickup runs every 20 minutes: Claude cloud scheduled tasks have a 1 hour minimum interval and fresh clones without local files. Only Orca documents a precheck. For any other runner, a shell precheck followed by `claude -p` or `codex exec` run from cron or systemd gives the same effect and keeps a skipped run free of usage.
- Provider terms allow scripted and scheduled use only on the paths the providers document. Anthropic documents scheduled tasks, `claude -p` and a one-year `CLAUDE_CODE_OAUTH_TOKEN` for subscriptions. OpenAI documents API keys as the default for automation and warns against ChatGPT-managed auth in CI for public repositories (BenchKeeper is public). OpenAI's Terms of Use could not be fetched (HTTP 403), so the subscription question is open for Codex.

Recommendation for #344 (research view, the decision stays with the issue owner): keep the template format and the lint, keep the adapter interface small, ship the Orca adapter first, and make the generic fallback "template to a script with precheck, run by the user's own cron or systemd timer". Do not build a scheduler. Cloud scheduled tasks and the Codex app are later adapters at most, each with the limits in the tables.

## Orca

Sources: https://www.onorca.dev/docs/cli/automations, https://www.onorca.dev/docs/remote-servers, and the installed CLI help (1.4.237).

| Topic | What the documents say | Source |
|---|---|---|
| Schedule | `--trigger` takes `hourly`, `daily`, `weekdays`, `weekly`, a 5-field cron expression or an RRULE; `--time`, `--day`, `--timezone` (IANA). | CLI help; docs page |
| Prompt and agent | `--prompt`, `--provider` (codex, claude, gemini and others). | CLI help |
| Extra agent arguments | `--extra-agent-args="--model opus --effort high"`. "Only model, effort, and a few safe options are accepted (Claude, Codex, CodeBuddy, Cursor, Grok, OMP); extras cannot be combined with --reuse-session." The docs add Claude's `--add-dir`. | CLI help; docs page |
| Target | `--repo`, `--workspace` (existing worktree or folder), `--project` with `--host`; `--workspace-mode` (`existing` or `new-per-run`), `--base-branch`. With no target flag Orca uses the enclosing worktree of the shell. | CLI help; docs page |
| Precheck | `--precheck <command>` runs "a bounded command before scheduled runs; exit code 0 continues, anything else records a skipped run." `--precheck-timeout` exists; the help gives no default or unit (unverified). | CLI help |
| Session reuse | `--reuse-session` "only with existing-workspace automations" submits later runs "to the previous live automation session when it is still available"; `--fresh-session` turns it off. | CLI help; docs page |
| Missed-run grace | `--missed-run-grace-minutes <n>`, described only as "Missed-run grace window". The docs show `--missed-run-grace-minutes 30` and do not say what Orca does inside or outside the window (unverified). | CLI help; docs page |
| Enabled state | `--enabled` or `--disabled`; the docs recommend creating disabled while tuning. | CLI help; docs page |
| Management | `list`, `show`, `create`, `edit`, `run`, `runs --id`, `remove` ("deletes an automation and its run history"). `create` is documented at the CLI help; `show`, `edit`, `run`, `runs`, `remove` are taken from the docs page, not run. | docs page |
| Output | `--json` on every command. | CLI help |
| Remote hosts | `--pairing-code`, `--environment`, `--source-context` run against a paired Orca server. A server "must stay awake"; agents there "keep running when the client laptop sleeps". | CLI help; remote-servers page |
| Needs the app running | Not stated for local automations (unverified). `orca serve` is documented for a host that "should run without the desktop window". Whether a local schedule fires while Orca is closed is unverified. | remote-servers page |
| Run model | Runs start in an Orca terminal or worktree. The docs say agents "that take the prompt on the command line, such as Claude and Codex" get it that way. Whether Orca starts `claude` interactively or as `claude -p` is not stated (unverified); this decides which provider terms path applies. | docs page |
| Plan requirements, limits | None stated by Orca. The agent's own plan limits apply. | docs page |

### Claims of #344 against the installed version (1.4.237)

| Claim in #344 | Result |
|---|---|
| Schedule (preset, cron or RRULE) with a time zone | Confirmed. |
| A prompt | Confirmed. |
| An agent and extra agent arguments (model and effort) | Confirmed. Extra: extras cannot be combined with `--reuse-session`, so a template cannot have both a model override and session reuse. |
| A project, an existing worktree, or a new worktree per run | Confirmed (`--repo`, `--project`, `--workspace`, `--workspace-mode`). |
| `--precheck`, exit code 0 starts the run, anything else records a skipped run | Confirmed. The command is "bounded"; a `--precheck-timeout` option exists (not mentioned in #344). |
| Reuse of the previous live session | Confirmed, existing-workspace automations only. |
| A missed-run grace window | The option exists. Its behavior is undocumented. |
| Enabled or disabled | Confirmed. |

Not in #344 and relevant: host selection (`--host`, `--environment`, `--pairing-code`) and `--source-context`. Orca has no template, parameter or "installed from" metadata in `create --help` (absence in the help text, not a statement by Orca).

## Claude Code

Sources: https://code.claude.com/docs/en/scheduled-tasks, https://code.claude.com/docs/en/routines, https://code.claude.com/docs/en/desktop-scheduled-tasks, https://code.claude.com/docs/en/headless, https://code.claude.com/docs/en/github-actions, https://code.claude.com/docs/en/authentication, https://code.claude.com/docs/en/legal-and-compliance.

Cloud scheduled tasks are the former "routines" and are a research preview ("Behavior, limits, and the API surface may change").

| Feature | Cloud scheduled task (routine) | Desktop scheduled task | `/loop` and session cron |
|---|---|---|---|
| Runs on | Anthropic cloud, or an organization's self-hosted environment | Your machine | Your machine |
| Needs machine on | No | Yes: "Tasks only run while the desktop app is running and your computer is awake." | Yes, and an open, idle session |
| Plans | Pro, Max, Team, Enterprise; needs a claude.ai login (not a Console API key or cloud provider) | Desktop 1.1.5368 or later (plan not stated) | Any Claude Code login (plan not stated) |
| Minimum interval | 1 hour; "Expressions that run more often than once per hour are rejected." | 1 hour in the forms; Claude can set shorter, 1 minute | 1 minute |
| Schedule forms | Presets, cron (UTC unless `CRON_TZ=`), one-off, API trigger, GitHub events (pull request, release, issue) | Hourly, daily, weekdays, weekly, manual, custom cron (local time) | `/loop 5m ...`, self-paced, `CronCreate` |
| Missed runs | Not stated (unverified). Runs wait if the 100 per hour limit is hit. | "exactly one catch-up run for the most recently missed time" within 7 days; a sleeping computer skips the run | "No catch-up for missed fires"; fires once when idle; recurring tasks expire after 7 days |
| Precheck | None documented (unverified). Each run starts a full session. | None documented (unverified). | None documented (unverified). |
| Local files and worktree | No: "fresh clone", branches prefixed `claude/` | Local folder; optional isolated Git worktree per run | The open session |
| Permissions | Starts in auto mode; a run can stop and wait for an answer | Per-task permission mode; Manual mode stalls until approved | Inherits the session |
| Session reuse | New session per run | Fresh session per run | Same session |
| Format and management | Account store; web, Desktop, `/schedule` (needs v2.1.225 or later for GitHub triggers from the CLI); no file format; API trigger cannot be added from the CLI | Prompt in `scheduled-tasks/<task-name>/SKILL.md` under the Claude config folder (front matter `name`, `description`); schedule, folder, model, enabled state not in the file | Not persistent beyond 7 days |
| Limits | 100 scheduled runs per hour per account; 30 "Run now" or API fires per hour per task; GitHub event hourly caps (values not given in the page); "None of these hourly limits has overage" | Not stated | 50 tasks per session; 7-day expiry |
| Usage | "Scheduled tasks draw down subscription usage the same way interactive sessions do." Usage credits can fund runs past the limit. | Subscription | Subscription |

Identity: cloud runs act as the user ("Commits and pull requests carry your GitHub user"). The fired prompt "can't act as approval or consent for actions during the run". `/schedule` is hidden for Console API keys and cloud-provider logins.

### `claude -p` (headless)

| Topic | What the documents say |
|---|---|
| Use | `claude -p "<prompt>"` runs non-interactively; exits 0 on success and non-zero on failure, so a shell precheck plus `claude -p` is a scriptable pattern. |
| Output | `--output-format` takes `text`, `json` or `stream-json`; `json` carries `total_cost_usd`, described as a client-side estimate. |
| Permissions | From v2.1.302, `claude -p` starts in Manual mode when nothing sets a mode, and a call needing approval is denied. Use `--allowedTools`, `--permission-mode` (`auto`, `dontAsk`, `acceptEdits`) and `--permission-prompts none` ("in a scheduled job"; v2.1.259 or later). |
| Auth | A subscription login works. `--bare` "doesn't use your subscription login" and does not read `CLAUDE_CODE_OAUTH_TOKEN`. `ANTHROPIC_API_KEY` is "always used when present" in `-p`. |
| Long-lived token | `claude setup-token` makes a one-year token for "CI pipelines, scripts"; it "requires a Pro, Max, Team, or Enterprise plan" and "can only make model requests". |
| Repository content | Without `--bare`, `-p` runs a project's hooks and MCP servers "even in a folder you've never trusted". Matters for scheduled runs in repositories with untrusted content. |
| Resume | `--continue`, `--resume <session id>`. |

### GitHub Actions (`anthropics/claude-code-action`)

- A `prompt` input runs the action "in automation mode on any GitHub event, including a cron schedule". Example `cron: "0 9 * * *"`.
- Auth: `ANTHROPIC_API_KEY`, or `CLAUDE_CODE_OAUTH_TOKEN` ("an OAuth token that authenticates with your Claude subscription, available on Pro, Max, Team, and Enterprise plans"). For a secret shared across repositories the page recommends an API key, "since an OAuth token is tied to the subscription of the person who ran `claude setup-token`".
- Costs: GitHub Actions minutes plus tokens; "If you authenticate with an OAuth token, runs use your Claude subscription instead of API billing." Caps: `--max-turns`, job timeouts, concurrency.
- Limits stated: "GitHub runs scheduled workflows only from the default branch and, in public repositories, disables the schedule after 60 days without repository activity." The action rejects a bot actor unless listed in `allowed_bots`, and scheduled runs are attributed to the user who last changed the cron line. GitHub's own minimum cron interval is not stated by Anthropic (unverified).
- Runs on GitHub runners: no access to the user's machine, local worktrees or local tools.

## Codex

Sources: https://learn.chatgpt.com/docs/automations (formerly https://developers.openai.com/codex/app/automations), https://learn.chatgpt.com/docs/non-interactive-mode, https://learn.chatgpt.com/docs/auth, https://learn.chatgpt.com/docs/auth/ci-cd-auth, https://learn.chatgpt.com/docs/enterprise/access-tokens, https://learn.chatgpt.com/docs/github-action, https://learn.chatgpt.com/docs/pricing.

| Feature | What the documents say |
|---|---|
| Scheduled tasks | Recurring background tasks in the ChatGPT desktop app and on the web. "Codex CLI doesn't provide the Scheduled management interface. Use ChatGPT web or the desktop app to create and manage scheduled tasks." No CLI or file format for creating one. |
| Schedule | Custom schedule controls or an RRULE such as `RRULE:FREQ=MONTHLY;BYMONTHDAY=1;BYHOUR=9;BYMINUTE=0`. In-chat tasks can use minute intervals. A minimum interval for standalone tasks is not stated (unverified). |
| Event triggers | Web and mobile, "eligible plans": Gmail, Slack, GitHub pull request activity. "One task can use multiple event triggers, but it can't combine event triggers with a time-based schedule." Not available in the desktop app, CLI or IDE extension. |
| Machine and project | "Keep the computer on and the app running when a scheduled task needs local files." The selected project "must still be available on disk when the task is scheduled to run." Web tasks have no local folder or worktree. |
| Worktree | In Git repositories a task runs in the local project or a new background worktree; worktrees accumulate until runs are archived. |
| Sandbox and approvals | "Scheduled tasks run unattended with your default sandbox settings." In read-only and workspace-write modes calls that need the network or other disallowed access fail. Tasks use `approval_policy = "never"` when organization policy allows it. |
| Precheck | None documented (unverified). |
| Session reuse | A task scheduled inside a chat returns to that chat with its context; standalone tasks start a new chat per run. |
| Missed runs | Not documented (unverified). |
| Plans | Pricing feature table lists scheduled tasks for Plus, Pro, Business, Enterprise (and an API column). Event triggers depend on plan and workspace settings. |
| Usage and limits | The automations page states none. Pricing page: "ChatGPT uses the same pricing, credits, and usage limits as Codex"; Plus and Business have five-hour message estimates, Pro "currently" none; weekly limits "may also apply". |
| `codex exec` | Runs without the TUI "for scripts and CI"; default read-only sandbox; `--sandbox workspace-write` allows edits; must run in a Git repository unless `--skip-git-repo-check`; `--json`, `-o`, `--output-schema`, `resume --last`. `--full-auto` "is no longer supported". |
| Auth in automation | `CODEX_API_KEY` for `codex exec`. "API keys are the right default for automation." ChatGPT-managed auth in CI is "advanced": "Do not use this workflow for public or open-source repositories", "Treat" the cached `auth.json` file "like a password". The CI guide applies "only when" the runner is "trusted private infrastructure" and "only one machine or serialized job stream will use a given `auth.json` copy". |
| Access tokens | "Codex access tokens are currently supported for ChatGPT Business and Enterprise workspaces", for `codex exec` jobs, scripts and schedulers on trusted runners. Not available on Plus or Pro (pricing table). |
| GitHub Action | `openai/codex-action` takes `openai-api-key`; the page recommends it over installing the CLI in a workflow. No subscription login input is documented there (unverified beyond the page excerpt read). |

## Provider terms

### Anthropic

Consumer Terms of Service (Free, Pro and Max users), effective Oct 8, 2025, Section 3, https://www.anthropic.com/legal/consumer-terms:

> You may not access or use, or help another person to access or use, our Services in the following ways:

> Except when you are accessing our Services via an Anthropic API Key or where we otherwise explicitly permit it, to access the Services through automated or non-human means, whether through a bot, script, or otherwise.

Claude Code legal page, https://code.claude.com/docs/en/legal-and-compliance:

> Advertised usage limits for Pro and Max plans assume ordinary, individual usage of Claude Code and the Agent SDK.

> OAuth authentication is intended exclusively for purchasers of Claude Free, Pro, Max, Team, and Enterprise subscription plans and is designed to support ordinary use of Claude Code and other native Anthropic applications.

> Developers building products or services that interact with Claude's capabilities, including those using the Agent SDK, should use API key authentication through Claude Console or a supported cloud provider. Anthropic does not permit third-party developers to offer Claude.ai login into their own applications, or to route requests through Free, Pro, or Max plan credentials on behalf of their users. Moreover, developers may not collect, store, or intermediate Claude.ai credentials or session tokens [...]

> Nor does it prevent an end user from signing in to the unmodified Claude Code binary with their own Claude subscription, including where a platform hosts Claude Code as described under *Can customers offer Claude Code in their products?* above.

Authentication page, https://code.claude.com/docs/en/authentication:

> For CI pipelines, scripts, or other environments where interactive browser login isn't available, generate a one-year OAuth token with `claude setup-token`

> This token authenticates with your Claude subscription and requires a Pro, Max, Team, or Enterprise plan.

Reading (analysis, not legal advice): the Consumer Terms ban automated access except through an API key or "where we otherwise explicitly permit it". Anthropic's own documents explicitly describe scheduled tasks, `claude -p` and a subscription OAuth token for scripts and CI, so these are the documented permitted paths. A user's own scheduled run through the unmodified `claude` binary with their own login matches the last quote above. What the documents do not settle: a third-party tool that stores or hands over the login or token (the "collect, store, or intermediate" sentence), and how "ordinary, individual usage" is measured for many unattended runs. For #344 this means: BenchKeeper and Orca must launch the user's own installed `claude` and never read, copy or store the login or token; the registry already holds no credential (#344 decision). The terms of the Commercial Terms of Service (Team, Enterprise, API) were not read (unverified).

### OpenAI

The Terms of Use at https://openai.com/policies/terms-of-use/ and https://openai.com/policies/row-terms-of-use/ returned HTTP 403 to every request and could not be read. No verbatim quote is available (unverified). A search result for the row-terms page lists a "What You Cannot Do" bullet on automatic or programmatic extraction of data or Output; that is a search snippet, not a read of the terms.

What the Codex documents say, verbatim (https://learn.chatgpt.com/docs/non-interactive-mode, https://learn.chatgpt.com/docs/auth):

> API keys are the right default for automation because they are simpler to provision and rotate. Use this path only if you specifically need to run as your Codex account.

> Do not use this workflow for public or open-source repositories.

> Use API key authentication for programmatic Codex CLI workflows, such as CI/CD jobs. Don't expose Codex execution in untrusted or public environments.

> Scheduled tasks run unattended with your default sandbox settings.

The documents do not state whether a Plus or Pro subscription may be used by an unattended `codex exec` run on the user's own machine, other than the "advanced" ChatGPT-managed auth path above. Whether a scheduler (Orca, cron) launching the interactive Codex CLI with the user's ChatGPT login is permitted is unverified.

## What this means for #344

| Need in #344 | Orca | Claude cloud task | Claude Desktop task | cron or timer plus `claude -p` or `codex exec` | Codex app task |
|---|---|---|---|---|---|
| Every 20 minutes | Yes (cron) | No (1 hour minimum) | Only if Claude sets it in a session | Yes | Unverified |
| Native precheck | Yes | No (unverified) | No (unverified) | Shell, before the agent starts | No (unverified) |
| Local worktree and tools | Yes | No (fresh clone) | Yes | Yes | Yes (app running) |
| Created from a file by a tool | CLI, JSON output | `/schedule` in a session or web | Prompt file, rest via UI or Claude | Yes, it is a file | No CLI |
| Works with machine off | Remote Orca server only | Yes | No | Needs a host that is on | No |
| Subscription use documented as allowed | Depends on how Orca launches the agent (unverified) | Yes | Yes | `claude`: documented (setup-token, `-p`); `codex`: unverified | Yes (it is the product) |

Implications for the design:

- Keep a template format: it is the only versioned, reviewable, lintable and portable form of an automation. Template fields that no runner can apply must be rejected or reported, not silently dropped (for example grace on a cron fallback, or model override together with session reuse on Orca).
- Keep the precheck mandatory in templates: Orca supports it natively; a cron fallback gets it as the first line of the script; cloud and app schedulers have none, so a template for those runners would start a paid session to find nothing.
- Per-parameter runner limits belong in the adapter: 1 hour floor for Claude cloud, 100 scheduled runs per hour per account, `claude/` branch prefix, hourly GitHub event caps, 7-day expiry for `/loop`.
- For the PR watcher, Claude cloud GitHub triggers (pull request, release, issue events) remove the polling need on that runner. Their filter fields are documented for pull requests only; issue filters are unverified.

## Unverified

- Orca: meaning of the missed-run grace window; whether local automations fire while the Orca app is closed; the default and unit of `--precheck-timeout`; whether Orca starts the agent interactively or as a non-interactive command; Orca's behavior for runs missed while the app was off. Orca's `show`, `edit`, `run`, `runs`, `remove` were taken from the docs page and not executed (the ticket allows only `create --help` and `list --help`).
- Claude: missed-run behavior, prechecks and run history limits for cloud tasks; plan requirement of Desktop tasks and `/loop`; GitHub's minimum cron interval; issue-event filters; the Commercial Terms of Service.
- Codex: minimum interval and missed-run behavior of scheduled tasks; precheck; whether a Plus or Pro login may drive unattended `codex exec`; the GitHub Action's subscription support; OpenAI's Terms of Use (HTTP 403).
- All documents describe the state on 2026-10-27; the Claude cloud feature is a research preview and may change.
