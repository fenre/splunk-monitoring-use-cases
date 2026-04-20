"""tools.build.templates.uc — per-use-case detail page template.

Each UC gets a permanent URL at ``/uc/UC-X.Y.Z/`` (HTML) plus a JSON
twin at ``/uc/UC-X.Y.Z/index.json``. The HTML is fully static — every
section (value, prerequisites, SPL, narrative, references, MITRE
mappings, regulations) renders without JavaScript.

Schema markup:

* ``TechArticle``     — the UC itself, with a code sample and keywords
* ``HowTo``           — added when the markdown contains ≥2 numbered steps
* ``BreadcrumbList``  — Home › Category › Subcategory › UC

Discovery:

* ``<link rel="canonical">``
* ``<link rel="alternate" type="application/json">`` to ``index.json``
* OpenGraph + Twitter cards
* ``<meta name="description">`` from the value statement
"""

from __future__ import annotations

from typing import Any

from . import _css, _helpers


def render_html(
    uc: dict[str, Any],
    cat: dict[str, Any],
    sub: dict[str, Any],
    cat_slug: str,
    *,
    ctx: _helpers.RenderContext,
) -> str:
    """Render the static HTML page for a single use case."""
    uc_id = str(uc.get("i", ""))
    title = str(uc.get("n", uc_id))
    value = str(uc.get("v", ""))
    cat_id = cat.get("i", 0)
    cat_name = str(cat.get("n", ""))
    sub_id = str(sub.get("i", ""))
    sub_name = str(sub.get("n", ""))

    page_url = f"{ctx.site_url}/uc/UC-{uc_id}/"
    json_url = f"{ctx.site_url}/uc/UC-{uc_id}/index.json"
    cat_url = f"{ctx.site_url}/category/{cat_slug}/"

    description = _helpers.truncate(value or _helpers.first_paragraph(uc.get("md", "")), 160)
    crit_label, crit_mod = _helpers.criticality_label(uc.get("c"))
    diff_label, diff_mod = _helpers.difficulty_label(uc.get("f"))

    keywords = sorted(
        {
            str(k)
            for k in (
                list(uc.get("mtype") or [])
                + list(uc.get("a") or [])
                + list(uc.get("e") or [])
                + list(uc.get("regs") or [])
                + [cat_name, sub_name]
            )
            if k
        }
    )

    breadcrumbs = [
        ("Home", f"{ctx.site_url}/"),
        ("Browse", f"{ctx.site_url}/browse/"),
        (cat_name, cat_url),
        (sub_name, f"{cat_url}#{_helpers.slug(sub_name)}"),
        (f"UC-{uc_id}", page_url),
    ]
    breadcrumbs = [(n, u) for n, u in breadcrumbs if n]

    jsonld = _helpers.jsonld_script(
        _helpers.jsonld_techarticle(
            headline=f"UC-{uc_id} — {title}",
            description=description,
            url=page_url,
            site_name=ctx.site_name,
            site_url=ctx.site_url,
            date_modified=str(uc.get("reviewed") or ctx.generated_at[:10]),
            keywords=keywords,
            code_sample=str(uc.get("q") or "") or None,
            code_sample_language="spl",
        ),
        _helpers.jsonld_howto(
            name=title,
            description=description,
            steps=_helpers.split_steps(uc.get("md", "")),
        ) or {},
        _helpers.jsonld_breadcrumb(breadcrumbs),
    )

    body = "\n".join(
        part for part in (
            _section_value(uc, value),
            _section_quick_facts(uc, cat_name, sub_name),
            _section_prerequisites(uc),
            _section_spl(uc),
            _section_dma_spl(uc),
            _section_implementation(uc),
            _section_visualization(uc),
            _section_known_fp(uc),
            _section_regulations_mitre(uc),
            _section_apps(uc),
            _section_references(uc),
            _section_full_narrative(uc),
            _section_provenance(uc),
        )
        if part
    )

    css = _css.page_css()
    asset_styles = _helpers.asset_url(ctx.asset_styles) if ctx.asset_styles else ""
    extra_link = (
        f'<link rel="prefetch" href="{_helpers.attr(asset_styles)}" as="style">'
        if asset_styles else ""
    )

    return _PAGE_TEMPLATE.format(
        title=_helpers.escape(f"UC-{uc_id} · {title} · {ctx.site_short}"),
        description=_helpers.attr(description),
        canonical=_helpers.attr(page_url),
        json_alt=_helpers.attr(json_url),
        og_title=_helpers.attr(f"UC-{uc_id} — {title}"),
        og_url=_helpers.attr(page_url),
        og_image=_helpers.attr(f"{ctx.site_url}/og-image-1200.png"),
        site_name=_helpers.attr(ctx.site_name),
        css=css,
        extra_link=extra_link,
        site_short=_helpers.escape(ctx.site_short),
        site_root=_helpers.attr(ctx.site_url),
        breadcrumb_html=_render_breadcrumb(breadcrumbs),
        uc_id=_helpers.escape(uc_id),
        uc_title=_helpers.escape(title),
        crit_label=_helpers.escape(crit_label),
        crit_mod=_helpers.escape(crit_mod),
        diff_label=_helpers.escape(diff_label),
        diff_mod=_helpers.escape(diff_mod),
        cat_url=_helpers.attr(cat_url),
        cat_name=_helpers.escape(cat_name),
        sub_name=_helpers.escape(sub_name),
        cat_id=_helpers.escape(str(cat_id)),
        body=body,
        jsonld=jsonld,
        json_url=_helpers.attr(json_url),
        repo_url=_helpers.attr(ctx.repo_url),
        site_url_safe=_helpers.attr(ctx.site_url),
    )


