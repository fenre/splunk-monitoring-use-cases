---
id: "6.1.14"
title: "Ceph Cluster Health and OSD Status"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.1.14 · Ceph Cluster Health and OSD Status

## Description

Ceph health warnings, OSD down/out events, and placement group (PG) state issues can lead to data unavailability or loss. Monitoring ensures rapid response to cluster degradation.

## Value

Ceph health warnings, OSD down/out events, and placement group (PG) state issues can lead to data unavailability or loss. Monitoring ensures rapid response to cluster degradation.

## Implementation

Run `ceph status --format json` and `ceph osd tree --format json` via cron or Splunk scripted input every 5 minutes. Parse JSON and extract health, osd_map (num_up, num_in, num_down), and pg_summary. Index to Splunk. Alert on health != HEALTH_OK, osd_down > 0, osd_out > 0, or PG states containing "degraded" or "stuck". Correlate OSD events with disk failure logs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (ceph status --format json).
• Ensure the following data sources are available: ceph status JSON, ceph osd tree, ceph pg stat.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run `ceph status --format json` and `ceph osd tree --format json` via cron or Splunk scripted input every 5 minutes. Parse JSON and extract health, osd_map (num_up, num_in, num_down), and pg_summary. Index to Splunk. Alert on health != HEALTH_OK, osd_down > 0, osd_out > 0, or PG states containing "degraded" or "stuck". Correlate OSD events with disk failure logs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="ceph:status"
| search health!="HEALTH_OK" OR osd_down>0 OR osd_out>0 OR "degraded" OR "stuck"
| eval pg_degraded=if(match(pg_summary, "degraded"), 1, 0)
| table _time, health, health_detail, osd_down, osd_out, osd_up, pg_degraded, pg_summary
| sort -_time
```

Understanding this SPL

**Ceph Cluster Health and OSD Status** — Ceph health warnings, OSD down/out events, and placement group (PG) state issues can lead to data unavailability or loss. Monitoring ensures rapid response to cluster degradation.

Documented **Data sources**: ceph status JSON, ceph osd tree, ceph pg stat. **App/TA** (typical add-on context): Custom scripted input (ceph status --format json). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: ceph:status. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="ceph:status". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `eval` defines or adjusts **pg_degraded** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Ceph Cluster Health and OSD Status**): table _time, health, health_detail, osd_down, osd_out, osd_up, pg_degraded, pg_summary
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (cluster health status), Table (OSD up/down/out counts), Timeline (health and OSD events), Bar chart (PG states distribution).

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
index=storage sourcetype="ceph:status"
| search health!="HEALTH_OK" OR osd_down>0 OR osd_out>0 OR "degraded" OR "stuck"
| eval pg_degraded=if(match(pg_summary, "degraded"), 1, 0)
| table _time, health, health_detail, osd_down, osd_out, osd_up, pg_degraded, pg_summary
| sort -_time
```

## Visualization

Single value (cluster health status), Table (OSD up/down/out counts), Timeline (health and OSD events), Bar chart (PG states distribution).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
