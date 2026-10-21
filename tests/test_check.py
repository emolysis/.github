"""Tests for scripts/check.py: each rule fails on a bad input and passes on the repository."""

from __future__ import annotations

import importlib.util
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_check() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check", ROOT / "scripts" / "check.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check = load_check()
P = Path("x.yml")


def doc(text: str) -> object:
    return yaml.safe_load(text)


# --- the repository itself ----------------------------------------------------------------


@pytest.mark.parametrize("test", check.TESTS, ids=lambda t: t.__name__)
def test_repository_passes(test: Callable[[], list[str]]) -> None:
    assert test() == []


def test_lint_passes() -> None:
    assert check.cmd_lint() == []


# --- CI reports as `gate` -----------------------------------------------------------------


CI = """
jobs:
  gate:
{name}    runs-on: ubuntu-latest
"""


@pytest.mark.parametrize("name", ["", "    name: gate\n"])
def test_ci_gate_ok(name: str) -> None:
    assert check.ci_gate_problems(P, doc(CI.format(name=name))) == []


@pytest.mark.parametrize("name", ["    name: task gate\n", "    name: CI\n"])
def test_ci_gate_renamed(name: str) -> None:
    [problem] = check.ci_gate_problems(P, doc(CI.format(name=name)))
    assert "reports as" in problem


def test_ci_gate_missing_job() -> None:
    [problem] = check.ci_gate_problems(P, doc("jobs:\n  build:\n    runs-on: ubuntu-latest\n"))
    assert "needs a job with id 'gate'" in problem


# --- the review runs once per pull request ------------------------------------------------


REVIEW = """
on:
  pull_request:
    types: [{types}]
"""


def test_review_trigger_ok() -> None:
    once = doc(REVIEW.format(types="opened, ready_for_review, labeled"))
    assert check.review_trigger_problems(P, once) == []


@pytest.mark.parametrize("types", ["opened, synchronize", "reopened", "opened, edited, labeled"])
def test_review_trigger_on_every_push(types: str) -> None:
    [problem] = check.review_trigger_problems(P, doc(REVIEW.format(types=types)))
    assert "every push" in problem


def test_review_trigger_default_types() -> None:
    [problem] = check.review_trigger_problems(P, doc("on:\n  pull_request:\n"))
    assert "explicit types" in problem
    [problem] = check.review_trigger_problems(P, doc("on:\n  pull_request:\n    types: []\n"))
    assert "synchronize" in problem


# --- labels that start automation stay off issue forms ------------------------------------


CLAUDE = """
jobs:
  claude:
    if: >-
      (github.event_name == 'issues' && github.event.label.name == 'agent') ||
      contains(github.event.comment.body, '@claude')
    steps:
      - uses: some/action@v1
        with:
          label_trigger: robot
      - run: echo hi
        if: github.event.label.name=='deploy'
"""


def test_trigger_labels() -> None:
    assert check.trigger_labels([doc(CLAUDE), doc("jobs: {}"), None]) == {
        "agent",
        "robot",
        "deploy",
    }


def test_repository_trigger_labels_include_agent() -> None:
    assert "agent" in check.trigger_labels(check.workflow_docs().values())


def test_form_with_trigger_label() -> None:
    problems = check.form_label_problems(P, ["agent"], {"agent", "bug"}, {"agent"})
    assert len(problems) == 1
    assert "starts a workflow" in problems[0]


def test_form_with_plain_and_unknown_labels() -> None:
    assert check.form_label_problems(P, ["bug"], {"agent", "bug"}, {"agent"}) == []
    [problem] = check.form_label_problems(P, ["nope"], {"bug"}, {"agent"})
    assert "not defined" in problem


def test_no_default_form_applies_agent() -> None:
    for path in (ROOT / ".github/ISSUE_TEMPLATE").glob("*.yml"):
        assert "agent" not in (doc(path.read_text(encoding="utf-8")) or {}).get("labels", [])


# --- reusable workflow: preview guard -----------------------------------------------------


GUARDED = """
env:
  EMOLYSIS_CHECKS_AVAILABLE: "{value}"
jobs:
  check:
    steps:
      - name: Preview guard
        if: {condition}
        run: |
          echo "::error::not yet"
          exit 1
      - run: emo check
"""
GUARD_IF = "env.EMOLYSIS_CHECKS_AVAILABLE != 'true'"


@pytest.mark.parametrize("condition", [GUARD_IF, "${{ env.EMOLYSIS_CHECKS_AVAILABLE!='true' }}"])
def test_preview_guard_ok(condition: str) -> None:
    text = GUARDED.format(value="false", condition=condition)
    assert check.preview_guard_problems(P, doc(text), published=False) == []


def test_preview_guard_switched_on_before_release() -> None:
    text = GUARDED.format(value="true", condition=GUARD_IF)
    [problem] = check.preview_guard_problems(P, doc(text), published=False)
    assert 'must be "false"' in problem
    assert check.preview_guard_problems(P, doc(text), published=True) == []


