"""tools.build.templates.landing — root landing page.

Slim home page that:

* Establishes the project identity (name, tagline, total UC count)
* Lists every category grouped by high-level domain (infra, security,
  cloud, app, industry, compliance, business)
* Links into ``/browse/`` for the interactive SPA
* Links to the per-category permanent URLs at ``/category/<slug>/``
* Embeds a ``WebSite`` JSON-LD payload + ``BreadcrumbList``

Target weight: <30 KB raw / <8 KB gz. Renders without JavaScript.
"""

from __future__ import annotations

from typing import Any

from . import _css, _helpers


_DOMAIN_ORDER = [
    ("infra",      "Infrastructure",   "Servers, networks, storage, virtualization, IoT/OT and the silicon they run on."),
    ("security",   "Security",         "Detection, response, and compliance — across endpoint, network, and identity."),
    ("cloud",      "Cloud",            "AWS, Azure, GCP, and the SaaS platforms that increasingly host the business."),
    ("app",        "Applications",     "Application performance, queues, microservices, ITSM and the developer pipeline."),
    ("industry",   "Industry",         "Industry-specific operational telemetry — manufacturing, energy, transport."),
    ("compliance", "Compliance",       "Regulatory mappings: PCI DSS, HIPAA, NIST, SOX, ISO 27001 and more."),
    ("business",   "Business",         "Business operations, customer experience, and revenue-impacting signals."),
]


def render_html(
    catalog,
    *,
    cat_slug_for: dict[int, str],
    regulation_summaries: list[dict[str, Any]] | None = None,
    ctx: _helpers.RenderContext,
) -> str:
    """Render the slim landing page.

    ``regulation_summaries`` (optional) is the descending-popularity list
    emitted by ``render_pages._emit_regulations``; the landing page shows
    the top 12 to surface the regulation rollups one click from the root.
    """
    total_uc = catalog.uc_count
    total_cat = len(catalog.categories)
    cat_by_id = {c.get("i"): c for c in catalog.categories}
    groups = catalog.cat_groups or {}

    hero_html = _render_hero(
        ctx,
        total_uc=total_uc,
        total_cat=total_cat,
        total_regs=len(regulation_summaries or []),
    )
    domain_html = _render_domains(cat_by_id, groups, cat_slug_for, catalog.cat_meta, ctx)
    regulation_html = _render_regulations(regulation_summaries or [], ctx)
    quick_links = _render_quick_links(ctx)

    breadcrumbs = [("Home", f"{ctx.site_url}/")]
    description = (
        f"{total_uc} curated Splunk monitoring use cases across {total_cat} domains, "
        "with ready-to-use SPL, CIM mappings, and compliance coverage."
    )

    jsonld = _helpers.jsonld_script(
        _helpers.jsonld_website(
            name=ctx.site_name,
            description=description,
            url=f"{ctx.site_url}/",
        ),
        _helpers.jsonld_breadcrumb(breadcrumbs),
    )

    css = _css.page_css()
    asset_styles = _helpers.asset_url(ctx.asset_styles) if ctx.asset_styles else ""
    extra_link = (
        f'<link rel="prefetch" href="{_helpers.attr(asset_styles)}" as="style">'
        if asset_styles else ""
    )

    return _PAGE_TEMPLATE.format(
        title=_helpers.escape(f"{ctx.site_name}"),
        description=_helpers.attr(description),
        canonical=_helpers.attr(f"{ctx.site_url}/"),
        og_title=_helpers.attr(ctx.site_name),
        og_url=_helpers.attr(f"{ctx.site_url}/"),
        og_image=_helpers.attr(f"{ctx.site_url}/og-image-1200.png"),
        site_name=_helpers.attr(ctx.site_name),
        css=css,
        extra_link=extra_link,
        site_short=_helpers.escape(ctx.site_short),
        site_root=_helpers.attr(ctx.site_url),
        hero_html=hero_html,
        domain_html=domain_html,
        regulation_html=regulation_html,
        quick_links=quick_links,
        jsonld=jsonld,
        repo_url=_helpers.attr(ctx.repo_url),
    )


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------


def _render_hero(
    ctx: _helpers.RenderContext,
    *,
    total_uc: int,
    total_cat: int,
    total_regs: int = 0,
) -> str:
    regs_clause = (
        f" mapped to <strong>{total_regs}</strong> regulatory frameworks"
        if total_regs else ""
    )
    return f"""<section class="hero">
<p class="kicker">{_helpers.escape(ctx.site_short)}</p>
<h1>{_helpers.escape(ctx.site_tagline or "Splunk monitoring use cases")}</h1>
<p class="lede">A vendor-neutral catalog of <strong>{total_uc:,}</strong> Splunk
detection, monitoring, and compliance use cases, grouped across
<strong>{total_cat}</strong> domains{regs_clause}. Every use case ships with reusable SPL,
CIM mappings, equipment tagging, and a permanent URL.</p>
<p class="hero-cta">
<a class="cta primary" href="{_helpers.attr(ctx.site_url)}/browse/">Browse the catalog →</a>
<a class="cta" href="{_helpers.attr(ctx.site_url)}/regulation/">Regulations</a>
<a class="cta" href="{_helpers.attr(ctx.site_url)}/api/">REST API</a>
<a class="cta" href="{_helpers.attr(ctx.repo_url)}" rel="noopener noreferrer">GitHub</a>
</p>
</section>"""


