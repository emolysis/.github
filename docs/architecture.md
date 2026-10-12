# Architecture — emolysis/.github

This repository has no runtime. It is a set of files that GitHub reads from a
repository named `.github` in an organization. What matters is which file GitHub reads,
where, and what it overrides.

## Parts

| Part | Files | Who reads it | Scope |
|---|---|---|---|
| Organization profile | `profile/README.md` | GitHub, on the organization page | Organization page only |
| Default issue forms | `.github/ISSUE_TEMPLATE/*.yml` | GitHub, when someone opens an issue | Every repository without its own `.github/ISSUE_TEMPLATE/` |
| Default PR template | `.github/PULL_REQUEST_TEMPLATE.md` | GitHub, when someone opens a pull request | Every repository without its own template |
| Default community files | `SECURITY.md`, `CONTRIBUTING.md` | GitHub, on the Security tab and when opening issues and pull requests | Every repository without its own copy |
| Starter workflows | `workflow-templates/<name>.yml` + `<name>.properties.json` | GitHub, under Actions > New workflow | Repositories in the organization |
| Reusable workflow | `.github/workflows/emolysis-checks.yml` | GitHub Actions, when a caller's job has `uses:` pointing at it | Any repository that calls it |
| This repository's own automation | `.github/workflows/{ci,claude,claude-review,labels}.yml` | GitHub Actions | This repository only |
| Shared labels | `.github/labels.yml` | The Labels workflow | This repository; each repository runs its own copy |

## Rules GitHub applies

- Defaults are all or nothing per kind: a repository with any issue template of its
  own sees none of the defaults; the same for the pull request template and each
  community file.
- The profile, the default community files and the starter workflows (for public
  repositories) work only while this repository is public. Keep it public.
- Starter workflows need both files with the same base name. The `$default-branch`
  placeholder in a starter workflow is replaced with the target repository's default
  branch when someone adds it.
- A reusable workflow runs with the caller's `GITHUB_TOKEN`, capped by the
  `permissions` declared in both files; `emolysis-checks.yml` asks for
  `contents: read` only. Its workflow-level `env` is its own; the caller's `env` does
  not pass through.

## Reusable workflow flow

`emolysis-checks.yml` is one job:

1. Preview guard: fails unless `EMOLYSIS_CHECKS_AVAILABLE` is `"true"`.
2. Validate inputs (`platform` against `databricks|snowflake|fabric|""`, version
   charset).
3. Check out the caller's repository without persisting credentials.
4. Install uv, then the emolysis CLI from PyPI (`uv tool install emolysis[==version]`).
5. Run `emo check [--platform <platform>]` in `inputs.path`.

The interface is specified in `docs/specs/emolysis-checks.md`.

## Checks

`scripts/check.py` (run by `task lint` and `task test`) parses every YAML and JSON
file, enforces the whitespace rules from `.editorconfig`, and checks the structure that
GitHub would otherwise only reject at runtime: issue form fields, labels used by forms
(none may start a workflow), the CI job reporting as `gate`, starter workflow
properties, the reusable workflow's preview guard, inputs and accepted `platform` values
against the docs, and that links and contact details stay inside the organization.
`tests/test_check.py` covers each check with failing inputs. actionlint (with
shellcheck) checks every workflow and starter workflow.
