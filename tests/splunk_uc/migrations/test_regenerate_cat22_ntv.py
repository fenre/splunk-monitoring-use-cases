"""Hermetic coverage suite for ``splunk_uc.migrations.regenerate_cat22_ntv``.

Brings coverage from 24.5% to 100%.

The driver re-renders the ``"22": { ... }`` block in
``non-technical-view.js``. Tests redirect ``REPO_ROOT`` / ``JS_PATH``
via ``monkeypatch`` and build a synthetic JS file containing a known
cat-22 block so the splicing logic can be exercised without touching
the live (multi-thousand-line) file.
"""

from __future__ import annotations

import pathlib

import pytest

from splunk_uc.migrations import regenerate_cat22_ntv as rc

# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_repo(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> pathlib.Path:
    """Hermetic repo with a JS file that has the expected block markers.

    ``rewrite_file`` and ``check_file`` bind ``JS_PATH`` as a default
    argument at import time, so monkey-patching the module-level
    constant alone is not enough — the default argument still points at
    the real file. We rebind the functions through tiny shims so the
    ``main`` entry-point (which calls them with zero args) hits the
    temp path too.
    """
    js_path = tmp_path / "non-technical-view.js"
    monkeypatch.setattr(rc, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(rc, "JS_PATH", js_path)

    orig_rewrite = rc.rewrite_file
    orig_check = rc.check_file

    def patched_rewrite(p: pathlib.Path | None = None) -> str:
        return orig_rewrite(p or rc.JS_PATH)

    def patched_check(p: pathlib.Path | None = None) -> bool:
        return orig_check(p or rc.JS_PATH)

    monkeypatch.setattr(rc, "rewrite_file", patched_rewrite)
    monkeypatch.setattr(rc, "check_file", patched_check)
    return tmp_path


def _stub_js(js_path: pathlib.Path, cat22_body: str = "OLD_BODY\n") -> None:
    """Write a synthetic JS file whose ``"22": {`` and ``"23": {``
    block headers are byte-identical to the generator's BLOCK_START /
    NEXT_BLOCK_START constants (which both end with ``{\n``)."""
    js_path.write_text(
        "// header\n"
        '  "21": { },\n'
        f'  "22": {{\n{cat22_body}  }},\n'
        '  "23": {\n'
        "    placeholder: 1,\n"
        "  },\n"
        "// footer\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


class TestJsString:
    def test_escapes_every_special_char(self) -> None:
        out = rc._js_string('hello\\world"\nthere\rstop\t!')
        # Quoted on both ends.
        assert out.startswith('"') and out.endswith('"')
        # Backslash → ``\\``
        assert "\\\\" in out
        # Double-quote → ``\"``
        assert '\\"' in out
        # Newline → ``\n`` (literal backslash + n)
        assert "\\n" in out
        # CR → ``\r``
        assert "\\r" in out
        # Tab → ``\t``
        assert "\\t" in out

    def test_plain_text_round_trip(self) -> None:
        # Plain ASCII passes through verbatim, only wrapped in quotes.
        assert rc._js_string("hello") == '"hello"'

    def test_unicode_passes_through_unescaped(self) -> None:
        # UTF-8 chars left as-is by design.
        assert rc._js_string("café") == '"café"'

    def test_p_and_ev_helpers_compose_paths(self) -> None:
        assert rc._p("section") == "docs/regulatory-primer.md#section"
        assert rc._ev("gdpr") == "docs/evidence-packs/gdpr.md"


class TestRenderOutcomes:
    def test_appends_commas_between_items(self) -> None:
        out = rc._render_outcomes(["a", "b", "c"])
        # Two commas between three items.
        assert out.count(",\n") == 3  # one per item including trailing ``],``
        # Each outcome appears as a JS string literal.
        for label in ("a", "b", "c"):
            assert f'"{label}"' in out

    def test_single_item_renders_without_trailing_comma_in_body(self) -> None:
        out = rc._render_outcomes(["only"])
        # Body has just ``"only"`` (no trailing comma after it).
        assert '"only"\n' in out
        # The closing ``],`` is still emitted on its own line.
        assert "    ],\n" in out


class TestRenderUc:
    def test_emits_object_with_id_and_why(self) -> None:
        out = rc._render_uc("22.1.1", "Because.")
        assert '{ id: "22.1.1", why: "Because." }' in out
        # Indented at exactly 8 spaces.
        assert out.startswith("        ")


class TestRenderArea:
    def test_renders_complete_area_with_trailing_comma_when_not_last(
        self,
    ) -> None:
        area = {
            "name": "n",
            "description": "d",
            "whatItIs": "w",
            "whoItAffects": "wa",
            "splunkValue": "sv",
            "primer": "docs/primer.md#x",
            "evidencePack": "docs/evidence-packs/e.md",
            "ucs": [("22.1.1", "why")],
        }
        out = rc._render_area(area, is_last=False)
        assert out.endswith(",")
        for snippet in (
            'name: "n"',
            'description: "d"',
            'whatItIs: "w"',
            'whoItAffects: "wa"',
            'splunkValue: "sv"',
            'primer: "docs/primer.md#x"',
            'evidencePack: "docs/evidence-packs/e.md"',
        ):
            assert snippet in out

    def test_renders_minimal_area_without_trailing_comma_when_last(
        self,
    ) -> None:
        # Tier-2/3 areas only have ``name`` + ``description`` + ``ucs``.
        # The conditional ``if area.get(key)`` then skips the four
        # optional fields — pinning the False branch.
        area = {
            "name": "n",
            "description": "d",
            "ucs": [("22.99.1", "y")],
        }
        out = rc._render_area(area, is_last=True)
        # No optional fields in the output.
        for missing in ("whatItIs", "whoItAffects", "splunkValue", "primer"):
            assert missing not in out
        # No trailing comma when ``is_last=True``.
        assert not out.endswith(",")


class TestRenderBlock:
    def test_emits_full_block_starting_with_22_key(self) -> None:
        out = rc.render_block()
        assert out.startswith('  "22": {')
        # Always ends with a trailing comma + newline (so the next
        # block's ``"23":`` slots in cleanly).
        assert out.endswith(",\n")
        # Both ``outcomes`` and ``areas`` sub-blocks present.
        assert "outcomes:" in out
        assert "areas:" in out


# ---------------------------------------------------------------------------
# _locate_block + rewrite_file + check_file
# ---------------------------------------------------------------------------


class TestLocateBlock:
    def test_returns_offsets_of_22_start_and_23_start(self) -> None:
        # BLOCK_START / NEXT_BLOCK_START both end with ``{\n`` so the
        # test fixture must too — otherwise the markers won't match.
        text = '// header\n  "22": {\nbody\n  "23": {\nmore\n  },\n'
        start, end = rc._locate_block(text)
        assert text[start:].startswith('  "22":')
        assert text[end:].startswith('  "23":')

    def test_raises_when_22_block_missing(self) -> None:
        with pytest.raises(ValueError, match='"22" block'):
            rc._locate_block('  "23": { },\n')

    def test_raises_when_23_block_missing(self) -> None:
        # ``"22": {\n`` is present, ``"23": {\n`` is not.
        with pytest.raises(ValueError, match='"23" block'):
            rc._locate_block('  "22": {\nbody\n  // no 23 here\n')


class TestRewriteFile:
    def test_replaces_existing_block_in_place(
        self, fake_repo: pathlib.Path
    ) -> None:
        _stub_js(rc.JS_PATH)
        result = rc.rewrite_file()
        # Returned text matches what was written.
        assert result == rc.JS_PATH.read_text(encoding="utf-8")
        # Old body gone, regenerated content present.
        assert "OLD_BODY" not in result
        # ``"22":`` still anchored, surrounded by header/footer.
        assert '"22": {' in result
        assert "// header" in result
        assert "// footer" in result

    def test_accepts_explicit_path_arg(
        self, tmp_path: pathlib.Path
    ) -> None:
        # Pin the ``js_path = JS_PATH`` default-arg override path.
        custom = tmp_path / "custom.js"
        _stub_js(custom)
        result = rc.rewrite_file(custom)
        assert custom.read_text(encoding="utf-8") == result


class TestCheckFile:
    def test_returns_true_when_file_matches_generator(
        self, fake_repo: pathlib.Path
    ) -> None:
        _stub_js(rc.JS_PATH)
        # Write the generator output into the file so they match.
        rc.rewrite_file()
        assert rc.check_file() is True

    def test_returns_false_on_drift(
        self, fake_repo: pathlib.Path
    ) -> None:
        _stub_js(rc.JS_PATH, cat22_body="STALE_BODY\n")
        assert rc.check_file() is False


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


class TestMain:
    def test_write_mode_rewrites_file_and_returns_0(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _stub_js(rc.JS_PATH)
        assert rc.main([]) == 0
        out = capsys.readouterr().out
        assert "Rewrote cat-22" in out

    def test_check_mode_returns_0_when_clean(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _stub_js(rc.JS_PATH)
        rc.rewrite_file()  # make on-disk match
        assert rc.main(["--check"]) == 0
        assert "up to date" in capsys.readouterr().out

    def test_check_mode_returns_1_on_drift(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _stub_js(rc.JS_PATH, cat22_body="STALE\n")
        assert rc.main(["--check"]) == 1
        err = capsys.readouterr().err
        assert "drift" in err

    def test_accepts_none_argv(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _stub_js(rc.JS_PATH)
        # argv=None makes argparse read sys.argv, so we set a minimal
        # one — anything more would be picked up as a flag.
        monkeypatch.setattr("sys.argv", ["regenerate_cat22_ntv"])
        assert rc.main(None) == 0