def _render_domains(
    cat_by_id: dict[int, dict[str, Any]],
    groups: dict[str, list[int]],
    cat_slug_for: dict[int, str],
    cat_meta: dict[str, dict[str, Any]],
    ctx: _helpers.RenderContext,
) -> str:
    parts: list[str] = ['<section><h2 class="section-h">Browse by domain</h2>']
    seen: set[int] = set()
    for key, label, blurb in _DOMAIN_ORDER:
        ids = groups.get(key, [])
        if not ids:
            continue
        cards: list[str] = []
        for cid in sorted(ids, key=lambda i: _helpers.sort_key(i)):
            cat = cat_by_id.get(cid)
            if not cat:
                continue
            seen.add(cid)
            cards.append(_render_card(cat, cat_slug_for, cat_meta, ctx))
        if not cards:
            continue
        parts.append(
            f'<section class="domain"><h3>{_helpers.escape(label)}</h3>'
            f'<p class="muted">{_helpers.escape(blurb)}</p>'
            f'<div class="grid">'
            + "".join(cards)
            + "</div></section>"
        )

    # Stragglers: any category not assigned to a domain.
    leftover = [c for c in cat_by_id.values() if c.get("i") not in seen]
    if leftover:
        cards = [
            _render_card(cat, cat_slug_for, cat_meta, ctx)
            for cat in sorted(leftover, key=lambda c: _helpers.sort_key(c.get("i", 0)))
        ]
        parts.append(
            '<section class="domain"><h3>Other</h3>'
            '<div class="grid">'
            + "".join(cards)
            + "</div></section>"
        )
    parts.append("</section>")
    return "\n".join(parts)


def _render_card(
    cat: dict[str, Any],
    cat_slug_for: dict[int, str],
    cat_meta: dict[str, dict[str, Any]],
    ctx: _helpers.RenderContext,
) -> str:
    cid = cat.get("i", 0)
    name = str(cat.get("n", ""))
    n_uc = sum(len(s.get("u", [])) for s in cat.get("s", []))
    slug = cat_slug_for.get(cid) or _helpers.slug(name)
    meta = cat_meta.get(str(cid), {}) or cat_meta.get(cid, {}) or {}
    blurb = _helpers.truncate(str(meta.get("desc") or ""), 130)
    if not blurb:
        blurb = f"{n_uc} use cases across {len(cat.get('s', []))} subcategories."
    return (
        f'<a class="card" href="{_helpers.attr(ctx.site_url)}/category/{_helpers.attr(slug)}/">'
        f'<div class="card-head"><span class="cat-id">Cat {cid}</span>'
        f'<span class="cat-count">{n_uc:,} UCs</span></div>'
        f'<div class="card-title">{_helpers.escape(name)}</div>'
        f'<p class="card-blurb">{_helpers.escape(blurb)}</p>'
        f'</a>'
    )


def _render_regulations(
    summaries: list[dict[str, Any]],
    ctx: _helpers.RenderContext,
) -> str:
    """Render the top-12 regulations rollup.

    ``summaries`` items must carry ``id``, ``slug``, ``shortName``,
    ``name``, ``useCaseCount``, ``tier``, and (optional) ``jurisdiction``.
    """
    if not summaries:
        return ""
    top = summaries[:12]
    cards: list[str] = []
    for fw in top:
        slug = fw.get("slug") or ""
        if not slug:
            continue
        n = fw.get("useCaseCount", 0)
        short = str(fw.get("shortName") or fw.get("id") or "")
        name = str(fw.get("name") or short)
        tier = fw.get("tier")
        tier_pill = (
            f'<span class="cat-id">Tier {int(tier)}</span>'
            if isinstance(tier, int) else ""
        )
        cards.append(
            f'<a class="card" href="{_helpers.attr(ctx.site_url)}/regulation/{_helpers.attr(slug)}/">'
            f'<div class="card-head">{tier_pill}'
            f'<span class="cat-count">{n:,} UCs</span></div>'
            f'<div class="card-title">{_helpers.escape(short)}</div>'
            f'<p class="card-blurb">{_helpers.escape(_helpers.truncate(name, 130))}</p>'
            f'</a>'
        )
    if not cards:
        return ""
    body = "".join(cards)
    return (
        f'<section><h2 class="section-h">Browse by regulation</h2>'
        f'<p class="muted">Top {len(cards)} frameworks by use-case coverage. '
        f'See the full <a href="{_helpers.attr(ctx.site_url)}/regulation/">regulation index</a> '
        f'for all {len(summaries)} mapped frameworks.</p>'
        f'<div class="grid">{body}</div></section>'
    )


def _render_quick_links(ctx: _helpers.RenderContext) -> str:
    items = [
        ("Catalog index (JSON)",      f"{ctx.site_url}/api/catalog-index.json"),
        ("Site manifest (JSON)",      f"{ctx.site_url}/manifest.json"),
        ("Regulations index (JSON)",  f"{ctx.site_url}/regulation/index.json"),
        ("OpenAPI",                    f"{ctx.site_url}/openapi.yaml"),
        ("Schemas",                    f"{ctx.site_url}/schemas/"),
        ("Sitemap",                    f"{ctx.site_url}/sitemap.xml"),
        ("Atom feed",                  f"{ctx.site_url}/feed.xml"),
        ("LLM-friendly index",         f"{ctx.site_url}/llms.txt"),
    ]
    li = "".join(
        f'<li><a href="{_helpers.attr(url)}">{_helpers.escape(label)}</a></li>'
        for label, url in items
    )
    return (
        f'<section><h2 class="section-h">For machines</h2>'
        f'<ul class="link-list">{li}</ul></section>'
    )


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
{hero_html}
{domain_html}
{regulation_html}
{quick_links}
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
