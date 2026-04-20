"""tools.build.templates.regulation — per-regulation rollup page template.

Each regulation framework gets a permanent URL at
``/regulation/<slug>/`` (HTML) plus a JSON twin at
``/regulation/<slug>/index.json``. The page lists every use case whose
``regs`` array references the framework (matched by ``id``,
``shortName``, ``name``, or any declared ``alias``) and groups them by
the originating category for readability.

Schema markup
-------------
* ``CollectionPage``  — the regulation as a curated list of UCs
* ``BreadcrumbList``  — Home › Browse › Regulations › <Framework>

Discovery
---------
* ``<link rel="canonical">``
* ``<link rel="alternate" type="application/json">``
* OpenGraph + Twitter cards
* Per-UC ``itemprop`` so consumers can scrape without JS

Data contract
-------------
Caller passes a ``mapping`` dict (built once by ``render_pages``) with
the precomputed UC list per framework and the canonical regulation slug
map. The template never mutates the catalog or the regulation record.

Threat model
------------
Pure HTML emission with every dynamic field routed through
``_helpers.escape``/``_helpers.attr``. JSON-LD payloads are serialised
through ``_helpers.jsonld_script`` which neutralises ``</`` sequences.
No inline ``<script>`` other than JSON-LD; no cross-origin asset loads.
"""

from __future__ import annotations

from typing import Any, Iterable

from . import _css, _helpers


def render_html(
    framework: dict[str, Any],
    *,
    slug: str,
    ucs: list[dict[str, Any]],
    cat_slug_for: dict[int, str],
    cat_name_for: dict[int, str],
    ctx: _helpers.RenderContext,
) -> str:
    """Render the static HTML page for a single regulation framework."""
    name = str(framework.get("name") or framework.get("shortName") or framework.get("id") or "")
    short = str(framework.get("shortName") or name)
    description = _framework_description(framework, len(ucs))
    page_url = f"{ctx.site_url}/regulation/{slug}/"
    json_url = f"{ctx.site_url}/regulation/{slug}/index.json"

    member_urls = [
        f"{ctx.site_url}/uc/UC-{str(uc.get('i', ''))}/"
        for uc in ucs
        if uc.get("i")
    ]

    breadcrumbs = [
        ("Home", f"{ctx.site_url}/"),
        ("Regulations", f"{ctx.site_url}/regulation/"),
        (short, page_url),
    ]

    jsonld = _helpers.jsonld_script(
        _helpers.jsonld_collection_page(
            name=f"{short} — Splunk Use Cases",
            description=description,
            url=page_url,
            site_name=ctx.site_name,
            site_url=ctx.site_url,
            member_urls=member_urls[:200],
            date_modified=ctx.generated_at[:10],
        ),
        _helpers.jsonld_breadcrumb(breadcrumbs),
    )

    grouped_html = _render_grouped_ucs(
        ucs,
        cat_slug_for=cat_slug_for,
        cat_name_for=cat_name_for,
        ctx=ctx,
    )

    facts_html = _render_facts(framework)

    css = _css.page_css()

    asset_styles = _helpers.asset_url(ctx.asset_styles, ctx.site_url) if ctx.asset_styles else ""
    extra_link = (
        f'<link rel="prefetch" href="{_helpers.attr(asset_styles)}" as="style">'
        if asset_styles else ""
    )

    return _PAGE_TEMPLATE.format(
        title=_helpers.escape(f"{short} mappings · {ctx.site_short}"),
        description=_helpers.attr(description),
        canonical=_helpers.attr(page_url),
        json_alt=_helpers.attr(json_url),
        og_title=_helpers.attr(f"{short} — Splunk Use Cases"),
        og_url=_helpers.attr(page_url),
        og_image=_helpers.attr(f"{ctx.site_url}/og-image-1200.png"),
        site_name=_helpers.attr(ctx.site_name),
        css=css,
        extra_link=extra_link,
        site_short=_helpers.escape(ctx.site_short),
        site_root=_helpers.attr(ctx.site_url),
        breadcrumb_html=_render_breadcrumb(breadcrumbs),
        framework_name=_helpers.escape(name),
        framework_short=_helpers.escape(short),
        uc_count=str(len(ucs)),
        category_count=str(len({uc.get("cat") for uc in ucs if uc.get("cat") is not None})),
        description_html=_helpers.escape(description),
        facts=facts_html,
        grouped_html=grouped_html,
        jsonld=jsonld,
        json_url=_helpers.attr(json_url),
        repo_url=_helpers.attr(ctx.repo_url),
    )


