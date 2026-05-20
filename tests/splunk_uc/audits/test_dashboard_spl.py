"""Tests for ``splunk_uc.audits.dashboard_spl``.

The audit drives a live splunkd:8089 instance via REST. The
``Splunkd`` HTTP client and the ``main`` entry point are integration-
flavoured and remain out of scope here. But the audit also carries a
sizeable pure-Python core — token-spec parsing, multiselect token
expansion, drilldown / time-token guard, ``<query>`` extraction from
Simple-XML dashboards, panel-title resolution — and that core was
sitting at ~16 % coverage with zero unit tests.

This file walks those pure-function paths against synthetic XML
strings so the regression net catches accidental changes to the
token-substitution contract (where v9.2.0 build 8 quietly shipped
malformed SPL into the Implementations panel) without requiring a
running Splunk container.
"""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from splunk_uc.audits import dashboard_spl as audit


# --------------------------------------------------------------------- #
# TokenSpec.expand — every input type
# --------------------------------------------------------------------- #


def test_token_expand_empty_default_returns_empty() -> None:
    spec = audit.TokenSpec(token="t", type="text", default="")
    assert spec.expand() == ""


def test_token_expand_dropdown_returns_plain_default() -> None:
    spec = audit.TokenSpec(token="t", type="dropdown", default="admin")
    assert spec.expand() == "admin"


def test_token_expand_text_with_value_prefix_and_suffix() -> None:
    spec = audit.TokenSpec(
        token="t",
        type="text",
        default="rec",
        value_prefix="action=",
        value_suffix='"',
    )
    assert spec.expand() == 'action=rec"'


def test_token_expand_multiselect_joins_values_with_default_delimiter() -> None:
    spec = audit.TokenSpec(
        token="t",
        type="multiselect",
        default="a,b,c",
        prefix="(",
        suffix=")",
        value_prefix='status="',
        value_suffix='"',
    )
    assert spec.expand() == '(status="a",status="b",status="c")'


def test_token_expand_multiselect_with_custom_delimiter() -> None:
    spec = audit.TokenSpec(
        token="t",
        type="multiselect",
        default="x,y",
        prefix="",
        suffix="",
        value_prefix="",
        value_suffix="",
        delimiter=" OR ",
    )
    assert spec.expand() == "x OR y"


def test_token_expand_multiselect_strips_blank_entries() -> None:
    """Spaces / empty entries inside a CSV must not become
    ``valuePrefix valueSuffix`` no-ops in the rendered SPL."""

    spec = audit.TokenSpec(
        token="t",
        type="multiselect",
        default="a, ,b,",
        prefix="(",
        suffix=")",
        value_prefix='status="',
        value_suffix='"',
    )
    assert spec.expand() == '(status="a",status="b")'


# --------------------------------------------------------------------- #
# _strip_ns
# --------------------------------------------------------------------- #


def test_strip_ns_removes_xml_namespace_prefix() -> None:
    assert audit._strip_ns("{http://example.org/ns}foo") == "foo"


def test_strip_ns_returns_input_when_no_namespace() -> None:
    assert audit._strip_ns("bare") == "bare"


# --------------------------------------------------------------------- #
# _parse_inputs
# --------------------------------------------------------------------- #


def test_parse_inputs_returns_empty_when_no_inputs() -> None:
    root = ET.fromstring("<form><label>x</label></form>")
    assert audit._parse_inputs(root) == {}


def test_parse_inputs_skips_input_without_token_attribute() -> None:
    root = ET.fromstring(
        "<form>"
        '<input type="text"><default>x</default></input>'
        "</form>"
    )
    assert audit._parse_inputs(root) == {}


def test_parse_inputs_collects_text_default() -> None:
    root = ET.fromstring(
        "<form>"
        '<input token="search_index" type="text">'
        "<default>os</default>"
        "</input>"
        "</form>"
    )
    specs = audit._parse_inputs(root)
    assert "search_index" in specs
    s = specs["search_index"]
    assert s.token == "search_index"
    assert s.type == "text"
    assert s.default == "os"


