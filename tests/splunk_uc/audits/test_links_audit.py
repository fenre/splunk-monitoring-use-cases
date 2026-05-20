"""Tests for ``splunk_uc.audits.links`` — the URL liveness auditor.

This file complements ``test_links_url_hygiene.py`` (which pinned
the regression contract for the ``URL_PATTERN`` / ``normalize_url``
/ malformed-URL-tolerance fix earlier today) with broad coverage of
the rest of the module:

* ``load_ignore_patterns`` — missing file, empty file, comment
  filtering, invalid-regex tolerance.
* ``collect_urls`` — walks ``content/cat-*/UC-*.json`` via
  ``iter_uc_sidecars`` (stubbed); pulls URLs from
  ``references[].url`` and the prose fields; deduplicates by URL,
  records each location; filters out non-``http(s)`` schemes.
* ``_head_code`` / ``_get_code`` / ``_probe_once`` / ``check_url``
  — HTTP probing with ``urllib.request.urlopen`` mocked. Covers
  the HEAD-then-GET fallback table, HEAD success, HEAD ``HTTPError``
  in the fallback set, HEAD ``HTTPError`` outside the fallback
  set, HEAD ``URLError`` (DNS / TCP failure), retry-on-429
  semantics in ``check_url``.
* ``main`` end-to-end — ``--dry-run`` mode, "no URLs" early
  return, ignore-file integration, broken-URL reporting,
  rc=0 / rc=1 paths, and the malformed-URL tolerance path.

The module's heavy lifting is HTTP work; tests stay hermetic by
mocking ``urllib.request.urlopen`` and ``time.sleep`` (so the
retry path doesn't actually sleep), and by stubbing
``iter_uc_sidecars`` so ``collect_urls`` doesn't walk the real
7,900-UC corpus on every run.
"""

from __future__ import annotations

import io
import urllib.error
from pathlib import Path
from typing import Any

import pytest

from splunk_uc.audits import links as audit


def _make_httperror(url: str, code: int, msg: str) -> urllib.error.HTTPError:
    """Construct an HTTPError that won't trigger Python 3.14's
    `ResourceWarning: Implicitly cleaning up <HTTPError ...>`
    when it is GC'd at scope exit.

    Python 3.14's HTTPError owns an `fp` and runs a deallocator
    that warns about implicit cleanup. We pass an explicit empty
    `BytesIO` (so cleanup is well-defined) and our test fixtures
    close the exception in a `finally` block where applicable.
    """

    return urllib.error.HTTPError(
        url=url, code=code, msg=msg, hdrs=None, fp=io.BytesIO()
    )


# --------------------------------------------------------------------- #
# load_ignore_patterns
# --------------------------------------------------------------------- #


def test_load_ignore_patterns_returns_empty_when_file_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(audit, "IGNORE_FILE", tmp_path / "missing")
    assert audit.load_ignore_patterns() == []


