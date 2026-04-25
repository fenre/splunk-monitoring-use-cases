<!-- AUTO-GENERATED from UC-1.2.64.json — DO NOT EDIT -->

---
id: "1.2.64"
title: "Event Log Channel Size / Overflow"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.2.64 · Event Log Channel Size / Overflow

## Description

When event logs reach maximum size with overwrite-oldest policy, critical security events are lost. With do-not-overwrite policy, the log stops recording entirely.

## Value

If a channel stops, your audit trail stops—this is a *data-loss* class alert for regulated shops, not a perf chart.

## Implementation

Deploy a scripted input that runs `wevtutil gl Security` (and other critical channels) every 15 minutes, parsing current size vs. max size. Default Security log is 20MB — often insufficient on DCs and servers with detailed auditing. Alert when any critical log exceeds 90% capacity. Alternatively, monitor EventCode 1101 (audit log full) in the System log. Recommended: increase Security log to 1GB+ on DCs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, custom scripted input.
• Ensure the following data sources are available: `sourcetype=WinEventLog:System` (EventCode 6005) + custom scripted input (`wevtutil gl Security`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy a scripted input that runs `wevtutil gl Security` (and other critical channels) every 15 minutes, parsing current size vs. max size. Default Security log is 20MB — often insufficient on DCs and servers with detailed auditing. Alert when any critical log exceeds 90% capacity. Alternatively, monitor EventCode 1101 (audit log full) in the System log. Recommended: increase Security log to 1GB+ on DCs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=windows:eventlog:size
| where used_pct > 90
| table _time, host, log_name, current_size_MB, max_size_MB, used_pct
```

Understanding this SPL

**Event Log Channel Size / Overflow** — When event logs reach maximum size with overwrite-oldest policy, critical security events are lost. With do-not-overwrite policy, the log stops recording entirely.

Documented **Data sources**: `sourcetype=WinEventLog:System` (EventCode 6005) + custom scripted input (`wevtutil gl Security`). **App/TA** (typical add-on context): `Splunk_TA_windows`, custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: windows:eventlog:size. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=windows:eventlog:size. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where used_pct > 90` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Event Log Channel Size / Overflow**): table _time, host, log_name, current_size_MB, max_size_MB, used_pct

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.dest span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

CIM tstats is an approximate mirror when Windows TA field extractions and CIM tags are complete. Enable the matching data model acceleration or tstats may return no rows.



Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (log fill percentage), Table (logs near capacity), Bar chart (log sizes by channel).

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
index=os sourcetype=windows:eventlog:size
| where used_pct > 90
| table _time, host, log_name, current_size_MB, max_size_MB, used_pct
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.dest span=1h
| where count>0
```

## Visualization

Gauge (log fill percentage), Table (logs near capacity), Bar chart (log sizes by channel).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
