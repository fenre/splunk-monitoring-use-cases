<!-- AUTO-GENERATED from UC-2.5.1.json — DO NOT EDIT -->

---
id: "2.5.1"
title: "IGEL Device Fleet Online/Offline Status"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.5.1 · IGEL Device Fleet Online/Offline Status

## Description

IGEL thin clients are the primary interface for VDI users in healthcare, finance, and enterprise environments. When a device goes offline, the user cannot access virtual desktops or published applications. Monitoring fleet-wide online/offline ratios and identifying persistently offline devices enables rapid remediation before users are affected at scale.

## Value

IGEL thin clients are the primary interface for VDI users in healthcare, finance, and enterprise environments. When a device goes offline, the user cannot access virtual desktops or published applications. Monitoring fleet-wide online/offline ratios and identifying persistently offline devices enables rapid remediation before users are affected at scale.

## Implementation

Create a scripted input that polls `GET /v3/thinclients` from the IGEL UMS REST API (IMI v3) every 5 minutes. Authenticate using a dedicated UMS service account with read-only permissions. Parse each device's `unitID`, `name`, `lastIP`, `movedToBin`, and online status. Index as JSON events. Group by UMS directory path (used as site/location). Alert when fleet-wide online percentage drops below 90% or when more than 10 devices at a single site go offline simultaneously.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input polling IGEL UMS REST API (`GET /v3/thinclients`).
• Ensure the following data sources are available: `index=endpoint` `sourcetype="igel:ums:inventory"` fields `device_name`, `online_status`, `last_ip`, `site`, `directory_path`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input that polls `GET /v3/thinclients` from the IGEL UMS REST API (IMI v3) every 5 minutes. Authenticate using a dedicated UMS service account with read-only permissions. Parse each device's `unitID`, `name`, `lastIP`, `movedToBin`, and online status. Index as JSON events. Group by UMS directory path (used as site/location). Alert when fleet-wide online percentage drops below 90% or when more than 10 devices at a single site go offline simultaneously.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=endpoint sourcetype="igel:ums:inventory"
| stats latest(online_status) as status, latest(last_ip) as last_ip, latest(directory_path) as site by device_name
| eval status_label=if(status="true", "Online", "Offline")
| stats count as total, sum(eval(if(status="true",1,0))) as online_count by site
| eval offline_count=total-online_count
| eval online_pct=round(online_count/total*100,1)
| table site, total, online_count, offline_count, online_pct
| sort -offline_count
```

Understanding this SPL

**IGEL Device Fleet Online/Offline Status** — IGEL thin clients are the primary interface for VDI users in healthcare, finance, and enterprise environments. When a device goes offline, the user cannot access virtual desktops or published applications. Monitoring fleet-wide online/offline ratios and identifying persistently offline devices enables rapid remediation before users are affected at scale.

Documented **Data sources**: `index=endpoint` `sourcetype="igel:ums:inventory"` fields `device_name`, `online_status`, `last_ip`, `site`, `directory_path`. **App/TA** (typical add-on context): Custom scripted input polling IGEL UMS REST API (`GET /v3/thinclients`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: endpoint; **sourcetype**: igel:ums:inventory. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=endpoint, sourcetype="igel:ums:inventory". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by device_name** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **status_label** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by site** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **offline_count** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **online_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **IGEL Device Fleet Online/Offline Status**): table site, total, online_count, offline_count, online_pct
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (fleet online %), Table (sites ranked by offline count), Status grid (device online/offline by site).

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
index=endpoint sourcetype="igel:ums:inventory"
| stats latest(online_status) as status, latest(last_ip) as last_ip, latest(directory_path) as site by device_name
| eval status_label=if(status="true", "Online", "Offline")
| stats count as total, sum(eval(if(status="true",1,0))) as online_count by site
| eval offline_count=total-online_count
| eval online_pct=round(online_count/total*100,1)
| table site, total, online_count, offline_count, online_pct
| sort -offline_count
```

## Visualization

Single value (fleet online %), Table (sites ranked by offline count), Status grid (device online/offline by site).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