# ---------------------------------------------------------------------------
# JSON twin
# ---------------------------------------------------------------------------


def render_index_json(
    framework: dict[str, Any],
    *,
    slug: str,
    ucs: list[dict[str, Any]],
    cat_slug_for: dict[int, str],
    cat_name_for: dict[int, str],
    ctx: _helpers.RenderContext,
) -> dict[str, Any]:
    """Build the JSON twin for ``/regulation/<slug>/index.json``."""
    page_url = f"{ctx.site_url}/regulation/{slug}/"
    short = framework.get("shortName") or framework.get("name") or framework.get("id")

    grouped: dict[int, list[dict[str, Any]]] = {}
    for uc in ucs:
        cat_id = uc.get("cat")
        if cat_id is None:
            continue
        grouped.setdefault(int(cat_id), []).append(uc)

    cat_payload: list[dict[str, Any]] = []
    for cat_id in sorted(grouped):
        items: list[dict[str, Any]] = []
        for uc in sorted(
            grouped[cat_id],
            key=lambda u: _helpers.sort_key(u.get("i", "")),
        ):
            uc_id = str(uc.get("i", ""))
            if not uc_id:
                continue
            items.append({
                "id": f"UC-{uc_id}",
                "shortId": uc_id,
                "title": uc.get("n", ""),
                "value": _helpers.truncate(uc.get("v", ""), 200),
                "criticality": uc.get("c"),
                "difficulty": uc.get("f"),
                "url": f"{ctx.site_url}/uc/UC-{uc_id}/",
                "json": f"{ctx.site_url}/uc/UC-{uc_id}/index.json",
            })
        cat_payload.append({
            "id": cat_id,
            "name": cat_name_for.get(cat_id, ""),
            "slug": cat_slug_for.get(cat_id, ""),
            "url": f"{ctx.site_url}/category/{cat_slug_for.get(cat_id, '')}/",
            "useCaseCount": len(items),
            "useCases": items,
        })

    return {
        "$schema": "/schemas/v2/regulation.schema.json",
        "version": "2.0.0",
        "id": framework.get("id") or slug,
        "slug": slug,
        "name": framework.get("name") or short,
        "shortName": short,
        "tier": framework.get("tier"),
        "jurisdiction": framework.get("jurisdiction") or [],
        "tags": framework.get("tags") or [],
        "aliases": framework.get("aliases") or [],
        "url": page_url,
        "html": page_url,
        "json": f"{page_url}index.json",
        "useCaseCount": len(ucs),
        "categoryCount": len(cat_payload),
        "categories": cat_payload,
        "generatedAt": ctx.generated_at,
    }


# ---------------------------------------------------------------------------
# Index page (lists all regulations)
# ---------------------------------------------------------------------------


def render_index_html(
    *,
    frameworks: list[tuple[dict[str, Any], str, int]],
    ctx: _helpers.RenderContext,
) -> str:
    """Render the ``/regulation/`` landing page listing every framework.

    ``frameworks`` is a list of ``(framework_dict, slug, uc_count)`` tuples
    sorted by descending UC count then framework short name.
    """
    page_url = f"{ctx.site_url}/regulation/"
    json_url = f"{ctx.site_url}/regulation/index.json"

    breadcrumbs = [
        ("Home", f"{ctx.site_url}/"),
        ("Regulations", page_url),
    ]

    rows: list[str] = []
    for fw, slug, count in frameworks:
        short = str(fw.get("shortName") or fw.get("name") or fw.get("id"))
        name = str(fw.get("name") or short)
        jurisdiction = ", ".join(fw.get("jurisdiction") or []) or "—"
        rows.append(
            f'<li class="uc-row">'
            f'<a class="uc-link" href="{_helpers.attr(ctx.site_url)}/regulation/{_helpers.attr(slug)}/">'
            f'<span class="uc-id">{_helpers.escape(short)}</span>'
            f'<span class="uc-title">{_helpers.escape(name)}</span>'
            f'</a>'
            f'<span class="uc-value">{_helpers.escape(jurisdiction)}</span>'
            f'<span class="badge badge-med">{count} UCs</span>'
            f'</li>'
        )

    description = (
        f"{len(frameworks)} compliance and regulatory frameworks mapped to "
        f"Splunk Monitoring Use Cases. Pick a framework to see every UC tagged "
        f"to it, grouped by category."
    )

    jsonld = _helpers.jsonld_script(
        _helpers.jsonld_collection_page(
            name="Compliance & Regulation Frameworks",
            description=description,
            url=page_url,
            site_name=ctx.site_name,
            site_url=ctx.site_url,
            member_urls=[
                f"{ctx.site_url}/regulation/{slug}/"
                for _, slug, _ in frameworks
            ],
            date_modified=ctx.generated_at[:10],
        ),
        _helpers.jsonld_breadcrumb(breadcrumbs),
    )

    css = _css.page_css()

    return _INDEX_TEMPLATE.format(
        title=_helpers.escape(f"Regulations · {ctx.site_short}"),
        description=_helpers.attr(description),
        canonical=_helpers.attr(page_url),
        json_alt=_helpers.attr(json_url),
        og_title=_helpers.attr("Compliance & Regulation Frameworks — Splunk UCs"),
        og_url=_helpers.attr(page_url),
        og_image=_helpers.attr(f"{ctx.site_url}/og-image-1200.png"),
        site_name=_helpers.attr(ctx.site_name),
        css=css,
        site_short=_helpers.escape(ctx.site_short),
        site_root=_helpers.attr(ctx.site_url),
        breadcrumb_html=_render_breadcrumb(breadcrumbs),
        description_html=_helpers.escape(description),
        framework_count=str(len(frameworks)),
        uc_total=str(sum(c for _, _, c in frameworks)),
        rows="".join(rows),
        jsonld=jsonld,
        json_url=_helpers.attr(json_url),
        repo_url=_helpers.attr(ctx.repo_url),
    )


