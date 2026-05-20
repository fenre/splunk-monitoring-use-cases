"""Unit tests for `src/splunk_uc/audits/action_pins.py`.

The audit verifies that every pinned third-party Action SHA in
`.github/workflows/*.yml` and `.github/actions/*/action.yml` matches
its trailing `# vX.Y.Z` tag comment by calling the GitHub
``/git/ref/tags/<tag>`` endpoint and (for annotated tags)
following the indirection through ``/git/tags/<sha>``.

This test module pins every contract surface:

- Module-level invariants (regex shapes, ``GITHUB_API`` constant).
- ``_iter_pin_sources`` (workflows-dir only, actions-dir only, both,
  neither).
- ``collect_pins`` (accepts both ``.github/`` and ``.github/workflows/``
  inputs; parses valid ``uses:`` lines; skips ``./`` and ``.``
  local composite-action references; aggregates duplicate pins;
  ignores non-matching lines).
- ``to_owner_repo`` (canonical happy path; subpath stripping;
  malformed-input ``ValueError``).
- ``resolve_tag_sha`` (lightweight-tag happy path; annotated-tag
  indirection; ``HTTPError 404`` → ``ValueError``;
  ``HTTPError 403/5xx`` → ``_TransientError``; non-4xx-non-5xx
  ``HTTPError`` re-raises; ``URLError`` → ``_TransientError``;
  annotated-tag second-hop ``HTTPError 403/5xx`` → ``_TransientError``;
  annotated-tag second-hop ``HTTPError 404`` re-raises;
  annotated-tag second-hop ``URLError`` → ``_TransientError``).
- ``main()`` (missing ``.github`` dir → 2; no pins found → 2;
  all-clean happy path → 0; SHA mismatch → 1; ``ValueError`` from
  ``to_owner_repo`` → 1; transient errors only → 0 with warning;
  transient errors with ``verified == 0`` → 0 with extra advice;
  ``GITHUB_TOKEN`` / ``GH_TOKEN`` env wired into Authorization
  header; ``HTTPError`` non-transient that escapes
  ``resolve_tag_sha`` → 1 entry in mismatches; ``KeyError`` from
  malformed payload → 1; default ``argv=None`` works).
- The ``__main__`` block exists with ``raise SystemExit(main())``.
"""

from __future__ import annotations

import json
import pathlib
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError

import pytest

from splunk_uc.audits import action_pins as ap

# Python 3.14 + pytest 8 surface a `PytestUnraisableExceptionWarning`
# whenever an `HTTPError` is constructed and garbage-collected because
# `urllib.error.HTTPError` inherits from `addinfourl` → `addbase` →
# `_TemporaryFileCloser`, whose `__del__` runs even when `fp=None`
# was passed in. The warning is harmless test-infrastructure noise:
# the audit code only reads `exc.code` and never touches `exc.fp`. We
# filter it module-wide so all `resolve_tag_sha` HTTPError tests pass.
pytestmark = pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")


# ----------------------------------------------------- module-level invariants


def test_module_sha_regex_matches_40_hex_chars() -> None:
    assert ap._SHA_RE.fullmatch("a" * 40) is not None
    assert ap._SHA_RE.fullmatch("0123456789abcdef" * 2 + "12345678") is not None
    assert ap._SHA_RE.fullmatch("g" * 40) is None  # 'g' is not hex
    assert ap._SHA_RE.fullmatch("a" * 39) is None  # too short


def test_module_uses_regex_matches_canonical_pin_line() -> None:
    line = "    - uses: actions/checkout@" + "a" * 40 + "  # v4.1.7"
    m = ap._USES_RE.match(line)
    assert m is not None
    assert m["action"] == "actions/checkout"
    assert m["sha"] == "a" * 40
    assert m["tag"] == "v4.1.7"


def test_module_uses_regex_accepts_no_leading_dash() -> None:
    line = "uses: actions/setup-python@" + "b" * 40 + " # v5.1.0"
    m = ap._USES_RE.match(line)
    assert m is not None
    assert m["tag"] == "v5.1.0"