def test_preview_guard_missing_env() -> None:
    text = GUARDED.format(value="false", condition=GUARD_IF).replace(
        'EMOLYSIS_CHECKS_AVAILABLE: "false"', "OTHER: x"
    )
    [problem] = check.preview_guard_problems(P, doc(text), published=False)
    assert "must define" in problem


def test_preview_guard_not_first_step() -> None:
    text = """
env:
  EMOLYSIS_CHECKS_AVAILABLE: "false"
jobs:
  check:
    steps:
      - run: emo check
"""
    [problem] = check.preview_guard_problems(P, doc(text), published=False)
    assert "first step must be the preview guard" in problem


def test_preview_guard_that_does_not_fail() -> None:
    text = GUARDED.format(value="false", condition=GUARD_IF).replace("exit 1", "exit 0")
    [problem] = check.preview_guard_problems(P, doc(text), published=False)
    assert "first step must be the preview guard" in problem


def test_cli_not_published() -> None:
    # The CLI has no release yet; flip this together with the workflow env.
    assert check.CLI_PUBLISHED is False


# --- reusable workflow: accepted platforms ------------------------------------------------


VALIDATE = """
jobs:
  check:
    steps:
      - run: |
          case "$PLATFORM" in
            {arm}) ;;
            *) exit 1 ;;
          esac
"""


def test_platforms_match_spec() -> None:
    text = VALIDATE.format(arm='"" | databricks | snowflake | fabric')
    assert check.accepted_platforms(doc(text)) == {"", "databricks", "snowflake", "fabric"}
    assert check.platform_problems(P, doc(text)) == []


@pytest.mark.parametrize(
    "arm",
    [
        '"" | databricks | snowflake | fabric | duckdb',
        "databricks | snowflake | fabric",
        '"" | databricks | snowflake',
    ],
)
def test_platforms_drift(arm: str) -> None:
    [problem] = check.platform_problems(P, doc(VALIDATE.format(arm=arm)))
    assert "the spec allows" in problem


def test_platforms_not_validated() -> None:
    [problem] = check.platform_problems(P, doc("jobs:\n  check:\n    steps:\n      - run: x\n"))
    assert "no step validates platform" in problem


def test_platform_doc_row() -> None:
    good = "| `platform` | empty | `databricks`, `snowflake` or `fabric`. |\n"
    assert check.platform_doc_problems(P, good) == []
    [problem] = check.platform_doc_problems(P, good.replace("`fabric`", "fabric"))
    assert "`fabric`" in problem
    [problem] = check.platform_doc_problems(P, "no table here\n")
    assert "no table row" in problem


# --- profile images load from this repository ---------------------------------------------


BANNER = check.PROFILE_IMAGE_PREFIX + "profile/banner.png"


def sizes(name: str) -> int | None:
    return {"profile/banner.png": 200_000, "profile/huge.png": 2_000_000}.get(name)


@pytest.mark.parametrize(
    "line",
    [f'<img src="{BANNER}" alt="EMOLYSIS" width="100%">', f"![EMOLYSIS]({BANNER})", "no image"],
)
def test_profile_image_ok(line: str) -> None:
    assert check.profile_image_problems(P, line + "\n", sizes) == []


@pytest.mark.parametrize(
    ("line", "message"),
    [
        (f'<img src="{BANNER}">', "needs alt text"),
        (f"![ ]({BANNER})", "needs alt text"),
        ('<img src="banner.png" alt="x">', "must load from"),
        ('<img src="https://example.org/banner.png" alt="x">', "must load from"),
        (f'<img src="{check.PROFILE_IMAGE_PREFIX}profile/gone.png" alt="x">', "not in this"),
        (f'<img src="{check.PROFILE_IMAGE_PREFIX}profile/huge.png" alt="x">', "over 1000000"),
    ],
)
def test_profile_image_problem(line: str, message: str) -> None:
    [problem] = check.profile_image_problems(P, line + "\n", sizes)
    assert message in problem


# --- the reusable workflow's secrets -----------------------------------------------------


def test_secrets_ok() -> None:
    secrets = {"token": {"description": "A machine token.", "required": False}}
    assert check.secret_problems(P, secrets) == []


def test_secrets_drift() -> None:
    [problem] = check.secret_problems(P, {})
    assert "expected ['token']" in problem
    [problem] = check.secret_problems(
        P,
        {
            "token": {"description": "x", "required": False},
            "other": {"description": "y", "required": False},
        },
    )
    assert "expected ['token']" in problem


def test_secret_needs_description_and_optional() -> None:
    problems = check.secret_problems(P, {"token": {"required": True}})
    assert any("needs a description" in p for p in problems)
    assert any("required: false" in p for p in problems)


def test_template_passes_unknown_secret(tmp_path: Path) -> None:
    path = tmp_path / "t.yml"
    path.write_text(
        "on: push\njobs:\n  emolysis:\n    uses: emolysis/.github/.github/workflows/"
        "emolysis-checks.yml@main\n    with:\n      path: .\n    secrets:\n"
        "      token: x\n      other: y\n",
        encoding="utf-8",
    )
    problems = check.check_template_calls(path, {"path"}, {"token"})
    assert any("unknown secrets ['other']" in p for p in problems)
    assert check.check_template_calls(path, {"path"}, {"token", "other"}) == []
