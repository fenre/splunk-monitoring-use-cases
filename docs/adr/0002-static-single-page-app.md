# ADR-0002: Static single-page app with no back-end

- **Status:** Accepted
- **Date:** 2023-03-15 (ratified retroactively 2026-04-16)
- **Deciders:** Repository maintainers

## Context

The catalog dashboard needs to serve ≥6,300 UCs with full-text search, multi-axis filtering, deep-links per UC, and a release-notes overlay. The audience is global and intermittent; a typical visitor views a handful of UCs and leaves. Monthly traffic is steady but low (tens of thousands of page views). There is no user login, no personalisation, no user-generated content on the public site.

We needed a runtime architecture that is:

- Free or near-free to host.
- Trivial for a fork to re-deploy.
- Fast enough to render a large list without a loading spinner.
- Free of runtime secrets (no API keys, no database credentials).
- Crawlable by search engines and by LLMs.

## Decision

**The dashboard is a single static HTML file ([`index.html`](../../index.html)) that loads [`data.js`](../../data.js) and [`non-technical-view.js`](../../non-technical-view.js) as `<script>` tags and renders in the browser. There is no back-end.**

- Deployment target: GitHub Pages from the `main` branch root.
- No bundler, no framework, no NPM dependencies. All JS is inline in `index.html` or in the two globals-exposing `data*.js` files.
- The release-notes overlay HTML is generated at build time (from `CHANGELOG.md`) and injected into `index.html` by [`sync_release_notes()`](../../build.py).

## Consequences

**Positive:**

- Cost to host: $0 on GitHub Pages.
- Page weight, compressed: ~5 MB; decompressed `data.js` ~37 MB held in memory after load.
- No runtime secrets; no attack surface beyond static-asset serving.
- A fork points GitHub Pages at their own repo root and inherits the full site.
- The site is serve-able from any static host (S3, Netlify, Vercel, Cloudflare Pages, internal GitLab Pages) without modification.
- Search and filter are O(n) over a small in-memory dataset; latency is single-digit milliseconds.

**Negative:**

- All 6,300 UCs are shipped to every visitor, whether they load one UC or a hundred. Mitigation: per-category `api/cat-N.json` shards exist for integrators who need smaller payloads.
- No personalisation, saved filters, or user accounts. Mitigation: not a goal; the content is read-only.
- List rendering of 6,300+ items requires virtualisation in the DOM. Mitigation: implemented in `index.html`.
- Search and sort run on the client. Mitigation: fits in memory and executes fast; no server-side search needed.

## Alternatives considered

- **Next.js / Remix / Astro.** Rejected: adds a build toolchain and Node dependency; forkers inherit it.
- **Elasticsearch + backend search API.** Rejected: requires infrastructure; high cost for tens of thousands of monthly users.
- **Notion / Confluence / GitBook.** Rejected: proprietary, not diffable, no JSON export guarantee, hard to fork.
- **Hugo / Jekyll / MkDocs.** Rejected: the UI is not a "docs site"; it is a faceted catalog with a virtualised list. Static-site generators do not handle 6,300-item virtualised lists idiomatically.
- **React SPA.** Rejected: build step + npm install every CI run; forkers inherit that.

## Consequences for the replicator

A fork can:

- Replace GitHub Pages with any static host (see [DESIGN.md §14.3](../DESIGN.md#143-swap-the-host)).
- Replace the static HTML with a React SPA without touching the build pipeline, because `data.js` and `catalog.json` are the stable contract.

## Links

- Implementation: [`index.html`](../../index.html), [`data.js`](../../data.js), [`build.py:write_data_js()`](../../build.py)
- Customisation surface: [`custom-text.js`](../../custom-text.js)
- CI deployment: `.github/workflows/pages.yml`
- Superseded by: —
