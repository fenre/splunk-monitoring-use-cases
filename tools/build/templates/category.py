"""tools.build.templates.category — per-category landing template.

Each category gets a permanent URL at ``/category/<slug>/`` (HTML) plus
a JSON twin at ``/category/<slug>/index.json``. The page groups every
UC in the category by subcategory, with a compact entry per UC linking
to ``/uc/UC-X.Y.Z/`` for the full detail.

Schema markup:

* ``CollectionPage``  — the category as a collection of UCs
* ``BreadcrumbList``  — Home › Browse › Category

Discovery:

* ``<link rel="canonical">``
* ``<link rel="alternate" type="application/json">``
* OpenGraph + Twitter cards
* Per-UC ``itemprop`` so consumers can scrape the listing without JS
"""

from __future__ import annotations

from typing import Any

from . import _css, _helpers


def render_html(
    cat: dict[str, Any],
    *,
    cat_slug: str,
    cat_meta: dict[str, Any],
    ctx: _helpers.RenderContext,
) -> str:
    """Render the static HTML page for a single category."""
    cat_id = cat.get("i", 0)
    cat_name = str(cat.get("n", ""))
    subs = sorted(
        cat.get("s", []),
        key=lambda s: _helpers.sort_key(s.get("i", 0)),
    )

    description = _helpers.truncate(
        str(cat_meta.get("desc") or _category_default_desc(cat_name, cat)),
        180,
    )
    page_url = f"{ctx.site_url}/category/{cat_slug}/"
    json_url = f"{ctx.site_url}/category/{cat_slug}/index.json"

    member_urls: list[str] = []
    for sub in subs:
        for uc in sorted(
            sub.get("u", []),
            key=lambda u: _helpers.sort_key(u.get("i", "")),
        ):
            uc_id = str(uc.get("i", ""))
            if uc_id:
                member_urls.append(f"{ctx.site_url}/uc/UC-{uc_id}/")

    breadcrumbs = [
        ("Home", f"{ctx.site_url}/"),
        ("Browse", f"{ctx.site_url}/browse/"),
        (cat_name, page_url),
    ]

    jsonld = _helpers.jsonld_script(
        _helpers.jsonld_collection_page(
            name=f"{cat_name} — Splunk Use Cases",
            description=description,
            url=page_url,
            site_name=ctx.site_name,
            site_url=ctx.site_url,
            member_urls=member_urls[:200],
            date_modified=ctx.generated_at[:10],
        ),
        _helpers.jsonld_breadcrumb(breadcrumbs),
    )

    sub_html = "\n".join(_render_subcategory(sub, ctx) for sub in subs if sub.get("u"))
    quick_facts = _render_quick_facts(cat_meta)

    css = _css.page_css()

    asset_styles = _helpers.asset_url(ctx.asset_styles, ctx.site_url) if ctx.asset_styles else ""
    extra_link = (
        f'<link rel="prefetch" href="{_helpers.attr(asset_styles)}" as="style">'
        if asset_styles else ""
    )

    return _PAGE_TEMPLATE.format(
        title=_helpers.escape(f"{cat_name} · {ctx.site_short}"),
        description=_helpers.attr(description),
        canonical=_helpers.attr(page_url),
        json_alt=_helpers.attr(json_url),
        og_title=_helpers.attr(f"{cat_name} — Splunk Use Cases"),
        og_url=_helpers.attr(page_url),
        og_image=_helpers.attr(f"{ctx.site_url}/og-image-1200.png"),
        site_name=_helpers.attr(ctx.site_name),
        css=css,
        extra_link=extra_link,
        site_short=_helpers.escape(ctx.site_short),
        site_root=_helpers.attr(ctx.site_url),
        breadcrumb_html=_render_breadcrumb(breadcrumbs),
        cat_name=_helpers.escape(cat_name),
        cat_id=_helpers.escape(str(cat_id)),
        cat_uc_count=str(sum(len(s.get("u", [])) for s in subs)),
        cat_sub_count=str(len([s for s in subs if s.get("u")])),
        description_html=_helpers.escape(description),
        quick_facts=quick_facts,
        sub_html=sub_html,
        jsonld=jsonld,
        json_url=_helpers.attr(json_url),
        repo_url=_helpers.attr(ctx.repo_url),
        site_url_safe=_helpers.attr(ctx.site_url),
    )


# ---------------------------------------------------------------------------
# JSON twin
# ---------------------------------------------------------------------------


