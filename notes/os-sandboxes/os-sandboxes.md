# OS sandboxes for a skill install preview and the agents' sandbox settings

Research for ESchuderer/BenchKeeper issue #375. Read on 2026-10-27. It feeds #286 (confine a skill install preview) and #312 (sandbox hardening settings in the catalog and a doctor check).

## Question

Which OS-level confinement can BenchKeeper use for the skill install preview (`app/src/prerun.mjs`) on Linux, macOS and Windows, and which sandbox settings do Claude Code and Codex document, with their platform support and prerequisites? Which hosts does a skills CLI install need to reach?

## Short answer

- Linux and WSL2: bubblewrap is the unprivileged primitive both agents use. It gives filesystem confinement and an all-or-nothing network switch (`--unshare-net`). It has no host allowlist. A host allowlist needs a proxy outside the sandbox, which is what Claude Code's sandbox does.
- macOS: Seatbelt through `sandbox-exec` works, but the tool is marked deprecated in its man page and Apple's developer support calls the profile language an undocumented implementation detail. Claude Code and Codex both still build on it.
- Windows: no agent-independent, documented, low-friction option. AppContainer is documented but is an app-model primitive with per-capability network switches, no domain filter, and file access through ACLs. Job Objects limit resources and process lifetime, not files or network. WSL2 is Linux and works with bubblewrap. Microsoft's new MXC SDK (early preview) and Anthropic's `sandbox-runtime` Windows backend (alpha) are the two policy-driven options, both pre-release.
- A ready wrapper exists: Anthropic's `@anthropic-ai/sandbox-runtime` (`srt`, Apache-2.0, beta research preview) wraps a command with a filesystem policy and a domain allowlist on macOS, Linux and, in alpha, Windows. It is the only single tool found that covers the preview's two gaps (absolute-path writes and the network) on all three OSes.
- Network confinement of the preview cannot be "off" if the preview runs the real command: a skills CLI install needs `registry.npmjs.org`, `github.com` and `api.github.com` (table below). A sandbox with no network cannot rehearse it.
- Claude Code settings: `sandbox.enabled`, `sandbox.failIfUnavailable`, `sandbox.allowUnsandboxedCommands` and `sandbox.network.allowedDomains` can be set in any settings file. `sandbox.network.strictAllowlist` and `sandbox.filesystem.disabled` are honored only from user or managed settings. Codex: `sandbox_mode = "workspace-write"` keeps the network off by default; a domain allowlist needs the experimental `features.network_proxy`.

## Linux and WSL2

| Option | What it does | Platform support and prerequisites | Source |
|---|---|---|---|
| bubblewrap (`bwrap`) | Builds a sandbox from an empty tmpfs root plus explicit bind mounts, with user, IPC, PID, network and UTS namespaces and optional seccomp. The project says it "is not a complete, ready-made sandbox with a specific security policy": the protection depends on the arguments. | Linux. Runs unprivileged through user namespaces. The setuid mode was removed. Current release v0.13.1 (2026-10-14). | https://github.com/containers/bubblewrap , https://api.github.com/repos/containers/bubblewrap/releases/latest |
| `--unshare-net` | New network namespace: no network, no host filter. | Needs `--unshare-user` unless root. | https://raw.githubusercontent.com/containers/bubblewrap/main/bwrap.xml |
| `--ro-bind`, `--bind`, `--tmpfs` | Read-only bind, read-write bind, fresh tmpfs: the filesystem policy. | Same. | same |
| `--die-with-parent`, `--new-session` | Child dies with the parent. `--new-session` calls `setsid()`; the README requires it unless TIOCSTI is filtered by seccomp (out-of-sandbox command execution). | Same. | https://github.com/containers/bubblewrap , bwrap.xml |
| `--clearenv`, `--setenv` | Drop and set environment variables. | Same. | bwrap.xml |
| `--disable-userns` | Stops the sandboxed process creating further user namespaces. | Requires `--unshare-user`. | bwrap.xml |
| Ubuntu 24.04+ AppArmor | `kernel.apparmor_restrict_unprivileged_userns=1` can block bubblewrap; the fix is an AppArmor profile for `/usr/bin/bwrap` with `userns,`. | Ubuntu 24.04 and later. | https://code.claude.com/docs/en/sandboxing |
| WSL2 | Linux kernel in a lightweight VM. bubblewrap works. Distributions share one network namespace. Windows drives are auto-mounted under `/mnt` and Windows process launching is enabled by default (`[automount] enabled=true`, `[interop] enabled=true`), so a bubblewrap policy must hide the mounted Windows drives itself. | Windows with WSL2. WSL1 is not supported by Claude Code or Codex. | https://learn.microsoft.com/en-us/windows/wsl/about , https://learn.microsoft.com/en-us/windows/wsl/wsl-config |
| `srt` (sandbox-runtime) on Linux | bubblewrap plus a removed network namespace; traffic goes over Unix sockets to a host proxy that enforces `allowedDomains` and `deniedDomains`. Seccomp blocks Unix sockets (x64 and arm64 filters shipped). | Needs `bubblewrap`, `socat`, `ripgrep`; bubblewrap 0.4.0 or later, 0.5.0 or later recommended; as root it needs `CAP_SETFCAP`. Node 22.12 or later. Beta research preview, version 0.0.81 on 2026-10-20. | https://github.com/anthropics/sandbox-runtime , https://registry.npmjs.org/@anthropic-ai/sandbox-runtime |

