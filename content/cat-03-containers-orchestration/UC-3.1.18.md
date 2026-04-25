<!-- AUTO-GENERATED from UC-3.1.18.json — DO NOT EDIT -->

---
id: "3.1.18"
title: "Docker Build Cache Efficiency"
criticality: "low"
splunkPillar: "Observability"
---

# UC-3.1.18 · Docker Build Cache Efficiency

## Description

Poor cache reuse lengthens CI pipelines and increases registry churn; measuring cache hits guides Dockerfile ordering and BuildKit settings.

## Value

Poor cache reuse lengthens CI pipelines and increases registry churn; measuring cache hits guides Dockerfile ordering and BuildKit settings.

## Implementation

Ship structured build logs to Splunk. Parse CACHED vs executed steps. Dashboard average cache hit rate per repo branch. Alert on sustained drop after Dockerfile changes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: CI log forwarding (BuildKit, docker build --progress=plain).
• Ensure the following data sources are available: `sourcetype=docker:build`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ship structured build logs to Splunk. Parse CACHED vs executed steps. Dashboard average cache hit rate per repo branch. Alert on sustained drop after Dockerfile changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="docker:build"
| eval cache_hit=if(match(_raw, "(?i)CACHED"),1,0)
| stats sum(cache_hit) as hits, count as steps by build_id, image_name
| eval hit_rate=round(100*hits/steps,1)
| where hit_rate < 30 AND steps>10
| sort hit_rate
```

Understanding this SPL

**Docker Build Cache Efficiency** — Poor cache reuse lengthens CI pipelines and increases registry churn; measuring cache hits guides Dockerfile ordering and BuildKit settings.

Documented **Data sources**: `sourcetype=docker:build`. **App/TA** (typical add-on context): CI log forwarding (BuildKit, docker build --progress=plain). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: docker:build. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="docker:build". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **cache_hit** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by build_id, image_name** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **hit_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where hit_rate < 30 AND steps>10` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Docker data, spot-check a few events against the Docker engine on the host and the container list you expect. Compare with known good and bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (hit rate over builds), Table (repo, hit rate), Bar chart (CI duration vs hit rate).

## SPL

```spl
index=containers sourcetype="docker:build"
| eval cache_hit=if(match(_raw, "(?i)CACHED"),1,0)
| stats sum(cache_hit) as hits, count as steps by build_id, image_name
| eval hit_rate=round(100*hits/steps,1)
| where hit_rate < 30 AND steps>10
| sort hit_rate
```

## Visualization

Line chart (hit rate over builds), Table (repo, hit rate), Bar chart (CI duration vs hit rate).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