# ---------------------------------------------------------------------------
# JSON twin
# ---------------------------------------------------------------------------


def render_index_json(
    uc: dict[str, Any],
    cat: dict[str, Any],
    sub: dict[str, Any],
    cat_slug: str,
    *,
    ctx: _helpers.RenderContext,
) -> dict[str, Any]:
    """Build the JSON twin for ``/uc/UC-X.Y.Z/index.json``.

    Returns the full UC payload (every field on the Catalog UC dict)
    plus parent context (cat, sub) and discovery URLs. Stable shape per
    docs/url-scheme.md.
    """
    uc_id = str(uc.get("i", ""))
    page_url = f"{ctx.site_url}/uc/UC-{uc_id}/"
    return {
        "$schema": "/schemas/v2/uc.schema.json",
        "version": "2.0.0",
        "id": f"UC-{uc_id}",
        "shortId": uc_id,
        "title": uc.get("n", ""),
        "url": page_url,
        "html": page_url,
        "json": f"{page_url}index.json",
        "category": {
            "id": cat.get("i"),
            "slug": cat_slug,
            "name": cat.get("n", ""),
            "url": f"{ctx.site_url}/category/{cat_slug}/",
        },
        "subcategory": {
            "id": sub.get("i"),
            "name": sub.get("n", ""),
        },
        "fields": {
            k: v for k, v in uc.items()
            if v not in (None, "", [], {})
        },
        "generatedAt": ctx.generated_at,
    }


# ---------------------------------------------------------------------------
# Section renderers (each returns "" when the source field is empty)
# ---------------------------------------------------------------------------


def _section_value(uc: dict[str, Any], value: str) -> str:
    if not value:
        return ""
    return f'<p class="lede">{_helpers.escape(value)}</p>'


def _section_quick_facts(uc: dict[str, Any], cat_name: str, sub_name: str) -> str:
    rows: list[tuple[str, str]] = []

    def _add(label: str, raw: Any, *, render_md: bool = False) -> None:
        if raw is None or raw == "" or raw == [] or raw == {}:
            return
        if isinstance(raw, list):
            html_value = ", ".join(_helpers.escape(str(v)) for v in raw if v)
        elif render_md:
            html_value = _helpers.render_markdown(str(raw))
        else:
            html_value = _helpers.escape(str(raw))
        rows.append((label, html_value))

    _add("Subcategory", sub_name)
    _add("Category", cat_name)
    _add("App / TA", uc.get("t"), render_md=True)
    _add("Data sources", uc.get("d"), render_md=True)
    _add("Required fields", uc.get("reqf"))
    _add("Data type", uc.get("dtype"))
    _add("Security domain", uc.get("sdomain"))
    _add("CIM models", uc.get("a"))
    _add("Monitoring type", uc.get("mtype"))
    _add("Equipment", uc.get("e"))
    _add("Equipment models", uc.get("em"))
    _add("Pillar", uc.get("pillar"))
    _add("Splunk versions", uc.get("sver"))
    _add("Status", uc.get("status"))
    _add("Last reviewed", uc.get("reviewed"))
    if not rows:
        return ""
    items = "\n".join(
        f"<dt>{_helpers.escape(label)}</dt><dd>{value}</dd>"
        for label, value in rows
    )
    return f'<section><h2>Quick facts</h2><dl class="facts">{items}</dl></section>'


