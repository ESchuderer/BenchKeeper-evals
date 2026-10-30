# Agent parity: Gemini CLI, GitHub Copilot CLI and Windows against Claude Code and Codex

Ticket: ESchuderer/BenchKeeper#377. Documentation read on 2026-10-27, primary sources only. Each table cell carries the source tags defined in the link list at the end. "BenchKeeper today" cites files of this repository at the head of `main` (3e1946b).

## Question

What do Gemini CLI, GitHub Copilot CLI and (for all four agents) Windows document, so that the gap to the support BenchKeeper gives Claude Code and Codex is known? Surfaces: instruction files, skills, plugins or extensions, hooks, settings files and their schema, MCP, subagents, usage and limit visibility, headless mode, sandbox, login and accounts, Windows.

## Short answer

1. **Gemini CLI is being retired for individuals.** Google's announcement of 2026-05-19 says Gemini CLI stops serving Google AI Pro, Google AI Ultra and free "Gemini Code Assist for individuals" users on 2026-06-18. It stays available for Gemini Code Assist Standard and Enterprise licenses and through paid Gemini and Gemini Enterprise Agent Platform API keys. The successor is Antigravity CLI, without "1:1 feature parity right out of the gate", and its migration page moves global skills to `$HOME/.gemini/antigravity-cli/skills/`, workspace skills to `.agents/skills/` and MCP servers to `$HOME/.gemini/config/mcp_config.json` or `.agents/mcp_config.json` ([g-blog], [g-migration]). Whatever 7.0 builds for "Gemini" targets two products with different paths. This decides ticket #385 before any feature work.
2. **Plugin parity is a BenchKeeper gap, not an agent gap.** `agents.json` sets `"plugins": false` for Gemini and Copilot (`app/src/agents.json:51`, `:72`), so both get copies of skills only (`docs/setup.md:44`). Both agents document an installable package: Gemini extensions (manifest `gemini-extension.json`, bundles MCP, skills, hooks, sub-agents, commands; [g-ext], [g-extref]) and Copilot plugins (manifest `plugin.json`, marketplaces, `enabledPlugins` in settings; [p-plugins]).
3. **Everything file-shaped can reach parity for all four agents.** Each documents instruction files, skills, MCP, settings, subagents and hooks as files in known locations, so the read-only and write paths BenchKeeper uses (rules, skills, MCP, settings, `extensions list`) have a documented target. The `extensions list` inventory covers only Claude Code and Codex today (`app/README.md:69`) and can be extended to Gemini and Copilot hooks, MCP servers and subagents.
4. **Usage and limit visibility cannot reach parity.** Only Claude Code documents a machine-readable feed: the status line input carries `rate_limits.five_hour` and `rate_limits.seven_day` with `used_percentage` and `resets_at` ([c-statusline]). Codex, Gemini CLI and Copilot document interactive commands (`/usage`, `/stats model`, `/usage`) and token counts in headless output at most. Nothing documented lets a script read the remaining percentage of a limit window for them. So `accounts track`, `accounts status` usage, `accounts limits` and auto-pick have nothing to build on for those three. `docs/setup.md:87` says "Codex has no documented source": that is right for a scriptable feed, but Codex does document `/usage` for account usage and rate-limit reset ([x-commands]).
5. **Multi-account support has only partial footing.** Claude Code documents separate logins through `CLAUDE_CONFIG_DIR` ([c-auth]). Codex documents `auth.json` under `CODEX_HOME` ([x-auth]), which BenchKeeper already uses (`app/README.md:72`), without calling it a multi-account method. Gemini CLI has `GEMINI_CLI_HOME` ([g-config]) and Copilot has `COPILOT_HOME` ([p-cfgdir]) as roots for their user directories, but neither page says where the login is cached or that the variable isolates it. Not verified for either.
6. **Windows: all four agents state native Windows support, with different limits.** Claude Code runs natively but its sandbox does not ([c-sandbox]); Codex has a native Windows sandbox and recommends Windows 11 ([x-winsandbox]); Gemini CLI lists Windows 11 24H2+ and PowerShell ([g-install]); Copilot CLI lists PowerShell and WSL ([p-about]) and requires PowerShell 6 or higher to install ([p-install]). BenchKeeper itself runs a CI smoke test on Windows and is untested by the owner (`app/README.md:39`). The agents document Windows handling for hooks (Claude `shell: powershell`, Copilot `powershell` key, Codex `commandWindows`), which a Windows hook-writing step would need.
7. **Four mismatches between `agents.json` and the docs** (details in the table): Copilot has project settings files (`.github/copilot/settings.json`, `settings.local.json`) while `agents.json:83` has `"settings": null`; Copilot reads `.mcp.json` before `.github/mcp.json` in one directory (`agents.json:84`); Codex now documents a root `plugin.json` as the portable manifest and `.codex-plugin/plugin.json` as a compatibility fallback; Claude Code reads `AGENTS.md` directly when no `CLAUDE.md` exists ([c-memory]), which BenchKeeper does not rely on (`CLAUDE.md` imports `AGENTS.md`).

