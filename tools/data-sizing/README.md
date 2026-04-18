# Data Sizing Assessment

Static, single-page web app that helps a Splunk practitioner build a
back-of-the-envelope sizing estimate for an ingest workload. It lives
under `tools/` so it ships with the catalogue but is independent of the
use-case content under `use-cases/`.

## What it does

- Catalogues common Splunk data sources (security, IT, OT, network,
  protocols, business, Cisco vendor stack, OT vendor stack).
- Lets the user add instances of each source with realistic
  per-endpoint or per-tag rates.
- Computes events-per-second, GB/day, and an indexer/storage estimate
  with retention assumptions.
- Exports a sharable report (clipboard / file download) for use in
  proposal or design docs.

The numbers are reference defaults derived from typical field
deployments. Always validate against your own collector telemetry
before sizing production.

## Files

| File | Role |
| --- | --- |
| `index.html` | Single page entry point. |
| `styles.css` | Theme tokens (mirrors the catalogue's Cisco-inspired palette). |
| `app.js` | UI state, calculation engine, export logic. |
| `mapping.js` | Source → category mapping with per-endpoint rates. |
| `ot-data-sources.js` | Reference catalogue of OT-specific sources. |

No build step, no runtime dependencies. Open `index.html` directly or
serve the directory with any static web server (`python3 -m http.server`
works fine for a quick preview).

## Live deployment

Published to GitHub Pages alongside the catalogue at
`/tools/data-sizing/`. Linked from the "Data Sizing" footer item on the
main catalogue page (`index.html`).

## Branding

The page header shows "Data Sizing Assessment — Community Reference"
and is styled with the same design tokens as the main catalogue. There
is no claim of an official Cisco product (see the v6.1 branding fix in
`CHANGELOG.md`).