def render_index_json(
    cat: dict[str, Any],
    *,
    cat_slug: str,
    cat_meta: dict[str, Any],
    ctx: _helpers.RenderContext,
) -> dict[str, Any]:
    """Build the JSON twin for ``/category/<slug>/index.json``."""
    cat_id = cat.get("i", 0)
    cat_name = str(cat.get("n", ""))
    page_url = f"{ctx.site_url}/category/{cat_slug}/"

    subs_payload: list[dict[str, Any]] = []
    for sub in sorted(
        cat.get("s", []),
        key=lambda s: _helpers.sort_key(s.get("i", 0)),
    ):
        uc_list: list[dict[str, Any]] = []
        for uc in sorted(
            sub.get("u", []),
            key=lambda u: _helpers.sort_key(u.get("i", "")),
        ):
            uc_id = str(uc.get("i", ""))
            if not uc_id:
                continue
            uc_list.append({
                "id": f"UC-{uc_id}",
                "shortId": uc_id,
                "title": uc.get("n", ""),
                "value": _helpers.truncate(uc.get("v", ""), 200),
                "criticality": uc.get("c"),
                "difficulty": uc.get("f"),
                "url": f"{ctx.site_url}/uc/UC-{uc_id}/",
                "json": f"{ctx.site_url}/uc/UC-{uc_id}/index.json",
                "monitoringTypes": uc.get("mtype") or [],
                "regulations": uc.get("regs") or [],
                "dataModels": uc.get("a") or [],
            })
        if uc_list:
            subs_payload.append({
                "id": sub.get("i"),
                "name": sub.get("n", ""),
                "useCases": uc_list,
            })

    return {
        "$schema": "/schemas/v2/category.schema.json",
        "version": "2.0.0",
        "id": cat_id,
        "slug": cat_slug,
        "name": cat_name,
        "url": page_url,
        "html": page_url,
        "json": f"{page_url}index.json",
        "description": cat_meta.get("desc") or "",
        "quickFacts": cat_meta.get("quick") or {},
        "icon": cat_meta.get("icon") or "",
        "subcategories": subs_payload,
        "useCaseCount": sum(len(s["useCases"]) for s in subs_payload),
        "generatedAt": ctx.generated_at,
    }


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------


def _category_default_desc(name: str, cat: dict[str, Any]) -> str:
    n = sum(len(s.get("u", [])) for s in cat.get("s", []))
    return (
        f"{name} use cases for Splunk Enterprise: {n} curated detection, "
        f"monitoring, and compliance scenarios with reusable SPL."
    )


def _render_quick_facts(cat_meta: dict[str, Any]) -> str:
    quick = cat_meta.get("quick") or {}
    if not quick or not isinstance(quick, dict):
        return ""
    parts: list[str] = ['<dl class="facts">']
    for label, value in quick.items():
        if not value:
            continue
        if isinstance(value, list):
            v_html = ", ".join(_helpers.escape(str(x)) for x in value if x)
        else:
            v_html = _helpers.escape(str(value))
        parts.append(
            f"<dt>{_helpers.escape(str(label))}</dt><dd>{v_html}</dd>"
        )
    parts.append("</dl>")
    return "\n".join(parts)


def _render_subcategory(
    sub: dict[str, Any],
    ctx: _helpers.RenderContext,
) -> str:
    sub_id = str(sub.get("i", ""))
    sub_name = str(sub.get("n", ""))
    ucs = sorted(
        sub.get("u", []),
        key=lambda u: _helpers.sort_key(u.get("i", "")),
    )
    if not ucs:
        return ""
    anchor = _helpers.slug(sub_name) or f"sub-{sub_id}"
    rows: list[str] = []
    for uc in ucs:
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
    return (
        f'<section id="{_helpers.attr(anchor)}">'
        f'<h2>{_helpers.escape(sub_name)} '
        f'<span class="muted">({len(ucs)})</span></h2>'
        f'<ul class="uc-list">{"".join(rows)}</ul>'
        f'</section>'
    )


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
<a href="{site_root}/api/">API</a>
<a href="{repo_url}" rel="noopener noreferrer">GitHub</a>
</nav>
</header>
<main id="main">
{breadcrumb_html}
<article>
<header>
<div class="uc-id">Category {cat_id}</div>
<h1>{cat_name}</h1>
<p class="lede">{description_html}</p>
<p class="muted">{cat_uc_count} use cases · {cat_sub_count} subcategories ·
<a href="{json_url}" rel="alternate">JSON twin →</a></p>
{quick_facts}
</header>
{sub_html}
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
