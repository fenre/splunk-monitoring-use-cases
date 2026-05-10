# Clause Navigator — User Guide

The [Clause Navigator](../clause-navigator.html) is the auditor-first
view of the catalogue. It flips the direction of the relationship
between use cases and regulations: instead of *"this UC covers these
clauses"*, you start at *"this clause"* and pull every UC that maps to
it.

Audience: external auditors, internal audit, compliance officers,
GRC analysts, legal teams reviewing what the catalogue claims to cover.

For the regulator/legal narrative, read the
[Regulatory Primer](regulatory-primer.md) and the per-regulation
[Compliance Story](compliance-story-guide.md). For the methodology that
governs the mappings, read the
[Coverage Methodology](coverage-methodology.md). For the auditor-facing
evidence rollups, read the [Evidence Packs](evidence-packs/).

## Quick start

1. Open [`clause-navigator.html`](../clause-navigator.html).
2. Pick a **regulation** from the dropdown (e.g. *NIS2*, *PCI DSS*,
   *HIPAA Security*, *GDPR*).
3. Filter by clause id, topic, or short name in the search input.
4. Expand any row to see every UC that maps to that clause.
5. Click a UC to deep-link into the catalogue, **filtered by that very
   clause**.

That's the auditor workflow in five steps.

## What you see

### Header bar

Same brand and theme toggle as the rest of the site. The audience nav
on the right gives you quick links to:

- **Catalog** — the main use-case browser.
- **Documentation** — this wiki.
- **Graph** — the [Knowledge Graph](knowledge-graph-guide.md).

### Filter strip

- **Regulation** dropdown — single-select. The clause table re-renders
  for the selected framework. The selection appears in the URL
  (`#reg=<id>`) so you can share or bookmark.
- **Search** input — `placeholder="Filter by regulation, clause id,
  topic, or regulation short name…"`. Tokenised match across clause id,
  clause title, framework name, and short name.
- **Active filters** badge row — clearable individual filters with the
  ✕ button.

### Coverage summary

A small KPI row above the table shows:

- Total clauses in the selected framework.
- Clauses with **at least one** mapped UC.
- Clauses with **no coverage**.
- Optional **assurance breakdown** — `audited`, `evidence_pending`,
  `community` — for frameworks that carry the `assurance` field.

### Clause table

Each row is a single clause:

| Column | What it shows |
|---|---|
| **Clause id** | The version-specific id (e.g. `Art21.2.b`, `164.312(a)(1)`). |
| **Topic** | Short summary string (when the regulation grammar provides one). |
| **Coverage** | Count of UCs that map. Zero is rendered as a "no coverage" badge. |
| **Top assurance** | The strongest assurance level present across mapped UCs. |
| **▼ Expand** | Reveals the per-UC mapping list. |

When expanded, the row shows:

- Each covering UC with title, criticality, difficulty, status,
  assurance level, and mapping mode (`primary`, `supports`,
  `compensating`).
- The **`controlObjective`** if authored.
- The **`evidenceArtifact`** when the catalogue can point to one.
- A direct link into the catalogue **filtered by that exact clause**
  (`index.html#reg=<id>&clause=<version>%23<clause>`).

## URL parameters

The Clause Navigator is fully bookmark-friendly:

- `clause-navigator.html#reg=<id>` — opens with a regulation selected.
- `clause-navigator.html?reg=<id>` — same, query-style for places that
  strip fragments.
- `clause-navigator.html#reg=<id>&clause=<version>%23<clause>` — opens
  with the row pre-expanded and scrolled into view.

The auditor workflow often involves emailing a colleague a "look at
this clause" link — do it with this URL grammar.

## Where the data comes from

| Surface | Source |
|---|---|
| Regulation list and grammar | `data/regulations.json` |
| Per-UC clause mappings | `compliance[]` block in `content/cat-NN-*/UC-X.Y.Z.json` |
| Build-time clause index consumed by the page | `api/v1/compliance/clauses/index.json` |
| Per-regulation index | `api/v1/compliance/regulations/<id>.json` and `api/v1/compliance/regulations/<id>@<version>.json` |
| Coverage statistics | `api/v1/compliance/coverage.json` |
| Gap detection | `api/v1/compliance/gaps.json` |

The page fetches `api/v1/compliance/clauses/index.json` once per visit
and renders the table client-side. There is no backend.

For the JSON schema of these endpoints see
[API Versioning](api-versioning.md) and
[Catalog Schema](catalog-schema.md).

## How to use it as an auditor

The expected workflow is:

1. **Scope** — pick the framework you're auditing for.
2. **Triage gaps** — sort or scroll for clauses with `0` coverage. These
   are the holes you need to surface either as findings, scope
   exclusions, or a request for additional UCs.
3. **Sample evidence** — for clauses with coverage, expand a few rows
   and click into the catalogue to read the SPL, the
   `detailedImplementation`, and the `knownFalsePositives`. Capture
   evidence per the [Coverage Methodology](coverage-methodology.md).
4. **Cross-reference the evidence pack** — most tier-1 frameworks have a
   curated [Evidence Pack](evidence-packs/) that summarises clause
   coverage in narrative form and is easier to attach to a workpaper.
5. **Escalate concerns** — anything missing or weak should land as a
   GitHub issue or in the [SME Review Guide](sme-review-guide.md)
   pipeline.

## Limitations

- Clause-level coverage is reported but **not legally binding**. Read
  [LEGAL.md](../LEGAL.md) and the [Legal Review Guide](legal-review-guide.md).
- A clause counted as "covered" means the catalogue maps **at least one
  UC** to it. The strength of the mapping (`mode`, `assurance`,
  `derivationSource`, `requires_sme_review`) is in the per-UC sidecar
  and in the row expansion — don't read past it.
- The catalogue maps to **specific clause versions**. Pre-2023 GDPR is
  *not* the same row as post-2023 UK GDPR — the framework@version pair
  matters.
- The Clause Navigator loads from a static JSON file. If the API hasn't
  been re-built since the last UC change, the table may lag. The
  build pipeline rebuilds it on every commit to `main`.

## Where to go next

- [Compliance Story](compliance-story-guide.md) — the buyer / auditor /
  implementer narrative for a single regulation, designed to be read as
  a story rather than a table.
- [Evidence Packs](evidence-packs/) — long-form auditor rollup per
  tier-1 regulation with control objectives and quick-start playbooks.
- [Regulatory Primer](regulatory-primer.md) — plain-language explanation
  of every framework the catalogue maps.
- [Coverage Methodology](coverage-methodology.md) — formal rules for how
  coverage is computed and what counts.