def test_parse_inputs_collects_full_multiselect_shape() -> None:
    """Mirror the production Implementations dashboard input — the one
    that broke in v9.2.0 build 8."""

    xml = (
        "<form>"
        '<input token="status_filter" type="multiselect">'
        "<default>not_started,in_progress</default>"
        "<delimiter>,</delimiter>"
        "<prefix>(</prefix>"
        "<suffix>)</suffix>"
        '<valuePrefix>status="</valuePrefix>'
        '<valueSuffix>"</valueSuffix>'
        "</input>"
        "</form>"
    )
    root = ET.fromstring(xml)
    spec = audit._parse_inputs(root)["status_filter"]
    assert spec.type == "multiselect"
    assert spec.default == "not_started,in_progress"
    assert spec.delimiter == ","
    assert spec.prefix == "("
    assert spec.suffix == ")"
    assert spec.value_prefix == 'status="'
    assert spec.value_suffix == '"'
    assert (
        spec.expand()
        == '(status="not_started",status="in_progress")'
    )


def test_parse_inputs_default_type_is_text() -> None:
    """When the XML omits ``type=``, ``TokenSpec.type`` defaults to
    ``text`` so ``expand()`` returns the plain default."""

    root = ET.fromstring(
        "<form>"
        '<input token="x"><default>v</default></input>'
        "</form>"
    )
    spec = audit._parse_inputs(root)["x"]
    assert spec.type == "text"
    assert spec.expand() == "v"


# --------------------------------------------------------------------- #
# _expand_tokens
# --------------------------------------------------------------------- #


def test_expand_tokens_substitutes_known_token() -> None:
    specs = {
        "host": audit.TokenSpec(
            token="host", type="text", default="srv01"
        )
    }
    spl = "search index=os host=$host$ | stats count"
    assert (
        audit._expand_tokens(spl, specs)
        == "search index=os host=srv01 | stats count"
    )


def test_expand_tokens_drops_unknown_token_to_empty() -> None:
    spl = "search foo=$mystery$"
    assert audit._expand_tokens(spl, {}) == "search foo="


@pytest.mark.parametrize(
    "token",
    [
        "row.uc_id",
        "click.value",
        "result.host",
        "earliest",
        "latest",
    ],
)
def test_expand_tokens_drops_drilldown_and_time_tokens(token: str) -> None:
    """Drilldown / time tokens are evaluated at interaction time, never
    at first-load. The audit substitutes them with an empty string so
    the surrounding SPL still validates."""

    spl = f"search foo | eval x=$" + token + "$"
    assert audit._expand_tokens(spl, {}) == "search foo | eval x="


def test_expand_tokens_handles_multiselect_substitution() -> None:
    """End-to-end: multiselect token must expand into the full
    ``prefix valuePrefix VAL valueSuffix [delim ...] suffix`` form."""

    specs = {
        "status_filter": audit.TokenSpec(
            token="status_filter",
            type="multiselect",
            default="a,b",
            prefix="(",
            suffix=")",
            value_prefix='status="',
            value_suffix='"',
        )
    }
    spl = "| inputlookup x $status_filter$ | table foo"
    assert (
        audit._expand_tokens(spl, specs)
        == '| inputlookup x (status="a",status="b") | table foo'
    )


# --------------------------------------------------------------------- #
# _collect_panels — driven from real ET trees
# --------------------------------------------------------------------- #


def _write_view(tmp_path: Path, name: str, body: str) -> Path:
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


def test_collect_panels_extracts_simple_search(tmp_path: Path) -> None:
    """Panel-title resolution requires ``<title>`` and ``<search>`` to
    share the same direct parent — the audit walks ancestors and breaks
    on the first one that contains ``<search>`` as a direct child,
    regardless of whether it also has ``<title>``. The Implementations
    dashboard uses this flat shape, so we mirror it here."""

    view = _write_view(
        tmp_path,
        "v.xml",
        (
            "<form>"
            "<row><panel><title>P1</title>"
            "<search>"
            "<query>index=os | stats count</query>"
            "<earliest>-1h</earliest>"
            "<latest>now</latest>"
            "</search>"
            "</panel></row>"
            "</form>"
        ),
    )
    panels, warnings = audit._collect_panels(view)
    assert warnings == []
    assert len(panels) == 1
    p = panels[0]
    assert p.view == "v.xml"
    assert p.panel == "P1"
    assert p.spl == "index=os | stats count"
    assert p.earliest == "-1h"
    assert p.latest == "now"


