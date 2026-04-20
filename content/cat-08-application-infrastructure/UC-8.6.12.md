---
id: "8.6.12"
title: "HashiCorp Consul Service Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.6.12 · HashiCorp Consul Service Health

## Description

Service registration, deregistration, and health check failures indicate Consul service discovery health. Critical checks mean services are unavailable for discovery and routing.

## Value

Service registration, deregistration, and health check failures indicate Consul service discovery health. Critical checks mean services are unavailable for discovery and routing.

## Implementation

Poll Consul `/v1/health/state/critical` and `/v1/catalog/services` via scripted input every minute. Parse Node, ServiceID, CheckID, Status, Output. Forward to Splunk via HEC. Alert when any service has critical health. Track service registration/deregistration events from catalog changes. Correlate with deployment events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom (Consul HTTP API).
• Ensure the following data sources are available: Consul `/v1/health/state/critical`, `/v1/catalog/services`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll Consul `/v1/health/state/critical` and `/v1/catalog/services` via scripted input every minute. Parse Node, ServiceID, CheckID, Status, Output. Forward to Splunk via HEC. Alert when any service has critical health. Track service registration/deregistration events from catalog changes. Correlate with deployment events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=consul sourcetype="consul:health"
| where status=="critical"
| stats count, latest(Output) as Output by Node, ServiceID, CheckID
| table Node, ServiceID, CheckID, count, Output
```

Understanding this SPL

**HashiCorp Consul Service Health** — Service registration, deregistration, and health check failures indicate Consul service discovery health. Critical checks mean services are unavailable for discovery and routing.

Documented **Data sources**: Consul `/v1/health/state/critical`, `/v1/catalog/services`. **App/TA** (typical add-on context): Custom (Consul HTTP API). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: consul; **sourcetype**: consul:health. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=consul, sourcetype="consul:health". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where status=="critical"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by Node, ServiceID, CheckID** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Pipeline stage (see **HashiCorp Consul Service Health**): table Node, ServiceID, CheckID, count, Output


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (service × health), Table (critical services), Single value (critical check count), Timeline (health transitions).

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
index=consul sourcetype="consul:health"
| where status=="critical"
| stats count, latest(Output) as Output by Node, ServiceID, CheckID
| table Node, ServiceID, CheckID, count, Output
```

## Visualization

Status grid (service × health), Table (critical services), Single value (critical check count), Timeline (health transitions).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
