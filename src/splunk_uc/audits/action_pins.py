#!/usr/bin/env python3
"""Verify every pinned action SHA in .github/ matches its trailing # vX.Y.Z tag.

Repo-overhaul plan §P2.5 (2026-05-08): the security policy in
``SECURITY.md`` mandates that every third-party GitHub Action be
pinned to a 40-character commit SHA, *and* that the trailing
``# vX.Y.Z`` comment honestly reflect which release that SHA
corresponds to.

Why honesty in the comment matters
----------------------------------

A reviewer trusting the comment can skip re-resolving the SHA when
deciding whether a bump is desirable; a maintainer reading the diff
trusts the comment to spot regressions. If the comment lies — either
through copy-paste error, force-push to the upstream tag, or a
malicious typo'd SHA pointing at a backdoored fork — the trust chain
breaks silently.

This script is the cheap, deterministic gate that surfaces such drift.
It is invoked from ``validate.yml`` on every PR and on a weekly cron;
local maintainers can run it via ``make audit-action-pins``.

Scope
-----

The audit walks both:

1. ``.github/workflows/*.yml`` — the actual workflow files.
2. ``.github/actions/*/action.yml`` — local composite actions that
   centralise repeated ``uses:`` patterns (e.g. ``setup-python``,
   ``setup-node``). When repo-overhaul plan §P2 moved 11 setup-python
   pin sites and 1 setup-node pin site into composite actions, the
   SHAs needed to remain in scope of this audit; otherwise a SHA
   bumped in the composite action would skip verification entirely.

References to local composite actions themselves
(``./.github/actions/...``) are excluded from the audit — they are
not third-party SHAs and have no upstream tag to verify against.

Behaviour
---------

For each ``uses: <action>@<sha> # <tag>`` directive across every
in-scope file (above), the script:

1. Hits ``GET /repos/{owner}/{repo}/git/ref/tags/<tag>`` to resolve
   the upstream tag's commit SHA.
2. For annotated tags, follows the indirection through
   ``/git/tags/<sha>`` to the underlying commit SHA.
3. Compares the resolved SHA against the locally pinned SHA.

Mismatches are reported with the upstream SHA so the maintainer can
decide: update the comment (the SHA is fine, just the label drifted),
or update the SHA (the upstream tag legitimately moved and we want
the new commit). Either remediation is a one-line edit.

Exit codes
----------

* ``0`` — every pinned SHA verifiably matches its claimed tag, OR every
  failure was a transient API error (rate limit, network) so the audit
  could not make a definitive determination. Emits a warning in the
  latter case so the maintainer notices.
* ``1`` — at least one pinned SHA *demonstrably* differs from the
  upstream tag's commit SHA. Real drift; must be fixed.
* ``2`` — usage error (no workflows found, malformed argv, etc.).

Authentication
--------------

Runs unauthenticated by default — sufficient for ~17 calls under the
60-req/h public quota. CI runs pass ``GITHUB_TOKEN`` via the standard
``GITHUB_TOKEN`` env var to lift the cap to 5,000 req/h. No other
secrets are required. When unauthenticated *and* rate-limited, the
script degrades to a warn-and-skip rather than failing the build.

Stdlib-only per ADR-0004; depends only on ``urllib.request`` + ``re``.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

# A 40-char hex string is the only acceptable pin for a third-party action.
_SHA_RE = re.compile(r"[a-f0-9]{40}")

# Match `uses: <action>@<sha> # <tag>` with leading whitespace and an
# optional list-item dash. The trailing comment is required so we can
# verify it.
_USES_RE = re.compile(
    r"^\s*-?\s*uses:\s*(?P<action>\S+?)@(?P<sha>[a-f0-9]{40})\s.*?#\s*(?P<tag>\S+)"
)

GITHUB_API = "https://api.github.com"


def _iter_pin_sources(github_dir: Path) -> list[Path]:
    """Return every YAML file that may carry a pinned ``uses:`` directive.

    Includes both workflow files (``.github/workflows/*.yml``) and
    composite-action definitions (``.github/actions/*/action.yml``).
    See module docstring for rationale.
    """
    sources: list[Path] = []
    workflow_dir = github_dir / "workflows"
    if workflow_dir.is_dir():
        sources.extend(sorted(workflow_dir.glob("*.yml")))
    actions_dir = github_dir / "actions"
    if actions_dir.is_dir():
        sources.extend(sorted(actions_dir.glob("*/action.yml")))
    return sources


def collect_pins(
    github_dir_or_workflow_dir: Path,
) -> dict[tuple[str, str, str], list[tuple[Path, int]]]:
    """Walk in-scope YAML and collect ``(action, tag, sha) -> [(file, lineno)]``.

    Accepts either ``.github/`` (preferred — covers workflows + composite
    actions) or ``.github/workflows/`` (legacy callers). The latter is
    detected by checking for the parent directory's name.
    """
    if github_dir_or_workflow_dir.name == "workflows":
        github_dir = github_dir_or_workflow_dir.parent
    else:
        github_dir = github_dir_or_workflow_dir

    pins: dict[tuple[str, str, str], list[tuple[Path, int]]] = {}
    for source in _iter_pin_sources(github_dir):
        for lineno, line in enumerate(source.read_text().splitlines(), 1):
            m = _USES_RE.match(line)
            if not m:
                continue
            action, sha, tag = m["action"], m["sha"], m["tag"]
            # Local composite actions (``./.github/actions/...``) are
            # out of scope — they are not third-party and have no
            # upstream tag. Match generically rather than the specific
            # ``./.github`` prefix in case future composite actions live
            # elsewhere.
            if action.startswith(("./", ".")):
                continue
            pins.setdefault((action, tag, sha), []).append((source, lineno))
    return pins


def to_owner_repo(action: str) -> str:
    """Resolve ``owner/repo/subpath/...`` to ``owner/repo``."""
    parts = action.split("/")
    if len(parts) < 2:
        raise ValueError(f"unparseable action {action!r}")
    return f"{parts[0]}/{parts[1]}"


class _TransientError(Exception):
    """Raised when the GitHub API call failed for a non-determinative reason.

    Distinguished from a definitive SHA mismatch so callers can treat
    rate limits and network blips as warn-and-skip rather than CI fail.
    """


def resolve_tag_sha(owner_repo: str, tag: str, headers: dict[str, str]) -> str:
    """Return the commit SHA the upstream ``<owner_repo>`` resolves ``<tag>`` to.

    Annotated tags require a second hop through ``/git/tags/<sha>`` to
    reach the underlying commit. Lightweight tags resolve directly.

    Raises :class:`_TransientError` on 403 (rate limit / abuse), 5xx, or
    network failure — callers must handle this distinctly from a real
    SHA mismatch.
    """
    url = f"{GITHUB_API}/repos/{owner_repo}/git/ref/tags/{tag}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as exc:
        # 403 = rate limit (often) or abuse-detection. 5xx = upstream
        # transient. 404 is a real authoring bug — the tag doesn't exist
        # so the comment is wrong. Treat 404 as a real mismatch.
        if exc.code == 404:
            raise ValueError(f"upstream tag {tag!r} does not exist on {owner_repo}") from exc
        if exc.code == 403 or 500 <= exc.code < 600:
            raise _TransientError(
                f"HTTP {exc.code} from {owner_repo}/{tag} (rate limit or upstream blip)"
            ) from exc
        raise
    except urllib.error.URLError as exc:
        # DNS / TCP / TLS failure — treat as transient.
        raise _TransientError(f"network error contacting {owner_repo}: {exc}") from exc

    obj = payload.get("object") or {}
    if obj.get("type") == "tag":
        tag_url = obj["url"]
        try:
            req2 = urllib.request.Request(tag_url, headers=headers)
            with urllib.request.urlopen(req2, timeout=15) as resp2:
                tag_payload = json.load(resp2)
        except urllib.error.HTTPError as exc:
            if exc.code == 403 or 500 <= exc.code < 600:
                raise _TransientError(
                    f"HTTP {exc.code} dereferencing annotated tag {tag} on {owner_repo}"
                ) from exc
            raise
        except urllib.error.URLError as exc:
            raise _TransientError(f"network error dereferencing tag: {exc}") from exc
        return str(tag_payload["object"]["sha"])
    return str(obj.get("sha", ""))


def main(argv: list[str] | None = None) -> int:
    # P6 (scripts taxonomy, 2026-05-09): the audit body now lives at
    # src/splunk_uc/audits/action_pins.py instead of scripts/audit_action_pins.py.
    # parents[3] resolves: action_pins.py -> audits/ -> splunk_uc/ -> src/ -> repo root.
    # The test suite's _StubPath fixture is updated alongside this change to
    # expose four parent levels matching the new on-disk depth.
    repo_root = Path(__file__).resolve().parents[3]
    github_dir = repo_root / ".github"
    if not github_dir.is_dir():
        print(f"error: {github_dir} is not a directory", file=sys.stderr)
        return 2

    pins = collect_pins(github_dir)
    if not pins:
        print("error: no pinned `uses:` directives found — nothing to verify.", file=sys.stderr)
        return 2

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "splunk-monitoring-use-cases-action-pin-audit",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    print(f"Verifying {len(pins)} (action, tag, sha) tuples against GitHub upstream...")
    mismatches: list[tuple[str, str, str, str, list[tuple[Path, int]]]] = []
    transient: list[tuple[str, str, str, str, list[tuple[Path, int]]]] = []
    verified = 0
    for (action, tag, pinned_sha), occurrences in sorted(pins.items()):
        owner_repo = to_owner_repo(action)
        try:
            actual_sha = resolve_tag_sha(owner_repo, tag, headers)
        except _TransientError as exc:
            transient.append((action, tag, pinned_sha, str(exc), occurrences))
            continue
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            mismatches.append((action, tag, pinned_sha, f"API error: {exc}", occurrences))
            continue
        except (KeyError, ValueError) as exc:  # malformed payload OR 404 (real drift)
            mismatches.append((action, tag, pinned_sha, str(exc), occurrences))
            continue

        if actual_sha != pinned_sha:
            mismatches.append(
                (
                    action,
                    tag,
                    pinned_sha,
                    f"upstream {tag} resolves to {actual_sha} not {pinned_sha}",
                    occurrences,
                )
            )
        else:
            verified += 1
            print(f"  OK  {action:55} {tag:10} {pinned_sha[:10]}")

    if mismatches:
        print()
        print(f"{len(mismatches)} MISMATCHES — pinned SHA disagrees with the # vX.Y.Z comment:")
        for action, tag, pinned_sha, reason, occurrences in mismatches:
            print(f"  {action}@{pinned_sha[:10]} (#{tag})")
            print(f"      {reason}")
            for wf, lineno in occurrences:
                print(f"      at {wf.relative_to(repo_root)}:{lineno}")
        print()
        print("Remediation: either update the SHA to match the upstream tag, or")
        print("fix the # vX.Y.Z comment to match the actual tag the SHA points at.")
        print("Run `python3 scripts/audit_action_pins.py` locally before re-pinning.")
        return 1

    if transient:
        # Soft warning — could not verify, but no real drift detected.
        # CI runs use a GITHUB_TOKEN so should hit this path only on
        # genuine outages.
        print()
        print(
            f"::warning::{len(transient)} pin(s) could not be verified due to "
            "transient API errors (rate limit or upstream blip). "
            f"Verified {verified}; suspect mismatches: 0."
        )
        for action, tag, pinned_sha, reason, _occurrences in transient:
            print(f"  SKIP {action}@{pinned_sha[:10]} (#{tag}) — {reason}")
        if verified == 0:
            print()
            print(
                "All pins skipped due to transient errors; not enough signal to "
                "claim 'verified'. Re-run with GITHUB_TOKEN set or wait for the "
                "rate-limit window to roll over (typically 60 minutes)."
            )
        return 0

    print(f"\nAll {len(pins)} pins verified — every SHA matches its claimed tag.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
