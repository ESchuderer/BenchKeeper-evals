# Auto mode and an allow text for a requested merge

Research for issue #425. Sources are the official Claude Code docs (fetched 2026-10-28), the Anthropic engineering post on auto mode, the output of `claude auto-mode defaults` on Claude Code 2.1.308 (the docs name this command as the way to read the built-in rules), and this repository at commit 93102c3. Anything not stated by those is under "Not verified".

## 1. What `autoMode` is and how the classifier treats merges and infrastructure

- `autoMode` is a settings object with the prose-rule arrays `environment`, `allow`, `soft_deny` and `hard_deny`, plus the Boolean `classifyAllShell` (v2.1.193 or later). Its scope is "User or managed". Source: https://code.claude.com/docs/en/settings-reference.md (entries `autoMode` and `autoMode.classifyAllShell`).
- Entries are natural-language prose, not regex or tool patterns. Source: https://code.claude.com/docs/en/auto-mode-config.md ("Define trusted infrastructure", "Override the block and allow rules").
- Roles: `hard_deny` is an unconditional boundary. `soft_deny` is a destructive action that user intent can clear. `allow` is an exception to the soft block rules. Source: https://code.claude.com/docs/en/auto-mode-config.md ("Override the block and allow rules").
- Precedence inside the classifier, as documented: `hard_deny` blocks unconditionally; `soft_deny` blocks next and `allow` exceptions or user intent can override it; explicit user intent overrides the remaining soft blocks "if the user's message directly and specifically describes the exact action Claude is about to take". "General requests don't count as explicit intent." Source: same section.
- Setting `allow`, `soft_deny`, `hard_deny` or `environment` without the literal `"$defaults"` entry replaces that section's whole built-in list. With `"$defaults"` the built-ins are spliced in at that position. Source: same section, and the CAUTION box there.
- Merge by default: the docs list "Merging a pull request no human has approved, approving Claude's own pull request, or disabling CI checks" as blocked by default. Source: https://code.claude.com/docs/en/permission-modes.md ("What the classifier blocks by default").
- The built-in rule behind this, printed by `claude auto-mode defaults` (Claude Code 2.1.308), is the soft-deny rule "Merge Without Review [named+specifics: must name merging without review]": "Merging a PR before any human has approved it." Its `--admin`/`--force` arm (bypassing required review or checks) needs its own naming of the bypass. `gh pr merge --auto` on a repository with required-reviews branch protection is not this rule; `--auto` is blocked on an unprotected repository or on a PR the agent is not working on. The related soft-deny rules are "Self-Approval" (approving a PR the agent authored), "CI Bypass" (for example `gh workflow disable`, marking a required check not-required, editing branch protection) and "ChatOps Trigger Comments" (`/merge`, `/deploy`, `atlantis apply`).
- Squash merge: no rule keys on the merge method. A squash merge is `gh pr merge --squash`, so the same "Merge Without Review" rule applies. This is an inference from the rule text above, not a documented statement.
- Pushes are not the problem: pushing to any branch of the session's repository, including the default branch, and creating a PR "that matches your request" run without a prompt, except a branch whose name marks a deploy or publication target (`production`, `release`, `gh-pages`). Source: https://code.claude.com/docs/en/permission-modes.md ("Pull requests and pushes"), https://code.claude.com/docs/en/auto-mode-config.md ("Common boundaries").
- Infrastructure by default: "Production deploys and migrations" and "Applying infrastructure changes to a protected IaC scope, or draining and removing cluster nodes" are blocked. Source: https://code.claude.com/docs/en/permission-modes.md. The built-in rule "Protected-Scope IaC Apply" says plan and dry-run are fine and "apply/destroy requires the user to name the specific change". "Protected IaC scopes" and "Sensitive remote targets" default to broad heuristics until named in `environment`. Source: https://code.claude.com/docs/en/auto-mode-config.md ("Define trusted infrastructure"), and the defaults output.
- The engineering post states the same limit: the classifier "gets wrong is whether a real consent signal in the session actually covers this action", and auto mode "is not a drop-in replacement for careful human review on high-stakes infrastructure". It reports a 17% false-negative rate on real overeager actions. Source: https://www.anthropic.com/engineering/claude-code-auto-mode.

