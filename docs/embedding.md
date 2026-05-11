# Embedding the Catalogue

Copy-paste recipes for putting catalogue content inside *your* page,
runbook, intranet, ITSM ticket template, or wiki.

Audience: integrators who want a UC to live somewhere other than the
catalogue itself — typically inside an existing internal portal,
runbook system, or vendor product page.

This doc replaces the "TBD" placeholder previously referenced in
[URL Scheme](url-scheme.md). For the API itself, see
[API Docs Page](api-docs-guide.md). For the schema of the JSON
payloads, see [Catalog Schema](catalog-schema.md).

## What's available today

Every UC in the catalogue is exposed at three coordinated URLs:

| URL | Format | Best for |
|---|---|---|
| `/uc/UC-X.Y.Z/` (or `/uc/UC-X.Y.Z/index.html`) | Full HTML page | Iframe embeds in a portal or wiki |
| `/uc/UC-X.Y.Z/index.json` | JSON twin | Custom rendering in your own app |
| `/uc/UC-X.Y.Z/uc.md` | Pure markdown twin | Pasting into wikis, LLM context, runbooks |

All three share the same identity, last-modified stamp, and catalogue
version number, so you can pick the format that matches the
embedding environment.

The same is true for **categories** (`/category/<slug>/{index.html,index.json}`)
and **regulations** (`/regulation/<slug>/{index.html,index.json}`).

## Approach 1 — Iframe a UC page

The simplest embed: drop a UC's HTML page in an iframe.

```html
<iframe
  src="https://fenre.github.io/splunk-monitoring-use-cases/uc/UC-9.6.4/"
  style="width: 100%; height: 800px; border: 0;"
  loading="lazy"
  title="UC-9.6.4 Brute force against AD over RDP"
  referrerpolicy="no-referrer">
</iframe>
```

Pros:

- Always up-to-date with the canonical content.
- Renders in the catalogue's design system, including dark mode.
- Includes the SPL with the **Copy** button, all references, and the
  related-documentation chips.

Cons:

- No size control beyond the iframe height — long UCs scroll within
  the frame.
- Mixes the catalogue's CSS with your page's CSS only via the iframe
  boundary.
- Content-Security-Policy on the host page must permit the catalogue
  origin.

