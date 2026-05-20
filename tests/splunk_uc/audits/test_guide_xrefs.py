"""Unit tests pinning ``splunk_uc.audits.guide_xrefs``.

The audit walks every markdown file under ``docs/guides/`` and verifies
that every internal markdown link to another ``.md`` file resolves to an
existing guide. The audit cares only about guide-to-guide links:

- Bare basenames (no ``/`` separator) — resolved against the source
  guide's own directory, which IS ``docs/guides/``.
- Paths containing a ``guides/`` segment — explicit cross-product
  references like ``docs/guides/foo.md`` or ``../guides/foo.md``.

Any other link target (e.g. ``../regulatory-primer.md``,
``../../AGENTS.md``, ``../../content/foo.json``) escapes the guides
directory and is the responsibility of a separate audit.

Broken targets surface as ``BrokenLink(source, target_raw, suggestion)``
records, where ``suggestion`` is the closest existing guide basename
within a difflib ratio of 0.6 — or ``None`` when no close match is
found.

The audit is **always gating on broken links** (exit code 2 on any
broken target). The ``--strict`` flag is reserved for parity with
sibling audits and is currently a no-op.

These tests build a synthetic ``docs/guides/`` tree under ``tmp_path``
and monkey-patch ``gx.GUIDES_DIR`` so the audit operates against the
fixture instead of the live filesystem.
"""

from __future__ import annotations

import dataclasses
import json
import pathlib
from typing import Protocol

import pytest

from splunk_uc.audits import guide_xrefs as gx


class WriteGuide(Protocol):
    """Factory protocol for writing a guide markdown file."""

    def __call__(self, name: str, body: str) -> pathlib.Path: ...


