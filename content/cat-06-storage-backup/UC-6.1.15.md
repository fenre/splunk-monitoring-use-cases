---
id: "6.1.15"
title: "NFS Export Availability"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.15 · NFS Export Availability

## Description

NFS mount point reachability and latency directly affect application availability. Monitoring from client perspective ensures end-to-end access validation.

## Value

NFS mount point reachability and latency directly affect application availability. Monitoring from client perspective ensures end-to-end access validation.

## Implementation

Deploy scripted input on one or more probe hosts. Script performs `showmount -e <server>` and attempts `mount -t nfs <server>:<export> <mountpoint>` or uses `rpcinfo -p` and a simple read/write test. Measure latency and record success/failure. Run every 5–10 minutes. Index results with export_path, server, status, latency_ms. Alert on status != ok or latency > 500 ms.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (showmount, mount probes).
• Ensure the following data sources are available: NFS mount probe results, rpcinfo output.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy scripted input on one or more probe hosts. Script performs `showmount -e <server>` and attempts `mount -t nfs <server>:<export> <mountpoint>` or uses `rpcinfo -p` and a simple read/write test. Measure latency and record success/failure. Run every 5–10 minutes. Index results with export_path, server, status, latency_ms. Alert on status != ok or latency > 500 ms.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="nfs:probe"
| search status!="ok" OR latency_ms>500
| table _time, export_path, server, status, latency_ms, error_message
| sort -_time
```

Understanding this SPL

**NFS Export Availability** — NFS mount point reachability and latency directly affect application availability. Monitoring from client perspective ensures end-to-end access validation.

Documented **Data sources**: NFS mount probe results, rpcinfo output. **App/TA** (typical add-on context): Custom scripted input (showmount, mount probes). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: nfs:probe. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="nfs:probe". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **NFS Export Availability**): table _time, export_path, server, status, latency_ms, error_message
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (exports with status and latency), Single value (unreachable exports count), Line chart (latency trend per export), Status grid (export × server).

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
index=storage sourcetype="nfs:probe"
| search status!="ok" OR latency_ms>500
| table _time, export_path, server, status, latency_ms, error_message
| sort -_time
```

## Visualization

Table (exports with status and latency), Single value (unreachable exports count), Line chart (latency trend per export), Status grid (export × server).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
