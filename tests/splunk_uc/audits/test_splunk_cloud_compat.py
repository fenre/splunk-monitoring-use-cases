"""Tests for ``splunk_uc.audits.splunk_cloud_compat``.

The audit surfaces SPL and pack-level patterns known to fail
``splunk-appinspect --mode=pre-cert`` or Splunk Cloud vetting. Before
this file the module ran at 22.0 % coverage from incidental imports
only — every SPL rule, every pack rule, ``render_report``, and the
``main`` CLI surface were untested.

This file walks a representative cross-section of the rule catalogue
end-to-end against a hermetic ``tmp_path`` corpus of ``catalog.json``
plus a fake ``ta/`` tree, asserts severity tallies surface
correctly, and exercises every documented exit-code branch.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from splunk_uc.audits import splunk_cloud_compat as audit


# --------------------------------------------------------------------- #
# rule-catalog sanity
# --------------------------------------------------------------------- #


def test_spl_rules_have_unique_ids() -> None:
    ids = [r.id for r in audit.SPL_RULES]
    assert len(set(ids)) == len(ids), f"duplicate SPL rule ids: {ids}"


def test_pack_rules_have_unique_ids() -> None:
    ids = [r.id for r in audit.PACK_RULES]
    assert len(set(ids)) == len(ids), f"duplicate PACK rule ids: {ids}"


def test_spl_rule_severities_are_known() -> None:
    for r in audit.SPL_RULES:
        assert r.severity in {"fail", "warn", "info"}, r


def test_pack_rule_severities_are_known() -> None:
    for r in audit.PACK_RULES:
        assert r.severity in {"fail", "warn"}, r


@pytest.mark.parametrize(
    "rule_id,sample_spl,should_match",
    [
        ("CLOUD-SPL-001", "search foo | runshellscript x", True),
        ("CLOUD-SPL-001", "search foo | rest x", False),
        ("CLOUD-SPL-002", "search foo | script bar", True),
        ("CLOUD-SPL-003", "search foo | crawl /etc", True),
        ("CLOUD-SPL-004", "search foo | dbxquery x", True),
        ("CLOUD-SPL-005", "search foo | sendemail x", True),
        ("CLOUD-SPL-006", "search foo | rest http://x", True),
        ("CLOUD-SPL-006", "search foo | rest /services/x", False),
        ("CLOUD-SPL-007", "search foo | collect index=summary", True),
        ("CLOUD-SPL-008", "search foo | loadjob 1234", True),
        ("CLOUD-SPL-009", "search foo | map search='bar'", True),
        (
            "CLOUD-SPL-009",
            "search foo | map maxsearches=10 search='bar'",
            False,
        ),
        ("CLOUD-SPL-010", "search foo | multisearch", True),
        ("CLOUD-SPL-011", "search foo | outputcsv ../escape.csv", True),
        ("CLOUD-SPL-011", "search foo | outputcsv safe.csv", False),
    ],
)
def test_spl_rule_patterns_match_documented_examples(
    rule_id: str, sample_spl: str, should_match: bool
) -> None:
    rule = next(r for r in audit.SPL_RULES if r.id == rule_id)
    hits = list(rule.pattern.finditer(sample_spl))
    if should_match:
        assert hits, f"{rule_id} did not match: {sample_spl!r}"
    else:
        assert not hits, f"{rule_id} false-positive on: {sample_spl!r}"


# --------------------------------------------------------------------- #
# hermetic catalog + pack fixture
# --------------------------------------------------------------------- #


@pytest.fixture
def hermetic_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> dict[str, Path]:
    """Point the audit at a hermetic catalogue + TA tree.

    Returns the rooted paths that tests need to seed.
    """

    repo = tmp_path
    dist = repo / "dist"
    docs = repo / "docs"
    test_results = repo / "test-results"
    ta = repo / "ta"
    apps = repo / "splunk-apps"
    for d in (dist, docs, test_results, ta, apps):
        d.mkdir(parents=True)

    monkeypatch.setattr(audit, "REPO_ROOT", repo)
    monkeypatch.setattr(audit, "CATALOG_PATH_PRIMARY", dist / "catalog.json")
    monkeypatch.setattr(audit, "CATALOG_PATH_LEGACY", repo / "catalog.json")
    monkeypatch.setattr(audit, "TA_DIR", ta)
    monkeypatch.setattr(audit, "APP_DIRS", (ta, apps))
    monkeypatch.setattr(audit, "DOC_OUT", docs / "splunk-cloud-compat.md")
    monkeypatch.setattr(
        audit, "JSON_OUT", test_results / "splunk-cloud-compat.json"
    )
    return {
        "repo": repo,
        "dist": dist,
        "ta": ta,
        "apps": apps,
        "docs": docs,
        "test_results": test_results,
    }


def _write_catalog(env: dict[str, Path], ucs: list[dict]) -> Path:
    """Write a minimal catalog.json with the given UC entries.

    Each UC dict needs keys ``i``, ``q``, ``qs`` (any may be omitted /
    blank).
    """

    payload = {
        "DATA": [
            {
                "s": [
                    {"u": ucs},
                ]
            }
        ]
    }
    path = env["dist"] / "catalog.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _write_conf(
    env: dict[str, Path], rel_path: str, body: str
) -> Path:
    p = env["repo"] / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


# --------------------------------------------------------------------- #
# _resolve_catalog_path
# --------------------------------------------------------------------- #


def test_resolve_catalog_prefers_primary(hermetic_env: dict[str, Path]) -> None:
    primary = hermetic_env["dist"] / "catalog.json"
    primary.write_text("{}", encoding="utf-8")
    legacy = hermetic_env["repo"] / "catalog.json"
    legacy.write_text("{}", encoding="utf-8")
    assert audit._resolve_catalog_path() == primary


def test_resolve_catalog_falls_back_to_legacy(
    hermetic_env: dict[str, Path],
) -> None:
    legacy = hermetic_env["repo"] / "catalog.json"
    legacy.write_text("{}", encoding="utf-8")
    assert audit._resolve_catalog_path() == legacy


def test_resolve_catalog_returns_none_when_neither_exists(
    hermetic_env: dict[str, Path],
) -> None:
    assert audit._resolve_catalog_path() is None


# --------------------------------------------------------------------- #
# audit_spl
# --------------------------------------------------------------------- #


def test_audit_spl_raises_when_catalog_missing(
    hermetic_env: dict[str, Path],
) -> None:
    with pytest.raises(FileNotFoundError):
        audit.audit_spl()


def test_audit_spl_returns_no_findings_for_clean_catalog(
    hermetic_env: dict[str, Path],
) -> None:
    _write_catalog(
        hermetic_env,
        ucs=[
            {"i": "1.1.1", "q": "index=os | stats count", "qs": ""},
            {"i": "1.1.2", "q": "search _internal | head 10", "qs": ""},
        ],
    )
    findings, total = audit.audit_spl()
    assert total == 2
    assert findings == []


def test_audit_spl_surfaces_fail_rule(
    hermetic_env: dict[str, Path],
) -> None:
    _write_catalog(
        hermetic_env,
        ucs=[
            {
                "i": "9.9.9",
                "q": "search foo | runshellscript bad.sh",
                "qs": "",
            }
        ],
    )
    findings, total = audit.audit_spl()
    assert total == 1
    assert len(findings) == 1
    assert findings[0].rule_id == "CLOUD-SPL-001"
    assert findings[0].severity == "fail"
    assert findings[0].location == "UC-9.9.9 (q)"
    assert "runshellscript" in findings[0].context.lower()


def test_audit_spl_scans_both_q_and_qs_fields(
    hermetic_env: dict[str, Path],
) -> None:
    _write_catalog(
        hermetic_env,
        ucs=[
            {
                "i": "1.1.1",
                "q": "| crawl /etc",
                "qs": "| dbxquery x",
            }
        ],
    )
    findings, _ = audit.audit_spl()
    locations = {f.location for f in findings}
    assert "UC-1.1.1 (q)" in locations
    assert "UC-1.1.1 (qs)" in locations


# --------------------------------------------------------------------- #
# audit_packs
# --------------------------------------------------------------------- #


def test_audit_packs_returns_empty_when_ta_dirs_missing(
    hermetic_env: dict[str, Path],
) -> None:
    """``APP_DIRS`` exist (fixture creates them) but contain no files."""

    assert audit.audit_packs() == []


def test_audit_packs_surfaces_custom_commands_conf(
    hermetic_env: dict[str, Path],
) -> None:
    _write_conf(
        hermetic_env,
        "ta/TA-foo/default/commands.conf",
        "[my_cmd]\nfilename = bar.py\n",
    )
    findings = audit.audit_packs()
    assert any(f.rule_id == "CLOUD-PACK-001" for f in findings)
    assert any("commands.conf" in f.location for f in findings)


def test_audit_packs_surfaces_restmap_and_web_exposes(
    hermetic_env: dict[str, Path],
) -> None:
    _write_conf(
        hermetic_env,
        "ta/TA-bar/default/restmap.conf",
        "[admin:hello]\nmatch = /hello\n",
    )
    _write_conf(
        hermetic_env,
        "splunk-apps/A1/default/web.conf",
        "[expose:my_endpoint]\nmethods = GET\n",
    )
    findings = audit.audit_packs()
    ids = {f.rule_id for f in findings}
    assert "CLOUD-PACK-002" in ids
    assert "CLOUD-PACK-003" in ids


def test_audit_packs_surfaces_script_input_and_python2_directive(
    hermetic_env: dict[str, Path],
) -> None:
    _write_conf(
        hermetic_env,
        "ta/TA-x/default/inputs.conf",
        "[script:///opt/run.sh]\ninterval = 60\n",
    )
    _write_conf(
        hermetic_env,
        "ta/TA-x/default/commands.conf",
        "[foo]\nfilename = bar.py\npython.version = python2\n",
    )
    findings = audit.audit_packs()
    ids = {f.rule_id for f in findings}
    assert "CLOUD-PACK-004" in ids
    assert "CLOUD-PACK-007" in ids


def test_audit_packs_records_line_numbers_in_location(
    hermetic_env: dict[str, Path],
) -> None:
    _write_conf(
        hermetic_env,
        "ta/TA-x/default/commands.conf",
        "# leading comment\n# second comment\n[my_cmd]\nfilename = foo.py\n",
    )
    findings = audit.audit_packs()
    matching = [f for f in findings if "commands.conf" in f.location]
    assert matching
    # The first [stanza] is at line 3.
    assert any(":3" in f.location for f in matching)


def test_audit_packs_skips_missing_app_dir_entry(
    hermetic_env: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """``APP_DIRS`` may include directories that don't exist (e.g.
    when the host repo has no ``splunk-apps/`` tree); the audit must
    skip silently rather than crash (covers line 292 of
    ``splunk_cloud_compat.py``)."""

    monkeypatch.setattr(
        audit,
        "APP_DIRS",
        (hermetic_env["ta"], tmp_path / "does-not-exist"),
    )
    # We still want at least one real finding so the test verifies
    # the loop did execute against the existing dir.
    _write_conf(
        hermetic_env,
        "ta/TA-x/default/commands.conf",
        "[my_cmd]\nfilename = bar.py\n",
    )
    findings = audit.audit_packs()
    assert findings
    assert all("does-not-exist" not in f.location for f in findings)


def test_audit_packs_skips_glob_matches_that_are_directories(
    hermetic_env: dict[str, Path],
) -> None:
    """A glob may resolve to a directory (e.g. someone creates an
    ``inputs.conf/`` folder by mistake); the audit must skip the
    non-file path instead of trying to read it (covers line 296 of
    ``splunk_cloud_compat.py``)."""

    # commands.conf is the glob target; create a directory in that
    # slot to force ``path.is_file()`` to return False.
    bogus = hermetic_env["ta"] / "TA-trap" / "default" / "commands.conf"
    bogus.mkdir(parents=True)
    findings = audit.audit_packs()
    # No findings should reference the bogus directory.
    assert all("TA-trap" not in f.location for f in findings)


def test_audit_packs_swallows_read_text_failure(
    hermetic_env: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A file that exists but raises on ``read_text`` (e.g. a broken
    symlink, permission error, or filesystem corruption) must be
    skipped silently (covers lines 299-300 of
    ``splunk_cloud_compat.py``)."""

    _write_conf(
        hermetic_env,
        "ta/TA-x/default/commands.conf",
        "[my_cmd]\nfilename = bar.py\n",
    )

    from pathlib import Path as _PathClass

    real_read_text = _PathClass.read_text

    def _selective_raise(self: _PathClass, *a: object, **k: object) -> str:
        if self.name == "commands.conf":
            raise OSError("simulated read failure")
        return real_read_text(self, *a, **k)

    monkeypatch.setattr(_PathClass, "read_text", _selective_raise)
    # No exception should bubble; commands.conf is silently skipped.
    findings = audit.audit_packs()
    assert all("commands.conf" not in f.location for f in findings)


