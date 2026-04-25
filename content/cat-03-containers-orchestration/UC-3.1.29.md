<!-- AUTO-GENERATED from UC-3.1.29.json — DO NOT EDIT -->

---
id: "3.1.29"
title: "Container Filesystem Write Rate"
criticality: "medium"
splunkPillar: "Security"
---

# UC-3.1.29 · Container Filesystem Write Rate

## Description

High write rates to the container's writable layer (overlay filesystem) indicate missing volume mounts, excessive application logging to local disk, or tmp file abuse. This degrades performance and fills the Docker storage driver, potentially affecting all containers on the host.

## Value

High write rates to the container's writable layer (overlay filesystem) indicate missing volume mounts, excessive application logging to local disk, or tmp file abuse. This degrades performance and fills the Docker storage driver, potentially affecting all containers on the host.

## Implementation

Collect `docker stats` or cAdvisor block I/O metrics at regular intervals. Extract `blkio.io_service_bytes_recursive` for read and write operations per container. Alert when any container sustains write rates above 100 MB per 5-minute window. Investigate which process inside the container is writing (use `docker exec` or container logs). Common root causes: application logging to stdout captured by json-file driver with no rotation, temp file accumulation, and missing persistent volume mounts for data directories.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `docker stats` scripted input, cAdvisor metrics.
• Ensure the following data sources are available: `sourcetype=docker:stats`, `sourcetype=cadvisor`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect `docker stats` or cAdvisor block I/O metrics at regular intervals. Extract `blkio.io_service_bytes_recursive` for read and write operations per container. Alert when any container sustains write rates above 100 MB per 5-minute window. Investigate which process inside the container is writing (use `docker exec` or container logs). Common root causes: application logging to stdout captured by json-file driver with no rotation, temp file accumulation, and missing persistent volume mounts fo…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="docker:stats"
| eval block_write_mb=round(block_write_bytes/1048576,2)
| timechart span=5m sum(block_write_mb) as write_mb by container_name
| where write_mb > 100
```

Understanding this SPL

**Container Filesystem Write Rate** — High write rates to the container's writable layer (overlay filesystem) indicate missing volume mounts, excessive application logging to local disk, or tmp file abuse. This degrades performance and fills the Docker storage driver, potentially affecting all containers on the host.

Documented **Data sources**: `sourcetype=docker:stats`, `sourcetype=cadvisor`. **App/TA** (typical add-on context): `docker stats` scripted input, cAdvisor metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: docker:stats. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="docker:stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **block_write_mb** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by container_name** — ideal for trending and alerting on this use case.
• Filters the current rows with `where write_mb > 100` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Docker data, spot-check a few events against the Docker engine on the host and the container list you expect. Compare with known good and bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (write rate per container), Bar chart (top writers), Table (containers exceeding threshold).

## SPL

```spl
index=containers sourcetype="docker:stats"
| eval block_write_mb=round(block_write_bytes/1048576,2)
| timechart span=5m sum(block_write_mb) as write_mb by container_name
| where write_mb > 100
```

## Visualization

Line chart (write rate per container), Bar chart (top writers), Table (containers exceeding threshold).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
