# Contributing — emolysis/.github

The organization-wide guide is [`CONTRIBUTING.md`](../CONTRIBUTING.md). This page adds
what is specific to this repository.

## Before you open a pull request

- `task gate` passes.
- `log/devlog.md` has an entry for the change.
- If you changed a default (issue form, pull request template, `SECURITY.md`,
  `CONTRIBUTING.md`), the pull request says so in its summary: it changes what every
  repository in the organization shows.
- If you changed the reusable workflow, `docs/specs/emolysis-checks.md` and the README
  are updated in the same pull request, and the change is backward compatible for
  existing callers.

## What does not belong here

This repository is public and applies to the whole organization. Do not add:

- content specific to one repository (put it in that repository);
- internal details, plans or anything about private repositories beyond their names;
- secrets, tokens, email addresses or links outside github.com/emolysis;
- logos or other brand assets (see `NOTICE`).

## Commits and reviews

Branches are `<area>/<topic>`. Commit as `<area>: <what>`, with `(green)` appended when
the gate passed; areas here are `profile`, `issues`, `pr-template`, `community`,
`workflows`, `templates`, `checks`, `docs`. Every pull request gets a Claude review against `AGENTS.md` when the
`ANTHROPIC_API_KEY` secret is set. A maintainer merges once CI is green.