## macOS

| Option | What it does | Platform support and prerequisites | Source |
|---|---|---|---|
| `sandbox-exec` with Seatbelt profiles | Runs a command under a profile (`-f`, `-n`, `-p`, `-D key=value`). The man page marks it deprecated and points to App Sandbox. | Built in. Apple developer support (a DTS engineer on the Apple Developer Forums, as relayed by the fetch tool, not re-checked against the raw page) says the sandbox profile language (SBPL) has never been documented for third-party use, is not considered API, and is an implementation detail; everything in `<sandbox.h>` is deprecated. Supported options named by DTS: Endpoint Security, App Sandbox, Virtualization. DTS also wrote that macOS 27 added `es_new_descendants_client` in Endpoint Security as the approach for third-party developers who sandbox child processes. | https://developer.apple.com/forums/thread/777509 , https://leancrew.com/all-this/man/man1/sandbox-exec.html (mirror of the man page; Apple's own man page was not fetched) |
| App Sandbox | Entitlement-based sandbox (`com.apple.security.app-sandbox`), applied to signed apps. | Not fetched from Apple's page (the fetch returned no body). DTS says it uses the same underlying implementation and may hit the same limits. | https://developer.apple.com/forums/thread/777509 |
| Claude Code sandbox on macOS | Uses the built-in Seatbelt framework; by default only the connection to the sandbox proxy is allowed. | No prerequisites. | https://code.claude.com/docs/en/sandboxing |
| Codex sandbox on macOS | Seatbelt policies; commands run through `sandbox-exec` with a profile that matches the selected sandbox mode. When it cannot enforce a policy it refuses to run the command instead of running it unsandboxed. | No prerequisites. | https://learn.chatgpt.com/docs/agent-approvals-security , https://learn.chatgpt.com/docs/permissions |
| `srt` on macOS | Generated Seatbelt profiles; network limited to a localhost port where the host proxies listen. Masked credential files are not supported (denied instead). | Needs `ripgrep` only. | https://github.com/anthropics/sandbox-runtime |

## Windows