def test_collect_panels_defaults_earliest_latest_when_missing(
    tmp_path: Path,
) -> None:
    view = _write_view(
        tmp_path,
        "v.xml",
        (
            "<form>"
            "<row><panel>"
            "<chart><search>"
            "<query>index=os | stats count</query>"
            "</search></chart>"
            "</panel></row>"
            "</form>"
        ),
    )
    panels, _ = audit._collect_panels(view)
    assert panels[0].earliest == "-15m"
    assert panels[0].latest == "now"


def test_collect_panels_skips_empty_query_elements(tmp_path: Path) -> None:
    """A ``<query></query>`` element with no body should be skipped
    silently rather than creating a panel with empty SPL."""

    view = _write_view(
        tmp_path,
        "v.xml",
        (
            "<form>"
            "<row><panel>"
            "<table><search><query>   </query></search></table>"
            "<chart><search>"
            "<query>index=os | stats count</query>"
            "</search></chart>"
            "</panel></row>"
            "</form>"
        ),
    )
    panels, _ = audit._collect_panels(view)
    assert len(panels) == 1
    assert "stats count" in panels[0].spl


def test_collect_panels_expands_form_inputs_into_panel_spl(
    tmp_path: Path,
) -> None:
    """Pin the v9.2.0-build-8 regression: a multiselect input feeding
    an ``| inputlookup ... (status="...",...)`` panel must expand
    into syntactically valid SPL, not the corrupt form that Splunk
    rejected with ``Invalid argument: '(status=not_started'``."""

    view = _write_view(
        tmp_path,
        "v.xml",
        (
            "<form>"
            '<input token="status_filter" type="multiselect">'
            "<default>not_started,in_progress</default>"
            "<delimiter>,</delimiter>"
            "<prefix>(</prefix>"
            "<suffix>)</suffix>"
            '<valuePrefix>status="</valuePrefix>'
            '<valueSuffix>"</valueSuffix>'
            "</input>"
            "<row><panel><title>Implementations</title>"
            "<search>"
            "<query>"
            "| inputlookup uc_recommender_implementations "
            "$status_filter$ | table uc_id, status, owner"
            "</query>"
            "</search>"
            "</panel></row>"
            "</form>"
        ),
    )
    panels, _ = audit._collect_panels(view)
    assert len(panels) == 1
    assert (
        '(status="not_started",status="in_progress")' in panels[0].spl
    )
    assert panels[0].panel == "Implementations"


def test_collect_panels_returns_parse_error_warning(
    tmp_path: Path,
) -> None:
    """A malformed XML file must surface a warning, not crash."""

    view = _write_view(tmp_path, "v.xml", "<form><unclosed>")
    panels, warnings = audit._collect_panels(view)
    assert panels == []
    assert warnings and "XML parse error" in warnings[0]
    assert "v.xml" in warnings[0]


def test_collect_panels_falls_back_to_synthetic_panel_label(
    tmp_path: Path,
) -> None:
    """When the surrounding panel has no ``<title>``, the audit must
    label it ``panel#N`` so log messages are still actionable."""

    view = _write_view(
        tmp_path,
        "v.xml",
        (
            "<form>"
            "<row><panel>"
            "<table><search>"
            "<query>index=foo | head 1</query>"
            "</search></table>"
            "</panel></row>"
            "</form>"
        ),
    )
    panels, _ = audit._collect_panels(view)
    assert panels[0].panel.startswith("panel#")


# --------------------------------------------------------------------- #
# AuditResult.fatal_messages
# --------------------------------------------------------------------- #


def test_audit_result_fatal_messages_filters_to_fatal_only() -> None:
    p = audit.Panel(view="v", panel="x", spl="")
    r = audit.AuditResult(
        panel=p,
        ok=False,
        messages=[
            {"type": "FATAL", "text": "boom"},
            {"type": "WARN", "text": "soft"},
            {"type": "fatal", "text": "case-insensitive"},
        ],
    )
    assert len(r.fatal_messages) == 2


def test_audit_result_fatal_messages_empty_when_no_fatal() -> None:
    p = audit.Panel(view="v", panel="x", spl="")
    r = audit.AuditResult(panel=p, ok=True, messages=[])
    assert r.fatal_messages == []


