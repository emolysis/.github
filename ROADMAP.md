# Roadmap — emolysis/.github

## Honest assessment (2026-10-12)

Fresh scaffold, not yet pushed. The organization profile, default issue forms, pull
request template, security policy and contributing guide are written and pass the gate.
The reusable `emo check` workflow and its starter workflow are a preview only: the
emolysis CLI is not published, so the workflow stops at its preview guard. Nothing here
has run on GitHub yet; the files are checked locally with actionlint, shellcheck and
`scripts/check.py`.

## Current focus

Get this repository live so the organization profile and the default issue and pull
request templates apply to every repository.

## Gaps

- `emolysis-checks.yml` is gated off (`EMOLYSIS_CHECKS_AVAILABLE: "false"`, enforced by
  `task gate`). Turn it on in the release that publishes the emolysis CLI, together with
  working `emo check` and `emo --version`; both are planned, neither exists yet.
- No end-to-end test of the reusable workflow: needs a published CLI and a small sample
  project that calls it from another repository.
- No release tags. The starter workflow calls `@main`; tag `v0` (and move it per
  release) once the workflow is usable.
- Private vulnerability reporting has to be enabled in the organization settings for
  public repositories before `SECURITY.md` works as written.
- Labels from `.github/labels.yml` are applied per repository by its Labels workflow;
  repositories created later need it too, or the same labels set as organization
  defaults.
- The profile has no logo or banner yet.

## Done

- 2026-10-12: scaffold: profile, issue forms (bug, feature, agent task), pull request
  template, `SECURITY.md`, `CONTRIBUTING.md`, preview reusable workflow and starter
  workflow, CI, Claude workflows, `task gate`.
- 2026-10-12: review fixes: CI reports as `gate`; the agent task form no longer applies
  `agent`; checks and tests for both, the preview guard and the accepted `platform`
  values; branches named `<area>/<topic>`.