| Option | What it does | Platform support and prerequisites | Source |
|---|---|---|---|
| AppContainer | Isolation by least privilege: file and registry access only where granted, network access granted per class (Internet, intranet, server), credential, device, process and window isolation. Created per user and per app with `CreateAppContainerProfile`, which takes capability SIDs. | Windows 8 and later, desktop apps. No domain-level network filter is documented on these pages. Loopback behavior for an AppContainer: unverified. | https://learn.microsoft.com/en-us/windows/win32/secauthz/appcontainer-isolation , https://learn.microsoft.com/en-us/windows/win32/api/userenv/nf-userenv-createappcontainerprofile |
| Job Objects | Group processes and enforce limits such as working set, priority, end-of-job time; `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` ends all processes when the last handle closes; UI restrictions exist. The documentation lists no filesystem or network restriction. Association cannot be undone; nesting from Windows 8. | Win32 API, no installation. Useful for cleanup and limits only. | https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects |
| WSL2 | See the Linux table: bubblewrap inside the distribution. Claude Code and Codex both use this path on Windows. | WSL2 only. | https://code.claude.com/docs/en/sandboxing , https://learn.chatgpt.com/docs/agent-approvals-security |
| MXC (Microsoft Execution Containers) | "A cross-platform, policy-driven execution layer for agents on Windows and WSL". Process isolation limits access to files and network domains outside policy; session isolation uses a separate user account. The Windows developer blog says GitHub Copilot CLI has adopted it. Codex selects it with `windows.sandbox = "mxc"`. | SDK in early preview. The repository states Windows 11 (x64 and arm64), Linux and macOS; default Windows backend `processcontainer`; MIT; npm `@microsoft/mxc-sdk`, NuGet `Microsoft.Mxc.Sdk`, crate `mxc-sdk`. The repository documents `network.egress.default: 'deny'` and "backend-dependent host filtering", no domain rule syntax. The Windows 11 build number is not stated. | https://blogs.windows.com/windowsdeveloper/2026/06/02/windows-platform-security-for-ai-agents/ , https://github.com/microsoft/mxc |
| `srt` on Windows (alpha) | Runs the command as a dedicated `srt-sandbox` local user, with a Windows Filtering Platform egress fence that allows only loopback to the proxy ports, a write-restricted token and ACEs on configured paths. | Alpha. One elevated, one-time `npx @anthropic-ai/sandbox-runtime windows-install` (UAC prompt). TLS stacks built on Schannel (`curl.exe` in System32, PowerShell `Invoke-WebRequest`, .NET `HttpClient`, `winget`, cargo) fail inside it; the profile read grant leaves `.npmrc` readable. Known fence gaps: a thread that swaps its token, and traffic carried by system services. | https://github.com/anthropics/sandbox-runtime |
| Claude Code on native Windows | "On native Windows, Claude Code runs commands unsandboxed." Use WSL2. | n/a | https://code.claude.com/docs/en/sandboxing |
| Codex on native Windows | Native Windows sandbox: MXC, or the legacy `elevated` (lower-privilege sandbox users, filesystem boundaries, firewall rules) and `unelevated` (weaker network isolation, cannot enforce every read/write carve-out). | `windows.sandbox` = `mxc`, `elevated` or `unelevated`; `features.prefer_mxc = true` prefers MXC with fallback. | https://learn.chatgpt.com/docs/permissions , https://learn.chatgpt.com/docs/config-file/config-reference |

## Claude Code sandbox settings

Behavior: https://code.claude.com/docs/en/sandboxing . Scope per key: https://code.claude.com/docs/en/settings-reference (index rows). "Any file" means user, project, local and managed settings. The sandbox as a whole runs on macOS, Linux and WSL2; WSL1 and native Windows are not supported.

