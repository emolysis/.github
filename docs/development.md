# Development — emolysis/.github

## Tools

- [uv](https://docs.astral.sh/uv/) runs every tool, pinned in `Taskfile.yml`:
  actionlint (from `actionlint-py`) with shellcheck (from `shellcheck-py`) on its
  `PATH`, ruff, `scripts/check.py` with PyYAML via its inline script metadata, and
  pytest for `tests/test_check.py`. Python 3.12 or newer.
- [Task](https://taskfile.dev) v3: `uv tool install go-task-bin` if you do not have it.

No lockfile: every tool is fetched by exact version.

```sh
task setup   # fetch the pinned tools; idempotent
task gate    # lint + test, non-mutating; what CI runs after task setup
task fmt     # fix whitespace, format scripts/
```

To bump a tool, change its version in `Taskfile.yml`, run `task setup && task gate`, and
note the bump in `log/devlog.md`.

## Changing an issue form or the pull request template

1. Edit the file under `.github/ISSUE_TEMPLATE/` or `.github/PULL_REQUEST_TEMPLATE.md`.
2. `task gate` checks the form structure, that its labels exist in
   `.github/labels.yml`, and that no form applies a label that starts a workflow
   (`agent`, read from `claude.yml`).
3. Remember the change applies to every repository without its own templates. Keep
   wording generic.

GitHub validates issue forms only when someone opens the chooser. After merging, open
**New issue** in this repository and confirm every form renders.

## Changing the reusable workflow

1. Update `docs/specs/emolysis-checks.md` first.
2. Change `.github/workflows/emolysis-checks.yml`, the README input table and, if the
   way it is called changes, `workflow-templates/emolysis-checks.yml`.
3. `task gate` fails if the inputs and the docs disagree, if the accepted `platform`
   values drift from `PLATFORMS` in `scripts/check.py`, or if the preview guard is not
   the first step or is switched on while `CLI_PUBLISHED` is false.
4. To try a change before merging, call the workflow from a scratch repository in the
   organization with `uses: emolysis/.github/.github/workflows/emolysis-checks.yml@<branch>`.

## Adding a starter workflow

Add `workflow-templates/<name>.yml` and `workflow-templates/<name>.properties.json`
(`name`, `description`, `categories`, optional `iconName` and `filePatterns`). Use an
Octicon (`"iconName": "octicon <name>"`) rather than a brand image. `task gate` checks
the pair and runs actionlint on the template.

## Claude in this repository

`claude.yml` reacts to issues labelled `agent` and to `@claude` mentions. The agent
task form does not add `agent`; a maintainer adds it after reading the issue.
`claude-review.yml` reviews pull requests against `AGENTS.md`. Both need the
`ANTHROPIC_API_KEY` secret and skip cleanly without it. Repository variables
`CLAUDE_MODEL`, `CLAUDE_REVIEW_MODEL` and `ANTHROPIC_BASE_URL` override the defaults.

`claude.yml` is shared by every repository and is not edited here. In a public
repository, an `@claude` comment from someone without write access ends in a failed run,
because claude-code-action rejects actors without write access. That failure is
expected and harmless. The trigger is deliberately not filtered on `author_association`,
which can block maintainers whose organization membership is private.

## Claude Code sessions

`.claude/hooks/session-start.sh` installs Task if needed and runs `task setup` in
Claude Code cloud sessions. Test it with:

```sh
CLAUDE_CODE_REMOTE=true CLAUDE_PROJECT_DIR=$PWD .claude/hooks/session-start.sh
```
