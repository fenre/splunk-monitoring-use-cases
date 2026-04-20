---
id: "3.1.11"
title: "Docker Daemon Resource Limits Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.1.11 · Docker Daemon Resource Limits Monitoring

## Description

Host-level CPU, memory, and storage pressure on the Docker engine starves containers before per-container limits trigger; early detection avoids fleet-wide slowdowns.

## Value

Host-level CPU, memory, and storage pressure on the Docker engine starves containers before per-container limits trigger; early detection avoids fleet-wide slowdowns.

## Implementation

Ingest `docker info` JSON (or `docker system df`) on an interval plus host memory/CPU from the node. Correlate with `docker:events` throttling and OOM. Alert when host memory used >85% or CPU saturation sustained >10 minutes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Connect for Docker, host metrics (Telegraf/OTel).
• Ensure the following data sources are available: `sourcetype=docker:info`, `sourcetype=docker:system`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest `docker info` JSON (or `docker system df`) on an interval plus host memory/CPU from the node. Correlate with `docker:events` throttling and OOM. Alert when host memory used >85% or CPU saturation sustained >10 minutes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="docker:info"
| eval mem_total_gb=round(MemTotal/1073741824, 2)
| eval mem_avail_gb=round(MemAvailable/1073741824, 2)
| eval mem_used_pct=round((MemTotal-MemAvailable)/MemTotal*100, 1)
| where mem_used_pct > 85 OR NCPU < 2
| table _time host mem_total_gb mem_avail_gb mem_used_pct NCPU
| sort -mem_used_pct
```

Understanding this SPL

**Docker Daemon Resource Limits Monitoring** — Host-level CPU, memory, and storage pressure on the Docker engine starves containers before per-container limits trigger; early detection avoids fleet-wide slowdowns.

Documented **Data sources**: `sourcetype=docker:info`, `sourcetype=docker:system`. **App/TA** (typical add-on context): Splunk Connect for Docker, host metrics (Telegraf/OTel). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: docker:info. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="docker:info". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **mem_total_gb** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **mem_avail_gb** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **mem_used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where mem_used_pct > 85 OR NCPU < 2` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Docker Daemon Resource Limits Monitoring**): table _time host mem_total_gb mem_avail_gb mem_used_pct NCPU
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (mem %, CPU load), Table (host, limits), Single value (hosts over threshold).

## SPL

```spl
index=containers sourcetype="docker:info"
| eval mem_total_gb=round(MemTotal/1073741824, 2)
| eval mem_avail_gb=round(MemAvailable/1073741824, 2)
| eval mem_used_pct=round((MemTotal-MemAvailable)/MemTotal*100, 1)
| where mem_used_pct > 85 OR NCPU < 2
| table _time host mem_total_gb mem_avail_gb mem_used_pct NCPU
| sort -mem_used_pct
```

## Visualization

Line chart (mem %, CPU load), Table (host, limits), Single value (hosts over threshold).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
