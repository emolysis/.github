# emolysis/.github

Organization-wide defaults for the `emolysis` GitHub organization: the profile shown on
the organization page, default community files (issue forms, pull request template,
security policy, contributing guide), and a reusable workflow that runs Emolysis checks
in your own CI.

## Status

Fresh scaffold (2026-10-12). Emolysis itself is in private development and not released.
The profile and community files are ready to use. The reusable `emo check` workflow is a
**preview**: the emolysis CLI it installs is not published yet, so the workflow fails
with a "not available yet" error until it is. See [ROADMAP.md](ROADMAP.md).

## How organization defaults work

GitHub reads some files from this repository and applies them across the organization:

| Path | Effect |
|---|---|
| `profile/README.md` | Shown on the organization page, github.com/emolysis. |
| `.github/ISSUE_TEMPLATE/` | Issue forms (bug, feature, agent task) for every repository that has no `.github/ISSUE_TEMPLATE/` of its own. |
| `.github/PULL_REQUEST_TEMPLATE.md` | Pull request template for every repository without its own. |
| `SECURITY.md` | Security policy for every repository without its own. |
| `CONTRIBUTING.md` | Contributing guide for every repository without its own. |
| `workflow-templates/` | Starter workflows listed under **Actions > New workflow** in organization repositories. |
| `.github/workflows/emolysis-checks.yml` | Reusable workflow; any repository can call it with `uses:`. |

A repository that has its own copy of a file uses its copy instead; defaults are not
merged. Everything else in `.github/workflows/` (CI, Claude, labels) runs for this
repository only.

## Reusable workflow: Emolysis checks (preview)

Not available yet. When the emolysis CLI is released, a pipeline project will be able
to run the same checks Emolysis runs locally (`emo check`: platform lint, golden tests
on DuckDB, cost estimate) in its own CI:

```yaml
jobs:
  emolysis:
    uses: emolysis/.github/.github/workflows/emolysis-checks.yml@main
    with:
      path: .
      platform: databricks
```

| Input | Default | Meaning |
|---|---|---|
| `path` | `.` | Directory of the Emolysis project (the one holding `emolysis.yml`). |
| `platform` | empty | `databricks`, `snowflake` or `fabric`. Empty uses the platform in `emolysis.yml`. |
| `emolysis-version` | empty | emolysis CLI version to install from PyPI. Empty installs the latest release. |

The workflow needs only `contents: read` and no platform credentials. Once releases are
tagged, pin a tag or commit SHA instead of `@main`. The same workflow is offered as the
"Emolysis checks (preview)" starter workflow. Interface spec:
[docs/specs/emolysis-checks.md](docs/specs/emolysis-checks.md).

## Working on this repository

Needs [uv](https://docs.astral.sh/uv/) and [Task](https://taskfile.dev) v3. All other
tools run through `uvx` with pinned versions.

```sh
task setup   # fetch pinned tools (actionlint, shellcheck, ruff, PyYAML, pytest) into the uv cache
task gate    # actionlint, YAML/JSON parse, whitespace, ruff, structural checks, pytest
task fmt     # fix whitespace and format scripts/ and tests/
```

Read [AGENTS.md](AGENTS.md) before changing anything.

## Layout

```text
profile/README.md                 organization profile
.github/ISSUE_TEMPLATE/           default issue forms and chooser config
.github/PULL_REQUEST_TEMPLATE.md  default pull request template
.github/workflows/                emolysis-checks.yml (reusable) and this repo's CI
.github/labels.yml                labels shared by every repository
workflow-templates/               starter workflows for organization repositories
SECURITY.md, CONTRIBUTING.md      default community files
docs/                             architecture, development, contributing, specs
scripts/check.py                  lint and structural checks behind task lint / task test
tests/test_check.py               tests for scripts/check.py
log/devlog.md                     dev log
```

## License

MIT, see [LICENSE](LICENSE). The Emolysis name and logos are not covered; see
[NOTICE](NOTICE).
