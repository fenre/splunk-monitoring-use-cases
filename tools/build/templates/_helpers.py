"""tools.build.templates._helpers — escape, slug, markdown, JSON-LD.

Pure-Python helpers shared by every page template. No external
dependencies. Stable enough that downstream tooling (e.g. exports,
embed widgets) can reuse them.

Threat model (codeguard-0-client-side-web-security):

* All UC content originates from trusted Markdown source files in this
  repo. We still escape every string before HTML emission — defence in
  depth in case a future loader admits external content.
* The mini Markdown renderer never executes user input; it parses a
  fixed subset (paragraphs, lists, code, bold/italic, links) and emits
  context-appropriate escapes.
* Link rendering rejects ``javascript:``, ``data:``, and ``vbscript:``
  URL schemes.
"""

from __future__ import annotations

import html
import json as _json
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional


# ---------------------------------------------------------------------------
# Render context (constants threaded through every template)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RenderContext:
    """Immutable per-build settings passed to every template."""

    site_url: str = "https://fenre.github.io/splunk-monitoring-use-cases"
    site_name: str = "Splunk Monitoring Use Cases"
    site_short: str = "Splunk UCs"
    site_tagline: str = (
        "Vendor-curated catalog of Splunk monitoring use cases — "
        "production-ready SPL, dashboards, and compliance mappings."
    )
    asset_styles: str = ""  # styles.<hash>.css filename, set by render_pages
    asset_app_js: str = ""  # app.<hash>.js filename, set by render_pages
    build_id: str = ""      # e.g., short git sha, set by render_pages
    generated_at: str = "1970-01-01T00:00:00Z"
    repo_url: str = "https://github.com/fenre/splunk-monitoring-use-cases"

    # Reverse index for the implementation-ordering roadmap: maps a
    # prerequisite UC id (full "UC-X.Y.Z" form) to the tuple of UC ids
    # that declare it in their ``prerequisiteUseCases`` list. Populated
    # once in render_pages.render() so templates can emit the "Enables"
    # section in O(1) without re-scanning the catalogue per UC.
    # Defaults to an empty mapping so callers that ignore this feature
    # continue to work unchanged. Callers must never mutate the mapping
    # after the context is constructed.
    uc_reverse_prereq: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    # Forward lookup of every UC id -> a (title, wave) pair. Used to
    # render clickable chips with a tooltip and wave badge in the
    # static-site Prerequisites / Enables sections.
    uc_title_index: Mapping[str, tuple[str, str]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Escaping primitives
# ---------------------------------------------------------------------------


def escape(text: Any) -> str:
    """HTML-escape ``text`` in element-content context.

    Uses ``html.escape(quote=True)`` so the same output is also safe in
    quoted attribute values. Coerces non-strings via ``str()``.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    return html.escape(text, quote=True)


def attr(value: Any) -> str:
    """Escape ``value`` for use inside an HTML attribute (always quoted).

    Same as :func:`escape` today; kept distinct so downstream readers
    can spot attribute-context call sites at a glance.
    """
    return escape(value)


# ---------------------------------------------------------------------------
# Slug + ordering helpers
# ---------------------------------------------------------------------------


def slug(name: str) -> str:
    """Lower-case ASCII slug suitable for filesystem paths and URLs.

    Keeps alphanumerics, replaces every other run with a single ``-``.
    Trailing/leading dashes stripped.
    """
    if not name:
        return "category"
    out: list[str] = []
    last_dash = False
    for ch in name.strip().lower():
        if ch.isalnum():
            out.append(ch)
            last_dash = False
        elif not last_dash:
            out.append("-")
            last_dash = True
    s = "".join(out).strip("-")
    return s or "category"


def sort_key(value: Any) -> tuple:
    """Sort key for hierarchical IDs like ``"1.10.2"`` (dotted ints).

    Mirrors ``render_api._sort_key`` so the per-UC and per-category
    iteration order matches the API.
    """
    s = str(value or "")
    parts: list[tuple[int, Any]] = []
    for chunk in s.split("."):
        try:
            parts.append((0, int(chunk)))
        except ValueError:
            parts.append((1, chunk))
    return tuple(parts)


# ---------------------------------------------------------------------------
# Mini Markdown → HTML renderer
# ---------------------------------------------------------------------------

# We deliberately implement a *tiny* Markdown subset rather than pull in
# python-markdown. Reasons:
#   * Reproducibility — pinning a Markdown library version creates a
#     supply-chain dep we'd rather not own.
#   * Performance — ~6,500 UCs × 5 KB markdown each is ~30 MB of text;
#     a pure-Python lexer beats spinning up a parser stack.
#   * Safety surface — we *never* allow raw HTML through. Every
#     character that could close an attribute or open a tag is
#     escaped before emission.
#
# Supported syntax:
#   paragraphs (blank-line separated)
#   bullet lists  (- foo / * foo / • foo)
#   numbered lists (1. foo)
#   fenced code blocks ```spl ... ```
#   inline code   `foo`
#   bold (**foo**) and italic (*foo*)
#   links [text](url)  — URL scheme allow-list (https/http/mailto)


_FENCE_OPEN = re.compile(r"^\s*```(\w*)\s*$")
_FENCE_CLOSE = re.compile(r"^\s*```\s*$")
_LIST_ITEM = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+(.*)$")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
_AUTOLINK = re.compile(r"(?<![\"'>])https?://[^\s<>\"]+")
_SAFE_LINK_SCHEMES = ("http://", "https://", "mailto:", "/", "#", "./", "../")


def render_markdown(md: str) -> str:
    """Convert a tiny Markdown subset to safe HTML.

    Returns the empty string for empty input. Output is *self-contained*
    HTML — every produced token is already escaped.
    """
    if not md:
        return ""
    if not isinstance(md, str):
        md = str(md)

    lines = md.splitlines()
    out: list[str] = []
    i = 0
    n = len(lines)
    in_list_kind: Optional[str] = None
    para_buf: list[str] = []

    def _flush_para() -> None:
        if not para_buf:
            return
        text = " ".join(s.strip() for s in para_buf if s.strip())
        if text:
            out.append("<p>" + _render_inline(text) + "</p>")
        para_buf.clear()

    def _flush_list() -> None:
        nonlocal in_list_kind
        if in_list_kind:
            out.append(f"</{in_list_kind}>")
            in_list_kind = None

    while i < n:
        line = lines[i]
        m_open = _FENCE_OPEN.match(line)
        if m_open:
            _flush_para()
            _flush_list()
            lang = m_open.group(1) or ""
            code_lines: list[str] = []
            i += 1
            while i < n and not _FENCE_CLOSE.match(lines[i]):
                code_lines.append(lines[i])
                i += 1
            i += 1
            cls = f' class="lang-{escape(lang)}"' if lang else ""
            out.append(
                f"<pre><code{cls}>"
                + escape("\n".join(code_lines))
                + "</code></pre>"
            )
            continue

        if not line.strip():
            _flush_para()
            _flush_list()
            i += 1
            continue

        m_li = _LIST_ITEM.match(line)
        if m_li:
            _flush_para()
            kind = "ol" if line.lstrip()[0:1].isdigit() else "ul"
            if in_list_kind and in_list_kind != kind:
                _flush_list()
            if not in_list_kind:
                out.append(f"<{kind}>")
                in_list_kind = kind
            out.append("<li>" + _render_inline(m_li.group(1).strip()) + "</li>")
            i += 1
            continue

        if in_list_kind:
            _flush_list()

        para_buf.append(line)
        i += 1

    _flush_para()
    _flush_list()
    return "\n".join(out)


def _render_inline(text: str) -> str:
    """Apply inline transformations (code, bold, italic, links) and escape."""

    placeholders: list[str] = []

    def _stash(html_token: str) -> str:
        idx = len(placeholders)
        placeholders.append(html_token)
        return f"\x00{idx}\x00"

    def _link_repl(match: "re.Match[str]") -> str:
        label = match.group(1)
        url = match.group(2)
        url_lc = url.lower()
        if not any(url_lc.startswith(s) for s in _SAFE_LINK_SCHEMES):
            return escape(label)
        rel = (
            ' rel="noopener noreferrer" target="_blank"'
            if url_lc.startswith(("http://", "https://"))
            else ""
        )
        return _stash(
            f'<a href="{attr(url)}"{rel}>{_render_inline(label)}</a>'
        )

    text = _LINK.sub(_link_repl, text)
    text = _INLINE_CODE.sub(
        lambda m: _stash("<code>" + escape(m.group(1)) + "</code>"), text
    )
    text = _BOLD.sub(
        lambda m: _stash("<strong>" + escape(m.group(1)) + "</strong>"), text
    )
    text = _ITALIC.sub(
        lambda m: _stash("<em>" + escape(m.group(1)) + "</em>"), text
    )

    text = _AUTOLINK.sub(
        lambda m: _stash(
            f'<a href="{attr(m.group(0))}" rel="noopener noreferrer" '
            f'target="_blank">{escape(m.group(0))}</a>'
        ),
        text,
    )

    text = escape(text)

    def _restore(match: "re.Match[str]") -> str:
        idx = int(match.group(1))
        return placeholders[idx]

    return re.sub(r"\x00(\d+)\x00", _restore, text)


# ---------------------------------------------------------------------------
# JSON-LD builders
# ---------------------------------------------------------------------------


def jsonld_breadcrumb(items: Iterable[tuple[str, str]]) -> dict[str, Any]:
    """Build a schema.org BreadcrumbList JSON-LD payload.

    ``items`` is an ordered iterable of ``(name, url)`` pairs, root first.
    """
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": position,
                "name": name,
                "item": url,
            }
            for position, (name, url) in enumerate(items, start=1)
        ],
    }


def jsonld_techarticle(
    *,
    headline: str,
    description: str,
    url: str,
    site_name: str,
    site_url: str,
    date_modified: str,
    keywords: Optional[list[str]] = None,
    code_sample: Optional[str] = None,
    code_sample_language: str = "spl",
) -> dict[str, Any]:
    """Build a schema.org TechArticle for a single use case."""
    payload: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": headline,
        "description": description,
        "url": url,
        "inLanguage": "en",
        "isAccessibleForFree": True,
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "publisher": {
            "@type": "Organization",
            "name": site_name,
            "url": site_url,
        },
        "dateModified": date_modified,
    }
    if keywords:
        payload["keywords"] = ", ".join(keywords)
    if code_sample:
        payload["proficiencyLevel"] = "Expert"
        payload["hasPart"] = {
            "@type": "SoftwareSourceCode",
            "programmingLanguage": code_sample_language,
            "codeSampleType": "code snippet",
            "text": code_sample,
        }
    return payload


def jsonld_howto(
    *,
    name: str,
    description: str,
    steps: list[tuple[str, str]],
    total_time_iso: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Build a schema.org HowTo if there are at least two steps."""
    if not steps or len(steps) < 2:
        return None
    payload: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": name,
        "description": description,
        "step": [
            {
                "@type": "HowToStep",
                "position": position,
                "name": step_name,
                "text": step_text,
            }
            for position, (step_name, step_text) in enumerate(steps, start=1)
        ],
    }
    if total_time_iso:
        payload["totalTime"] = total_time_iso
    return payload