# --------------------------------------------------------------------- #
# render_report
# --------------------------------------------------------------------- #


def test_render_report_summary_includes_counts() -> None:
    spl = [
        audit.Finding(
            rule_id="CLOUD-SPL-001",
            severity="fail",
            location="UC-1.1.1 (q)",
            context="runshellscript",
            message="msg",
            remediation="rem",
        ),
        audit.Finding(
            rule_id="CLOUD-SPL-007",
            severity="info",
            location="UC-1.1.2 (q)",
            context="collect",
            message="msg",
            remediation="rem",
        ),
    ]
    pack = [
        audit.Finding(
            rule_id="CLOUD-PACK-001",
            severity="fail",
            location="ta/X/default/commands.conf:1",
            context="[x]",
            message="msg",
            remediation="rem",
        )
    ]
    out = audit.render_report(spl, pack, total_ucs=5)
    assert "UCs audited: **5**" in out
    assert "Pack findings" in out
    assert "Severity legend" in out
    assert "Rule catalog" in out


def test_render_report_handles_empty_inputs() -> None:
    out = audit.render_report([], [], total_ucs=0)
    assert "UCs audited: **0**" in out
    assert "_No pack-level findings — packs are Splunk Cloud clean._" in out
    assert "_No SPL-level findings._" in out


