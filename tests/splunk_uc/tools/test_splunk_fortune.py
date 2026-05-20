"""Hermetic coverage suite for ``splunk_uc.tools.splunk_fortune``.

The fortune-cookie CLI is a decorative aid for engineers exploring
the catalog. It has no security or contract surface — but it ships
inside the same ``splunk_uc`` namespace, so any regression to its
loader (e.g., schema drift on ``catalog.json``) silently breaks
``python -m splunk_uc splunk-fortune`` for users.

This suite lifts the module from 18.8% to 100% with no real-FS or
network access. ``random.sample`` is monkeypatched per-test so the
output is deterministic and grep-able.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

import pytest

from splunk_uc.tools import splunk_fortune as sf

# ---------------------------------------------------------------------------
# load_catalog
# ---------------------------------------------------------------------------


class TestLoadCatalog:
    def test_falls_back_when_catalog_missing(self, tmp_path: pathlib.Path) -> None:
        missing = tmp_path / "no-such.json"
        assert sf.load_catalog(missing) is sf.FALLBACK

    def test_flattens_nested_data_blocks(self, tmp_path: pathlib.Path) -> None:
        catalog = tmp_path / "catalog.json"
        catalog.write_text(
            json.dumps(
                {
                    "DATA": [
                        {
                            "s": [
                                {
                                    "n": "Server",
                                    "u": [
                                        {"n": "CPU spike", "c": "high"},
                                        {"n": "Memory leak", "c": "medium"},
                                    ],
                                },
                                {
                                    "n": "Network",
                                    "u": [{"n": "Packet loss", "c": "low"}],
                                },
                            ]
                        },
                        # A second top-level block with an empty 's' should
                        # not contribute any UCs.
                        {"s": []},
                    ]
                }
            ),
            encoding="utf-8",
        )
        flat = sf.load_catalog(catalog)
        assert [u["n"] for u in flat] == ["CPU spike", "Memory leak", "Packet loss"]
        # Every UC must be annotated with its parent category name.
        assert {u["_category"] for u in flat} == {"Server", "Network"}

    def test_returns_fallback_when_flat_list_empty(
        self, tmp_path: pathlib.Path
    ) -> None:
        # Valid catalog shape but no UCs at all → fallback wins.
        catalog = tmp_path / "empty.json"
        catalog.write_text(json.dumps({"DATA": [{"s": [{"n": "X", "u": []}]}]}))
        assert sf.load_catalog(catalog) is sf.FALLBACK


# ---------------------------------------------------------------------------
# fortune_line
# ---------------------------------------------------------------------------


class TestFortuneLine:
    @pytest.mark.parametrize(
        "criticality, emoji",
        [
            ("high", "🔴"),
            ("medium", "🟡"),
            ("low", "🟢"),
            ("anything-else", "⚪"),
        ],
    )
    def test_renders_one_line_with_emoji(
        self, criticality: str, emoji: str
    ) -> None:
        uc = {"c": criticality, "n": "Title", "_category": "Cat"}
        line = sf.fortune_line(uc)
        assert line.startswith(f"{emoji} [{criticality}]")
        assert "Cat" in line
        assert "Title" in line

    def test_explicit_none_critical_renders_unknown_emoji_with_none_bracket(
        self,
    ) -> None:
        # An explicit ``c=None`` keeps the literal None in the bracket
        # because ``dict.get("c", "?")`` only returns the default when
        # the key is absent — not when the value is None.
        line = sf.fortune_line({"c": None, "n": "Title", "_category": "Cat"})
        assert line.startswith("⚪ [None]")

    def test_handles_missing_fields_with_sane_defaults(self) -> None:
        line = sf.fortune_line({})
        assert "Untitled" in line
        assert "[?]" in line


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _stub_random_sample(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make ``random.sample`` deterministic — always return the prefix.

    This keeps the CLI output byte-stable across test runs and removes
    the only source of non-determinism in the module.
    """
    monkeypatch.setattr(sf.random, "sample", lambda seq, k: list(seq)[:k])


