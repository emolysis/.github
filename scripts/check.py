# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Repository checks for emolysis/.github.

Subcommands:
  fmt   fix whitespace in place (LF line endings, no trailing whitespace, one final newline)
  lint  parse every YAML and JSON file and check whitespace (non-mutating)
  test  structural checks: issue forms, CI, workflow templates, the reusable workflow, docs,
        profile images

Exits 1 and prints one line per problem when a check fails.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent

TEXT_SUFFIXES = {".md", ".yml", ".yaml", ".json", ".py", ".sh", ".toml", ".txt", ""}
TEXT_NAMES = {"LICENSE", "NOTICE", ".editorconfig", ".gitattributes", ".gitignore"}
# Markdown uses two trailing spaces as a line break; .editorconfig keeps them.
TRAILING_WS_EXEMPT = {".md"}

WORKFLOWS_DIR = Path(".github/workflows")
CI_WORKFLOW = WORKFLOWS_DIR / "ci.yml"
# GitHub reports a job's check under its name; branch protection requires `gate`.
CI_GATE_JOB = "gate"
REUSABLE_WORKFLOW = WORKFLOWS_DIR / "emolysis-checks.yml"
REVIEW_WORKFLOW = WORKFLOWS_DIR / "claude-review.yml"
REVIEW_PUSH_EVENTS = {"synchronize", "reopened", "edited"}
REUSABLE_INPUTS = {"path", "platform", "emolysis-version"}
REUSABLE_SECRETS = {"token"}
REUSABLE_SPEC = Path("docs/specs/emolysis-checks.md")
# Values the reusable workflow accepts for `platform`, besides empty. The spec owns this list.
PLATFORMS = ("databricks", "snowflake", "fabric")
# The emolysis CLI is not published, so the reusable workflow stays behind its preview guard.
# Set to True in the release that publishes the CLI (spec: "Leaving preview").
CLI_PUBLISHED = False
PREVIEW_ENV = "EMOLYSIS_CHECKS_AVAILABLE"
REQUIRED_FILES = [
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "ROADMAP.md",
    "LICENSE",
    "NOTICE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "profile/README.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/config.yml",
    "log/devlog.md",
    str(REUSABLE_SPEC),
]
ROADMAP_SECTIONS = [
    "## Honest assessment (",
    "## Current focus",
    "## Gaps",
    "## Done",
]
ISSUE_FORM_TYPES = {"markdown", "textarea", "input", "dropdown", "checkboxes"}
GITHUB_URL = re.compile(r"https?://(?:www\.)?github\.com/([^/\s)\"'>#?]+)")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b")
REMOTE_REUSABLE = re.compile(r"^emolysis/\.github/(\.github/workflows/[^@]+)@\S+$")
LABEL_CONDITION = re.compile(r"github\.event\.label\.name\s*==\s*'([^']+)'")
PLATFORM_CASE = re.compile(r'case "\$PLATFORM" in\s*\n\s*([^)\n]+)\)\s*;;')
# Profile images load from this repository's main branch, which the organization page shows.
PROFILE_README = Path("profile/README.md")
PROFILE_IMAGE_PREFIX = "https://github.com/emolysis/.github/raw/main/"
PROFILE_IMAGE_MAX_BYTES = 1_000_000
HTML_IMG = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
HTML_ATTR = re.compile(r'\b(src|alt)="([^"]*)"')
MARKDOWN_IMG = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)")

Problems = list[str]