def test_module_uses_regex_rejects_unpinned_action() -> None:
    """A `uses:` line without 40-char hex SHA must not match."""
    line = "    - uses: actions/checkout@v4 # v4"
    assert ap._USES_RE.match(line) is None


def test_module_uses_regex_rejects_missing_comment() -> None:
    """The trailing # <tag> is required by the contract."""
    line = "    - uses: actions/checkout@" + "a" * 40
    assert ap._USES_RE.match(line) is None


def test_module_github_api_constant() -> None:
    assert ap.GITHUB_API == "https://api.github.com"


# --------------------------------------------------- _iter_pin_sources


def test_iter_pin_sources_includes_workflows_only(tmp_path: Path) -> None:
    workflows = tmp_path / "workflows"
    workflows.mkdir()
    (workflows / "ci.yml").write_text("x", encoding="utf-8")
    (workflows / "deploy.yml").write_text("x", encoding="utf-8")
    sources = ap._iter_pin_sources(tmp_path)
    assert len(sources) == 2
    names = sorted(p.name for p in sources)
    assert names == ["ci.yml", "deploy.yml"]


def test_iter_pin_sources_includes_actions_only(tmp_path: Path) -> None:
    actions = tmp_path / "actions" / "setup-x"
    actions.mkdir(parents=True)
    (actions / "action.yml").write_text("x", encoding="utf-8")
    sources = ap._iter_pin_sources(tmp_path)
    assert len(sources) == 1
    assert sources[0].name == "action.yml"


def test_iter_pin_sources_includes_both(tmp_path: Path) -> None:
    (tmp_path / "workflows").mkdir()
    (tmp_path / "workflows" / "a.yml").write_text("x", encoding="utf-8")
    actions = tmp_path / "actions" / "setup-foo"
    actions.mkdir(parents=True)
    (actions / "action.yml").write_text("x", encoding="utf-8")
    sources = ap._iter_pin_sources(tmp_path)
    assert len(sources) == 2


def test_iter_pin_sources_returns_empty_when_neither_exists(tmp_path: Path) -> None:
    assert ap._iter_pin_sources(tmp_path) == []


def test_iter_pin_sources_sorts_workflows_alphabetically(tmp_path: Path) -> None:
    """Workflows are extended in sorted order; deterministic output matters for diffs."""
    workflows = tmp_path / "workflows"
    workflows.mkdir()
    (workflows / "z.yml").write_text("x", encoding="utf-8")
    (workflows / "a.yml").write_text("x", encoding="utf-8")
    sources = ap._iter_pin_sources(tmp_path)
    assert [p.name for p in sources] == ["a.yml", "z.yml"]


# ------------------------------------------------------------ collect_pins


def test_collect_pins_accepts_github_dir_directly(tmp_path: Path) -> None:
    """Passing `.github` reads workflows + actions both."""
    workflows = tmp_path / "workflows"
    workflows.mkdir()
    (workflows / "ci.yml").write_text(
        "    - uses: actions/checkout@" + "a" * 40 + " # v4.1.7\n",
        encoding="utf-8",
    )
    pins = ap.collect_pins(tmp_path)
    assert ("actions/checkout", "v4.1.7", "a" * 40) in pins


def test_collect_pins_accepts_workflows_dir_via_parent_detection(tmp_path: Path) -> None:
    """Passing `.github/workflows` must walk back up to `.github` first."""
    workflows = tmp_path / "workflows"
    workflows.mkdir()
    (workflows / "ci.yml").write_text(
        "    - uses: actions/checkout@" + "b" * 40 + " # v4.0.0\n",
        encoding="utf-8",
    )
    pins = ap.collect_pins(workflows)
    assert ("actions/checkout", "v4.0.0", "b" * 40) in pins