| Key | Meaning | Platform support and prerequisites | Scope | Source |
|---|---|---|---|---|
| `sandbox.enabled` | Turns Bash sandboxing on. Off by default. Covers Bash, PowerShell and Monitor and their children, not the file tools, MCP servers, hooks, LSP servers, status line commands or `apiKeyHelper`. | macOS, Linux, WSL2; Linux and WSL2 need `bubblewrap` and `socat` | Any file | https://code.claude.com/docs/en/sandboxing |
| `sandbox.failIfUnavailable` | `true`: Claude Code exits at startup when the sandbox cannot run (missing dependency, unsupported platform). Default: commands run unsandboxed. Minimum version: unverified. | same | Any file | https://code.claude.com/docs/en/sandboxing |
| `sandbox.allowUnsandboxedCommands` | `false`: the `dangerouslyDisableSandbox` retry is ignored ("Strict sandbox mode"). In managed settings it also makes Claude Code ignore repository settings that loosen the sandbox. | same | Any file | https://code.claude.com/docs/en/sandboxing |
| `sandbox.autoAllowBashIfSandboxed` | Default `true`: sandboxed commands run without a prompt. | same | Any file | https://code.claude.com/docs/en/sandboxing |
| `sandbox.excludedCommands` | Patterns that run outside the sandbox with full access ("An excluded command runs with your full access."). | same | Any file | https://code.claude.com/docs/en/sandboxing |
| `sandbox.network.allowedDomains` | Hosts the proxy allows; starts empty; `*.` wildcards; an entry without a port allows every port. A host not on the list is prompted, not denied, unless `strictAllowlist`. Broad entries such as `github.com` allow exfiltration paths (domain fronting). | same; the proxy runs on the host, Linux reaches it through `socat` | Any file | https://code.claude.com/docs/en/sandboxing |
| `sandbox.network.deniedDomains` | Blocks hosts even inside a broader allow. | same | Any file | https://code.claude.com/docs/en/sandboxing |
| `sandbox.network.strictAllowlist` | Deny hosts outside the allowlist instead of prompting. Needs v2.1.219 or later. | same | User or managed only | https://code.claude.com/docs/en/sandboxing |
| `sandbox.network.allowManagedDomainsOnly` | Only managed `allowedDomains` count. | same | Managed only | https://code.claude.com/docs/en/sandboxing |
| `sandbox.network.allowLocalBinding` | Listen on ports and connect to localhost; no effect on direct localhost connections on Linux and WSL2. | macOS effective | Any file | https://code.claude.com/docs/en/sandboxing |
| `sandbox.filesystem.allowWrite`, `denyWrite`, `denyRead`, `allowRead` | Path policy. Default: writes to the working directory, `$TMPDIR` and added directories; reads of the whole machine except denied paths (credential files such as SSH keys stay readable by default). | macOS, Linux, WSL2; Linux and WSL2 need `bubblewrap` and `socat` | Any file | https://code.claude.com/docs/en/sandboxing |
| `sandbox.filesystem.disabled` | Turn off filesystem isolation, keep network isolation. Needs v2.1.216 or later. | same | User or managed only | https://code.claude.com/docs/en/sandboxing |
| `permissions.blockReadsOutsideWorkingDirectories` | Blocks sandboxed commands reading the home directory and other user-file directories outside the working directory. Needs v2.1.257 or later; `true` is honored from any scope. | same | Any scope (`true`) | https://code.claude.com/docs/en/settings |
| `sandbox.credentials.files`, `sandbox.credentials.envVars` | `deny` or `mask` credential files and variables. File masking needs v2.1.221 or later and does not work on macOS (masked files are unreadable there). | same | Any file | https://code.claude.com/docs/en/sandboxing |
| `sandbox.enableWeakerNestedSandbox` | For unprivileged containers such as Docker; the page says it "considerably weakens security". | Linux inside a container | Any file | https://code.claude.com/docs/en/sandboxing |
| `sandbox.allowNestedUserNamespaces` | Lets Chromium, nested bubblewrap or `unshare` create user namespaces; turns off a security boundary. Needs v2.1.305 or later. | Linux and WSL2 | User or managed only | https://code.claude.com/docs/en/sandboxing |
| `sandbox.allowAppleEvents` | Lets sandboxed commands use Apple Events; removes code-execution isolation. | macOS only | User or managed only | https://code.claude.com/docs/en/sandboxing |

## Codex sandbox settings

The old `developers.openai.com/codex/...` URLs answer with a permanent redirect to the `learn.chatgpt.com` pages below.

