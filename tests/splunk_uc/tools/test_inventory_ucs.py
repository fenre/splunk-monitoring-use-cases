"""Hermetic coverage suite for ``splunk_uc.tools.inventory_ucs``.

Brings coverage from 20.2% to 100%.

The driver walks ``content/cat-*/UC-*.json`` and emits an inventory
JSON + CSV under ``data/inventory/``. All tests redirect ``REPO``,
``CONTENT_DIR``, and ``OUT_DIR`` via ``monkeypatch`` so the live
catalogue is never touched.
"""

from __future__ import annotations

import csv as csv_lib
import json
import pathlib

import pytest

from splunk_uc.tools import inventory_ucs as iv

# ---------------------------------------------------------------------------
# Fixture: hermetic repo skeleton
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_repo(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> pathlib.Path:
    """Construct a hermetic repo skeleton and redirect every module
    constant at it."""

    content = tmp_path / "content"
    out_dir = tmp_path / "data" / "inventory"
    content.mkdir()

    monkeypatch.setattr(iv, "REPO", tmp_path)
    monkeypatch.setattr(iv, "CONTENT_DIR", content)
    monkeypatch.setattr(iv, "OUT_DIR", out_dir)
    return tmp_path


def _make_sidecar(
    cat_dir: pathlib.Path,
    *,
    uc_id: str,
    title: str = "Test UC",
    extra: dict[str, object] | None = None,
) -> pathlib.Path:
    cat_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "id": uc_id,
        "title": title,
        "criticality": "High",
        "difficulty": "Medium",
    }
    if extra:
        payload.update(extra)
    path = cat_dir / f"UC-{uc_id}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# UseCase dataclass + helpers
# ---------------------------------------------------------------------------


class TestUseCaseDataclass:
    def test_sort_key_returns_tuple(self) -> None:
        uc = iv.UseCase(
            uc_id="UC-1.2.3",
            category=1,
            subcategory=2,
            index=3,
            title="x",
            source_file="content/cat-01-x/UC-1.2.3.json",
        )
        assert uc.sort_key == (1, 2, 3)

    def test_default_factories_isolate_per_instance(self) -> None:
        a = iv.UseCase(
            uc_id="UC-1.1.1",
            category=1,
            subcategory=1,
            index=1,
            title="a",
            source_file="x.json",
        )
        b = iv.UseCase(
            uc_id="UC-1.1.2",
            category=1,
            subcategory=1,
            index=2,
            title="b",
            source_file="y.json",
        )
        a.monitoring_type.append("real-time")
        # ``b`` must NOT see ``a``'s mutation — proves field(default_factory=list).
        assert b.monitoring_type == []


class TestNormaliseList:
    def test_none_and_empty_string_return_empty(self) -> None:
        assert iv._normalise_list(None) == []
        assert iv._normalise_list("") == []

    def test_dash_and_na_and_none_string_return_empty(self) -> None:
        for raw in ("-", "n/a", "none", "  N/A  ", "  -.  ", "."):
            assert iv._normalise_list(raw) == [], raw

    def test_string_split_on_separators_and_and(self) -> None:
        assert iv._normalise_list("GDPR, PCI DSS; HIPAA / SOX and ISO 27001") == [
            "GDPR",
            "PCI DSS",
            "HIPAA",
            "SOX",
            "ISO 27001",
        ]

    def test_string_returns_single_value_when_no_separators(self) -> None:
        assert iv._normalise_list("just-one") == ["just-one"]

    def test_list_input_filters_none_and_skip_tokens(self) -> None:
        # None values are dropped, skip-tokens are dropped, surviving
        # values are stripped.
        assert iv._normalise_list(
            ["GDPR ", None, "", "  ", "-", "n/a", " HIPAA "]
        ) == ["GDPR", "HIPAA"]

    def test_list_coerces_non_string_items_to_str(self) -> None:
        assert iv._normalise_list([42, 3.14]) == ["42", "3.14"]

    def test_non_list_non_string_falls_to_default_empty(self) -> None:
        # Pin the final ``return []`` for unsupported types
        # (dict, int, ...). The ``raw in (None, "")`` short-circuit
        # would except on dicts so we use an int.
        assert iv._normalise_list({"key": "val"}) == []