def jsonld_collection_page(
    *,
    name: str,
    description: str,
    url: str,
    site_name: str,
    site_url: str,
    member_urls: list[str],
    date_modified: str,
) -> dict[str, Any]:
    """Build a schema.org CollectionPage for a category landing page."""
    payload: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": name,
        "description": description,
        "url": url,
        "inLanguage": "en",
        "isAccessibleForFree": True,
        "publisher": {
            "@type": "Organization",
            "name": site_name,
            "url": site_url,
        },
        "dateModified": date_modified,
        "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": len(member_urls),
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": pos,
                    "url": url,
                }
                for pos, url in enumerate(member_urls, start=1)
            ],
        },
    }
    return payload


def jsonld_website(
    *,
    name: str,
    description: str,
    url: str,
) -> dict[str, Any]:
    """Build a schema.org WebSite payload (used by the landing page)."""
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": name,
        "alternateName": "Splunk UCs",
        "description": description,
        "url": url,
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": f"{url}/browse/?q={{search_term_string}}",
            },
            "query-input": "required name=search_term_string",
        },
    }


def jsonld_script(*payloads: dict[str, Any]) -> str:
    """Serialise one or more JSON-LD payloads inside <script> tags.

    Splits into multiple scripts so a malformed payload doesn't poison
    every other graph on the page. Uses ``ensure_ascii=False`` for
    smaller payloads (Unicode glyphs gzip well).
    """
    parts: list[str] = []
    for payload in payloads:
        if not payload:
            continue
        body = _json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        # </script> in any string context could close the tag. The JSON
        # escaping above produces "<\/script>" only if we explicitly opt
        # in — we don't. So defensively replace the literal sequence in
        # the serialised string.
        body = body.replace("</", "<\\/")
        parts.append(
            f'<script type="application/ld+json">{body}</script>'
        )
    return "".join(parts)