def _seed_catalog(path: pathlib.Path, *ucs: dict[str, Any]) -> None:
    path.write_text(
        json.dumps({"DATA": [{"s": [{"n": "Server", "u": list(ucs)}]}]}),
        encoding="utf-8",
    )


class TestMain:
    def test_prints_cookie_and_one_fortune_by_default(
        self,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        catalog = tmp_path / "catalog.json"
        _seed_catalog(
            catalog,
            {"n": "CPU spike", "c": "high", "v": "CPU > 90%", "q": "search index=cpu"},
        )
        rc = sf.main(["--catalog", str(catalog)])
        assert rc == 0
        out = capsys.readouterr().out
        # Cookie ASCII header
        assert "SPLunk" in out
        # Fortune
        assert "CPU spike" in out
        # SPL sample header (because q is non-empty)
        assert "── sample SPL ──" in out
        # Closing benediction
        assert "May your pipelines" in out

    def test_count_three_picks_three(
        self,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        catalog = tmp_path / "catalog.json"
        _seed_catalog(
            catalog,
            {"n": "A", "c": "high", "v": "a", "q": ""},
            {"n": "B", "c": "medium", "v": "b", "q": ""},
            {"n": "C", "c": "low", "v": "c", "q": ""},
            {"n": "D", "c": "low", "v": "d", "q": ""},
        )
        rc = sf.main(["--count", "3", "--catalog", str(catalog)])
        assert rc == 0
        out = capsys.readouterr().out
        # First three only (random.sample is stubbed to return the prefix).
        assert "A" in out and "B" in out and "C" in out
        assert "D" not in out

    def test_truncates_long_value_with_ellipsis(
        self,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        long_value = "x" * 250
        catalog = tmp_path / "catalog.json"
        _seed_catalog(
            catalog, {"n": "Long", "c": "high", "v": long_value, "q": ""}
        )
        rc = sf.main(["--catalog", str(catalog)])
        assert rc == 0
        out = capsys.readouterr().out
        # 200 chars of 'x' then ellipsis.
        assert ("x" * 200) in out
        assert "…" in out

    def test_truncates_multi_line_spl_with_ellipsis(
        self,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # 10 pipe stages -> only first 8 printed + trailing ellipsis.
        spl = "\n".join(f"| stage{i}" for i in range(10))
        catalog = tmp_path / "catalog.json"
        _seed_catalog(
            catalog, {"n": "BigSPL", "c": "high", "v": "v", "q": spl}
        )
        rc = sf.main(["--catalog", str(catalog)])
        assert rc == 0
        out = capsys.readouterr().out
        for i in range(8):
            assert f"stage{i}" in out
        # The 9th and 10th stages are suppressed; ellipsis line replaces them.
        assert "stage9" not in out
        assert "…" in out

    def test_omits_spl_block_when_query_empty(
        self,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        catalog = tmp_path / "catalog.json"
        _seed_catalog(catalog, {"n": "Quiet", "c": "low", "v": "v", "q": ""})
        rc = sf.main(["--catalog", str(catalog)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "── sample SPL ──" not in out

    def test_short_spl_no_truncation_marker(
        self,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # 5 lines (< 8 cap) → no trailing ellipsis after the SPL block.
        spl = "\n".join(f"| stage{i}" for i in range(5))
        catalog = tmp_path / "catalog.json"
        _seed_catalog(
            catalog, {"n": "ShortSPL", "c": "high", "v": "v", "q": spl}
        )
        rc = sf.main(["--catalog", str(catalog)])
        assert rc == 0
        out = capsys.readouterr().out
        for i in range(5):
            assert f"stage{i}" in out

    def test_falls_back_when_catalog_missing(
        self,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc = sf.main(["--catalog", str(tmp_path / "no-such.json")])
        assert rc == 0
        out = capsys.readouterr().out
        # FALLBACK has one UC titled "Emergency SPL"
        assert "Emergency SPL" in out