def test_collect_pins_skips_local_composite_actions(tmp_path: Path) -> None:
    """`./.github/actions/...` references are out of scope."""
    workflows = tmp_path / "workflows"
    workflows.mkdir()
    (workflows / "ci.yml").write_text(
        "    - uses: ./.github/actions/setup-python@" + "c" * 40 + " # v1.0\n",
        encoding="utf-8",
    )
    pins = ap.collect_pins(tmp_path)
    assert pins == {}


def test_collect_pins_skips_local_dot_prefix_actions(tmp_path: Path) -> None:
    """Plain `.` prefix is also out of scope."""
    workflows = tmp_path / "workflows"
    workflows.mkdir()
    (workflows / "ci.yml").write_text(
        "    - uses: .github/actions/setup-x@" + "d" * 40 + " # v0.1\n",
        encoding="utf-8",
    )
    pins = ap.collect_pins(tmp_path)
    assert pins == {}


def test_collect_pins_aggregates_duplicate_pins(tmp_path: Path) -> None:
    """Same (action, tag, sha) triple → single key, multi-occurrence value."""
    workflows = tmp_path / "workflows"
    workflows.mkdir()
    sha = "e" * 40
    body = (
        "    - uses: actions/checkout@" + sha + " # v4.1.7\n"
        "    - uses: actions/checkout@" + sha + " # v4.1.7\n"
    )
    (workflows / "ci.yml").write_text(body, encoding="utf-8")
    pins = ap.collect_pins(tmp_path)
    key = ("actions/checkout", "v4.1.7", sha)
    assert key in pins
    assert len(pins[key]) == 2
    assert pins[key][0][1] == 1  # lineno
    assert pins[key][1][1] == 2


def test_collect_pins_aggregates_across_files(tmp_path: Path) -> None:
    workflows = tmp_path / "workflows"
    workflows.mkdir()
    sha = "f" * 40
    (workflows / "a.yml").write_text(
        "    - uses: actions/checkout@" + sha + " # v4.1.7\n", encoding="utf-8"
    )
    (workflows / "b.yml").write_text(
        "    - uses: actions/checkout@" + sha + " # v4.1.7\n", encoding="utf-8"
    )
    pins = ap.collect_pins(tmp_path)
    key = ("actions/checkout", "v4.1.7", sha)
    assert len(pins[key]) == 2


def test_collect_pins_ignores_non_uses_lines(tmp_path: Path) -> None:
    workflows = tmp_path / "workflows"
    workflows.mkdir()
    (workflows / "ci.yml").write_text(
        "name: CI\non: push\njobs:\n  build:\n    runs-on: ubuntu-latest\n",
        encoding="utf-8",
    )
    pins = ap.collect_pins(tmp_path)
    assert pins == {}


# --------------------------------------------------------------- to_owner_repo


def test_to_owner_repo_canonical() -> None:
    assert ap.to_owner_repo("actions/checkout") == "actions/checkout"


def test_to_owner_repo_strips_subpath() -> None:
    assert ap.to_owner_repo("docker/setup-buildx-action/foo/bar") == "docker/setup-buildx-action"


def test_to_owner_repo_raises_on_malformed_input() -> None:
    with pytest.raises(ValueError, match="unparseable action"):
        ap.to_owner_repo("bareword")


def test_to_owner_repo_raises_on_empty_input() -> None:
    with pytest.raises(ValueError):
        ap.to_owner_repo("")


# ------------------------------------------------------------- _TransientError


def test_transient_error_is_exception_subclass() -> None:
    """The custom exception lets callers treat transient errors distinctly."""
    assert issubclass(ap._TransientError, Exception)


# ------------------------------------------- resolve_tag_sha mocking helpers


