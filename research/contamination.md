# Contamination: how an agent could reach finished MorphCook implementations

Answers [Contamination: how an agent could reach finished MorphCook implementations, and what controls and detection exist](https://github.com/ESchuderer/BenchKeeper-research/issues/12), a child of the [Wayfinder map](https://github.com/ESchuderer/BenchKeeper-research/issues/8). Facts, options and validity effects only. No option is recommended; the owner decides in [MorphCook brief definition: prompt, scope, limits and any change to the spec](https://github.com/ESchuderer/BenchKeeper-research/issues/16) and [Runner and record: where it lives, what it records and how raw data is kept](https://github.com/ESchuderer/BenchKeeper-research/issues/18).

Date of research: 2026-10-27. Claude Code documentation was read as served on that date, so version-gated statements may differ in other versions. Every external claim carries a URL; anything I did not confirm is marked "unverified".

## Reference state of the two repositories

- [TheMorpheus407/morphcook](https://github.com/TheMorpheus407/morphcook): MIT, public, created 2026-06-10, 46 stars, 9 forks, 32 top-level folders (one per model run). `main` was at commit `d314a20dbcb5d0d96bbe7334967adc6b6ecc6813` (2026-10-15) when I measured. New folders keep arriving (2026-09-30, 2026-10-07, 2026-10-15), so any reference set must name a commit. Its README says the first commit that touches a folder is the model's one-shot output and every later commit is human-directed, so `main` shows more than the one-shot runs.
- [TheMorpheus407/morphcook-cli-benchmark](https://github.com/TheMorpheus407/morphcook-cli-benchmark): public, created 2026-09-01, 3 stars, 0 forks. Three folders (`implementations/antigravity-cli`, `claude-code`, `codex-cli`), plus `PROMPT.md` and `SPEC.md`. Its README says scores, transcripts and run tooling are not published.
- Its `PROMPT.md` (the "upstream prompt") says: "You may use the internet and install dependencies when useful." The two prompt files I read inside `morphcook` (`claude-opus-5/prompt.txt`, `claude-fable-5-1/prompt.txt`) are a different, shorter text and say nothing about the internet; I did not read the others.
- `SPEC.md` names the repository: "Repo name: `morphcook` (GitHub, private)" (line 466). The product name and the package name `morphcook` are therefore in every run by default. A search for the word `morphcook` in a transcript shows nothing about contamination; the owner name `TheMorpheus407`, repository URLs and the Android package id seen in the F-Droid listing below do.

## 1. Ways an agent can obtain the implementations

Controllability is stated for a Claude Code run inside a container. "Egress" means the container's outbound network.

| Path | Tool the agent would use | Host seen on the wire | Stopped by egress rule on hostnames? |
|---|---|---|---|
| `git clone`, `git fetch`, `gh repo clone`, `gh api`, `gh search code` | Bash | `github.com`, `api.github.com` | Only by blocking `github.com` entirely. A hostname rule cannot tell one GitHub repository from another. |
| Archive download, e.g. `github.com/<owner>/<repo>/archive/refs/heads/main.tar.gz` | Bash (`curl`, `wget`), WebFetch | `github.com` (the archive URL form is documented at [GitHub Docs](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives)); redirect target host unverified | Same as above. |
| Raw file | Bash, WebFetch | `raw.githubusercontent.com`. I confirmed on 2026-10-27 that the README of the repository answers 200 there. | Yes, if that host is blocked. |
| Public mirror of GitHub | Bash, WebFetch | `cdn.jsdelivr.net/gh/<owner>/<repo>@<ref>/<file>`. The [jsDelivr README](https://github.com/jsdelivr/jsdelivr) says it serves any GitHub repository and keeps a permanent copy "even if GitHub goes down or a repository ... is deleted". I confirmed a 200 for this repository on 2026-10-27. | Yes, only if blocked explicitly. Other mirrors and code-reading sites exist; unverified, I did not enumerate them. |
| Forks | Same as clone | `github.com` | The 9 forks hold copies independent of the upstream repository, so removing or hiding upstream would not remove them. |
| Web search | WebSearch | none from the container: the search runs on Anthropic's backend and returns titles and URLs ([tools reference, WebSearch](https://code.claude.com/docs/en/tools-reference#websearch-tool-behavior)) | No. Container egress cannot block it. Only the tool can be denied. |
| Page fetch | WebFetch | any host the agent names | WebFetch runs inside the Claude Code process, not in the Bash sandbox ([sandboxing](https://code.claude.com/docs/en/sandboxing)), so it is covered by a container-level egress rule or by permission rules, not by the sandbox allowlist. |
| claude.ai MCP connectors | MCP tools | `mcp-proxy.anthropic.com` | Connector traffic routes through this host and is "enabled by default for claude.ai-authenticated users" ([network config](https://code.claude.com/docs/en/network-config#network-access-requirements)). A host rule on this name blocks all connectors; off switches are `ENABLE_CLAUDEAI_MCP_SERVERS=false` or the `disableClaudeAiConnectors` setting. Whether any connector on the benchmark account can read GitHub is unverified. |
| Package registries | `flutter pub get`, `dart pub` | `pub.dev` | The repository is not on pub.dev: the package name `morphcook` returns 404 at `https://pub.dev/api/packages/morphcook` and a search for it returns no packages (checked 2026-10-27). A Flutter project may still declare git dependencies that point at GitHub (pub feature; I did not verify its documentation page), which brings back the GitHub path. |
| Credentials already in the container | `gh`, `git` | `github.com` | A logged-in `gh` or a token in the environment is an authenticated route to the same repository. The analyzer's sandbox passes no environment except what the caller gives ([analyzer/sandbox.py:3-4](../analyzer/sandbox.py)); no runner exists yet. |
| Training data | none | none | Not controllable. The repository was created 2026-06-10 and its folders appeared through 2026-10-15. Which model's training data contains it is unverified; I found no official statement. A fingerprint hit cannot tell a fetched copy from a memorized one (see section 4). |

Findability, one dated data point: a general WebSearch on 2026-10-27 ("morphcook flutter github recipe app") did not return the GitHub repository. It returned an F-Droid page for `de.themorpheus.morphcook` (https://f-droid.org/ar/packages/de.themorpheus.morphcook/) and generic Flutter recipe repositories. The F-Droid page names the developer and so is a lead to the source. One query is not a measure of how likely an agent is to find the repository.

## 2. What Claude Code documents for restricting network and fetch tools

| Control | What it does | Limit | Source |
|---|---|---|---|
| Sandbox (`sandbox.enabled`) | OS-level filesystem and network isolation for Bash, PowerShell and Monitor commands and their children. Network goes through a proxy that checks the host against `allowedDomains`, which start empty. Off by default. | Does not cover Read, Edit, Write, WebFetch, WebSearch, hooks, local MCP servers. "`allowedDomains` doesn't limit WebFetch." | [sandboxing](https://code.claude.com/docs/en/sandboxing) |
| `sandbox.network.allowedDomains`, `deniedDomains` | Hostname allow and deny lists with wildcards such as `*.npmjs.org`. A denied host is refused in every permission mode. An entry without a port allows every port. | The proxy decides from the client-supplied hostname and does not terminate TLS by default. Docs warn that allowing broad domains such as `github.com` can create paths for exfiltration, and that "domain fronting or similar techniques" can reach hosts outside the allowlist. A path-level rule (allow one repository, deny another) is not possible without TLS inspection. | [sandboxing, security limitations](https://code.claude.com/docs/en/sandboxing#security-limitations) |
| `sandbox.network.strictAllowlist` | Denies hosts outside the allowlist instead of prompting. | Applies to sandboxed commands. | [sandboxing](https://code.claude.com/docs/en/sandboxing), [settings reference](https://code.claude.com/docs/en/settings-reference) |
| `sandbox.network.allowManagedDomainsOnly` (managed settings) | Non-allowed domains are blocked automatically; only managed `allowedDomains` and `WebFetch(domain:...)` rules count. | Needs managed settings delivery. | [sandboxing](https://code.claude.com/docs/en/sandboxing) |
| `sandbox.allowUnsandboxedCommands: false`, `sandbox.failIfUnavailable: true` | Disable the `dangerouslyDisableSandbox` retry; refuse to start when the sandbox cannot run. | Without them, a blocked command can be retried unsandboxed, and approval depends on the permission mode. | [sandboxing](https://code.claude.com/docs/en/sandboxing) |
| Permission mode in headless runs | `claude -p` starts in Manual mode when nothing sets a mode (v2.1.302 and later); a call that needs approval is denied. `dontAsk` denies every call that would prompt. `bypassPermissions` lets a non-allowed host through without prompting. | A denial is returned to the agent, which may try another route. | [headless](https://code.claude.com/docs/en/headless), [sandboxing, new domain requests](https://code.claude.com/docs/en/sandboxing) |
| `WebFetch(domain:...)` rules, bare `WebFetch` deny | Allow or deny by hostname, wildcards supported (v2.1.172 and later for wildcard matching). A bare `WebFetch` deny removes the tool. `CLAUDE_CODE_DISABLE_WEB_FETCH=1` (v2.1.285 and later) turns it off. | WebFetch "alone doesn't prevent network access. If Bash is allowed, Claude can still use `curl`, `wget`, or other tools to reach any URL." | [permissions](https://code.claude.com/docs/en/permissions#webfetch), [tools reference](https://code.claude.com/docs/en/tools-reference#webfetch-tool-behavior) |
| `WebSearch` deny | A bare `WebSearch` entry in `allow` or `deny` is the only form; it takes no specifier. The model-side tool can set `allowed_domains` and `blocked_domains` per call, but that is the agent's own choice, not a policy. | No domain policy for WebSearch. The search backend is not configurable. | [tools reference](https://code.claude.com/docs/en/tools-reference#websearch-tool-behavior) |
| Bash deny rules for `curl`, `wget` | Block those programs by command text. | The docs call argument patterns "fragile" and list the bypasses: options before the URL, other protocols, redirects, variables. A deny rule "doesn't match the same program by path or inside `sh -c`". Pair with the sandbox allowlist. | [permissions, Bash](https://code.claude.com/docs/en/permissions) |
| Whole-process boundary | Sandbox runtime (`srt claude`), dev container with firewall script, custom container, VM. These cover file tools, MCP servers and hooks as well as Bash. | The reference `init-firewall.sh` resolves each listed domain to IPs once at start and adds the GitHub IP ranges from `api.github.com/meta` (script lines 43-63, 67-88), then sets default policy DROP. So the reference container allows the whole of GitHub. | [sandbox environments](https://code.claude.com/docs/en/sandbox-environments), [dev container](https://code.claude.com/docs/en/devcontainer), [script](https://github.com/anthropics/claude-code/blob/main/.devcontainer/init-firewall.sh) |
| Proxy variables | Claude Code honors `HTTPS_PROXY`, `HTTP_PROXY`, `NO_PROXY`; no SOCKS support. | A custom proxy that terminates TLS needs its CA inside the container (`NODE_EXTRA_CA_CERTS`). | [network config](https://code.claude.com/docs/en/network-config) |
| `--bare` | Skips hooks, skills, custom commands, subagents, plugins, MCP servers, auto memory and CLAUDE.md. | Needs `ANTHROPIC_API_KEY`; does not use the subscription login. | [headless](https://code.claude.com/docs/en/headless#start-faster-with-bare-mode) |

Claude Code's own network needs (what a container allowlist must keep for the model API), from [network config, network access requirements](https://code.claude.com/docs/en/network-config#network-access-requirements):

- `api.anthropic.com`: model requests; also the WebFetch domain safety check, which sends the hostname before each fetch ([data usage](https://code.claude.com/docs/en/data-usage#webfetch-domain-safety-check)). `skipWebFetchPreflight: true` disables the check.
- `claude.ai` and `platform.claude.com`: OAuth sign-in and token refresh. An API-key run can drop these two ([sandbox environments](https://code.claude.com/docs/en/sandbox-environments)). Subscription auth is the owner's stated plan on the map, so these two apply.
- Optional and disabled by `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`: the two Datadog intake hosts, surveys, feature flags.
- `downloads.claude.ai`, `registry.npmjs.org`, `github.com`, `raw.githubusercontent.com`: installer, updates, plugin installs and marketplace clones. These matter for arms that install plugins or skills from GitHub at run time. Installing at image build time instead removes the need; the cost is that the arm's install step then runs outside the recorded session.

## 3. What a container egress allowlist must still permit for a Flutter build

The brief asks for a Flutter app that "tests and static analysis pass" and that the agent "has run" (upstream `PROMPT.md`). What the container needs depends on which commands the agent runs.

| Need | Host | Evidence |
|---|---|---|
| Flutter SDK archive (if not baked into the image) | `storage.googleapis.com` (`/flutter_infra_release/releases/stable/linux/flutter_linux_<version>-stable.tar.xz`) | [Flutter docs, mirrors](https://docs.flutter.dev/community/china) |
| Dart SDK on first tool run | `${FLUTTER_STORAGE_BASE_URL:-https://storage.googleapis.com}/flutter_infra_release/flutter/<engine>/` | update_dart_sdk.sh in the `bin` directory of [flutter/flutter](https://github.com/flutter/flutter), lines 133-134 |
| Engine and other artifacts | Same base as above; the tool also lists `chrome-infra-packages.appspot.com` (CIPD) next to it in its list of hosts blocked in China | [cache.dart lines 253 and 536-552](https://github.com/flutter/flutter/blob/master/packages/flutter_tools/lib/src/cache.dart) |
| Packages (`flutter pub get`) | `pub.dev`. The package archive URL is returned by the API as `https://pub.dev/api/archives/<name>-<version>.tar.gz`; the pub repository spec allows the archive URL to redirect to other storage hosts, so the allowlist may need more than `pub.dev` (I observed none on 2026-10-27; treat as unverified for later dates). | [Dart pub environment variables](https://dart.dev/tools/pub/environment-variables), [repository spec v2](https://github.com/dart-lang/pub/blob/master/doc/repository-spec-v2.md) |
| Android build (`flutter build apk`) in addition | `services.gradle.org` (Gradle distribution), `dl.google.com` (`google()` Maven), `repo.maven.apache.org` (`mavenCentral()`), `storage.googleapis.com/download.flutter.io` (Flutter engine Maven repository). The Android SDK packages come from Google as well (host unverified). `plugins.gradle.org` is unverified. | [gradle-wrapper template](https://github.com/flutter/flutter/blob/master/packages/flutter_tools/templates/app/android.tmpl/gradle/wrapper/gradle-wrapper.properties.tmpl), [Gradle RepositoryHandler](https://docs.gradle.org/current/javadoc/org/gradle/api/artifacts/dsl/RepositoryHandler.html), [FlutterPlugin.kt lines 108-125](https://github.com/flutter/flutter/blob/master/packages/flutter_tools/gradle/src/main/kotlin/FlutterPlugin.kt) |
| Fonts named in the spec (Playfair Display, JetBrains Mono, Caveat) | Spec line 141: `google_fonts`, "Bundled, not fetched at runtime". The agent has to obtain the font files from somewhere; the `google_fonts` package can fetch at runtime and prefers matching asset files ([package page](https://pub.dev/packages/google_fonts)). The host a run would use (`fonts.googleapis.com`, `fonts.gstatic.com`, GitHub) is unverified. One finished run (`Grok-4.6`) ships the `.ttf` files in `app/assets/fonts/`. | [SPEC.md](https://github.com/TheMorpheus407/morphcook/blob/main/SPEC.md) |
| `flutter` version freshness check | `git fetch --tags` against the SDK checkout's remote (GitHub for a git checkout) on official channels. When the fetch fails the tool prints the error and the check is skipped; I did not verify whether the surrounding command still succeeds. An SDK unpacked from the archive has no checkout to fetch. `FLUTTER_GIT_URL` names the expected remote. | [version.dart lines 353-370, 444-456, 805-862](https://github.com/flutter/flutter/blob/master/packages/flutter_tools/lib/src/version.dart) |

Reading the table by command:

- `flutter test` and `flutter analyze` need no network once the SDK, its artifacts and the package cache are present. Without a warm cache they need the Dart SDK and engine hosts plus pub.
- `flutter build apk` adds the Gradle, Google Maven, Maven Central and Flutter Maven hosts and the Android SDK.
- `storage.googleapis.com` is a shared Google Cloud Storage host. Allowing it for the SDK allows any public bucket on it. Hostname rules cannot narrow that to the Flutter buckets without TLS inspection (see the sandbox warning in section 2).
- Allowing `pub.dev` lets the agent fetch any published package, which is a normal part of the task.

Ways to build the allowlist, none of which I tested:

1. Internal network plus a filtering proxy. Docker: `docker network create --internal` ("Containers on an internal network may communicate between each other, but not with any other network", [Docker docs](https://docs.docker.com/reference/cli/docker/network/create/)). Podman: `--internal` adds no default route and DNS only resolves container names ([Podman docs](https://docs.podman.io/en/latest/markdown/podman-network-create.1.html)). The proxy container is the only member with outbound access. The agent container sets `HTTPS_PROXY`; Claude Code honors it ([network config](https://code.claude.com/docs/en/network-config)) and pub honors lowercase `http_proxy` and `https_proxy` ([Dart troubleshooting](https://dart.dev/tools/pub/troubleshoot)). Whether Gradle and `git` use the same variables is unverified. This is the only pattern here that leaves a hostname log outside the agent's reach.
2. IP-level firewall inside the container, as in the Claude Code reference script. Needs `NET_ADMIN` and `NET_RAW` ([dev container](https://code.claude.com/docs/en/devcontainer#restrict-network-egress)); resolves names once at start, so CDN address changes during a long run are a risk; analyzer `container_argv` drops all capabilities today ([analyzer/sandbox.py:49](../analyzer/sandbox.py)) and would not carry this unchanged.
3. Local mirrors through documented variables: `PUB_HOSTED_URL` for pub and `FLUTTER_STORAGE_BASE_URL` for Flutter artifacts ([Flutter docs](https://docs.flutter.dev/community/china), [Dart docs](https://dart.dev/tools/pub/environment-variables)). With both pointed at mirrors run by the benchmark runner, the container needs no public hosts besides the model API. The Gradle and Maven hosts are not covered by these two variables (unverified for Gradle mirrors).

Existing code: `sandbox.run` and `container_argv` take a `network` string that defaults to `"none"` ([analyzer/sandbox.py:43, 61](../analyzer/sandbox.py)); that code runs analysis of finished runs. No runner exists (map, "Today's product"), so there is no place yet where the agent's own network is set.

## 4. After-the-fact detection

### 4.1 Transcript signals

What is documented: `claude -p --output-format stream-json` emits `tool_use` and `tool_result` blocks and, with `--permission-prompts none`, `permission_denied` system messages and a `permission_denials` list in the result ([headless](https://code.claude.com/docs/en/headless)). On-disk transcripts are JSONL under `projects/<project>/<session-id>.jsonl` in the Claude configuration directory (`.claude` by default), but "the entry format is internal to Claude Code and changes between versions" ([sessions](https://code.claude.com/docs/en/sessions#where-transcripts-are-stored)). Retention is 30 days by default (`cleanupPeriodDays`, [data usage](https://code.claude.com/docs/en/data-usage)), so a run record must copy the transcript at the end of the run.

Calls that show access (match on the `input` of the call and on URLs in the `tool_result`):

| Tool | Field | Patterns |
|---|---|---|
| Bash | `command` | `git clone`, `git fetch`, `git ls-remote`, `gh repo clone`, `gh api`, `gh search`, `curl`, `wget`, `npx degit`, one-line scripts in `python -c` or `node -e` that open URLs; hosts `github.com`, `api.github.com`, `raw.githubusercontent.com`, `codeload.github.com`, `cdn.jsdelivr.net/gh`; strings `TheMorpheus407`, `morphcook-cli-benchmark`, the owner names of the 9 forks, `de.themorpheus.morphcook`, `f-droid.org` |
| WebFetch | `url` | same hosts and strings |
| WebSearch | `query`; URLs in `tool_result` | the same strings; result URLs that name the repository or a fork |
| Write, Edit | file content | a script that fetches (the URL then sits in a file, not in the Bash command) |
| Read, Grep, Glob | `file_path`, `path` | paths outside the project folder that hold a clone |
| any | `tool_result` content | lines that match the known-implementation fingerprints (see 4.2) |

Limits of text matching: the permissions page lists the same evasions for any command-text rule (variables, redirects, option reordering) ([permissions](https://code.claude.com/docs/en/permissions)). A URL built from variables, a downloaded script that then clones, base64 text or a shortener hides the host from the `command` field. The record from a filtering proxy (option 1 in section 3) is independent of the agent's own text: it logs the host of every connection. Without TLS inspection it shows `github.com` but not which repository, so a proxy log proves "GitHub was contacted", not "this repository was read". Leftovers in the run folder also count: `.git/config` remotes, a nested clone directory, `git log` author trailers (the landing commit of `Grok-4.6` in the reference repository carries a `Co-Authored-By` trailer).

### 4.2 Similar-code detection with the analyzer's fingerprint

What exists, with file and line:

- `fingerprint` ([analyzer/analyze.py:285-293](../analyzer/analyze.py)) hashes each stripped source line longer than 40 characters, skipping lines that start with `import `, `//`, `*` or `export `, and keeps the first 10 hex characters of SHA-256 (40 bits).
- `copy_pairs` ([analyzer/analyze.py:296-306](../analyzer/analyze.py)) compares every pair of runs in one report and flags a pair when shared hashes reach `COPY_THRESHOLD = 0.25` ([line 46](../analyzer/analyze.py)) of the smaller set. The result is a warning line ([line 556](../analyzer/analyze.py)).
- `SOURCE_EXT` is `.ts .tsx .js .jsx .mjs .cjs` ([line 43](../analyzer/analyze.py)), so for a Dart project `files` is empty, `fingerprint` returns `[]`, and `copy_pairs` skips the pair (`if fa and fb`, [line 302](../analyzer/analyze.py)). Today the analyzer detects nothing for MorphCook, and it compares runs only with each other, not with the published implementations.

How it would work against the known implementations (method, not a decision):

1. Build a reference set once: fingerprints of each folder of `morphcook` and of `morphcook-cli-benchmark/implementations`, at a pinned commit. Store the hashes, not the code. Two references per folder are possible: `main` (what a fetching agent would see) and the folder's first commit (the one-shot output, per the README). I measured `main` only.
2. For each run, fingerprint its Dart files (and compare the same way) against each reference separately, plus the share of the run's hashes found in any reference.
3. Adapt for Dart: add `.dart` to the source set; skip `part `, `part of`, `///` and `/*` lines as well as `import` and `export`; skip generated files (`*.g.dart`, `*.freezed.dart`, `*.gr.dart`, `*.mocks.dart`) and `build/`, `.dart_tool/`; optionally run `dart format` first so layout differences do not change the hash.
4. Fingerprint assets as well. The recipe corpus is a large part of the brief (`assets/*.json` in the spec's list), and fonts are binary. Identical-file hashes (SHA-256 of whole files) are cheap and unambiguous for assets, fonts and scaffold files.
5. Treat lines that appear in many references as brief-forced (they come from the spec or from `flutter create`) and drop them before scoring, so an independent run does not look similar.

Measurement on the reference set (corpus commit `d314a20`, 32 folders, 31 with Dart files, `.dart` files only, rule adapted as in step 3 without `dart format`; my script, not repository code; I read the files as text and executed nothing):

| Quantity | Value |
|---|---|
| Fingerprints per folder (min / median / max) | 329 / 1641 / 7776 |
| Distinct fingerprints across all folders | 57,642 |
| Fingerprints present in 3 or more folders / 10 or more | 1,063 / 117 |
| Folder pairs compared | 465 |
| Pair share, median / 90th percentile / maximum | 0.038 / 0.064 / 0.485 |
| Pairs at or above 0.05 / 0.10 / 0.25 / 0.50 | 129 / 9 / 1 / 0 |
| After dropping fingerprints that occur in 3 or more folders: median / maximum | 0.001 / 0.407 |

Reading: independent runs of the same spec share a median of about 4 percent of distinctive lines, falling to about 0.1 percent when brief-forced lines are removed. The current threshold of 0.25 is far above that baseline; a partial copy (one file out of many) stays below 0.25 and sits in the range where only the common-line filter separates it from independent runs. The expected false-match rate from the 40-bit hash for a run of about 2,000 hashes against 58,000 reference hashes is about 1e-4 (2,000 x 58,000 / 2^40), computed, not measured.

One pair stands out inside the reference set. `Grok-4.6` and `claude-fable-5` share 0.485 of the smaller Dart fingerprint set (0.407 after dropping common lines). Of the 139 files in `Grok-4.6`, 69 are byte-identical to the file at the same path in `claude-fable-5`: 17 JSON asset files (the recipe corpus, ontology, ingredient dictionary and others), the font files, and the Android and iOS scaffold files; none of its 52 Dart files is byte-identical. The `Grok-4.6` landing commit message is "land benchmark variant" with a `Co-Authored-By: Claude Fable 5` trailer. The cause is not established by anything I read: the repository's data does not say whether the assets were supplied, copied by the run, or copied when the folder was landed. Consequences for a reference set: some folders in the public repository are not independent of each other, and an agent that fetched either folder would produce a similar result.

Limits of the fingerprint approach:

- It needs the same lines. Renaming identifiers, reformatting or restructuring lowers the share. A copy of one or a few files stays under a min-set share of 0.25 even when the files are identical.
- Fingerprints cannot tell fetching apart from memorized training data, or from independent convergence on boilerplate. They show similarity, not access. Access evidence comes from 4.1.
- The reference set is a moving target and includes human edits after the one-shot commit.
- I did not measure the three `morphcook-cli-benchmark` implementations, a run against a reference, or the effect of `dart format`.

## 5. Which controls change the agent's behaviour compared with how users run it

Users run Claude Code interactively or headless with its default tools: Bash, WebFetch and WebSearch available, normal network, plugins, skills, CLAUDE.md and subscription login. The upstream prompt also allows the internet. Each row below departs from that. Effects on scores are not measured; they are listed so the later tickets can weigh them.

| Option | Contamination effect | Validity cost (what changes for the agent) | Other cost |
|---|---|---|---|
| A. Detection only: full tool set, record transcript and proxy log, fingerprint afterward | Does not prevent access; flags it. A flagged run is excluded or reported separately. | None for behaviour. Runs that fetched a copy still cost tokens and a rerun. | Needs transcript capture, a proxy log, a reference set, Dart support in the analyzer ([Analyzer for Dart: fixed analysis config, sandbox image, and what the reviewer and tester see](https://github.com/ESchuderer/BenchKeeper-research/issues/20)). |
| B. Host denylist: block `github.com`, `api.github.com`, `raw.githubusercontent.com`, `codeload.github.com`, `cdn.jsdelivr.net` and similar; all else open | Closes the common routes. Leaves forks on other hosts, unknown mirrors, and WebSearch results. | Agent cannot clone or read any GitHub repository, including legitimate ones (examples, issues, package source). Some pub packages and docs live there. Arms that install from GitHub at run time need it. | A denylist is never complete. |
| C. Allowlist egress: model API, pub, Flutter and Gradle hosts only (section 3) | Closes all but allowed hosts. `storage.googleapis.com` stays open as a shared host. | Agent cannot read arbitrary documentation or search results it follows. WebFetch denied or limited to allowlisted hosts. Users normally can. Failed fetches become denials that cost turns ([headless](https://code.claude.com/docs/en/headless)). | Maintaining the host list per Flutter and Gradle version; Android needs more hosts than test and analyze. |
| D. Offline with local mirrors (`PUB_HOSTED_URL`, `FLUTTER_STORAGE_BASE_URL`, pre-installed SDK) | Closes everything except the model API. | Same as C, stronger: the agent also loses the live package index unless the mirror proxies it. | The runner operates and pins mirrors; Gradle and Maven coverage unverified. |
| E. Remove tools: deny `WebFetch` and `WebSearch` (permission rules or `CLAUDE_CODE_DISABLE_WEB_FETCH`) | Closes both tools. Bash network stays open unless combined with B, C or D. | Changes tool surface the user has; the agent cannot look up docs by search. | Alone does not stop `curl` ([permissions](https://code.claude.com/docs/en/permissions)). |
| F. Disable the web path of connectors: `ENABLE_CLAUDEAI_MCP_SERVERS=false` | Closes MCP connector routes on the account. | Removes any connectors a user might have. | Whether any relevant connector exists on the benchmark account is unverified. |
| G. `--bare` or a stripped configuration | Reduces what an agent can load. | Removes plugins, skills, subagents, MCP servers, CLAUDE.md. That removes the arms under test. It also needs an API key rather than the subscription login ([headless](https://code.claude.com/docs/en/headless#start-faster-with-bare-mode)). | Conflicts with the subscription plan on the map. |
| H. Change the prompt (for example forbid fetching the implementations) | Adds a rule the agent can follow or ignore; it is not a boundary (the docs say CLAUDE.md guidance "shapes what Claude tries but doesn't enforce a boundary", [permissions](https://code.claude.com/docs/en/permissions)). | A changed prompt is a change to the brief; the upstream prompt allows the internet. Any edit must be written down in [MorphCook brief definition: prompt, scope, limits and any change to the spec](https://github.com/ESchuderer/BenchKeeper-research/issues/16). | The same prompt wording for every arm keeps arms comparable. |
| I. Sandbox on top of C or D (`sandbox.enabled`, `strictAllowlist`, no unsandboxed retry) | Second layer for Bash inside the container. | Same as C; the sandbox does not cover WebFetch or WebSearch. | Needs `enableWeakerNestedSandbox` inside an unprivileged container ([sandbox environments](https://code.claude.com/docs/en/sandbox-environments)), which the docs say "considerably weakens security". |

Cross-cutting facts for the decision:

- Every control in B to F applies equally to every arm only if it is part of the shared run environment. A control that differs by arm (for example installing plugins at run time for one arm) is a confound.
- Any control makes the benchmark measure "the brief without outside access" rather than "the brief as users run it". Published results would need to say which. This feeds [Evidence bar: rounds, pairing, win rule and the wording a claim may use](https://github.com/ESchuderer/BenchKeeper-research/issues/15) and [Publication: where results appear, claim wording, reproducibility package and naming other projects](https://github.com/ESchuderer/BenchKeeper-research/issues/22).
- No control touches training data. If a model has seen the folders, only the similarity side (4.2) can show an effect, and not cause.
- The fingerprint reference set belongs to the record decided in [Runner and record: where it lives, what it records and how raw data is kept](https://github.com/ESchuderer/BenchKeeper-research/issues/18): the commit of the reference corpus, the hash of the hash list, and the transcript and proxy log of each run.

## What I could not verify

- Which models have the repositories in their training data.
- Whether Gradle, `git` and the Android SDK manager honor the same proxy variables as Claude Code and pub; whether `plugins.gradle.org` and the Android SDK host are needed; whether pub or Flutter redirect archives to other hosts on dates other than 2026-10-27.
- Whether a failed freshness check in the Flutter tool aborts the surrounding command.
- Whether any claude.ai connector on the benchmark account can read GitHub.
- Which host a run would use to obtain the three font families.
- Mirrors and code-reading sites for GitHub other than jsDelivr.
- The pub documentation for git dependencies (not read).
- Fingerprint behaviour for the three `morphcook-cli-benchmark` folders, for first-commit references, with `dart format`, and against a real run.
- The cause of the overlap between `Grok-4.6` and `claude-fable-5`.
- Effects of any control on scores; none were measured.
