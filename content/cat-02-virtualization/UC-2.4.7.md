---
id: "2.4.7"
title: "oVirt / RHV Data Center Health"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.4.7 · oVirt / RHV Data Center Health

## Description

Data center and storage domain operational status for oVirt and Red Hat Virtualization (RHV). Detects storage domain maintenance mode, data center connectivity issues, and storage domain activation failures that prevent VM operations.

## Value

Data center and storage domain operational status for oVirt and Red Hat Virtualization (RHV). Detects storage domain maintenance mode, data center connectivity issues, and storage domain activation failures that prevent VM operations.

## Implementation

Create scripted input polling oVirt API: `GET /api/datacenters` and `GET /api/storagedomains`. Authenticate via oVirt SSO (username/password or token). Parse status (up/down/maintenance), active flag, and available space. Run every 5 minutes. Alert when data center status != "up" or storage domain status != "active". Create separate sourcetypes for datacenter and storagedomain events. Monitor storage domain available percentage for capacity. Correlate with oVirt engine logs for root cause.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom (oVirt REST API input).
• Ensure the following data sources are available: oVirt REST API (`/api/datacenters`, `/api/storagedomains`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input polling oVirt API: `GET /api/datacenters` and `GET /api/storagedomains`. Authenticate via oVirt SSO (username/password or token). Parse status (up/down/maintenance), active flag, and available space. Run every 5 minutes. Alert when data center status != "up" or storage domain status != "active". Create separate sourcetypes for datacenter and storagedomain events. Monitor storage domain available percentage for capacity. Correlate with oVirt engine logs for root cause.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=virtualization sourcetype="ovirt_datacenter"
| stats latest(status) as dc_status, latest(local) as local_dc, latest(name) as dc_name by id
| where dc_status!="up"
| table dc_name, dc_status, local_dc
```

Understanding this SPL

**oVirt / RHV Data Center Health** — Data center and storage domain operational status for oVirt and Red Hat Virtualization (RHV). Detects storage domain maintenance mode, data center connectivity issues, and storage domain activation failures that prevent VM operations.

Documented **Data sources**: oVirt REST API (`/api/datacenters`, `/api/storagedomains`). **App/TA** (typical add-on context): Custom (oVirt REST API input). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: virtualization; **sourcetype**: ovirt_datacenter. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=virtualization, sourcetype="ovirt_datacenter". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where dc_status!="up"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **oVirt / RHV Data Center Health**): table dc_name, dc_status, local_dc


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (data centers and storage domains), Table (operational status), Gauge (storage domain capacity).

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
index=virtualization sourcetype="ovirt_datacenter"
| stats latest(status) as dc_status, latest(local) as local_dc, latest(name) as dc_name by id
| where dc_status!="up"
| table dc_name, dc_status, local_dc
```

## Visualization

Status grid (data centers and storage domains), Table (operational status), Gauge (storage domain capacity).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
