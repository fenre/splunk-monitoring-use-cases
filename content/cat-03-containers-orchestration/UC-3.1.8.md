<!-- AUTO-GENERATED from UC-3.1.8.json — DO NOT EDIT -->

---
id: "3.1.8"
title: "Docker Daemon Errors"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.1.8 · Docker Daemon Errors

## Description

Docker daemon errors affect all containers on the host. Network, storage driver, and containerd errors can cause widespread container failures.

## Value

Docker daemon errors affect all containers on the host. Network, storage driver, and containerd errors can cause widespread container failures.

## Implementation

Forward Docker daemon logs (usually via journald or `/var/log/docker.log`). Alert on fatal errors. Track error patterns by host.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Syslog, Docker daemon log forwarding.
• Ensure the following data sources are available: `/var/log/docker.log` or `journalctl -u docker`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward Docker daemon logs (usually via journald or `/var/log/docker.log`). Alert on fatal errors. Track error patterns by host.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="docker:daemon" level="error" OR level="fatal"
| stats count by host, msg
| sort -count
```

Understanding this SPL

**Docker Daemon Errors** — Docker daemon errors affect all containers on the host. Network, storage driver, and containerd errors can cause widespread container failures.

Documented **Data sources**: `/var/log/docker.log` or `journalctl -u docker`. **App/TA** (typical add-on context): Syslog, Docker daemon log forwarding. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: docker:daemon. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="docker:daemon". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, msg** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Docker data, spot-check a few events against the Docker engine on the host and the container list you expect. Compare with known good and bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, error, count), Timeline, Bar chart by error type.

## SPL

```spl
index=containers sourcetype="docker:daemon" level="error" OR level="fatal"
| stats count by host, msg
| sort -count
```

## Visualization

Table (host, error, count), Timeline, Bar chart by error type.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