## 2. Does a denial repeat after the user approves in the conversation?

- It can, and the docs say when. A stated approval "can clear the block", but only if the message names the action and "the specific thing that makes it dangerous"; "Naming the verb alone clears nothing, so 'you can force-push' leaves the block in place." Source: https://code.claude.com/docs/en/permission-modes.md ("Approvals you state in conversation").
- An approval "covers the destructive action you named, so a later action is blocked again unless you granted the approval as standing". The docs point to `autoMode.allow` for a routine pattern. "Some blocks stay in place"; to run such a step, leave auto mode and answer the permission prompt. Source: same section.
- For a merge, the rule's own tag says the user must name "merging without review". A bare "merge it" or "go" therefore plausibly does not clear it (inference from the tag; this matches the issue's observation of a denial repeating after "go").
- Fallbacks: after 3 blocks in a row or 20 in total, auto mode pauses and Claude Code resumes prompting; approving the prompted action resumes auto mode. The thresholds are not configurable. A blocked action is listed in `/permissions` under "Recently denied", where `r` retries it with a manual approval. In a non-interactive `-p` run without `--permission-prompt-tool` the action does not run and Claude keeps working. Source: https://code.claude.com/docs/en/permission-modes.md ("When auto mode falls back").
- A boundary stated in conversation ("wait until I review") blocks matching actions until lifted, and can be lost to context compaction. Source: same page ("Boundaries you state in conversation").

## 3. Which scopes honour `autoMode`

- Read: user settings (`settings.json` in the Claude Code config folder), managed settings, and the `--settings` flag or Agent SDK inline JSON. Source: https://code.claude.com/docs/en/auto-mode-config.md ("Where the classifier reads configuration").
- Not read: `.claude/settings.json` and `.claude/settings.local.json`. Quote: "The classifier doesn't read `autoMode` from project settings in `.claude/settings.json` or `.claude/settings.local.json`. Both files live in the repo directory, so a checked-in repo or a build step could otherwise inject its own allow rules. Move any `autoMode` block in `.claude/settings.local.json` to `settings.json` in the Claude Code config folder." Source: same section.
- So project local settings do not honour `autoMode`; the answer to the issue's "global or project local" is global (user) only. The `/permissions` Auto mode tab and `/auto-mode-setup` also write only to `settings.json` in the Claude Code config folder. Source: https://code.claude.com/docs/en/auto-mode-config.md ("Edit rules from /permissions", "Generate environment entries").
- Entries from several scopes are concatenated; a developer can add entries but cannot remove managed ones. Source: same page and https://code.claude.com/docs/en/settings-reference.md.
- Project-level alternatives that the docs do describe:
  - The classifier reads the same CLAUDE.md content Claude loads, so a project instruction steers it too. Source: https://code.claude.com/docs/en/auto-mode-config.md ("Where the classifier reads configuration"). The docs give "never force push" as the example; whether a CLAUDE.md line can clear a soft block is not stated.
  - `permissions.allow` rules are resolved before the classifier and narrow ones stay in effect in auto mode (only broad rules such as `Bash(*)` are dropped). Sources: https://code.claude.com/docs/en/permission-modes.md ("How the classifier evaluates actions"), https://code.claude.com/docs/en/auto-mode-config.md ("Route all shell commands through the classifier"). Project `permissions.allow` waits for workspace trust; the untracked local file does not. Source: https://code.claude.com/docs/en/settings.md ("Keep personal settings out of a repository"). This route does not look at who asked for the merge, so it widens more than an `autoMode.allow` text.

## 4. Allow text for "merge when the user asked for it"

