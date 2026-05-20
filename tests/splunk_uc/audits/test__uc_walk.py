"""Hermetic unit tests for ``splunk_uc.audits._uc_walk``.

P16 wave WW (2026-05-19). The shared helper that every audit walks the
JSON SSOT through. Pinning it at 100% catches drift in the four
primitive helpers — ``iter_uc_sidecars``, ``cat_dirs``, ``uc_label``,
``get_text_field``, ``get_list_field`` — before it ripples through
every downstream audit's test suite.

Tests pin every documented contract:

* Module-level constants ``REPO`` walks 3 parents up per ADR-0009,
  ``CONTENT == REPO/content``.
* ``iter_uc_sidecars`` matrix (empty dir → no yields; sorted order;
  non-dict JSON skipped; malformed JSON skipped; OSError on open
  swallowed; non-UC files ignored; multiple category dirs walked).
* ``cat_dirs`` matrix (returns sorted ``cat-*`` directories; non-cat
  dirs ignored; files starting with ``cat-`` ignored — only true dirs;
  empty content yields empty list).
* ``uc_label`` matrix (id present → ``UC-<id> (relpath)``; id missing
  → ``UC-<unknown> (relpath)``; non-string id stringified;
  relpath is relative to REPO).
* ``get_text_field`` matrix (string value → returned verbatim; missing
  key → empty string; non-string value → empty string).
* ``get_list_field`` matrix (list value → returned verbatim; missing
  key → empty list; non-list value → empty list).
"""

from __future__ import annotations

import json
import pathlib
from typing import Any, Protocol

import pytest

import splunk_uc.audits._uc_walk as uw


# ----------------------------------------------------------- module constants --
def test_repo_walks_three_parents_up() -> None:
    here = pathlib.Path(uw.__file__).resolve()
    assert uw.REPO == here.parents[3]


def test_content_constant() -> None:
    assert uw.CONTENT == uw.REPO / "content"


