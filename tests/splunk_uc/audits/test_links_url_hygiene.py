r"""Regression tests for ``audit-links`` URL hygiene.

The audit was crashing on the live catalogue with ``ValueError: Invalid
IPv6 URL`` because:

1.  ``URL_PATTERN`` was permissive (``https?://[^\s,<>]+``) and dragged
    markdown decoration into the URL match — ``http://...]\``` (the
    closing markdown-table cell + closing inline-code backtick), and
    ``https://{cnf['VXRM_FQDN']}/.../...\"`` (trailing JSON-escaped
    double-quote from a code fence).
2.  ``normalize_url`` stripped ``.``/``,``/``;``/``!`` and unbalanced
    ``)`` / ``]`` but **not** trailing inline-code backticks, curly
    braces, double quotes, or single quotes — so those characters
    survived into the URL.
3.  ``main()`` then called ``urlsplit(u).netloc.lower()`` on every URL
    without try/except. A single malformed URL (e.g. the literal
    placeholder ``https://[server]:[port]/...``) aborted the whole
    audit before any HTTP probe ran.

This file pins the three contracts that fix the crash:

* ``URL_PATTERN`` MUST NOT include trailing inline-code, curly-brace,
  quote, or backslash characters in the captured URL.
* ``normalize_url`` MUST strip trailing inline-code-backtick, double-
  quote, single-quote, curly-brace, and backslash characters.
* ``main()`` MUST tolerate at least one malformed URL via try/except
  on ``urlsplit`` (the audit becomes non-crashing; the malformed URL
  is silently dropped so it doesn't pollute the host map).

We deliberately keep the regex-tightening conservative: any printable
characters except whitespace, ``,``, ``<``, ``>``, the inline-code
backtick, curly braces, ASCII single / double quotes, and the
backslash are still allowed. That keeps URL fragments like
``Entropy_(information_theory)`` intact while killing the markdown-
decoration class of false positives.
"""

from __future__ import annotations

import pytest
import importlib


@pytest.fixture
def links_mod():
    """Re-import the audit so each test sees pristine module state."""

    import splunk_uc.audits.links as m

    importlib.reload(m)
    return m


# ----------------------------------------------------------------------
# URL_PATTERN — captured URL must not include markdown decoration
# ----------------------------------------------------------------------


def test_url_pattern_excludes_trailing_backtick(links_mod) -> None:
    r"""A code-fenced URL ``\`http://x/path\``` must extract as
    ``http://x/path``, not ``http://x/path\```.
    """

    raw = "see `http://example.com/health` for details"
    hits = links_mod.URL_PATTERN.findall(raw)
    assert hits, "URL_PATTERN should still match http URLs"
    for h in hits:
        assert not h.endswith("`"), h


def test_url_pattern_excludes_trailing_double_quote(links_mod) -> None:
    """A JSON-embedded URL like ``"https://x/y"`` must extract as
    ``https://x/y``, not include the closing ``"``.
    """

    raw = 'config = "https://example.com/api"'
    hits = links_mod.URL_PATTERN.findall(raw)
    assert hits
    for h in hits:
        assert not h.endswith('"'), h


def test_url_pattern_excludes_trailing_curly_brace(links_mod) -> None:
    """A templated URL like ``https://{host}/path`` must NOT bleed
    into adjacent markdown braces.
    """

    raw = "POST https://example.com/api}"  # accidental trailing brace
    hits = links_mod.URL_PATTERN.findall(raw)
    assert hits
    for h in hits:
        assert "}" not in h, h


def test_url_pattern_excludes_trailing_backslash(links_mod) -> None:
    raw = 'reference = "https://example.com/path\\nmore"'
    hits = links_mod.URL_PATTERN.findall(raw)
    assert hits
    for h in hits:
        assert "\\" not in h, h


# ----------------------------------------------------------------------
# normalize_url — trailing decoration strip
# ----------------------------------------------------------------------