| Key | Meaning | Platform support and prerequisites | Source |
|---|---|---|---|
| `sandbox_mode` | `read-only`, `workspace-write`, `danger-full-access`. In a version-controlled folder the default is Auto (`workspace-write` with on-request approval); otherwise read-only until the folder is trusted. | macOS: Seatbelt, nothing to install. Linux and WSL2: `bubblewrap` (Codex uses the first `bwrap` on `PATH`, else a bundled helper that needs unprivileged user namespaces; Ubuntu 24.04 may need an AppArmor profile). WSL1: dropped after Codex 0.114. Native Windows: see the Windows table. | https://learn.chatgpt.com/docs/sandboxing , https://learn.chatgpt.com/docs/agent-approvals-security |
| `approval_policy` | `on-request`, `never`, or `{ granular = { ... } }`; `untrusted` is unsupported and `on-failure` deprecated. | All platforms. | https://learn.chatgpt.com/docs/config-file/config-reference |
| `sandbox_workspace_write.network_access` | Outbound network inside `workspace-write`. The agent runs with the network off by default. | Same as `sandbox_mode`. | https://learn.chatgpt.com/docs/agent-approvals-security , https://learn.chatgpt.com/docs/config-file/config-reference |
| `sandbox_workspace_write.writable_roots`, `exclude_tmpdir_env_var`, `exclude_slash_tmp` | Extra writable roots; drop `$TMPDIR` or `/tmp` from the writable set. | Same as `sandbox_mode`. | https://learn.chatgpt.com/docs/config-file/config-reference |
| `default_permissions` with `permissions.<name>.filesystem` | Beta permission profiles (`:read-only`, `:workspace`, `:danger-full-access`, own names). `read`, `write`, `deny`; deny wins. Not to be combined with `sandbox_mode`. Deny-read globs are snapshotted when the process starts. | macOS: per the page Codex refuses to run a command when it cannot enforce the policy instead of running it unsandboxed. Linux and WSL: bubblewrap and seccomp; the legacy Landlock option is rejected for filesystem-restricted policies. | https://learn.chatgpt.com/docs/permissions , https://learn.chatgpt.com/docs/config-file/config-reference |
| `permissions.<name>.network.enabled`, `.mode`, `.domains.<pattern>` | `allow` or `deny` per host pattern (`*.example.com`, `**.example.com`, `*`). `enabled = true` does not start the proxy; with the proxy off, network access is direct and unrestricted and domain rules are not enforced. | Same as `sandbox_mode`. | https://learn.chatgpt.com/docs/permissions , https://learn.chatgpt.com/docs/config-file/config-reference |
| `features.network_proxy` | Starts the proxy that enforces domain rules; the config reference marks it experimental and off by default. It does not filter web search, apps, MCP or other hosted tools. An administrator's `experimental_network` requirement can start it instead. | Same as `sandbox_mode`. | https://learn.chatgpt.com/docs/permissions , https://learn.chatgpt.com/docs/config-file/config-reference |
| `windows.sandbox`, `features.prefer_mxc` | Native Windows backend: `mxc`, `elevated`, `unelevated`; `prefer_mxc = true` prefers MXC with fallback. | Native Windows; MXC needs Windows 11 per the MXC repository. | https://learn.chatgpt.com/docs/config-file/config-reference , https://learn.chatgpt.com/docs/permissions |
| `requirements.toml`: `allowed_sandbox_modes`, `allowed_approval_policies`, `allowed_permission_profiles` | Admin-enforced constraints on the keys above. | Permission-profile allowlists need Codex 0.138.0 or later. | https://learn.chatgpt.com/docs/config-file/config-reference |
| Containers (Docker and similar) | Per the page the sandbox may not work when the host or container configuration blocks the namespace, setuid `bwrap` or `seccomp` operations Codex needs; the page suggests isolating the container and running `danger-full-access` inside it. | Linux containers. | https://learn.chatgpt.com/docs/agent-approvals-security |

## Hosts a skills CLI install needs

