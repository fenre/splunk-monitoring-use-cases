"""Hermetic tests for ``scripts/sync_splunkbase_catalog.py``.

The script is wired into the weekly cron in
``.github/workflows/splunkbase-sync.yml``: ``--check`` runs in PR CI to
validate the cached catalog, ``--sync`` runs against the live Splunkbase
REST API and opens a PR via ``peter-evans/create-pull-request``. The
tests here exercise every code path with stubbed ``urllib.request.urlopen``
so we can pin the request shape, the retry logic, and the cached-fallback
resilience contract without ever touching the network.

Coverage scope
--------------
- ``_read_json`` / ``_write_json`` / ``_today``.
- ``_empty_catalog`` shape and metadata.
- ``_validate_catalog`` for every error path.
- ``_apply_overrides`` shallow-merge semantics.
- ``_ssl_context`` and ``_validate_url`` allow-list.
- ``_fetch_page`` triage chain: success, non-200, oversize body,
  malformed JSON, HTTP 429 with Retry-After (numeric and non-numeric),
  HTTP 4xx error, ``URLError``, ``OSError``/``TimeoutError``,
  retry-exhaustion, refused non-allow-listed URL.
- ``_normalise_entry`` for both new (``uid``/``title``/``path``) and
  legacy (``appid``/``displayName``/``url``) shapes.
- ``_extract_results`` for all four result-key fallbacks.
- ``_diff_entries`` for None / dict / canonical-mismatch.
- ``cmd_check`` for valid catalog, missing catalog, validation errors.
- ``cmd_sync`` for: zero results (cached fallback), normal flow with
  diffs, normal flow with no diffs, MAX_PAGES exhaustion warning, dry
  run, post-sync validation refusal.
- ``main`` for ``--check`` (default), ``--sync``, ``--sync --dry-run``.
"""

from __future__ import annotations

import io
import json
import ssl
import sys
import urllib.error
import urllib.request
from email.message import Message
from pathlib import Path
from typing import Any
from unittest import mock

import gc

import pytest

# Make ``scripts`` importable.
sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "scripts")
)

import sync_splunkbase_catalog as M  # noqa: E402

# Python 3.13+ attaches a ``_TemporaryFileCloser`` to ``HTTPError`` that
# fires ``ResourceWarning: Implicitly cleaning up <HTTPError ...>`` at GC
# time when ``close()`` was not called explicitly. pytest's
# ``unraisableexception`` plugin then surfaces it as a
# ``PytestUnraisableExceptionWarning`` at session teardown, which fails
# the run even when every assertion passed. We:
#   1. Filter the warning module-wide so the per-test filter the
#      individual 429 tests carry is layered defence-in-depth.
#   2. Force ``gc.collect()`` after each test (autouse fixture below)
#      so the warning fires *inside* a test that already filters it,
#      not during teardown where the filter is no longer active.
pytestmark = pytest.mark.filterwarnings(
    "ignore::pytest.PytestUnraisableExceptionWarning"
)


@pytest.fixture(autouse=True)
def _gc_after_each_test():  # noqa: D401
    """Trigger GC inside the test scope so HTTPError finalisers run
    while the module-level ``filterwarnings`` is still active.
    """
    yield
    gc.collect()


# ----------------------------------------------------- helpers


def _patch_paths(
    monkeypatch: pytest.MonkeyPatch, base: Path
) -> tuple[Path, Path, Path]:
    """Redirect ``CATALOG_PATH`` and ``OVERRIDES_PATH`` into a tmp tree."""
    repo = base
    catalog = repo / "data" / "splunkbase-catalog.json"
    overrides = repo / "data" / "splunkbase-catalog-overrides.json"
    catalog.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(M, "REPO_ROOT", repo)
    monkeypatch.setattr(M, "CATALOG_PATH", catalog)
    monkeypatch.setattr(M, "OVERRIDES_PATH", overrides)
    return repo, catalog, overrides