class _FakeResponse:
    """Mimic the context-manager protocol of urlopen's response."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def _make_urlopen(payloads: Sequence[dict[str, Any] | Exception]) -> Any:
    """Return a fake `urlopen` that returns successive payloads or raises."""
    calls = {"n": 0}

    def fake_urlopen(req: Any, timeout: int = 15) -> _FakeResponse:
        idx = calls["n"]
        calls["n"] += 1
        item = payloads[idx]
        if isinstance(item, Exception):
            raise item
        return _FakeResponse(item)

    return fake_urlopen


def _http_error(code: int) -> HTTPError:
    """Construct an HTTPError without leaving a dangling fp.

    Python 3.14 emits PytestUnraisableExceptionWarning when an
    HTTPError carrying a `BytesIO` `fp` is garbage-collected
    because `_TemporaryFileCloser.__del__` tries to close it.
    Passing `fp=None` sidesteps the destructor path entirely; the
    audit only reads `exc.code` so the missing `fp` is fine.
    """
    return HTTPError(
        url="http://x",
        code=code,
        msg="boom",
        hdrs=None,  # type: ignore[arg-type]
        fp=None,
    )


# ---------------------------------------------------------- resolve_tag_sha


def test_resolve_tag_sha_lightweight_tag_happy_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A lightweight tag returns ``object.sha`` directly."""

    def fake_load(fp: Any) -> dict[str, Any]:
        return {"object": {"type": "commit", "sha": "abc123"}}

    monkeypatch.setattr(ap.urllib.request, "urlopen", _make_urlopen([{}]))
    monkeypatch.setattr(ap.json, "load", fake_load)
    sha = ap.resolve_tag_sha("actions/checkout", "v4", {})
    assert sha == "abc123"


def test_resolve_tag_sha_annotated_tag_double_hop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An annotated tag requires a second hop via ``object.url``."""
    payloads = [
        {"object": {"type": "tag", "url": "http://api/x", "sha": "deadbeef"}},
        {"object": {"sha": "feedface"}},
    ]
    monkeypatch.setattr(ap.urllib.request, "urlopen", _make_urlopen(payloads))
    real_loads = json.loads

    def fake_load(fp: Any) -> Any:
        return real_loads(fp.read())

    monkeypatch.setattr(ap.json, "load", fake_load)
    sha = ap.resolve_tag_sha("actions/checkout", "v4.1.7", {})
    assert sha == "feedface"


def test_resolve_tag_sha_returns_empty_when_no_sha_in_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing ``object.sha`` falls through to the empty-string fallback."""
    monkeypatch.setattr(ap.urllib.request, "urlopen", _make_urlopen([{}]))
    monkeypatch.setattr(ap.json, "load", lambda fp: {"object": {"type": "commit"}})
    sha = ap.resolve_tag_sha("actions/checkout", "v4", {})
    assert sha == ""


def test_resolve_tag_sha_no_object_key_returns_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``payload.get('object') or {}`` falls through when key absent."""
    monkeypatch.setattr(ap.urllib.request, "urlopen", _make_urlopen([{}]))
    monkeypatch.setattr(ap.json, "load", lambda fp: {})
    sha = ap.resolve_tag_sha("actions/checkout", "v4", {})
    assert sha == ""


def test_resolve_tag_sha_404_raises_value_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raising_urlopen(req: Any, timeout: int = 15) -> Any:
        raise _http_error(404)

    monkeypatch.setattr(ap.urllib.request, "urlopen", raising_urlopen)
    with pytest.raises(ValueError, match="does not exist"):
        ap.resolve_tag_sha("actions/checkout", "v999", {})


def test_resolve_tag_sha_403_raises_transient_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raising_urlopen(req: Any, timeout: int = 15) -> Any:
        raise _http_error(403)

    monkeypatch.setattr(ap.urllib.request, "urlopen", raising_urlopen)
    with pytest.raises(ap._TransientError, match="HTTP 403"):
        ap.resolve_tag_sha("actions/checkout", "v4", {})


def test_resolve_tag_sha_500_raises_transient_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raising_urlopen(req: Any, timeout: int = 15) -> Any:
        raise _http_error(503)

    monkeypatch.setattr(ap.urllib.request, "urlopen", raising_urlopen)
    with pytest.raises(ap._TransientError, match="HTTP 503"):
        ap.resolve_tag_sha("actions/checkout", "v4", {})


def test_resolve_tag_sha_other_http_error_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A 401 etc. is neither 404 nor 403/5xx → re-raised as-is."""

    def raising_urlopen(req: Any, timeout: int = 15) -> Any:
        raise _http_error(401)

    monkeypatch.setattr(ap.urllib.request, "urlopen", raising_urlopen)
    with pytest.raises(HTTPError):
        ap.resolve_tag_sha("actions/checkout", "v4", {})