Primary source: the `skills` 1.7.2 package itself (https://registry.npmjs.org/skills/-/skills-1.7.2.tgz, `dist/cli.mjs`), read for the commands BenchKeeper runs: `npx -y skills@npm:skills@1.7.2 add https://github.com/<owner>/<repo>/tree/<commit> -s <name> [-g] --copy -y` with `DO_NOT_TRACK=1` (`app/src/steps/global.mjs:335`, `app/src/steps/project.mjs:432`). Line numbers below refer to that `cli.mjs`.

| Host | Why | When | Evidence |
|---|---|---|---|
| `registry.npmjs.org` | `npx` downloads the CLI tarball (`dist.tarball` is `https://registry.npmjs.org/skills/-/skills-1.7.2.tgz`) and its two dependencies `tar` and `yaml`. | Always, unless the user's npm settings name another registry or a cache holds it. The preview copies the user's registry, proxy and certificate settings. | Registry metadata; `package.json` `dependencies`. |
| `github.com` | `git clone --depth 1` of the repository in the URL, with the commit as ref. | Always for a GitHub source (`cloneRepo`, line 930). Redirects git may follow: unverified. | `cli.mjs:915-935`. |
| `api.github.com` | `GET /repos/<owner>/<repo>` to test whether the source is private (`isRepoPrivate`, line 82, called from `add` at line 5339); `GET /repos/<owner>/<repo>/git/trees/<ref>?recursive=1` to record the skill's folder hash in the global lock file (`fetchRepoTree`, line 5729, when installing with `-g` and no blob install). | Every GitHub source; the tree call for global installs. Failures are caught in the code read; what the user sees when the host is blocked: unverified (not run). | `cli.mjs:80-90`, `3840-3860`, `5333-5340`, `5726-5730`. |
| `www.skills.sh` | Telemetry (`/tele/t`) and audit data (`/tele/audit`). | Skipped when `DO_NOT_TRACK` or `DISABLE_TELEMETRY` is set (line 2808); BenchKeeper sets `DO_NOT_TRACK=1`. | `cli.mjs:2797-2835`. |
| `raw.githubusercontent.com`, `skills.sh` (`/api/download/...`) | "Blob install" shortcut. | Only for owners `vercel`, `vercel-labs`, `heygen-com`, `remotion-dev` or `zapier/connectors` and only when the URL has no ref (`tryBlobInstall` returns null when a ref is given, line 4111). BenchKeeper's URLs carry a commit, so this path is not taken. | `cli.mjs:4110-4112`, `5083-5100`. |
| `gitlab.com`, other hosts, `/.well-known/agent-skills/` | Other source types. | Not used by BenchKeeper's GitHub-only sources (`plugins/benchkeeper/library/library.json` has no non-GitHub URL). | `cli.mjs:3134-3136`. |

The signature check that runs before the preview (`app/src/verify.mjs`, `npm install` then `npm audit signatures`) runs outside the rehearsal (`app/src/prerun.mjs`), so a sandbox around the rehearsal does not need to allow it. Which hosts `npm audit signatures` contacts: unverified.

So a preview sandbox with a domain allowlist would need: `registry.npmjs.org`, `github.com`, `api.github.com` (and a user's own registry host if `.npmrc` sets one).

## Notes for the two tickets

For #286 (facts only, no decision):
- bubblewrap gives all-or-nothing network. A limit to registry hosts needs a host-side proxy reached through a Unix socket, which `srt` ships on Linux, macOS and (alpha) Windows.
- The rehearsal runs the real command, so a sandbox with no network defeats it. Either the allowlist above, or the preview is skipped where no sandbox exists (the owner's second decision in #286).
- A write confinement alone (`--ro-bind` the system, `--bind` the scratch folder) stops absolute-path writes, which is the first gap named in `docs/security.md:87`.
- On Windows nothing documented gives both gaps without installing something privileged (`srt` alpha needs an elevated install) or an unreleased SDK (MXC preview).

For #312:
- `failIfUnavailable`, `allowUnsandboxedCommands` and `network.allowedDomains` can be written to project settings; `strictAllowlist` and `filesystem.disabled` cannot, so a doctor check of the project file cannot see them and a catalog entry for `strictAllowlist` belongs in the user file.
- Without `strictAllowlist`, an off-list host produces a prompt, not a denial.
- Codex: the doctor check would read `sandbox_mode`, `sandbox_workspace_write.network_access` and `features.network_proxy` in `config.toml`; a managed `requirements.toml` can constrain them.

## Not verified

- Apple's own `sandbox-exec(1)` man page and the App Sandbox documentation page: not read (the man page only through a third-party mirror; the Apple page returned no text). The deprecation of the tool rests on that mirror and on the DTS forum post.
- The macOS 27 `es_new_descendants_client` statement is from a DTS forum reply, not from Apple's reference documentation.
- Whether an AppContainer process can reach loopback (a host-side proxy) without the loopback exemption: not found in the pages read.
- The Windows 11 build that MXC and Codex's `mxc` backend require; whether Copilot CLI's use of MXC is current (blog statement only).
- The minimum Claude Code version of `sandbox.failIfUnavailable` and `sandbox.allowUnsandboxedCommands`.
- The `settings-reference` page was read only up to its index rows (it is long); `strictAllowlist` and `filesystem.disabled` scopes come from those rows.
- Hosts contacted by `npm audit signatures`, redirects of `git clone` against github.com, and the behavior of the skills CLI when `api.github.com` is blocked: not run.
- Whether `sandbox-runtime` (`srt`) can wrap `npx` with its npm cache and git on all three OSes: not run. Its Windows backend is alpha.
- Codex's behavior when bubblewrap is missing on Linux (the pages read give no fallback statement).
- Landlock on Linux as an alternative to bubblewrap: not researched; Codex's permissions page says it rejects the legacy Landlock option for filesystem-restricted policies.