def repo_files() -> list[Path]:
    """Tracked and untracked-but-not-ignored files, relative to the repository root."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout.decode()
        names = [n for n in out.split("\0") if n]
    except (OSError, subprocess.CalledProcessError):
        names = [
            str(p.relative_to(ROOT))
            for p in ROOT.rglob("*")
            if p.is_file() and ".git" not in p.relative_to(ROOT).parts
        ]
    return sorted(Path(n) for n in names if (ROOT / n).is_file())


def is_text(path: Path) -> bool:
    return path.suffix in TEXT_SUFFIXES or path.name in TEXT_NAMES


def text_files() -> Iterator[Path]:
    for path in repo_files():
        if is_text(path):
            yield path


def load_yaml(path: Path) -> Any:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def workflow_on(doc: dict[str, Any]) -> Any:
    # YAML 1.1 reads the bare key `on` as boolean true.
    return doc.get("on", doc.get(True))


# --- fmt and whitespace ------------------------------------------------------------------


def normalized(path: Path, text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if path.suffix not in TRAILING_WS_EXEMPT:
        text = "\n".join(line.rstrip(" \t") for line in text.split("\n"))
    return text.rstrip("\n") + "\n" if text.strip() else text


def whitespace_problems(path: Path, text: str) -> Problems:
    problems: Problems = []
    if "\r" in text:
        problems.append(f"{path}: CR line endings; use LF")
    if text and not text.endswith("\n"):
        problems.append(f"{path}: missing final newline")
    if text.endswith("\n\n"):
        problems.append(f"{path}: blank lines at end of file")
    for number, line in enumerate(text.split("\n"), start=1):
        if path.suffix not in TRAILING_WS_EXEMPT and line != line.rstrip(" \t"):
            problems.append(f"{path}:{number}: trailing whitespace")
        if path.suffix in {".yml", ".yaml"} and "\t" in line:
            problems.append(f"{path}:{number}: tab character in YAML")
    return problems


def cmd_fmt() -> Problems:
    for path in text_files():
        full = ROOT / path
        text = full.read_text(encoding="utf-8")
        fixed = normalized(path, text)
        if fixed != text:
            full.write_text(fixed, encoding="utf-8", newline="\n")
            print(f"formatted {path}")
    return []


# --- lint --------------------------------------------------------------------------------


def cmd_lint() -> Problems:
    problems: Problems = []
    for path in text_files():
        try:
            text = (ROOT / path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            problems.append(f"{path}: not valid UTF-8")
            continue
        problems += whitespace_problems(path, text)
        if path.suffix in {".yml", ".yaml"}:
            try:
                yaml.safe_load(text)
            except yaml.YAMLError as exc:
                problems.append(f"{path}: invalid YAML: {exc}".replace("\n", " "))
        elif path.suffix == ".json":
            try:
                json.loads(text)
            except json.JSONDecodeError as exc:
                problems.append(f"{path}: invalid JSON: {exc}")
    return problems


# --- test --------------------------------------------------------------------------------


def check_required_files() -> Problems:
    problems = [
        f"{name}: required file is missing"
        for name in REQUIRED_FILES
        if not (ROOT / name).is_file()
    ]
    claude = ROOT / "CLAUDE.md"
    if claude.is_file() and claude.read_text(encoding="utf-8") != "@AGENTS.md\n":
        problems.append("CLAUDE.md: must contain exactly one line, @AGENTS.md")
    roadmap = ROOT / "ROADMAP.md"
    if roadmap.is_file():
        text = roadmap.read_text(encoding="utf-8")
        problems += [
            f"ROADMAP.md: missing section starting with {heading!r}"
            for heading in ROADMAP_SECTIONS
            if heading not in text
        ]
    return problems


def label_names() -> set[str]:
    labels = load_yaml(Path(".github/labels.yml")) or []
    return {label["name"] for label in labels}


def workflow_docs() -> dict[Path, Any]:
    return {
        path.relative_to(ROOT): load_yaml(path.relative_to(ROOT))
        for path in sorted((ROOT / WORKFLOWS_DIR).glob("*.yml"))
    }


def trigger_labels(workflows: Iterable[Any]) -> set[str]:
    """Labels whose addition starts a workflow: `label_trigger` inputs and label conditions."""
    labels: set[str] = set()
    for doc in workflows:
        for job in ((doc or {}).get("jobs") or {}).values():
            labels.update(LABEL_CONDITION.findall(str(job.get("if", ""))))
            for step in job.get("steps") or []:
                labels.update(LABEL_CONDITION.findall(str(step.get("if", ""))))
                trigger = (step.get("with") or {}).get("label_trigger")
                if trigger:
                    labels.add(str(trigger))
    return labels


def form_label_problems(
    path: Path, labels: Iterable[str], known: set[str], automated: set[str]
) -> Problems:
    problems: Problems = []
    for label in labels:
        if label not in known:
            problems.append(f"{path}: label {label!r} is not defined in .github/labels.yml")
        if label in automated:
            # Default forms reach outside users of public repositories, and GitHub applies
            # form labels for any author. Automation starts only after a maintainer's review.
            problems.append(
                f"{path}: label {label!r} starts a workflow; forms must not apply it, "
                "a maintainer adds it after review"
            )
    return problems


def check_issue_forms() -> Problems:
    problems: Problems = []
    known_labels = label_names()
    # Every repository runs the same shared claude.yml, so this repository's workflows
    # name the labels that start automation anywhere the default forms apply.
    automated = trigger_labels(workflow_docs().values())
    forms_dir = Path(".github/ISSUE_TEMPLATE")
    forms = sorted(p.relative_to(ROOT) for p in (ROOT / forms_dir).glob("*.yml"))
    if not forms:
        problems.append(f"{forms_dir}: no issue forms")
    for path in forms:
        doc = load_yaml(path)
        if path.name == "config.yml":
            problems += check_issue_config(path, doc)
            continue
        if not isinstance(doc, dict):
            problems.append(f"{path}: must be a mapping")
            continue
        for key in ("name", "description"):
            if not isinstance(doc.get(key), str) or not doc[key].strip():
                problems.append(f"{path}: missing {key}")
        problems += form_label_problems(path, doc.get("labels") or [], known_labels, automated)
        body = doc.get("body")
        if not isinstance(body, list) or not body:
            problems.append(f"{path}: body must be a non-empty list")
            continue
        ids: set[str] = set()
        has_field = False
        for index, element in enumerate(body):
            kind = element.get("type")
            if kind not in ISSUE_FORM_TYPES:
                problems.append(f"{path}: body[{index}] has unknown type {kind!r}")
                continue
            if kind == "markdown":
                continue
            has_field = True
            element_id = element.get("id")
            if not element_id:
                problems.append(f"{path}: body[{index}] ({kind}) needs an id")
            elif element_id in ids:
                problems.append(f"{path}: duplicate id {element_id!r}")
            else:
                ids.add(element_id)
            if not (element.get("attributes") or {}).get("label"):
                problems.append(f"{path}: body[{index}] ({kind}) needs attributes.label")
            if kind == "dropdown" and not (element.get("attributes") or {}).get("options"):
                problems.append(f"{path}: body[{index}] dropdown needs options")
        if not has_field:
            problems.append(f"{path}: body has no input fields")
    return problems


def check_issue_config(path: Path, doc: Any) -> Problems:
    problems: Problems = []
    if not isinstance(doc, dict) or not isinstance(doc.get("blank_issues_enabled"), bool):
        return [f"{path}: blank_issues_enabled must be true or false"]
    for link in doc.get("contact_links") or []:
        for key in ("name", "url", "about"):
            if not link.get(key):
                problems.append(f"{path}: contact link is missing {key}")
        if not str(link.get("url", "")).startswith("https://"):
            problems.append(f"{path}: contact link url must be https")
    return problems


def check_workflows() -> Problems:
    problems: Problems = []
    for path, doc in workflow_docs().items():
        if "permissions" not in doc:
            problems.append(f"{path}: set top-level permissions explicitly")
        if path == REVIEW_WORKFLOW:
            problems += review_trigger_problems(path, doc)
        problems += draft_trigger_problems(path, doc)
    return problems


def draft_trigger_problems(path: Path, doc: Any) -> Problems:
    """A workflow whose jobs skip drafts lists ready_for_review in its pull_request types:
    the default types never fire when a draft is marked ready, so it would run nothing until
    the next push (emolysis/rules standards/ci.md, Minutes, Drafts)."""
    doc = doc or {}
    jobs = doc.get("jobs") or {}
    skips = any(
        "github.event.pull_request.draft" in str((job or {}).get("if", "")) for job in jobs.values()
    )
    on = workflow_on(doc)
    if not skips or not isinstance(on, dict) or "pull_request" not in on:
        return []
    types = (on.get("pull_request") or {}).get("types") or []
    if "ready_for_review" not in types:
        return [f"{path}: jobs skip drafts, so pull_request.types must list ready_for_review"]
    return []


def review_trigger_problems(path: Path, doc: Any) -> Problems:
    """The automated review runs once per pull request, never on every push: a review
    spends runner minutes and API credit (emolysis/rules standards/ci.md, Minutes)."""
    on = workflow_on(doc or {})
    pull_request = (on or {}).get("pull_request") if isinstance(on, dict) else None
    if not isinstance(pull_request, dict):
        return [f"{path}: trigger on pull_request with explicit types"]
    types = pull_request.get("types")
    if not isinstance(types, list) or not types:
        return [f"{path}: pull_request.types must list the events; the default has synchronize"]
    on_push = sorted(REVIEW_PUSH_EVENTS & set(types))
    if on_push:
        return [
            f"{path}: pull_request.types {on_push} run the review on every push; "
            "use opened, ready_for_review and labeled"
        ]
    return []


def ci_gate_problems(path: Path, doc: Any) -> Problems:
    """CI must report its result as the required status check `gate`."""
    job = ((doc or {}).get("jobs") or {}).get(CI_GATE_JOB)
    if not isinstance(job, dict):
        return [f"{path}: needs a job with id {CI_GATE_JOB!r}, the required status check"]
    name = job.get("name", CI_GATE_JOB)
    if name != CI_GATE_JOB:
        return [
            f"{path}: job {CI_GATE_JOB!r} reports as {name!r}, not {CI_GATE_JOB!r}; "
            f"drop its name or set it to {CI_GATE_JOB}"
        ]
    return []


def check_ci_gate() -> Problems:
    if not (ROOT / CI_WORKFLOW).is_file():
        return [f"{CI_WORKFLOW}: required file is missing"]
    return ci_gate_problems(CI_WORKFLOW, load_yaml(CI_WORKFLOW))


def expression(value: Any) -> str:
    """A workflow `if:` with `${{ }}` and all whitespace removed, for comparison."""
    text = str(value or "").strip()
    if text.startswith("${{") and text.endswith("}}"):
        text = text[3:-2]
    return re.sub(r"\s+", "", text)


def preview_guard_problems(path: Path, doc: Any, published: bool) -> Problems:
    """Every job starts with the preview guard; it stays on until the CLI is published."""
    problems: Problems = []
    env = (doc or {}).get("env") or {}
    if PREVIEW_ENV not in env:
        problems.append(f"{path}: workflow env must define {PREVIEW_ENV}")
    elif not published and str(env[PREVIEW_ENV]) != "false":
        problems.append(
            f'{path}: {PREVIEW_ENV} must be "false" until the emolysis CLI is published'
        )
    guard = expression(f"env.{PREVIEW_ENV} != 'true'")
    for job_id, job in ((doc or {}).get("jobs") or {}).items():
        steps = job.get("steps") or [{}]
        first = steps[0]
        if expression(first.get("if")) != guard or "exit 1" not in str(first.get("run", "")):
            problems.append(
                f"{path}: job {job_id}: the first step must be the preview guard "
                f"(if: env.{PREVIEW_ENV} != 'true', then exit 1)"
            )
    return problems


def accepted_platforms(doc: Any) -> set[str] | None:
    """The `platform` values the workflow's validation step lets through, or None."""
    for job in ((doc or {}).get("jobs") or {}).values():
        for step in job.get("steps") or []:
            match = PLATFORM_CASE.search(str(step.get("run", "")))
            if match:
                return {alt.strip().strip('"') for alt in match.group(1).split("|")}
    return None


