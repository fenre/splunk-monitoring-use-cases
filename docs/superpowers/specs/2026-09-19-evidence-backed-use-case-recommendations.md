# Evidence-backed use case recommendations

**Status:** accepted  
**Date:** 2026-09-19  
**Name:** recommendation profiles (not “evidence packs”)

## Problem

Catalog-metadata ranking (quality tier × wave × criticality) does not answer
“what should we implement first for this product?” Equipment tags are too
greedy or too sparse, so ranking never sees the right UCs. The Splunk
recommender app scores inventory match, which is readiness, not value.

## Contract

1. **Value** comes from hand-authored **recommendation profiles** with an
   ordered core pack (5–10 UC IDs) cited to vendor docs, Splunk Lantern, and
   SRE practice. Do not invent ROI numbers. Customer stories are measurement
   patterns only.
2. **Readiness** comes from prerequisites, required data, suites, maturity,
   and (in Splunk) live inventory. A high-value UC with no data stays visible
   as **High value, unblock first**, never dropped.
3. **Quality tier is confidence**, not value.
4. Presentation classes: **Start now**, **High value, unblock first**,
   **Foundation**, **Later**.
5. Profiles override equipment-tag matching for the six pilot products.
   Unprofiled slugs keep the catalog-only fallback.
6. Zero-context copy: “Best-practice starting point,” not “most valuable for you.”
7. Linux means OS telemetry (CPU, memory, disk, auth, service crash), not
   every UC that mentions Linux.
8. If a cited vendor control has no catalog ID, **author the UC**. Do not
   silently skip it.

## Pilot products

`cisco_ise`, `vmware`, `paloalto`, `aws`, `kubernetes`, `linux`.

## Artifacts

| Artifact | Role |
|---|---|
| `data/recommendation-profiles/<slug>.json` | Authoritative profile |
| `schemas/recommendation-profile.schema.json` | Validation |
| `graph-recommend.json` | Compact public payload |
| `api/v1/recommender/profiles.json` | Additive v1 API |
| `graph-recommend.js` | Shared ranker (graph, tests, VISTA) |

## Context depths

- **Zero-context:** core pack order.
- **Guided:** optional questionnaire (role, outcomes, suites, maturity).
- **VISTA-rich / Splunk-inventory-rich:** same context object plus readiness.

## Out of scope

MCP `search_use_cases` ranking, full 331-slug coverage, Use Case Registry
export, live CISA KEV lookups.