# --------------------------------------------------------------------- #
# _resolve_token
# --------------------------------------------------------------------- #


def test_resolve_token_prefers_environment_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_AUDIT_TOKEN", "fromenv")
    assert audit._resolve_token("TEST_AUDIT_TOKEN") == "fromenv"


def test_resolve_token_returns_empty_when_unset(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """If the env var is empty AND secrets.env doesn't exist (or has
    no matching line), the function returns ``""``. We point
    ``__file__`` at a tmp_path stub so the real secrets.env never
    influences the test outcome."""

    monkeypatch.delenv("TEST_AUDIT_TOKEN", raising=False)
    # Build a fake "src/splunk_uc/audits/x.py" structure with no
    # adjacent secrets.env at parents[3].
    fake_root = tmp_path / "src" / "splunk_uc" / "audits"
    fake_root.mkdir(parents=True)
    fake_module = fake_root / "x.py"
    fake_module.write_text("", encoding="utf-8")
    monkeypatch.setattr(audit, "__file__", str(fake_module))
    assert audit._resolve_token("TEST_AUDIT_TOKEN") == ""


def test_resolve_token_reads_secrets_env_when_env_unset(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("TEST_AUDIT_TOKEN", raising=False)
    fake_root = tmp_path / "src" / "splunk_uc" / "audits"
    fake_root.mkdir(parents=True)
    fake_module = fake_root / "x.py"
    fake_module.write_text("", encoding="utf-8")
    secrets = tmp_path / "secrets.env"
    secrets.write_text(
        "# header comment\n"
        "OTHER_VAR=ignored\n"
        'TEST_AUDIT_TOKEN="from-secrets"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(audit, "__file__", str(fake_module))
    assert audit._resolve_token("TEST_AUDIT_TOKEN") == "from-secrets"


# --------------------------------------------------------------------- #
# main — exit-2 paths (no live splunkd needed)
# --------------------------------------------------------------------- #


def test_main_returns_two_when_views_dir_missing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = audit.main(
        [
            "--app-root",
            str(tmp_path / "no-such-app"),
            "--token-var",
            "AUDIT_NO_SUCH_TOKEN",
        ]
    )
    err = capsys.readouterr().err
    assert rc == 2
    assert "views dir not found" in err


def test_main_returns_two_when_token_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    app_root = tmp_path / "app"
    views = app_root / "default" / "data" / "ui" / "views"
    views.mkdir(parents=True)
    monkeypatch.delenv("AUDIT_NO_SUCH_TOKEN", raising=False)
    # Point the audit at a stub __file__ so secrets.env lookup misses.
    fake_root = tmp_path / "src" / "splunk_uc" / "audits"
    fake_root.mkdir(parents=True)
    monkeypatch.setattr(
        audit, "__file__", str(fake_root / "x.py")
    )

    rc = audit.main(
        [
            "--app-root",
            str(app_root),
            "--token-var",
            "AUDIT_NO_SUCH_TOKEN",
        ]
    )
    err = capsys.readouterr().err
    assert rc == 2
    assert "AUDIT_NO_SUCH_TOKEN not set" in err


def test_main_returns_zero_when_no_panels(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Empty views dir with a valid token MUST exit 0 without
    contacting splunkd (the print path is the only side effect)."""

    app_root = tmp_path / "app"
    views = app_root / "default" / "data" / "ui" / "views"
    views.mkdir(parents=True)
    monkeypatch.setenv("AUDIT_FAKE_TOKEN", "abc")

    rc = audit.main(
        [
            "--app-root",
            str(app_root),
            "--token-var",
            "AUDIT_FAKE_TOKEN",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "no <search><query> elements found" in out


# --------------------------------------------------------------------- #
# Splunkd HTTP client — stubbed via a FakeOpener that the audit
# treats as ``urllib.request.urlopen``. We never reach the network.
# --------------------------------------------------------------------- #


class _FakeResponse:
    """Mirror just enough of ``http.client.HTTPResponse`` for the
    audit's ``urlopen(...).__enter__`` contract."""

    def __init__(self, *, status: int, body: bytes) -> None:
        self.status = status
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:  # pragma: no cover
        return None


class _FakeOpener:
    """Replays a programmed list of responses (or raises programmed
    exceptions) in the order ``urlopen`` is called. Each call also
    records the (method, url, body) tuple in ``calls`` so tests can
    assert on dispatch shape."""

    def __init__(
        self,
        responses: list[object],
    ) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, str, str | None]] = []

    def __call__(
        self,
        req: object,
        context: object = None,
        timeout: int = 30,
    ) -> _FakeResponse:
        method = getattr(req, "get_method", lambda: "")() or ""
        url = getattr(req, "full_url", "")
        body = getattr(req, "data", None)
        body_text = body.decode("utf-8") if isinstance(body, bytes) else None
        self.calls.append((method, url, body_text))
        if not self.responses:
            raise AssertionError("FakeOpener exhausted; test asked for more dispatches than programmed")
        nxt = self.responses.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt  # type: ignore[return-value]


def test_splunkd_dispatch_blocking_happy_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two HTTP calls: dispatch (POST jobs → returns sid) + status
    (GET jobs/sid → returns isFailed=False). The DELETE cleanup is
    best-effort, so we tolerate the FakeOpener running out."""

    opener = _FakeOpener(
        [
            _FakeResponse(
                status=201,
                body=b'{"sid": "1700000000.1"}',
            ),
            _FakeResponse(
                status=200,
                body=(
                    b'{"entry": [{"content": {"isFailed": false, '
                    b'"isDone": true, "resultCount": 42, "messages": []}}]}'
                ),
            ),
            _FakeResponse(status=200, body=b"{}"),
        ]
    )
    monkeypatch.setattr(audit.urllib.request, "urlopen", opener)

    client = audit.Splunkd("https://example:8089", "tok", insecure=True)
    result = client.dispatch_blocking(
        "search index=os",
        app="myapp",
        earliest="-15m",
        latest="now",
    )

    assert result.ok is True
    assert result.is_failed is False
    assert result.is_done is True
    assert result.result_count == 42
    assert result.transport_error is None

    # First call is the POST to /search/jobs under nobody namespace.
    method, url, body = opener.calls[0]
    assert method == "POST"
    assert "/servicesNS/nobody/myapp/search/jobs" in url
    assert body is not None
    assert "search=search+index%3Dos" in body
    assert "exec_mode=blocking" in body


def test_splunkd_dispatch_blocking_marks_fatal_message_as_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The v9.2.0-build-8 regression: even when ``isFailed`` is
    false, a FATAL-typed message in the job status payload must
    flip ``ok`` to false."""

    opener = _FakeOpener(
        [
            _FakeResponse(status=201, body=b'{"sid": "abc"}'),
            _FakeResponse(
                status=200,
                body=(
                    b'{"entry": [{"content": {"isFailed": false, '
                    b'"isDone": true, "resultCount": 0, '
                    b'"messages": [{"type": "FATAL", '
                    b'"text": "Invalid argument"}]}}]}'
                ),
            ),
            _FakeResponse(status=200, body=b"{}"),
        ]
    )
    monkeypatch.setattr(audit.urllib.request, "urlopen", opener)

    client = audit.Splunkd("https://x:8089", "tok")
    result = client.dispatch_blocking(
        "| inputlookup foo (status=bar",
        app="a",
        earliest="-1h",
        latest="now",
    )

    assert result.ok is False
    assert result.is_failed is False
    assert any(m["type"] == "FATAL" for m in result.messages)
    assert len(result.fatal_messages) == 1


def test_splunkd_dispatch_blocking_handles_transport_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import urllib.error

    opener = _FakeOpener(
        [urllib.error.URLError("connection refused")]
    )
    monkeypatch.setattr(audit.urllib.request, "urlopen", opener)

    client = audit.Splunkd("https://x:8089", "tok")
    result = client.dispatch_blocking(
        "search foo",
        app="a",
        earliest="-1h",
        latest="now",
    )

    assert result.ok is False
    assert result.transport_error is not None
    assert "connection refused" in result.transport_error


def test_splunkd_dispatch_blocking_handles_no_sid_in_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A 2xx response with no ``sid`` key — e.g. when splunkd's
    dispatch endpoint silently 200s with an empty payload — must
    surface as a transport-level error, not a panel-level pass."""

    opener = _FakeOpener(
        [_FakeResponse(status=200, body=b"{}")]
    )
    monkeypatch.setattr(audit.urllib.request, "urlopen", opener)

    client = audit.Splunkd("https://x:8089", "tok")
    result = client.dispatch_blocking(
        "search foo",
        app="a",
        earliest="-1h",
        latest="now",
    )
    assert result.ok is False
    assert result.transport_error is not None
    assert "no sid returned" in result.transport_error


def test_splunkd_dispatch_blocking_handles_http_error_on_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A 400 dispatch response with a Splunk-formatted ``messages``
    array (and no sid) must record both the HTTP code and the
    underlying message list.

    ``HTTPError`` is constructed without a backing ``fp`` and
    explicitly closed in a ``try/finally`` to dodge a Python 3.14
    ``ResourceWarning`` raised by the implicit ``addinfourl``
    cleanup — the repo's ``filterwarnings = ["error"]`` config
    would otherwise promote that warning into a test failure.
    """

    import urllib.error

    err = urllib.error.HTTPError(
        url="https://x:8089/services/search/jobs",
        code=400,
        msg="Bad Request",
        hdrs=None,  # type: ignore[arg-type]
        fp=None,
    )
    try:
        # The audit calls ``err.read()`` on the HTTPError; the
        # default ``addinfourl.read()`` won't fire without a
        # backing fp, so we stub ``.read`` directly on the
        # instance.
        err.read = lambda: b'{"messages": [{"type": "FATAL", "text": "boom"}]}'  # type: ignore[method-assign]
        opener = _FakeOpener([err])
        monkeypatch.setattr(audit.urllib.request, "urlopen", opener)

        client = audit.Splunkd("https://x:8089", "tok")
        result = client.dispatch_blocking(
            "search foo",
            app="a",
            earliest="-1h",
            latest="now",
        )
        assert result.ok is False
        assert result.transport_error is not None
        assert "HTTP 400" in result.transport_error
        assert result.messages and result.messages[0]["type"] == "FATAL"
    finally:
        err.close()


def test_splunkd_dispatch_blocking_handles_http_error_on_job_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dispatch succeeds (returns a sid) but the follow-up GET to
    ``/search/jobs/<sid>`` returns 500 — the audit must classify
    this as a transport-level failure (covers line 355 of
    ``dashboard_spl.py``)."""

    import urllib.error

    err = urllib.error.HTTPError(
        url="https://x:8089/services/search/jobs/abc",
        code=500,
        msg="Internal Server Error",
        hdrs=None,  # type: ignore[arg-type]
        fp=None,
    )
    try:
        err.read = lambda: b'{"messages": [{"type": "FATAL", "text": "broken"}]}'  # type: ignore[method-assign]
        opener = _FakeOpener(
            [
                _FakeResponse(status=201, body=b'{"sid": "abc"}'),
                err,
            ]
        )
        monkeypatch.setattr(audit.urllib.request, "urlopen", opener)

        client = audit.Splunkd("https://x:8089", "tok")
        result = client.dispatch_blocking(
            "search foo",
            app="a",
            earliest="-1h",
            latest="now",
        )
        assert result.ok is False
        assert result.transport_error is not None
        assert "HTTP 500 on job status" in result.transport_error
    finally:
        err.close()


def test_splunkd_dispatch_blocking_handles_unexpected_job_status_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dispatch succeeds but the job-status payload is missing the
    expected ``entry[0].content`` chain — the audit must surface a
    deterministic transport-level error rather than KeyError-crash
    (covers lines 362-363 of ``dashboard_spl.py``)."""

    opener = _FakeOpener(
        [
            _FakeResponse(status=201, body=b'{"sid": "abc"}'),
            _FakeResponse(status=200, body=b'{"entry": []}'),  # no [0]
            # DELETE cleanup may run after this; FakeOpener tolerates exhaustion
        ]
    )
    monkeypatch.setattr(audit.urllib.request, "urlopen", opener)

    client = audit.Splunkd("https://x:8089", "tok")
    result = client.dispatch_blocking(
        "search foo",
        app="a",
        earliest="-1h",
        latest="now",
    )
    assert result.ok is False
    assert result.transport_error is not None
    assert "unexpected job-status payload" in result.transport_error


def test_splunkd_dispatch_blocking_tolerates_delete_cleanup_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The trailing DELETE that cleans up the dispatch directory is
    best-effort — any exception must be swallowed and the audit must
    still return a healthy ``AuditResult`` (covers lines 378-379 of
    ``dashboard_spl.py``)."""

    opener = _FakeOpener(
        [
            _FakeResponse(status=201, body=b'{"sid": "abc"}'),
            _FakeResponse(
                status=200,
                body=(
                    b'{"entry": [{"content": {"isFailed": false, '
                    b'"isDone": true, "resultCount": 7, "messages": []}}]}'
                ),
            ),
            RuntimeError("cleanup blew up"),  # raised on the DELETE
        ]
    )
    monkeypatch.setattr(audit.urllib.request, "urlopen", opener)

    client = audit.Splunkd("https://x:8089", "tok")
    result = client.dispatch_blocking(
        "search index=os",
        app="myapp",
        earliest="-15m",
        latest="now",
    )
    assert result.ok is True
    assert result.result_count == 7
    assert result.transport_error is None


def test_splunkd_request_falls_back_to_raw_on_non_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If splunkd returns a non-JSON body, ``_request`` must wrap it
    under ``{"raw": ...}`` rather than crash the audit."""

    opener = _FakeOpener(
        [_FakeResponse(status=200, body=b"<html>nope</html>")]
    )
    monkeypatch.setattr(audit.urllib.request, "urlopen", opener)

    client = audit.Splunkd("https://x:8089", "tok")
    code, payload = client._request("GET", "/healthz")
    assert code == 200
    assert payload == {"raw": "<html>nope</html>"}


def test_splunkd_constructor_strips_trailing_slash() -> None:
    c = audit.Splunkd("https://x:8089/", "tok", insecure=True)
    assert c.base_url == "https://x:8089"
    assert c.ctx is not None  # insecure=True allocates the SSL context


def test_splunkd_constructor_strict_tls_leaves_ctx_none() -> None:
    c = audit.Splunkd("https://x:8089", "tok", insecure=False)
    assert c.ctx is None


# --------------------------------------------------------------------- #
# main — live-dispatch path with mocked HTTP
# --------------------------------------------------------------------- #


def _write_minimal_dashboard(app_root: Path, name: str, spl: str) -> None:
    views = app_root / "default" / "data" / "ui" / "views"
    views.mkdir(parents=True, exist_ok=True)
    (views / name).write_text(
        (
            "<form>"
            "<row><panel><title>P</title>"
            "<search>"
            f"<query>{spl}</query>"
            "<earliest>-15m</earliest>"
            "<latest>now</latest>"
            "</search>"
            "</panel></row>"
            "</form>"
        ),
        encoding="utf-8",
    )


def test_main_dispatches_panels_and_returns_zero_on_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """End-to-end: a single dashboard with one panel, mocked-success
    HTTP dispatch, exits 0 and prints a PASS line."""

    app_root = tmp_path / "app"
    _write_minimal_dashboard(app_root, "v.xml", "search foo | head 1")
    monkeypatch.setenv("AUDIT_FAKE_TOKEN", "tok")

    opener = _FakeOpener(
        [
            _FakeResponse(status=201, body=b'{"sid": "abc"}'),
            _FakeResponse(
                status=200,
                body=(
                    b'{"entry": [{"content": {"isFailed": false, '
                    b'"isDone": true, "resultCount": 7, '
                    b'"messages": []}}]}'
                ),
            ),
            _FakeResponse(status=200, body=b"{}"),
        ]
    )
    monkeypatch.setattr(audit.urllib.request, "urlopen", opener)

    rc = audit.main(
        [
            "--app-root",
            str(app_root),
            "--token-var",
            "AUDIT_FAKE_TOKEN",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "[PASS]" in out
    assert "v.xml" in out
    assert "7 rows" in out


def test_main_returns_one_on_dispatch_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Mocked dispatch returns FATAL → main exits 1 and writes a
    FAIL line to stderr."""

    app_root = tmp_path / "app"
    _write_minimal_dashboard(
        app_root,
        "v.xml",
        "| inputlookup uc_recommender_implementations (status=not_started",
    )
    monkeypatch.setenv("AUDIT_FAKE_TOKEN", "tok")

    opener = _FakeOpener(
        [
            _FakeResponse(status=201, body=b'{"sid": "abc"}'),
            _FakeResponse(
                status=200,
                body=(
                    b'{"entry": [{"content": {"isFailed": true, '
                    b'"isDone": true, "resultCount": 0, '
                    b'"messages": [{"type": "FATAL", '
                    b'"text": "Invalid argument"}]}}]}'
                ),
            ),
            _FakeResponse(status=200, body=b"{}"),
        ]
    )
    monkeypatch.setattr(audit.urllib.request, "urlopen", opener)

    rc = audit.main(
        [
            "--app-root",
            str(app_root),
            "--token-var",
            "AUDIT_FAKE_TOKEN",
        ]
    )
    cap = capsys.readouterr()
    assert rc == 1
    assert "[FAIL]" in cap.err
    assert "Invalid argument" in cap.err
    assert "1 of 1 dashboard panels FAILED" in cap.err


def test_main_prints_transport_error_under_fail_line(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When a panel fails *with* a transport error, the per-panel
    FAIL output must include a ``transport:`` line (covers line 506
    of ``dashboard_spl.py``)."""

    import urllib.error

    app_root = tmp_path / "app"
    _write_minimal_dashboard(app_root, "v.xml", "search foo | head 1")
    monkeypatch.setenv("AUDIT_FAKE_TOKEN", "tok")

    opener = _FakeOpener(
        [urllib.error.URLError("name or service not known")]
    )
    monkeypatch.setattr(audit.urllib.request, "urlopen", opener)

    rc = audit.main(
        [
            "--app-root",
            str(app_root),
            "--token-var",
            "AUDIT_FAKE_TOKEN",
        ]
    )
    cap = capsys.readouterr()
    assert rc == 1
    assert "[FAIL]" in cap.err
    assert "transport:" in cap.err
    assert "name or service not known" in cap.err


def test_main_quiet_mode_suppresses_pass_lines(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--quiet`` MUST suppress the per-panel PASS and the summary
    counter line, but FAIL lines still fire on failure."""

    app_root = tmp_path / "app"
    _write_minimal_dashboard(app_root, "v.xml", "search foo | head 1")
    monkeypatch.setenv("AUDIT_FAKE_TOKEN", "tok")

    opener = _FakeOpener(
        [
            _FakeResponse(status=201, body=b'{"sid": "abc"}'),
            _FakeResponse(
                status=200,
                body=(
                    b'{"entry": [{"content": {"isFailed": false, '
                    b'"isDone": true, "resultCount": 0, '
                    b'"messages": []}}]}'
                ),
            ),
            _FakeResponse(status=200, body=b"{}"),
        ]
    )
    monkeypatch.setattr(audit.urllib.request, "urlopen", opener)

    rc = audit.main(
        [
            "--app-root",
            str(app_root),
            "--token-var",
            "AUDIT_FAKE_TOKEN",
            "--quiet",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "[PASS]" not in out
    assert "dashboard SPL audit" not in out


def test_main_warns_on_xml_parse_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A malformed view file MUST NOT abort the run — it produces a
    warning while the other panels still get dispatched."""

    app_root = tmp_path / "app"
    views = app_root / "default" / "data" / "ui" / "views"
    views.mkdir(parents=True)
    (views / "bad.xml").write_text("<form><unclosed>", encoding="utf-8")
    _write_minimal_dashboard(app_root, "ok.xml", "search foo")
    monkeypatch.setenv("AUDIT_FAKE_TOKEN", "tok")

    opener = _FakeOpener(
        [
            _FakeResponse(status=201, body=b'{"sid": "abc"}'),
            _FakeResponse(
                status=200,
                body=(
                    b'{"entry": [{"content": {"isFailed": false, '
                    b'"isDone": true, "resultCount": 0, '
                    b'"messages": []}}]}'
                ),
            ),
            _FakeResponse(status=200, body=b"{}"),
        ]
    )
    monkeypatch.setattr(audit.urllib.request, "urlopen", opener)

    rc = audit.main(
        [
            "--app-root",
            str(app_root),
            "--token-var",
            "AUDIT_FAKE_TOKEN",
        ]
    )
    cap = capsys.readouterr()
    assert rc == 0
    assert "[WARN]" in cap.err
    assert "bad.xml" in cap.err
    assert "XML parse error" in cap.err