def platform_problems(path: Path, doc: Any) -> Problems:
    accepted = accepted_platforms(doc)
    expected = {"", *PLATFORMS}
    if accepted is None:
        return [f'{path}: no step validates platform with case "$PLATFORM" in ...']
    if accepted != expected:
        return [f"{path}: platform accepts {sorted(accepted)}, the spec allows {sorted(expected)}"]
    return []


def platform_doc_problems(path: Path, text: str) -> Problems:
    """The doc's `platform` table row lists every accepted platform."""
    rows = [line for line in text.splitlines() if line.startswith("| `platform` |")]
    if not rows:
        return [f"{path}: no table row for input `platform`"]
    return [
        f"{path}: `platform` row does not list `{platform}`"
        for platform in PLATFORMS
        if f"`{platform}`" not in rows[0]
    ]


def reusable_inputs() -> dict[str, Any]:
    doc = load_yaml(REUSABLE_WORKFLOW)
    call = (workflow_on(doc) or {}).get("workflow_call") or {}
    inputs: dict[str, Any] = call.get("inputs") or {}
    return inputs


def reusable_secrets() -> dict[str, Any]:
    doc = load_yaml(REUSABLE_WORKFLOW)
    call = (workflow_on(doc) or {}).get("workflow_call") or {}
    secrets: dict[str, Any] = call.get("secrets") or {}
    return secrets


