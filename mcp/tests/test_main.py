"""Tests for ``splunk_uc_mcp.__main__`` — the CLI entry point.

The entry point is invoked two ways: ``python -m splunk_uc_mcp`` and the
``splunk-uc-mcp`` console script (both routed through :func:`main`). We
cannot exercise the real stdio loop in unit tests — that would block
on stdin — so every test here stubs out
:func:`splunk_uc_mcp.server.run_stdio_server` and asserts that
:func:`main` parsed CLI flags + env vars into the right keyword
arguments before delegation. Together with the existing
``test_server.py`` integration suite, this gives the CLI a
hermetically tested surface: argparse routing, logging setup,
env-var fallbacks, and the KeyboardInterrupt clean-shutdown contract.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import pytest

from splunk_uc_mcp import __main__ as cli
from splunk_uc_mcp import __version__


# --------------------------------------------------------------------- #
# _configure_logging
# --------------------------------------------------------------------- #


def test_configure_logging_passes_info_level_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``verbose=False`` must invoke ``basicConfig`` with ``INFO``. We
    cannot read the root logger's level after the call because
    pytest's own logging plugin (or an earlier test in the same
    process) may have configured handlers, in which case
    ``basicConfig`` is a no-op. Spy on the call instead — that's the
    contract that matters for production startup."""

    captured: list[dict[str, object]] = []

    def _spy(**kwargs: object) -> None:
        captured.append(kwargs)

    monkeypatch.setattr(logging, "basicConfig", _spy)
    cli._configure_logging(verbose=False)
    assert len(captured) == 1
    assert captured[0]["level"] == logging.INFO
    assert captured[0]["stream"] is sys.stderr


