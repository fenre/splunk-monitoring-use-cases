---
id: "3.1.15"
title: "Image Layer Bloat Analysis"
criticality: "low"
splunkPillar: "Security"
---

# UC-3.1.15 · Image Layer Bloat Analysis

## Description

Large layer stacks slow pulls and increase attack surface; trending layer count and size guides image slimming and base image updates.

## Value

Large layer stacks slow pulls and increase attack surface; trending layer count and size guides image slimming and base image updates.

## Implementation

Nightly job exports `docker history` JSON per promoted image. Store per-layer size and count. Report images exceeding policy thresholds.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom input (`docker history --no-trunc`, `docker image inspect`).
• Ensure the following data sources are available: `sourcetype=docker:image:history`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Nightly job exports `docker history` JSON per promoted image. Store per-layer size and count. Report images exceeding policy thresholds.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="docker:image:history"
| stats sum(layer_size_bytes) as total_bytes, dc(layer_id) as layer_count by image_id, repository
| eval total_mb=round(total_bytes/1048576,1)
| where layer_count>25 OR total_mb>800
| sort -total_mb
```

Understanding this SPL

**Image Layer Bloat Analysis** — Large layer stacks slow pulls and increase attack surface; trending layer count and size guides image slimming and base image updates.

Documented **Data sources**: `sourcetype=docker:image:history`. **App/TA** (typical add-on context): Custom input (`docker history --no-trunc`, `docker image inspect`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: docker:image:history. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="docker:image:history". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by image_id, repository** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **total_mb** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where layer_count>25 OR total_mb>800` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (image vs MB), Table (image, layers, total MB), Trend (average image size).

## SPL

```spl
index=containers sourcetype="docker:image:history"
| stats sum(layer_size_bytes) as total_bytes, dc(layer_id) as layer_count by image_id, repository
| eval total_mb=round(total_bytes/1048576,1)
| where layer_count>25 OR total_mb>800
| sort -total_mb
```

## Visualization

Bar chart (image vs MB), Table (image, layers, total MB), Trend (average image size).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