def secret_problems(path: Path, secrets: dict[str, Any]) -> Problems:
    """The reusable workflow's secrets: the documented set, each described and optional."""
    problems: Problems = []
    if set(secrets) != REUSABLE_SECRETS:
        problems.append(
            f"{path}: secrets are {sorted(secrets)}, expected {sorted(REUSABLE_SECRETS)}"
        )
    for name, spec in secrets.items():
        if not (spec or {}).get("description"):
            problems.append(f"{path}: secret {name!r} needs a description")
        if (spec or {}).get("required") is not False:
            problems.append(f"{path}: secret {name!r} must be `required: false`")
    return problems


def check_reusable_workflow() -> Problems:
    doc = load_yaml(REUSABLE_WORKFLOW)
    problems = preview_guard_problems(REUSABLE_WORKFLOW, doc, CLI_PUBLISHED)
    problems += platform_problems(REUSABLE_WORKFLOW, doc)
    secrets = reusable_secrets()
    problems += secret_problems(REUSABLE_WORKFLOW, secrets)
    inputs = reusable_inputs()
    if set(inputs) != REUSABLE_INPUTS:
        problems.append(
            f"{REUSABLE_WORKFLOW}: inputs are {sorted(inputs)}, expected {sorted(REUSABLE_INPUTS)}"
        )
    for name, spec in inputs.items():
        if not (spec or {}).get("description"):
            problems.append(f"{REUSABLE_WORKFLOW}: input {name!r} needs a description")
        if (spec or {}).get("type") != "string":
            problems.append(f"{REUSABLE_WORKFLOW}: input {name!r} must be type string")
    for doc_path in (Path("README.md"), REUSABLE_SPEC):
        full = ROOT / doc_path
        if not full.is_file():
            continue
        text = full.read_text(encoding="utf-8")
        for name in inputs:
            if f"`{name}`" not in text:
                problems.append(f"{doc_path}: does not document input `{name}`")
        for name in secrets:
            if f"`{name}`" not in text:
                problems.append(f"{doc_path}: does not document secret `{name}`")
        problems += platform_doc_problems(doc_path, text)
    return problems


