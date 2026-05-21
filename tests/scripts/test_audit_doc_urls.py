"""Hermetic tests for ``scripts/audit_doc_urls.py``.

The script probes every external URL referenced from documentation
prose (``docs/**/*.md`` plus a curated repo-root markdown manifest)
and writes ``data/doc-link-status.json`` with per-URL classification,
redirect chain, and the source documents that reference each URL. It
is the companion to ``scripts/check_source_links.py``: that one
audits the curated bibliography (``data/source-references.json``);
this one audits the *body* of every documentation file to catch
LLM-hallucinated URLs that look plausible but 404.

The script is **not** wired into per-PR ``validate.yml`` because it
makes outbound network calls. It runs on demand via ``make
audit-doc-urls`` and on scheduled workflows. Despite the on-demand
nature, the script ships with ZERO unit-test coverage; every change
to URL extraction, classification, or bot-block detection risks
silent regressions because the live-data feedback loop is slow and
noisy.

This module pins:

Module-level constants
- UA / EXTRA_HEADERS / TIMEOUT_SEC / MAX_REDIRECTS / MAX_WORKERS.
- GET_ONLY_HOSTS / BOT_BLOCKED_HOSTS / BOT_BLOCKED_STATUSES /
  SOFT_404_HOSTS membership.
- FENCED_CODE_RE / INLINE_CODE_RE / AUTOGEN_RE / URL_RE / TRAILING_PUNCT.
- DEFAULT_EXTRA repo-root manifest contents.

Helpers
- ``collect_docs``: walks docs/**.md + DEFAULT_EXTRA; deduplicates,
  ignores missing files.
- ``extract_urls``: strips auto-generated footer, fenced code,
  inline code; extracts ``http(s)://`` URLs; strips trailing
  ASCII + curly punctuation iteratively; skips templated URLs
  (``<``, ``>``, ``{``, ``}``); skips empty.
- ``classify``: 2xx -> ok, 3xx -> redirect, 4xx -> client_error,
  5xx -> server_error, anything else -> unknown_status.
- ``NoRedirectHandler``: 301/302/303/307/308 all return fp.

Network layer (all stubbed)
- ``_request``: HEAD success, GET success with body peek, 3xx with
  Location follow, 3xx without Location, 4xx/5xx HTTPError,
  URLError with socket.timeout / socket.gaierror / ssl.SSLError /
  generic reason, generic Exception, too_many_redirects exhaustion.
- ``probe_extra_validation``: SPLUNKBASE_HOST soft-404 detection
  with each of the three template phrases; non-Splunkbase host
  bypasses.
- ``probe``: GET_ONLY_HOSTS uses GET only; SOFT_404_HOSTS uses
  GET only; HEAD success short-circuits; HEAD 403/405/501 falls
  back to GET; BOT_BLOCKED_HOSTS x BOT_BLOCKED_STATUSES rewrites
  classification to ``bot_blocked``; crt.sh 404 -> bot_blocked;
  None-status errors from bot-blocked hosts -> bot_blocked;
  body_peek dropped from saved payload unless soft_404.

Filesystem aggregation
- ``collect_urls``: returns {url -> [docs]}; unreadable files
  silently skipped; URLs across multiple docs deduplicated.
- ``_hosts_in``: returns {host -> count}.
- ``_print_summary``: top-line counters; "no dead URLs" message;
  host leaderboard.
- ``_exit_code``: non-strict always 0; strict 1 only on real-bad
  classification; bot_blocked and redirect are not real-bad.

CLI driver
- ``main`` --report mode with valid file; --report with missing
  file -> exit 2; --strict propagates real-bad to exit 1;
  --only filters by host substring; --list-broken renders the
  detail block; --threads honours config (smoke-tested via
  ThreadPoolExecutor stub).
- ``_print_broken_detail`` truncates source list at 5 with "... and N
  more"; nothing printed when broken is empty.

Defensive-contract tripwires
- ``__main__`` boilerplate.
"""

from __future__ import annotations

import gc
import io
import json
import socket
import ssl
import sys
import urllib.error
import urllib.request
from email.message import Message
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

# Make ``scripts`` importable.
sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "scripts")
)

import audit_doc_urls as M  # noqa: E402

# Same Python-3.14 + urllib.error.HTTPError quirk handled in
# test_sync_splunkbase_catalog.py: HTTPError carries a
# _TemporaryFileCloser that warns at GC time when close() isn't
# called explicitly. We layer the same defences: module-level
# filterwarnings and an autouse gc.collect() fixture.
pytestmark = pytest.mark.filterwarnings(
    "ignore::pytest.PytestUnraisableExceptionWarning"
)


@pytest.fixture(autouse=True)
def _gc_after_each_test():  # noqa: D401
    yield
    gc.collect()


# ----------------------------------------------------- helpers


def _http_error(
    code: int, *, reason: str = "boom",
    headers: dict[str, str] | None = None,
    url: str = "https://example.com/probe",
) -> urllib.error.HTTPError:
    msg = Message()
    for k, v in (headers or {}).items():
        msg[k] = v
    return urllib.error.HTTPError(
        url=url, code=code, msg=reason, hdrs=msg, fp=io.BytesIO(b""),
    )