# ---------------------------------------------------------------------------
# UC-specific helpers (criticality labels, status icons)
# ---------------------------------------------------------------------------


_CRITICALITY_LABELS = {
    "critical": ("Critical", "crit"),
    "high":     ("High",     "high"),
    "medium":   ("Medium",   "med"),
    "low":      ("Low",      "low"),
}

_DIFFICULTY_LABELS = {
    "beginner":     ("Beginner",     "beg"),
    "intermediate": ("Intermediate", "int"),
    "advanced":     ("Advanced",     "adv"),
    "expert":       ("Expert",       "exp"),
}

_WAVE_LABELS = {
    "crawl": ("Crawl", "crawl"),
    "walk":  ("Walk",  "walk"),
    "run":   ("Run",   "run"),
}


def criticality_label(value: Any) -> tuple[str, str]:
    """Return ``(human_label, css_modifier)`` for a UC ``c`` field."""
    key = str(value or "").lower().strip()
    return _CRITICALITY_LABELS.get(key, (value or "—", "unk"))


def difficulty_label(value: Any) -> tuple[str, str]:
    """Return ``(human_label, css_modifier)`` for a UC ``f`` field."""
    key = str(value or "").lower().strip()
    return _DIFFICULTY_LABELS.get(key, (value or "—", "unk"))


