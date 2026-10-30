# Codex accounts: usage source, login status, terms

Research for issue #373 (parent #372, feeds #300 and #385). All pages were read on 2026-10-27. Quotes were checked against the page text (Markdown versions of the docs, the Services Agreement PDF, the Codex source at commit `6fe77fc12346591b8037a8704640e40196b19044`, `main` on 2026-10-27). In quotes, the home-directory shorthand of the original path is written `$HOME`.

## Question

What do OpenAI's official documents say about Codex accounts: (1) a documented way to read the remaining usage of an account, (2) how `codex login status` behaves and what per-account configuration exists beyond `CODEX_HOME`, (3) what the terms say about several accounts of one person and about switching accounts at a limit.

## Short answer

1. Usage: three documented sources. `/status` inside a CLI session, the web dashboard at `https://chatgpt.com/codex/settings/usage`, and the app-server method `account/rateLimits/read` (fields `usedPercent`, `windowDurationMins`, `resetsAt`). Only the app-server method is programmatic. It needs the account's login, so run it with that account's `CODEX_HOME`.
2. Login status: `codex login status` prints to stderr and exits 0 when credentials are present, 1 when not. Exit 0 means credentials are stored, not that they still work. No per-account setting exists besides `CODEX_HOME`. Profiles (`--profile`) layer config files under the same `CODEX_HOME`. With `keyring` or `auto` storage the keyring entry is keyed by a hash of the `CODEX_HOME` path, so separate folders do not collide.
3. Terms: the consumer Terms of Use, the Usage Policies and the help-center account sharing policy could not be read (HTTP 403 from a bot challenge). Only the OpenAI Services Agreement (business and developer customers) was read verbatim. It forbids sharing credentials between users and circumventing rate limits or Usage Limits. No text read speaks to one person holding several accounts or switching at a limit. Treat the consumer position as unverified.

## 1. Remaining usage of a Codex account

### `/status` (interactive CLI only)

Source: https://learn.chatgpt.com/docs/pricing (read 2026-10-27; the old URL `developers.openai.com/codex/pricing` redirects here):

> If you want to see your remaining limits during an active Codex CLI session, you can use `/status`.

