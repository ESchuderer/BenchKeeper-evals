# srt around the skill install preview: prototype result (issue 405)

Verdict: works with conditions, on Linux, inside a rootless podman container. The conditions are listed under "Verdict". macOS, Windows and a plain Linux host were not tested.

## Setup

- Tool: `@anthropic-ai/sandbox-runtime` (`srt`), exact version 0.0.81, published 2026-10-20T01:13:23Z on the npm registry (8 days before the run on 2026-10-28), `latest` tag, Apache-2.0, `engines.node >=22.12.0`. Source: https://www.npmjs.com/package/@anthropic-ai/sandbox-runtime and https://github.com/anthropics/sandbox-runtime. The URL `https://github.com/anthropic-experimental/sandbox-runtime` answers 301 and redirects to the `anthropics` one. The README calls it a "Beta Research Preview".
- Host: Linux 7.3 (CachyOS), podman 6.1.4 rootless.
- Dev container: `devcontainer up --docker-path podman --workspace-folder .` does not build today. Step 2 of `.devcontainer/Dockerfile` fails with `E: Version '20250419~deb12u1' for 'ca-certificates' was not found` (the exact Debian pin the Dockerfile comment calls a shortcut). It was not changed. The prototype used a throwaway image instead: the same base `docker.io/library/node:22.23.3-bookworm-slim@sha256:efd0ab5780c2d9ab1f0f869571a00d5edb17793bff4cce4a2792e3eb0ffc7562`, user `node`, plus `git ca-certificates bubblewrap socat ripgrep` unpinned (Debian bookworm: bubblewrap 0.8.0, ripgrep 13.0.0), started with the same user namespace flag as `.devcontainer/compose.yaml` (`--userns=keep-id:uid=1000,gid=1000`). No Playwright. The container has no extra capabilities and no `--privileged`.
- Two containers of that image: `bk-srt` (podman defaults) and `bk-srt2` (adds `--security-opt 'unmask=/proc/*'`). srt was installed in each with `npm i --save-exact @anthropic-ai/sandbox-runtime@0.0.81` in `/tmp/srt`.
- Scripts and the Dockerfile: `notes/srt-preview-prototype/srt-preview/` (mounted read-only at `/work`). `run.mjs` mirrors `app/src/prerun.mjs` (scratch folder with `h` and `p`, scratch `HOME`, empty git config, npmrc without credentials, `DO_NOT_TRACK=1`, `npm_config_registry`, `npm_config_ignore_scripts=true`, `npm_config_before` seven days back) and runs the command bare or under srt with `spawnSync(argv)`, no shell. `probe.mjs` is a set of single-action probes. `suite.mjs`, `extra.mjs`, `hosts.mjs`, `precreate.mjs`, `diff.mjs`, `facts.mjs` drive the checks.

## What was run

Build and start (host):

```
podman build -t bk-srt-proto notes/srt-preview-prototype/srt-preview   # uses notes/srt-preview-prototype/srt-preview/Dockerfile
podman run -d --name bk-srt  --init --userns=keep-id:uid=1000,gid=1000 -v <repo>/notes/srt-preview-prototype/srt-preview:/work:ro,z localhost/bk-srt-proto sleep infinity
podman run -d --name bk-srt2 --init --userns=keep-id:uid=1000,gid=1000 --security-opt 'unmask=/proc/*' -v <repo>/notes/srt-preview-prototype/srt-preview:/work:ro,z localhost/bk-srt-proto sleep infinity
```

The command under test is the preview command of `app/src/steps/project.mjs` (project) and `app/src/steps/global.mjs` (with `-g`), at the pinned skills CLI, source `https://github.com/anthropics/skills`, skill `skill-creator` (37 files):

```
npx -y skills@npm:skills@1.7.2 add https://github.com/anthropics/skills -s skill-creator -a claude-code -a codex --copy -y
```

Wrapped, `run.mjs` spawns this argv (no shell on the app side):

```
srt --settings <scratch>/srt.json -- npx -y skills@npm:skills@1.7.2 add https://github.com/anthropics/skills -s skill-creator -a claude-code -a codex --copy -y
```

`--` is required: the skills flags `-s` and `-c` collide with srt's own options. The settings file:

```json
{ "network": { "allowedDomains": ["registry.npmjs.org", "github.com", "api.github.com"], "deniedDomains": [] },
  "filesystem": { "denyRead": ["<real home>/.ssh"], "allowRead": [], "allowWrite": ["<scratch folder>"], "denyWrite": [] } }
```

