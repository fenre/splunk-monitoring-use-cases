"""Unit tests for ``splunk_uc.audits.spl_duplicates``.

P16 wave II: lifts ``src/splunk_uc/audits/spl_duplicates.py`` from
~18% to 100% combined coverage. Pins every documented contract of
the SPL duplicate-detection audit:

(a) ``_canonical_spl`` collapses whitespace, masks macro arguments,
    and lowercases the result so semantically equivalent SPLs hash
    to the same digest.
(b) ``_collect`` walks the SSOT, skipping UCs without a ``spl``
    field or with whitespace-only SPL, and groups by 12-char SHA-256
    digest of the canonical SPL.
(c) ``main`` prints a deterministic informational summary; the
    cluster table is sorted by size descending then by digest, and
    truncates at 30 clusters with a ``... and N more`` footer, and
    each cluster lists at most 5 UCs with its own truncation footer.
    The audit always exits 0 — never a release gate.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Any, Protocol

import pytest

from splunk_uc.audits import _uc_walk
from splunk_uc.audits import spl_duplicates as sd


class MakeUC(Protocol):
    def __call__(
        self,
        uc_id: str,
        payload: dict[str, Any] | None = None,
        category: int = 1,
    ) -> pathlib.Path: ...


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Hermetic repo with content/ skeleton — patch the upstream
    ``_uc_walk.CONTENT`` since ``iter_uc_sidecars`` closes over it.
    """
    (tmp_path / "content").mkdir()
    monkeypatch.setattr(_uc_walk, "REPO", tmp_path)
    monkeypatch.setattr(_uc_walk, "CONTENT", tmp_path / "content")
    return tmp_path


@pytest.fixture
def make_uc(fake_repo: pathlib.Path) -> MakeUC:
    def _make(
        uc_id: str,
        payload: dict[str, Any] | None = None,
        category: int = 1,
    ) -> pathlib.Path:
        cat_dir = fake_repo / "content" / f"cat-{category:02d}-test-cat"
        cat_dir.mkdir(parents=True, exist_ok=True)
        sidecar = cat_dir / f"UC-{uc_id}.json"
        merged = {"id": uc_id, **(payload or {})}
        sidecar.write_text(json.dumps(merged), encoding="utf-8")
        return sidecar

    return _make


# ----------------------------------------------------------------------
# Module constants
# ----------------------------------------------------------------------


class TestModuleConstants:
    def test_re_ws_collapses_whitespace(self) -> None:
        assert sd.RE_WS.sub(" ", "a    b\nc\td") == "a b c d"

    def test_re_macro_args_matches_macro_call(self) -> None:
        m = sd.RE_MACRO_ARGS.search("`my_macro(foo,bar)`")
        assert m is not None
        assert m.group(1) == "my_macro"

    def test_re_macro_args_rejects_uppercase(self) -> None:
        """The macro-name capture is lowercase-only by spec."""
        assert sd.RE_MACRO_ARGS.search("`MyMacro(foo)`") is None


# ----------------------------------------------------------------------
# _canonical_spl
# ----------------------------------------------------------------------


class TestCanonicalSpl:
    def test_empty_string(self) -> None:
        assert sd._canonical_spl("") == ""

    def test_whitespace_only_collapses_to_empty(self) -> None:
        assert sd._canonical_spl("  \t\n  ") == ""

    def test_collapses_multiple_spaces(self) -> None:
        assert sd._canonical_spl("index=main    sourcetype=foo") == ("index=main sourcetype=foo")

    def test_collapses_newlines_and_tabs(self) -> None:
        assert sd._canonical_spl("index=main\n\tsourcetype=foo") == ("index=main sourcetype=foo")

    def test_lowercases_keywords(self) -> None:
        assert sd._canonical_spl("INDEX=MAIN | STATS COUNT") == "index=main | stats count"

    def test_masks_macro_arguments(self) -> None:
        """``foo(bar,baz)`` collapses to ``foo(..)``."""
        result = sd._canonical_spl("`my_macro(arg1,arg2)`")
        assert result == "`my_macro(..)`"

    def test_masks_multiple_macros(self) -> None:
        result = sd._canonical_spl("`a(x)` | `b(y,z)`")
        assert result == "`a(..)` | `b(..)`"

    def test_macro_mask_does_not_affect_non_macros(self) -> None:
        """The mask regex requires backticks plus lowercase macro
        identifier; unbacked function calls aren't masked."""
        result = sd._canonical_spl("eval x=foo(1,2)")
        # `foo(1,2)` without surrounding backticks is left alone.
        assert "foo(1,2)" in result

    def test_two_inputs_canonicalize_to_same_digest(self) -> None:
        """Whitespace, case, and macro-arg variations produce the
        same canonical hash."""
        a = sd._canonical_spl("index=main\n  | `my_macro(ENV)` | stats count BY host")
        b = sd._canonical_spl("INDEX=MAIN | `my_macro(prod)` | stats count by HOST")
        assert a == b


