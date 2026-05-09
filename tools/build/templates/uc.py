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

from build.models import CatalogCategory, CatalogSubcategory, CatalogUC

from . import _css, _helpers


def render_html(
    uc: CatalogUC,
    cat: CatalogCategory,
    sub: CatalogSubcategory,
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
    md_url = f"{ctx.site_url}/uc/UC-{uc_id}/uc.md"
    cat_url = f"{ctx.site_url}/category/{cat_slug}/"

    description = _helpers.truncate(value or _helpers.first_paragraph(uc.get("md", "")), 160)
    crit_label, crit_mod = _helpers.criticality_label(uc.get("c"))
    diff_label, diff_mod = _helpers.difficulty_label(uc.get("f"))
    wave_pair = _helpers.wave_label(uc.get("wv"))

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
            _section_implementation_ordering(uc, ctx=ctx),
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
    asset_styles = _helpers.asset_url(ctx.asset_styles, ctx.site_url) if ctx.asset_styles else ""
    extra_link = (
        f'<link rel="prefetch" href="{_helpers.attr(asset_styles)}" as="style">'
        if asset_styles else ""
    )

    if wave_pair is None:
        wave_badge_html = ""
    else:
        wave_lbl, wave_mod = wave_pair
        wave_badge_html = (
            '<span class="badge badge-wave-'
            + _helpers.attr(wave_mod)
            + '" title="'
            + _helpers.attr(_wave_tooltip(wave_mod))
            + '">Wave: '
            + _helpers.escape(wave_lbl)
            + "</span>"
        )

    return _PAGE_TEMPLATE.format(
        title=_helpers.escape(f"UC-{uc_id} · {title} · {ctx.site_short}"),
        description=_helpers.attr(description),
        canonical=_helpers.attr(page_url),
        json_alt=_helpers.attr(json_url),
        md_alt=_helpers.attr(md_url),
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
        wave_badge=wave_badge_html,
        cat_url=_helpers.attr(cat_url),
        cat_name=_helpers.escape(cat_name),
        sub_name=_helpers.escape(sub_name),
        cat_id=_helpers.escape(str(cat_id)),
        body=body,
        jsonld=jsonld,
        json_url=_helpers.attr(json_url),
        md_url=_helpers.attr(md_url),
        repo_url=_helpers.attr(ctx.repo_url),
        site_url_safe=_helpers.attr(ctx.site_url),
    )


# ---------------------------------------------------------------------------
# JSON twin
# ---------------------------------------------------------------------------


def render_index_json(
    uc: CatalogUC,
    cat: CatalogCategory,
    sub: CatalogSubcategory,
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
    self_full = f"UC-{uc_id}" if uc_id else ""

    # Stable top-level surface for the implementation-roadmap payload.
    # Keep keys omitted when empty so partners can distinguish "no
    # ordering declared" from "empty list". ``enabledBy`` is the
    # precomputed reverse lookup so consumers don't need to re-walk the
    # full catalog.
    ordering: dict[str, Any] = {}
    wave = str(uc.get("wv") or "").strip().lower()
    if wave in ("crawl", "walk", "run"):
        ordering["wave"] = wave
    pre_raw = uc.get("pre") or []
    pre = [
        str(p).strip() for p in pre_raw
        if isinstance(p, str) and str(p).strip() and str(p).strip() != self_full
    ] if isinstance(pre_raw, (list, tuple)) else []
    if pre:
        ordering["prerequisiteUseCases"] = pre
    enables = tuple(ctx.uc_reverse_prereq.get(self_full, ()))
    if enables:
        ordering["enabledBy"] = list(enables)

    payload: dict[str, Any] = {
        "$schema": "/schemas/v2/uc.schema.json",
        "version": "2.0.0",
        "id": f"UC-{uc_id}",
        "shortId": uc_id,
        "title": uc.get("n", ""),
        "url": page_url,
        "html": page_url,
        "json": f"{page_url}index.json",
        "markdown": f"{page_url}uc.md",
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
    if ordering:
        payload["implementationOrdering"] = ordering
    return payload


# ---------------------------------------------------------------------------
# Plain-markdown twin — LLM-friendly UC representation
# ---------------------------------------------------------------------------


def render_markdown_twin(
    uc: CatalogUC,
    cat: CatalogCategory,
    sub: CatalogSubcategory,
    cat_slug: str,
    *,
    ctx: _helpers.RenderContext,
) -> str:
    """Render a clean-markdown twin for ``/uc/UC-X.Y.Z/uc.md``.

    The HTML page at ``index.html`` is wrapped in CSS, JSON-LD, and a
    progressive-enhancement header. AI agents and ``curl`` users do not
    benefit from any of that — they want the SPL, the description, and
    the metadata in plain text.

    This twin is intentionally:

    * Pure markdown, no HTML.
    * Deterministic — same input produces byte-identical output.
    * Lightweight — typically 2-6 KB per UC.
    * Self-contained — links back to the canonical HTML page and JSON
      twin so a follow-up fetch is one hop away.

    Output shape:

        # UC-X.Y.Z — Title

        > Plain-language explanation (grandmaExplanation, when present).

        | Field | Value |
        | ... quick-facts table ...

        ## Description, ## Value, ## SPL, ## CIM SPL,
        ## Implementation, ## Visualization, ## Known false positives,
        ## CIM models, ## MITRE ATT&CK, ## Regulations,
        ## References, ## Plain-language explanation.

    Sections with empty source fields are omitted.
    """
    uc_id = str(uc.get("i", ""))
    title = str(uc.get("n", uc_id))
    page_url = f"{ctx.site_url}/uc/UC-{uc_id}/"
    json_url = f"{ctx.site_url}/uc/UC-{uc_id}/index.json"

    last_modified = str(uc.get("reviewed") or "").strip() or ctx.generated_at

    lines: list[str] = []
    lines.append(f"# UC-{uc_id} — {title}")
    lines.append("")
    lines.append(
        f"> Canonical HTML: {page_url}  ·  JSON twin: {json_url}"
    )
    lines.append(
        f"> Last-modified: {last_modified}  ·  Catalogue-version: {ctx.version}"
    )
    lines.append("")

    ge = str(uc.get("ge") or "").strip()
    if ge:
        lines.append("## In plain language")
        lines.append("")
        lines.append(f"> {ge}")
        lines.append("")

    facts: list[tuple[str, str]] = []

    def _add_fact(label: str, raw: Any) -> None:
        if raw is None or raw == "" or raw == [] or raw == {}:
            return
        if isinstance(raw, (list, tuple)):
            value = ", ".join(str(v) for v in raw if v not in (None, ""))
        else:
            value = str(raw).strip()
        if not value:
            return
        # Pipe characters in markdown table cells need escaping.
        value = value.replace("|", "\\|").replace("\n", " ")
        facts.append((label, value))

    cat_name = str(cat.get("n", ""))
    sub_name = str(sub.get("n", ""))
    _add_fact("Category", f"{cat.get('i')} — {cat_name}" if cat_name else "")
    _add_fact("Subcategory", sub_name)
    _add_fact("Criticality", uc.get("c"))
    _add_fact("Difficulty", uc.get("f"))
    _add_fact("Wave", uc.get("wv"))
    _add_fact("Monitoring type", uc.get("mtype"))
    _add_fact("Pillar", uc.get("pillar"))
    _add_fact("App / TA", uc.get("t"))
    _add_fact("Data sources", uc.get("d"))
    _add_fact("CIM models", uc.get("a"))
    _add_fact("Required fields", uc.get("reqf"))
    _add_fact("Data type", uc.get("dtype"))
    _add_fact("Security domain", uc.get("sdomain"))
    _add_fact("Equipment", uc.get("e"))
    _add_fact("Equipment models", uc.get("em"))
    _add_fact("Splunk versions", uc.get("sver"))
    _add_fact("Status", uc.get("status"))
    _add_fact("Last reviewed", uc.get("reviewed"))

    if facts:
        lines.append("## Quick facts")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("| --- | --- |")
        for label, value in facts:
            lines.append(f"| {label} | {value} |")
        lines.append("")

    pre = uc.get("pre") or []
    if isinstance(pre, (list, tuple)) and pre:
        lines.append("## Prerequisite use cases")
        lines.append("")
        for p in pre:
            p_str = str(p).strip()
            if not p_str:
                continue
            short = p_str[3:] if p_str.startswith("UC-") else p_str
            lines.append(
                f"- [{p_str}]({ctx.site_url}/uc/UC-{short}/)"
            )
        lines.append("")

    enables = tuple(ctx.uc_reverse_prereq.get(f"UC-{uc_id}", ()))
    if enables:
        lines.append("## Enables")
        lines.append("")
        for e in enables:
            short = e[3:] if e.startswith("UC-") else e
            lines.append(
                f"- [{e}]({ctx.site_url}/uc/UC-{short}/)"
            )
        lines.append("")

    def _add_text_section(heading: str, raw: Any) -> None:
        text = str(raw or "").strip()
        if not text:
            return
        lines.append(f"## {heading}")
        lines.append("")
        lines.append(text)
        lines.append("")

    def _add_code_section(heading: str, raw: Any, lang: str = "spl") -> None:
        text = str(raw or "").strip()
        if not text:
            return
        lines.append(f"## {heading}")
        lines.append("")
        lines.append(f"```{lang}")
        lines.append(text)
        lines.append("```")
        lines.append("")

    _add_text_section("Description", uc.get("md") or uc.get("v"))
    _add_text_section("Value", uc.get("v"))
    _add_code_section("SPL", uc.get("q"), "spl")
    _add_code_section("CIM SPL (tstats)", uc.get("qs"), "spl")
    _add_text_section("Implementation", uc.get("m"))
    _add_text_section("Detailed implementation", uc.get("md"))
    _add_text_section("Visualization", uc.get("z"))

    # ``kfp`` is annotated as ``str`` in CatalogUC and the runtime data
    # confirms this. The list/tuple defensive branch is preserved for
    # forward compatibility (a future schema migration may expose
    # structured falsePositives entries) — narrowed via Any to avoid
    # mypy's disjoint-subclass complaint.
    kfp_raw: Any = uc.get("kfp")
    if kfp_raw:
        lines.append("## Known false positives")
        lines.append("")
        if isinstance(kfp_raw, (list, tuple)):
            for item in kfp_raw:
                if str(item).strip():
                    lines.append(f"- {str(item).strip()}")
        else:
            lines.append(str(kfp_raw).strip())
        lines.append("")

    mitre = uc.get("mitre") or []
    if isinstance(mitre, (list, tuple)) and mitre:
        lines.append("## MITRE ATT&CK")
        lines.append("")
        for t in mitre:
            t_str = str(t).strip()
            if t_str:
                lines.append(f"- {t_str}")
        lines.append("")

    regs = uc.get("regs") or []
    if isinstance(regs, (list, tuple)) and regs:
        lines.append("## Regulations")
        lines.append("")
        for r in regs:
            r_str = str(r).strip()
            if r_str:
                lines.append(f"- {r_str}")
        lines.append("")

    # ``refs`` is the wire-format CSV string ("[Title](url), [...]") in
    # the current SSOT-derived catalog; the conversion lives in
    # parse_content. Pre-2026-05-09 catalogs sometimes carried a list
    # of structured ``UseCaseReference`` entries instead, and the
    # legacy markdown corpus did too — the list/tuple branch handles
    # those cases for forward/backward compatibility. mypy correctly
    # treats it as unreachable under the current TypedDict, but the
    # branch is intentional defence-in-depth.
    refs: Any = uc.get("refs") or []
    if isinstance(refs, (list, tuple)) and refs:
        lines.append("## References")
        lines.append("")
        for r in refs:
            r_str = str(r).strip()
            if r_str:
                lines.append(f"- {r_str}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        f"Source: [Splunk Monitoring Use Cases]({ctx.site_url}/) — "
        f"licensed MIT. UC-IDs are stable; see "
        f"[/llms.txt]({ctx.site_url}/llms.txt) for the catalog index "
        f"and [/AGENTS.md]({ctx.site_url}/AGENTS.md) for the agent "
        f"entrypoint."
    )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section renderers (each returns "" when the source field is empty)
# ---------------------------------------------------------------------------


def _section_value(uc: CatalogUC, value: str) -> str:
    if not value:
        return ""
    return f'<p class="lede">{_helpers.escape(value)}</p>'


def _section_quick_facts(uc: CatalogUC, cat_name: str, sub_name: str) -> str:
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


def _section_prerequisites(uc: CatalogUC) -> str:
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
        "<section><h2>Environment prerequisites</h2><ul>"
        + "".join(parts)
        + "</ul></section>"
    )


# Human-readable tooltip copy for each wave label. Kept consistent with
# the SPA (see ``waveBadge`` in index.html) so curators only need to
# update one description per wave across both renderers.
_WAVE_TOOLTIPS = {
    "crawl": (
        "Foundation wave — the platform, TAs, and data sources this "
        "use case relies on. Implement first."
    ),
    "walk": (
        "Intermediate wave — extends or correlates foundation data. "
        "Implement after at least one crawl UC from the same category."
    ),
    "run": (
        "Advanced wave — advanced analytics, cross-source correlation, "
        "or ML. Implement after walk UCs are stable."
    ),
}


def _wave_tooltip(mod: str) -> str:
    """Return the tooltip string for ``mod`` (``crawl``/``walk``/``run``)."""
    return _WAVE_TOOLTIPS.get(str(mod).lower(), "")


def _section_implementation_ordering(
    uc: CatalogUC, *, ctx: _helpers.RenderContext
) -> str:
    """Render the UC-to-UC prerequisite + Enables section.

    Emits:

    * "Implement first" — links out to every UC in ``uc["pre"]`` (forward
      edges of the dependency graph).
    * "Enables" — links out to every UC that depends on this one, looked
      up in ``ctx.uc_reverse_prereq``.

    Returns ``""`` when both directions are empty so the section is
    omitted entirely. Each link carries the target's wave badge inline
    to reinforce the roadmap story without a second round-trip.
    """
    uid = str(uc.get("i") or "").strip()
    self_full = f"UC-{uid}" if uid else ""
    pre_raw = uc.get("pre") or []
    pre: list[str] = []
    if isinstance(pre_raw, (list, tuple)):
        pre = [str(p).strip() for p in pre_raw if isinstance(p, str) and str(p).strip()]
    # Keep declared order but strip self-refs defensively; the validator
    # already rejects these, we must not crash render if seed data is
    # still in flight.
    pre = [p for p in pre if p != self_full]

    enables = tuple(ctx.uc_reverse_prereq.get(self_full, ()))

    if not pre and not enables:
        return ""

    parts: list[str] = ['<section class="uc-ordering"><h2>Implementation ordering</h2>']
    if pre:
        parts.append(
            '<h3>Implement first (prerequisites)</h3>'
            '<ul class="uc-chip-list">'
        )
        for dep in pre:
            parts.append(_render_uc_chip(dep, ctx=ctx))
        parts.append("</ul>")

    if enables:
        parts.append(
            '<h3>Enables</h3>'
            '<ul class="uc-chip-list">'
        )
        for dep in enables:
            parts.append(_render_uc_chip(dep, ctx=ctx))
        parts.append("</ul>")

    parts.append("</section>")
    return "".join(parts)


def _render_uc_chip(
    uc_full: str, *, ctx: _helpers.RenderContext
) -> str:
    """Render a single clickable UC chip: link, title tooltip, wave badge."""
    title, wave = ctx.uc_title_index.get(uc_full, ("", ""))
    short = uc_full[3:] if uc_full.startswith("UC-") else uc_full
    href = f"{ctx.site_url}/uc/UC-{short}/"
    label = title or uc_full
    inner_wave = ""
    if wave:
        pair = _helpers.wave_label(wave)
        if pair is not None:
            w_lbl, w_mod = pair
            inner_wave = (
                ' <span class="chip-wave chip-wave-'
                + _helpers.attr(w_mod)
                + '" title="'
                + _helpers.attr(_wave_tooltip(w_mod))
                + '">'
                + _helpers.escape(w_lbl)
                + "</span>"
            )
    return (
        '<li><a class="uc-chip" href="'
        + _helpers.attr(href)
        + '" title="'
        + _helpers.attr(label)
        + '"><span class="chip-id">'
        + _helpers.escape(uc_full)
        + "</span>"
        + inner_wave
        + "</a></li>"
    )


def _section_spl(uc: CatalogUC) -> str:
    spl = str(uc.get("q") or "").strip()
    if not spl:
        return ""
    return (
        '<section><h2>SPL</h2>'
        '<pre><code class="lang-spl">'
        + _helpers.escape(spl)
        + '</code></pre></section>'
    )


def _section_dma_spl(uc: CatalogUC) -> str:
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


def _section_implementation(uc: CatalogUC) -> str:
    text = str(uc.get("m") or "").strip()
    if not text:
        return ""
    return (
        "<section><h2>Implementation</h2>"
        + _helpers.render_markdown(text)
        + "</section>"
    )


def _section_visualization(uc: CatalogUC) -> str:
    text = str(uc.get("z") or "").strip()
    if not text:
        return ""
    return (
        "<section><h2>Visualization</h2>"
        + _helpers.render_markdown(text)
        + "</section>"
    )


def _section_known_fp(uc: CatalogUC) -> str:
    text = str(uc.get("kfp") or "").strip()
    if not text:
        return ""
    return (
        "<section><h2>Known false positives</h2>"
        + _helpers.render_markdown(text)
        + "</section>"
    )


def _section_regulations_mitre(uc: CatalogUC) -> str:
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
            label = str(m)
            if not label:
                continue
            parts.append("<li>" + _helpers.escape(label) + "</li>")
        parts.append("</ul>")
    parts.append("</section>")
    return "\n".join(parts)


def _section_apps(uc: CatalogUC) -> str:
    sapp = uc.get("sapp") or []
    ta = uc.get("ta_link") or {}
    if not sapp and not ta:
        return ""
    parts: list[str] = ["<section><h2>Splunkbase apps</h2><ul>"]
    ta_name = ta.get("name", "") if isinstance(ta, dict) else ""
    if ta_name:
        ta_url = ta.get("url", "") if isinstance(ta, dict) else ""
        if ta_url:
            parts.append(
                '<li><a href="'
                + _helpers.attr(ta_url)
                + '" rel="noopener noreferrer" target="_blank">'
                + _helpers.escape(ta_name)
                + "</a> <em>(primary TA)</em></li>"
            )
        else:
            parts.append(
                "<li>"
                + _helpers.escape(ta_name)
                + " <em>(primary TA)</em></li>"
            )
    for app in sapp:
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


def _section_references(uc: CatalogUC) -> str:
    refs = str(uc.get("refs") or "").strip()
    if not refs:
        return ""
    return (
        "<section><h2>References</h2>"
        + _helpers.render_markdown(refs)
        + "</section>"
    )


def _section_full_narrative(uc: CatalogUC) -> str:
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


def _section_provenance(uc: CatalogUC) -> str:
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
<meta name="theme-color" content="#003B8A" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0F1214" media="(prefers-color-scheme: dark)">
<link rel="canonical" href="{canonical}">
<link rel="alternate" type="application/json" href="{json_alt}" title="JSON twin">
<link rel="alternate" type="application/json" href="{json_alt}">
<link rel="alternate" type="text/markdown" href="{md_alt}" title="LLM-friendly markdown twin">
<meta property="og:type" content="article">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{og_url}">
<meta property="og:site_name" content="{site_name}">
<meta property="og:image" content="{og_image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{og_title}">
<meta name="twitter:description" content="{description}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{css}</style>
{extra_link}
{jsonld}
</head>
<body>
<header class="site">
<nav>
<a class="brand" href="{site_root}/">Use Case Catalog</a><span class="brand-sub">Community Reference</span>
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
{wave_badge}
<a class="badge" href="{cat_url}">{cat_name}</a>
</div>
</header>
{body}
<footer>
<p><a href="{json_url}" rel="alternate">JSON twin →</a> <a href="{md_url}" rel="alternate">Markdown twin →</a></p>
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