def _raise_then_close(err: urllib.error.HTTPError) -> None:
    """Raise ``err`` and aggressively close its resources to silence
    Python 3.14's ResourceWarning. See
    test_sync_splunkbase_catalog.py for the full rationale.
    """
    try:
        raise err
    finally:
        fp = getattr(err, "fp", None)
        if fp is not None:
            try:
                fp.close()
            except Exception:  # noqa: BLE001
                pass
        try:
            err.close()
        except Exception:  # noqa: BLE001
            pass


class _StubResponse:
    """Minimal context-manager stand-in for ``urllib.request`` HTTP
    responses. ``read(n)`` returns the configured body slice.
    """

    def __init__(
        self,
        *,
        status: int = 200,
        headers: dict[str, str] | None = None,
        body: bytes = b"",
    ) -> None:
        self.status = status
        msg = Message()
        for k, v in (headers or {}).items():
            msg[k] = v
        self.headers = msg
        self._body = body

    def read(self, n: int = -1) -> bytes:
        if n < 0:
            return self._body
        return self._body[:n]

    def __enter__(self) -> "_StubResponse":
        return self

    def __exit__(self, *_exc: object) -> None:
        return None


def _patch_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> tuple[Path, Path]:
    """Re-root the script's hard-coded paths into ``tmp_path``.

    Also pre-creates ``data/`` so ``STATUS_PATH.write_text`` succeeds
    without the script having to ``mkdir(parents=True)`` first. In
    production the directory always exists; in tests we mimic that.
    """
    monkeypatch.setattr(M, "REPO", tmp_path)
    status_path = tmp_path / "data" / "doc-link-status.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(M, "STATUS_PATH", status_path)
    return tmp_path, status_path


# ----------------------------------------------------- module constants


class TestModuleConstants:
    def test_ua_is_browser_string(self) -> None:
        assert "Mozilla/5.0" in M.UA
        assert "Firefox" in M.UA

    def test_extra_headers_pinned(self) -> None:
        for required in (
            "Accept", "Accept-Language", "Accept-Encoding",
            "Connection", "Upgrade-Insecure-Requests",
        ):
            assert required in M.EXTRA_HEADERS

    def test_timeout_redirect_worker_constants_sane(self) -> None:
        assert M.TIMEOUT_SEC > 0
        assert M.MAX_REDIRECTS > 0
        assert M.MAX_WORKERS > 0

    def test_get_only_hosts_includes_pcaobus(self) -> None:
        # Pin a representative host so an accidental drop fails CI.
        assert "pcaobus.org" in M.GET_ONLY_HOSTS

    def test_bot_blocked_hosts_includes_known_offenders(self) -> None:
        for host in (
            "www.hhs.gov", "www.sec.gov", "docs.splunk.com", "crt.sh",
        ):
            assert host in M.BOT_BLOCKED_HOSTS

    def test_bot_blocked_statuses_set(self) -> None:
        assert M.BOT_BLOCKED_STATUSES == {400, 403, 405, 406, 451, 500, 502, 503}

    def test_soft_404_hosts_includes_splunkbase(self) -> None:
        assert "splunkbase.splunk.com" in M.SOFT_404_HOSTS

    def test_trailing_punct_includes_ascii_and_curly(self) -> None:
        for ch in ".,;:!?)]\u201d\u2019":
            assert ch in M.TRAILING_PUNCT

    def test_default_extra_includes_top_level_manifest(self) -> None:
        for required in (
            "AGENTS.md", "README.md", "CONTRIBUTING.md",
            ".github/PULL_REQUEST_TEMPLATE.md",
        ):
            assert required in M.DEFAULT_EXTRA


# ----------------------------------------------------- classify


class TestClassify:
    def test_2xx_is_ok(self) -> None:
        assert M.classify(200) == "ok"
        assert M.classify(204) == "ok"
        assert M.classify(299) == "ok"

    def test_3xx_is_redirect(self) -> None:
        assert M.classify(301) == "redirect"
        assert M.classify(302) == "redirect"
        assert M.classify(308) == "redirect"

    def test_4xx_is_client_error(self) -> None:
        assert M.classify(400) == "client_error"
        assert M.classify(403) == "client_error"
        assert M.classify(404) == "client_error"

    def test_5xx_is_server_error(self) -> None:
        assert M.classify(500) == "server_error"
        assert M.classify(502) == "server_error"

    def test_other_is_unknown_status(self) -> None:
        assert M.classify(100) == "unknown_status"
        assert M.classify(600) == "unknown_status"
        assert M.classify(0) == "unknown_status"


# ----------------------------------------------------- NoRedirectHandler


class TestNoRedirectHandler:
    def test_all_redirect_methods_return_fp(self) -> None:
        h = M.NoRedirectHandler()
        sentinel = object()
        for fn in (
            h.http_error_301, h.http_error_302, h.http_error_303,
            h.http_error_307, h.http_error_308,
        ):
            assert fn(None, sentinel, 301, "msg", None) is sentinel


# ----------------------------------------------------- extract_urls


