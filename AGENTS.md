# AGENTS.md — emolysis/.github

This public repository holds the defaults GitHub applies across the `emolysis`
organization: the organization profile, default issue forms, pull request template,
security policy and contributing guide, the starter workflows, and the reusable
`emolysis-checks.yml` workflow that users call from their own CI. It has no product
code. `README.md` explains which file does what.

## What we are building
**An entire data team. One download.** Emolysis is the agentic lakehouse for data
engineering and analytics. We're building a team of agents you can direct from your
laptop: to investigate business questions, develop dashboards, and build and test
pipelines for your data platform. The person directs the work and reviews the results;
production pipelines run on the user's own data platform. Nothing is released yet.

The organization profile (`profile/README.md`, with `profile/banner.png` on top) says
this to everyone who visits the organization. Keep these words when you change it. Say
"we're building" or "will" for anything not released, and never claim that no setup is
needed, that it works offline or that all data stays on the machine: prompts go to the
model provider the user chooses.

## Read first
1. This file.
2. Shared standards: emolysis/rules (private), if you have access. Its `AGENTS.md` links
   the standards every repository follows.
3. `docs/architecture.md`, `docs/development.md`, `docs/contributing.md`.
4. `ROADMAP.md` (honest assessment, current focus, gaps) and the latest entries in
   `log/devlog.md`.
5. `docs/specs/` for the area you are changing (`emolysis-checks.md` for the reusable
   workflow).

## Ground rules
- Work from specs in `docs/specs/`, never from chat history. No spec, no code: open an
  issue labelled `needs-spec`.
- `task gate` green before you finish. Never weaken a check, lower a floor, or skip a
  test to get green.
- Files here change every repository in the organization. Keep issue forms, the pull
  request template and the community files generic: no repository-specific content.
- Issue forms never apply a label that starts a workflow (`agent`): the forms reach
  outside users of public repositories, so a maintainer adds `agent` after review.
- The reusable workflow's inputs are a public interface. Change them only together with
  `docs/specs/emolysis-checks.md` and the README table, and never in a way that breaks
  existing callers without a new major tag.
- Keep `emolysis-checks.yml` and its starter template marked preview, with the preview
  guard on, until the emolysis CLI is published with `emo check` and `emo --version`.
- The CI job id is `gate` with no other name: it is the required status check.
- Workflows declare least-privilege `permissions` and pin actions to a major version.
- Architecture review: a change to the reusable workflow's inputs or to the CI `gate`
  contract goes through the architecture review in emolysis/rules (private) before code,
  if you have access; the pull request then says `Architecture: go (<date>)` or
  `Architecture: pending`.
- Every change ships with tests: extend `scripts/check.py` when you add a new kind of
  file or rule, and cover each new check in `tests/test_check.py`.
- Public/private boundary: this repository is public. Nothing about internal
  architecture, private repositories, customers or anything a public user does not
  need. Link only to github.com/emolysis. No email addresses.

## Picking work
`ROADMAP.md` → Current focus → Gaps → `log/devlog.md` "Still open". Prefer the top item.

## Parallel agents
- One worktree per agent, on a branch named `<area>/<topic>`
  (`git worktree add ../org-dotgithub-<topic> -b <area>/<topic>`).
- Edit only files you own for the task; new things go in new files, not shared ones.
- Shared files (`Taskfile.yml`, `scripts/check.py`, `.github/labels.yml`) get surgical
  edits.
- If someone else's change breaks the tree, do not fix their files; wait or report.

## Before you finish
1. `task gate` passes.
2. Add a terse entry to `log/devlog.md`: date, what landed, numbers, still open.
3. Commit as `<area>: <what>` (append `(green)` when the gate passed).

## Commands
| Command | What it does |
|---|---|
| `task setup` | Fetch the pinned tools (actionlint, shellcheck, ruff, PyYAML, pytest) into the uv cache. Idempotent. |
| `task gate` | Everything CI checks, non-mutating: `lint` then `test`. |
| `task lint` | actionlint (with shellcheck) on every workflow and starter workflow, YAML and JSON parse, whitespace, ruff on `scripts/` and `tests/`. |
| `task test` | Structural checks: issue forms and their labels, the CI `gate` job, starter workflow properties, the reusable workflow's preview guard and inputs vs docs, required files, link and email hygiene; then pytest on `tests/`. |
| `task fmt` | Fix whitespace in place and format `scripts/` and `tests/`. |