# ----------------------------------------------------------------------
# _collect
# ----------------------------------------------------------------------


class TestCollect:
    def test_empty_content_returns_empty(self, fake_repo: pathlib.Path) -> None:
        assert sd._collect() == {}

    def test_single_uc_clustered(self, make_uc: MakeUC) -> None:
        make_uc("1.1.1", {"title": "Foo", "spl": "search index=main"})
        clusters = sd._collect()
        assert len(clusters) == 1
        (members,) = clusters.values()
        assert len(members) == 1
        file_name, uc_id, title = members[0]
        assert file_name == "UC-1.1.1.json"
        assert uc_id == "UC-1.1.1"
        assert title == "Foo"

    def test_missing_spl_skipped(self, make_uc: MakeUC) -> None:
        make_uc("1.1.1", {"title": "No SPL"})
        assert sd._collect() == {}

    def test_non_string_spl_skipped(self, make_uc: MakeUC) -> None:
        make_uc("1.1.1", {"title": "Bad SPL", "spl": 42})
        assert sd._collect() == {}

    def test_empty_string_spl_skipped(self, make_uc: MakeUC) -> None:
        make_uc("1.1.1", {"title": "Empty", "spl": ""})
        assert sd._collect() == {}

    def test_whitespace_only_spl_skipped(self, make_uc: MakeUC) -> None:
        """Pure whitespace SPL is rejected via ``spl.strip()``."""
        make_uc("1.1.1", {"title": "Spaces", "spl": "   \t\n  "})
        assert sd._collect() == {}

    def test_missing_id_falls_back_to_unknown(self, fake_repo: pathlib.Path) -> None:
        cat = fake_repo / "content" / "cat-01-test"
        cat.mkdir(parents=True)
        sidecar = cat / "UC-1.1.1.json"
        sidecar.write_text(
            json.dumps({"title": "T", "spl": "search index=main"}),
            encoding="utf-8",
        )
        clusters = sd._collect()
        (members,) = clusters.values()
        _file, uc_id, _title = members[0]
        assert uc_id == "UC-<unknown>"

    def test_missing_title_falls_back_to_placeholder(self, make_uc: MakeUC) -> None:
        make_uc("1.1.1", {"spl": "search index=main"})
        clusters = sd._collect()
        (members,) = clusters.values()
        _file, _uc_id, title = members[0]
        assert title == "(no title)"

    def test_whitespace_only_title_falls_back(self, make_uc: MakeUC) -> None:
        """``str(title).strip() or '(no title)'`` covers blank strings."""
        make_uc("1.1.1", {"title": "   ", "spl": "search index=main"})
        clusters = sd._collect()
        (members,) = clusters.values()
        _, _, title = members[0]
        assert title == "(no title)"

    def test_two_identical_spls_cluster(self, make_uc: MakeUC) -> None:
        make_uc("1.1.1", {"title": "A", "spl": "search index=main"})
        make_uc("1.1.2", {"title": "B", "spl": "search index=main"})
        clusters = sd._collect()
        assert len(clusters) == 1
        (members,) = clusters.values()
        assert len(members) == 2
        # Order follows sidecar walk order (sorted by glob).
        assert {m[1] for m in members} == {"UC-1.1.1", "UC-1.1.2"}

    def test_two_distinct_spls_separate_clusters(self, make_uc: MakeUC) -> None:
        make_uc("1.1.1", {"title": "A", "spl": "search index=main"})
        make_uc("1.1.2", {"title": "B", "spl": "search index=other"})
        clusters = sd._collect()
        assert len(clusters) == 2

    def test_digest_is_truncated_sha256(self, make_uc: MakeUC) -> None:
        """The digest key is the first 12 hex chars of SHA-256."""
        spl = "search index=main"
        canonical = sd._canonical_spl(spl)
        expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
        make_uc("1.1.1", {"title": "T", "spl": spl})
        clusters = sd._collect()
        assert list(clusters.keys()) == [expected]


# ----------------------------------------------------------------------
# main()
# ----------------------------------------------------------------------


