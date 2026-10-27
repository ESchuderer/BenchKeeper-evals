# Flutter and Dart in the analyzer sandbox

Research for the ticket [Flutter and Dart in the analyzer sandbox: tools, image, and how a built app can be exercised and seen](https://github.com/ESchuderer/BenchKeeper-research/issues/10), part of the map [Wayfinder map: benchmark research for BenchKeeper 7.0, MorphCook brief](https://github.com/ESchuderer/BenchKeeper-research/issues/8). It feeds [Analyzer for Dart: fixed analysis config, sandbox image, and what the reviewer and tester see](https://github.com/ESchuderer/BenchKeeper-research/issues/20), [Scoring a greenfield Flutter app: acceptance checks, static checks, process checks, review and human rating](https://github.com/ESchuderer/BenchKeeper-research/issues/19) and [Runner and record: where it lives, what it records and how raw data is kept](https://github.com/ESchuderer/BenchKeeper-research/issues/18). It states facts, options and costs. It makes no decision.

Date of the measurements: 2026-10-27. Flutter stable at that date was 3.47.8 with Dart 3.13.7 (released 2026-10-23, from the official releases file). Everything marked "measured" was run by the researcher in throwaway podman containers on one Linux host (16 CPUs, 31 GB RAM). Everything marked "unverified" was not run and has no official source read.

## Summary of the facts that matter most

- The pinned SDK is a 1.58 GB archive (2.5 GB unpacked) with a published sha256. Download, verify and unpack took 79 s here. The image layers measured 78 MB (Debian base), 100 MB (git, curl and the other prerequisites) and 2.74 GB (SDK, tool packages, web artifacts). The current Node image is 251 MB.
- The sandbox as written cannot run the `flutter` command. `sandbox.py` starts containers with `--read-only`, and the `flutter` wrapper script writes `bin/cache/engine.stamp` on every call (measured, exit 1, "Read-only file system"). The SDK's own `dart` binary called by its full path does run on a read-only root (measured). All Flutter measurements below ran without `--read-only` and with every other flag of `container_argv` kept.
- After the dependency step, analysis, format check, tests with coverage, `flutter build web` and a Linux desktop integration test all ran with `--network none` (measured). Only the dependency fetch needs the network.
- Flutter web gives the Playwright tester almost nothing by default: the accessibility tree is off, and the first snapshot holds one element, a button "Enable accessibility". Playwright cannot click it because it sits outside the viewport. Three ways to switch the tree on were measured to work (a `browser_evaluate` call, a Playwright init script, or `SemanticsBinding.instance.ensureSemantics()` in the app). With the tree on, text fields, checkboxes, buttons, tabs, dialogs, routes and lists appear with names and can be driven (measured on a small demo app).
- A default `flutter build web` loads CanvasKit from `www.gstatic.com`. With the tester limited to the app's origin (`review.py:261-265`) that request is blocked and the app does not render at all (measured). Building with `--no-web-resources-cdn` fixes this.
- `dart pub get` and `flutter pub get` did not run package code in the probe. `flutter test`, `flutter build web` and `dart run` ran a dependency's build hook (measured). `flutter config --no-enable-native-assets` stopped that for the first two and made `flutter test` exit 1 when a dependency has a hook (measured).
- Today's jscpd call with its current ignore list scanned 1383 files and 210,295 lines of a default Flutter app (one Dart source file plus the generated platform folders) because the pub cache and `.dart_tool` sit inside the project folder, and reported 11.08 percent duplication (measured).
- Lizard has no Dart reader. It still returned results for `.dart` files, with missed functions (measured). jscpd supports Dart.

## What the analyzer does today that touches Dart

Facts from the code in this repository, for reference when reading the sections below.

| Where | Fact |
|---|---|
| `analyzer/analyze.py:94-105` | `find_project` finds `pubspec.yaml` and exits with "Dart/Flutter runs are not supported yet". |
| `analyzer/analyze.py:41-43` | `SKIP_DIRS` has `build` and `coverage` but not `.dart_tool` or `.pub-cache`. `SOURCE_EXT` lists only JS and TS suffixes. |
| `analyzer/analyze.py:49-50` | The suppression patterns are all TS and ESLint or Biome markers plus `: any` and `as any`. |
| `analyzer/analyze.py:147-154` | The install step runs `npm ci --ignore-scripts` with `network="bridge"`. Network is open only there. |
| `analyzer/analyze.py:64-73`, `157-180`, `208-232` | Biome and jscpd run on the host through `host_run` (documented as "a trusted tool (one that only reads text)"), not in the container. Lizard runs in the analyzer's own Python process (`import lizard`). |
| `analyzer/analyze.py:226-227` | jscpd runs with `--min-lines 6` and ignores `**/node_modules/**,**/dist/**,**/build/**`. |
| `analyzer/analyze.py:242-246` | The test step defaults to `npm test --silent`; the caller can pass another argv. |
| `analyzer/sandbox.py:22-26`, `43-58` | The image is the first `FROM` line of `analyzer/sandbox/Dockerfile` (digest pinned). Flags: `--cap-drop ALL`, `no-new-privileges`, 2 GB memory, 2 CPUs, 512 PIDs, `--read-only`, `--tmpfs /tmp:rw,size=512m`, the run copy bind-mounted at `/work`, `HOME=/tmp`, user mapped to the host user. |
| `analyzer/review.py:88-127` | Blinding copies the project found by `find_project` and rewrites only the `name` and `description` of `package.json`. A Dart package name sits in `pubspec.yaml` and in every `package:<name>/` import; no code handles it. |
| `analyzer/review.py:214-258` | `start_command` and `start_app` read npm scripts (`preview`, `start`, `dev`, `build`). There is a `--start-cmd` override. |
| `analyzer/review.py:261-265` | The Playwright MCP server is started with `--headless --isolated --block-service-workers --viewport-size 390x844 --allowed-origins http://127.0.0.1:<port> --output-dir <dir>`. No `--browser`, `--caps` or `--init-script`. |
| `analyzer/review.py:282-292`, `150` | The tester prompt asks for a screenshot per bug "and name its file", and allows all tools of the `playwright` server (`--allowedTools mcp__playwright`). |

## 1. Lint, format check, analysis, tests and coverage

Measured with Flutter 3.47.8 in the container described in section 2, on the default `flutter create` app plus small files with deliberate problems. "Offline" means the command ran with `--network none` after `pub get` had filled the cache.

| Purpose | Command | Exit codes (measured unless noted) | Machine-readable output | Offline |
|---|---|---|---|---|
| Dependency fetch | `flutter pub get` or `dart pub get` | 0 ok; 69 when pub.dev is unreachable (measured, after 26 s of retries) | none | No. Works offline only with `--offline` and a filled cache (measured, with `--enforce-lockfile`) |
| Static analysis and lints | `dart analyze --format=json` | 0 clean; 1 infos (only with `--fatal-infos`); 2 warnings; 3 errors; 4 crash. Codes from the [SDK source](https://github.com/dart-lang/sdk/blob/main/pkg/dartdev/lib/src/commands/analyze.dart); warnings gave 2 in the probe | JSON, or a pipe-delimited form with `--format=machine`. Both are hidden options: they show only in `dart analyze --help -v` and in the source | Yes |
| Static analysis, Flutter wrapper | `flutter analyze --no-pub` | 0 clean; 1 on 2 warnings (measured). `--fatal-infos` and `--fatal-warnings` default to on, so any issue fails | Text lines only (severity, message, `file:line:col`, rule name), plus `--write=<file>` for the same text | Yes with `--no-pub`. Without it the command runs `pub get` first (help text) |
| Format check | `dart format -o none --set-exit-if-changed .` | 0 unchanged; 1 changed ([docs](https://dart.dev/tools/dart-format)); measured 1, with a "Changed <file>" line per file | `-o json` prints each file's formatted source, not a change list | Yes |
| Tests | `flutter test --no-pub` | 0 pass; 1 fail (measured) | `-r json`, or `--file-reporter json:<path>` (measured; the format is described at the [test package JSON reporter page](https://dart.dev/go/test-docs/json_reporter.md), named in the help text, not fetched) | Yes |
| Coverage | `flutter test --no-pub --coverage` | as tests | `coverage/lcov.info`. Options in the help text: `--coverage-path`, `--coverage-package`, `--branch-coverage`, `--merge-coverage` | Yes |

Facts about these commands:

- The run's own `analysis_options.yaml` controls both analysis and the format check. The file can switch rules off, exclude paths, set `formatter: page_width` ([analysis docs](https://dart.dev/tools/analysis), [format docs](https://dart.dev/tools/dart-format)), and enable analyzer plugins that run Dart code when `dart analyze` or `flutter analyze` runs ([analyzer plugins](https://dart.dev/tools/analyzer-plugins); not run here). `dart analyze --help -v` lists no option for a different options file, only `--packages`, `--sdk-path` and `--cache`. A fixed config therefore means replacing the file inside the analyzed copy (not tested).
- `avoid_dynamic_calls` is not listed in the rule files of `lints` 6.1.0 and `flutter_lints` 6.0.0 that the default app pulled in (grep of the pub cache, measured). The rule exists ([rule page](https://dart.dev/tools/linter-rules/avoid_dynamic_calls)). The `strict-casts`, `strict-inference` and `strict-raw-types` language options default to false ([analysis docs](https://dart.dev/tools/analysis)).
- `flutter test --coverage` produced an `lcov.info` that listed only `lib/main.dart`; an extra file in `lib/` that no test imported was absent (measured). The official coverage page was not reachable (404), so this behavior has no documentation source here.
- `flutter test` runs `test/` only. Integration tests run with `flutter test integration_test -d <device>` ([docs](https://docs.flutter.dev/testing/integration-tests)).
- Timings in this setup (warm image, 2 CPUs): `flutter analyze` 4 s, `flutter test` 1 to 6 s, `flutter build web --release` 14 to 22 s, the same with `--wasm` 22 to 23 s, a Linux integration test including its build 9 s. A web release build of the default app is 40 MB.

## 2. A pinned Flutter SDK in a container

### Sources and licence

| Source | Pin | Facts |
|---|---|---|
| Release archive from Google storage | Version plus sha256 in the official [releases file](https://storage.googleapis.com/flutter_infra_release/releases/releases_linux.json). 3.47.8 stable: `stable/linux/flutter_linux_3.47.8-stable.tar.xz`, sha256 `baf7dcc5a3dbba60fe863bf493a6cf203195621f7786eaa5a1bba02cd0d87dd2` (verified in the build) | 1,581,444,364 bytes. Manual install steps: [docs.flutter.dev/install/manual](https://docs.flutter.dev/install/manual) (prerequisites `curl git unzip xz-utils zip libglu1-mesa`). The archive page lists all versions: [docs.flutter.dev/install/archive](https://docs.flutter.dev/install/archive) |
| Git checkout | A tag or commit of `https://github.com/flutter/flutter.git` | The archive page names `git clone -b main` for the main channel. Cloning a stable tag and the first-run artifact download were not run here (unverified) |
| Prebuilt community image | A registry digest | A third-party Flutter image repository exists ([cirruslabs/docker-images-flutter](https://github.com/cirruslabs/docker-images-flutter)). A search showed open issues there about removed images and "after the stoppage of support" (issue 429, as listed in search results; content not read). Status unverified. A search of the flutter/flutter issue tracker found no official Flutter image (absence unverified) |
| Official Dart image | Digest of `dart:3.13.7-sdk` | [Docker Official Image](https://hub.docker.com/_/dart) maintained by the Dart Docker Team. It holds the Dart SDK. The page does not mention Flutter, so it cannot run `flutter_test` projects (inference from the SDK split, not measured) |

Licences: the Flutter repository is BSD 3-Clause, "Copyright 2014 The Flutter Authors" ([LICENSE](https://raw.githubusercontent.com/flutter/flutter/main/LICENSE)). The Dart SDK repository is BSD 3-Clause, "the Dart project authors" ([LICENSE](https://raw.githubusercontent.com/dart-lang/sdk/main/LICENSE)). The Flutter archive also carries engine artifacts; their licences were not reviewed. The Android SDK has its own licence acceptance step (`flutter doctor --android-licenses`, [Android setup](https://docs.flutter.dev/platform-integration/android/setup)).

### Measured image build

Base `debian:bookworm-slim`, one `RUN` that downloads, verifies and unpacks the archive, then `flutter --version`, `flutter precache --web`, and `chmod -R a+rwX` on the SDK and on a tool pub cache.

| Step | Result |
|---|---|
| apt install of curl, git, unzip, xz-utils, zip, libglu1-mesa and their dependencies | 4 s, 24 MB download, 117 MB installed |
| Download of the archive | 44 s (about 36 MB/s) |
| Download, sha256 check and unpack | 79 s together |
| `flutter --version` on first run | 0 s by the build timer. File owners and dates show that the Dart SDK, the web SDK and the tool snapshot come from the archive |
| `flutter precache --web` | 3 to 6 s |
| Whole `podman build` of the second variant (apt, SDK, first run, precache web) | 113 s |
| Unpacked SDK | 2.5 GB, of which `bin/cache` 1.8 GB |
| Image layers (from `podman history`) | 78 MB base, 100 MB prerequisites, 2.74 GB SDK layer, so 2.92 GB. `podman images` showed 2.92 GB right after the build and 5.66 GB later for the same layers; the cause was not found, so layer sizes are the figure to use |
| Extra layer for Linux desktop builds and a virtual display (clang, cmake, ninja-build, pkg-config, libgtk-3-dev, libstdc++-12-dev, xvfb, xauth, x11-apps, imagemagick, Mesa DRI, libegl1) | 23 s, 875 MB |

A first image, in which the archive was downloaded in one layer and deleted in a later one, was 4.37 GB; a layer cannot shrink an earlier layer.

The packages named in the Linux desktop requirements are `clang cmake ninja-build pkg-config libgtk-3-dev libstdc++-12-dev` ([Linux setup](https://docs.flutter.dev/platform-integration/linux/install-linux/install-linux-from-web)).

### What the container needs that the Node sandbox does not (all measured)

- Writable SDK directory. The engine-version step of the `flutter` wrapper script (under `bin/internal`) writes `bin/cache/engine.stamp.tmp.<pid>` and `engine.realm` on each `flutter` call and the script runs with `set -e`. Under `--read-only` the call exits 1. `/opt/sdk/flutter/bin/cache/dart-sdk/bin/dart --version` and `dart analyze` ran on a read-only root. Options: drop `--read-only` for this image (done in all runs here), or find another writable mount for `bin/cache` (not tried).
- The container user is the host user (`--userns=keep-id` on podman, `--user uid:gid` on docker). Files extracted by `tar` as root keep the archive owner (uid 1000 here). With the first image, a run as another owner failed in two ways: git reported "dubious ownership" for the SDK checkout, and the tool failed to update its packages ("Permission denied" on `packages/flutter_tools/.dart_tool`). The measured fix was `git config --system --add safe.directory '*'` and `chmod -R a+rwX` on the SDK, both inside the image. The chmod is done in the same `RUN` as the unpack so it adds no layer.
- First-run state belongs to the image. After the build steps `flutter --version` and `flutter precache --web`, `packages/flutter_tools/.dart_tool` and a 140 MB tool pub cache existed (the build ran as root with `FLUTTER_ALLOW_ROOT=1` and `PUB_CACHE=/opt/sdk-pub-cache`; which of the two steps created them was not separated). They are in the image before the sandbox starts.
- `PUB_CACHE` must point into `/work`. The sandbox sets `HOME=/tmp`, which is a 512 MB tmpfs that disappears with the container, and the install and analysis steps are separate containers. The cache path is written as an absolute `file:///work/.pub-cache/...` into `.dart_tool/package_config.json` (measured), so the cache has to exist at that same path in each later container. For the default app the cache was 19 MB for 25 packages.
- Telemetry. `--suppress-analytics` is a global flag of both tools (help output). Network was off in all later runs and no failure came from analytics.
- All commands in section 1 passed within `--memory 2g --cpus 2 --pids-limit 512`.

## 3. Exercising a built app without a person, and seeing it

### 3a. Flutter web in a browser with Playwright MCP

Setup of the probe: `@playwright/mcp` 0.0.83 (the version pinned in `analyzer/tools/package.json`), driven over stdio by a small client script; Chromium 155 from the Playwright cache; flags as in `review.py:261-265` plus `--browser chromium`. The built app was served by `python3 -m http.server` on the host, not in a sandbox container. Source for the tool list and options: the [Playwright MCP README](https://github.com/microsoft/playwright-mcp/blob/main/README.md), and `--help` of 0.0.83.

Build constraint first:

- A default `flutter build web` loads `canvaskit.js`, `canvaskit.wasm` and the Roboto font from `www.gstatic.com` and `fonts.gstatic.com`. With `--allowed-origins` limited to the app origin, Chromium blocked them (`ERR_BLOCKED_BY_CLIENT`), the console showed 6 errors, and the snapshot was empty (measured).
- `flutter build web --no-web-resources-cdn` (flag listed in `flutter build web --help`) bundles CanvasKit in the build. With it the app rendered with 0 console errors. The text `https://fonts.gstatic.com/s/` stays in `main.dart.js` as the base for fallback fonts. No request to it appeared for Latin text; text in other scripts was not tested (unverified).
- The `--wasm` build with the same flag gave the same tree and the same results. Skwasm printed a console warning that multi-threading needs the headers `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: require-corp`, and ran single-threaded.
- The default browser of `@playwright/mcp` 0.0.83 on this host was the `chrome` channel and it failed with "Chromium distribution 'chrome' is not found at /opt/google/chrome/chrome" until `--browser chromium` was passed. `review.py:261-265` passes no `--browser`, and `.github/workflows/code-quality.yml:146` installs only Chromium. Whether this fails in CI was not checked (unverified).

Is the semantics tree enough? The Flutter docs state ([web accessibility](https://docs.flutter.dev/ui/accessibility/web-accessibility)): "For performance reasons, Flutter's web accessibility is not on by default. To turn on accessibility, the user needs to press an invisible button with `aria-label="Enable accessibility"`." The engine source describes the placeholder on desktop as `position: absolute` at `-1px`, `1px` by `1px`, "just outside the viewport so only AT can reach it", and Tab alone must not enable semantics ([semantics_helper.dart](https://raw.githubusercontent.com/flutter/flutter/master/engine/src/flutter/lib/web_ui/lib/src/engine/semantics/semantics_helper.dart)). Measured on the demo app:

| Step | Result |
|---|---|
| First `browser_snapshot` | One element: `button "Enable accessibility"` |
| `browser_click` on that ref | Fails after 5 s: "element is outside of the viewport". Same with a 390x844 viewport and with `--device "iPhone 15"` |
| `locator.click({force: true})` through `browser_run_code_unsafe` | Fails with "Element is outside of the viewport" |
| `browser_press_key` Tab then Enter | Tree stayed off (one attempt) |
| `browser_evaluate` with `() => document.querySelector('flt-semantics-placeholder').click()` | Tree on. `browser_evaluate` and `browser_run_code_unsafe` are in the default tool list of 0.0.83, and `--allowedTools mcp__playwright` in `review.py:150` allows every tool of the server |
| `--init-script` file that polls for `flt-semantics-placeholder` and calls `.click()` | Tree on at the first snapshot after load, and again after `browser_navigate` to the same URL (reload) |
| `SemanticsBinding.instance.ensureSemantics()` called in the app's `main` | Tree on with no init script and again after reload. The [docs](https://docs.flutter.dev/ui/accessibility/web-accessibility) give this snippet; it needs a change in the app's source |

With the tree on, the demo app (Material widgets) showed:

| Widget | Snapshot node |
|---|---|
| AppBar title | `heading "Recipes" [level=2]` |
| TextField with label | `textbox "Search recipes"`; after `browser_type` the value `pasta` shows in the node and a bound `Text` updated to "query: pasta" |
| CheckboxListTile | `checkbox "Vegan"` |
| ElevatedButton | `button "Open dialog"` |
| ListTile with subtitle | one `button "Recipe 0 20 min"` (title and subtitle merged) |
| NavigationBar | `tablist` with `tab "Home" [selected]` and `tab "Saved"` |
| AlertDialog | `alertdialog` with `button "Close"` (only the dialog is in the tree while it is open) |
| Pushed route | Old page gone from the tree; new page has `button "Back"`, `heading "Details"` and its text |
| `GestureDetector` over `CustomPaint`, no `Semantics` | `button` with no name |
| `Image` (a failing network image) | absent |
| Static `Text` | `generic` node with the text |
| `ListView.builder` with 80 items | 17 `Item` nodes at first (0 to 16). After 12 mouse-wheel steps of 1500 px through `browser_run_code_unsafe`, items 63 to 79 were in the tree and items 0 to 16 were gone. `browser_mouse_wheel` needs `--caps vision`; `browser_press_key` with PageDown or End was not tried (unverified) |
| Wrapping | Every page sits under about six nested unnamed `generic` nodes |

Other measured facts:

- `browser_take_screenshot` with a file name saved a PNG and returned no image in the tool response (0 images). Without a file name the response held 1 image. In the probe the named file landed in the client's working directory, not in `--output-dir`; the README says files with an explicit name resolve against the workspace root and files without one go to `--output-dir`. The tester prompt asks for named files (`review.py:282-292`) and the tester runs with `cwd=tester`, a temporary directory removed at the end (`review.py:330-337`). Whether named screenshots reach the artifacts folder with Claude Code as the client was not checked (unverified).
- The default tool list of 0.0.83 has no coordinate tools: they are behind `--caps vision` (README). With `--caps vision`, `browser_mouse_click_xy` clicked the floating action button at (345, 800) with the semantics tree off, and the counter went from 0 to 1 (confirmed on a screenshot). The screenshot returned showed the rendered counter page.
- Software WebGL in headless Chromium rendered the app; the console only showed "GPU stall due to ReadPixels" warnings.
- The static file server is a gap. The Flutter image is Debian with no Python or Node, and `start_command` is npm-only (`review.py:214-224`). Options not run: add a static server to the image; use `flutter run -d web-server` (a development compile, not tried); serve `build/web` from the Node image (needs a server package, network at install).

### 3b. `integration_test` on Linux desktop under a virtual display

Measured in the extended image (sandbox flags without `--read-only`, `--network none`): `xvfb-run -a -s "-screen 0 1280x800x24" flutter test integration_test -d linux --no-pub` built the Linux app and passed a tap-and-check test in 9 s. This follows the [integration test docs](https://docs.flutter.dev/testing/integration-tests), which say a Linux CI "must invoke an X server first" and show `xvfb-run`. The test is code in the run (or code that the benchmark runner adds); it does not give a model free interaction.

Screenshots:

- `IntegrationTestWidgetsFlutterBinding.takeScreenshot` threw `MissingPluginException(No implementation found for method captureScreenshot ...)` on Linux (measured).
- Running the built binary under Xvfb and capturing with ImageMagick `import -window root` gave an all-black 800x600 PNG on two attempts (once with `LIBGL_ALWAYS_SOFTWARE=1`). The app was running (Impeller GL, VM service started). Cause not found; a window manager or a different capture method may help (unverified).
- `matchesGoldenFile` in a widget test wrote a PNG without any display or browser (measured, 8.9 KB). Text was drawn as solid blocks, the default test font, so a reviewer cannot read it. Loading real fonts into the test was not tried (unverified).

Web equivalent: `flutter drive --driver=test_driver/integration_test.dart --target=integration_test/app_test.dart -d web-server` runs headless and needs ChromeDriver installed with `npx @puppeteer/browsers install chromedriver@stable` (docs, same page). Not run.

### 3c. Android emulator in a container

Not run: it needs the Android SDK, a system image and KVM, which means large downloads and a device passed into the container. Sources disagree on feasibility:

- The Android docs say: "You can't run a VM-accelerated emulator inside another VM, such as a VM hosted by VirtualBox, VMWare, or Docker. You must run a VM-accelerated emulator directly on your host computer." ([emulator acceleration](https://developer.android.com/studio/run/emulator-acceleration)). On Linux the emulator "relies on KVM"; without acceleration it "is not supported and is very slow" and needs `ANDROID_I_WANT_MY_TCG=yes` ([emulator command line](https://developer.android.com/studio/run/emulator-commandline)). `-no-window` exists for servers without a display (same page).
- Google's [android-emulator-container-scripts](https://github.com/google/android-emulator-container-scripts) (Apache-2.0) build emulator images and run them with `--device /dev/kvm`. The README says KVM must be enabled on the host, nested virtualization is slow, and the tooling is "still an experimental feature".
- `analyzer/sandbox.py:49-53` drops all capabilities and passes no devices. A KVM device would be a change to the container flags.
- Flutter needs Android Studio or the command-line SDK tools, 36 as the listed API level, and accepted licences ([Android setup](https://docs.flutter.dev/platform-integration/android/setup)). Whether `flutter build apk` can run with the network off after a first fetch (Gradle and Maven downloads) was not checked (unverified).

### Which routes can give screenshots to the reviewer

| Route | Screenshot to the reviewer | Free exploration by the model |
|---|---|---|
| Flutter web with Playwright MCP | Yes, measured (inline image without a file name) | Yes once the semantics tree is on, or by coordinates with `--caps vision` |
| Linux `integration_test` under Xvfb | Not obtained (`takeScreenshot` unsupported, root capture black) | No, scripted test code only |
| Widget-test golden | PNG, but text is blocks | No |
| Android emulator | Unverified (adb screencap is the usual route, not read) | Unverified |

## 4. Equivalents of today's checks

| Today (JS and TS) | Dart or Flutter equivalent | Dart support, as measured or documented |
|---|---|---|
| Biome lint and format | `dart analyze` plus `dart format -o none --set-exit-if-changed` | Both ship in the SDK. See section 1 for exit codes and output |
| `tsc` type errors | Errors from `dart analyze` (severity ERROR, exit 3) | Part of the same command |
| ESLint | Lint rules in `analysis_options.yaml` (`package:flutter_lints` in the default app) | The run's own file decides the rules. See section 1 |
| lizard cyclomatic complexity | lizard 1.24.1 on `.dart` files | The [README language list](https://github.com/terryyin/lizard/blob/master/README.rst) has no Dart, and `get_reader_for('a.dart')` returned `None`. It still produced results. On a 40-line sample it reported `Calc::score` with CCN 12 (hand count 11, difference not investigated) but missed the arrow-bodied function, the getter and the static method, and listed `switch` as a function with CCN 1. A line `String describe(int n) => switch (n) {...}` was read as a function named `switch` |
| lizard alternative | `dart_code_linter` 4.4.3 (published 2026-10-26, [repository](https://github.com/bancolombia/dart-code-linter), MIT licence file in the package, "based on a fork of Dart Code Metrics") | `dart run dart_code_linter:metrics analyze lib --reporter=json` worked on the sample. It found all 10 functions including the getter, arrow functions and constructor; `Calc.score` CCN 10, `describe` CCN 1 (switch arms not counted). It needs `dart pub get` to fetch it as a dev dependency, then runs as Dart code. The JSON comes after progress text on stdout and has to be cut out |
| Commercial alternative | DCM (dcm.dev). Free plan: 1 seat, up to 50k analysed lines, 100 lint rules, 22 metrics ([pricing](https://dcm.dev/pricing)). Subscriptions for more. The page does not say whether it is open source and does not mention a JSON reporter | Not run |
| Discontinued package | `dart_code_metrics` 5.7.6, last published 2023-07-16, `isDiscontinued: true` ([pub.dev API](https://pub.dev/api/packages/dart_code_metrics)) | Not run |
| jscpd duplication | jscpd 5.4.1 | Dart is a built-in format (`dart`, `.dart`, [FORMATS.md](https://github.com/kucherenko/jscpd/blob/master/FORMATS.md)). On two near-identical Dart files it found 1 clone, 27 duplicated lines, 36.99 percent (measured). Run with the current ignore list on the default Flutter app (two Dart files, plus the generated platform folders, `coverage/`, a test report and the pub cache) it scanned 1383 files and 210,295 lines in 12 formats because `.pub-cache` was inside the folder, and reported 11.08 percent and 1072 clones (measured) |
| Suppression count | A new pattern list is needed | Documented markers ([analysis docs](https://dart.dev/tools/analysis)): `// ignore: <rule>`, `// ignore_for_file: <rule>` (also `// ignore_for_file: type=lint`), and in `analysis_options.yaml`: `analyzer: exclude:`, `analyzer: errors: <rule>: ignore`. The `dynamic` type: a token match on `dynamic` and `as dynamic`; the lint `avoid_dynamic_calls` allows `as dynamic` ([rule page](https://dart.dev/tools/linter-rules/avoid_dynamic_calls)). A `// dart format off` marker is not in the format docs page (unverified); `// dart format width=<n>` is. In the probe an `// ignore: unused_import` comment removed that warning from `dart analyze` output |
| Tests | `flutter test` (section 1) | Exit code and JSON reporter |
| Coverage | `flutter test --coverage` | lcov file |

Things in `analyzer/analyze.py` and `review.py` that a Dart run would touch, as facts: `SKIP_DIRS` and the jscpd `--ignore` list lack `.dart_tool`, `.pub-cache` and generated `*.g.dart` files; `safe_copy` (`analyze.py:81-91`) filters by `SKIP_DIRS`, so a run's own `.dart_tool` (absolute `package_config.json` paths, build-hook cache) would be copied; `flutter create` generates platform folders (`web/`, `linux/` and others for the platforms chosen) with C, C++ and JavaScript files that jscpd would scan; and `blind()` has no handling of the `pubspec.yaml` name.

## 5. What the dependency step can run, and installing without running code

Measured with a local probe: a path dependency `evil_pkg` with a `hook/build.dart` (writes a marker file and its environment keys), a `bin/` executable listed under `executables`, and a library with a top-level initializer that writes a marker. Hooks are described in the [Dart hooks docs](https://dart.dev/tools/hooks): "The hooks are run automatically when invoking the `run`, `build`, or `test` commands." The docs describe hooks as running in a "semi-hermetic environment" with most environment variables stripped, framed as reproducibility, and give no sandbox or disable switch.

| Command | Package code ran? |
|---|---|
| `dart pub get`, `flutter pub get` | No marker. The probe used a path dependency, so the `--precompile` step for hosted packages is not covered; the help text says it builds executables of immediate dependencies (compile only, not shown to run anything) |
| `flutter analyze`, `dart analyze`, `dart format` | No marker (with the default app's options file; analyzer plugins named in `analysis_options.yaml` would run Dart code per the docs, not tested) |
| `flutter test` | Hook ran. Environment keys it saw: `HOME` and `PATH`. It wrote a file into `/work` |
| `flutter build web` | Hook ran, same keys |
| `dart run` | Hook ran |
| The test or app code itself | Runs as ordinary code in `flutter test` or `dart run`, as with `npm test` |

Hook results are cached in `.dart_tool/hooks_runner`; a second run with the cache present did not run the hook again. The tests above removed it between runs.

Switching hooks off, measured in the same container as the command (the setting lives in `HOME`, which is the tmpfs `/tmp` in the sandbox, so every container must set it):

| Setting | `flutter test` | `flutter build web` | `dart run` |
|---|---|---|---|
| `flutter config --no-enable-native-assets` | No hook. Exit 1 with "Package(s) evil_pkg require the dart assets feature to be enabled" | No hook, built, exit 0 | Hook still ran |
| env var `FLUTTER_ENABLE_NATIVE_ASSETS=false` (a guessed name) | Hook still ran | not tried | not tried |

So switching off hooks costs the test step for any package that has one. `flutter config` also has `--enable-dart-data-assets` (help text).

Install-time controls that exist in the tools (documented in [pub get](https://dart.dev/tools/pub/cmd/pub-get) and measured where noted):

- `--enforce-lockfile` fails when `pubspec.lock` does not exactly match, or when the content hash of a hosted package changed. It ran fine against a fresh copy with the lockfile (measured). The sample lockfile held a sha256 for 24 of its 27 entries (the rest are SDK or path packages).
- `--offline` uses only the local cache (measured offline with a filled cache).
- `--[no-]precompile` (help text).
- Advisories are shown during resolution, and `ignored_advisories` in the root `pubspec.yaml` silences them for the root package only ([security advisories](https://dart.dev/tools/pub/security-advisories)).
- The package cache location is the `PUB_CACHE` variable ([pub get](https://dart.dev/tools/pub/cmd/pub-get)).
- Dependencies from git or from a custom hosted URL were not tried (unverified).

## Options and costs, stated without a recommendation

SDK in the image:

| Option | Cost |
|---|---|
| Archive plus sha256 in a `RUN` step (this research) | The pin is in a `RUN` or `ARG` line, not in the `FROM` line that `sandbox.image()` reads and that the existing Dependabot setup bumps (the Dependabot behavior for non-`FROM` lines is not verified). 79 s and 1.58 GB download per rebuild; 2.92 GB image |
| Prebuilt third-party image pinned by digest | Pin sits in the `FROM` line. Maintenance status unverified; trust in a third party |
| Official Dart image for static checks only | Small change to the pin mechanism, but `flutter_test` projects cannot be analyzed or tested without the Flutter SDK packages |

Running the `flutter` command under `--read-only`: the wrapper fails. Choices measured or implied: drop `--read-only` for the Flutter image (all measurements here); call `dart` and the SDK's internal tools directly (partly shown); or a writable mount for `bin/cache` (not tried).

Exercising the app: tree switched on by the runner (init script or an evaluate call) with the app unchanged; tree switched on by the app (`ensureSemantics()` in the spec or a patch of the source, which changes the object under test); coordinate and screenshot only with `--caps vision`; test-code routes (`integration_test`, goldens) that give pass or fail but not free exploration.

## What I ran

All in podman 6.1.4 on the author's host, throwaway images and containers (removed at the end). Container flags copied from `analyzer/sandbox.py:43-58`: `--rm --init --userns=keep-id --cap-drop ALL --security-opt no-new-privileges --memory 2g --cpus 2 --pids-limit 512 --tmpfs /tmp:rw,size=512m`, a bind mount at `/work`, `HOME=/tmp`, `PUB_CACHE=/work/.pub-cache`, and `--network none` except for `pub get` and `flutter create` (bridge); `--read-only` left out for the reasons above.

- Images: `debian:bookworm-slim` plus the archive for Flutter 3.47.8 (three build variants, last one described above), plus the Linux desktop layer.
- Projects: default `flutter create` apps with small edits; a probe package with a hook, an executable and a library initializer; a two-file Dart sample for lizard, jscpd and `dart_code_linter`.
- Web: `flutter build web --release`, with and without `--no-web-resources-cdn`, and with `--wasm`; `@playwright/mcp` 0.0.83 over stdio against the built folder served by `python3 -m http.server` on the host, using Chromium 155. Where the code ran: inside podman containers, the Flutter SDK and every pub package (the default app's dependencies, `hooks` 2.2.0, `dart_code_linter` 4.4.3, the probe package). On the host, outside any container: `@playwright/mcp` 0.0.83 with Chromium 155, jscpd 5.4.1 (installed with npm install scripts off), lizard 1.24.1 (pip, in a virtual environment) and `python3 -m http.server` for the built web folders. The host-side tools ran only on sample files and on apps the researcher built from `flutter create` output; no downloaded repository was cloned or run.
- Tools: lizard 1.24.1 in a Python virtual environment; jscpd 5.4.1 from npm.

The final image definition (the last `RUN` is the desktop layer), and the init script used in the web probe:

```dockerfile
FROM docker.io/library/debian:bookworm-slim
RUN apt-get update -y -q && apt-get install -y -q --no-install-recommends curl ca-certificates git unzip xz-utils zip libglu1-mesa >/dev/null && rm -rf /var/lib/apt/lists/* && git config --system --add safe.directory '*'
ENV PATH=/opt/sdk/flutter/bin:$PATH FLUTTER_SUPPRESS_ANALYTICS=true CI=true
RUN set -e; \
    curl -sSfL -o /tmp/flutter.tar.xz https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_3.47.8-stable.tar.xz; \
    echo "baf7dcc5a3dbba60fe863bf493a6cf203195621f7786eaa5a1bba02cd0d87dd2  /tmp/flutter.tar.xz" | sha256sum -c -; \
    mkdir /opt/sdk && tar -xf /tmp/flutter.tar.xz -C /opt/sdk && rm /tmp/flutter.tar.xz; \
    export FLUTTER_ALLOW_ROOT=1 PUB_CACHE=/opt/sdk-pub-cache; \
    flutter --version; flutter precache --web; \
    chmod -R a+rwX /opt/sdk /opt/sdk-pub-cache
RUN apt-get update -y -q && apt-get install -y -q --no-install-recommends clang cmake ninja-build pkg-config libgtk-3-dev libstdc++-12-dev xvfb xauth x11-apps imagemagick libgl1-mesa-dri libegl1 >/dev/null && rm -rf /var/lib/apt/lists/*
```

```js
// --init-script: once Flutter's semantics placeholder exists, activate it.
(() => {
  const t = setInterval(() => {
    const el = document.querySelector('flt-semantics-placeholder');
    if (el) { el.click(); clearInterval(t); }
  }, 100);
})();
```

## What I could not verify

- The Android emulator in a container, and any Android build offline.
- A git-tag based SDK install and its first-run network needs.
- Whether the missing `--browser chromium` breaks the analyzer's CI.
- Non-Latin text on a no-CDN web build (fallback fonts).
- A Linux desktop screenshot of the running app (root capture was black), loaded fonts in golden tests.
- Hooks from hosted or git dependencies, and `--precompile` behavior; analyzer plugins; `ignored_advisories` effects.
- Dependabot behavior for non-`FROM` pins; the status of the third-party Flutter image; the absence of an official Flutter image.
- The official page for coverage (404) and the `// dart format off` marker.
- Whether a read-only root can work with a writable `bin/cache` mount.
- The cause of the `podman images` size change from 2.92 GB to 5.66 GB for unchanged layers.