@pytest.fixture
def fake_guides(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Build a fake ``docs/guides/`` tree and rewire ``gx.GUIDES_DIR``."""
    guides_dir = tmp_path / "docs" / "guides"
    guides_dir.mkdir(parents=True)
    monkeypatch.setattr(gx, "GUIDES_DIR", str(guides_dir))
    return guides_dir


@pytest.fixture
def write_guide(fake_guides: pathlib.Path) -> WriteGuide:
    """Return a factory that creates ``docs/guides/<name>`` files."""

    def _make(name: str, body: str) -> pathlib.Path:
        path = fake_guides / name
        path.write_text(body, encoding="utf-8")
        return path

    return _make


# ---------------------------------------------------------------------------
# Module-level constants and regex
# ---------------------------------------------------------------------------


def test_script_dir_resolves_to_audits_directory() -> None:
    """SCRIPT_DIR resolves to the audits/ package directory."""
    assert pathlib.Path(gx.SCRIPT_DIR).name == "audits"
    assert pathlib.Path(gx.SCRIPT_DIR).is_absolute()


def test_repo_root_resolves_to_three_parents_up() -> None:
    """REPO_ROOT walks three parents up to land at the repo root."""
    repo_root = pathlib.Path(gx.REPO_ROOT)
    assert repo_root.is_absolute()
    assert (repo_root / "src" / "splunk_uc" / "audits").is_dir()


def test_guides_dir_lives_under_docs() -> None:
    """GUIDES_DIR is ``<REPO_ROOT>/docs/guides``."""
    guides_dir = pathlib.Path(gx.GUIDES_DIR)
    assert guides_dir.name == "guides"
    assert guides_dir.parent.name == "docs"


def test_link_re_captures_bare_basename() -> None:
    """``[text](file.md)`` captures ``file.md`` as group 2."""
    matches = gx.LINK_RE.findall("[Foo](file.md)")
    assert matches == [("Foo", "file.md")]


def test_link_re_captures_relative_path() -> None:
    """``[text](../guides/file.md)`` captures the full relative path."""
    matches = gx.LINK_RE.findall("[Foo](../guides/file.md)")
    assert matches == [("Foo", "../guides/file.md")]


def test_link_re_strips_anchor_fragment() -> None:
    """``[text](file.md#anchor)`` captures ``file.md`` only (anchor stripped)."""
    matches = gx.LINK_RE.findall("[Foo](file.md#anchor)")
    assert matches == [("Foo", "file.md")]


def test_link_re_strips_query_string() -> None:
    """``[text](file.md?q=v)`` captures ``file.md`` only (query stripped)."""
    matches = gx.LINK_RE.findall("[Foo](file.md?q=v)")
    assert matches == [("Foo", "file.md")]


def test_link_re_requires_md_suffix() -> None:
    """Links to non-``.md`` files are NOT matched (audit scope)."""
    assert gx.LINK_RE.findall("[Foo](image.png)") == []
    assert gx.LINK_RE.findall("[Foo](foo.json)") == []


def test_link_re_ignores_link_with_spaces_in_target() -> None:
    """Targets with whitespace are NOT matched (the audit avoids those)."""
    assert gx.LINK_RE.findall("[Foo](my file.md)") == []


def test_link_re_ignores_anchor_only_link() -> None:
    """Anchor-only ``[text](#section)`` links are NOT matched."""
    assert gx.LINK_RE.findall("[Foo](#section)") == []


def test_link_re_matches_multiple_links() -> None:
    """Every link in the same body is captured."""
    body = "[A](a.md) and [B](b.md) and [C](c.md)"
    matches = gx.LINK_RE.findall(body)
    assert matches == [("A", "a.md"), ("B", "b.md"), ("C", "c.md")]


# ---------------------------------------------------------------------------
# _is_guide_target
# ---------------------------------------------------------------------------


def test_is_guide_target_accepts_bare_basename() -> None:
    """Bare basenames (no ``/``) ARE guide targets."""
    assert gx._is_guide_target("file.md") is True
    assert gx._is_guide_target("aws.md") is True


def test_is_guide_target_accepts_explicit_guides_path() -> None:
    """Paths containing ``guides/`` ARE guide targets."""
    assert gx._is_guide_target("docs/guides/file.md") is True
    assert gx._is_guide_target("../guides/file.md") is True
    assert gx._is_guide_target("../../docs/guides/file.md") is True


def test_is_guide_target_rejects_paths_escaping_guides_dir() -> None:
    """Paths without ``guides/`` AND containing ``/`` are NOT guide targets."""
    assert gx._is_guide_target("../regulatory-primer.md") is False
    assert gx._is_guide_target("../../AGENTS.md") is False
    assert gx._is_guide_target("../../content/foo.md") is False


def test_is_guide_target_empty_string_treated_as_guide_target() -> None:
    """Empty string has no ``/`` so is treated as a guide target.

    The audit's pre-filter is intentionally permissive; the downstream
    existence check catches the actually-broken cases.
    """
    assert gx._is_guide_target("") is True


# ---------------------------------------------------------------------------
# _existing_guides
# ---------------------------------------------------------------------------


def test_existing_guides_returns_md_filenames(write_guide: WriteGuide) -> None:
    """Every ``.md`` file in GUIDES_DIR is returned by basename."""
    write_guide("aws.md", "body")
    write_guide("azure.md", "body")
    assert gx._existing_guides() == {"aws.md", "azure.md"}


def test_existing_guides_returns_empty_when_no_guides(
    fake_guides: pathlib.Path,
) -> None:
    """An empty guides dir yields an empty set."""
    assert gx._existing_guides() == set()


def test_existing_guides_returns_empty_when_dir_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """A missing GUIDES_DIR yields an empty set (no exception)."""
    monkeypatch.setattr(gx, "GUIDES_DIR", str(tmp_path / "nope"))
    assert gx._existing_guides() == set()


def test_existing_guides_skips_non_md_files(write_guide: WriteGuide) -> None:
    """Non-``.md`` files are not in the guide set."""
    write_guide("aws.md", "body")
    write_guide("README.txt", "body")
    write_guide("foo.json", "{}")
    assert gx._existing_guides() == {"aws.md"}


def test_existing_guides_skips_dotfiles(write_guide: WriteGuide) -> None:
    """Files starting with ``.`` are skipped."""
    write_guide("aws.md", "body")
    write_guide(".hidden.md", "body")
    assert gx._existing_guides() == {"aws.md"}


# ---------------------------------------------------------------------------
# _normalize
# ---------------------------------------------------------------------------


def test_normalize_bare_basename_returns_same() -> None:
    """A bare basename is returned unchanged."""
    assert gx._normalize("aws.md") == "aws.md"


def test_normalize_strips_single_parent_dir_prefix() -> None:
    """One ``../`` is stripped from the front."""
    assert gx._normalize("../aws.md") == "aws.md"


def test_normalize_strips_multiple_parent_dir_prefixes() -> None:
    """Multiple ``../`` prefixes are all stripped (legacy authoring)."""
    assert gx._normalize("../../../aws.md") == "aws.md"


def test_normalize_strips_docs_guides_prefix() -> None:
    """``docs/guides/`` prefix is removed via ``removeprefix``."""
    assert gx._normalize("docs/guides/aws.md") == "aws.md"


def test_normalize_handles_combined_parent_and_guides_prefix() -> None:
    """``../docs/guides/`` is fully stripped."""
    assert gx._normalize("../docs/guides/aws.md") == "aws.md"


def test_normalize_extracts_basename_when_other_dirs_present() -> None:
    """``os.path.basename`` returns just the final path component."""
    assert gx._normalize("../guides/aws.md") == "aws.md"


def test_normalize_returns_empty_for_directory_only_path() -> None:
    """A path ending in ``/`` yields empty basename."""
    assert gx._normalize("docs/guides/") == ""


# ---------------------------------------------------------------------------
# _suggest
# ---------------------------------------------------------------------------


def test_suggest_returns_close_match() -> None:
    """A typo within difflib's 0.6 cutoff returns the closest match."""
    suggestion = gx._suggest("aws.md", {"aws-guide.md", "azure.md"})
    assert suggestion in {"aws-guide.md"}


def test_suggest_returns_none_when_no_close_match() -> None:
    """An entirely different name returns ``None``."""
    assert gx._suggest("zzz.md", {"aws.md", "azure.md"}) is None


def test_suggest_returns_none_when_existing_is_empty() -> None:
    """An empty existing set returns ``None``."""
    assert gx._suggest("aws.md", set()) is None


def test_suggest_returns_first_of_multiple_close_matches() -> None:
    """``n=1`` ensures only the single closest match is returned."""
    suggestion = gx._suggest("aws.md", {"aws-old.md", "aws-new.md"})
    assert suggestion in {"aws-old.md", "aws-new.md"}


# ---------------------------------------------------------------------------
# BrokenLink dataclass
# ---------------------------------------------------------------------------


def test_broken_link_dataclass_is_frozen() -> None:
    """``BrokenLink`` is frozen — attribute assignment raises."""
    link = gx.BrokenLink(source="a.md", target_raw="b.md", suggestion=None)
    with pytest.raises(dataclasses.FrozenInstanceError):
        link.source = "x.md"


def test_broken_link_fields_are_attribute_accessible() -> None:
    """All three fields are reachable as attributes."""
    link = gx.BrokenLink(
        source="docs/guides/a.md",
        target_raw="missing.md",
        suggestion="aws.md",
    )
    assert link.source == "docs/guides/a.md"
    assert link.target_raw == "missing.md"
    assert link.suggestion == "aws.md"


def test_broken_link_suggestion_can_be_none() -> None:
    """``suggestion`` accepts ``None`` for no-close-match case."""
    link = gx.BrokenLink(source="a.md", target_raw="b.md", suggestion=None)
    assert link.suggestion is None


# ---------------------------------------------------------------------------
# collect_broken_links
# ---------------------------------------------------------------------------


def test_collect_returns_empty_when_guides_dir_empty(
    fake_guides: pathlib.Path,
) -> None:
    """An empty guides dir → ``(broken=[], total=0)``."""
    broken, total = gx.collect_broken_links()
    assert broken == []
    assert total == 0


def test_collect_returns_empty_when_guides_dir_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """A missing guides dir returns ``(broken=[], total=0)``."""
    monkeypatch.setattr(gx, "GUIDES_DIR", str(tmp_path / "nope"))
    broken, total = gx.collect_broken_links()
    assert broken == []
    assert total == 0


def test_collect_returns_zero_links_when_no_md_links_in_guides(
    write_guide: WriteGuide,
) -> None:
    """A guide with no ``.md`` links yields 0 scanned and 0 broken."""
    write_guide("aws.md", "body without any links\n")
    broken, total = gx.collect_broken_links()
    assert broken == []
    assert total == 0


def test_collect_counts_valid_links_in_total(write_guide: WriteGuide) -> None:
    """A valid link to an existing guide adds to total but not to broken."""
    write_guide("aws.md", "body")
    write_guide("azure.md", "[See aws](aws.md)\n")
    broken, total = gx.collect_broken_links()
    assert broken == []
    assert total == 1


def test_collect_flags_broken_basename_link(write_guide: WriteGuide) -> None:
    """A link to a non-existing guide surfaces as ``BrokenLink``."""
    write_guide("aws.md", "[Missing](missing.md)\n")
    broken, total = gx.collect_broken_links()
    assert total == 1
    assert len(broken) == 1
    assert broken[0].source == "docs/guides/aws.md"
    assert broken[0].target_raw == "missing.md"


def test_collect_flags_broken_relative_guides_link(
    write_guide: WriteGuide,
) -> None:
    """``../guides/<missing>.md`` cross-references are also flagged."""
    write_guide("aws.md", "[Missing](../guides/nowhere.md)\n")
    broken, total = gx.collect_broken_links()
    assert total == 1
    assert len(broken) == 1
    assert broken[0].target_raw == "../guides/nowhere.md"


def test_collect_skips_non_guide_targets(write_guide: WriteGuide) -> None:
    """Links escaping the guides dir are ignored (different audit)."""
    write_guide(
        "aws.md",
        "[Primer](../regulatory-primer.md)\n[Agents](../../AGENTS.md)\n",
    )
    broken, total = gx.collect_broken_links()
    assert broken == []
    assert total == 0


def test_collect_suggestion_populated_for_near_miss(
    write_guide: WriteGuide,
) -> None:
    """A typo'd target gets a difflib suggestion populated."""
    write_guide("aws-detailed.md", "body")
    write_guide("azure.md", "[See aws](aws-detaild.md)\n")
    broken, _total = gx.collect_broken_links()
    assert len(broken) == 1
    assert broken[0].suggestion == "aws-detailed.md"


def test_collect_suggestion_none_when_no_close_match(
    write_guide: WriteGuide,
) -> None:
    """An entirely unrelated target yields ``suggestion=None``."""
    write_guide("aws.md", "[Missing](zzz.md)\n")
    broken, _total = gx.collect_broken_links()
    assert len(broken) == 1
    assert broken[0].suggestion is None


def test_collect_walks_guides_in_sorted_order(
    write_guide: WriteGuide,
) -> None:
    """``os.listdir`` results are sorted before iteration (deterministic)."""
    write_guide("zzz.md", "[A](aaa.md)\n")
    write_guide("aaa.md", "[Z](zzz.md)\n")
    broken, total = gx.collect_broken_links()
    # Both files exist so neither link is broken; just ensure no crash.
    assert total == 2
    assert broken == []


def test_collect_skips_non_md_files(write_guide: WriteGuide) -> None:
    """Non-``.md`` files in GUIDES_DIR are not scanned."""
    write_guide("aws.md", "[Other](README.txt)\n")
    (pathlib.Path(gx.GUIDES_DIR) / "README.txt").write_text("[X](unrelated.md)", encoding="utf-8")
    broken, total = gx.collect_broken_links()
    # The .txt file is not scanned, so we get 0 links total.
    assert total == 0
    assert broken == []


def test_collect_skips_dotfiles(write_guide: WriteGuide) -> None:
    """Files starting with ``.`` are not scanned."""
    write_guide("aws.md", "body")
    (pathlib.Path(gx.GUIDES_DIR) / ".hidden.md").write_text("[X](unrelated.md)", encoding="utf-8")
    broken, total = gx.collect_broken_links()
    assert total == 0
    assert broken == []


def test_collect_continues_on_oserror_for_unreadable_file(
    fake_guides: pathlib.Path,
) -> None:
    """An ``OSError`` reading a guide is suppressed via ``continue``.

    Simulated by creating a guide that points at a *directory* of the
    same name — opening a directory raises ``IsADirectoryError`` which
    is an ``OSError`` subclass.
    """
    (fake_guides / "blocked.md").mkdir()
    (fake_guides / "aws.md").write_text("[X](unrelated.md)", encoding="utf-8")
    broken, total = gx.collect_broken_links()
    assert total == 1
    assert len(broken) == 1
    assert broken[0].source == "docs/guides/aws.md"


def test_collect_handles_multiple_broken_links_in_one_guide(
    write_guide: WriteGuide,
) -> None:
    """Multiple broken links in one guide all surface independently."""
    write_guide("aws.md", "[A](missing-a.md)\n[B](missing-b.md)\n")
    broken, total = gx.collect_broken_links()
    assert total == 2
    assert len(broken) == 2


def test_collect_returns_total_count_across_all_guides(
    write_guide: WriteGuide,
) -> None:
    """``total`` accumulates across multiple source guides."""
    write_guide("aws.md", "[X](x.md)\n")
    write_guide("azure.md", "[Y](y.md)\n")
    broken, total = gx.collect_broken_links()
    assert total == 2
    assert len(broken) == 2


# ---------------------------------------------------------------------------
# main() — text output
# ---------------------------------------------------------------------------


def test_main_returns_0_when_no_broken_links(
    write_guide: WriteGuide, capsys: pytest.CaptureFixture[str]
) -> None:
    """Clean guides → exit 0 with success message."""
    write_guide("aws.md", "body")
    assert gx.main([]) == 0
    captured = capsys.readouterr()
    assert "Guide cross-reference audit" in captured.out
    assert "No broken cross-product links found." in captured.out


def test_main_returns_0_when_guides_dir_empty(
    fake_guides: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Empty guides dir → exit 0 (no broken links and no scanned links)."""
    assert gx.main([]) == 0
    captured = capsys.readouterr()
    assert "Scanned 0 internal guide links across 0 guides." in captured.out


def test_main_returns_2_when_broken_link_present(
    write_guide: WriteGuide, capsys: pytest.CaptureFixture[str]
) -> None:
    """A broken link → exit 2 (gating)."""
    write_guide("aws.md", "[Missing](missing.md)\n")
    assert gx.main([]) == 2
    captured = capsys.readouterr()
    assert "Found 1 broken link(s):" in captured.out
    assert "missing.md" in captured.out


def test_main_includes_suggestion_in_text_output(
    write_guide: WriteGuide, capsys: pytest.CaptureFixture[str]
) -> None:
    """Suggestions are rendered as ``-> suggest: <name>``."""
    write_guide("aws-detailed.md", "body")
    write_guide("azure.md", "[Typo](aws-detaild.md)\n")
    assert gx.main([]) == 2
    captured = capsys.readouterr()
    assert "-> suggest: aws-detailed.md" in captured.out


def test_main_renders_no_close_match_when_suggestion_is_none(
    write_guide: WriteGuide, capsys: pytest.CaptureFixture[str]
) -> None:
    """No close match → ``-> no close match`` suffix."""
    write_guide("aws.md", "[Missing](zzz.md)\n")
    assert gx.main([]) == 2
    captured = capsys.readouterr()
    assert "-> no close match" in captured.out


def test_main_argv_none_uses_sys_argv_default(
    write_guide: WriteGuide,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``argv=None`` falls through to argparse's ``sys.argv`` default."""
    monkeypatch.setattr("sys.argv", ["audit-guide-xrefs"])
    write_guide("aws.md", "body")
    assert gx.main(None) == 0


def test_main_help_exits_clean(capsys: pytest.CaptureFixture[str]) -> None:
    """``--help`` exits 0 with documented flags visible."""
    with pytest.raises(SystemExit) as exc:
        gx.main(["--help"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "--json" in captured.out
    assert "--strict" in captured.out


def test_main_strict_flag_is_no_op_when_clean(
    write_guide: WriteGuide,
) -> None:
    """``--strict`` does NOT change exit when clean (it's reserved)."""
    write_guide("aws.md", "body")
    assert gx.main(["--strict"]) == 0


def test_main_strict_flag_does_not_change_exit_when_broken(
    write_guide: WriteGuide,
) -> None:
    """``--strict`` does NOT change exit when broken (audit always gating)."""
    write_guide("aws.md", "[Missing](missing.md)\n")
    assert gx.main(["--strict"]) == 2


# ---------------------------------------------------------------------------
# main() — JSON output
# ---------------------------------------------------------------------------


def test_main_json_emits_empty_list_when_clean(
    write_guide: WriteGuide, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--json`` with no broken links → ``[]`` on stdout and exit 0."""
    write_guide("aws.md", "body")
    assert gx.main(["--json"]) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == []


def test_main_json_emits_broken_links_array(
    write_guide: WriteGuide, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--json`` emits one object per broken link with all 3 fields."""
    write_guide("aws-detailed.md", "body")
    write_guide("azure.md", "[Typo](aws-detaild.md)\n[Missing](zzz.md)\n")
    assert gx.main(["--json"]) == 2
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert len(payload) == 2
    sources = {item["source"] for item in payload}
    assert sources == {"docs/guides/azure.md"}
    suggestions = {item["suggestion"] for item in payload}
    assert "aws-detailed.md" in suggestions
    assert None in suggestions


def test_main_json_exit_code_2_when_broken(
    write_guide: WriteGuide,
) -> None:
    """``--json`` mode still exits 2 on broken links."""
    write_guide("aws.md", "[Missing](missing.md)\n")
    assert gx.main(["--json"]) == 2


def test_main_json_exit_code_0_when_clean(write_guide: WriteGuide) -> None:
    """``--json`` mode exits 0 when nothing is broken."""
    write_guide("aws.md", "body")
    assert gx.main(["--json"]) == 0


def test_main_json_does_not_print_human_header(
    write_guide: WriteGuide, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--json`` mode does NOT print the ``Guide cross-reference audit`` banner."""
    write_guide("aws.md", "body")
    assert gx.main(["--json"]) == 0
    captured = capsys.readouterr()
    assert "Guide cross-reference audit" not in captured.out


def test_main_json_payload_has_canonical_field_order(
    write_guide: WriteGuide, capsys: pytest.CaptureFixture[str]
) -> None:
    """JSON payload keys are exactly ``source``, ``target``, ``suggestion``."""
    write_guide("aws.md", "[Missing](missing.md)\n")
    assert gx.main(["--json"]) == 2
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert len(payload) == 1
    assert set(payload[0].keys()) == {"source", "target", "suggestion"}
