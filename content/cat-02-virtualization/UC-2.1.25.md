---
id: "2.1.25"
title: "Storage I/O Control (SIOC) Throttling"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.1.25 · Storage I/O Control (SIOC) Throttling

## Description

SIOC throttles VM disk I/O when datastore latency exceeds thresholds (default 30ms). When SIOC activates, VMs experience injected latency that appears as slow storage from the guest perspective. Detecting SIOC activation reveals contention invisible from the guest OS.

## Value

SIOC throttles VM disk I/O when datastore latency exceeds thresholds (default 30ms). When SIOC activates, VMs experience injected latency that appears as slow storage from the guest perspective. Detecting SIOC activation reveals contention invisible from the guest OS.

## Implementation

Collected via Splunk_TA_vmware. SIOC triggers when datastore latency exceeds its configured threshold. Monitor the sizeNormalizedDatastoreLatency counter which SIOC uses for its decisions. Alert when latency approaches the SIOC threshold (default 30ms). Correlate with per-VM IOPS from UC-2.1.17 to identify the VM causing contention.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:perf:datastore`, vCenter events.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collected via Splunk_TA_vmware. SIOC triggers when datastore latency exceeds its configured threshold. Monitor the sizeNormalizedDatastoreLatency counter which SIOC uses for its decisions. Alert when latency approaches the SIOC threshold (default 30ms). Correlate with per-VM IOPS from UC-2.1.17 to identify the VM causing contention.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:perf:datastore" counter="datastore.sizeNormalizedDatastoreLatency.average"
| stats avg(Value) as avg_latency by datastore, host
| where avg_latency > 25
| sort -avg_latency
| table datastore, host, avg_latency
```

Understanding this SPL

**Storage I/O Control (SIOC) Throttling** — SIOC throttles VM disk I/O when datastore latency exceeds thresholds (default 30ms). When SIOC activates, VMs experience injected latency that appears as slow storage from the guest perspective. Detecting SIOC activation reveals contention invisible from the guest OS.

Documented **Data sources**: `sourcetype=vmware:perf:datastore`, vCenter events. **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:perf:datastore. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:perf:datastore". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by datastore, host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where avg_latency > 25` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Storage I/O Control (SIOC) Throttling**): table datastore, host, avg_latency


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (datastore latency over time with SIOC threshold line), Table (datastores near threshold), Heatmap (datastores by latency).

## SPL

```spl
index=vmware sourcetype="vmware:perf:datastore" counter="datastore.sizeNormalizedDatastoreLatency.average"
| stats avg(Value) as avg_latency by datastore, host
| where avg_latency > 25
| sort -avg_latency
| table datastore, host, avg_latency
```

## Visualization

Line chart (datastore latency over time with SIOC threshold line), Table (datastores near threshold), Heatmap (datastores by latency).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
