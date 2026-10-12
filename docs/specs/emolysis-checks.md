# Spec: reusable workflow `emolysis-checks.yml`

Status: preview. The interface below is planned; the workflow is gated off until the
emolysis CLI is published.

## Purpose

Let any repository that holds an Emolysis pipeline project run `emo check` in its own
GitHub Actions CI, with one `uses:` line and no platform credentials. A green run means
the project passes the same checks Emolysis runs locally.

## Interface

File: `.github/workflows/emolysis-checks.yml` in `emolysis/.github`, `on: workflow_call`.

| Input | Type | Required | Default | Rule |
|---|---|---|---|---|
| `path` | string | no | `.` | Directory holding the project's `emolysis.yml`, relative to the repository root. |
| `platform` | string | no | empty | One of `databricks`, `snowflake`, `fabric`, or empty to use the platform set in `emolysis.yml`. Anything else fails the run before installing. |
| `emolysis-version` | string | no | empty | Exact version of the `emolysis` PyPI distribution, for example `0.1.0`. Must start with a digit and contain only `0-9A-Za-z.+!-`. Empty installs the latest release. |

No secrets and no outputs. Permissions: `contents: read`.

Callers reference a tag or commit SHA once releases exist; `@main` until then.

## Behavior

1. **Preview guard.** While the workflow-level env `EMOLYSIS_CHECKS_AVAILABLE` is not
   `"true"`, the job fails immediately with an error annotation titled "Emolysis checks
   are not available yet" and installs nothing.
2. **Validate inputs** as in the table. Invalid input fails with an error annotation
   naming the input and the bad value.
3. **Check out** the caller's repository with `persist-credentials: false`.
4. **Install** uv (`astral-sh/setup-uv`), then `uv tool install emolysis` or
   `emolysis==<emolysis-version>`, and put uv's tool directory on `PATH`.
5. **Print** `emo --version`.
6. **Run** `emo check`, adding `--platform <platform>` when `platform` is set, with
   `path` as the working directory. The job's result is `emo check`'s exit status.

`emo check` and `emo --version` are planned for the CLI and do not exist yet; the
preview guard stays on until they ship. `emo check` itself (specified with the CLI, not
here) lints the project for the target platform, runs its golden tests on DuckDB against
the committed fixtures, and reports a cost estimate. It must not need network access to
a data platform.

## Starter workflow

`workflow-templates/emolysis-checks.yml` calls this workflow on pushes to
`$default-branch` and on pull requests, cancels superseded pull request runs, and passes
`path: .`. `workflow-templates/emolysis-checks.properties.json` names it "Emolysis
checks (preview)" and suggests it for repositories with an `emolysis.yml` or
`emolysis.yaml` at the root.

## Leaving preview

In the release that publishes the CLI with a working `emo check`:

1. Set `EMOLYSIS_CHECKS_AVAILABLE: "true"` and `CLI_PUBLISHED = True` in
   `scripts/check.py`, drop the preview wording from the workflow, the starter workflow,
   its properties file, the README and `profile/README.md`.
2. Run it end to end from a sample project in another organization repository.
3. Tag the release `v0` and point the starter workflow at `@v0`.

## Out of scope

Platform credentials, deploying, publishing dashboards, commenting on pull requests.
Those belong to other integrations.