def check_workflow_templates() -> Problems:
    problems: Problems = []
    templates_dir = ROOT / "workflow-templates"
    workflows = {p.name.removesuffix(".yml") for p in templates_dir.glob("*.yml")}
    properties = {
        p.name.removesuffix(".properties.json") for p in templates_dir.glob("*.properties.json")
    }
    for name in sorted(workflows - properties):
        problems.append(f"workflow-templates/{name}.yml: missing {name}.properties.json")
    for name in sorted(properties - workflows):
        problems.append(f"workflow-templates/{name}.properties.json: missing {name}.yml")
    inputs = set(reusable_inputs())
    for name in sorted(workflows & properties):
        props_path = f"workflow-templates/{name}.properties.json"
        props = json.loads((templates_dir / f"{name}.properties.json").read_text(encoding="utf-8"))
        for key in ("name", "description"):
            if not isinstance(props.get(key), str) or not props[key].strip():
                problems.append(f"{props_path}: missing {key}")
        categories = props.get("categories")
        if not isinstance(categories, list) or not categories:
            problems.append(f"{props_path}: categories must be a non-empty list")
        icon = props.get("iconName")
        if (
            icon
            and not icon.startswith("octicon ")
            and not (templates_dir / f"{icon}.svg").is_file()
        ):
            problems.append(f"{props_path}: iconName {icon!r} has no {icon}.svg")
        for pattern in props.get("filePatterns") or []:
            try:
                re.compile(pattern)
            except re.error as exc:
                problems.append(f"{props_path}: bad filePatterns entry {pattern!r}: {exc}")
        problems += check_template_calls(
            Path(f"workflow-templates/{name}.yml"), inputs, set(reusable_secrets())
        )
    return problems


