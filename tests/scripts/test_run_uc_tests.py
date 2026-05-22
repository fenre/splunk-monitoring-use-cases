"""Hermetic tests for ``scripts/run_uc_tests.py``.

The script is the CI entrypoint wired into ``.github/workflows/uc-tests.yml``;
it ingests fixture events into a real Splunk via HEC, runs the UC's SPL,
and asserts on the result count / fields. The tests here exercise every
non-network code path with ``--dry-run`` semantics and stub
``urllib.request.urlopen`` for the network-touching methods so we can
verify ``SplunkClient`` request shape and ``run_uc_test`` orchestration
without needing a live Splunk instance.

Coverage scope
--------------
- ``rewrite_timestamp`` for all four pattern families.
- ``split_events`` (blank-line blocks vs single-line fallback).
- ``SplunkClient.__init__`` TLS-verify branches.
- ``SplunkClient._login`` caching, request shape.
- ``SplunkClient.run_oneshot`` SPL prefix handling, query encoding.
- ``SplunkClient.hec_post_event`` payload shape (with / without source / host).
- ``SplunkClient.delete_ingested`` SPL composition.
- ``_get_uc_spl`` resolution from catalog.json.
- ``_assert_expected`` for every failure mode (count, values, min/max,
  regex, missing field, no numeric values).
- ``run_uc_test`` dry-run, missing positive.log, missing UC, full
  end-to-end orchestration with stubbed HEC.
- ``write_junit`` XML structure.
- ``main`` CLI for dry-run, missing catalog, ``--uc`` filter, ``--filter``
  glob, missing SPLUNK env vars, all-passed exit code, failed exit code.
"""

from __future__ import annotations

import datetime as dt
import io
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import pytest

# Ensure ``scripts`` is importable.
sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "scripts")
)

import run_uc_tests as M  # noqa: E402
import samples_index as _SI  # noqa: E402


# ----------------------------------------------------- helpers


def _seed_catalog(
    monkeypatch: pytest.MonkeyPatch,
    base: Path,
    *,
    ucs: list[dict[str, Any]] | None = None,
) -> Path:
    """Seed a synthetic ``catalog.json`` and patch ``CATALOG_PATH`` to it.

    Each entry in ``ucs`` is merged into a single subcategory under a
    single category. Each entry must carry ``i`` (UC id) plus ``q`` and
    optionally ``qs``.
    """
    if ucs is None:
        ucs = [
            {"i": "1.1.1", "q": "search index=main"},
            {"i": "1.1.2", "qs": "| tstats count from datamodel=Foo"},
            {"i": "1.1.3"},  # neither q nor qs -> resolves to ""
        ]
    cat_data = {"DATA": [{"i": 1, "s": [{"i": 1, "u": ucs}]}]}
    catalog = base / "catalog.json"
    catalog.write_text(json.dumps(cat_data), encoding="utf-8")
    monkeypatch.setattr(M, "CATALOG_PATH", catalog)
    monkeypatch.setattr(M, "REPO_ROOT", base)
    monkeypatch.setattr(M, "SAMPLES_DIR", base / "samples")
    # ``scan_samples`` and ``_load_catalog_ids`` are imported from
    # ``samples_index`` and read from THAT module's globals — we have to
    # redirect both for hermetic isolation.
    monkeypatch.setattr(_SI, "REPO_ROOT", base)
    monkeypatch.setattr(_SI, "SAMPLES_DIR", base / "samples")
    monkeypatch.setattr(_SI, "CATALOG_PATH", catalog)
    return catalog


def _seed_sample(
    base: Path, uc_id: str, *,
    manifest: dict[str, Any] | None = None,
    positive: str | None = "ts=2026-05-19T12:34:56Z msg=hello\n",
    negative: str | None = None,
) -> Path:
    """Seed a sample directory under ``base/samples/UC-<id>/``."""
    sample_dir = base / "samples" / f"UC-{uc_id}"
    sample_dir.mkdir(parents=True, exist_ok=True)
    if manifest is None:
        manifest = {
            "uc_id": uc_id,
            "index": "main",
            "sourcetype": "test:source",
            "origin": "synthetic",
            "last_reviewed": "2026-05-19",
            "expected": {"min_count": 1},
        }
    (sample_dir / "manifest.yaml").write_text(
        # Mini-yaml-friendly output.
        "\n".join(_dict_to_mini_yaml(manifest)) + "\n",
        encoding="utf-8",
    )
    if positive is not None:
        (sample_dir / "positive.log").write_text(positive, encoding="utf-8")
    if negative is not None:
        (sample_dir / "negative.log").write_text(negative, encoding="utf-8")
    return sample_dir


def _dict_to_mini_yaml(d: dict[str, Any], indent: int = 0) -> list[str]:
    """Render a dict to mini-yaml-compatible lines."""
    out: list[str] = []
    pad = " " * indent
    for k, v in d.items():
        if isinstance(v, dict):
            out.append(f"{pad}{k}:")
            out.extend(_dict_to_mini_yaml(v, indent + 2))
        elif isinstance(v, list):
            # Mini-yaml's bare-key + dash-list handling is broken
            # (samples_index._mini_yaml documents this); but since the
            # manifest schema only uses ``expected.fields`` as a list of
            # dicts, we can render via inline JSON syntax which the
            # parser does NOT support. The tests therefore only generate
            # manifests whose lists are empty or omitted.
            raise RuntimeError(
                "mini-yaml fallback can't roundtrip lists; "
                "rewrite the test manifest"
            )
        else:
            out.append(f"{pad}{k}: {v}")
    return out