For the full per-UC URL family (HTML, JSON, markdown, JSON-LD, OSCAL,
STIX), see [URL Scheme — `/uc/`](url-scheme.md#uc).

## Approach 2 — Fetch JSON and render in your own UI

Fetch the per-UC JSON and render the fields you care about. The JSON
twin is small (~2 KB) and stable.

```javascript
const ucId = 'UC-9.6.4';
const base = 'https://fenre.github.io/splunk-monitoring-use-cases';
const res = await fetch(`${base}/uc/${ucId}/index.json`);
const uc = await res.json();
document.getElementById('uc-card').innerHTML = `
  <h2>${uc.title}</h2>
  <p>${uc.value}</p>
  <p><strong>SPL:</strong></p>
  <pre><code>${escapeHtml(uc.spl)}</code></pre>
  <p>
    <a href="${base}/uc/${ucId}/" target="_blank" rel="noopener">
      Read the full use case →
    </a>
  </p>
`;
```

Pros:

- Full control over rendering.
- Pick exactly the fields you want.
- No iframe sandbox issues.

Cons:

- You own the rendering — re-implement what the catalogue does for
  free in the iframe approach (CIM chips, MITRE links, related-doc chips, …).
- Field shape is documented in [Catalog Schema](catalog-schema.md);
  authored fields are in [Use Case Field Reference](use-case-fields.md).

When using `innerHTML` with arbitrary content, **always escape** the
strings (use a DOMPurify-style sanitizer or `textContent` + manual
DOM construction). Catalogue strings are author-controlled, but
nothing stops a malicious PR; treat the JSON as untrusted input.

## Approach 3 — Paste the markdown twin

For runbooks, ServiceNow knowledge articles, Confluence pages,
internal wikis, or LLM context windows: fetch the markdown twin and
paste it.

```bash
curl -sSL https://fenre.github.io/splunk-monitoring-use-cases/uc/UC-9.6.4/uc.md \
  > uc-9.6.4.md
```

The markdown is "pure" — no front matter, no Liquid, no Jinja, no
custom tags — so it pastes cleanly into any markdown renderer
(GitHub, GitLab, Confluence Markdown, Obsidian, Notion-with-md, etc.).

Each markdown file is stamped with `Last-modified` and
`Catalogue-version` lines so you (or your wiki platform) can detect
when an update has shipped.

For LLM context use, prefer the markdown twin over the JSON because
it's already prose-shaped.

## Approach 4 — Catalogue deep-link "view in catalogue" buttons

If you want to keep your page lightweight but provide a path into the
full catalogue, use the [URL hash grammar](url-scheme.md#browse) for
deep-links:

```html
<a href="https://fenre.github.io/splunk-monitoring-use-cases/index.html#uc-9.6.4">
  View in catalogue →
</a>

<a href="https://fenre.github.io/splunk-monitoring-use-cases/index.html#cat-9/9.6">
  Browse subcategory 9.6 →
</a>

<a href="https://fenre.function.io/splunk-monitoring-use-cases/index.html#reg=NIS2">
  Filter by NIS2 →
</a>
```

These open the catalogue with the appropriate state pre-set. They're
the right choice for "deep dive into one UC" or "browse this
category" links from a parent page.

## Approach 5 — RSS feed

The catalogue emits an RSS feed of recently added UCs at
`https://fenre.github.io/splunk-monitoring-use-cases/feed.xml`. Embed
it in any RSS reader, intranet news ticker, or Slack feed bot.

## Versioning and stability

The URLs in this doc are **frozen at v7.0.0**. The contract is in
[URL Scheme](url-scheme.md) and [API Versioning](api-versioning.md):
URLs and JSON shape are stable for the lifetime of the v1 API.
Additive changes (new fields, new UCs) are in scope. Removals and
type changes are not.

If you embed at scale, pin to a known catalogue version by checking
the `version` and `lastModified` fields in `catalog.json` or per-UC
JSON. Breaking changes will bump the major version and live under
`/api/v2/` — your `/api/v1/` URLs stay valid.

## Caching, CSP, CORS

- The catalogue is served from GitHub Pages with default CDN caching
  (~10 minutes for static assets at the edge).
- All endpoints permit cross-origin reads (CORS `*`).
- For self-hosted intranets that cannot reach the public catalogue,
  build the catalogue locally (`make build`) and serve `dist/` from
  the same origin as the embedding page.
- Add the catalogue origin to your CSP `frame-src` (for iframe
  embeds) or `connect-src` (for `fetch`).

Recommended CSP additions:

```
frame-src   https://fenre.github.io;
connect-src https://fenre.github.io;
img-src     https://fenre.github.io;
```

## Performance

| Asset | Size | Strategy |
|---|---|---|
| Per-UC HTML | ~50 KB compressed | Iframe with `loading="lazy"` |
| Per-UC JSON | ~2 KB | Fetch on demand |
| Per-UC markdown | ~3 KB | Fetch on demand |
| `catalog.json` (full) | ~5 MB compressed | Cache server-side; not for browser embeds |

Per-UC fetches are tiny and CDN-cached — fine to do directly from a
browser.

## Planned (not yet shipped)

The repo's [URL scheme](url-scheme.md#embeddable-widgets) reserves a
namespace for **purpose-built embed widgets**:

- `/embed/uc/UC-X.Y.Z/` — small iframeable card (~5 KB) with an
  `auto-resize` `postMessage` helper.
- `/embed/category/<slug>/` — paginated list of UCs in a category.
- `/embed/scorecard/` — site-wide scorecard widget.
- `/embed/embed.js` — auto-resize + theming helper (≤3 KB).

These are **planned, not shipped**. Today, use approaches 1–4.

When the embed widgets ship, they will:

- Render in a much smaller box than the full UC page.
- Auto-resize their iframe height via `postMessage`.
- Inherit (or contrast with) the parent page's theme.
- Be permanently URL-stable per [URL Scheme](url-scheme.md).

## Compliance with `ai.txt` / attribution

When you embed catalogue content in a customer-facing page, please
honour the [`ai.txt`](../ai.txt) attribution preference. A link to the
catalogue source URL or a mention of "Splunk monitoring use case
catalogue" is appreciated and helps users find the canonical version.

## Where to go next

- [URL Scheme](url-scheme.md) — the full URL grammar, including the
  per-UC `/uc/UC-X.Y.Z/` family of artefacts.
- [API Docs Page](api-docs-guide.md) — interactive API explorer.
- [Catalog Schema](catalog-schema.md) — what's in the JSON twin.
- [API Versioning](api-versioning.md) — stability and deprecation
  policy.
- [`AGENTS-EXAMPLES.md`](../AGENTS-EXAMPLES.md) — recipes for AI
  agents (RAG, prompt-engineering) consuming the same JSON.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<a id="ref-2"></a>**[2]** Splunk Inc. (2026). *Splunk Common Information Model Add-on Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/CIM

<a id="ref-3"></a>**[3]** Splunk Inc. (2026). *Splunk Enterprise Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk

<a id="ref-4"></a>**[4]** Splunk Inc. (2026). *Splunk Enterprise Security Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ES

<a id="ref-5"></a>**[5]** Splunk Inc. (2026). *Splunk IT Service Intelligence Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ITSI

### Related repository documents

- [`docs/api-docs-guide.md`](api-docs-guide.md)
- [`docs/api-versioning.md`](api-versioning.md)
- [`docs/catalog-schema.md`](catalog-schema.md)
- [`docs/url-scheme.md`](url-scheme.md)
- [`docs/use-case-fields.md`](use-case-fields.md)

### Cited by

- [`docs/build-artefacts-reference.md`](build-artefacts-reference.md)
- [`docs/site-user-guide.md`](site-user-guide.md)
- [`docs/url-scheme.md`](url-scheme.md)

<!-- END-AUTOGENERATED-SOURCES -->
