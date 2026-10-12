# Contributing

This guide applies to every repository in the `emolysis` organization that does not
have its own `CONTRIBUTING.md`.

## Each repository's own docs come first

Every repository has an `AGENTS.md` at its root and a `docs/contributing.md`. They are
authoritative for that repository: read them before you change anything. They apply to
people and to coding agents alike.

## Workflow

1. Open or pick an issue. Larger changes need a spec under `docs/specs/` first; an issue
   without one is labelled `needs-spec`.
2. Work on a short-lived branch named `<area>/<topic>` and open a pull request into
   `main`. Fill in the pull request template.
3. Install the toolchain and run the gate:

   ```sh
   task setup   # install pinned tools and dependencies (idempotent)
   task gate    # everything CI checks; must pass before review
   ```

   `task` is [Task](https://taskfile.dev) v3. `task --list` shows every task.
4. Add a short entry to `log/devlog.md`: date, what landed, numbers, what is still open.
5. Keep commits small and name them `<area>: <what>`.

CI runs exactly `task setup && task gate`. A pull request merges only when it is green.
Never weaken a check, lower a threshold or skip a test to get there.

## Security

Do not report vulnerabilities in issues or pull requests. Follow the security policy on
the repository's **Security** tab and report privately.

## License

Contributions to a public repository are made under that repository's license. The
Emolysis name and logos are not covered by it; see the repository's `NOTICE`.
