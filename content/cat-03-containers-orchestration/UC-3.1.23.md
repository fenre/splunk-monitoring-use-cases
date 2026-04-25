<!-- AUTO-GENERATED from UC-3.1.23.json — DO NOT EDIT -->

---
id: "3.1.23"
title: "Container Network I/O Anomalies"
criticality: "medium"
splunkPillar: "Security"
---

# UC-3.1.23 · Container Network I/O Anomalies

## Description

Per-container network throughput monitoring detects noisy neighbors saturating shared networks, unusual outbound traffic indicating data exfiltration, and connectivity issues causing application timeouts.

## Value

Per-container network throughput monitoring detects noisy neighbors saturating shared networks, unusual outbound traffic indicating data exfiltration, and connectivity issues causing application timeouts.

## Implementation

Collect `docker stats` output or cAdvisor metrics at regular intervals. Extract `rx_bytes`, `tx_bytes`, `rx_packets`, `tx_packets`, and `rx_dropped`/`tx_dropped` per container. Baseline per-container network profiles and alert on deviations above 3 standard deviations. High TX from a container that normally has low outbound traffic is a strong exfiltration indicator. Dropped packets signal network saturation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `docker stats` scripted input, cAdvisor metrics.
• Ensure the following data sources are available: `sourcetype=docker:stats`, `sourcetype=cadvisor`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect `docker stats` output or cAdvisor metrics at regular intervals. Extract `rx_bytes`, `tx_bytes`, `rx_packets`, `tx_packets`, and `rx_dropped`/`tx_dropped` per container. Baseline per-container network profiles and alert on deviations above 3 standard deviations. High TX from a container that normally has low outbound traffic is a strong exfiltration indicator. Dropped packets signal network saturation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="docker:stats"
| eval rx_mb=round(rx_bytes/1048576,2), tx_mb=round(tx_bytes/1048576,2)
| timechart span=5m avg(rx_mb) as rx_avg_mb, avg(tx_mb) as tx_avg_mb by container_name
| eventstats avg(tx_avg_mb) as baseline_tx, stdev(tx_avg_mb) as stdev_tx by container_name
| where tx_avg_mb > baseline_tx + 3*stdev_tx
```

Understanding this SPL

**Container Network I/O Anomalies** — Per-container network throughput monitoring detects noisy neighbors saturating shared networks, unusual outbound traffic indicating data exfiltration, and connectivity issues causing application timeouts.

Documented **Data sources**: `sourcetype=docker:stats`, `sourcetype=cadvisor`. **App/TA** (typical add-on context): `docker stats` scripted input, cAdvisor metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: docker:stats. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="docker:stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **rx_mb** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by container_name** — ideal for trending and alerting on this use case.
• `eventstats` rolls up events into metrics; results are split **by container_name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where tx_avg_mb > baseline_tx + 3*stdev_tx` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Docker data, spot-check a few events against the Docker engine on the host and the container list you expect. Compare with known good and bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (TX/RX per container), Bar chart (top talkers), Table (anomalous containers).

## SPL

```spl
index=containers sourcetype="docker:stats"
| eval rx_mb=round(rx_bytes/1048576,2), tx_mb=round(tx_bytes/1048576,2)
| timechart span=5m avg(rx_mb) as rx_avg_mb, avg(tx_mb) as tx_avg_mb by container_name
| eventstats avg(tx_avg_mb) as baseline_tx, stdev(tx_avg_mb) as stdev_tx by container_name
| where tx_avg_mb > baseline_tx + 3*stdev_tx
```

## Visualization

Line chart (TX/RX per container), Bar chart (top talkers), Table (anomalous containers).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