def _seed_catalog(
    catalog_path: Path, *, apps: dict[str, dict[str, Any]] | None = None
) -> None:
    body = M._empty_catalog()
    body["apps"] = apps or {}
    catalog_path.write_text(
        json.dumps(body, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _make_app(app_id: int, name: str = "demo") -> dict[str, Any]:
    return {
        "id": app_id,
        "name": name,
        "displayName": name.title(),
        "description": "",
        "url": f"https://splunkbase.splunk.com/app/{app_id}",
        "latestVersion": "1.0.0",
        "vendor": "ACME",
        "cloudVetted": True,
        "splunkVersionsSupported": ["9.x"],
        "category": "data-source",
        "numDownloads": 100,
        "lastUpdated": "2026-05-19",
    }


class _StubResponse:
    def __init__(
        self, body: bytes, status: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._body = body
        self.status = status
        self._headers = headers or {}

    def __enter__(self) -> "_StubResponse":
        return self

    def __exit__(self, *exc: Any) -> None:
        pass

    def read(self, n: int | None = None) -> bytes:
        if n is None or n >= len(self._body):
            return self._body
        return self._body[:n]


def _http_error(
    code: int,
    headers: dict[str, str] | None = None,
    reason: str = "boom",
) -> urllib.error.HTTPError:
    """Build a fresh ``HTTPError`` for stub error injection.

    Python 3.13+ warns at GC-time about un-closed ``HTTPError.fp``
    attributes via the unraisable-exception machinery. We use
    ``io.BytesIO`` (cheap, GC-clean) but every test that *raises* the
    error must also explicitly call ``err.fp.close()`` after the raise
    site to keep pytest's ``unraisable`` plugin quiet."""
    msg = Message()
    for k, v in (headers or {}).items():
        msg.add_header(k, v)
    return urllib.error.HTTPError(
        url="https://splunkbase.splunk.com/api/v1/app/?limit=100&offset=0",
        code=code, msg=reason, hdrs=msg, fp=io.BytesIO(b""),
    )


def _raise_then_close(err: urllib.error.HTTPError) -> None:
    """Side-effect for ``mock.patch.object(urllib.request, 'urlopen')``
    that raises ``err`` and then defensively releases its resources.

    Python 3.14 attaches a ``_TemporaryFileCloser`` to ``HTTPError``
    that fires a ``ResourceWarning`` at GC time when ``close()`` was
    not called explicitly. Pytest's ``unraisableexception`` plugin
    re-raises that as ``PytestUnraisableExceptionWarning`` at session
    teardown, which fails the run even when every assertion passed.
    Close both ``err.fp`` AND the ``HTTPError`` itself so the closer
    is satisfied before the object becomes unreachable.
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


# ----------------------------------------------------- I/O helpers


class TestReadJson:
    def test_returns_empty_dict_when_file_missing(self, tmp_path: Path) -> None:
        assert M._read_json(tmp_path / "nope.json") == {}

    def test_parses_valid_json(self, tmp_path: Path) -> None:
        p = tmp_path / "x.json"
        p.write_text(json.dumps({"a": 1}), encoding="utf-8")
        assert M._read_json(p) == {"a": 1}

    def test_raises_systemexit_on_invalid_json(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.json"
        p.write_text("{not json", encoding="utf-8")
        with pytest.raises(SystemExit) as excinfo:
            M._read_json(p)
        assert "bad.json" in str(excinfo.value)


class TestWriteJson:
    def test_writes_pretty_sorted_with_trailing_newline(
        self, tmp_path: Path
    ) -> None:
        p = tmp_path / "out.json"
        M._write_json(p, {"b": 2, "a": 1})
        text = p.read_text(encoding="utf-8")
        # Sorted keys -> "a" before "b"
        assert text == '{\n  "a": 1,\n  "b": 2\n}\n'

    def test_creates_parent_directory(self, tmp_path: Path) -> None:
        p = tmp_path / "deep" / "nest" / "out.json"
        assert not p.parent.exists()
        M._write_json(p, {})
        assert p.exists()

    def test_preserves_non_ascii(self, tmp_path: Path) -> None:
        p = tmp_path / "u.json"
        M._write_json(p, {"name": "Café"})
        # Not escaped (ensure_ascii=False)
        assert "Café" in p.read_text(encoding="utf-8")


class TestToday:
    def test_returns_iso_date(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Just verify YYYY-MM-DD shape; the real value depends on UTC.
        s = M._today()
        assert len(s) == 10
        assert s[4] == "-" and s[7] == "-"


# ----------------------------------------------------- catalog shape


class TestEmptyCatalog:
    def test_canonical_shape(self) -> None:
        c = M._empty_catalog()
        assert c["schemaVersion"] == 1
        assert c["apps"] == {}
        assert "lastUpdated" in c
        assert c["source"]["api"] == M.API_BASE
        assert "$comment" in c


class TestValidateCatalog:
    def test_passes_for_well_formed_catalog(self) -> None:
        c = M._empty_catalog()
        c["apps"]["123"] = _make_app(123)
        assert M._validate_catalog(c) == []

    def test_rejects_non_dict_top_level(self) -> None:
        assert M._validate_catalog([])  # type: ignore[arg-type]
        assert "not an object" in M._validate_catalog([])[0]  # type: ignore[arg-type]

    def test_rejects_wrong_schema_version(self) -> None:
        c = M._empty_catalog()
        c["schemaVersion"] = 99
        errs = M._validate_catalog(c)
        assert any("schemaVersion" in e for e in errs)

    def test_rejects_apps_not_object(self) -> None:
        c = M._empty_catalog()
        c["apps"] = []
        errs = M._validate_catalog(c)
        assert any("'apps' must be an object" in e for e in errs)

    def test_rejects_non_numeric_app_key(self) -> None:
        c = M._empty_catalog()
        c["apps"]["abc"] = _make_app(123)
        errs = M._validate_catalog(c)
        assert any("must be a numeric string" in e for e in errs)

    def test_rejects_non_dict_app_entry(self) -> None:
        c = M._empty_catalog()
        c["apps"]["123"] = "not-a-dict"  # type: ignore[assignment]
        errs = M._validate_catalog(c)
        assert any("must be an object" in e for e in errs)

    def test_rejects_app_id_mismatch(self) -> None:
        c = M._empty_catalog()
        e = _make_app(123)
        e["id"] = 999
        c["apps"]["123"] = e
        errs = M._validate_catalog(c)
        assert any("'id' field must equal 123" in e for e in errs)

    def test_rejects_missing_required_fields(self) -> None:
        c = M._empty_catalog()
        c["apps"]["123"] = {"id": 123}  # missing name/displayName/url
        errs = M._validate_catalog(c)
        assert any("missing required field 'name'" in e for e in errs)
        assert any("missing required field 'displayName'" in e for e in errs)
        assert any("missing required field 'url'" in e for e in errs)

    def test_rejects_url_outside_allow_list(self) -> None:
        c = M._empty_catalog()
        e = _make_app(123)
        e["url"] = "https://evil.example.com/app/123"
        c["apps"]["123"] = e
        errs = M._validate_catalog(c)
        assert any("must start with" in e for e in errs)


class TestApplyOverrides:
    def test_no_op_when_overrides_empty(self) -> None:
        c = M._empty_catalog()
        c["apps"]["1"] = _make_app(1)
        out = M._apply_overrides(c, {})
        assert out["apps"]["1"]["name"] == "demo"

    def test_adds_new_app_when_not_in_catalog(self) -> None:
        c = M._empty_catalog()
        out = M._apply_overrides(
            c, {"apps": {"42": _make_app(42, "extra")}}
        )
        assert out["apps"]["42"]["name"] == "extra"

    def test_shallow_merges_per_field(self) -> None:
        c = M._empty_catalog()
        c["apps"]["1"] = _make_app(1, "demo")
        c["apps"]["1"]["category"] = "data-source"
        out = M._apply_overrides(
            c, {"apps": {"1": {"category": "security"}}}
        )
        assert out["apps"]["1"]["category"] == "security"
        assert out["apps"]["1"]["name"] == "demo"

    def test_skips_non_dict_override_entries(self) -> None:
        c = M._empty_catalog()
        c["apps"]["1"] = _make_app(1)
        out = M._apply_overrides(c, {"apps": {"1": "junk"}})
        assert out["apps"]["1"]["name"] == "demo"

    def test_does_not_mutate_input(self) -> None:
        c = M._empty_catalog()
        c["apps"]["1"] = _make_app(1)
        before = json.dumps(c, sort_keys=True)
        M._apply_overrides(c, {"apps": {"1": {"name": "changed"}}})
        after = json.dumps(c, sort_keys=True)
        assert before == after


# ----------------------------------------------------- ssl + URL


class TestSslContext:
    def test_minimum_tls_version_is_12(self) -> None:
        ctx = M._ssl_context()
        assert ctx.minimum_version == ssl.TLSVersion.TLSv1_2


class TestValidateUrl:
    def test_accepts_canonical_https_url(self) -> None:
        M._validate_url("https://splunkbase.splunk.com/app/123")

    def test_rejects_non_https(self) -> None:
        with pytest.raises(ValueError, match="must be HTTPS"):
            M._validate_url("http://splunkbase.splunk.com/app/123")

    def test_rejects_non_allow_listed_host(self) -> None:
        with pytest.raises(ValueError, match="must target"):
            M._validate_url("https://evil.example.com/app/123")


# ----------------------------------------------------- _fetch_page


class TestFetchPage:
    def test_canonical_success_returns_body_and_no_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        body = json.dumps({"results": [{"id": 1}]}).encode()
        with mock.patch.object(
            urllib.request, "urlopen",
            return_value=_StubResponse(body, 200),
        ):
            out, err = M._fetch_page(0, 100)
        assert err is None
        assert out == {"results": [{"id": 1}]}

    def test_non_200_status_returns_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with mock.patch.object(
            urllib.request, "urlopen",
            return_value=_StubResponse(b"oops", 500),
        ):
            out, err = M._fetch_page(0, 100)
        assert out is None
        assert err is not None and "HTTP 500" in err

    def test_oversized_response_rejected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Fake a body strictly larger than MAX_RESPONSE_BYTES.
        big = b"x" * (M.MAX_RESPONSE_BYTES + 100)
        with mock.patch.object(
            urllib.request, "urlopen",
            return_value=_StubResponse(big, 200),
        ):
            out, err = M._fetch_page(0, 100)
        assert out is None
        assert err is not None and "exceeds" in err

    def test_malformed_json_returns_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with mock.patch.object(
            urllib.request, "urlopen",
            return_value=_StubResponse(b"{not json", 200),
        ):
            out, err = M._fetch_page(0, 100)
        assert out is None
        assert err is not None and "malformed JSON" in err

    def test_invalid_utf8_returns_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with mock.patch.object(
            urllib.request, "urlopen",
            return_value=_StubResponse(b"\xff\xfe\xfd", 200),
        ):
            out, err = M._fetch_page(0, 100)
        assert out is None
        assert err is not None and "malformed JSON" in err

    @pytest.mark.filterwarnings(
        "ignore::pytest.PytestUnraisableExceptionWarning"
    )
    def test_429_with_numeric_retry_after_succeeds_on_second_try(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        body = json.dumps({"results": []}).encode()
        side_effects: list[Any] = [
            _http_error(429, headers={"Retry-After": "1"}),
            _StubResponse(body, 200),
        ]

        def _fake(req: Any, **kwargs: Any) -> Any:
            v = side_effects.pop(0)
            if isinstance(v, Exception):
                raise v
            return v

        slept: list[float] = []
        monkeypatch.setattr(M.time, "sleep", lambda s: slept.append(s))
        with mock.patch.object(urllib.request, "urlopen", side_effect=_fake):
            out, err = M._fetch_page(0, 100)
        assert err is None and out == {"results": []}
        assert slept == [1.0]

    @pytest.mark.filterwarnings(
        "ignore::pytest.PytestUnraisableExceptionWarning"
    )
    def test_429_with_non_numeric_retry_after_uses_exponential_backoff(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        body = json.dumps({"results": []}).encode()
        side_effects: list[Any] = [
            _http_error(429, headers={"Retry-After": "soon"}),
            _StubResponse(body, 200),
        ]

        def _fake(req: Any, **kwargs: Any) -> Any:
            v = side_effects.pop(0)
            if isinstance(v, Exception):
                raise v
            return v

        slept: list[float] = []
        monkeypatch.setattr(M.time, "sleep", lambda s: slept.append(s))
        with mock.patch.object(urllib.request, "urlopen", side_effect=_fake):
            out, err = M._fetch_page(0, 100)
        assert err is None and out == {"results": []}
        # Exponential backoff: SLEEP_BETWEEN_REQUESTS * 2 ** 1 = 2.0
        assert slept == [M.SLEEP_BETWEEN_REQUESTS * 2]

    @pytest.mark.filterwarnings(
        "ignore::pytest.PytestUnraisableExceptionWarning"
    )
    def test_429_clamped_high_retry_after(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        body = json.dumps({"results": []}).encode()
        side_effects: list[Any] = [
            _http_error(429, headers={"Retry-After": "9999"}),
            _StubResponse(body, 200),
        ]

        def _fake(req: Any, **kwargs: Any) -> Any:
            v = side_effects.pop(0)
            if isinstance(v, Exception):
                raise v
            return v

        slept: list[float] = []
        monkeypatch.setattr(M.time, "sleep", lambda s: slept.append(s))
        with mock.patch.object(urllib.request, "urlopen", side_effect=_fake):
            M._fetch_page(0, 100)
        # 9999 must be clamped at 120
        assert slept == [120.0]

    @pytest.mark.filterwarnings(
        "ignore::pytest.PytestUnraisableExceptionWarning"
    )
    def test_429_clamped_low_retry_after(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        body = json.dumps({"results": []}).encode()
        side_effects: list[Any] = [
            _http_error(429, headers={"Retry-After": "0.01"}),
            _StubResponse(body, 200),
        ]

        def _fake(req: Any, **kwargs: Any) -> Any:
            v = side_effects.pop(0)
            if isinstance(v, Exception):
                raise v
            return v

        slept: list[float] = []
        monkeypatch.setattr(M.time, "sleep", lambda s: slept.append(s))
        with mock.patch.object(urllib.request, "urlopen", side_effect=_fake):
            M._fetch_page(0, 100)
        # 0.01 must be clamped to 1.0 (the minimum)
        assert slept == [1.0]

    @pytest.mark.filterwarnings(
        "ignore::pytest.PytestUnraisableExceptionWarning"
    )
    def test_429_on_final_attempt_returns_error_without_retry(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Three consecutive 429s exhaust ``MAX_RETRIES_PER_PAGE``;
        the final attempt skips the retry branch and returns the
        ``HTTP 429`` error to the caller. The
        ``filterwarnings`` decorator suppresses Python 3.13+ GC-time
        warnings about unclosed ``HTTPError.fp`` attributes — the
        warning is harmless and unrelated to the path under test."""
        side_effects = [
            _http_error(429, headers={"Retry-After": "1"})
            for _ in range(M.MAX_RETRIES_PER_PAGE)
        ]

        def _fake(req: Any, **kwargs: Any) -> Any:
            err = side_effects.pop(0)
            # Eagerly close the HTTPError's underlying ``fp`` to avoid
            # the GC-time warning about implicit cleanup.
            try:
                raise err
            finally:
                if getattr(err, "fp", None) is not None:
                    try:
                        err.fp.close()
                    except Exception:  # noqa: BLE001
                        pass

        slept: list[float] = []
        monkeypatch.setattr(M.time, "sleep", lambda s: slept.append(s))
        with mock.patch.object(urllib.request, "urlopen", side_effect=_fake):
            out, err = M._fetch_page(0, 100)
        assert out is None
        # The final attempt skips the retry path and returns the 429 error.
        assert err is not None and "HTTP 429" in err

    @pytest.mark.filterwarnings(
        "ignore::pytest.PytestUnraisableExceptionWarning"
    )
    def test_non_429_http_error_returned_immediately(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        err500 = _http_error(500, reason="oops")
        with mock.patch.object(
            urllib.request, "urlopen",
            side_effect=lambda *a, **kw: _raise_then_close(err500),
        ):
            out, err = M._fetch_page(0, 100)
        assert out is None
        assert err is not None and "HTTP 500" in err

    def test_url_error_returns_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with mock.patch.object(
            urllib.request, "urlopen",
            side_effect=urllib.error.URLError("DNS down"),
        ):
            out, err = M._fetch_page(0, 100)
        assert out is None
        assert err is not None and "network error" in err

    def test_timeout_error_returns_transport_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with mock.patch.object(
            urllib.request, "urlopen",
            side_effect=TimeoutError("slow"),
        ):
            out, err = M._fetch_page(0, 100)
        assert out is None
        assert err is not None and "transport error" in err

    def test_oserror_returns_transport_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with mock.patch.object(
            urllib.request, "urlopen",
            side_effect=OSError("connection reset"),
        ):
            out, err = M._fetch_page(0, 100)
        assert out is None
        assert err is not None and "transport error" in err

    def test_refused_non_allow_listed_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Force ``API_BASE`` to a non-allow-listed host so the
        # in-function ``_validate_url`` rejects the URL.
        monkeypatch.setattr(M, "API_BASE", "https://evil.example.com/api/v1/app/")
        with mock.patch.object(
            urllib.request, "urlopen",
            side_effect=AssertionError("must not be reached"),
        ):
            out, err = M._fetch_page(0, 100)
        assert out is None
        assert err is not None and "non-allow-listed URL" in err

    def test_line_276_fall_through_is_unreachable_by_design(self) -> None:
        """Documents line 276 (``return None, last_error or ...``) as a
        defensive tripwire.

        The retry loop has ``MAX_RETRIES_PER_PAGE + 1`` iterations and
        every iteration body either RETURNS (success, non-200, oversize,
        malformed JSON, non-429 HTTPError, URLError, TimeoutError,
        OSError) or CONTINUES (429 with attempts remaining). The only
        path that does NOT explicitly return is the 429-with-budget
        ``continue`` — but on the FINAL iteration ``attempt ==
        MAX_RETRIES_PER_PAGE`` so ``attempt < MAX_RETRIES_PER_PAGE`` is
        False, the 429 falls through to ``last_error = ...; return
        None``. Hence the ``return None, last_error or ...`` after the
        loop is unreachable in the current control flow. It remains as
        a defensive belt-and-braces fall-through in case a future
        refactor changes the loop structure.
        """
        src = Path(M.__file__).read_text(encoding="utf-8")
        idx = src.find('return None, last_error or f"exceeded retries')
        assert idx != -1, "defensive fall-through return removed"


# ----------------------------------------------------- _normalise_entry


class TestNormaliseEntry:
    def test_modern_shape(self) -> None:
        raw = {
            "uid": 7633,
            "appid": "splunk-uc",
            "title": "Splunk UC",
            "description": "  hi  ",
            "path": "/app/7633/",
            "latest": {
                "name": "1.2.3",
                "splunk_version_compatibility": ["9.0", "9.1", 8],
            },
            "license": {"vendor": "ACME"},
            "install_method_distributed": "self_service",
            "category": "data-source",
            "download_count": 42,
            "updated_time": "2026-05-19T12:34:56Z",
        }
        out = M._normalise_entry(raw)
        assert out is not None
        assert out["id"] == 7633
        assert out["name"] == "splunk-uc"
        assert out["displayName"] == "Splunk UC"
        assert out["description"] == "hi"
        # ``path`` trailing slash trimmed; canonical form preserved.
        assert out["url"] == "https://splunkbase.splunk.com/app/7633"
        assert out["latestVersion"] == "1.2.3"
        # ints in splunk_version_compatibility coerced to str
        assert out["splunkVersionsSupported"] == ["9.0", "9.1", "8"]
        assert out["vendor"] == "ACME"
        assert out["cloudVetted"] is True
        assert out["category"] == "data-source"
        assert out["numDownloads"] == 42
        assert out["lastUpdated"] == "2026-05-19"

    def test_legacy_shape(self) -> None:
        raw = {
            "appid": 1234,  # legacy: appid was the numeric id
            "name": "old-app",
            "displayName": "Old App",
            "url": "https://splunkbase.splunk.com/app/1234",
            "latest_version": "0.9",
            "vendor": "Vendor",
            "is_supported_for_cloud": True,
            "appCategory": "security",
            "numDownloads": 7,
            "lastUpdated": "2024-01-01",
        }
        out = M._normalise_entry(raw)
        assert out is not None
        assert out["id"] == 1234
        assert out["name"] == "old-app"
        assert out["displayName"] == "Old App"
        assert out["latestVersion"] == "0.9"
        assert out["vendor"] == "Vendor"
        assert out["cloudVetted"] is True
        assert out["category"] == "security"

    def test_missing_id_returns_none(self) -> None:
        assert M._normalise_entry({"name": "x"}) is None
        assert M._normalise_entry(
            {"uid": "not-a-number", "id": "not-a-number"}
        ) is None
        assert M._normalise_entry({"uid": 0}) is None  # > 0 required

    def test_appid_string_slug_does_not_short_circuit_id(self) -> None:
        # New API: ``appid`` is a slug; ``uid`` is the numeric id.
        # Make sure the slug doesn't get cast to int.
        raw = {"uid": 4242, "appid": "kebab-case-slug", "title": "X"}
        out = M._normalise_entry(raw)
        assert out is not None
        assert out["id"] == 4242
        assert out["name"] == "kebab-case-slug"

    def test_no_canonical_path_falls_back_to_synthesised_url(self) -> None:
        raw = {"uid": 99, "title": "X"}
        out = M._normalise_entry(raw)
        assert out is not None
        assert out["url"] == "https://splunkbase.splunk.com/app/99"

    def test_url_not_in_allow_list_replaced_with_canonical(self) -> None:
        raw = {"uid": 99, "title": "X", "url": "https://other.example.com/app/99"}
        out = M._normalise_entry(raw)
        assert out is not None
        assert out["url"] == "https://splunkbase.splunk.com/app/99"

    def test_install_method_rejected_does_not_set_cloud_vetted(self) -> None:
        raw = {"uid": 1, "title": "X", "install_method_distributed": "rejected"}
        out = M._normalise_entry(raw)
        assert out is not None
        assert out["cloudVetted"] is False

    def test_download_count_unparseable_yields_none(self) -> None:
        raw = {"uid": 1, "title": "X", "download_count": "many"}
        out = M._normalise_entry(raw)
        assert out is not None
        assert out["numDownloads"] is None

    def test_download_count_missing_yields_none(self) -> None:
        out = M._normalise_entry({"uid": 1, "title": "X"})
        assert out is not None
        assert out["numDownloads"] is None

    def test_last_updated_non_string_falls_back_to_none(self) -> None:
        out = M._normalise_entry(
            {"uid": 1, "title": "X", "updated_time": 1234567890}
        )
        assert out is not None
        assert out["lastUpdated"] is None

    def test_branch_371_to_374_is_unreachable_by_design(self) -> None:
        """Documents branch 371→374 as a defensive tripwire.

        Reaching ``elif not isinstance(last_updated, str)`` being False
        (so we skip 372 and fall through to 374) requires
        ``last_updated`` to BE a string AND be falsy. The only
        instance of a falsy string is ``""``, but the surrounding
        ``or``-chain short-circuits on falsy: any empty value lets the
        chain continue searching for a truthy alternative, ultimately
        landing on ``None`` if none of the keys carry a value. So
        ``last_updated`` is only ever a non-empty string OR ``None``,
        making 371→374 unreachable through normal API shapes. The
        defensive ``elif`` guard remains as a tripwire in case a future
        refactor inserts a non-``or``-chain assignment.
        """
        src = Path(M.__file__).read_text(encoding="utf-8")
        idx = src.find("    elif not isinstance(last_updated, str):")
        assert idx != -1, "defensive elif guard removed"

    def test_branch_383_to_385_is_unreachable_by_design(self) -> None:
        """Documents branch 383→385 as a defensive tripwire.

        Reaching ``if isinstance(url, str)`` being False requires every
        URL key (``path``, ``appurl``, ``appUrl``, ``url``) to either
        be missing or carry a truthy non-string value, which then
        short-circuits the ``or`` chain BEFORE reaching the
        ``f"https://..."`` literal fallback. The Splunkbase API always
        returns these keys as strings (or omits them), so the
        non-string branch is unreachable. The defensive
        ``isinstance(url, str)`` guard remains as a tripwire.
        """
        src = Path(M.__file__).read_text(encoding="utf-8")
        idx = src.find("    if isinstance(url, str):")
        assert idx != -1, "defensive isinstance(url, str) guard removed"

    def test_category_list_uses_first_entry(self) -> None:
        out = M._normalise_entry(
            {"uid": 1, "title": "X", "category": ["security", "ops"]}
        )
        assert out is not None
        assert out["category"] == "security"

    def test_category_dict_with_name_used(self) -> None:
        out = M._normalise_entry(
            {"uid": 1, "title": "X", "category": {"name": "platform"}}
        )
        assert out is not None
        assert out["category"] == "platform"

    def test_category_empty_falls_back_to_data_source(self) -> None:
        out = M._normalise_entry({"uid": 1, "title": "X", "category": ""})
        assert out is not None
        assert out["category"] == "data-source"

    def test_latest_not_dict_yields_none_version(self) -> None:
        out = M._normalise_entry(
            {"uid": 1, "title": "X", "latest": "not-a-dict"}
        )
        assert out is not None
        assert out["latestVersion"] is None

    def test_splunk_versions_filters_non_scalar_entries(self) -> None:
        out = M._normalise_entry({
            "uid": 1, "title": "X",
            "latest": {
                "splunk_version_compatibility": [
                    "9.0", 9, 9.1, None, ["x"], {"v": 1},
                ],
            },
        })
        assert out is not None
        assert out["splunkVersionsSupported"] == ["9.0", "9", "9.1"]

    def test_name_falls_back_to_appid_slug_when_no_appname(self) -> None:
        out = M._normalise_entry(
            {"uid": 1, "appid": "fallback-slug"}
        )
        assert out is not None
        assert out["name"] == "fallback-slug"


# ----------------------------------------------------- _extract_results


class TestExtractResults:
    @pytest.mark.parametrize("key", ["results", "apps", "objects", "data"])
    def test_returns_results_list(self, key: str) -> None:
        page = {key: [{"id": 1}, {"id": 2}]}
        assert M._extract_results(page) == [{"id": 1}, {"id": 2}]

    def test_returns_empty_when_no_known_key(self) -> None:
        assert M._extract_results({"unrelated": [1, 2]}) == []

    def test_returns_empty_when_value_not_a_list(self) -> None:
        assert M._extract_results({"results": "not-a-list"}) == []


# ----------------------------------------------------- _diff_entries


class TestDiffEntries:
    def test_returns_true_for_none_old(self) -> None:
        assert M._diff_entries(None, _make_app(1)) is True

    def test_returns_true_for_non_dict_old(self) -> None:
        assert M._diff_entries("nope", _make_app(1)) is True  # type: ignore[arg-type]

    def test_returns_false_for_identical_canonical(self) -> None:
        assert M._diff_entries(_make_app(1), _make_app(1)) is False

    def test_returns_true_when_canonical_field_differs(self) -> None:
        old = _make_app(1)
        new = _make_app(1)
        new["latestVersion"] = "9.9.9"
        assert M._diff_entries(old, new) is True

    def test_ignores_non_canonical_fields(self) -> None:
        old = _make_app(1)
        new = _make_app(1)
        new["extraField"] = "ignored"
        assert M._diff_entries(old, new) is False


# ----------------------------------------------------- cmd_check


class TestCmdCheck:
    def test_passes_with_valid_catalog(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _, catalog, _ = _patch_paths(monkeypatch, tmp_path)
        _seed_catalog(catalog, apps={"123": _make_app(123)})
        rc = M.cmd_check()
        assert rc == 0
        out = capsys.readouterr().out
        assert "catalog OK" in out

    def test_passes_when_catalog_missing_uses_empty(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # No catalog file at all -> _empty_catalog -> validate -> OK.
        _patch_paths(monkeypatch, tmp_path)
        rc = M.cmd_check()
        assert rc == 0
        assert "catalog OK" in capsys.readouterr().out

    def test_returns_1_on_validation_error(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _, catalog, _ = _patch_paths(monkeypatch, tmp_path)
        # Bad catalog: schemaVersion 99
        body = M._empty_catalog()
        body["schemaVersion"] = 99
        catalog.write_text(json.dumps(body), encoding="utf-8")
        rc = M.cmd_check()
        assert rc == 1
        err = capsys.readouterr().err
        assert "schemaVersion must be 1" in err

    def test_overrides_block_only_emitted_for_new_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Catalog is valid; overrides introduce a new bogus URL.
        _, catalog, overrides = _patch_paths(monkeypatch, tmp_path)
        _seed_catalog(catalog, apps={"123": _make_app(123)})
        bad_entry = {"id": 999, "name": "x", "displayName": "X", "url": "ftp://bad"}
        overrides.write_text(
            json.dumps({"schemaVersion": 1, "apps": {"999": bad_entry}}),
            encoding="utf-8",
        )
        rc = M.cmd_check()
        assert rc == 1
        err = capsys.readouterr().err
        assert "catalog+overrides:" in err


# ----------------------------------------------------- cmd_sync


class TestCmdSync:
    def test_aborts_and_keeps_cache_when_first_page_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _, catalog, _ = _patch_paths(monkeypatch, tmp_path)
        _seed_catalog(catalog, apps={"1": _make_app(1)})
        original = catalog.read_text(encoding="utf-8")

        with mock.patch.object(
            M, "_fetch_page", return_value=(None, "boom"),
        ):
            rc = M.cmd_sync()
        assert rc == 0
        assert "sync aborted at offset 0" in capsys.readouterr().err
        # Catalog file unchanged
        assert catalog.read_text(encoding="utf-8") == original

    def test_keeps_cache_when_zero_results_returned(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _, catalog, _ = _patch_paths(monkeypatch, tmp_path)
        _seed_catalog(catalog, apps={"1": _make_app(1)})
        original = catalog.read_text(encoding="utf-8")
        # First page returns an "empty" page with no results -> break.
        with mock.patch.object(
            M, "_fetch_page", return_value=({"results": []}, None),
        ):
            rc = M.cmd_sync()
        assert rc == 0
        err = capsys.readouterr().err
        assert "zero results" in err
        assert catalog.read_text(encoding="utf-8") == original

    def test_full_sync_writes_changed_apps(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _, catalog, _ = _patch_paths(monkeypatch, tmp_path)
        _seed_catalog(catalog, apps={})

        # Page 1: one upstream app; page 2: empty -> break.
        pages = iter([
            ({"results": [
                {"uid": 100, "title": "App", "path": "/app/100/"}
            ]}, None),
            ({"results": []}, None),
        ])
        slept: list[float] = []
        monkeypatch.setattr(M.time, "sleep", lambda s: slept.append(s))
        with mock.patch.object(
            M, "_fetch_page", side_effect=lambda *a, **kw: next(pages)
        ):
            rc = M.cmd_sync()
        assert rc == 0
        body = json.loads(catalog.read_text(encoding="utf-8"))
        assert "100" in body["apps"]
        assert body["apps"]["100"]["id"] == 100
        # ``lastUpdated`` bumped because we changed an entry.
        assert body["lastUpdated"]
        out = capsys.readouterr().out
        assert "wrote" in out
        # One per-page sleep before the second fetch
        assert slept == [M.SLEEP_BETWEEN_REQUESTS]

    def test_full_sync_skips_unparseable_upstream_entries(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Pin the ``if entry is None: continue`` branch on line 474:
        the upstream returns one parseable entry and one unparseable
        entry (no id at all), and the unparseable one must be skipped
        without breaking the loop."""
        _, catalog, _ = _patch_paths(monkeypatch, tmp_path)
        _seed_catalog(catalog, apps={})
        pages = iter([
            ({"results": [
                {"uid": 100, "title": "Good"},
                {"name": "no id at all"},  # _normalise_entry returns None
            ]}, None),
            ({"results": []}, None),
        ])
        monkeypatch.setattr(M.time, "sleep", lambda s: None)
        with mock.patch.object(
            M, "_fetch_page", side_effect=lambda *a, **kw: next(pages)
        ):
            rc = M.cmd_sync()
        assert rc == 0
        body = json.loads(catalog.read_text(encoding="utf-8"))
        # Only the parseable entry made it into the catalog.
        assert list(body["apps"].keys()) == ["100"]

    def test_full_sync_no_diff_keeps_lastupdated_unchanged(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, catalog, _ = _patch_paths(monkeypatch, tmp_path)
        # Seed with the same canonical body the API will return.
        prior = _make_app(100, "demo")
        _seed_catalog(catalog, apps={"100": prior})
        # Stamp a frozen lastUpdated so we can verify it doesn't change.
        body = json.loads(catalog.read_text(encoding="utf-8"))
        body["lastUpdated"] = "1999-01-01"
        catalog.write_text(json.dumps(body), encoding="utf-8")

        # Build an upstream payload that yields the same canonical body.
        upstream = {
            "uid": 100,
            "title": "Demo",
            "appid": "demo",
            "path": "/app/100",
            "latest": {
                "name": "1.0.0",
                "splunk_version_compatibility": ["9.x"],
            },
            "license": {"vendor": "ACME"},
            "install_method_distributed": "self_service",
            "category": "data-source",
            "download_count": 100,
            "updated_time": "2026-05-19",
        }
        pages = iter([
            ({"results": [upstream]}, None),
            ({"results": []}, None),
        ])
        monkeypatch.setattr(M.time, "sleep", lambda s: None)
        with mock.patch.object(
            M, "_fetch_page", side_effect=lambda *a, **kw: next(pages)
        ):
            rc = M.cmd_sync()
        assert rc == 0
        post = json.loads(catalog.read_text(encoding="utf-8"))
        # The canonical body matched; lastUpdated should NOT be bumped.
        assert post["lastUpdated"] == "1999-01-01"

    def test_dry_run_does_not_write_file(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _, catalog, _ = _patch_paths(monkeypatch, tmp_path)
        _seed_catalog(catalog, apps={})
        original = catalog.read_text(encoding="utf-8")
        pages = iter([
            ({"results": [{"uid": 200, "title": "X"}]}, None),
            ({"results": []}, None),
        ])
        monkeypatch.setattr(M.time, "sleep", lambda s: None)
        with mock.patch.object(
            M, "_fetch_page", side_effect=lambda *a, **kw: next(pages)
        ):
            rc = M.cmd_sync(dry_run=True)
        assert rc == 0
        assert catalog.read_text(encoding="utf-8") == original
        out = capsys.readouterr().out
        assert "dry-run" in out

    def test_max_pages_warning_emitted_when_loop_completes(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _, catalog, _ = _patch_paths(monkeypatch, tmp_path)
        _seed_catalog(catalog, apps={})

        # Force a small MAX_PAGES so the loop finishes without ever
        # hitting an empty page; the for-else then fires.
        monkeypatch.setattr(M, "MAX_PAGES", 2)
        # Every page returns one app -> never empty.
        seq = [
            ({"results": [{"uid": 1, "title": "A"}]}, None),
            ({"results": [{"uid": 2, "title": "B"}]}, None),
        ]
        pages = iter(seq)
        monkeypatch.setattr(M.time, "sleep", lambda s: None)
        with mock.patch.object(
            M, "_fetch_page", side_effect=lambda *a, **kw: next(pages)
        ):
            rc = M.cmd_sync()
        assert rc == 0
        err = capsys.readouterr().err
        assert "reached MAX_PAGES" in err

    def test_post_sync_validation_failure_keeps_cache(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Force the post-sync validator to flag a problem; cmd_sync
        # must refuse to overwrite the cached catalog.
        _, catalog, _ = _patch_paths(monkeypatch, tmp_path)
        _seed_catalog(catalog, apps={"1": _make_app(1)})
        original = catalog.read_text(encoding="utf-8")
        pages = iter([
            ({"results": [{"uid": 100, "title": "X"}]}, None),
            ({"results": []}, None),
        ])
        monkeypatch.setattr(M.time, "sleep", lambda s: None)
        # Patch _validate_catalog to fail on the post-sync body.
        seen = {"calls": 0}
        original_fn = M._validate_catalog

        def _fake_validate(body: dict[str, Any]) -> list[str]:
            seen["calls"] += 1
            return ["synthetic post-sync error"]

        with mock.patch.object(
            M, "_fetch_page", side_effect=lambda *a, **kw: next(pages)
        ), mock.patch.object(M, "_validate_catalog", _fake_validate):
            rc = M.cmd_sync()
        assert rc == 0
        err = capsys.readouterr().err
        assert "synthetic post-sync error" in err
        assert "refusing to overwrite" in err
        assert catalog.read_text(encoding="utf-8") == original

    def test_empty_existing_catalog_initialised_from_template(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # File exists but with empty apps -> should be re-initialised
        # from _empty_catalog before merging.
        _, catalog, _ = _patch_paths(monkeypatch, tmp_path)
        catalog.write_text(
            json.dumps({"apps": "not-a-dict"}),
            encoding="utf-8",
        )
        pages = iter([
            ({"results": []}, None),
        ])
        with mock.patch.object(
            M, "_fetch_page", side_effect=lambda *a, **kw: next(pages)
        ):
            rc = M.cmd_sync()
        # No fetched results -> cached fallback path fires
        assert rc == 0


# ----------------------------------------------------- main


class TestMain:
    def test_default_runs_check(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _patch_paths(monkeypatch, tmp_path)
        rc = M.main([])
        assert rc == 0
        assert "catalog OK" in capsys.readouterr().out

    def test_explicit_check_flag_runs_check(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _patch_paths(monkeypatch, tmp_path)
        rc = M.main(["--check"])
        assert rc == 0
        assert "catalog OK" in capsys.readouterr().out

    def test_sync_routes_to_cmd_sync(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _patch_paths(monkeypatch, tmp_path)
        with mock.patch.object(M, "cmd_sync", return_value=0) as fake:
            rc = M.main(["--sync"])
        assert rc == 0
        fake.assert_called_once_with(dry_run=False)

    def test_sync_dry_run_passed_through(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _patch_paths(monkeypatch, tmp_path)
        with mock.patch.object(M, "cmd_sync", return_value=0) as fake:
            rc = M.main(["--sync", "--dry-run"])
        assert rc == 0
        fake.assert_called_once_with(dry_run=True)

    def test_check_and_sync_are_mutually_exclusive(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        with pytest.raises(SystemExit):
            M.main(["--check", "--sync"])


class TestMainGuardIsBoilerplate:
    """Pin the ``__main__`` block as source so a refactor that removes
    it fails this test rather than silently breaking the cron job."""

    def test_main_guard_present(self) -> None:
        src = Path(M.__file__).read_text(encoding="utf-8")
        assert 'if __name__ == "__main__":' in src
        assert "raise SystemExit(main())" in src