def check_template_calls(path: Path, inputs: set[str], secrets: set[str] | None = None) -> Problems:
    problems: Problems = []
    doc = load_yaml(path)
    for job_id, job in (doc.get("jobs") or {}).items():
        uses = job.get("uses")
        if not uses:
            continue
        match = REMOTE_REUSABLE.match(uses)
        if not match:
            continue
        if not (ROOT / match.group(1)).is_file():
            problems.append(f"{path}: job {job_id} calls {uses}, which does not exist here")
            continue
        if Path(match.group(1)) == REUSABLE_WORKFLOW:
            unknown = set(job.get("with") or {}) - inputs
            if unknown:
                problems.append(f"{path}: job {job_id} passes unknown inputs {sorted(unknown)}")
            passed = job.get("secrets")
            if isinstance(passed, dict):
                unknown_secrets = set(passed) - (secrets or set())
                if unknown_secrets:
                    problems.append(
                        f"{path}: job {job_id} passes unknown secrets {sorted(unknown_secrets)}"
                    )
    return problems


def profile_image_problems(path: Path, text: str, size_of: Callable[[str], int | None]) -> Problems:
    """Every image has alt text and is a file of this repository, at most 1 MB."""
    problems: Problems = []
    for number, line in enumerate(text.split("\n"), start=1):
        images = [
            (attrs.get("src", ""), attrs.get("alt", ""))
            for attrs in (dict(HTML_ATTR.findall(tag)) for tag in HTML_IMG.findall(line))
        ]
        images += [(src, alt) for alt, src in MARKDOWN_IMG.findall(line)]
        for src, alt in images:
            if not alt.strip():
                problems.append(f"{path}:{number}: image needs alt text")
            if not src.startswith(PROFILE_IMAGE_PREFIX):
                problems.append(f"{path}:{number}: image must load from {PROFILE_IMAGE_PREFIX}")
                continue
            size = size_of(src.removeprefix(PROFILE_IMAGE_PREFIX))
            if size is None:
                problems.append(f"{path}:{number}: image {src} is not in this repository")
            elif size > PROFILE_IMAGE_MAX_BYTES:
                problems.append(f"{path}:{number}: image is over {PROFILE_IMAGE_MAX_BYTES} bytes")
    return problems


def check_profile_images() -> Problems:
    def size_of(name: str) -> int | None:
        file = ROOT / name
        return file.stat().st_size if file.is_file() else None

    readme = ROOT / PROFILE_README
    if not readme.is_file():
        return []
    return profile_image_problems(PROFILE_README, readme.read_text(encoding="utf-8"), size_of)


def check_public_hygiene() -> Problems:
    problems: Problems = []
    for path in text_files():
        text = (ROOT / path).read_text(encoding="utf-8")
        for number, line in enumerate(text.split("\n"), start=1):
            for owner in GITHUB_URL.findall(line):
                if owner != "emolysis":
                    problems.append(f"{path}:{number}: links outside github.com/emolysis")
            if EMAIL.search(line):
                problems.append(f"{path}:{number}: email address in a public repository")
    return problems


TESTS: list[Callable[[], Problems]] = [
    check_required_files,
    check_issue_forms,
    check_workflows,
    check_ci_gate,
    check_reusable_workflow,
    check_workflow_templates,
    check_profile_images,
    check_public_hygiene,
]


def cmd_test() -> Problems:
    problems: Problems = []
    for test in TESTS:
        problems += test()
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["fmt", "lint", "test"])
    args = parser.parse_args(argv)
    commands = {"fmt": cmd_fmt, "lint": cmd_lint, "test": cmd_test}
    problems = commands[args.command]()
    for problem in problems:
        print(problem)
    if problems:
        print(f"{args.command}: {len(problems)} problem(s)", file=sys.stderr)
        return 1
    print(f"{args.command}: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