The docs show allow entries as one sentence of the form "<Action> is allowed: <reason>" (https://code.claude.com/docs/en/auto-mode-config.md, example under "Override the block and allow rules"). They advise adding to `allow` "when the classifier repeatedly flags a routine pattern the default exceptions don't cover" and keeping `"$defaults"`. A fitting entry, to put in `settings.json` in the Claude Code config folder:

```json
{
  "autoMode": {
    "allow": [
      "$defaults",
      "Merging a pull request with `gh pr merge` in the session's own repository is allowed when the user's own message asks to merge that specific pull request: the user is the reviewer and the merge is the requested step. This does not cover `--admin` or `--force`, disabling or editing required checks or branch protection, merging a pull request the user did not ask to merge, or merging on the agent's own initiative."
    ]
  }
}
```

Why this does not widen anything else:

- `"$defaults"` keeps every other built-in rule, including Self-Approval, CI Bypass, ChatOps Trigger Comments and Protected-Scope IaC Apply. Without it the whole built-in `allow` list is replaced.
- The entry names one command and one trigger (the user's message names the pull request), and it lists the neighbouring actions it leaves blocked.
- It is an exception to "Merge Without Review" only; the docs say allow rules act as exceptions to matching soft-deny rules, so it clears nothing that is not matched by that rule's description.
- Run `claude auto-mode config` to confirm the entry is in the effective rules, and `claude auto-mode critique` to get feedback on ambiguity. Source: https://code.claude.com/docs/en/auto-mode-config.md ("Inspect the defaults and your effective config").

Limits that the entry cannot remove:

- It is user-global, so it applies in every repository, not one project. To scope it, name the repository or owner in the sentence (prose scoping; whether the classifier honours it reliably is not documented).
- It lets a merge pass the review rule in a repository with no required review. Server-side branch protection or rulesets are the real gate there.
- Infrastructure changes: no allow text is suggested. The docs keep apply and destroy under "name the specific change", and the safe wording is in the user's message ("apply the plan that adds X to Y"). For a recurring non-production target, the docs' own example pattern is an allow sentence naming a concrete isolated target, such as a staging namespace.

## 5. What BenchKeeper does today

- No `autoMode` is written or offered. `app/src/steps/global.mjs:63-65`: "BenchKeeper adds no permission rules: Claude Code's auto mode (its defaults) decides what needs a prompt", and `PERMISSION_ASK = []` at line 65. The same file, line 212, offers to remove existing `permissions.ask` rules.
- `app/src/allow.mjs:2` states BenchKeeper "follows the agents' own defaults (auto mode) and adds no ask rules". `app/src/allow.mjs:61` says `autoMode.allow` and `autoMode.environment` hold prose for the classifier, so they are not read by the allow-rule view.
- The settings catalog lists two keys, both with scope "User or managed": `autoMode` at `app/src/settings/claude-settings-keys.json:165` and `autoMode.classifyAllShell` at line 171. It also lists `disableAutoMode` (line 363) and `useAutoModeDuringPlan` (line 1389).
- The copy of the schema in the repository describes `autoMode` and its four arrays at `app/src/settings/claude-code-settings.schema.json:3728-3766` (`allow` 3733, `soft_deny` 3740, `environment` 3747, `hard_deny` 3754, `classifyAllShell` 3761).
- Nothing under `docs/`, `plugins/` or `app/test` mentions `autoMode`; `docs/security.md:260` describes auto mode in general terms.

## Not verified

- Whether the classifier honours the negative clauses ("does not cover `--admin`") inside an allow sentence as exclusions. The docs give no example of one.
- Whether editing a GitHub ruleset through `gh api` falls under the "CI Bypass" rule. The rule text names branch protection and required checks, not rulesets.
- Whether `gh pr merge --squash` or a repository without required reviews is judged differently from the default text; the rule text mentions only `--auto`, `--admin` and `--force`.
- Whether a CLAUDE.md sentence can clear a soft block. The docs say the classifier reads CLAUDE.md but give only a "never" example.
- The v2.1.207 date at which `.claude/settings.local.json` stopped being read for `autoMode`: a search summary mentioned it, the fetched doc page does not, so it is not relied on.
- Whether `Bash(gh pr merge *)` counts as a "narrow" rule that stays in effect in auto mode, and how its glob treats flags such as `--admin`.
- The built-in rule texts come from the installed binary (2.1.308) and may change between releases; the docs say `"$defaults"` follows those updates.
