<!-- AUTO-GENERATED from UC-6.1.13.json — DO NOT EDIT -->

---
id: "6.1.13"
title: "TrueNAS / FreeNAS Pool Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.1.13 · TrueNAS / FreeNAS Pool Health

## Description

ZFS pool degradation, scrub results, and resilver progress directly impact data integrity. Early detection of unhealthy pools prevents data loss and enables timely intervention during rebuilds.

## Value

ZFS pool degradation, scrub results, and resilver progress directly impact data integrity. Early detection of unhealthy pools prevents data loss and enables timely intervention during rebuilds.

## Implementation

Create scripted input or HTTP Event Collector (HEC) input that polls TrueNAS REST API every 5–15 minutes. Use `/api/v2.0/pool` for pool list and `/api/v2.0/pool/id/{id}` for detailed status including scrub/resilver. Authenticate with API key. Parse JSON response and index to Splunk with sourcetype `truenas:pool`. Alert on health != HEALTHY or status != ONLINE. Track resilver progress and ETA during rebuilds.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom (TrueNAS REST API).
• Ensure the following data sources are available: TrueNAS API (/api/v2.0/pool, /api/v2.0/pool/id/X).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input or HTTP Event Collector (HEC) input that polls TrueNAS REST API every 5–15 minutes. Use `/api/v2.0/pool` for pool list and `/api/v2.0/pool/id/{id}` for detailed status including scrub/resilver. Authenticate with API key. Parse JSON response and index to Splunk with sourcetype `truenas:pool`. Alert on health != HEALTHY or status != ONLINE. Track resilver progress and ETA during rebuilds.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="truenas:pool"
| search status!="ONLINE" OR health!="HEALTHY" OR "resilver" OR "scrub"
| eval health_status=coalesce(health, status)
| table _time, pool_name, health_status, status, size, used_pct, resilver_progress, scrub_status
| sort -_time
```

Understanding this SPL

**TrueNAS / FreeNAS Pool Health** — ZFS pool degradation, scrub results, and resilver progress directly impact data integrity. Early detection of unhealthy pools prevents data loss and enables timely intervention during rebuilds.

Documented **Data sources**: TrueNAS API (/api/v2.0/pool, /api/v2.0/pool/id/X). **App/TA** (typical add-on context): Custom (TrueNAS REST API). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: truenas:pool. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="truenas:pool". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `eval` defines or adjusts **health_status** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **TrueNAS / FreeNAS Pool Health**): table _time, pool_name, health_status, status, size, used_pct, resilver_progress, scrub_status
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare pools, datasets, and alerts with the TrueNAS web UI or SCALE CLI for the same resource and timestamp.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Point on-call to the ONTAP or array runbook, Cisco SAN references, and SNMP/REST credentials already used in production—not generic platform steps only. Consider visualizations: Single value (pools not healthy), Table (pool name, health, resilver %), Timeline (health change events), Gauge (resilver progress during rebuild).

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
index=storage sourcetype="truenas:pool"
| search status!="ONLINE" OR health!="HEALTHY" OR "resilver" OR "scrub"
| eval health_status=coalesce(health, status)
| table _time, pool_name, health_status, status, size, used_pct, resilver_progress, scrub_status
| sort -_time
```

## Visualization

Single value (pools not healthy), Table (pool name, health, resilver %), Timeline (health change events), Gauge (resilver progress during rebuild).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
