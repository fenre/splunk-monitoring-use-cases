"""Hermetic tests for ``scripts/parse_uc_catalog.py``.

The script walks the JSON SSOT (``content/cat-*/UC-*.json``) and emits a
flat ``manifest-all.json`` consumed by the ``uc-manifest`` CI workflow.
We exercise every public helper plus every branch in ``main()`` against
synthetic SSOT trees rooted at ``tmp_path`` — no network, no real
content directory mutation, every test cleans up after itself.

Coverage target: 100% of ``scripts/parse_uc_catalog.py``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = str(REPO_ROOT / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import parse_uc_catalog as M  # noqa: E402


# -----------------------------------------------------------------------------
# Fixture helpers
# -----------------------------------------------------------------------------

def _seed_content(
    base: Path,
    cat: int,
    slug: str,
    uc_id: str,
    title: str,
) -> Path:
    """Create ``content/cat-NN-slug/UC-X.Y.Z.json`` and return the file path."""
    cat_dir = base / f"cat-{cat:02d}-{slug}"
    cat_dir.mkdir(parents=True, exist_ok=True)
    sidecar = cat_dir / f"UC-{uc_id}.json"
    sidecar.write_text(
        json.dumps({"id": uc_id, "title": title}),
        encoding="utf-8",
    )
    return sidecar


def _seed_family_config(path: Path, mapping: dict[str, str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"category_to_family": mapping}),
        encoding="utf-8",
    )
    return path


# -----------------------------------------------------------------------------
# Pure helpers
# -----------------------------------------------------------------------------


class TestRepoRoot:
    def test_returns_path_object(self) -> None:
        out = M.repo_root()
        assert isinstance(out, Path)

    def test_resolves_to_repo_root(self) -> None:
        assert (M.repo_root() / "scripts" / "parse_uc_catalog.py").is_file()


class TestCategoryFromDirname:
    @pytest.mark.parametrize(
        "name,expected",
        [
            ("cat-1-foo", 1),
            ("cat-09-bar-baz", 9),
            ("cat-23-x", 23),
            ("cat-100-anything", 100),
        ],
    )
    def test_canonical_matches(self, name: str, expected: int) -> None:
        assert M.category_from_dirname(name) == expected

    @pytest.mark.parametrize(
        "name",
        [
            "cat-foo",  # no number
            "category-1-foo",  # wrong prefix
            "1-cat-foo",  # number first
            "",  # empty
            "cat-",  # incomplete
            "cat-1",  # missing trailing slug (regex requires .+)
        ],
    )
    def test_non_matching_returns_none(self, name: str) -> None:
        assert M.category_from_dirname(name) is None


class TestLoadFamilyMap:
    def test_loads_from_json(self, tmp_path: Path) -> None:
        cfg = _seed_family_config(
            tmp_path / "uc_to_log_family.json",
            {"1": "web", "5": "auth"},
        )
        assert M.load_family_map(cfg) == {"1": "web", "5": "auth"}

    def test_missing_key_returns_empty_dict(self, tmp_path: Path) -> None:
        cfg = tmp_path / "no_mapping.json"
        cfg.write_text(json.dumps({"unrelated": "x"}), encoding="utf-8")
        assert M.load_family_map(cfg) == {}

    def test_empty_mapping_returns_empty_dict(self, tmp_path: Path) -> None:
        cfg = _seed_family_config(tmp_path / "empty.json", {})
        assert M.load_family_map(cfg) == {}


class TestParseUcSidecar:
    def test_canonical_payload(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(M, "repo_root", lambda: tmp_path)
        sidecar = _seed_content(
            tmp_path / "content", cat=1, slug="foo", uc_id="1.1.1", title="Hello"
        )
        out = M.parse_uc_sidecar(sidecar, 1, "web")
        assert out is not None
        assert out["uc_id"] == "1.1.1"
        assert out["title"] == "Hello"
        assert out["catalog_category"] == 1
        assert out["log_family"] == "web"
        assert out["source_file"].endswith("UC-1.1.1.json")
        # source_file is a POSIX-relative path under the repo root
        assert "content/cat-01-foo/" in out["source_file"]
        assert not out["source_file"].startswith("/")

    def test_strips_title_whitespace(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(M, "repo_root", lambda: tmp_path)
        cat_dir = tmp_path / "content" / "cat-01-foo"
        cat_dir.mkdir(parents=True)
        sidecar = cat_dir / "UC-1.1.1.json"
        sidecar.write_text(
            json.dumps({"id": "1.1.1", "title": "  spacey  \n"}),
            encoding="utf-8",
        )
        out = M.parse_uc_sidecar(sidecar, 1, "web")
        assert out is not None
        assert out["title"] == "spacey"

    def test_missing_id_falls_back_to_filename(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``payload.get("id") or path.stem.removeprefix("UC-")`` — pin the
        fallback path used when the JSON omits the ``id`` field."""
        monkeypatch.setattr(M, "repo_root", lambda: tmp_path)
        cat_dir = tmp_path / "content" / "cat-01-foo"
        cat_dir.mkdir(parents=True)
        sidecar = cat_dir / "UC-2.2.2.json"
        sidecar.write_text(
            json.dumps({"title": "no id field"}),
            encoding="utf-8",
        )
        out = M.parse_uc_sidecar(sidecar, 1, "web")
        assert out is not None
        assert out["uc_id"] == "2.2.2"

    def test_missing_title_defaults_to_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(M, "repo_root", lambda: tmp_path)
        cat_dir = tmp_path / "content" / "cat-01-foo"
        cat_dir.mkdir(parents=True)
        sidecar = cat_dir / "UC-3.3.3.json"
        sidecar.write_text(json.dumps({"id": "3.3.3"}), encoding="utf-8")
        out = M.parse_uc_sidecar(sidecar, 1, "web")
        assert out is not None
        assert out["title"] == ""

    def test_returns_none_on_missing_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``OSError`` branch — non-existent file."""
        monkeypatch.setattr(M, "repo_root", lambda: tmp_path)
        out = M.parse_uc_sidecar(
            tmp_path / "missing.json", 1, "web"
        )
        assert out is None

    def test_returns_none_on_invalid_json(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``json.JSONDecodeError`` branch — malformed file."""
        monkeypatch.setattr(M, "repo_root", lambda: tmp_path)
        cat_dir = tmp_path / "content" / "cat-01-foo"
        cat_dir.mkdir(parents=True)
        bad = cat_dir / "UC-bad.json"
        bad.write_text("{not-json", encoding="utf-8")
        assert M.parse_uc_sidecar(bad, 1, "web") is None