## Comparison

One row per surface, one column per agent plus what BenchKeeper does today.

| Surface | Claude Code | Codex | Gemini CLI | Copilot CLI | BenchKeeper today |
| --- | --- | --- | --- | --- | --- |
| Instruction files | `CLAUDE.md`, `.claude/CLAUDE.md`, `$HOME/.claude/CLAUDE.md`, `.claude/rules/`; `AGENTS.md` read when no `CLAUDE.md` exists; `@` imports [c-memory] | `$HOME/.codex/AGENTS.md` (or `AGENTS.override.md`), then `AGENTS.md` per directory from project root down, extra names via `project_doc_fallback_filenames`, 32 KiB cap [x-agentsmd] | `$HOME/.gemini/GEMINI.md`, workspace and subdirectory `GEMINI.md`; `context.fileName` accepts `AGENTS.md`; `@file.md` imports [g-md] | `$HOME/.copilot/copilot-instructions.md`, `$HOME/.copilot/instructions/**/*.instructions.md`, `.github/copilot-instructions.md`, `.github/instructions/**/*.instructions.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `COPILOT_CUSTOM_INSTRUCTIONS_DIRS` [p-instr] | Global rules for all four, a marked block except Claude Code; project `CLAUDE.md` import for Claude Code, `AGENTS.md` block for the rest; Gemini also sets `context.fileName` (`app/src/agents.json:5-24`, `:26-45`, `:47-66`, `:68-87`; `docs/setup.md:43`) |
| Skills | `$HOME/.claude/skills/`, `.claude/skills/`, plugin `skills/`; `SKILL.md` per the Agent Skills standard; `.agents/skills` not mentioned on the page read [c-skills] | `.agents/skills` from cwd up to repo root, `$HOME/.agents/skills`, `/etc/codex/skills`; optional `agents/openai.yaml` with `allow_implicit_invocation` [x-skills] | `$HOME/.gemini/skills/` or `$HOME/.agents/skills/`, `.gemini/skills/` or `.agents/skills/` (`.agents` wins), extension skills [g-skills] | `.github/skills`, `.claude/skills`, `.agents/skills`, `$HOME/.copilot/skills`, `$HOME/.agents/skills`; `SKILL.md` with `name`, `description` [p-skills] | Claude `.claude/skills`; Codex `.agents/skills`; Gemini global `.gemini/skills`, project `.agents/skills`; Copilot global `.copilot/skills`, project `.agents/skills` (`app/src/agents.json:5-87`) |
| Plugins or extensions | Plugin: `.claude-plugin/plugin.json`; bundles skills, agents, hooks, MCP; marketplace `.claude-plugin/marketplace.json`; `/plugin`, `claude plugin` [c-plugins] | Plugin: root `plugin.json` portable, `.codex-plugin/plugin.json` fallback; marketplace `.agents/plugins/marketplace.json` or `.claude-plugin/marketplace.json`; `codex plugin marketplace add owner/repo`; cache `$HOME/.codex/plugins/cache/` [x-buildplugins]; browse with `/plugins` [x-plugins] | Extension: `gemini-extension.json`; bundles MCP, commands, skills, `agents/`, `hooks/hooks.json`, `policies/`, themes; `gemini extensions install <GitHub URL or path> [--ref]`; lives in `$HOME/.gemini/extensions` [g-extref]; gallery at geminicli.com [g-ext]; Antigravity calls them plugins, `agy plugin import gemini` [g-blog], [g-migration] | Plugin: `plugin.json` (Agent Plugins 1.0 with `$schema`, or legacy); bundles agents, skills, hooks, MCP, LSP; marketplaces `copilot-plugins` and `awesome-copilot` by default; `copilot plugin install`; `enabledPlugins` in user or repository settings [p-plugins] | `plugins: true` for Claude Code and Codex, `false` for Gemini and Copilot (`app/src/agents.json:9`, `:30`, `:51`, `:72`); Gemini and Copilot get skill copies (`docs/setup.md:44`) |
| Hooks | Events such as `SessionStart`, `PreToolUse`, `PostToolUse`, `Stop`, `StopFailure`; in `$HOME/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json`, plugin `hooks/hooks.json`, skill and subagent frontmatter; handlers `command`, `http`, `mcp_tool`, `prompt`, `agent` [c-hooks] | `PreToolUse`, `PostToolUse`, `SessionStart`, `Stop`, `SubagentStart` and others; `hooks.json` or `[hooks]` in `$HOME/.codex/` and `<repo>/.codex/`; handlers `command`, `mcp_tool`; project layers load only when trusted [x-hooks], [x-configbasic] | `SessionStart`, `BeforeTool`, `AfterTool`, `BeforeAgent` and others; `hooks` key in `.gemini/settings.json`, `$HOME/.gemini/settings.json`, `/etc/gemini-cli/settings.json`, extensions; handler `command` only [g-hooks] | `sessionStart`, `preToolUse`, `postToolUse`, `agentStop` and others; `.github/hooks/NAME.json`, `$HOME/.copilot/hooks/`, `hooks` key in repository settings, plugin `hooks.json`; handler `command` with `bash` and `powershell` fields [p-hooks], [p-cfgdir], [p-plugins] | `extensions list` shows hooks for Claude Code and Codex only (`app/README.md:69`); BenchKeeper plugin hook support follows `plugins: true` |
| Settings files and schema | User `$HOME/.claude/settings.json`, project `.claude/settings.json`, local `.claude/settings.local.json`, managed; strict JSON; `$schema` `https://json.schemastore.org/claude-code-settings.json`; `$HOME/.claude.json` for state and user MCP [c-settings] | `$HOME/.codex/config.toml`, project `.codex/config.toml` (trusted projects), profiles, `/etc/codex/config.toml`, `requirements.toml`; TOML; no published schema found in the pages read [x-configbasic], [x-configref] | User `$HOME/.gemini/settings.json`, project `.gemini/settings.json`, system (Windows `C:\ProgramData\gemini-cli\settings.json`); JSON; schema `schemas/settings.schema.json` in the repository [g-config] | User `$HOME/.copilot/settings.json` (JSONC, `$schema` tolerated), repository `.github/copilot/settings.json` and `settings.local.json`; `config.json` is internal state, not settings [p-cfgdir], [p-cmdref] | JSON for Claude and Gemini, TOML for Codex, JSONC global for Copilot; Copilot project `"settings": null` (`app/src/agents.json:83`) |
| MCP | User `$HOME/.claude.json`, project `.mcp.json`, key `mcpServers`; `claude mcp add` [c-mcp] | `[mcp_servers.<id>]` in `config.toml`; `codex mcp add`, `codex mcp login` [x-mcp] | `mcpServers` in `settings.json` (user and project); `gemini mcp add`; tokens in `$HOME/.gemini/mcp-oauth-tokens.json` [g-mcp]; Antigravity moves to `$HOME/.gemini/config/mcp_config.json` [g-migration] | User `$HOME/.copilot/mcp-config.json`, project `.mcp.json` and `.github/mcp.json` (`.mcp.json` wins in one directory); key `mcpServers`; `copilot mcp add` [p-mcp] | Paths as documented, Copilot project `.github/mcp.json` (`app/src/agents.json:5-87`, `:84`) |
| Subagents | `.claude/agents/`, `$HOME/.claude/agents/`, plugin `agents/`; Markdown with YAML frontmatter [c-subagents] | `$HOME/.codex/agents/`, `.codex/agents/`; TOML with `name`, `description`, `developer_instructions` [x-subagents] | `.gemini/agents/*.md`, `$HOME/.gemini/agents/*.md`; Markdown with YAML frontmatter [g-subagents] | `.github/agents/`, `$HOME/.copilot/agents/`; Markdown with `.agent.md` extension [p-agents] | `.claude/agents`, `.codex/agents`, `.gemini/agents`, `.copilot/agents`, `.github/agents` (`app/src/agents.json:5-87`) |
| Usage and limit visibility | Status line script input: `rate_limits.five_hour` and `seven_day` `used_percentage`, `resets_at`, `context_window.used_percentage` [c-statusline]; `--output-format json` has `total_cost_usd` [c-headless] | `/usage` "View account token usage or use a rate-limit reset", `/status` session tokens, `/statusline` picks footer items [x-commands]; `tui.status_line` is a list of item identifiers, not a script [x-configref]; `exec --json` `turn.completed` carries token counts [x-exec] | `/stats model` shows session tokens and quota information, summary on exit [g-quota]; headless JSON `stats` with token usage [g-headless]; no programmatic quota access documented [g-quota] | `/usage` shows session AI credits, duration, lines edited, tokens per model; `/context`; `/limits` sets a per-response soft maximum [p-overview], [p-cmdref]; `statusLine` setting is an object, input fields not documented [p-cfgdir] | Usage tracking by status line script and `StopFailure` hook for Claude Code only (`docs/setup.md:87`); `accounts` is `claude` or `codex` only (`app/README.md:72`) |
| Headless mode | `claude -p`, `--output-format text, json, stream-json`, `--json-schema`, `--bare`; exit 0 on success, 143 on SIGTERM [c-headless] | `codex exec`, `--json` JSONL events, `--output-schema`, `-o`; numeric exit codes not documented [x-exec] | `-p`, runs headless without a TTY; `--output-format` JSON and streaming JSONL; exit 0, 1, 42, 53 [g-headless] | `-p`, `--output-format json` gives JSONL, `-s` for output only, `--allow-all-tools` and related flags; record fields and exit codes for `-p` not documented [p-prog] | `eval` runs real agent sessions for `claude` and `codex` (`app/README.md:76`); `run` wraps `claude\|codex` (`app/README.md:73`) |
| Sandbox | macOS Seatbelt; Linux and WSL2 bubblewrap; native Windows and WSL1 not supported, commands run unsandboxed [c-sandbox] | macOS Seatbelt; Windows native sandbox in PowerShell (`mxc`, `elevated`, `unelevated`); Linux and WSL2 bubblewrap; default `workspace-write` [x-sandbox], [x-winsandbox] | Seatbelt on macOS; Docker or Podman; Windows Native (`icacls`, Low Mandatory Level); gVisor and LXC on Linux; `-s`, `GEMINI_SANDBOX`, `tools.sandbox` [g-sandbox] | Off by default; `/sandbox enable`, `sandbox.enabled`; macOS 15+, Linux with bubblewrap 0.5.0+, recent Windows 11 [p-sandbox], [p-cfgdir] | Project setup takes `--env container\|host-agent\|sandbox\|host` and `--sandbox` (`app/README.md:56`); how that varies per agent was not checked |
| Login and accounts | `/login`, `claude auth login`, `CLAUDE_CODE_OAUTH_TOKEN` from `claude setup-token`; one `CLAUDE_CONFIG_DIR` per account; credentials in Keychain (macOS) or `.credentials.json` [c-auth] | `codex login`, `--with-api-key`, `--device-auth`; `auth.json` under `CODEX_HOME` or keyring (`cli_auth_credentials_store`); `codex login status` exits 0 when credentials exist; multiple accounts not described [x-auth], [x-commands] | Google sign-in, `GEMINI_API_KEY`, Vertex AI variables; "cached locally", path not stated; headless needs a cached login or environment variables; multiple accounts not described [g-auth] | `/login`, `copilot login`, `--with-token`; token variables `COPILOT_GITHUB_TOKEN`, `GH_TOKEN`, `GITHUB_TOKEN` in that order; fine-grained PAT with "Copilot Requests"; `COPILOT_HOME` [p-install], [p-prog], [p-cmdref] | Accounts, `accounts login`, `run --account` for Claude Code and Codex, `CLAUDE_CONFIG_DIR` and `CODEX_HOME` (`app/README.md:72-73`) |
| Windows | Windows 10 1809+; native install by PowerShell, CMD or WinGet; Git for Windows optional (PowerShell tool without it); sandbox only in WSL2; hooks accept `"shell": "powershell"` [c-setup], [c-hooks] | Windows 11 recommended, Windows 10 best effort (1809+); native sandbox by default, WSL2 when Linux tooling is needed; standalone PowerShell installer; hooks have `commandWindows` [x-winsandbox], [x-wsl], [x-cli], [x-hooks] | Windows 11 24H2+, shell PowerShell, Node 20+; `%USERPROFILE%\.gemini\commands`; system settings in `C:\ProgramData`; WSL not mentioned on the install page [g-install], [g-cmds], [g-enterprise] | PowerShell and WSL; WinGet install, PowerShell 6+ on the install page, PowerShell 7.0+ on the hooks page; user hooks in `%USERPROFILE%\.copilot\hooks\` [p-about], [p-install], [p-hooks] | CI smoke test only (start, plan, apply with a ledger run); untested by the owner (`app/README.md:39`, `docs/setup.md:33`) |

## Gap per agent

Gemini CLI (against what Claude Code and Codex get):

- Plugins: extension install, update and uninstall exist ([g-extref]); BenchKeeper installs skill copies only.
- Hooks, MCP and subagent inventory in `extensions list`: documented locations ([g-hooks], [g-mcp], [g-subagents]); not built.
- Usage, limits, accounts, auto-pick: no documented source, see Short answer 4 and 5.
- Evals: headless JSON and streaming JSONL with `tool_use` and `tool_result` events are documented ([g-headless]); per-session skill trigger detection was not checked against them.
- Product risk: see Short answer 1.

Copilot CLI:

- Project settings: `.github/copilot/settings.json` and `settings.local.json` exist; `agents.json` has none. `enabledPlugins` and `hooks` live there ([p-cfgdir], [p-plugins]).
- Plugins: documented package, marketplaces and settings key ([p-plugins]); BenchKeeper installs skill copies only.
- Hooks, MCP and subagent inventory in `extensions list`: documented locations ([p-hooks], [p-mcp], [p-agents]); not built.
- Usage, limits, accounts, auto-pick: interactive `/usage` and `/limits` only, see Short answer 4 and 5.
- Evals: `-p` and JSONL output are documented but the record fields are not ([p-prog]).

Windows:

- The four agents document native Windows paths for config (`%USERPROFILE%` forms), hooks and install. BenchKeeper's own Windows coverage is a smoke test.
- Sandbox: native support differs (Claude Code none, Codex native, Gemini native with unknown enabling steps, Copilot recent Windows 11).

## What is unverified

- Whether any agent exposes remaining limit percentage to a script other than Claude Code. Codex `/statusline` footer items might include rate-limit items (a Codex maintainer says so in a GitHub issue, not in the documentation I read), and `tui.status_line` is documented only as "item identifiers".
- Codex `config.toml` JSON schema: not found in [x-configbasic] or the part of [x-configref] I read (about 100,000 of 156,740 characters).
- Exit codes for `codex exec` and `copilot -p`.
- Gemini: the credential cache path, the exact streaming flag value (`--output-format` takes JSON and streaming JSON, value not stated on [g-headless]), how the Windows Native sandbox is turned on ([g-sandbox] omits the steps), where extension hooks are located beyond `hooks/hooks.json` in [g-extref].
- Copilot: `statusLine` input fields, `-p` JSONL record fields, where the login is cached, whether `COPILOT_HOME` isolates it, the complete `settings.json` key list (the page read ended at 200,000 of 200,838 characters), the exact stable path of the session transcript beyond `session-state/<id>/events.jsonl` ([p-cfgdir]).
- Whether Codex's portable `plugin.json` and Copilot's Agent Plugins 1.0 are the same specification; if they are, one manifest could serve both. [x-buildplugins] and [p-plugins] do not say.
- Two OpenAI pages disagree on plugin hooks: [x-hooks] says installed plugins can bundle hooks through `hooks/hooks.json`; [x-buildplugins] says hooks are "Supported only for manually installed Codex desktop plugins". Not resolved here. It bears on the Ponytail `SessionStart` hook in Codex (`docs/setup.md:44`).
- Antigravity CLI: hooks, subagents and Windows support are not covered by [g-migration]; settings file format beyond the MCP move is not described.
- Whether other agents' transcripts allow the "unused skill" signal of `insights` (`app/README.md:64`, Claude Code sessions only today). Copilot documents `session-state/<id>/events.jsonl` without a field list; Codex and Gemini transcripts were not checked.
- Whether BenchKeeper's own hooks and scripts run on Windows (not part of the agents' documentation).
- Redirects: `developers.openai.com/codex/...` pages answer with a permanent redirect to `learn.chatgpt.com/docs/...`; the cited Codex URLs are the redirect targets as fetched. `developers.openai.com/plugins/build/plugins` was fetched directly.

## Sources

[c-setup]: https://code.claude.com/docs/en/setup
[c-memory]: https://code.claude.com/docs/en/memory
[c-settings]: https://code.claude.com/docs/en/settings
[c-statusline]: https://code.claude.com/docs/en/statusline
[c-sandbox]: https://code.claude.com/docs/en/sandboxing
[c-hooks]: https://code.claude.com/docs/en/hooks
[c-plugins]: https://code.claude.com/docs/en/plugins
[c-skills]: https://code.claude.com/docs/en/skills
[c-subagents]: https://code.claude.com/docs/en/sub-agents
[c-mcp]: https://code.claude.com/docs/en/mcp
[c-headless]: https://code.claude.com/docs/en/headless
[c-auth]: https://code.claude.com/docs/en/authentication
[x-agentsmd]: https://learn.chatgpt.com/docs/agent-configuration/agents-md
[x-skills]: https://learn.chatgpt.com/docs/build-skills
[x-plugins]: https://learn.chatgpt.com/docs/plugins
[x-buildplugins]: https://developers.openai.com/plugins/build/plugins
[x-hooks]: https://learn.chatgpt.com/docs/hooks
[x-configbasic]: https://learn.chatgpt.com/docs/config-file/config-basic.md
[x-configref]: https://learn.chatgpt.com/docs/config-file/config-reference
[x-subagents]: https://learn.chatgpt.com/docs/agent-configuration/subagents.md
[x-exec]: https://learn.chatgpt.com/docs/non-interactive-mode
[x-auth]: https://learn.chatgpt.com/docs/auth.md
[x-mcp]: https://learn.chatgpt.com/docs/extend/mcp.md
[x-sandbox]: https://learn.chatgpt.com/docs/sandboxing.md
[x-commands]: https://learn.chatgpt.com/docs/developer-commands.md?surface=cli
[x-cli]: https://learn.chatgpt.com/docs/codex/cli.md
[x-winsandbox]: https://learn.chatgpt.com/docs/windows/windows-sandbox
[x-wsl]: https://learn.chatgpt.com/docs/windows/wsl.md
[g-blog]: https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/
[g-migration]: https://antigravity.google/docs/cli/gcli-migration
[g-md]: https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/gemini-md.md
[g-skills]: https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/skills.md
[g-ext]: https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/extensions/index.md
[g-extref]: https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/extensions/reference.md
[g-hooks]: https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/hooks/index.md
[g-config]: https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/reference/configuration.md
[g-subagents]: https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/core/subagents.md
[g-headless]: https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/headless.md
[g-sandbox]: https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/sandbox.md
[g-quota]: https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/resources/quota-and-pricing.md
[g-mcp]: https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/tools/mcp-server.md
[g-cmds]: https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/custom-commands.md
[g-enterprise]: https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/enterprise.md
[g-install]: https://geminicli.com/docs/get-started/installation/
[g-auth]: https://geminicli.com/docs/get-started/authentication/
[p-about]: https://docs.github.com/en/copilot/concepts/agents/about-copilot-cli
[p-install]: https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/install-copilot-cli
[p-instr]: https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions
[p-skills]: https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills
[p-agents]: https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli
[p-mcp]: https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers
[p-hooks]: https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-hooks
[p-plugins]: https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-cli-plugins
[p-sandbox]: https://docs.github.com/en/copilot/concepts/about-cloud-and-local-sandboxes
[p-cfgdir]: https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference
[p-prog]: https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-programmatic-reference
[p-cmdref]: https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference
[p-overview]: https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/overview