def _section_prerequisites(uc: dict[str, Any]) -> str:
    parts: list[str] = []
    if uc.get("t"):
        parts.append(
            "<li><strong>App / TA:</strong> "
            + _helpers.render_markdown(str(uc["t"]))
            + "</li>"
        )
    if uc.get("d"):
        parts.append(
            "<li><strong>Data sources:</strong> "
            + _helpers.render_markdown(str(uc["d"]))
            + "</li>"
        )
    if uc.get("reqf"):
        parts.append(
            "<li><strong>Required fields:</strong> "
            + _helpers.escape(uc["reqf"])
            + "</li>"
        )
    if not parts:
        return ""
    return (
        "<section><h2>Prerequisites</h2><ul>"
        + "".join(parts)
        + "</ul></section>"
    )


def _section_spl(uc: dict[str, Any]) -> str:
    spl = str(uc.get("q") or "").strip()
    if not spl:
        return ""
    return (
        '<section><h2>SPL</h2>'
        '<pre><code class="lang-spl">'
        + _helpers.escape(spl)
        + '</code></pre></section>'
    )


def _section_dma_spl(uc: dict[str, Any]) -> str:
    qs = str(uc.get("qs") or "").strip()
    dma = str(uc.get("dma") or "").strip()
    if not qs and not dma:
        return ""
    parts: list[str] = ["<section><h2>Data model acceleration</h2>"]
    if dma:
        parts.append(_helpers.render_markdown(dma))
    if qs:
        parts.append(
            '<pre><code class="lang-spl">'
            + _helpers.escape(qs)
            + "</code></pre>"
        )
    parts.append("</section>")
    return "\n".join(parts)


def _section_implementation(uc: dict[str, Any]) -> str:
    text = str(uc.get("m") or "").strip()
    if not text:
        return ""
    return (
        "<section><h2>Implementation</h2>"
        + _helpers.render_markdown(text)
        + "</section>"
    )


def _section_visualization(uc: dict[str, Any]) -> str:
    text = str(uc.get("z") or "").strip()
    if not text:
        return ""
    return (
        "<section><h2>Visualization</h2>"
        + _helpers.render_markdown(text)
        + "</section>"
    )


def _section_known_fp(uc: dict[str, Any]) -> str:
    text = str(uc.get("kfp") or "").strip()
    if not text:
        return ""
    return (
        "<section><h2>Known false positives</h2>"
        + _helpers.render_markdown(text)
        + "</section>"
    )


def _section_regulations_mitre(uc: dict[str, Any]) -> str:
    regs = uc.get("regs") or []
    mitre = uc.get("mitre") or []
    if not regs and not mitre:
        return ""
    parts: list[str] = ["<section><h2>Compliance &amp; threat coverage</h2>"]
    if regs:
        parts.append("<h3>Regulations</h3><div class=\"badges\">")
        for r in regs:
            parts.append(
                '<span class="badge">' + _helpers.escape(str(r)) + "</span>"
            )
        parts.append("</div>")
    if mitre:
        parts.append("<h3>MITRE ATT&amp;CK</h3><ul>")
        for m in mitre:
            if isinstance(m, dict):
                tid = m.get("id") or m.get("technique_id") or ""
                tname = m.get("name") or m.get("technique") or ""
                if tid and tname:
                    label = f"{tid} — {tname}"
                elif tid or tname:
                    label = str(tid or tname)
                else:
                    continue
            else:
                label = str(m)
            parts.append("<li>" + _helpers.escape(label) + "</li>")
        parts.append("</ul>")
    parts.append("</section>")
    return "\n".join(parts)


def _section_apps(uc: dict[str, Any]) -> str:
    sapp = uc.get("sapp") or []
    ta = uc.get("ta_link")
    if not sapp and not ta:
        return ""
    parts: list[str] = ["<section><h2>Splunkbase apps</h2><ul>"]
    if isinstance(ta, dict) and ta.get("name"):
        url = ta.get("url") or ""
        if url:
            parts.append(
                '<li><a href="'
                + _helpers.attr(url)
                + '" rel="noopener noreferrer" target="_blank">'
                + _helpers.escape(ta["name"])
                + "</a> <em>(primary TA)</em></li>"
            )
        else:
            parts.append(
                "<li>"
                + _helpers.escape(ta["name"])
                + " <em>(primary TA)</em></li>"
            )
    for app in sapp:
        if not isinstance(app, dict):
            continue
        name = app.get("name") or ""
        url = app.get("url") or ""
        desc = app.get("desc") or ""
        if not name:
            continue
        if url:
            link = (
                '<a href="'
                + _helpers.attr(url)
                + '" rel="noopener noreferrer" target="_blank">'
                + _helpers.escape(name)
                + "</a>"
            )
        else:
            link = _helpers.escape(name)
        suffix = " — " + _helpers.escape(desc) if desc else ""
        parts.append("<li>" + link + suffix + "</li>")
    parts.append("</ul></section>")
    return "\n".join(parts)


