<!-- AUTO-GENERATED from UC-4.1.63.json — DO NOT EDIT -->

---
id: "4.1.63"
title: "ECS Service Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.1.63 · ECS Service Health

## Description

Service-level running count versus desired indicates deployment failures, capacity shortfall, or health check flapping.

## Value

Service-level running count versus desired indicates deployment failures, capacity shortfall, or health check flapping.

## Implementation

Ingest ECS service events from EventBridge for steady-state issues. Dashboard desired vs running from `DescribeServices` snapshots if scripted. Alert on failed deployments or service unable to reach steady state.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudwatch` (AWS/ECS — CPUUtilization, MemoryUtilization), `sourcetype=aws:cloudwatch:events` (service events).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest ECS service events from EventBridge for steady-state issues. Dashboard desired vs running from `DescribeServices` snapshots if scripted. Alert on failed deployments or service unable to reach steady state.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/ECS" (metric_name="CPUUtilization" OR metric_name="MemoryUtilization")
| stats latest(Average) as util by ClusterName, ServiceName, metric_name
| where util > 85
```

Understanding this SPL

**ECS Service Health** — Service-level running count versus desired indicates deployment failures, capacity shortfall, or health check flapping.

Documented **Data sources**: `sourcetype=aws:cloudwatch` (AWS/ECS — CPUUtilization, MemoryUtilization), `sourcetype=aws:cloudwatch:events` (service events). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by ClusterName, ServiceName, metric_name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where util > 85` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (service health), Line chart (CPU/memory by service), Table (cluster, service, failures).

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
index=aws sourcetype="aws:cloudwatch" namespace="AWS/ECS" (metric_name="CPUUtilization" OR metric_name="MemoryUtilization")
| stats latest(Average) as util by ClusterName, ServiceName, metric_name
| where util > 85
```

## CIM SPL

```spl
| tstats `summariesonly` max(Performance.cpu_load_percent) as peak
  from datamodel=Performance.Performance
  by Performance.object Performance.host span=1h
| where isnotnull(peak)
| sort - peak
```

## Visualization

Status grid (service health), Line chart (CPU/memory by service), Table (cluster, service, failures).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
