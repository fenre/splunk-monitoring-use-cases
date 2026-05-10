"""Unit tests for ``src/splunk_uc/audits/placeholders.py``.

The placeholder audit is a content-quality gate that flags TBD/FIXME
markers, bracketed ``<YOUR_...>`` placeholders, ``example.com`` docs
URLs, and templated stub titles like ``"control theme N"`` inside the
JSON SSOT.

Two regressions guard rails are pinned here:

1. **False-positive fixes** — earlier revisions of the audit matched
   ``XX:XXXX`` IPv6 multicast notation and ``CHG-XXXX`` ticket
   placeholders as ``literal-tbd`` findings, which is wrong; both are
   real operational notation. The tightened regex must not match
   these patterns. Conversely, a bare ``TBD`` token in prose must
   still be caught.

2. **Baseline filtering** — the audit ships with a JSON baseline of
   accepted (tracked) findings under
   ``data/audits/placeholders-baseline.json``. The audit must
   subtract these from the surfaced findings before the ``--check``
   severity gate runs, so CI fails only on NEW findings (regressions)
   while the long-tail content debt stays visible in reports.

The tests work directly against the module's helper functions and the
in-process ``main()`` entry point — no subprocess overhead needed.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
from pathlib import Path

import pytest

from splunk_uc.audits import placeholders as audit


def test_literal_tbd_regex_rejects_ipv6_multicast() -> None:
    """``ff02::1:ffXX:XXXX`` is real IPv6 notation, not a placeholder.

    Earlier revisions of the audit matched any ``\\bXXX+\\b`` token,
    which fired on Solicited-Node multicast addresses and EUI-64
    patterns inside cat-5 IPv6 use cases. The tightened regex uses
    negative look-around to require non-alphanumeric / non-``: # -``
    surroundings, so address fragments no longer trip the gate.
    """
    samples = [
        "ff02::1:ffXX:XXXX should not match",
        "EUI-64 pattern ::ffXX:XXXX:XXXX is documented",
        "joined ff02::1:ffXX:XXXX from solicited-node multicast",
    ]
    for s in samples:
        assert audit._LITERAL_TBD.search(s) is None, (
            f"audit literal-tbd regex incorrectly matched IPv6 sample: {s!r}"
        )


def test_literal_tbd_regex_rejects_ticket_placeholders() -> None:
    """``CHG-XXXX`` and ``#XXX`` are change-management ticket templates.

    These are the conventional way to refer to "the change ticket the
    operator should fill in" in implementation runbooks. They are
    documented placeholders, not unfinished content, and must not
    fire the audit.
    """
    samples = [
        "annotate as 'expected — CHG-XXXX.' No further action.",
        "approved emergency, ticket #XXX.",
        "raise CHG-XXXX in ServiceNow",
    ]
    for s in samples:
        assert audit._LITERAL_TBD.search(s) is None, (
            f"audit literal-tbd regex incorrectly matched ticket sample: {s!r}"
        )


def test_literal_tbd_regex_still_catches_real_placeholders() -> None:
    """The tightened regex must still flag real ``TBD`` / ``FIXME``."""
    samples = [
        "value: TBD",
        "Status: FIXME",
        "field XXX needs population",
        '"IPv6 management transport readiness","TBD",fail,2026-05-01',
    ]
    for s in samples:
        m = audit._LITERAL_TBD.search(s)
        assert m is not None, f"regex missed real placeholder in: {s!r}"
        assert re.match(r"TBD|FIXME|XXX+", m.group(0))


def test_baseline_load_missing_file_returns_empty(tmp_path: Path) -> None:
    """Missing baseline file must not raise; treat as no suppressions."""
    missing = tmp_path / "does-not-exist.json"
    assert audit._load_baseline(missing) == set()


def test_baseline_load_parses_entries(tmp_path: Path) -> None:
    """A well-formed baseline parses into ``(uc_id, file, category)`` triples."""
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps(
            {
                "schema": "placeholders-baseline.v1",
                "entries": [
                    {
                        "uc_id": "UC-22.17.1",
                        "file": "UC-22.17.1.json",
                        "category": "control-theme-n",
                    },
                    {
                        "uc_id": "UC-1.1.1",
                        "file": "UC-1.1.1.json",
                        "category": "angle-placeholder",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    triples = audit._load_baseline(baseline)
    assert (
        "UC-22.17.1",
        "UC-22.17.1.json",
        "control-theme-n",
    ) in triples
    assert ("UC-1.1.1", "UC-1.1.1.json", "angle-placeholder") in triples
    assert len(triples) == 2


def test_baseline_load_tolerates_garbage(tmp_path: Path) -> None:
    """Malformed baseline JSON degrades to empty (with warning), not crash."""
    bad = tmp_path / "bad.json"
    bad.write_text("not valid json {", encoding="utf-8")
    assert audit._load_baseline(bad) == set()


def test_check_passes_against_committed_baseline() -> None:
    """The shipped baseline must absorb every current HIGH finding.

    This is the structural CI guard: as long as no NEW HIGH-severity
    placeholder findings are introduced, ``audit-placeholders --check``
    must exit 0. Drift here means either the baseline is stale or a
    new UC has been added with placeholder content; both should fail
    PR review and prompt a baseline refresh / content fix.
    """
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
        rc = audit.main(["--check"])
    assert rc == 0, (
        "placeholder audit failed against the shipped baseline. "
        "Either the baseline is stale (refresh with "
        "`PYTHONPATH=src python3 -m splunk_uc audit-placeholders "
        "--write-baseline --no-baseline`) or a new HIGH-severity "
        "placeholder finding has been introduced.\n"
        f"\n--- stdout ---\n{buf_out.getvalue()}\n"
        f"--- stderr ---\n{buf_err.getvalue()}"
    )


def test_no_baseline_flag_surfaces_everything() -> None:
    """``--no-baseline`` must skip baseline filtering and surface all findings.

    This is the cleanup / refresh path — running without the baseline
    shows the full debt list so reviewers can pick UCs to repair.
    """
    buf_out = io.StringIO()
    with contextlib.redirect_stdout(buf_out):
        rc = audit.main(["--no-baseline"])
    assert rc == 0
    out = buf_out.getvalue()
    assert "Baseline: disabled (--no-baseline)" in out
    # The unfiltered audit MUST still find the long-tail control-theme-n
    # debt; if this regresses to zero something is wrong with the walker.
    assert "control-theme-n" in out


def test_no_baseline_with_check_fails_on_committed_debt() -> None:
    """``--no-baseline --check`` must surface the existing debt as failures.

    Confirms the baseline is genuinely doing the work — without it the
    audit hard-fails on the same content the baseline-filtered run
    accepts. This pins the contract for reviewers reading the PR.
    """
    buf_out = io.StringIO()
    with contextlib.redirect_stdout(buf_out):
        rc = audit.main(["--no-baseline", "--check"])
    assert rc == 1, (
        "audit-placeholders --no-baseline --check is expected to FAIL "
        "(non-zero) because the JSON SSOT carries 200+ tracked debt "
        "findings the baseline normally absorbs. If this passes, the "
        "regex tightening over-relaxed and now misses real placeholders."
    )


def test_default_baseline_path_resolves() -> None:
    """The default baseline path must point at the shipped JSON file."""
    assert audit.DEFAULT_BASELINE.exists(), (
        f"shipped placeholders baseline missing at {audit.DEFAULT_BASELINE} "
        "— refresh with `PYTHONPATH=src python3 -m splunk_uc "
        "audit-placeholders --write-baseline --no-baseline`"
    )
    data = json.loads(audit.DEFAULT_BASELINE.read_text(encoding="utf-8"))
    assert data["schema"] == "placeholders-baseline.v1"
    assert isinstance(data["entries"], list)
    assert data["entry_count"] == len(data["entries"])
    assert data["entry_count"] > 0, "baseline file must contain at least one entry"


def test_write_baseline_round_trips(tmp_path: Path) -> None:
    """``--write-baseline`` snapshot is loadable by the same audit."""
    target = tmp_path / "audits" / "placeholders-baseline.json"
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
        rc = audit.main(
            [
                "--write-baseline",
                "--no-baseline",
                "--baseline",
                str(target),
            ]
        )
    assert rc == 0, buf_err.getvalue()
    assert target.exists()
    triples = audit._load_baseline(target)
    assert len(triples) > 0, "round-trip baseline must contain entries"


@pytest.mark.parametrize(
    "category, expected_severity",
    [
        ("literal-tbd", "HIGH"),
        ("literal-todo", "HIGH"),
        ("calculated-value", "HIGH"),
        ("control-theme-n", "HIGH"),
        # angle-placeholder + example-com were demoted from HIGH to MED:
        # they are RFC 2606 / docs convention patterns that are legitimate
        # in implementation guides; we still surface them in reports but
        # don't fail CI by default.
        ("angle-placeholder", "MED"),
        ("example-com", "MED"),
    ],
)
def test_marker_severities_pinned(category: str, expected_severity: str) -> None:
    """Pin the severity assignment for each placeholder rule."""
    matches = [m for m in audit._MARKERS if m[0] == category]
    assert matches, f"marker {category!r} missing from _MARKERS table"
    assert matches[0][2] == expected_severity, (
        f"marker {category!r} severity changed from {expected_severity!r} "
        f"to {matches[0][2]!r}; update tests + baseline schema if intentional"
    )