def test_resolve_tag_sha_url_error_raises_transient(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raising_urlopen(req: Any, timeout: int = 15) -> Any:
        raise URLError("DNS down")

    monkeypatch.setattr(ap.urllib.request, "urlopen", raising_urlopen)
    with pytest.raises(ap._TransientError, match="network error"):
        ap.resolve_tag_sha("actions/checkout", "v4", {})


def test_resolve_tag_sha_annotated_tag_second_hop_403(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """403 on the dereference hop is also a transient error."""
    calls = {"n": 0}

    def two_step_urlopen(req: Any, timeout: int = 15) -> Any:
        idx = calls["n"]
        calls["n"] += 1
        if idx == 0:
            return _FakeResponse({})
        raise _http_error(403)

    monkeypatch.setattr(ap.urllib.request, "urlopen", two_step_urlopen)
    monkeypatch.setattr(
        ap.json,
        "load",
        lambda fp: {"object": {"type": "tag", "url": "http://api/x", "sha": "x"}},
    )
    with pytest.raises(ap._TransientError, match="dereferencing annotated tag"):
        ap.resolve_tag_sha("actions/checkout", "v4", {})


def test_resolve_tag_sha_annotated_tag_second_hop_504(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"n": 0}

    def two_step_urlopen(req: Any, timeout: int = 15) -> Any:
        idx = calls["n"]
        calls["n"] += 1
        if idx == 0:
            return _FakeResponse({})
        raise _http_error(504)

    monkeypatch.setattr(ap.urllib.request, "urlopen", two_step_urlopen)
    monkeypatch.setattr(
        ap.json,
        "load",
        lambda fp: {"object": {"type": "tag", "url": "http://api/x", "sha": "x"}},
    )
    with pytest.raises(ap._TransientError):
        ap.resolve_tag_sha("actions/checkout", "v4", {})


def test_resolve_tag_sha_annotated_tag_second_hop_404_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """404 on second hop is *not* in the 403/5xx range → re-raised as-is."""
    calls = {"n": 0}

    def two_step_urlopen(req: Any, timeout: int = 15) -> Any:
        idx = calls["n"]
        calls["n"] += 1
        if idx == 0:
            return _FakeResponse({})
        raise _http_error(404)

    monkeypatch.setattr(ap.urllib.request, "urlopen", two_step_urlopen)
    monkeypatch.setattr(
        ap.json,
        "load",
        lambda fp: {"object": {"type": "tag", "url": "http://api/x", "sha": "x"}},
    )
    with pytest.raises(HTTPError):
        ap.resolve_tag_sha("actions/checkout", "v4", {})


def test_resolve_tag_sha_annotated_tag_second_hop_url_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"n": 0}

    def two_step_urlopen(req: Any, timeout: int = 15) -> Any:
        idx = calls["n"]
        calls["n"] += 1
        if idx == 0:
            return _FakeResponse({})
        raise URLError("connection reset")

    monkeypatch.setattr(ap.urllib.request, "urlopen", two_step_urlopen)
    monkeypatch.setattr(
        ap.json,
        "load",
        lambda fp: {"object": {"type": "tag", "url": "http://api/x", "sha": "x"}},
    )
    with pytest.raises(ap._TransientError, match="dereferencing tag"):
        ap.resolve_tag_sha("actions/checkout", "v4", {})


# -------------------------------------------------------- main() — sandbox fixtures


@pytest.fixture
def fake_github_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Build a synthetic repo with `.github/` and rewire __file__ via parents[3]."""
    fake_root = tmp_path / "fakerepo"
    src_audits = fake_root / "src" / "splunk_uc" / "audits"
    src_audits.mkdir(parents=True)
    # We don't actually have to write a real action_pins.py file — monkey-patching
    # ap.__file__ is enough for the parents[3] resolution.
    fake_module_path = src_audits / "action_pins.py"
    fake_module_path.write_text("x", encoding="utf-8")
    monkeypatch.setattr(ap, "__file__", str(fake_module_path))
    (fake_root / ".github").mkdir()
    return fake_root


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Drop GITHUB_TOKEN / GH_TOKEN by default so tests are deterministic."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)


def _write_workflow(fake_root: Path, body: str, name: str = "ci.yml") -> None:
    wf = fake_root / ".github" / "workflows"
    wf.mkdir(exist_ok=True)
    (wf / name).write_text(body, encoding="utf-8")


# ----------------------------------------------------------------- main()


def test_main_missing_github_dir_exits_2(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_root = tmp_path / "fakerepo"
    src_audits = fake_root / "src" / "splunk_uc" / "audits"
    src_audits.mkdir(parents=True)
    fake_module_path = src_audits / "action_pins.py"
    fake_module_path.write_text("x", encoding="utf-8")
    monkeypatch.setattr(ap, "__file__", str(fake_module_path))
    # No .github/ dir.

    rc = ap.main([])
    assert rc == 2
    assert "is not a directory" in capsys.readouterr().err


def test_main_no_pins_found_exits_2(
    fake_github_repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A `.github/` with no workflows or actions returns 2."""
    rc = ap.main([])
    assert rc == 2
    assert "no pinned `uses:` directives found" in capsys.readouterr().err


def test_main_happy_path_returns_zero(
    fake_github_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sha = "a" * 40
    _write_workflow(fake_github_repo, f"    - uses: actions/checkout@{sha} # v4.1.7\n")
    monkeypatch.setattr(ap, "resolve_tag_sha", lambda owner, tag, headers: sha)
    rc = ap.main([])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Verifying 1 (action, tag, sha)" in out
    assert "OK" in out
    assert "All 1 pins verified" in out


def test_main_mismatch_returns_one(
    fake_github_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Pinned SHA != resolved SHA → exit 1 with a remediation message."""
    pinned = "a" * 40
    actual = "b" * 40
    _write_workflow(fake_github_repo, f"    - uses: actions/checkout@{pinned} # v4.1.7\n")
    monkeypatch.setattr(ap, "resolve_tag_sha", lambda owner, tag, headers: actual)
    rc = ap.main([])
    assert rc == 1
    out = capsys.readouterr().out
    assert "1 MISMATCHES" in out
    assert "Remediation" in out
    assert "actions/checkout" in out
    assert "ci.yml:1" in out


def test_main_to_owner_repo_value_error_propagates(
    fake_github_repo: Path,
) -> None:
    """A malformed action without `/` propagates from `to_owner_repo`.

    The audit's try/except in main() wraps `resolve_tag_sha` only —
    `to_owner_repo` is called outside the guard. A bareword action
    therefore escapes as an uncaught `ValueError`. This is documented
    behaviour: every real GitHub Action has at least `owner/name`, so
    the path is defensive but unreachable in practice. We pin the
    propagation explicitly so any future refactor that swallows the
    error doesn't change behaviour silently.
    """
    sha = "a" * 40
    _write_workflow(fake_github_repo, f"    - uses: bareword@{sha} # v1\n")
    with pytest.raises(ValueError, match="unparseable action"):
        ap.main([])


def test_main_transient_error_emits_warning_returns_zero(
    fake_github_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sha = "a" * 40
    _write_workflow(fake_github_repo, f"    - uses: actions/checkout@{sha} # v4.1.7\n")

    def raise_transient(owner: str, tag: str, headers: dict[str, str]) -> str:
        raise ap._TransientError("rate limited")

    monkeypatch.setattr(ap, "resolve_tag_sha", raise_transient)
    rc = ap.main([])
    assert rc == 0
    out = capsys.readouterr().out
    assert "::warning::" in out
    assert "SKIP" in out
    assert "All pins skipped due to transient errors" in out


def test_main_transient_with_other_verified_does_not_emit_extra_advice(
    fake_github_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When `verified >= 1`, the extra rate-limit guidance is suppressed."""
    sha_a = "a" * 40
    sha_b = "b" * 40
    _write_workflow(
        fake_github_repo,
        f"    - uses: actions/checkout@{sha_a} # v4.1.7\n"
        f"    - uses: actions/setup-python@{sha_b} # v5.0.0\n",
    )

    def selective(owner: str, tag: str, headers: dict[str, str]) -> str:
        if owner.startswith("actions/checkout"):
            return sha_a
        raise ap._TransientError("rate limit")

    monkeypatch.setattr(ap, "resolve_tag_sha", selective)
    rc = ap.main([])
    assert rc == 0
    out = capsys.readouterr().out
    assert "::warning::" in out
    assert "All pins skipped" not in out


def test_main_http_error_treated_as_mismatch(
    fake_github_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A non-transient HTTP/URLError that escapes resolve_tag_sha → mismatch."""
    sha = "a" * 40
    _write_workflow(fake_github_repo, f"    - uses: actions/checkout@{sha} # v4.1.7\n")

    def raise_http(owner: str, tag: str, headers: dict[str, str]) -> str:
        raise _http_error(401)

    monkeypatch.setattr(ap, "resolve_tag_sha", raise_http)
    rc = ap.main([])
    assert rc == 1
    out = capsys.readouterr().out
    assert "API error" in out


def test_main_url_error_treated_as_mismatch(
    fake_github_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sha = "a" * 40
    _write_workflow(fake_github_repo, f"    - uses: actions/checkout@{sha} # v4.1.7\n")

    def raise_url(owner: str, tag: str, headers: dict[str, str]) -> str:
        raise URLError("blah")

    monkeypatch.setattr(ap, "resolve_tag_sha", raise_url)
    rc = ap.main([])
    assert rc == 1


def test_main_key_error_from_malformed_payload_is_mismatch(
    fake_github_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A `KeyError` from a broken payload is treated as a real mismatch."""
    sha = "a" * 40
    _write_workflow(fake_github_repo, f"    - uses: actions/checkout@{sha} # v4.1.7\n")

    def raise_key(owner: str, tag: str, headers: dict[str, str]) -> str:
        raise KeyError("object")

    monkeypatch.setattr(ap, "resolve_tag_sha", raise_key)
    rc = ap.main([])
    assert rc == 1
    out = capsys.readouterr().out
    assert "1 MISMATCHES" in out


def test_main_value_error_404_treated_as_mismatch(
    fake_github_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sha = "a" * 40
    _write_workflow(fake_github_repo, f"    - uses: actions/checkout@{sha} # v4.1.7\n")

    def raise_val(owner: str, tag: str, headers: dict[str, str]) -> str:
        raise ValueError("upstream tag 'v4' does not exist on actions/checkout")

    monkeypatch.setattr(ap, "resolve_tag_sha", raise_val)
    rc = ap.main([])
    assert rc == 1


def test_main_github_token_wired_to_authorization_header(
    fake_github_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sha = "a" * 40
    _write_workflow(fake_github_repo, f"    - uses: actions/checkout@{sha} # v4.1.7\n")
    captured: dict[str, dict[str, str]] = {}

    def sniffing(owner: str, tag: str, headers: dict[str, str]) -> str:
        captured["headers"] = dict(headers)
        return sha

    monkeypatch.setattr(ap, "resolve_tag_sha", sniffing)
    monkeypatch.setenv("GITHUB_TOKEN", "secret123")
    rc = ap.main([])
    assert rc == 0
    assert captured["headers"]["Authorization"] == "Bearer secret123"


def test_main_gh_token_fallback(
    fake_github_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`GH_TOKEN` is honoured when `GITHUB_TOKEN` is absent."""
    sha = "a" * 40
    _write_workflow(fake_github_repo, f"    - uses: actions/checkout@{sha} # v4.1.7\n")
    captured: dict[str, dict[str, str]] = {}

    def sniffing(owner: str, tag: str, headers: dict[str, str]) -> str:
        captured["headers"] = dict(headers)
        return sha

    monkeypatch.setattr(ap, "resolve_tag_sha", sniffing)
    monkeypatch.setenv("GH_TOKEN", "gh-token-fallback")
    rc = ap.main([])
    assert rc == 0
    assert captured["headers"]["Authorization"] == "Bearer gh-token-fallback"


def test_main_no_token_means_no_authorization_header(
    fake_github_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sha = "a" * 40
    _write_workflow(fake_github_repo, f"    - uses: actions/checkout@{sha} # v4.1.7\n")
    captured: dict[str, dict[str, str]] = {}

    def sniffing(owner: str, tag: str, headers: dict[str, str]) -> str:
        captured["headers"] = dict(headers)
        return sha

    monkeypatch.setattr(ap, "resolve_tag_sha", sniffing)
    rc = ap.main([])
    assert rc == 0
    assert "Authorization" not in captured["headers"]


def test_main_default_user_agent_and_accept_headers(
    fake_github_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sha = "a" * 40
    _write_workflow(fake_github_repo, f"    - uses: actions/checkout@{sha} # v4.1.7\n")
    captured: dict[str, dict[str, str]] = {}

    def sniffing(owner: str, tag: str, headers: dict[str, str]) -> str:
        captured["headers"] = dict(headers)
        return sha

    monkeypatch.setattr(ap, "resolve_tag_sha", sniffing)
    ap.main([])
    assert captured["headers"]["Accept"] == "application/vnd.github+json"
    assert captured["headers"]["X-GitHub-Api-Version"] == "2022-11-28"
    assert "splunk-monitoring-use-cases" in captured["headers"]["User-Agent"]


def test_main_argv_none_falls_through_to_sys_argv(
    fake_github_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sha = "a" * 40
    _write_workflow(fake_github_repo, f"    - uses: actions/checkout@{sha} # v4.1.7\n")
    monkeypatch.setattr(ap, "resolve_tag_sha", lambda owner, tag, headers: sha)
    monkeypatch.setattr(sys, "argv", ["prog"])
    rc = ap.main(None)
    assert rc == 0


def test_main_pins_iterated_sorted_for_deterministic_output(
    fake_github_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The for-loop sorts pins; the OK lines must come out in sorted order."""
    sha_a = "a" * 40
    sha_b = "b" * 40
    _write_workflow(
        fake_github_repo,
        # Add z first, a second; sorted output should put 'a' before 'z'.
        f"    - uses: zorg/foo@{sha_b} # v9\n    - uses: aaa/foo@{sha_a} # v1\n",
    )
    monkeypatch.setattr(
        ap,
        "resolve_tag_sha",
        lambda owner, tag, headers: sha_a if owner.startswith("aaa") else sha_b,
    )
    rc = ap.main([])
    assert rc == 0
    out = capsys.readouterr().out
    aaa_pos = out.find("aaa/foo")
    zorg_pos = out.find("zorg/foo")
    assert 0 <= aaa_pos < zorg_pos


# ---------------------------------------------------------- __main__ block


def test_dunder_main_block_exists() -> None:
    src = pathlib.Path(ap.__file__).read_text(encoding="utf-8")
    assert 'if __name__ == "__main__":' in src
    assert "raise SystemExit(main())" in src
