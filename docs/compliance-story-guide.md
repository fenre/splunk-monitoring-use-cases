# Compliance Story — User Guide

The [Compliance Story](../compliance-story.html) page tells a complete
narrative for a single regulation in three parallel tracks:

- **Buyer** — what the law is, who it affects, why it matters, what
  Splunk delivers, what *this* catalogue specifically delivers.
- **Auditor** — coverage headline, top 5 highlights of evidence,
  top 3 gaps, signed-provenance pointers.
- **Implementer** — quick-start playbook with a sequenced wave plan
  (crawl / walk / run) and direct catalogue deep-links.

Audience: executives evaluating Splunk for a regulation, GRC teams
building roadmaps, auditors orienting before a deeper drill-in,
implementers picking the first 5 use cases to deploy.

This is the **narrative companion** to the [Clause
Navigator](clause-navigator-guide.md). The Clause Navigator is a table;
the Compliance Story is a story.

## Quick start

1. Open [`compliance-story.html?reg=<id>`](../compliance-story.html) — for
   example `?reg=NIS2` or `?reg=PCI-DSS`.
2. The page loads `api/v1/compliance/story/<id>.json` and renders the
   three-track narrative.
3. From the index view (no `?reg=` parameter), you can browse every
   regulation that has a story and pick one.

If `?reg=` is missing, the page shows an index of every available
story with a search input.

## What a story contains

Each story JSON carries these blocks (rendered in this order on the page):

### 1. Header

- Regulation **full name** and **short name**.
- Regulation **version**.
- A one-line headline of what we deliver.
- Theme toggle, audience nav, **Back to index** link.

### 2. What this regulation is

- **What it is** — the elevator pitch.
- **Who it affects** — scope.
- **Top obligations** — the headline articles / clauses the regulator
  tends to focus on.
- A pointer to the [Regulatory Primer](regulatory-primer.md) section
  for the full plain-language story.

### 3. Coverage headline

- Total clauses we map.
- Percentage with at least one mapped UC.
- Per-tier rollup (when the framework has a tier system).
- Per-clause **assurance distribution** (`audited` /
  `evidence_pending` / `community`).
- Coverage trend (delta vs the previous release window).

### 4. Top 5 highlights

The five strongest mappings — i.e. clauses where the catalogue has the
deepest evidence (gold-tier UCs, multiple supporting UCs, audited
assurance). Each highlight shows:

- Clause id and title.
- The **primary UC** that covers it.
- Why this is a highlight (1 sentence).
- A direct deep-link into the catalogue filtered by that clause.

### 5. Top 3 gaps

The three clauses where the catalogue is weakest — typically: zero
coverage, draft-only coverage, or coverage that requires SME review.
Each gap shows:

- Clause id and title.
- What's missing (no UC, draft-only, requires SME review, etc.).
- A pointer to the issue or PR that's working on it (when one exists).

### 6. Implementer playbook

A sequenced **crawl / walk / run** plan tied to the catalogue's
[implementation-roadmap](catalog-schema.md#implementationroadmap):

- **Crawl (week 1–4)** — the foundational UCs you need first; usually
  data-onboarding plus the highest-criticality detections.
- **Walk (month 2–3)** — fills out the obligated clauses.
- **Run (month 4+)** — depth UCs, ML detections, advanced anomaly
  hunting, audit-grade dashboards.

Each wave lists 5–10 specific UCs with deep-links into the catalogue.

### 7. Evidence and provenance

- Pointer to the auditor-facing [Evidence Pack](evidence-packs/) for
  the framework.
- Signed-provenance ledger reference (see
  [Signed Provenance](signed-provenance.md)).
- Last-reviewed date.

## URL parameters

- `compliance-story.html` — index of every story available.
- `compliance-story.html?reg=<id>` — opens the story for a regulation.
- `compliance-story.html?reg=<id>#highlights` / `#gaps` /
  `#playbook` — deep-links to a section.

The page also reads the `#reg=` hash form so it composes with the
URL conventions of the Clause Navigator and the catalogue.

## Where the data comes from

| Surface | Source |
|---|---|
| Story JSON | `api/v1/compliance/story/<regulationId>.json` |
| Story index | `api/v1/compliance/story/index.json` (when present) |
| Mapped clauses and UCs | Same source as the [Clause Navigator](clause-navigator-guide.md): `api/v1/compliance/clauses/index.json` |
| Coverage statistics | `api/v1/compliance/coverage.json` |
| Implementation roadmap | `catalog.json` → `implementationRoadmap` |
| Tier rollups | `data/regulations.json` framework metadata |

The story JSON is generated at build time from the per-UC `compliance[]`
sidecars by `tools/build/render_legacy_artifacts.py` (and related
generators). When you add a UC that maps a tier-1 regulation clause, the
story regenerates on next build.

## How to use it as a buyer

1. Pick the regulation you're scoped against.
2. Read **What it is** + **Who it affects** to confirm scope.
3. Check the **coverage headline** for the top-line "are we ready"
   answer.
4. Read the **top 5 highlights** to see where Splunk is strongest.
5. Read the **top 3 gaps** to see what you still need (either as
   compensating controls or scope exclusions).
6. Hand the **implementer playbook** to your delivery team.

## How to use it as an auditor

1. Use the **coverage headline** as your starting tier of risk
   assessment.
2. Walk the **highlights** to sample evidence — they're the strongest
   mappings, so they're the right places to test deep.
3. Walk the **gaps** to surface findings.
4. Cross-reference the [Clause Navigator](clause-navigator-guide.md)
   for the full clause table when you need exhaustive coverage.
5. Pull the [Evidence Pack](evidence-packs/) to attach to your
   workpapers.

## How to use it as an implementer

1. Skip straight to the **implementer playbook**.
2. Click into each UC and pick the lowest-difficulty version that
   delivers the value. The catalogue's wave/prerequisite rubric is
   designed for this — see [Implementation Ordering](implementation-ordering.md).
3. Pull the per-UC `detailedImplementation` for SPL and
   visualization specifics.
4. Use the [Recommender App](recommender-app.md) inside Splunk to
   confirm you have the data sources flowing.

## Limitations

- Stories are generated from authored sidecars. If a UC isn't tagged
  with the right `compliance[]` clause, it won't show up in the story.
- The **top 5 highlights** and **top 3 gaps** are **selected
  algorithmically** from the mapping data, not curated. They will shift
  release-over-release as the catalogue evolves.
- Same legal caveat as everything else: this is design and operational
  guidance, not legal advice. See [LEGAL.md](../LEGAL.md).

## Where to go next

- [Clause Navigator](clause-navigator-guide.md) — the exhaustive table
  view, when the narrative isn't enough.
- [Evidence Packs](evidence-packs/) — long-form auditor rollups.
- [Regulatory Primer](regulatory-primer.md) — full plain-language
  reference for every framework.
- [Coverage Methodology](coverage-methodology.md) — formal definition of
  how coverage is computed.
- [Implementation Ordering](implementation-ordering.md) — how the
  crawl/walk/run wave model works.