The CLI reference (https://learn.chatgpt.com/docs/developer-commands?surface=cli) describes `/status` as "Display session configuration and token usage." and lists "writable roots, and current token usage" as output. The sentence naming rate limits for `/status` appears in the VS Code command list on the same site, not in the CLI section I could confirm verbatim. There is no non-interactive flag documented for it.

### Usage dashboard (web)

Same pricing page:

> You can find your current limits in the usage dashboard (https://chatgpt.com/codex/settings/usage).

It needs a signed-in browser session. No API is described.

### App-server `account/rateLimits/read` (programmatic)

Source: https://learn.chatgpt.com/docs/app-server.md. The method list says:

> `account/rateLimits/read` - fetch ChatGPT rate limits.
> `account/rateLimits/updated` (notify) - emitted whenever a user's ChatGPT rate limits change.

The documented example response contains `rateLimits.primary` and `rateLimits.secondary` with `usedPercent`, `windowDurationMins` and `resetsAt` (Unix seconds), `rateLimitReachedType`, `rateLimitsByLimitId` (keyed by metered limit id such as `codex`), and `rateLimitResetCredits`. The page states: "`usedPercent` is current usage within the quota window." and "`resetsAt` is a Unix timestamp (seconds) for the next reset."

The type definitions in the Codex source (`codex-rs/app-server-protocol/schema/typescript/v2/GetAccountRateLimitsResponse.ts`, `RateLimitSnapshot.ts`, `RateLimitWindow.ts` at the commit above) add `ordinaryUsageAllowed: boolean | null`, `accountId`, `planType`, `credits` and `spendControlReached`. The source comment on `ordinaryUsageAllowed` says null means unavailable and "clients must not infer recovery from percentages or reset times."

How it is reached: `codex app-server` (stdio by default) with a mandatory `initialize` request first (app-server page: "Clients must send a single `initialize` request per transport connection before invoking any other method on that connection"). The account is the one in the `CODEX_HOME` the process runs with.

Also listed, but without a described response in what I read: `account/usage/read` ("fetch ChatGPT account token-activity summaries and daily buckets") and the CLI `/usage` command (token activity, "daily, weekly, or cumulative"). These report token activity, not remaining quota.

### Related limit facts

- Pricing page: "Local messages and cloud chats share your plan's usage allowance. Weekly limits may also apply." and "Pro plans currently have no five-hour limit."
- The Codex source marks the rate-limit data as backend-supplied, so which plans return both `primary` and `secondary` windows is unverified.

## 2. Login status and per-account configuration

### `codex login status`

Docs, https://learn.chatgpt.com/docs/auth.md: "Run `codex login status` to see the active authentication method."

CLI reference: "`codex login status` exits with `0` when credentials are present, which is helpful in automation scripts."

Source, `codex-rs/cli/src/login.rs` lines 488 to 554 (`run_login_status`), all output via `eprintln!` (stderr):

| State | stderr text | Exit |
|---|---|---|
| ChatGPT login (`Chatgpt`, `ChatgptAuthTokens`) | `Logged in using ChatGPT` | 0 |
| API key | `API key configured - <masked key>` plus a notice | 0 |
| Access token (`AgentIdentity`) | `Logged in using access token` | 0 |
| Personal access token | `Logged in using personal access token` | 0 |
| Workload identity | `Logged in using workload identity` | 0 |
| No stored auth | `Not logged in` | 1 |
| Load error | `Error checking login status: <err>` | 1 |

Consequences for a preflight:

- Parse nothing from stdout. Read the exit code, and stderr only for the mode.
- Exit 0 means stored credentials loaded. This function does no network call and no token refresh, so an expired or revoked login still returns 0 (read from the source; actual behavior with an expired refresh token was not run, unverified).
- The documented validity check is app-server `account/read` with `"params": { "refreshToken": ... }`: "fetch current account info; optionally refresh tokens." It reports account and plan details, so it can also tell which account a `CODEX_HOME` holds.
- The docs say tokens refresh automatically: "Codex refreshes tokens automatically during use before they expire, so active sessions usually continue without requiring another browser login."

### Per-account configuration

- `CODEX_HOME` (https://learn.chatgpt.com/docs/config-file/environment-variables.md): "Sets the root for Codex state, including config, auth, logs, sessions, skills, and standalone package metadata. If you set it, the directory must already exist." Default `$HOME/.codex`. This is the only account-level switch documented.
- `CODEX_SQLITE_HOME` (default `CODEX_HOME`) moves SQLite state; the `sqlite_home` option takes precedence.
- Credential store, `cli_auth_credentials_store` (auth page): "`file` stores credentials in `auth.json` under `CODEX_HOME` (defaults to `$HOME/.codex`)." `keyring` uses the OS store and fails if unavailable, `auto` prefers the OS store and falls back to `auth.json`, `ephemeral` is memory only.
- Keyring collision: the source (`codex-rs/login/src/auth/storage.rs`, `compute_store_key`, lines 258 to 269) builds the keyring key as `cli|` plus a truncated SHA-256 of the canonicalized `CODEX_HOME` path. Two different `CODEX_HOME` folders therefore use two keyring entries. The docs do not state this, so it is an implementation detail that may change.
- Profiles (https://learn.chatgpt.com/docs/config-file/config-advanced.md): "When you pass `--profile profile-name`, Codex loads `$HOME/.codex/config.toml`, then overlays `$HOME/.codex/profile-name.config.toml`." (the page wraps this line). A profile is a config layer under the same `CODEX_HOME`, so the docs describe no way for it to select an account. Whether a profile file could set `cli_auth_credentials_store` or other auth keys is not stated (unverified).
- Shared login: "The CLI and extension share the same cached login details." (auth page). The desktop app, CLI and extension therefore follow the same `CODEX_HOME`.
- Managed restrictions: `forced_login_method = "chatgpt" # or "api"` and `forced_chatgpt_workspace_id`; "If the active credentials don't match the configured restrictions, Codex logs the user out and exits."
- Headless: `codex login --device-auth` is preferred ("Enable device code login in your ChatGPT security settings (personal account) or ChatGPT workspace permissions (workspace admin)."). Copying `auth.json` is documented ("Treat `$HOME/.codex/auth.json` like a password"), as is `--with-access-token` from stdin.
- Codex access tokens (https://learn.chatgpt.com/docs/enterprise/access-tokens): "Codex access tokens are currently supported for ChatGPT Business and Enterprise workspaces." and "Each token belongs to its creator and that user's ChatGPT workspace."
- Not documented: a command or setting to hold several accounts in one `CODEX_HOME`, or to switch accounts. A developer forum post complains about de-authing and re-authing between accounts, which is not an official statement.

## 3. Terms on several accounts and switching at a limit

### What could be read

Source: OpenAI Services Agreement, `ONLINE v.010126`, https://cdn.openai.com/osa/openai-services-agreement.pdf (read 2026-10-27). Scope from the document: "Services" means "OpenAI's services for businesses, enterprises, or developers" and "Account" means "an administrative account provided to Customer by OpenAI for the purpose of administering the Services." It is a customer agreement for organizations, not the consumer terms for a personal ChatGPT plan. Whether it governs a Business or Enterprise Codex seat is likely, but I did not confirm it from an OpenAI page.

Section 3.1:

> Customer will not share Account access credentials or individual login credentials between multiple users. Customer may not resell or lease access to its Account or any End User Account.

Section 3.2:

> End User Accounts may only be provisioned to, registered for, and used by, a single End User.

Section 3.3 (h) and (i), Customer will not, and will not permit End Users to:

> (h) interfere with or disrupt the Services, including circumvent any rate limits or restrictions or bypass any protective measures or safety mitigations for the Services; (i) violate or circumvent Usage Limits or otherwise configure the Services to avoid Usage Limits.

Definition: "Usage Limits" means "End User, messaging, token, throughput rate, or other limits on Customer's use of the Services as described in the applicable Order Form or Documentation."

Reading: the agreement bars sharing one account between users and circumventing limits. It says nothing about one person holding several accounts, and nothing about switching at a limit. Rotating to another account to continue past a limit could be read under 3.3(h) and (i); this is an interpretation, not a statement in the text.

### What could not be read

These returned HTTP 403 (Cloudflare "Just a moment..." challenge, also in a real browser session) on 2026-10-27, so no verbatim text was obtained:

- https://openai.com/policies/terms-of-use/ and https://openai.com/policies/row-terms-of-use/ (consumer Terms of Use)
- https://openai.com/policies/eu-terms-of-use/
- https://openai.com/policies/usage-policies/
- https://help.openai.com/en/articles/10471989-openai-account-sharing-policy (account sharing policy)
- https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan

Search-engine summaries of these pages say the consumer terms bar sharing credentials and circumventing rate limits, and that the help-center policy says accounts are for one individual. These are summaries, not quotes, so they are unverified. No source I read mentions several accounts per person.

The Codex for Open Source terms page (https://learn.chatgpt.com/docs/codex-for-oss-terms) says its terms supplement the OpenAI Terms of Use and OpenAI policies, which confirms those documents govern Codex use but gives no text.

## Unverified

- Consumer Terms of Use, Usage Policies and the help-center account sharing policy: not readable (403). Wording on credential sharing, several accounts per person and switching at a limit is unverified. A person must read these pages in a browser before BenchKeeper ships account rotation.
- Whether the Services Agreement applies to a given Codex seat.
- `codex login status` behavior with an expired or revoked login (source suggests exit 0; not run).
- Which plans return which rate-limit windows from `account/rateLimits/read`, and whether the method works for API-key logins (the docs call it "ChatGPT rate limits").
- Keyring keying per `CODEX_HOME` is source behavior at one commit, not a documented guarantee.
- The sentence naming rate limits in the `/status` output is only confirmed for the VS Code command list and the pricing page, not the CLI reference section.
- No Codex event or hook for a limit being hit was looked for beyond `account/rateLimits/updated` and `rateLimitReachedType`; a Claude Code `StopFailure`-style hook equivalent was not searched.
