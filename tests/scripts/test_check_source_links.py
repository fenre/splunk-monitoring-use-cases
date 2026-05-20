"""Hermetic unit tests for ``scripts/check_source_links.py``.

The script makes outbound HTTP probes; it is NOT wired into the per-PR
``validate.yml`` (it runs on demand or in a scheduled job). Tests here
mock the urllib opener so we never hit the network.

Coverage targets:
  * ``load_sources`` — flattens nested sections, drops ``_meta``.
  * ``classify`` — status-code → string mapping.
  * ``_request`` — success / redirect / no-Location-redirect /
    HTTPError / URLError (timeout / dns / tls / unknown) /
    generic-Exception / too-many-redirects.
  * ``NoRedirectHandler`` — every ``http_error_30x`` short-circuit.
  * ``probe`` — GET-only host route, HEAD-then-GET fallback on
    403/405/501, bot-blocked re-classification.
  * ``_print_summary`` — empty, populated, dead-list truncation,
    redirected-list truncation.
  * ``_exit_code`` — strict on/off branches.
  * ``main`` — argparse, ``--report`` (with and without status file),
    ``--only`` filter, end-to-end run with mocked ``probe``.
"""
from __future__ import annotations

import importlib.util
import json
import socket
import ssl
import sys
import urllib.error
from http.client import HTTPMessage
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "check_source_links.py"