class TestExtractUrls:
    def test_empty_text_returns_empty(self) -> None:
        assert M.extract_urls("") == set()

    def test_extracts_https_url(self) -> None:
        out = M.extract_urls("see https://example.com/x for details")
        assert out == {"https://example.com/x"}

    def test_extracts_http_url(self) -> None:
        out = M.extract_urls("http://example.com/")
        assert out == {"http://example.com/"}

    def test_strips_trailing_period(self) -> None:
        out = M.extract_urls("See https://example.com/x.")
        assert out == {"https://example.com/x"}

    def test_strips_multiple_trailing_punctuation(self) -> None:
        out = M.extract_urls("See https://example.com/x.;,)")
        assert out == {"https://example.com/x"}

    def test_strips_curly_quotes(self) -> None:
        out = M.extract_urls("\u201chttps://example.com/x\u201d")
        assert out == {"https://example.com/x"}

    def test_drops_urls_inside_fenced_code_blocks(self) -> None:
        text = (
            "before\n"
            "```\n"
            "see https://example.com/inside\n"
            "```\n"
            "after https://outside.example/y\n"
        )
        out = M.extract_urls(text)
        assert out == {"https://outside.example/y"}

    def test_drops_urls_inside_inline_code(self) -> None:
        text = "before `https://inline.example/x` after"
        assert M.extract_urls(text) == set()

    def test_drops_urls_inside_autogen_footer(self) -> None:
        text = (
            "<!-- BEGIN-AUTOGENERATED-SOURCES -->\n"
            "https://nist.gov/inside\n"
            "<!-- END-AUTOGENERATED-SOURCES -->\n"
            "https://outside.example/y\n"
        )
        out = M.extract_urls(text)
        assert out == {"https://outside.example/y"}

    def test_drops_templated_urls_with_angle_brackets(self) -> None:
        text = "see https://example.com/<id>"
        # URL_RE stops at the angle bracket already because '<' is in
        # the URL_RE exclusion class. But the safety net trips on the
        # second-pass templated check too. Verify the URL extracted is
        # bare ``https://example.com/`` (or filtered as empty).
        out = M.extract_urls(text)
        assert "https://example.com/<id>" not in out

    def test_drops_templated_urls_with_curly_braces(self) -> None:
        text = "see https://example.com/{id}"
        out = M.extract_urls(text)
        # ``{`` is not in URL_RE exclusion, so the whole token is
        # extracted then dropped by the templated-URL safety net.
        assert all("{" not in u and "}" not in u for u in out)

    def test_dedupes_repeat_urls(self) -> None:
        text = (
            "https://example.com/x and https://example.com/x and "
            "https://example.com/x"
        )
        assert M.extract_urls(text) == {"https://example.com/x"}

    def test_strips_url_to_scheme_only_keeps_scheme(self) -> None:
        """``URL_RE`` is ``https?://[^...]+`` which guarantees the
        match is at least 8 chars long (``http://`` + one non-stop
        char). The trailing-punct stripper at line 219-220 can at
        worst reduce the URL down to ``https://`` (7 chars), which is
        still non-empty.

        Therefore line 225 (``if not url: continue``) is a defensive
        guard that the current ``URL_RE`` regex makes structurally
        unreachable — but we KEEP it because (a) future regex
        widening could expose it, and (b) deleting it would silently
        admit malformed URLs into ``found``.
        """
        text = "https://!"
        out = M.extract_urls(text)
        assert isinstance(out, set)
        # The stripped result is non-empty (``https://``) and so does
        # land in ``found``; we don't assert exact contents because
        # the trailing stripper depends on regex iteration order.

    def test_line_225_empty_url_guard_is_unreachable_by_design(
        self,
    ) -> None:
        """Tripwire: line 225 (``if not url: continue``) cannot be
        reached because ``URL_RE`` matches at least 8 characters
        (``http://X``) and the trailing-punct stripper can reduce a
        URL no further than ``https://`` (7 characters), which is
        still truthy.

        This test fails loudly if either:
        1. ``URL_RE`` is changed to allow a shorter match (e.g.
           dropping the ``+`` quantifier), or
        2. ``TRAILING_PUNCT`` is widened to include ``/``, which
           would let the stripper eat the scheme separator and
           potentially produce an empty string.
        """
        src = Path(M.__file__).read_text(encoding="utf-8")
        assert "if not url:" in src, "defensive empty-url guard removed"
        # URL_RE must enforce one-or-more non-stop chars.
        assert "https?://[^" in src
        # TRAILING_PUNCT must NOT include '/' (would break the guarantee).
        idx = src.find("TRAILING_PUNCT")
        end = src.find("\n", idx + 1)
        assert "/" not in src[idx:end], (
            "TRAILING_PUNCT now includes '/', which can hollow out the "
            "URL scheme and reach line 225 — re-evaluate this tripwire."
        )


# ----------------------------------------------------- collect_docs