# ---------------------------------------------------------------------------
# parse_sidecar
# ---------------------------------------------------------------------------


class TestParseSidecar:
    def test_happy_path_returns_use_case(
        self, fake_repo: pathlib.Path
    ) -> None:
        cat_dir = iv.CONTENT_DIR / "cat-01-foo"
        path = _make_sidecar(
            cat_dir,
            uc_id="1.2.3",
            extra={
                "monitoringType": ["real-time", "scheduled"],
                "splunkPillar": "security",
                "regulations": ["GDPR"],
                "mitreAttack": ["T1059"],
            },
        )
        uc = iv.parse_sidecar(path, 1)
        assert uc is not None
        assert uc.uc_id == "UC-1.2.3"
        assert uc.category == 1
        assert uc.subcategory == 2
        assert uc.index == 3
        assert uc.title == "Test UC"
        assert uc.source_file == "content/cat-01-foo/UC-1.2.3.json"
        assert uc.monitoring_type == ["real-time", "scheduled"]
        assert uc.regulations == ["GDPR"]

    def test_returns_none_for_unreadable_sidecar(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat_dir = iv.CONTENT_DIR / "cat-01-foo"
        cat_dir.mkdir()
        bad = cat_dir / "UC-1.1.1.json"
        bad.write_text("{ not valid json", encoding="utf-8")
        assert iv.parse_sidecar(bad, 1) is None
        assert "WARN: skipping unreadable sidecar" in capsys.readouterr().err

    def test_falls_back_to_filename_when_payload_missing_id(
        self, fake_repo: pathlib.Path
    ) -> None:
        cat_dir = iv.CONTENT_DIR / "cat-01-foo"
        cat_dir.mkdir()
        # Payload without ``id`` — driver derives it from the filename
        # stem via ``removeprefix('UC-')``.
        path = cat_dir / "UC-1.2.3.json"
        path.write_text(json.dumps({"title": "x"}), encoding="utf-8")
        uc = iv.parse_sidecar(path, 1)
        assert uc is not None
        assert uc.uc_id == "UC-1.2.3"

    def test_returns_none_for_malformed_id(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat_dir = iv.CONTENT_DIR / "cat-01-foo"
        cat_dir.mkdir()
        path = cat_dir / "UC-broken.json"
        # Two dots instead of two dots+three-int triplet → split returns
        # the wrong number of pieces.
        path.write_text(json.dumps({"id": "not.an.id.too.long"}), encoding="utf-8")
        assert iv.parse_sidecar(path, 1) is None
        assert "malformed id" in capsys.readouterr().err

    def test_returns_none_when_split_produces_non_numeric_pieces(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat_dir = iv.CONTENT_DIR / "cat-01-foo"
        cat_dir.mkdir()
        path = cat_dir / "UC-A.B.C.json"
        path.write_text(json.dumps({"id": "A.B.C"}), encoding="utf-8")
        assert iv.parse_sidecar(path, 1) is None
        assert "malformed id" in capsys.readouterr().err

    def test_warns_when_id_category_disagrees_with_dir(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # The UC lives under cat-99 but its id says cat-1 — driver
        # WARNs but STILL returns the UC (it does not return None).
        cat_dir = iv.CONTENT_DIR / "cat-99-other"
        path = _make_sidecar(cat_dir, uc_id="1.2.3")
        uc = iv.parse_sidecar(path, 99)
        assert uc is not None
        assert "but lives under" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# discover_category_dirs + parse_category
# ---------------------------------------------------------------------------


class TestDiscoverCategoryDirs:
    def test_returns_sorted_pairs(self, fake_repo: pathlib.Path) -> None:
        (iv.CONTENT_DIR / "cat-03-c").mkdir()
        (iv.CONTENT_DIR / "cat-01-a").mkdir()
        (iv.CONTENT_DIR / "cat-02-b").mkdir()
        pairs = iv.discover_category_dirs()
        nums = [n for n, _ in pairs]
        assert nums == [1, 2, 3]

    def test_skips_non_directories(self, fake_repo: pathlib.Path) -> None:
        (iv.CONTENT_DIR / "cat-01-a").mkdir()
        # A file matching the glob is dropped by the is_dir() guard.
        (iv.CONTENT_DIR / "cat-99-stray.txt").write_text("x", encoding="utf-8")
        pairs = iv.discover_category_dirs()
        assert [n for n, _ in pairs] == [1]

    def test_skips_dirs_with_no_numeric_prefix(
        self, fake_repo: pathlib.Path
    ) -> None:
        (iv.CONTENT_DIR / "cat-01-a").mkdir()
        # Matches the glob but not the regex — dropped.
        (iv.CONTENT_DIR / "cat-NN-not-a-num").mkdir()
        pairs = iv.discover_category_dirs()
        assert [n for n, _ in pairs] == [1]


class TestParseCategory:
    def test_yields_use_cases_sorted_by_filename(
        self, fake_repo: pathlib.Path
    ) -> None:
        cat_dir = iv.CONTENT_DIR / "cat-01-foo"
        _make_sidecar(cat_dir, uc_id="1.1.3")
        _make_sidecar(cat_dir, uc_id="1.1.1")
        _make_sidecar(cat_dir, uc_id="1.1.2")
        ids = [uc.uc_id for uc in iv.parse_category(cat_dir, 1)]
        # Sorted on filename (which has UC-1.1.X.json so lexical == numeric).
        assert ids == ["UC-1.1.1", "UC-1.1.2", "UC-1.1.3"]

    def test_drops_unparseable_sidecars(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat_dir = iv.CONTENT_DIR / "cat-01-foo"
        cat_dir.mkdir()
        (cat_dir / "UC-bad.json").write_text("{ broken", encoding="utf-8")
        _make_sidecar(cat_dir, uc_id="1.1.1")
        ids = [uc.uc_id for uc in iv.parse_category(cat_dir, 1)]
        # The unreadable one is silently dropped (with a stderr warning).
        assert ids == ["UC-1.1.1"]


# ---------------------------------------------------------------------------
# validate / write_json / write_csv / print_stats
# ---------------------------------------------------------------------------


class TestValidate:
    def _uc(self, uc_id: str, source: str = "x.json") -> iv.UseCase:
        cat, sub, idx = (int(p) for p in uc_id.removeprefix("UC-").split("."))
        return iv.UseCase(
            uc_id=uc_id,
            category=cat,
            subcategory=sub,
            index=idx,
            title="x",
            source_file=source,
        )

    def test_no_duplicates_returns_empty(self) -> None:
        ucs = [self._uc("UC-1.1.1"), self._uc("UC-1.1.2")]
        assert iv.validate(ucs) == []

    def test_duplicates_emit_paired_error(self) -> None:
        a = self._uc("UC-1.1.1", source="a.json")
        b = self._uc("UC-1.1.1", source="b.json")
        errs = iv.validate([a, b])
        assert errs == ["duplicate UC id UC-1.1.1: b.json vs a.json"]


class TestWriteJson:
    def test_writes_well_formed_payload(
        self, fake_repo: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        target = tmp_path / "ucs.json"
        ucs = [
            iv.UseCase(
                uc_id="UC-1.1.1",
                category=1,
                subcategory=1,
                index=1,
                title="t",
                source_file="x.json",
            )
        ]
        iv.write_json(ucs, target)
        payload = json.loads(target.read_text(encoding="utf-8"))
        assert payload["schemaVersion"] == 1
        assert payload["totalUseCases"] == 1
        assert payload["useCases"][0]["uc_id"] == "UC-1.1.1"
        # Trailing newline preserved.
        assert target.read_text(encoding="utf-8").endswith("\n")


class TestWriteCsv:
    def test_writes_header_and_one_row(self, tmp_path: pathlib.Path) -> None:
        target = tmp_path / "ucs.csv"
        uc = iv.UseCase(
            uc_id="UC-1.1.1",
            category=1,
            subcategory=1,
            index=1,
            title="t",
            source_file="x.json",
            criticality="High",
            difficulty="Easy",
            monitoring_type=["a", "b"],
            splunk_pillar="security",
            regulations=["GDPR", "HIPAA"],
            mitre_attack=["T1059"],
        )
        iv.write_csv([uc], target)
        with target.open(encoding="utf-8") as fh:
            rows = list(csv_lib.reader(fh))
        assert rows[0] == [
            "uc_id",
            "category",
            "subcategory",
            "title",
            "criticality",
            "difficulty",
            "monitoring_type",
            "splunk_pillar",
            "regulations",
            "mitre_attack",
            "source_file",
            "source_line",
        ]
        # Multi-value columns rendered as ``"; "``-joined strings.
        assert rows[1][6] == "a; b"
        assert rows[1][8] == "GDPR; HIPAA"


class TestPrintStats:
    def test_zero_ucs_emits_no_division_error(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        iv.print_stats([])
        out = capsys.readouterr().out
        assert "Total UCs: 0" in out

    def test_full_summary_with_regs_and_categories(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ucs = [
            iv.UseCase(
                uc_id="UC-1.1.1",
                category=1,
                subcategory=1,
                index=1,
                title="x",
                source_file="x.json",
                regulations=["GDPR", "PCI DSS"],
            ),
            iv.UseCase(
                uc_id="UC-2.1.1",
                category=2,
                subcategory=1,
                index=1,
                title="x",
                source_file="x.json",
                regulations=["GDPR"],
            ),
            iv.UseCase(
                uc_id="UC-2.1.2",
                category=2,
                subcategory=1,
                index=2,
                title="x",
                source_file="x.json",
                # No regulations → with_regs not incremented.
                regulations=[],
            ),
        ]
        iv.print_stats(ucs)
        out = capsys.readouterr().out
        assert "Total UCs: 3" in out
        assert "UCs with Regulations:" in out
        assert "cat-01: 1" in out
        assert "cat-02: 2" in out
        assert "GDPR" in out
        assert "PCI DSS" in out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


class TestMain:
    def test_returns_2_when_duplicates_present(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat_a = iv.CONTENT_DIR / "cat-01-a"
        cat_b = iv.CONTENT_DIR / "cat-01-other"
        # Same UC ID under two different cat-01 directories.
        _make_sidecar(cat_a, uc_id="1.1.1")
        _make_sidecar(cat_b, uc_id="1.1.1")
        rc = iv.main([])
        assert rc == 2
        assert "ERROR: duplicate UC id" in capsys.readouterr().err

    def test_writes_json_and_csv_without_stats_block(
        self,
        fake_repo: pathlib.Path,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat_dir = iv.CONTENT_DIR / "cat-01-foo"
        _make_sidecar(cat_dir, uc_id="1.1.1")
        out_dir = tmp_path / "out"
        rc = iv.main(["--out-dir", str(out_dir)])
        assert rc == 0
        assert (out_dir / "ucs.json").is_file()
        assert (out_dir / "ucs.csv").is_file()
        captured = capsys.readouterr().out
        assert "wrote" in captured
        # No stats block.
        assert "Total UCs:" not in captured

    def test_prints_stats_when_stats_flag_set(
        self,
        fake_repo: pathlib.Path,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat_dir = iv.CONTENT_DIR / "cat-01-foo"
        _make_sidecar(cat_dir, uc_id="1.1.1", extra={"regulations": ["GDPR"]})
        out_dir = tmp_path / "out"
        rc = iv.main(["--out-dir", str(out_dir), "--stats"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Total UCs: 1" in out
        assert "GDPR" in out

    def test_accepts_none_argv(
        self,
        fake_repo: pathlib.Path,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # When argv=None, argparse parses sys.argv. We monkeypatch
        # sys.argv to a minimal value that won't fail.
        monkeypatch.setattr(
            "sys.argv",
            ["inventory_ucs", "--out-dir", str(tmp_path / "out")],
        )
        rc = iv.main(None)
        assert rc == 0