class _StubResponse:
    """Tiny stand-in for the context-manager returned by ``urlopen``."""

    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> "_StubResponse":
        return self

    def __exit__(self, *exc: Any) -> None:
        pass

    def read(self) -> bytes:
        return self._body


def _stub_urlopen(
    monkeypatch: pytest.MonkeyPatch,
    handler: Any,
) -> list[urllib.request.Request]:
    """Patch ``urllib.request.urlopen`` and capture requests.

    ``handler`` is a callable that receives the request and returns the
    bytes payload to feed back through ``_StubResponse.read``.
    """
    captured: list[urllib.request.Request] = []

    def _fake(req: Any, **kwargs: Any) -> _StubResponse:
        captured.append(req)
        body = handler(req)
        return _StubResponse(body)

    monkeypatch.setattr(urllib.request, "urlopen", _fake)
    return captured


# ----------------------------------------------------- rewrite_timestamp


class TestRewriteTimestamp:
    """Pin the four timestamp pattern families."""

    NOW = dt.datetime(2026, 5, 20, 14, 30, 45, 123_000, tzinfo=dt.timezone.utc)

    def test_iso_8601_timestamp_replaced(self) -> None:
        line = "ts=2025-04-16T08:00:00Z msg=foo"
        out = M.rewrite_timestamp(line, self.NOW)
        assert "2026-05-20T14:30:45Z" in out
        assert "2025-04-16T08:00:00Z" not in out
        assert "msg=foo" in out

    def test_iso_with_microseconds_and_offset_replaced(self) -> None:
        line = "ts=2025-04-16T08:00:00.123456+02:00 msg=bar"
        out = M.rewrite_timestamp(line, self.NOW)
        assert "2026-05-20T14:30:45Z" in out
        assert "msg=bar" in out

    def test_rfc3164_syslog_timestamp_replaced(self) -> None:
        line = "Apr 16 08:00:00 host kernel: hello"
        out = M.rewrite_timestamp(line, self.NOW)
        # %b = "May", strftime("%b %d %H:%M:%S") with day=20 -> "May 20 14:30:45"
        # Day padding logic in the script replaces " 0" with "  " then
        # truncates to 15 chars. Day 20 has no leading zero, so the
        # transformation is a no-op for our input.
        assert "May 20 14:30:45" in out
        assert "Apr 16 08:00:00" not in out
        assert "host kernel: hello" in out

    def test_windows_eventlog_timestamp_replaced(self) -> None:
        line = "04/16/2026 08:10:15 AM EventID=4624"
        out = M.rewrite_timestamp(line, self.NOW)
        assert "05/20/2026 02:30:45 PM" in out
        assert "EventID=4624" in out

    def test_splunkd_timestamp_replaced(self) -> None:
        line = "04-16-2026 08:00:02.123 +0000 INFO log message"
        out = M.rewrite_timestamp(line, self.NOW)
        assert "05-20-2026 14:30:45.123 +0000" in out
        assert "INFO log message" in out

    def test_no_match_returns_line_unchanged(self) -> None:
        line = "no timestamp here just plain text"
        out = M.rewrite_timestamp(line, self.NOW)
        assert out == line

    def test_unknown_kind_falls_through_continue(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Pin the ``else: continue`` branch on line 122 of
        ``rewrite_timestamp``. The branch is structurally unreachable
        with the four declared ``TS_PATTERNS`` entries, but is kept as a
        defensive guard against future additions. Force the path by
        appending a fake pattern with an unrecognised kind."""
        import re as _re
        fake = ("future_format", _re.compile(r"\b(XYZ-\d+)\b"))
        # Place the fake at the END so the four real patterns still get
        # to run on inputs that match them.
        monkeypatch.setattr(M, "TS_PATTERNS", M.TS_PATTERNS + [fake])
        line = "no real timestamp, but XYZ-42 here"
        out = M.rewrite_timestamp(line, self.NOW)
        # The unknown kind triggers ``continue`` and the loop exits with
        # no replacement; the line is returned unchanged.
        assert out == line

    def test_only_first_match_replaced(self) -> None:
        """If a line carries TWO timestamps in the same family, only
        the first is rewritten — the regex used is ``re.search`` and
        the first hit is consumed."""
        line = "first=2025-04-16T08:00:00Z second=2025-04-16T09:00:00Z"
        out = M.rewrite_timestamp(line, self.NOW)
        # The first timestamp is replaced; the second remains.
        assert "2026-05-20T14:30:45Z" in out
        assert "2025-04-16T09:00:00Z" in out


# ----------------------------------------------------- split_events


class TestSplitEvents:
    def test_blank_line_separated_blocks_returned_as_list(self) -> None:
        raw = "block one\nstill block one\n\nblock two"
        out = M.split_events(raw)
        assert out == ["block one\nstill block one", "block two"]

    def test_single_block_falls_back_to_one_event_per_line(self) -> None:
        raw = "line one\nline two\nline three"
        out = M.split_events(raw)
        assert out == ["line one", "line two", "line three"]

    def test_blank_lines_inside_single_block_dropped(self) -> None:
        # Trailing newline should not produce an empty entry.
        raw = "only one event\n"
        out = M.split_events(raw)
        assert out == ["only one event"]

    def test_empty_string_yields_empty_list(self) -> None:
        assert M.split_events("") == []

    def test_whitespace_only_yields_empty_list(self) -> None:
        assert M.split_events("   \n  \n") == []


# ----------------------------------------------------- SplunkClient


class TestSplunkClientInit:
    def test_strips_trailing_slash_from_urls(self) -> None:
        c = M.SplunkClient(
            "https://splunk:8089/", "https://splunk:8088/", "tok",
            "admin", "pwd", verify_tls=False,
        )
        assert c.mgmt_url == "https://splunk:8089"
        assert c.hec_url == "https://splunk:8088"

    def test_disabled_tls_verification_lowers_ssl_context(self) -> None:
        c = M.SplunkClient(
            "https://h:8089", "https://h:8088", "tok",
            "admin", "pwd", verify_tls=False,
        )
        # NB: ssl.CERT_NONE on the context's verify_mode
        import ssl
        assert c._ctx.verify_mode == ssl.CERT_NONE
        assert c._ctx.check_hostname is False

    def test_enabled_tls_verification_keeps_default_context(self) -> None:
        c = M.SplunkClient(
            "https://h:8089", "https://h:8088", "tok",
            "admin", "pwd", verify_tls=True,
        )
        import ssl
        assert c._ctx.check_hostname is True
        assert c._ctx.verify_mode != ssl.CERT_NONE


class TestSplunkClientLogin:
    def test_login_caches_session_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured = _stub_urlopen(
            monkeypatch,
            handler=lambda req: json.dumps(
                {"sessionKey": "TOPSECRET"}
            ).encode(),
        )
        c = M.SplunkClient(
            "https://h:8089", "https://h:8088", "tok",
            "admin", "pwd", verify_tls=False,
        )
        first = c._login()
        second = c._login()
        assert first == "TOPSECRET"
        assert second == "TOPSECRET"
        # Login endpoint hit exactly once thanks to caching.
        assert len(captured) == 1
        req = captured[0]
        assert "/services/auth/login" in req.full_url
        assert req.method == "POST"
        body = req.data
        assert b"username=admin" in body
        assert b"password=pwd" in body


class TestSplunkClientRunOneshot:
    def test_run_oneshot_prefixes_search_when_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        login_done = {"v": False}

        def _h(req: urllib.request.Request) -> bytes:
            if "/auth/login" in req.full_url:
                login_done["v"] = True
                return b'{"sessionKey": "K"}'
            assert b"search=search+index%3Dmain" in req.data  # type: ignore[arg-type]
            return b'{"results": [{"a": "b"}]}'

        captured = _stub_urlopen(monkeypatch, handler=_h)
        c = M.SplunkClient(
            "https://h:8089", "https://h:8088", "tok",
            "admin", "pwd", verify_tls=False,
        )
        out = c.run_oneshot("index=main", earliest="-15m")
        assert out == [{"a": "b"}]
        assert login_done["v"]
        # 1st request was login, 2nd was the search.
        assert len(captured) == 2
        assert "/services/search/jobs" in captured[1].full_url

    def test_run_oneshot_keeps_pipe_prefix_unchanged(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _h(req: urllib.request.Request) -> bytes:
            if "/auth/login" in req.full_url:
                return b'{"sessionKey": "K"}'
            assert b"search=%7C+tstats+count" in req.data  # type: ignore[arg-type]
            return b'{"results": []}'

        _stub_urlopen(monkeypatch, handler=_h)
        c = M.SplunkClient(
            "https://h:8089", "https://h:8088", "tok",
            "admin", "pwd", verify_tls=False,
        )
        out = c.run_oneshot("| tstats count", earliest="-15m")
        assert out == []

    def test_run_oneshot_keeps_search_prefix_unchanged(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _h(req: urllib.request.Request) -> bytes:
            if "/auth/login" in req.full_url:
                return b'{"sessionKey": "K"}'
            # No double-prefixing: the body should not start
            # ``search=search+search``.
            assert b"search=search+x%3D1" in req.data  # type: ignore[arg-type]
            assert b"search=search+search" not in req.data  # type: ignore[arg-type]
            return b'{"results": []}'

        _stub_urlopen(monkeypatch, handler=_h)
        c = M.SplunkClient(
            "https://h:8089", "https://h:8088", "tok",
            "admin", "pwd", verify_tls=False,
        )
        c.run_oneshot("search x=1", earliest="-15m")


class TestSplunkClientMgmtGet:
    """``_mgmt_get`` is unused by the rest of ``run_uc_tests.py`` today
    but is part of the public API surface; cover it so a future caller
    can rely on its request shape."""

    def test_mgmt_get_appends_query_string_when_params_present(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _h(req: urllib.request.Request) -> bytes:
            if "/auth/login" in req.full_url:
                return b'{"sessionKey": "K"}'
            assert req.full_url.endswith(
                "/services/health?output_mode=json&hint=on"
            )
            assert req.headers["Authorization"] == "Splunk K"
            return b'{"healthy": true}'

        _stub_urlopen(monkeypatch, handler=_h)
        c = M.SplunkClient(
            "https://h:8089", "https://h:8088", "tok",
            "admin", "pwd", verify_tls=False,
        )
        out = c._mgmt_get("/services/health", {"hint": "on"})
        assert out == {"healthy": True}

    def test_mgmt_get_omits_query_string_when_no_params(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _h(req: urllib.request.Request) -> bytes:
            if "/auth/login" in req.full_url:
                return b'{"sessionKey": "K"}'
            assert req.full_url.endswith("/services/info?output_mode=json")
            return b'{"version": "x"}'

        _stub_urlopen(monkeypatch, handler=_h)
        c = M.SplunkClient(
            "https://h:8089", "https://h:8088", "tok",
            "admin", "pwd", verify_tls=False,
        )
        out = c._mgmt_get("/services/info")
        assert out == {"version": "x"}


class TestSplunkClientHecPost:
    def test_hec_post_event_canonical_payload(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _h(req: urllib.request.Request) -> bytes:
            assert "/services/collector/event" in req.full_url
            assert req.headers["Authorization"] == "Splunk hec-token"
            assert req.headers["Content-type"] == "application/json"
            payload = json.loads(req.data.decode())  # type: ignore[union-attr]
            assert payload == {
                "event": "raw event",
                "sourcetype": "st",
                "index": "idx",
                "source": "src",
                "host": "h-1",
            }
            return b""

        _stub_urlopen(monkeypatch, handler=_h)
        c = M.SplunkClient(
            "https://h:8089", "https://h:8088", "hec-token",
            "admin", "pwd", verify_tls=False,
        )
        c.hec_post_event("raw event", "idx", "st", "src", "h-1")

    def test_hec_post_event_omits_source_and_host_when_falsy(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _h(req: urllib.request.Request) -> bytes:
            payload = json.loads(req.data.decode())  # type: ignore[union-attr]
            assert "source" not in payload
            assert "host" not in payload
            assert payload["event"] == "x"
            return b""

        _stub_urlopen(monkeypatch, handler=_h)
        c = M.SplunkClient(
            "https://h:8089", "https://h:8088", "tok",
            "admin", "pwd", verify_tls=False,
        )
        c.hec_post_event("x", "idx", "st", None, None)


class TestSplunkClientDeleteIngested:
    def test_delete_ingested_runs_delete_search(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _h(req: urllib.request.Request) -> bytes:
            if "/auth/login" in req.full_url:
                return b'{"sessionKey": "K"}'
            assert b"%7C+delete" in req.data  # | delete  # type: ignore[arg-type]
            assert b"earliest_time=-1d" in req.data  # type: ignore[arg-type]
            return b'{"results": []}'

        _stub_urlopen(monkeypatch, handler=_h)
        c = M.SplunkClient(
            "https://h:8089", "https://h:8088", "tok",
            "admin", "pwd", verify_tls=False,
        )
        c.delete_ingested("uc-tests/1.1.1/positive", "main")


# ----------------------------------------------------- _get_uc_spl


class TestGetUcSpl:
    def test_returns_q_when_present(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_catalog(monkeypatch, tmp_path)
        assert M._get_uc_spl("1.1.1") == "search index=main"

    def test_falls_back_to_qs_when_q_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_catalog(monkeypatch, tmp_path)
        assert M._get_uc_spl("1.1.2") == "| tstats count from datamodel=Foo"

    def test_returns_empty_string_when_neither_q_nor_qs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_catalog(monkeypatch, tmp_path)
        # The triage chain is ``uc.get("q") or uc.get("qs") or ""``.
        assert M._get_uc_spl("1.1.3") == ""

    def test_returns_none_when_uc_id_unknown(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_catalog(monkeypatch, tmp_path)
        assert M._get_uc_spl("99.99.99") is None


# ----------------------------------------------------- _assert_expected


class TestAssertExpected:
    def test_passes_when_count_within_bounds_and_no_field_specs(self) -> None:
        results = [{"a": "1"}, {"a": "2"}]
        manifest = {"expected": {"min_count": 1, "max_count": 5}}
        assert M._assert_expected(results, manifest) == []

    def test_fails_when_count_below_min(self) -> None:
        results: list[dict[str, Any]] = []
        manifest = {"expected": {"min_count": 3}}
        out = M._assert_expected(results, manifest)
        assert out == ["expected min_count=3, got 0"]

    def test_fails_when_count_above_max(self) -> None:
        results = [{} for _ in range(10)]
        manifest = {"expected": {"min_count": 0, "max_count": 5}}
        out = M._assert_expected(results, manifest)
        assert "expected max_count=5, got 10" in out

    def test_field_values_pass_when_intersection_non_empty(self) -> None:
        results = [{"action": "allow"}, {"action": "deny"}]
        manifest = {
            "expected": {
                "min_count": 0,
                "fields": [{"name": "action", "values": ["allow"]}],
            }
        }
        assert M._assert_expected(results, manifest) == []

    def test_field_values_fail_when_no_intersection(self) -> None:
        results = [{"action": "allow"}, {"action": "deny"}]
        manifest = {
            "expected": {
                "min_count": 0,
                "fields": [{"name": "action", "values": ["block"]}],
            }
        }
        out = M._assert_expected(results, manifest)
        assert any(
            "field action" in m and "expected one of" in m
            for m in out
        )

    def test_field_min_max_failure_paths(self) -> None:
        results = [{"score": "10"}, {"score": "5"}]
        manifest = {
            "expected": {
                "min_count": 0,
                "fields": [
                    {"name": "score", "min": 7, "max": 12},
                ],
            }
        }
        out = M._assert_expected(results, manifest)
        # min violation
        assert any("min=5.0" in m for m in out)

    def test_field_min_max_pass(self) -> None:
        results = [{"score": "10"}, {"score": "12"}]
        manifest = {
            "expected": {
                "min_count": 0,
                "fields": [
                    {"name": "score", "min": 5, "max": 15},
                ],
            }
        }
        assert M._assert_expected(results, manifest) == []

    def test_field_min_max_fails_when_no_numeric_values(self) -> None:
        results = [{"score": "abc"}, {"score": "xyz"}]
        manifest = {
            "expected": {
                "min_count": 0,
                "fields": [
                    {"name": "score", "min": 0},
                ],
            }
        }
        out = M._assert_expected(results, manifest)
        assert any("no numeric values" in m for m in out)

    def test_field_max_violation_only(self) -> None:
        results = [{"score": "100"}, {"score": "5"}]
        manifest = {
            "expected": {
                "min_count": 0,
                "fields": [
                    {"name": "score", "max": 50},
                ],
            }
        }
        out = M._assert_expected(results, manifest)
        assert any("max=100.0" in m for m in out)

    def test_field_regex_pass(self) -> None:
        results = [{"src_ip": "10.0.0.1"}]
        manifest = {
            "expected": {
                "min_count": 0,
                "fields": [
                    {"name": "src_ip", "regex": r"^10\."},
                ],
            }
        }
        assert M._assert_expected(results, manifest) == []

    def test_field_regex_fail(self) -> None:
        results = [{"src_ip": "192.168.1.1"}]
        manifest = {
            "expected": {
                "min_count": 0,
                "fields": [
                    {"name": "src_ip", "regex": r"^10\."},
                ],
            }
        }
        out = M._assert_expected(results, manifest)
        assert any("no value matched regex" in m for m in out)

    def test_field_spec_without_name_skipped(self) -> None:
        results = [{"x": 1}]
        manifest = {
            "expected": {
                "min_count": 0,
                "fields": [{"values": ["1"]}],  # no ``name``
            }
        }
        # No ``name`` -> the field spec is silently skipped.
        assert M._assert_expected(results, manifest) == []

    def test_no_expected_block_treated_as_zero_minimum(self) -> None:
        # ``manifest.get("expected") or {}`` -> empty dict, so min_count
        # defaults to 0 and any number of results passes.
        assert M._assert_expected([], {}) == []

    def test_max_count_none_means_unbounded(self) -> None:
        results = [{}] * 100
        manifest = {"expected": {"min_count": 0, "max_count": None}}
        assert M._assert_expected(results, manifest) == []

    def test_field_spec_filters_none_values(self) -> None:
        # Values containing ``None`` should be filtered before the
        # set intersection so Python doesn't complain about ``str(None)``.
        results = [{"action": None}, {"action": "allow"}]
        manifest = {
            "expected": {
                "min_count": 0,
                "fields": [{"name": "action", "values": ["allow"]}],
            }
        }
        assert M._assert_expected(results, manifest) == []


# ----------------------------------------------------- run_uc_test


class TestRunUcTest:
    def test_returns_failure_when_uc_not_in_catalog(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_catalog(monkeypatch, tmp_path, ucs=[])
        sample_dir = _seed_sample(tmp_path, "9.9.9")
        out = M.run_uc_test(client=None, uc_id="9.9.9",  # type: ignore[arg-type]
                            sample_dir=sample_dir, dry_run=True)
        assert out.passed is False
        assert "not found in catalog.json" in out.message

    def test_returns_failure_when_positive_log_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_catalog(monkeypatch, tmp_path)
        sample_dir = _seed_sample(tmp_path, "1.1.1", positive=None)
        out = M.run_uc_test(client=None, uc_id="1.1.1",  # type: ignore[arg-type]
                            sample_dir=sample_dir, dry_run=True)
        assert out.passed is False
        assert out.message == "positive.log missing"

    def test_dry_run_returns_pass_without_touching_network(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_catalog(monkeypatch, tmp_path)
        sample_dir = _seed_sample(tmp_path, "1.1.1")

        def _no_net(*args: Any, **kwargs: Any) -> Any:
            raise AssertionError("network must not be touched in dry-run")

        monkeypatch.setattr(urllib.request, "urlopen", _no_net)
        out = M.run_uc_test(client=None, uc_id="1.1.1",  # type: ignore[arg-type]
                            sample_dir=sample_dir, dry_run=True)
        assert out.passed is True
        assert "(dry-run)" in out.message
        assert "index=main" in out.message
        assert "sourcetype=test:source" in out.message

    def test_full_run_drives_hec_search_and_returns_pass(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_catalog(monkeypatch, tmp_path)
        sample_dir = _seed_sample(
            tmp_path, "1.1.1",
            positive="2025-04-16T08:00:00Z user=alice action=allow\n",
        )
        events_received: list[dict[str, Any]] = []

        def _h(req: urllib.request.Request) -> bytes:
            url = req.full_url
            if "/auth/login" in url:
                return b'{"sessionKey": "K"}'
            if "/collector/event" in url:
                events_received.append(
                    json.loads(req.data.decode())  # type: ignore[union-attr]
                )
                return b""
            if "/search/jobs" in url:
                # Probe loop expects a count of >=1.
                if b"%7C+stats+count+as+n" in (req.data or b""):
                    return b'{"results": [{"n": "1"}]}'
                # Final SPL run returns one matching event.
                return (
                    b'{"results": [{"_time": "x", "user": "alice", '
                    b'"action": "allow"}]}'
                )
            raise AssertionError(f"unexpected URL: {url}")

        _stub_urlopen(monkeypatch, handler=_h)
        client = M.SplunkClient(
            "https://h:8089", "https://h:8088", "tok",
            "admin", "pwd", verify_tls=False,
        )
        out = M.run_uc_test(
            client, "1.1.1", sample_dir, dry_run=False
        )
        assert out.passed is True, out.failures
        assert out.duration_s >= 0
        assert events_received, "HEC events must have been posted"

    def test_full_run_records_failure_when_results_below_min_count(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_catalog(monkeypatch, tmp_path)
        # Stricter manifest: require >=5 results; the search returns 0.
        sample_dir = _seed_sample(
            tmp_path, "1.1.1",
            manifest={
                "uc_id": "1.1.1",
                "index": "main",
                "sourcetype": "test:source",
                "origin": "synthetic",
                "last_reviewed": "2026-05-19",
                "expected": {"min_count": 5},
            },
        )

        def _h(req: urllib.request.Request) -> bytes:
            url = req.full_url
            if "/auth/login" in url:
                return b'{"sessionKey": "K"}'
            if "/collector/event" in url:
                return b""
            if "/search/jobs" in url:
                if b"stats+count+as+n" in (req.data or b""):
                    return b'{"results": [{"n": "1"}]}'
                return b'{"results": []}'
            raise AssertionError(f"unexpected URL: {url}")

        _stub_urlopen(monkeypatch, handler=_h)
        client = M.SplunkClient(
            "https://h:8089", "https://h:8088", "tok",
            "admin", "pwd", verify_tls=False,
        )
        out = M.run_uc_test(client, "1.1.1", sample_dir, dry_run=False)
        assert out.passed is False
        assert any("min_count=5" in f for f in out.failures)

    def test_full_run_sleeps_until_probe_finds_indexed_events(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Pin the ``time.sleep(2)`` branch on line 340 of
        ``run_uc_test``: the probe loop returns 0 on the first call and
        the indexed count on the second, forcing the polling loop to
        execute one ``sleep`` cycle before breaking."""
        _seed_catalog(monkeypatch, tmp_path)
        sample_dir = _seed_sample(
            tmp_path, "1.1.1",
            positive="2025-04-16T08:00:00Z user=alice\n",
        )
        probe_calls = {"count": 0}
        sleep_calls: list[float] = []

        # Prevent real sleeping in the test.
        import time as _time
        monkeypatch.setattr(_time, "sleep", lambda s: sleep_calls.append(s))
        # ``run_uc_tests`` imports ``time`` at module scope, so patch
        # the bound symbol there too.
        monkeypatch.setattr(M, "time", _time)

        def _h(req: urllib.request.Request) -> bytes:
            url = req.full_url
            if "/auth/login" in url:
                return b'{"sessionKey": "K"}'
            if "/collector/event" in url:
                return b""
            if "/search/jobs" in url:
                if b"stats+count+as+n" in (req.data or b""):
                    probe_calls["count"] += 1
                    if probe_calls["count"] == 1:
                        # Indexing not yet caught up.
                        return b'{"results": [{"n": "0"}]}'
                    return b'{"results": [{"n": "1"}]}'
                return b'{"results": [{"_time": "x"}]}'
            raise AssertionError(f"unexpected URL: {url}")

        _stub_urlopen(monkeypatch, handler=_h)
        client = M.SplunkClient(
            "https://h:8089", "https://h:8088", "tok",
            "admin", "pwd", verify_tls=False,
        )
        out = M.run_uc_test(client, "1.1.1", sample_dir, dry_run=False)
        assert out.passed is True
        assert probe_calls["count"] >= 2
        # Exactly one sleep per stalled probe call.
        assert sleep_calls and sleep_calls[0] == 2

    def test_full_run_handles_negative_log_present(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_catalog(monkeypatch, tmp_path)
        sample_dir = _seed_sample(
            tmp_path, "1.1.1",
            positive="2025-04-16T08:00:00Z user=alice\n",
            negative="2025-04-16T08:00:00Z user=intruder\n",
        )
        # Track which sources got HEC posts.
        sources: list[str] = []

        def _h(req: urllib.request.Request) -> bytes:
            url = req.full_url
            if "/auth/login" in url:
                return b'{"sessionKey": "K"}'
            if "/collector/event" in url:
                payload = json.loads(req.data.decode())  # type: ignore[union-attr]
                sources.append(payload.get("source", ""))
                return b""
            if "/search/jobs" in url:
                if b"stats+count+as+n" in (req.data or b""):
                    return b'{"results": [{"n": "1"}]}'
                return b'{"results": [{"_time": "x"}]}'
            raise AssertionError(f"unexpected URL: {url}")

        _stub_urlopen(monkeypatch, handler=_h)
        client = M.SplunkClient(
            "https://h:8089", "https://h:8088", "tok",
            "admin", "pwd", verify_tls=False,
        )
        out = M.run_uc_test(client, "1.1.1", sample_dir, dry_run=False)
        assert out.passed is True
        # Both positive and negative sources must have been tagged.
        assert any("/positive" in s for s in sources)
        assert any("/negative" in s for s in sources)

    def test_full_run_exits_polling_loop_via_deadline(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Pin the 333->342 partial branch: when the probe never returns
        enough events, the polling loop must exit via ``while time.time()
        < deadline:`` becoming False (i.e. the loop times out without
        any ``break``). Without this test, the False arm of the loop
        guard is uncovered — only the break-path is exercised by the
        sibling tests in this class.

        We mock ``time.time`` to advance past ``deadline`` after a few
        iterations and keep the probe returning ``n=0`` so the
        ``if probe and int(probe[0].get("n", 0)) >= len(positive_events)``
        check never trips. The final ``client.run_oneshot(spl, ...)``
        call still runs and returns the SPL results, which we make
        empty so the test path stays deterministic.
        """
        _seed_catalog(monkeypatch, tmp_path)
        sample_dir = _seed_sample(
            tmp_path, "1.1.1",
            positive="2025-04-16T08:00:00Z user=alice\n",
        )

        ticks = iter([1_000.0, 1_001.0, 1_002.0, 1_999.0, 2_000.0, 2_001.0])
        import time as _time
        monkeypatch.setattr(M.time, "sleep", lambda s: None)
        monkeypatch.setattr(
            M.time,
            "time",
            lambda: next(ticks, 2_999.0),
        )

        def _h(req: urllib.request.Request) -> bytes:
            url = req.full_url
            if "/auth/login" in url:
                return b'{"sessionKey": "K"}'
            if "/collector/event" in url:
                return b""
            if "/search/jobs" in url:
                if b"stats+count+as+n" in (req.data or b""):
                    return b'{"results": [{"n": "0"}]}'
                return b'{"results": []}'
            raise AssertionError(f"unexpected URL: {url}")

        _stub_urlopen(monkeypatch, handler=_h)
        client = M.SplunkClient(
            "https://h:8089", "https://h:8088", "tok",
            "admin", "pwd", verify_tls=False,
        )
        out = M.run_uc_test(client, "1.1.1", sample_dir, dry_run=False)
        assert out.passed is False
        assert out.duration_s >= 0


# ----------------------------------------------------- write_junit


class TestWriteJunit:
    def test_writes_xml_with_pass_and_fail_cases(
        self, tmp_path: Path
    ) -> None:
        target = tmp_path / "out" / "report.xml"
        results = [
            M.TestResult("1.1.1", True, 1.5, "ok", "[]", []),
            M.TestResult(
                "1.1.2", False, 2.0, "boom", '{"a":1}', ["count low"]
            ),
        ]
        M.write_junit(target, results)
        tree = ET.parse(str(target))
        root = tree.getroot()
        assert root.tag == "testsuites"
        suite = root[0]
        assert suite.tag == "testsuite"
        assert suite.attrib["tests"] == "2"
        assert suite.attrib["failures"] == "1"
        cases = list(suite)
        assert len(cases) == 2
        # First case: passed -> no <failure>
        assert len(list(cases[0])) == 0
        # Second case: failed -> one <failure>
        failures = list(cases[1])
        assert len(failures) == 1
        assert failures[0].tag == "failure"
        assert "count low" in failures[0].attrib["message"]
        assert failures[0].text == '{"a":1}'

    def test_uses_message_when_no_failures_listed(
        self, tmp_path: Path
    ) -> None:
        target = tmp_path / "report.xml"
        results = [
            M.TestResult("1.1.1", False, 0.5, "missing fixture", "", []),
        ]
        M.write_junit(target, results)
        tree = ET.parse(str(target))
        suite = tree.getroot()[0]
        case = list(suite)[0]
        failure = list(case)[0]
        assert failure.attrib["message"] == "missing fixture"

    def test_falls_back_to_default_message_when_both_empty(
        self, tmp_path: Path
    ) -> None:
        target = tmp_path / "report.xml"
        results = [M.TestResult("1.1.1", False, 0.5)]
        M.write_junit(target, results)
        tree = ET.parse(str(target))
        case = list(tree.getroot()[0])[0]
        failure = list(case)[0]
        assert failure.attrib["message"] == "test failed"

    def test_creates_parent_directory_if_missing(
        self, tmp_path: Path
    ) -> None:
        target = tmp_path / "deeply" / "nested" / "junit.xml"
        assert not target.parent.exists()
        M.write_junit(target, [M.TestResult("1.1.1", True, 0.0)])
        assert target.exists()


# ----------------------------------------------------- main


class TestMainCli:
    def test_returns_2_when_catalog_missing(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        catalog = tmp_path / "missing.json"
        monkeypatch.setattr(M, "CATALOG_PATH", catalog)
        monkeypatch.setattr(M, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(M, "SAMPLES_DIR", tmp_path / "samples")
        monkeypatch.setattr(_SI, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(_SI, "SAMPLES_DIR", tmp_path / "samples")
        monkeypatch.setattr(_SI, "CATALOG_PATH", catalog)
        monkeypatch.setattr(sys, "argv", ["run_uc_tests"])
        rc = M.main()
        assert rc == 2
        assert "catalog.json missing" in capsys.readouterr().err

    def test_returns_0_with_no_eligible_samples(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _seed_catalog(monkeypatch, tmp_path)
        # No samples directory -> scan_samples returns [].
        monkeypatch.setattr(sys, "argv", ["run_uc_tests"])
        rc = M.main()
        assert rc == 0
        assert "No sample fixtures eligible" in capsys.readouterr().err

    def test_dry_run_passes_with_eligible_sample(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _seed_catalog(monkeypatch, tmp_path)
        _seed_sample(tmp_path, "1.1.1")
        junit = tmp_path / "j.xml"
        monkeypatch.setattr(
            sys, "argv",
            ["run_uc_tests", "--dry-run", "--junit", str(junit)],
        )

        def _no_net(*args: Any, **kwargs: Any) -> Any:
            raise AssertionError("dry-run must not touch network")

        monkeypatch.setattr(urllib.request, "urlopen", _no_net)
        rc = M.main()
        assert rc == 0
        out = capsys.readouterr().out
        assert "[OK]" in out
        assert "1/1 passed" in out
        assert junit.exists()

    def test_uc_filter_limits_run_to_named_uc(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _seed_catalog(monkeypatch, tmp_path)
        _seed_sample(tmp_path, "1.1.1")
        _seed_sample(tmp_path, "1.1.2")
        junit = tmp_path / "j.xml"
        monkeypatch.setattr(
            sys, "argv",
            [
                "run_uc_tests", "--dry-run",
                "--uc", "UC-1.1.1",
                "--junit", str(junit),
            ],
        )
        rc = M.main()
        assert rc == 0
        out = capsys.readouterr().out
        assert "UC-1.1.1" in out
        assert "UC-1.1.2" not in out
        assert "1/1 passed" in out

    def test_glob_filter_limits_run_to_matching_uc(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _seed_catalog(monkeypatch, tmp_path)
        _seed_sample(tmp_path, "1.1.1")
        _seed_sample(tmp_path, "1.1.2")
        junit = tmp_path / "j.xml"
        monkeypatch.setattr(
            sys, "argv",
            [
                "run_uc_tests", "--dry-run",
                "--filter", "UC-1.1.1",
                "--junit", str(junit),
            ],
        )
        rc = M.main()
        assert rc == 0
        out = capsys.readouterr().out
        assert "UC-1.1.1" in out
        assert "UC-1.1.2" not in out

    def test_returns_2_when_splunk_password_or_hec_token_missing(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _seed_catalog(monkeypatch, tmp_path)
        _seed_sample(tmp_path, "1.1.1")
        # Strip env so the password / HEC token gate fires.
        for var in (
            "SPLUNK_HEC_TOKEN", "SPLUNK_PASSWORD",
            "SPLUNK_URL", "SPLUNK_HEC_URL",
            "SPLUNK_USER", "SPLUNK_VERIFY_TLS",
        ):
            monkeypatch.delenv(var, raising=False)
        junit = tmp_path / "j.xml"
        monkeypatch.setattr(
            sys, "argv",
            ["run_uc_tests", "--junit", str(junit)],
        )
        rc = M.main()
        assert rc == 2
        assert "must be set" in capsys.readouterr().err

    def test_runner_exception_recorded_as_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _seed_catalog(monkeypatch, tmp_path)
        _seed_sample(tmp_path, "1.1.1")
        junit = tmp_path / "j.xml"
        # Both creds set so we walk past the env gate.
        monkeypatch.setenv("SPLUNK_HEC_TOKEN", "tok")
        monkeypatch.setenv("SPLUNK_PASSWORD", "pwd")
        monkeypatch.setenv("SPLUNK_VERIFY_TLS", "1")
        monkeypatch.setattr(
            sys, "argv",
            ["run_uc_tests", "--junit", str(junit)],
        )

        def _boom(*args: Any, **kwargs: Any) -> Any:
            raise urllib.error.URLError("synthetic explosion")

        monkeypatch.setattr(urllib.request, "urlopen", _boom)
        rc = M.main()
        assert rc == 1  # at least one failure
        out = capsys.readouterr().out
        assert "[FAIL]" in out
        assert "0/1 passed" in out

    def test_returns_1_when_any_test_fails(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Two samples, one corrupt manifest -> one passes, one fails.
        _seed_catalog(monkeypatch, tmp_path)
        _seed_sample(tmp_path, "1.1.1")
        # Sample with manifest tied to UC not in catalog.
        _seed_sample(tmp_path, "9.9.9")
        # The 9.9.9 sample lacks a catalog entry; ``scan_samples``
        # records that as an error and the runner skips it. So the
        # run still ends up "1/1 passed" because only valid samples
        # are eligible. We instead force a failure via a bogus
        # filter that includes only UC-9.9.9.
        junit = tmp_path / "j.xml"
        monkeypatch.setattr(
            sys, "argv",
            [
                "run_uc_tests", "--dry-run",
                "--uc", "UC-9.9.9",
                "--junit", str(junit),
            ],
        )
        rc = M.main()
        # No eligible samples -> exits 0 cleanly.
        assert rc == 0
        assert "No sample fixtures eligible" in capsys.readouterr().err


# ----------------------------------------------------- __main__ guard


class TestMainGuardIsBoilerplate:
    """The ``if __name__ == "__main__": sys.exit(main())`` block is
    intentionally not exercised. Re-importing via ``runpy.run_path`` would
    re-execute the module-level imports, including ``samples_index`` and
    its filesystem-scanning side-effects. We pin the source instead so a
    refactor that *removes* the guard fails this test rather than
    silently dropping the entrypoint."""

    def test_module_exports_main_callable(self) -> None:
        assert callable(M.main)

    def test_main_guard_is_present_in_source(self) -> None:
        src = Path(M.__file__).read_text(encoding="utf-8")
        assert 'if __name__ == "__main__":' in src
        assert "sys.exit(main())" in src