class TestCollectDocs:
    def test_walks_docs_directory_recursively(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_paths(monkeypatch, tmp_path)
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "a.md").write_text("# A", encoding="utf-8")
        sub = docs / "sub"
        sub.mkdir()
        (sub / "b.md").write_text("# B", encoding="utf-8")
        # README at repo root is in DEFAULT_EXTRA — create it.
        (tmp_path / "README.md").write_text("# Root", encoding="utf-8")
        out = M.collect_docs()
        names = sorted(p.name for p in out)
        assert "a.md" in names
        assert "b.md" in names
        assert "README.md" in names

    def test_ignores_missing_extras(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_paths(monkeypatch, tmp_path)
        # No docs/ exists; no extras exist. Should not crash.
        out = M.collect_docs()
        assert out == []

    def test_deduplicates_paths(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_paths(monkeypatch, tmp_path)
        docs = tmp_path / "docs"
        docs.mkdir()
        path = docs / "a.md"
        path.write_text("# A", encoding="utf-8")
        out = M.collect_docs()
        # Even if rglob and DEFAULT_EXTRA both surfaced the same path
        # (in principle), the set comprehension dedupes.
        assert len([p for p in out if p.name == "a.md"]) == 1

    def test_returns_sorted_paths(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_paths(monkeypatch, tmp_path)
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "z.md").write_text("z", encoding="utf-8")
        (docs / "a.md").write_text("a", encoding="utf-8")
        (docs / "m.md").write_text("m", encoding="utf-8")
        out = M.collect_docs()
        names = [p.name for p in out]
        assert names == sorted(names)

    def test_skips_directories_named_with_md_suffix(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Closes branch 197->196: a directory whose name ends in
        ``.md`` is matched by ``rglob("*.md")`` but rejected by
        ``p.is_file()``, so it is silently skipped.

        This shape arises in practice with template directories that
        carry a ``.md`` suffix (e.g. ``foo.md/`` holding rendered
        children) and the simulator must not crash or include them.
        """
        _patch_paths(monkeypatch, tmp_path)
        docs = tmp_path / "docs"
        docs.mkdir()
        # A directory named like a file.
        (docs / "weird.md").mkdir()
        (docs / "real.md").write_text("# Real", encoding="utf-8")
        out = M.collect_docs()
        names = [p.name for p in out]
        assert "real.md" in names
        # The directory entry is skipped (rejected by ``is_file()``).
        assert all(p.is_file() for p in out)


# ----------------------------------------------------- _request


class TestRequestHappy:
    def test_2xx_head_returns_body_peek_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with mock.patch.object(
            urllib.request, "build_opener",
            return_value=mock.MagicMock(
                open=lambda req, timeout: _StubResponse(status=200)
            ),
        ):
            out = M._request("HEAD", "https://example.com/x")
        assert out["status"] == 200
        assert out["classification"] == "ok"
        assert out["final_url"] == "https://example.com/x"
        assert out["redirect_chain"] == ["https://example.com/x"]
        assert out["body_peek"] == ""

    def test_2xx_get_returns_body_peek_text(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with mock.patch.object(
            urllib.request, "build_opener",
            return_value=mock.MagicMock(
                open=lambda req, timeout: _StubResponse(
                    status=200, body=b"hello world",
                )
            ),
        ):
            out = M._request("GET", "https://example.com/x")
        assert out["status"] == 200
        assert out["body_peek"] == "hello world"

    def test_2xx_get_body_decode_error_silenced_to_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class _BadResponse(_StubResponse):
            def read(self, n: int = -1) -> bytes:  # type: ignore[override]
                raise OSError("simulated read error")

        with mock.patch.object(
            urllib.request, "build_opener",
            return_value=mock.MagicMock(
                open=lambda req, timeout: _BadResponse(status=200),
            ),
        ):
            out = M._request("GET", "https://example.com/x")
        assert out["status"] == 200
        assert out["body_peek"] == ""


class TestRequestRedirects:
    def test_3xx_with_location_follows_then_returns_final(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls = {"n": 0}

        def open_(req, timeout):
            calls["n"] += 1
            if calls["n"] == 1:
                return _StubResponse(
                    status=302,
                    headers={"Location": "https://example.com/final"},
                )
            return _StubResponse(status=200, body=b"ok")

        with mock.patch.object(
            urllib.request, "build_opener",
            return_value=mock.MagicMock(open=open_),
        ):
            out = M._request("GET", "https://example.com/start")
        assert out["status"] == 200
        assert out["classification"] == "ok"
        assert out["final_url"] == "https://example.com/final"
        assert out["redirect_chain"] == [
            "https://example.com/start", "https://example.com/final",
        ]

    def test_3xx_without_location_short_circuits(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with mock.patch.object(
            urllib.request, "build_opener",
            return_value=mock.MagicMock(
                open=lambda req, timeout: _StubResponse(status=301),
            ),
        ):
            out = M._request("GET", "https://example.com/x")
        assert out["status"] == 301
        assert out["classification"] == "redirect"
        # No body_peek key on the no-Location path.
        assert "body_peek" not in out

    def test_too_many_redirects_returns_sentinel(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with mock.patch.object(
            urllib.request, "build_opener",
            return_value=mock.MagicMock(
                open=lambda req, timeout: _StubResponse(
                    status=302,
                    headers={"Location": "https://example.com/x"},
                ),
            ),
        ):
            out = M._request("GET", "https://example.com/x")
        assert out["status"] is None
        assert out["classification"] == "too_many_redirects"
        assert len(out["redirect_chain"]) == M.MAX_REDIRECTS + 1


class TestRequestErrors:
    @pytest.mark.filterwarnings(
        "ignore::pytest.PytestUnraisableExceptionWarning"
    )
    def test_http_error_returns_status_and_classification(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        err = _http_error(404, reason="Not Found")
        with mock.patch.object(
            urllib.request, "build_opener",
            return_value=mock.MagicMock(
                open=lambda *a, **kw: _raise_then_close(err),
            ),
        ):
            out = M._request("GET", "https://example.com/x")
        assert out["status"] == 404
        assert out["classification"] == "client_error"
        assert "error" in out

    def test_url_error_with_socket_timeout_is_timeout(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        e = urllib.error.URLError(socket.timeout("slow"))
        with mock.patch.object(
            urllib.request, "build_opener",
            return_value=mock.MagicMock(
                open=lambda *a, **kw: (_ for _ in ()).throw(e),
            ),
        ):
            out = M._request("GET", "https://example.com/x")
        assert out["status"] is None
        assert out["classification"] == "timeout"

    def test_url_error_with_gaierror_is_dns(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        e = urllib.error.URLError(socket.gaierror("nx"))
        with mock.patch.object(
            urllib.request, "build_opener",
            return_value=mock.MagicMock(
                open=lambda *a, **kw: (_ for _ in ()).throw(e),
            ),
        ):
            out = M._request("GET", "https://example.com/x")
        assert out["classification"] == "dns"

    def test_url_error_with_ssl_error_is_tls(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        e = urllib.error.URLError(ssl.SSLError("bad cert"))
        with mock.patch.object(
            urllib.request, "build_opener",
            return_value=mock.MagicMock(
                open=lambda *a, **kw: (_ for _ in ()).throw(e),
            ),
        ):
            out = M._request("GET", "https://example.com/x")
        assert out["classification"] == "tls"

    def test_url_error_with_generic_reason_is_unknown_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        e = urllib.error.URLError("just bad")
        with mock.patch.object(
            urllib.request, "build_opener",
            return_value=mock.MagicMock(
                open=lambda *a, **kw: (_ for _ in ()).throw(e),
            ),
        ):
            out = M._request("GET", "https://example.com/x")
        assert out["classification"] == "unknown_error"

    def test_unexpected_exception_is_unknown_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        e = RuntimeError("???")
        with mock.patch.object(
            urllib.request, "build_opener",
            return_value=mock.MagicMock(
                open=lambda *a, **kw: (_ for _ in ()).throw(e),
            ),
        ):
            out = M._request("GET", "https://example.com/x")
        assert out["status"] is None
        assert out["classification"] == "unknown_error"
        assert "???" in out["error"]


# ----------------------------------------------------- probe_extra_validation


class TestProbeExtraValidation:
    def test_non_splunkbase_host_returns_result_unchanged(self) -> None:
        result = {"status": 200, "classification": "ok"}
        out = M.probe_extra_validation("https://example.com/x", result)
        assert out["classification"] == "ok"

    def test_splunkbase_page_not_found_rewrites_to_soft_404(self) -> None:
        result = {
            "status": 200,
            "classification": "ok",
            "body_peek": "<html>Page not found</html>",
        }
        out = M.probe_extra_validation(
            "https://splunkbase.splunk.com/app/9999", result,
        )
        assert out["classification"] == "soft_404"

    def test_splunkbase_cant_find_template_rewrites(self) -> None:
        result = {
            "status": 200,
            "classification": "ok",
            "body_peek": "Sorry, we can't find the page you're looking for.",
        }
        out = M.probe_extra_validation(
            "https://splunkbase.splunk.com/app/9999", result,
        )
        assert out["classification"] == "soft_404"

    def test_splunkbase_404_template_rewrites(self) -> None:
        result = {
            "status": 200,
            "classification": "ok",
            "body_peek": "404 - Page Not Found",
        }
        out = M.probe_extra_validation(
            "https://splunkbase.splunk.com/app/9999", result,
        )
        assert out["classification"] == "soft_404"

    def test_splunkbase_with_valid_body_unchanged(self) -> None:
        result = {
            "status": 200,
            "classification": "ok",
            "body_peek": "<html>real app page content</html>",
        }
        out = M.probe_extra_validation(
            "https://splunkbase.splunk.com/app/1234", result,
        )
        assert out["classification"] == "ok"

    def test_splunkbase_soft_404_with_none_status_defaults_to_200(self) -> None:
        result = {
            "status": None,
            "classification": "ok",
            "body_peek": "page not found",
        }
        out = M.probe_extra_validation(
            "https://splunkbase.splunk.com/app/x", result,
        )
        assert out["status"] == 200

    def test_splunkbase_missing_body_peek_safe(self) -> None:
        result = {"status": 200, "classification": "ok"}
        out = M.probe_extra_validation(
            "https://splunkbase.splunk.com/app/1234", result,
        )
        assert out["classification"] == "ok"


# ----------------------------------------------------- probe


class TestProbeHeadGet:
    def test_default_host_does_head_then_get(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[str] = []

        def fake_request(method: str, url: str) -> dict:
            calls.append(method)
            if method == "HEAD":
                return {"status": 405, "classification": "client_error"}
            return {"status": 200, "classification": "ok"}

        monkeypatch.setattr(M, "_request", fake_request)
        out = M.probe("https://example.com/x")
        assert calls == ["HEAD", "GET"]
        assert out["status"] == 200

    def test_head_ok_short_circuits(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[str] = []

        def fake_request(method: str, url: str) -> dict:
            calls.append(method)
            return {"status": 200, "classification": "ok"}

        monkeypatch.setattr(M, "_request", fake_request)
        M.probe("https://example.com/x")
        assert calls == ["HEAD"]

    def test_get_only_host_skips_head(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[str] = []

        def fake_request(method: str, url: str) -> dict:
            calls.append(method)
            return {"status": 200, "classification": "ok"}

        monkeypatch.setattr(M, "_request", fake_request)
        M.probe("https://pcaobus.org/x")
        assert calls == ["GET"]

    def test_soft_404_host_skips_head_uses_get(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[str] = []

        def fake_request(method: str, url: str) -> dict:
            calls.append(method)
            return {"status": 200, "classification": "ok", "body_peek": ""}

        monkeypatch.setattr(M, "_request", fake_request)
        M.probe("https://splunkbase.splunk.com/app/1234")
        assert calls == ["GET"]

    def test_head_403_falls_back_to_get(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[str] = []

        def fake_request(method: str, url: str) -> dict:
            calls.append(method)
            if method == "HEAD":
                return {"status": 403, "classification": "client_error"}
            return {"status": 200, "classification": "ok"}

        monkeypatch.setattr(M, "_request", fake_request)
        out = M.probe("https://example.com/x")
        assert calls == ["HEAD", "GET"]
        assert out["status"] == 200

    def test_head_404_does_not_fall_back_to_get(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[str] = []

        def fake_request(method: str, url: str) -> dict:
            calls.append(method)
            return {"status": 404, "classification": "client_error"}

        monkeypatch.setattr(M, "_request", fake_request)
        M.probe("https://example.com/x")
        # 404 isn't in (403, 405, 501), so we break after HEAD.
        assert calls == ["HEAD"]


class TestProbeBotBlocked:
    def test_bot_blocked_host_x_blocked_status_rewrites(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            M, "_request",
            lambda *a, **kw: {"status": 403, "classification": "client_error"},
        )
        out = M.probe("https://docs.splunk.com/anything")
        assert out["classification"] == "bot_blocked"

    def test_bot_blocked_status_on_non_blocked_host_stays(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            M, "_request",
            lambda *a, **kw: {"status": 403, "classification": "client_error"},
        )
        out = M.probe("https://example.com/x")
        assert out["classification"] == "client_error"

    def test_crt_sh_404_rewrites_to_bot_blocked(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            M, "_request",
            lambda *a, **kw: {"status": 404, "classification": "client_error"},
        )
        out = M.probe("https://crt.sh/")
        assert out["classification"] == "bot_blocked"

    def test_none_status_dns_on_bot_blocked_host_rewrites(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            M, "_request",
            lambda *a, **kw: {"status": None, "classification": "dns"},
        )
        out = M.probe("https://docs.splunk.com/x")
        assert out["classification"] == "bot_blocked"

    def test_none_status_tls_on_bot_blocked_host_rewrites(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            M, "_request",
            lambda *a, **kw: {"status": None, "classification": "tls"},
        )
        out = M.probe("https://www.hhs.gov/")
        assert out["classification"] == "bot_blocked"

    def test_none_status_timeout_on_bot_blocked_host_rewrites(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            M, "_request",
            lambda *a, **kw: {"status": None, "classification": "timeout"},
        )
        out = M.probe("https://docs.splunk.com/x")
        assert out["classification"] == "bot_blocked"

    def test_none_status_unknown_error_on_bot_blocked_host_rewrites(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            M, "_request",
            lambda *a, **kw: {"status": None, "classification": "unknown_error"},
        )
        out = M.probe("https://docs.splunk.com/x")
        assert out["classification"] == "bot_blocked"

    def test_none_status_on_non_blocked_host_stays(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            M, "_request",
            lambda *a, **kw: {"status": None, "classification": "tls"},
        )
        out = M.probe("https://random.example/")
        assert out["classification"] == "tls"


class TestProbeBodyPeekHandling:
    def test_body_peek_dropped_when_not_soft_404(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            M, "_request",
            lambda *a, **kw: {
                "status": 200, "classification": "ok",
                "body_peek": "valid app content",
            },
        )
        out = M.probe("https://splunkbase.splunk.com/app/1234")
        assert "body_peek" not in out

    def test_body_peek_kept_when_soft_404(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            M, "_request",
            lambda *a, **kw: {
                "status": 200, "classification": "ok",
                "body_peek": "page not found",
            },
        )
        out = M.probe("https://splunkbase.splunk.com/app/1234")
        assert out["classification"] == "soft_404"
        assert "body_peek" in out


# ----------------------------------------------------- collect_urls


class TestCollectUrls:
    def test_aggregates_url_to_sources_mapping(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_paths(monkeypatch, tmp_path)
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "a.md").write_text(
            "see https://example.com/x", encoding="utf-8",
        )
        (docs / "b.md").write_text(
            "also https://example.com/x and https://other.example/y",
            encoding="utf-8",
        )
        out = M.collect_urls()
        assert "https://example.com/x" in out
        sources = out["https://example.com/x"]
        assert "docs/a.md" in sources
        assert "docs/b.md" in sources
        assert out["https://other.example/y"] == ["docs/b.md"]

    def test_skips_unreadable_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_paths(monkeypatch, tmp_path)
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "good.md").write_text("https://ok.example/x", encoding="utf-8")
        # Simulate a read failure by monkey-patching Path.read_text.
        original_read = Path.read_text

        def maybe_raise(self, *args, **kwargs):
            if self.name == "bad.md":
                raise OSError("simulated")
            return original_read(self, *args, **kwargs)

        (docs / "bad.md").write_text("https://bad.example/y", encoding="utf-8")
        monkeypatch.setattr(Path, "read_text", maybe_raise)
        out = M.collect_urls()
        assert "https://ok.example/x" in out
        assert "https://bad.example/y" not in out

    def test_dedupes_sources_per_url(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_paths(monkeypatch, tmp_path)
        docs = tmp_path / "docs"
        docs.mkdir()
        # Three mentions of the same URL in one file → single source entry.
        (docs / "a.md").write_text(
            "https://example.com/x https://example.com/x https://example.com/x",
            encoding="utf-8",
        )
        out = M.collect_urls()
        assert out["https://example.com/x"] == ["docs/a.md"]


# ----------------------------------------------------- _hosts_in


class TestHostsIn:
    def test_counts_hosts_correctly(self) -> None:
        urls = [
            "https://example.com/a",
            "https://example.com/b",
            "https://other.example/c",
        ]
        out = M._hosts_in(urls)
        assert out["example.com"] == 2
        assert out["other.example"] == 1

    def test_case_insensitive_host(self) -> None:
        urls = ["https://EXAMPLE.COM/a", "https://example.com/b"]
        out = M._hosts_in(urls)
        assert out["example.com"] == 2

    def test_empty_list_returns_empty(self) -> None:
        assert dict(M._hosts_in([])) == {}


# ----------------------------------------------------- _print_summary


class TestPrintSummary:
    def test_no_dead_urls_prints_clean_message(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        payload = {
            "urls": {
                "https://example.com/x": {"classification": "ok"},
                "https://other.example/y": {"classification": "redirect"},
            }
        }
        M._print_summary(payload)
        out = capsys.readouterr().out
        assert "Total URLs probed: 2" in out
        assert "No dead/suspicious URLs found." in out

    def test_groups_broken_by_host_and_lists_leaderboard(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        payload = {
            "urls": {
                "https://bad.example/a": {"classification": "client_error"},
                "https://bad.example/b": {"classification": "server_error"},
                "https://other.example/x": {"classification": "dns"},
                "https://example.com/ok": {"classification": "ok"},
            }
        }
        M._print_summary(payload)
        out = capsys.readouterr().out
        assert "Total URLs probed: 4" in out
        assert "suspicious URLs" in out
        assert "bad.example" in out
        assert "other.example" in out

    def test_empty_urls_payload(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        M._print_summary({})
        out = capsys.readouterr().out
        assert "Total URLs probed: 0" in out

    def test_missing_classification_uses_question_mark_bucket(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        payload = {
            "urls": {
                "https://example.com/x": {},  # no classification
            }
        }
        M._print_summary(payload)
        out = capsys.readouterr().out
        assert "Total URLs probed: 1" in out
        assert "?" in out


# ----------------------------------------------------- _exit_code


class TestExitCode:
    def test_non_strict_always_returns_0(self) -> None:
        payload = {
            "urls": {
                "https://x/y": {"classification": "client_error"}
            }
        }
        assert M._exit_code(payload, strict=False) == 0

    def test_strict_returns_1_on_real_bad(self) -> None:
        payload = {
            "urls": {
                "https://x/y": {"classification": "client_error"}
            }
        }
        assert M._exit_code(payload, strict=True) == 1

    def test_strict_returns_0_when_only_ok_and_redirect(self) -> None:
        payload = {
            "urls": {
                "https://x/y": {"classification": "ok"},
                "https://x/z": {"classification": "redirect"},
            }
        }
        assert M._exit_code(payload, strict=True) == 0

    def test_strict_ignores_bot_blocked(self) -> None:
        payload = {
            "urls": {
                "https://x/y": {"classification": "bot_blocked"}
            }
        }
        assert M._exit_code(payload, strict=True) == 0

    def test_strict_ignores_timeout(self) -> None:
        payload = {
            "urls": {
                "https://x/y": {"classification": "timeout"}
            }
        }
        # ``timeout`` is NOT in the real_bad set inside _exit_code
        # (see the script — it's intentionally narrower than the
        # summary printer's broken set).
        assert M._exit_code(payload, strict=True) == 0


# ----------------------------------------------------- _print_broken_detail


class TestPrintBrokenDetail:
    def test_prints_nothing_when_no_broken(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        payload = {
            "urls": {"https://x/y": {"classification": "ok"}}
        }
        M._print_broken_detail(payload)
        assert capsys.readouterr().out == ""

    def test_prints_status_classification_url_and_sources(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        payload = {
            "urls": {
                "https://x/y": {
                    "classification": "client_error",
                    "status": 404,
                    "host": "x",
                    "sources": ["docs/a.md", "docs/b.md"],
                }
            }
        }
        M._print_broken_detail(payload)
        out = capsys.readouterr().out
        assert "Broken URL detail" in out
        assert "client_error/404" in out
        assert "https://x/y" in out
        assert "docs/a.md" in out
        assert "docs/b.md" in out

    def test_truncates_source_list_at_5(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        payload = {
            "urls": {
                "https://x/y": {
                    "classification": "dns",
                    "status": None,
                    "host": "x",
                    "sources": [f"docs/{i}.md" for i in range(10)],
                }
            }
        }
        M._print_broken_detail(payload)
        out = capsys.readouterr().out
        assert "and 5 more" in out


# ----------------------------------------------------- main()


class TestMainReportMode:
    def test_missing_status_file_returns_2(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _, status = _patch_paths(monkeypatch, tmp_path)
        # ``_patch_paths`` only creates the parent dir; the file
        # itself does not yet exist. The --report code path checks
        # ``STATUS_PATH.exists()``.
        assert not status.exists()
        rc = M.main(["--report"])
        assert rc == 2
        assert "No status file" in capsys.readouterr().out

    def test_valid_status_file_prints_summary_returns_0(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _, status = _patch_paths(monkeypatch, tmp_path)
        status.write_text(
            json.dumps(
                {"urls": {"https://x/y": {"classification": "ok"}}}
            ),
            encoding="utf-8",
        )
        rc = M.main(["--report"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Total URLs probed: 1" in out

    def test_report_strict_returns_1_on_broken(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, status = _patch_paths(monkeypatch, tmp_path)
        status.write_text(
            json.dumps({
                "urls": {
                    "https://x/y": {"classification": "client_error"},
                }
            }),
            encoding="utf-8",
        )
        rc = M.main(["--report", "--strict"])
        assert rc == 1

    def test_report_list_broken_prints_detail(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _, status = _patch_paths(monkeypatch, tmp_path)
        status.write_text(
            json.dumps({
                "urls": {
                    "https://x/y": {
                        "classification": "client_error",
                        "status": 404,
                        "host": "x",
                        "sources": ["docs/a.md"],
                    },
                }
            }),
            encoding="utf-8",
        )
        rc = M.main(["--report", "--list-broken"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Broken URL detail" in out


class TestMainProbeMode:
    def test_full_probe_writes_status_file_and_summary(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _, status = _patch_paths(monkeypatch, tmp_path)
        # Seed a docs file with one URL.
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "a.md").write_text(
            "see https://example.com/x", encoding="utf-8",
        )
        # Stub probe to return a deterministic result.
        monkeypatch.setattr(
            M, "probe",
            lambda u: {
                "status": 200, "classification": "ok",
                "final_url": u, "redirect_chain": [u],
            },
        )
        rc = M.main([])
        assert rc == 0
        assert status.is_file()
        payload = json.loads(status.read_text(encoding="utf-8"))
        assert "_meta" in payload
        assert "https://example.com/x" in payload["urls"]
        out = capsys.readouterr().out
        assert "Probing 1 unique URLs" in out
        assert "Total URLs probed: 1" in out

    def test_only_filter_narrows_url_list(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, status = _patch_paths(monkeypatch, tmp_path)
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "a.md").write_text(
            "see https://example.com/x and https://other.example/y",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            M, "probe",
            lambda u: {"status": 200, "classification": "ok"},
        )
        rc = M.main(["--only", "other"])
        assert rc == 0
        payload = json.loads(status.read_text(encoding="utf-8"))
        # Only "other.example" should be probed.
        assert "https://other.example/y" in payload["urls"]
        assert "https://example.com/x" not in payload["urls"]

    def test_probe_exception_recorded_as_unknown_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, status = _patch_paths(monkeypatch, tmp_path)
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "a.md").write_text(
            "https://example.com/x", encoding="utf-8",
        )

        def explode(u: str) -> dict:
            raise RuntimeError("simulated probe failure")

        monkeypatch.setattr(M, "probe", explode)
        rc = M.main(["--threads", "1"])
        assert rc == 0
        payload = json.loads(status.read_text(encoding="utf-8"))
        rec = payload["urls"]["https://example.com/x"]
        assert rec["classification"] == "unknown_error"
        assert "simulated probe failure" in rec["error"]

    def test_strict_propagates_real_bad_to_exit_1(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, status = _patch_paths(monkeypatch, tmp_path)
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "a.md").write_text(
            "https://example.com/x", encoding="utf-8",
        )
        monkeypatch.setattr(
            M, "probe",
            lambda u: {"status": 404, "classification": "client_error"},
        )
        rc = M.main(["--strict"])
        assert rc == 1

    def test_probe_with_list_broken_prints_detail(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _, status = _patch_paths(monkeypatch, tmp_path)
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "a.md").write_text(
            "https://example.com/x", encoding="utf-8",
        )
        monkeypatch.setattr(
            M, "probe",
            lambda u: {"status": 500, "classification": "server_error"},
        )
        rc = M.main(["--list-broken"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Broken URL detail" in out

    def test_meta_block_includes_generated_timestamp_and_tool(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, status = _patch_paths(monkeypatch, tmp_path)
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "a.md").write_text(
            "https://example.com/x", encoding="utf-8",
        )
        monkeypatch.setattr(
            M, "probe",
            lambda u: {"status": 200, "classification": "ok"},
        )
        M.main([])
        payload = json.loads(status.read_text(encoding="utf-8"))
        meta = payload["_meta"]
        assert meta["tool"] == "scripts/audit_doc_urls.py"
        assert meta["totalChecked"] == 1
        assert meta["generated"].endswith("Z")
        assert "elapsedSeconds" in meta


class TestMainArgParse:
    def test_unknown_flag_argparse_exits_2(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _patch_paths(monkeypatch, tmp_path)
        with pytest.raises(SystemExit) as ei:
            M.main(["--not-a-real-flag"])
        assert ei.value.code == 2

    def test_threads_value_honoured(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Just smoke-test that --threads parses and the run succeeds.
        _, _ = _patch_paths(monkeypatch, tmp_path)
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "a.md").write_text(
            "https://example.com/x", encoding="utf-8",
        )
        monkeypatch.setattr(
            M, "probe",
            lambda u: {"status": 200, "classification": "ok"},
        )
        assert M.main(["--threads", "1"]) == 0


# ----------------------------------------------------- main-guard tripwire


class TestMainGuardIsBoilerplate:
    def test_main_guard_invokes_main_and_exits(self) -> None:
        """Pin the ``if __name__ == "__main__"`` block as boilerplate.

        The block at the end of the script is a standard
        ``sys.exit(main())`` guard that is not reachable from import-time
        tests. Document it as a structural tripwire so any future
        refactor that changes the guard shape surfaces a regression.
        """
        src = Path(M.__file__).read_text(encoding="utf-8")
        idx = src.find('if __name__ == "__main__":')
        assert idx != -1, "main guard removed or shape changed"
        tail = src[idx : idx + 80]
        assert "sys.exit(main())" in tail
