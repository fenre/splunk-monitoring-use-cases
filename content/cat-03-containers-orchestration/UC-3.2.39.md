---
id: "3.2.39"
title: "Kubernetes Events Anomaly Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.39 · Kubernetes Events Anomaly Detection

## Description

Sudden `Warning` event storms often precede control plane or network incidents; statistical baselines catch abnormal rates per namespace.

## Value

Sudden `Warning` event storms often precede control plane or network incidents; statistical baselines catch abnormal rates per namespace.

## Implementation

Baseline Warning rate per namespace with rolling stdev. Tune thresholds for chatty namespaces. Optional: replace with `anomalydetection` or MLTK for seasonality.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk ML Toolkit (optional) or scheduled analytics.
• Ensure the following data sources are available: `sourcetype=kube:objects:events`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Baseline Warning rate per namespace with rolling stdev. Tune thresholds for chatty namespaces. Optional: replace with `anomalydetection` or MLTK for seasonality.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:objects:events" type="Warning"
| bin _time span=15m
| stats count as warn_count by _time, namespace
| eventstats avg(warn_count) as avg_w stdev(warn_count) as sd by namespace
| eval z=if(sd>0 AND sd!=null, (warn_count-avg_w)/sd, 0)
| where abs(z)>3 AND warn_count>10
| table _time namespace warn_count avg_w z
| sort -warn_count
```

Understanding this SPL

**Kubernetes Events Anomaly Detection** — Sudden `Warning` event storms often precede control plane or network incidents; statistical baselines catch abnormal rates per namespace.

Documented **Data sources**: `sourcetype=kube:objects:events`. **App/TA** (typical add-on context): Splunk ML Toolkit (optional) or scheduled analytics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:objects:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:objects:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, namespace** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eventstats` rolls up events into metrics; results are split **by namespace** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **z** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where abs(z)>3 AND warn_count>10` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Kubernetes Events Anomaly Detection**): table _time namespace warn_count avg_w z
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart with overlay, Table (namespace, spike z-score), Single value (anomaly intervals).

## SPL

```spl
index=k8s sourcetype="kube:objects:events" type="Warning"
| bin _time span=15m
| stats count as warn_count by _time, namespace
| eventstats avg(warn_count) as avg_w stdev(warn_count) as sd by namespace
| eval z=if(sd>0 AND sd!=null, (warn_count-avg_w)/sd, 0)
| where abs(z)>3 AND warn_count>10
| table _time namespace warn_count avg_w z
| sort -warn_count
```

## Visualization

Timechart with overlay, Table (namespace, spike z-score), Single value (anomaly intervals).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
