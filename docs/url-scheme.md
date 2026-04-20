# URL Scheme

> **Status:** Locked at v7.0.0. Every URL on this page is a permanent contract. The
> `tools/audits/url_freeze.py` audit blocks merges that remove or rename a URL
> exposed by the latest release's `dist/manifest.json`. New URLs may be added at any
> time; existing ones are retired only via the deprecation process in
> [`api-versioning.md`](api-versioning.md).

## Design rules

1. **Permanent.** Once published in a tagged release, a URL never changes meaning.
2. **Human-readable.** Slugs are lowercase, hyphenated, ASCII-only.
3. **Machine-friendly.** Every HTML page has a sibling JSON at the same path with
   `index.json` (or other documented name); every list page also has a paired Atom or
   CSV export.
4. **Versioned where versioning matters.** Versioning lives in `/api/v{N}/` only.
   Content URLs (`/uc/`, `/category/`, `/regulation/`) carry no version in the path —
   stability is enforced by the URL-freeze audit.
5. **No verbs in paths.** Read-only.
6. **Trailing slash on directories.** All directory URLs end with `/`. The build
   emits `index.html` and (where defined) `index.json` inside each directory so the
   server doesn't have to care.
7. **One canonical URL per resource.** No `?` query strings change the canonical
   resource. Filter/search state in `/browse/` lives in the URL hash (`#`) so it
   doesn't fragment caches.

## Path namespace

The site is hosted at `https://splunk-monitoring.io/` (or your fork's GitHub Pages
URL). All paths below are relative to that origin.

### Reserved roots (never reuse for content)

| Root | Reserved for | Status |
|---|---|---|
| `/api/` | Versioned & unversioned machine endpoints | Active |
| `/{lang}/` | Future i18n (e.g. `/de/`, `/ja/`). Two-letter ISO 639-1 only. | Reserved |
| `/v/{shortid}/` | Permashort UC links (Sigstore-signed mapping in `dist/api/shortlinks.json`) | Reserved |
| `/embed/` | iframeable widgets | Active |
| `/exports/` | Bulk exports (CSV/JSON/OSCAL/STIX/ZIP) | Active |
| `/assets/` | Fingerprinted CSS/JS/images | Active |

### Top-level pages

| URL | Type | Description |
|---|---|---|
| `/` | HTML | Landing page. Links to `/browse/`, top categories, latest UCs. ≤100 KB gz. |
| `/browse/` | HTML+JS | Interactive SPA. Bootstraps from `/api/catalog-index.json`. URL hash carries filter state, e.g. `/browse/#cat=10&pillar=security&q=okta`. |
| `/about/` | HTML | Project mission, governance link. |
| `/changelog/` | HTML | Mirror of `CHANGELOG.md`. |
| `/governance/` | HTML | Mirror of `docs/governance.md`. |

### Content pages (the contract)

#### Use cases

```
/uc/UC-X.Y.Z/                    HTML (canonical)
/uc/UC-X.Y.Z/index.json          JSON (full UC record per uc.schema.json)
/uc/UC-X.Y.Z/jsonld.json         JSON-LD: TechArticle + HowTo + BreadcrumbList
/uc/UC-X.Y.Z/oscal.json          OSCAL component-definition fragment
/uc/UC-X.Y.Z/stix.json           STIX 2.1 bundle (security UCs only)
/uc/UC-X.Y.Z/csv-row.json        Single-row CSV-shaped JSON for spreadsheets
/uc/UC-X.Y.Z/uc.md               Original Markdown prose (verbatim from content/)
/uc/UC-X.Y.Z/og.png              1200×630 OpenGraph image (auto-generated)
```

`X.Y.Z` is the existing `category.subcategory.usecase` numeric ID (e.g.
`UC-22.1.1`). IDs are forever; renumbering is forbidden.

#### Categories

```
/category/<slug>/                       HTML (canonical)
/category/<slug>/index.json             JSON: {category, subcategories[], ucs[]}
/category/<slug>/export.csv             All UCs in this category, CSV
/category/<slug>/export.oscal.json      Category as one OSCAL component-definition
```

`<slug>` is derived from the category name in `content/cat-NN-slug/_category.json`,
e.g. `/category/security-infrastructure/`. The numeric prefix (`cat-10`) is **not**
in the URL — slug is the canonical identifier. A `cat-NN` → slug mapping is
published in `dist/api/manifest.json` for tooling.

#### Regulations

```
/regulation/<slug>/                  HTML (canonical)
/regulation/<slug>/index.json        JSON: {regulation, clauses[], ucs[], gaps}
```

`<slug>` matches `data/regulations.json` regulation IDs, e.g. `/regulation/nis2/`,
`/regulation/pci-dss/`, `/regulation/iso-27001/`.

#### Equipment (lazy)

```
/equipment/<slug>/                   HTML (only emitted if ≥1 UC references it)
/equipment/<slug>/index.json         JSON
```

`<slug>` is derived from `data/equipment.json` model IDs.

### Embeddable widgets