# ---------------------------------------------------------------- fixtures ----
class WriteUC(Protocol):
    def __call__(
        self,
        cat: str,
        uc_id: str,
        body: Any = ...,
    ) -> pathlib.Path: ...


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Patch ``REPO`` / ``CONTENT`` to a synthetic repo root."""
    (tmp_path / "content").mkdir()
    monkeypatch.setattr(uw, "REPO", tmp_path)
    monkeypatch.setattr(uw, "CONTENT", tmp_path / "content")
    return tmp_path


@pytest.fixture
def write_uc(fake_repo: pathlib.Path) -> WriteUC:
    """Factory creating a UC sidecar with an arbitrary JSON body."""

    def _factory(
        cat: str,
        uc_id: str,
        body: Any = ...,
    ) -> pathlib.Path:
        cat_dir = fake_repo / "content" / cat
        cat_dir.mkdir(exist_ok=True)
        path = cat_dir / f"UC-{uc_id}.json"
        if body is ...:
            body = {"id": uc_id}
        if isinstance(body, str):
            path.write_text(body, encoding="utf-8")
        else:
            path.write_text(json.dumps(body), encoding="utf-8")
        return path

    return _factory


# ------------------------------------------------------- iter_uc_sidecars ----
def test_iter_uc_sidecars_empty_content_yields_nothing(
    fake_repo: pathlib.Path,
) -> None:
    """Empty content tree → no yields."""
    assert list(uw.iter_uc_sidecars()) == []


def test_iter_uc_sidecars_single_dict_payload(fake_repo: pathlib.Path, write_uc: WriteUC) -> None:
    """A clean dict sidecar is yielded."""
    write_uc("cat-1-test", "1.1.1")
    results = list(uw.iter_uc_sidecars())
    assert len(results) == 1
    path, payload = results[0]
    assert path.name == "UC-1.1.1.json"
    assert payload == {"id": "1.1.1"}


def test_iter_uc_sidecars_yields_sorted(fake_repo: pathlib.Path, write_uc: WriteUC) -> None:
    """Sidecars are yielded in sorted-glob order."""
    write_uc("cat-2-bar", "2.1.1")
    write_uc("cat-1-foo", "1.1.1")
    write_uc("cat-1-foo", "1.2.1")
    paths = [p.name for p, _ in uw.iter_uc_sidecars()]
    # glob returns sorted within each subdir and across subdirs.
    assert paths == ["UC-1.1.1.json", "UC-1.2.1.json", "UC-2.1.1.json"]


def test_iter_uc_sidecars_skips_non_dict_payload(
    fake_repo: pathlib.Path, write_uc: WriteUC
) -> None:
    """JSON arrays / strings / numbers are silently skipped."""
    write_uc("cat-1-test", "1.1.1", body=["not", "a", "dict"])
    write_uc("cat-1-test", "1.1.2", body="just-a-string")
    write_uc("cat-1-test", "1.1.3", body=42)
    write_uc("cat-1-test", "1.1.4", body={"id": "1.1.4"})  # valid
    results = list(uw.iter_uc_sidecars())
    assert len(results) == 1
    assert results[0][1] == {"id": "1.1.4"}


def test_iter_uc_sidecars_skips_malformed_json(fake_repo: pathlib.Path, write_uc: WriteUC) -> None:
    """Files that fail ``json.load`` are silently skipped."""
    write_uc("cat-1-test", "1.1.1", body="this { is { not } json")
    write_uc("cat-1-test", "1.1.2")  # valid dict
    results = list(uw.iter_uc_sidecars())
    assert len(results) == 1
    assert results[0][0].name == "UC-1.1.2.json"


def test_iter_uc_sidecars_skips_oserror_on_open(
    fake_repo: pathlib.Path,
    write_uc: WriteUC,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``OSError`` raised by ``open()`` is silently swallowed."""
    write_uc("cat-1-test", "1.1.1")

    real_open = pathlib.Path.open

    def boom_open(self: pathlib.Path, *a: Any, **kw: Any) -> Any:
        if self.name == "UC-1.1.1.json":
            raise OSError("simulated permission denied")
        return real_open(self, *a, **kw)

    monkeypatch.setattr(pathlib.Path, "open", boom_open)
    results = list(uw.iter_uc_sidecars())
    assert results == []  # the only UC raised OSError → skipped


def test_iter_uc_sidecars_ignores_non_uc_files(fake_repo: pathlib.Path, write_uc: WriteUC) -> None:
    """Files not matching ``UC-*.json`` are not yielded."""
    write_uc("cat-1-test", "1.1.1")
    (fake_repo / "content" / "cat-1-test" / "README.md").write_text("stuff", encoding="utf-8")
    (fake_repo / "content" / "cat-1-test" / "category.json").write_text(
        json.dumps({"id": 1}), encoding="utf-8"
    )
    paths = [p.name for p, _ in uw.iter_uc_sidecars()]
    assert paths == ["UC-1.1.1.json"]


# -------------------------------------------------------------- cat_dirs ----
def test_cat_dirs_returns_sorted_cat_dirs(fake_repo: pathlib.Path) -> None:
    (fake_repo / "content" / "cat-2-bar").mkdir()
    (fake_repo / "content" / "cat-1-foo").mkdir()
    (fake_repo / "content" / "cat-10-zzz").mkdir()
    dirs = [d.name for d in uw.cat_dirs()]
    # lexicographic sort: 10 < 2
    assert dirs == ["cat-1-foo", "cat-10-zzz", "cat-2-bar"]


def test_cat_dirs_ignores_files_starting_with_cat(
    fake_repo: pathlib.Path,
) -> None:
    """Files named ``cat-*`` (not dirs) are filtered out via ``is_dir``."""
    (fake_repo / "content" / "cat-1-foo").mkdir()
    (fake_repo / "content" / "cat-not-a-dir").write_text("file content", encoding="utf-8")
    dirs = [d.name for d in uw.cat_dirs()]
    assert dirs == ["cat-1-foo"]