# -----------------------------------------------------------------------------
# main()
# -----------------------------------------------------------------------------


class TestMain:
    """End-to-end argparse + walk coverage. Each test seeds a fresh
    ``content/`` tree under ``tmp_path`` and stubs ``repo_root`` so
    ``source_file`` paths render relative to the temp tree."""

    @pytest.fixture
    def fake_repo(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> Path:
        """A clean repo skeleton at ``tmp_path`` with content/, config/."""
        (tmp_path / "content").mkdir()
        (tmp_path / "config").mkdir()
        monkeypatch.setattr(M, "repo_root", lambda: tmp_path)
        return tmp_path

    def _run(
        self,
        argv: list[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> int:
        monkeypatch.setattr(sys, "argv", ["parse_uc_catalog.py", *argv])
        return M.main()

    def test_writes_to_output_file(
        self,
        fake_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _seed_content(fake_repo / "content", 1, "foo", "1.1.1", "Title A")
        _seed_content(fake_repo / "content", 2, "bar", "2.2.2", "Title B")
        _seed_family_config(
            fake_repo / "config" / "uc_to_log_family.json",
            {"1": "web", "2": "auth"},
        )
        out = fake_repo / "out" / "manifest.json"
        rc = self._run(
            [
                "--content-dir",
                str(fake_repo / "content"),
                "--config",
                str(fake_repo / "config" / "uc_to_log_family.json"),
                "--output",
                str(out),
            ],
            monkeypatch,
        )
        assert rc == 0
        assert out.exists()
        manifest = json.loads(out.read_text(encoding="utf-8"))
        assert manifest["uc_count"] == 2
        ids = sorted(r["uc_id"] for r in manifest["use_cases"])
        assert ids == ["1.1.1", "2.2.2"]
        # log_family is per-category from the family map
        by_id = {r["uc_id"]: r for r in manifest["use_cases"]}
        assert by_id["1.1.1"]["log_family"] == "web"
        assert by_id["2.2.2"]["log_family"] == "auth"

    def test_writes_to_stdout_when_no_output(
        self,
        fake_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _seed_content(fake_repo / "content", 1, "foo", "1.1.1", "Hello")
        _seed_family_config(
            fake_repo / "config" / "uc_to_log_family.json", {"1": "web"}
        )
        rc = self._run(
            [
                "--content-dir",
                str(fake_repo / "content"),
                "--config",
                str(fake_repo / "config" / "uc_to_log_family.json"),
            ],
            monkeypatch,
        )
        assert rc == 0
        out = capsys.readouterr().out
        manifest = json.loads(out)
        assert manifest["uc_count"] == 1
        assert manifest["use_cases"][0]["uc_id"] == "1.1.1"

    def test_default_family_is_web_when_not_in_map(
        self,
        fake_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """``family_map.get(str(cat), "web")`` — pin the default."""
        _seed_content(fake_repo / "content", 7, "x", "7.1.1", "Q")
        # config has NO entry for cat 7
        _seed_family_config(
            fake_repo / "config" / "uc_to_log_family.json", {"1": "auth"}
        )
        self._run(
            [
                "--content-dir",
                str(fake_repo / "content"),
                "--config",
                str(fake_repo / "config" / "uc_to_log_family.json"),
            ],
            monkeypatch,
        )
        manifest = json.loads(capsys.readouterr().out)
        assert manifest["use_cases"][0]["log_family"] == "web"

    def test_skips_non_directories_in_content_dir(
        self,
        fake_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Pin the ``if not cat_dir.is_dir(): continue`` branch — a
        stray file at the top level of content/ must not crash the walk."""
        _seed_content(fake_repo / "content", 1, "foo", "1.1.1", "Q")
        # Stray file at content/ root (not a directory)
        (fake_repo / "content" / "README.md").write_text("# stray", encoding="utf-8")
        _seed_family_config(
            fake_repo / "config" / "uc_to_log_family.json", {"1": "web"}
        )
        rc = self._run(
            [
                "--content-dir",
                str(fake_repo / "content"),
                "--config",
                str(fake_repo / "config" / "uc_to_log_family.json"),
            ],
            monkeypatch,
        )
        assert rc == 0
        manifest = json.loads(capsys.readouterr().out)
        assert manifest["uc_count"] == 1

    def test_skips_directories_with_unrecognised_names(
        self,
        fake_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Pin the ``if cat is None: continue`` branch — a directory
        that doesn't match the cat-NN-slug pattern must be silently skipped."""
        _seed_content(fake_repo / "content", 1, "foo", "1.1.1", "Q")
        # Junk directory — doesn't match the cat-NN-slug regex
        (fake_repo / "content" / "junk-dir").mkdir()
        # Stash a UC sidecar inside it — should NOT be picked up
        (fake_repo / "content" / "junk-dir" / "UC-99.99.99.json").write_text(
            json.dumps({"id": "99.99.99", "title": "should-be-ignored"}),
            encoding="utf-8",
        )
        _seed_family_config(
            fake_repo / "config" / "uc_to_log_family.json", {"1": "web"}
        )
        self._run(
            [
                "--content-dir",
                str(fake_repo / "content"),
                "--config",
                str(fake_repo / "config" / "uc_to_log_family.json"),
            ],
            monkeypatch,
        )
        manifest = json.loads(capsys.readouterr().out)
        ids = [r["uc_id"] for r in manifest["use_cases"]]
        assert "99.99.99" not in ids
        assert ids == ["1.1.1"]

    def test_skips_unparseable_sidecar(
        self,
        fake_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Pin the ``if row is not None: append`` branch — a malformed
        sidecar must be skipped (not crash, not appear in manifest)."""
        _seed_content(fake_repo / "content", 1, "foo", "1.1.1", "Good")
        bad = fake_repo / "content" / "cat-01-foo" / "UC-bad.json"
        bad.write_text("{not-json", encoding="utf-8")
        _seed_family_config(
            fake_repo / "config" / "uc_to_log_family.json", {"1": "web"}
        )
        rc = self._run(
            [
                "--content-dir",
                str(fake_repo / "content"),
                "--config",
                str(fake_repo / "config" / "uc_to_log_family.json"),
            ],
            monkeypatch,
        )
        assert rc == 0
        manifest = json.loads(capsys.readouterr().out)
        assert manifest["uc_count"] == 1
        assert manifest["use_cases"][0]["uc_id"] == "1.1.1"

    def test_deterministic_id_ordering(
        self,
        fake_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Pin ``all_rows.sort(key=lambda r: r["uc_id"])`` — output must
        be stable regardless of filesystem walk order."""
        _seed_content(fake_repo / "content", 2, "bar", "2.1.1", "B")
        _seed_content(fake_repo / "content", 1, "foo", "1.1.1", "A")
        _seed_content(fake_repo / "content", 1, "foo", "1.2.1", "C")
        _seed_family_config(
            fake_repo / "config" / "uc_to_log_family.json",
            {"1": "web", "2": "auth"},
        )
        self._run(
            [
                "--content-dir",
                str(fake_repo / "content"),
                "--config",
                str(fake_repo / "config" / "uc_to_log_family.json"),
            ],
            monkeypatch,
        )
        manifest = json.loads(capsys.readouterr().out)
        ids = [r["uc_id"] for r in manifest["use_cases"]]
        assert ids == ["1.1.1", "1.2.1", "2.1.1"]

    def test_check_passes_with_at_least_one_uc(
        self,
        fake_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _seed_content(fake_repo / "content", 1, "foo", "1.1.1", "Q")
        _seed_family_config(
            fake_repo / "config" / "uc_to_log_family.json", {"1": "web"}
        )
        out = fake_repo / "manifest.json"
        rc = self._run(
            [
                "--content-dir",
                str(fake_repo / "content"),
                "--config",
                str(fake_repo / "config" / "uc_to_log_family.json"),
                "--output",
                str(out),
                "--check",
            ],
            monkeypatch,
        )
        assert rc == 0

    def test_check_fails_when_no_use_cases_found(
        self,
        fake_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Empty content/ directory but valid config
        _seed_family_config(
            fake_repo / "config" / "uc_to_log_family.json", {"1": "web"}
        )
        rc = self._run(
            [
                "--content-dir",
                str(fake_repo / "content"),
                "--config",
                str(fake_repo / "config" / "uc_to_log_family.json"),
                "--check",
            ],
            monkeypatch,
        )
        assert rc == 1
        assert "no use cases parsed" in capsys.readouterr().err

    def test_creates_parent_directories_for_output(
        self,
        fake_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``args.output.parent.mkdir(parents=True, exist_ok=True)`` —
        pin parent-directory creation for the output file."""
        _seed_content(fake_repo / "content", 1, "foo", "1.1.1", "Q")
        _seed_family_config(
            fake_repo / "config" / "uc_to_log_family.json", {"1": "web"}
        )
        deeply_nested = fake_repo / "deeply" / "nested" / "manifest.json"
        rc = self._run(
            [
                "--content-dir",
                str(fake_repo / "content"),
                "--config",
                str(fake_repo / "config" / "uc_to_log_family.json"),
                "--output",
                str(deeply_nested),
            ],
            monkeypatch,
        )
        assert rc == 0
        assert deeply_nested.exists()
        assert deeply_nested.parent.is_dir()

    def test_output_is_valid_json_with_required_fields(
        self,
        fake_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Top-level manifest contract: description, generated_at,
        uc_count, use_cases. Pin against schema drift."""
        _seed_content(fake_repo / "content", 1, "foo", "1.1.1", "T")
        _seed_family_config(
            fake_repo / "config" / "uc_to_log_family.json", {"1": "web"}
        )
        out = fake_repo / "m.json"
        self._run(
            [
                "--content-dir",
                str(fake_repo / "content"),
                "--config",
                str(fake_repo / "config" / "uc_to_log_family.json"),
                "--output",
                str(out),
            ],
            monkeypatch,
        )
        manifest = json.loads(out.read_text(encoding="utf-8"))
        for key in ("description", "generated_at", "uc_count", "use_cases"):
            assert key in manifest
        # generated_at is RFC3339-ish
        assert "T" in manifest["generated_at"]
        # row-level contract
        for row in manifest["use_cases"]:
            for key in (
                "uc_id",
                "title",
                "catalog_category",
                "source_file",
                "log_family",
            ):
                assert key in row


# -----------------------------------------------------------------------------
# Module entrypoint
# -----------------------------------------------------------------------------
#
# NOTE: ``parse_uc_catalog.py`` ends with::
#
#     if __name__ == "__main__":
#         raise SystemExit(main())
#
# Covering this 2-line tail with a ``runpy`` test would re-execute the
# script with the *real* repository as cwd, polluting ``stdout`` / writing
# to disk if ``--output`` is in argv. The branch is structurally identical
# to the same idiom we exercise in dozens of other CLIs; the
# coverage gain (2 lines) doesn't justify the side-effect risk. Documented
# as intentionally omitted.