def test_configure_logging_passes_debug_level_when_verbose(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``--verbose`` / ``-v`` must invoke ``basicConfig`` with
    ``DEBUG`` so operators can trace tool dispatch and arg-hash
    lines. Same spy pattern as the INFO test — root-logger state is
    unreliable inside a pytest process."""

    captured: list[dict[str, object]] = []

    def _spy(**kwargs: object) -> None:
        captured.append(kwargs)

    monkeypatch.setattr(logging, "basicConfig", _spy)
    cli._configure_logging(verbose=True)
    assert len(captured) == 1
    assert captured[0]["level"] == logging.DEBUG


def test_configure_logging_routes_to_stderr_with_structured_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pin the two production-critical formatter contracts together
    so a future refactor that flips them to stdout or strips the
    timestamp/level prefix breaks immediately. JSON-RPC traffic uses
    stdout; logs MUST stay on stderr."""

    captured: list[dict[str, object]] = []
    monkeypatch.setattr(
        logging, "basicConfig", lambda **kw: captured.append(kw)
    )
    cli._configure_logging(verbose=False)
    assert captured[0]["stream"] is sys.stderr
    fmt = captured[0]["format"]
    assert "%(asctime)s" in fmt  # type: ignore[operator]
    assert "%(levelname)" in fmt  # type: ignore[operator]
    assert "%(name)s" in fmt  # type: ignore[operator]
    assert "%(message)s" in fmt  # type: ignore[operator]


# --------------------------------------------------------------------- #
# _build_parser
# --------------------------------------------------------------------- #


def test_parser_accepts_all_supported_flags() -> None:
    """Smoke-test the four documented flags. We do NOT assert specific
    default values beyond ``None`` because env-var fallback happens in
    :func:`main`, not the parser — keeping the boundary clean."""

    parser = cli._build_parser()
    args = parser.parse_args(
        [
            "--catalog-root",
            "/tmp/somewhere",
            "--base-url",
            "https://example.com/uc",
            "--verbose",
        ]
    )
    assert args.catalog_root == Path("/tmp/somewhere")
    assert args.base_url == "https://example.com/uc"
    assert args.verbose is True


def test_parser_defaults_are_none() -> None:
    """When nothing is passed, every optional flag must be ``None`` /
    ``False`` so :func:`main` can apply env-var fallbacks cleanly."""

    parser = cli._build_parser()
    args = parser.parse_args([])
    assert args.catalog_root is None
    assert args.base_url is None
    assert args.verbose is False


def test_parser_short_verbose_flag() -> None:
    """``-v`` must alias to ``--verbose`` so the CLI is concise."""

    parser = cli._build_parser()
    args = parser.parse_args(["-v"])
    assert args.verbose is True


def test_parser_version_action_exits_zero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--version`` must print the canonical version string and exit
    with status 0 — argparse uses ``SystemExit`` for version actions.
    The output is what users see in their shell."""

    parser = cli._build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--version"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    # argparse writes --version output to stdout, not stderr.
    assert __version__ in captured.out
    assert "splunk-uc-mcp" in captured.out


# --------------------------------------------------------------------- #
# _version_string
# --------------------------------------------------------------------- #


def test_version_string_includes_prog_name_and_pep440_version() -> None:
    """The version string is what argparse prints for ``--version``; it
    must be stable so downstream wrappers can parse it."""

    out = cli._version_string()
    assert out.startswith("splunk-uc-mcp ")
    assert __version__ in out


# --------------------------------------------------------------------- #
# main — happy path + flag plumbing
# --------------------------------------------------------------------- #


def _stub_run_stdio_server(
    *,
    monkeypatch: pytest.MonkeyPatch,
    raise_keyboard_interrupt: bool = False,
    return_code: int = 0,
) -> dict[str, Any]:
    """Install a stub :func:`run_stdio_server` and return a capture dict.

    The stub records the keyword arguments it received so each test can
    assert on the exact (catalog_root, base_url) tuple :func:`main`
    constructed from the CLI + env-var inputs.
    """

    captured: dict[str, Any] = {}

    def _stub(*, catalog_root: Path | None, base_url: str | None) -> int:
        captured["catalog_root"] = catalog_root
        captured["base_url"] = base_url
        if raise_keyboard_interrupt:
            raise KeyboardInterrupt
        return return_code

    # Patch the function on the server module — main() imports it lazily
    # inside the function body so we need to patch it at the source.
    import splunk_uc_mcp.server as server_module

    monkeypatch.setattr(server_module, "run_stdio_server", _stub)
    return captured


def test_main_passes_explicit_catalog_root_and_base_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the CLI provides both flags, the env vars must not override
    them — explicit args always win."""

    captured = _stub_run_stdio_server(monkeypatch=monkeypatch)
    monkeypatch.setenv("SPLUNK_UC_CATALOG_ROOT", "/should/not/be/used")
    monkeypatch.setenv("SPLUNK_UC_BASE_URL", "https://wrong.example.com")

    rc = cli.main(
        [
            "--catalog-root",
            "/explicit/path",
            "--base-url",
            "https://explicit.example.com/uc",
        ]
    )
    assert rc == 0
    assert captured["catalog_root"] == Path("/explicit/path")
    assert captured["base_url"] == "https://explicit.example.com/uc"


def test_main_falls_back_to_env_vars_when_flags_omitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When neither flag is passed, ``SPLUNK_UC_CATALOG_ROOT`` /
    ``SPLUNK_UC_BASE_URL`` env vars supply the defaults."""

    captured = _stub_run_stdio_server(monkeypatch=monkeypatch)
    monkeypatch.setenv("SPLUNK_UC_CATALOG_ROOT", "/from/env")
    monkeypatch.setenv("SPLUNK_UC_BASE_URL", "https://env.example.com/uc")

    rc = cli.main([])
    assert rc == 0
    assert captured["catalog_root"] == Path("/from/env")
    assert captured["base_url"] == "https://env.example.com/uc"


def test_main_passes_none_when_neither_flag_nor_env_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without flags or env vars, ``main`` must hand the server ``None``
    so :class:`Catalog` falls back to its own discovery rules (cwd or
    hosted mirror)."""

    captured = _stub_run_stdio_server(monkeypatch=monkeypatch)
    monkeypatch.delenv("SPLUNK_UC_CATALOG_ROOT", raising=False)
    monkeypatch.delenv("SPLUNK_UC_BASE_URL", raising=False)

    rc = cli.main([])
    assert rc == 0
    assert captured["catalog_root"] is None
    assert captured["base_url"] is None


def test_main_only_catalog_root_env_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Independent env vars: only ``SPLUNK_UC_CATALOG_ROOT`` set, base
    URL falls back to ``None`` (which lets Catalog pick its default
    GitHub Pages mirror)."""

    captured = _stub_run_stdio_server(monkeypatch=monkeypatch)
    monkeypatch.setenv("SPLUNK_UC_CATALOG_ROOT", "/just/the/root")
    monkeypatch.delenv("SPLUNK_UC_BASE_URL", raising=False)

    rc = cli.main([])
    assert rc == 0
    assert captured["catalog_root"] == Path("/just/the/root")
    assert captured["base_url"] is None


def test_main_only_base_url_env_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """Independent env vars: only ``SPLUNK_UC_BASE_URL`` set, catalog
    root falls back to ``None``."""

    captured = _stub_run_stdio_server(monkeypatch=monkeypatch)
    monkeypatch.delenv("SPLUNK_UC_CATALOG_ROOT", raising=False)
    monkeypatch.setenv("SPLUNK_UC_BASE_URL", "https://just-url.example.com")

    rc = cli.main([])
    assert rc == 0
    assert captured["catalog_root"] is None
    assert captured["base_url"] == "https://just-url.example.com"


def test_main_passes_verbose_through_logging_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``--verbose`` flips logging to DEBUG before the server starts;
    we verify the flag was honoured by hooking ``_configure_logging``
    via monkeypatch and asserting it was called with True."""

    captured_verbose: list[bool] = []

    def _spy(verbose: bool) -> None:
        captured_verbose.append(verbose)

    monkeypatch.setattr(cli, "_configure_logging", _spy)
    _stub_run_stdio_server(monkeypatch=monkeypatch)
    monkeypatch.delenv("SPLUNK_UC_CATALOG_ROOT", raising=False)
    monkeypatch.delenv("SPLUNK_UC_BASE_URL", raising=False)

    rc = cli.main(["--verbose"])
    assert rc == 0
    assert captured_verbose == [True]


def test_main_returns_zero_on_keyboard_interrupt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the user hits Ctrl+C inside the stdio loop, ``main`` must
    swallow the KeyboardInterrupt and exit 0 — anything else would
    propagate into the shell as a non-zero exit and break orchestration
    contracts (e.g., the ``splunk-uc-mcp`` console script run by
    ``claude mcp add ...``)."""

    _stub_run_stdio_server(
        monkeypatch=monkeypatch, raise_keyboard_interrupt=True
    )
    monkeypatch.delenv("SPLUNK_UC_CATALOG_ROOT", raising=False)
    monkeypatch.delenv("SPLUNK_UC_BASE_URL", raising=False)

    rc = cli.main([])
    assert rc == 0


def test_main_propagates_nonzero_exit_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the stdio loop returns a non-zero code (today only 0 is
    possible, but the contract leaves the door open for future error
    paths), ``main`` must surface it verbatim so the shell sees the
    failure."""

    _stub_run_stdio_server(monkeypatch=monkeypatch, return_code=42)
    monkeypatch.delenv("SPLUNK_UC_CATALOG_ROOT", raising=False)
    monkeypatch.delenv("SPLUNK_UC_BASE_URL", raising=False)

    rc = cli.main([])
    assert rc == 42


def test_main_uses_sys_argv_when_argv_is_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``main(argv=None)`` is the production entry — it must fall back
    to ``sys.argv[1:]``. Pin the contract by stubbing sys.argv and
    confirming the parser saw the env-supplied catalog root flow
    through, rather than crashing on missing positional args."""

    captured = _stub_run_stdio_server(monkeypatch=monkeypatch)
    monkeypatch.setattr(sys, "argv", ["splunk-uc-mcp"])
    monkeypatch.delenv("SPLUNK_UC_CATALOG_ROOT", raising=False)
    monkeypatch.delenv("SPLUNK_UC_BASE_URL", raising=False)

    rc = cli.main(None)
    assert rc == 0
    # No flags, no env — both kwargs come through as None.
    assert captured == {"catalog_root": None, "base_url": None}
