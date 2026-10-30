# Anthropic Code Review: what it offers and what BenchKeeper should do with it

Ticket: ESchuderer/BenchKeeper#378. Read on 2026-10-27. Claude Code is the main agent.

## Question

What does Anthropic's Code Review offer, and which improvements follow for BenchKeeper's review steps (the `workflow` skill's reviews, the pre-push review, `orchestrating-projects`) and for setup of repositories?

## Short answer

Code Review is a managed GitHub service for Team and Enterprise organizations. Several agents read each pull request, a verification step drops false positives, and the result is inline comments (Important, Nit, Pre-existing), a summary and a check run. It never approves or blocks, reads `CLAUDE.md` and `REVIEW.md` from the repository, and bills token usage as usage credits. Most of it needs a plan BenchKeeper's users may not have. What transfers is the method: fixed review depth per risk, severity rules, a round cap, and risk-scaled human approval. BenchKeeper's pre-push `/code-review` already matches Anthropic's local command. The ranked gaps are small edits to `software.md`, `orchestrating-projects` and the PR body, plus one setup question (a `REVIEW.md` skeleton and branch protection for repositories that use the service). Which of them go into 7.0 is the owner's decision in #398.

## Sources and how they compare

| Source | Role | Read as |
|---|---|---|
| [Code Review docs](https://code.claude.com/docs/en/code-review) and its sub-pages: [setup](https://code.claude.com/docs/en/code-review-setup.md), [customize](https://code.claude.com/docs/en/code-review-customize.md), [pull requests](https://code.claude.com/docs/en/code-review-pull-requests.md), [costs](https://code.claude.com/docs/en/code-review-costs.md), [troubleshooting](https://code.claude.com/docs/en/code-review-troubleshooting.md), [local `/code-review`](https://code.claude.com/docs/en/code-review-local), [ultrareview](https://code.claude.com/docs/en/ultrareview.md) | Reference. The authority for behavior, setup and limits. | Came back close to verbatim. |
| [GA announcement](https://claude.com/resources/articles/code-review-is-now-generally-available) (2026-10-15) | Product news: out of research preview, speed, review levels, credits. | Came back as a summary by the fetch tool. |
| [Preview announcement](https://claude.com/resources/articles/code-review) (2026-03-09) | Linked from the GA page. Source of the old price figure. | Summary by the fetch tool. |
| [Blog "How the Claude Code team does code review"](https://claude.dev/blog/solving-code-review-at-anthropic/) (2026-10-15) | How Anthropic's own team layers review. Not a product description. | Summary by the fetch tool. |

How they differ:

- The docs describe the product as it ships. The blog describes Anthropic's internal process around it. Where they disagree, the docs describe the product: the docs say a review never approves or blocks and the check run never concludes as a failure, while the blog says open bug or security findings block merge in Anthropic's repositories. That is a repository rule on resolved threads or an internal setup, not a product switch (inference, not stated by any page).
- The GA page gives speed (6 to 10 minutes, down from about 20 in the preview) and the Quick, Standard, Deep choice. The docs give no timing and no dollar figure. The only dollar figure is the preview page's "$15 to $25 on average". The GA and docs pages say cost scales with level, change size and code complexity, so the preview figure is dated and unverified for GA.
- The blog's adoption checklist names the product as one option next to the Claude Code GitHub Action, and the docs' comparison table lists five ways to get a review (below).

Host check for `claude.dev`: unverified as Anthropic's. For: its tagline reads "Sharing tips, tricks, and POVs from Anthropic's developers", its DOCS link goes to `code.claude.com/docs`, and the post links Anthropic pages. Against: the site has no legal or copyright footer, and neither the docs index (`https://code.claude.com/docs/llms.txt`), the GA article, the preview article nor the Anthropic engineering post `anthropic.com/engineering/redesigning-source-control` links to `claude.dev`. A web search found no Anthropic-hosted copy. Treat the blog's numbers as Anthropic-authored and unconfirmed by an Anthropic-hosted page. Nothing in the ranked list below depends on a blog number alone.

## What the product does

From the [docs](https://code.claude.com/docs/en/code-review):

- Four stages on Anthropic infrastructure: find (several agents read the diff and surrounding code in parallel), verify (candidate findings are checked against the code), rank (deduplicate, sort by severity), post.
- Output: inline comments, a summary in the review body, and a check run named "Claude Code Review". Severities: Important (fix before merge), Nit, Pre-existing ([pull request page](https://code.claude.com/docs/en/code-review-pull-requests.md#severity-levels)). The default focus is correctness, not formatting or missing tests.
- Read-only access to the repository. It does not build or run the code. It posts comments and the check run, resolves its own earlier threads when a push fixes them, and cannot push commits.
- Never approves and never blocks. The check run ends neutral or skipped, never failed, so a required check cannot gate on it. A script can read the severity counts from the last line of the check run's details (`bughunter-severity` JSON; the page gives the `gh api` commands) and gate on `normal` above zero.
- Trigger per repository: once after PR creation, after every push, or manual. Comment commands: `@claude review`, `@claude review always`, `once`, `stop`, `off`, `pause`. A commenter needs write access, bots do not start reviews, drafts and fork PRs are skipped by automatic runs. Later automatic reviews focus on what changed and post fewer nits and pre-existing findings.
- Replies to a finding do not dismiss it. Resolving the thread does. A fix push lets the next review resolve the thread.

Related ways to get a review, from the docs' [comparison table](https://code.claude.com/docs/en/code-review#compare-ways-to-get-a-review):

| Option | Starts | Runs | Needs |
|---|---|---|---|
| Code Review service | PR events or `@claude review` | Anthropic infrastructure | Team or Enterprise, GitHub, Owner setup |
| `/code-review` | You, on your branch | Your Claude Code session | Any plan |
| Ultrareview (`/code-review ultra`) | You | Cloud sandbox | claude.ai sign-in |
| `claude-code-action` in your CI | Your pipeline | Your runners | API key or subscription token |
| Own reviewer (subagent or skill) | You or Claude | Your session | Writing one |

Local commands ([commands reference](https://code.claude.com/docs/en/commands.md), [local review](https://code.claude.com/docs/en/code-review-local)):

- `/review` is an alias of `/code-review` since v2.1.223. Both take an effort level (`low` to `max`, `ultra`), `--fix`, `--comment` (GitHub PR or GitLab merge request), `--max-findings` and a target (PR number, branch, path, revision range). The review runs as a background subagent with its own context, follows `CLAUDE.md` and does not read `REVIEW.md`.
- With no level typed, it reuses the last level from `low` to `max` you typed, even from an earlier session.
- `/security-review` reviews the diff against origin's default branch and needs an `origin` remote. `/simplify` covers cleanup only, `/verify` builds and runs the app.
- `/code-review` is a bundled skill. A project or personal skill named `code-review` replaces it, and `/review` keeps the bundled one ([resolve skills that share a name](https://code.claude.com/docs/en/skills.md#resolve-skills-that-share-a-name)).
- Plugin features: the in-session [security-guidance plugin](https://code.claude.com/docs/en/security-guidance.md) (hooks: per-edit pattern check, end-of-turn diff review, commit and push review; extra rules in `.claude/claude-security-guidance.md`) is described as the in-session companion to Code Review. [`claude plugin eval`](https://code.claude.com/docs/en/plugin-evals.md) scores a plugin's behavior with graders over three runs per case by default. The GitHub Action example installs `code-review@claude-code-plugins` ([GitHub Actions page](https://code.claude.com/docs/en/github-actions.md#run-a-skill)).

## Plans, prices and limits

- Plans: Team and Enterprise only ([availability](https://code.claude.com/docs/en/code-review.md#availability)). GitHub only, including GitHub Enterprise Server and Enterprise Cloud with data residency. Not available with Zero Data Retention, the HIPAA configuration or customer-managed encryption keys. A Claude organization on a qualifying plan is required even when developers use Bedrock, Google Cloud's Agent Platform or Foundry. Seat prices of the plans were not fetched (unverified, not needed here).
- Price: no flat per-review price ([costs](https://code.claude.com/docs/en/code-review-costs.md#pricing)). Billed on token usage as usage credits, separately from the plan's included usage, to the organization. Cost scales with level, change size, code complexity and number of candidate issues. The preview page said "$15 to $25" on average ([preview](https://claude.com/resources/articles/code-review)); no current figure is published on the pages read. The Average cost column in the admin table gives each repository's own number.
- Controls: monthly spend limit for the Code Review service on `claude.ai/admin-settings/usage`, level per organization or repository (Quick, Standard default, Deep), runs per repository, analytics at `claude.ai/analytics/code-review`. Reviews are skipped when a limit or the credit balance runs out. Covering a whole GitHub organization needs a spend limit and github.com.
- GA offer: eligible Enterprise organizations can claim at least $10,000 in Code Review credits by 2027-01-15, expiring 30 days after claiming ([GA article](https://claude.com/resources/articles/code-review-is-now-generally-available)). Terms were not read (linked support article).
- Ultrareview: 3 free runs on Pro and Max (one-time), then typically $5 to $25 in usage credits, 15 to 25 minutes, branch diffs up to 500 files and 8,000 lines by default ([ultrareview](https://code.claude.com/docs/en/ultrareview.md)). It is a research preview whose pricing may change.
- Local `/code-review` counts toward the session's normal plan usage or API billing. The GitHub Action uses runner minutes plus API tokens or a subscription token ([costs section](https://code.claude.com/docs/en/github-actions.md#manage-costs)).

## Setup and the files it reads

Setup ([setup page](https://code.claude.com/docs/en/code-review-setup.md)): an Owner of the Claude organization turns on "Allow code review" in Admin settings > Claude Code, connects GitHub, installs the Claude GitHub App (one app shared with the GitHub Action and cloud auto-fix; its permission set includes Actions, Contents, Pull requests and Workflows read and write, per the [permissions table](https://code.claude.com/docs/en/github-actions.md#github-app-permissions)), picks repositories, then verifies with a non-draft test PR. No workflow file goes into the repository. New repositories start at "after every push", the most expensive setting.

Files in the repository ([customize page](https://code.claude.com/docs/en/code-review-customize.md)):

- `CLAUDE.md`: the root file and the `CLAUDE.md` files in parent directories of each changed file. A violation becomes a finding.
- `REVIEW.md` at the root, plus optional `REVIEW.md` in subdirectories. Review-only rules: what Important means, a nit cap, paths to skip, checks to always run, an evidence requirement. The service reads it, `/code-review` does not.
- `REVIEW.md` can include up to 8 root-level files with a line of `@file`, and up to 8 skill files as `@.claude/skills/<folder>/SKILL.md` (only the body is used, 30,000 bytes per skill, 150,000 bytes in total, 64 Markdown links at most or the whole root file is skipped).
- Branch rule: `REVIEW.md` is read from the base or default branch, never from the PR's own changes. Lowering severity, excluding paths and capping nits are honored only when the copy comes from a protected default branch. Protection counts as a ruleset that restricts updates, or requires pull requests with at least one approval that is dismissed on a new push or required after the last push (a classic rule counts only for the default branch). With an unprotected default branch only the root file is read, and with unconfirmed protection nothing is read.

## How it differs from BenchKeeper's reviews

BenchKeeper's reviews, from the repository at this commit:

- `plugins/benchkeeper/skills/workflow/software.md:14`: before pushing, for standard, full or risky work, Claude Code runs `/code-review` with no target, risky changes also `/security-review`. Codex or no `origin`: a correctness pass and a security pass by subagents. Docs-only changes skip it unless risky.
- `software.md:15` and `:16`: draft PR with `Closes #<issue>` and key decisions, `gh pr checks --watch`, `gh pr ready`, merge only on the user's instruction.
- `plugins/benchkeeper/skills/workflow/full-tier.md:8`: a spec review of the branch (`mattpocock-skills:code-review`) before the pre-push review.
- `plugins/benchkeeper/skills/workflow/SKILL.md:22`: reviews run once, after the last edit, in a subagent that returns only failures.
- `plugins/benchkeeper/skills/orchestrating-projects/SKILL.md:18-27, :42`: policy fields (`merge.allowed`, `merge.requiredChecks`, `closeIssue`, `trustedAuthors`); the coordinator verifies the diff and required checks, merges only when allowed.
- `plugins/benchkeeper/skills/orchestrating-projects/spec-template.md`: workers address review comments, do not merge.
- `app/src/steps/project.mjs:283-297`: setup writes one BenchKeeper block into `AGENTS.md` and a `CLAUDE.md` that holds only `@AGENTS.md`. It writes no `REVIEW.md`, no PR template and no `CODEOWNERS`.
- `app/src/baseline/profiles/oss.json`: ruleset on `main` with a required pull request, 0 required approvals, no stale-review dismissal, required thread resolution, linear history.

Differences:

| Topic | Anthropic | BenchKeeper |
|---|---|---|
| Local review | `/code-review`, effort level, runs as a forked subagent | Same command, bare, so the depth is the last level the user typed (`software.md:14`) |
| Independent second look | A fresh-context agent reviews before the PR (blog); service on every PR | Same through `/code-review` and Codex subagents, nothing on the PR itself |
| Rules for the reviewer | `CLAUDE.md` plus `REVIEW.md` with severity, nit cap, skip paths, evidence | `AGENTS.md` block only; no review-specific rules |
| Severity handling | Important, Nit, Pre-existing; Anthropic repos require each finding to be fixed or resolved with a reason (blog) | No rule on how to treat findings |
| Convergence | Blog: cap of three rounds, then reconsider the approach; diff-only re-review; fix the bug class; never repeat findings | None; a review can loop |
| Human approval | Blog: low, medium, high risk tiers set from the change, not the author; CI workflow files and listed sensitive paths always need a person; an approval covers one commit | Tiers (quick, standard, full) drive effort, not who approves; the merge policy is one `merge.allowed` switch per project |
| PR template | Blog: Testing, Risk, How to revert | Closes, key decisions (`software.md:15`) |
| Merge gate on the review | Check run never fails; counts readable from a script | `merge.requiredChecks` names checks by name only |
| Post-merge learning | Blog: incidents and reverts become an eval set that scores reviewer changes | Evals view for own skills exists (#367); no link to incidents |

Where BenchKeeper already agrees: it uses the same `/code-review` (and has a "do not install a skill named `code-review` into `.claude/skills/`" rule, `plugins/benchkeeper/skills/setting-up-projects/SKILL.md:101`, which matches the docs' name-replacement rule); `/security-review` needs `origin` and BenchKeeper's Codex or no-origin fallback matches; the oss profile already requires thread resolution, which fits how Code Review resolves its own threads on a fix push; a worker never merges; `trustedAuthors` keeps bots out unless listed.

## Ranked improvements and gaps

Effort: S under an hour, M a few hours, L a day or more. All are proposals for #398; none is decided.

1. Pin the pre-push review depth. Bare `/code-review` reuses the last typed level, even from an earlier session, so the same step runs at different depths ([local review, tune effort](https://code.claude.com/docs/en/code-review-local#tune-effort-and-arguments)). Name a level per tier in `plugins/benchkeeper/skills/workflow/software.md:14` (for example `high` for standard, `xhigh` for full or risky; the choice is the owner's). Also mention `/review` as the same command. Mirror the sentence in `web/src/data/facts.json` (line 211, then `node web/scripts/readme.mjs`). Effort S. Confidence high that the behavior is as documented, medium on the level mapping.
2. Add a convergence rule to the review step. Cap review-and-fix rounds at three, then stop and reconsider the approach or ask; re-review only the new diff after the first round; when a finding is a class of bug fix every instance; treat each finding as fixed or answered with a reason; never post a finding twice. Sources: [blog, "Improving the reviewer"](https://claude.dev/blog/solving-code-review-at-anthropic/) (figures from the blog, unverified host) and the docs' own behavior for later reviews ([what a later review covers](https://code.claude.com/docs/en/code-review-pull-requests.md#what-a-later-review-covers)). File: `plugins/benchkeeper/skills/workflow/software.md` (new line in "Review before pushing") and `SKILL.md:22`. Effort S. The plugin version and changelog rule applies (`AGENTS.md`).
3. Teach the coordinator how to read the hosted review. In `plugins/benchkeeper/skills/orchestrating-projects/SKILL.md` (Outcomes, "Done with a PR") and `policy.example.json`: the Claude Code Review check run is neutral or skipped and never fails, so naming it in `merge.requiredChecks` gates nothing; read the severity counts from the check run (`gh api repos/OWNER/REPO/check-runs/ID`, the last line of `output.text`) and treat Important above zero, or a title starting with "Code review not repeated", as not mergeable; a missing line means no verdict. Resolving a thread dismisses a finding, a reply does not, and comment commands from bots do not start a review, so the coordinator needs the owner's identity or asks for a review by checks. Add the service's bot to `trustedAuthors` only deliberately (its login was not verified). Source: [pull request page, "Read the result from a script"](https://code.claude.com/docs/en/code-review-pull-requests.md#read-the-result-from-a-script). Effort M. Only useful for projects that use the service.
4. Extend the PR body with Testing, Risk and How to revert. Source: blog adoption checklist (unverified host). Files: `software.md:15`, and optionally a `.github/pull_request_template.md` under `app/src/baseline/templates/` (the baseline is a pinned copy of `ESchuderer/repo-baseline`, see `app/src/baseline.mjs`, so the template belongs upstream first). Effort S for the skill text, M for the baseline template.
5. Make merge policy risk-aware. Add to `orchestration.json` (`policy.example.json`) a field that lists paths or change classes the coordinator never merges (CI workflow files, authentication, secrets, deploy configuration; the skill already defines "risky" in `workflow/SKILL.md:18`), and rule that a new commit after verification means verifying again (blog: an approval covers one specific commit; an agent's approval never counts as a person's). Files: `orchestrating-projects/SKILL.md:18-27, :42`, `policy.example.json`, `spec-template.md`. Effort M. Also decide whether setup offers a `CODEOWNERS` for those paths; the repository's rulesets are the owner's (`AGENTS.md`), so the setup would only propose.
6. Setup option for repositories that use the hosted service. When the user says the organization runs Code Review, offer a `REVIEW.md` skeleton (what Important means, nit cap, skip paths, evidence requirement) and warn about two facts. First, `CLAUDE.md` is only `@AGENTS.md` after BenchKeeper's setup (`app/src/steps/project.mjs:297`); whether the service expands that import is unverified, so the safe form is the rules also present in `CLAUDE.md` text or a check on a test PR. Second, `REVIEW.md` exclusions and nit caps need a protected default branch as defined above, and the oss profile (`app/src/baseline/profiles/oss.json`: 0 approvals, no dismissal on push, no update restriction) does not obviously meet it. That second point is an inference from the docs' definition, not tested. Effort M for the optional step, S for a note in `setting-up-projects`. Needs the owner's yes because it touches rulesets and the repository files; it must not name internal sources.
7. Evaluate Anthropic's official security plugin for the security pack. `security-guidance@claude-plugins-official` reviews edits, turns and commits in-session and takes project rules from `.claude/claude-security-guidance.md`. It installs a Python environment under the user's `.claude/security/` folder with the Agent SDK and runs hooks and model calls, which BenchKeeper's own security stance (`AGENTS.md`, issue #184) would have to weigh. Source: [security-guidance](https://code.claude.com/docs/en/security-guidance.md). File: a new note under `evaluations/` plus the index `EVALUATIONS.md` (the repository's convention). Effort M. Not a reason to change `workflow` now.
8. Optional caller workflow for users without Team or Enterprise. The Action can run `code-review@claude-code-plugins` on pull requests in the user's own CI ([GitHub Actions page](https://code.claude.com/docs/en/github-actions.md#run-a-skill)). Costs: API tokens or a subscription token, runner minutes, secrets in the repository, no secrets on fork PRs, and an agent that reads untrusted PR text. The page's example uses unpinned `@v6` and `@v1` tags, which conflicts with BenchKeeper's rule to pin actions to commit SHAs. Would be a repo-baseline caller (`app/src/baseline/callers/`). Effort L, and the security review comes first. Rank low.
9. `/verify` in the verify step for Claude Code. It builds and runs the app and observes the result ([commands](https://code.claude.com/docs/en/commands.md)). BenchKeeper's Verify section (`software.md:55-57`) asks for build, lint, tests and a browser check; `/verify` could be named as one way to do the run-it part. Effort S. Confidence low that it adds anything beyond the existing Playwright step.
10. Incidents and reverts as eval cases. The blog scores reviewer changes against past incident PRs (claim from the blog, unverified host). BenchKeeper has evals for its own skills (#367) and `plugins/benchkeeper/evals/`; a loop that adds a case when a review missed a defect would use them. `claude plugin eval` exists for plugin behavior ([plugin evals](https://code.claude.com/docs/en/plugin-evals.md)) but loads no `CLAUDE.md` (`evaluations/studies.md:46`). Effort L. Rank low, later.

Not recommended: copying the service's spend limit, analytics or hosted runs (they exist only in Anthropic's admin and billing). Nightly review agents over existing code (blog) are a scheduling feature, out of scope for the review steps.

## What could not be verified

- Whether `claude.dev` is an Anthropic site (see above).
- Any current dollar price per review; plan seat prices; the terms of the Enterprise credit offer (linked support article not read).
- Whether the service expands an `@AGENTS.md` import inside `CLAUDE.md`.
- Whether the oss baseline ruleset counts as protection for `REVIEW.md` (inference from the docs' definition, not run against a repository).
- The login of the bot that posts reviews and whether it fits BenchKeeper's `trustedAuthors` rule.
- The blog's and the announcements' numbers (they came through the fetch tool's summary, not as raw HTML). The blog's internal process (blocking findings, risk classifier, merge queue) has no second source.
- The owner's plan: whether the hosted service is available to the owner at all is unknown, so items 3 and 6 are conditional.
- Sub-pages not read in full: [GitHub Enterprise Server](https://code.claude.com/docs/en/github-enterprise-server.md), [Claude Security plugin](https://code.claude.com/docs/en/claude-security.md), the [Anthropic secure-SDLC post](https://claude.com/blog/how-anthropic-secures-its-ai-native-software-development-lifecycle), and the linked [automated security reviews](https://support.claude.com/en/articles/11932705-automated-security-reviews-in-claude-code) article.
