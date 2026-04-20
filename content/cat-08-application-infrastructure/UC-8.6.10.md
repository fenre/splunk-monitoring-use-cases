---
id: "8.6.10"
title: "Envoy Proxy Upstream Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.6.10 · Envoy Proxy Upstream Health

## Description

Upstream cluster health, retry rate, and circuit breaker trips indicate Envoy proxy and backend service health. Detection enables rapid isolation of failing upstreams.

## Value

Upstream cluster health, retry rate, and circuit breaker trips indicate Envoy proxy and backend service health. Detection enables rapid isolation of failing upstreams.

## Implementation

Enable Envoy admin interface (`/stats`). Poll via scripted input or Prometheus scrape every 30 seconds. Parse envoy_cluster_upstream_cx_active, envoy_cluster_upstream_rq_retry, envoy_cluster_upstream_rq_retry_overflow, circuit_breakers.*.rq_open. Forward to Splunk via HEC. Alert when retry rate spikes or circuit breaker opens. Correlate with upstream service health checks.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom (Envoy admin /stats, Prometheus metrics).
• Ensure the following data sources are available: Envoy /stats endpoint (envoy_cluster_upstream_cx_active, envoy_cluster_upstream_rq_retry).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Envoy admin interface (`/stats`). Poll via scripted input or Prometheus scrape every 30 seconds. Parse envoy_cluster_upstream_cx_active, envoy_cluster_upstream_rq_retry, envoy_cluster_upstream_rq_retry_overflow, circuit_breakers.*.rq_open. Forward to Splunk via HEC. Alert when retry rate spikes or circuit breaker opens. Correlate with upstream service health checks.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=mesh sourcetype="envoy:stats"
| search "envoy_cluster_upstream" ("cx_active" OR "rq_retry" OR "circuit_breakers")
| rex "envoy_cluster\.(?<cluster>[^.]+)\.(?<metric>\w+)=(?<value>\d+)"
| stats latest(value) as val by cluster, metric
| where metric=="rq_retry" AND val > 0 OR metric=="circuit_breakers_default_rq_open" AND val > 0
```

Understanding this SPL

**Envoy Proxy Upstream Health** — Upstream cluster health, retry rate, and circuit breaker trips indicate Envoy proxy and backend service health. Detection enables rapid isolation of failing upstreams.

Documented **Data sources**: Envoy /stats endpoint (envoy_cluster_upstream_cx_active, envoy_cluster_upstream_rq_retry). **App/TA** (typical add-on context): Custom (Envoy admin /stats, Prometheus metrics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: mesh; **sourcetype**: envoy:stats. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=mesh, sourcetype="envoy:stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by cluster, metric** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where metric=="rq_retry" AND val > 0 OR metric=="circuit_breakers_default_rq_open" AND val > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (cluster × health), Line chart (retry rate over time), Table (clusters with circuit breaker trips), Single value (active circuit breakers).

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=mesh sourcetype="envoy:stats"
| search "envoy_cluster_upstream" ("cx_active" OR "rq_retry" OR "circuit_breakers")
| rex "envoy_cluster\.(?<cluster>[^.]+)\.(?<metric>\w+)=(?<value>\d+)"
| stats latest(value) as val by cluster, metric
| where metric=="rq_retry" AND val > 0 OR metric=="circuit_breakers_default_rq_open" AND val > 0
```

## Visualization

Status grid (cluster × health), Line chart (retry rate over time), Table (clusters with circuit breaker trips), Single value (active circuit breakers).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