def test_render_report_truncates_spl_findings_above_50() -> None:
    spl = [
        audit.Finding(
            rule_id="CLOUD-SPL-007",
            severity="info",
            location=f"UC-1.{i:03d}.1 (q)",
            context="collect",
            message="msg",
            remediation="rem",
        )
        for i in range(60)
    ]
    out = audit.render_report(spl, [], total_ucs=60)
    assert "…and 10 more" in out


def test_render_report_escapes_pipe_in_context() -> None:
    """GitHub-flavoured-markdown tables require ``|`` escape inside
    backticks. The audit must turn raw ``|`` into ``&#124;``."""

    finding = audit.Finding(
        rule_id="CLOUD-PACK-001",
        severity="fail",
        location="ta/X/default/commands.conf:1",
        context="[a] | b | c",
        message="msg",
        remediation="rem",
    )
    out = audit.render_report([], [finding], total_ucs=1)
    assert "&#124;" in out
    # The raw '|' inside the context must be gone (after substitution).
    # We allow other '|' in the markdown table machinery itself.
    table_line = next(
        (line for line in out.splitlines() if "ta/X" in line), None
    )
    assert table_line is not None
    # Drop the markdown column separators by splitting on them
    cells = table_line.split("|")
    context_cell = cells[-2]  # second-to-last cell holds the context
    assert "|" not in context_cell.replace("`", "")


