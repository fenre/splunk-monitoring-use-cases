# Site User Guide

A walkthrough of the catalogue website at
[`index.html`](https://fenre.github.io/splunk-monitoring-use-cases/) — every
filter, tab, panel, and keyboard shortcut. This is the doc to read first if
you're a SOC analyst, IT operator, compliance officer, or executive who
just wants to *use* the catalogue without diving into the JSON API or the
authoring contract.

For developer-facing topics see [Architecture](architecture.md),
[Catalog Schema](catalog-schema.md), and [API Versioning](api-versioning.md).

## Top bar

The header is sticky and stays in view as you scroll.

| Control | What it does |
|---|---|
| ☰ **Hamburger** | Mobile-only — opens the category sidebar. |
| **Use Case Catalog** logo | Returns to the home view. |
| **Catalog / Documentation / Graph** | Switches between the three principal sites: this catalogue (`index.html`), the [documentation wiki](../docs.html), and the [knowledge graph](knowledge-graph-guide.md). |
| **Equipment** dropdown | Filters use cases by what hardware/vendor you have. See [Inventory & Sizing](inventory-and-sizing.md). |
| **My Inventory** | Opens the equipment-selection modal. Selections persist across visits in `localStorage`. |
| **Non-technical / Technical** | Audience toggle. See [Non-technical view](non-technical-view.md) for what changes. |
| 🔍 **Mobile search** | Compact search input on small screens. |
| **? How to use** | In-app help overlay with five tabs (Web / API / AI / Packs / Tools). |

## Sidebar

The left sidebar is the master navigation. It lists the 23 categories with
their use-case counts, expandable into subcategories. Click a category
name to filter the main view; click a subcategory to scope further.

The **Overview** row at the top resets the view to the home tab grid.

On screens narrower than 1080 px the sidebar is off-canvas — use the
hamburger to toggle.

## Search

Search is the fastest way into the catalogue. There are two inputs:

- **Header search** (sticky, always visible): full-text search across UC
  titles, values, descriptions, SPL queries, equipment, and references.
  Press `⌘K` (Mac) or `Ctrl+K` (Windows/Linux) to focus it from anywhere.
- **Mobile search bar** (small screens): same backing index, expanded for
  touch.

Search is *not* exact-match — it tokenises the query and ranks UCs by
field weight (title > value > implementation > SPL). When a search is
active, the URL gets a `#search=…` fragment so you can share or bookmark
the result set.

For the full set of URL-hash patterns (categories, subcategories,
regulations, MITRE, search, UC detail), see [URL Scheme](url-scheme.md).

## Tab bar (Technical view)

Below the search input you'll find six tabs that change *how* the result
set is grouped:

| Tab | What you see |
|---|---|
| **Categories** | Cards for each of the 23 domains, each linking into the category. |
| **Subcategories** | Cards for every subcategory — useful when you know the area but not the category. |
| **Use Cases** | Flat grid of every UC, paginated, sortable. The main "browse mode". |
| **Quick wins** | UCs marked `criticality: critical` AND `difficulty: beginner|intermediate` — highest value for least effort. |
| **Recently added** | UCs added in the last release window, surfaced by the build. |
| **Quality** | Group by [quality tier](gold-standard-template.md) (gold / silver / bronze / none) so you can see where the catalogue is strong and where it's thin. |

The tab choice persists in the URL fragment (`#alluc`, `#subcats`,
`#quickwins`, `#recent`, `#quality`).

## Filters

The filter strip above the result grid combines basic and advanced filters.

### Basic filters (always visible)

- **Pillar** chips — Security / Observability subset of `splunkPillar`.
- **Criticality** — `critical`, `high`, `medium`, `low`.
- **Difficulty** — `beginner`, `intermediate`, `advanced`, `expert`.
- **Status** — `verified`, `community`, `draft`.
- **Freshness** — last reviewed: ≤6 mo / 6–12 mo / >12 mo / never.
- **Regulation** — picks a regulation, then unlocks **Clause** for fine-grained selection.
- **Monitoring type** — from the curated `monitoringType` enum.
- **Trend** chip — UCs whose title matches `/trend/i` (anomaly / spike / drift detectors).

Each active filter shows up as a tag below the strip — click ✕ on any
tag to remove just that one. Use **Clear all** to start over.

### Advanced filters (collapsible)

Click **Advanced filters** to expand:

- **ES Detection** (`escu` field) — yes / no / all.
- **Detection type** — alert, dashboard, report, summary index, etc.
- **Premium apps** — UCs that depend on Splunk Enterprise Security, ITSI, SOAR, etc.
- **CIM model** — pick from the [CIM models inventory](cim-models-inventory.md).
- **App / TA** — Splunkbase ID list. UCs that match any selected TA.
- **Industry** — vertical/industry tags (`ind` field).
- **MITRE** — searchable dropdown of tactics + techniques. See [MITRE ATT&CK Mapping](mitre-attack-mapping.md).
- **MITRE Coverage Map** button — opens a modal with a full
  tactic × technique grid coloured by UC count. Click any tile to filter
  the catalogue by that technique.
- **Data source** — pick a source group (then a specific source) or type your own string.

The result count to the right of the filter strip updates live.

## Sort and export

In the **Use Cases** tab, the right edge of the strip carries:

- **Sort** dropdown — criticality, easiest/hardest first, A–Z / Z–A,
  by category. The choice persists in `localStorage`.
- **CSV / JSON** export buttons — download the *currently filtered*
  result set in either format.

## Use case cards

Each card carries a glanceable summary:

- Coloured **criticality dot** in the top-left.
- **Title** (or full UC ID below).
- A short **value** statement.
- **Tags** for difficulty, wave, depth tier, status, provenance,
  ESCU / RBA, archived app, regulation chips, telco use-case mark.
- A **multi-select checkbox** for the [Data Sizing tray](inventory-and-sizing.md#sizing-tray).

Click anywhere on the card to open the detail panel.

## Detail panel

When you click a card, the catalogue swaps to a **master-detail view**:
left sidebar stays, the middle column shows a list of sibling UCs in the
same category, the right column shows the full detail of the selected UC.

The detail panel sections (in order):

1. **Header** — UC ID, title, badges (criticality, difficulty, wave, depth, status, provenance), and meta line (monitoring type, pillar, Splunk versions, last reviewed, reviewer, industry, security domain, detection type, quality score).
2. **Open full page** — link to the static SSG page at `/uc/UC-X.Y.Z/`. Useful for sharing.
3. **In plain language** — the `grandmaExplanation` field.
4. **Quality gaps** — visible for thin UCs; lists what's missing per the [scorecard methodology](scorecard.md).
5. **Implementation ordering** — prerequisites and wave.
6. **Value** — full value statement.
7. **MITRE** chips — click any to filter the catalogue.
8. **Regulations** chips and **Compliance clauses** table — click any to filter.
9. **CIM**, **App/TA**, **equipment / models**, **premium apps**, **required fields**, **schema** — wire-up reference data.
10. **SPL / tstats / script** with **Copy** buttons.
11. **Implementation** + **Detailed implementation** + **Known false positives** + **References**.
12. **Visualization** + optional Splunkbase app screenshots / non-technical viz mockups.
13. **Telco use case** narrative when present.
14. **Related documentation** chips — pulled from [`docs-uc-map.js`](../docs-uc-map.js) and link straight into the doc wiki.
15. **Report issue on GitHub** — opens a pre-filled issue against the right file.

The middle column (**sibling list**) lets you walk through every UC in
the category without leaving the detail view.

The URL gains `#uc-X.Y.Z` so you can share or bookmark.

## Modals

The catalogue uses overlays for a few features that benefit from a
focused space:

- **My Equipment / Inventory** — pick the hardware/vendor you have, search, import/export JSON, **Apply Filter** to filter the catalogue, **Estimate Sizing →** to push the selection into the [Data Sizing Assessment](inventory-and-sizing.md).
- **MITRE ATT&CK Coverage Map** — visual tactic × technique grid with click-to-filter.
- **Sources** — the source catalogue of UC origins (vendor docs, security frameworks, community blogs).
- **Release notes** — versioned changelog rendered with the same design tokens. See [`CHANGELOG.md`](../CHANGELOG.md) for the markdown.
- **How to use** — five-tab help overlay (Web / API / AI / Packs / Tools).

Press `Esc` to close any modal.

## Footer

- **Text size** − / + — adjusts UI font size site-wide (persisted).
- **Theme** toggle — light / dark / auto.
- **Color-blind friendly** — alternate palette for criticality dots.
- **Sources**, **Release notes** — open the modals above.
- **Feedback** — GitHub link.

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `⌘K` / `Ctrl+K` | Focus search |
| `Esc` | Close any modal / detail panel |
| `←` / `→` (in detail panel) | Previous / next UC in the sibling list |

## Sharing what you found

Every meaningful state is reflected in the URL fragment, so you can
bookmark or share what you're looking at:

- `index.html#cat-9` — Category 9
- `index.html#cat-9/9.6` — Subcategory 9.6
- `index.html#uc-9.6.4` — A specific UC's detail panel
- `index.html#search=keberos+wireless` — A search result
- `index.html#reg=NIS2&clause=v1%23Art21.2.b` — Filtered by a clause
- `index.html#mitre=T1110.003` — Filtered by a MITRE technique

For the complete grammar, see [URL Scheme](url-scheme.md). For embedding
catalogue content in your own page, see [Embedding](embedding.md).

## Where to go next

- Brand new to the catalogue? Read the [README](../README.md).
- Want to write your own UCs? Start with the [Gold Standard Template](gold-standard-template.md) and [Use Case Field Reference](use-case-fields.md).
- Building integrations? Read [API Versioning](api-versioning.md), the [API Docs page](api-docs-guide.md), and [AGENTS-EXAMPLES](../AGENTS-EXAMPLES.md).
- Compliance team? Start with the [Regulatory Primer](regulatory-primer.md), then walk the [Clause Navigator](clause-navigator-guide.md) and a [Compliance Story](compliance-story-guide.md) for your framework.