def test_normalize_url_strips_trailing_backtick(links_mod) -> None:
    assert links_mod.normalize_url("http://x.io/path`") == "http://x.io/path"


def test_normalize_url_strips_trailing_double_quote(links_mod) -> None:
    assert links_mod.normalize_url('http://x.io/path"') == "http://x.io/path"


def test_normalize_url_strips_trailing_single_quote(links_mod) -> None:
    assert links_mod.normalize_url("http://x.io/path'") == "http://x.io/path"


def test_normalize_url_strips_trailing_curly_brace(links_mod) -> None:
    assert links_mod.normalize_url("http://x.io/path}") == "http://x.io/path"


def test_normalize_url_strips_trailing_backslash(links_mod) -> None:
    assert links_mod.normalize_url("http://x.io/path\\") == "http://x.io/path"


def test_normalize_url_strips_chained_decoration(links_mod) -> None:
    r"""Real catalog case: trailing inline-code backtick + sentence
    punctuation should be stripped down to the bare URL."""

    out = links_mod.normalize_url("http://x.io/path`.,;!")
    assert out == "http://x.io/path"


def test_normalize_url_preserves_balanced_parentheses(links_mod) -> None:
    """Existing contract — must not regress."""

    url = "https://en.wikipedia.org/wiki/Entropy_(information_theory)"
    assert links_mod.normalize_url(url) == url


# ----------------------------------------------------------------------
# main() — must not crash on malformed URLs
# ----------------------------------------------------------------------


def test_main_tolerates_malformed_urls(
    links_mod,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Live catalogue had 5 garbage URLs (placeholder-bracket strings
    like ``https://[server]:[port]/ums/check-status``) that broke
    ``urlsplit``. The audit MUST not abort — it should warn (or
    silently drop) the malformed URL and continue.

    We stub ``collect_urls`` and ``load_ignore_patterns`` so the
    test stays hermetic.
    """

    # 1 malformed URL + 1 good URL. With --dry-run the audit never
    # actually hits the network, so we exercise the parsing/grouping
    # path that previously crashed.
    bad = "https://[server]:[port]/ums/check-status"
    good = "https://example.com/api"
    monkeypatch.setattr(
        links_mod,
        "collect_urls",
        lambda: {bad: ["UC-1.1.1"], good: ["UC-1.1.2"]},
    )
    monkeypatch.setattr(links_mod, "load_ignore_patterns", lambda: [])

    # --dry-run path: still must not crash on bad URL.
    rc = links_mod.main(["--dry-run"])
    assert rc == 0
    captured = capsys.readouterr()
    out = captured.out + captured.err
    # The good URL must appear in the dry-run output.
    assert good in out


def test_main_live_path_tolerates_malformed_urls(
    links_mod,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The live host-grouping path (not dry-run) is where the original
    ``ValueError: Invalid IPv6 URL`` crash happened, because
    ``urlsplit(u).netloc`` was called on every URL without try/except.

    Stub ``check_url`` so we don't hit the network; verify the audit
    completes, reports the good URL as live, and emits a WARN line for
    the malformed URL it had to skip.
    """

    bad = "https://[server]:[port]/ums/check-status"
    good = "https://example.com/api"
    monkeypatch.setattr(
        links_mod,
        "collect_urls",
        lambda: {bad: ["UC-1.1.1"], good: ["UC-1.1.2"]},
    )
    monkeypatch.setattr(links_mod, "load_ignore_patterns", lambda: [])
    monkeypatch.setattr(
        links_mod, "check_url", lambda u: (True, "HEAD 200")
    )

    rc = links_mod.main([])
    assert rc == 0, "audit must not crash on a malformed URL"

    captured = capsys.readouterr()
    combined = captured.out + captured.err

    # The malformed URL must be reported as skipped, not as broken,
    # not via a Python traceback.
    assert "WARN" in combined and "malformed URL" in combined
    assert "Traceback" not in combined
    assert "ValueError" not in combined