# --------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------- #


def test_main_returns_two_when_catalog_missing(
    hermetic_env: dict[str, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = audit.main([])
    err = capsys.readouterr().err
    assert rc == 2
    assert "catalog.json missing" in err


def test_main_returns_zero_for_clean_catalog_and_writes_outputs(
    hermetic_env: dict[str, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_catalog(
        hermetic_env,
        ucs=[{"i": "1.1.1", "q": "index=os | stats count"}],
    )
    rc = audit.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert audit.DOC_OUT.exists()
    assert audit.JSON_OUT.exists()
    assert "Findings: fail=0, warn=0, info=0" in out


def test_main_returns_one_when_fail_finding_present(
    hermetic_env: dict[str, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_catalog(
        hermetic_env,
        ucs=[{"i": "1.1.1", "q": "| runshellscript x"}],
    )
    rc = audit.main([])
    assert rc == 1


def test_main_strict_returns_one_on_warn_only(
    hermetic_env: dict[str, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_catalog(
        hermetic_env,
        ucs=[{"i": "1.1.1", "q": "| dbxquery foo"}],  # severity=warn
    )
    rc_default = audit.main([])
    capsys.readouterr()
    rc_strict = audit.main(["--strict"])
    assert rc_default == 0
    assert rc_strict == 1


def test_main_no_write_does_not_create_outputs(
    hermetic_env: dict[str, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_catalog(
        hermetic_env,
        ucs=[{"i": "1.1.1", "q": "index=os | stats count"}],
    )
    rc = audit.main(["--no-write"])
    assert rc == 0
    assert not audit.DOC_OUT.exists()
    assert not audit.JSON_OUT.exists()
