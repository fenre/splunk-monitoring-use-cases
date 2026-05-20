"""Smoke + reload tests for the top-level ``splunk_uc`` package.

The package's ``__init__`` reads ``VERSION`` at the repo root. Two
branches are worth pinning:

1. The happy path: ``splunk_uc.__version__`` is a non-empty string
   read from ``VERSION``.
2. The fallback path: when the VERSION file cannot be read (sdist
   without VERSION, broken filesystem, encoding error), the package
   import still succeeds and ``__version__`` falls back to
   ``"0.0.0+unknown"``.

The second case is exercised by reloading the package with a stubbed
``Path.read_text`` that raises ``OSError`` — this is the canonical
contract documented in the source comment "package can be imported
even from a sdist that omits VERSION".
"""

from __future__ import annotations

import importlib

import pytest

import splunk_uc


def test_version_is_populated_from_repo_version_file() -> None:
    """Happy path: the imported package surfaces a non-empty version
    string. We deliberately do NOT pin the exact value (it drifts
    with every release) — only the contract that *something* is set."""
    assert isinstance(splunk_uc.__version__, str)
    assert len(splunk_uc.__version__) > 0


def test_version_falls_back_when_version_file_is_unreadable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If reading VERSION raises OSError or UnicodeDecodeError, the
    package MUST still import successfully and fall back to the
    documented ``"0.0.0+unknown"`` sentinel. Pin this so a future
    refactor of the version-read block cannot accidentally start
    crashing the import."""
    import pathlib as _pathlib

    real_read_text = _pathlib.Path.read_text

    def _explode(self: _pathlib.Path, *args: object, **kwargs: object) -> str:
        # Only fail for the VERSION lookup; other read_text() calls
        # in the same reload (e.g. site initialisation) stay live.
        if self.name == "VERSION":
            raise OSError("simulated missing VERSION")
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(_pathlib.Path, "read_text", _explode)
    reloaded = importlib.reload(splunk_uc)
    try:
        assert reloaded.__version__ == "0.0.0+unknown"
    finally:
        # Restore the patch and reload again so subsequent tests see
        # the real version string. Without this the test pollutes the
        # module cache for the rest of the session.
        monkeypatch.undo()
        importlib.reload(splunk_uc)


def test_all_export_contract() -> None:
    """``__all__`` is a stable surface contract for `from splunk_uc
    import *`. Pin the current shape so adding a new symbol is a
    conscious decision."""
    assert splunk_uc.__all__ == ["__version__"]
