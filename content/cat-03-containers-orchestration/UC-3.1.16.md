---
id: "3.1.16"
title: "Docker Volume Usage Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.1.16 · Docker Volume Usage Trending

## Description

Named volumes grow with databases and caches; trending usage prevents write failures and emergency disk expansion.

## Value

Named volumes grow with databases and caches; trending usage prevents write failures and emergency disk expansion.

## Implementation

Parse `docker system df -v` or volume inspect into Splunk daily. Alert when volume used GB grows >20% week-over-week or host filesystem backing the volume >85%.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (`docker system df -v`).
• Ensure the following data sources are available: `sourcetype=docker:volumes`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Parse `docker system df -v` or volume inspect into Splunk daily. Alert when volume used GB grows >20% week-over-week or host filesystem backing the volume >85%.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="docker:volumes"
| eval used_pct=if(SizeGB>0, round(UsedGB/SizeGB*100,1), null())
| timechart span=1d avg(UsedGB) as used_gb by volume_name
```

Understanding this SPL

**Docker Volume Usage Trending** — Named volumes grow with databases and caches; trending usage prevents write failures and emergency disk expansion.

Documented **Data sources**: `sourcetype=docker:volumes`. **App/TA** (typical add-on context): Custom scripted input (`docker system df -v`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: docker:volumes. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="docker:volumes". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by volume_name** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (used GB over time), Table (volume, host, used %), Single value (largest volume).

## SPL

```spl
index=containers sourcetype="docker:volumes"
| eval used_pct=if(SizeGB>0, round(UsedGB/SizeGB*100,1), null())
| timechart span=1d avg(UsedGB) as used_gb by volume_name
```

## Visualization

Line chart (used GB over time), Table (volume, host, used %), Single value (largest volume).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