def test_load_ignore_patterns_strips_comments_and_blank_lines(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    f = tmp_path / "ignore"
    f.write_text(
        "# top comment\n"
        "\n"
        "example\\.com\n"
        "  # indented comment lines NOT stripped because '.strip()' doesn't see them as starting with #\n"  # noqa: E501
        "\n"
        "# trailing comment\n"
        "another\\.org\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(audit, "IGNORE_FILE", f)
    patterns = audit.load_ignore_patterns()
    sources = [p.pattern for p in patterns]
    # NOTE the comment-with-leading-spaces above is stripped before the
    # ``startswith("#")`` check so we DO drop it too. Pin both real
    # entries are present, nothing else.
    assert sources == ["example\\.com", "another\\.org"]


def test_load_ignore_patterns_skips_invalid_regex(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An unparseable regex must warn but not crash."""

    f = tmp_path / "ignore"
    f.write_text("(\nvalid\\.org\n", encoding="utf-8")  # first line is unclosed group
    monkeypatch.setattr(audit, "IGNORE_FILE", f)
    patterns = audit.load_ignore_patterns()
    err = capsys.readouterr().err
    assert [p.pattern for p in patterns] == ["valid\\.org"]
    assert "invalid ignore regex" in err


# --------------------------------------------------------------------- #
# collect_urls — _uc_walk.iter_uc_sidecars stubbed
# --------------------------------------------------------------------- #


def _stub_sidecars(
    monkeypatch: pytest.MonkeyPatch,
    sidecars: list[tuple[Path, dict[str, Any]]],
) -> None:
    """Replace ``iter_uc_sidecars`` with a deterministic iterator
    over the given (path, payload) pairs."""

    monkeypatch.setattr(audit, "iter_uc_sidecars", lambda: iter(sidecars))


def test_collect_urls_pulls_from_references_array(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(audit, "REPO_ROOT", tmp_path)
    sidecar = tmp_path / "content" / "cat-01-x" / "UC-1.1.1.json"
    sidecar.parent.mkdir(parents=True)
    sidecar.touch()
    payload = {
        "id": "1.1.1",
        "references": [
            {"url": "https://docs.splunk.com/Documentation"},
            {"url": "https://other.example.com/page"},
            {"url": "ftp://not-http.example.com"},  # MUST be skipped
            {"title": "missing-url entry"},  # MUST be skipped
            "not-a-dict",  # MUST be skipped
        ],
    }
    _stub_sidecars(monkeypatch, [(sidecar, payload)])
    out = audit.collect_urls()
    urls = sorted(out.keys())
    assert urls == [
        "https://docs.splunk.com/Documentation",
        "https://other.example.com/page",
    ]
    # location string is "<relpath> (UC-X.Y.Z)"
    loc = out["https://docs.splunk.com/Documentation"][0]
    assert "content/cat-01-x/UC-1.1.1.json" in loc
    assert "(UC-1.1.1)" in loc


def test_collect_urls_pulls_from_prose_fields(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(audit, "REPO_ROOT", tmp_path)
    sidecar = tmp_path / "content" / "cat-01-x" / "UC-1.1.2.json"
    sidecar.parent.mkdir(parents=True)
    sidecar.touch()
    payload = {
        "id": "1.1.2",
        "description": "See https://docs.splunk.com/intro for details.",
        "value": "Mentioned in https://splunk.com/value-page",
        "implementation": "no urls here",
        "dataSources": 12345,  # non-str — must be ignored, not crash
    }
    _stub_sidecars(monkeypatch, [(sidecar, payload)])
    out = audit.collect_urls()
    assert sorted(out.keys()) == [
        "https://docs.splunk.com/intro",
        "https://splunk.com/value-page",
    ]


def test_collect_urls_handles_missing_references_field(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(audit, "REPO_ROOT", tmp_path)
    sidecar = tmp_path / "content" / "cat-01-x" / "UC-1.1.3.json"
    sidecar.parent.mkdir(parents=True)
    sidecar.touch()
    payload = {"id": "1.1.3"}  # no references[], no prose
    _stub_sidecars(monkeypatch, [(sidecar, payload)])
    assert audit.collect_urls() == {}


def test_collect_urls_deduplicates_across_sidecars(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The same URL appearing on two UCs should appear once in
    the keys with two location strings."""

    monkeypatch.setattr(audit, "REPO_ROOT", tmp_path)
    base = tmp_path / "content" / "cat-01-x"
    base.mkdir(parents=True)
    a = base / "UC-1.1.1.json"
    b = base / "UC-1.1.2.json"
    a.touch()
    b.touch()
    shared = "https://docs.splunk.com/shared"
    pa = {"id": "1.1.1", "references": [{"url": shared}]}
    pb = {"id": "1.1.2", "references": [{"url": shared}]}
    _stub_sidecars(monkeypatch, [(a, pa), (b, pb)])
    out = audit.collect_urls()
    assert list(out.keys()) == [shared]
    assert len(out[shared]) == 2


def test_normalize_url_strips_unbalanced_trailing_bracket() -> None:
    """A bare ``]`` with no opener anywhere in the URL must be
    stripped (covers the strip branch on line 111 of ``links.py``
    for the bracket — not the paren — codepath, which the
    Wikipedia-style URL test in ``test_links_url_hygiene.py``
    doesn't exercise)."""

    assert audit.normalize_url("https://x/page]") == "https://x/page"


def test_normalize_url_preserves_balanced_brackets() -> None:
    """A balanced ``[...]`` in the URL must NOT be stripped."""

    raw = "https://x/api/v1/items[0]/value"
    assert audit.normalize_url(raw) == raw


def test_collect_urls_normalises_trailing_decoration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """references[].url with trailing punctuation (an author
    pastes a URL with a trailing comma) must be normalised
    before being stored."""

    monkeypatch.setattr(audit, "REPO_ROOT", tmp_path)
    sidecar = tmp_path / "content" / "cat-01-x" / "UC-1.1.4.json"
    sidecar.parent.mkdir(parents=True)
    sidecar.touch()
    payload = {
        "id": "1.1.4",
        "references": [{"url": "https://docs.splunk.com/intro."}],
    }
    _stub_sidecars(monkeypatch, [(sidecar, payload)])
    out = audit.collect_urls()
    # trailing dot stripped
    assert list(out.keys()) == ["https://docs.splunk.com/intro"]


# --------------------------------------------------------------------- #
# HTTP probes — urlopen mocked
# --------------------------------------------------------------------- #


class _FakeResp:
    """Mimic the bits of ``http.client.HTTPResponse`` we touch."""

    def __init__(self, code: int, body: bytes = b"OK") -> None:
        self._code = code
        self._body = body

    def __enter__(self) -> "_FakeResp":
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def getcode(self) -> int:
        return self._code

    def read(self, n: int = -1) -> bytes:
        return self._body


def test_head_code_returns_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        audit.urllib.request,
        "urlopen",
        lambda req, timeout: _FakeResp(200),
    )
    assert audit._head_code("https://x/") == 200


def test_get_code_returns_status_and_swallows_read_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _BrokenReadResp(_FakeResp):
        def read(self, n: int = -1) -> bytes:
            raise OSError("simulated read truncation")

    monkeypatch.setattr(
        audit.urllib.request,
        "urlopen",
        lambda req, timeout: _BrokenReadResp(200),
    )
    assert audit._get_code("https://x/") == 200


def test_probe_once_returns_true_on_head_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(audit, "_head_code", lambda url: 200)
    ok, detail, code = audit._probe_once("https://x/")
    assert ok is True
    assert detail == "HEAD 200"
    assert code == 200


def test_probe_once_falls_back_to_get_on_head_fallback_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A HEAD that returns one of the FALLBACK codes (400, 403,
    405, 501) triggers a GET retry — pin the resulting tuple."""

    monkeypatch.setattr(audit, "_head_code", lambda url: 405)
    monkeypatch.setattr(audit, "_get_code", lambda url: 200)
    ok, detail, code = audit._probe_once("https://x/")
    assert ok is True
    assert "GET 200" in detail
    assert "HEAD 405" in detail
    assert code == 405


def test_probe_once_returns_false_on_head_4xx_outside_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(audit, "_head_code", lambda url: 404)
    ok, detail, code = audit._probe_once("https://x/")
    assert ok is False
    assert detail == "HEAD 404"
    assert code == 404


def test_probe_once_falls_back_on_head_httperror_in_fallback_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raised: list[urllib.error.HTTPError] = []

    def _head(url: str) -> int:
        err = _make_httperror(url, 403, "Forbidden")
        raised.append(err)
        raise err

    monkeypatch.setattr(audit, "_head_code", _head)
    monkeypatch.setattr(audit, "_get_code", lambda url: 200)
    try:
        ok, detail, code = audit._probe_once("https://x/")
        assert ok is True
        assert "GET 200" in detail
        assert "HEAD 403" in detail
        assert code == 403
    finally:
        for e in raised:
            e.close()


def test_probe_once_returns_false_on_head_httperror_outside_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raised: list[urllib.error.HTTPError] = []

    def _head(url: str) -> int:
        err = _make_httperror(url, 410, "Gone")
        raised.append(err)
        raise err

    monkeypatch.setattr(audit, "_head_code", _head)
    try:
        ok, detail, code = audit._probe_once("https://x/")
        assert ok is False
        assert detail == "HEAD 410"
        assert code == 410
    finally:
        for e in raised:
            e.close()


def test_probe_once_falls_back_on_head_urlerror(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """HEAD raising ``URLError`` (DNS / TCP failure) triggers
    a GET retry — covers the URLError branch in ``_probe_once``."""

    def _head(url: str) -> int:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(audit, "_head_code", _head)
    monkeypatch.setattr(audit, "_get_code", lambda url: 200)
    ok, detail, code = audit._probe_once("https://x/")
    assert ok is True
    assert "GET 200" in detail
    assert "HEAD connection refused" in detail
    assert code is None


def test_finish_with_get_returns_false_when_get_httperrors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raised: list[urllib.error.HTTPError] = []

    def _get(url: str) -> int:
        err = _make_httperror(url, 500, "ISE")
        raised.append(err)
        raise err

    monkeypatch.setattr(audit, "_get_code", _get)
    try:
        ok, detail = audit._finish_with_get("https://x/", "HEAD 403")
        assert ok is False
        assert "GET 500" in detail
        assert "HEAD 403" in detail
    finally:
        for e in raised:
            e.close()


def test_finish_with_get_returns_false_when_get_urlerrors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _get(url: str) -> int:
        raise urllib.error.URLError("network unreachable")

    monkeypatch.setattr(audit, "_get_code", _get)
    ok, detail = audit._finish_with_get("https://x/", "HEAD 405")
    assert ok is False
    assert "network unreachable" in detail
    assert "HEAD 405" in detail


def test_check_url_returns_probe_result_immediately_on_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        audit, "_probe_once", lambda url: (True, "HEAD 200", 200)
    )
    # Make sleep visible if it's incorrectly called (would lengthen test).
    monkeypatch.setattr(audit.time, "sleep", lambda s: None)
    ok, detail = audit.check_url("https://x/")
    assert ok is True
    assert detail == "HEAD 200"


def test_check_url_retries_once_on_rate_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A 429/503 triggers ONE retry after sleep."""

    call_count = {"n": 0}

    def _probe(url: str) -> tuple[bool, str, int | None]:
        call_count["n"] += 1
        if call_count["n"] == 1:
            return False, "HEAD 429", 429
        return True, "HEAD 200", 200

    monkeypatch.setattr(audit, "_probe_once", _probe)
    sleep_args: list[float] = []
    monkeypatch.setattr(audit.time, "sleep", lambda s: sleep_args.append(s))

    ok, detail = audit.check_url("https://x/")
    assert ok is True
    assert "after retry" in detail
    assert call_count["n"] == 2
    assert sleep_args == [audit.RETRY_AFTER_DEFAULT]


def test_check_url_does_not_retry_on_non_rate_limit_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        audit, "_probe_once", lambda url: (False, "HEAD 404", 404)
    )
    sleep_args: list[float] = []
    monkeypatch.setattr(audit.time, "sleep", lambda s: sleep_args.append(s))
    ok, detail = audit.check_url("https://x/")
    assert ok is False
    assert detail == "HEAD 404"
    assert sleep_args == []


# --------------------------------------------------------------------- #
# main — end-to-end with collect_urls stubbed
# --------------------------------------------------------------------- #


def _stub_collect_urls(
    monkeypatch: pytest.MonkeyPatch,
    url_sources: dict[str, list[str]],
) -> None:
    monkeypatch.setattr(audit, "collect_urls", lambda: dict(url_sources))


def test_main_returns_zero_when_no_urls_found(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _stub_collect_urls(monkeypatch, {})
    rc = audit.main([])
    err = capsys.readouterr().err
    assert rc == 0
    assert "No URLs found" in err


def test_main_dry_run_lists_urls_without_probing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    _stub_collect_urls(
        monkeypatch,
        {
            "https://a.example.com/x": ["one"],
            "https://b.example.com/y": ["two"],
        },
    )
    monkeypatch.setattr(audit, "IGNORE_FILE", tmp_path / "missing-ignore")
    # check_url must NOT be called.
    monkeypatch.setattr(
        audit,
        "check_url",
        lambda u: pytest.fail(f"dry-run must not probe {u!r}"),
    )
    rc = audit.main(["--dry-run"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Dry run: 2 unique URL(s)" in out
    assert "https://a.example.com/x" in out
    assert "https://b.example.com/y" in out


def test_main_dry_run_respects_ignore_file(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    ignore = tmp_path / "ignore"
    ignore.write_text("a\\.example\\.com\n", encoding="utf-8")
    monkeypatch.setattr(audit, "IGNORE_FILE", ignore)
    _stub_collect_urls(
        monkeypatch,
        {
            "https://a.example.com/x": ["a"],
            "https://b.example.com/y": ["b"],
        },
    )
    rc = audit.main(["--dry-run"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "1 unique URL(s), 1 ignored" in out


def test_main_returns_zero_when_every_url_passes(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(audit, "IGNORE_FILE", tmp_path / "missing-ignore")
    _stub_collect_urls(
        monkeypatch,
        {
            "https://a.example.com/x": ["one"],
            "https://b.example.com/y": ["two"],
        },
    )
    monkeypatch.setattr(audit, "check_url", lambda u: (True, "HEAD 200"))
    monkeypatch.setattr(audit.time, "sleep", lambda s: None)
    rc = audit.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "URLs checked (unique): 2" in out
    assert "OK:                    2" in out
    assert "Broken:                0" in out


def test_main_returns_one_when_any_url_broken(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(audit, "IGNORE_FILE", tmp_path / "missing-ignore")
    url_sources = {
        "https://good.example.com/x": ["UC-1.1.1"],
        "https://broken.example.com/y": ["UC-1.1.2"],
    }
    _stub_collect_urls(monkeypatch, url_sources)

    def _check(u: str) -> tuple[bool, str]:
        return (False, "HEAD 500") if "broken" in u else (True, "HEAD 200")

    monkeypatch.setattr(audit, "check_url", _check)
    monkeypatch.setattr(audit.time, "sleep", lambda s: None)
    rc = audit.main([])
    cap = capsys.readouterr()
    assert rc == 1
    assert "URLs checked (unique): 2" in cap.out
    assert "Broken:                1" in cap.out
    # Broken URLs land on stderr with the location string.
    assert "BROKEN [HEAD 500] https://broken.example.com/y" in cap.err
    assert "UC-1.1.2" in cap.err


def test_main_swallows_check_url_exceptions_and_reports_repr(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """``check_host`` wraps every probe in a ``try/except``; an
    unexpected exception (e.g. socket library blew up) must yield
    a broken-URL with the ``repr(exc)`` as the detail rather than
    abort the worker."""

    monkeypatch.setattr(audit, "IGNORE_FILE", tmp_path / "missing-ignore")
    _stub_collect_urls(
        monkeypatch,
        {"https://crashy.example.com/x": ["UC-1.1.5"]},
    )

    def _explode(u: str) -> tuple[bool, str]:
        raise RuntimeError("kapow")

    monkeypatch.setattr(audit, "check_url", _explode)
    monkeypatch.setattr(audit.time, "sleep", lambda s: None)
    rc = audit.main([])
    cap = capsys.readouterr()
    assert rc == 1
    assert "kapow" in cap.err
    assert "UC-1.1.5" in cap.err


def test_main_tolerates_malformed_url_via_urlsplit(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Live ROADMAP regression: ``urlsplit('https://[server]:[port]/...')``
    raises ``ValueError: Invalid IPv6 URL``. Today's hardening
    must skip the bad URL with a WARN, NOT abort the run. (Mirrors
    the contract pinned in ``test_links_url_hygiene.py`` but
    exercised against the live ``main`` happy-path code, including
    the post-WARN dropped-URL filtering.)"""

    monkeypatch.setattr(audit, "IGNORE_FILE", tmp_path / "missing-ignore")
    _stub_collect_urls(
        monkeypatch,
        {
            "https://[server]:[port]/api": ["UC-1.1.6"],
            "https://good.example.com/x": ["UC-1.1.7"],
        },
    )
    monkeypatch.setattr(audit, "check_url", lambda u: (True, "HEAD 200"))
    monkeypatch.setattr(audit.time, "sleep", lambda s: None)
    rc = audit.main([])
    cap = capsys.readouterr()
    assert rc == 0
    assert "WARN: skipped 1 malformed URL(s)" in cap.err
    # And the summary should count only the good URL.
    assert "URLs checked (unique): 1" in cap.out


def test_main_throttles_within_host_with_per_host_delay(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """When two URLs share a host, the threaded worker sleeps
    ``PER_HOST_DELAY_SEC`` between the second and any later
    request (covers ``time.sleep(PER_HOST_DELAY_SEC)`` on
    line 305 of ``links.py``)."""

    monkeypatch.setattr(audit, "IGNORE_FILE", tmp_path / "missing-ignore")
    _stub_collect_urls(
        monkeypatch,
        {
            "https://same-host.example.com/a": ["UC-A"],
            "https://same-host.example.com/b": ["UC-B"],
        },
    )
    monkeypatch.setattr(audit, "check_url", lambda u: (True, "HEAD 200"))
    sleeps: list[float] = []
    monkeypatch.setattr(audit.time, "sleep", lambda s: sleeps.append(s))
    rc = audit.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "URLs checked (unique): 2" in out
    # Two URLs on the same host → exactly one inter-request sleep.
    assert audit.PER_HOST_DELAY_SEC in sleeps


def test_main_reports_ignored_count_in_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    ignore = tmp_path / "ignore"
    ignore.write_text("ignored\\.example\\.com\n", encoding="utf-8")
    monkeypatch.setattr(audit, "IGNORE_FILE", ignore)
    _stub_collect_urls(
        monkeypatch,
        {
            "https://ignored.example.com/x": ["U1"],
            "https://good.example.com/y": ["U2"],
        },
    )
    monkeypatch.setattr(audit, "check_url", lambda u: (True, "HEAD 200"))
    monkeypatch.setattr(audit.time, "sleep", lambda s: None)
    rc = audit.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Ignored (fragile):     1" in out