Also set: `CLAUDE_CODE_TMPDIR=<scratch>/tmp` in the environment of srt, and an empty `<scratch>/p/.claude/skills` and `<scratch>/h/.claude/skills` (both explained below). Runs (in the container):

```
podman exec bk-srt  node /work/run.mjs srt --cache=real --debug            # first run, default container
podman exec bk-srt  node /work/run.mjs srt --cache=real --extra='{"enableWeakerNestedSandbox":true}'
podman exec bk-srt  node /work/suite.mjs weak
podman exec bk-srt2 node /work/suite.mjs
podman exec bk-srt2 node /work/extra.mjs
podman exec bk-srt2 node /work/hosts.mjs
podman exec bk-srt2 node /work/precreate.mjs
podman exec bk-srt2 node /work/diff.mjs --global bare-bare
podman exec bk-srt2 node /work/facts.mjs
```

## Failures on the way, with error text

1. Default container, default srt settings: srt starts bubblewrap and it stops before the command runs, exit 1:

   ```
   bwrap: Can't mount proc on /newroot/proc: Operation not permitted
   ```

   Cause: rootless podman masks paths under `/proc`, and the kernel refuses a fresh procfs in a nested user namespace then. User namespaces themselves are allowed (`bwrap --ro-bind / / --unshare-user --unshare-net --unshare-pid true` exits 0; `user.max_user_namespaces` is 2147483647). Two ways out, both tested with identical results on every check below:
   - Container flag: `--security-opt 'unmask=/proc/*'` (podman-run option, documented at https://docs.podman.io/en/latest/markdown/podman-run.1.html). srt keeps its fresh `/proc`.
   - srt setting `"enableWeakerNestedSandbox": true`. In `dist/sandbox/linux-sandbox-utils.js` (line 3057) this only drops `--proc /proc`, so the command sees the container's `/proc`. The README says the option "considerably weakens security". Not needed when the container flag is available.
2. With the sandbox up, the skills CLI stops with `ENOENT: no such file or directory, mkdtemp '/tmp/claude/skills-03MbIk'`. srt sets `TMPDIR` to `$CLAUDE_CODE_TMPDIR`, else `$CLAUDE_TMPDIR`, else the fixed `/tmp/claude`, and that folder must exist. Fix: set `CLAUDE_CODE_TMPDIR` to a folder inside the scratch folder.
3. Install of the Claude Code copy fails but the command exits 0 and the Codex copy is written (19 files instead of 37), in project and global mode:

   ```
   Failed to install 1 ... skill-creator -> Claude Code: ENOENT: no such file or directory, mkdir '<scratch>/p/.claude/skills'
   ```

   Cause: srt always denies writes to `.claude/commands` and `.claude/agents` (README, "Mandatory Deny Paths"). When `.claude` does not exist, bubblewrap covers the first missing folder, `.claude`, with an empty read-only folder, so `.claude/skills` cannot be created. Fix: create `.claude` (an empty `.claude/skills` is enough) in the scratch project and in the scratch home before the run. Then 37 files appear. Without the fix the preview would show an incomplete file list with a successful exit code.
4. npm cache read-only (`npm_config_cache` outside the allowed write paths): `npm error EROFS ... open '<home>/.npm/_cacache/tmp/<id>'` and, with a warm cache and `npm_config_offline=true`, `npm error code ENOTCACHED ... cache mode is 'only-if-cached' but no cached response is available`. A read-only npm cache does not work for this command (the `before` setting makes npm revalidate the packument and it writes cache files).

## Results

Fixes 2 and 3 are applied in all runs below. "Same" means the same relative file paths and the same content hashes as the run without srt.

### (c) The preview command finishes and lists the same files

| Case | Without srt | With srt (real cache writable) | With srt (scratch cache) |
|---|---|---|---|
| project, `skill-creator` | exit 0, 37 files, 1.7 s | exit 0, 37 files, same, 2.0 s | exit 0, 37 files, same, 2.5 s |
| global (`-g`, scratch home) | exit 0, 37 files, 1.8 s | exit 0, 37 files, same except the lock file | exit 0, 37 files, same except the lock file |

The global lock file `.agents/.skill-lock.json` differs by content between any two runs, with or without srt (timestamps): `diff.mjs --global bare-bare` shows the same difference between two runs without srt. The preview compares file content to the real home and would show it either way. In global mode srt also prints `bash: <scratch>/h/.bashrc: Permission denied` twice to stderr; the exit code is 0 and the files are complete.

Time, four runs each, seconds: without srt 1.4 1.4 2.0 1.5; srt with the real cache 2.0 2.1 1.9 1.9; srt with a scratch cache (cold npm download of the skills CLI) 2.5 2.4 2.4 2.8. Added time: about 0.5 s (real cache) to 1.0 s (scratch cache).

### (a) A write outside the scratch folder fails

Probe commands run under the same srt settings. "bare" is without srt.

| Probe | Without srt | With srt |
|---|---|---|
| write inside the scratch project | ok | ok |
| write `/tmp/bk-outside.txt` (absolute path outside the scratch folder) | ok | fails, `EROFS` |
| write a file in the real home | ok | fails, `EROFS` |
| write through a symlink in the scratch folder that points to the real home | ok | fails, `EROFS` |
| write `<scratch>/p/.bashrc` (srt mandatory deny) | ok | fails, `EACCES` |
| write `<home>/.npm/bk-marker.txt` with the real npm cache in `allowWrite` | ok | ok (not confined) |
| same, cache not in `allowWrite` (scratch cache) | ok | fails, `EROFS` |
| read `<home>/.ssh/id_test` (throwaway file) with `denyRead: [<home>/.ssh]` | ok | fails, `ENOENT` |
| read another file in the real home | ok | ok (reads are open by default) |

Reads are allow-by-default. A stricter setting was tried: `denyRead: [<real home>]` with a scratch npm cache. The command still finishes with the same 37 files (scratch folder under `/tmp`).

### (b) Network is limited to an allow list

| Probe (allow list `registry.npmjs.org`, `github.com`, `api.github.com`) | Without srt | With srt |
|---|---|---|
| `npm view skills@1.7.2 version` (registry) | ok | ok |
| `git ls-remote https://github.com/anthropics/skills HEAD` | ok | ok |
| `git ls-remote` of a gitlab.com repository | ok | fails: `CONNECT tunnel failed, response 403` |
| `npm view ... --registry https://registry.yarnpkg.com/` | ok | fails: `npm error 403 on a server you do not have access to` |
| same, after adding `registry.yarnpkg.com` to the allow list | ok | ok |
| raw TCP connect to `1.1.1.1:443`, no proxy | connected | fails: `ENETUNREACH` (the sandbox has no network interface; all traffic must pass the proxy) |

Hosts the preview command needs, with project and global mode and a scratch cache: `registry.npmjs.org` and `github.com` are enough (exit 0, 37 files, both modes). Only the registry, only github.com, or an empty list fail (exit 1, no files). `api.github.com` was never requested for this source (debug log: allowed requests were `registry.npmjs.org:443` and `github.com:443` only); keep it in the list only if a source or a later skills CLI needs it. A registry from the user's `.npmrc` has to be added to the list; the app already copies that registry setting into the scratch npmrc.

### (d) The command that runs is the exact argv

- The app side passes an argv array to `srt` and spawns without a shell, as `run.mjs` does.
- srt itself, on Linux and macOS, joins the argv into one shell-quoted string and runs it as `bash -c` (`dist/cli.js` lines 446 and 477, `quote()` in `dist/utils/shell-quote.js`). Example of the string: `npx -y skills@npm:skills@1.7.2 add https://github.com/o/r -s 'a b' '$(id)'`. So no shell string is built by BenchKeeper, but a shell parses srt's string inside the sandbox. On Windows srt spawns an argv with `shell: false` (same file, lines 467 and 468; not tested). The library function `SandboxManager.wrapWithSandboxArgv` does not remove the shell on Linux or macOS: its documentation comment in `dist/sandbox/sandbox-manager.js` (line 2084 and the block above it) says that on macOS and Linux the result is `[binShell, '-c', <wrapWithSandbox result>]`. Read from the source, not run. So "no shell string" is met on the app side only; inside the sandbox srt always runs `bash -c` on its own quoted string on Linux and macOS.
- Check: a child printed its `process.argv` for 17 hostile arguments (`a b`, `$(touch bk-inject1)`, `; touch bk-inject2`, `it's`, a backtick command, an argument with a line break, an empty string, `*`, `-s`, `--`, `-y`, `\n`, `~`, `$HOME`, a double-quoted word, `|x`, `&&`). The array under srt is identical to the array without srt, and no injected command ran (no `bk-inject*` file in the scratch folder).

### Missing prerequisites (issue check 5)

Simulated by pointing the setting at a path that does not exist (the packages were not removed): `bwrapPath`, `socatPath` and `ripgrep.command` each give exit 1 with `Error: Sandbox dependencies not available: bubblewrap (bwrap) not executable at /nonexistent/bwrap` (and the same wording for `socat not executable at ...` and `ripgrep (/nonexistent/rg) not found`). The command did not run (the marker file the command writes was absent), so there is no unconfined fallback. The `bwrap: Can't mount proc` failure above is the same class: exit 1, command not run, but the message comes from bubblewrap and does not name the cause.

Other observations: srt creates and removes empty placeholder files in the scratch folder while the command runs (`.gitconfig`, `.bashrc`, `.mcp.json`, `.vscode` and others), none were left in the file lists; no `/tmp/claude-empty-*` folder was left behind.

## Verdict: works with conditions

srt wraps the exact preview command, confines writes to the scratch folder, limits the network to the allow list, and the preview lists the same files as without it, on Linux in rootless podman. The tool is beta (version 0.0.x). The build issue must meet these conditions, or the result is wrong or weaker:

1. Prerequisites on Linux: `bubblewrap` (0.8.0 tested), `socat`, `ripgrep`, and unprivileged user namespaces (README: on Ubuntu 24.04 and later `kernel.apparmor_restrict_unprivileged_userns` must be off or an AppArmor profile must allow bubblewrap). Treat a non-zero exit of srt as "preview unavailable" and never retry the command without srt. Check for the three programs first and print an actionable message, because the bubblewrap failure text does not name the cause.
2. Inside a rootless podman or Docker container, srt needs `--security-opt 'unmask=/proc/*'` on `podman run` (or `enableWeakerNestedSandbox`, which is weaker). On a plain host this masking does not exist; that was not tested here, so the owner must run the host check below.
3. Set `CLAUDE_CODE_TMPDIR` to a folder inside the scratch folder for the srt process.
4. Create `.claude` (for the project and, in global mode, for the scratch home) in the scratch folder before the run, or the Claude Code copy fails silently with exit 0.
5. Use a scratch npm cache (`npm_config_cache` inside the scratch folder, +1.0 s per preview, cold download). A writable real cache lets the command write into the user's cache, which is outside the scratch folder and would be reused by the real run; a read-only cache does not work.
6. Allow list: `registry.npmjs.org` and `github.com`, plus the registry host of the user's npmrc. Add `api.github.com` only on evidence.
7. Decide on reads: by default everything readable is readable. Add `denyRead` for the credential folders (tested: the SSH folder gives `ENOENT`) or deny the whole home (tested: works with a scratch cache and a scratch folder under `/tmp`).
8. Pin `srt` to an exact version at least seven days old (0.0.81 qualifies) and decide how the app gets it (it is an npm package that itself needs the registry and has dependencies; the signature check of `app/src/verify.mjs` would apply the same way as for the skills CLI). The Dev Container image would need `bubblewrap`, `socat`, `ripgrep` for tests that run it.
9. Requirement "no shell" (`docs/security.md` line 41, "App to child processes: argv only, no shell"): the app still passes argv only, but srt runs a shell on a string it quotes itself (Linux, macOS). Either accept that as a stated exception (the 17-argument round trip above shows `quote()` is faithful) or do not claim "no shell" for the wrapped preview. Change line 41 accordingly.
10. The signature check (`c.verify`) and the app itself stay outside the sandbox; only `c.argv` is wrapped.
11. Update `docs/security.md` row "A command's own writes are not confined": absolute-path writes and network are stopped only where srt is available and the preview runs through it.

Not tested: macOS, Windows, a plain Linux host, other skill sources (non-GitHub), the `verify` step under srt, an srt version other than 0.0.81.

## For the owner: run it on a plain Linux host

Needs `bubblewrap`, `socat`, `ripgrep` from the distribution, Node 22 and npm. `suite.mjs` creates two throwaway fakes (a fake key file in the SSH folder and a fake readable file in the home folder, and the SSH folder if it is missing), refuses to run if either file already exists, and removes what it made when it ends. `extra.mjs` and `hosts.mjs` write nothing outside scratch folders.

```
mkdir -p /tmp/srt && cd /tmp/srt && npm init -y && npm i --save-exact @anthropic-ai/sandbox-runtime@0.0.81
cd <repo>/notes/srt-preview-prototype/srt-preview
node suite.mjs      # (a), (b), (c); add the word weak only if the bwrap proc error appears
node extra.mjs
node hosts.mjs
```

If `bwrap: Can't mount proc` appears on the host, record `bwrap --version`, `uname -r` and the distribution. macOS: the same scripts run with `SRT_BIN` pointing at the installed `srt`; `sandbox-exec` has no `.claude` cover (it uses glob denies), so check 4 may not apply there. Unverified.
