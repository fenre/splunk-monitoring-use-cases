#!/usr/bin/env python3
"""Subagent UC-firewall — block subagent-authored PRs from touching UC sidecars.

Lane B Task B-7 (Catalog Parallel Execution Atlas). CI runs this on every
pull request via ``validate.yml``; local maintainers can reproduce with
``--labels`` / ``paths`` flags.

Protected paths (v1)
--------------------

* ``content/cat-*/UC-*.json`` — handwritten catalogue sidecars

See ``docs/subagent-firewall.md`` and ``docs/parallel-execution-substrate.md`` §4.

Exit codes
----------

* ``0`` — gate passed (or no PR context to evaluate).
* ``1`` — ``subagent-authored`` label present and diff touches UC sidecar(s).
* ``2`` — misconfiguration (missing env, ``gh`` / ``git`` failure in CI mode).
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

SUBAGENT_AUTHORED_LABEL = "subagent-authored"

# TODO(F-13): Extend protection to handwritten entries in
# apps/web/src/data/starter-bundles.data.ts (__handwritten: true markers).
UC_SIDECAR_RE = re.compile(r"^content/cat-[^/]+/UC-[^/]+\.json$")


@dataclass(frozen=True)
class FirewallResult:
    passed: bool
    reason: str
    violating_paths: list[str]


def is_uc_sidecar_path(path: str) -> bool:
    """Return True when ``path`` is a UC JSON sidecar under ``content/cat-*/``."""
    return UC_SIDECAR_RE.match(path) is not None


def evaluate_firewall(labels: Iterable[str], changed_paths: Iterable[str]) -> FirewallResult:
    """Evaluate the subagent UC-firewall for a PR label set and changed paths."""
    label_set = {label.strip() for label in labels if label.strip()}
    if SUBAGENT_AUTHORED_LABEL not in label_set:
        return FirewallResult(
            passed=True,
            reason="no subagent-authored label — maintainer may edit UC sidecars",
            violating_paths=[],
        )

    violating = sorted(path for path in changed_paths if is_uc_sidecar_path(path))
    if violating:
        return FirewallResult(
            passed=False,
            reason=(
                f"subagent-authored PR touches {len(violating)} UC sidecar(s) "
                "— handwritten catalogue content is maintainer-only"
            ),
            violating_paths=violating,
        )

    return FirewallResult(
        passed=True,
        reason="subagent-authored PR with no UC sidecar changes",
        violating_paths=[],
    )


def _run_command(argv: list[str], *, label: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def _fetch_labels(repo: str, pr_number: str, token: str) -> list[str]:
    endpoint = f"repos/{repo}/pulls/{pr_number}"
    proc = _run_command(
        ["gh", "api", endpoint, "--jq", ".labels[].name"],
        label="gh api labels",
    )
    if proc.returncode != 0:
        stderr = proc.stderr.strip() or proc.stdout.strip() or "unknown gh error"
        raise RuntimeError(f"gh api failed for {endpoint}: {stderr}")
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _fetch_changed_paths() -> list[str]:
    proc = _run_command(
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        label="git diff",
    )
    if proc.returncode != 0:
        stderr = proc.stderr.strip() or proc.stdout.strip() or "unknown git error"
        raise RuntimeError(f"git diff origin/main...HEAD failed: {stderr}")
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _resolve_inputs(
    *,
    check: bool,
    cli_labels: list[str] | None,
    cli_paths: list[str] | None,
    pr_number: str | None,
) -> tuple[list[str], list[str]]:
    """Resolve labels and changed paths from CLI flags or CI environment."""
    labels = cli_labels
    paths = cli_paths

    env_pr = os.environ.get("GITHUB_EVENT_PULL_REQUEST_NUMBER", "").strip() or None
    env_repo = os.environ.get("GITHUB_REPOSITORY", "").strip() or None
    env_token = os.environ.get("GH_TOKEN", "").strip() or None
    effective_pr = pr_number or env_pr

    need_ci = check and (labels is None or paths is None)
    if not need_ci:
        return labels or [], paths or []

    if not effective_pr and not env_repo and not env_token:
        return [], []

    if labels is None:
        if not (effective_pr and env_repo and env_token):
            missing = [
                name
                for name, value in (
                    ("GITHUB_EVENT_PULL_REQUEST_NUMBER or --pr-number", effective_pr),
                    ("GITHUB_REPOSITORY", env_repo),
                    ("GH_TOKEN", env_token),
                )
                if not value
            ]
            raise RuntimeError(
                "CI mode requires PR context to fetch labels: missing "
                + ", ".join(missing)
            )
        labels = _fetch_labels(env_repo, effective_pr, env_token)

    if paths is None:
        paths = _fetch_changed_paths()

    return labels, paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Subagent UC-firewall: fail closed when a PR labelled "
            f"{SUBAGENT_AUTHORED_LABEL!r} touches content/cat-*/UC-*.json."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="CI mode: resolve labels/paths from GitHub + git when not passed explicitly.",
    )
    parser.add_argument(
        "--pr-number",
        metavar="N",
        help="Pull request number (fallback when GITHUB_EVENT_PULL_REQUEST_NUMBER is unset).",
    )
    parser.add_argument(
        "--labels",
        action="append",
        default=None,
        metavar="NAME",
        help="PR label (repeatable; bypasses gh api when provided).",
    )
    parser.add_argument(
        "--paths",
        action="append",
        default=None,
        metavar="PATH",
        help="Changed file path (repeatable; bypasses git diff when provided).",
    )
    args = parser.parse_args(argv)

    try:
        labels, paths = _resolve_inputs(
            check=args.check,
            cli_labels=args.labels,
            cli_paths=args.paths,
            pr_number=args.pr_number,
        )
    except RuntimeError as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        return 2

    if args.check and not labels and not paths and not args.labels and not args.paths:
        print("Subagent UC-firewall: no PR context — skipping check (PASS).")
        return 0

    result = evaluate_firewall(labels, paths)

    if result.passed:
        print(f"Subagent UC-firewall PASS — {result.reason}.")
        return 0

    sys.stderr.write(f"Subagent UC-firewall FAIL — {result.reason}.\n")
    for path in result.violating_paths:
        sys.stderr.write(f"  - {path}\n")
    sys.stderr.write(
        "Remove UC sidecar changes from this PR or drop the subagent-authored label.\n"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