class TestMain:
    def test_empty_content_returns_zero(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = sd.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "SPL duplicate audit (informational)" in out
        assert "UCs with SPL:           0" in out
        assert "No duplicate SPL clusters found." in out

    def test_singleton_clusters_no_dup_output(
        self,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When every UC has a unique SPL, the duplicate cluster
        section is empty and the audit reports no duplicates."""
        make_uc("1.1.1", {"title": "A", "spl": "search index=a"})
        make_uc("1.1.2", {"title": "B", "spl": "search index=b"})
        rc = sd.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "UCs with SPL:           2" in out
        assert "UCs in a dup cluster:   0" in out
        assert "Distinct dup clusters:  0" in out
        assert "No duplicate SPL clusters found." in out

    def test_dup_cluster_reported(
        self,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        make_uc("1.1.1", {"title": "A", "spl": "search index=main"})
        make_uc("1.1.2", {"title": "B", "spl": "search index=main"})
        rc = sd.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "UCs with SPL:           2" in out
        assert "UCs in a dup cluster:   2" in out
        assert "Distinct dup clusters:  1" in out
        assert "Top clusters" in out
        assert "size=2" in out
        assert "UC-1.1.1" in out
        assert "UC-1.1.2" in out

    def test_cluster_member_truncation_at_5(
        self,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A cluster with >5 members prints first 5 and a footer."""
        for z in range(1, 8):  # 7 members
            make_uc(f"1.1.{z}", {"title": f"T{z}", "spl": "search index=x"})
        rc = sd.main([])
        out = capsys.readouterr().out
        assert rc == 0
        # The cluster reports its size correctly.
        assert "size=7" in out
        # Truncation footer appears.
        assert "... and 2 more" in out
        # Exactly 5 UC lines appear.
        cluster_section = out.split("Top clusters")[1]
        uc_lines = [line for line in cluster_section.splitlines() if "UC-1.1." in line]
        assert len(uc_lines) == 5

    def test_cluster_exactly_5_no_truncation(
        self,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Boundary: exactly 5 members → no ``... and N more`` line."""
        for z in range(1, 6):
            make_uc(f"1.1.{z}", {"title": f"T{z}", "spl": "search index=x"})
        rc = sd.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "size=5" in out
        assert "more" not in out.split("Top clusters")[1].split("\n")[2]

    def test_clusters_sorted_by_size_descending(
        self,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Larger clusters list first."""
        # Cluster A: 3 members
        for z in range(1, 4):
            make_uc(f"1.1.{z}", {"title": f"T{z}", "spl": "search index=a"})
        # Cluster B: 2 members
        for z in range(1, 3):
            make_uc(f"2.1.{z}", {"title": f"T{z}", "spl": "search index=b"}, category=2)
        rc = sd.main([])
        out = capsys.readouterr().out
        assert rc == 0
        # The 3-member cluster appears before the 2-member cluster.
        s3 = out.index("size=3")
        s2 = out.index("size=2")
        assert s3 < s2

    def test_more_than_30_clusters_truncated(
        self,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When >30 dup clusters exist, output is truncated."""
        # Build 31 clusters of 2 identical-SPL UCs each.
        for cluster_i in range(31):
            uc_a = f"1.1.{cluster_i * 2 + 1}"
            uc_b = f"1.1.{cluster_i * 2 + 2}"
            spl = f"search index=cluster_{cluster_i}"
            make_uc(uc_a, {"title": "A", "spl": spl})
            make_uc(uc_b, {"title": "B", "spl": spl})
        rc = sd.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Distinct dup clusters:  31" in out
        assert "... and 1 more clusters." in out

    def test_exactly_30_clusters_no_truncation(
        self,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Boundary: exactly 30 clusters → no truncation footer."""
        for cluster_i in range(30):
            uc_a = f"1.1.{cluster_i * 2 + 1}"
            uc_b = f"1.1.{cluster_i * 2 + 2}"
            spl = f"search index=cluster_{cluster_i}"
            make_uc(uc_a, {"title": "A", "spl": spl})
            make_uc(uc_b, {"title": "B", "spl": spl})
        rc = sd.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Distinct dup clusters:  30" in out
        # The trailing-cluster footer does not appear when count == 30.
        assert "more clusters" not in out


class TestMainCli:
    def test_argv_none_uses_sys_argv(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("sys.argv", ["spl_duplicates"])
        assert sd.main(None) == 0

    def test_help_exits_clean(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit) as excinfo:
            sd.main(["--help"])
        out = capsys.readouterr().out
        assert excinfo.value.code == 0
        assert "SPL" in out or "duplicate" in out.lower()