_spec = importlib.util.spec_from_file_location("check_source_links", SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("check_source_links", _mod)
_spec.loader.exec_module(_mod)
M = _mod


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Re-point LIBRARY_PATH and STATUS_PATH at a temp dir."""
    repo = tmp_path / "repo"
    (repo / "data").mkdir(parents=True)
    monkeypatch.setattr(M, "REPO", repo)
    monkeypatch.setattr(M, "LIBRARY_PATH", repo / "data" / "source-references.json")
    monkeypatch.setattr(M, "STATUS_PATH", repo / "data" / "source-links-status.json")
    return repo


def _write_library(repo: Path, payload: dict[str, Any]) -> None:
    (repo / "data" / "source-references.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# load_sources
# ---------------------------------------------------------------------------


class TestLoadSources:
    def test_flattens_sections_into_id_keyed_map(self, fake_paths: Path) -> None:
        _write_library(
            fake_paths,
            {
                "_meta": {"generatedAt": "2026-01-01"},
                "vendors": {
                    "splunk-itsi": {"url": "https://docs.splunk.com/itsi"},
                    "cisco-meraki": {"url": "https://meraki.cisco.com"},
                },
                "regulations": {
                    "gdpr": {"url": "https://eur-lex.europa.eu/gdpr"},
                },
            },
        )
        out = M.load_sources()
        assert set(out.keys()) == {"splunk-itsi", "cisco-meraki", "gdpr"}
        assert out["splunk-itsi"]["url"] == "https://docs.splunk.com/itsi"
        # Stamped section + id metadata.
        assert out["splunk-itsi"]["_section"] == "vendors"
        assert out["splunk-itsi"]["_id"] == "splunk-itsi"
        assert out["gdpr"]["_section"] == "regulations"

    def test_drops_underscore_meta_sections(self, fake_paths: Path) -> None:
        _write_library(
            fake_paths,
            {
                "_meta": {"x": 1},
                "_internal": {"private": {"url": "https://x.example"}},
                "vendors": {"a": {"url": "https://a.example"}},
            },
        )
        out = M.load_sources()
        assert set(out.keys()) == {"a"}


# ---------------------------------------------------------------------------
# classify
# ---------------------------------------------------------------------------


class TestClassify:
    @pytest.mark.parametrize(
        ("status", "expected"),
        [
            (200, "ok"),
            (201, "ok"),
            (204, "ok"),
            (299, "ok"),
            (300, "redirect"),
            (301, "redirect"),
            (302, "redirect"),
            (399, "redirect"),
            (400, "client_error"),
            (403, "client_error"),
            (404, "client_error"),
            (499, "client_error"),
            (500, "server_error"),
            (502, "server_error"),
            (503, "server_error"),
            (599, "server_error"),
            (100, "unknown_status"),
            (600, "unknown_status"),
            (0, "unknown_status"),
        ],
    )
    def test_classify_buckets_status_codes(self, status: int, expected: str) -> None:
        assert M.classify(status) == expected


# ---------------------------------------------------------------------------
# NoRedirectHandler
# ---------------------------------------------------------------------------


class TestNoRedirectHandler:
    def test_http_error_30x_returns_fp_unchanged(self) -> None:
        """Every ``http_error_30x`` alias must return the response
        body unchanged so ``_request`` can read the Location header
        itself."""
        handler = M.NoRedirectHandler()
        sentinel = object()
        # All five HTTP redirect codes the script registers.
        for code in (301, 302, 303, 307, 308):
            handler_method = getattr(handler, f"http_error_{code}")
            ret = handler_method(None, sentinel, code, "msg", HTTPMessage())
            assert ret is sentinel


# ---------------------------------------------------------------------------
# _request
# ---------------------------------------------------------------------------


class _FakeResponse:
    """Minimal stand-in for a urllib opener response."""

    def __init__(self, status: int, headers: dict[str, str] | None = None) -> None:
        self.status = status
        self.headers = HTTPMessage()
        for k, v in (headers or {}).items():
            self.headers[k] = v

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        pass


class _FakeOpener:
    """Stand-in for ``urllib.request.build_opener(...)``.

    Each ``open()`` call dequeues from the SHARED response queue; if
    an entry is an ``Exception`` instance (or subclass), it's raised
    instead of returned. This lets a single test orchestrate redirect
    chains and error fallbacks deterministically.

    The script's ``_request`` loop calls ``build_opener()`` afresh on
    every redirect iteration, so the queue MUST be shared across all
    opener instances created during one ``_request`` call. We achieve
    that by storing the queue list by reference (no copy).
    """

    def __init__(self, queue: list[Any]) -> None:
        self._queue = queue

    def open(self, req: Any, timeout: float | None = None) -> Any:
        if not self._queue:
            raise AssertionError("Test ran out of mocked responses")
        item = self._queue.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item


def _patch_opener(monkeypatch: pytest.MonkeyPatch, responses: list[Any]) -> None:
    """Install a build_opener replacement that shares one queue across
    every opener it returns. The list is mutated in-place by the fake
    opener's ``open()`` so successive ``_request`` iterations see the
    queue progress as they would with a real network round-trip."""
    queue = list(responses)
    monkeypatch.setattr(
        M.urllib.request, "build_opener", lambda *_: _FakeOpener(queue)
    )


class TestRequest:
    def test_returns_ok_on_200(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_opener(monkeypatch, [_FakeResponse(200)])
        out = M._request("GET", "https://x.example", max_redirects=5)
        assert out["status"] == 200
        assert out["classification"] == "ok"
        assert out["final_url"] == "https://x.example"
        assert out["redirect_chain"] == ["https://x.example"]

    def test_returns_status_when_redirect_has_no_location(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A 3xx without a Location header MUST short-circuit to the
        bare redirect status — guarding the missing-header branch at
        line 133-135."""
        _patch_opener(monkeypatch, [_FakeResponse(301, {})])
        out = M._request("GET", "https://x.example", max_redirects=5)
        assert out["status"] == 301
        assert out["classification"] == "redirect"

    def test_follows_absolute_redirect(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_opener(
            monkeypatch,
            [
                _FakeResponse(301, {"Location": "https://y.example/new"}),
                _FakeResponse(200),
            ],
        )
        out = M._request("GET", "https://x.example", max_redirects=5)
        assert out["classification"] == "ok"
        assert out["final_url"] == "https://y.example/new"
        assert out["redirect_chain"] == [
            "https://x.example",
            "https://y.example/new",
        ]

    def test_resolves_relative_redirect_against_current_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``Location: /new-path`` MUST be resolved against the
        current URL via ``urljoin``."""
        _patch_opener(
            monkeypatch,
            [
                _FakeResponse(302, {"Location": "/new-path"}),
                _FakeResponse(200),
            ],
        )
        out = M._request(
            "GET", "https://x.example/old-path", max_redirects=5
        )
        assert out["final_url"] == "https://x.example/new-path"

    def test_too_many_redirects(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Three redirects with max_redirects=2 → exceeds the loop.
        _patch_opener(
            monkeypatch,
            [
                _FakeResponse(301, {"Location": "https://a.example"}),
                _FakeResponse(301, {"Location": "https://b.example"}),
                _FakeResponse(301, {"Location": "https://c.example"}),
            ],
        )
        out = M._request("GET", "https://start.example", max_redirects=2)
        assert out["classification"] == "too_many_redirects"
        assert out["status"] is None

    def test_http_error_returns_status_and_classification(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # ``HTTPError(..., fp=None)`` allocates an ``addinfourl``
        # object that, on Python 3.14, raises a ``ResourceWarning``
        # via ``_TemporaryFileCloser.__del__`` during GC unless the
        # exception is explicitly closed. The repo enforces
        # ``filterwarnings = ["error"]`` in pyproject.toml which
        # promotes that warning into a test failure on the NEXT test's
        # setup. The ``try/finally err.close()`` pattern (mirroring
        # tests/splunk_uc/audits/test_dashboard_spl.py) drains the
        # finalizer inside this test's scope.
        err = urllib.error.HTTPError(
            url="https://x.example",
            code=404,
            msg="Not Found",
            hdrs=None,  # type: ignore[arg-type]
            fp=None,
        )
        try:
            _patch_opener(monkeypatch, [err])
            out = M._request("GET", "https://x.example", max_redirects=5)
            assert out["status"] == 404
            assert out["classification"] == "client_error"
            assert "error" in out
        finally:
            err.close()

    def test_url_error_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        err = urllib.error.URLError(socket.timeout("read timed out"))
        _patch_opener(monkeypatch, [err])
        out = M._request("GET", "https://x.example", max_redirects=5)
        assert out["status"] is None
        assert out["classification"] == "timeout"

    def test_url_error_dns(self, monkeypatch: pytest.MonkeyPatch) -> None:
        err = urllib.error.URLError(socket.gaierror("nodename nor servname"))
        _patch_opener(monkeypatch, [err])
        out = M._request("GET", "https://nonexistent.example", max_redirects=5)
        assert out["classification"] == "dns"

    def test_url_error_tls(self, monkeypatch: pytest.MonkeyPatch) -> None:
        err = urllib.error.URLError(ssl.SSLError("cert verify failed"))
        _patch_opener(monkeypatch, [err])
        out = M._request("GET", "https://expired.example", max_redirects=5)
        assert out["classification"] == "tls"

    def test_url_error_unknown_reason(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A URLError whose reason isn't timeout / gaierror / SSLError
        falls through to ``unknown_error`` (line 153-154)."""
        err = urllib.error.URLError(ConnectionResetError("Connection reset"))
        _patch_opener(monkeypatch, [err])
        out = M._request("GET", "https://x.example", max_redirects=5)
        assert out["classification"] == "unknown_error"

    def test_generic_exception_fallback(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Any non-urllib exception must be caught and reported with
        ``unknown_error`` classification (line 158-161)."""
        _patch_opener(monkeypatch, [RuntimeError("opener exploded")])
        out = M._request("GET", "https://x.example", max_redirects=5)
        assert out["classification"] == "unknown_error"
        assert "error" in out


# ---------------------------------------------------------------------------
# probe
# ---------------------------------------------------------------------------


class TestProbe:
    def test_get_only_host_skips_head(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A host listed in ``GET_ONLY_HOSTS`` must be probed with GET
        directly — no HEAD attempt."""
        calls: list[str] = []

        def fake_request(method: str, url: str, max_redirects: int) -> dict:
            calls.append(method)
            return {"status": 200, "classification": "ok", "final_url": url}

        monkeypatch.setattr(M, "_request", fake_request)
        result = M.probe("https://csrc.nist.gov/some-doc")
        assert calls == ["GET"]
        assert result["classification"] == "ok"

    def test_head_then_get_fallback_on_403(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When HEAD returns 403/405/501, ``probe`` retries with GET."""
        sequence = [
            {"status": 403, "classification": "client_error", "final_url": "x"},
            {"status": 200, "classification": "ok", "final_url": "x"},
        ]

        def fake_request(method: str, url: str, max_redirects: int) -> dict:
            return sequence.pop(0)

        monkeypatch.setattr(M, "_request", fake_request)
        result = M.probe("https://docs.example.com/page")
        assert result["classification"] == "ok"

    @pytest.mark.parametrize("fallback_status", [405, 501])
    def test_head_then_get_fallback_on_405_and_501(
        self, monkeypatch: pytest.MonkeyPatch, fallback_status: int
    ) -> None:
        """The fallback also fires on 405 (Method Not Allowed) and
        501 (Not Implemented)."""
        sequence = [
            {"status": fallback_status, "classification": "client_error",
             "final_url": "x"},
            {"status": 200, "classification": "ok", "final_url": "x"},
        ]
        monkeypatch.setattr(
            M, "_request", lambda *_args, **_kw: sequence.pop(0)
        )
        result = M.probe("https://example.com")
        assert result["classification"] == "ok"

    def test_returns_first_ok_without_fallback(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If HEAD already returns 200 we MUST NOT try GET."""
        calls: list[str] = []

        def fake_request(method: str, url: str, max_redirects: int) -> dict:
            calls.append(method)
            return {"status": 200, "classification": "ok", "final_url": url}

        monkeypatch.setattr(M, "_request", fake_request)
        M.probe("https://example.com")
        assert calls == ["HEAD"]

    def test_returns_non_fallback_status_on_first_attempt(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A 404 (not in {403,405,501}) breaks the loop on first
        iteration — pin the ``break`` at line 189."""
        calls: list[str] = []

        def fake_request(method: str, url: str, max_redirects: int) -> dict:
            calls.append(method)
            return {"status": 404, "classification": "client_error",
                    "final_url": url}

        monkeypatch.setattr(M, "_request", fake_request)
        result = M.probe("https://example.com")
        assert calls == ["HEAD"]
        assert result["status"] == 404

    def test_bot_blocked_host_403_reclassified(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Hosts in ``BOT_BLOCKED_HOSTS`` that return 403 across HEAD
        and GET MUST be re-classified as ``bot_blocked`` to keep them
        out of the dead-link list."""
        sequence = [
            {"status": 403, "classification": "client_error",
             "final_url": "x"},
            {"status": 403, "classification": "client_error",
             "final_url": "x"},
        ]
        monkeypatch.setattr(
            M, "_request", lambda *_args, **_kw: sequence.pop(0)
        )
        result = M.probe("https://www.hhs.gov/some-policy")
        assert result["classification"] == "bot_blocked"

    def test_bot_blocked_host_404_NOT_reclassified(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Only 403 triggers the bot_blocked reclass — a real 404 from
        a bot-blocked host stays a client_error so genuine link rot is
        still surfaced."""
        monkeypatch.setattr(
            M, "_request",
            lambda *_args, **_kw: {"status": 404,
                                   "classification": "client_error",
                                   "final_url": "x"},
        )
        result = M.probe("https://www.hhs.gov/missing")
        assert result["classification"] == "client_error"


# ---------------------------------------------------------------------------
# _print_summary
# ---------------------------------------------------------------------------


class TestPrintSummary:
    def test_empty_payload_prints_zero_total(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        M._print_summary({"sources": {}})
        out = capsys.readouterr().out
        assert "Summary:" in out
        # Format string is f"  {'TOTAL':<18s} {total:>4d}" — exact
        # alignment varies with Python's str formatter; verify the
        # logical content rather than the spacing.
        assert "TOTAL" in out
        # Total of 0 sources renders as a right-aligned 4-char "   0".
        assert "   0" in out

    def test_redirected_section_lists_canonical_targets(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        payload = {
            "sources": {
                "a": {
                    "classification": "redirect",
                    "url": "https://old.example",
                    "final_url": "https://new.example",
                },
                "b": {
                    "classification": "ok",
                    "url": "https://stable.example",
                    "final_url": "https://stable.example",
                },
            }
        }
        M._print_summary(payload)
        out = capsys.readouterr().out
        assert "1 sources redirected" in out
        assert "https://old.example" in out
        assert "https://new.example" in out

    def test_redirect_with_unchanged_final_url_NOT_listed(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A 3xx response whose ``final_url`` is the same as the
        original URL is treated as a self-redirect and NOT printed
        (line 286)."""
        payload = {
            "sources": {
                "a": {
                    "classification": "redirect",
                    "url": "https://self.example",
                    "final_url": "https://self.example",
                }
            }
        }
        M._print_summary(payload)
        out = capsys.readouterr().out
        assert "redirected to a new canonical URL" not in out

    def test_dead_section_lists_unhealthy_sources(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        payload = {
            "sources": {
                "broken": {
                    "classification": "dns",
                    "url": "https://gone.example",
                    "status": None,
                    "error": "nodename or servname",
                },
                "tls-bad": {
                    "classification": "tls",
                    "url": "https://expired.example",
                    "status": None,
                    "error": "cert expired",
                },
            }
        }
        M._print_summary(payload)
        out = capsys.readouterr().out
        assert "2 sources are unreachable" in out
        assert "broken" in out
        assert "tls-bad" in out

    def test_redirected_list_truncated_at_20(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        sources = {
            f"r{i:02d}": {
                "classification": "redirect",
                "url": f"https://old-{i}.example",
                "final_url": f"https://new-{i}.example",
            }
            for i in range(25)
        }
        M._print_summary({"sources": sources})
        out = capsys.readouterr().out
        # First 20 printed; 5 trail to "and N more".
        assert "and 5 more" in out

    def test_dead_list_truncated_at_30(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        sources = {
            f"d{i:02d}": {
                "classification": "client_error",
                "url": f"https://dead-{i}.example",
                "status": 404,
            }
            for i in range(40)
        }
        M._print_summary({"sources": sources})
        out = capsys.readouterr().out
        assert "and 10 more" in out

    def test_dead_section_uses_status_or_error_in_reason(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The reason string format is ``f"{c} ({status or error})"`` —
        both branches must show through."""
        payload = {
            "sources": {
                "with_status": {
                    "classification": "client_error",
                    "url": "https://x.example",
                    "status": 404,
                },
                "with_error_only": {
                    "classification": "dns",
                    "url": "https://y.example",
                    "status": None,
                    "error": "host not found",
                },
            }
        }
        M._print_summary(payload)
        out = capsys.readouterr().out
        assert "client_error (404)" in out
        assert "dns (host not found)" in out


# ---------------------------------------------------------------------------
# _exit_code
# ---------------------------------------------------------------------------


class TestExitCode:
    def test_returns_zero_when_strict_disabled(self) -> None:
        payload = {
            "sources": {
                "a": {"classification": "client_error"},
                "b": {"classification": "tls"},
            }
        }
        assert M._exit_code(payload, strict=False) == 0

    def test_returns_one_when_strict_and_any_dead(self) -> None:
        payload = {
            "sources": {
                "ok": {"classification": "ok"},
                "broken": {"classification": "dns"},
            }
        }
        assert M._exit_code(payload, strict=True) == 1

    def test_returns_zero_when_strict_and_only_healthy(self) -> None:
        payload = {
            "sources": {
                "a": {"classification": "ok"},
                "b": {"classification": "redirect"},
                "c": {"classification": "bot_blocked"},
            }
        }
        assert M._exit_code(payload, strict=True) == 0

    def test_returns_zero_when_payload_empty_and_strict(self) -> None:
        assert M._exit_code({"sources": {}}, strict=True) == 0


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


class TestMainReport:
    def test_report_without_status_file_returns_2(
        self,
        fake_paths: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_library(fake_paths, {"vendors": {"a": {"url": "https://a.example"}}})
        rc = M.main(["--report"])
        out = capsys.readouterr().out
        assert rc == 2
        assert "No status file found" in out

    def test_report_with_status_file_prints_summary(
        self,
        fake_paths: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_library(fake_paths, {"vendors": {"a": {"url": "https://a.example"}}})
        # Pre-write a status file.
        M.STATUS_PATH.write_text(
            json.dumps(
                {
                    "_meta": {"totalChecked": 1},
                    "sources": {
                        "a": {
                            "classification": "ok",
                            "url": "https://a.example",
                            "status": 200,
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        rc = M.main(["--report"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Summary:" in out
        assert "ok" in out

    def test_report_with_strict_returns_1_on_dead(
        self,
        fake_paths: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_library(fake_paths, {"vendors": {"a": {"url": "https://a.example"}}})
        M.STATUS_PATH.write_text(
            json.dumps(
                {
                    "sources": {
                        "a": {
                            "classification": "dns",
                            "url": "https://a.example",
                            "status": None,
                            "error": "host not found",
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        rc = M.main(["--report", "--strict"])
        assert rc == 1


class TestMainEndToEnd:
    def test_runs_with_mocked_probe(
        self,
        fake_paths: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_library(
            fake_paths,
            {
                "vendors": {
                    "splunk-itsi": {"url": "https://docs.splunk.com/itsi"},
                    "cisco-meraki": {"url": "https://meraki.cisco.com"},
                }
            },
        )

        def fake_probe(url: str) -> dict:
            return {
                "status": 200,
                "classification": "ok",
                "final_url": url,
                "redirect_chain": [url],
            }

        monkeypatch.setattr(M, "probe", fake_probe)
        rc = M.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Checking 2 URLs" in out
        # Status file is written.
        assert M.STATUS_PATH.exists()
        loaded = json.loads(M.STATUS_PATH.read_text(encoding="utf-8"))
        assert loaded["_meta"]["totalChecked"] == 2
        assert loaded["_meta"]["tool"] == "scripts/check_source_links.py"
        assert "splunk-itsi" in loaded["sources"]

    def test_only_filter_narrows_check_set(
        self,
        fake_paths: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_library(
            fake_paths,
            {
                "vendors": {
                    "splunk-itsi": {"url": "https://docs.splunk.com/itsi"},
                    "cisco-meraki": {"url": "https://meraki.cisco.com"},
                }
            },
        )

        probed: list[str] = []

        def fake_probe(url: str) -> dict:
            probed.append(url)
            return {"classification": "ok", "final_url": url, "status": 200}

        monkeypatch.setattr(M, "probe", fake_probe)
        rc = M.main(["--only", "splunk"])
        assert rc == 0
        assert len(probed) == 1
        assert "docs.splunk.com" in probed[0]

    def test_strict_returns_1_when_any_source_dead(
        self,
        fake_paths: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _write_library(
            fake_paths,
            {"vendors": {"a": {"url": "https://a.example"}}},
        )
        monkeypatch.setattr(
            M, "probe",
            lambda url: {"classification": "dns", "status": None,
                         "error": "host not found", "final_url": url},
        )
        rc = M.main(["--strict"])
        assert rc == 1

    def test_handles_probe_exception_per_source(
        self,
        fake_paths: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """If the worker future raises, the per-source result MUST
        still be recorded with classification ``unknown_error`` —
        pin the inner ``except Exception`` at line 233."""
        _write_library(
            fake_paths,
            {"vendors": {"a": {"url": "https://a.example"}}},
        )

        def boom(url: str) -> dict:
            raise RuntimeError("probe blew up")

        monkeypatch.setattr(M, "probe", boom)
        rc = M.main([])
        loaded = json.loads(M.STATUS_PATH.read_text(encoding="utf-8"))
        assert loaded["sources"]["a"]["classification"] == "unknown_error"
        assert "probe blew up" in loaded["sources"]["a"]["error"]
        # Default (non-strict) → exit 0 even with the failure.
        assert rc == 0

    def test_skips_sources_without_url(
        self,
        fake_paths: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Entries lacking a ``url`` key are skipped at submit time
        (line 227 ``if rec.get("url")``)."""
        _write_library(
            fake_paths,
            {
                "vendors": {
                    "no-url": {"title": "Internal note, no URL"},
                    "has-url": {"url": "https://x.example"},
                }
            },
        )
        probed: list[str] = []
        monkeypatch.setattr(
            M, "probe",
            lambda url: probed.append(url) or {"classification": "ok",
                                               "final_url": url, "status": 200},
        )
        M.main([])
        assert probed == ["https://x.example"]
        loaded = json.loads(M.STATUS_PATH.read_text(encoding="utf-8"))
        # Only the source with a URL ends up in the status file.
        assert set(loaded["sources"].keys()) == {"has-url"}


# ---------------------------------------------------------------------------
# urllib redirect handler — ensure all method aliases are bound
# ---------------------------------------------------------------------------


class TestNoRedirectHandlerWiring:
    def test_all_redirect_codes_share_implementation(self) -> None:
        """The aliases ``http_error_302 = http_error_301`` etc. (lines
        171-174 in the script) make every redirect handler the SAME
        function object. Pin the identity to catch a future maintainer
        accidentally splitting them — which would re-enable urllib's
        built-in redirect handling and silently break the chain
        recording."""
        h = M.NoRedirectHandler
        assert h.http_error_302 is h.http_error_301
        assert h.http_error_303 is h.http_error_301
        assert h.http_error_307 is h.http_error_301
        assert h.http_error_308 is h.http_error_301