def render_index_payload(
    *,
    frameworks: list[tuple[dict[str, Any], str, int]],
    ctx: _helpers.RenderContext,
) -> dict[str, Any]:
    """JSON twin for ``/regulation/index.json``."""
    return {
        "$schema": "/schemas/v2/regulation-index.schema.json",
        "version": "2.0.0",
        "url": f"{ctx.site_url}/regulation/",
        "json": f"{ctx.site_url}/regulation/index.json",
        "frameworkCount": len(frameworks),
        "useCaseTotal": sum(c for _, _, c in frameworks),
        "frameworks": [
            {
                "id": fw.get("id") or slug,
                "slug": slug,
                "shortName": fw.get("shortName"),
                "name": fw.get("name"),
                "tier": fw.get("tier"),
                "jurisdiction": fw.get("jurisdiction") or [],
                "tags": fw.get("tags") or [],
                "aliases": fw.get("aliases") or [],
                "useCaseCount": count,
                "url": f"{ctx.site_url}/regulation/{slug}/",
                "json": f"{ctx.site_url}/regulation/{slug}/index.json",
            }
            for fw, slug, count in frameworks
        ],
        "generatedAt": ctx.generated_at,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _framework_description(framework: dict[str, Any], uc_count: int) -> str:
    name = str(framework.get("name") or framework.get("shortName") or framework.get("id") or "this framework")
    parts = [
        f"{uc_count} Splunk monitoring use cases mapped to {name}.",
    ]
    juris = framework.get("jurisdiction") or []
    if juris:
        parts.append("Jurisdiction: " + ", ".join(juris) + ".")
    tags = framework.get("tags") or []
    if tags:
        parts.append("Topics: " + ", ".join(tags) + ".")
    return _helpers.truncate(" ".join(parts), 240)


def _render_facts(framework: dict[str, Any]) -> str:
    rows: list[str] = ['<dl class="facts">']
    name = framework.get("name")
    if name:
        rows.append(f'<dt>Name</dt><dd>{_helpers.escape(name)}</dd>')
    short = framework.get("shortName")
    if short and short != name:
        rows.append(f'<dt>Short name</dt><dd>{_helpers.escape(short)}</dd>')
    juris = framework.get("jurisdiction") or []
    if juris:
        rows.append(
            "<dt>Jurisdiction</dt><dd>"
            + _helpers.escape(", ".join(juris))
            + "</dd>"
        )
    tags = framework.get("tags") or []
    if tags:
        rows.append(
            "<dt>Topics</dt><dd>"
            + _helpers.escape(", ".join(tags))
            + "</dd>"
        )
    aliases = framework.get("aliases") or []
    if aliases:
        rows.append(
            "<dt>Also known as</dt><dd>"
            + _helpers.escape(", ".join(aliases))
            + "</dd>"
        )
    versions = framework.get("versions") or []
    if versions:
        latest = versions[-1]
        url = latest.get("authoritativeUrl") or ""
        ver = latest.get("version") or ""
        if url:
            rows.append(
                "<dt>Authoritative source</dt><dd><a href="
                + f'"{_helpers.attr(url)}" rel="noopener noreferrer" target="_blank">'
                + _helpers.escape(f"{name or short} {ver}".strip())
                + "</a></dd>"
            )
        elif ver:
            rows.append(f'<dt>Latest version</dt><dd>{_helpers.escape(ver)}</dd>')
    rows.append("</dl>")
    return "\n".join(rows)


def _render_grouped_ucs(
    ucs: Iterable[dict[str, Any]],
    *,
    cat_slug_for: dict[int, str],
    cat_name_for: dict[int, str],
    ctx: _helpers.RenderContext,
) -> str:
    grouped: dict[int, list[dict[str, Any]]] = {}
    for uc in ucs:
        cat_id = uc.get("cat")
        if cat_id is None:
            continue
        grouped.setdefault(int(cat_id), []).append(uc)

    if not grouped:
        return '<p class="muted">No use cases mapped to this framework yet.</p>'

    sections: list[str] = []
    for cat_id in sorted(grouped):
        cat_name = cat_name_for.get(cat_id, f"Category {cat_id}")
        cat_slug = cat_slug_for.get(cat_id, "")
        items = sorted(
            grouped[cat_id],
            key=lambda u: _helpers.sort_key(u.get("i", "")),
        )
        rows: list[str] = []
        for uc in items:
            uc_id = str(uc.get("i", ""))
            if not uc_id:
                continue
            title = str(uc.get("n", uc_id))
            value = _helpers.truncate(uc.get("v", ""), 140)
            crit_label, crit_mod = _helpers.criticality_label(uc.get("c"))
            rows.append(
                f'<li class="uc-row">'
                f'<a class="uc-link" href="{_helpers.attr(ctx.site_url)}/uc/UC-{_helpers.escape(uc_id)}/">'
                f'<span class="uc-id">UC-{_helpers.escape(uc_id)}</span>'
                f'<span class="uc-title">{_helpers.escape(title)}</span>'
                f'</a>'
                f'<span class="uc-value">{_helpers.escape(value)}</span>'
                f'<span class="badge badge-{_helpers.escape(crit_mod)}">{_helpers.escape(crit_label)}</span>'
                f'</li>'
            )
        anchor = _helpers.slug(cat_name) or f"cat-{cat_id}"
        cat_link = (
            f' <a class="muted" href="{_helpers.attr(ctx.site_url)}/category/'
            f'{_helpers.attr(cat_slug)}/">→</a>'
            if cat_slug else ""
        )
        sections.append(
            f'<section id="{_helpers.attr(anchor)}">'
            f'<h2>{_helpers.escape(cat_name)} '
            f'<span class="muted">({len(rows)})</span>{cat_link}</h2>'
            f'<ul class="uc-list">{"".join(rows)}</ul>'
            f'</section>'
        )
    return "\n".join(sections)


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
# Page templates
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
<meta property="og:type" content="website">
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
<a href="{site_root}/regulation/">Regulations</a>
<a href="{site_root}/api/">API</a>
<a href="{repo_url}" rel="noopener noreferrer">GitHub</a>
</nav>
</header>
<main id="main">
{breadcrumb_html}
<article>
<header>
<div class="uc-id">Regulation</div>
<h1>{framework_name}</h1>
<p class="lede">{description_html}</p>
<p class="muted">{uc_count} use cases · {category_count} categories ·
<a href="{json_url}" rel="alternate">JSON twin →</a></p>
{facts}
</header>
{grouped_html}
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


_INDEX_TEMPLATE = """<!DOCTYPE html>
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
<meta property="og:type" content="website">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{og_url}">
<meta property="og:site_name" content="{site_name}">
<meta property="og:image" content="{og_image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{og_title}">
<meta name="twitter:description" content="{description}">
<style>{css}</style>
{jsonld}
</head>
<body>
<header class="site">
<nav>
<a class="brand" href="{site_root}/">{site_short}</a>
<a href="{site_root}/browse/">Browse</a>
<a href="{site_root}/regulation/">Regulations</a>
<a href="{site_root}/api/">API</a>
<a href="{repo_url}" rel="noopener noreferrer">GitHub</a>
</nav>
</header>
<main id="main">
{breadcrumb_html}
<article>
<header>
<div class="uc-id">Compliance &amp; Regulation</div>
<h1>Regulation Frameworks</h1>
<p class="lede">{description_html}</p>
<p class="muted">{framework_count} frameworks · {uc_total} mapped use cases ·
<a href="{json_url}" rel="alternate">JSON twin →</a></p>
</header>
<ul class="uc-list">{rows}</ul>
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