def wave_label(value: Any) -> tuple[str, str] | None:
    """Return ``(human_label, css_modifier)`` for a UC ``wv`` field, or None.

    Returns ``None`` when no wave is set or the value is not one of
    ``crawl`` / ``walk`` / ``run`` — callers can use that to skip the
    badge entirely rather than rendering a placeholder.
    """
    key = str(value or "").lower().strip()
    if not key:
        return None
    return _WAVE_LABELS.get(key)


def truncate(text: Any, n: int) -> str:
    """Truncate ``text`` to ``n`` characters, appending ``…`` if cut."""
    if text is None:
        return ""
    s = str(text)
    if len(s) <= n:
        return s
    return s[: n - 1].rstrip() + "…"


def first_paragraph(md: str, max_chars: int = 240) -> str:
    """Return the first paragraph of ``md``, plain text, truncated."""
    if not md:
        return ""
    chunk = md.split("\n\n", 1)[0].strip()
    chunk = re.sub(r"`([^`]+)`", r"\1", chunk)
    chunk = re.sub(r"\*\*([^*]+)\*\*", r"\1", chunk)
    chunk = re.sub(r"\*([^*]+)\*", r"\1", chunk)
    chunk = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", chunk)
    chunk = " ".join(chunk.split())
    return truncate(chunk, max_chars)


def split_steps(md: str) -> list[tuple[str, str]]:
    """Try to split a UC's Markdown ``md`` into HowTo (name, text) steps.

    Recognises ``Step 1 — Foo`` / ``Step 1. Foo`` / ``Step 1 Foo`` headers
    and groups the following lines as that step's body. Falls back to
    the empty list when the document doesn't look stepped.
    """
    if not md:
        return []
    steps: list[tuple[str, str]] = []
    current_name: Optional[str] = None
    current_buf: list[str] = []
    step_re = re.compile(
        r"^\s*Step\s+(\d+)\s*[\.\):\-—–]?\s*(.*)$",
        re.IGNORECASE,
    )
    for line in md.splitlines():
        m = step_re.match(line)
        if m:
            if current_name is not None:
                steps.append((current_name, " ".join(current_buf).strip()))
            current_name = (m.group(2).strip() or f"Step {m.group(1)}")
            current_buf = []
        elif current_name is not None:
            current_buf.append(line.strip())
    if current_name is not None:
        steps.append((current_name, " ".join(current_buf).strip()))
    steps = [(n, t) for (n, t) in steps if t]
    if not steps:
        return []
    cleaned: list[tuple[str, str]] = []
    for name, text in steps:
        text = re.sub(r"`{3}[\s\S]*?`{3}", " [SPL] ", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)
        cleaned.append((truncate(name, 80), truncate(text, 600)))
    return cleaned


# ---------------------------------------------------------------------------
# Asset path helpers (root-absolute so SSG pages render from any depth)
# ---------------------------------------------------------------------------


def asset_url(filename: str, site_url: str = "") -> str:
    """Return a root-absolute URL for a fingerprinted asset.

    SSG pages live at ``/uc/UC-X.Y.Z/`` and ``/category/<slug>/``, both
    two levels deep. Relative refs would resolve incorrectly, so every
    page links assets via root-absolute paths.

    When ``site_url`` includes a subpath (e.g. GitHub Pages at
    ``https://user.github.io/repo``), the asset path is prefixed with the
    subpath so ``/repo/assets/foo.css`` resolves correctly.
    """
    if not filename:
        return ""
    if filename.startswith("/"):
        return filename
    if site_url:
        from urllib.parse import urlparse
        base_path = urlparse(site_url).path.rstrip("/")
        if base_path:
            return f"{base_path}/assets/{filename}"
    return f"/assets/{filename}"