def _section_references(uc: dict[str, Any]) -> str:
    refs = str(uc.get("refs") or "").strip()
    if not refs:
        return ""
    return (
        "<section><h2>References</h2>"
        + _helpers.render_markdown(refs)
        + "</section>"
    )


def _section_full_narrative(uc: dict[str, Any]) -> str:
    md = str(uc.get("md") or "").strip()
    if not md:
        return ""
    if str(uc.get("m") or "").strip() and md.startswith("Prerequisites"):
        # The md is the rendered version of Prerequisites + Step blocks +
        # Understanding-this-SPL prose. The shorter `m` field above
        # already covers the narrative; collapse the long version into
        # a <details> so the page is scannable but the deep dive is
        # preserved for power users.
        return (
            "<section><h2>Detailed walkthrough</h2>"
            "<details><summary>Show full narrative</summary>"
            + _helpers.render_markdown(md)
            + "</details></section>"
        )
    return (
        "<section><h2>Detailed walkthrough</h2>"
        + _helpers.render_markdown(md)
        + "</section>"
    )


def _section_provenance(uc: dict[str, Any]) -> str:
    rby = str(uc.get("rby") or "").strip()
    sver = str(uc.get("sver") or "").strip()
    reviewed = str(uc.get("reviewed") or "").strip()
    if not (rby or sver or reviewed):
        return ""
    parts: list[str] = []
    if reviewed:
        parts.append(f"Last reviewed: {_helpers.escape(reviewed)}")
    if rby:
        parts.append(f"Reviewer: {_helpers.escape(rby)}")
    if sver:
        parts.append(f"Splunk versions: {_helpers.escape(sver)}")
    return (
        '<section><h2>Provenance</h2><p class="prov">'
        + " · ".join(parts)
        + "</p></section>"
    )


# ---------------------------------------------------------------------------
# Breadcrumb HTML
# ---------------------------------------------------------------------------


def _render_breadcrumb(items: list[tuple[str, str]]) -> str:
    parts: list[str] = ['<nav aria-label="Breadcrumb" class="breadcrumb"><ol>']
    last = len(items) - 1
    for i, (name, url) in enumerate(items):
        if i == last:
            parts.append(
                '<li aria-current="page">'
                + _helpers.escape(name)
                + "</li>"
            )
        else:
            parts.append(
                '<li><a href="'
                + _helpers.attr(url)
                + '">'
                + _helpers.escape(name)
                + "</a></li>"
            )
    parts.append("</ol></nav>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# Page template
# ---------------------------------------------------------------------------


_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="theme-color" content="#a3360e" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#1a1817" media="(prefers-color-scheme: dark)">
<link rel="canonical" href="{canonical}">
<link rel="alternate" type="application/json" href="{json_alt}" title="JSON twin">
<link rel="alternate" type="application/json" href="{json_alt}">
<meta property="og:type" content="article">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{og_url}">
<meta property="og:site_name" content="{site_name}">
<meta property="og:image" content="{og_image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{og_title}">
<meta name="twitter:description" content="{description}">
<style>{css}</style>
{extra_link}
{jsonld}
</head>
<body>
<header class="site">
<nav>
<a class="brand" href="{site_root}/">{site_short}</a>
<a href="{site_root}/browse/">Browse</a>
<a href="{site_root}/category/{cat_id}/">Category</a>
<a href="{site_url_safe}/api/">API</a>
<a href="{repo_url}" rel="noopener noreferrer">GitHub</a>
</nav>
</header>
<main id="main">
{breadcrumb_html}
<article>
<header>
<div class="uc-id">UC-{uc_id}</div>
<h1>{uc_title}</h1>
<div class="badges">
<span class="badge badge-{crit_mod}">Criticality: {crit_label}</span>
<span class="badge">Difficulty: {diff_label}</span>
<a class="badge" href="{cat_url}">{cat_name}</a>
</div>
</header>
{body}
<footer>
<p><a href="{json_url}" rel="alternate">JSON twin →</a></p>
</footer>
</article>
</main>
<footer class="site">
<nav>
<span>&copy; Splunk Monitoring Use Cases · CC-BY-4.0</span>
<a href="{site_root}/api/">API</a>
<a href="{site_root}/sitemap.xml">Sitemap</a>
<a href="{repo_url}" rel="noopener noreferrer">Source</a>
</nav>
</footer>
</body>
</html>
"""
