"""Unit tests for the retired ``splunk_uc.generators.md_from_json`` stub.

The module was reduced to a no-op stub on 2026-05-18 (F21 close) when
the 7,929 ``content/cat-*/UC-*.md`` companions were deleted from the
repo. The per-UC markdown twin is now emitted only at build time by
``tools/build/templates/uc.py::render_markdown_twin``. The stub is
retained so out-of-tree callers don't crash with
``ModuleNotFoundError`` and so the coverage-baseline entry stays
valid.

These tests pin two things:

* Calling ``main()`` prints the retirement notice to ``stderr`` and
  returns exit code 2 (non-zero) so any orchestration that still
  invokes the module breaks loudly rather than silently producing
  stale files.
* The module-level ``_RETIRED_MSG`` constant names the replacement
  pipeline so anyone reading the stderr output can follow the
  trail.
"""

from __future__ import annotations

import pytest

from splunk_uc.generators import md_from_json as M


class TestRetiredMessage:
    def test_message_mentions_retirement_date(self) -> None:
        assert "2026-05-18" in M._RETIRED_MSG

    def test_message_mentions_f21(self) -> None:
        assert "F21" in M._RETIRED_MSG

    def test_message_points_to_replacement_pipeline(self) -> None:
        assert "render_markdown_twin" in M._RETIRED_MSG
        assert "dist/uc/UC-X.Y.Z/uc.md" in M._RETIRED_MSG


class TestMainStub:
    def test_main_returns_2(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = M.main()
        assert rc == 2

    def test_main_prints_to_stderr(self, capsys: pytest.CaptureFixture[str]) -> None:
        M.main()
        captured = capsys.readouterr()
        assert M._RETIRED_MSG in captured.err
        assert captured.out == ""

    def test_main_ignores_argv(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Stub deliberately ignores argv (no argparse).
        rc = M.main(["--something", "--else"])
        assert rc == 2