def test_cat_dirs_ignores_non_cat_directories(
    fake_repo: pathlib.Path,
) -> None:
    """Dirs not starting with ``cat-`` are filtered out."""
    (fake_repo / "content" / "cat-1-foo").mkdir()
    (fake_repo / "content" / "docs").mkdir()
    (fake_repo / "content" / "_workspace").mkdir()
    dirs = [d.name for d in uw.cat_dirs()]
    assert dirs == ["cat-1-foo"]


def test_cat_dirs_empty_content_yields_empty_list(
    fake_repo: pathlib.Path,
) -> None:
    assert uw.cat_dirs() == []


# -------------------------------------------------------------- uc_label ----
def test_uc_label_renders_id_and_relpath(fake_repo: pathlib.Path, write_uc: WriteUC) -> None:
    p = write_uc("cat-1-test", "1.1.1")
    label = uw.uc_label(p, {"id": "1.1.1"})
    assert label == "UC-1.1.1 (content/cat-1-test/UC-1.1.1.json)"


def test_uc_label_missing_id_renders_as_unknown(fake_repo: pathlib.Path, write_uc: WriteUC) -> None:
    p = write_uc("cat-1-test", "noid", body={"no_id_field": True})
    label = uw.uc_label(p, {})
    assert label.startswith("UC-<unknown>")
    assert "content/cat-1-test/UC-noid.json" in label


def test_uc_label_non_string_id_stringified(fake_repo: pathlib.Path, write_uc: WriteUC) -> None:
    p = write_uc("cat-1-test", "1.1.1")
    label = uw.uc_label(p, {"id": 42})
    assert label.startswith("UC-42 (")


def test_uc_label_returns_string_with_forward_slash(
    fake_repo: pathlib.Path, write_uc: WriteUC
) -> None:
    """The relpath should use the same separator as the OS — on POSIX,
    that's forward slash. We just assert the relative-to-REPO behaviour.
    """
    p = write_uc("cat-1-test", "1.1.1")
    label = uw.uc_label(p, {"id": "1.1.1"})
    rel = p.relative_to(uw.REPO)
    assert str(rel) in label


# ---------------------------------------------------------- get_text_field ---
def test_get_text_field_string_returned_verbatim() -> None:
    assert uw.get_text_field({"k": "hello"}, "k") == "hello"


def test_get_text_field_empty_string_returned_verbatim() -> None:
    assert uw.get_text_field({"k": ""}, "k") == ""


def test_get_text_field_missing_key_returns_empty_string() -> None:
    assert uw.get_text_field({}, "k") == ""


def test_get_text_field_non_string_value_returns_empty_string() -> None:
    """Numbers, lists, dicts, None all yield empty string."""
    assert uw.get_text_field({"k": 42}, "k") == ""
    assert uw.get_text_field({"k": [1, 2]}, "k") == ""
    assert uw.get_text_field({"k": {"x": 1}}, "k") == ""
    assert uw.get_text_field({"k": None}, "k") == ""


# ---------------------------------------------------------- get_list_field ---
def test_get_list_field_list_returned_verbatim() -> None:
    assert uw.get_list_field({"k": [1, 2, 3]}, "k") == [1, 2, 3]


def test_get_list_field_empty_list_returned_verbatim() -> None:
    assert uw.get_list_field({"k": []}, "k") == []


def test_get_list_field_missing_key_returns_empty_list() -> None:
    assert uw.get_list_field({}, "k") == []


def test_get_list_field_non_list_value_returns_empty_list() -> None:
    """Strings, dicts, numbers, None all yield empty list."""
    assert uw.get_list_field({"k": "string"}, "k") == []
    assert uw.get_list_field({"k": {"x": 1}}, "k") == []
    assert uw.get_list_field({"k": 42}, "k") == []
    assert uw.get_list_field({"k": None}, "k") == []
