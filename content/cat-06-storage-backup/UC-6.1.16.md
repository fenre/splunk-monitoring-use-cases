<!-- AUTO-GENERATED from UC-6.1.16.json — DO NOT EDIT -->

---
id: "6.1.16"
title: "SMB / CIFS Share Availability"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.16 · SMB / CIFS Share Availability

## Description

Windows/SMB share reachability is critical for file-serving workloads. Monitoring ensures shares are accessible before users report issues.

## Value

Windows/SMB share reachability is critical for file-serving workloads. Monitoring ensures shares are accessible before users report issues.

## Implementation

Deploy scripted input on Windows or Linux probe host. Use `smbclient -L //server` or `net use \\server\share` (Windows) to test connectivity. Optionally perform read/write test and measure latency. Run every 5–10 minutes. Index share_path, server, status, latency_ms. Alert on status != ok or latency exceeding threshold. Use domain credentials with minimal read-only access.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (smbclient, net use).
• Ensure the following data sources are available: SMB share probe results.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy scripted input on Windows or Linux probe host. Use `smbclient -L //server` or `net use \\server\share` (Windows) to test connectivity. Optionally perform read/write test and measure latency. Run every 5–10 minutes. Index share_path, server, status, latency_ms. Alert on status != ok or latency exceeding threshold. Use domain credentials with minimal read-only access.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="smb:probe"
| search status!="ok" OR latency_ms>1000
| table _time, share_path, server, status, latency_ms, error_message
| sort -_time
```

Understanding this SPL

**SMB / CIFS Share Availability** — Windows/SMB share reachability is critical for file-serving workloads. Monitoring ensures shares are accessible before users report issues.

Documented **Data sources**: SMB share probe results. **App/TA** (typical add-on context): Custom scripted input (smbclient, net use). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: smb:probe. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="smb:probe". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **SMB / CIFS Share Availability**): table _time, share_path, server, status, latency_ms, error_message
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare the same metric, object name, and interval in the vendor or cloud console (array, backup, or object store) that is the source of truth for this feed.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Point on-call to the ONTAP or array runbook, Cisco SAN references, and SNMP/REST credentials already used in production—not generic platform steps only. Consider visualizations: Table (shares with status and latency), Single value (unreachable shares count), Line chart (latency trend per share), Status grid (share × server).

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
index=storage sourcetype="smb:probe"
| search status!="ok" OR latency_ms>1000
| table _time, share_path, server, status, latency_ms, error_message
| sort -_time
```

## Visualization

Table (shares with status and latency), Single value (unreachable shares count), Line chart (latency trend per share), Status grid (share × server).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
