# Devlog — .github

Newest entry first. Format: `standards/devlog.md` in emolysis/rules (private).

## 2026-10-18 · profile: the new positioning and banner (green)

- Landed: `profile/README.md` opens with the banner `profile/banner.png` and the approved
  positioning: "An entire data team. One download.", the agentic lakehouse for data
  engineering and analytics, a team of agents you direct from your laptop. Unreleased
  features in the future tense; status unchanged ("Nothing is released yet").
- Landed: `check_profile_images` in `scripts/check.py`: every profile image has alt text,
  loads from this repository's main branch and is at most 1 MB. Nine new cases in
  `tests/test_check.py`. `AGENTS.md` opens with "What we are building".
- Numbers: 41 tests pass; banner 2000x500 PNG, 212 KB.
- Decisions: the founder supplied the banner; it shows the organization's contact address
  and website as part of the image. The text rule (no email addresses) still holds and
  passes.
- Still open: the banner renders on the organization page once this reaches `main`.

## 2026-10-12 · workflows: review fixes, CI reports as `gate`, agent form label (green)

- Landed: `.github/workflows/ci.yml` job `gate` now reports as `gate` (was `task gate`), the required status check.
- Landed: `.github/ISSUE_TEMPLATE/agent-task.yml` no longer applies `agent`; a maintainer adds it after review, so an outside issue author cannot start `claude.yml` through the form.
- Landed: `scripts/check.py` checks that no issue form applies a label that starts a workflow (read from `claude.yml`), that CI reports as `gate`, that the reusable workflow's preview guard is its first step and stays off while `CLI_PUBLISHED` is false, and that `platform` accepts exactly `databricks`, `snowflake`, `fabric` or empty, as the spec and README list. `tests/test_check.py` (pytest 9.1.1, run by `task test`) covers each check with failing inputs.
- Landed: branches are `<area>/<topic>` in `AGENTS.md`, `CONTRIBUTING.md` and `docs/contributing.md`; `docs/specs/emolysis-checks.md` says `emo check` and `emo --version` are planned and not in the CLI yet (interface unchanged); this devlog in the standard format.
- Numbers: 6 workflow files pass actionlint 1.7.12 with shellcheck 0.11.0; `scripts/check.py test` runs 7 check groups (+1); 31 pytest tests pass (new).
- Decisions: shared `claude.yml` trigger unchanged; outside `@claude` comments end in a failed run by design. Reasoning in `docs/development.md`, "Claude in this repository".
- Still open: enable the reusable workflow when the CLI ships `emo check` and `emo --version`; end-to-end test from a sample project; release tags; private vulnerability reporting org-wide.
- Next: get this repository live (`ROADMAP.md` Current focus).

## 2026-10-12 · scaffold: org profile, default community files, preview reusable workflow (green)

- Landed: `profile/README.md`; default issue forms `bug`, `feature`, `agent-task` (applied label `agent`) and chooser `config.yml`; `.github/PULL_REQUEST_TEMPLATE.md`; `SECURITY.md` (private vulnerability reporting only); `CONTRIBUTING.md`.
- Landed: reusable workflow `.github/workflows/emolysis-checks.yml` (inputs `path`, `platform`, `emolysis-version`) and starter workflow `workflow-templates/emolysis-checks.yml`, both preview and gated off; spec `docs/specs/emolysis-checks.md`.
- Landed: CI, Claude, Claude review and Labels workflows; `Taskfile.yml` (`setup`, `fmt`, `lint`, `test`, `gate`); `scripts/check.py`.
- Numbers: 6 workflow files pass actionlint 1.7.12 with shellcheck 0.11.0; `scripts/check.py test` runs 6 check groups.
- Still open: enable the reusable workflow when the CLI ships; end-to-end test from a sample project; release tags; enable private vulnerability reporting org-wide.