```
/embed/uc/UC-X.Y.Z/                  iframeable card for a single UC (~5 KB)
/embed/category/<slug>/              compact paginated list of UCs in a category
/embed/scorecard/                    site-wide scorecard widget
/embed/embed.js                      auto-resize + postMessage theming helper (≤3 KB)
```

Documented with copy-paste snippets in [`docs/embedding.md`](embedding.md).

### Discovery

| URL | Description |
|---|---|
| `/sitemap.xml` | Sitemap index (auto-shards `/sitemap-pages-NN.xml` when total > 50 K URLs). |
| `/sitemap-pages-NN.xml` | Per-shard URL set. |
| `/robots.txt` | `Allow: /`, points to sitemap. |
| `/feed.xml` | Atom feed of the last 50 added/changed UCs. |
| `/llms.txt` | Concise index for LLM agents. |
| `/llms-full.txt` | Verbose index with every UC ID and title. |
| `/manifest.webmanifest` | PWA manifest (Service Worker enabled). |
| `/openapi.yaml` | OpenAPI 3.1 description of `/api/v1/` and the lazy-load endpoints. |

### API surface

See [`api-versioning.md`](api-versioning.md) for the full contract.

```
/api/catalog-index.json          UC stubs for /browse/ bootstrap (gzip-targeted ≤1 MB)
/api/cat-N.json                  Per-category full UC payload (lazy-loaded by /browse/)
/api/manifest.json               Global path index for machine consumers
/api/shortlinks.json             /v/{shortid}/ → /uc/UC-X.Y.Z/ map

/api/v1/                         Versioned, semver-stable API (current major)
/api/v2/                         Reserved for next major
```

### Bulk exports

```
/exports/catalog.csv             All UCs, one row each
/exports/catalog.json            All UCs, structured
/exports/catalog.oscal.json      Site-wide OSCAL bundle
/exports/catalog.stix.json       STIX bundle of security UCs
/exports/catalog.zip             ZIP containing all of the above + uc/*/uc.md
```

### Build proof (machine consumers)

```
/integrity.json                  SHA-256 of every artefact + Merkle tree root
/BUILD-INFO.json                 git SHA, schema versions, UC count, asset hashes
/.well-known/security.txt        coordinated disclosure contact
```

`integrity.json` is Sigstore-signed in CI via `actions/attest-build-provenance@v1`.
The signature is published as a GitHub release attestation; verify with:

```bash
gh attestation verify dist/integrity.json --owner <owner>
```

## URL hash conventions (`/browse/`)

`/browse/` accepts a tilde-style hash that is stable across releases. Order of keys
does not matter; unknown keys are ignored.

| Key | Example | Meaning |
|---|---|---|
| `cat` | `cat=10` | Category numeric ID |
| `sub` | `sub=10.1` | Subcategory numeric ID |
| `pillar` | `pillar=security` | Splunk pillar (security/observability/itops/platform) |
| `mtype` | `mtype=detection` | monitoringType (detection/health/inventory/compliance) |
| `crit` | `crit=critical` | criticality |
| `reg` | `reg=nis2,pci-dss` | Comma-list of regulation slugs |
| `mitre` | `mitre=T1078` | ATT&CK technique ID |
| `q` | `q=okta+mfa` | Free-text search |

Example: `/browse/#cat=10&pillar=security&reg=nis2,pci-dss&q=okta`. The hash format
is locked; new keys may be added but existing keys are forever.

## Redirects from v6.x

The v6.x → v7.0 cutover deliberately breaks deep links (per the project owner). The
build emits `dist/_redirects` (Cloudflare/Fastly) and `<meta http-equiv="refresh">`
fallbacks (GitHub Pages) for the most-trafficked v6.x URLs:

| v6.x URL | v7.0 redirect target |
|---|---|
| `/use-cases/cat-NN-<slug>.md` | `/category/<slug>/` |
| `/api/cat-N.json` | unchanged (still emitted) |
| `/scorecard.html` | `/exports/scorecard.html` |
| `/regulatory-primer.html` | `/regulation/` |
| `/api-docs.html` | `/openapi.yaml` |

After v7.0.0, **no further URL breaks are permitted**. Any future change goes through
the RFC process in [`governance.md`](governance.md), with a minimum 12-month parallel
support window matching the API deprecation policy.

## Why this layout

* **Hierarchical without hierarchy in IDs.** UC IDs (`UC-22.1.1`) carry their
  category in the number for human reading, but the URL keeps the UC at the root
  (`/uc/UC-22.1.1/`) so re-categorisation never moves a UC.
* **One slug per concept, everywhere.** Category and regulation slugs match across
  HTML, JSON, OSCAL, sitemap, manifest, and exports — search engines, LLMs, and
  scripts converge on the same identifiers.
* **Static-first, machine-equal.** Every HTML page has a JSON twin at the same path,
  giving humans and machines first-class access without duplicate URL trees.
* **Embed and export are first-class.** `/embed/`, `/exports/`, and `/v/` are
  reserved roots so we can scale them without polluting the content namespace.
