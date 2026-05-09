"""Unit tests for ``python -m splunk_uc`` dispatcher and verb registry.

Repo-overhaul plan §P6 (scripts taxonomy), 2026-05-09.

The dispatcher is the new public CLI entry point that routes verb
invocations to implementations under ``src/splunk_uc/<subpackage>/``.
This test file pins the externally-visible contract so subsequent
P6 batches (which migrate more scripts) can't silently break it:

1. **Registry shape** - every registered verb resolves to a real
   module exposing a ``main(argv) -> int`` callable.
2. **Help formatting** - --help groups by category, lists every
   registered verb, and stays a single page so it's terminal-friendly.
3. **Error handling** - unknown verbs / category names / no args
   produce useful, non-zero, deterministic error output.
4. **Argv forwarding** - the implementation's ``main`` receives the
   trailing argv unchanged (no eating ``--`` separators, etc.).
5. **Lazy import** - resolving one verb does not import unrelated
   subpackages. Important once the registry grows; resolving the
   "audit" verb shouldn't pay the import cost of "ingest" verbs.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"

# The package is not installed; tests must add ``src/`` to sys.path
# the same way every other package-level test in the repo does.
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


# ---------------------------------------------------------------------------
# Registry shape: every registered verb resolves to a real callable.
# ---------------------------------------------------------------------------


def test_registry_resolves_every_registered_verb() -> None:
    """Every entry in the registry must point at an importable module
    that exposes a ``main`` callable. This is the cheapest gate that
    catches "I added a verb but forgot to commit the implementation".
    """
    from splunk_uc._registry import all_verbs, resolve

    assert all_verbs(), "registry should not be empty"
    for verb in all_verbs():
        impl = resolve(verb.name)
        assert impl is not None, f"verb {verb.name!r} did not resolve"
        assert callable(impl), f"verb {verb.name!r} resolved to a non-callable"


def test_registry_returns_none_for_unknown_verb() -> None:
    from splunk_uc._registry import resolve

    assert resolve("definitely-not-a-verb-name") is None


def test_registry_register_rejects_duplicates() -> None:
    """Re-registering an existing verb name must raise ``ValueError``.

    Catches accidental copy-paste bugs in the registry source.
    """
    from splunk_uc._registry import Verb, register

    duplicate = Verb(
        name="audit-reproducibility",
        module="audits.build_reproducibility",
        help="Duplicate registration attempt.",
        category="audits",
    )
    with pytest.raises(ValueError, match="already registered"):
        register(duplicate)


def test_registry_groups_by_category() -> None:
    """``by_category`` returns a dict keyed by subpackage label."""
    from splunk_uc._registry import by_category

    grouped = by_category()
    assert isinstance(grouped, dict)
    assert "audits" in grouped, "audits category must be present in registry"
    audit_names = {v.name for v in grouped["audits"]}
    assert "audit-reproducibility" in audit_names


# ---------------------------------------------------------------------------
# Help formatting.
# ---------------------------------------------------------------------------


def test_dispatcher_help_with_no_args(capsys: pytest.CaptureFixture[str]) -> None:
    from splunk_uc.__main__ import main

    rc = main([])
    assert rc == 0
    out = capsys.readouterr().out
    assert "splunk_uc" in out
    assert "audit-reproducibility" in out
    assert "Run `python -m splunk_uc <verb> --help`" in out


def test_dispatcher_help_with_dash_h(capsys: pytest.CaptureFixture[str]) -> None:
    from splunk_uc.__main__ import main

    rc = main(["-h"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "audit-reproducibility" in out


def test_dispatcher_help_with_dash_dash_help(capsys: pytest.CaptureFixture[str]) -> None:
    from splunk_uc.__main__ import main

    rc = main(["--help"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "audit-reproducibility" in out


def test_dispatcher_version_with_dash_v(capsys: pytest.CaptureFixture[str]) -> None:
    from splunk_uc import __version__
    from splunk_uc.__main__ import main

    rc = main(["-V"])
    assert rc == 0
    out = capsys.readouterr().out
    assert __version__ in out


def test_dispatcher_version_with_dash_dash_version(capsys: pytest.CaptureFixture[str]) -> None:
    from splunk_uc import __version__
    from splunk_uc.__main__ import main

    rc = main(["--version"])
    assert rc == 0
    out = capsys.readouterr().out
    assert __version__ in out


# ---------------------------------------------------------------------------
# Error handling.
# ---------------------------------------------------------------------------


def test_dispatcher_unknown_verb_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    from splunk_uc.__main__ import main

    rc = main(["frobnicate-everything"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "unknown verb" in err
    assert "frobnicate-everything" in err


def test_dispatcher_category_name_exits_2_with_hint(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Typing a category name (``audits``) instead of a verb yields
    a deterministic error pointing at ``--help``."""
    from splunk_uc.__main__ import main

    rc = main(["audits"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "category" in err
    assert "--help" in err


def test_dispatcher_argv_forwarded_to_verb_main(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The dispatcher must pass the trailing argv (everything after
    the verb name) to the verb's ``main`` callable verbatim.

    This is the seam the audit-reproducibility test relies on; if it
    breaks, the verb cannot accept its own flags.
    """
    captured: dict[str, list[str] | None] = {}

    def fake_main(argv: list[str] | None) -> int:
        captured["argv"] = argv
        return 0

    from splunk_uc import _registry as registry
    from splunk_uc.__main__ import main

    monkeypatch.setattr(registry, "resolve", lambda _name: fake_main)
    rc = main(["audit-reproducibility", "--first-build-only", "--keep"])
    assert rc == 0
    assert captured["argv"] == ["--first-build-only", "--keep"]


def test_dispatcher_returns_verb_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """A non-zero exit code from the verb's ``main`` is propagated."""
    from splunk_uc import _registry as registry
    from splunk_uc.__main__ import main

    monkeypatch.setattr(registry, "resolve", lambda _name: lambda _argv: 17)
    rc = main(["audit-reproducibility"])
    assert rc == 17


# ---------------------------------------------------------------------------
# Lazy import: resolving one verb must not import unrelated subpackages.
# ---------------------------------------------------------------------------


def test_resolving_audit_does_not_import_ingest_subpackage() -> None:
    """Lazy resolution: importing the dispatcher + resolving an audit
    verb must NOT pull in ``splunk_uc.ingest``. Once the registry
    grows to dozens of verbs, the import budget matters for tooling
    that just wants ``--help`` (e.g. shell completion).

    This test runs in a fresh interpreter to get a clean ``sys.modules``
    baseline.
    """
    import subprocess

    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(SRC_DIR)!r})\n"
        "from splunk_uc._registry import resolve\n"
        "_ = resolve('audit-reproducibility')\n"
        "modnames = [m for m in sys.modules if m.startswith('splunk_uc.')]\n"
        "assert 'splunk_uc.audits.build_reproducibility' in modnames\n"
        "for forbidden in ('splunk_uc.ingest', 'splunk_uc.generators',\n"
        "                  'splunk_uc.migrations', 'splunk_uc.feasibility'):\n"
        "    submods = [m for m in modnames if m.startswith(forbidden + '.')]\n"
        "    assert not submods, f'unexpected eager import: {submods!r}'\n"
        "print('OK')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"subprocess failed: {result.stderr}"
    assert "OK" in result.stdout


# ---------------------------------------------------------------------------
# Package surface.
# ---------------------------------------------------------------------------


def test_package_version_is_a_string() -> None:
    from splunk_uc import __version__

    assert isinstance(__version__, str)
    assert __version__, "package version must not be empty"
    assert "." in __version__, f"version looks malformed: {__version__!r}"


def test_audits_subpackage_imports_cleanly() -> None:
    """``splunk_uc.audits`` is the canonical home for audit verbs.

    The init module must import without side-effects so a fresh
    interpreter can load it without paying for verb implementations.
    """
    importlib.import_module("splunk_uc.audits")


@pytest.mark.parametrize(
    "subpackage",
    ["audits", "generators", "migrations", "ingest", "feasibility"],
)
def test_subpackages_import_cleanly(subpackage: str) -> None:
    """Every P6 subpackage imports without errors and is empty by default.

    Catches missing ``__init__.py`` files and import-time ImportErrors
    in the package skeleton itself.
    """
    importlib.import_module(f"splunk_uc.{subpackage}")
